#!/usr/bin/env python3
"""Differentially test four camp-state predicates and selected caller windows."""
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
import time

import capstone

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang
from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, TEXT, U32_MASK, Case, Runner,
    difference, require_unicorn, validate_leaf,
)


FUNCTIONS = {
    0x0028C124: {"symbol": "candidate_0028c124", "offset": 0x2180,
                 "constant": 6, "caller_r_bias": 0x2188},
    0x0028C850: {"symbol": "candidate_0028c850", "offset": 0x2180,
                 "constant": 5, "caller_r_bias": 0x2188},
    0x0028C868: {"symbol": "candidate_0028c868", "offset": 0x3048,
                 "constant": 14, "caller_r_bias": 0x54A8},
    0x002D01EC: {"symbol": "candidate_002d01ec", "offset": 0x2180,
                 "constant": 4, "caller_r_bias": 0x2188},
}
REFERENCE_WORDS = {
    0x0028C124: (0xE2800A02, 0xE5900180, 0xE3500006,
                 0x13A00001, 0x03A00000, 0xE12FFF1E),
    0x0028C850: (0xE2800A02, 0xE5900180, 0xE3500005,
                 0x13A00001, 0x03A00000, 0xE12FFF1E),
    0x0028C868: (0xE2800A03, 0xE5900048, 0xE350000E,
                 0x13A00001, 0x03A00000, 0xE12FFF1E),
    0x002D01EC: (0xE2800A02, 0xE5900180, 0xE3500004,
                 0x13A00001, 0x03A00000, 0xE12FFF1E),
}
EXPECTED_CALLS = {
    0x0028C124: (0x0019E68C, 0x0019E700, 0x0019EAE8, 0x00227D50,
                 0x0026CA9C, 0x0027E594, 0x003AEAD0),
    0x0028C850: (0x0019E440, 0x0019E4C4, 0x0019E520, 0x00267F78,
                 0x0027E5D0, 0x003AEC34, 0x003AF32C),
    0x0028C868: (0x0019E328, 0x0019E388, 0x0019E3A0),
    0x002D01EC: (0x0019E340, 0x003AED38),
}
CALLER_WINDOWS = {
    0x0028C124: {
        "name": "engine_func_0027e584", "call": 0x0027E594,
        "start": 0x0027E58C, "not_equal_stop": 0x0027E5A0,
        "equal_stop": 0x0027E5B4, "setup": "manager_r4_plus_8",
        "instructions": ((0x0027E58C, "ldr", "r4, [r0, #0x20]"),
                          (0x0027E590, "add", "r0, r4, #8"),
                          (0x0027E594, "bl", "#0x28c124"),
                          (0x0027E598, "cmp", "r0, #0"),
                          (0x0027E59C, "beq", "#0x27e5b4")),
    },
    0x0028C850: {
        "name": "engine_func_0027e5c0", "call": 0x0027E5D0,
        "start": 0x0027E5C8, "not_equal_stop": 0x0027E5DC,
        "equal_stop": 0x0027E5F0, "setup": "manager_r4_plus_8",
        "instructions": ((0x0027E5C8, "ldr", "r4, [r0, #0x20]"),
                          (0x0027E5CC, "add", "r0, r4, #8"),
                          (0x0027E5D0, "bl", "#0x28c850"),
                          (0x0027E5D4, "cmp", "r0, #0"),
                          (0x0027E5D8, "beq", "#0x27e5f0")),
    },
    0x002D01EC: {
        "name": "engine_func_003aed28", "call": 0x003AED38,
        "start": 0x003AED30, "not_equal_stop": 0x003AED44,
        "equal_stop": 0x003AED54, "setup": "manager_r4_plus_8",
        "instructions": ((0x003AED30, "ldr", "r4, [r0, #0x20]"),
                          (0x003AED34, "add", "r0, r4, #8"),
                          (0x003AED38, "bl", "#0x2d01ec"),
                          (0x003AED3C, "cmp", "r0, #0"),
                          (0x003AED40, "beq", "#0x3aed54")),
    },
    0x0028C868: {
        "name": "btlUI_Calc", "call": 0x0019E328,
        "start": 0x0019E320, "not_equal_stop": 0x0019E338,
        "equal_stop": 0x0019F1F4, "setup": "preloaded_r4_plus_0x2460",
        "instructions": ((0x0019E320, "add", "r0, r4, #0x2000"),
                          (0x0019E324, "add", "r0, r0, #0x460"),
                          (0x0019E328, "bl", "#0x28c868"),
                          (0x0019E32C, "cmp", "r0, #0"),
                          (0x0019E330, "nop", ""),
                          (0x0019E334, "beq", "#0x19f1f4")),
    },
}
WRONG_SYMBOLS = {
    address: {
        "offset": f"wrong_offset_{address:08x}",
        "constant": f"wrong_constant_{address:08x}",
        "sense": f"wrong_sense_{address:08x}",
    }
    for address in FUNCTIONS
}


