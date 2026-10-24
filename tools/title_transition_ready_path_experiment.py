#!/usr/bin/env python3
"""Trace one synthetic readiness-to-title-help path in the pinned original ARM."""
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

from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, arm, unicorn,
)
from tools.tbb_semantic_experiment import TITLE_TBB_SLOT_BASE, TITLE_TBB_SLOT_ID
from tools.title_help_presentation_experiment import (
    EXPECTED_HELP, extract_help_entries, verify_reference,
)

START = 0x001E9FD4
STOP = 0x001EA15C  # pre-instruction stop before Camp_SetSlotMessage
HELP_ENTRY = 0x001EA12C
READY_VISIBLE = 0x0025A274
READY_SECOND = 0x002D569C
TBB_GLOBAL = 0x002C0EC4
TBB_SUBTABLE = 0x002AC2F4
TBB_PAYLOAD = 0x002C0E9C
PRESENTATION_CALLEE = 0x0029F10C
HELP_RGBA = 0x323232FF
TBB_CONTAINER_OFFSET = 0x100
WORK_OFFSET = 0x800
HANDLE_OFFSET = 0xC00
CHILD_OFFSET = 0xD00
HELP_OFFSET = 0x16
HELP_STRIDE = 0x56


def make_case(raw_tbb: bytes, selection: int) -> tuple[Case, dict]:
    if selection not in range(len(EXPECTED_HELP)):
        raise ValueError("selection must be 0..3")
    if len(raw_tbb) > DATA_SIZE - TBB_CONTAINER_OFFSET:
        raise ValueError("TitleTable.tbb does not fit in experiment memory")
    data = bytearray([0xCD]) * DATA_SIZE
    data[TBB_CONTAINER_OFFSET:TBB_CONTAINER_OFFSET + len(raw_tbb)] = raw_tbb
    work, handle, child = (DATA + WORK_OFFSET, DATA + HANDLE_OFFSET,
                           DATA + CHILD_OFFSET)
    struct.pack_into("<I", data, WORK_OFFSET + 8, selection)
    struct.pack_into("<I", data, WORK_OFFSET + 0x8C, handle)
    data[WORK_OFFSET + 0x94] = 1
    struct.pack_into("<I", data, HANDLE_OFFSET + 8, child)
    struct.pack_into("<i", data, CHILD_OFFSET + 0x34, 0)
    struct.pack_into("<i", data, CHILD_OFFSET + 0x58, 0)

    registers = [0xA5A50000 | index for index in range(13)]
    # These are the two work aliases used by the pinned mid-callback window.
    registers[4] = work
    registers[5] = work
    case = Case(f"synthetic-fast-readiness-selection-{selection}",
                tuple(registers), bytes(data), bytes([0xCD]) * STACK_SIZE, 0)
    setup = {"work": hex(work), "handle": hex(handle), "child": hex(child),
             "child_0x34_signed": 0, "child_0x58_signed": 0,
             "work_0x94": 1, "selection": selection}
    return case, setup


