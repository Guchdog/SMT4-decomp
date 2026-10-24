#!/usr/bin/env python3
"""Test original callback candidates separately at the synthetic H1 second gate."""
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

SECOND_BODY = 0x0020FFAC
SECOND_CALL = 0x00210010
SECOND_RETURN = 0x00210014
FIRST_BODY = 0x002872B0
FIRST_CALLBACK = 0x01000100
FIRST_STUB_WORD = 0xE12FFF1E
CALLBACK_CLAMP = 0x0015555C
CALLBACK_TYPE1 = 0x00151404
CALLBACK_ENDS = {CALLBACK_CLAMP: 0x00155584, CALLBACK_TYPE1: 0x00151468}
CALLBACK_OBJECT = DATA + 0xC00
CODE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
TABLE_META, TABLE_BASE, TABLE_RECORD = 0xC20, 0xC60, 0xD00
TBB_GLOBAL, TBB_SUBTABLE, TBB_PAYLOAD = 0x002C0EC4, 0x002AC2F4, 0x002C0E9C
PRESENTATION_CALLEE = 0x0029F10C


def put32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", data, offset, value & 0xFFFFFFFF)


def putf32(data: bytearray, offset: int, value: float) -> None:
    struct.pack_into("<f", data, offset, value)


def make_memory(candidate: int) -> bytes:
    data = bytearray(initial_memory())
    put32(data, CHILD_B + 0x58, 1)
    put32(data, NESTED_B + 0x148, 1)
    put32(data, NESTED_B + 0x28, DATA + TABLE_META)
    put32(data, NESTED_B + 0x14C, 1)
    put32(data, TABLE_META + 0x28, 1)
    put32(data, TABLE_META + 0x1C, DATA + TABLE_BASE)
    put32(data, TABLE_BASE, 0)
    put32(data, TABLE_BASE + 4, DATA + TABLE_RECORD)
    putf32(data, TABLE_RECORD + 0x38, 0.9)
    putf32(data, TABLE_RECORD + 0x44, 0.25)
    putf32(data, TABLE_RECORD + 0x48, 0.6)
    put32(data, TABLE_RECORD + 0x4C, candidate)
    # Use the explicitly initialized argument object from the first-gate harness.
    put32(data, TABLE_RECORD + 0x50, CALLBACK_OBJECT)
    return bytes(data)


