#!/usr/bin/env python3
"""Differential experiment for two tagged relative-payload getters.

The code image is hash-pinned and read-only. Candidate builds and JSON reports
are written only below the caller-selected ignored build/ output directory.
"""
from __future__ import annotations

import argparse
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
from tools.semantic_experiment import DATA, DATA_SIZE, TEXT, Case, Runner, difference
from tools.semantic_experiment_support import (
    compile_candidate_symbols,
    load_pinned_reference,
)

U32_MASK = 0xFFFFFFFF
FUNCTIONS = {
    0x003E6974: {
        "symbol": "candidate_003e6974",
        "tag": 0x0300,
        "bytes": "b010d0e1030c51e304109005010080000000a0131eff2fe1",
        "caller_site": 0x003E71E4,
        "caller": 0x003E71C4,
    },
    0x003E69A8: {
        "symbol": "candidate_003e69a8",
        "tag": 0x4100,
        "bytes": "b010d0e1410c51e3041090050000a013010080001eff2fe1",
        "caller_site": 0x003E7104,
        "caller": 0x003E70F8,
    },
}
NEGATIVES = {
    address: {
        "wrong_tag": f"wrong_tag_{address:08x}",
        "wrong_offset": f"wrong_offset_{address:08x}",
    }
    for address in FUNCTIONS
}


def _disassemble(image: bytes, address: int, size: int):
    raw = image[address - TEXT:address - TEXT + size]
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    return list(decoder.disasm(raw, address))


def verify_reference(image: bytes, game_info: dict, ledger: list[dict]) -> dict:
    """Fail closed on image identity, exact function bytes, and matching rows."""
    if len(image) != int(game_info["code_bin_size"]):
        raise ValueError("code.bin size differs from configured image")
    digest = hashlib.sha256(image).hexdigest()
    if digest != game_info["code_sha256"].lower():
        raise ValueError("code.bin SHA-256 differs from configured revision")
    rows = {int(row["address"], 16): row for row in ledger}
    details = {}
    for address, spec in FUNCTIONS.items():
        expected = bytes.fromhex(spec["bytes"])
        actual = image[address - TEXT:address - TEXT + len(expected)]
        if actual != expected:
            raise ValueError(f"original bytes differ at {address:#010x}")
        row = rows.get(address)
        if (row is None or int(row["size"]) != len(expected)
                or row["status"] != "matching"):
            raise ValueError(f"function ledger does not pin {address:#010x} as matching/24B")
        instructions = _disassemble(image, address, len(expected))
        if sum(instruction.size for instruction in instructions) != len(expected):
            raise ValueError(f"incomplete disassembly at {address:#010x}")
        details[hex(address)] = {
            "tag": hex(spec["tag"]),
            "size": len(expected),
            "bytes_hex": actual.hex(),
            "sha256": hashlib.sha256(actual).hexdigest(),
            "ledger_name": row["name"],
            "category": row["category"],
            "instructions": [
                f"{insn.mnemonic.lower()} {insn.op_str.lower()}".strip()
                for insn in instructions
            ],
        }

    caller_sites = {}
    for address, spec in FUNCTIONS.items():
        site = spec["caller_site"]
        instructions = _disassemble(image, site, 4)
        if (len(instructions) != 1 or instructions[0].mnemonic.lower() != "bl"
                or int(instructions[0].op_str.replace("#", ""), 16) != address):
            raise ValueError(f"direct caller BL drift at {site:#010x}")
        caller_sites[hex(address)] = {
            "caller": hex(spec["caller"]),
            "callsite": hex(site),
            "instruction": f"{instructions[0].mnemonic} {instructions[0].op_str}",
            "bytes_hex": instructions[0].bytes.hex(),
            "scope": "static direct-BL evidence only; caller setup/whole path not executed",
        }
    return {
        "code_sha256": digest,
        "functions": details,
        "callers": caller_sites,
    }


def _write_case_word(data: bytearray, address: int, value: int, width: int) -> None:
    if address < DATA or address + width > DATA + DATA_SIZE:
        raise ValueError(f"test field outside mapped RAM: {address:#010x}")
    if width == 2:
        struct.pack_into("<H", data, address - DATA, value & 0xFFFF)
    elif width == 4:
        struct.pack_into("<I", data, address - DATA, value & U32_MASK)
    else:
        raise ValueError("unsupported test field width")


