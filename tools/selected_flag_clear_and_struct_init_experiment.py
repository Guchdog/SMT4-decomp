#!/usr/bin/env python3
"""Differential experiments for two simple AAPCS leaf behaviors."""
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

SOURCE = ROOT / "experiments/semantic_equivalence/selected_flag_clear_and_struct_init_candidates.cpp"
SEEDS = (7, 20261024)
FLAG_ADDRESS = 0x0023E634
STRUCT_ADDRESS = 0x00286700
MASK_ADDRESS = 0x002B540C
FLAG_EXPECTED = (
    ("ldrh", "r1, [r0]"), ("tst", "r1, #0x40"),
    ("bicne", "r1, r1, #0x40"), ("strhne", "r1, [r0]"), ("uxth", "r1, r1"),
    ("tst", "r1, #0x80"), ("bicne", "r1, r1, #0x80"), ("strhne", "r1, [r0]"), ("uxth", "r1, r1"),
    ("tst", "r1, #0x100"), ("bicne", "r1, r1, #0x100"), ("strhne", "r1, [r0]"), ("uxth", "r1, r1"),
    ("tst", "r1, #0x10"), ("bicne", "r1, r1, #0x10"), ("strhne", "r1, [r0]"), ("uxth", "r1, r1"),
    ("tst", "r1, #8"), ("bicne", "r1, r1, #8"), ("strhne", "r1, [r0]"), ("bx", "lr"),
)
STRUCT_EXPECTED = (
    ("mov", "r2, #0"), ("mov", "r3, #0x3f800000"),
    ("str", "r2, [r0, #4]"), ("str", "r3, [r0]"), ("str", "r2, [r0, #8]"),
    ("ldr", "ip, [r1]"), ("str", "ip, [r0, #0xc]"),
    ("strd", "r2, r3, [r0, #0x10]"), ("str", "r2, [r0, #0x18]"),
    ("ldr", "ip, [r1, #4]"), ("str", "r2, [r0, #0x20]"),
    ("str", "ip, [r0, #0x1c]"), ("strd", "r2, r3, [r0, #0x24]"),
    ("ldr", "r1, [r1, #8]"), ("add", "ip, r0, #0x2c"),
    ("stm", "ip, {r1, r2}"), ("str", "r2, [r0, #0x34]"),
    ("strd", "r2, r3, [r0, #0x38]"), ("bx", "lr"),
)
MASK_EXPECTED = (
    ("mov", "r3, #1"), ("bics", "r3, r3, r1"), ("mvn", "r2, #0"),
    ("mov", "r3, #2"), ("streq", "r2, [r0]"), ("bics", "r3, r3, r1"),
    ("mov", "r3, #4"), ("streq", "r2, [r0, #4]"), ("bics", "r3, r3, r1"),
    ("mov", "r3, #8"), ("streq", "r2, [r0, #8]"), ("bics", "r3, r3, r1"),
    ("mov", "r3, #0x10"), ("streq", "r2, [r0, #0xc]"), ("bics", "r3, r3, r1"),
    ("mov", "r3, #0x20"), ("streq", "r2, [r0, #0x10]"), ("bics", "r3, r3, r1"),
    ("mov", "r3, #0x80"), ("streq", "r2, [r0, #0x14]"), ("bics", "r3, r3, r1"),
    ("mov", "r3, #0x100"), ("streq", "r2, [r0, #0x18]"), ("bics", "r3, r3, r1"),
    ("mov", "r3, #0x200"), ("streq", "r2, [r0, #0x1c]"), ("bics", "r3, r3, r1"),
    ("mov", "r3, #0x800"), ("streq", "r2, [r0, #0x20]"), ("bics", "r3, r3, r1"),
    ("mov", "r3, #0x400"), ("streq", "r2, [r0, #0x24]"),
    ("bics", "r1, r3, r1"), ("streq", "r2, [r0, #0x28]"), ("bx", "lr"),
)