def run_candidate(image: bytes, raw_tbb: bytes, candidate: int) -> dict:
    if candidate not in CALLBACK_ENDS:
        raise ValueError(f"unsupported original callback candidate: {candidate:#x}")
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
    uc.mem_write(FIRST_CALLBACK, struct.pack("<I", FIRST_STUB_WORD))

    trace: list[int] = []
    reads: list[dict] = []
    writes: list[dict] = []
    calls: list[dict] = []
    callback = {"count": 0, "entry": None, "return": None, "writes": []}
    stopped = {"boundary": False, "args": None}

    def capture(machine) -> dict:
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
            "fpscr": hex(machine.reg_read(arm.UC_ARM_REG_FPSCR)),
        }

    def code_hook(machine, address, _size, _user):
        trace.append(address)
        if address in (FIRST_BODY, SECOND_BODY, TBB_GLOBAL, TBB_SUBTABLE, TBB_PAYLOAD):
            calls.append({"target": hex(address), "r0": hex(machine.reg_read(arm.UC_ARM_REG_R0)),
                          "lr": hex(machine.reg_read(arm.UC_ARM_REG_LR))})
        if address == candidate:
            callback["count"] += 1
            callback["entry"] = capture(machine)
        if address == CALLBACK_ENDS[candidate] - 4:
            callback["at_return"] = capture(machine)
        if address == SECOND_RETURN:
            callback["return"] = capture(machine)
        if address == STOP:
            stopped["boundary"] = True
            stopped["args"] = {"r0": hex(machine.reg_read(arm.UC_ARM_REG_R0)),
                                "r1": hex(machine.reg_read(arm.UC_ARM_REG_R1)),
                                "lr": hex(machine.reg_read(arm.UC_ARM_REG_LR))}
            machine.emu_stop()

    def memory_hook(machine, access, address, size, value, _user):
        pc = machine.reg_read(arm.UC_ARM_REG_PC)
        if access == unicorn.UC_MEM_READ:
            reads.append({"pc": hex(pc), "address": hex(address), "size": size})
        elif access == unicorn.UC_MEM_WRITE:
            row = {"pc": hex(pc), "address": hex(address), "size": size,
                   "value": hex(value & ((1 << (size * 8)) - 1))}
            writes.append(row)
            if candidate <= pc < CALLBACK_ENDS[candidate]:
                callback["writes"].append(row)

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
    uc.mem_write(DATA, make_memory(candidate))
    uc.mem_write(STACK, bytes([0xCD]) * STACK_SIZE)
    try:
        uc.emu_start(START, 0, count=8192)
    except unicorn.UcError as exc:
        raise RuntimeError(f"ARM fault at {uc.reg_read(arm.UC_ARM_REG_PC):#x}: {exc}") from exc
    if not stopped["boundary"] or uc.reg_read(arm.UC_ARM_REG_PC) != STOP:
        raise RuntimeError(f"did not reach presentation boundary; PC={uc.reg_read(arm.UC_ARM_REG_PC):#x}")

    final = bytes(uc.mem_read(DATA, DATA_SIZE))
    u8 = lambda off: final[off]
    f32 = lambda off: struct.unpack_from("<f", final, off)[0]
    literal_reads = {0x001E9EC4, 0x002C0EDC, 0x002AC348, 0x002AC34C, 0x002C0EC0,
                     0x00151468, 0x0015146C, 0x0014D6DC, 0x0014D6E0,
                     0x0014D6EC, 0x0014D704, 0x002A33F0, 0x002A33F4}
    allowed_ranges = (
        (DATA + WORK, DATA + WORK + 0xA0),
        (DATA + HANDLE_A, DATA + HANDLE_A + 0x0C),
        (DATA + HANDLE_B, DATA + HANDLE_B + 0x0C),
        (DATA + 0x400, DATA + 0x460),
        (DATA + CHILD_B, DATA + CHILD_B + 0x60),
        (DATA + NESTED_A, DATA + NESTED_A + 0x1F7),
        (DATA + NESTED_B, DATA + NESTED_B + 0x1F7),
        (DATA + 0xC00, DATA + 0xC20),
        (DATA + TABLE_META, DATA + TABLE_META + 0x2C),
        (DATA + TABLE_BASE, DATA + TABLE_BASE + 8),
        (DATA + TABLE_RECORD, DATA + TABLE_RECORD + 0x5C),
        (DATA + TBB_CONTAINER_OFFSET, DATA + TBB_CONTAINER_OFFSET + len(raw_tbb)),
        (TITLE_TBB_SLOT_BASE + TITLE_TBB_SLOT_ID * 0x10,
         TITLE_TBB_SLOT_BASE + (TITLE_TBB_SLOT_ID + 1) * 0x10),
        (0x00493BD0, 0x00493BD4),
        (SP - 0x40, SP),
    )
    unexpected_reads = [r for r in reads if int(r["address"], 16) not in literal_reads
                        and not any(a <= int(r["address"], 16) < b for a, b in allowed_ranges)]
    if unexpected_reads:
        raise AssertionError(f"read outside explicit model/TBB/stack/literals: {unexpected_reads}")
    if callback["count"] != 1 or callback["entry"] is None or callback["return"] is None:
        raise AssertionError(f"candidate callback did not execute/return exactly once: {callback}")
    if callback["entry"]["r1"] != hex(candidate) or callback["entry"]["lr"] != hex(SECOND_RETURN):
        raise AssertionError(f"second-gate callback ABI mismatch: {callback}")
    if SECOND_CALL not in trace or SECOND_BODY not in trace or PRESENTATION_CALLEE in trace:
        raise AssertionError("missing original second gate or presentation boundary was crossed")
    expected_calls = [FIRST_BODY, SECOND_BODY, TBB_GLOBAL, TBB_SUBTABLE, TBB_PAYLOAD]
    if [int(c["target"], 16) for c in calls] != expected_calls:
        raise AssertionError(f"direct-call sequence mismatch: {calls}")
    if any(int(r["address"], 16) not in (SP - 8, SP - 4, SP - 0x10, SP - 0x0C,
                                          SP - 0x20, SP - 0x18, SP - 0x28, SP - 0x24,
                                          SP - 0x40, SP - 0x38, SP - 0x30,
                                          DATA + TABLE_RECORD + 0x38,
                                          DATA + TABLE_RECORD + 0x3C,
                                          DATA + TABLE_RECORD + 0x58,
                                          DATA + HANDLE_A, DATA + NESTED_A + 0x1F6,
                                          DATA + WORK + 0x98, DATA + NESTED_B + 0x38,
                                          DATA + NESTED_B + 0x3C, DATA + NESTED_B + 0x58,
                                          DATA + HANDLE_B, DATA + NESTED_B + 0x1F6,
                                          DATA + WORK + 0x94)
           for r in writes):
        raise AssertionError(f"write outside exact modeled transition/stack addresses: {writes}")
    if any(int(r["address"], 16) not in range(SP - 0x40, SP)
           for r in callback["writes"]):
        raise AssertionError(f"candidate wrote outside its modeled stack frame: {callback['writes']}")
    if candidate == CALLBACK_CLAMP and callback["writes"]:
        raise AssertionError(f"clamp callback unexpectedly wrote: {callback['writes']}")

    table = extract_help_entries(raw_tbb)
    entry = table["entries"][0]
    expected_ptr = DATA + TBB_CONTAINER_OFFSET + table["payload_file_offset"] + entry["relative_payload_offset"]
    if int(stopped["args"]["r0"], 16) != expected_ptr or int(stopped["args"]["r1"], 16) != 0x323232FF:
        raise AssertionError(f"help caller args mismatch: {stopped['args']}")
    if entry["text"] != EXPECTED_HELP[0]:
        raise AssertionError(f"unexpected real TBB entry: {entry['text']!r}")
    candidate_callees = [pc for pc in (0x0014D608, 0x0015258C, 0x002A337C, 0x002A464E)
                         if pc in trace]

    return {
        "passed": True,
        "evidence_type": "candidate-synthetic: pinned original ARM executes the original callback candidate through the synthetic second-gate record",
        "callback_candidate": hex(candidate),
        "callback_selection": "explicit synthetic record pointer; live title selection unknown",
        "code_sha256": CODE_SHA256,
        "tbb_sha256": hashlib.sha256(raw_tbb).hexdigest(),
        "callback": callback,
        "callback_instruction_pcs": [hex(pc) for pc in trace
                                      if candidate <= pc < CALLBACK_ENDS[candidate]],
        "callback_callees_reached": [hex(pc) for pc in candidate_callees],
        "reached_original_calls": calls,
        "second_gate_call_pc": hex(SECOND_CALL),
        "stop_before_presentation": hex(STOP),
        "help_text": entry["text"],
        "read_count": len(reads), "reads": reads,
        "unexpected_reads": unexpected_reads,
        "write_count": len(writes), "writes": writes,
        "callback_writes": callback["writes"],
        "final_state": {"selected_record_0x38": f32(TABLE_RECORD + 0x38),
                        "selected_record_0x3c": f32(TABLE_RECORD + 0x3C),
                        "selected_record_0x58": u8(TABLE_RECORD + 0x58),
                        "work_0x94": u8(WORK + 0x94)},
        "limits": [
            "The record, callback argument, transition graph, and FP inputs are synthetic; neither candidate is claimed to be the live second-gate callback.",
            "Candidate callback bytes are not patched or stubbed; execution uses original instructions from the pinned US code.bin.",
            "All reads are checked against explicit object/table/TBB/stack/literal regions; all writes are checked against explicit stack and transition-state addresses.",
            "Execution stops before Camp_SetSlotMessage; no renderer, visible UI, gameplay, Azahar, or live asset selection is established.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", choices=("15555c", "151404"), required=True)
    parser.add_argument("--code", type=Path,
                        default=ROOT / "build/semantic-equivalence/real-assets/exefs/code.bin")
    parser.add_argument("--tbb", type=Path,
                        default=ROOT / "build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    candidate = CALLBACK_CLAMP if args.candidate == "15555c" else CALLBACK_TYPE1
    report = run_candidate(args.code.read_bytes(), args.tbb.read_bytes(), candidate)
    output = args.output or ROOT / f"build/semantic-equivalence/title-second-gate-{args.candidate}/report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Second-gate candidate {candidate:#010x} PASS; report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
