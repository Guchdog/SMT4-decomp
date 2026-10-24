#!/usr/bin/env python3
"""Exercise the first positive transition helper gate with an explicit callback stub."""
from __future__ import annotations

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

START = 0x001E9FD4
MUTATOR = 0x001EA070
HELP = 0x001EA12C
STOP = 0x001EA15C
PRESENTATION_CALLEE = 0x0029F10C
READY_VISIBLE = 0x0025A274
READY_SECOND = 0x002D569C
FADE_A = 0x002872A4
FADE_A_BODY = 0x002872B0
FADE_A_CALLBACK = 0x002872E4
FADE_A_CONTINUATION = 0x002872E8
FADE_B = 0x0020FFA0
TBB_GLOBAL = 0x002C0EC4
TBB_SUBTABLE = 0x002AC2F4
TBB_PAYLOAD = 0x002C0E9C
CODE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"

WORK, HANDLE_A, HANDLE_B = 0x100, 0x300, 0x340
CHILD_A, CHILD_B = 0x400, 0x600
NESTED_A, NESTED_B = 0x800, 0xA00
TBB_CONTAINER_OFFSET = 0x1000
CALLBACK_STUB = 0x01000100
CALLBACK_OBJECT = DATA + 0xC00
CALLBACK_WORD = 0xE12FFF1E  # bx lr; no memory effects and no FP/register writes.


def put32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", data, offset, value & 0xFFFFFFFF)


def putf32(data: bytearray, offset: int, value: float) -> None:
    struct.pack_into("<f", data, offset, value)


def initial_memory() -> bytes:
    data = bytearray([0xCD]) * DATA_SIZE
    put32(data, WORK + 0x8C, DATA + HANDLE_A)
    put32(data, WORK + 0x90, DATA + HANDLE_B)
    put32(data, WORK + 8, 0)
    data[WORK + 0x94] = 0
    put32(data, HANDLE_A, 4)  # Skip conditional alpha call on resource A.
    put32(data, HANDLE_B, 0)  # Skip conditional alpha call on resource B.
    put32(data, HANDLE_A + 8, DATA + CHILD_A)
    put32(data, HANDLE_B + 8, DATA + CHILD_B)

    # Readiness predicate one takes its positive path but returns true: bit 0
    # is clear and the two finite floats it compares are equal.
    for child, nested in ((CHILD_A, NESTED_A), (CHILD_B, NESTED_B)):
        put32(data, child, 0)
        put32(data, child + 0x34, 1)
        put32(data, child + 0x58, 0)  # readiness two and fade B early-return.
        put32(data, child + 0x2C, DATA + nested)
        put32(data, child + 0x4C, DATA + nested)
        putf32(data, nested + 0x38, 1.0)
        putf32(data, nested + 0x48, 1.0)

    # The positive 0x002872A4 body calls this exact, bounded synthetic callee.
    put32(data, NESTED_B + 0x4C, CALLBACK_STUB)
    put32(data, NESTED_B + 0x50, CALLBACK_OBJECT)
    putf32(data, NESTED_B + 0x44, 0.5)
    putf32(data, NESTED_B + 0x48, 1.0)
    return bytes(data)


