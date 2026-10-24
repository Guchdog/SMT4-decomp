#!/usr/bin/env python3
"""Two-seed bounded differential experiment for 0x003E8BA0."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
from tools.semantic_experiment import DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference
from tools.semantic_experiment_support import compile_candidate_symbols, load_pinned_reference

ADDRESS = 0x003E8BA0
SIZE = 88
SYMBOL = "candidate_003e8ba0"
NEGATIVE = "negative_wrong_first_lane_003e8ba0"
SEEDS = (20261024, 20261025)
EXPECTED_CODE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
EXPECTED_BYTES = bytes.fromhex(
    "080082e204c0b2e50130a0e30c30d3e10030900500308105"
    "00c092e50230a0e30c30d3e1043090050430810500c092e5"
    "0430a0e30c30d3e10830900508308105003092e50820a0e3"
    "0320d2e10c0090050c0081051eff2fe1"
)


def _direct_bl_callers(image: bytes, target: int) -> list[int]:
    refs = []
    for offset in range(0, len(image) - 3, 4):
        word = struct.unpack_from("<I", image, offset)[0]
        if word & 0x0F000000 != 0x0B000000 or word >> 28 == 0xF:
            continue
        displacement = (word & 0x00FFFFFF) << 2
        if displacement & (1 << 25):
            displacement -= 1 << 26
        if (TEXT + offset + 8 + displacement) & 0xFFFFFFFF == target:
            refs.append(TEXT + offset)
    return refs


def verify_reference(reference) -> dict:
    image = reference.image
    if hashlib.sha256(image).hexdigest() != EXPECTED_CODE_SHA256:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    row = next((item for item in reference.ledger
                if int(item["address"], 16) == ADDRESS), None)
    if row is None or row["status"].strip() != "matching" or int(row["size"]) != SIZE:
        raise ValueError("ledger entry missing or changed at 0x003E8BA0")
    raw = image[ADDRESS - TEXT:ADDRESS - TEXT + SIZE]
    if raw != EXPECTED_BYTES:
        raise ValueError("function bytes changed at 0x003E8BA0")
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoded = [(ins.mnemonic.lower(), ins.op_str.lower()) for ins in decoder.disasm(raw, ADDRESS)]
    if not decoded or decoded[-1] != ("bx", "lr"):
        raise ValueError("unexpected function boundary at 0x003E8BA0")
    refs = _direct_bl_callers(image, ADDRESS)
    adjacent_refs = _direct_bl_callers(image, 0x003E8B44)
    return {
        "code_sha256": EXPECTED_CODE_SHA256,
        "address": hex(ADDRESS),
        "size": SIZE,
        "function_sha256": hashlib.sha256(raw).hexdigest(),
        "ledger_name": row["name"],
        "direct_bl_callers": [hex(site) for site in refs],
        "adjacent_progress_writer": {
            "address": "0x003e8b44",
            "direct_bl_callers": [hex(site) for site in adjacent_refs],
            "relationship": "adjacent ledger entry only; no call/data-flow relationship inferred",
        },
        "instructions": [f"{mnemonic} {operands}".strip() for mnemonic, operands in decoded],
    }


def make_cases(seed: int, samples: int = 128):
    if samples < 0:
        raise ValueError("samples must be non-negative")
    rng = random.Random(seed ^ ADDRESS)
    masks = (0, 1, 2, 4, 8, 3, 5, 10, 15, 0xFFFFFFF0)
    for index in range(len(masks) + samples):
        data = bytearray(rng.randbytes(DATA_SIZE))
        source = DATA + 0x200 + (index % 8) * 4
        destination = DATA + 0x700 + (index % 8) * 4
        mask = masks[index] if index < len(masks) else rng.getrandbits(32)
        struct.pack_into("<I", data, source - DATA + 4, mask)
        for lane in range(4):
            struct.pack_into("<I", data, source - DATA + 8 + lane * 4,
                             rng.getrandbits(32))
        registers = [rng.getrandbits(32) for _ in range(13)]
        registers[1], registers[2] = destination, source
        yield Case(f"ordinary-mask-{index}-{mask:08x}", tuple(registers), bytes(data),
                   rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)

    # The first write aliases the mask; subsequent per-lane mask reads must
    # observe that changed value, matching the original's repeated LDRs.
    data = bytearray(rng.randbytes(DATA_SIZE))
    source = DATA + 0x300
    destination = source + 4
    struct.pack_into("<I", data, source - DATA + 4, 1)
    struct.pack_into("<IIII", data, source - DATA + 8, 0, 0x22222222,
                     0x33333333, 0x44444444)
    registers = [rng.getrandbits(32) for _ in range(13)]
    registers[1], registers[2] = destination, source
    yield Case("destination-overwrites-mask", tuple(registers), bytes(data),
               rng.randbytes(STACK_SIZE), 0xA0000000)


def _fault_cases(seed: int):
    rng = random.Random(seed ^ ADDRESS ^ 0xF017)
    for label, source_offset in (("first-lane-read-fault", DATA_SIZE - 8),
                                 ("later-lane-read-fault-after-write", DATA_SIZE - 12)):
        data = bytearray(rng.randbytes(DATA_SIZE))
        source = DATA + source_offset
        destination = DATA + 0x300
        struct.pack_into("<I", data, source - DATA + 4, 1 if label.startswith("first") else 3)
        if label.startswith("later"):
            struct.pack_into("<I", data, source - DATA + 8, 0xAABBCCDD)
        registers = [rng.getrandbits(32) for _ in range(13)]
        registers[1], registers[2] = destination, source
        yield Case(label, tuple(registers), bytes(data), rng.randbytes(STACK_SIZE), 0x60000000)


def run(code_path: Path, output: Path, seed: int = SEEDS[0], samples: int = 128) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    reference = verify_reference(pinned)
    source_file = ROOT / "experiments/semantic_equivalence/conditional_mask_copy_003e8ba0.cpp"
    compiled = compile_candidate_symbols(source_file, output / "candidate.o", ROOT,
                                         {SYMBOL, NEGATIVE})
    original = Runner(pinned.image, ADDRESS)
    candidate = Runner(pinned.image, ADDRESS, compiled[SYMBOL])
    results = []
    for case in make_cases(seed, samples):
        expected, actual = original.run(case), candidate.run(case)
        reason = difference(expected, actual, returns_value=True)
        results.append({"case": case.label, "passed": reason is None, "difference": reason})
        if reason:
            break

    control_case = next(case for case in make_cases(seed, 0)
                        if case.label.startswith("ordinary-mask-1-"))
    negative = Runner(pinned.image, ADDRESS, compiled[NEGATIVE]).run(control_case)
    baseline = original.run(control_case)
    control_detected = (baseline.data != negative.data)

    fault_results = []
    for case in _fault_cases(seed):
        expected, actual = original.run(case), candidate.run(case)
        same = (expected.fault is not None and actual.fault is not None
                and expected.fault == actual.fault
                and expected.result == actual.result
                and expected.preserved == actual.preserved
                and expected.data == actual.data
                and expected.reads == actual.reads and expected.writes == actual.writes)
        fault_results.append({"case": case.label, "faults_match": same,
                              "original_fault": expected.fault,
                              "candidate_fault": actual.fault,
                              "partial_memory_match": expected.data == actual.data})

    report = {
        "experiment": "conditional_mask_copy_003e8ba0",
        "seed": seed,
        "comparisons": len(results),
        "functions": [{"address": hex(ADDRESS), "original_bytes": SIZE,
                       "candidate_bytes": len(compiled[SYMBOL]),
                       "passed": all(item["passed"] for item in results),
                       "failure": next((item for item in results if not item["passed"]), None)}],
        "negative_control": {"name": NEGATIVE, "detected": control_detected},
        "fault_probes": fault_results,
        "reference": reference,
        "limitations": [
            "Tests aligned ordinary RAM only; arbitrary invalid pointers, MMIO, and whole-game behavior are not claimed.",
            "Differential runner compares final memory and read/write byte footprints, not temporal bus-event order.",
            "The ARM direct-BL scan does not detect Thumb BL, indirect dispatch, or establish a caller contract.",
            "0x003E8B44 is the adjacent progress writer, but adjacency alone does not establish semantic or caller relation.",
        ],
    }
    report["passed"] = (all(item["passed"] for item in results) and control_detected
                         and all(item["faults_match"] for item in fault_results))
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--output", type=Path, default=Path("build/semantic-equivalence/conditional-mask-copy-003e8ba0"))
    parser.add_argument("--seed", type=int, default=SEEDS[0])
    parser.add_argument("--samples", type=int, default=128)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed, args.samples)
    print(json.dumps({"passed": report["passed"], "seed": report["seed"],
                      "comparisons": report["comparisons"], "output": str(args.output)}))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
