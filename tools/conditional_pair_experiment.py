#!/usr/bin/env python3
"""Differential-test two conditional contiguous two-word stores."""
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
    DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference, validate_leaf,
)

FUNCTIONS = {0x00110C2C: 0x1C, 0x00121150: 0x30}
CALLERS = {0x00110C2C: (0x00103714,), 0x00121150: (0x001095E0,)}
ALL_ADDRESSES = tuple(FUNCTIONS)
U32_MASK = 0xFFFFFFFF


def _arm_imm(value: int) -> str:
    return f"#{value}" if value < 10 else f"#0x{value:x}"


def _instructions(image: bytes, address: int, size: int):
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    start = address - TEXT
    decoded = list(decoder.disasm(image[start:start + size], address))
    return tuple((item.mnemonic, item.op_str) for item in decoded), sum(
        item.size for item in decoded
    )


def discover_bl_callers(image: bytes) -> dict[int, tuple[int, ...]]:
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


def verify_reference(image: bytes, configured_hash: str, rows: list[dict]) -> None:
    if hashlib.sha256(image).hexdigest() != configured_hash:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    by_address = {int(row["address"], 16): row for row in rows}
    for address, offset in FUNCTIONS.items():
        row = by_address.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != 24:
            raise ValueError(f"Missing matching 24-byte function at {address:#010x}")
        expected = (
            ("cmp", "r1, #0"),
            ("addne", f"r0, r0, {_arm_imm(offset)}"),
            ("moveq", "r0, #0"),
            ("stmne", "r0, {r1, r2}"),
            ("movne", "r0, #1"),
            ("bx", "lr"),
        )
        actual, decoded_size = _instructions(image, address, 24)
        if actual != expected or decoded_size != 24:
            raise ValueError(f"Original instructions changed at {address:#010x}: {actual}")
    callers = discover_bl_callers(image)
    for address, expected_sites in CALLERS.items():
        if callers[address] != expected_sites:
            raise ValueError(f"Caller BL set changed at {address:#010x}: {callers[address]}")


def _case(seed: int, label: str, address: int, first: int, second: int) -> Case:
    rng = random.Random(seed ^ address)
    data = bytearray(rng.randbytes(DATA_SIZE))
    context = DATA + 0x100
    offset = FUNCTIONS[address]
    struct.pack_into("<II", data, context - DATA + offset, 0xDEADBEEF, 0xA55AA55A)
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0], regs[1], regs[2] = context, first & U32_MASK, second & U32_MASK
    return Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def _cases(address: int, samples: int, seed: int):
    offset = FUNCTIONS[address]
    context = DATA + 0x100
    field = context + offset
    fixed = (
        (0, 0xCAFEBABE, "null-zero-second"),
        (0, U32_MASK, "null-max-second"),
        (1, 2, "non-null-small-values"),
        (0x11223344, 0xAABBCCDD, "distinct-pattern"),
        (0x80000000, U32_MASK, "unsigned-boundaries"),
        (field, field + 4, "pointer-value-equals-destination"),
    )
    for index, (first, second, label) in enumerate(fixed):
        yield _case(seed + index, label, address, first, second)
    rng = random.Random(seed ^ address)
    for index in range(samples):
        # Alternate null/non-null first arguments; for non-null inputs use
        # both scalar and mapped-address-shaped values (stored, never loaded).
        first = 0 if index % 2 == 0 else rng.choice((rng.getrandbits(32),
                                                       DATA + 0x400 + (index & 0xFC)))
        yield _case(seed + 100 + index, f"random-pair-{index}", address,
                    first, rng.getrandbits(32))


def _caller_case(seed: int, label: str, address: int, first: int, second: int) -> Case:
    case = _case(seed, label, address, first, second)
    return case


