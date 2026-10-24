#!/usr/bin/env python3
"""Differentially test two repeated byte-equality predicates and callers."""
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
    DATA, DATA_SIZE, SP, STACK, STACK_SIZE, TEXT, Case, Runner, difference,
)
from tools.semantic_experiment_support import (
    compile_candidate_symbols, load_pinned_reference,
)

FUNCTIONS = {
    0x00126430: {
        "offset": 0x44, "constant": 2, "words":
        (0xE5D00044, 0xE3500002, 0x03A00001, 0x13A00000, 0xE12FFF1E),
        "symbol": "candidate_00126430",
        "callers": (0x00115958,),
    },
    0x0027EC84: {
        "offset": 0, "constant": 0, "words":
        (0xE5D00000, 0xE3500000, 0x03A00001, 0x13A00000, 0xE12FFF1E),
        "symbol": "candidate_0027ec84",
        "callers": (0x001B4DF8, 0x0038E688, 0x0038E72C, 0x0038E888,
                    0x0038E990, 0x0038EAB4, 0x0038EB80, 0x0038EE74,
                    0x0038F020, 0x0038F56C, 0x0038FFC8, 0x00392418,
                    0x003924BC, 0x00392730, 0x00392BEC, 0x00392C94),
    },
}
CALLER_WINDOWS = {
    0x00126430: {
        "caller_entry": 0x00114374, "caller_name": "Camp_DemonicaArchiveLoad",
        "start": 0x00115954,
        "call": 0x00115958, "stops": (0x00115968, 0x00115984),
        "setup": ((0x00115954, "ldr", "r0, [r4, #4]"),),
        "tail": ((0x0011595C, "cmp", "r0, #0"),
                 (0x00115960, "nop", ""),
                 (0x00115964, "beq", "#0x115984")),
    },
    0x0027EC84: {
        "caller_entry": 0x0038E58C, "caller_name": "engine_func_0038e58c",
        "start": 0x0038E684,
        "call": 0x0038E688, "stops": (0x0038E698, 0x0038E6A4),
        "setup": ((0x0038E684, "mov", "r0, sp"),),
        "tail": ((0x0038E68C, "cmp", "r0, #0"),
                 (0x0038E690, "movne", "r0, #2"),
                 (0x0038E694, "beq", "#0x38e6a4")),
    },
}


def _direct_bl_targets(image: bytes) -> dict[int, list[int]]:
    found = {target: [] for target in FUNCTIONS}
    for offset in range(0, len(image) - 3, 4):
        word = struct.unpack_from("<I", image, offset)[0]
        if word & 0x0F000000 != 0x0B000000:
            continue
        displacement = word & 0xFFFFFF
        if displacement & 0x800000:
            displacement -= 0x1000000
        target = (TEXT + offset + 8 + (displacement << 2)) & 0xFFFFFFFF
        if target in found:
            found[target].append(TEXT + offset)
    return found


