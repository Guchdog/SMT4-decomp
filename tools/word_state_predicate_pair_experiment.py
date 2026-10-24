#!/usr/bin/env python3
"""Test a pair of word-sized state equality predicates and their branches."""
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
    DATA, DATA_SIZE, STACK_SIZE, TEXT, U32_MASK, Case, Runner, difference,
)
from tools.semantic_experiment_support import (
    compile_candidate_symbols, load_pinned_reference,
)

FIELD_OFFSET = 0x3048
FUNCTIONS = {
    0x0028C290: {"constant": 7, "words":
                 (0xE2800A03, 0xE5900048, 0xE3500007, 0x03A00001, 0x13A00000, 0xE12FFF1E),
                 "symbol": "candidate_0028c290",
                 "callers": (0x0019E4F0, 0x0019E818, 0x0019EACC)},
    0x002E42E0: {"constant": 2, "words":
                 (0xE2800A03, 0xE5900048, 0xE3500002, 0x03A00001, 0x13A00000, 0xE12FFF1E),
                 "symbol": "candidate_002e42e0",
                 "callers": (0x0019E3E4,)},
}
CALLER_WINDOWS = {
    0x0028C290: {
        "name": "btlUI_Calc", "entry": 0x0019E034, "site": 0x0019E4F0,
        "start": 0x0019E4EC, "stops": (0x0019E500, 0x0019E558),
        "instructions": ((0x0019E4EC, "mov", "r0, r5"),
                         (0x0019E4F0, "bl", "#0x28c290"),
                         (0x0019E4F4, "cmp", "r0, #0"),
                         (0x0019E4F8, "nop", ""),
                         (0x0019E4FC, "beq", "#0x19e558")),
        "argument_bias": 0,
    },
    0x002E42E0: {
        "name": "btlUI_Calc", "entry": 0x0019E034, "site": 0x0019E3E4,
        "start": 0x0019E3DC, "stops": (0x0019E3F4, 0x0019E488),
        "instructions": ((0x0019E3DC, "add", "r0, r0, #0x460"),
                         (0x0019E3E0, "mov", "r5, r0"),
                         (0x0019E3E4, "bl", "#0x2e42e0"),
                         (0x0019E3E8, "cmp", "r0, #0"),
                         (0x0019E3EC, "nop", ""),
                         (0x0019E3F0, "beq", "#0x19e488")),
        "argument_bias": 0x460,
    },
}


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
    functions, callers = {}, {}
    for address, spec in FUNCTIONS.items():
        row = by_address.get(address)
        if row is None or row["status"] != "matching" or int(row["size"]) != 24:
            raise ValueError(f"Ledger entry changed at {address:#010x}")
        code = reference.image[address - TEXT:address - TEXT + 24]
        words = struct.unpack("<6I", code)
        if words != spec["words"]:
            raise ValueError(f"Instruction words changed at {address:#010x}: {words}")
        if tuple(refs[address]) != spec["callers"]:
            raise ValueError(f"Direct caller set changed at {address:#010x}: {refs[address]}")
        functions[hex(address)] = {
            "ledger_name": row["name"], "field_offset": hex(FIELD_OFFSET),
            "equals": spec["constant"], "instruction_words": [f"0x{x:08x}" for x in words],
            "direct_call_count": len(refs[address]),
            "direct_call_sites": [hex(site) for site in refs[address]],
        }
    for address, window in CALLER_WINDOWS.items():
        caller = by_address.get(window["entry"])
        if caller is None or caller["name"] != window["name"]:
            raise ValueError(f"Caller ledger identity changed at {window['entry']:#010x}")
        if window["site"] not in refs[address]:
            raise ValueError(f"Pinned caller has no direct BL at {window['site']:#010x}")
        instructions = []
        for site, mnemonic, operands in window["instructions"]:
            decoded = next(decoder.disasm(reference.image[site - TEXT:site - TEXT + 4], site), None)
            if decoded is None or (decoded.mnemonic, decoded.op_str) != (mnemonic, operands):
                raise ValueError(f"Caller instruction drift at {site:#010x}")
            instructions.append({"address": hex(site), "mnemonic": mnemonic,
                                 "operands": operands})
        callers[hex(address)] = {"caller": window["name"], "entry": hex(window["entry"]),
                                 "callsite": hex(window["site"]),
                                 "stop_pcs": [hex(pc) for pc in window["stops"]],
                                 "instructions": instructions}
    return {"code_sha256": reference.game_info["code_sha256"],
            "functions": functions, "callers": callers}


def _store_u32(memory: bytearray, offset: int, value: int):
    memory[offset:offset + 4] = (value & U32_MASK).to_bytes(4, "little")


def _field_address(object_address: int) -> int:
    return (object_address + FIELD_OFFSET) & U32_MASK