def run(code_path: Path, output: Path, samples: int = 64, seed: int = 20261024) -> dict:
    if samples < 0:
        raise ValueError("samples must be nonnegative")
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    verify_reference(image, game["code_sha256"], rows)

    source = ROOT / "experiments/semantic_equivalence/conditional_pair_candidates.cpp"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    object_path = output / "conditional_pair_candidates.o"
    build = compile_tu_armv6k(source, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    compiled = {}
    for symbol, (code, relocations) in extract_elf_functions_detailed(object_path).items():
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        validate_leaf(code)
        compiled[symbol] = code
    required = {f"candidate_{address:08x}" for address in ALL_ADDRESSES} | {
        "negative_wrong_offset", "negative_reversed_pair",
        "negative_unconditional_store", "negative_wrong_boolean",
    }
    missing = required - compiled.keys()
    if missing:
        raise ValueError(f"Missing compiled symbols: {sorted(missing)}")

    results = []
    for address, offset in FUNCTIONS.items():
        original = Runner(image, address)
        candidate = Runner(image, address, compiled[f"candidate_{address:08x}"],
                           replacement_validator=validate_leaf)
        count = 0
        failure = None
        for case in _cases(address, samples, seed):
            reason = difference(original.run(case), candidate.run(case), returns_value=True)
            count += 1
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
        result = {"address": hex(address), "offset": hex(offset),
                  "original_bytes": 24,
                  "candidate_bytes": len(compiled[f"candidate_{address:08x}"]),
                  "cases": count, "passed": failure is None, "failure": failure}
        results.append(result)
        print(json.dumps(result), flush=True)

    controls = (
        (0x00110C2C, "negative_wrong_offset", 0x11223344, 0xAABBCCDD,
         "distinct-pattern"),
        (0x00121150, "negative_reversed_pair", 0x11223344, 0xAABBCCDD,
         "distinct-pattern"),
        (0x00121150, "negative_unconditional_store", 0, U32_MASK,
         "null-max-second"),
        (0x00110C2C, "negative_wrong_boolean", 1, 2,
         "non-null-small-values"),
    )
    negative_controls = []
    for address, symbol, first, second, label in controls:
        case = next(case for case in _cases(address, 0, seed)
                    if case.label == label)
        original = Runner(image, address)
        wrong = Runner(image, address, compiled[symbol], replacement_validator=validate_leaf)
        reason = difference(original.run(case), wrong.run(case), returns_value=True)
        negative_controls.append({"name": symbol, "target": hex(address),
                                  "detected": reason is not None, "reason": reason})

    # Execute each actual BL instruction with injected caller arguments, then
    # stop at its continuation. This validates call/return integration without
    # running whole sound setup routines or their PC-relative global accesses.
    caller_windows = []
    caller_arguments = ((0, 0xCAFEBABE), (DATA + 0x400, 0x12345678))
    for address, sites in CALLERS.items():
        candidate_code = compiled[f"candidate_{address:08x}"]
        for site in sites:
            original = Runner(image, address)
            candidate = Runner(image, address, candidate_code,
                               replacement_validator=validate_leaf)
            for index, (first, second) in enumerate(caller_arguments):
                case = _caller_case(seed + index + site, f"{hex(site)}-arg-{index}",
                                    address, first, second)
                original_result = original.run(case, start=site, stops=(site + 4,))
                candidate_result = candidate.run(case, start=site, stops=(site + 4,))
                reason = difference(original_result, candidate_result,
                                    returns_value=True, caller_window=True,
                                    compare_flags=False)
                caller_windows.append({"target": hex(address), "callsite": hex(site),
                                       "case": case.label, "passed": reason is None,
                                       "failure": reason})

    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Candidate source changed during the experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True)
    report = {
        "schema": 1,
        "passed": all(item["passed"] for item in results)
                  and all(item["detected"] for item in negative_controls)
                  and all(item["passed"] for item in caller_windows),
        "scope": "two conditional two-word stores at offsets +0x1c/+0x30; aligned in-bounds ordinary RAM",
        "reference_sha256": hashlib.sha256(image).hexdigest(),
        "source_sha256": source_hash,
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler": compiler.stdout.splitlines()[0],
        "seed": seed,
        "random_cases_per_function": samples,
        "functions": results,
        "verified_callers": {hex(target): [hex(site) for site in sites]
                              for target, sites in CALLERS.items()},
        "caller_windows": caller_windows,
        "negative_controls": negative_controls,
        "limitations": [
            "Caller windows begin at the verified BL with arguments injected; preceding allocation/global setup is not executed",
            "The observed callers are sound-effect setup paths; their actual global allocator state and object layout are not modeled",
            "The stored r1 value is not dereferenced; null/non-null and pointer-shaped values are tested as data",
            "Bounded differential testing is evidence, not a formal equivalence proof",
            "Only aligned, in-bounds ordinary RAM is covered; MMIO, concurrency, unaligned access, exceptions and partial-fault ordering are excluded",
            "No production source, ledger, game image, emulator, patch or save data is changed",
        ],
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Conditional pair-store experiment {'PASS' if report['passed'] else 'FAIL'}; report: {report_path}", flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/conditional-pairs")
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    try:
        result = run(args.code, args.output, args.samples, args.seed)
    except (RuntimeError, ValueError, OSError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
