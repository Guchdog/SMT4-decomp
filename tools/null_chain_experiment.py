#!/usr/bin/env python3
"""Differentially test five isolated null-aware pointer-chain getters."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys

import capstone

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang
from tools.semantic_experiment import (
    DATA, DATA_SIZE, TEXT, Case, Runner, difference, validate_leaf,
)

U32_MASK = 0xFFFFFFFF
FUNCTIONS = {
    0x00141468: {"symbol": "candidate_00141468", "first": 8, "second": 0},
    0x002344B4: {"symbol": "candidate_002344b4", "first": 4, "second": 8},
    0x003DF578: {"symbol": "candidate_003df578", "first": 4, "second": 4},
    0x003DF588: {"symbol": "candidate_003df588", "first": 4, "second": 8},
    0x003DF598: {"symbol": "candidate_003df598", "first": 4, "second": 4},
}
REFERENCE_WORDS = {
    0x00141468: (0xE5900008, 0xE3500000, 0x15900000, 0xE12FFF1E),
    0x002344B4: (0xE5900004, 0xE3500000, 0x15900008, 0xE12FFF1E),
    0x003DF578: (0xE5900004, 0xE3500000, 0x15900004, 0xE12FFF1E),
    0x003DF588: (0xE5900004, 0xE3500000, 0x15900008, 0xE12FFF1E),
    0x003DF598: (0xE5900004, 0xE3500000, 0x15900004, 0xE12FFF1E),
}
NEGATIVES = {
    address: {
        "wrong_root": f"wrong_root_{address:08x}",
        "wrong_leaf": f"wrong_leaf_{address:08x}",
    }
    for address in FUNCTIONS
}


def verify_reference(image: bytes, expected_sha256: str) -> dict:
    actual_sha256 = hashlib.sha256(image).hexdigest()
    if not expected_sha256 or actual_sha256 != expected_sha256:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    result = {}
    for address, words in REFERENCE_WORDS.items():
        expected = struct.pack("<4I", *words)
        actual = image[address - TEXT:address - TEXT + len(expected)]
        if actual != expected:
            raise ValueError(f"Original pointer-chain bytes differ at {address:#010x}")
        result[hex(address)] = {
            "size": len(expected), "sha256": hashlib.sha256(actual).hexdigest(),
            "words": [f"0x{word:08x}" for word in words],
        }
    return {"sha256": actual_sha256, "functions": result}


def direct_callers(image: bytes) -> dict:
    """Record direct BL xrefs; indirect dispatch is outside this scan's claim."""
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    cs.detail = True
    targets = set(FUNCTIONS)
    refs = {address: [] for address in targets}
    for instruction in cs.disasm(image, TEXT):
        if instruction.mnemonic == "bl" and instruction.operands:
            target = instruction.operands[0].imm
            if target in refs:
                refs[target].append(instruction.address)
    return {hex(address): [hex(site) for site in sites]
            for address, sites in refs.items()}


def _write_word(data: bytearray, address: int, value: int) -> None:
    if address < DATA or address + 4 > DATA + DATA_SIZE or address % 4:
        raise ValueError(f"Test word is outside aligned mapped RAM: {address:#010x}")
    struct.pack_into("<I", data, address - DATA, value & U32_MASK)


def _make_case(address: int, label: str, seed: int, *, base: int,
               middle: int, middle_alt: int, leaf_value: int,
               leaf_alt_value: int, null_middle: bool = False,
               null_leaf: bool = False, write_alternate_root: bool = True,
               write_alternate_leaf: bool = True) -> Case:
    spec = FUNCTIONS[address]
    label_salt = sum((index + 1) * byte for index, byte in enumerate(label.encode()))
    rng = random.Random(seed ^ address ^ base ^ label_salt)
    data = bytearray(rng.randbytes(DATA_SIZE))
    root_slot = base + spec["first"]
    _write_word(data, root_slot, 0 if null_middle else middle)
    alt_root_offset = 4 if spec["first"] == 8 else 8
    if write_alternate_root and base + alt_root_offset + 4 <= DATA + DATA_SIZE:
        _write_word(data, base + alt_root_offset, middle_alt)

    leaf_slot = middle + spec["second"]
    _write_word(data, leaf_slot, 0 if null_leaf else leaf_value)
    alt_leaf_offset = 4 if spec["second"] != 4 else 8
    if write_alternate_leaf and middle + alt_leaf_offset + 4 <= DATA + DATA_SIZE:
        _write_word(data, middle + alt_leaf_offset, leaf_alt_value)
    # A wrong-root-offset control must still have a valid, distinguishable path.
    if middle_alt + spec["second"] + 4 <= DATA + DATA_SIZE:
        _write_word(data, middle_alt + spec["second"], leaf_alt_value)

    registers = [rng.getrandbits(32) for _ in range(13)]
    registers[0] = base
    return Case(label, tuple(registers), bytes(data), rng.randbytes(0x2000),
                rng.getrandbits(4) << 28)