def verify_reference(image: bytes, game_info: dict, ledger: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != game_info["code_sha256"]:
        raise ValueError("code.bin SHA-256 differs from configured pin")
    by_address = {int(row["address"], 16): row for row in ledger}
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    functions = {}
    for address, size, expected, observation in (
        (FLAG_ADDRESS, 84, FLAG_EXPECTED,
         "Clears bits 0x40, 0x80, 0x100, 0x10 and 0x08 in one halfword; stores after each bit that was set."),
        (STRUCT_ADDRESS, 76, STRUCT_EXPECTED,
         "Writes constants and three source words within a 0x40-byte destination record in the pinned instruction order."),
        (MASK_ADDRESS, 140, MASK_EXPECTED,
         "For eleven mask bits, writes 0xffffffff into the corresponding output slot when that bit is set."),
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
        functions[hex(address)] = {
            "name": row["name"], "size": size,
            "sha256": hashlib.sha256(body).hexdigest(), "bytes": body.hex(),
            "instructions": [f"{mnemonic} {operands}" for mnemonic, operands in actual],
            "observation": observation,
        }
    return {"code_sha256": digest, "functions": functions}


def _case(seed: int, index: int, r0: int, r1: int = 0, *, flags: int | None = None,
          overlap: int | None = None) -> Case:
    rng = random.Random(seed ^ (index * 0x9E3779B1))
    data = bytearray(rng.randbytes(DATA_SIZE))
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0] = DATA + r0
    regs[1] = DATA + (r0 + overlap if overlap is not None else r1)
    if flags is not None:
        struct.pack_into("<H", data, r0, flags)
    return Case(f"case-{index}", tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                (0, 0x40000000, 0x80000000, 0xC0000000)[index % 4])


def run(code_path: Path, output: Path, seed: int) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.game_info, pinned.ledger)
    symbols = compile_candidate_symbols(
        SOURCE, output / "selected_flag_clear_and_struct_init.o", ROOT,
        {"candidate_0023e634", "candidate_00286700", "candidate_002b540c", "negative_wrong_mask_slot",
         "negative_unconditional_flag_store", "negative_wrong_struct_source",
         "negative_omit_struct_source", "negative_omit_mask_slot"})
    rng = random.Random(seed)
    flag_values = [0, 0xFFFF, 0x0040, 0x0188, 0x01D8, 0x0008, 0x0020]
    flag_values += [rng.getrandbits(16) for _ in range(57)]
    flag_original = Runner(pinned.image, FLAG_ADDRESS)
    flag_candidate = Runner(pinned.image, FLAG_ADDRESS, symbols["candidate_0023e634"])
    flag_failure = None
    for index, value in enumerate(flag_values):
        case = _case(seed, index, 0x100, flags=value)
        original, candidate = flag_original.run(case), flag_candidate.run(case)
        reason = difference(original, candidate, returns_value=False, compare_flags=False)
        if reason:
            flag_failure = {"case": case.label, "reason": reason}
            break
    flag_result = {"address": hex(FLAG_ADDRESS), "candidate_bytes": len(symbols["candidate_0023e634"]),
                   "cases": len(flag_values) if flag_failure is None else index + 1,
                   "passed": flag_failure is None, "failure": flag_failure}

    struct_cases = [(0x200, 0x600, None), (0x200, 0x600, 0),
                    (0x200, 0x600, 4), (0x200, 0x600, -4)]
    struct_cases += [(0x200 + (i % 8) * 4, 0x700 + (i % 8) * 4, None)
                     for i in range(60)]
    struct_original = Runner(pinned.image, STRUCT_ADDRESS)
    struct_candidate = Runner(pinned.image, STRUCT_ADDRESS, symbols["candidate_00286700"])
    struct_failure = None
    for index, (dst_off, src_off, overlap) in enumerate(struct_cases):
        if overlap is None:
            case = _case(seed + 1, index, dst_off, src_off)
        else:
            case = _case(seed + 1, index, dst_off, src_off, overlap=overlap)
        original, candidate = struct_original.run(case), struct_candidate.run(case)
        reason = difference(original, candidate, returns_value=False, compare_flags=False)
        if reason:
            struct_failure = {"case": case.label, "reason": reason}
            break
    struct_result = {"address": hex(STRUCT_ADDRESS), "candidate_bytes": len(symbols["candidate_00286700"]),
                     "cases": len(struct_cases) if struct_failure is None else index + 1,
                     "passed": struct_failure is None, "failure": struct_failure}

    rng_mask = random.Random(seed ^ 0xB540C)
    masks = [0, 0xFFFFFFFF, 0x7FF, 0xFFF]
    masks.extend(1 << bit for bit in (0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 10))
    masks.extend(rng_mask.getrandbits(32) for _ in range(49))
    mask_original = Runner(pinned.image, MASK_ADDRESS)
    mask_candidate = Runner(pinned.image, MASK_ADDRESS, symbols["candidate_002b540c"])
    mask_failure = None
    for index, mask in enumerate(masks):
        case = _case(seed + 2, index, 0x300)
        regs = list(case.registers)
        regs[1] = mask
        case = Case(case.label, tuple(regs), case.data, case.stack, case.nzcv)
        original, candidate = mask_original.run(case), mask_candidate.run(case)
        reason = difference(original, candidate, returns_value=False, compare_flags=False)
        if reason:
            mask_failure = {"case": case.label, "reason": reason}
            break
    mask_result = {"address": hex(MASK_ADDRESS), "candidate_bytes": len(symbols["candidate_002b540c"]),
                   "cases": len(masks) if mask_failure is None else index + 1,
                   "passed": mask_failure is None, "failure": mask_failure}

    controls = []
    flag_case = _case(seed + 101, 88, 0x100, flags=0x0020)
    base = Runner(pinned.image, FLAG_ADDRESS).run(flag_case)
    for symbol in ("negative_wrong_flag_mask", "negative_unconditional_flag_store"):
        wrong = Runner(pinned.image, FLAG_ADDRESS, symbols[symbol]).run(flag_case)
        controls.append({"candidate": symbol, "detected": base.data != wrong.data or base.writes != wrong.writes})
    struct_case = _case(seed + 103, 91, 0x200, 0x600)
    base = Runner(pinned.image, STRUCT_ADDRESS).run(struct_case)
    for symbol in ("negative_wrong_struct_source", "negative_omit_struct_source"):
        wrong = Runner(pinned.image, STRUCT_ADDRESS, symbols[symbol]).run(struct_case)
        controls.append({"candidate": symbol, "detected": base.data != wrong.data})
    mask_case = _case(seed + 107, 99, 0x300)
    mask_regs = list(mask_case.registers)
    mask_regs[1] = 1
    mask_case = Case(mask_case.label + "-wrong-mask", tuple(mask_regs),
                     mask_case.data, mask_case.stack, mask_case.nzcv)
    base = Runner(pinned.image, MASK_ADDRESS).run(mask_case)
    wrong = Runner(pinned.image, MASK_ADDRESS, symbols["negative_wrong_mask_slot"]).run(mask_case)
    controls.append({"candidate": "negative_wrong_mask_slot",
                     "detected": base.data != wrong.data or base.writes != wrong.writes})
    mask_case = _case(seed + 109, 101, 0x300)
    mask_regs = list(mask_case.registers)
    mask_regs[1] = 0x400
    mask_case = Case(mask_case.label + "-omit-mask", tuple(mask_regs),
                     mask_case.data, mask_case.stack, mask_case.nzcv)
    base = Runner(pinned.image, MASK_ADDRESS).run(mask_case)
    wrong = Runner(pinned.image, MASK_ADDRESS, symbols["negative_omit_mask_slot"]).run(mask_case)
    controls.append({"candidate": "negative_omit_mask_slot",
                     "detected": base.data != wrong.data or base.writes != wrong.writes})
    results = [flag_result, struct_result, mask_result]
    report = {
        "schema": 1, "experiment": "selected_flag_clear_and_struct_initializer",
        "passed": all(item["passed"] for item in results) and all(item["detected"] for item in controls),
        "scope": "three pinned ordinary-memory ARM leaves; isolated differential, not game boot",
        "reference_sha256": pinned.game_info["code_sha256"],
        "reference_functions": reference["functions"],
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "seed": seed, "function_comparisons": sum(item["cases"] for item in results),
        "functions": results, "negative_controls": controls, "caller_windows": [],
        "limitations": ["Finite seeded inputs do not prove equivalence for every state.",
                        "Only isolated ordinary RAM on Unicorn ARM11 was checked.",
                        "No caller windows, emulator boot, ledger or production code changes."],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