def run_positive_gate(image: bytes, raw_tbb: bytes) -> dict:
    if hashlib.sha256(image).hexdigest() != CODE_SHA256:
        raise ValueError("code.bin is not the pinned US reference image")
    verify_reference(image)
    if len(raw_tbb) > 0x1000:
        raise ValueError("TitleTable.tbb does not fit the explicit extra data page")
    runner = Runner(image, START)
    uc = runner.uc
    uc.mem_map(DATA + 0x1000, 0x1000,
               unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    table_pointer_address = TITLE_TBB_SLOT_BASE + TITLE_TBB_SLOT_ID * 0x10 + 4
    uc.mem_protect(table_pointer_address & ~0xFFF, 0x1000,
                   unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    uc.mem_write(table_pointer_address, struct.pack("<I", DATA + TBB_CONTAINER_OFFSET))
    uc.mem_write(DATA + TBB_CONTAINER_OFFSET, raw_tbb)
    uc.mem_write(CALLBACK_STUB, struct.pack("<I", CALLBACK_WORD))

    trace: list[int] = []
    reads: list[dict] = []
    writes: list[dict] = []
    calls: list[dict] = []
    callback = {"count": 0, "input": None, "output": None, "memory_writes": []}
    stopped = {"at_help": False, "presentation_args": None}

    def code_hook(machine, address, _size, _user):
        trace.append(address)
        if address in (READY_VISIBLE, READY_SECOND, FADE_A, FADE_B,
                       TBB_GLOBAL, TBB_SUBTABLE, TBB_PAYLOAD):
            calls.append({"target": hex(address),
                          "r0": hex(machine.reg_read(arm.UC_ARM_REG_R0)),
                          "lr": hex(machine.reg_read(arm.UC_ARM_REG_LR))})
        if address == CALLBACK_STUB:
            callback["count"] += 1
            callback["input"] = {
                "r0_object": hex(machine.reg_read(arm.UC_ARM_REG_R0)),
                "r1_callback": hex(machine.reg_read(arm.UC_ARM_REG_R1)),
                "lr": hex(machine.reg_read(arm.UC_ARM_REG_LR)),
                "s0_bits": hex(machine.reg_read(arm.UC_ARM_REG_S0)),
                "s2_bits": hex(machine.reg_read(arm.UC_ARM_REG_S2)),
            }
        if address == FADE_A_CONTINUATION:
            callback["output"] = {
                "r0": hex(machine.reg_read(arm.UC_ARM_REG_R0)),
                "s0_bits": hex(machine.reg_read(arm.UC_ARM_REG_S0)),
            }
        if address == STOP:
            stopped["at_help"] = True
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
            if CALLBACK_STUB <= pc < CALLBACK_STUB + 4:
                callback["memory_writes"].append(row)

    uc.hook_add(unicorn.UC_HOOK_CODE, code_hook)
    uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE, memory_hook)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    registers = [0xA5A50000 | i for i in range(13)]
    registers[4] = DATA + WORK
    registers[5] = DATA + WORK
    registers[7] = 1
    for i, value in enumerate(registers):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), value)
    for i in range(8, 16):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_D{i}"), 0)
    uc.reg_write(arm.UC_ARM_REG_S16, struct.unpack("<I", struct.pack("<f", 0.75))[0])
    uc.reg_write(arm.UC_ARM_REG_S17, struct.unpack("<I", struct.pack("<f", 0.25))[0])
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, STOP)
    uc.mem_write(DATA, initial_memory())
    uc.mem_write(STACK, bytes([0xCD]) * STACK_SIZE)
    try:
        uc.emu_start(START, 0, count=4096)
    except unicorn.UcError as exc:
        raise RuntimeError(f"ARM fault at {uc.reg_read(arm.UC_ARM_REG_PC):#x}: {exc}") from exc
    if not stopped["at_help"] or uc.reg_read(arm.UC_ARM_REG_PC) != STOP:
        raise RuntimeError(f"did not reach presentation boundary; PC={uc.reg_read(arm.UC_ARM_REG_PC):#x}")

    final = bytes(uc.mem_read(DATA, DATA_SIZE))
    u32 = lambda off: struct.unpack_from("<I", final, off)[0]
    u8 = lambda off: final[off]
    f32 = lambda off: struct.unpack_from("<f", final, off)[0]
    allowed_ranges = (
        (DATA + WORK, DATA + WORK + 0xA0),
        (DATA + HANDLE_A, DATA + HANDLE_A + 0x0C),
        (DATA + HANDLE_B, DATA + HANDLE_B + 0x0C),
        (DATA + CHILD_A, DATA + CHILD_A + 0x60),
        (DATA + CHILD_B, DATA + CHILD_B + 0x60),
        (DATA + NESTED_A, DATA + NESTED_A + 0x1F7),
        (DATA + NESTED_B, DATA + NESTED_B + 0x1F7),
        (DATA + TBB_CONTAINER_OFFSET, DATA + TBB_CONTAINER_OFFSET + len(raw_tbb)),
        (TITLE_TBB_SLOT_BASE + TITLE_TBB_SLOT_ID * 0x10,
         TITLE_TBB_SLOT_BASE + (TITLE_TBB_SLOT_ID + 1) * 0x10),
        (0x00493BD0, 0x00493BD4),  # Original TBB manager slot.
        (SP - 8, SP),
    )
    literal_reads = {0x001E9EC4, 0x002C0EDC, 0x002AC348, 0x002AC34C, 0x002C0EC0}
    unexpected_reads = [row for row in reads
                        if int(row["address"], 16) not in literal_reads
                        and not any(start <= int(row["address"], 16) < end
                                    for start, end in allowed_ranges)]
    if unexpected_reads:
        raise AssertionError(f"read outside explicit graph, stack, TBB, or literal pools: {unexpected_reads}")
    expected_calls = [READY_VISIBLE, READY_SECOND, FADE_A, FADE_B,
                      TBB_GLOBAL, TBB_SUBTABLE, TBB_PAYLOAD]
    if [int(row["target"], 16) for row in calls] != expected_calls:
        raise AssertionError(f"unexpected direct helper order: {calls}")
    if callback["count"] != 1 or FADE_A_BODY not in trace:
        raise AssertionError("positive first fade gate did not execute exactly one synthetic callback")
    if callback["memory_writes"]:
        raise AssertionError(f"synthetic callback unexpectedly wrote memory: {callback['memory_writes']}")
    expected_input = {"r0_object": hex(CALLBACK_OBJECT),
                      "r1_callback": hex(CALLBACK_STUB),
                      "lr": hex(FADE_A_CONTINUATION),
                      "s0_bits": hex(struct.unpack("<I", struct.pack("<f", 0.5))[0]),
                      "s2_bits": hex(struct.unpack("<I", struct.pack("<f", 0.75))[0])}
    if callback["input"] != expected_input:
        raise AssertionError(f"callback ABI mismatch: {callback['input']} != {expected_input}")
    if callback["output"] != {"r0": hex(CALLBACK_OBJECT), "s0_bits": expected_input["s0_bits"]}:
        raise AssertionError(f"callback stub output mismatch: {callback['output']}")

    expected_writes = {
        SP - 8: 0x02000100,  # Original helper's saved r4.
        SP - 4: 0x001EA0D0,  # Original helper's outer-call return address.
        DATA + HANDLE_A: 6,
        DATA + NESTED_A + 0x1F6: 0,
        DATA + WORK + 0x98: None,
        DATA + NESTED_B + 0x38: None,
        DATA + NESTED_B + 0x3C: None,
        DATA + NESTED_B + 0x58: 1,
        DATA + HANDLE_B: 0,
        DATA + NESTED_B + 0x1F6: 1,
        DATA + WORK + 0x94: 1,
    }
    actual_write_addresses = {int(row["address"], 16) for row in writes}
    if actual_write_addresses != set(expected_writes):
        raise AssertionError(f"write footprint mismatch: {writes}")
    for address, value in expected_writes.items():
        if value is not None:
            row = next(row for row in writes if int(row["address"], 16) == address)
            if int(row["value"], 16) != value:
                raise AssertionError(f"unexpected value at {address:#x}: {row}")
    if (u32(HANDLE_A) != 6 or u32(HANDLE_B) != 0 or u8(WORK + 0x94) != 1
            or f32(WORK + 0x98) != 0.75 or f32(NESTED_B + 0x38) != 0.5
            or f32(NESTED_B + 0x3C) != 1.0 or u8(NESTED_B + 0x58) != 1):
        raise AssertionError("final original ARM transition stores differ from expected state")

    table = extract_help_entries(raw_tbb)
    entry = table["entries"][0]
    expected_pointer = (DATA + TBB_CONTAINER_OFFSET + table["payload_file_offset"]
                        + entry["relative_payload_offset"])
    args = stopped["presentation_args"]
    if int(args["r0"], 16) != expected_pointer or int(args["r1"], 16) != 0x323232FF:
        raise AssertionError(f"unexpected help arguments: {args}")
    if entry["text"] != EXPECTED_HELP[0] or PRESENTATION_CALLEE in trace:
        raise AssertionError("help text mismatch or presentation callee entered")

    return {
        "passed": True,
        "evidence_type": "continuous pinned original ARM execution with a one-instruction explicit synthetic BLX callback",
        "code_sha256": CODE_SHA256,
        "tbb_sha256": hashlib.sha256(raw_tbb).hexdigest(),
        "start": hex(START), "positive_gate_entry": hex(FADE_A),
        "positive_gate_body": hex(FADE_A_BODY), "callback_call_pc": hex(FADE_A_CALLBACK),
        "callback_stub": hex(CALLBACK_STUB), "callback_word": hex(CALLBACK_WORD),
        "help_entry": hex(HELP), "stop_before_presentation": hex(STOP),
        "presentation_callee_not_entered": hex(PRESENTATION_CALLEE),
        "reached": {"mutator": MUTATOR in trace,
                    "first_fade_positive_body": FADE_A_BODY in trace,
                    "second_fade_early_return": FADE_B in trace and 0x0020FFAC not in trace,
                    "help_boundary": HELP in trace},
        "direct_calls": calls,
        "callback": callback,
        "help_args": args, "help_text": entry["text"],
        "read_count": len(reads), "reads": reads,
        "read_accesses_outside_explicit_model": unexpected_reads,
        "write_count": len(writes), "writes": writes,
        "final_state": {"handle_a_flags": u32(HANDLE_A),
                        "handle_b_flags": u32(HANDLE_B),
                        "work_0x94": u8(WORK + 0x94),
                        "work_0x98": f32(WORK + 0x98),
                        "callback_nested_0x38": f32(NESTED_B + 0x38),
                        "callback_nested_0x3c": f32(NESTED_B + 0x3C),
                        "callback_nested_0x58": u8(NESTED_B + 0x58)},
        "limits": [
            "Synthetic work/handle/child graph and explicit finite VFP inputs; no Azahar snapshot or runtime-normality claim.",
            "Executes original ARM readiness, mutator, first positive fade body, second fade early-return, and real TBB help lookup continuously.",
            "The dynamic callback is intentionally synthetic: bx lr only, with no memory effects; its address and ABI observations are recorded.",
            "Stops before Camp_SetSlotMessage; does not establish rendered UI, gameplay, or behavior in Azahar.",
            "Only the first fade helper positive-gate body is covered; 0x0020FFAC positive body remains untested.",
            "The original fade helper's two stack-save writes are included in the 11-write trace; callback-stub write count is zero.",
        ],
    }


def main() -> int:
    parser = __import__("argparse").ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path,
                        default=ROOT / "build/semantic-equivalence/real-assets/exefs/code.bin")
    parser.add_argument("--tbb", type=Path,
                        default=ROOT / "build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/title-transition-positive-gate/report.json")
    args = parser.parse_args()
    report = run_positive_gate(args.code.read_bytes(), args.tbb.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Title positive-gate path PASS; report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
