#!/usr/bin/env python3
"""Differential-test a repeated table-callback family in isolated RAM.

The candidates and all reports stay outside production paths. This checks the
machine-level record writes for aligned, non-aliasing ordinary RAM only; it is
not a proof of caller-level behavior or a game/emulator integration test.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
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

BYTE_CALLBACKS = {
    0x0035B6FC: (0x11, 4),
    0x0035B728: (0x11, 3),
    0x0035B754: (8, 1),
    0x0035B814: (8, 2),
    0x0035B840: (8, 3),
    0x0035B86C: (0x11, 6),
    0x0035B8C4: (0x11, 2),
    0x0035B95C: (7, 1),
    0x0035BACC: (7, 2),
    0x0035BB48: (7, 3),
    0x0035BB98: (0x11, 5),
}
HALFWORD_CALLBACKS = {
    0x0035B898: 7,
    0x0035B988: 0x1B,
    0x0035B9B4: 0xC,
    0x0035B9E0: 0xA,
    0x0035BAA0: 0xD,
    0x0035BAF8: 9,
}
ALL_ADDRESSES = tuple(sorted((*BYTE_CALLBACKS, *HALFWORD_CALLBACKS)))
TABLE_START = 0x00473080
TABLE_END = 0x00473250
U32_MASK = 0xFFFFFFFF


@dataclass(frozen=True)
class FunctionSpec:
    address: int
    width: str
    type_value: int
    field_value: int

    @property
    def candidate_symbol(self):
        return f"candidate_{self.address:08x}"


def _arm_imm(value: int) -> str:
    return f"#{value}" if value < 10 else f"#0x{value:x}"


def expected_instructions(spec: FunctionSpec):
    value = _arm_imm(spec.field_value)
    type_value = _arm_imm(spec.type_value)
    field_store = "strb" if spec.width == "byte" else "strh"
    return (
        ("ldr", "ip, [r1]"),
        ("mov", f"r3, {type_value}"),
        ("mov", f"r2, {value}"),
        ("strb", "r3, [ip, #8]"),
        ("ldr", "r1, [r1]"),
        (field_store, f"r2, [r1, #0xa]"),
        ("ldr", "r1, [r0, #0x10]"),
        ("add", "r1, r1, #1"),
        ("str", "r1, [r0, #0x10]"),
        ("mov", "r0, r3" if spec.width == "halfword" else "r0, #0"),
        ("bx", "lr"),
    )


def verify_reference(image: bytes, configured_hash: str, rows: list[dict]) -> list[FunctionSpec]:
    digest = hashlib.sha256(image).hexdigest()
    if digest != configured_hash:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    by_address = {int(row["address"], 16): row for row in rows}
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    specs = []
    for address in ALL_ADDRESSES:
        row = by_address.get(address)
        if row is None or row["status"].strip() != "matching":
            raise ValueError(f"Missing matching ledger row for {address:#010x}")
        if int(row["size"]) != 44:
            raise ValueError(f"Unexpected size for {address:#010x}")
        if address in BYTE_CALLBACKS:
            type_value, field_value = BYTE_CALLBACKS[address]
            spec = FunctionSpec(address, "byte", type_value, field_value)
        else:
            spec = FunctionSpec(address, "halfword", 0, HALFWORD_CALLBACKS[address])
        offset = address - TEXT
        insns = list(cs.disasm(image[offset:offset + 44], address))
        actual = tuple((item.mnemonic, item.op_str) for item in insns)
        if actual != expected_instructions(spec) or sum(item.size for item in insns) != 44:
            raise ValueError(f"Original instructions changed at {address:#010x}: {actual}")
        specs.append(spec)

    # These are pointer-table references rather than statically decoded BLs.
    # Every selected callback occupies the first word of an 8-byte table slot.
    table_offset = TABLE_START - TEXT
    table = image[table_offset:TABLE_END - TEXT]
    if len(table) != TABLE_END - TABLE_START:
        raise ValueError("Callback pointer-table slice is incomplete")
    found = set()
    for offset in range(0, len(table), 8):
        function_pointer, auxiliary = struct.unpack_from("<II", table, offset)
        if function_pointer in ALL_ADDRESSES:
            if auxiliary != 0:
                raise ValueError(f"Unexpected auxiliary table word for {function_pointer:#x}")
            found.add(function_pointer)
    if found != set(ALL_ADDRESSES):
        raise ValueError("Callback table no longer references the full candidate family")
    return specs


def _case(seed: int, label: str, spec: FunctionSpec) -> Case:
    rng = random.Random(seed ^ spec.address)
    data = bytearray(rng.randbytes(DATA_SIZE))
    # Keep slot, record and context independent. Each base and the halfword
    # field are naturally aligned, and all offsets remain in mapped RAM.
    slot = DATA + 0x40
    record = DATA + 0x200
    context = DATA + 0x800
    struct.pack_into("<I", data, slot - DATA, record)
    counter = (0, 1, 0x7FFFFFFF, U32_MASK)[seed % 4]
    struct.pack_into("<I", data, context - DATA + 0x10, counter)
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0], regs[1] = context, slot
    return Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def _cases(spec: FunctionSpec, samples: int, seed: int):
    for i in range(8 + samples):
        yield _case(seed + i, f"aligned-independent-ram-{i}", spec)


def run(code_path: Path, output: Path, samples: int = 64, seed: int = 20261024) -> dict:
    if samples < 0:
        raise ValueError("samples must be nonnegative")
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    specs = verify_reference(image, game["code_sha256"], rows)

    source = ROOT / "experiments/semantic_equivalence/table_callback_candidates.cpp"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    object_path = output / "table_callback_candidates.o"
    build = compile_tu_armv6k(source, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    compiled = {}
    for symbol, (code, relocations) in extract_elf_functions_detailed(object_path).items():
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        validate_leaf(code)
        compiled[symbol] = code
    required = {spec.candidate_symbol for spec in specs} | {
        "negative_byte_field", "negative_halfword_field",
    }
    missing = required - compiled.keys()
    if missing:
        raise ValueError(f"Missing compiled symbols: {sorted(missing)}")

    results = []
    for spec in specs:
        original = Runner(image, spec.address)
        candidate = Runner(image, spec.address, compiled[spec.candidate_symbol],
                           replacement_validator=validate_leaf)
        failure = None
        count = 0
        for case in _cases(spec, samples, seed):
            reason = difference(original.run(case), candidate.run(case), returns_value=True)
            count += 1
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
        result = {"address": hex(spec.address), "width": spec.width,
                  "type_value": spec.type_value, "field_value": spec.field_value,
                  "original_bytes": 44,
                  "candidate_bytes": len(compiled[spec.candidate_symbol]),
                  "cases": count, "passed": failure is None, "failure": failure}
        results.append(result)
        print(json.dumps(result), flush=True)

    negative_controls = []
    controls = (
        (BYTE_CALLBACKS, 0x0035B6FC, "negative_byte_field", "byte"),
        (HALFWORD_CALLBACKS, 0x0035B898, "negative_halfword_field", "halfword"),
    )
    specs_by_address = {spec.address: spec for spec in specs}
    for _, address, symbol, width in controls:
        spec = specs_by_address[address]
        case = next(iter(_cases(spec, 0, seed)))
        original = Runner(image, address)
        wrong = Runner(image, address, compiled[symbol], replacement_validator=validate_leaf)
        reason = difference(original.run(case), wrong.run(case), returns_value=True)
        negative_controls.append({"name": symbol, "target": hex(address),
                                  "detected": reason is not None, "reason": reason})

    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Candidate source changed during the experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True)
    report = {
        "schema": 1,
        "passed": all(row["passed"] for row in results)
                  and all(row["detected"] for row in negative_controls),
        "scope": "17 isolated callback candidates referenced by an 8-byte pointer table; aligned independent ordinary RAM only",
        "reference_sha256": hashlib.sha256(image).hexdigest(),
        "source_sha256": source_hash,
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler": compiler.stdout.splitlines()[0],
        "seed": seed,
        "random_cases_per_function": samples,
        "functions": results,
        "negative_controls": negative_controls,
        "limitations": [
            "Table slots establish indirect callback references, not semantic names or a complete caller-level contract",
            "Bounded differential testing is evidence, not a formal equivalence proof",
            "Only aligned ordinary RAM with independent slot, record and context objects is covered",
            "Unaligned access, MMIO/volatile hardware semantics, concurrency, timing and fault ordering are excluded",
            "Aliasing among r0 context, r1 slot cell and the pointed-to record is excluded and needs dedicated cases before widening the claim",
            "No production source, ledger, game image, emulator, patch or save data is changed",
        ],
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Table callback experiment {'PASS' if report['passed'] else 'FAIL'}; report: {report_path}", flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/table-callbacks")
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    try:
        report = run(args.code, args.output, args.samples, args.seed)
    except (RuntimeError, ValueError, OSError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
