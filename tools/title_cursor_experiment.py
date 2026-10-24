#!/usr/bin/env python3
"""Isolated differential check for the title cursor-normalization block."""
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

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang
from tools.semantic_experiment import (
    DATA, DATA_SIZE, INJECT, RETURN, STACK_SIZE, TEXT, Case, Runner,
    validate_local_blob,
)


BLOCK_START = 0x001E9DAC
BLOCK_STOP = 0x001E9DC4
WORK = DATA + 0x100
CURSOR_FIELD = WORK + 8
U32_MASK = 0xFFFFFFFF
PROVISIONAL_VALUES = (-1, 0, 1, 2, 3, 4)


def verify_reference_block(image: bytes, configured_hash: str) -> dict:
    actual_hash = hashlib.sha256(image).hexdigest()
    if actual_hash != configured_hash:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    import capstone
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    offset = BLOCK_START - TEXT
    code = image[offset : offset + (BLOCK_STOP - BLOCK_START)]
    instructions = list(cs.disasm(code, BLOCK_START))
    expected = [
        (0x001E9DAC, "add", "r0, r0, #4"),
        (0x001E9DB0, "asr", "r1, r0, #0x1f"),
        (0x001E9DB4, "add", "r1, r0, r1, lsr #30"),
        (0x001E9DB8, "bic", "r1, r1, #3"),
        (0x001E9DBC, "sub", "r0, r0, r1"),
        (0x001E9DC0, "str", "r0, [r4, #8]"),
    ]
    actual = [(item.address, item.mnemonic, item.op_str) for item in instructions]
    if actual != expected or sum(item.size for item in instructions) != len(code):
        raise ValueError("Pinned title cursor block differs from the six recorded instructions")
    return {
        "sha256": actual_hash,
        "instructions": [
            {"address": hex(address), "mnemonic": mnemonic, "operands": operands}
            for address, mnemonic, operands in actual
        ],
    }


def cases(seed: int = 20261024):
    rng = random.Random(seed)
    for provisional in PROVISIONAL_VALUES:
        data = bytearray(rng.randbytes(DATA_SIZE))
        struct.pack_into("<I", data, CURSOR_FIELD - DATA, 0xA5A5A5A5)
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0] = provisional & U32_MASK
        regs[4] = WORK
        yield Case(f"provisional-{provisional}", tuple(regs), bytes(data),
                   rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def candidate_case(original_case: Case) -> Case:
    regs = list(original_case.registers)
    regs[0] = CURSOR_FIELD
    regs[1] = original_case.registers[0]
    return Case(original_case.label, tuple(regs), original_case.data,
                original_case.stack, original_case.nzcv)


def reference_value(provisional: int) -> int:
    adjusted = ((provisional & U32_MASK) + 4) & U32_MASK
    sign_fill = U32_MASK if adjusted & 0x80000000 else 0
    correction = sign_fill >> 30
    truncated_multiple = (adjusted + correction) & U32_MASK & ~3
    return (adjusted - truncated_multiple) & U32_MASK


def compare_block(original: Runner, candidate: Runner, case: Case) -> str | None:
    reference = original.run(case, start=BLOCK_START, stops=(BLOCK_STOP,), budget=32)
    rebuilt = candidate.run(candidate_case(case), budget=128)
    if reference.fault:
        return f"reference fault: {reference.fault}"
    if rebuilt.fault:
        return f"candidate fault: {rebuilt.fault}"
    if not reference.stopped or reference.pc != BLOCK_STOP:
        return "reference did not reach the recorded block stop"
    if not rebuilt.stopped or rebuilt.pc != RETURN:
        return "candidate did not return through its ABI boundary"
    if reference.result != rebuilt.result:
        return "normalized cursor differs in r0"
    if reference.result != reference_value(case.registers[0]):
        return "original block result differs from its recorded arithmetic"
    if reference.data != rebuilt.data:
        return "work memory differs"
    if reference.reads != rebuilt.reads or reference.writes != rebuilt.writes:
        return "observable memory access footprint differs"
    if reference.live_stack != rebuilt.live_stack:
        return "live stack differs"
    if reference.preserved != rebuilt.preserved:
        return "callee-saved register/SP/VFP state differs"
    if reference.nzcv != rebuilt.nzcv:
        return "condition flags differ"
    if struct.unpack_from("<I", reference.data, CURSOR_FIELD - DATA)[0] != reference.result:
        return "original block did not store r0 to work+8"
    if struct.unpack_from("<I", rebuilt.data, CURSOR_FIELD - DATA)[0] != rebuilt.result:
        return "candidate did not store r0 to the cursor field"
    return None


def run(code_path: Path, output: Path, seed: int = 20261024) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    block = verify_reference_block(image, game["code_sha256"])

    source = ROOT / "experiments/semantic_equivalence/title_cursor_candidate.cpp"
    object_path = output / "title_cursor_candidate.o"
    build = compile_tu_armv6k(source, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    functions = extract_elf_functions_detailed(object_path)
    required = ("title_cursor_normalize_store", "title_cursor_negative_no_bias")
    codes = {}
    for name in required:
        if name not in functions:
            raise ValueError(f"Missing candidate function: {name}")
        code, relocations = functions[name]
        if relocations:
            raise ValueError(f"Unsupported relocation in {name}: {relocations}")
        validate_local_blob(code)
        codes[name] = code

    original = Runner(image, BLOCK_START)
    rebuilt = Runner(image, BLOCK_START, codes[required[0]],
                     replacement_validator=validate_local_blob)
    results = []
    for case in cases(seed):
        reason = compare_block(original, rebuilt, case)
        results.append({"case": case.label, "input_u32": hex(case.registers[0] & U32_MASK),
                        "expected": hex(reference_value(case.registers[0])),
                        "passed": reason is None, "reason": reason})

    wrong = Runner(image, BLOCK_START, codes[required[1]],
                   replacement_validator=validate_local_blob)
    negative_control = None
    negative_case = next(case for case in cases(seed) if case.registers[0] == U32_MASK)
    reason = compare_block(original, wrong, negative_case)
    negative_control = {
        "detected": reason is not None,
        "case": negative_case.label,
        "reason": reason,
    }

    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True)
    report = {
        "passed": all(item["passed"] for item in results) and negative_control["detected"],
        "scope": "isolated semantic experiment for the six-instruction title cursor block; no production callback edit, IPS, emulator, or save data",
        "block_start": hex(BLOCK_START),
        "block_stop": hex(BLOCK_STOP),
        "reference": block,
        "candidate_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "candidate_object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "candidate_bytes": len(codes[required[0]]),
        "negative_control_bytes": len(codes[required[1]]),
        "compiler": compiler.stdout.splitlines()[0],
        "seed": seed,
        "provisional_values": list(PROVISIONAL_VALUES),
        "cases": results,
        "negative_control": negative_control,
        "memory_contract": {"work_base": hex(WORK), "cursor_field": hex(CURSOR_FIELD),
                            "written_bytes": 4},
        "limitations": [
            "Only the isolated arithmetic/store block is covered, not input polling or event dispatch",
            "This block is inline in ui_func_001e989c and is not a standalone production function",
            "The result is bounded differential evidence, not a formal proof",
        ],
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Title cursor experiment {'PASS' if report['passed'] else 'FAIL'}; report: {report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/title-cursor/seed-20261024")
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    try:
        result = run(args.code, args.output, args.seed)
    except (RuntimeError, ValueError, OSError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
