#!/usr/bin/env python3
"""Extend the H1 synthetic positive path through 0x0020FFAC and its table lookup."""
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
    CALLBACK_STUB as FIRST_CALLBACK, CALLBACK_WORD, CHILD_B,
    HANDLE_A, HANDLE_B, NESTED_A, NESTED_B, START, STOP, TBB_CONTAINER_OFFSET,
    WORK, initial_memory,
)

SECOND_BODY = 0x0020FFAC
SECOND_ENTRY = 0x0020FFA0
SECOND_CALLBACK_CALL = 0x00210010
SECOND_CALLBACK_CONTINUATION = 0x00210014
FADE_A = 0x002872A4
FADE_A_BODY = 0x002872B0
FADE_B = SECOND_ENTRY
FADE_B_BODY = SECOND_BODY
HELP = 0x001EA12C
PRESENTATION_CALLEE = 0x0029F10C
TBB_GLOBAL = 0x002C0EC4
TBB_SUBTABLE = 0x002AC2F4
TBB_PAYLOAD = 0x002C0E9C
CODE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"

TABLE_META = 0xC20
TABLE_BASE = 0xC60
TABLE_RECORD = 0xD00
SECOND_CALLBACK_ARG = DATA + 0xE00
SECOND_CALLBACK_STUB = 0x01000120


def put32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", data, offset, value & 0xFFFFFFFF)


def putf32(data: bytearray, offset: int, value: float) -> None:
    struct.pack_into("<f", data, offset, value)


def extend_memory() -> bytes:
    data = bytearray(initial_memory())
    # Positive gate for 0x0020FFA0. The preceding 0x002872A4 positive route
    # remains intact because this is the same child B/nested B graph.
    put32(data, CHILD_B + 0x58, 1)
    put32(data, NESTED_B + 0x148, 1)
    put32(data, NESTED_B + 0x28, DATA + TABLE_META)
    put32(data, NESTED_B + 0x14C, 1)
    put32(data, TABLE_META + 0x28, 1)  # stride, in 32-bit table entries
    put32(data, TABLE_META + 0x1C, DATA + TABLE_BASE)
    put32(data, TABLE_BASE, 0)  # index 0 is intentionally null and unused
    put32(data, TABLE_BASE + 4, DATA + TABLE_RECORD)

    # Record selected by base + (index * stride * 4). Its +0x4c callback is
    # isolated from the earlier helper's callback at descriptor+0x4c.
    putf32(data, TABLE_RECORD + 0x38, 0.9)
    putf32(data, TABLE_RECORD + 0x44, 0.25)
    putf32(data, TABLE_RECORD + 0x48, 0.6)
    put32(data, TABLE_RECORD + 0x4C, SECOND_CALLBACK_STUB)
    put32(data, TABLE_RECORD + 0x50, SECOND_CALLBACK_ARG)
    return bytes(data)