def make_cases(address: int, seed: int = 20261024, samples: int = 64) -> list[Case]:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    spec = FUNCTIONS[address]
    base = DATA + 0x100
    middle = DATA + 0x300
    middle_alt = DATA + 0x400
    cases = [
        _make_case(address, "valid-chain", seed, base=base, middle=middle,
                   middle_alt=middle_alt, leaf_value=DATA + 0x600,
                   leaf_alt_value=DATA + 0x700),
        _make_case(address, "null-intermediate", seed + 1, base=base,
                   middle=middle, middle_alt=middle_alt, leaf_value=DATA + 0x600,
                   leaf_alt_value=DATA + 0x700, null_middle=True),
        _make_case(address, "null-leaf-result", seed + 2, base=base,
                   middle=middle, middle_alt=middle_alt, leaf_value=DATA + 0x600,
                   leaf_alt_value=DATA + 0x700, null_leaf=True),
        _make_case(address, "zero-leaf-value", seed + 3, base=base,
                   middle=middle, middle_alt=middle_alt, leaf_value=0,
                   leaf_alt_value=DATA + 0x700),
        _make_case(address, "high-bit-leaf-value", seed + 4, base=base,
                   middle=middle, middle_alt=middle_alt, leaf_value=0x80000000,
                   leaf_alt_value=DATA + 0x700),
    ]

    # Place each dereferenced word at the final aligned word in mapped DATA.
    root_edge_base = DATA + DATA_SIZE - 4 - spec["first"]
    cases.append(_make_case(
        address, "root-field-last-word", seed + 5, base=root_edge_base,
        middle=middle, middle_alt=middle_alt, leaf_value=DATA + 0x600,
        leaf_alt_value=DATA + 0x700, write_alternate_root=False,
    ))
    leaf_edge_middle = DATA + DATA_SIZE - 4 - spec["second"]
    cases.append(_make_case(
        address, "leaf-field-last-word", seed + 6, base=base,
        middle=leaf_edge_middle, middle_alt=middle_alt,
        leaf_value=0xFFFFFFFF, leaf_alt_value=DATA + 0x700,
        write_alternate_leaf=False,
    ))

    rng = random.Random(seed ^ address)
    for index in range(samples):
        base = DATA + rng.choice((0x100, 0x180, 0x280, 0x500))
        middle = DATA + rng.choice((0x300, 0x380, 0x480, 0x700))
        middle_alt = DATA + rng.choice((0x800, 0x880, 0x980, 0xA00))
        cases.append(_make_case(
            address, f"random-{index}", seed + index + 7, base=base,
            middle=middle, middle_alt=middle_alt,
            leaf_value=rng.choice((0, 1, 0x7FFFFFFF, 0x80000000,
                                   0xFFFFFFFF, DATA + 0x600,
                                   rng.getrandbits(32))),
            leaf_alt_value=DATA + 0x700 + (index % 16) * 4,
        ))
    return cases


def expected_reads(address: int, case: Case) -> frozenset[int]:
    spec = FUNCTIONS[address]
    base = case.registers[0]
    first_slot = base + spec["first"]
    middle = struct.unpack_from("<I", case.data, first_slot - DATA)[0]
    result = set(range(first_slot, first_slot + 4))
    if middle:
        second_slot = middle + spec["second"]
        if not DATA <= second_slot <= DATA + DATA_SIZE - 4:
            raise ValueError("Generated non-null pointer is not backed by mapped RAM")
        result.update(range(second_slot, second_slot + 4))
    return frozenset(result)


