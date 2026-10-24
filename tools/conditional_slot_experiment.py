#!/usr/bin/env python3
"""Differential-test two conditional pointer-slot initializers."""
from __future__ import annotations

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
from tools.build_check import find_clang
from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference,
)
from tools.semantic_experiment_support import (
    compile_candidate_symbols, load_pinned_reference,
)

FUNCTIONS = {
    0x0014E744: {"offset": 0x28, "callers": (0x002AE7C0, 0x002C5EDC)},
    0x002B0418: {"offset": 0x24,
                 "callers": (0x0029A300, 0x0029BE0C, 0x002AE7B4, 0x002C5ED0)},
}
CALLER_WINDOWS = (
    # This window invokes the +0x24 routine, then immediately reloads the same
    # object pointer and exercises the +0x28 routine on that object.
    {"callee": 0x002B0418, "site": 0x002AE7B4, "stop": 0x002AE7C4,
     "setup": "object_slot_then_second_initializer"},
    {"callee": 0x002B0418, "site": 0x002C5ED0, "stop": 0x002C5EE0,
     "setup": "object_register_then_second_initializer"},
    {"callee": 0x0014E744, "site": 0x002AE7C0, "stop": 0x002AE7C4,
     "setup": "direct_object_and_value"},
    {"callee": 0x0014E744, "site": 0x002C5EDC, "stop": 0x002C5EE0,
     "setup": "object_register_and_value"},
)
U32_MASK = 0xFFFFFFFF


def _instructions(image: bytes, address: int, size: int):
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    offset = address - TEXT
    decoded = list(decoder.disasm(image[offset:offset + size], address))
    return tuple((item.mnemonic.lower(), item.op_str.lower()) for item in decoded), sum(
        item.size for item in decoded
    )


def _direct_callers(image: bytes, targets: set[int]) -> dict[int, tuple[int, ...]]:
    found = {address: [] for address in targets}
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


