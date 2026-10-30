#!/usr/bin/env python3
"""Differentially validate the production Calc+Draw combined image offline."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.h2_calc_experiment import Scenario as CalcScenario
from tools.h2_calc_sequence_experiment import (
    PersistentCalc, _assert_tick, sequence_specs,
)
from tools.h2_draw_experiment import DrawMachine, compare as compare_draw, directed_scenarios
from tools.h2_secondary_experiment import (
    ENTRY as SECONDARY_ENTRY,
    Run as SecondaryRun,
    compare as compare_secondary,
    compile_candidates as compile_secondary_candidates,
    make_cases as secondary_cases,
)
from tools.h2_init_orchestration_experiment import (
    INIT as INITIALIZER_ENTRY,
    InitRun,
    build_cases as initializer_cases,
    compare as compare_initializer,
    compile_candidate as compile_initializer_candidates,
)
from tools.h2_ready_experiment import (
    ADDRESS as READY_ENTRY,
    SCENARIOS as ready_scenarios,
    compare as compare_ready,
    run_callback as run_ready_callback,
)
from tools.h2_combined_code_patch import (
    DRAW_HELPER_VMA, DRAW_VMA, INIT_STRING_POOL_VMA, ORIGINAL_SHA256,
    parse_elf32, patch_call, SECONDARY_CAVE_VMA,
)

EXPECTED_COMBINED_SHA256 = "eaac1ebd0875436210b49e5c0874ab93d7087a47b52847b85bc8f3f59b003186"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compare_calc(original: dict, patched: dict, original_hash: str,
                 patched_hash: str) -> str | None:
    for name, result, expected_hash in (("original", original, original_hash),
                                        ("patched", patched, patched_hash)):
        if result["fault"]:
            return f"{name} fault: {result['fault']}"
        if not result["stopped"]:
            return f"{name} missed Calc return sentinel"
        if result["preserved"] != result["expected_preserved"]:
            return f"{name} violates callee-saved ABI"
        if result["image_sha256"] != expected_hash:
            return f"{name} image identity mismatch"
    for field in ("return", "pc", "preserved", "work", "config", "work_global",
                  "config_global", "trace"):
        if original[field] != patched[field]:
            return f"{field} differs"
    return None


def validate_draw(original_image: bytes, patched_image: bytes) -> dict:
    rows = []
    first = None
    for scenario in directed_scenarios():
        left = DrawMachine(original_image, scenario=scenario).run()
        right = DrawMachine(patched_image, scenario=scenario).run()
        # The replacement points at a copied %s literal in the cave; compare
        # formatted contents/arguments, not the expectedly different guest
        # address of that equivalent read-only string.
        left_cmp, right_cmp = dict(left), dict(right)
        left_cmp["trace"] = [tuple((event[0], 0, *event[2:]))
                             if event[0] == "format_text" else event
                             for event in left["trace"]]
        right_cmp["trace"] = [tuple((event[0], 0, *event[2:]))
                              if event[0] == "format_text" else event
                              for event in right["trace"]]
        difference = compare_draw(left_cmp, right_cmp)
        original_indices = [e[2] for e in left["trace"] if e[0] == "format_text"]
        patched_indices = [e[2] for e in right["trace"] if e[0] == "format_text"]
        if scenario.expect_no_tbb and any(
                e[0] in ("tbb_subtable", "tbb_payload")
                for e in left["trace"] + right["trace"]):
            difference = difference or "unexpected TBB call in unsigned-index guard case"
        row = {"case": scenario.label, "passed": difference is None,
               "difference": difference,
               "format_indices": {"original": original_indices, "patched": patched_indices},
               "trace_count": {"original": len(left["trace"]), "patched": len(right["trace"])}}
        rows.append(row)
        if difference and first is None:
            first = {"case": scenario.label, "difference": difference}

    # Mutate one resolved BL to target the helper's second instruction. This
    # must make the same path diverge, proving the final-address call matters.
    bad = bytearray(patched_image)
    call_off = DRAW_VMA - 0x00100000 + 332
    word = struct.unpack_from("<I", bad, call_off)[0]
    struct.pack_into("<I", bad, call_off,
                     patch_call(word, DRAW_VMA + 332, DRAW_HELPER_VMA + 4))
    control_case = next(s for s in directed_scenarios() if s.label == "active-selected-row-0")
    good_run = DrawMachine(patched_image, scenario=control_case).run()
    bad_run = DrawMachine(bytes(bad), scenario=control_case).run()
    good_cmp, bad_cmp = dict(good_run), dict(bad_run)
    for result in (good_cmp, bad_cmp):
        result["trace"] = [tuple((event[0], 0, *event[2:]))
                           if event[0] == "format_text" else event
                           for event in result["trace"]]
    control_diff = compare_draw(good_cmp, bad_cmp)
    negative = {"name": "first-helper-call-target-plus-four", "detected": control_diff is not None,
                "difference": control_diff, "case": control_case.label}
    return {"case_count": len(rows), "cases_passed": sum(r["passed"] for r in rows),
            "first_counterexample": first, "negative_control": negative,
            "cases": rows,
            "evidence": {"arm_differential": "passed" if first is None else "failed",
                         "caller": "not_run", "runtime": "not_run"},
            "limits": ["Cursor, TBB, layout, format/font, panel/sprite, render-value, touch and indirect callback services remain deterministic HLE boundaries.",
                       "This compares the production Draw symbol and outlined helper at final addresses, not the title scheduler or visible UI."]}


def validate_calc_sequences(original_image: bytes, patched_image: bytes,
                            seeds: list[int]) -> dict:
    original_hash, patched_hash = sha256(original_image), sha256(patched_image)
    sequences = []
    for seed in seeds:
        for spec in sequence_specs(seed):
            initial = spec["steps"][0]["scenario"]
            left_machine = PersistentCalc(original_image, initial, spec["seed"])
            right_machine = PersistentCalc(patched_image, initial, spec["seed"])
            ticks = []
            for step in spec["steps"]:
                left = left_machine.tick(step["scenario"])
                right = right_machine.tick(step["scenario"])
                expected_left = _assert_tick(left, step, "original")
                expected_right = _assert_tick(right, step, "patched")
                difference = compare_calc(left, right, original_hash, patched_hash)
                passed = not expected_left and not expected_right and not difference
                ticks.append({"tick": step["label"], "passed": passed,
                              "expected_original": expected_left,
                              "expected_patched": expected_right,
                              "difference": difference,
                              "artifact_sha256": {"original": left["image_sha256"],
                                                  "patched": right["image_sha256"]},
                              "state": {"original": left["state"], "patched": right["state"]},
                              "return": {"original": hex(left["return"]),
                                         "patched": hex(right["return"])}})
            sequences.append({"name": spec["label"], "seed": seed,
                              "passed": all(t["passed"] for t in ticks), "ticks": ticks})

    scenario_original = CalcScenario("negative-decrement", 1, row=0,
                                     values=(1, 2, 3), logical={(4, 0): 1})
    scenario_wrong = CalcScenario("wrong-map-to-increment", 1, row=0,
                                  values=(1, 2, 3), logical={(3, 0): 1})
    left = PersistentCalc(original_image, scenario_original, 17).tick(scenario_original)
    right = PersistentCalc(patched_image, scenario_original, 17).tick(scenario_wrong)
    control_diff = compare_calc(left, right, original_hash, patched_hash)
    negative = {"name": "wrong-logical-map-4-0-to-3-0",
                "detected": control_diff is not None, "difference": control_diff,
                "original_state_value": struct.unpack_from("<I", left["work"], 0x28)[0],
                "mutant_state_value": struct.unpack_from("<I", right["work"], 0x28)[0]}
    return {"sequence_count": len(sequences),
            "sequences_passed": sum(s["passed"] for s in sequences),
            "tick_count": sum(len(s["ticks"]) for s in sequences),
            "ticks_passed": sum(t["passed"] for s in sequences for t in s["ticks"]),
            "negative_control": negative, "sequences": sequences,
            "evidence": {"arm_differential": "passed" if all(s["passed"] for s in sequences)
                         else "failed", "caller": "partial", "runtime": "not_run"},
            "limits": ["Calc sequences use the original HLE cursor/script/resource boundaries and do not execute through the title scheduler.",
                       "The Calc image hash is the combined image; Draw changes are present but outside the Calc callback's observed state contract."]}


def validate_secondary(original_image: bytes, patched_image: bytes,
                       output: Path, seeds: list[int]) -> dict:
    rows = []
    first = None
    for seed in seeds:
        for case in secondary_cases():
            left = SecondaryRun(original_image, SECONDARY_ENTRY, None, case, seed).run()
            right = SecondaryRun(patched_image, SECONDARY_ENTRY, None, case, seed).run()
            difference = compare_secondary(left, right)
            rows.append({"seed": seed, "case": case["label"],
                         "passed": difference is None, "difference": difference,
                         "helper_count": {"original": len(left["trace"]),
                                          "patched": len(right["trace"])},
                         "return_pc": {"original": hex(left["pc"]),
                                       "patched": hex(right["pc"])}})
            if difference and first is None:
                first = {"seed": seed, "case": case["label"], "difference": difference}

    # Put the reviewed wrong-count candidate at the exact final Secondary VMA.
    # The patched entry branch remains intact, so the mutant exercises the same
    # cave route as the production body and proves this path is observable.
    mutant_root = output / "secondary-negative-control-build"
    mutant_root.mkdir()
    mutants, build = compile_secondary_candidates(mutant_root)
    mutant_body = mutants["candidate_002caef0_wrong_count"]
    cave_span = 0x003FF000 - SECONDARY_CAVE_VMA
    if len(mutant_body) > cave_span:
        raise ValueError("Secondary wrong-count control exceeds the allocated subrange")
    mutant_image = bytearray(patched_image)
    cave_off = SECONDARY_CAVE_VMA - 0x00100000
    mutant_image[cave_off:cave_off + cave_span] = bytes(cave_span)
    mutant_image[cave_off:cave_off + len(mutant_body)] = mutant_body
    control_case = next(case for case in secondary_cases()
                        if case["label"] == "both-loops-distinct")
    control_seed = seeds[0]
    control_original = SecondaryRun(original_image, SECONDARY_ENTRY, None,
                                    control_case, control_seed).run()
    control_mutant = SecondaryRun(bytes(mutant_image), SECONDARY_ENTRY, None,
                                  control_case, control_seed).run()
    control_difference = compare_secondary(control_original, control_mutant)
    negative = {"name": "wrong-count-candidate-at-final-secondary-vma",
                "detected": control_difference is not None,
                "difference": control_difference, "case": control_case["label"],
                "seed": control_seed,
                "candidate_bytes": len(mutant_body),
                "build": build}
    return {"case_count": len(rows), "cases_passed": sum(row["passed"] for row in rows),
            "first_counterexample": first, "negative_control": negative,
            "cases": rows,
            "evidence": {"arm_differential": "passed" if first is None else "failed",
                         "caller": "partial", "runtime": "not_run"},
            "limits": ["Helper 0x002B9008 is modeled with its direct manager-halfword effect; other cleanup/task helpers are trace-only HLE boundaries.",
                       "The State-9/10 caller records callback registration but does not schedule or execute this Secondary callback."]}


def validate_initializer(original_image: bytes, patched_image: bytes,
                         output: Path, seeds: list[int]) -> dict:
    rows = []
    first = None
    for seed in seeds:
        for case in initializer_cases(seed, samples=2):
            left = InitRun(original_image, None, INITIALIZER_ENTRY, seed=seed).run(case)
            right = InitRun(patched_image, None, INITIALIZER_ENTRY, seed=seed).run(case)
            left_cmp, right_cmp = dict(left), dict(right)
            left_cmp["trace"] = _normalize_initializer_string_pointers(left["trace"])
            right_cmp["trace"] = _normalize_initializer_string_pointers(right["trace"])
            difference = compare_initializer(left_cmp, right_cmp)
            rows.append({"seed": seed, "case": case["label"],
                         "passed": difference is None, "difference": difference,
                         "task_names": [event.get("r0_string") for event in right["trace"]
                                        if event.get("name") == "process_factory_hle"],
                         "return": {"original": hex(left["return"]),
                                    "patched": hex(right["return"])},
                         "writes": {"original": len(left["writes"]),
                                    "patched": len(right["writes"])}})
            if difference and first is None:
                first = {"seed": seed, "case": case["label"], "difference": difference}

    # The existing wrong-group-count candidate has the same observed helper
    # model and entry contract. Retarget its one shared task-name literal to
    # the verified copied pool so the mutant tests that production caller path.
    mutant_root = output / "initializer-negative-control-build"
    mutant_root.mkdir()
    mutants, build = compile_initializer_candidates(mutant_root)
    mutant_body = bytearray(mutants["candidate_002f4ca0_wrong_count"])
    old_base, new_base = struct.pack("<I", 0x002F4E84), struct.pack("<I", INIT_STRING_POOL_VMA)
    if mutant_body.count(old_base) != 1:
        raise ValueError("initializer wrong-count mutant no longer has one expected task-name pointer")
    mutant_body = mutant_body.replace(old_base, new_base)
    if len(mutant_body) > 572:
        raise ValueError("initializer wrong-count mutant exceeds the original entry span")
    mutant_image = bytearray(patched_image)
    init_off = INITIALIZER_ENTRY - 0x00100000
    mutant_image[init_off:init_off + 572] = bytes(572)
    mutant_image[init_off:init_off + len(mutant_body)] = mutant_body
    control_case = initializer_cases(seeds[0], samples=2)[0]
    control_original = InitRun(original_image, None, INITIALIZER_ENTRY,
                               seed=seeds[0]).run(control_case)
    control_mutant = InitRun(bytes(mutant_image), None, INITIALIZER_ENTRY,
                             seed=seeds[0]).run(control_case)
    control_left, control_right = dict(control_original), dict(control_mutant)
    control_left["trace"] = _normalize_initializer_string_pointers(control_original["trace"])
    control_right["trace"] = _normalize_initializer_string_pointers(control_mutant["trace"])
    control_difference = compare_initializer(control_left, control_right)
    negative = {"name": "wrong-sprite-group-count-0x17-at-final-entry",
                "detected": control_difference is not None,
                "difference": control_difference,
                "case": control_case["label"], "seed": seeds[0],
                "candidate_bytes": len(mutant_body), "build": build,
                "retargeted_task_name_pool": hex(INIT_STRING_POOL_VMA)}
    return {"case_count": len(rows), "cases_passed": sum(row["passed"] for row in rows),
            "first_counterexample": first, "negative_control": negative,
            "cases": rows,
            "evidence": {"arm_differential": "passed" if first is None else "failed",
                         "caller": "partial", "runtime": "not_run"},
            "limits": ["Allocator, task factories, sprite/cursor/resource, asynchronous loader, sound/reset, and other subsystem effects use the original helper bodies plus explicit HLE boundaries.",
                       "The rodata pool is present in the final mapped image; actual installed Azahar loader exposure/protection and runtime string reads remain untested."]}


def _normalize_initializer_string_pointers(trace: list[dict]) -> list[dict]:
    """Normalize relocated pool addresses while preserving actual string contents."""
    string_arguments = {0x002C5978, 0x002C4C00, 0x00118488, 0x00297704}
    normalized = []
    for event in trace:
        item = dict(event)
        if int(item["address"], 16) in string_arguments:
            args = list(item["r0_r3"])
            args[0] = "0x00000000"
            item["r0_r3"] = args
        normalized.append(item)
    return normalized


def validate_ready_gate(original_image: bytes, patched_image: bytes) -> dict:
    rows = []
    first = None
    for case in ready_scenarios:
        left = run_ready_callback(original_image, None, case)
        right = run_ready_callback(patched_image, None, case)
        difference = compare_ready(left, right)
        rows.append({"case": case["label"], "passed": difference is None,
                     "difference": difference,
                     "original": {"return": left["return"], "pc": left["pc"],
                                  "sp": left["sp"], "trace": left["trace"]},
                     "patched": {"return": right["return"], "pc": right["pc"],
                                 "sp": right["sp"], "trace": right["trace"]}})
        if difference and first is None:
            first = {"case": case["label"], "difference": difference}

    bad = bytearray(patched_image)
    ready_off = READY_ENTRY - 0x00100000
    bad[ready_off:ready_off + 8] = bytes.fromhex("0100a0e31eff2fe1")
    control_case = next(case for case in ready_scenarios
                        if case["label"] == "task-still-registered")
    control_original = run_ready_callback(original_image, None, control_case)
    control_mutant = run_ready_callback(bytes(bad), None, control_case)
    control_difference = compare_ready(control_original, control_mutant)
    negative = {"name": "always-ready-result-at-final-ready-vma",
                "detected": control_difference is not None,
                "difference": control_difference, "case": control_case["label"]}
    return {"case_count": len(rows), "cases_passed": sum(row["passed"] for row in rows),
            "first_counterexample": first, "negative_control": negative,
            "cases": rows,
            "evidence": {"arm_differential": "passed" if first is None else "failed",
                         "caller": "partial", "runtime": "not_run"},
            "limits": ["The task-registration helper 0x002BF41C is modeled with the same result in both runs; its task-list implementation is not part of this callback differential.",
                       "The comparator checks SP restoration and all callee-saved GPR/VFP registers but does not compare caller-owned stack bytes."]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--patched", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[7, 20261024])
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.mkdir(parents=True)
    original, patched = args.original.read_bytes(), args.patched.read_bytes()
    if sha256(original) != ORIGINAL_SHA256:
        raise ValueError("original image identity differs from the pinned reference")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8")) if args.manifest else None
    if manifest is None:
        if sha256(patched) != EXPECTED_COMBINED_SHA256:
            raise ValueError("input image identity differs from the reviewed combined patch")
        manifest = {"patched_sha256": EXPECTED_COMBINED_SHA256,
                    "placements": {}}
    if manifest.get("patched_sha256") != sha256(patched):
        raise ValueError("manifest does not identify the supplied patched image")
    started = time.perf_counter()
    draw = validate_draw(original, patched)
    calc = validate_calc_sequences(original, patched, args.seeds)
    secondary = (validate_secondary(original, patched, args.output, args.seeds)
                 if "secondary_body" in manifest.get("placements", {}) else None)
    initializer = (validate_initializer(original, patched, args.output, args.seeds)
                   if "initializer" in manifest.get("placements", {}) else None)
    ready_gate = (validate_ready_gate(original, patched)
                  if "ready_gate" in manifest.get("placements", {}) else None)
    passed = (draw["cases_passed"] == draw["case_count"]
              and draw["negative_control"]["detected"]
              and calc["sequences_passed"] == calc["sequence_count"]
              and calc["negative_control"]["detected"]
              and (secondary is None or (
                  secondary["cases_passed"] == secondary["case_count"]
                  and secondary["negative_control"]["detected"]))
              and (initializer is None or (
                  initializer["cases_passed"] == initializer["case_count"]
                  and initializer["negative_control"]["detected"]))
              and (ready_gate is None or (
                  ready_gate["cases_passed"] == ready_gate["case_count"]
                  and ready_gate["negative_control"]["detected"])))
    report = {"schema": 1, "passed": passed,
              "original_sha256": sha256(original), "combined_sha256": sha256(patched),
              "runner_sha256": sha256(Path(__file__).read_bytes()),
              "draw": draw, "calc": calc, "secondary": secondary,
              "initializer": initializer, "ready_gate": ready_gate,
              "elapsed_seconds": round(time.perf_counter() - started, 3),
              "evidence": {"compiled": "passed", "arm_differential": "passed" if passed else "failed",
                           "caller": "partial", "runtime": "not_run"}}
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": passed, "draw": [draw["cases_passed"], draw["case_count"]],
                      "calc_sequences": [calc["sequences_passed"], calc["sequence_count"]],
                      "calc_ticks": [calc["ticks_passed"], calc["tick_count"]],
                      "secondary_cases": ([secondary["cases_passed"], secondary["case_count"]]
                                          if secondary else None),
                      "initializer_cases": ([initializer["cases_passed"], initializer["case_count"]]
                                            if initializer else None),
                      "ready_cases": ([ready_gate["cases_passed"], ready_gate["case_count"]]
                                      if ready_gate else None),
                      "report": str(args.output / "report.json")}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
