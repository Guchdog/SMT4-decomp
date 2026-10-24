#!/usr/bin/env python3
"""Differentially test two script-VM record initializers on ordinary RAM."""
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
from tools.semantic_experiment import DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference
from tools.semantic_experiment_support import compile_candidate_symbols, load_pinned_reference

ADDRESSES = (0x00353124, 0x003531AC)
FUNCTION_SIZE = 60
EXPECTED_BYTES = bytes.fromhex(
    "0030a0e3003080e5043080e5083080e50c3080e5103080e5143080e5183080e51c"
    "3080e5203080e5243080e52830c0e52c3080e2060083e81eff2fe1"
)
ZERO_WORD_OFFSETS = tuple(range(0, 0x28, 4))
EXPECTED_WRITE_EVENTS = tuple((offset, 4) for offset in ZERO_WORD_OFFSETS) + (
    (0x28, 1), (0x2C, 4), (0x30, 4),
)
U32_MASK = 0xFFFFFFFF


def decode(image: bytes, address: int, size: int):
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    offset = address - TEXT
    instructions = list(decoder.disasm(image[offset:offset + size], address))
    if sum(item.size for item in instructions) != size:
        raise ValueError(f"incomplete instruction body at {address:#010x}")
    return tuple((item.mnemonic, item.op_str) for item in instructions)


def verify_reference(image: bytes, ledger: list[dict[str, str]]):
    rows = {int(row["address"], 16): row for row in ledger}
    expected = (
        ("mov", "r3, #0"),
        ("str", "r3, [r0]"),
        ("str", "r3, [r0, #4]"),
        ("str", "r3, [r0, #8]"),
        ("str", "r3, [r0, #0xc]"),
        ("str", "r3, [r0, #0x10]"),
        ("str", "r3, [r0, #0x14]"),
        ("str", "r3, [r0, #0x18]"),
        ("str", "r3, [r0, #0x1c]"),
        ("str", "r3, [r0, #0x20]"),
        ("str", "r3, [r0, #0x24]"),
        ("strb", "r3, [r0, #0x28]"),
        ("add", "r3, r0, #0x2c"),
        ("stm", "r3, {r1, r2}"),
        ("bx", "lr"),
    )
    for address in ADDRESSES:
        row = rows.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != FUNCTION_SIZE:
            raise ValueError(f"missing matching {FUNCTION_SIZE}-byte ledger row at {address:#010x}")
        actual = decode(image, address, FUNCTION_SIZE)
        if actual != expected:
            raise ValueError(f"instruction body changed at {address:#010x}: {actual}")
        offset = address - TEXT
        if image[offset:offset + FUNCTION_SIZE] != EXPECTED_BYTES:
            raise ValueError(f"pinned bytes changed at {address:#010x}")
    return rows


def verify_candidate_shape(code: bytes):
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoder.detail = True
    instructions = list(decoder.disasm(code, 0))
    if not instructions or sum(item.size for item in instructions) != len(code):
        raise ValueError("candidate has incomplete ARM disassembly")
    if instructions[-1].mnemonic != "bx" or instructions[-1].op_str != "lr":
        raise ValueError("candidate must return with bx lr")
    events = []
    for instruction in instructions:
        if instruction.mnemonic in ("str", "strb", "strh"):
            operands = instruction.operands
            if len(operands) != 2 or operands[1].type != capstone.CS_OP_MEM:
                raise ValueError(f"unexpected store shape: {instruction.mnemonic} {instruction.op_str}")
            memory = operands[1].mem
            if instruction.reg_name(memory.base) != "r0" or memory.index:
                raise ValueError(f"candidate store not based directly on r0: {instruction.op_str}")
            width = {"str": 4, "strb": 1, "strh": 2}[instruction.mnemonic]
            events.append((memory.disp, width))
        elif instruction.mnemonic.startswith("stm"):
            operands = instruction.operands
            if len(operands) != 2 or operands[1].type != capstone.CS_OP_REGS:
                raise ValueError(f"unexpected multiple-store shape: {instruction.op_str}")
            base = instruction.reg_name(operands[0].reg)
            if base != "r0":
                raise ValueError(f"multiple-store base is not r0: {instruction.op_str}")
            registers = sorted(instruction.reg_name(reg) for reg in instruction.regs_access()[1])
            # Only the final value pair is allowed to be grouped; the source STM
            # uses an adjusted temporary base, so this is a structural fallback.
            raise ValueError(f"unexpected grouped store in candidate; inspect ABI/base semantics: {registers}")
        elif instruction.mnemonic == "bx" and instruction.op_str == "lr":
            continue
        elif instruction.mnemonic.startswith(("ldr", "ldm")):
            raise ValueError(f"candidate must not load memory: {instruction.mnemonic} {instruction.op_str}")
    if tuple(events) != EXPECTED_WRITE_EVENTS:
        raise ValueError(f"candidate store order/width differs: {tuple(events)}")


