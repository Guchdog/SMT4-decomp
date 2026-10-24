#!/usr/bin/env python3
"""Differential experiment for four small scalar field predicates.

The original hash-pinned code.bin is the oracle. Outputs are local-only under
ignored build/ paths. Caller windows start at the pinned BL itself: they verify
that the real caller consumes r0 in cmp/conditional-branch, but intentionally do
not claim to validate global/object setup instructions that precede the BL.
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

U32_MASK = 0xFFFFFFFF
FUNCTIONS = {
    0x0014E634: ("candidate_0014e634", 20,
                 (("ldr", "r0, [r0]"), ("cmp", "r0, #5"),
                  ("moveq", "r0, #1"), ("movne", "r0, #0"), ("bx", "lr")),
                 0, 5, True, "wrong_constant_0014e634"),
    0x003358E0: ("candidate_003358e0", 20,
                 (("ldr", "r0, [r0, #0xc]"), ("cmp", "r0, #4"),
                  ("moveq", "r0, #1"), ("movne", "r0, #0"), ("bx", "lr")),
                 0x0C, 4, True, "wrong_constant_003358e0"),
    0x0034C9E0: ("candidate_0034c9e0", 20,
                 (("ldr", "r0, [r0, #0x2c]"), ("cmp", "r0, #4"),
                  ("moveq", "r0, #1"), ("movne", "r0, #0"), ("bx", "lr")),
                 0x2C, 4, True, "wrong_constant_0034c9e0"),
    0x0034CB7C: ("candidate_0034cb7c", 20,
                 (("ldr", "r0, [r0, #0x2c]"), ("cmp", "r0, #1"),
                  ("moveq", "r0, #0"), ("movne", "r0, #1"), ("bx", "lr")),
                 0x2C, 1, False, "wrong_sense_0034cb7c"),
}

# Each window begins exactly at the real BL and includes the caller's cmp and
# branch consuming r0. stop is either the branch target or fallthrough PC.
CALLER_WINDOWS = {
    0x0014E634: {
        "site": 0x002C5EF4, "stop": (0x002C5F04, 0x002C5F20),
        "instructions": (
            (0x002C5EF4, "bl", "#0x14e634"),
            (0x002C5EF8, "cmp", "r0, #0"),
            (0x002C5EFC, "mov", "r0, #0"),
            (0x002C5F00, "beq", "#0x2c5f20"),
        ),
        "consumption": "cmp r0,#0 then beq; MOV does not overwrite flags",
    },
    0x003358E0: {
        "site": 0x003D2BF0, "stop": (0x003D2C00, 0x003D2C8C),
        "instructions": (
            (0x003D2BF0, "bl", "#0x3358e0"),
            (0x003D2BF4, "cmp", "r0, #0"),
            (0x003D2BF8, "nop", ""),
            (0x003D2BFC, "beq", "#0x3d2c8c"),
        ),
        "consumption": "cmp r0,#0 then beq",
    },
    0x0034C9E0: {
        "site": 0x00226F90, "stop": (0x00226FA0, 0x002270C0),
        "instructions": (
            (0x00226F90, "bl", "#0x34c9e0"),
            (0x00226F94, "cmp", "r0, #0"),
            (0x00226F98, "mov", "r7, #0"),
            (0x00226F9C, "beq", "#0x2270c0"),
        ),
        "consumption": "cmp r0,#0 then beq; MOV does not overwrite flags",
    },
    0x0034CB7C: {
        "site": 0x003DD21C, "stop": (0x003DD228, 0x003DD334),
        "instructions": (
            (0x003DD21C, "bl", "#0x34cb7c"),
            (0x003DD220, "cmp", "r0, #0"),
            (0x003DD224, "beq", "#0x3dd334"),
        ),
        "consumption": "cmp r0,#0 then beq",
    },
}


@dataclass(frozen=True)
class Spec:
    address: int
    symbol: str
    size: int
    field_offset: int
    expected: int
    equality: bool
    negative_symbol: str


def _specs():
    return [Spec(a, values[0], values[1], values[3], values[4], values[5], values[6])
            for a, values in FUNCTIONS.items()]


def _instructions(image: bytes, address: int, size: int):
    offset = address - TEXT
    raw = image[offset:offset + size]
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    return list(cs.disasm(raw, address))


def verify_reference(image: bytes, expected_sha256: str, rows: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if not expected_sha256 or digest != expected_sha256:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    by_address = {int(row["address"], 16): row for row in rows}
    result = {}
    for address, values in FUNCTIONS.items():
        symbol, size, expected, *_ = values
        row = by_address.get(address)
        if row is None or int(row["size"]) != size or row["status"] != "matching":
            raise ValueError(f"Ledger entry missing/changed at {address:#010x}")
        instructions = _instructions(image, address, size)
        decoded = tuple((item.mnemonic.lower(), item.op_str.lower()) for item in instructions)
        if decoded != expected or sum(item.size for item in instructions) != size:
            raise ValueError(f"Original instructions changed at {address:#010x}")
        result[hex(address)] = {
            "size": size,
            "symbol": symbol,
            "instructions": [f"{mnemonic} {operands}".strip()
                             for mnemonic, operands in expected],
            "function_sha256": hashlib.sha256(
                image[address - TEXT:address - TEXT + size]).hexdigest(),
            "ledger_name": row["name"],
            "category": row["category"],
        }
    return {"code_sha256": digest, "functions": result}


def verify_callers(image: bytes, expected_sha256: str) -> dict:
    if hashlib.sha256(image).hexdigest() != expected_sha256:
        raise ValueError("caller evidence SHA-256 does not match code.bin")
    result = {}
    for address, window in CALLER_WINDOWS.items():
        actual = []
        for site, mnemonic, operands in window["instructions"]:
            instruction = _instructions(image, site, 4)
            if len(instruction) != 1 or (instruction[0].mnemonic.lower(),
                                         instruction[0].op_str.lower()) != (
                                             mnemonic, operands):
                raise ValueError(f"caller consumer/setup drift at {site:#010x}")
            actual.append({"address": hex(site), "mnemonic": mnemonic,
                           "operands": operands,
                           "bytes": instruction[0].bytes.hex()})
        result[hex(address)] = {
            "callsite": hex(window["site"]),
            "stops": [hex(pc) for pc in window["stop"]],
            "consumption": window["consumption"],
            "scope_limit": (
                "Starts at the pinned BL; proves caller r0 consumption and branch, "
                "not the preceding global/object argument setup. r0 is supplied "
                "as a valid test-object pointer."
            ),
            "instructions": actual,
        }
    return result


def make_cases(spec: Spec, seed: int, samples: int = 64):
    if samples < 0:
        raise ValueError("samples must be non-negative")
    rng = random.Random(seed ^ spec.address)
    base = DATA + 0x100
    values = [0, 1, spec.expected - 1, spec.expected, spec.expected + 1,
              0x7FFFFFFF, 0x80000000, U32_MASK]
    for index, value in enumerate(values):
        memory = bytearray(rng.randbytes(DATA_SIZE))
        pointer = base + (index % 8) * 4
        value &= U32_MASK
        memory[pointer - DATA + spec.field_offset:pointer - DATA + spec.field_offset + 4] = value.to_bytes(4, "little")
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0] = pointer
        yield Case(f"boundary-{index}-value-{value:08x}", tuple(regs), bytes(memory),
                   rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)
    for index in range(samples):
        memory = bytearray(rng.randbytes(DATA_SIZE))
        pointer = base + (index % 8) * 4
        value = rng.getrandbits(32)
        memory[pointer - DATA + spec.field_offset:pointer - DATA + spec.field_offset + 4] = value.to_bytes(4, "little")
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0] = pointer
        yield Case(f"random-{index}", tuple(regs), bytes(memory),
                   rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def _compare(original: Runner, candidate: Runner, case: Case):
    return difference(original.run(case), candidate.run(case), returns_value=True)


def run(code_path: Path, output: Path, seed: int = 20261024,
        samples: int = 64) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    reference = verify_reference(image, game["code_sha256"], rows)
    caller_evidence = verify_callers(image, game["code_sha256"])

    source = ROOT / "experiments/semantic_equivalence/scalar_predicate_candidates.cpp"
    build = compile_tu_armv6k(source, output / "scalar_predicate_candidates.o", ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    compiled = {}
    for symbol, (code, relocations) in extract_elf_functions_detailed(
            output / "scalar_predicate_candidates.o").items():
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        validate_leaf(code)
        compiled[symbol] = code

    required = {spec.symbol for spec in _specs()} | {
        spec.negative_symbol for spec in _specs()
    }
    missing = required - compiled.keys()
    if missing:
        raise ValueError(f"Missing candidate symbols: {sorted(missing)}")

    functions = []
    for spec in _specs():
        original = Runner(image, spec.address)
        candidate = Runner(image, spec.address, compiled[spec.symbol])
        count = 0
        failure = None
        for case in make_cases(spec, seed, samples):
            reason = _compare(original, candidate, case)
            count += 1
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
        functions.append({"address": hex(spec.address), "candidate": spec.symbol,
                          "original_bytes": spec.size,
                          "candidate_bytes": len(compiled[spec.symbol]),
                          "passed": failure is None, "cases": count,
                          "failure": failure})
        print(json.dumps(functions[-1]), flush=True)

    negative_controls = []
    for spec in _specs():
        case = next(case for case in make_cases(spec, seed, 0)
                    if int.from_bytes(case.data[case.registers[0] - DATA + spec.field_offset:
                                                  case.registers[0] - DATA + spec.field_offset + 4],
                                      "little") == spec.expected)
        wrong = Runner(image, spec.address, compiled[spec.negative_symbol])
        reason = _compare(Runner(image, spec.address), wrong, case)
        negative_controls.append({"address": hex(spec.address),
                                  "control": spec.negative_symbol,
                                  "detected": reason is not None,
                                  "reason": reason,
                                  "expected_reason": "return value differs"})

    caller_results = []
    for spec in _specs():
        window = CALLER_WINDOWS[spec.address]
        address = DATA + 0x100
        for value in (spec.expected, (spec.expected + 1) & U32_MASK):
            memory = bytearray(DATA_SIZE)
            memory[0x100 + spec.field_offset:0x104 + spec.field_offset] = value.to_bytes(4, "little")
            regs = [0] * 13
            regs[0] = address
            # Non-r0 caller state is intentionally benign; execution starts at BL,
            # so the external/global argument setup is outside this checked window.
            case = Case(f"caller-{spec.address:08x}-value-{value}", tuple(regs),
                        bytes(memory), bytes(STACK_SIZE), 0)
            original = Runner(image, spec.address)
            candidate = Runner(image, spec.address, compiled[spec.symbol])
            original_result = original.run(case, start=window["site"],
                                           stops=window["stop"], budget=64)
            candidate_result = candidate.run(case, start=window["site"],
                                             stops=window["stop"], budget=64)
            reason = difference(original_result, candidate_result,
                                returns_value=False, caller_window=True,
                                compare_flags=True)
            caller_results.append({"address": hex(spec.address),
                                   "callsite": hex(window["site"]),
                                   "input": f"0x{value:08x}",
                                   "expected_branch_pc": hex(original_result.pc),
                                   "passed": reason is None,
                                   "reason": reason})
    report = {
        "experiment": "four_scalar_field_predicates",
        "code_sha256": reference["code_sha256"],
        "seed": seed, "random_samples_per_function": samples,
        "reference": reference,
        "caller_evidence": caller_evidence,
        "functions": functions,
        "negative_controls": negative_controls,
        "caller_windows": caller_results,
        "passed": (all(item["passed"] for item in functions)
                   and all(item["detected"] for item in negative_controls)
                   and all(item["passed"] for item in caller_results)),
        "limitations": [
            "Tests use aligned ordinary RAM and only pinned observed callers.",
            "Caller tests start at the original BL and supply r0 directly; preceding global/object setup is not executed.",
            "This is isolated ARM execution evidence, not a whole-game equivalence proof or production integration.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--output", type=Path, default=Path("build/semantic-equivalence/scalar-predicates"))
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--samples", type=int, default=64)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed, args.samples)
    print(json.dumps({"passed": report["passed"],
                      "function_count": len(report["functions"]),
                      "comparisons": sum(x["cases"] for x in report["functions"]),
                      "caller_windows": len(report["caller_windows"]),
                      "output": str(args.output)}))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
