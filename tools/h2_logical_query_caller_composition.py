#!/usr/bin/env python3
"""Exercise real H2 Calc/query wrappers with original or typed query helpers."""
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

import unicorn
from unicorn import arm_const as arm

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_experiment import (
    ADDRESS as CALC_ADDRESS,
    CalcMachine,
    Scenario,
    directed_scenarios,
    relocated_candidate,
)
from tools.semantic_experiment import arm_branch

MODE0_ADDRESS = 0x002B902C
MODE1_ADDRESS = 0x002BFFBC
LOGICAL_WRAPPER = 0x002C1830
MODE0_INJECT = 0x01004000
MODE1_INJECT = 0x01004200
FLAGS = 0x004650A8
THRESHOLD = 0x004650AC
SELECTOR = 0x004650B0
COUNTERS = 0x004E3C58
CALC_SOURCE = ROOT / "experiments/semantic_equivalence/h2_calc_candidate.cpp"
MODE0_SOURCE = ROOT / "experiments/semantic_equivalence/h2_logical_mode0_query_candidate.cpp"
MODE1_SOURCE = ROOT / "experiments/semantic_equivalence/h2_logical_mode1_query_candidate.cpp"
CODE_DEFAULT = ROOT / "extracted/exefs/code.bin"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_candidate(source: Path, output: Path) -> tuple[Path, list[str]]:
    output.mkdir(parents=True, exist_ok=True)
    obj = output / f"{source.stem}.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or f"compile failed: {source.name}")
    return obj, list(result.args)


def extract_body(obj: Path, symbol: str) -> bytes:
    functions = extract_elf_functions_detailed(obj)
    if symbol not in functions:
        raise ValueError(f"{obj.name} lacks {symbol}")
    body, relocations = functions[symbol]
    if relocations:
        raise ValueError(f"{symbol} has unsupported relocations: {relocations}")
    return body


def logical_counter_seed(scenario: Scenario) -> list[int]:
    counters = [0] * 31
    assigned: dict[int, int] = {}
    for (query_id, mode), result in (scenario.logical or {}).items():
        if mode not in (0, 1):
            continue
        if not 0 <= query_id < 31:
            raise ValueError(f"scenario query ID outside helper domain: {query_id}")
        value = 1 if result else 0
        if query_id in assigned and assigned[query_id] != value:
            raise ValueError(f"scenario requests incompatible modes for ID {query_id}")
        assigned[query_id] = value
        counters[query_id] = value
    return counters


class LogicalQueryCalcMachine(CalcMachine):
    """Keep the real 0x2c1830 wrapper; optionally branch into typed helpers."""

    def __init__(self, image: bytes, scenario: Scenario, calc_code: bytes | None,
                 mode0_code: bytes | None, mode1_code: bytes | None):
        self.logical_wrapper_trace: list[tuple[int, int]] = []
        self.query_entry_trace: list[tuple[int, int]] = []
        super().__init__(image, entry_code=calc_code, scenario=scenario)

        if mode0_code is not None:
            self.uc.mem_write(MODE0_INJECT, mode0_code)
            self.uc.mem_write(MODE0_ADDRESS, arm_branch(MODE0_ADDRESS, MODE0_INJECT))
        if mode1_code is not None:
            self.uc.mem_write(MODE1_INJECT, mode1_code)
            self.uc.mem_write(MODE1_ADDRESS, arm_branch(MODE1_ADDRESS, MODE1_INJECT))

        # Reproduce the initialized H2 mode-0 profile and scenario-level logical
        # outcomes through the producer's query counters; no keyboard or mouse
        # event or H2 physical-button mapping is implied.
        self.uc.mem_write(FLAGS, struct.pack("<I", 0))
        self.uc.mem_write(THRESHOLD, struct.pack("<I", 7))
        self.uc.mem_write(SELECTOR, struct.pack("<I", 2))
        words = logical_counter_seed(scenario)
        self.uc.mem_write(COUNTERS, b"".join(struct.pack("<I", value) for value in words))

    def _code(self, uc, address, size, user_data):
        if address == LOGICAL_WRAPPER:
            self.logical_wrapper_trace.append((uc.reg_read(arm.UC_ARM_REG_R0),
                                               uc.reg_read(arm.UC_ARM_REG_R1)))
            # Do not return a mocked value; execute the pinned wrapper body.
            return
        if address == MODE0_ADDRESS:
            self.query_entry_trace.append((0, uc.reg_read(arm.UC_ARM_REG_R0)))
        elif address == MODE1_ADDRESS:
            self.query_entry_trace.append((1, uc.reg_read(arm.UC_ARM_REG_R0)))
        return super()._code(uc, address, size, user_data)

    def run(self) -> dict:
        result = super().run()
        result["logical_wrapper_trace"] = list(self.logical_wrapper_trace)
        result["query_entry_trace"] = list(self.query_entry_trace)
        return result