def verify_reference(reference) -> dict:
    by_address = {int(row["address"], 16): row for row in reference.ledger}
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    evidence = {}
    direct_refs = _direct_bl_targets(reference.image)
    for address, spec in FUNCTIONS.items():
        row = by_address.get(address)
        if row is None or row["status"] != "matching" or int(row["size"]) != 20:
            raise ValueError(f"Unexpected ledger row at {address:#010x}")
        code = reference.image[address - TEXT:address - TEXT + 20]
        words = struct.unpack("<5I", code)
        if words != spec["words"]:
            raise ValueError(f"Instruction words changed at {address:#010x}: {words}")
        decoded = [(item.mnemonic, item.op_str) for item in decoder.disasm(code, address)]
        offset = spec["offset"]
        load = ("ldrb", "r0, [r0]" if offset == 0 else f"r0, [r0, #0x{offset:x}]")
        expected = (load, ("cmp", f"r0, #{spec['constant']}"),
                    ("moveq", "r0, #1"), ("movne", "r0, #0"), ("bx", "lr"))
        if tuple(decoded) != expected:
            raise ValueError(f"Decoded predicate changed at {address:#010x}: {decoded}")
        refs = direct_refs[address]
        if tuple(refs) != spec["callers"]:
            raise ValueError(f"Direct caller set changed at {address:#010x}: {refs}")
        evidence[hex(address)] = {
            "ledger_name": row["name"], "size": int(row["size"]),
            "field_offset": hex(offset), "equals": spec["constant"],
            "instruction_words": [f"0x{x:08x}" for x in words],
            "direct_call_count": len(refs), "direct_calls": [hex(x) for x in refs],
        }

    windows = {}
    for address, window in CALLER_WINDOWS.items():
        caller_row = by_address.get(window["caller_entry"])
        if (caller_row is None or caller_row["name"] != window["caller_name"]
                or window["call"] not in direct_refs[address]):
            raise ValueError(f"Pinned caller ledger entry changed at {window['call']:#010x}")
    for address, window in CALLER_WINDOWS.items():
        instructions = window["setup"] + ((window["call"], "bl",
            f"#0x{address:x}"),) + window["tail"]
        for site, mnemonic, operands in instructions:
            raw = reference.image[site - TEXT:site - TEXT + 4]
            decoded = next(decoder.disasm(raw, site), None)
            if decoded is None or (decoded.mnemonic, decoded.op_str) != (mnemonic, operands):
                raise ValueError(f"Caller instruction drift at {site:#010x}")
        windows[hex(address)] = {
            "caller_entry": hex(window["caller_entry"]),
            "caller_name": window["caller_name"],
            "call": hex(window["call"]), "start": hex(window["start"]),
            "stop_pcs": [hex(pc) for pc in window["stops"]],
            "consumers": [{"address": hex(a), "mnemonic": m, "operands": o}
                          for a, m, o in window["tail"]],
        }
    return {"code_sha256": reference.game_info["code_sha256"],
            "functions": evidence, "caller_windows": windows}


