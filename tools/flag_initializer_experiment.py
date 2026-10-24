#!/usr/bin/env python3
"""Differential-test two flag-setting fixed-record initializers."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
from tools.build_check import find_clang
from tools.semantic_experiment import DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference
from tools.semantic_experiment_support import compile_candidate_symbols, load_pinned_reference

TAGS = {0x00383780: 0x11, 0x003A1A6C: 0x13}
U32_MASK = 0xFFFFFFFF


def decode(image: bytes, address: int, size: int):
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    offset = address - TEXT
    decoded = list(cs.disasm(image[offset:offset + size], address))
    if sum(item.size for item in decoded) != size:
        raise ValueError(f"incomplete instruction body at {address:#010x}")
    return tuple((item.mnemonic, item.op_str) for item in decoded)


def discover_direct_callers(image: bytes):
    """Find ARM BL encodings only; this says nothing about Thumb/indirect calls."""
    callers = {address: [] for address in TAGS}
    for index in range(len(image) // 4):
        word = struct.unpack_from("<I", image, index * 4)[0]
        if (word & 0x0F000000) != 0x0B000000 or (word >> 28) == 0xF:
            continue
        displacement = (word & 0x00FFFFFF) << 2
        if displacement & (1 << 25):
            displacement -= 1 << 26
        target = (TEXT + index * 4 + 8 + displacement) & U32_MASK
        if target in callers:
            callers[target].append(TEXT + index * 4)
    return {address: tuple(sites) for address, sites in callers.items()}


def verify_reference(image: bytes, ledger: list[dict[str, str]]):
    rows = {int(row["address"], 16): row for row in ledger}
    for address, tag in TAGS.items():
        row = rows.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != 28:
            raise ValueError(f"missing matching 28-byte ledger row at {address:#010x}")
        expected = (("ldr", "r1, [r0]"), ("mov", "r2, #0"),
                    ("orr", "r1, r1, #1"), ("str", "r1, [r0], #4"),
                    ("mov", f"r1, #0x{tag:x}"), ("stm", "r0, {r1, r2}"),
                    ("bx", "lr"))
        actual = decode(image, address, 28)
        if actual != expected:
            raise ValueError(f"instruction body changed at {address:#010x}: {actual}")
    callers = discover_direct_callers(image)
    # Recorded as a scan result only. No caller window is claimed or executed.
    return rows, callers


def make_case(seed: int, label: str):
    rng = random.Random(seed)
    data = bytearray(rng.randbytes(DATA_SIZE))
    base = DATA + 0x100
    initial = {
        "clear": 0,
        "already-set": 1,
        "bit-one-only": 2,
        "high-bit": 0x80000000,
        "all-ones": U32_MASK,
        "alternating": 0xAAAAAAAA,
    }.get(label, rng.getrandbits(32))
    struct.pack_into("<I", data, base - DATA, initial)
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0] = base
    return Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def run(code_path: Path, output: Path, samples=128, seed=20261024):
    if samples < 0:
        raise ValueError("samples must be nonnegative")
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    rows, callers = verify_reference(pinned.image, pinned.ledger)
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / "experiments/semantic_equivalence/flag_initializer_candidates.cpp"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    object_path = output / "flag_initializer_candidates.o"
    required = {f"candidate_{address:08x}" for address in TAGS} | {
        "negative_wrong_flag", "negative_wrong_constant", "negative_wrong_offset",
        "negative_wrong_return",
    }
    compiled = compile_candidate_symbols(source, object_path, ROOT, required)

    function_results = []
    for address in TAGS:
        original = Runner(pinned.image, address)
        candidate = Runner(pinned.image, address, compiled[f"candidate_{address:08x}"])
        labels = ("clear", "already-set", "bit-one-only", "high-bit", "all-ones", "alternating")
        trials = [(label, seed + index) for index, label in enumerate(labels)]
        trials += [(f"random-{index}", random.Random(seed ^ address ^ index).getrandbits(32))
                   for index in range(samples)]
        for label, case_seed in trials:
            case = make_case(case_seed, label)
            # Include NZCV explicitly; the original non-S instructions preserve it.
            reason = difference(original.run(case), candidate.run(case), returns_value=True,
                                compare_flags=True)
            if reason:
                raise AssertionError(f"{address:#010x} {label}: {reason}")
        function_results.append({"address": hex(address), "tag": hex(TAGS[address]),
                                 "candidate_bytes": len(compiled[f"candidate_{address:08x}"]),
                                 "cases": len(trials), "passed": True,
                                 "checks": ["return", "callee-saved registers/SP", "NZCV",
                                            "full mapped data/stack image", "read/write byte footprints"]})

    # Controls use the first initializer/tag and ensure each semantic dimension is observable.
    base_case = make_case(seed ^ 0xC0FFEE, "negative-control")
    original = Runner(pinned.image, 0x00383780)
    negatives = []
    for symbol in ("negative_wrong_flag", "negative_wrong_constant", "negative_wrong_offset",
                   "negative_wrong_return"):
        wrong = Runner(pinned.image, 0x00383780, compiled[symbol])
        reason = difference(original.run(base_case), wrong.run(base_case), returns_value=True,
                            compare_flags=True)
        negatives.append({"name": symbol, "detected": reason is not None, "reason": reason})

    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("candidate source changed during experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True).stdout.splitlines()[0]
    report = {
        "schema": 1,
        "passed": all(item["passed"] for item in function_results)
        and all(item["detected"] for item in negatives),
        "reference_sha256": pinned.game_info["code_sha256"],
        "source_sha256": source_hash,
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler": compiler, "seed": seed, "random_cases_per_function": samples,
        "functions": function_results,
        "direct_arm_bl_scan": {hex(address): [hex(site) for site in sites]
                                for address, sites in callers.items()},
        "executed_direct_caller_windows": [],
        "negative_controls": negatives,
        "contract": "aligned ordinary RAM; flags[0] |= 1; flags[1] = tag (0x11/0x13); flags[2] = 0; return base+4",
        "limitations": [
            "No caller windows were manually established/executed; scan detects ARM BL encodings only and misses Thumb/indirect calls",
            "C++ emits ordinary volatile accesses; original STM writes two words as one architectural instruction, so partial-fault ordering/atomicity is not established equivalent",
            "Unaligned addresses, MMIO, concurrent observers, exceptions/fault injection and hardware bus transaction behavior are excluded",
            "Mapped-memory differential tests compare resulting bytes, return/register/NZCV state, and read/write byte footprints, not fault-time partial effects",
            "Bounded tests are evidence, not a formal equivalence proof",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/flag-initializers-seed20261024")
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    try:
        report = run(args.code, args.output, args.samples, args.seed)
    except (RuntimeError, ValueError, OSError, AssertionError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    print(f"Flag initializer experiment {'PASS' if report['passed'] else 'FAIL'}; report: {args.output / 'report.json'}")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