def make_cases(address: int, seed: int, samples: int):
    spec = FUNCTIONS[address]
    rng = random.Random(seed ^ address)
    for value in (0, 1, spec["constant"] - 1, spec["constant"],
                  spec["constant"] + 1, 0x7FFFFFFF, U32_MASK):
        data = bytearray(DATA_SIZE)
        base = 0x100
        object_address = (DATA + base - FIELD_OFFSET) & U32_MASK
        _store_u32(data, base, value)
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0] = object_address
        yield Case(f"boundary-{value:08x}", tuple(regs), bytes(data),
                   rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)
    for index in range(samples):
        data = bytearray(rng.randbytes(DATA_SIZE))
        base = 0x100
        object_address = (DATA + base - FIELD_OFFSET) & U32_MASK
        value = rng.getrandbits(32)
        _store_u32(data, base, value)
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0] = object_address
        yield Case(f"random-{index}-value-{value:08x}", tuple(regs), bytes(data),
                   rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def _caller_case(address: int, value: int, seed: int) -> Case:
    data = bytearray(DATA_SIZE)
    field_offset = 0x100
    _store_u32(data, field_offset, value)
    field_address = DATA + field_offset
    window = CALLER_WINDOWS[address]
    argument = (field_address - FIELD_OFFSET - window["argument_bias"]) & U32_MASK
    regs = [random.Random(seed ^ index).getrandbits(32) for index in range(13)]
    if address == 0x0028C290:
        regs[5] = argument
    else:
        regs[0] = argument
    return Case(f"caller-{address:08x}-field-{value:08x}", tuple(regs), bytes(data),
                bytes(STACK_SIZE), (seed & 0xF) << 28)


def _expected_field_reads(case: Case, *, caller: bool = False) -> frozenset[int]:
    field_address = DATA + 0x100 if caller else (case.registers[0] + FIELD_OFFSET) & U32_MASK
    return frozenset(range(field_address, field_address + 4))


def run(code_path: Path, output: Path, seed: int, samples: int) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    output.mkdir(parents=True, exist_ok=True)
    reference = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                      ROOT / "config/functions.csv")
    reference_evidence = verify_reference(reference)
    source = ROOT / "experiments/semantic_equivalence/word_state_predicate_pair_candidates.cpp"
    negative_symbols = [f"wrong_{kind}_{address:08x}" for address in FUNCTIONS
                       for kind in ("offset", "constant", "sense")]
    required = [spec["symbol"] for spec in FUNCTIONS.values()] + negative_symbols
    compiled = compile_candidate_symbols(source, output / "word_state_predicate_pair.o",
                                         ROOT, required)
    functions, negatives, caller_results = [], [], []
    for address, spec in FUNCTIONS.items():
        original = Runner(reference.image, address)
        candidate = Runner(reference.image, address, compiled[spec["symbol"]])
        wrong_runners = {name: Runner(reference.image, address, compiled[name])
                         for name in negative_symbols if name.endswith(f"{address:08x}")}
        count, failure = 0, None
        for case in make_cases(address, seed, samples):
            old, new = original.run(case), candidate.run(case)
            reason = difference(old, new)
            if not reason and (old.reads != _expected_field_reads(case) or old.writes):
                reason = "unexpected u32 field read/write footprint"
            count += 1
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
        functions.append({"address": hex(address), "candidate": spec["symbol"],
                          "candidate_bytes": len(compiled[spec["symbol"]]),
                          "cases": count, "passed": failure is None, "failure": failure})

        negative_case = next(case for case in make_cases(address, seed, 0)
                             if case.label == f"boundary-{spec['constant']:08x}")
        for kind in ("offset", "constant", "sense"):
            symbol = f"wrong_{kind}_{address:08x}"
            reason = difference(original.run(negative_case),
                               wrong_runners[symbol].run(negative_case))
            negatives.append({"address": hex(address), "control": symbol,
                              "detected": reason is not None, "reason": reason})

        window = CALLER_WINDOWS[address]
        for value in (spec["constant"], spec["constant"] + 1):
            case = _caller_case(address, value, seed + value)
            old = original.run(case, start=window["start"], stops=window["stops"], budget=32)
            new = candidate.run(case, start=window["start"], stops=window["stops"], budget=32)
            reason = difference(old, new, returns_value=False, caller_window=True,
                                compare_flags=True)
            if not reason and (old.reads != _expected_field_reads(case, caller=True) or old.writes):
                reason = "unexpected caller field footprint"
            caller_results.append({"address": hex(address), "caller": window["name"],
                                   "callsite": hex(window["site"]), "field_value": value,
                                   "path_pc": hex(old.pc), "passed": reason is None,
                                   "reason": reason})

    report = {
        "experiment": "word_state_equality_predicate_pair", "seed": seed,
        "random_samples_per_function": samples, "field_offset": hex(FIELD_OFFSET),
        "reference": reference_evidence, "functions": functions,
        "negative_controls": negatives, "caller_windows": caller_results,
        "passed": all(row["passed"] for row in functions + caller_results)
                  and all(row["detected"] for row in negatives),
        "limitations": [
            "Field access uses a synthetic base whose arithmetic offset lands inside mapped DATA RAM; the intermediate object pointer itself is never dereferenced.",
            "Caller tests execute the original argument setup, BL, compare, and branch; they use synthetic state fields.",
            "This is isolated ARM execution evidence only, not production integration or whole-game equivalence.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--output", type=Path, default=Path("build/semantic-equivalence/word-state-predicates"))
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--samples", type=int, default=64)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed, args.samples)
    print(json.dumps({"passed": report["passed"], "functions": report["functions"],
                      "negative_controls": report["negative_controls"],
                      "caller_windows": report["caller_windows"]}, indent=2))


if __name__ == "__main__":
    main()