def make_case(seed: int, label: str):
    rng = random.Random(seed)
    data = bytearray(rng.randbytes(DATA_SIZE))
    base = DATA + 0x100
    values = {
        "distinct": (0x12345678, 0xA5C39E71),
        "zeros": (0, 0),
        "all-ones": (U32_MASK, U32_MASK),
    }.get(label)
    if values is None:
        values = (rng.getrandbits(32), rng.getrandbits(32))
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0], regs[1], regs[2] = base, *values
    regs[4] = base
    return Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def _install_write_trace(runner: Runner, events: list[tuple[int, int, int]]):
    import unicorn

    def record(_uc, _access, address, size, value, _user):
        if DATA <= address < DATA + DATA_SIZE:
            events.append((address, size, value & ((1 << (size * 8)) - 1)))

    runner.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, record)


def run(code_path: Path, output: Path, samples: int = 64, seed: int = 20261024):
    if samples < 0:
        raise ValueError("samples must be nonnegative")
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    verify_reference(pinned.image, pinned.ledger)
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / "experiments/semantic_equivalence/script_vm_init_candidates.cpp"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    object_path = output / "script_vm_init_candidates.o"
    required = {f"candidate_{address:08x}" for address in ADDRESSES} | {
        "negative_skip_byte", "negative_word_at_byte", "negative_swapped_values",
    }
    compiled = compile_candidate_symbols(source, object_path, ROOT, required)
    for address in ADDRESSES:
        verify_candidate_shape(compiled[f"candidate_{address:08x}"])

    function_results = []
    negatives = []
    for address in ADDRESSES:
        original = Runner(pinned.image, address)
        candidate = Runner(pinned.image, address, compiled[f"candidate_{address:08x}"])
        reference_events: list[tuple[int, int, int]] = []
        candidate_events: list[tuple[int, int, int]] = []
        _install_write_trace(original, reference_events)
        _install_write_trace(candidate, candidate_events)
        trial_seeds = [("distinct", seed), ("zeros", seed + 1),
                       ("all-ones", seed + 2)]
        trial_seeds += [(f"random-{i}", random.Random(seed ^ address ^ i).getrandbits(32))
                        for i in range(samples)]
        for label, case_seed in trial_seeds:
            case = make_case(case_seed, label)
            reference_events.clear()
            candidate_events.clear()
            result_original = original.run(case)
            result_candidate = candidate.run(case)
            reason = difference(result_original, result_candidate, returns_value=True)
            if reason:
                raise AssertionError(f"{address:#010x} {label}: {reason}")
            if result_original.nzcv != result_candidate.nzcv:
                raise AssertionError(f"{address:#010x} {label}: NZCV flags differ")
            expected_events = tuple((DATA + 0x100 + offset, width,
                                     (case.registers[1] if offset == 0x2C else
                                      case.registers[2] if offset == 0x30 else 0))
                                    for offset, width in EXPECTED_WRITE_EVENTS)
            if tuple(reference_events) != expected_events:
                raise AssertionError(f"{address:#010x} reference write trace changed: {reference_events}")
            if tuple(candidate_events) != tuple(reference_events):
                raise AssertionError(f"{address:#010x} ordered write trace differs: {candidate_events}")
        function_results.append({"address": hex(address), "cases": len(trial_seeds),
                                 "candidate_bytes": len(compiled[f"candidate_{address:08x}"]),
                                 "ordered_write_width_trace": "verified", "passed": True})

    # Negative controls use the second independently pinned copy of this body.
    address = ADDRESSES[1]
    base_case = make_case(seed, "distinct")
    reference = Runner(pinned.image, address)
    for symbol in ("negative_skip_byte", "negative_word_at_byte", "negative_swapped_values"):
        wrong = Runner(pinned.image, address, compiled[symbol])
        reason = difference(reference.run(base_case), wrong.run(base_case), returns_value=True)
        negatives.append({"name": symbol, "detected": reason is not None, "reason": reason})

    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("candidate source changed during experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True).stdout.splitlines()[0]
    report = {
        "schema": 1,
        "passed": all(row["passed"] for row in function_results)
        and all(row["detected"] for row in negatives),
        "reference_sha256": pinned.game_info["code_sha256"],
        "function_bytes_sha256": hashlib.sha256(EXPECTED_BYTES).hexdigest(),
        "source_sha256": source_hash,
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler": compiler, "seed": seed, "random_cases_per_function": samples,
        "functions": function_results,
        "manually_verified_caller_windows": [],
        "caller_scan": "scaffold group 33 found no possible ARM BL callers; absence is not proof",
        "negative_controls": negatives,
        "contract": "base in aligned ordinary RAM; zero STR words at +0..+0x24 in order, zero STRB at +0x28, then store incoming r1/r2 words at +0x2c/+0x30 in order; return original r0",
        "compared": ["return r0", "callee-saved registers and SP", "NZCV flags",
                     "full data memory", "stack memory", "read/write byte footprints",
                     "ordered write address/width/value trace", "execution faults on tested valid RAM"],
        "limitations": [
            "No manually verified callers were available; indirect and Thumb call paths are not exercised",
            "Ordinary aligned RAM only; MMIO, concurrency, unaligned access and aliasing side effects are excluded",
            "Fault/exception equivalence is excluded: separate STR operations and grouped STM may differ in partial-fault visibility",
            "The bounded differential run is evidence, not a formal proof or a production integration",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/script-vm-initializers-seed20261024")
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    try:
        report = run(args.code, args.output, args.samples, args.seed)
    except (RuntimeError, ValueError, OSError, AssertionError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    print(f"Script-VM initializer experiment {'PASS' if report['passed'] else 'FAIL'}; report: {args.output / 'report.json'}")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