def _make_case(address: int, label: str, seed: int, *, tag: int,
               offset: int, alternate_offset: int) -> Case:
    spec = FUNCTIONS[address]
    base = DATA + 0x100
    rng = random.Random(seed ^ address ^ sum(label.encode("utf-8")))
    memory = bytearray(rng.randbytes(DATA_SIZE))
    _write_case_word(memory, base, tag, 2)
    _write_case_word(memory, base + 4, offset, 4)
    _write_case_word(memory, base + 8, alternate_offset, 4)
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0] = base
    return Case(label, tuple(regs), bytes(memory), rng.randbytes(0x2000),
                rng.getrandbits(4) << 28)


def make_cases(address: int, seed: int = 20261024,
               samples: int = 64) -> list[Case]:
    if address not in FUNCTIONS:
        raise ValueError(f"unknown getter address {address:#010x}")
    if samples < 0:
        raise ValueError("samples must be non-negative")
    tag = FUNCTIONS[address]["tag"]
    cases = [
        _make_case(address, "valid-offset-zero", seed, tag=tag,
                   offset=0, alternate_offset=0x87654321),
        _make_case(address, "valid-offset-one", seed + 1, tag=tag,
                   offset=1, alternate_offset=0x87654321),
        _make_case(address, "valid-offset-four", seed + 2, tag=tag,
                   offset=4, alternate_offset=0x87654321),
        _make_case(address, "valid-offset-high-bit", seed + 3, tag=tag,
                   offset=0x80000000, alternate_offset=0x12345678),
        _make_case(address, "valid-offset-wrap", seed + 4, tag=tag,
                   offset=U32_MASK, alternate_offset=0x12345678),
        _make_case(address, "wrong-tag-zero", seed + 5, tag=0,
                   offset=0x11223344, alternate_offset=0x55667788),
        _make_case(address, "wrong-tag-adjacent", seed + 6,
                   tag=(tag + 1) & 0xFFFF, offset=0x11223344,
                   alternate_offset=0x55667788),
        _make_case(address, "wrong-tag-all-ones", seed + 7, tag=0xFFFF,
                   offset=0x11223344, alternate_offset=0x55667788),
    ]
    rng = random.Random(seed ^ address)
    for index in range(samples):
        current_tag = tag if index % 2 == 0 else rng.choice((0, tag ^ 1, 0xFFFF))
        cases.append(_make_case(
            address, f"random-{index}", seed + index + 8,
            tag=current_tag,
            offset=rng.getrandbits(32),
            alternate_offset=rng.getrandbits(32),
        ))
    return cases


def _fault_relation(original, candidate) -> dict:
    """Report harness-observed null-base faults without calling them a value."""
    passed = (
        original.fault is not None and candidate.fault is not None
        and original.fault == candidate.fault
        and original.reads == candidate.reads == frozenset()
        and original.writes == candidate.writes == frozenset()
    )
    return {
        "passed": passed,
        "original_fault": original.fault,
        "candidate_fault": candidate.fault,
        "original_reads": sorted(hex(value) for value in original.reads),
        "candidate_reads": sorted(hex(value) for value in candidate.reads),
        "scope": "Unicorn unmapped-null observation only; not a target OS/data-abort proof",
    }


