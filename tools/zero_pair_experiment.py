#!/usr/bin/env python3
"""Isolated differential experiment for three two-word zero initializers."""
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
from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference,
)
from tools.semantic_experiment_support import (
    compile_candidate_symbols, load_pinned_reference,
)

TARGETS = (0x0011B850, 0x0017F5E8, 0x0017F5F8)
DIRECT_CALLERS = {0x0011B850: (0x00110D94, 0x0011109C)}
CALLBACK_SITES = {
    0x0017F5E8: (0x0037E330, 0x003F4154),
    0x0017F5F8: (0x003ED7F4,),
}
U32_MASK = 0xFFFFFFFF


def instructions(image: bytes, address: int, size: int):
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    off = address - TEXT
    decoded = list(cs.disasm(image[off:off + size], address))
    if sum(item.size for item in decoded) != size:
        raise ValueError(f"incomplete instruction body at {address:#010x}")
    return tuple((item.mnemonic, item.op_str) for item in decoded)


def verify_reference(image: bytes, ledger: list[dict[str, str]]):
    rows = {int(row["address"], 16): row for row in ledger}
    expected = (("mov", "r1, #0"), ("mov", "r2, r1"),
                ("stm", "r0, {r1, r2}"), ("bx", "lr"))
    for address in TARGETS:
        row = rows.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != 16:
            raise ValueError(f"missing matching 16-byte ledger entry at {address:#010x}")
        actual = instructions(image, address, 16)
        if actual != expected:
            raise ValueError(f"instruction body changed at {address:#010x}: {actual}")

    for site in DIRECT_CALLERS[0x0011B850]:
        actual = instructions(image, site, 4)
        if len(actual) != 1 or actual[0][0] != "bl":
            raise ValueError(f"expected direct BL at {site:#010x}, got {actual}")
    # Callback references are verified as literal loads of the exact function
    # address, followed shortly by the registration BLX documented in source.
    literal_values = {0x0017F5E8: (0x0037E3EC, 0x003F4210),
                      0x0017F5F8: (0x003ED824,)}
    for target, refs in literal_values.items():
        for ref in refs:
            off = ref - TEXT
            if struct.unpack_from("<I", image, off)[0] != target:
                raise ValueError(f"callback literal changed at {ref:#010x}")
    for target, sites in CALLBACK_SITES.items():
        for site in sites:
            block = instructions(image, site, 20)
            if not any(mnemonic == "blx" for mnemonic, _ in block):
                raise ValueError(f"registration BLX not found near {site:#010x}: {block}")
    return rows


def verify_candidate_shape(code: bytes):
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoded = tuple((item.mnemonic, item.op_str) for item in cs.disasm(code, 0))
    expected = (("mov", "r1, #0"), ("str", "r1, [r0]"),
                ("str", "r1, [r0, #4]"), ("bx", "lr"))
    if decoded != expected:
        raise ValueError(f"candidate must retain ordered stores at +0/+4: {decoded}")


def case_for(seed: int, label: str):
    rng = random.Random(seed)
    data = bytearray(rng.randbytes(DATA_SIZE))
    base = DATA + 0x100
    struct.pack_into("<II", data, base - DATA, 0xA5A55A5A, 0xDEADBEEF)
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0] = base
    return Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def cases(seed: int, samples: int):
    for i, label in enumerate(("distinct-sentinels", "all-ones", "zero")):
        yield case_for(seed + i, label)
    rng = random.Random(seed ^ 0xA11CE)
    for i in range(samples):
        # Keep an independent, aligned destination and vary surrounding data.
        yield case_for(rng.getrandbits(32), f"random-{i}")


def run(code_path: Path, output: Path, samples=64, seed=20261024):
    if samples < 0:
        raise ValueError("samples must be nonnegative")
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    rows = verify_reference(pinned.image, pinned.ledger)
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / "experiments/semantic_equivalence/zero_pair_candidates.cpp"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    object_path = output / "zero_pair_candidates.o"
    required = {f"candidate_{address:08x}" for address in TARGETS} | {
        "negative_second_offset", "negative_missing_store", "negative_wrong_return",
    }
    compiled = compile_candidate_symbols(source, object_path, ROOT, required)
    for address in TARGETS:
        verify_candidate_shape(compiled[f"candidate_{address:08x}"])
    results = []
    for address in TARGETS:
        original = Runner(pinned.image, address)
        candidate = Runner(pinned.image, address, compiled[f"candidate_{address:08x}"])
        count = 0
        for case in cases(seed ^ address, samples):
            reason = difference(original.run(case), candidate.run(case), returns_value=True)
            if reason:
                raise AssertionError(f"{address:#010x} {case.label}: {reason}")
            count += 1
        results.append({"address": hex(address), "candidate_bytes": len(compiled[f"candidate_{address:08x}"]),
                        "cases": count, "passed": True})

    # Exercise each known direct caller's BL instruction using an injected,
    # valid pointer argument; this specifically checks the r0 return/window.
    caller_results = []
    target = 0x0011B850
    original = Runner(pinned.image, target)
    candidate = Runner(pinned.image, target, compiled[f"candidate_{target:08x}"])
    for site in DIRECT_CALLERS[target]:
        case = case_for(seed ^ site, f"caller-{site:08x}")
        ro = original.run(case, start=site, stops=(site + 4,))
        rc = candidate.run(case, start=site, stops=(site + 4,))
        reason = difference(ro, rc, returns_value=True, caller_window=True,
                            compare_flags=False)
        caller_results.append({"callsite": hex(site), "passed": reason is None, "failure": reason})

    negative = []
    controls = ("negative_second_offset", "negative_missing_store", "negative_wrong_return")
    base_case = case_for(seed, "distinct-sentinels")
    for symbol in controls:
        runner = Runner(pinned.image, target, compiled[symbol])
        reason = difference(original.run(base_case), runner.run(base_case), returns_value=True)
        negative.append({"name": symbol, "detected": reason is not None, "reason": reason})

    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("candidate source changed while running")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True).stdout.splitlines()[0]
    report = {
        "schema": 1, "passed": all(item["passed"] for item in results + caller_results)
        and all(item["detected"] for item in negative),
        "reference_sha256": pinned.game_info["code_sha256"],
        "source_sha256": source_hash, "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler": compiler, "seed": seed, "samples_per_function": samples,
        "functions": results, "direct_caller_windows": caller_results,
        "callback_registration_evidence": {hex(k): [hex(x) for x in v] for k, v in CALLBACK_SITES.items()},
        "negative_controls": negative,
        "contract": "aligned ordinary-RAM r0; store zero to exactly [r0] and [r0+4], preserve/return r0",
        "limitations": [
            "Callback references are verified through literal and nearby registration-BLX sites, not end-to-end texture initialization",
            "No source/destination alias exists: values are constants; adjacent stores do not overlap",
            "Unaligned accesses, MMIO, exceptions, concurrency and partial-fault ordering are excluded",
            "Bounded differential tests provide evidence, not a formal equivalence proof",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, default=ROOT / "build/semantic-equivalence/zero-pairs")
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    try:
        report = run(args.code, args.output, args.samples, args.seed)
    except (RuntimeError, ValueError, OSError, AssertionError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    print(f"Zero-pair experiment {'PASS' if report['passed'] else 'FAIL'}; report: {args.output / 'report.json'}")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
