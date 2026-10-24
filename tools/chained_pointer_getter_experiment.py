#!/usr/bin/env python3
"""Differentially test three isolated chained-pointer getter candidates."""
from __future__ import annotations

import argparse
import capstone
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

from tools.semantic_experiment import DATA, DATA_SIZE, TEXT, Case, Runner, difference
from tools.semantic_experiment_support import (
    compile_candidate_symbols,
    load_pinned_reference,
)

U32_MASK = 0xFFFFFFFF
FUNCTIONS = {
    0x00207B78: {"symbol": "candidate_00207b78", "root": 0x4C},
    0x002DF440: {"symbol": "candidate_002df440", "root": 0x30},
    0x002F300C: {"symbol": "candidate_002f300c", "root": 0x9C},
}
PINNED_BYTES = {
    0x00207B78: "4c0090e5240090e5201090e5000051e3b80090150000a003010080101eff2fe1",
    0x002DF440: "300090e5240090e5201090e5000051e3b80090150000a003010080101eff2fe1",
    0x002F300C: "9c0090e5240090e5201090e5000051e3b80090150000a003010080101eff2fe1",
}
NEGATIVES = {
    address: {
        "wrong_root": f"wrong_root_{address:08x}",
        "wrong_middle": f"wrong_middle_{address:08x}",
        "wrong_value": f"wrong_value_{address:08x}",
        "wrong_sum": f"wrong_sum_{address:08x}",
        "unconditional_branch": f"unconditional_{address:08x}",
    }
    for address in FUNCTIONS
}


def verify_reference(image: bytes, game_info: dict, ledger: list[dict]) -> dict:
    """Pin image identity, per-function ledger rows, and exact original bytes."""
    actual_hash = hashlib.sha256(image).hexdigest()
    if len(image) != int(game_info["code_bin_size"]):
        raise ValueError("code.bin size differs from configured image")
    if actual_hash != game_info["code_sha256"].lower():
        raise ValueError("code.bin SHA-256 differs from configured revision")
    rows = {int(row["address"], 16): row for row in ledger}
    details = {}
    for address, expected_hex in PINNED_BYTES.items():
        expected = bytes.fromhex(expected_hex)
        offset = address - TEXT
        actual = image[offset:offset + len(expected)]
        if actual != expected:
            raise ValueError(f"original bytes differ at {address:#010x}")
        row = rows.get(address)
        if row is None or int(row["size"]) != len(expected) or row["status"] != "matching":
            raise ValueError(f"function ledger does not pin {address:#010x} as matching/32B")
        details[hex(address)] = {
            "ledger": row,
            "size": len(actual),
            "sha256": hashlib.sha256(actual).hexdigest(),
            "bytes_hex": actual.hex(),
        }
    return {"code_sha256": actual_hash, "functions": details}


def direct_callers(image: bytes) -> dict[str, list[str]]:
    """Collect only ARM BL encodings; this is not a complete callgraph."""
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    cs.detail = True
    by_target = {address: [] for address in FUNCTIONS}
    for insn in cs.disasm(image, TEXT):
        if insn.id == capstone.arm.ARM_INS_BL and insn.operands:
            operand = insn.operands[0]
            if operand.type == capstone.arm.ARM_OP_IMM and operand.imm in by_target:
                by_target[operand.imm].append(insn.address)
    return {hex(address): [hex(site) for site in sites]
            for address, sites in by_target.items()}


def _write_word(data: bytearray, address: int, value: int) -> None:
    if address < DATA or address + 4 > DATA + DATA_SIZE or address % 4:
        raise ValueError(f"test word outside aligned mapped RAM: {address:#010x}")
    struct.pack_into("<I", data, address - DATA, value & U32_MASK)


