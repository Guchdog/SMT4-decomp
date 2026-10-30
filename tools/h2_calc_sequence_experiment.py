#!/usr/bin/env python3
"""Run persistent offline TitleConfig_Calc state sequences on original/patched images."""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import (
    SYMBOL, build_patch, elf_function_section_offset, normalize_local_text_addends,
)
from tools.h2_calc_experiment import (
    ADDRESS, CONFIG_GLOBAL, DATA, WORK, WORK_GLOBAL, CalcMachine, Scenario,
)

CODE_DEFAULT = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "experiments/semantic_equivalence/h2_calc_candidate.cpp"
EXPECTED_ORIGINAL_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
EXPECTED_PATCHED_SHA256 = "c9ebf62679043512c22c684b50f9e9cbf1fe824e016f119c2de4bddf664eb45d"
WORK_SIZE = 0x158
U32 = 0xFFFFFFFF


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PersistentCalc:
    """Reuse a CalcMachine's Unicorn address space and work/config across ticks."""
    def __init__(self, image: bytes, first: Scenario, seed: int):
        self.image_hash = sha256_bytes(image)
        self.machine = CalcMachine(image, scenario=first)
        # Give each seeded pass a distinct, valid row-2 value. The other fields
        # used by each directed branch are explicitly initialized by Scenario.
        work = bytearray(self.machine.uc.mem_read(WORK, WORK_SIZE))
        struct.pack_into("<I", work, 0x30, 2 + (seed % 8))
        self.machine.uc.mem_write(WORK, bytes(work))

    def tick(self, scenario: Scenario) -> dict:
        self.machine.scenario = scenario
        result = self.machine.run()
        uc = self.machine.uc
        result["state"] = struct.unpack_from("<I", result["work"], 0x08)[0]
        result["work_global"] = bytes(uc.mem_read(WORK_GLOBAL, 4))
        result["config_global"] = bytes(uc.mem_read(CONFIG_GLOBAL, 8))
        # The immutable host-side image bytes are fixed for the lifetime of
        # this sequence. Guest text mappings may contain mutable runtime data;
        # their byte-for-byte snapshot is not the artifact identity.
        result["image_sha256"] = self.image_hash
        result["trace"] = [list(call) for call in result["trace"]]
        return result


def _sequence(label: str, seed: int, steps: list[dict]) -> dict:
    # Vary an unaffected-but-valid option across seeded passes to ensure each
    # pass uses a fresh cloned initial fixture, not leaked prior sequence state.
    seeded_steps = []
    row2_seed = 2 + (seed % 8)
    for step in steps:
        scenario = step["scenario"]
        values = list(scenario.values)
        if scenario.state in (0, 1) and scenario.row != 2:
            values[2] = row2_seed
        seeded_steps.append({**step, "scenario": replace(scenario, values=tuple(values))})
    return {"label": label, "seed": seed, "steps": seeded_steps}