def install_title_slot(runner: Runner, container_pointer: int) -> int:
    slot_pointer_address = TITLE_TBB_SLOT_BASE + TITLE_TBB_SLOT_ID * 0x10 + 4
    page = slot_pointer_address & ~0xFFF
    runner.uc.mem_protect(page, 0x1000,
                          unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    runner.uc.mem_write(slot_pointer_address, struct.pack("<I", container_pointer))
    return slot_pointer_address


def run_case(image: bytes, raw_tbb: bytes, selection: int) -> dict:
    case, setup = make_case(raw_tbb, selection)
    runner = Runner(image, START)
    slot_address = install_title_slot(runner, DATA + TBB_CONTAINER_OFFSET)
    trace: list[int] = []
    reads: list[dict] = []
    calls: list[dict] = []
    writes: list[dict] = []
    stop_state = {"stopped": False, "presentation_args": None}
    call_targets = {READY_VISIBLE, READY_SECOND, TBB_GLOBAL, TBB_SUBTABLE,
                    TBB_PAYLOAD}

    def code_hook(uc, address, _size, _user):
        trace.append(address)
        if address in call_targets:
            calls.append({"target": hex(address),
                          "r0_r3": [hex(uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")))
                                    for i in range(4)],
                          "lr": hex(uc.reg_read(arm.UC_ARM_REG_LR))})
        if address == STOP:
            stop_state["stopped"] = True
            stop_state["presentation_args"] = {
                "r0": hex(uc.reg_read(arm.UC_ARM_REG_R0)),
                "r1": hex(uc.reg_read(arm.UC_ARM_REG_R1)),
                "lr": hex(uc.reg_read(arm.UC_ARM_REG_LR)),
            }
            uc.emu_stop()

    def memory_hook(uc, access, address, size, value, _user):
        if access == unicorn.UC_MEM_READ:
            raw = bytes(uc.mem_read(address, size))
            pc = uc.reg_read(arm.UC_ARM_REG_PC)
            reads.append({"pc": hex(pc), "address": hex(address), "size": size,
                          "value_hex": raw.hex()})
        elif access == unicorn.UC_MEM_WRITE:
            pc = uc.reg_read(arm.UC_ARM_REG_PC)
            writes.append({"pc": hex(pc), "address": hex(address),
                           "size": size, "value": hex(value & ((1 << (8 * size)) - 1))})

    runner.uc.hook_add(unicorn.UC_HOOK_CODE, code_hook)
    runner.uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE,
                       memory_hook)
    execution = runner.run(case, start=START, stops=(), budget=1024)
    if execution.fault:
        raise RuntimeError(f"selection {selection}: ARM fault at {execution.pc:#x}: {execution.fault}")
    if not stop_state["stopped"] or execution.pc != STOP:
        raise RuntimeError(f"selection {selection}: expected pre-call stop {STOP:#x}; "
                           f"stopped={stop_state['stopped']} pc={execution.pc:#x}")

    parsed = extract_help_entries(raw_tbb)
    entry = parsed["entries"][selection]
    expected_pointer = DATA + TBB_CONTAINER_OFFSET + parsed["payload_file_offset"] + entry["relative_payload_offset"]
    arguments = stop_state["presentation_args"]
    if int(arguments["r0"], 16) != expected_pointer:
        raise AssertionError(f"selection {selection}: ARM pointer {arguments['r0']} != {expected_pointer:#x}")
    if int(arguments["r1"], 16) != HELP_RGBA:
        raise AssertionError(f"selection {selection}: unexpected color {arguments['r1']}")
    if PRESENTATION_CALLEE in trace:
        raise AssertionError("Camp_SetSlotMessage was executed despite the pre-call stop")

    minimal_addresses = {DATA + WORK_OFFSET + 8, DATA + WORK_OFFSET + 0x8C,
                         DATA + WORK_OFFSET + 0x94, DATA + HANDLE_OFFSET + 8,
                         DATA + CHILD_OFFSET + 0x34, DATA + CHILD_OFFSET + 0x58,
                         slot_address, DATA + TBB_CONTAINER_OFFSET,
                         DATA + TBB_CONTAINER_OFFSET + 8,
                         DATA + TBB_CONTAINER_OFFSET + 0x0C}
    reached = {
        "start": START in trace,
        "first_readiness_call": READY_VISIBLE in trace,
        "second_readiness_call": READY_SECOND in trace,
        "help_entry": HELP_ENTRY in trace,
        "help_stop_before_presentation_call": STOP in trace,
        "mutation_block_skipped": 0x001EA070 not in trace,
        "camp_set_slot_message_not_entered": PRESENTATION_CALLEE not in trace,
    }
    if not all(reached.values()):
        raise AssertionError(f"selection {selection}: reachability evidence incomplete: {reached}")
    read_addresses = {int(item["address"], 16) for item in reads}
    unexpected_reads = sorted(read_addresses - minimal_addresses)
    # Table arithmetic reads the TBL1 header/offset entry in addition to the
    # synthetic fields. Report the exact addresses; fail on reads outside the
    # explicit graph and real TBB/global-slot regions.
    allowed_ranges = ((DATA + WORK_OFFSET, DATA + WORK_OFFSET + 0xA0),
                      (DATA + HANDLE_OFFSET, DATA + HANDLE_OFFSET + 0xC),
                      (DATA + CHILD_OFFSET, DATA + CHILD_OFFSET + 0x5C),
                      (DATA + TBB_CONTAINER_OFFSET,
                       DATA + TBB_CONTAINER_OFFSET + len(raw_tbb)),
                      (TITLE_TBB_SLOT_BASE + TITLE_TBB_SLOT_ID * 0x10,
                       TITLE_TBB_SLOT_BASE + (TITLE_TBB_SLOT_ID + 1) * 0x10))
    # These are the literal-pool words consumed by the original ARM caller
    # and TBB accessors, not additional object-graph state.
    code_literal_reads = {0x001E9EC4, 0x002C0EDC, 0x002AC348, 0x002AC34C,
                          0x002C0EC0}
    out_of_scope_reads = [item for item in reads
                          if int(item["address"], 16) not in code_literal_reads
                          and not any(start <= int(item["address"], 16) < end
                                      for start, end in allowed_ranges)]
    if out_of_scope_reads:
        raise AssertionError(f"selection {selection}: read outside modeled work/handle/child/TBB/global slot: "
                             f"{out_of_scope_reads}")
    if writes:
        raise AssertionError(f"selection {selection}: unexpected writes on this fast path: {writes}")

    return {"selection": selection, "setup": setup,
            "reached": reached, "executed_pc_count": len(trace),
            "executed_pcs": [hex(pc) for pc in trace],
            "call_entries": calls, "pre_presentation_call_args": arguments,
            "expected_pointer": hex(expected_pointer), "text": entry["text"],
            "read_count": len(reads), "read_accesses": reads,
            "distinct_read_addresses": [hex(value) for value in sorted(read_addresses)],
            "read_addresses_not_in_core_expected_set": [hex(value) for value in unexpected_reads],
            "writes": writes, "passed": True}


def run(code_path: Path, tbb_path: Path) -> dict:
    image = code_path.read_bytes()
    code_sha256 = verify_reference(image)
    raw_tbb = tbb_path.read_bytes()
    asset_sha256 = hashlib.sha256(raw_tbb).hexdigest()
    asset = extract_help_entries(raw_tbb)
    selections = [run_case(image, raw_tbb, index) for index in range(4)]
    expected_targets = [READY_VISIBLE, READY_SECOND, TBB_GLOBAL, TBB_SUBTABLE,
                        TBB_PAYLOAD]
    for result in selections:
        targets = [int(call["target"], 16) for call in result["call_entries"]]
        if targets != expected_targets:
            raise AssertionError(f"selection {result['selection']}: unexpected helper call order {targets}")
    return {
        "passed": True,
        "evidence_type": "continuous pinned original ARM execution in Unicorn on explicit synthetic fast-readiness inputs",
        "code_sha256": code_sha256,
        "asset_sha256": asset_sha256,
        "start": hex(START), "help_entry": hex(HELP_ENTRY),
        "stop_before_call": hex(STOP),
        "presentation_callee_not_entered": hex(PRESENTATION_CALLEE),
        "global_tbb_slot_pointer": hex(TITLE_TBB_SLOT_BASE + TITLE_TBB_SLOT_ID * 0x10 + 4),
        "asset": asset,
        "selections": selections,
        "limits": [
            "Synthetic branch-coverage setup only: child+0x34=0, child+0x58=0, and work+0x94=1; it is not claimed to be a runtime-normal state.",
            "Executes original ARM continuously from 0x001E9FD4 through both original readiness helpers and original TBB getter code, stopping before Camp_SetSlotMessage.",
            "Does not exercise the 0x001EA070 mutation/transition block, execute the presentation callee, render UI, establish behavior in Azahar, or constitute a C++ candidate.",
            "Only the modeled work/handle/child fields and the real TBB container/global slot are initialized; no full transition or renderer state is claimed.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--tbb", type=Path,
                        default=ROOT / "build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/title-transition-ready-path/report.json")
    args = parser.parse_args()
    report = run(args.code, args.tbb)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(f"Title readiness-to-help path {'PASS' if report['passed'] else 'FAIL'}; report: {args.output}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
