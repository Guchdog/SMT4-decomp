#!/usr/bin/env python3
"""Run the first positive H1 fade gate with original callback code at 0x15555c."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.semantic_experiment import (  # noqa: E402
    DATA, DATA_SIZE, STACK, STACK_SIZE, SP, Runner, arm, unicorn,
)
from tools.tbb_semantic_experiment import TITLE_TBB_SLOT_BASE, TITLE_TBB_SLOT_ID  # noqa: E402
from tools.title_help_presentation_experiment import (  # noqa: E402
    EXPECTED_HELP, extract_help_entries, verify_reference,
)
from tools.title_transition_positive_gate_experiment import (  # noqa: E402
    CHILD_B, HANDLE_A, HANDLE_B, NESTED_A, NESTED_B, START, STOP,
    TBB_CONTAINER_OFFSET, WORK, initial_memory,
)

REAL_CALLBACK = 0x0015555C
CALLBACK_CONTAINING_FUNCTION = 0x00155540
CALLBACK_RETURN_INSTRUCTION = 0x00155580
FIRST_FADE_ENTRY = 0x002872A4
FIRST_FADE_BODY = 0x002872B0
FIRST_FADE_CALL = 0x002872E4
FIRST_FADE_CONTINUATION = 0x002872E8
SECOND_FADE_ENTRY = 0x0020FFA0
SECOND_FADE_BODY = 0x0020FFAC
HELP = 0x001EA12C
PRESENTATION_STOP = 0x001EA15C
PRESENTATION_CALLEE = 0x0029F10C
TBB_GLOBAL = 0x002C0EC4
TBB_SUBTABLE = 0x002AC2F4
TBB_PAYLOAD = 0x002C0E9C
CODE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
CALLBACK_PCS = tuple(range(REAL_CALLBACK, CALLBACK_RETURN_INSTRUCTION + 4, 4))


def put32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", data, offset, value & 0xFFFFFFFF)


def make_memory() -> bytes:
    data = bytearray(initial_memory())
    # Keep the prior experiment's synthetic graph and change only its indirect
    # callback target to original pinned code. No stub bytes are installed.
    put32(data, NESTED_B + 0x4C, REAL_CALLBACK)
    return bytes(data)


def run_original_callback(image: bytes, raw_tbb: bytes) -> dict:
    if hashlib.sha256(image).hexdigest() != CODE_SHA256:
        raise ValueError("code.bin is not the pinned US reference image")
    verify_reference(image)
    if len(raw_tbb) > 0x1000:
        raise ValueError("TitleTable.tbb does not fit the explicit extra data page")
    runner = Runner(image, START)
    uc = runner.uc
    uc.mem_map(DATA + 0x1000, 0x1000,
               unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    slot_ptr = TITLE_TBB_SLOT_BASE + TITLE_TBB_SLOT_ID * 0x10 + 4
    uc.mem_protect(slot_ptr & ~0xFFF, 0x1000,
                   unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    uc.mem_write(slot_ptr, struct.pack("<I", DATA + TBB_CONTAINER_OFFSET))
    uc.mem_write(DATA + TBB_CONTAINER_OFFSET, raw_tbb)

    trace: list[int] = []
    reads: list[dict] = []
    writes: list[dict] = []
    direct_calls: list[dict] = []
    callback = {"count": 0, "entry": None, "at_return_instruction": None,
                "after_return": None, "memory_writes": []}
    stopped = {"at_boundary": False, "presentation_args": None}

    def capture(machine):
        return {
            "r0": hex(machine.reg_read(arm.UC_ARM_REG_R0)),
            "r1": hex(machine.reg_read(arm.UC_ARM_REG_R1)),
            "r2": hex(machine.reg_read(arm.UC_ARM_REG_R2)),
            "r3": hex(machine.reg_read(arm.UC_ARM_REG_R3)),
            "r4": hex(machine.reg_read(arm.UC_ARM_REG_R4)),
            "lr": hex(machine.reg_read(arm.UC_ARM_REG_LR)),
            "s0_bits": hex(machine.reg_read(arm.UC_ARM_REG_S0)),
            "s1_bits": hex(machine.reg_read(arm.UC_ARM_REG_S1)),
            "s2_bits": hex(machine.reg_read(arm.UC_ARM_REG_S2)),
            "s3_bits": hex(machine.reg_read(arm.UC_ARM_REG_S3)),
            "fpscr": hex(machine.reg_read(arm.UC_ARM_REG_FPSCR)),
        }

    def code_hook(machine, address, _size, _user):
        trace.append(address)
        if address in (FIRST_FADE_ENTRY, SECOND_FADE_ENTRY,
                       TBB_GLOBAL, TBB_SUBTABLE, TBB_PAYLOAD):
            direct_calls.append({"target": hex(address),
                                 "r0": hex(machine.reg_read(arm.UC_ARM_REG_R0)),
                                 "lr": hex(machine.reg_read(arm.UC_ARM_REG_LR))})
        if address == REAL_CALLBACK:
            callback["count"] += 1
            callback["entry"] = capture(machine)
        if address == CALLBACK_RETURN_INSTRUCTION:
            callback["at_return_instruction"] = capture(machine)
        if address == FIRST_FADE_CONTINUATION:
            callback["after_return"] = capture(machine)
        if address == PRESENTATION_STOP:
            stopped["at_boundary"] = True
            stopped["presentation_args"] = {
                "r0": hex(machine.reg_read(arm.UC_ARM_REG_R0)),
                "r1": hex(machine.reg_read(arm.UC_ARM_REG_R1)),
                "lr": hex(machine.reg_read(arm.UC_ARM_REG_LR)),
            }
            machine.emu_stop()

    def memory_hook(machine, access, address, size, value, _user):
        pc = machine.reg_read(arm.UC_ARM_REG_PC)
        if access == unicorn.UC_MEM_READ:
            reads.append({"pc": hex(pc), "address": hex(address), "size": size})
        elif access == unicorn.UC_MEM_WRITE:
            row = {"pc": hex(pc), "address": hex(address), "size": size,
                   "value": hex(value & ((1 << (size * 8)) - 1))}
            writes.append(row)
            if REAL_CALLBACK <= pc <= CALLBACK_RETURN_INSTRUCTION:
                callback["memory_writes"].append(row)

    uc.hook_add(unicorn.UC_HOOK_CODE, code_hook)
    uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE, memory_hook)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    regs = [0xA5A50000 | i for i in range(13)]
    regs[4] = DATA + WORK
    regs[5] = DATA + WORK
    regs[7] = 1
    for i, value in enumerate(regs):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), value)
    for i in range(8, 16):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_D{i}"), 0)
    uc.reg_write(arm.UC_ARM_REG_S16, struct.unpack("<I", struct.pack("<f", 0.75))[0])
    uc.reg_write(arm.UC_ARM_REG_S17, struct.unpack("<I", struct.pack("<f", 0.25))[0])
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, PRESENTATION_STOP)
    uc.mem_write(DATA, make_memory())
    uc.mem_write(STACK, bytes([0xCD]) * STACK_SIZE)
    try:
        uc.emu_start(START, 0, count=4096)
    except unicorn.UcError as exc:
        raise RuntimeError(f"ARM fault at {uc.reg_read(arm.UC_ARM_REG_PC):#x}: {exc}") from exc
    if not stopped["at_boundary"] or uc.reg_read(arm.UC_ARM_REG_PC) != PRESENTATION_STOP:
        raise RuntimeError(f"did not reach presentation boundary; PC={uc.reg_read(arm.UC_ARM_REG_PC):#x}")

    final = bytes(uc.mem_read(DATA, DATA_SIZE))
    u32 = lambda off: struct.unpack_from("<I", final, off)[0]
    u8 = lambda off: final[off]
    f32 = lambda off: struct.unpack_from("<f", final, off)[0]
    allowed_ranges = (
        (DATA + WORK, DATA + WORK + 0xA0),
        (DATA + HANDLE_A, DATA + HANDLE_A + 0x0C),
        (DATA + HANDLE_B, DATA + HANDLE_B + 0x0C),
        (DATA + 0x400, DATA + 0x460),
        (DATA + CHILD_B, DATA + CHILD_B + 0x60),
        (DATA + NESTED_A, DATA + NESTED_A + 0x1F7),
        (DATA + NESTED_B, DATA + NESTED_B + 0x1F7),
        (DATA + TBB_CONTAINER_OFFSET, DATA + TBB_CONTAINER_OFFSET + len(raw_tbb)),
        (TITLE_TBB_SLOT_BASE + TITLE_TBB_SLOT_ID * 0x10,
         TITLE_TBB_SLOT_BASE + (TITLE_TBB_SLOT_ID + 1) * 0x10),
        (0x00493BD0, 0x00493BD4),
        (SP - 8, SP),
    )
    literal_reads = {0x001E9EC4, 0x002C0EDC, 0x002AC348,
                     0x002AC34C, 0x002C0EC0}
    unexpected_reads = [row for row in reads
                        if int(row["address"], 16) not in literal_reads
                        and not any(start <= int(row["address"], 16) < end
                                    for start, end in allowed_ranges)]
    if unexpected_reads:
        raise AssertionError(f"read outside explicit model/TBB/stack/literals: {unexpected_reads}")
    if callback["count"] != 1 or callback["entry"] is None:
        raise AssertionError(f"original callback count or entry capture mismatch: {callback}")
    callback_pcs = [pc for pc in trace if REAL_CALLBACK <= pc <= CALLBACK_RETURN_INSTRUCTION]
    if tuple(callback_pcs) != CALLBACK_PCS:
        raise AssertionError(f"original callback instruction path differs: {[hex(pc) for pc in callback_pcs]}")
    if callback["memory_writes"]:
        raise AssertionError(f"original clamp callback unexpectedly wrote memory: {callback['memory_writes']}")
    if callback["at_return_instruction"]["s0_bits"] != "0x3f400000":
        raise AssertionError(f"clamp callback output before return is not 0.75: {callback}")
    if callback["after_return"]["s0_bits"] != "0x3f400000":
        raise AssertionError(f"caller did not observe clamp result: {callback}")
    expected_direct = [FIRST_FADE_ENTRY, SECOND_FADE_ENTRY,
                       TBB_GLOBAL, TBB_SUBTABLE, TBB_PAYLOAD]
    if [int(row["target"], 16) for row in direct_calls] != expected_direct:
        raise AssertionError(f"unexpected original call sequence: {direct_calls}")
    if SECOND_FADE_BODY in trace:
        raise AssertionError("this experiment is scoped to the first positive path")

    expected_writes = {
        SP - 8: [0x02000100], SP - 4: [0x001EA0D0],
        DATA + HANDLE_A: [6], DATA + NESTED_A + 0x1F6: [0],
        DATA + WORK + 0x98: [0x3F400000],
        DATA + NESTED_B + 0x38: [0x3F400000],
        DATA + NESTED_B + 0x3C: [0x3F800000],
        DATA + NESTED_B + 0x58: [1], DATA + HANDLE_B: [0],
        DATA + NESTED_B + 0x1F6: [1], DATA + WORK + 0x94: [1],
    }
    actual: dict[int, list[int]] = {}
    for row in writes:
        actual.setdefault(int(row["address"], 16), []).append(int(row["value"], 16))
    if actual != expected_writes:
        raise AssertionError(f"memory-write sequence mismatch: {actual}")
    if (u32(HANDLE_A) != 6 or u32(HANDLE_B) != 0 or u8(WORK + 0x94) != 1
            or f32(WORK + 0x98) != 0.75 or f32(NESTED_B + 0x38) != 0.75
            or f32(NESTED_B + 0x3C) != 1.0 or u8(NESTED_B + 0x58) != 1):
        raise AssertionError("final original callback/mutator values differ")

    table = extract_help_entries(raw_tbb)
    entry = table["entries"][0]
    expected_pointer = (DATA + TBB_CONTAINER_OFFSET + table["payload_file_offset"]
                        + entry["relative_payload_offset"])
    args = stopped["presentation_args"]
    if int(args["r0"], 16) != expected_pointer or int(args["r1"], 16) != 0x323232FF:
        raise AssertionError(f"unexpected help caller args: {args}")
    if entry["text"] != EXPECTED_HELP[0] or PRESENTATION_CALLEE in trace:
        raise AssertionError("help text mismatch or presentation callee entered")

    return {
        "passed": True,
        "evidence_type": "continuous pinned original ARM execution through a real in-image callback body",
        "code_sha256": CODE_SHA256,
        "tbb_sha256": hashlib.sha256(raw_tbb).hexdigest(),
        "callback_candidate": hex(REAL_CALLBACK),
        "callback_containing_symbol_range": [hex(CALLBACK_CONTAINING_FUNCTION), hex(CALLBACK_RETURN_INSTRUCTION + 4)],
        "callback_instruction_pcs": [hex(pc) for pc in callback_pcs],
        "callback": callback,
        "caller_inputs": {"s16": 0.75, "nestedB_0x44": 0.5, "nestedB_0x48": 1.0},
        "caller_clamped_value_s2": 0.75,
        "callback_output_s0": f32(NESTED_B + 0x38),
        "start": hex(START), "first_positive_entry": hex(FIRST_FADE_ENTRY),
        "first_positive_body": hex(FIRST_FADE_BODY),
        "stop_before_presentation": hex(PRESENTATION_STOP),
        "help_entry": hex(HELP), "help_text": entry["text"],
        "direct_calls": direct_calls,
        "read_count": len(reads), "reads": reads,
        "unexpected_reads": unexpected_reads,
        "write_count": len(writes), "writes": writes,
        "final_state": {"handle_a_flags": u32(HANDLE_A),
                        "handle_b_flags": u32(HANDLE_B),
                        "work_0x94": u8(WORK + 0x94),
                        "work_0x98": f32(WORK + 0x98),
                        "nestedB_0x38": f32(NESTED_B + 0x38),
                        "nestedB_0x3c": f32(NESTED_B + 0x3C),
                        "nestedB_0x58": u8(NESTED_B + 0x58)},
        "limits": [
            "The graph and FP inputs are synthetic and no live title/runtime snapshot was used.",
            "0x0015555C is run as original code from the pinned ARM image; no callback stub or replacement instruction is installed.",
            "Constructor/type-0 defaults provide static candidate evidence only; the live title asset's type byte and runtime callback target are not established here.",
            "The test stops before Camp_SetSlotMessage and establishes no renderer, visual UI, gameplay, or Azahar behavior.",
            "The second positive helper body 0x0020FFAC is outside this first-gate experiment.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path,
                        default=ROOT / "build/semantic-equivalence/real-assets/exefs/code.bin")
    parser.add_argument("--tbb", type=Path,
                        default=ROOT / "build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/title-transition-original-callback/report.json")
    args = parser.parse_args()
    report = run_original_callback(args.code.read_bytes(), args.tbb.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Title original callback path PASS; report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
