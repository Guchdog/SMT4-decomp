#!/usr/bin/env python3
"""Differentially test three constant-offset ARM leaf reconstructions."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang
from tools.semantic_experiment import (
    DATA,
    DATA_SIZE,
    STACK_SIZE,
    TEXT,
    U32_MASK,
    Case,
    Runner,
    difference,
    require_unicorn,
    validate_leaf,
)


@dataclass(frozen=True)
class OffsetFunction:
    address: int
    first_offset: int
    second_offset: int

    @property
    def offset(self) -> int:
        return (self.first_offset + self.second_offset) & U32_MASK

    @property
    def symbol(self) -> str:
        return f"candidate_{self.address:08x}"

    @property
    def negative_symbol(self) -> str:
        return f"negative_candidate_{self.address:08x}"


FUNCTIONS = (
    OffsetFunction(0x00343550, 0x400, 0x1B4),
    OffsetFunction(0x00343584, 0xC00, 0x4),
    OffsetFunction(0x00343590, 0x400, 0x2FC),
)


def verify_reference(image: bytes, expected_sha256: str, ledger: list[dict]) -> None:
    if hashlib.sha256(image).hexdigest() != expected_sha256:
        raise ValueError("Private code.bin SHA-256 does not match the configured revision")
    by_address = {int(row["address"], 16): row for row in ledger}
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    for function in FUNCTIONS:
        row = by_address.get(function.address)
        if row is None or int(row["size"]) != 12:
            raise ValueError(f"Missing or changed ledger entry at {function.address:#010x}")
        start = function.address - TEXT
        original = image[start:start + 12]
        instructions = list(decoder.disasm(original, function.address))
        actual = tuple((item.mnemonic, item.op_str) for item in instructions)
        immediate = lambda value: f"#{value}" if value < 10 else f"#0x{value:x}"
        expected = (
            ("add", f"r0, r0, {immediate(function.first_offset)}"),
            ("add", f"r0, r0, {immediate(function.second_offset)}"),
            ("bx", "lr"),
        )
        if len(instructions) != 3 or sum(item.size for item in instructions) != 12:
            raise ValueError(f"Incomplete ARM body at {function.address:#010x}")
        if actual != expected:
            raise ValueError(
                f"Original instruction shape changed at {function.address:#010x}: {actual}"
            )


def make_cases(function: OffsetFunction, samples: int, seed: int):
    rng = random.Random(seed ^ function.address)
    boundary_values = (
        0,
        1,
        U32_MASK,
        (U32_MASK - function.offset) & U32_MASK,
        (U32_MASK - function.offset + 1) & U32_MASK,
        (U32_MASK - function.offset - 1) & U32_MASK,
        0x7FFFFFFF,
        0x80000000,
    )
    for index in range(len(boundary_values) + samples):
        registers = [rng.getrandbits(32) for _ in range(13)]
        registers[0] = (
            boundary_values[index]
            if index < len(boundary_values)
            else rng.getrandbits(32)
        )
        yield Case(
            f"boundary-{index}" if index < len(boundary_values) else f"random-{index - len(boundary_values)}",
            tuple(registers),
            rng.randbytes(DATA_SIZE),
            rng.randbytes(STACK_SIZE),
            rng.getrandbits(4) << 28,
        )


def run(code_path: Path, output: Path, samples: int = 64, seed: int = 20261024):
    require_unicorn()
    if samples < 0:
        raise ValueError("samples must be nonnegative")
    started = time.perf_counter()
    image = Path(code_path).read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        ledger = list(csv.DictReader(stream))
    verify_reference(image, game["code_sha256"], ledger)
    source = ROOT / "experiments/semantic_equivalence/scalar_offset_candidates.cpp"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    obj = output / "scalar_offset_candidates.o"
    build = compile_tu_armv6k(source, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    compiled = extract_elf_functions_detailed(obj)
    for symbol, (code, relocations) in compiled.items():
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        validate_leaf(code)

    results = []
    for function in FUNCTIONS:
        original_code = image[function.address - TEXT:function.address - TEXT + 12]
        original = Runner(image, function.address)
        rebuilt = Runner(image, function.address, compiled[function.symbol][0])
        comparisons = []
        for case in make_cases(function, samples, seed):
            outcome = difference(
                original.run(case), rebuilt.run(case), compare_flags=True
            )
            if outcome:
                comparisons.append({"label": case.label, "reason": outcome})
                break
            comparisons.append({"label": case.label, "passed": True})
        results.append({
            "address": hex(function.address),
            "offset": hex(function.offset),
            "original_bytes": len(original_code),
            "candidate_bytes": len(compiled[function.symbol][0]),
            "byte_identical": original_code == compiled[function.symbol][0],
            "passed": all(item.get("passed") for item in comparisons),
            "cases": len(comparisons),
            "failure": next((item for item in comparisons if not item.get("passed")), None),
        })

    controls = []
    for function in FUNCTIONS:
        case = next(make_cases(function, 0, seed))
        original = Runner(image, function.address)
        wrong = Runner(image, function.address, compiled[function.negative_symbol][0])
        reason = difference(original.run(case), wrong.run(case), compare_flags=True)
        controls.append({
            "name": function.negative_symbol,
            "target": hex(function.address),
            "detected": reason == "return value differs",
            "reason": reason,
        })

    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Candidate source changed during experiment")
    compiler = subprocess.run(
        [str(find_clang()), "--version"], capture_output=True, text=True, check=True
    ).stdout.splitlines()[0]
    report = {
        "passed": all(item["passed"] for item in results)
        and all(item["detected"] for item in controls),
        "scope": "three isolated constant-offset getter leaves; no IPS or game integration",
        "reference_sha256": game["code_sha256"],
        "source_sha256": source_hash,
        "compiler": compiler,
        "seed": seed,
        "random_samples_per_function": samples,
        "functions": results,
        "negative_controls": controls,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "limitations": [
            "Differential cases are bounded evidence, not a formal proof",
            "Caller windows are not included; tests compare return, NZCV, ABI state, RAM, and footprints",
            "No production source, ledger, game image, patch, emulator, or save data is changed",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Scalar offset experiment {'PASS' if report['passed'] else 'FAIL'}; report: {output / 'report.json'}")
    return report


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, default=ROOT / "build/semantic-equivalence/scalar-offsets")
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    try:
        report = run(args.code, args.output, args.samples, args.seed)
    except (RuntimeError, ValueError, OSError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
