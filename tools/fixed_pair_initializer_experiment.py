#!/usr/bin/env python3
"""Differential-test two small fixed pair-record initializers."""
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

OFFSETS = {0x00399D4C: 0x04, 0x003ABCF4: 0x14}
CALLERS = {0x00399D4C: (0x001924DC, 0x00276C04), 0x003ABCF4: ()}
CALLBACK_TABLE = {"slot": 0x004024D8, "previous": 0, "next": 0}
U32_MASK = 0xFFFFFFFF


def decode(image: bytes, address: int, size: int):
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    offset = address - TEXT
    decoded = list(cs.disasm(image[offset:offset + size], address))
    if sum(item.size for item in decoded) != size:
        raise ValueError(f"incomplete instruction body at {address:#010x}")
    return tuple((item.mnemonic, item.op_str) for item in decoded)


def discover_callers(image: bytes):
    result = {address: [] for address in OFFSETS}
    for index in range(len(image) // 4):
        word = struct.unpack_from("<I", image, index * 4)[0]
        if (word & 0x0F000000) != 0x0B000000 or (word >> 28) == 0xF:
            continue
        displacement = (word & 0x00FFFFFF) << 2
        if displacement & (1 << 25):
            displacement -= 1 << 26
        target = (TEXT + index * 4 + 8 + displacement) & U32_MASK
        if target in result:
            result[target].append(TEXT + index * 4)
    return {address: tuple(sites) for address, sites in result.items()}


def verify_reference(image: bytes, ledger: list[dict[str, str]]):
    rows = {int(row["address"], 16): row for row in ledger}
    for address, offset in OFFSETS.items():
        row = rows.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != 20:
            raise ValueError(f"missing matching 20-byte ledger row at {address:#010x}")
        imm = "#4" if offset == 4 else "#0x14"
        expected = (("add", f"r0, r0, {imm}"), ("mov", "r1, #1"),
                    ("mov", "r2, #0"), ("stm", "r0, {r1, r2}"), ("bx", "lr"))
        actual = decode(image, address, 20)
        if actual != expected:
            raise ValueError(f"instruction body changed at {address:#010x}: {actual}")
    callers = discover_callers(image)
    for address, expected in CALLERS.items():
        if callers[address] != expected:
            raise ValueError(f"BL caller set changed for {address:#010x}: {callers[address]}")
    if decode(image, 0x001924D8, 8) != (("add", "r0, r4, #0x40"), ("bl", "#0x399d4c")):
        raise ValueError("first caller setup/window changed")
    if decode(image, 0x00276C00, 8) != (("add", "r0, r4, #0x40"), ("bl", "#0x399d4c")):
        raise ValueError("second caller setup/window changed")
    table_offset = CALLBACK_TABLE["slot"] - TEXT
    table = tuple(struct.unpack_from("<I", image, table_offset + delta)[0]
                  for delta in (-4, 0, 4))
    expected_table = (CALLBACK_TABLE["previous"], 0x003ABCF4, CALLBACK_TABLE["next"])
    if table != expected_table:
        raise ValueError(f"callback table neighborhood changed: {table}")
    return rows


def verify_candidate_shape(code: bytes, offset: int):
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    actual = tuple((item.mnemonic, item.op_str) for item in cs.disasm(code, 0))
    first = f"[r0, #{offset}]" if offset < 10 else f"[r0, #0x{offset:x}]"
    second_offset = offset + 4
    second = f"[r0, #{second_offset}]" if second_offset < 10 else f"[r0, #0x{second_offset:x}]"
    return_offset = "#4" if offset == 4 else "#0x14"
    expected = (("mov", "r1, #1"), ("str", f"r1, {first}"),
                ("mov", "r1, #0"), ("str", f"r1, {second}"),
                ("add", f"r0, r0, {return_offset}"), ("bx", "lr"))
    if actual != expected:
        raise ValueError(f"candidate body does not retain ordered pair initializer: {actual}")


def make_case(seed: int, label: str, offset: int):
    rng = random.Random(seed)
    data = bytearray(rng.randbytes(DATA_SIZE))
    base = DATA + 0x100
    if label == "zeroed-fields":
        values = (0, 0)
    elif label == "all-ones-fields":
        values = (U32_MASK, U32_MASK)
    else:
        values = (0xA5A55A5A, 0xDEADBEEF)
    struct.pack_into("<II", data, base - DATA + offset, *values)
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0] = base
    regs[4] = base
    return Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def run(code_path: Path, output: Path, samples=64, seed=20261024):
    if samples < 0:
        raise ValueError("samples must be nonnegative")
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    verify_reference(pinned.image, pinned.ledger)
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / "experiments/semantic_equivalence/fixed_pair_initializer_candidates.cpp"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    object_path = output / "fixed_pair_initializer_candidates.o"
    required = {f"candidate_{address:08x}" for address in OFFSETS} | {
        "negative_wrong_offset", "negative_wrong_value", "negative_wrong_return",
    }
    compiled = compile_candidate_symbols(source, object_path, ROOT, required)
    for address, offset in OFFSETS.items():
        verify_candidate_shape(compiled[f"candidate_{address:08x}"], offset)

    results = []
    for address, offset in OFFSETS.items():
        original = Runner(pinned.image, address)
        candidate = Runner(pinned.image, address, compiled[f"candidate_{address:08x}"])
        trials = [("distinct-fields", seed), ("zeroed-fields", seed + 1),
                  ("all-ones-fields", seed + 2)]
        trials += [(f"random-{i}", random.Random(seed ^ address ^ i).getrandbits(32))
                   for i in range(samples)]
        for index, (label, case_seed) in enumerate(trials):
            case = make_case(case_seed, label, offset)
            reason = difference(original.run(case), candidate.run(case), returns_value=True)
            if reason:
                raise AssertionError(f"{address:#010x} {label}: {reason}")
        results.append({"address": hex(address), "offset": hex(offset),
                        "candidate_bytes": len(compiled[f"candidate_{address:08x}"]),
                        "cases": len(trials), "passed": True})

    # Execute each direct caller's pointer setup plus BL, stopping on return.
    caller_results = []
    address = 0x00399D4C
    original = Runner(pinned.image, address)
    candidate = Runner(pinned.image, address, compiled[f"candidate_{address:08x}"])
    for site in CALLERS[address]:
        case = make_case(seed ^ site, f"caller-{site:08x}", OFFSETS[address])
        ro = original.run(case, start=site - 4, stops=(site + 4,))
        rc = candidate.run(case, start=site - 4, stops=(site + 4,))
        reason = difference(ro, rc, returns_value=True, caller_window=True,
                            compare_flags=False)
        caller_results.append({"callsite": hex(site), "passed": reason is None,
                               "failure": reason})

    controls = ("negative_wrong_offset", "negative_wrong_value", "negative_wrong_return")
    base_case = make_case(seed, "negative-control", OFFSETS[0x003ABCF4])
    original = Runner(pinned.image, 0x003ABCF4)
    negatives = []
    for symbol in controls:
        wrong = Runner(pinned.image, 0x003ABCF4, compiled[symbol])
        reason = difference(original.run(base_case), wrong.run(base_case), returns_value=True)
        negatives.append({"name": symbol, "detected": reason is not None, "reason": reason})

    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("candidate source changed during experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True).stdout.splitlines()[0]
    report = {
        "schema": 1,
        "passed": all(x["passed"] for x in results + caller_results)
        and all(x["detected"] for x in negatives),
        "reference_sha256": pinned.game_info["code_sha256"],
        "source_sha256": source_hash,
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler": compiler, "seed": seed, "random_cases_per_function": samples,
        "functions": results, "direct_caller_windows": caller_results,
        "callback_table_reference": {"slot": hex(CALLBACK_TABLE["slot"]),
                                     "target": hex(0x003ABCF4),
                                     "direct_bl_callers": []},
        "negative_controls": negatives,
        "contract": "aligned ordinary-RAM base; write [base+offset]=1 and [base+offset+4]=0; return adjusted record pointer",
        "limitations": [
            "0x003ABCF4 is evidenced as a table function pointer, but the indirect dispatch path is not executed",
            "Writes are adjacent, non-overlapping words; source/destination aliasing does not apply",
            "Unaligned memory, MMIO, concurrency, exceptions and partial-fault ordering are excluded",
            "Bounded tests are evidence, not a formal equivalence proof",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/fixed-pair-initializers")
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    try:
        report = run(args.code, args.output, args.samples, args.seed)
    except (RuntimeError, ValueError, OSError, AssertionError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    print(f"Fixed-pair initializer experiment {'PASS' if report['passed'] else 'FAIL'}; report: {args.output / 'report.json'}")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
