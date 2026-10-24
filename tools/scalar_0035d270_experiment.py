#!/usr/bin/env python3
"""Bounded differential test for scalar selector 0x0035D270.

The hash-pinned original code.bin is the oracle. This isolated singleton does
not change production sources or the match ledger, and does not claim whole-game
equivalence or a verified caller context.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference, validate_leaf,
)

ADDRESS = 0x0035D270
SIZE = 20
SYMBOL = "candidate_0035d270"
NEGATIVE_SYMBOL = "wrong_zero_result_0035d270"
EXPECTED_CODE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
EXPECTED_FUNCTION_SHA256 = "20c6f495beebbbfe1dc9035359091341679775179b6df41e1657b91b968f52f1"
INSTRUCTIONS = (
    ("ldr", "r0, [r0, #0x18]"),
    ("cmp", "r0, #0"),
    ("moveq", "r0, #3"),
    ("movne", "r0, #1"),
    ("bx", "lr"),
)


@dataclass(frozen=True)
class Spec:
    address: int = ADDRESS
    field_offset: int = 0x18
    size: int = SIZE


def _instructions(image: bytes, address: int, size: int):
    raw = image[address - TEXT:address - TEXT + size]
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    return list(cs.disasm(raw, address))


def verify_reference(image: bytes, expected_sha256: str, rows: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if not expected_sha256 or digest != expected_sha256 or digest != EXPECTED_CODE_SHA256:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    by_address = {int(row["address"], 16): row for row in rows}
    row = by_address.get(ADDRESS)
    if row is None or int(row["size"]) != SIZE or row["status"] != "matching":
        raise ValueError(f"Ledger entry missing/changed at {ADDRESS:#010x}")
    decoded = tuple((item.mnemonic.lower(), item.op_str.lower())
                    for item in _instructions(image, ADDRESS, SIZE))
    if decoded != INSTRUCTIONS:
        raise ValueError(f"Original instructions changed at {ADDRESS:#010x}")
    raw = image[ADDRESS - TEXT:ADDRESS - TEXT + SIZE]
    function_digest = hashlib.sha256(raw).hexdigest()
    if function_digest != EXPECTED_FUNCTION_SHA256:
        raise ValueError("Function byte pin does not match the selected revision")
    return {
        "code_sha256": digest,
        "functions": {hex(ADDRESS): {
            "size": SIZE,
            "symbol": SYMBOL,
            "instructions": [f"{m} {o}".strip() for m, o in INSTRUCTIONS],
            "function_sha256": function_digest,
            "ledger_name": row["name"],
            "category": row["category"],
        }},
    }


def make_cases(seed: int, samples: int = 256):
    if samples < 0:
        raise ValueError("samples must be non-negative")
    rng = random.Random(seed ^ ADDRESS)
    base = DATA + 0x100
    boundaries = (0, 1, 2, 3, 0x7FFFFFFF, 0x80000000,
                  0xFFFFFFFE, 0xFFFFFFFF)
    for index, value in enumerate(boundaries):
        memory = bytearray(rng.randbytes(DATA_SIZE))
        pointer = base + (index % 8) * 4
        memory[pointer - DATA + 0x18:pointer - DATA + 0x1C] = value.to_bytes(4, "little")
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0] = pointer
        yield Case(f"boundary-{index}-value-{value:08x}", tuple(regs), bytes(memory),
                   rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)
    for index in range(samples):
        memory = bytearray(rng.randbytes(DATA_SIZE))
        pointer = base + (index % 8) * 4
        value = rng.getrandbits(32)
        memory[pointer - DATA + 0x18:pointer - DATA + 0x1C] = value.to_bytes(4, "little")
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0] = pointer
        yield Case(f"random-{index}", tuple(regs), bytes(memory),
                   rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def run(code_path: Path, output: Path, seed: int = 20261024,
        samples: int = 256) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    reference = verify_reference(image, game["code_sha256"], rows)

    source = ROOT / "experiments/semantic_equivalence/scalar_0035d270_candidate.cpp"
    build = compile_tu_armv6k(source, output / "scalar_0035d270_candidate.o", ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    compiled = {}
    for symbol, (code, relocations) in extract_elf_functions_detailed(
            output / "scalar_0035d270_candidate.o").items():
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        validate_leaf(code)
        compiled[symbol] = code
    missing = {SYMBOL, NEGATIVE_SYMBOL} - compiled.keys()
    if missing:
        raise ValueError(f"Missing candidate symbols: {sorted(missing)}")

    original = Runner(image, ADDRESS)
    candidate = Runner(image, ADDRESS, compiled[SYMBOL])
    count = 0
    failure = None
    for case in make_cases(seed, samples):
        reason = difference(original.run(case), candidate.run(case), returns_value=True)
        count += 1
        if reason:
            failure = {"case": case.label, "reason": reason}
            break

    # The negative control must disagree when the observed field is zero.
    control_case = next(case for case in make_cases(seed, 0)
                        if int.from_bytes(case.data[case.registers[0] - DATA + 0x18:
                                                     case.registers[0] - DATA + 0x1C],
                                          "little") == 0)
    negative_reason = difference(
        Runner(image, ADDRESS).run(control_case),
        Runner(image, ADDRESS, compiled[NEGATIVE_SYMBOL]).run(control_case),
        returns_value=True)
    negative_control = {
        "control": NEGATIVE_SYMBOL,
        "detected": negative_reason == "return value differs",
        "reason": negative_reason,
        "expected_reason": "return value differs",
    }
    function = {
        "address": hex(ADDRESS), "candidate": SYMBOL,
        "original_bytes": SIZE, "candidate_bytes": len(compiled[SYMBOL]),
        "passed": failure is None, "cases": count, "failure": failure,
    }
    report = {
        "experiment": "singleton_scalar_selector_0035d270",
        "code_sha256": reference["code_sha256"],
        "seed": seed, "random_samples": samples,
        "reference": reference, "function": function,
        "negative_control": negative_control,
        "passed": function["passed"] and negative_control["detected"],
        "observables": ["r0 return value", "callee-saved r4-r11 and SP",
                        "RAM contents", "read/write footprint", "return continuation"],
        "limitations": [
            "Tests use aligned ordinary RAM, with the 32-bit field at object+0x18 mapped.",
            "Only the isolated leaf is tested; no direct caller window is claimed or simulated.",
            "Condition flags are not compared: they are caller-clobbered and no verified caller contract is pinned.",
            "This bounded ARM execution evidence is not a whole-game equivalence proof or production integration.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--output", type=Path,
                        default=Path("build/semantic-equivalence/scalar-0035d270/seed-20261024"))
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--samples", type=int, default=256)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed, args.samples)
    print(json.dumps({"passed": report["passed"], "seed": report["seed"],
                      "comparisons": report["function"]["cases"],
                      "output": str(args.output)}))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
