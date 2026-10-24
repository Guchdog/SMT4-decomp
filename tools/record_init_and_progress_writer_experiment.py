#!/usr/bin/env python3
"""Differential tests for a record initializer and stateful progress writer."""
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

SOURCE = ROOT / "experiments/semantic_equivalence/record_init_and_progress_writer_candidates.cpp"
SEEDS = (7, 20261024)
INIT_ADDRESS = 0x00296F18
PROGRESS_ADDRESS = 0x003E8B44
INIT_EXPECTED = (
    ("mov", "ip, #0"), ("str", "r2, [r0, #0x1c]"), ("str", "ip, [r0]"),
    ("str", "ip, [r0, #4]"), ("str", "ip, [r0, #8]"), ("str", "ip, [r0, #0xc]"),
    ("str", "ip, [r0, #0x20]"), ("mov", "r3, #2"), ("str", "r1, [r0, #0x10]"),
    ("str", "r3, [r0, #0x14]"), ("str", "ip, [r0, #0x24]"), ("cmp", "r1, #0"),
    ("str", "r1, [r0, #0x18]"), ("movle", "r1, #0"),
    ("str", "r1, [r0, #0x18]"), ("mov", "r1, #6"), ("str", "r1, [r0]"),
    ("bx", "lr"),
)
PROGRESS_EXPECTED = (
    ("ldr", "r0, [r1, #4]"), ("add", "r3, r1, #8"), ("bic", "r0, r0, #0xf"),
    ("orr", "r0, r0, #1"), ("str", "r0, [r1, #4]"), ("ldr", "ip, [r2]"),
    ("str", "ip, [r1, #8]"), ("ldr", "ip, [r1, #4]"), ("orr", "ip, ip, #2"),
    ("str", "ip, [r1, #4]"), ("ldr", "ip, [r2, #4]"), ("str", "ip, [r1, #0xc]"),
    ("ldr", "ip, [r1, #4]"), ("orr", "ip, ip, #4"), ("str", "ip, [r1, #4]"),
    ("ldr", "ip, [r2, #8]"), ("str", "ip, [r3, #8]"), ("ldr", "r0, [r1, #4]"),
    ("orr", "r0, r0, #8"), ("str", "r0, [r1, #4]"), ("ldr", "r0, [r2, #0xc]"),
    ("str", "r0, [r3, #0xc]"), ("bx", "lr"),
)


def verify_reference(image: bytes, game_info: dict, ledger: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != game_info["code_sha256"]:
        raise ValueError("code.bin SHA-256 differs from configured pin")
    by_address = {int(row["address"], 16): row for row in ledger}
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    functions = {}
    for address, size, expected, semantics in (
        (INIT_ADDRESS, 72, INIT_EXPECTED,
         "Writes fixed record defaults, carries input value to offset 0x10, clamps offset 0x18 to zero when signed input is <= 0, and sets status 6."),
        (PROGRESS_ADDRESS, 92, PROGRESS_EXPECTED,
         "Clears the low four status bits, sets bit 0, copies four source words to destination+8..+0x14, and sets progress bits 1,2,3 with intervening writes."),
    ):
        row = by_address.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != size:
            raise ValueError(f"missing matching {size}-byte row at {address:#010x}")
        start = address - TEXT
        body = image[start:start + size]
        actual = tuple((insn.mnemonic.lower(), insn.op_str.lower())
                       for insn in decoder.disasm(body, address))
        if actual != expected:
            raise ValueError(f"reference instructions changed at {address:#010x}: {actual}")
        functions[hex(address)] = {"name": row["name"], "size": size,
                                   "sha256": hashlib.sha256(body).hexdigest(),
                                   "bytes": body.hex(), "instructions": [f"{m} {o}" for m, o in actual],
                                   "observation": semantics}
    return {"code_sha256": digest, "functions": functions}


def _case(seed: int, index: int, *, r0: int, r1: int, r2: int,
          value: int | None = None, type_value: int | None = None,
          state: int | None = None) -> Case:
    rng = random.Random(seed ^ (index * 0x9E3779B1))
    data = bytearray(rng.randbytes(DATA_SIZE))
    if value is not None:
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0], regs[1], regs[2] = DATA + r0, value & 0xFFFFFFFF, type_value or 0
    else:
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0], regs[1], regs[2] = rng.getrandbits(32), DATA + r1, DATA + r2
        if state is not None:
            struct.pack_into("<I", data, r1 + 4, state)
    return Case(f"case-{index}", tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                (0, 0x40000000, 0x80000000, 0xC0000000)[index % 4])


