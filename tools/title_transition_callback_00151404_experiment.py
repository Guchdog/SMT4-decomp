#!/usr/bin/env python3
"""Run original callback candidate 0x00151404 and its reached callees on H1."""
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

CALLBACK = 0x00151404
CALLBACK_END = 0x00151468  # before embedded literal/data words
FIRST_FADE_ENTRY = 0x002872A4
FIRST_FADE_BODY = 0x002872B0
FIRST_FADE_CALL = 0x002872E4
FIRST_FADE_CONTINUATION = 0x002872E8
SOFT_FLOAT_ADD = 0x0014D608
SOFT_FLOAT_ADD_CONTINUATION = 0x0014D670
SOFT_FLOAT_HELPER = 0x0015258C
SOFT_FLOAT_DIV_HELPER = 0x002A337C
UNEXPECTED_SPECIAL_CALLBACK = 0x002A464E
SECOND_FADE_ENTRY = 0x0020FFA0
SECOND_FADE_BODY = 0x0020FFAC
HELP = 0x001EA12C
PRESENTATION_STOP = 0x001EA15C
PRESENTATION_CALLEE = 0x0029F10C
TBB_GLOBAL = 0x002C0EC4
TBB_SUBTABLE = 0x002AC2F4
TBB_PAYLOAD = 0x002C0E9C
CODE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
CALLBACK_PCS = tuple(range(CALLBACK, CALLBACK_END, 4))


def put32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", data, offset, value & 0xFFFFFFFF)


def make_memory() -> bytes:
    data = bytearray(initial_memory())
    # Same explicit first-positive path, with only the indirect function
    # pointer changed to the statically registered type-1 candidate.
    put32(data, NESTED_B + 0x4C, CALLBACK)
    return bytes(data)


