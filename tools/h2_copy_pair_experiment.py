#!/usr/bin/env python3
"""Differentially validate UiConfig_CopyPair on aligned ordinary RAM."""
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
    STACK_SIZE,
    Case,
    Runner,
    difference,
    validate_leaf,
)

ADDRESS = 0x002ADB40
SOURCE = ROOT / "experiments/semantic_equivalence/h2_copy_pair_candidate.cpp"
CODE_DEFAULT = ROOT / "extracted/exefs/code.bin"
BASE = DATA + 0x400

LAYOUTS = {
    "same-pointer": (0, 0),
    "destination-after-source-overlap": (1, 0),
    "destination-before-source-overlap": (0, 1),
    "adjacent-destination-after-source": (2, 0),
    "adjacent-destination-before-source": (0, 2),
    "disjoint": (0, 5),
}
PATTERNS = (
    (0, 0, 0, 0, 0, 0, 0, 0),
    (0xFFFFFFFF,) * 8,
    (0x11223344, 0x55667788, 0x99AABBCC, 0xDDEEFF00,
     0x01020304, 0xA5A5A5A5, 0x5A5A5A5A, 0xCAFEBABE),
    (0x80000000, 0x7FFFFFFF, 0x00000001, 0xFFFFFFFE,
     0x40000000, 0xC0000000, 0x0000FFFF, 0xFFFF0000),
    (0xAAAAAAAA, 0x55555555, 0xAAAAAAAA, 0x55555555,
     0xAAAAAAAA, 0x55555555, 0xAAAAAAAA, 0x55555555),
    (0x01020304, 0x05060708, 0x09101112, 0x13141516,
     0x17181920, 0x21222324, 0x25262728, 0x29303132),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cases(seed: int, samples: int):
    if samples < 0:
        raise ValueError("samples must be nonnegative")
    rng = random.Random(seed)
    for layout, offsets in LAYOUTS.items():
        for pattern_index, words in enumerate(PATTERNS):
            yield f"directed-{layout}-pattern-{pattern_index}", layout, offsets, words
    layout_items = tuple(LAYOUTS.items())
    for index in range(samples):
        layout, offsets = rng.choice(layout_items)
        words = tuple(rng.getrandbits(32) for _ in range(8))
        yield f"seeded-{index}-{layout}", layout, offsets, words


def make_case(label: str, offsets: tuple[int, int], words: tuple[int, ...],
              rng: random.Random) -> Case:
    import struct

    registers = [rng.getrandbits(32) for _ in range(13)]
    destination_offset, source_offset = offsets
    registers[0] = BASE + destination_offset * 4
    registers[1] = BASE + source_offset * 4
    data = bytearray(rng.randbytes(DATA_SIZE))
    struct.pack_into("<8I", data, BASE - DATA, *words)
    return Case(label, tuple(registers), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def run_experiment(code_path: Path, output: Path, seed: int, samples: int) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    code_path = code_path.resolve()
    image = code_path.read_bytes()
    image_hash = sha256(code_path)
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    if len(image) != game["code_bin_size"] or image_hash != game["code_sha256"]:
        raise ValueError("Private code.bin does not match configured US revision")

    source_hash = sha256(SOURCE)
    obj_path = output / "h2_copy_pair_candidate.o"
    compilation = compile_tu_armv6k(SOURCE, obj_path, ROOT)
    if compilation.returncode:
        raise RuntimeError(compilation.stderr or "ARMv6K candidate compilation failed")
    compiled = extract_elf_functions_detailed(obj_path)
    required = ("candidate_002adb40", "candidate_002adb40_wrong_forward")
    for name in required:
        if name not in compiled:
            raise RuntimeError(f"Missing compiled symbol {name}")
        body, relocations = compiled[name]
        if relocations:
            raise ValueError(f"Unexpected relocation in {name}: {relocations}")
        validate_leaf(body)

    original = Runner(image, ADDRESS)
    rebuilt = Runner(image, ADDRESS, compiled[required[0]][0])
    rng = random.Random(seed ^ ADDRESS)
    count = 0
    first_counterexample = None
    observed_reads: set[int] = set()
    observed_writes: set[int] = set()
    candidate_reads: set[int] = set()
    candidate_writes: set[int] = set()
    case_list = list(cases(seed, samples))
    for label, _layout, offsets, words in case_list:
        case = make_case(label, offsets, words, rng)
        left = original.run(case)
        right = rebuilt.run(case)
        observed_reads.update(left.reads)
        observed_writes.update(left.writes)
        candidate_reads.update(right.reads)
        candidate_writes.update(right.writes)
        error = difference(left, right, returns_value=True)
        if error:
            first_counterexample = {"case": label, "source_words": [f"0x{x:08X}" for x in words[:2]],
                                    "destination_word_offset": offsets[0],
                                    "source_word_offset": offsets[1], "error": error}
            break
        count += 1

    # A sequential forward copy must fail when dst=src+1: its first store
    # overwrites the second source word before that word is loaded.
    bad_layout = "destination-after-source-overlap"
    bad_offsets = LAYOUTS[bad_layout]
    bad_words = PATTERNS[2]
    negative_rng = random.Random(seed ^ 0xBADF00D)
    negative_case = make_case("wrong-forward-overlap", bad_offsets, bad_words, negative_rng)
    negative_original = Runner(image, ADDRESS)
    negative_wrong = Runner(image, ADDRESS, compiled[required[1]][0])
    negative_error = difference(negative_original.run(negative_case),
                                negative_wrong.run(negative_case), returns_value=True)

    if sha256(SOURCE) != source_hash:
        raise RuntimeError("Candidate source changed during experiment")
    report = {
        "schema": 1,
        "passed": first_counterexample is None and negative_error == "data memory differs",
        "scope": "UiConfig_CopyPair / 0x002ADB40 isolated helper",
        "reference_sha256": image_hash,
        "reference_bytes": len(image),
        "source_sha256": source_hash,
        "object_sha256": sha256(obj_path),
        "compiler": subprocess_version(find_clang()),
        "compile_command": compilation.args,
        "compile_exit": compilation.returncode,
        "seed": seed,
        "seeded_cases": samples,
        "directed_layouts": list(LAYOUTS),
        "directed_patterns_per_layout": len(PATTERNS),
        "case_count": len(case_list),
        "cases_passed": count,
        "first_counterexample": first_counterexample,
        "negative_control": {
            "name": "candidate_002adb40_wrong_forward",
            "case": "destination-after-source-overlap with distinct source words",
            "detected": negative_error == "data memory differs",
            "difference": negative_error,
        },
        "observed_accesses": {
            "original_data_read_byte_count_union": len(observed_reads),
            "original_data_write_byte_count_union": len(observed_writes),
            "original_data_read_addresses": [hex(x) for x in sorted(observed_reads)],
            "original_data_write_addresses": [hex(x) for x in sorted(observed_writes)],
            "candidate_data_read_byte_count_union": len(candidate_reads),
            "candidate_data_write_byte_count_union": len(candidate_writes),
            "candidate_data_read_addresses": [hex(x) for x in sorted(candidate_reads)],
            "candidate_data_write_addresses": [hex(x) for x in sorted(candidate_writes)],
        },
        "limits": [
            "Supported pointers are non-null, four-byte aligned, and each covers two valid u32 words in ordinary writable RAM.",
            "Tests same pointer, one-word overlap in either direction, adjacent disjoint regions, and disjoint regions; both words are loaded before either store.",
            "No null, unaligned, invalid, MMIO, concurrent-observer, or inaccessible-memory behavior is claimed.",
            "No caller window, initializer composition, UI, persistence, patch integration, or game runtime was tested.",
        ],
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def subprocess_version(clang: Path) -> str:
    import subprocess
    result = subprocess.run([str(clang), "--version"], capture_output=True, text=True, check=True)
    return result.stdout.splitlines()[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=CODE_DEFAULT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--samples", type=int, default=512)
    args = parser.parse_args()
    report = run_experiment(args.code, args.output, args.seed, args.samples)
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
