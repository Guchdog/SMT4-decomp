#!/usr/bin/env python3
"""Differentially test only EffPolygonThunder's point-count normalization."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import (
    DATA, DATA_SIZE, INJECT, STACK_SIZE, SP, STACK, Case, Runner, U32_MASK,
    unicorn,
)

WINDOWS = (
    {
        "address": 0x0031596C,
        "start": 0x003159DC,
        "stop": 0x003159F4,
        "stack_object_offset": 0x60,
        "candidate": "candidate_thunder_min3",
        "control": "candidate_wrong_min2",
        "oddify": False,
    },
    {
        "address": 0x0032170C,
        "start": 0x00321764,
        "stop": 0x0032177C,
        "stack_object_offset": 0x60,
        "candidate": "candidate_thunder_min3",
        "control": "candidate_wrong_min2",
        "oddify": False,
    },
    {
        "address": 0x00327D90,
        "start": 0x00327DEC,
        "stop": 0x00327E18,
        "stack_object_offset": 0x68,
        "candidate": "candidate_thunder_min3_odd",
        "control": "candidate_wrong_no_odd",
        "oddify": True,
    },
)
OBJECT_OFFSET = 0x100
POINTS_OFFSET = 0x3C


def _inputs(samples: int, seed: int):
    rng = random.Random(seed)
    counts = list(range(512))
    counts += [0x7FFFFFFF, 0x80000000, 0xFFFFFFFC, 0xFFFFFFFD,
               0xFFFFFFFE, U32_MASK]
    counts += [rng.getrandbits(32) for _ in range(samples)]
    for index, count in enumerate(counts):
        data = bytearray(rng.randbytes(DATA_SIZE))
        struct.pack_into("<I", data, OBJECT_OFFSET + POINTS_OFFSET, count)
        stack = bytearray(rng.randbytes(STACK_SIZE))
        for window in WINDOWS:
            # The ARM runner places SP at STACK + 0x1000, not at the base
            # of its mapped stack page.
            struct.pack_into("<I", stack, 0x1000 + window["stack_object_offset"],
                             DATA + OBJECT_OFFSET)
        regs = tuple(rng.getrandbits(32) for _ in range(13))
        yield index, count, Case(
            f"point-count-{count:08x}", regs, bytes(data), bytes(stack),
            rng.getrandbits(4) << 28,
        )


def _build_candidates(output: Path) -> dict[str, bytes]:
    source = ROOT / "experiments/semantic_equivalence/eff_polygon_thunder_prefix_candidates.cpp"
    output.mkdir(parents=True, exist_ok=True)
    obj = output / "eff_polygon_thunder_prefix_candidates.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    functions = extract_elf_functions_detailed(obj)
    if not functions:
        raise RuntimeError("No candidate functions were extracted from the ARM object")
    for name, (_, relocations) in functions.items():
        if relocations:
            raise ValueError(f"Unsupported relocation in {name}: {relocations}")
    return {name: code for name, (code, _) in functions.items()}


def _field(data: bytes | bytearray) -> int:
    return struct.unpack_from("<I", data, OBJECT_OFFSET + POINTS_OFFSET)[0]


def _expected(count: int, oddify: bool) -> int:
    result = max(count, 3)
    if oddify and result % 2 == 0:
        result += 1
    return result & U32_MASK


def _run_one_window(image: bytes, window: dict, code: bytes,
                    cases, *, label: str) -> dict:
    original = Runner(image, window["address"])
    candidate = Runner(image, window["address"], replacement=code)
    count = 0
    for _, input_count, case in cases:
        arm_result = original.run(case, start=window["start"],
                                  stops=(window["stop"],), budget=64)
        candidate_regs = list(case.registers)
        candidate_regs[0] = DATA + OBJECT_OFFSET
        candidate_case = Case(case.label, tuple(candidate_regs), case.data,
                              case.stack, case.nzcv)
        cpp_result = candidate.run(candidate_case, budget=128)
        if arm_result.fault or not arm_result.stopped or arm_result.pc != window["stop"]:
            raise AssertionError(
                f"{label} original prefix failed at {arm_result.pc:#x}: {arm_result.fault}"
            )
        if cpp_result.fault or not cpp_result.stopped:
            raise AssertionError(f"{label} C++ candidate failed: {cpp_result.fault}")
        arm_value = _field(arm_result.data)
        cpp_value = _field(cpp_result.data)
        expected = _expected(input_count, window["oddify"])
        if arm_value != expected:
            raise AssertionError(
                f"{label} ARM result for {input_count:#x}: {arm_value:#x} != {expected:#x}"
            )
        if cpp_value != arm_value:
            raise AssertionError(
                f"{label} differential mismatch for {input_count:#x}: "
                f"ARM {arm_value:#x}, C++ {cpp_value:#x}"
            )
        if arm_result.writes != cpp_result.writes:
            raise AssertionError(f"{label} write footprint differs for {input_count:#x}")
        allowed = set(range(DATA + OBJECT_OFFSET + POINTS_OFFSET,
                            DATA + OBJECT_OFFSET + POINTS_OFFSET + 4))
        if arm_result.writes != allowed:
            raise AssertionError(f"{label} wrote outside the point-count field")
        count += 1
    return {"address": hex(window["address"]), "name": label,
            "start": hex(window["start"]), "stop": hex(window["stop"]),
            "candidate": window["candidate"], "cases": count, "passed": True,
            "observable": "final object+0x3C and byte write footprint only"}


def run(code_path: Path, output: Path, samples: int = 512,
        seed: int = 20261024) -> dict:
    if unicorn is None:
        raise RuntimeError("Unicorn is required for the focused differential experiment")
    if samples < 0:
        raise ValueError("samples must be nonnegative")
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(image).hexdigest()
    if len(image) != game["code_bin_size"] or digest != game["code_sha256"]:
        raise ValueError("code.bin does not match the configured US revision")
    candidates = _build_candidates(output)
    all_cases = list(_inputs(samples, seed))
    results = []
    for window in WINDOWS:
        symbol = window["candidate"]
        if symbol not in candidates:
            raise KeyError(f"candidate symbol not found: {symbol}")
        results.append(_run_one_window(image, window, candidates[symbol],
                                       all_cases, label=symbol))

    controls = []
    for window in WINDOWS:
        symbol = window["control"]
        if symbol not in candidates:
            raise KeyError(f"negative-control symbol not found: {symbol}")
        control = Runner(image, window["address"], replacement=candidates[symbol])
        original = Runner(image, window["address"])
        target_count = 4 if window["oddify"] else 0
        case = next(item[2] for item in all_cases if item[1] == target_count)
        regs = list(case.registers)
        regs[0] = DATA + OBJECT_OFFSET
        mutant_case = Case(case.label, tuple(regs), case.data, case.stack, case.nzcv)
        arm_result = original.run(case, start=window["start"],
                                  stops=(window["stop"],), budget=64)
        mutant_result = control.run(mutant_case, budget=128)
        detected = _field(arm_result.data) != _field(mutant_result.data)
        controls.append({"address": hex(window["address"]), "name": symbol,
                         "detected": detected, "expected": hex(_field(arm_result.data)),
                         "mutant": hex(_field(mutant_result.data))})
        if not detected:
            raise AssertionError(f"negative control was not detected: {symbol}")

    return {"schema": 1, "passed": all(row["passed"] for row in results)
            and all(row["detected"] for row in controls),
            "scope": "three pre-geometry point-count prefixes only; no full constructor equivalence",
            "reference_sha256": digest, "seed": seed, "samples_per_window": len(all_cases),
            "results": results, "negative_controls": controls}