def compare_runs(left: dict, right: dict) -> str | None:
    for label, item in (("original", left), ("candidate", right)):
        if item["fault"] is not None:
            return f"{label} fault: {item['fault']}"
        if not item["stopped"]:
            return f"{label} did not reach return sentinel"
        if item["preserved"] != item["expected_preserved"]:
            return f"{label} violates callee-saved register/SP/d8-d15 ABI"
    for key in ("fault", "stopped", "return", "pc", "preserved", "work", "config",
                "trace", "logical_wrapper_trace", "query_entry_trace"):
        if left[key] != right[key]:
            return f"{key} differs"
    return None


def absolute_gates(result: dict) -> dict:
    return {
        "no_fault": result["fault"] is None,
        "reached_return_sentinel": result["stopped"],
        "preserved_abi_state": result["preserved"] == result["expected_preserved"],
    }


def scenarios() -> list[Scenario]:
    result = directed_scenarios(seed=7, samples=0)
    result.extend([
        Scenario("mode0-fallback-D", 1, row=0, values=(1, 2, 3),
                 logical={(4, 0): 0, (0xD, 0): 1}),
        Scenario("mode0-fallback-C", 1, row=1, values=(1, 9, 3),
                 logical={(3, 0): 0, (0xC, 0): 1}),
        Scenario("mode0-primary-and-fallback-zero", 1, row=0, values=(1, 2, 3),
                 logical={(4, 0): 0, (0xD, 0): 0}),
        Scenario("mode0-primary-trigger", 1, row=0, values=(1, 2, 3),
                 logical={(4, 0): 1}),
        Scenario("mode1-H2-ID9", 1, row=0, row_handle=0x110,
                 values=(1, 2, 3), logical={(9, 1): 1}),
        Scenario("mode1-ID0-positive", 1, row=0, row_handle=0x110,
                 values=(1, 2, 3), logical={(9, 1): 0, (0, 1): 1}),
        Scenario("mode1-ID1-positive", 1, row=0, row_handle=0x110,
                 values=(1, 2, 3), logical={(9, 1): 0, (0, 1): 0, (1, 1): 1}),
    ])
    return result


