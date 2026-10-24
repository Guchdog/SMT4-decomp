#!/usr/bin/env python3
"""Differentially test two signed-byte field getters against the pinned ARM image."""
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
    0x003E6368: {"offset": 0x556, "words": (0xE2800C05, 0xE1D005D6, 0xE12FFF1E),
                 "symbol": "candidate_003e6368"},
    0x003E8878: {"offset": 0x45E, "words": (0xE2800B01, 0xE1D005DE, 0xE12FFF1E),
                 "symbol": "candidate_003e8878"},
}
CONTROLS = ("wrong_offset", "wrong_width", "wrong_sign")


def verify_reference(image: bytes, ledger: list[dict[str, str]]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Unexpected code.bin SHA-256: {digest}")
    by_address = {int(row["address"], 16): row for row in ledger}
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    evidence = {}
    for address, spec in FUNCTIONS.items():
        row = by_address.get(address)
        if row is None or int(row["size"]) != 12 or row["status"] != "matching":
            raise ValueError(f"Ledger entry changed at {address:#010x}")
        original = image[address - TEXT:address - TEXT + 12]
        words = struct.unpack("<3I", original)
        if words != spec["words"]:
            raise ValueError(f"Instruction words changed at {address:#010x}: {words}")
        decoded = [(item.mnemonic, item.op_str) for item in decoder.disasm(original, address)]
        expected = [("add", "r0, r0, #0x500" if address == 0x003E6368
                     else "r0, r0, #0x400"),
                    ("ldrsb", f"r0, [r0, #0x{spec['offset'] & 0xff:x}]"),
                    ("bx", "lr")]
        if decoded != expected:
            raise ValueError(f"Instruction contract changed at {address:#010x}: {decoded}")
        evidence[hex(address)] = {
            "name": row["name"], "size": int(row["size"]),
            "effective_offset": hex(spec["offset"]),
            "instruction_words": [f"0x{x:08x}" for x in spec["words"]],
            "disassembly": decoded,
        }
    return {"code_sha256": digest, "functions": evidence}


def make_cases(address: int, samples: int, seed: int):
    if samples < 0:
        raise ValueError("samples must be non-negative")
    offset = FUNCTIONS[address]["offset"]
    rng = random.Random(seed ^ address)
    for index, low in enumerate((0, 1, 0x7F, 0x80, 0xFE, 0xFF)):
        data = bytearray(DATA_SIZE)
        base = 0x200 + (index % 8) * 4
        high = (0xA5 ^ index) & 0xFF
        data[base + offset] = low
        data[base + offset + 1] = high
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0] = DATA + base
        yield Case(f"boundary-{low:02x}-next-{high:02x}", tuple(regs), bytes(data),
                   rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)
    for index in range(samples):
        data = bytearray(rng.randbytes(DATA_SIZE))
        base = 0x200 + (index % 8) * 4
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0] = DATA + base
        yield Case(f"random-{index}", tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                   rng.getrandbits(4) << 28)


def _negative_case(address: int, seed: int) -> Case:
    offset = FUNCTIONS[address]["offset"]
    data = bytearray(DATA_SIZE)
    base = 0x180
    # Signed byte is -1; adjacent byte makes a signed halfword 0x7fff, and the
    # adjacent field makes the wrong-offset read +127.
    data[base + offset:base + offset + 2] = b"\xff\x7f"
    regs = [0] * 13
    regs[0] = DATA + base
    return Case(f"negative-controls-seed-{seed}", tuple(regs), bytes(data),
                bytes(STACK_SIZE), (seed & 0xF) << 28)


def _fault_case(address: int, seed: int) -> Case:
    offset = FUNCTIONS[address]["offset"]
    regs = [0] * 13
    regs[0] = DATA + DATA_SIZE - offset
    return Case(f"unmapped-effective-byte-seed-{seed}", tuple(regs), bytes(DATA_SIZE),
                bytes(STACK_SIZE), (seed & 0xF) << 28)


def run(code_path: Path, output: Path, seed: int, samples: int) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.ledger)
    compiled = compile_candidate_symbols(
        ROOT / "experiments/semantic_equivalence/signed_byte_pair_candidates.cpp",
        output / "signed_byte_pair_candidates.o", ROOT,
        [spec["symbol"] for spec in FUNCTIONS.values()] +
        [f"{control}_{address:08x}" for address in FUNCTIONS for control in CONTROLS])
    functions, negatives, faults = [], [], []
    for address, spec in FUNCTIONS.items():
        original = Runner(pinned.image, address)
        candidate = Runner(pinned.image, address, compiled[spec["symbol"]])
        count = 0
        failure = None
        for case in make_cases(address, samples, seed):
            old, new = original.run(case), candidate.run(case)
            reason = difference(old, new, returns_value=True)
            effective = case.registers[0] - DATA + spec["offset"]
            if not reason and (old.reads != frozenset((DATA + effective,)) or old.writes):
                reason = "unexpected byte read footprint or write"
            count += 1
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
        functions.append({"address": hex(address), "candidate": spec["symbol"],
                          "original_bytes": 12, "candidate_bytes": len(compiled[spec["symbol"]]),
                          "cases": count, "passed": failure is None, "failure": failure})

        case = _negative_case(address, seed)
        old = original.run(case)
        for control in CONTROLS:
            name = f"{control}_{address:08x}"
            bad = Runner(pinned.image, address, compiled[name]).run(case)
            reason = difference(old, bad, returns_value=True)
            negatives.append({"address": hex(address), "control": control,
                              "detected": reason is not None, "reason": reason})

        case = _fault_case(address, seed)
        old, new = original.run(case), candidate.run(case)
        same_fault = bool(old.fault) and bool(new.fault)
        fault_ok = (same_fault and old.writes == new.writes and not old.writes
                    and old.data == new.data)
        faults.append({"address": hex(address), "passed": fault_ok,
                       "original_fault": old.fault, "candidate_fault": new.fault,
                       "effective_address": hex(DATA + DATA_SIZE)})

    report = {
        "experiment": "signed_byte_field_getter_pair", "seed": seed,
        "random_samples_per_function": samples, "reference": reference,
        "functions": functions, "negative_controls": negatives,
        "fault_behavior": faults, "caller_windows": [],
        "passed": all(item["passed"] for item in functions + faults)
                  and all(item["detected"] for item in negatives),
        "limitations": [
            "Two isolated ARM-state leaf functions were tested; no caller window was added because no callsite was manually established.",
            "Valid tests use mapped ordinary RAM. A separate unmapped effective-byte case confirms both versions fault, but does not model hardware/MMIO behavior.",
            "ABI checks cover returned r0, callee-saved registers, SP, continuation, memory, and exact byte read footprint in the bounded harness.",
            "This is not whole-program or emulator evidence and does not integrate candidates into production.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--output", type=Path,
                        default=Path("build/semantic-equivalence/signed-byte-pair"))
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--samples", type=int, default=128)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed, args.samples)
    print(json.dumps({"passed": report["passed"], "functions": report["functions"],
                      "negative_controls": report["negative_controls"],
                      "fault_behavior": report["fault_behavior"]}, indent=2))


if __name__ == "__main__":
    main()
