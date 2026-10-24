#!/usr/bin/env python3
"""Bounded differential experiment for two field round-trips and a predicate."""
from __future__ import annotations

import argparse
import csv
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
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference, validate_leaf

SEEDS = (20261024, 20261025)
SPECS = {
    0x00146CE0: {
        "size": 16, "symbol": "candidate_00146ce0", "negative": "wrong_offset_00146ce0",
        "sha256": "619196341d897f5bfb0ee59c62a206e78a93910257df5555cd70c4b8947d9bfd",
        "offset": 0x34, "width": 2, "signed": False,
        "instructions": (("add", "r2, r0, #0x24"), ("ldrh", "r0, [r0, #0x34]"),
                         ("strh", "r1, [r2, #0x10]"), ("bx", "lr")),
    },
    0x00146D10: {
        "size": 16, "symbol": "candidate_00146d10", "negative": "wrong_unsigned_return_00146d10",
        "sha256": "54d0867aaa67ee0aaaf7889faba85709894ffd1bacdc117e3224a2f50626536a",
        "offset": 0x38, "width": 1, "signed": True,
        "instructions": (("add", "r2, r0, #0x24"), ("ldrsb", "r0, [r0, #0x38]"),
                         ("strb", "r1, [r2, #0x14]"), ("bx", "lr")),
    },
    0x002523C0: {
        "size": 16, "symbol": "candidate_002523c0", "negative": "wrong_comparison_002523c0",
        "sha256": "5681d46e62e1721f54a7149ebea5d671114701074fcc45cea5902cfd7b7e481d",
        "offset": 0, "width": 4, "signed": False,
        "instructions": (("ldr", "r0, [r0]"), ("cmp", "r0, #1"),
                         ("movne", "r0, #0"), ("bx", "lr")),
    },
}
EXPECTED_CODE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
U32 = 0xFFFFFFFF


def verify_reference(image: bytes, rows: list[dict], expected_code_sha256: str) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != expected_code_sha256 or digest != EXPECTED_CODE_SHA256:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    by_address = {int(row["address"], 16): row for row in rows}
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    pinned = {}
    for address, spec in SPECS.items():
        row = by_address.get(address)
        if row is None or int(row["size"]) != spec["size"] or row["status"] != "matching":
            raise ValueError(f"Ledger entry missing/changed at {address:#010x}")
        raw = image[address - TEXT:address - TEXT + spec["size"]]
        if hashlib.sha256(raw).hexdigest() != spec["sha256"]:
            raise ValueError(f"Function byte pin changed at {address:#010x}")
        decoded = tuple((ins.mnemonic.lower(), ins.op_str.lower()) for ins in cs.disasm(raw, address))
        if decoded != spec["instructions"]:
            raise ValueError(f"Original instruction pin changed at {address:#010x}")
        pinned[hex(address)] = {"size": spec["size"], "sha256": spec["sha256"],
                                "instructions": [f"{m} {o}" for m, o in decoded],
                                "ledger_name": row["name"], "category": row["category"]}
    return {"code_sha256": digest, "functions": pinned}


def make_cases(address: int, seed: int, samples: int = 256):
    if samples < 0:
        raise ValueError("samples must be non-negative")
    rng = random.Random(seed ^ address)
    spec = SPECS[address]
    if address == 0x00146CE0:
        values = ((0, 0), (0xFFFF, 0x10000), (1, U32), (0x8000, 0x80000000),
                  (0x1234, 0xA1B2C3D4)) + tuple(
                      (rng.getrandbits(16), rng.getrandbits(32)) for _ in range(samples))
    elif address == 0x00146D10:
        values = tuple((b, rng.getrandbits(32)) for b in range(256)) + tuple(
            (rng.getrandbits(8), rng.getrandbits(32)) for _ in range(samples))
    elif address == 0x002523C0:
        bounds = (0, 1, 2, 3, 0xFFFFFFFF, 0x80000000, 0xFFFFFFFE)
        values = tuple((v, 0) for v in bounds) + tuple(
            (rng.getrandbits(32), 0) for _ in range(samples))
    else:
        raise ValueError(f"No case generator for {address:#010x}")

    for index, (value, new_value) in enumerate(values):
        memory = bytearray(rng.randbytes(DATA_SIZE))
        pointer = DATA + 0x100 + (index % 16) * 4
        if address == 0x00146CE0:
            struct.pack_into("<H", memory, pointer - DATA + spec["offset"], value)
        elif address == 0x00146D10:
            memory[pointer - DATA + spec["offset"]] = value
        else:
            struct.pack_into("<I", memory, pointer - DATA, value)
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0] = pointer
        if address != 0x002523C0:
            regs[1] = new_value
        yield Case(f"case-{index}", tuple(regs), bytes(memory), rng.randbytes(STACK_SIZE),
                   rng.getrandbits(4) << 28)


def _fault_probe(address: int, seed: int) -> Case:
    rng = random.Random(seed ^ address ^ 0xFA017)
    memory = bytearray(rng.randbytes(DATA_SIZE))
    regs = [rng.getrandbits(32) for _ in range(13)]
    offset = SPECS[address]["offset"]
    regs[0] = DATA + DATA_SIZE - offset + 4
    if address != 0x002523C0:
        regs[1] = 0xABCDEF81
    return Case("unmapped-field-read", tuple(regs), bytes(memory), rng.randbytes(STACK_SIZE), 0x60000000)