def _case(address: int, label: str, seed: int, *, value: int,
          total: int = 0x12345678, wrong_root_path: bool = True,
          root_base: int | None = None, first: int | None = None,
          second: int | None = None, set_root: bool = True,
          set_middle: bool = True, set_value: bool = True,
          set_total: bool = True, null_first_link: bool = False,
          null_second_link: bool = False) -> Case:
    spec = FUNCTIONS[address]
    root_base = DATA + 0x100 if root_base is None else root_base
    first = DATA + 0x300 if first is None else first
    second = DATA + 0x500 if second is None else second
    alt_first = DATA + 0x700
    alt_second = DATA + 0x900
    data = bytearray(random.Random(seed ^ address).randbytes(DATA_SIZE))

    if set_root:
        _write_word(data, root_base + spec["root"],
                    0 if null_first_link else first)
        if wrong_root_path and root_base + spec["root"] + 4 + 4 <= DATA + DATA_SIZE:
            _write_word(data, root_base + spec["root"] + 4, alt_first)
    if set_middle:
        _write_word(data, first + 0x24,
                    0 if null_second_link else second)
        if first + 0x28 + 4 <= DATA + DATA_SIZE:
            _write_word(data, first + 0x28, alt_second)
    if set_value:
        _write_word(data, second + 0x20, value)
        # Distinguish the shifted value load from the true final word.
        if second + 0x24 + 4 <= DATA + DATA_SIZE:
            _write_word(data, second + 0x24, 0x2468ACE1)
    if set_total:
        _write_word(data, second + 0xB8, total)
        if second + 0xBC + 4 <= DATA + DATA_SIZE:
            _write_word(data, second + 0xBC, 0x13579BDF)

    # Populate the deliberately wrong root path with a distinct valid result.
    if wrong_root_path and root_base + spec["root"] + 4 + 4 <= DATA + DATA_SIZE:
        _write_word(data, alt_first + 0x24, alt_second)
        _write_word(data, alt_first + 0x28, second)
        _write_word(data, alt_second + 0x20, 0x10203040)
        _write_word(data, alt_second + 0xB8, 0x50607080)

    rng = random.Random(seed + address + sum(label.encode()))
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0] = root_base
    return Case(label, tuple(regs), bytes(data), rng.randbytes(0x2000),
                rng.getrandbits(4) << 28)


def make_cases(address: int, seed: int = 20261024, samples: int = 64) -> list[Case]:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    spec = FUNCTIONS[address]
    cases = [
        _case(address, "zero-terminal-word", seed, value=0, total=0xA1B2C3D4),
        _case(address, "nonzero-terminal-word", seed + 1, value=0x10293847,
              total=0x76543210),
        _case(address, "high-bit-terminal-word", seed + 2, value=0x80000001,
              total=0xFFFFFFFF),
        _case(address, "null-first-link-fault", seed + 3, value=0x10293847,
              null_first_link=True),
        _case(address, "null-second-link-fault", seed + 4, value=0x10293847,
              null_second_link=True),
    ]

    # Each individual dereferenced field is placed at the last aligned word in
    # mapped RAM, while all subsequent links remain ordinary valid RAM.
    cases.append(_case(
        address, "root-slot-last-word", seed + 5, value=0,
        root_base=DATA + DATA_SIZE - 4 - spec["root"], wrong_root_path=False,
    ))
    cases.append(_case(
        address, "middle-slot-last-word", seed + 6, value=0,
        first=DATA + DATA_SIZE - 4 - 0x24,
    ))
    cases.append(_case(
        address, "terminal-slot-last-word", seed + 7, value=0,
        second=DATA + DATA_SIZE - 4 - 0x20,
        set_total=False,
    ))
    cases.append(_case(
        address, "sum-slot-last-word", seed + 8, value=0x01020304,
        second=DATA + DATA_SIZE - 4 - 0xB8,
    ))

    rng = random.Random(seed ^ address)
    for index in range(samples):
        value = rng.choice((0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF,
                            rng.getrandbits(32)))
        cases.append(_case(address, f"random-{index}", seed + index + 9,
                           value=value, total=rng.getrandbits(32)))
    return cases


