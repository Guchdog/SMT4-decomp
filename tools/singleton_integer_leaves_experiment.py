#!/usr/bin/env python3
"""Differentially test three isolated, non-byte-identical integer leaf candidates.

The pinned private code image remains the oracle. This experiment does not edit
production sources, the byte-identical ledger, or the game image.
"""
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
    0x00130FE8: {
        "size": 16, "symbol": "candidate_00130fe8", "negative": "wrong_increment_00130fe8",
        "sha256": "ba1c527a558d0543330cb69d86d7f7c482df407265b4c1a17ff7256affb66b4d",
        "instructions": (("mov", "r0, #0x144"), ("add", "r1, r1, #1"), ("mul", "r0, r1, r0"), ("bx", "lr")),
    },
    0x0015C408: {
        "size": 16, "symbol": "candidate_0015c408", "negative": "wrong_store_offset_0015c408",
        "sha256": "c8604614c175406c86f7cbd445e3a36b97d84719993769144a6926a4a653e1f6",
        "instructions": (("str", "r1, [r0, #0x1c]"), ("add", "r1, r1, r2"), ("str", "r1, [r0, #0x20]"), ("bx", "lr")),
    },
    0x002A17D4: {
        "size": 16, "symbol": "candidate_002a17d4", "negative": "wrong_bit_002a17d4",
        "sha256": "e62a700e728d9043c13fe9edc53b30a5200d065bf22c3bb4a02ca3533c03ef28",
        "instructions": (("ldr", "r0, [r0, #0x754]"), ("and", "r0, r0, #0x10000"), ("lsr", "r0, r0, #0x10"), ("bx", "lr")),
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
        pinned[hex(address)] = {
            "size": spec["size"], "sha256": spec["sha256"],
            "instructions": [f"{m} {o}" for m, o in decoded], "ledger_name": row["name"],
            "category": row["category"],
        }
    return {"code_sha256": digest, "functions": pinned}


def _case(label: str, regs: list[int], memory: bytearray, rng: random.Random, nzcv: int) -> Case:
    return Case(label, tuple(regs), bytes(memory), rng.randbytes(STACK_SIZE), nzcv << 28)


def make_cases(address: int, seed: int, samples: int = 256):
    if samples < 0:
        raise ValueError("samples must be non-negative")
    rng = random.Random(seed ^ address)
    if address == 0x00130FE8:
        edge = (0, 1, 0xFFFFFFFE, U32, 0x7FFFFFFF, 0x80000000, 0xFFFFFEBC)
        for i, value in enumerate(edge + tuple(rng.getrandbits(32) for _ in range(samples))):
            regs = [rng.getrandbits(32) for _ in range(13)]
            regs[1] = value
            yield Case(f"multiply-{i}-{value:08x}", tuple(regs), rng.randbytes(DATA_SIZE),
                       rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)
    elif address == 0x0015C408:
        edge = ((0, 0), (U32, 1), (0x7FFFFFFF, 1), (0x80000000, 0x80000000),
                (0x11223344, 0x01020304))
        pairs = edge + tuple((rng.getrandbits(32), rng.getrandbits(32)) for _ in range(samples))
        for i, (first, delta) in enumerate(pairs):
            regs = [rng.getrandbits(32) for _ in range(13)]
            ptr = DATA + 0x100 + (i % 16) * 4
            regs[0], regs[1], regs[2] = ptr, first, delta
            memory = bytearray(rng.randbytes(DATA_SIZE))
            yield _case(f"ordered-store-{i}", regs, memory, rng, rng.getrandbits(4))
    elif address == 0x002A17D4:
        edge = (0, 1, 0xFFFF, 0x10000, 0x20000, 0xFFFFFFFF, 0x80000000, 0xFFFF0000)
        for i, word in enumerate(edge + tuple(rng.getrandbits(32) for _ in range(samples))):
            memory = bytearray(rng.randbytes(DATA_SIZE))
            ptr = DATA + 0x100 + (i % 16) * 4
            struct.pack_into("<I", memory, ptr - DATA + 0x754, word)
            regs = [rng.getrandbits(32) for _ in range(13)]
            regs[0] = ptr
            yield _case(f"extract-bit16-{i}-{word:08x}", regs, memory, rng, rng.getrandbits(4))
    else:
        raise ValueError(f"No case generator for {address:#010x}")


def _fault_case(address: int, seed: int) -> Case:
    rng = random.Random(seed ^ address ^ 0xF017)
    memory = bytearray(rng.randbytes(DATA_SIZE))
    regs = [rng.getrandbits(32) for _ in range(13)]
    if address == 0x0015C408:
        regs[0] = DATA + DATA_SIZE - 0x20  # first word mapped, second word unmapped
        regs[1], regs[2] = 0xAABBCCDD, 0x11223344
    elif address == 0x002A17D4:
        regs[0] = DATA + DATA_SIZE - 0x750  # [object+0x754] lies four bytes out of map
    else:
        raise ValueError("This address has no relevant memory-fault probe")
    return Case("partial-store-fault" if address == 0x0015C408 else "unmapped-field-read",
                tuple(regs), bytes(memory), rng.randbytes(STACK_SIZE), 0xA0000000)


def run(code_path: Path, output: Path, seed: int = 20261024, samples: int = 256) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    reference = verify_reference(image, rows, game["code_sha256"])
    source = ROOT / "experiments/semantic_equivalence/singleton_integer_leaves_candidates.cpp"
    build = compile_tu_armv6k(source, output / "singleton_integer_leaves_candidates.o", ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    compiled = {}
    for symbol, (blob, relocations) in extract_elf_functions_detailed(
            output / "singleton_integer_leaves_candidates.o").items():
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        validate_leaf(blob)
        compiled[symbol] = blob
    required = {spec["symbol"] for spec in SPECS.values()} | {spec["negative"] for spec in SPECS.values()}
    if required - compiled.keys():
        raise ValueError(f"Missing candidate symbols: {sorted(required - compiled.keys())}")

    results = []
    controls = []
    faults = []
    for address, spec in SPECS.items():
        original = Runner(image, address)
        candidate = Runner(image, address, compiled[spec["symbol"]])
        compared = 0
        failure = None
        for case in make_cases(address, seed, samples):
            reason = difference(original.run(case), candidate.run(case), returns_value=address != 0x0015C408)
            compared += 1
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
        result = {"address": hex(address), "symbol": spec["symbol"],
                  "original_bytes": spec["size"], "candidate_bytes": len(compiled[spec["symbol"]]),
                  "comparisons": compared, "passed": failure is None, "failure": failure}
        if address == 0x0015C408:
            # A separate probe checks exact write-set parity even though r0 is not a return contract.
            sample = next(make_cases(address, seed, 1))
            a, b = original.run(sample), candidate.run(sample)
            result["write_bytes"] = len(a.writes)
            result["read_bytes"] = len(a.reads)
            result["access_sets_match"] = a.reads == b.reads and a.writes == b.writes
            result["write_order_observable"] = "No; this runner compares final access sets, not event sequence"
            result["passed"] = result["passed"] and result["access_sets_match"]
        results.append(result)

        # Each wrong reconstruction is tested with a value guaranteed to expose its targeted error.
        if address == 0x00130FE8:
            control = next(make_cases(address, seed, 0))
        elif address == 0x0015C408:
            control = next(make_cases(address, seed, 4))
            regs = list(control.registers); regs[1], regs[2] = 5, 9
            control = Case("distinct-store-values", tuple(regs), control.data, control.stack, control.nzcv)
        else:
            control = next(make_cases(address, seed, 0))
            memory = bytearray(control.data)
            struct.pack_into("<I", memory, control.registers[0] - DATA + 0x754, 0x00010000)
            control = Case("targeted-bit16-control", control.registers, bytes(memory),
                           control.stack, control.nzcv)
        negative = Runner(image, address, compiled[spec["negative"]])
        reason = difference(original.run(control), negative.run(control),
                            returns_value=address != 0x0015C408)
        expected = "data memory differs" if address == 0x0015C408 else "return value differs"
        controls.append({"address": hex(address), "negative": spec["negative"],
                         "detected": reason == expected, "reason": reason, "expected": expected})

        if address in (0x0015C408, 0x002A17D4):
            fault = _fault_case(address, seed)
            fault_a, fault_b = original.run(fault), candidate.run(fault)
            # Fault PCs differ because the C++ body is relocated. Compare fault
            # class and all observable state/footprints instead of requiring a
            # matching instruction address.
            matched = (fault_a.fault is not None and fault_b.fault is not None
                       and fault_a.fault == fault_b.fault
                       and fault_a.preserved == fault_b.preserved
                       and fault_a.data == fault_b.data
                       and fault_a.reads == fault_b.reads
                       and fault_a.writes == fault_b.writes
                       and (address == 0x0015C408 or fault_a.result == fault_b.result))
            faults.append({"address": hex(address), "case": fault.label,
                           "original_fault": fault_a.fault, "candidate_fault": fault_b.fault,
                           "faults_match": matched,
                           "partial_write_parity": address != 0x0015C408 or fault_a.data == fault_b.data})

    report = {
        "experiment": "singleton_integer_leaves",
        "code_sha256": reference["code_sha256"], "seed": seed, "random_samples_per_function": samples,
        "reference": reference, "functions": results, "negative_controls": controls,
        "fault_probes": faults,
        "direct_bl_callers": {hex(a): [] for a in SPECS},
        "observables": ["r0 for value-returning leaves", "callee-saved GPRs and SP",
                        "memory contents", "read/write byte footprint", "return/fault state"],
        "limitations": [
            "No direct ARM BL xrefs were found by the bounded linear Capstone sweep; no caller window is claimed.",
            "NZCV is not compared because no verified caller flag contract is available.",
            "The store runner checks final access sets and partial-fault memory, not temporal bus-event ordering.",
            "Only aligned ordinary RAM probes are covered; no MMIO, complete-game, or whole-program proof is claimed.",
            "C++ candidates remain isolated; production source and byte-identical ledger are unchanged.",
        ],
    }
    report["passed"] = (all(x["passed"] for x in results)
                         and all(x["detected"] for x in controls)
                         and all(x["faults_match"] and x["partial_write_parity"] for x in faults))
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--output", type=Path, default=Path("build/semantic-equivalence/singleton-integer-leaves/seed-20261024"))
    parser.add_argument("--seed", type=int, default=SEEDS[0])
    parser.add_argument("--samples", type=int, default=256)
    args = parser.parse_args()
    result = run(args.code, args.output, args.seed, args.samples)
    print(json.dumps({"passed": result["passed"], "seed": result["seed"],
                      "comparisons": sum(f["comparisons"] for f in result["functions"]),
                      "output": str(args.output)}))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