def run_original_151404(image: bytes, raw_tbb: bytes) -> dict:
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
    callback = {"count": 0, "entry": None, "before_return": None,
                "after_return": None, "stack_writes": []}
    callees: list[dict] = []
    stopped = {"at_boundary": False, "presentation_args": None}

    def capture(machine):
        return {
            "r0": hex(machine.reg_read(arm.UC_ARM_REG_R0)),
            "r1": hex(machine.reg_read(arm.UC_ARM_REG_R1)),
            "r2": hex(machine.reg_read(arm.UC_ARM_REG_R2)),
            "r3": hex(machine.reg_read(arm.UC_ARM_REG_R3)),
            "r4": hex(machine.reg_read(arm.UC_ARM_REG_R4)),
            "lr": hex(machine.reg_read(arm.UC_ARM_REG_LR)),
            "sp": hex(machine.reg_read(arm.UC_ARM_REG_SP)),
            "s0_bits": hex(machine.reg_read(arm.UC_ARM_REG_S0)),
            "s1_bits": hex(machine.reg_read(arm.UC_ARM_REG_S1)),
            "s2_bits": hex(machine.reg_read(arm.UC_ARM_REG_S2)),
            "s3_bits": hex(machine.reg_read(arm.UC_ARM_REG_S3)),
            "s16_bits": hex(machine.reg_read(arm.UC_ARM_REG_S16)),
            "s17_bits": hex(machine.reg_read(arm.UC_ARM_REG_S17)),
            "s18_bits": hex(machine.reg_read(arm.UC_ARM_REG_S18)),
            "fpscr": hex(machine.reg_read(arm.UC_ARM_REG_FPSCR)),
        }

    def code_hook(machine, address, _size, _user):
        trace.append(address)
        if address in (FIRST_FADE_ENTRY, SOFT_FLOAT_ADD, SOFT_FLOAT_HELPER,
                       SOFT_FLOAT_DIV_HELPER, UNEXPECTED_SPECIAL_CALLBACK,
                       SECOND_FADE_ENTRY, TBB_GLOBAL, TBB_SUBTABLE, TBB_PAYLOAD):
            row = {"target": hex(address), **capture(machine)}
            direct_calls.append(row)
            if address in (SOFT_FLOAT_ADD, SOFT_FLOAT_HELPER,
                           SOFT_FLOAT_DIV_HELPER, UNEXPECTED_SPECIAL_CALLBACK):
                callees.append({"target": hex(address), "entry": capture(machine)})
        if address == CALLBACK:
            callback["count"] += 1
            callback["entry"] = capture(machine)
        if address == CALLBACK_END - 4:
            callback["before_return"] = capture(machine)
        if address == FIRST_FADE_CONTINUATION:
            callback["after_return"] = capture(machine)
        if address == SOFT_FLOAT_ADD_CONTINUATION:
            callees.append({"target": hex(SOFT_FLOAT_ADD),
                            "continuation": capture(machine)})
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
            if CALLBACK <= pc < CALLBACK_END:
                callback["stack_writes"].append(row)

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
        uc.emu_start(START, 0, count=8192)
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
        (SP - 0x40, SP),
    )
    allowed_code_constants = {
        0x00151468, 0x0015146C, 0x0014D6DC, 0x0014D6E0,
        0x0014D6EC, 0x0014D704, 0x002A33F0, 0x002A33F4,
        0x002C0EDC, 0x002AC348, 0x002AC34C, 0x002C0EC0, 0x001E9EC4,
    }
    unexpected_reads = [row for row in reads
                        if int(row["address"], 16) not in allowed_code_constants
                        and not any(start <= int(row["address"], 16) < end
                                    for start, end in allowed_ranges)]
    if unexpected_reads:
        raise AssertionError(f"read outside explicit state/stack/TBB/constants: {unexpected_reads}")
    if callback["count"] != 1 or callback["entry"] is None:
        raise AssertionError(f"callback was not entered exactly once: {callback}")
    callback_pcs = [pc for pc in trace if CALLBACK <= pc < CALLBACK_END]
    if not callback_pcs:
        raise AssertionError("the candidate callback's original instructions did not execute")
    if any(not (SP - 0x20 <= int(row["address"], 16) < SP)
           for row in callback["stack_writes"]):
        raise AssertionError(f"candidate callback wrote outside its stack frame: {callback['stack_writes']}")
    if SOFT_FLOAT_DIV_HELPER in trace:
        raise AssertionError("this input unexpectedly reached the earlier optional division path")
    if UNEXPECTED_SPECIAL_CALLBACK in trace:
        raise AssertionError("the direct callee reached an unmodeled exceptional BLX")
    if SOFT_FLOAT_ADD not in trace or SOFT_FLOAT_HELPER not in trace:
        raise AssertionError(f"expected original direct callee chain was not reached: {callees}")
    if callback["after_return"]["s0_bits"] != "0x3f400000":
        raise AssertionError(f"callback output S0 did not return 0.75: {callback}")
    if callback["after_return"]["s0_bits"] != callback["before_return"]["s0_bits"]:
        raise AssertionError("caller observed a different S0 than the callback's pre-return value")
    expected_direct = [FIRST_FADE_ENTRY, SOFT_FLOAT_ADD, SOFT_FLOAT_HELPER,
                       SECOND_FADE_ENTRY, TBB_GLOBAL, TBB_SUBTABLE, TBB_PAYLOAD]
    actual_direct = [int(row["target"], 16) for row in direct_calls]
    if actual_direct != expected_direct:
        raise AssertionError(f"unexpected direct call sequence: {[hex(v) for v in actual_direct]}")
    if SECOND_FADE_BODY in trace:
        raise AssertionError("this experiment is scoped to the first positive path")

    expected_writes = {
        SP - 8: [0x02000100], SP - 4: [0x001EA0D0],
        SP - 0x10: [0x02000A00], SP - 0x0C: [0x002872E8],
        SP - 0x20: [0x3E8000003F400000], SP - 0x18: [0],
        SP - 0x28: [0x02000A00], SP - 0x24: [0x0015145C],
        SP - 0x40: [0x3F0000003E800000], SP - 0x38: [0x3F000000],
        SP - 0x30: [0],
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
        formatted = [{**row, "address": hex(int(row["address"], 16)),
                      "value": hex(int(row["value"], 16))} for row in writes]
        raise AssertionError(f"memory-write sequence differs: {formatted}")
    if (u32(HANDLE_A) != 6 or u32(HANDLE_B) != 0 or u8(WORK + 0x94) != 1
            or f32(WORK + 0x98) != 0.75 or f32(NESTED_B + 0x38) != 0.75
            or f32(NESTED_B + 0x3C) != 1.0 or u8(NESTED_B + 0x58) != 1):
        raise AssertionError("final callback/mutator state differs")

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
        "evidence_type": "continuous pinned original ARM execution through callback 0x00151404 and reached original direct callees",
        "code_sha256": CODE_SHA256,
        "tbb_sha256": hashlib.sha256(raw_tbb).hexdigest(),
        "callback_candidate": hex(CALLBACK),
        "callback_instruction_pcs": [hex(pc) for pc in callback_pcs],
        "callback": callback,
        "stack_writes": [row for row in writes
                         if SP - 0x40 <= int(row["address"], 16) < SP],
        "reached_original_callees": callees,
        "direct_calls": direct_calls,
        "start": hex(START), "first_positive_body": hex(FIRST_FADE_BODY),
        "stop_before_presentation": hex(PRESENTATION_STOP),
        "help_entry": hex(HELP), "help_text": entry["text"],
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
            "The work/object graph and FP values are synthetic, not sampled from a live title.",
            "The callback pointer is explicitly set to 0x00151404; static type-1 registration is not proof the title runtime selects it.",
            "The callback and reached direct callees execute original pinned ARM instructions; the exceptional indirect target at 0x002A464E is not reached by this finite input.",
            "Execution stops before Camp_SetSlotMessage; no renderer, visible UI, gameplay, or Azahar behavior is claimed.",
            "The alternate 0x0020FFAC positive helper is outside this first-gate experiment.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path,
                        default=ROOT / "build/semantic-equivalence/real-assets/exefs/code.bin")
    parser.add_argument("--tbb", type=Path,
                        default=ROOT / "build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/title-transition-callback-00151404/report.json")
    args = parser.parse_args()
    report = run_original_151404(args.code.read_bytes(), args.tbb.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Title callback 0x00151404 path PASS; report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