def expected_reads(address: int, case: Case) -> frozenset[int]:
    """Expected byte-level read set for normal, fully mapped paths."""
    base = case.registers[0]
    data = case.data
    root = base + FUNCTIONS[address]["root"]
    first = struct.unpack_from("<I", data, root - DATA)[0]
    middle_slot = first + 0x24
    second = struct.unpack_from("<I", data, middle_slot - DATA)[0]
    value_slot = second + 0x20
    value = struct.unpack_from("<I", data, value_slot - DATA)[0]
    reads = set(range(root, root + 4)) | set(range(middle_slot, middle_slot + 4))
    reads.update(range(value_slot, value_slot + 4))
    if value:
        total_slot = second + 0xB8
        reads.update(range(total_slot, total_slot + 4))
    return frozenset(reads)


def _compile(source: Path, object_path: Path) -> dict[str, bytes]:
    required = [spec["symbol"] for spec in FUNCTIONS.values()]
    required.extend(symbol for controls in NEGATIVES.values()
                    for symbol in controls.values())
    return compile_candidate_symbols(source, object_path, ROOT, required)


def _fault_observation(result) -> dict:
    return {
        "faulted": result.fault is not None,
        "fault": result.fault,
        "stopped": result.stopped,
        "reads": sorted(hex(value) for value in result.reads),
        "writes": sorted(hex(value) for value in result.writes),
        "data_unchanged": not any(result.writes),
    }


