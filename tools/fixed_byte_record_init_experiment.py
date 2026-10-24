#!/usr/bin/env python3
"""Two-seed ordinary-memory differential for two fixed byte record writers."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference,
)
from tools.semantic_experiment_support import compile_candidate_symbols, load_pinned_reference

FUNCTIONS = {
    0x002B63BC: ("candidate_002b63bc", bytes((0, 0, 0, 0, 15, 15, 15, 0,
                                                0, 0, 0, 0, 0, 15, 15, 15, 0, 0))),
    0x002B6410: ("candidate_002b6410", bytes((1, 0, 0, 0, 0, 3, 15, 0,
                                                0, 1, 0, 0, 0, 0, 3, 15, 0, 0))),
}
SIZE = 84
SIZES = {0x002B63BC: 84, 0x002B6410: 92}
SOURCE = ROOT / "experiments/semantic_equivalence/fixed_byte_record_init_candidates.cpp"
SEEDS = (7, 20261024)


def expected_instructions(address: int, values: bytes):
    prelude = {
        0x002B63BC: {0: (("mov", "r1, #0"),),
                     3: (("mov", "r2, #0xf"),)},
        0x002B6410: {0: (("mov", "r2, #1"), ("mov", "r1, #0")),
                     4: (("mov", "r3, #3"),),
                     5: (("mov", "ip, #0xf"),)},
    }[address]
    register = ({0: "r1", 15: "r2"} if address == 0x002B63BC else
                {0: "r1", 1: "r2", 3: "r3", 15: "ip"})
    result = []
    for offset, value in enumerate(values):
        result.extend(prelude.get(offset, ()))
        location = "[r0]" if offset == 0 else (
            f"[r0, #{offset}]" if offset < 10 else f"[r0, #0x{offset:x}]")
        result.append(("strb", f"{register[value]}, {location}"))
    result.append(("bx", "lr"))
    return tuple(result)


def verify_reference(image: bytes, game_info: dict, ledger: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != game_info["code_sha256"]:
        raise ValueError("code.bin SHA-256 differs from configured pin")
    by_address = {int(row["address"], 16): row for row in ledger}
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    functions = {}
    for address, (symbol, output) in FUNCTIONS.items():
        size = SIZES[address]
        row = by_address.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != size:
            raise ValueError(f"missing matching {size}-byte ledger row at {address:#010x}")
        start = address - TEXT
        body = image[start:start + size]
        decoded = tuple((x.mnemonic.lower(), x.op_str.lower())
                        for x in decoder.disasm(body, address))
        expected = expected_instructions(address, output)
        if decoded != expected:
            raise ValueError(f"reference instruction sequence changed at {address:#010x}: {decoded}")
        functions[hex(address)] = {
            "name": row["name"], "size": size,
            "sha256": hashlib.sha256(body).hexdigest(), "bytes": body.hex(),
            "output_bytes": output.hex(),
            "contract": "Writes exactly 18 output bytes in increasing address order; no reads; returns with r0 unchanged.",
        }
    return {"code_sha256": digest, "functions": functions}


def _case(address: int, seed: int, index: int, record_offset: int) -> Case:
    rng = random.Random(seed ^ address ^ (index * 0x9E3779B1))
    data = bytearray(rng.randbytes(DATA_SIZE))
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0] = DATA + record_offset
    nzcv = (0, 0x40000000, 0x80000000, 0xC0000000)[index % 4]
    return Case(f"case-{index}-offset-{record_offset:#x}", tuple(regs), bytes(data),
                rng.randbytes(STACK_SIZE), nzcv)


def _compare(original, candidate) -> str | None:
    if original.fault or candidate.fault:
        if bool(original.fault) != bool(candidate.fault):
            return "fault outcome differs"
        if original.stopped != candidate.stopped:
            return "fault/return state differs"
        if original.preserved != candidate.preserved:
            return "callee-saved state differs on fault"
        if original.data != candidate.data:
            return "partial data differs on fault"
        if original.reads != candidate.reads or original.writes != candidate.writes:
            return "partial access footprint differs on fault"
        return None
    return difference(original, candidate, returns_value=False, compare_flags=False)


def run(code_path: Path, output: Path, seed: int) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.game_info, pinned.ledger)
    symbols = compile_candidate_symbols(
        SOURCE, output / "fixed_byte_record_init_candidates.o", ROOT,
        {symbol for symbol, _ in FUNCTIONS.values()} |
        {"negative_wrong_value_record", "negative_omit_last_record"})
    cases = []
    for i in range(72):
        cases.append((f"random-{i}", 0x100 + (i % 16)))
    cases.extend((f"late-fault-{length}", DATA_SIZE - length) for length in (1, 5, 17))
    results = []
    for address, (symbol, _) in FUNCTIONS.items():
        original_runner = Runner(pinned.image, address)
        candidate_runner = Runner(pinned.image, address, symbols[symbol])
        failure = None
        fault_count = 0
        for index, (label, offset) in enumerate(cases):
            case = _case(address, seed, index, offset)
            original = original_runner.run(case)
            candidate = candidate_runner.run(case)
            if original.fault:
                fault_count += 1
            reason = _compare(original, candidate)
            if reason:
                failure = {"case": label, "reason": reason,
                           "original_fault": original.fault,
                           "candidate_fault": candidate.fault}
                break
        results.append({"address": hex(address), "candidate": symbol,
                        "original_bytes": SIZES[address],
                        "candidate_bytes": len(symbols[symbol]),
                        "cases": len(cases) if failure is None else index + 1,
                        "fault_cases": fault_count,
                        "passed": failure is None, "failure": failure})
    control_case = _case(0x002B6410, seed, 101, 0x180)
    base_runner = Runner(pinned.image, 0x002B6410)
    base = base_runner.run(control_case)
    negatives = []
    for symbol, label in (("negative_wrong_value_record", "wrong fixed byte"),
                          ("negative_omit_last_record", "omitted final store")):
        altered = Runner(pinned.image, 0x002B6410, symbols[symbol]).run(control_case)
        negatives.append({"candidate": symbol, "detects": label,
                          "detected": base.data != altered.data})
    report = {
        "schema": 1, "experiment": "fixed_byte_record_initializer_pair",
        "passed": all(row["passed"] for row in results) and all(row["detected"] for row in negatives),
        "scope": "two pinned ordinary-memory ARM leaves; isolated differential, not game boot",
        "reference_sha256": pinned.game_info["code_sha256"],
        "reference_functions": reference["functions"],
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "seed": seed, "cases_per_function": len(cases),
        "function_comparisons": sum(row["cases"] for row in results),
        "case_mix": {"random_initialized_records": 72, "late_fault_prefixes": 3},
        "functions": results, "negative_controls": negatives,
        "caller_windows": [],
        "limitations": ["Finite seeded tests do not prove equivalence for all inputs.",
                        "Only ordinary RAM, isolated ARM11 execution and the pinned image were tested.",
                        "No caller windows, emulator boot, ledger or production code changes."],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