def _instruction_at(image: bytes, address: int):
    offset = address - TEXT
    if offset < 0 or offset + 4 > len(image):
        raise ValueError(f"Address outside code image: {address:#010x}")
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    cs.detail = True
    return next(cs.disasm(image[offset:offset + 4], address), None)


def _all_instructions(image: bytes, start: int, count: int):
    result = []
    for index in range(count):
        instruction = _instruction_at(image, start + index * 4)
        if instruction is None:
            raise ValueError(f"Could not decode instruction at {start + index * 4:#010x}")
        result.append(instruction)
    return result


def _ledger_rows() -> list[dict]:
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _scan_direct_calls(image: bytes) -> dict[int, list[int]]:
    """Find ARM BL encodings without assuming linear disassembly over literal pools."""
    refs = {address: [] for address in FUNCTIONS}
    for offset in range(0, len(image) - 3, 4):
        word = struct.unpack_from("<I", image, offset)[0]
        if word & 0x0F000000 != 0x0B000000:
            continue
        displacement = word & 0x00FFFFFF
        if displacement & 0x00800000:
            displacement -= 0x01000000
        site = TEXT + offset
        target = (site + 8 + displacement * 4) & U32_MASK
        if target in refs:
            decoded = _instruction_at(image, site)
            if decoded is None or decoded.mnemonic != "bl" or decoded.operands[0].imm != target:
                raise ValueError(f"BL scan did not decode as expected at {site:#010x}")
            refs[target].append(site)
    return refs


def verify_reference(image: bytes, expected_sha256: str, ledger: list[dict]) -> dict:
    actual_hash = hashlib.sha256(image).hexdigest()
    if not expected_sha256 or actual_hash != expected_sha256:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    by_address = {int(row["address"], 16): row for row in ledger}
    functions = {}
    for address, expected_words in REFERENCE_WORDS.items():
        row = by_address.get(address)
        if row is None or int(row["size"]) != 24 or row["status"] != "matching":
            raise ValueError(f"Missing/changed matching ledger row at {address:#010x}")
        raw = image[address - TEXT:address - TEXT + 24]
        words = struct.unpack("<6I", raw)
        if words != expected_words:
            raise ValueError(f"Original predicate instructions differ at {address:#010x}")
        functions[hex(address)] = {
            "name": row["name"], "category": row["category"], "size": 24,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "instructions": [f"0x{word:08x}" for word in words],
            "field_offset_from_argument": FUNCTIONS[address]["offset"],
            "not_equal_constant": FUNCTIONS[address]["constant"],
        }
    return {"sha256": actual_hash, "functions": functions}