def run_second_positive_gate(image: bytes, raw_tbb: bytes) -> dict:
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
    uc.mem_write(FIRST_CALLBACK, struct.pack("<I", CALLBACK_WORD))
    uc.mem_write(SECOND_CALLBACK_STUB, struct.pack("<I", CALLBACK_WORD))

    trace: list[int] = []
    reads: list[dict] = []
    writes: list[dict] = []
    direct_calls: list[dict] = []
    callback_events: dict[str, dict] = {}
    stopped = {"at_help": False, "presentation_args": None}
    callback_specs = {
        FIRST_CALLBACK: ("first_fade", 0x002872E8),
        SECOND_CALLBACK_STUB: ("second_fade", SECOND_CALLBACK_CONTINUATION),
    }

    def code_hook(machine, address, _size, _user):
        trace.append(address)
        if address in (FADE_A, FADE_B, TBB_GLOBAL, TBB_SUBTABLE, TBB_PAYLOAD):
            direct_calls.append({"target": hex(address),
                                 "r0": hex(machine.reg_read(arm.UC_ARM_REG_R0)),
                                 "r1": hex(machine.reg_read(arm.UC_ARM_REG_R1)),
                                 "lr": hex(machine.reg_read(arm.UC_ARM_REG_LR))})
        if address in callback_specs:
            name, _continuation = callback_specs[address]
            callback_events[name] = {
                "count": callback_events.get(name, {}).get("count", 0) + 1,
                "entry": {
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
                },
            }
        if address in (0x002872E8, SECOND_CALLBACK_CONTINUATION):
            name = "first_fade" if address == 0x002872E8 else "second_fade"
            if name in callback_events:
                callback_events[name]["return"] = {
                    "r0": hex(machine.reg_read(arm.UC_ARM_REG_R0)),
                    "r1": hex(machine.reg_read(arm.UC_ARM_REG_R1)),
                    "r2": hex(machine.reg_read(arm.UC_ARM_REG_R2)),
                    "r3": hex(machine.reg_read(arm.UC_ARM_REG_R3)),
                    "s0_bits": hex(machine.reg_read(arm.UC_ARM_REG_S0)),
                    "s1_bits": hex(machine.reg_read(arm.UC_ARM_REG_S1)),
                    "s2_bits": hex(machine.reg_read(arm.UC_ARM_REG_S2)),
                    "s3_bits": hex(machine.reg_read(arm.UC_ARM_REG_S3)),
                    "fpscr": hex(machine.reg_read(arm.UC_ARM_REG_FPSCR)),
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
            writes.append({"pc": hex(pc), "address": hex(address), "size": size,
                           "value": hex(value & ((1 << (size * 8)) - 1))})

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
    uc.reg_write(arm.UC_ARM_REG_LR, STOP)
    uc.mem_write(DATA, extend_memory())
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
    literal_reads = {0x001E9EC4, 0x002C0EDC, 0x002AC348, 0x002AC34C, 0x002C0EC0}
    allowed_ranges = (
        (DATA + WORK, DATA + WORK + 0xA0),
        (DATA + HANDLE_A, DATA + HANDLE_A + 0x0C),
        (DATA + HANDLE_B, DATA + HANDLE_B + 0x0C),
        (DATA + 0x400, DATA + 0x460),
        (DATA + CHILD_B, DATA + CHILD_B + 0x60),
        (DATA + NESTED_A, DATA + NESTED_A + 0x1F7),
        (DATA + NESTED_B, DATA + NESTED_B + 0x1F7),
        (DATA + TABLE_META, DATA + TABLE_META + 0x2C),
        (DATA + TABLE_BASE, DATA + TABLE_BASE + 8),
        (DATA + TABLE_RECORD, DATA + TABLE_RECORD + 0x5C),
        (DATA + TBB_CONTAINER_OFFSET, DATA + TBB_CONTAINER_OFFSET + len(raw_tbb)),
        (TITLE_TBB_SLOT_BASE + TITLE_TBB_SLOT_ID * 0x10,
         TITLE_TBB_SLOT_BASE + (TITLE_TBB_SLOT_ID + 1) * 0x10),
        (0x00493BD0, 0x00493BD4),
        (SP - 8, SP),
    )
    unexpected_reads = [row for row in reads
                        if int(row["address"], 16) not in literal_reads
                        and not any(start <= int(row["address"], 16) < end
                                    for start, end in allowed_ranges)]
    if unexpected_reads:
        raise AssertionError(f"read outside the explicit graph/stack/TBB/literals: {unexpected_reads}")

    expected_direct = [FADE_A, FADE_B, TBB_GLOBAL, TBB_SUBTABLE, TBB_PAYLOAD]
    if [int(row["target"], 16) for row in direct_calls] != expected_direct:
        raise AssertionError(f"direct call order mismatch: {direct_calls}")
    if FADE_A_BODY not in trace or FADE_B_BODY not in trace or SECOND_CALLBACK_CALL not in trace:
        raise AssertionError("did not execute both original positive fade bodies and second BLX")
    if callback_events.get("first_fade", {}).get("count") != 1:
        raise AssertionError(f"first callback count differs: {callback_events}")
    if callback_events.get("second_fade", {}).get("count") != 1:
        hits = [i for i, pc in enumerate(trace) if pc in (SECOND_CALLBACK_CALL, SECOND_CALLBACK_STUB)]
        contexts = [[hex(pc) for pc in trace[max(0, i - 4):i + 5]] for i in hits]
        raise AssertionError(f"second callback count differs: {callback_events}; contexts={contexts}")
    # First helper's original state/ABI is shared with the passing prerequisite.
    expected_first = {"r0": "0x2000c00", "r1": hex(FIRST_CALLBACK),
                      "lr": "0x2872e8", "s0_bits": "0x3f000000",
                      "s2_bits": "0x3f400000"}
    first = callback_events["first_fade"]["entry"]
    if any(first[key] != value for key, value in expected_first.items()):
        raise AssertionError(f"first positive gate prerequisite changed: {first}")
    expected_second = {"r0": hex(SECOND_CALLBACK_ARG), "r1": hex(SECOND_CALLBACK_STUB),
                       "lr": hex(SECOND_CALLBACK_CONTINUATION),
                       "s0_bits": "0x3e800000", "s1_bits": "0x3f19999a",
                       "s2_bits": "0x3f19999a"}
    second = callback_events["second_fade"]["entry"]
    if any(second[key] != value for key, value in expected_second.items()):
        raise AssertionError(f"second positive callback ABI mismatch: {second}")
    if callback_events["second_fade"]["return"]["s0_bits"] != "0x3e800000":
        raise AssertionError(f"synthetic second callback did not preserve s0: {callback_events['second_fade']}")

    expected_data_writes = {
        DATA + HANDLE_A: 6,
        DATA + NESTED_A + 0x1F6: 0,
        DATA + WORK + 0x98: 0x3F400000,
        DATA + NESTED_B + 0x38: 0x3F000000,
        DATA + NESTED_B + 0x3C: 0x3F800000,
        DATA + NESTED_B + 0x58: 1,
        DATA + HANDLE_B: 0,
        DATA + NESTED_B + 0x1F6: 1,
        DATA + TABLE_RECORD + 0x38: 0x3E800000,
        DATA + TABLE_RECORD + 0x3C: 0x3F666666,
        DATA + TABLE_RECORD + 0x58: 1,
        DATA + WORK + 0x94: 1,
    }
    actual = {int(row["address"], 16) for row in writes}
    expected_addresses = set(expected_data_writes) | {SP - 8, SP - 4}
    if actual != expected_addresses:
        raise AssertionError(f"write footprint mismatch: {writes}")
    for address, expected in expected_data_writes.items():
        item = next(row for row in reversed(writes)
                    if int(row["address"], 16) == address)
        if int(item["value"], 16) != expected:
            raise AssertionError(f"write value mismatch at {address:#x}: {item}")
    stack_writes = {address: [int(row["value"], 16) for row in writes
                              if int(row["address"], 16) == address]
                    for address in (SP - 8, SP - 4)}
    if stack_writes != {SP - 8: [0x02000100, 0x02000100],
                        SP - 4: [0x001EA0D0, 0x001EA0E0]}:
        raise AssertionError(f"unexpected original helper stack saves: {stack_writes}")
    if any(row["pc"] in (hex(FIRST_CALLBACK), hex(SECOND_CALLBACK_STUB)) for row in writes):
        raise AssertionError("a synthetic callback unexpectedly wrote memory")

    if (u32(HANDLE_A) != 6 or u32(HANDLE_B) != 0 or u8(WORK + 0x94) != 1
            or f32(TABLE_RECORD + 0x38) != 0.25
            or u32(TABLE_RECORD + 0x3C) != 0x3F666666
            or u8(TABLE_RECORD + 0x58) != 1):
        raise AssertionError(f"final indexed-record/transition values mismatch: "
                             f"{f32(TABLE_RECORD + 0x38)=}, {f32(TABLE_RECORD + 0x3C)=}, "
                             f"{u8(TABLE_RECORD + 0x58)=}, {u8(WORK + 0x94)=}")
    table = extract_help_entries(raw_tbb)
    entry = table["entries"][0]
    expected_pointer = (DATA + TBB_CONTAINER_OFFSET + table["payload_file_offset"]
                        + entry["relative_payload_offset"])
    args = stopped["presentation_args"]
    if int(args["r0"], 16) != expected_pointer or int(args["r1"], 16) != 0x323232FF:
        raise AssertionError(f"help caller args differ: {args}")
    if entry["text"] != EXPECTED_HELP[0] or PRESENTATION_CALLEE in trace:
        raise AssertionError("help text mismatch or renderer callee entered")

    return {
        "passed": True,
        "evidence_type": "continuous pinned original ARM execution with two explicit one-instruction synthetic BLX stubs",
        "code_sha256": CODE_SHA256,
        "tbb_sha256": hashlib.sha256(raw_tbb).hexdigest(),
        "start": hex(START), "first_positive_body": hex(FADE_A_BODY),
        "second_positive_entry": hex(SECOND_ENTRY), "second_positive_body": hex(SECOND_BODY),
        "second_blx_pc": hex(SECOND_CALLBACK_CALL),
        "stop_before_presentation": hex(STOP),
        "help_entry": hex(HELP), "help_text": entry["text"],
        "direct_calls": direct_calls,
        "callbacks": callback_events,
        "callback_stub_contract": {
            "instruction_word": hex(CALLBACK_WORD),
            "instruction": "bx lr",
            "stub_addresses": {"first_fade": hex(FIRST_CALLBACK),
                               "second_fade": hex(SECOND_CALLBACK_STUB)},
            "memory_writes": [],
            "register_and_fp_effect": "preserve all recorded general registers and s0-s2",
        },
        "indexed_table": {
            "descriptor": hex(DATA + NESTED_B),
            "descriptor_0x148": u32(NESTED_B + 0x148),
            "metadata": hex(DATA + TABLE_META),
            "stride": u32(TABLE_META + 0x28),
            "base": hex(u32(TABLE_META + 0x1C)),
            "index": u32(NESTED_B + 0x14C),
            "selected_slot_address": hex(DATA + TABLE_BASE + 4),
            "selected_record": hex(u32(TABLE_BASE + 4)),
        },
        "indexed_table_reads": [row for row in reads
                                if int(row["pc"], 16) in {
                                    0x0020FFB0, 0x0020FFB8, 0x0020FFC4,
                                    0x0020FFC8, 0x0020FFCC, 0x0020FFD0,
                                    0x0020FFD8}],
        "help_args": args, "read_count": len(reads), "reads": reads,
        "unexpected_reads": unexpected_reads,
        "write_count": len(writes), "writes": writes,
        "distinct_write_addresses": [hex(value) for value in sorted(actual)],
        "final_state": {"selected_record_0x38": f32(TABLE_RECORD + 0x38),
                        "selected_record_0x3c": f32(TABLE_RECORD + 0x3C),
                        "selected_record_0x58": u8(TABLE_RECORD + 0x58),
                        "childB_transition_byte": u8(NESTED_B + 0x1F6),
                        "work_0x94": u8(WORK + 0x94)},
        "limits": [
            "All work, handles, objects, index, table, record, FP values, and callback targets are explicit synthetic state, not a runtime snapshot.",
            "Both transition helper bodies are original ARM; each BLX target is a one-instruction bx lr stub with zero memory effects.",
            "The real TitleTable.tbb lookup is original ARM; execution stops before Camp_SetSlotMessage, so no renderer/UI behavior is claimed.",
            "No claim that the second helper's callback target/behavior matches the game; the original target is supplied by the synthetic record.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path,
                        default=ROOT / "build/semantic-equivalence/real-assets/exefs/code.bin")
    parser.add_argument("--tbb", type=Path,
                        default=ROOT / "build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/title-transition-second-positive-gate/report.json")
    args = parser.parse_args()
    report = run_second_positive_gate(args.code.read_bytes(), args.tbb.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Title second positive-gate path PASS; report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