def _compile_candidates(output: Path) -> dict[str, bytes]:
    source = ROOT / "experiments/semantic_equivalence/null_chain_candidates.cpp"
    object_path = output / "null_chain_candidates.o"
    build = compile_tu_armv6k(source, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    functions = extract_elf_functions_detailed(object_path)
    required = [item["symbol"] for item in FUNCTIONS.values()]
    required += [symbol for pair in NEGATIVES.values() for symbol in pair.values()]
    compiled = {}
    for symbol in required:
        if symbol not in functions:
            raise ValueError(f"Missing candidate function: {symbol}")
        code, relocations = functions[symbol]
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        validate_leaf(code)
        compiled[symbol] = code
    return compiled


def run(code_path: Path, output: Path, seed: int = 20261024,
        samples: int = 64) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    reference = verify_reference(image, game["code_sha256"])
    source = ROOT / "experiments/semantic_equivalence/null_chain_candidates.cpp"
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    compiled = _compile_candidates(output)
    results = []
    controls = []

    for address, spec in FUNCTIONS.items():
        oracle = Runner(image, address)
        rebuilt = Runner(image, address, compiled[spec["symbol"]])
        function_cases = make_cases(address, seed, samples)
        compared = []
        for case in function_cases:
            original = oracle.run(case)
            candidate = rebuilt.run(case)
            reason = difference(original, candidate)
            footprint = expected_reads(address, case)
            if reason is None and (original.reads != footprint or original.writes):
                reason = "reference footprint differs from the two-level contract"
            compared.append({"case": case.label, "passed": reason is None,
                             "reason": reason,
                             "reads": sorted(hex(value) for value in original.reads),
                             "writes": sorted(hex(value) for value in original.writes)})
        results.append({
            "address": hex(address), "candidate": spec["symbol"],
            "reference_bytes": 16, "candidate_bytes": len(compiled[spec["symbol"]]),
            "byte_identical": image[address - TEXT:address - TEXT + 16]
            == compiled[spec["symbol"]], "passed": all(item["passed"] for item in compared),
            "case_count": len(compared), "cases": compared,
            "first_offset": spec["first"], "second_offset": spec["second"],
        })

        # Fixed, deliberately distinguishable paths make each changed offset fail.
        control_case = function_cases[0]
        for label, symbol in NEGATIVES[address].items():
            wrong = Runner(image, address, compiled[symbol])
            reason = difference(oracle.run(control_case), wrong.run(control_case))
            controls.append({"address": hex(address), "control": label,
                             "case": control_case.label,
                             "detected": reason is not None,
                             "reason": reason})

    # Null at the base is not a successful nullable input: the original first LDR
    # dereferences it. Confirm both implementations fault instead of claiming a
    # fabricated null-safe contract for the root pointer.
    null_root = {}
    for address, spec in FUNCTIONS.items():
        registers = [0] + [0xA5A5A5A5] * 12
        case = Case("null-base-expected-fault", tuple(registers), bytes(DATA_SIZE),
                    bytes(0x2000), 0)
        original = Runner(image, address).run(case)
        candidate = Runner(image, address, compiled[spec["symbol"]]).run(case)
        null_root[hex(address)] = {
            "both_faulted": bool(original.fault and candidate.fault),
            "original_fault": original.fault, "candidate_fault": candidate.fault,
        }

    if hashlib.sha256(source.read_bytes()).hexdigest() != source_digest:
        raise RuntimeError("Candidate source changed during the experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True)
    caller_refs = direct_callers(image)
    report = {
        "schema": 1,
        "passed": all(result["passed"] for result in results)
        and all(item["detected"] for item in controls)
        and all(item["both_faulted"] for item in null_root.values()),
        "scope": "isolated semantic differential only; no production, docs, IPS, or emulator changes",
        "reference": reference,
        "source_sha256": source_digest,
        "object_sha256": hashlib.sha256(
            (output / "null_chain_candidates.o").read_bytes()).hexdigest(),
        "compiler": compiler.stdout.splitlines()[0],
        "seed": seed, "random_samples_per_function": samples,
        "candidate_functions": results, "negative_controls": controls,
        "null_base_behavior": null_root,
        "caller_window": {
            "added": False, "direct_bl_references": caller_refs,
            "reason": "No direct BL xrefs to these five entries were found; likely indirect dispatch. Caller-window setup was not inferred.",
        },
        "contract": {
            "semantics": "Read a 32-bit word at base+first offset; if nonzero read one word at middle+second offset; return that word, including zero.",
            "null_policy": "Only the intermediate link is checked. The base itself must be a valid readable pointer; both variants fault for a null base. A zero second-load result is returned as zero.",
            "memory": "At most two aligned 4-byte reads, no writes; the second read occurs only when the first link is nonzero.",
        },
        "limitations": [
            "Tests use aligned ordinary mapped RAM and do not claim MMIO, volatile device, concurrent mutation, or unaligned behavior.",
            "No direct caller windows were possible from statically found BL references; indirect callers remain unanalyzed.",
            "Random and boundary differential cases are bounded evidence, not a formal proof.",
            "These are experimental C++ candidates; production bodies and exact-match ledger are unchanged.",
        ],
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Null-chain experiment {'PASS' if report['passed'] else 'FAIL'}; report: {report_path}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/null-chain/seed-20261024")
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