def run(output: Path, code_path: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    image = code_path.read_bytes()
    calc_obj, calc_args = compile_candidate(CALC_SOURCE, output / "compile-calc")
    mode0_obj, mode0_args = compile_candidate(MODE0_SOURCE, output / "compile-mode0")
    mode1_obj, mode1_args = compile_candidate(MODE1_SOURCE, output / "compile-mode1")
    calc_code, calc_fixups = relocated_candidate(calc_obj)
    mode0_code = extract_body(mode0_obj, "candidate_002b902c")
    mode1_code = extract_body(mode1_obj, "candidate_002bffbc")

    # Existing production objects prove these injected candidates are exactly
    # the production helper bodies, not independently different test copies.
    production_mode0 = ROOT / "build/agent-work/H2-semantic/h2-logical-mode0-query/run-003/checks/compile-consumers/leaf_batch30_b.o"
    production_mode1 = ROOT / "build/agent-work/H2-semantic/h2-logical-mode1-query/run-003/checks/compile-consumers/leaf_batch32_c.o"
    mode0_equal = mode0_code == extract_body(production_mode0, "ui_func_002b902c")
    mode1_equal = mode1_code == extract_body(production_mode1, "ui_func_002bffbc")
    if not mode0_equal or not mode1_equal:
        raise ValueError("injected helper body differs from its compiled production body")

    rows = []
    first_mismatch = None
    bad_mode0 = extract_body(mode0_obj, "candidate_002b902c_bad_counter")
    for scenario in scenarios():
        original = LogicalQueryCalcMachine(image, scenario, None, None, None).run()
        calc_cpp = LogicalQueryCalcMachine(image, scenario, calc_code, None, None).run()
        helpers_cpp = LogicalQueryCalcMachine(image, scenario, None, mode0_code, mode1_code).run()
        both_cpp = LogicalQueryCalcMachine(image, scenario, calc_code,
                                           mode0_code, mode1_code).run()
        executions = {"original": original, "calc_cpp": calc_cpp,
                      "typed_queries_cpp": helpers_cpp, "calc_and_queries_cpp": both_cpp}
        gates = {name: absolute_gates(execution) for name, execution in executions.items()}
        gates_passed = all(all(values.values()) for values in gates.values())
        comparisons = {
            "calc_candidate_with_original_queries": compare_runs(original, calc_cpp),
            "typed_queries_with_original_calc": compare_runs(original, helpers_cpp),
            "calc_and_queries_candidates": compare_runs(original, both_cpp),
        }
        passed = gates_passed and all(value is None for value in comparisons.values())
        row = {"scenario": scenario.label, "passed": passed,
               "absolute_gates": gates,
               "comparisons": comparisons,
               "wrapper_calls": original["logical_wrapper_trace"],
               "query_entries": original["query_entry_trace"],
               "work_sha256": sha256(original["work"]),
               "config_hex": original["config"].hex()}
        rows.append(row)
        if not passed and first_mismatch is None:
            first_mismatch = {"scenario": scenario.label, "comparisons": comparisons,
                              "absolute_gates": gates}

    fallback = next(s for s in scenarios() if s.label == "mode0-fallback-D")
    good_fallback = LogicalQueryCalcMachine(image, fallback, calc_code,
                                            mode0_code, mode1_code).run()
    bad_fallback = LogicalQueryCalcMachine(image, fallback, calc_code,
                                           bad_mode0, mode1_code).run()
    negative_detected = compare_runs(good_fallback, bad_fallback) is not None
    negative_difference = compare_runs(good_fallback, bad_fallback)
    if not negative_detected and first_mismatch is None:
        first_mismatch = {"scenario": fallback.label,
                          "reason": "wrong-counter query mutant did not change caller behavior"}

    observed_query_entries = sorted({tuple(entry) for row in rows
                                     for entry in row["query_entries"]})
    required_query_entries = {(0, 4), (0, 3), (0, 0xD), (0, 0xC),
                              (1, 9), (1, 0), (1, 1)}
    missing_query_entries = sorted(required_query_entries - set(observed_query_entries))
    if missing_query_entries and first_mismatch is None:
        first_mismatch = {"reason": "required dispatcher query entries were not reached",
                          "missing": missing_query_entries}

    report = {
        "schema": 1,
        "status": "passed" if first_mismatch is None else "failed",
        "scope": "offline injected Calc/logical-wrapper/query-helper caller composition with deterministic non-input services",
        "reference": {"code_sha256": sha256(image), "calc": hex(CALC_ADDRESS),
                      "logical_wrapper": hex(LOGICAL_WRAPPER),
                      "mode0_helper": hex(MODE0_ADDRESS), "mode1_helper": hex(MODE1_ADDRESS)},
        "candidates": {
            "calc": {"source_sha256": sha256(CALC_SOURCE.read_bytes()),
                     "object_sha256": sha256(calc_obj.read_bytes()),
                     "compiler_args": calc_args, "local_fixups": calc_fixups},
            "mode0": {"source_sha256": sha256(MODE0_SOURCE.read_bytes()),
                      "object_sha256": sha256(mode0_obj.read_bytes()),
                      "body_sha256": sha256(mode0_code), "body_size": len(mode0_code),
                      "production_body_equal": mode0_equal, "compiler_args": mode0_args},
            "mode1": {"source_sha256": sha256(MODE1_SOURCE.read_bytes()),
                      "object_sha256": sha256(mode1_obj.read_bytes()),
                      "body_sha256": sha256(mode1_code), "body_size": len(mode1_code),
                      "production_body_equal": mode1_equal, "compiler_args": mode1_args}},
        "coverage": {"scenario_count": len(rows), "scenarios_passed": sum(r["passed"] for r in rows),
                     "execution_count": sum(len(r["absolute_gates"]) for r in rows),
                     "all_absolute_gates_passed": all(
                         all(gates.values()) for row in rows
                         for gates in row["absolute_gates"].values()),
                     "mode0_fallback_D_present": any(r["scenario"] == "mode0-fallback-D" for r in rows),
                     "mode0_fallback_C_present": any(r["scenario"] == "mode0-fallback-C" for r in rows),
                     "required_query_entries": [list(pair) for pair in sorted(required_query_entries)],
                     "observed_query_entries": [list(pair) for pair in observed_query_entries],
                     "required_query_entries_all_reached": not missing_query_entries,
                     "query_inputs_seeded_from_logical_results": True},
        "negative_control": {"name": "wrong-counter mode0 helper in H2 fallback-D scenario",
                             "detected": negative_detected,
                             "difference": negative_difference},
        "evidence": {"caller": "passed" if first_mismatch is None else "failed",
                     "arm_differential": "partial", "runtime": "not_run"},
        "limits": ["Typed helpers are injected at synthetic addresses by branch instructions for offline caller testing; no IPS/code.bin integration is claimed.",
                   "The mode-0 candidate retains original 0x002c6c10. Selector zero, producer scheduling, physical controls, event delivery, persistence and Azahar runtime are not established.",
                   "Allocator, task/process, cursor, touch, render, script/resource and other non-input Calc boundaries retain deterministic HLE behavior.",
                   "Scenario counter words encode requested logical outcomes directly; this is not a producer test or a safe runtime event-injection seam."],
        "first_mismatch": first_mismatch,
        "cases": rows,
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code", type=Path, default=CODE_DEFAULT)
    args = parser.parse_args()
    report = run(args.output, args.code)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
