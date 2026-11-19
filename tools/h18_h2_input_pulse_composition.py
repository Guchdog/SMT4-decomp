#!/usr/bin/env python3
"""Offline release/press/hold/release composition for H2 logical query ID0/mode1."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unicorn
from unicorn import arm_const as arm

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips
from tools import h2_1078d8_11c5ec_chain as input_chain
from tools import h2_2c1830_experiment as logical_wrapper

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
QUERY_ADDR = 0x002C1830
QUERY_SIZE = 504
MODE1_ADDR = 0x00800000  # isolated executable scratch page; do not overwrite neighboring original code
MODE1_SIZE = 68
INPUT = 0x004650A0
STATE = 0x004E3C28
COUNTERS = 0x004E3C58
TABLE = 0x004099C0
STOP = input_chain.STOP
SP = input_chain.SP
NOP = struct.pack("<I", 0xE320F000)
MODE1_SOURCE = ROOT / "experiments/semantic_equivalence/h2_logical_mode1_query_candidate.cpp"
QUERY_SOURCE = ROOT / "experiments/semantic_equivalence/h2_2c1830_candidate.cpp"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def model_trace(events: list[dict], initial_counter: int = 0,
                mask: int = 1) -> list[dict]:
    """Model the documented row-0 counter and mode-1 primary/fallback result."""
    counter = initial_counter & 0xFFFFFFFF
    rows: list[dict] = []
    for event in events:
        available = int(event.get("available", 1) != 0)
        state_word = int(event.get("state_word", 0)) & 0xFFFFFFFF
        row_gate = int(event.get("row_gate", 0)) & 0xFFFFFFFF
        flags = int(event.get("flags", 0)) & 0xFFFFFFFF
        if row_gate != 0:
            counter = 0
        elif available:
            counter = (counter + 1) & 0xFFFFFFFF if state_word & mask else 0
        primary = int((flags & 1) == 0 and counter == 1)
        fallback = int(event.get("fallback_result", 0)) & 0xFFFFFFFF
        query = primary if primary != 0 else fallback
        rows.append({"label": event.get("label", f"event-{len(rows)}"),
                     "counter": counter, "availability": available,
                     "primary": primary, "fallback": fallback,
                     "query": query})
    return rows


def _pad_slot(body: bytes, slot_size: int, name: str) -> bytes:
    if len(body) > slot_size:
        raise ValueError(f"{name} body {len(body)} exceeds its {slot_size}-byte slot")
    if (slot_size - len(body)) % 4:
        raise ValueError(f"{name} body padding is not ARM word aligned")
    return body + NOP * ((slot_size - len(body)) // 4)


def _compile_candidate(source: Path, output: Path, symbol: str):
    output.mkdir(parents=True, exist_ok=True)
    obj = output / f"{source.stem}.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or f"compile failed for {source}")
    funcs = extract_elf_functions_detailed(obj)
    if symbol not in funcs:
        raise ValueError(f"{obj.name} does not contain {symbol}")
    body, relocs = funcs[symbol]
    return obj, body, relocs, list(result.args)


def write_scratch_helper_artifacts(output: Path, candidate_body: bytes,
                                   mutant_body: bytes) -> dict:
    """Persist the exact separately mapped helper bodies used by the control."""
    if not candidate_body or not mutant_body or candidate_body == mutant_body:
        raise ValueError("scratch control requires distinct nonempty helper bodies")
    candidate_path = output / "mode1-helper.bin"
    mutant_path = output / "wrong-counter-mutant-helper.bin"
    candidate_path.write_bytes(candidate_body)
    mutant_path.write_bytes(mutant_body)
    manifest = {
        "mapping_address": hex(MODE1_ADDR),
        "mapping_size": "0x1000",
        "candidate_helper_file": candidate_path.name,
        "candidate_helper_sha256": sha(candidate_body),
        "mutant_helper_file": mutant_path.name,
        "mutant_helper_sha256": sha(mutant_body),
        "distinct_bytes": candidate_body != mutant_body,
        "reproduction": "load candidate-image.bin; map a 0x1000 page at mapping_address; write mutant_helper_file at its base; run dispatcher entry 0x002c1830 with r0=0,r1=1 after the same refresh fixture",
    }
    (output / "scratch-helper-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def build_candidate_images(output: Path, original: bytes) -> dict:
    chain_image, reader_body, refresh_body, reader_relocs, refresh_relocs, _, _, chain_patches = (
        input_chain.build_staged(output / "refresh-reader-build", original)
    )
    mode_obj, mode_body, mode_relocs, mode_args = _compile_candidate(
        MODE1_SOURCE, output / "mode1-build", "candidate_002bffbc")
    bad_obj, bad_body, bad_relocs, bad_args = _compile_candidate(
        MODE1_SOURCE, output / "mode1-mutant-build", "candidate_002bffbc_bad_counter")
    query_obj, query_body, query_relocs, query_args = _compile_candidate(
        QUERY_SOURCE, output / "dispatcher-build", "candidate_002c1830")
    if mode_relocs or bad_relocs:
        raise ValueError("mode-1 candidate bodies must not have relocations")
    # The compiled helper is 68 bytes while its original function span is only 60.
    # Keep it in a separately mapped scratch page and relocate the wrapper call there.
    logical_wrapper.HELPERS["ui_func_002bffbc"] = MODE1_ADDR
    final_query = logical_wrapper.relocate(query_body, query_relocs, QUERY_ADDR)
    if len(final_query) > QUERY_SIZE:
        raise ValueError("dispatcher candidate exceeds original slot")

    payloads = list(chain_patches)
    payloads.append((QUERY_ADDR - input_chain.IMAGE_BASE,
                     _pad_slot(final_query, QUERY_SIZE, "dispatcher")))
    candidate = bytearray(original)
    for offset, payload in payloads:
        candidate[offset:offset + len(payload)] = payload
    candidate = bytes(candidate)
    ips = encode_ips(payloads, len(original))
    if apply_ips(original, ips) != candidate:
        raise AssertionError("combined replacement IPS does not replay to the staged image")

    expected_slots = {(off, off + len(payload)) for off, payload in payloads}
    changed = {i for i, (a, b) in enumerate(zip(original, candidate)) if a != b}
    if any(not any(start <= i < end for start, end in expected_slots) for i in changed):
        raise AssertionError("candidate image changed outside declared slots")
    return {
        "image": candidate,
        "ips": ips,
        "payloads": payloads,
        "reader_body": reader_body,
        "refresh_body": refresh_body,
        "mode1_body": mode_body,
        "bad_mode1_body": bad_body,
        "query_body": final_query,
        "reader_relocations": reader_relocs,
        "refresh_relocations": refresh_relocs,
        "mode1_relocations": mode_relocs,
        "query_relocations": query_relocs,
        "objects": {"mode1": sha(mode_obj.read_bytes()),
                    "mode1_mutant": sha(bad_obj.read_bytes()),
                    "dispatcher": sha(query_obj.read_bytes())},
        "compile_args": {"mode1": mode_args, "mode1_mutant": bad_args,
                         "dispatcher": query_args},
        "changed_bytes": len(changed),
    }


def fixture_case(seed: int, row_gate: int = 0) -> dict:
    case = input_chain.make_case(0, seed, mode=0, count=1, selector=0,
                                 flag_a=0, flag_b=0, post_gate=1)
    context = bytearray(case["context_bytes"])
    struct.pack_into("<I", context, 8, 0)
    context[0x30] = 0
    case["context_bytes"] = bytes(context)
    case["table"] = [(row_gate, 1)] + [(1, 0)] * 30
    case["counters"] = [0] * 31 + [0xDEADBEEF]
    return case


class PulseMachine(input_chain.Machine):
    def __init__(self, image: bytes, case: dict, mode1_body: bytes | None = None):
        super().__init__(image, case)
        if mode1_body is not None:
            self.uc.mem_map(MODE1_ADDR, 0x1000)
            self.uc.mem_write(MODE1_ADDR, mode1_body)
        self.query_trace: list[dict] = []
        for address in (QUERY_ADDR, MODE1_ADDR, 0x00124FA8):
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._query_hook,
                             begin=address, end=address)

    def _query_hook(self, uc, address, _size, _data):
        self.query_trace.append({
            "pc": hex(address),
            "r0": uc.reg_read(arm.UC_ARM_REG_R0),
            "r1": uc.reg_read(arm.UC_ARM_REG_R1),
            "lr": hex(uc.reg_read(arm.UC_ARM_REG_LR)),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        })

    def refresh_and_query(self, event: dict) -> dict:
        self.case["count"] = int(event.get("ring_count", 1))
        state_word = int(event.get("state_word", 0)) & 0xFFFFFFFF
        self.case["record"] = (state_word, 0, 0, 0, 0)
        self.writes.clear()
        self.ring_calls.clear()
        refresh_result = self.run()
        query_flags = int(event.get("flags", 0)) & 0xFFFFFFFF
        self.uc.mem_write(INPUT + 8, struct.pack("<I", query_flags))

        callee_regs = [getattr(arm, f"UC_ARM_REG_R{i}") for i in range(4, 12)]
        callee_before = [(0xA0100000 + i * 0x01010101) & 0xFFFFFFFF
                         for i in range(len(callee_regs))]
        for reg, value in zip(callee_regs, callee_before):
            self.uc.reg_write(reg, value)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, STOP)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 1)
        self.query_trace.clear()
        before_write_count = len(self.writes)
        fault = None
        try:
            self.uc.emu_start(QUERY_ADDR, STOP, count=50000)
        except unicorn.UcError as exc:
            fault = str(exc)
        query_stop = self.uc.reg_read(arm.UC_ARM_REG_PC) == STOP
        callee_after = [self.uc.reg_read(reg) for reg in callee_regs]
        query_writes = self.writes[before_write_count:]
        external_query_writes = [row for row in query_writes
                                 if not input_chain.STACK <= row[0] < input_chain.STACK + input_chain.STACK_SIZE]
        snapshot = {
            "refresh": refresh_result,
            "query_return": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "query_fault": fault,
            "query_stopped": query_stop,
            "query_sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "query_callee_saved": callee_after == callee_before,
            "query_trace": list(self.query_trace),
            "query_external_writes": external_query_writes,
            "query_flags": query_flags,
            "counter0": struct.unpack("<I", self.uc.mem_read(COUNTERS, 4))[0],
            "counter1": struct.unpack("<I", self.uc.mem_read(COUNTERS + 4, 4))[0],
            "state_word": struct.unpack("<I", self.uc.mem_read(STATE, 4))[0],
            "availability": struct.unpack("<I", self.uc.mem_read(INPUT + 4, 4))[0],
        }
        return snapshot


def event(label: str, state_word: int, ring_count: int = 1,
          flags: int = 0) -> dict:
    return {"label": label, "state_word": state_word, "ring_count": ring_count,
            "flags": flags}


DIRECTED_EVENTS = [
    event("release", 0),
    event("press", 1),
    event("held", 1),
    event("release_after_hold", 0),
    event("press_again", 1),
]


def run_profile(image: bytes, seed: int, events: list[dict],
                mode1_body: bytes | None = None) -> list[dict]:
    machine = PulseMachine(image, fixture_case(seed), mode1_body)
    rows = []
    for item in events:
        actual = machine.refresh_and_query(item)
        rows.append({"label": item["label"], **actual})
    return rows


def _comparable(row: dict) -> dict:
    refresh = row["refresh"]
    return {
        "refresh_fault": refresh["fault"],
        "refresh_sp": refresh["sp"],
        "refresh_callee_saved": refresh["callee_saved"],
        "state": refresh["state"],
        "context": refresh["context"],
        "availability": refresh["availability"],
        "counters": refresh["counters"],
        "ring_calls": refresh["ring_calls"],
        "refresh_writes": refresh["global_writes"],
        "query_return": row["query_return"],
        "query_fault": row["query_fault"],
        "query_stopped": row["query_stopped"],
        "query_sp": row["query_sp"],
        "query_callee_saved": row["query_callee_saved"],
        "query_external_writes": row["query_external_writes"],
        "counter0": row["counter0"],
        "counter1": row["counter1"],
        "state_word": row["state_word"],
        "query_flags": row["query_flags"],
    }


def _query_shape(row: dict) -> list[tuple[str, int, int]]:
    return [(item["pc"], item["r0"], item["r1"]) for item in row["query_trace"]]


def _absolute_gates(rows: list[dict]) -> dict:
    return {
        "no_refresh_or_query_fault": all(r["refresh"]["fault"] is None and r["query_fault"] is None for r in rows),
        "refresh_and_query_stopped": all(r["refresh"]["sp"] == SP and r["query_stopped"] for r in rows),
        "refresh_and_query_abi_preserved": all(r["refresh"]["callee_saved"] and r["query_callee_saved"] and r["query_sp"] == SP for r in rows),
        "one_ring_call_per_refresh": all(len(r["refresh"]["ring_calls"]) == 1 and r["refresh"]["ring_calls"][0]["source_is_fixture"] and r["refresh"]["ring_calls"][0]["sp_aligned_8"] for r in rows),
        "query_calls_expected_dispatcher": all(r["query_trace"] and r["query_trace"][0]["pc"] == hex(QUERY_ADDR) and r["query_trace"][0]["r0"] == 0 and r["query_trace"][0]["r1"] == 1 for r in rows),
        "query_does_not_write_external_data": all(not r["query_external_writes"] for r in rows),
    }


def run(output: Path, seed: int = 20261118) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise SystemExit("pinned original code.bin hash mismatch")
    built = build_candidate_images(output, original)

    original_rows = run_profile(original, seed, DIRECTED_EVENTS)
    candidate_rows = run_profile(built["image"], seed, DIRECTED_EVENTS,
                                  built["mode1_body"])
    if len(original_rows) != len(candidate_rows):
        raise AssertionError("original and candidate event counts differ")
    comparisons = []
    for left, right in zip(original_rows, candidate_rows):
        same = _comparable(left) == _comparable(right)
        comparisons.append({"label": left["label"], "equal": same,
                            "original": _comparable(left),
                            "candidate": _comparable(right),
                            "original_query_trace": left["query_trace"],
                            "candidate_query_trace": right["query_trace"]})

    expected = model_trace([{"label": x["label"], "available": 1,
                             "state_word": x["state_word"], "flags": 0}
                            for x in DIRECTED_EVENTS])
    observed_expected = all(
        row["counter0"] == model["counter"] and row["query_return"] == model["query"]
        for row, model in zip(original_rows, expected)
    )
    mutant_rows = run_profile(built["image"], seed, [event("press", 1)],
                              built["bad_mode1_body"])
    good_press = next(x for x in candidate_rows if x["label"] == "press")
    negative_detected = mutant_rows[0]["query_return"] != good_press["query_return"]

    # A nonmatching source snapshot skips counter writes; this can retain an old edge pulse.
    stale_events = [event("press_before_unavailable", 1),
                    event("unavailable_refresh", 0, ring_count=0),
                    event("release_after_unavailable", 0, ring_count=1)]
    stale_original = run_profile(original, seed, stale_events)
    stale_candidate = run_profile(built["image"], seed, stale_events,
                                   built["mode1_body"])
    stale_comparisons = [_comparable(a) == _comparable(b)
                         for a, b in zip(stale_original, stale_candidate)]

    # Query flag bit 0 suppresses mode-1 primary query while the pulse counter remains one.
    gate_events = [event("press_query_gated", 1, flags=1),
                   event("same_counter_ungated", 0, ring_count=0, flags=0)]
    gate_original = run_profile(original, seed, gate_events)
    gate_candidate = run_profile(built["image"], seed, gate_events,
                                  built["mode1_body"])
    gate_comparisons = [_comparable(a) == _comparable(b)
                        for a, b in zip(gate_original, gate_candidate)]

    # The row's nonzero first word is the independent table gate and forces counter0 to zero.
    row_gate_case = fixture_case(seed, row_gate=1)
    row_gate_original_machine = PulseMachine(original, row_gate_case)
    row_gate_candidate_machine = PulseMachine(built["image"], row_gate_case,
                                              built["mode1_body"])
    row_gate_case_event = event("table_gate", 1)
    row_gate_original = row_gate_original_machine.refresh_and_query(row_gate_case_event)
    row_gate_candidate = row_gate_candidate_machine.refresh_and_query(row_gate_case_event)
    row_gate_equal = _comparable(row_gate_original) == _comparable(row_gate_candidate)

    absolute = _absolute_gates(original_rows + candidate_rows + mutant_rows +
                               stale_original + stale_candidate + gate_original +
                               gate_candidate + [row_gate_original, row_gate_candidate])
    comparisons_pass = all(x["equal"] for x in comparisons) and all(stale_comparisons) and all(gate_comparisons) and row_gate_equal
    report = {
        "image_sha256": sha(original),
        "candidate_image_sha256": sha(built["image"]),
        "candidate_ips_sha256": sha(built["ips"]),
        "fixture_sha256": sha(json.dumps({"events": DIRECTED_EVENTS, "seed": seed}, sort_keys=True).encode()),
        "seed": seed,
        "candidate_slots": [{"address": hex(input_chain.IMAGE_BASE + offset),
                             "size": len(payload), "sha256": sha(payload)}
                            for offset, payload in built["payloads"]],
        "candidate_objects": built["objects"],
        "candidate_body_bytes": {"reader": len(built["reader_body"]),
                                 "refresher": len(built["refresh_body"]),
                                 "mode1": len(built["mode1_body"]),
                                 "mode1_mutant": len(built["bad_mode1_body"]),
                                 "dispatcher": len(built["query_body"])},
        "relocations": {"reader": built["reader_relocations"],
                        "refresher": built["refresh_relocations"],
                        "mode1": built["mode1_relocations"],
                        "dispatcher": [{"offset": r.offset, "type": r.relocation_type,
                                        "symbol": r.symbol_name,
                                        "target": logical_wrapper.HELPERS.get(r.symbol_name)}
                                       for r in built["query_relocations"]]},
        "directed_events": DIRECTED_EVENTS,
        "original_trace": original_rows,
        "candidate_trace": candidate_rows,
        "original_candidate_comparisons": comparisons,
        "model_trace": expected,
        "model_matches_original": observed_expected,
        "unavailable_events": stale_events,
        "unavailable_original_trace": stale_original,
        "unavailable_candidate_trace": stale_candidate,
        "unavailable_comparisons_equal": stale_comparisons,
        "query_gate_events": gate_events,
        "query_gate_original_trace": gate_original,
        "query_gate_candidate_trace": gate_candidate,
        "query_gate_comparisons_equal": gate_comparisons,
        "table_gate_original": row_gate_original,
        "table_gate_candidate": row_gate_candidate,
        "table_gate_comparison_equal": row_gate_equal,
        "negative_control": {"mutant": "candidate_002bffbc_bad_counter",
                             "good_press_query": good_press["query_return"],
                             "mutant_press_query": mutant_rows[0]["query_return"],
                             "detected": negative_detected,
                             "trace": mutant_rows[0],
                             "scratch_helper_artifacts": write_scratch_helper_artifacts(
                                 output, built["mode1_body"], built["bad_mode1_body"])},
        "absolute_gates": absolute,
        "all_passed": False,
        "runtime": "not_run",
        "scope": "pinned original versus production refresher/reader and typed mode1/dispatcher candidates staged at original VMAs; controlled 0x0012A758 ring seam; synthetic ordinary RAM",
    }
    report["all_passed"] = (
        comparisons_pass and observed_expected and negative_detected and
        all(absolute.values()) and
        all(row["counter0"] == exp["counter"] for row, exp in zip(original_rows, expected))
    )
    (output / "candidate-image.bin").write_bytes(built["image"])
    (output / "candidate.ips").write_bytes(built["ips"])
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_passed": report["all_passed"],
                      "events": len(DIRECTED_EVENTS),
                      "equal": sum(x["equal"] for x in comparisons),
                      "negative_control_detected": negative_detected,
                      "report": str(output / "report.json")}, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261118)
    args = parser.parse_args()
    report = run(args.output_dir, args.seed)
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
