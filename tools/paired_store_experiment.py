#!/usr/bin/env python3
"""Differential-test three offset-specific paired-word store candidates."""
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

OFFSETS = {
    0x00158784: 0x84,
    0x0023347C: 0x40,
    0x00292E88: 0x40,
}
BASELINE_ADDRESS = 0x00131414
CALLERS = {
    0x00158784: (0x001548D8,),
    0x0023347C: (0x0022D978, 0x003915E4, 0x003A1518, 0x003A20F4,
                 0x003A23A4, 0x003A2E3C),
    0x00292E88: (0x001C4B1C, 0x001C4E14, 0x001C5008, 0x001C5554,
                 0x001C5740, 0x001C57F4, 0x001C5908, 0x001C5938,
                 0x00205978, 0x002059B0, 0x002059F0, 0x0026D700,
                 0x0026D7E4, 0x0028AC34, 0x0028AC7C, 0x00293640,
                 0x0029367C, 0x002936D0, 0x0029370C),
}
ALL_ADDRESSES = tuple(OFFSETS)
U32_MASK = 0xFFFFFFFF


@dataclass(frozen=True)
class FunctionSpec:
    address: int
    offset: int

    @property
    def candidate_symbol(self):
        return f"candidate_{self.address:08x}"


def discover_bl_callers(image: bytes) -> dict[int, tuple[int, ...]]:
    """Find ARM immediate BL references without decoding unrelated data words."""
    found = {address: [] for address in (*ALL_ADDRESSES, BASELINE_ADDRESS)}
    word_count = len(image) // 4
    for index in range(word_count):
        word = struct.unpack_from("<I", image, index * 4)[0]
        # ARM B/BL encoding (condition field excluded from this mask).
        if (word & 0x0F000000) != 0x0B000000 or (word >> 28) == 0xF:
            continue
        displacement = (word & 0x00FFFFFF) << 2
        if displacement & (1 << 25):
            displacement -= 1 << 26
        callsite = TEXT + index * 4
        target = (callsite + 8 + displacement) & U32_MASK
        if target in found:
            found[target].append(callsite)
    return {address: tuple(sites) for address, sites in found.items()}


def _instructions(image: bytes, address: int, size: int):
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    offset = address - TEXT
    decoded = list(cs.disasm(image[offset:offset + size], address))
    return tuple((item.mnemonic, item.op_str) for item in decoded), sum(i.size for i in decoded)


def verify_reference(image: bytes, configured_hash: str, rows: list[dict]) -> list[FunctionSpec]:
    if hashlib.sha256(image).hexdigest() != configured_hash:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    by_address = {int(row["address"], 16): row for row in rows}
    specs = []
    for address, offset in (*OFFSETS.items(), (BASELINE_ADDRESS, 4)):
        row = by_address.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != 12:
            raise ValueError(f"Missing matching 12-byte ledger entry at {address:#010x}")
        expected = (
            ("add", f"r0, r0, #{offset}" if offset < 10 else f"r0, r0, #0x{offset:x}"),
            ("stm", "r0, {r1, r2}"),
            ("bx", "lr"),
        )
        actual, decoded_size = _instructions(image, address, 12)
        if actual != expected or decoded_size != 12:
            raise ValueError(f"Original instruction sequence changed at {address:#010x}: {actual}")
        if address != BASELINE_ADDRESS:
            specs.append(FunctionSpec(address, offset))

    callers = discover_bl_callers(image)
    for target, expected_sites in CALLERS.items():
        if callers[target] != expected_sites:
            raise ValueError(
                f"Direct caller set changed for {target:#010x}: "
                f"expected {[hex(x) for x in expected_sites]}, got {[hex(x) for x in callers[target]]}"
            )
    if callers[BASELINE_ADDRESS] != (0x00121D1C,):
        raise ValueError("Baseline paired-store caller set changed")
    return specs


def caller_inventory(rows: list[dict]) -> dict[str, list[dict]]:
    containing = []
    for row in rows:
        address = int(row["address"], 16)
        end = address + int(row["size"])
        for target, callsites in CALLERS.items():
            for callsite in callsites:
                if address <= callsite < end:
                    containing.append({
                        "target": hex(target), "callsite": hex(callsite),
                        "caller": row["name"], "category": row["category"],
                        "caller_address": hex(address),
                    })
    return {"calls": containing}