def verify_callers(image: bytes, ledger: list[dict]) -> dict:
    refs = _scan_direct_calls(image)
    by_address = {int(row["address"], 16): row for row in ledger}
    evidence = {}
    for target, expected_sites in EXPECTED_CALLS.items():
        sites = tuple(sorted(refs[target]))
        if sites != tuple(sorted(expected_sites)):
            raise ValueError(f"Direct caller set changed for {target:#010x}: {sites}")
        validated = []
        for site in sites:
            caller = next((row for address, row in by_address.items()
                           if address <= site < address + int(row["size"])), None)
            if caller is None or caller["status"] != "matching":
                raise ValueError(f"Call site {site:#010x} is not in a matching ledger function")
            tail = _all_instructions(image, site + 4, 4)
            # Every known direct caller consumes the boolean with cmp r0, #0,
            # optionally a padding NOP, and a conditional branch.
            if tail[0].mnemonic != "cmp" or tail[0].op_str != "r0, #0":
                raise ValueError(f"Caller stopped consuming r0 at {site:#010x}")
            branch = tail[1]
            if branch.mnemonic == "nop":
                branch = tail[2]
            if branch.mnemonic not in ("beq", "bne"):
                raise ValueError(f"Boolean branch changed after {site:#010x}")
            validated.append({"site": hex(site), "caller": caller["name"],
                              "caller_entry": caller["address"],
                              "compare": "cmp r0, #0", "branch": branch.mnemonic,
                              "branch_target": branch.op_str})
        evidence[hex(target)] = validated

    windows = {}
    for target, window in CALLER_WINDOWS.items():
        instructions = []
        for address, mnemonic, operands in window["instructions"]:
            instruction = _instruction_at(image, address)
            if instruction is None or (instruction.mnemonic, instruction.op_str) != (
                mnemonic, operands
            ):
                raise ValueError(f"Caller window drift at {address:#010x}")
            instructions.append({"address": hex(address), "mnemonic": mnemonic,
                                 "operands": operands, "bytes": instruction.bytes.hex()})
        if window["call"] not in refs[target]:
            raise ValueError(f"Pinned caller window has no BL to {target:#010x}")
        windows[hex(target)] = {
            "caller": window["name"], "call": hex(window["call"]),
            "start": hex(window["start"]),
            "not_equal_stop": hex(window["not_equal_stop"]),
            "equal_stop": hex(window["equal_stop"]),
            "instructions": instructions,
        }
    return {"all_direct_calls": evidence, "tested_windows": windows}


def _write_word(data: bytearray, address: int, value: int) -> None:
    if address < DATA or address + 4 > DATA + DATA_SIZE or address % 4:
        raise ValueError(f"Expected aligned word in mapped test RAM: {address:#010x}")
    struct.pack_into("<I", data, address - DATA, value & U32_MASK)


