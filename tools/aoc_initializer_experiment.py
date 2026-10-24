#!/usr/bin/env python3
"""Differentially test three equivalent four-word initializers in isolation."""
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
    DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference, validate_leaf,
)


FUNCTIONS = {
    0x00352950: "candidate_00352950",
    0x003530F8: "candidate_003530f8",
    0x00354D28: "candidate_00354d28",
}
REFERENCE_WORDS = (
    0xE92D4070,  # push {r4, r5, r6, lr}
    0xE1A05002,  # mov r5, r2
    0xE1A04003,  # mov r4, r3
    0xE5801000,  # str r1, [r0]
    0xE2802004,  # add r2, r0, #4
    0xE3A01000,  # mov r1, #0
    0xE580400C,  # str r4, [r0, #0xc]
    0xE8820022,  # stm r2, {r1, r5}
    0xE8BD8070,  # pop {r4, r5, r6, pc}
)

# Pinned direct callers and immediately consumed values:
# AOC texture: source +0x80, buffer +0x5AC, size 0x20000, result -> +0x5A8.
# AOC archive: source +0x80, buffer +0x5B4, size 0x20000, result -> +0x5B0.
# Script VM: stack descriptor at sp+0x8D0; source +0x80, buffer sp+8,
# size 0x400; the resulting descriptor is passed to 0x00354C30.
CALLER_WINDOWS = {
    "aoc_texture": (
        (0x0038B418, "ldr", "r1, [r4, #0x80]"),
        (0x0038B41C, "ldr", "r2, [r4, #0x5ac]"),
        (0x0038B420, "mov", "r3, #0x20000"),
        (0x0038B424, "bl", "#0x3530f8"),
        (0x0038B428, "str", "r0, [r4, #0x5a8]"),
    ),
    "aoc_archive": (
        (0x0038B5A4, "ldr", "r1, [r4, #0x80]"),
        (0x0038B5A8, "ldr", "r2, [r4, #0x5b4]"),
        (0x0038B5AC, "mov", "r3, #0x20000"),
        (0x0038B5B0, "bl", "#0x352950"),
        (0x0038B5B4, "str", "r0, [r4, #0x5b0]"),
    ),
    "script_vm_descriptor": (
        (0x0038DEA8, "add", "r8, sp, #0x8d0"),
        (0x0038DEAC, "ldr", "r1, [r4, #0x80]"),
        (0x0038DEB0, "mov", "r3, #0x400"),
        (0x0038DEB4, "add", "r2, sp, #8"),
        (0x0038DEB8, "mov", "r0, r8"),
        (0x0038DEBC, "bl", "#0x354d28"),
        (0x0038DEC0, "add", "r2, r4, #0x400"),
        (0x0038DEC4, "add", "r0, sp, #0x800"),
        (0x0038DEC8, "add", "r2, r2, #0x294"),
        (0x0038DECC, "mov", "r1, r8"),
        (0x0038DED0, "add", "r0, r0, #8"),
        (0x0038DED4, "bl", "#0x354c30"),
    ),
}

U32_MASK = 0xFFFFFFFF
OBJECT_OFFSETS = (0x100, 0x104, 0x108, 0x10C, 0xFF0)
POINTER_SENTINELS = (0, 1, U32_MASK, DATA, DATA + 0x100,
                     DATA + 0x104, DATA + 0x108, DATA + 0x10C)
SIZE_BOUNDARIES = (0, 1, 2, 3, 4, 0x10, 0x20000, 0x400,
                   0x7FFFFFFF, 0x80000000, U32_MASK)


def _instruction_at(image: bytes, address: int):
    offset = address - TEXT
    if offset < 0 or offset + 4 > len(image):
        raise ValueError(f"Address outside code image: {address:#010x}")
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    return next(cs.disasm(image[offset:offset + 4], address), None)


