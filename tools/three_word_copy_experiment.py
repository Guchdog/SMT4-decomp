#!/usr/bin/env python3
"""Differential-test three offset-specific 12-byte ARM copy reconstructions."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang
from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, SP, TEXT, Case, Runner, difference, validate_leaf,
)

FUNCTIONS = {
    0x00232B00: {"offset": 0x4C, "caller": 0x00396AE4},
    0x00232B14: {"offset": 0x40, "caller": 0x00396AD8},
    0x00232B28: {"offset": 0x28, "caller": 0x00396ACC},
}
ALL_ADDRESSES = tuple(FUNCTIONS)
EXPECTED_CALLERS = {
    0x00232B00: (0x00396AE4, 0x00396C4C, 0x00396F90),
    0x00232B14: (0x00396AD8, 0x00396C40, 0x00396F84),
    0x00232B28: (0x00396ACC, 0x00396C34, 0x00396F78),
}
U32_MASK = 0xFFFFFFFF


def discover_bl_callers(image: bytes) -> dict[int, tuple[int, ...]]:
    """Find ARM BL references by decoding the immediate branch displacement."""
    found = {address: [] for address in ALL_ADDRESSES}
    for index in range(len(image) // 4):
        word = struct.unpack_from("<I", image, index * 4)[0]
        if (word & 0x0F000000) != 0x0B000000 or (word >> 28) == 0xF:
            continue
        displacement = (word & 0x00FFFFFF) << 2
        if displacement & (1 << 25):
            displacement -= 1 << 26
        site = TEXT + index * 4
        target = (site + 8 + displacement) & U32_MASK
        if target in found:
            found[target].append(site)
    return {address: tuple(sites) for address, sites in found.items()}


def _disassemble(image: bytes, address: int, size: int):
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    start = address - TEXT
    instructions = list(decoder.disasm(image[start:start + size], address))
    return tuple((item.mnemonic.lower(), item.op_str.lower()) for item in instructions), sum(
        item.size for item in instructions
    )


def verify_reference(image: bytes, expected_hash: str, ledger: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != expected_hash:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    by_address = {int(row["address"], 16): row for row in ledger}
    expected_shape = (
        ("ldrd", "r2, r3, [r1]"),
        ("ldr", "r1, [r1, #8]"),
        ("str", "r1, [r0, #0x54]"),
        ("strd", "r2, r3, [r0, #0x4c]"),
        ("bx", "lr"),
    )
    functions = {}
    for address, details in FUNCTIONS.items():
        row = by_address.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != 20:
            raise ValueError(f"Missing matching 20-byte ledger row at {address:#010x}")
        offset = details["offset"]
        shape = list(expected_shape)
        shape[2] = ("str", f"r1, [r0, #0x{offset + 8:x}]")
        shape[3] = ("strd", f"r2, r3, [r0, #0x{offset:x}]")
        actual, decoded_size = _disassemble(image, address, 20)
        if actual != tuple(shape) or decoded_size != 20:
            raise ValueError(f"Original instruction sequence changed at {address:#010x}: {actual}")
        functions[hex(address)] = {
            "offset": hex(offset), "ledger_name": row["name"],
            "category": row["category"], "size": 20,
            "sha256": hashlib.sha256(image[address - TEXT:address - TEXT + 20]).hexdigest(),
            "instructions": [f"{mnemonic} {operands}" for mnemonic, operands in actual],
        }

    callers = discover_bl_callers(image)
    for address, expected in EXPECTED_CALLERS.items():
        if callers[address] != expected:
            raise ValueError(
                f"Direct callers changed at {address:#010x}: expected "
                f"{[hex(site) for site in expected]}, got {[hex(site) for site in callers[address]]}"
            )
    caller_instructions = {}
    for address, site in ((address, details["caller"])
                          for address, details in FUNCTIONS.items()):
        actual, _ = _disassemble(image, site, 4)
        if len(actual) != 1 or actual[0] != ("bl", f"#0x{address:x}"):
            raise ValueError(f"Caller BL changed at {site:#010x}")
        after, _ = _disassemble(image, site + 4, 4)
        caller_instructions[hex(site)] = {
            "callee": hex(address), "bl": f"bl #0x{address:x}",
            "continuation_instruction": f"{after[0][0]} {after[0][1]}" if after else None,
            "result_consumption": "r0 is overwritten/reloaded before being consumed",
        }
    return {"code_sha256": digest, "functions": functions,
            "caller_windows": caller_instructions,
            "direct_caller_counts": {hex(a): len(callers[a]) for a in ALL_ADDRESSES}}


def _case(spec_address: int, label: str, seed: int, source_delta: int,
          first: int | None = None, second: int | None = None, third: int | None = None) -> Case:
    label_salt = sum((index + 1) * ord(character)
                     for index, character in enumerate(label))
    rng = random.Random(seed ^ spec_address ^ label_salt)
    data = bytearray(rng.randbytes(DATA_SIZE))
    destination_base = DATA + 0x300
    effective = destination_base + FUNCTIONS[spec_address]["offset"]
    source = effective + source_delta
    words = (first if first is not None else rng.getrandbits(32),
             second if second is not None else rng.getrandbits(32),
             third if third is not None else rng.getrandbits(32))
    for index, value in enumerate(words):
        struct.pack_into("<I", data, source - DATA + index * 4, value & U32_MASK)
    registers = [rng.getrandbits(32) for _ in range(13)]
    registers[0], registers[1] = destination_base, source
    return Case(label, tuple(registers), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def make_cases(address: int, samples: int, seed: int):
    offset = FUNCTIONS[address]["offset"]
    fixed = (
        (0x100, "non-overlap-pattern", 0x11223344, 0xAABBCCDD, 0xDEADBEEF),
        (0, "exact-alias", 1, 0x80000000, U32_MASK),
        (-4, "destination-starts-after-source", 0x01020304, 0xA1A2A3A4, 0xB1B2B3B4),
        (4, "destination-starts-before-source", 0x11223344, 0x55667788, 0x99AABBCC),
        (0x100, "zero-words", 0, 0, 0),
        (0x100, "distinct-boundaries", U32_MASK, 0x7FFFFFFF, 0x80000000),
    )
    for source_delta, label, first, second, third in fixed:
        yield _case(address, label, seed, source_delta, first, second, third)
    rng = random.Random(seed ^ address)
    for index in range(samples):
        yield _case(address, f"random-{index}", seed + index,
                    0x100 + (index % 16) * 4,
                    rng.getrandbits(32), rng.getrandbits(32), rng.getrandbits(32))


def _candidate_load_store_order(code: bytes):
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoded = list(decoder.disasm(code, 0x01000000))
    memory_ops = []
    for item in decoded:
        if item.mnemonic.startswith(("ldr", "str")):
            memory_ops.append(("load" if item.mnemonic.startswith("ldr") else "store",
                               item.mnemonic, item.op_str))
    first_store = next((i for i, item in enumerate(memory_ops) if item[0] == "store"), len(memory_ops))
    return memory_ops, first_store


def _caller_case(address: int, seed: int, index: int) -> Case:
    rng = random.Random(seed ^ address ^ (index * 0x9E3779B1))
    data = bytearray(rng.randbytes(DATA_SIZE))
    destination_base, source = DATA + 0x280, DATA + 0x100
    for word_index in range(3):
        struct.pack_into("<I", data, source - DATA + word_index * 4,
                         rng.getrandbits(32))
    registers = [rng.getrandbits(32) for _ in range(13)]
    registers[0], registers[1] = destination_base, source
    return Case(f"caller-{address:08x}-{index}", tuple(registers), bytes(data),
                rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def run(code_path: Path, output: Path, samples: int = 64, seed: int = 20261024) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        ledger = list(csv.DictReader(stream))
    reference = verify_reference(image, game["code_sha256"], ledger)

    source_path = ROOT / "experiments/semantic_equivalence/three_word_copy_candidates.cpp"
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    object_path = output / "three_word_copy_candidates.o"
    build = compile_tu_armv6k(source_path, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    compiled = {}
    for symbol, (code, relocations) in extract_elf_functions_detailed(object_path).items():
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        validate_leaf(code)
        compiled[symbol] = code
    required = {f"candidate_{address:08x}" for address in ALL_ADDRESSES} | {
        "negative_wrong_destination", "negative_late_load",
    }
    if missing := required - compiled.keys():
        raise ValueError(f"Missing compiled candidate symbols: {sorted(missing)}")

    for address in ALL_ADDRESSES:
        symbol = f"candidate_{address:08x}"
        memory_ops, first_store = _candidate_load_store_order(compiled[symbol])
        if first_store != 3 or len(memory_ops) != 6:
            raise ValueError(f"Expected 3 loads before 3 stores in {symbol}: {memory_ops}")

    functions = []
    for address in ALL_ADDRESSES:
        symbol = f"candidate_{address:08x}"
        original, candidate = Runner(image, address), Runner(image, address, compiled[symbol])
        count, failure = 0, None
        labels = []
        for case in make_cases(address, samples, seed):
            reason = difference(original.run(case), candidate.run(case),
                                returns_value=True, compare_flags=True)
            count += 1
            labels.append(case.label)
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
        functions.append({"address": hex(address), "destination_offset": hex(FUNCTIONS[address]["offset"]),
                          "original_bytes": 20, "candidate_bytes": len(compiled[symbol]),
                          "candidate_load_store_order": _candidate_load_store_order(compiled[symbol])[0],
                          "passed": failure is None, "cases": count,
                          "directed_cases": [label for label in labels if not label.startswith("random-")],
                          "failure": failure})

    controls = []
    wrong_offset_case = _case(0x00232B00, "control-wrong-offset", seed, 0x100,
                              0x12345678, 0x23456789, 0x3456789A)
    original = Runner(image, 0x00232B00)
    wrong = Runner(image, 0x00232B00, compiled["negative_wrong_destination"])
    reason = difference(original.run(wrong_offset_case), wrong.run(wrong_offset_case),
                        returns_value=True, compare_flags=True)
    controls.append({"name": "negative_wrong_destination", "detected": reason is not None,
                     "reason": reason, "expected_reason": "data memory differs"})

    late_load_case = _case(0x00232B14, "control-late-load", seed, -4,
                           0x01020304, 0xA1A2A3A4, 0xB1B2B3B4)
    original = Runner(image, 0x00232B14)
    wrong = Runner(image, 0x00232B14, compiled["negative_late_load"])
    reason = difference(original.run(late_load_case), wrong.run(late_load_case),
                        returns_value=True, compare_flags=True)
    controls.append({"name": "negative_late_load", "detected": reason is not None,
                     "reason": reason, "expected_reason": "data memory differs"})

    caller_results = []
    for address in ALL_ADDRESSES:
        site = FUNCTIONS[address]["caller"]
        symbol = f"candidate_{address:08x}"
        original, candidate = Runner(image, address), Runner(image, address, compiled[symbol])
        for index in range(2):
            case = _caller_case(address, seed, index)
            left = original.run(case, start=site, stops=(site + 4,), budget=32)
            right = candidate.run(case, start=site, stops=(site + 4,), budget=32)
            reason = difference(left, right, returns_value=True,
                                caller_window=True, compare_flags=True)
            caller_results.append({"callee": hex(address), "callsite": hex(site),
                                   "case": case.label, "passed": reason is None,
                                   "reason": reason})

    if hashlib.sha256(source_path.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Candidate source changed during the experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True)
    report = {
        "schema": 1, "experiment": "three_12_byte_record_copies",
        "passed": all(item["passed"] for item in functions)
                  and all(item["detected"] for item in controls)
                  and all(item["passed"] for item in caller_results),
        "scope": "three isolated 12-byte copies; aligned ordinary RAM, including exact and partial overlap",
        "reference_sha256": reference["code_sha256"], "reference": reference,
        "source_sha256": source_hash,
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler": compiler.stdout.splitlines()[0], "seed": seed,
        "random_samples_per_function": samples,
        "function_comparisons": sum(item["cases"] for item in functions),
        "caller_comparisons": len(caller_results), "functions": functions,
        "negative_controls": controls, "caller_results": caller_results,
        "limitations": [
            "The three real caller windows start at the pinned BL and stop immediately after return; they do not execute the preceding object/stack setup or later field consumers.",
            "Tests model aligned ordinary RAM only, not MMIO, concurrent mutation, unaligned accesses, or partial-fault behavior.",
            "This isolated ARM evidence is not a whole-game equivalence proof and does not change production sources or the match ledger.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    report = run(args.code, args.output, samples=args.samples, seed=args.seed)
    print(json.dumps({"passed": report["passed"],
                      "function_comparisons": report["function_comparisons"],
                      "caller_comparisons": report["caller_comparisons"],
                      "negative_controls": report["negative_controls"]}, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