def _case(seed: int, label: str, spec: FunctionSpec, first: int, second: int) -> Case:
    rng = random.Random(seed ^ spec.address)
    data = bytearray(rng.randbytes(DATA_SIZE))
    base = DATA + 0x100
    effective = base + spec.offset
    struct.pack_into("<II", data, effective - DATA, 0xDEADBEEF, 0xA55AA55A)
    registers = [rng.getrandbits(32) for _ in range(13)]
    registers[0], registers[1], registers[2] = base, first & U32_MASK, second & U32_MASK
    return Case(label, tuple(registers), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def _cases(spec: FunctionSpec, samples: int, seed: int):
    fixed = (
        (0, 0, "zero-pair"),
        (0x11223344, 0xAABBCCDD, "distinct-pattern"),
        (U32_MASK, 0x80000000, "unsigned-boundary"),
        (0x7FFFFFFF, 1, "increment-boundary"),
    )
    for index, (first, second, label) in enumerate(fixed):
        yield _case(seed + index, label, spec, first, second)
    rng = random.Random(seed ^ spec.address)
    for index in range(samples):
        yield _case(seed + 100 + index, f"random-pair-{index}", spec,
                    rng.getrandbits(32), rng.getrandbits(32))


def _candidate_instruction_order(code: bytes):
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    cs.detail = True
    decoded = list(cs.disasm(code, 0x01000000))
    stores = []
    for item in decoded:
        if item.mnemonic.startswith("str") and item.operands:
            mems = [operand for operand in item.operands
                    if operand.type == capstone.arm.ARM_OP_MEM]
            if mems:
                stores.append((item.mnemonic, item.op_str))
    return stores


def run(code_path: Path, output: Path, samples: int = 64, seed: int = 20261024) -> dict:
    if samples < 0:
        raise ValueError("samples must be nonnegative")
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    specs = verify_reference(image, game["code_sha256"], rows)

    source = ROOT / "experiments/semantic_equivalence/paired_store_candidates.cpp"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    object_path = output / "paired_store_candidates.o"
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
        "negative_wrong_offset", "negative_swapped_store", "negative_wrong_return",
    }
    missing = required - compiled.keys()
    if missing:
        raise ValueError(f"Missing compiled candidate symbols: {sorted(missing)}")

    # Require the generated candidates to retain the two ordered stores. This
    # guards access ordering even though regular RAM's final state alone cannot.
    for spec in specs:
        stores = _candidate_instruction_order(compiled[spec.candidate_symbol])
        if len(stores) != 2 or stores[0][0] != "str" or stores[1][0] != "str":
            raise ValueError(f"Candidate does not compile to two ordered word stores: {stores}")

    results = []
    for spec in specs:
        original = Runner(image, spec.address)
        candidate = Runner(image, spec.address, compiled[spec.candidate_symbol],
                           replacement_validator=validate_leaf)
        count = 0
        failure = None
        for case in _cases(spec, samples, seed):
            reason = difference(original.run(case), candidate.run(case), returns_value=True)
            count += 1
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
        result = {"address": hex(spec.address), "offset": hex(spec.offset),
                  "original_bytes": 12, "candidate_bytes": len(compiled[spec.candidate_symbol]),
                  "candidate_store_order": _candidate_instruction_order(compiled[spec.candidate_symbol]),
                  "cases": count, "passed": failure is None, "failure": failure}
        results.append(result)
        print(json.dumps(result), flush=True)

    controls = (
        (0x00158784, "negative_wrong_offset", "distinct-pattern"),
        (0x0023347C, "negative_swapped_store", "distinct-pattern"),
        (0x00292E88, "negative_wrong_return", "distinct-pattern"),
    )
    spec_by_address = {spec.address: spec for spec in specs}
    negative_controls = []
    for address, symbol, label in controls:
        spec = spec_by_address[address]
        case = next(case for case in _cases(spec, 0, seed)
                    if case.label == label)
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
        "passed": all(item["passed"] for item in results)
                  and all(item["detected"] for item in negative_controls),
        "scope": "three isolated paired-word store candidates at offsets +0x84/+0x40; aligned valid ordinary RAM only",
        "reference_sha256": hashlib.sha256(image).hexdigest(),
        "source_sha256": source_hash,
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler": compiler.stdout.splitlines()[0],
        "seed": seed,
        "random_cases_per_function": samples,
        "functions": results,
        "caller_inventory": caller_inventory(rows),
        "baseline": {"address": hex(BASELINE_ADDRESS), "offset": "0x4",
                     "direct_callers": ["0x00121d1c"]},
        "negative_controls": negative_controls,
        "limitations": [
            "The three routines share the paired-store ABI but callers use different object layouts and contexts",
            "All direct BL sites are verified; sampled caller windows discard or overwrite r0, but candidate preserves observed adjusted-pointer r0",
            "Bounded differential testing is evidence, not a formal equivalence proof",
            "Tests cover aligned, in-bounds ordinary RAM; unaligned memory, MMIO, concurrency, exceptions and partial-fault ordering are excluded",
            "The two destination words do not overlap; argument values arrive in registers, so source/destination pointer aliasing is not part of this contract",
            "No production source, ledger, game image, emulator, patch or save data is changed",
        ],
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Paired-store experiment {'PASS' if report['passed'] else 'FAIL'}; report: {report_path}", flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/paired-stores")
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
