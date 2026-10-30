#!/usr/bin/env python3
"""Differentially validate production UiConfig_FillPair ARM code."""
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
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, Case, Runner, difference,
)

ADDRESS = 0x0027EDF8
SOURCE = ROOT / "src/engine/leaf_matching.cpp"
CODE = ROOT / "extracted/exefs/code.bin"
HIGH_PATTERNS = (0, 0x00000100, 0xABCD0000, 0xFFFFFF00)
WRONG_SOURCE = '''
using u8 = unsigned char;
using u32 = unsigned int;
extern "C" void wrong_fill_pair(u8* p, u32 value) {
    u32 repeated = value & 0xFFFFu;
    asm volatile("" : "+r"(repeated));
    repeated |= repeated << 8;
    asm volatile("" : "+r"(repeated));
    repeated |= repeated << 16;
    asm volatile("" : "+r"(repeated));
    asm volatile("str %1, [%0]\\nstr %1, [%0, #4]"
                 : : "r"(p), "r"(repeated) : "memory");
}
'''


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(output: Path, seed: int = 7) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    image = CODE.read_bytes()
    image_hash = sha256(image)
    source_hash = sha256(SOURCE.read_bytes())
    candidate_obj = output / "leaf_matching.production.o"
    result = compile_tu_armv6k(SOURCE, candidate_obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "production TU compilation failed")
    symbols = extract_elf_functions_detailed(candidate_obj)
    candidate, relocations = symbols["camp_func_0027edf8"]
    if relocations:
        raise ValueError(f"production candidate has relocations: {relocations}")

    wrong_source = output / "wrong_fill_pair.cpp"
    wrong_source.write_text(WRONG_SOURCE, encoding="utf-8")
    wrong_obj = output / "wrong_fill_pair.o"
    wrong_result = compile_tu_armv6k(wrong_source, wrong_obj, ROOT)
    if wrong_result.returncode:
        raise RuntimeError(wrong_result.stderr or "negative-control compile failed")
    wrong, wrong_relocations = extract_elf_functions_detailed(wrong_obj)["wrong_fill_pair"]
    if wrong_relocations:
        raise ValueError(f"negative control has relocations: {wrong_relocations}")

    original_runner = Runner(image, ADDRESS)
    candidate_runner = Runner(image, ADDRESS, candidate)
    rng = random.Random(seed ^ ADDRESS)
    count = 0
    first = None
    writes: set[int] = set()
    candidate_writes: set[int] = set()
    for offset in range(4):
        for high in HIGH_PATTERNS:
            for low in range(256):
                regs = [rng.getrandbits(32) for _ in range(13)]
                regs[0] = DATA + 0x400 + offset
                regs[1] = high | low
                case = Case(
                    f"dst-offset-{offset}-high-{high:08x}-low-{low:02x}",
                    tuple(regs), rng.randbytes(DATA_SIZE), rng.randbytes(STACK_SIZE),
                    rng.getrandbits(4) << 28,
                )
                expected = original_runner.run(case)
                actual = candidate_runner.run(case)
                writes.update(expected.writes)
                candidate_writes.update(actual.writes)
                reason = difference(expected, actual, returns_value=True)
                if reason:
                    first = {"case": case.label, "difference": reason}
                    break
                count += 1
            if first:
                break
        if first:
            break

    negative_case = Case(
        "wrong-high-byte-mask", tuple([DATA + 0x500, 0xABCD1255] + [0] * 11),
        rng.randbytes(DATA_SIZE), rng.randbytes(STACK_SIZE), 0,
    )
    negative_difference = difference(
        original_runner.run(negative_case),
        Runner(image, ADDRESS, wrong).run(negative_case), returns_value=True,
    )
    if sha256(SOURCE.read_bytes()) != source_hash:
        raise RuntimeError("production source changed during validation")
    report = {
        "schema": 1,
        "scope": "production UiConfig_FillPair at 0x0027EDF8",
        "reference_sha256": image_hash,
        "source_sha256": source_hash,
        "candidate_object_sha256": sha256(candidate_obj.read_bytes()),
        "candidate_body_bytes": len(candidate),
        "candidate_body_hex": candidate.hex(),
        "compile_command": result.args,
        "seed": seed,
        "destination_offsets": [0, 1, 2, 3],
        "high_byte_patterns": [f"0x{x:08X}" for x in HIGH_PATTERNS],
        "cases_expected": 4 * len(HIGH_PATTERNS) * 256,
        "cases_passed": count,
        "first_counterexample": first,
        "observed_write_union": [len(writes), len(candidate_writes)],
        "write_addresses_equal": writes == candidate_writes,
        "negative_control": {
            "source_sha256": sha256(wrong_source.read_bytes()),
            "object_sha256": sha256(wrong_obj.read_bytes()),
            "case": negative_case.label,
            "detected": negative_difference == "data memory differs",
            "difference": negative_difference,
        },
        "passed": (first is None and count == 4096 and writes == candidate_writes
                   and negative_difference == "data memory differs"),
        "limits": [
            "The defined C++ contract requires eight writable ordinary-memory bytes; the destination may be unaligned.",
            "The test covers offsets 0 through 3 and 1,024 value patterns per offset; it does not claim fault, MMIO, or concurrent-observer equivalence.",
            "This helper differential does not prove caller allocation success, UI behavior, persistence, or runtime equivalence.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    report = run(args.output.resolve(), args.seed)
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