def verify_reference(image: bytes, game_info: dict, ledger: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != game_info["code_sha256"]:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    by_address = {int(row["address"], 16): row for row in ledger}
    result = {}
    for address, details in FUNCTIONS.items():
        row = by_address.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != 28:
            raise ValueError(f"Missing matching 28-byte ledger row at {address:#010x}")
        offset = details["offset"]
        expected = (
            ("ldr", "r2, [r0]"), ("cmp", "r2, #0"), ("mov", "r2, #0"),
            ("moveq", "r2, #1"), ("streq", f"r1, [r0, #0x{offset:x}]"),
            ("mov", "r0, r2"), ("bx", "lr"),
        )
        actual, size = _instructions(image, address, 28)
        if actual != expected or size != 28:
            raise ValueError(f"Original instruction sequence changed at {address:#010x}: {actual}")
        result[hex(address)] = {
            "offset": hex(offset), "size": size,
            "instructions": [f"{mnemonic} {operands}" for mnemonic, operands in actual],
            "function_sha256": hashlib.sha256(image[address - TEXT:address - TEXT + size]).hexdigest(),
            "ledger_name": row["name"], "category": row["category"],
        }

    callers = _direct_callers(image, set(FUNCTIONS))
    for address, details in FUNCTIONS.items():
        if callers[address] != details["callers"]:
            raise ValueError(f"Direct caller set changed at {address:#010x}: {callers[address]}")
    caller_evidence = {}
    for window in CALLER_WINDOWS:
        site, target = window["site"], window["callee"]
        actual, _ = _instructions(image, site, 4)
        if actual != (("bl", f"#0x{target:x}"),):
            raise ValueError(f"Caller BL changed at {site:#010x}")
        caller_evidence[hex(site)] = {
            "callee": hex(target), "stop": hex(window["stop"]),
            "setup": window["setup"],
            "scope": "Starts at the pinned BL; argument setup before it is not executed.",
        }
    return {"code_sha256": digest, "functions": result,
            "callers": {hex(address): [hex(site) for site in sites]
                        for address, sites in callers.items()},
            "caller_windows": caller_evidence}


def _make_case(address: int, seed: int, label: str, existing: int,
               value: int, second_value: int = 0) -> Case:
    salt = sum((index + 1) * ord(char) for index, char in enumerate(label))
    rng = random.Random(seed ^ address ^ salt)
    data = bytearray(rng.randbytes(DATA_SIZE))
    object_pointer = DATA + 0x200
    struct.pack_into("<I", data, object_pointer - DATA, existing & U32_MASK)
    registers = [rng.getrandbits(32) for _ in range(13)]
    registers[0], registers[1] = object_pointer, value & U32_MASK
    # The chained 0x002AE7B4 / 0x002C5ED0 caller windows reuse one object via
    # r4/r5 and then call the other initializer with the secondary payload.
    registers[4] = DATA + 0x80
    registers[5] = object_pointer
    registers[7] = second_value & U32_MASK
    registers[8] = second_value & U32_MASK
    struct.pack_into("<I", data, 0x80, object_pointer)
    return Case(label, tuple(registers), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def make_cases(address: int, samples: int, seed: int):
    boundaries = (
        (0, 0, "empty-zero-value"),
        (0, 1, "empty-one-value"),
        (0, U32_MASK, "empty-max-value"),
        (1, 0x12345678, "occupied-one"),
        (U32_MASK, 0x87654321, "occupied-max"),
        (0x80000000, 0xAABBCCDD, "occupied-sign-bit"),
    )
    for existing, value, label in boundaries:
        yield _make_case(address, seed, label, existing, value)
    rng = random.Random(seed ^ address)
    for index in range(samples):
        yield _make_case(address, seed + index, f"random-{index}",
                         rng.getrandbits(32), rng.getrandbits(32))


def _caller_case(window: dict, seed: int, index: int, existing: int) -> Case:
    address = window["callee"]
    case = _make_case(address, seed + index, f"caller-{address:08x}-{index}",
                      existing, 0x13579BDF + index, 0x2468ACE0 + index)
    registers = list(case.registers)
    if window["setup"] == "object_slot_then_second_initializer":
        registers[0] = DATA + 0x200
        registers[1] = 0x13579BDF + index
        registers[4] = DATA + 0x80
        registers[7] = 0x2468ACE0 + index
    elif window["setup"] == "object_register_then_second_initializer":
        registers[0] = DATA + 0x200
        registers[1] = 0x13579BDF + index
        registers[5] = DATA + 0x200
        registers[8] = 0x2468ACE0 + index
    elif window["setup"] == "object_register_and_value":
        registers[0] = DATA + 0x200
        registers[1] = 0x2468ACE0 + index
        registers[5] = DATA + 0x200
    return Case(case.label, tuple(registers), case.data, case.stack, case.nzcv)


def run(code_path: Path, output: Path, samples: int = 64,
        seed: int = 20261024) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    reference_input = load_pinned_reference(
        code_path, ROOT / "config/game_info.json", ROOT / "config/functions.csv"
    )
    image, game_info, ledger = (reference_input.image, reference_input.game_info,
                                reference_input.ledger)
    reference = verify_reference(image, game_info, ledger)
    output.mkdir(parents=True, exist_ok=True)
    source_path = ROOT / "experiments/semantic_equivalence/conditional_slot_candidates.cpp"
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    compiled = compile_candidate_symbols(
        source_path, output / "conditional_slot_candidates.o", ROOT,
        {"candidate_0014e744", "candidate_002b0418",
         "negative_wrong_field", "negative_store_unconditionally"},
    )

    functions = []
    for address, details in FUNCTIONS.items():
        symbol = f"candidate_{address:08x}"
        original, candidate = Runner(image, address), Runner(image, address, compiled[symbol])
        count, failure = 0, None
        for case in make_cases(address, samples, seed):
            reason = difference(original.run(case), candidate.run(case),
                                returns_value=True, compare_flags=False)
            count += 1
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
        functions.append({"address": hex(address), "offset": hex(details["offset"]),
                          "original_bytes": 28, "candidate_bytes": len(compiled[symbol]),
                          "cases": count, "passed": failure is None,
                          "failure": failure})

    negative_controls = []
    control_cases = (
        (0x0014E744, "negative_wrong_field", 0, 0xA1B2C3D4),
        (0x002B0418, "negative_store_unconditionally", 0x76543210, 0xDEADBEEF),
    )
    for address, symbol, existing, value in control_cases:
        case = _make_case(address, seed, f"control-{symbol}", existing, value)
        original = Runner(image, address)
        wrong = Runner(image, address, compiled[symbol])
        reason = difference(original.run(case), wrong.run(case),
                            returns_value=True, compare_flags=False)
        negative_controls.append({"name": symbol, "address": hex(address),
                                  "detected": reason is not None, "reason": reason,
                                  "expected_reason": "data memory differs"})

    caller_results = []
    for window in CALLER_WINDOWS:
        address, site, stop = window["callee"], window["site"], window["stop"]
        symbol = f"candidate_{address:08x}"
        original, candidate = Runner(image, address), Runner(image, address, compiled[symbol])
        for index, existing in enumerate((0, 1)):
            case = _caller_case(window, seed, index, existing)
            baseline = original.run(case, start=site, stops=(stop,), budget=128)
            rebuilt = candidate.run(case, start=site, stops=(stop,), budget=128)
            reason = difference(baseline, rebuilt, returns_value=False,
                                caller_window=True, compare_flags=False)
            caller_results.append({"callee": hex(address), "callsite": hex(site),
                                   "initial_header": hex(existing), "passed": reason is None,
                                   "reason": reason, "stop": hex(stop)})

    if hashlib.sha256(source_path.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Candidate source changed during experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True)
    report = {
        "schema": 1, "experiment": "two_conditional_pointer_slot_initializers",
        "passed": (all(item["passed"] for item in functions)
                   and all(item["detected"] for item in negative_controls)
                   and all(item["passed"] for item in caller_results)),
        "scope": "two isolated conditional slot initializers plus four bounded caller windows",
        "reference": reference, "source_sha256": source_hash,
        "compiler": compiler.stdout.splitlines()[0], "seed": seed,
        "random_samples_per_function": samples,
        "function_comparisons": sum(item["cases"] for item in functions),
        "caller_comparisons": len(caller_results), "functions": functions,
        "negative_controls": negative_controls, "caller_results": caller_results,
        "limitations": [
            "Caller windows start at pinned BLs, so preceding object and argument setup is not tested.",
            "Fixtures use aligned ordinary RAM; MMIO, concurrent mutation and partial faults are outside scope.",
            "The tests compare state and consumed values for these bounded paths; they are not whole-game equivalence evidence.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    import argparse
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