def sequence_specs(seed: int) -> list[dict]:
    return [
        _sequence("state0-wait-ready-state1-entry", seed, [
            {"label": "resource-wait", "scenario": Scenario("resource-wait", 0, resource_available=0), "expect_state": 0, "service_results": {"resource_available": 0}},
            {"label": "resource-ready-initialize", "scenario": Scenario("resource-ready", 0, resource_available=1), "expect_state": 1, "service_results": {"resource_available": 1, "sprite_ready": 1}},
            {"label": "state1-no-event", "scenario": Scenario("state1-no-event", 1), "expect_state": 1, "logical": {(4, 0): 0, (3, 0): 0}},
        ]),
        _sequence("state1-logical-actions-and-clamps", seed, [
            {"label": "no-event", "scenario": Scenario("no-event", 1, row=0, values=(1, 9, 3)), "expect_state": 1, "logical": {(4, 0): 0, (3, 0): 0}, "work_values": {0: 1, 1: 9}},
            {"label": "decrement-clamped-at-zero", "scenario": Scenario("decrement-zero", 1, row=0, logical={(4, 0): 1}), "expect_state": 1, "logical": {(4, 0): 1}, "work_values": {0: 0}},
            {"label": "decrement-at-zero-again", "scenario": Scenario("decrement-zero-again", 1, row=0, logical={(4, 0): 1}), "expect_state": 1, "logical": {(4, 0): 1}, "work_values": {0: 0}},
            {"label": "increment-nine-to-ten", "scenario": Scenario("increment-nine", 1, row=1, logical={(3, 0): 1}), "expect_state": 1, "logical": {(3, 0): 1}, "work_values": {1: 10}},
            {"label": "increment-clamped-at-ten", "scenario": Scenario("increment-ten", 1, row=1, logical={(3, 0): 1}), "expect_state": 1, "logical": {(3, 0): 1}, "work_values": {1: 10}},
        ]),
        *[_sequence(f"state2-exit-result-{decision}", seed, [
            {"label": "state1-to-state2", "scenario": Scenario("to-state2", 1, logical={(0, 1): 1}), "expect_state": 2, "logical": {(0, 1): 1}},
            {"label": "script-pending", "scenario": Scenario("pending", 2, script_runner=1), "expect_state": 2, "script_runner": 1},
            {"label": f"exit-result-{decision}", "scenario": Scenario("exit", 2, script_runner=2, exit_decision=decision),
             "expect_state": 3 if decision == 0 else (1 if decision == 1 else 2), "exit_decision": decision},
        ]) for decision in (0, 1, 2, 3)],
        _sequence("state2-to-state3-to-state4-readiness", seed, [
            {"label": "state1-to-state2", "scenario": Scenario("to-state2", 1, logical={(0, 1): 1}), "expect_state": 2, "logical": {(0, 1): 1}},
            {"label": "script-pending", "scenario": Scenario("pending", 2, script_runner=1), "expect_state": 2, "script_runner": 1},
            {"label": "state2-result-zero-to-state3", "scenario": Scenario("to-state3", 2, script_runner=2, exit_decision=0), "expect_state": 3, "config4": 1},
            {"label": "state3-not-ready", "scenario": Scenario("not-ready", 3, sprite_ready=0), "expect_state": 3, "service_results": {"sprite_ready": 0}},
            {"label": "state3-ready-to-state4", "scenario": Scenario("ready", 3, sprite_ready=1), "expect_state": 4, "service_results": {"sprite_ready": 1}},
        ]),
        _sequence("state1-logical-exit-to-state3", seed, [
            {"label": "logical-state3-transition", "scenario": Scenario("logical-state3", 1, logical={(1, 1): 1}), "expect_state": 3, "logical": {(1, 1): 1}},
            {"label": "state3-ready-to-state4", "scenario": Scenario("ready", 3, sprite_ready=1), "expect_state": 4, "service_results": {"sprite_ready": 1}},
        ]),
    ]


def _assert_tick(result: dict, step: dict, side: str) -> str | None:
    if result["fault"]:
        return f"{side} fault: {result['fault']}"
    if not result["stopped"]:
        return f"{side} missed Calc return sentinel"
    if result["preserved"] != result["expected_preserved"]:
        return f"{side} violated callee-saved r4-r11/SP/d8-d15"
    if result["state"] != step["expect_state"]:
        return f"{side} state {result['state']} != expected {step['expect_state']}"
    if "config4" in step and result["config"][4] != step["config4"]:
        return f"{side} config[4]={result['config'][4]} != {step['config4']}"
    for index, expected in step.get("work_values", {}).items():
        actual = struct.unpack_from("<I", result["work"], 0x28 + 4 * index)[0]
        if actual != expected:
            return f"{side} option[{index}]={actual} != expected {expected}"
    logical_expected = step.get("logical")
    if logical_expected:
        events = [call for call in result["trace"] if call[0] == "logical_query"]
        observed = {(int(call[1]), int(call[2])): int(call[3]) for call in events}
        for pair, value in logical_expected.items():
            if observed.get(pair) != value:
                return f"{side} logical service {pair} returned {observed.get(pair)}, expected {value}"
    if "exit_decision" in step:
        exits = [call for call in result["trace"] if call[0] == "exit_decision"]
        if exits != [["exit_decision", step["exit_decision"] & U32]]:
            return f"{side} state-2 exit decision trace {exits!r}"
    if "script_runner" in step:
        calls = [call for call in result["trace"] if call[0] == "script_runner"]
        if len(calls) != 1 or calls[0][-1] != step["script_runner"]:
            return f"{side} script-runner poll trace {calls!r}"
    for service, expected in step.get("service_results", {}).items():
        calls = [call for call in result["trace"] if call[0] == service]
        if not calls or calls[-1][-1] != expected:
            return f"{side} {service} trace {calls!r} did not end in {expected}"
    return None


