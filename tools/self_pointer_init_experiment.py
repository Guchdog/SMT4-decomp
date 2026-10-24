#!/usr/bin/env python3
"""Differentially test two identical self-pointer initializer leaves."""
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
import unicorn
from tools.build_check import find_clang
from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference,
)
from tools.semantic_experiment_support import (
    compile_candidate_symbols, load_pinned_reference,
)

TARGETS = (0x00237F10, 0x003F7394)
EXPECTED_BYTES = bytes.fromhex(
    "0020a0e30110a0e3002080e50410c0e5081080e2081080e5102080e50c1080e5"
    "1eff2fe1"
)
EXPECTED_WRITES = ((0, 4, 0), (4, 1, 1), (8, 4, "self+8"),
                   (0x10, 4, 0), (0x0C, 4, "self+8"))
NEGATIVE_CONTROLS = (
    "negative_wide_flag", "negative_wrong_self_pointer",
    "negative_reordered_stores", "negative_missing_zero",
)


def disassemble(image: bytes, address: int, size: int) -> bytes:
    offset = address - TEXT
    return image[offset:offset + size]


def verify_reference(image: bytes, ledger: list[dict[str, str]]):
    rows = {int(row["address"], 16): row for row in ledger}
    for address in TARGETS:
        row = rows.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != 36:
            raise ValueError(f"missing matching 36-byte ledger entry at {address:#010x}")
        actual = disassemble(image, address, 36)
        if actual != EXPECTED_BYTES:
            raise ValueError(f"pinned instruction bytes changed at {address:#010x}")
    if disassemble(image, TARGETS[0], 36) != disassemble(image, TARGETS[1], 36):
        raise ValueError("the two functions no longer have identical pinned bytes")
    return rows


def make_case(seed: int, label: str, base_offset: int | None = None):
    rng = random.Random(seed)
    data = bytearray(rng.randbytes(DATA_SIZE))
    offset = base_offset if base_offset is not None else 0x100 + rng.randrange(0, 0x300, 4)
    base = DATA + offset
    # Distinct sentinels make the byte-width and field offsets observable.
    sentinels = (0xA5A55A5A, 0xDEADBEEF, 0x11223344, 0x55667788,
                 0xCAFEBABE)
    for word_index, value in enumerate(sentinels):
        address = offset + word_index * 4
        if address + 4 <= len(data):
            struct.pack_into("<I", data, address, value)
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0] = base
    return Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def cases(seed: int, samples: int):
    fixed = (
        (0x100, "distinct-sentinels"), (0x104, "next-aligned-object"),
        (0x2FC, "near-random-window-end"), (0x7F0, "high-address-ordinary-ram"),
    )
    for i, (offset, label) in enumerate(fixed):
        yield make_case(seed ^ (0x51 + i), label, offset)
    rng = random.Random(seed ^ 0x51F1A11)
    for i in range(samples):
        offset = rng.randrange(0x100, 0x800, 4)
        yield make_case(rng.getrandbits(32), f"random-aligned-{i}", offset)


def capture_writes(runner: Runner):
    events = []

    def hook(_uc, access, address, size, value, _user_data):
        events.append((address, size, value & ((1 << (size * 8)) - 1)))

    runner.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, hook)
    return events


def expected_events(base: int):
    return ((base, 4, 0), (base + 4, 1, 1), (base + 8, 4, base + 8),
            (base + 0x10, 4, 0), (base + 0x0C, 4, base + 8))


def event_trace(runner: Runner, case: Case):
    events = capture_writes(runner)
    result = runner.run(case)
    return result, tuple(events)