def make_cases(address: int, seed: int, samples: int):
    spec = FUNCTIONS[address]
    rng = random.Random(seed ^ address)
    for value in range(256):
        data = bytearray(DATA_SIZE)
        base = 0x100 + (value % 4) * 8
        data[base + spec["offset"]] = value
        if spec["offset"]:
            data[base + spec["offset"] + 1] = 0xA7
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0] = DATA + base
        yield Case(f"byte-{value:02x}", tuple(regs), bytes(data),
                   rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)
    for index in range(samples):
        data = bytearray(rng.randbytes(DATA_SIZE))
        base = 0x100 + (index % 8) * 8
        value = rng.randrange(256)
        data[base + spec["offset"]] = value
        if spec["offset"]:
            data[base + spec["offset"] + 1] = rng.randrange(1, 256)
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0] = DATA + base
        yield Case(f"random-{index}-byte-{value:02x}", tuple(regs), bytes(data),
                   rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def _caller_case(address: int, value: int, seed: int) -> Case:
    spec = FUNCTIONS[address]
    data = bytearray(DATA_SIZE)
    stack = bytearray(STACK_SIZE)
    regs = [0] * 13
    if address == 0x00126430:
        object_ptr = DATA + 0x100
        field_ptr = DATA + 0x300
        data[0x104:0x108] = field_ptr.to_bytes(4, "little")
        data[0x300 + spec["offset"]] = value
        data[0x300 + spec["offset"] + 1] = 0xB6
        regs[4] = object_ptr
    else:
        stack[SP - STACK] = value
        stack[SP - STACK + 1] = 0xB6
    return Case(f"caller-{address:08x}-{value:02x}-seed-{seed}", tuple(regs),
                bytes(data), bytes(stack), (seed & 0xF) << 28)


def _expected_read(address: int, case: Case, *, caller: bool = False) -> frozenset[int]:
    if caller and address == 0x0027EC84:
        return frozenset((SP,))
    if caller and address == 0x00126430:
        ptr = int.from_bytes(case.data[0x104:0x108], "little")
        return frozenset(range(DATA + 0x104, DATA + 0x108)) | frozenset(
            (ptr + FUNCTIONS[address]["offset"],))
    return frozenset((case.registers[0] + FUNCTIONS[address]["offset"],))


def run(code_path: Path, output: Path, seed: int, samples: int) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    output.mkdir(parents=True, exist_ok=True)
    reference = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                      ROOT / "config/functions.csv")
    reference_evidence = verify_reference(reference)
    source = ROOT / "experiments/semantic_equivalence/byte_predicate_pair_candidates.cpp"
    controls = [f"wrong_{kind}_{address:08x}" for address in FUNCTIONS
                for kind in ("offset", "constant", "sense")]
    required = [spec["symbol"] for spec in FUNCTIONS.values()] + controls
    compiled = compile_candidate_symbols(source, output / "byte_predicate_pair.o",
                                         ROOT, required)
    functions, negatives, caller_results = [], [], []
    for address, spec in FUNCTIONS.items():
        original = Runner(reference.image, address)
        candidate = Runner(reference.image, address, compiled[spec["symbol"]])
        negatives_runners = {name: Runner(reference.image, address, compiled[name])
                             for name in controls if name.endswith(f"{address:08x}")}
        count, failure = 0, None
        for case in make_cases(address, seed, samples):
            old, new = original.run(case), candidate.run(case)
            reason = difference(old, new)
            if not reason and (old.reads != _expected_read(address, case) or old.writes):
                reason = "unexpected isolated read/write footprint"
            count += 1
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
        functions.append({"address": hex(address), "candidate": spec["symbol"],
                          "candidate_bytes": len(compiled[spec["symbol"]]),
                          "cases": count, "passed": failure is None, "failure": failure})

        neg_case_value = 2 if address == 0x00126430 else 0
        neg_label = f"byte-{neg_case_value:02x}"
        neg_case = next(case for case in make_cases(address, seed, 0)
                        if case.label == neg_label)
        for kind in ("offset", "constant", "sense"):
            name = f"wrong_{kind}_{address:08x}"
            wrong = negatives_runners[name]
            reason = difference(original.run(neg_case), wrong.run(neg_case))
            negatives.append({"address": hex(address), "control": name,
                              "detected": reason is not None, "reason": reason})

        window = CALLER_WINDOWS[address]
        values = (2, 1) if address == 0x00126430 else (0, 1)
        for value in values:
            case = _caller_case(address, value, seed + value)
            old = original.run(case, start=window["start"], stops=window["stops"], budget=32)
            new = candidate.run(case, start=window["start"], stops=window["stops"], budget=32)
            reason = difference(old, new, returns_value=False, caller_window=True,
                                compare_flags=True)
            if not reason and (old.reads != _expected_read(address, case, caller=True)
                               or old.writes != frozenset()):
                reason = "unexpected caller-window memory footprint"
            caller_results.append({"address": hex(address), "callsite": hex(window["call"]),
                                   "input_byte": value, "path_pc": hex(old.pc),
                                   "passed": reason is None, "reason": reason})

    report = {
        "experiment": "paired_byte_equality_predicates", "seed": seed,
        "random_samples_per_function": samples, "full_byte_domain": True,
        "reference": reference_evidence, "functions": functions,
        "negative_controls": negatives, "caller_windows": caller_results,
        "passed": all(row["passed"] for row in functions + caller_results)
                  and all(row["detected"] for row in negatives),
        "limitations": [
            "Isolated tests exhaust all 256 input byte values and add seeded random register/memory state.",
            "Caller windows start at the first pinned setup instruction; preceding caller production of r4 or stack contents is supplied synthetically.",
            "Two representative direct callers are tested, not all 17 direct call sites.",
            "No production integration or whole-game/emulator equivalence is claimed.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--output", type=Path, default=Path("build/semantic-equivalence/byte-predicate-pair"))
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--samples", type=int, default=64)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed, args.samples)
    print(json.dumps({"passed": report["passed"], "functions": report["functions"],
                      "negative_controls": report["negative_controls"],
                      "caller_windows": report["caller_windows"]}, indent=2))


if __name__ == "__main__":
    main()