def run(code_path: Path, output: Path, seed: int = 20261024,
        samples: int = 64) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(
        code_path, ROOT / "config/game_info.json", ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.game_info, pinned.ledger)
    source = ROOT / "experiments/semantic_equivalence/tagged_payload_getter_candidates.cpp"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    symbols = [spec["symbol"] for spec in FUNCTIONS.values()]
    symbols.extend(symbol for spec in NEGATIVES.values() for symbol in spec.values())
    compiled = compile_candidate_symbols(
        source, output / "tagged_payload_getter_candidates.o", ROOT, symbols)

    functions = []
    negative_controls = []
    null_faults = []
    for address, spec in FUNCTIONS.items():
        oracle = Runner(pinned.image, address)
        candidate = Runner(pinned.image, address, compiled[spec["symbol"]])
        comparisons = []
        generated = make_cases(address, seed, samples)
        for case in generated:
            original_result = oracle.run(case)
            candidate_result = candidate.run(case)
            reason = difference(original_result, candidate_result)
            base = case.registers[0]
            tag = struct.unpack_from("<H", case.data, base - DATA)[0]
            expected_reads = set(range(base, base + 2))
            if tag == spec["tag"]:
                expected_reads.update(range(base + 4, base + 8))
            if (reason is None and
                    (original_result.reads != frozenset(expected_reads)
                     or original_result.writes)):
                reason = "reference memory footprint differs from conditional tagged-offset contract"
            comparisons.append({
                "case": case.label,
                "tag": hex(tag),
                "offset": hex(struct.unpack_from("<I", case.data, base - DATA + 4)[0]),
                "passed": reason is None,
                "reason": reason,
                "result": hex(original_result.result),
                "reads": sorted(hex(value) for value in original_result.reads),
            })

        functions.append({
            "address": hex(address),
            "symbol": spec["symbol"],
            "tag": hex(spec["tag"]),
            "original_bytes": 24,
            "candidate_bytes": len(compiled[spec["symbol"]]),
            "byte_identical": bytes.fromhex(spec["bytes"]) == compiled[spec["symbol"]],
            "case_count": len(comparisons),
            "passed_count": sum(item["passed"] for item in comparisons),
            "passed": all(item["passed"] for item in comparisons),
            "cases": comparisons,
        })

        valid_case = next(item for item in generated
                          if item.label == "valid-offset-four")
        baseline = oracle.run(valid_case)
        for label, symbol in NEGATIVES[address].items():
            control = Runner(pinned.image, address, compiled[symbol])
            observed = control.run(valid_case)
            reason = difference(baseline, observed)
            negative_controls.append({
                "address": hex(address), "control": label,
                "case": valid_case.label,
                "detected": reason is not None, "reason": reason,
            })

        # Input NULL is outside the valid contract, but retain a fail-closed
        # observation that both implementations fault rather than inventing a
        # nullptr return. The tag load should be the first observable operation.
        rng = random.Random(seed ^ address ^ 0x4E554C4C)
        null_regs = [rng.getrandbits(32) for _ in range(13)]
        null_regs[0] = 0
        null_case = Case("null-base-precondition-violation", tuple(null_regs),
                         bytes(DATA_SIZE), rng.randbytes(0x2000),
                         rng.getrandbits(4) << 28)
        null_faults.append({
            "address": hex(address),
            **_fault_relation(oracle.run(null_case), candidate.run(null_case)),
        })

    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("candidate source changed during the experiment")
    compiler = subprocess.run([str(find_clang()), "--version"],
                              capture_output=True, text=True, check=True)
    passed = (
        all(item["passed"] for item in functions)
        and len(negative_controls) == 4
        and all(item["detected"] for item in negative_controls)
        and all(item["passed"] for item in null_faults)
    )
    report = {
        "schema": 1,
        "passed": passed,
        "scope": "isolated differential experiment only; no production or ledger integration",
        "reference": reference,
        "source_sha256": source_hash,
        "object_sha256": hashlib.sha256(
            (output / "tagged_payload_getter_candidates.o").read_bytes()).hexdigest(),
        "compiler": compiler.stdout.splitlines()[0],
        "seed": seed,
        "random_samples_per_function": samples,
        "function_comparison_count": sum(item["case_count"] for item in functions),
        "negative_control_count": len(negative_controls),
        "null_fault_count": len(null_faults),
        "candidate_functions": functions,
        "negative_controls": negative_controls,
        "null_faults": null_faults,
        "observed_contract": {
            "valid_base_precondition": "base points to at least 8 readable bytes; null is outside the valid contract",
            "tag_load": "read u16 at base+0 unconditionally",
            "wrong_tag": "return null without reading the offset field",
            "valid_tag": "read u32 at base+4 and return 32-bit base+offset; offset zero returns base",
            "writes": "none in tested ordinary mapped RAM",
        },
        "limitations": [
            "Evidence is bounded to the pinned code image, tested ARM emulation cases, and ordinary mapped RAM; it is not a formal proof.",
            "Null-base probes are precondition-violation fault observations in Unicorn, not a portable C++ contract or a target OS/data-abort guarantee.",
            "Direct BL sites are pinned as static evidence only; caller setup, caller execution, indirect dispatch, and whole-game behavior are not covered.",
            "MMIO, concurrent mutation, unusual alignment, and production integration are not established.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                         encoding="utf-8")
    print(f"Tagged payload getter experiment {'PASS' if passed else 'FAIL'}; report: {output / 'report.json'}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/tagged-payload-getters")
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
