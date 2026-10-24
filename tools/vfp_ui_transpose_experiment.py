#!/usr/bin/env python3
"""Two-seed isolated differential test of the 0x002B7AA8 VFP word transpose."""
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

import capstone
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, get_armv6k_flags
from tools.semantic_experiment import TEXT, DATA, STACK, STACK_SIZE, INJECT
from tools.semantic_experiment import require_unicorn
from tools.semantic_experiment_support import load_pinned_reference
from tools.vfp_matrix_transpose_experiment import Runner, compare

ADDRESS = 0x002B7AA8
SIZE = 72
EXPECTED = (
    ("vldr", "s0, [r1]"), ("vldr", "s1, [r1, #0x10]"),
    ("vldr", "s2, [r1, #0x20]"), ("vldr", "s3, [r1, #0x30]"),
    ("vldr", "s4, [r1, #4]"), ("vldr", "s5, [r1, #0x14]"),
    ("vldr", "s6, [r1, #0x24]"), ("vldr", "s7, [r1, #0x34]"),
    ("vldr", "s8, [r1, #8]"), ("vldr", "s9, [r1, #0x18]"),
    ("vldr", "s10, [r1, #0x28]"), ("vldr", "s11, [r1, #0x38]"),
    ("vldr", "s12, [r1, #0xc]"), ("vldr", "s13, [r1, #0x1c]"),
    ("vldr", "s14, [r1, #0x2c]"), ("vldr", "s15, [r1, #0x3c]"),
    ("vstmia", "r0, {s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15}"),
    ("bx", "lr"),
)


def verify_reference(image: bytes, code_sha: str, ledger_rows: list[dict]) -> dict:
    row = next((item for item in ledger_rows if int(item["address"], 16) == ADDRESS), None)
    if row is None or int(row["size"]) != SIZE or row["status"] != "matching":
        raise ValueError("matching ledger entry missing/changed at 0x002b7aa8")
    code = image[ADDRESS - TEXT:ADDRESS - TEXT + SIZE]
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoded = list(decoder.disasm(code, ADDRESS))
    actual = tuple((item.mnemonic.lower(), item.op_str.lower()) for item in decoded)
    if sum(item.size for item in decoded) != SIZE or actual != EXPECTED:
        raise ValueError(f"VFP transpose body changed: {actual}")
    return {
        "code_sha256": code_sha,
        "address": hex(ADDRESS),
        "size": SIZE,
        "bytes_sha256": hashlib.sha256(code).hexdigest(),
        "instructions": [f"{mnemonic} {operands}" for mnemonic, operands in EXPECTED],
        "observed_behavior": (
            "Loads the 4x4 source matrix in transposed indexing order into s0-s15, "
            "then stores 16 raw words contiguously to destination."
        ),
        "abi_evidence": (
            "Arguments are r0/r1, only caller-saved s0-s15 are touched, and "
            "GPR callee-saved state/SP are untouched; no arithmetic or FPSCR change."
        ),
        "caller_evidence": "No direct ARM BL callers found in the pinned code scan; indirect/Thumb dispatch is not excluded.",
    }


def make_case(seed: int, index: int, overlap: int | None = None):
    rng = random.Random(seed ^ (index * 0x9E3779B1))
    data = bytearray(rng.randbytes(0x4000))
    src_off = 0x400
    dst_off = 0x800 if overlap is None else src_off + overlap
    words = [rng.getrandbits(32) for _ in range(16)]
    data[src_off:src_off + 64] = b"".join(struct.pack("<I", word) for word in words)
    gp = [rng.getrandbits(32) for _ in range(13)]
    gp[0], gp[1] = DATA + dst_off, DATA + src_off
    return {"gp": tuple(gp), "s": [rng.getrandbits(32) for _ in range(32)],
            "data": bytes(data), "stack": rng.randbytes(STACK_SIZE)}


def run(code_path: Path, output: Path, seed: int):
    require_unicorn()
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.game_info["code_sha256"], pinned.ledger)
    source_path = ROOT / "experiments/semantic_equivalence/vfp_ui_transpose_candidate.cpp"
    object_path = output / "vfp_ui_transpose_candidate.o"
    build = compile_tu_armv6k(source_path, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K candidate compilation failed")
    symbols = {}
    for name, (code, relocations) in extract_elf_functions_detailed(object_path).items():
        if relocations:
            raise ValueError(f"unexpected relocation in {name}: {relocations}")
        symbols[name] = code
    required = {"candidate_002b7aa8", "wrong_ui_transpose_002b7aa8"}
    if required - symbols.keys():
        raise ValueError(f"candidate symbols missing: {sorted(required - symbols.keys())}")
    flags = get_armv6k_flags(ROOT)
    if any(flag == "-Ofast" or flag.startswith("-ffast-math") for flag in flags):
        raise ValueError("fast-math is disallowed")
    cases = [make_case(seed, i, overlap=(4 if i == 32 else None)) for i in range(64)]
    results = []
    for index, case in enumerate(cases):
        ref = Runner(pinned.image, ADDRESS).run(case)
        cand = Runner(pinned.image, ADDRESS, symbols["candidate_002b7aa8"]).run(case)
        reason = compare(ref, cand)
        if reason:
            results.append({"case": index, "passed": False, "failure": reason})
            break
    else:
        results.append({"cases": len(cases), "passed": True})
    negative_case = make_case(seed, 0)
    ref = Runner(pinned.image, ADDRESS).run(negative_case)
    wrong = Runner(pinned.image, ADDRESS, symbols["wrong_ui_transpose_002b7aa8"]).run(negative_case)
    report = {
        "experiment": "vfp_ui_word_transpose_singleton",
        "passed": all(item["passed"] for item in results) and ref["data"] != wrong["data"],
        "reference": reference,
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler_flags": flags, "fast_math": False, "seed": seed,
        "function_comparisons": len(cases), "functions": results,
        "negative_control": {"name": "wrong_ui_transpose_002b7aa8",
                             "detects_transpose_order": ref["data"] != wrong["data"]},
        "comparison_policy": ["return/fault", "callee-saved GPR/VFP and SP",
                              "RAM after return", "ordinary-memory read/write byte sets"],
        "limits": ["aligned ordinary RAM only", "finite two-seed differential evidence",
                   "no direct BL callers found; runtime dispatch/caller liveness unverified"],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.code, args.output, args.seed), indent=2))


if __name__ == "__main__":
    main()