def run(code_path: Path, output: Path, seed: int) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.game_info, pinned.ledger)
    symbols = compile_candidate_symbols(
        SOURCE, output / "record_init_and_progress_writer.o", ROOT,
        {"candidate_00296f18", "candidate_003e8b44", "negative_wrong_value_threshold",
         "negative_omit_status_write", "negative_wrong_state_clear_mask",
         "negative_omit_progress_copy"})
    rng = random.Random(seed)
    values = [-(1 << 31), -1, 0, 1, 2, 0x7FFFFFFF]
    values += [rng.randint(-(1 << 31), (1 << 31) - 1) for _ in range(58)]
    init_ref, init_candidate = Runner(pinned.image, INIT_ADDRESS), Runner(
        pinned.image, INIT_ADDRESS, symbols["candidate_00296f18"])
    init_failure = None
    for index, value in enumerate(values):
        case = _case(seed, index, r0=0x100, r1=0, r2=0, value=value,
                     type_value=rng.getrandbits(32))
        original, candidate = init_ref.run(case), init_candidate.run(case)
        reason = difference(original, candidate, returns_value=False, compare_flags=False)
        if reason:
            init_failure = {"case": case.label, "reason": reason}
            break
    init_result = {"address": hex(INIT_ADDRESS), "candidate_bytes": len(symbols["candidate_00296f18"]),
                   "cases": len(values) if init_failure is None else index + 1,
                   "passed": init_failure is None, "failure": init_failure}

    rng_progress = random.Random(seed ^ 0x3E8B44)
    pointer_pairs = [(0x200, 0x700), (0x200, 0x204), (0x200, 0x208),
                     (0x200, 0x1FC), (0x200, 0x600)]
    pointer_pairs += [(0x200 + 4 * (i % 8), 0x700 + 4 * (i % 8)) for i in range(59)]
    progress_ref, progress_candidate = Runner(pinned.image, PROGRESS_ADDRESS), Runner(
        pinned.image, PROGRESS_ADDRESS, symbols["candidate_003e8b44"])
    progress_failure = None
    for index, (dst, src) in enumerate(pointer_pairs):
        case = _case(seed + 1, index, r0=0, r1=dst, r2=src,
                     state=rng_progress.getrandbits(32))
        original, candidate = progress_ref.run(case), progress_candidate.run(case)
        reason = difference(original, candidate, returns_value=False, compare_flags=False)
        if reason:
            progress_failure = {"case": case.label, "destination": hex(dst),
                                "source": hex(src), "reason": reason}
            break
    progress_result = {"address": hex(PROGRESS_ADDRESS), "candidate_bytes": len(symbols["candidate_003e8b44"]),
                       "cases": len(pointer_pairs) if progress_failure is None else index + 1,
                       "alias_cases": 4, "passed": progress_failure is None,
                       "failure": progress_failure}

    controls = []
    base_case = _case(seed + 101, 70, r0=0x100, r1=0, r2=0, value=1, type_value=0x1234)
    base = Runner(pinned.image, INIT_ADDRESS).run(base_case)
    for symbol in ("negative_wrong_value_threshold", "negative_omit_status_write"):
        wrong = Runner(pinned.image, INIT_ADDRESS, symbols[symbol]).run(base_case)
        controls.append({"candidate": symbol, "detected": base.data != wrong.data or base.writes != wrong.writes})
    progress_case = _case(seed + 103, 72, r0=0, r1=0x200, r2=0x700, state=0x10)
    base = Runner(pinned.image, PROGRESS_ADDRESS).run(progress_case)
    for symbol in ("negative_wrong_state_clear_mask", "negative_omit_progress_copy"):
        wrong = Runner(pinned.image, PROGRESS_ADDRESS, symbols[symbol]).run(progress_case)
        controls.append({"candidate": symbol, "detected": base.data != wrong.data or base.writes != wrong.writes})
    results = [init_result, progress_result]
    report = {
        "schema": 1, "experiment": "record_init_and_progress_writer",
        "passed": all(item["passed"] for item in results) and all(item["detected"] for item in controls),
        "scope": "two pinned ordinary-memory ARM leaves; isolated differential, not game boot",
        "reference_sha256": pinned.game_info["code_sha256"],
        "reference_functions": reference["functions"],
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "seed": seed, "function_comparisons": sum(item["cases"] for item in results),
        "functions": results, "negative_controls": controls, "caller_windows": [],
        "limitations": ["Finite seeded tests are evidence, not proof for all inputs.",
                        "Only isolated ordinary RAM on Unicorn ARM11 was tested.",
                        "No callers, game boot, ledger or production source changes."],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
