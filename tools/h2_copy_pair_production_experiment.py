#!/usr/bin/env python3
"""Differentially validate the typed production UiConfig_CopyPair wrapper."""
from __future__ import annotations

import argparse
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
    DATA, DATA_SIZE, STACK, STACK_SIZE, Case, Runner, difference,
)

ADDRESS = 0x002ADB40
SOURCE = ROOT / "src/engine/leaf_matching.cpp"
NEGATIVE_SOURCE = ROOT / "experiments/semantic_equivalence/h2_copy_pair_candidate.cpp"
CODE = ROOT / "extracted/exefs/code.bin"
H2_CONFIG = 0x0044E0F8
ERROR_STRING = 0x004656F1
BASE = DATA + 0x400


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _case(label: str, destination: int, source: int, words: tuple[int, int],
          rng: random.Random, *, stack_destination: bool = False) -> Case:
    data = bytearray(rng.randbytes(DATA_SIZE))
    if DATA <= source < DATA + DATA_SIZE:
        struct.pack_into("<II", data, source - DATA, *words)
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0], regs[1] = destination, source
    return Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def directed_cases(rng: random.Random):
    words = (0x11223344, 0x55667788)
    for destination_offset in range(4):
        for source_offset in range(4):
            yield _case(
                f"alignment-dst-{destination_offset}-src-{source_offset}",
                BASE + destination_offset, BASE + 0x80 + source_offset,
                words, rng,
            )
    for delta in range(-7, 8):
        source_offset = 0x100
        destination_offset = source_offset + delta
        yield _case(
            f"overlap-byte-delta-{delta:+d}", BASE + destination_offset,
            BASE + source_offset, (0xA1B2C3D4, 0x55667788), rng,
        )
    yield _case("h2-config-global-source", BASE + 0x200, H2_CONFIG,
                words, rng)
    yield _case("readonly-odd-error-string", STACK + 0x100, ERROR_STRING,
                words, rng)


def seeded_cases(seed: int, count: int, rng: random.Random):
    local = random.Random(seed)
    for index in range(count):
        source_offset = local.randrange(0x300, 0x500)
        delta = local.randrange(-7, 8)
        destination_offset = source_offset + delta
        words = (local.getrandbits(32), local.getrandbits(32))
        yield _case(
            f"seeded-{index}-delta-{delta:+d}", BASE + destination_offset,
            BASE + source_offset, words, rng,
        )


def run(output: Path, seed: int = 7, samples: int = 512) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    image = CODE.read_bytes()
    image_hash = sha256(image)
    source_hash = sha256(SOURCE.read_bytes())
    production_obj = output / "leaf_matching.production.o"
    result = compile_tu_armv6k(SOURCE, production_obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "production TU compilation failed")
    production = extract_elf_functions_detailed(production_obj)
    candidate, relocations = production["ui_func_002adb40"]
    original_body = image[ADDRESS - 0x00100000:ADDRESS - 0x00100000 + 20]
    if relocations:
        raise ValueError(f"production CopyPair has relocations: {relocations}")
    if len(candidate) != 20:
        raise ValueError(f"production CopyPair escaped its 20-byte slot: {len(candidate)}")

    negative_obj = output / "h2_copy_pair_experiment.o"
    negative_result = compile_tu_armv6k(NEGATIVE_SOURCE, negative_obj, ROOT)
    if negative_result.returncode:
        raise RuntimeError(negative_result.stderr or "negative-control compile failed")
    negative_symbols = extract_elf_functions_detailed(negative_obj)
    wrong, wrong_relocations = negative_symbols["candidate_002adb40_wrong_forward"]
    if wrong_relocations:
        raise ValueError(f"wrong-copy negative control has relocations: {wrong_relocations}")

    original_runner = Runner(image, ADDRESS)
    candidate_runner = Runner(image, ADDRESS, candidate)
    rng = random.Random(seed ^ ADDRESS)
    cases = list(directed_cases(rng))
    cases.extend(seeded_cases(seed, samples, rng))
    first = None
    passed = 0
    for case in cases:
        expected = original_runner.run(case)
        actual = candidate_runner.run(case)
        reason = difference(expected, actual, returns_value=True)
        if reason:
            first = {"case": case.label, "difference": reason,
                     "destination": hex(case.registers[0]),
                     "source": hex(case.registers[1])}
            break
        passed += 1

    negative_case = _case(
        "wrong-forward-overlap", BASE + 4, BASE,
        (0x11223344, 0x55667788), random.Random(seed ^ 0xBADF00D),
    )
    negative_difference = difference(
        original_runner.run(negative_case),
        Runner(image, ADDRESS, wrong).run(negative_case),
        returns_value=True,
    )
    report = {
        "schema": 1,
        "scope": "production UiConfig_CopyPair at 0x002ADB40",
        "reference_sha256": image_hash,
        "source_sha256": source_hash,
        "production_object_sha256": sha256(production_obj.read_bytes()),
        "negative_source_sha256": sha256(NEGATIVE_SOURCE.read_bytes()),
        "negative_object_sha256": sha256(negative_obj.read_bytes()),
        "compile_command": result.args,
        "body_bytes": len(candidate),
        "body_hex": candidate.hex(),
        "body_equals_pinned_original": candidate == original_body,
        "seed": seed,
        "seeded_cases": samples,
        "directed_cases": len(cases) - samples,
        "cases_expected": len(cases),
        "cases_passed": passed,
        "first_counterexample": first,
        "directed_domains": [
            "all source/destination alignments modulo four",
            "byte-overlap deltas from -7 through +7",
            "the H2 g_ConfigBytes source address",
            "the actual odd read-only ERROR string source address",
        ],
        "negative_control": {
            "name": "candidate_002adb40_wrong_forward",
            "difference": negative_difference,
            "detected": negative_difference == "data memory differs",
        },
        "passed": (first is None and passed == len(cases)
                   and len(candidate) == 20 and candidate == original_body
                   and negative_difference == "data memory differs"),
        "limits": [
            "Inline ARM LDR/STR operations preserve the original target-specific ordinary-memory behavior for unaligned addresses; this does not claim MMIO or fault equivalence.",
            "Dynamic caller object extents and lifetimes are not established by this helper differential.",
            "The original and candidate helper runs do not validate UI, persistence, restart, or Azahar runtime behavior.",
        ],
    }
    if sha256(SOURCE.read_bytes()) != source_hash:
        raise RuntimeError("production source changed during differential run")
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--samples", type=int, default=512)
    args = parser.parse_args()
    result = run(args.output.resolve(), args.seed, args.samples)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