def _fault_parity(a, b) -> bool:
    # Original and relocated C++ fault at different PCs; compare fault classes
    # and all stable observable state rather than absolute instruction addresses.
    return (a.fault is not None and a.fault == b.fault
            and a.preserved == b.preserved and a.data == b.data
            and a.reads == b.reads and a.writes == b.writes)


def run(code_path: Path, output: Path, seed: int = SEEDS[0], samples: int = 256) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    reference = verify_reference(image, rows, game["code_sha256"])
    source = ROOT / "experiments/semantic_equivalence/field_roundtrip_predicate_candidates.cpp"
    build = compile_tu_armv6k(source, output / "field_roundtrip_predicate_candidates.o", ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    compiled = {}
    for symbol, (blob, relocations) in extract_elf_functions_detailed(
            output / "field_roundtrip_predicate_candidates.o").items():
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        validate_leaf(blob)
        compiled[symbol] = blob
    required = {s[k] for s in SPECS.values() for k in ("symbol", "negative")}
    if required - compiled.keys():
        raise ValueError(f"Missing candidate symbols: {sorted(required - compiled.keys())}")

    results, controls, faults = [], [], []
    for address, spec in SPECS.items():
        returns_value = True
        original = Runner(image, address)
        candidate = Runner(image, address, compiled[spec["symbol"]])
        failure = None
        comparisons = 0
        for case in make_cases(address, seed, samples):
            reason = difference(original.run(case), candidate.run(case), returns_value=returns_value)
            comparisons += 1
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
        result = {"address": hex(address), "candidate": spec["symbol"],
                  "original_bytes": spec["size"], "candidate_bytes": len(compiled[spec["symbol"]]),
                  "comparisons": comparisons, "passed": failure is None, "failure": failure}
        if address in (0x00146CE0, 0x00146D10):
            result["field_read_and_write_same_address"] = True
            result["reads_per_success"] = spec["width"]
            result["writes_per_success"] = spec["width"]
        results.append(result)

        control = next(make_cases(address, seed, 1))
        if address == 0x00146CE0:
            # The wrong offset is deliberately distinct from the read field.
            regs = list(control.registers); regs[1] = 0xBEEF
            memory = bytearray(control.data)
            struct.pack_into("<H", memory, regs[0] - DATA + 0x34, 0x1234)
            struct.pack_into("<H", memory, regs[0] - DATA + 0x38, 0x5678)
            control = Case("wrong-halfword-offset", tuple(regs), bytes(memory), control.stack, control.nzcv)
        elif address == 0x00146D10:
            memory = bytearray(control.data)
            memory[control.registers[0] - DATA + 0x38] = 0x80
            control = Case("signed-byte-boundary-80", control.registers, bytes(memory), control.stack, control.nzcv)
        else:
            memory = bytearray(control.data)
            struct.pack_into("<I", memory, control.registers[0] - DATA, 2)
            control = Case("wrong-predicate-value", control.registers, bytes(memory), control.stack, control.nzcv)
        negative = Runner(image, address, compiled[spec["negative"]])
        reason = difference(original.run(control), negative.run(control), returns_value=True)
        controls.append({"address": hex(address), "negative": spec["negative"],
                         "detected": reason is not None, "reason": reason})

        fault_case = _fault_probe(address, seed)
        fault_a, fault_b = original.run(fault_case), candidate.run(fault_case)
        matched = _fault_parity(fault_a, fault_b)
        faults.append({"address": hex(address), "case": fault_case.label,
                       "original_fault": fault_a.fault, "candidate_fault": fault_b.fault,
                       "faults_match": matched, "partial_write_parity": fault_a.data == fault_b.data})

    report = {
        "experiment": "field_roundtrip_predicate_leaves", "code_sha256": reference["code_sha256"],
        "seed": seed, "random_samples": samples, "reference": reference,
        "functions": results, "negative_controls": controls, "fault_probes": faults,
        "direct_bl_callers": {hex(a): [] for a in SPECS},
        "limitations": [
            "No direct ARM BL xrefs were found by a bounded linear Capstone sweep; no caller window is claimed.",
            "Only aligned ordinary RAM, selected value boundaries, and seeded samples were exercised.",
            "NZCV is not compared because no verified caller flag contract is available.",
            "Faulting probes compare fault class and observable state, not relocated PC addresses.",
            "C++ candidates remain isolated; there is no whole-game equivalence or production integration claim.",
        ],
    }
    report["passed"] = (all(f["passed"] for f in results)
                         and all(c["detected"] for c in controls)
                         and all(f["faults_match"] and f["partial_write_parity"] for f in faults))
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--output", type=Path, default=Path("build/semantic-equivalence/field-roundtrip-predicate/seed-20261024"))
    parser.add_argument("--seed", type=int, default=SEEDS[0])
    parser.add_argument("--samples", type=int, default=256)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed, args.samples)
    print(json.dumps({"passed": report["passed"], "seed": report["seed"],
                      "comparisons": sum(f["comparisons"] for f in report["functions"]),
                      "output": str(args.output)}))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