def _case(address: int, label: str, seed: int, field_value: int) -> Case:
    rng = random.Random(seed ^ address ^ field_value)
    spec = FUNCTIONS[address]
    field_address = DATA + 0x100
    # The two adjacent words deliberately differ from the expected field to
    # expose ±4-byte addressing mistakes while remaining in ordinary RAM.
    data = bytearray(rng.randbytes(DATA_SIZE))
    _write_word(data, field_address - 4, (spec["constant"] + 2) & U32_MASK)
    _write_word(data, field_address, field_value)
    _write_word(data, field_address + 4, (spec["constant"] + 1) & U32_MASK)
    registers = [rng.getrandbits(32) for _ in range(13)]
    registers[0] = (field_address - spec["offset"]) & U32_MASK
    return Case(label, tuple(registers), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def make_cases(address: int, seed: int = 20261024, samples: int = 64) -> list[Case]:
    if samples < 0:
        raise ValueError("samples must be nonnegative")
    constant = FUNCTIONS[address]["constant"]
    fixed = [
        ("below-constant", constant - 1),
        ("equal-constant", constant),
        ("above-constant", constant + 1),
        ("zero", 0),
        ("high-bit", 0x80000000),
        ("all-ones", U32_MASK),
    ]
    cases = [_case(address, label, seed + index, value)
             for index, (label, value) in enumerate(fixed)]
    rng = random.Random(seed ^ address)
    for index in range(samples):
        value = rng.choice((rng.getrandbits(32), constant, constant - 1,
                            constant + 1, 0x7FFFFFFF, 0x80000000, U32_MASK))
        cases.append(_case(address, f"random-{index}", seed + index + 6, value))
    return cases


def _compile_candidates(output: Path) -> tuple[dict[str, bytes], Path]:
    source = ROOT / "experiments/semantic_equivalence/state_predicate_candidates.cpp"
    obj = output / "state_predicate_candidates.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    functions = extract_elf_functions_detailed(obj)
    required = [spec["symbol"] for spec in FUNCTIONS.values()]
    required.extend(symbol for family in WRONG_SYMBOLS.values()
                    for symbol in family.values())
    compiled = {}
    for symbol in required:
        if symbol not in functions:
            raise ValueError(f"Missing candidate symbol: {symbol}")
        code, relocations = functions[symbol]
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        validate_leaf(code)
        compiled[symbol] = code
    return compiled, obj


def _caller_case(address: int, field_value: int, seed: int) -> Case:
    window = CALLER_WINDOWS[address]
    spec = FUNCTIONS[address]
    field_address = DATA + 0x100
    rng = random.Random(seed ^ address ^ field_value)
    data = bytearray(rng.randbytes(DATA_SIZE))
    _write_word(data, field_address - 4, spec["constant"] + 2)
    _write_word(data, field_address, field_value)
    _write_word(data, field_address + 4, spec["constant"] + 1)
    registers = [rng.getrandbits(32) for _ in range(13)]
    if window["setup"] == "manager_r4_plus_8":
        manager = DATA + 0x200
        synthetic_r4 = (field_address - spec["caller_r_bias"]) & U32_MASK
        _write_word(data, manager + 0x20, synthetic_r4)
        registers[0] = manager
    else:
        registers[4] = (field_address - spec["caller_r_bias"]) & U32_MASK
    return Case(f"caller-{field_value:#x}", tuple(registers), bytes(data),
                rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def _expected_field_reads(address: int, *, caller: bool) -> frozenset[int]:
    field = DATA + 0x100
    expected = set(range(field, field + 4))
    if caller and CALLER_WINDOWS[address]["setup"] == "manager_r4_plus_8":
        expected.update(range(DATA + 0x200 + 0x20, DATA + 0x200 + 0x24))
    return frozenset(expected)


def run(code_path: Path, output: Path, seed: int = 20261024,
        samples: int = 64) -> dict:
    require_unicorn()
    if samples < 0:
        raise ValueError("samples must be nonnegative")
    started = time.perf_counter()
    image = Path(code_path).read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    ledger = _ledger_rows()
    reference = verify_reference(image, game["code_sha256"], ledger)
    caller_evidence = verify_callers(image, ledger)
    source = ROOT / "experiments/semantic_equivalence/state_predicate_candidates.cpp"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    compiled, obj = _compile_candidates(output)

    results = []
    controls = []
    for address, spec in FUNCTIONS.items():
        oracle = Runner(image, address)
        rebuilt = Runner(image, address, compiled[spec["symbol"]])
        comparisons = []
        for case in make_cases(address, seed, samples):
            original = oracle.run(case)
            candidate = rebuilt.run(case)
            reason = difference(original, candidate)
            expected_reads = _expected_field_reads(address, caller=False)
            if reason is None and (original.reads != expected_reads or original.writes):
                reason = "unexpected isolated read/write footprint"
            comparisons.append({"case": case.label, "passed": reason is None,
                                "reason": reason})
        results.append({
            "address": hex(address), "candidate": spec["symbol"],
            "field_offset": hex(spec["offset"]), "not_equal_constant": spec["constant"],
            "original_bytes": 24, "candidate_bytes": len(compiled[spec["symbol"]]),
            "byte_identical": image[address - TEXT:address - TEXT + 24]
            == compiled[spec["symbol"]], "passed": all(item["passed"] for item in comparisons),
            "case_count": len(comparisons), "cases": comparisons,
        })

        equal_case = _case(address, "equal-constant-negative-control", seed,
                           spec["constant"])
        for kind, symbol in WRONG_SYMBOLS[address].items():
            wrong = Runner(image, address, compiled[symbol])
            reason = difference(oracle.run(equal_case), wrong.run(equal_case))
            controls.append({"address": hex(address), "kind": kind,
                             "candidate": symbol, "detected": reason == "return value differs",
                             "reason": reason})

    caller_results = []
    for address, window in CALLER_WINDOWS.items():
        spec = FUNCTIONS[address]
        original = Runner(image, address)
        rebuilt = Runner(image, address, compiled[spec["symbol"]])
        for value, expected_stop, label in (
            (spec["constant"], window["equal_stop"], "equal"),
            (spec["constant"] + 1, window["not_equal_stop"], "not-equal"),
        ):
            case = _caller_case(address, value, seed + value)
            original_run = original.run(case, start=window["start"],
                                        stops=(window["equal_stop"], window["not_equal_stop"]))
            candidate_run = rebuilt.run(case, start=window["start"],
                                        stops=(window["equal_stop"], window["not_equal_stop"]))
            reason = difference(original_run, candidate_run, caller_window=True,
                                compare_flags=True)
            if reason is None and original_run.pc != expected_stop:
                reason = "caller reached unexpected branch continuation"
            expected_reads = _expected_field_reads(address, caller=True)
            if reason is None and (original_run.reads != expected_reads or original_run.writes):
                reason = "unexpected caller-window read/write footprint"
            caller_results.append({
                "address": hex(address), "caller": window["name"], "path": label,
                "field_value": hex(value), "expected_stop": hex(expected_stop),
                "original_stop": hex(original_run.pc),
                "candidate_stop": hex(candidate_run.pc), "passed": reason is None,
                "reason": reason,
                "reads": sorted(hex(item) for item in original_run.reads),
                "writes": sorted(hex(item) for item in original_run.writes),
            })

    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Candidate source changed during experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True).stdout.splitlines()[0]
    report = {
        "passed": all(item["passed"] for item in results)
        and all(item["detected"] for item in controls)
        and all(item["passed"] for item in caller_results),
        "scope": "four isolated state predicates and four original caller fragments; production/docs/IPS/emulator untouched",
        "reference": reference, "caller_evidence": caller_evidence,
        "source_sha256": source_hash,
        "object_sha256": hashlib.sha256(obj.read_bytes()).hexdigest(),
        "compiler": compiler, "seed": seed, "random_samples_per_function": samples,
        "functions": results, "negative_controls": controls,
        "caller_window_results": caller_results,
        "setup_limitations": [
            "Three selected callers load the state pointer from the game's global singleton before the pinned window; the window starts after that literal/global setup and supplies a synthetic manager object.",
            "The 28c868 window starts at the original field-offset setup with synthetic r4. It verifies the real adds, BL, compare and branch, not the earlier producer of r4.",
            "Synthetic state pointers are chosen so the final field lands in the shared runner's 4 KiB DATA map; this does not assert a recovered full game structure layout.",
        ],
        "limitations": [
            "The exact enclosing structure names/types are unknown; claims are limited to observed 32-bit offsets and comparisons.",
            "Only aligned ordinary RAM is tested; root/base null is not handled by the original LDR and is outside the successful-input contract.",
            "Bounded differential tests do not prove behavior in all game states or full-game integration.",
        ],
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"State predicate experiment {'PASS' if report['passed'] else 'FAIL'}; report: {report_path}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/state-predicates/seed-20261024")
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--samples", type=int, default=64)
    args = parser.parse_args()
    try:
        report = run(args.code, args.output, args.seed, args.samples)
    except (RuntimeError, ValueError, OSError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