def compare_tick(original: dict, patched: dict) -> str | None:
    for name, result in (("original", original), ("patched", patched)):
        if result["fault"]:
            return f"{name} fault: {result['fault']}"
        if not result["stopped"]:
            return f"{name} missed Calc return sentinel"
        if result["preserved"] != result["expected_preserved"]:
            return f"{name} violates callee-saved ABI"
        if result["image_sha256"] not in (EXPECTED_ORIGINAL_SHA256, EXPECTED_PATCHED_SHA256):
            return f"{name} image identity changed during sequence"
    for field in ("return", "pc", "preserved", "work", "config", "work_global", "config_global", "trace"):
        if original[field] != patched[field]:
            return f"{field} differs"
    return None


def run_sequence(original_image: bytes, patched_image: bytes, spec: dict) -> dict:
    initial = spec["steps"][0]["scenario"]
    original = PersistentCalc(original_image, initial, spec["seed"])
    patched = PersistentCalc(patched_image, initial, spec["seed"])
    rows = []
    for step in spec["steps"]:
        left = original.tick(step["scenario"])
        right = patched.tick(step["scenario"])
        expected_left = _assert_tick(left, step, "original")
        expected_right = _assert_tick(right, step, "patched")
        difference = compare_tick(left, right)
        rows.append({"tick": step["label"], "passed": not expected_left and not expected_right and not difference,
                     "expected_original": expected_left, "expected_patched": expected_right,
                     "difference": difference,
                     "artifact_sha256": {"original": left["image_sha256"],
                                          "patched": right["image_sha256"]},
                     "state": {"original": left["state"], "patched": right["state"]},
                     "return": {"original": hex(left["return"]), "patched": hex(right["return"])},
                     "pc": {"original": hex(left["pc"]), "patched": hex(right["pc"])},
                     "sp": {"original": hex(left["preserved"][8]), "patched": hex(right["preserved"][8])},
                     "fault": {"original": left["fault"], "patched": right["fault"]},
                     "preserved": {"original": [hex(value) for value in left["preserved"]],
                                   "patched": [hex(value) for value in right["preserved"]]},
                     "work": {"original": left["work"].hex(), "patched": right["work"].hex()},
                     "work_sha256": {"original": sha256_bytes(left["work"]), "patched": sha256_bytes(right["work"])},
                     "config": {"original": left["config"].hex(), "patched": right["config"].hex()},
                     "globals": {"work_global_original": left["work_global"].hex(),
                                 "work_global_patched": right["work_global"].hex(),
                                 "config_global_original": left["config_global"].hex(),
                                 "config_global_patched": right["config_global"].hex()},
                     "trace": {"original": left["trace"], "patched": right["trace"]}})
    return {"name": spec["label"], "seed": spec["seed"], "passed": all(row["passed"] for row in rows), "ticks": rows}


def run_wrong_logical_control(original_image: bytes, patched_image: bytes) -> dict:
    scenario_original = Scenario("negative-decrement", 1, row=0, values=(1, 2, 3), logical={(4, 0): 1})
    scenario_wrong = Scenario("wrong-map-to-increment", 1, row=0, values=(1, 2, 3), logical={(3, 0): 1})
    original = PersistentCalc(original_image, scenario_original, 17).tick(scenario_original)
    patched = PersistentCalc(patched_image, scenario_original, 17).tick(scenario_wrong)
    difference = compare_tick(original, patched)
    return {"name": "wrong-logical-map-4-0-to-3-0", "detected": difference is not None,
            "difference": difference,
            "original_state_value": struct.unpack_from("<I", original["work"], 0x28)[0],
            "mutant_state_value": struct.unpack_from("<I", patched["work"], 0x28)[0]}