def run(code_path: Path, output: Path, samples: int = 64, seed: int = 20261024):
    if samples < 0:
        raise ValueError("samples must be nonnegative")
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    verify_reference(pinned.image, pinned.ledger)
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / "experiments/semantic_equivalence/self_pointer_init_candidates.cpp"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    object_path = output / "self_pointer_init_candidates.o"
    required = {f"candidate_{address:08x}" for address in TARGETS} | set(NEGATIVE_CONTROLS)
    compiled = compile_candidate_symbols(source, object_path, ROOT, required)

    function_results = []
    total_comparisons = 0
    for address in TARGETS:
        reference = Runner(pinned.image, address)
        candidate = Runner(pinned.image, address, compiled[f"candidate_{address:08x}"])
        count = 0
        for case in cases(seed ^ address, samples):
            original_result, original_events = event_trace(reference, case)
            candidate_result, candidate_events = event_trace(candidate, case)
            reason = difference(original_result, candidate_result, returns_value=True,
                                compare_flags=True)
            if reason:
                raise AssertionError(f"{address:#010x} {case.label}: {reason}")
            expected = expected_events(case.registers[0])
            if original_events != expected or candidate_events != expected:
                raise AssertionError(
                    f"{address:#010x} {case.label}: unexpected ordered write trace; "
                    f"reference={original_events}, candidate={candidate_events}, expected={expected}"
                )
            count += 1
        function_results.append({"address": hex(address), "candidate_bytes": len(compiled[f"candidate_{address:08x}"]),
                                 "cases": count, "passed": True,
                                 "write_trace": [list(event) for event in expected_events(DATA + 0x100)]})
        total_comparisons += count

    # A base at the last 16 bytes of the one mapped RAM page faults on +0x10.
    # Compare the observable prefix explicitly: this checks fault ordering and
    # that the later +0x0c write does not occur after the fault.
    fault_case = make_case(seed ^ 0xFA017, "fault-at-plus-0x10", DATA_SIZE - 16)
    fault_results = []
    for address in TARGETS:
        reference = Runner(pinned.image, address)
        candidate = Runner(pinned.image, address, compiled[f"candidate_{address:08x}"])
        original_result, original_events = event_trace(reference, fault_case)
        candidate_result, candidate_events = event_trace(candidate, fault_case)
        # Unicorn's valid-memory write hook also reports the attempted unmapped
        # +0x10 store, so the trace has four attempts but only three completed.
        expected_attempts = expected_events(fault_case.registers[0])[:4]
        passed = (
            original_result.fault is not None and candidate_result.fault is not None
            and not original_result.stopped and not candidate_result.stopped
            and original_result.data == candidate_result.data
            and original_events == candidate_events == expected_attempts
            and original_result.preserved == candidate_result.preserved
            and original_result.nzcv == candidate_result.nzcv
        )
        if not passed:
            raise AssertionError(f"fault-prefix mismatch at {address:#010x}: "
                                 f"orig={original_result.fault}/{original_events}, "
                                 f"candidate={candidate_result.fault}/{candidate_events}")
        fault_results.append({"address": hex(address), "passed": True,
                              "completed_writes_before_fault": 3,
                              "write_attempts_including_fault": len(original_events),
                              "fault": original_result.fault})

    negative_results = []
    negative_case = make_case(seed, "negative-control-distinct-sentinels", 0x180)
    for address in TARGETS:
        original = Runner(pinned.image, address)
        original_result = original.run(negative_case)
        for symbol in NEGATIVE_CONTROLS:
            wrong = Runner(pinned.image, address, compiled[symbol])
            wrong_result, wrong_events = event_trace(wrong, negative_case)
            reason = difference(original_result, wrong_result, returns_value=True,
                                compare_flags=True)
            detected = reason is not None or wrong_events != expected_events(negative_case.registers[0])
            if not detected:
                raise AssertionError(f"negative control was not detected: {symbol}")
            negative_results.append({"address": hex(address), "name": symbol,
                                     "detected": True, "reason": reason or "write trace differs"})

    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("candidate source changed while running")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True).stdout.splitlines()[0]
    report = {
        "schema": 1,
        "passed": all(item["passed"] for item in function_results + fault_results)
        and all(item["detected"] for item in negative_results),
        "reference_sha256": pinned.game_info["code_sha256"],
        "source_sha256": source_hash,
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler": compiler,
        "seed": seed,
        "samples_per_function": samples,
        "functions": function_results,
        "function_comparisons": total_comparisons,
        "direct_caller_windows": [],
        "caller_review": "No direct ARM BL caller was found by the scaffold scan; no caller windows are claimed or pinned.",
        "ordered_write_fault_cases": fault_results,
        "negative_controls": negative_results,
        "contract": "aligned ordinary RAM at r0; ordered STR [r0], STRB [r0+4], STR [r0+8]=r0+8, STR [r0+0x10], STR [r0+0x0c]=r0+8; return r0; preserve observed NZCV",
        "limitations": [
            "No direct ARM BL caller was identified; indirect references/callback uses were not inferred or executed",
            "Aligned ordinary RAM only; unaligned accesses, MMIO, concurrency and DMA observers are excluded",
            "There are no source reads, so source/destination overlap has no load-alias case; only ordered destination stores are tested",
            "A mapped-page-boundary fault checks the observed partial-write prefix, not every memory-fault class or hardware bus behavior",
            "Bounded differential evidence is not a formal equivalence proof or whole-game validation",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/self-pointer-initializers-seed20261024")
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    try:
        report = run(args.code, args.output, args.samples, args.seed)
    except (RuntimeError, ValueError, OSError, AssertionError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    print(f"Self-pointer initializer experiment {'PASS' if report['passed'] else 'FAIL'}; "
          f"report: {args.output / 'report.json'}")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