def verify_reference(image: bytes, expected_sha256: str) -> dict:
    """Pin the binary and verify all three original instruction bodies."""
    actual_sha256 = hashlib.sha256(image).hexdigest()
    if not expected_sha256 or actual_sha256 != expected_sha256:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    expected = struct.pack("<9I", *REFERENCE_WORDS)
    bodies = {}
    for address in FUNCTIONS:
        offset = address - TEXT
        code = image[offset:offset + len(expected)]
        if code != expected:
            raise ValueError(f"Original initializer bytes differ at {address:#010x}")
        bodies[hex(address)] = {
            "size": len(code),
            "sha256": hashlib.sha256(code).hexdigest(),
            "instructions": len(REFERENCE_WORDS),
        }
    return {"sha256": actual_sha256, "functions": bodies}


def verify_callers(image: bytes, expected_sha256: str) -> dict:
    """Fail closed if observed direct-caller argument setup/use changes."""
    if hashlib.sha256(image).hexdigest() != expected_sha256:
        raise ValueError("caller evidence SHA-256 does not match code.bin")
    result = {}
    for name, window in CALLER_WINDOWS.items():
        actual = []
        for address, mnemonic, operands in window:
            instruction = _instruction_at(image, address)
            if instruction is None or (instruction.mnemonic, instruction.op_str) != (
                mnemonic, operands
            ):
                raise ValueError(f"caller bounds/type evidence drift at {address:#010x}")
            actual.append({"address": hex(address), "mnemonic": mnemonic,
                           "operands": operands, "bytes": instruction.bytes.hex()})
        result[name] = actual
    return result


def make_cases(address: int, seed: int, samples: int):
    """Cover null/sentinel values, caller sizes, aliased pointers, and random words."""
    if samples < 0:
        raise ValueError("samples must be non-negative")
    rng = random.Random(seed ^ address)
    fixed = (
        ("all-zero", DATA + 0x100, 0, 0, 0),
        ("aoc-texture-caller", DATA + 0x100, DATA + 0x300, DATA + 0x500, 0x20000),
        ("aoc-archive-caller", DATA + 0x104, DATA + 0x304, DATA + 0x504, 0x20000),
        ("script-vm-caller", DATA + 0x108, DATA + 0x308, DATA + 0x508, 0x400),
        ("null-source", DATA + 0x10C, 0, DATA + 0x600, 0x400),
        ("null-buffer", DATA + 0x110, DATA + 0x610, 0, 0x20000),
        # The values alias the destination object and its individual words.
        ("source-buffer-same", DATA + 0x114, DATA + 0x700, DATA + 0x700, 0x10),
        ("source-points-at-object", DATA + 0x118, DATA + 0x118, DATA + 0x11C, 1),
        ("pointers-alias-destination-words", DATA + 0x11C, DATA + 0x120,
         DATA + 0x124, U32_MASK),
        ("max-sentinel-pointers", DATA + 0x128, U32_MASK, 1, U32_MASK),
        ("boundary-zero-size", DATA + 0xFF0, DATA + 0xFF0, DATA + 0xFFC, 0),
        ("boundary-size-one", DATA + 0xFF0, 0, U32_MASK, 1),
    )
    for label, object_pointer, source_pointer, buffer_pointer, size in fixed:
        yield _case(label, object_pointer, source_pointer, buffer_pointer, size,
                    rng)

    for index in range(samples):
        object_offset = OBJECT_OFFSETS[rng.randrange(len(OBJECT_OFFSETS))]
        object_pointer = DATA + object_offset
        source_pointer = _random_pointer(rng, object_pointer)
        buffer_pointer = _random_pointer(rng, object_pointer)
        size = SIZE_BOUNDARIES[index % len(SIZE_BOUNDARIES)] if index < len(SIZE_BOUNDARIES) \
            else rng.getrandbits(32)
        label = f"random-{index}"
        if source_pointer == buffer_pointer:
            label += "-pointer-alias"
        yield _case(label, object_pointer, source_pointer, buffer_pointer, size,
                    rng)


def _random_pointer(rng: random.Random, object_pointer: int) -> int:
    selector = rng.randrange(4)
    if selector == 0:
        return rng.choice(POINTER_SENTINELS)
    if selector == 1:
        return object_pointer + rng.choice((0, 4, 8, 12))
    if selector == 2:
        return DATA + rng.randrange(DATA_SIZE)
    return rng.getrandbits(32)