def run(code_path: Path, output: Path, seed: int = 20261024,
        samples: int = 64) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(
        code_path, ROOT / "config/game_info.json", ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.game_info, pinned.ledger)
    source = ROOT / "experiments/semantic_equivalence/chained_pointer_getter_candidates.cpp"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    object_path = output / "chained_pointer_getter_candidates.o"
    compiled = _compile(source, object_path)
    functions = []
    negative_controls = []
    fault_cases = []

    for address, spec in FUNCTIONS.items():
        oracle = Runner(pinned.image, address)
        rebuilt = Runner(pinned.image, address, compiled[spec["symbol"]])
        comparisons = []
        generated = make_cases(address, seed, samples)
        for case in generated:
            original = oracle.run(case)
            candidate = rebuilt.run(case)
            if original.fault or candidate.fault:
                # Fault cases are checked as a separate relation: both fault at
                # the same stage after the same observed RAM reads, with no writes.
                expected_visible_reads = set()
                if case.label == "null-first-link-fault":
                    root = case.registers[0] + spec["root"]
                    expected_visible_reads.update(range(root, root + 4))
                if case.label == "null-second-link-fault":
                    root = case.registers[0] + spec["root"]
                    expected_visible_reads.update(range(root, root + 4))
                    expected_visible_reads.update(range(DATA + 0x300 + 0x24,
                                                        DATA + 0x300 + 0x28))
                same_fault_behavior = (
                    original.fault is not None and candidate.fault is not None
                    and original.reads == candidate.reads
                    and original.writes == candidate.writes == frozenset()
                    and original.data == candidate.data
                    and original.preserved == candidate.preserved
                    and original.fault == candidate.fault
                    and original.reads == frozenset(expected_visible_reads)
                )
                fault_cases.append({
                    "address": hex(address), "case": case.label,
                    "passed": same_fault_behavior,
                    "original": _fault_observation(original),
                    "candidate": _fault_observation(candidate),
                    "expected_ram_reads": sorted(hex(value)
                                                  for value in expected_visible_reads),
                })
                comparisons.append({"case": case.label, "passed": same_fault_behavior,
                                    "reason": None if same_fault_behavior else
                                    "fault behavior/read stage differs"})
                continue

            reason = difference(original, candidate)
            expected = expected_reads(address, case)
            if reason is None and (original.reads != expected or original.writes):
                reason = "reference access footprint differs from pinned load contract"
            comparisons.append({
                "case": case.label, "passed": reason is None, "reason": reason,
                "result": hex(original.result),
                "reads": sorted(hex(value) for value in original.reads),
                "writes": sorted(hex(value) for value in original.writes),
            })

        original_bytes = bytes.fromhex(PINNED_BYTES[address])
        functions.append({
            "address": hex(address), "symbol": spec["symbol"],
            "original_size": len(original_bytes),
            "candidate_size": len(compiled[spec["symbol"]]),
            "byte_identical": original_bytes == compiled[spec["symbol"]],
            "case_count": len(comparisons),
            "passed_count": sum(item["passed"] for item in comparisons),
            "passed": all(item["passed"] for item in comparisons),
            "root_offset": spec["root"], "middle_offset": 0x24,
            "terminal_value_offset": 0x20, "conditional_sum_offset": 0xB8,
            "cases": comparisons,
        })

        # Four offset controls are exercised on nonzero paths, where returned
        # values and the access footprint distinguish each substituted field.
        nonzero_case = next(item for item in generated
                            if item.label == "nonzero-terminal-word")
        reference_result = oracle.run(nonzero_case)
        for label, symbol in list(NEGATIVES[address].items())[:4]:
            control = Runner(pinned.image, address, compiled[symbol])
            candidate_result = control.run(nonzero_case)
            reason = difference(reference_result, candidate_result)
            negative_controls.append({"address": hex(address), "control": label,
                                      "case": nonzero_case.label,
                                      "detected": reason is not None, "reason": reason})

        # The wrong branch must be caught specifically on the zero-terminal path.
        zero_case = next(item for item in generated if item.label == "zero-terminal-word")
        wrong_branch = Runner(pinned.image, address,
                             compiled[NEGATIVES[address]["unconditional_branch"]])
        branch_result = wrong_branch.run(zero_case)
        reason = difference(oracle.run(zero_case), branch_result)
        negative_controls.append({"address": hex(address),
                                  "control": "unconditional_branch",
                                  "case": zero_case.label,
                                  "detected": reason is not None, "reason": reason})

    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("candidate source changed during the experiment")
    compiler = subprocess.run([str(__import__("tools.build_check", fromlist=["find_clang"])
                                .find_clang()), "--version"],
                              capture_output=True, text=True, check=True)
    callers = direct_callers(pinned.image)
    passed = (all(item["passed"] for item in functions)
              and all(item["passed"] for item in fault_cases)
              and len(negative_controls) == 15
              and all(item["detected"] for item in negative_controls))
    report = {
        "schema": 1,
        "passed": passed,
        "scope": "isolated semantic experiment only; no production, ledger, docs, IPS, or emulator changes",
        "reference": reference,
        "source_sha256": source_hash,
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler": compiler.stdout.splitlines()[0],
        "seed": seed,
        "random_samples_per_function": samples,
        "function_comparison_count": sum(item["case_count"] for item in functions),
        "fault_case_count": len(fault_cases),
        "negative_control_count": len(negative_controls),
        "candidate_functions": functions,
        "fault_cases": fault_cases,
        "negative_controls": negative_controls,
        "caller_evidence": {
            "method": "linear Capstone ARM direct-BL scan over pinned code image",
            "direct_bl_references": callers,
            "caller_windows_added": False,
            "reason": "No direct ARM BL references found; no caller window is inferred from the incomplete scan.",
            "limitations": "Thumb BL, indirect calls, data/code misclassification, and runtime dispatch are not covered.",
        },
        "contract_observed": {
            "loads": "base+root, first+0x24, second+0x20 unconditionally; if the third loaded word is nonzero, also load second+0xb8",
            "result": "zero when second+0x20 is zero; otherwise uint32 addition of that word and second+0xb8",
            "earlier_null_links": "not checked; test confirms they fault in the harness before returning",
            "writes": "none in tested ordinary mapped RAM",
        },
        "limitations": [
            "Differential evidence is bounded to aligned ordinary RAM in the ARM emulator harness; it is not a formal proof.",
            "Fault parity for zero intermediate pointers was observed only in the harness's unmapped low address region.",
            "No caller windows were added because the available ARM BL scan found no direct references; indirect/Thumb callers remain unknown.",
            "MMIO, concurrent mutation, unusual alignment, and architectural data-abort details beyond the harness are not established.",
            "Experimental candidates are not integrated into production or the byte-exact ledger.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                         encoding="utf-8")
    print(f"Chained pointer getter experiment {'PASS' if passed else 'FAIL'}; report: {output / 'report.json'}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/chained-pointer-getters-seed20261024")
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
