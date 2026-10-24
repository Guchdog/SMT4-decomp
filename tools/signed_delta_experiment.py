#!/usr/bin/env python3
"""Differentially test signed two-word conditional-delta ARM leaves."""
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
from tools.semantic_experiment import DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference
from tools.semantic_experiment_support import compile_candidate_symbols, load_pinned_reference

EXPECTED_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
FUNCTIONS = {
    0x001220C4: {"offset": 0x6C, "words": None, "symbol": "candidate_001220c4"},
    0x001220D8: {"offset": 0x7C, "words": None, "symbol": "candidate_001220d8"},
}
CONTROLS = ("wrong_offset_001220c4", "wrong_signedness_001220c4",
            "wrong_subtrahend_order_001220c4")
SIGNED_BOUNDARIES = (0, 1, 0x7FFFFFFF, 0x80000000, 0x80000001, 0xFFFFFFFF)


def verify_reference(image: bytes, ledger: list[dict[str, str]]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Unexpected code.bin SHA-256: {digest}")
    by_address = {int(row["address"], 16): row for row in ledger}
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    evidence = {}
    for address, spec in FUNCTIONS.items():
        row = by_address.get(address)
        if row is None or int(row["size"]) != 20 or row["status"] != "matching":
            raise ValueError(f"Ledger entry changed at {address:#010x}")
        raw = image[address - TEXT:address - TEXT + 20]
        words = struct.unpack("<5I", raw)
        decoded = [(i.mnemonic, i.op_str) for i in decoder.disasm(raw, address)]
        expected = [
            ("ldrd", f"r0, r1, [r0, #0x{spec['offset']:x}]"),
            ("cmp", "r1, r0"), ("movge", "r0, #0"),
            ("sublt", "r0, r0, r1"), ("bx", "lr"),
        ]
        if decoded != expected:
            raise ValueError(f"Instruction contract changed at {address:#010x}: {decoded}")
        spec["words"] = words
        evidence[hex(address)] = {
            "name": row["name"], "size": int(row["size"]),
            "instruction_words": [f"0x{x:08x}" for x in words],
            "raw_bytes_sha256": hashlib.sha256(raw).hexdigest(),
            "disassembly": decoded,
            "field_order": [f"object+0x{spec['offset']:x} -> r0", f"object+0x{spec['offset'] + 4:x} -> r1"],
        }
    return {"code_sha256": digest, "functions": evidence}


def make_cases(address: int, samples: int, seed: int):
    if samples < 0:
        raise ValueError("samples must be non-negative")
    offset = FUNCTIONS[address]["offset"]
    rng = random.Random(seed ^ address)
    # Cartesian boundary pairs cover equality, signed ordering boundaries,
    # and 32-bit subtraction wraparound. Object base is 8-byte aligned.
    for left_index, left in enumerate(SIGNED_BOUNDARIES):
        for right_index, right in enumerate(SIGNED_BOUNDARIES):
            data = bytearray(DATA_SIZE)
            base = 0x200
            struct.pack_into("<II", data, base + offset, left, right)
            # Offset-neighbor sentinels detect a wrong displacement.
            struct.pack_into("<II", data, base + offset + 8, right, left)
            regs = [rng.getrandbits(32) for _ in range(13)]
            regs[0] = DATA + base
            yield Case(f"boundary-{left_index}-{right_index}", tuple(regs), bytes(data),
                       rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)
    for index in range(samples):
        data = bytearray(rng.randbytes(DATA_SIZE))
        base = 0x200 + (index % 8) * 8
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0] = DATA + base
        yield Case(f"random-{index}", tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                   rng.getrandbits(4) << 28)


def _pair_case(address: int, left: int, right: int, seed: int, *, wrong_offset=False) -> Case:
    offset = FUNCTIONS[address]["offset"]
    base = 0x180
    data = bytearray(DATA_SIZE)
    pair_offset = offset + (4 if wrong_offset else 0)
    struct.pack_into("<II", data, base + pair_offset, left, right)
    if wrong_offset:
        struct.pack_into("<II", data, base + offset, 0x80000000, 0x7fffffff)
    regs = [0] * 13
    regs[0] = DATA + base
    return Case(f"negative-control-{seed}", tuple(regs), bytes(data), bytes(STACK_SIZE),
                (seed & 0xF) << 28)


def _fault_case(address: int, seed: int) -> Case:
    # Effective LDRD begins at the final mapped word: the second word is
    # unmapped. The object pointer itself remains 8-byte aligned.
    offset = FUNCTIONS[address]["offset"]
    base = DATA_SIZE - offset - 4
    regs = [0] * 13
    regs[0] = DATA + base
    return Case(f"cross-boundary-ldrd-seed-{seed}", tuple(regs), bytes(DATA_SIZE),
                bytes(STACK_SIZE), (seed & 0xF) << 28)


