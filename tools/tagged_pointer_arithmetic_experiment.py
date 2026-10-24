#!/usr/bin/env python3
"""Test two gated ARM pointer additions, including modulo-2^32 behavior."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import struct
import sys

import capstone

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference,
)
from tools.semantic_experiment_support import (
    compile_candidate_symbols, load_pinned_reference,
)

FUNCTIONS = {
    0x003E698C: {
        "tag_offset": 8, "displacement_offset": 0x0c,
        "words": (0xE1D010B8, 0xE2412C01, 0xE2522001, 0x0590100C,
                  0x13A00000, 0x00800001, 0xE12FFF1E),
        "symbol": "candidate_003e698c",
        "callers": (0x003E702C, 0x003E7138),
    },
    0x003E69C0: {
        "tag_offset": 0x10, "displacement_offset": 0x14,
        "words": (0xE1D011B0, 0xE2412C01, 0xE2522001, 0x05901014,
                  0x13A00000, 0x00800001, 0xE12FFF1E),
        "symbol": "candidate_003e69c0",
        "callers": (0x003E7074, 0x003E71D8),
    },
}
CALLER_WINDOWS = {
    0x003E698C: {
        "name": "func_003e7024", "entry": 0x003E7024, "site": 0x003E702C,
        "start": 0x003E7024, "stop": 0x003E7034,
        "instructions": ((0x003E7024, "push", "{r4, lr}"),
                         (0x003E7028, "ldr", "r0, [r0, #8]"),
                         (0x003E702C, "bl", "#0x3e698c"),
                         (0x003E7030, "ldr", "r0, [r0]")),
    },
    0x003E69C0: {
        "name": "func_003e706c", "entry": 0x003E706C, "site": 0x003E7074,
        "start": 0x003E706C, "stop": 0x003E707C,
        "instructions": ((0x003E706C, "push", "{r4, lr}"),
                         (0x003E7070, "ldr", "r0, [r0, #8]"),
                         (0x003E7074, "bl", "#0x3e69c0"),
                         (0x003E7078, "ldr", "r0, [r0]")),
    },
}
U32_MASK = 0xFFFFFFFF


def _direct_bl_targets(image: bytes) -> dict[int, list[int]]:
    refs = {target: [] for target in FUNCTIONS}
    for offset in range(0, len(image) - 3, 4):
        word = struct.unpack_from("<I", image, offset)[0]
        if word & 0x0F000000 != 0x0B000000:
            continue
        displacement = word & 0xFFFFFF
        if displacement & 0x800000:
            displacement -= 0x1000000
        target = (TEXT + offset + 8 + (displacement << 2)) & U32_MASK
        if target in refs:
            refs[target].append(TEXT + offset)
    return refs


def verify_reference(reference) -> dict:
    by_address = {int(row["address"], 16): row for row in reference.ledger}
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    refs = _direct_bl_targets(reference.image)
    functions = {}
    for address, spec in FUNCTIONS.items():
        row = by_address.get(address)
        if row is None or row["status"] != "matching" or int(row["size"]) != 28:
            raise ValueError(f"Ledger entry changed at {address:#010x}")
        code = reference.image[address - TEXT:address - TEXT + 28]
        words = struct.unpack("<7I", code)
        if words != spec["words"]:
            raise ValueError(f"Instruction words changed at {address:#010x}: {words}")
        if tuple(refs[address]) != spec["callers"]:
            raise ValueError(f"Direct caller set changed at {address:#010x}: {refs[address]}")
        functions[hex(address)] = {
            "name": row["name"], "tag_offset": hex(spec["tag_offset"]),
            "displacement_offset": hex(spec["displacement_offset"]),
            "tag_equals": "0x101", "instruction_words": [f"0x{x:08x}" for x in words],
            "direct_call_count": len(refs[address]),
            "direct_call_sites": [hex(site) for site in refs[address]],
        }
    callers = {}
    for address, window in CALLER_WINDOWS.items():
        caller = by_address.get(window["entry"])
        if caller is None or caller["name"] != window["name"]:
            raise ValueError(f"Caller ledger row changed at {window['entry']:#010x}")
        if window["site"] not in refs[address]:
            raise ValueError(f"Caller BL missing at {window['site']:#010x}")
        instructions = []
        for pc, mnemonic, operands in window["instructions"]:
            decoded = next(decoder.disasm(reference.image[pc - TEXT:pc - TEXT + 4], pc), None)
            if decoded is None or (decoded.mnemonic, decoded.op_str) != (mnemonic, operands):
                raise ValueError(f"Caller instruction drift at {pc:#010x}")
            instructions.append({"address": hex(pc), "mnemonic": mnemonic,
                                 "operands": operands})
        callers[hex(address)] = {"entry": hex(window["entry"]), "name": window["name"],
                                 "site": hex(window["site"]), "stop": hex(window["stop"]),
                                 "instructions": instructions}
    return {"code_sha256": reference.game_info["code_sha256"],
            "functions": functions, "callers": callers}


def _put32(memory: bytearray, offset: int, value: int):
    memory[offset:offset + 4] = (value & U32_MASK).to_bytes(4, "little")


def make_cases(address: int, seed: int, samples: int):
    spec = FUNCTIONS[address]
    rng = random.Random(seed ^ address)
    pointer_values = (0, 1, 0x20, 0x100, 0x7FFFFFFF, 0xFFFFFF00,
                      0xFFFFFFF0, U32_MASK)
    for index, tag in enumerate((0, 1, 0x100, 0x101, 0x102, 0xFFFF)):
        for displacement in pointer_values:
            data = bytearray(DATA_SIZE)
            base = 0x100 + (index % 4) * 0x20
            data[base + spec["tag_offset"]:base + spec["tag_offset"] + 2] = tag.to_bytes(2, "little")
            _put32(data, base + spec["displacement_offset"], displacement)
            regs = [rng.getrandbits(32) for _ in range(13)]
            regs[0] = DATA + base
            yield Case(f"tag-{tag:04x}-disp-{displacement:08x}", tuple(regs), bytes(data),
                       rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)
    for index in range(samples):
        data = bytearray(rng.randbytes(DATA_SIZE))
        base = 0x100 + (index % 8) * 0x20
        tag = 0x101 if index % 2 else rng.choice((0, 1, 0x100, 0x102, 0xFFFF))
        displacement = rng.getrandbits(32)
        data[base + spec["tag_offset"]:base + spec["tag_offset"] + 2] = tag.to_bytes(2, "little")
        _put32(data, base + spec["displacement_offset"], displacement)
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0] = DATA + base
        yield Case(f"random-{index}-tag-{tag:04x}-disp-{displacement:08x}", tuple(regs),
                   bytes(data), rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def _caller_case(address: int, displacement: int, seed: int) -> Case:
    spec = FUNCTIONS[address]
    data = bytearray(DATA_SIZE)
    outer = 0x100
    inner = 0x200
    data[outer + 8:outer + 12] = (DATA + inner).to_bytes(4, "little")
    data[inner + spec["tag_offset"]:inner + spec["tag_offset"] + 2] = (0x101).to_bytes(2, "little")
    _put32(data, inner + spec["displacement_offset"], displacement)
    target = (inner + displacement) & U32_MASK
    if DATA <= DATA + target and DATA + target + 4 <= DATA + DATA_SIZE:
        _put32(data, target, 0xC0DE0000 | (seed & 0xFFFF))
    regs = [random.Random(seed ^ i).getrandbits(32) for i in range(13)]
    regs[0] = DATA + outer
    return Case(f"caller-{address:08x}-disp-{displacement:08x}", tuple(regs), bytes(data),
                bytes(STACK_SIZE), (seed & 0xF) << 28)


def _expected_reads(address: int, case: Case) -> frozenset[int]:
    base = case.registers[0]
    spec = FUNCTIONS[address]
    reads = set(range(base + spec["tag_offset"], base + spec["tag_offset"] + 2))
    data_offset = base - DATA
    tag = int.from_bytes(case.data[data_offset + spec["tag_offset"]:
                                   data_offset + spec["tag_offset"] + 2], "little")
    if tag == 0x101:
        reads.update(range(base + spec["displacement_offset"],
                           base + spec["displacement_offset"] + 4))
    return frozenset(reads)


def run(code_path: Path, output: Path, seed: int, samples: int) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    output.mkdir(parents=True, exist_ok=True)
    reference = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                      ROOT / "config/functions.csv")
    reference_evidence = verify_reference(reference)
    source = ROOT / "experiments/semantic_equivalence/tagged_pointer_arithmetic_candidates.cpp"
    negative_symbols = [f"wrong_{kind}_{address:08x}" for address in FUNCTIONS
                       for kind in ("tag_offset", "disp_offset", "add")]
    required = [spec["symbol"] for spec in FUNCTIONS.values()] + negative_symbols
    compiled = compile_candidate_symbols(source, output / "tagged_pointer_arithmetic.o",
                                         ROOT, required)

    functions, negatives, caller_results = [], [], []
    for address, spec in FUNCTIONS.items():
        original = Runner(reference.image, address)
        candidate = Runner(reference.image, address, compiled[spec["symbol"]])
        wrong_runners = {symbol: Runner(reference.image, address, compiled[symbol])
                         for symbol in negative_symbols if symbol.endswith(f"{address:08x}")}
        count, failure = 0, None
        for case in make_cases(address, seed, samples):
            old, new = original.run(case), candidate.run(case)
            reason = difference(old, new)
            if not reason and (old.reads != _expected_reads(address, case) or old.writes):
                reason = "isolated read/write footprint differs from gated ARM contract"
            count += 1
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
        functions.append({"address": hex(address), "candidate": spec["symbol"],
                          "candidate_bytes": len(compiled[spec["symbol"]]),
                          "cases": count, "passed": failure is None, "failure": failure})

        # For direct negative controls, use a valid mapped object and a true tag.
        test_data = bytearray(DATA_SIZE)
        base = 0x100
        test_data[base + spec["tag_offset"]:base + spec["tag_offset"] + 2] = (0x101).to_bytes(2, "little")
        _put32(test_data, base + spec["displacement_offset"], 0x20)
        case_regs = [0] * 13
        case_regs[0] = DATA + base
        neg_case = Case("negative-controls-valid-tag", tuple(case_regs), bytes(test_data),
                        bytes(STACK_SIZE), 0)
        for kind in ("tag_offset", "disp_offset", "add"):
            symbol = f"wrong_{kind}_{address:08x}"
            wrong = wrong_runners[symbol]
            reason = difference(original.run(neg_case), wrong.run(neg_case))
            negatives.append({"address": hex(address), "control": symbol,
                              "detected": reason is not None, "reason": reason})

        window = CALLER_WINDOWS[address]
        displacement = 0x20
        call_case = _caller_case(address, displacement, seed)
        old = Runner(reference.image, address).run(call_case, start=window["start"],
                                                   stops=(window["stop"],), budget=32)
        new = Runner(reference.image, address, compiled[spec["symbol"]]).run(
            call_case, start=window["start"], stops=(window["stop"],), budget=32)
        reason = difference(old, new, returns_value=True, caller_window=True,
                            compare_flags=True)
        caller_results.append({"address": hex(address), "caller": window["name"],
                               "callsite": hex(window["site"]), "passed": reason is None,
                               "reason": reason, "result": hex(old.result)})

    report = {
        "experiment": "tagged_pointer_modular_arithmetic_pair", "seed": seed,
        "random_samples_per_function": samples, "boundary_tags": ["0x0", "0x1", "0x100", "0x101", "0x102", "0xffff"],
        "boundary_displacements": [f"0x{x:08x}" for x in (0, 1, 0x20, 0x100, 0x7fffffff, 0xffffff00, 0xfffffff0, 0xffffffff)],
        "reference": reference_evidence, "functions": functions,
        "negative_controls": negatives, "caller_windows": caller_results,
        "passed": all(row["passed"] for row in functions + caller_results)
                  and all(row["detected"] for row in negatives),
        "limitations": [
            "Exhaustive tag boundary matrix and seeded 32-bit displacements are executed with ordinary aligned RAM.",
            "The caller wrappers are tested only on the valid 0x101 tag path; invalid tags return null and those wrappers dereference the result, so the game-level invalid contract is not inferred from the wrapper.",
            "Caller setup supplies a synthetic outer object and inner tagged object; this is not whole-game or emulator evidence.",
            "Candidates and tests are isolated; production sources and shared harness are unchanged.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--output", type=Path, default=Path("build/semantic-equivalence/tagged-pointer-arithmetic"))
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--samples", type=int, default=64)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed, args.samples)
    print(json.dumps({"passed": report["passed"], "functions": report["functions"],
                      "negative_controls": report["negative_controls"],
                      "caller_windows": report["caller_windows"]}, indent=2))


if __name__ == "__main__":
    main()