def _case(label: str, object_pointer: int, source_pointer: int,
          buffer_pointer: int, size: int, rng: random.Random) -> Case:
    if object_pointer % 4 or object_pointer < DATA or object_pointer + 0x10 > DATA + DATA_SIZE:
        raise ValueError("destination must be a valid aligned four-word object in mapped DATA")
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0:4] = [object_pointer, source_pointer & U32_MASK,
                 buffer_pointer & U32_MASK, size & U32_MASK]
    return Case(label, tuple(regs), rng.randbytes(DATA_SIZE),
                rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def run(code_path: Path, output: Path, seed: int = 20261024,
        samples: int = 64) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    reference = verify_reference(image, game["code_sha256"])
    caller_evidence = verify_callers(image, game["code_sha256"])

    source = ROOT / "experiments/semantic_equivalence/aoc_initializer_candidates.cpp"
    object_path = output / "aoc_initializer_candidates.o"
    build = compile_tu_armv6k(source, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    functions = extract_elf_functions_detailed(object_path)
    required = (*FUNCTIONS.values(), "wrong_initializer_nonzero_reserved")
    compiled = {}
    for symbol in required:
        if symbol not in functions:
            raise ValueError(f"Missing candidate function: {symbol}")
        code, relocations = functions[symbol]
        if relocations:
            raise ValueError(f"Unsupported external relocation in {symbol}: {relocations}")
        validate_leaf(code)
        compiled[symbol] = code

    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    results = []
    controls = []
    for address, symbol in FUNCTIONS.items():
        oracle = Runner(image, address)
        rebuilt = Runner(image, address, compiled[symbol])
        cases = list(make_cases(address, seed, samples))
        compared = []
        for case in cases:
            reason = difference(oracle.run(case), rebuilt.run(case))
            compared.append({"case": case.label, "passed": reason is None,
                             "reason": reason,
                             "arguments": [hex(value) for value in case.registers[:4]]})
        results.append({"address": hex(address), "candidate": symbol,
                        "reference_bytes": 36, "candidate_bytes": len(compiled[symbol]),
                        "byte_identical": image[address - TEXT:address - TEXT + 36]
                        == compiled[symbol], "passed": all(item["passed"] for item in compared),
                        "case_count": len(compared), "cases": compared})

        wrong = Runner(image, address, compiled["wrong_initializer_nonzero_reserved"])
        negative_case = next(case for case in cases if case.label == "all-zero")
        reason = difference(oracle.run(negative_case), wrong.run(negative_case))
        controls.append({"address": hex(address), "case": negative_case.label,
                         "detected": reason is not None,
                         "expected_reason": "data memory differs", "reason": reason})

    if hashlib.sha256(source.read_bytes()).hexdigest() != source_digest:
        raise RuntimeError("Candidate source changed during experiment; rerun stable inputs")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True)
    report = {
        "schema": 1,
        "passed": all(result["passed"] for result in results)
        and all(item["detected"] and item["reason"] == item["expected_reason"]
                for item in controls),
        "scope": "isolated semantic differential experiment; production, IPS, emulator and saves untouched",
        "reference": reference,
        "caller_evidence": caller_evidence,
        "source_sha256": source_digest,
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler": compiler.stdout.splitlines()[0],
        "seed": seed,
        "random_samples_per_function": samples,
        "candidate_functions": results,
        "negative_controls": controls,
        "layout": {"size": 16, "words": ["source", "zero", "buffer", "size"],
                   "writes": "exactly bytes +0x00..+0x0F of the destination",
                   "source_and_buffer": "stored as opaque pointer values; never dereferenced"},
        "limitations": [
            "Differential tests cover the recorded four-word initializer contract, not downstream resource behavior",
            "The script-VM descriptor type name is unknown; only the caller-observed four-word layout is claimed",
            "Boundary and seeded random inputs are bounded evidence, not a formal proof",
            "Experimental functions do not replace production bodies or count as byte-exact matching",
        ],
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"AOC initializer experiment {'PASS' if report['passed'] else 'FAIL'}; report: {report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/aoc-initializers/seed-20261024")
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