def run(code_path: Path, output: Path, seed: int, samples: int) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.ledger)
    compiled = compile_candidate_symbols(
        ROOT / "experiments/semantic_equivalence/signed_delta_candidates.cpp",
        output / "signed_delta_candidates.o", ROOT,
        [spec["symbol"] for spec in FUNCTIONS.values()] + list(CONTROLS))

    functions, negatives, faults = [], [], []
    for address, spec in FUNCTIONS.items():
        original = Runner(pinned.image, address)
        candidate = Runner(pinned.image, address, compiled[spec["symbol"]])
        count, failure = 0, None
        observed_reads = None
        for case in make_cases(address, samples, seed):
            old, new = original.run(case), candidate.run(case)
            reason = difference(old, new, returns_value=True, compare_flags=True)
            base = case.registers[0]
            expected_reads = frozenset(range(base + spec["offset"], base + spec["offset"] + 8))
            if not reason and (old.reads != expected_reads or old.writes):
                reason = f"unexpected LDRD read footprint/write: reads={sorted(old.reads)}, writes={sorted(old.writes)}"
            count += 1
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
            observed_reads = sorted(old.reads)
        functions.append({"address": hex(address), "candidate": spec["symbol"],
                          "original_bytes": 20, "candidate_bytes": len(compiled[spec["symbol"]]),
                          "candidate_bytes_equal": compiled[spec["symbol"]] == pinned.image[address - TEXT:address - TEXT + 20],
                          "classification": "byte-identical exact-compilation experiment"
                          if compiled[spec["symbol"]] == pinned.image[address - TEXT:address - TEXT + 20]
                          else "non-byte-identical semantic experiment",
                          "cases": count, "passed": failure is None,
                          "last_read_footprint": observed_reads, "failure": failure})

        controls = [
            ("wrong_offset_001220c4", _pair_case(address, 0x80000000, 0x7FFFFFFF, seed, wrong_offset=True)),
            ("wrong_signedness_001220c4", _pair_case(address, 0x80000000, 0x7FFFFFFF, seed)),
            ("wrong_subtrahend_order_001220c4", _pair_case(address, 0x7FFFFFFF, 0x80000000, seed)),
        ]
        # These controls are defined for the +0x6c member. Do not compare them
        # to the +0x7c function since their offsets are intentionally fixed.
        if address == 0x001220C4:
            for control, case in controls:
                old = original.run(case)
                bad = Runner(pinned.image, address, compiled[control]).run(case)
                reason = difference(old, bad, returns_value=True, compare_flags=True)
                negatives.append({"address": hex(address), "control": control,
                                  "detected": reason is not None, "reason": reason})

        case = _fault_case(address, seed)
        old, new = original.run(case), candidate.run(case)
        same_fault = bool(old.fault) and bool(new.fault)
        fault_ok = (same_fault and old.data == new.data and new.writes == old.writes
                    and old.reads == new.reads)
        faults.append({"address": hex(address), "passed": fault_ok,
                       "original_fault": old.fault, "candidate_fault": new.fault,
                       "original_reads": sorted(old.reads), "candidate_reads": sorted(new.reads),
                       "writes": sorted(old.writes)})

    report = {
        "experiment": "signed_two_word_conditional_delta_pair", "seed": seed,
        "random_samples_per_function": samples, "boundary_pairs_per_function": len(SIGNED_BOUNDARIES) ** 2,
        "reference": reference, "functions": functions, "negative_controls": negatives,
        "fault_behavior": faults, "caller_windows": [],
        "semantics": {
            "loads": "LDRD loads little-endian word at object+offset into r0 and next word at +4 into r1",
            "comparison": "CMP computes r1-r0 and sets NZCV; GE/LT are signed predicates (N==V / N!=V)",
            "result": "if signed(r1)>=signed(r0), return 0; otherwise return (r0-r1) modulo 2^32",
            "flags": "final NZCV equals CMP's NZCV because conditional MOVGE/SUBLT do not set flags",
            "access": "one 8-byte LDRD at offset; no writes; LDRD may fault as a whole on inaccessible memory",
        },
        "limitations": [
            "Both source-revision identity and each ledger entry/instruction sequence are pinned.",
            "Tests use a bounded Unicorn ARM11MPCore harness with ordinary mapped RAM; hardware bus/MMIO semantics are not modeled.",
            "No caller window was added; this is isolated leaf equivalence, not whole-program or emulator evidence.",
            "Inline ARM assembly is required to preserve the exact LDRD and CMP NZCV contract; an ordinary C++ relational expression cannot guarantee either.",
            "This experiment is isolated and does not alter the production ledger or integrate candidates into the game.",
        ],
    }
    report["candidate_classification"] = (
        "both candidates compile byte-for-byte identical to pinned originals"
        if all(item["candidate_bytes_equal"] for item in functions)
        else "at least one candidate differs in bytes; remains semantic-only")
    report["passed"] = (all(item["passed"] and item["candidate_bytes_equal"] for item in functions)
                        and all(item["detected"] for item in negatives))
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--output", type=Path, default=Path("build/semantic-equivalence/signed-delta-seed20261024"))
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--samples", type=int, default=128)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed, args.samples)
    print(json.dumps({"passed": report["passed"], "functions": report["functions"],
                      "negative_controls": report["negative_controls"],
                      "fault_behavior": report["fault_behavior"]}, indent=2))


if __name__ == "__main__":
    main()
