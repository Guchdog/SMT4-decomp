#!/usr/bin/env python3
"""Two-seed differential for one signed-halfword range clamp leaf."""
from __future__ import annotations

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
from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference,
)
from tools.semantic_experiment_support import compile_candidate_symbols, load_pinned_reference

ADDRESS = 0x001285C4
SIZE = 76
SYMBOL = "candidate_001285c4"
SOURCE = ROOT / "experiments/semantic_equivalence/signed_halfword_range_clamp_candidate.cpp"
SEEDS = (7, 20261024)
EXPECTED = (
    ("ldrsh", "r1, [r0]"), ("cmp", "r1, #0x28"),
    ("movlt", "r1, #0x28"), ("strhlt", "r1, [r0]"),
    ("ldrsh", "r1, [r0, #2]"), ("cmp", "r1, #0x24"),
    ("movlt", "r1, #0x24"), ("strhlt", "r1, [r0, #2]"),
    ("ldrsh", "r2, [r0, #6]"), ("mov", "r1, #0x91"),
    ("cmp", "r2, #0x91"), ("strhgt", "r1, [r0, #6]"),
    ("ldrsh", "r2, [r0, #8]"), ("cmp", "r2, #0x91"),
    ("strhgt", "r1, [r0, #8]"),
    ("ldrsh", "r2, [r0, #0xa]"), ("cmp", "r2, #0x91"),
    ("strhgt", "r1, [r0, #0xa]"), ("bx", "lr"),
)
FIELDS = (0, 1, 3, 4, 5)


def verify_reference(image: bytes, game_info: dict, ledger: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != game_info["code_sha256"]:
        raise ValueError("code.bin SHA-256 differs from configured pin")
    row = next((item for item in ledger if int(item["address"], 16) == ADDRESS), None)
    if row is None or row["status"].strip() != "matching" or int(row["size"]) != SIZE:
        raise ValueError("missing matching 76-byte ledger row at 0x001285c4")
    start = ADDRESS - TEXT
    body = image[start:start + SIZE]
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    actual = tuple((insn.mnemonic.lower(), insn.op_str.lower())
                   for insn in decoder.disasm(body, ADDRESS))
    if actual != EXPECTED:
        raise ValueError(f"reference instruction sequence changed: {actual}")
    return {"code_sha256": digest, "functions": {hex(ADDRESS): {
        "name": row["name"], "size": SIZE,
        "sha256": hashlib.sha256(body).hexdigest(), "bytes": body.hex(),
        "semantics": "Signed halfwords at offsets 0 and 2 are clamped upward to 40 and 36; offsets 6, 8, and 10 are clamped downward to 145. Offsets 4 and all other bytes are untouched.",
    }}}


def _case(seed: int, index: int, values: tuple[int, ...]) -> Case:
    rng = random.Random(seed ^ (index * 0x9E3779B1))
    data = bytearray(rng.randbytes(DATA_SIZE))
    for offset, value in zip(FIELDS, values):
        struct.pack_into("<h", data, 0x100 + offset * 2, value)
    registers = [rng.getrandbits(32) for _ in range(13)]
    registers[0] = DATA + 0x100
    flags = (0, 0x40000000, 0x80000000, 0xC0000000)[index % 4]
    return Case(f"case-{index}", tuple(registers), bytes(data),
                rng.randbytes(STACK_SIZE), flags)


def make_cases(seed: int) -> list[Case]:
    rng = random.Random(seed)
    cases = []
    boundaries = (-32768, -1, 0, 35, 36, 39, 40, 41, 144, 145, 146, 32767)
    for index in range(72):
        if index < len(boundaries):
            values = tuple(boundaries[(index + lane * 3) % len(boundaries)]
                           for lane in range(len(FIELDS)))
        else:
            values = tuple(rng.randint(-32768, 32767) for _ in FIELDS)
        cases.append(_case(seed, index, values))
    return cases


def run(code_path: Path, output: Path, seed: int) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.game_info, pinned.ledger)
    symbols = compile_candidate_symbols(
        SOURCE, output / "signed_halfword_range_clamp.o", ROOT,
        {SYMBOL, "negative_wrong_upper_clamp", "negative_omit_lower_clamp"})
    cases = make_cases(seed)
    original_runner = Runner(pinned.image, ADDRESS)
    candidate_runner = Runner(pinned.image, ADDRESS, symbols[SYMBOL])
    failure = None
    for case in cases:
        original = original_runner.run(case)
        candidate = candidate_runner.run(case)
        reason = difference(original, candidate, returns_value=False, compare_flags=False)
        if reason:
            failure = {"case": case.label, "reason": reason}
            break
    result = {"address": hex(ADDRESS), "candidate": SYMBOL,
              "original_bytes": SIZE, "candidate_bytes": len(symbols[SYMBOL]),
              "cases": len(cases) if failure is None else cases.index(case) + 1,
              "passed": failure is None, "failure": failure}
    controls = []
    for symbol, label, values in (
        ("negative_wrong_upper_clamp", "upper bound off by one", (41, 36, 145, 145, 145)),
        ("negative_omit_lower_clamp", "missing lower-bound store", (39, 36, 145, 145, 145)),
    ):
        case = _case(seed + 101, 77, values)
        original = Runner(pinned.image, ADDRESS).run(case)
        wrong = Runner(pinned.image, ADDRESS, symbols[symbol]).run(case)
        controls.append({"candidate": symbol, "detects": label,
                         "detected": original.data != wrong.data})
    report = {
        "schema": 1, "experiment": "signed_halfword_range_clamp_001285c4",
        "passed": result["passed"] and all(item["detected"] for item in controls),
        "scope": "one pinned ordinary-memory ARM leaf; isolated differential, not game boot",
        "reference_sha256": pinned.game_info["code_sha256"],
        "reference_functions": reference["functions"],
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "seed": seed, "function_comparisons": result["cases"],
        "case_mix": {"directed_boundary_vectors": 12, "random_signed_vectors": 60},
        "functions": [result], "negative_controls": controls,
        "caller_windows": [],
        "limitations": ["Finite seeded tests do not prove equivalence for all inputs.",
                        "Only ordinary RAM and isolated ARM11 execution were tested.",
                        "No caller windows, emulator boot, ledger or production code changes."],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