def build_patched_image(
    original_image: bytes, output: Path, source_path: Path = SOURCE,
    symbol: str = SYMBOL, expected_size: int | None = None,
) -> tuple[bytes, dict]:
    source_path = source_path.resolve()
    obj_path = output / f"{source_path.stem}.o"
    from tools.build_check import compile_tu_armv6k
    from tools.asm_diff import extract_elf_functions_detailed
    build = compile_tu_armv6k(source_path, obj_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K Calc candidate compilation failed")
    symbols = extract_elf_functions_detailed(obj_path)
    if symbol not in symbols:
        raise ValueError(f"Calc symbol missing from object: {symbol}")
    body, relocs = symbols[symbol]
    section_offset = elf_function_section_offset(obj_path, symbol)
    body = normalize_local_text_addends(body, relocs, section_offset)
    if expected_size is not None and len(body) != expected_size:
        raise ValueError(f"Calc symbol size changed: expected {expected_size}, got {len(body)}")
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    patched, ips, manifest = build_patch(original_image, body, relocs, game)
    if sha256_bytes(patched) != EXPECTED_PATCHED_SHA256:
        raise ValueError("final-address patched artifact hash differs from reviewed artifact")
    return patched, {"compile_exit": build.returncode, "compile_command": build.args,
                     "source_path": str(source_path),
                     "source_sha256": sha256_bytes(source_path.read_bytes()),
                     "object_sha256": sha256_bytes(obj_path.read_bytes()),
                     "symbol": symbol, "symbol_size": len(body),
                     "symbol_section_offset": hex(section_offset),
                     "patched_sha256": sha256_bytes(patched),
                     "ips_sha256": sha256_bytes(ips), "patch_manifest": manifest}


def experiment(
    code_path: Path, output: Path, seeds: list[int], source_path: Path = SOURCE,
    symbol: str = SYMBOL, expected_size: int | None = None,
) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    original_image = code_path.read_bytes()
    if sha256_bytes(original_image) != EXPECTED_ORIGINAL_SHA256:
        raise ValueError("--code must be the frozen pinned original code.bin")
    patched_image, build = build_patched_image(
        original_image, output, source_path, symbol, expected_size
    )
    original_hash, patched_hash = sha256_bytes(original_image), sha256_bytes(patched_image)
    sequences = []
    for seed in seeds:
        for spec in sequence_specs(seed):
            sequences.append(run_sequence(original_image, patched_image, spec))
    negative = run_wrong_logical_control(original_image, patched_image)
    passed = all(seq["passed"] for seq in sequences) and negative["detected"]
    report = {
        "schema": 1, "passed": passed,
        "scope": "persistent offline Calc callback sequences using the pinned original and reviewed final-address patched image",
        "reference_sha256": original_hash, "patched_sha256": patched_hash,
        "source_sha256": build["source_sha256"],
        "source_path": build["source_path"], "object_sha256": build["object_sha256"],
        "symbol": build["symbol"], "symbol_size": build["symbol_size"],
        "symbol_section_offset": build["symbol_section_offset"],
        "runner_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "test_sha256": sha256_bytes((ROOT / "tests/test_h2_calc_sequence_experiment.py").read_bytes()),
        "build": build, "seed_passes": seeds,
        "sequence_count": len(sequences), "sequences_passed": sum(s["passed"] for s in sequences),
        "tick_count": sum(len(s["ticks"]) for s in sequences),
        "ticks_passed": sum(row["passed"] for s in sequences for row in s["ticks"]),
        "negative_control": negative, "sequences": sequences,
        "evidence": {"compiled": "passed", "arm_differential": "passed" if passed else "failed",
                     "caller": "partial", "runtime": "not_run"},
        "limits": [
            "The same explicit service responses are harness controls; logical query return values do not establish physical input mappings.",
            "Cursor, touch, resource, script/task, render, audio, animation, and state-decision services remain at HLE boundaries; original mapper and encoder helper bodies still execute from the pinned image.",
            "The runner calls Calc persistently in its own Unicorn callback harness, not through the title initializer/caller scheduler. It does not establish visible UI, persistence, profile behavior, Azahar, RSP, keyboard/mouse, or whole-game behavior.",
            "No state-2 decision is labeled confirm or cancel. Helper return domains, malformed cursor/work layouts, and out-of-domain values remain unresolved."
        ],
        "elapsed_seconds": round(time.perf_counter() - started, 3)
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "patched-image.bin").write_bytes(patched_image)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=CODE_DEFAULT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[7, 20261024])
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--symbol", default=SYMBOL)
    parser.add_argument("--expected-size", type=int)
    args = parser.parse_args(argv)
    report = experiment(args.code, args.output, args.seeds, args.source,
                        args.symbol, args.expected_size)
    print(json.dumps({"passed": report["passed"], "sequences": report["sequences_passed"],
                      "ticks": report["ticks_passed"], "negative_control": report["negative_control"],
                      "report": str(args.output / "report.json")}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
