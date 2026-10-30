#!/usr/bin/env python3
"""Differentially test titleConfig's two-word replicated-byte fill helper."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang
from tools.semantic_experiment import (
    DATA,
    DATA_SIZE,
    RETURN,
    SP,
    STACK,
    STACK_SIZE,
    Case,
    Runner,
    difference,
    validate_local_blob,
)

ADDRESS = 0x0027EDF8
SOURCE = ROOT / "experiments/semantic_equivalence/h2_pair_fill_candidate.cpp"
CODE_DEFAULT = ROOT / "extracted/exefs/code.bin"
DESTINATION = DATA + 0x200


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cases(seed: int, samples: int):
    rng = random.Random(seed)
    cases = []
    high_parts = (0, 0x00000100, 0xA5A50000, 0xFFFFFF00)
    for low in range(256):
        for high in high_parts:
            value = (low | high) & 0xFFFFFFFF
            label = f"low-{low:02x}-high-{high:08x}"
            cases.append((label, value))
    for index in range(samples):
        value = rng.getrandbits(32)
        cases.append((f"seeded-{index}", value))
    return cases


def make_case(label: str, value: int, rng: random.Random) -> Case:
    registers = [rng.getrandbits(32) for _ in range(13)]
    registers[0] = DESTINATION
    registers[1] = value
    return Case(label, tuple(registers), rng.randbytes(DATA_SIZE),
                rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def run_experiment(code_path: Path, output: Path, seed: int, samples: int) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    code_path = code_path.resolve()
    image = code_path.read_bytes()
    obj_path = output / "h2_pair_fill_candidate.o"
    compilation = compile_tu_armv6k(SOURCE, obj_path, ROOT)
    if compilation.returncode:
        raise RuntimeError(compilation.stderr or "ARMv6K candidate compilation failed")
    symbols = extract_elf_functions_detailed(obj_path)
    for required in ("candidate_0027edf8", "candidate_0027edf8_wrong_one_word"):
        if required not in symbols:
            raise RuntimeError(f"Missing compiled symbol {required}")
        body, relocations = symbols[required]
        if relocations:
            raise RuntimeError(f"Unexpected relocation in {required}: {relocations}")

    candidate_code = symbols["candidate_0027edf8"][0]
    wrong_code = symbols["candidate_0027edf8_wrong_one_word"][0]
    original = Runner(image, ADDRESS)
    rebuilt = Runner(image, ADDRESS, candidate_code,
                     replacement_validator=validate_local_blob)
    wrong = Runner(image, ADDRESS, wrong_code,
                   replacement_validator=validate_local_blob)
    rng = random.Random(seed ^ ADDRESS)
    count = 0
    first_counterexample = None
    for label, value in cases(seed, samples):
        case = make_case(label, value, rng)
        error = difference(original.run(case), rebuilt.run(case), returns_value=False)
        if error:
            first_counterexample = {"case": label, "input": f"0x{value:08X}", "error": error}
            break
        count += 1

    negative_label = "low-00-high-00000000"
    negative_rng = random.Random(seed ^ 0xBADF00D)
    negative_case = make_case(negative_label, 0, negative_rng)
    negative_error = difference(original.run(negative_case), wrong.run(negative_case),
                                returns_value=False)
    report = {
        "schema": 1,
        "passed": first_counterexample is None and negative_error is not None,
        "scope": "UiConfig_FillPair / 0x0027EDF8 isolated helper",
        "reference_sha256": json.loads((ROOT / "config/game_info.json").read_text())[
            "code_sha256"],
        "image_sha256": sha256(code_path),
        "source_sha256": sha256(SOURCE),
        "object_sha256": sha256(obj_path),
        "compiler": find_clang().as_posix(),
        "compile_command": compilation.args,
        "compile_exit": compilation.returncode,
        "seed": seed,
        "seeded_cases": samples,
        "case_count": len(cases(seed, samples)),
        "cases_passed": count,
        "first_counterexample": first_counterexample,
        "negative_control": {
            "name": "candidate_0027edf8_wrong_one_word",
            "case": negative_label,
            "detected": negative_error is not None,
            "difference": negative_error,
        },
        "limits": [
            "Tests ordinary writable RAM with an aligned two-word destination.",
            "Does not establish complete titleConfig initializer or caller behavior.",
        ],
        "elapsed_seconds": round(time.time() - started, 3),
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=CODE_DEFAULT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--samples", type=int, default=256)
    args = parser.parse_args()
    report = run_experiment(args.code, args.output, args.seed, args.samples)
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
