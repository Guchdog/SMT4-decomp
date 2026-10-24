#!/usr/bin/env python3
"""Differential semantic experiment for 19 engine leaf functions.

All outputs stay under ignored build/ paths. The pinned original code image is
the oracle; no production callback, patch image, emulator, or save data is used.
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
import tools.semantic_experiment as semantic
from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference, validate_leaf,
)

COPY_PLAIN = (
    0x002C7084, 0x002DD080, 0x002F3450, 0x002F98E0,
    0x002FAF08, 0x00302764, 0x00315960, 0x0031AB34,
)
COPY_OFFSET = (
    0x002C6EB0, 0x002DF400, 0x002E8114, 0x002E8284,
    0x002F3280, 0x00304154, 0x0030F234,
)
GETTERS = (0x003F5A68, 0x003F5E34, 0x003F635C, 0x003F6800)
ALL_ADDRESSES = COPY_PLAIN + COPY_OFFSET + GETTERS
U32_MASK = 0xFFFFFFFF
COPY_CASES = (
    (1, 0, "overlap-dst-after"),
    (0, 1, "overlap-dst-before"),
    (2, 2, "identical-pointer"),
    (8, 0, "disjoint"),
    (0, 8, "disjoint-reverse"),
)
class VfpEnabledRunner(Runner):
    """Runner with CP10/11 and VFP enabled for original ARM11 transfers."""

    def __init__(self, image: bytes, entry: int, replacement: bytes | None = None,
                 replacement_validator=validate_leaf):
        super().__init__(image, entry, replacement, replacement_validator)

    def run(self, case: Case, *, start: int | None = None,
            stops: tuple[int, ...] = (semantic.RETURN,), budget: int = 128):
        # CPACR grants full access to CP10/11 and FPEXC.EN enables VFP.
        self.uc.reg_write(semantic.arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(semantic.arm.UC_ARM_REG_FPEXC, 0x40000000)
        # These are caller-saved and deliberately not compared by difference,
        # but identical deterministic initial state keeps each side reproducible.
        for index in range(8):
            pattern = ((index + 1) * 0x11111111) & U32_MASK
            self.uc.reg_write(getattr(semantic.arm, f"UC_ARM_REG_D{index}"),
                              (pattern << 32) | (pattern ^ U32_MASK))
        return super().run(case, start=start, stops=stops, budget=budget)


@dataclass(frozen=True)
class FunctionSpec:
    address: int
    kind: str
    candidate_symbol: str
    size: int


def verify_reference(image: bytes, configured_hash: str, rows: list[dict]) -> list[FunctionSpec]:
    digest = hashlib.sha256(image).hexdigest()
    if digest != configured_hash:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    by_address = {int(row["address"], 16): row for row in rows}
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    specs = []
    for address in ALL_ADDRESSES:
        row = by_address.get(address)
        if row is None:
            raise ValueError(f"Missing function ledger row for {address:#010x}")
        size = int(row["size"])
        if address in COPY_PLAIN:
            kind, expected_size = "plain_copy", 12
            expected = (("vldmia", "r1, {s0, s1, s2, s3}"),
                        ("vstmia", "r0, {s0, s1, s2, s3}"), ("bx", "lr"))
        elif address in COPY_OFFSET:
            kind, expected_size = "offset_copy", 16
            expected = (("vldmia", "r1, {s0, s1, s2, s3}"),
                        ("add", "r0, r0, #0x10"),
                        ("vstmia", "r0, {s0, s1, s2, s3}"), ("bx", "lr"))
        else:
            kind, expected_size = "getter", 12
            expected = (("ldr", "r0, [r0, #4]"), ("mov", "r0, r0"), ("bx", "lr"))
        if size != expected_size:
            raise ValueError(f"Unexpected ledger size for {address:#010x}: {size}")
        offset = address - TEXT
        raw = image[offset : offset + size]
        insns = list(cs.disasm(raw, address))
        if tuple((item.mnemonic, item.op_str) for item in insns) != expected:
            raise ValueError(f"Original instructions changed for {address:#010x}")
        if sum(item.size for item in insns) != size:
            raise ValueError(f"Incomplete original instruction decode at {address:#010x}")
        specs.append(FunctionSpec(address, kind, f"candidate_{address:08x}", size))
    return specs


def _case(seed: int, label: str, arg0: int, arg1: int = 0, *, words=None) -> Case:
    rng = random.Random(seed)
    data = bytearray(rng.randbytes(DATA_SIZE))
    if words is not None:
        struct.pack_into("<8I", data, 0x100, *words)
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0], regs[1] = arg0, arg1
    return Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def copy_cases(spec: FunctionSpec, samples: int, seed: int):
    shift = 0 if spec.kind == "plain_copy" else 4
    base = DATA + 0x100
    initial = (0x11223344, 0x55667788, 0x99AABBCC, 0xDDEEFF00,
               0x01020304, 0xA5A5A5A5, 0x5A5A5A5A, 0xFFFFFFFF)
    for index, (dst_word, src_word, label) in enumerate(COPY_CASES):
        # dst_word is the effective destination; the offset group receives the
        # original base pointer four words earlier, as its assembly does.
        original_dst = base + (dst_word - shift) * 4
        source = base + src_word * 4
        case = _case(seed + index, label, original_dst, source, words=initial)
        yield case
    rng = random.Random(seed ^ spec.address)
    for index in range(samples):
        dst_word = rng.randrange(0, 12)
        src_word = rng.randrange(0, 12)
        original_dst = base + (dst_word - shift) * 4
        source = base + src_word * 4
        case = _case(seed + 1000 + index, f"random-aligned-{index}",
                     original_dst, source)
        yield case


def getter_cases(spec: FunctionSpec, samples: int, seed: int):
    rng = random.Random(seed ^ spec.address)
    for index in range(8 + samples):
        data = bytearray(rng.randbytes(DATA_SIZE))
        pointer = DATA + 0x100 + (index % 16) * 4
        value = (0x01020304, 0x80000000, U32_MASK, index)[index % 4]
        struct.pack_into("<I", data, pointer - DATA + 4, value)
        struct.pack_into("<I", data, pointer - DATA + 8, value ^ U32_MASK)
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0] = pointer
        yield Case(f"valid-aligned-{index}", tuple(regs), bytes(data),
                   rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def candidate_cases(spec: FunctionSpec, samples: int, seed: int):
    if spec.kind == "getter":
        return getter_cases(spec, samples, seed)
    return copy_cases(spec, samples, seed)


def _compare(original: Runner, candidate: Runner, case: Case, spec: FunctionSpec):
    return difference(original.run(case), candidate.run(case),
                      returns_value=(spec.kind == "getter"))


def run(code_path: Path, output: Path, samples: int = 64, seed: int = 20261024) -> dict:
    if samples < 0:
        raise ValueError("samples must be nonnegative")
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    specs = verify_reference(image, game["code_sha256"], rows)

    source = ROOT / "experiments/semantic_equivalence/engine_leaf_candidates.cpp"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    object_path = output / "engine_leaf_candidates.o"
    build = compile_tu_armv6k(source, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    functions = extract_elf_functions_detailed(object_path)
    compiled = {}
    for symbol, (code, relocations) in functions.items():
        if relocations:
            raise ValueError(f"External/unsupported relocation in {symbol}: {relocations}")
        validate_leaf(code)
        compiled[symbol] = code

    required = {spec.candidate_symbol for spec in specs} | {
        "negative_plain_forward_copy", "negative_offset_forward_copy",
        "negative_getter_offset",
    }
    missing = required - compiled.keys()
    if missing:
        raise ValueError(f"Missing compiled candidate symbols: {sorted(missing)}")

    results = []
    by_address = {spec.address: spec for spec in specs}
    for spec in specs:
        original = VfpEnabledRunner(image, spec.address)
        candidate = VfpEnabledRunner(image, spec.address, compiled[spec.candidate_symbol],
                                      replacement_validator=validate_leaf)
        passed = True
        count = 0
        failure = None
        for case in candidate_cases(spec, samples, seed):
            reason = _compare(original, candidate, case, spec)
            count += 1
            if reason:
                passed, failure = False, {"case": case.label, "reason": reason}
                break
        results.append({"address": hex(spec.address), "kind": spec.kind,
                        "candidate": spec.candidate_symbol,
                        "original_bytes": spec.size,
                        "candidate_bytes": len(compiled[spec.candidate_symbol]),
                        "passed": passed, "cases": count, "failure": failure})
        print(json.dumps(results[-1]), flush=True)

    controls = []
    control_specs = (
        (COPY_PLAIN[0], "negative_plain_forward_copy", "overlap-dst-after"),
        (COPY_OFFSET[0], "negative_offset_forward_copy", "overlap-dst-after"),
        (GETTERS[0], "negative_getter_offset", "valid-aligned-0"),
    )
    for address, symbol, label in control_specs:
        spec = by_address[address]
        case = next(case for case in candidate_cases(spec, 0, seed)
                    if case.label == label)
        original = VfpEnabledRunner(image, address)
        wrong = VfpEnabledRunner(image, address, compiled[symbol],
                                  replacement_validator=validate_leaf)
        reason = _compare(original, wrong, case, spec)
        controls.append({"name": symbol, "target": hex(address), "case": label,
                         "detected": reason is not None, "reason": reason})

    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Candidate source changed during the experiment; rerun on stable input")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True)
    report = {
        "schema": 1,
        "passed": all(item["passed"] for item in results)
                  and all(item["detected"] for item in controls),
        "scope": "19 isolated leaf candidates: 8 plain copies, 7 copies to dst+0x10, 4 raw-word getters; not production code or a game boot",
        "reference_sha256": hashlib.sha256(image).hexdigest(),
        "source_sha256": source_hash,
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler": compiler.stdout.splitlines()[0],
        "seed": seed,
        "random_cases_per_copy": samples,
        "random_cases_per_getter": samples,
        "functions": results,
        "negative_controls": controls,
        "limitations": [
            "Bounded differential testing is evidence, not a formal equivalence proof",
            "Copies cover aligned ordinary RAM, including overlap; unaligned pointers, MMIO, concurrency, timing, and exceptions are excluded",
            "Unicorn executes the original VFP transfers with CPACR CP10/11 and FPEXC.EN enabled on the configured ARM11 model",
            "d0-d7 are initialized deterministically per run but are caller-saved and are not asserted equal",
            "Getter tests use valid aligned readable pointers only",
            "No production functions, matching ledger, game image, emulator, patch, or save data are changed",
        ],
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Engine leaf experiment {'PASS' if report['passed'] else 'FAIL'}; report: {report_path}", flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/engine-leaves")
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
