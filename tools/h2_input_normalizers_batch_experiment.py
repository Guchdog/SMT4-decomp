#!/usr/bin/env python3
"""Three-slot integration differential for the H2 sample normalizers."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import h2_input_normalizer_branch0_experiment as branch0
from tools import h2_input_normalizer_branch1_experiment as branch1
from tools import h2_input_normalizer_branch2_experiment as branch2
from tools import h2_11c5ec_experiment as reader
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SLOTS = (
    (branch0.ADDRESS, branch0.SLOT_SIZE, "selector0", branch0),
    (branch1.ADDRESS, branch1.SLOT_SIZE, "selector1", branch1),
    (branch2.ADDRESS, branch2.SLOT_SIZE, "selector2", branch2),
)
DISPATCH_CALLS = ((0x00128678, branch0.ADDRESS),
                  (0x00128698, branch1.ADDRESS),
                  (0x00128658, branch2.ADDRESS))
CALIBRATION_OFFSETS = {0: (0x0C, 0x12), 1: (0x0E, 0x14), 2: (0x10, 0x16)}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def call_target(image: bytes, site: int) -> tuple[int, int]:
    word = struct.unpack_from("<I", image, site - reader.CODE_BASE)[0]
    if word & 0xFF000000 != 0xEB000000:
        raise ValueError(f"expected ARM BL at {site:#x}, got {word:#x}")
    disp = word & 0x00FFFFFF
    if disp & 0x00800000:
        disp -= 0x01000000
    return word, site + 8 + (disp << 2)


def compile_and_stage(original: bytes, out: Path) -> tuple[bytes, list, list, list]:
    out.mkdir(parents=True, exist_ok=True)
    sections = []
    summaries = []
    compiler_args = []
    for address, slot_size, label, module in SLOTS:
        body, relocations, args = module.compile_body(out / label)
        if len(body) > slot_size:
            raise ValueError(f"{label} body {len(body)} exceeds slot {slot_size}")
        if (slot_size - len(body)) % 4:
            raise ValueError(f"{label} slot tail is not ARM-word aligned")
        # Compile-body adapters have already resolved each declared call
        # relocation to its original even ARM target; selector 2 has none.
        if any(row.get("entry_bit0") != 0 for row in relocations):
            raise ValueError(f"{label} has a non-ARM relocation target")
        payload = body + struct.pack("<I", 0xE320F000) * ((slot_size - len(body)) // 4)
        sections.append((address - reader.CODE_BASE, payload))
        compiler_args.extend(args)
        summaries.append({"label": label, "address": hex(address),
                          "slot_bytes": slot_size, "body_bytes": len(body),
                          "body_sha256": sha(body), "relocations": relocations})

    staged = apply_ips(original, encode_ips(sections, len(original)))
    for address, slot_size, _label, _module in SLOTS:
        start = address - reader.CODE_BASE
        if staged[start:start + slot_size] == original[start:start + slot_size]:
            raise AssertionError(f"{address:#x} slot unexpectedly unchanged")
    starts = sorted((address - reader.CODE_BASE, address - reader.CODE_BASE + size)
                    for address, size, _label, _module in SLOTS)
    cursor = 0
    for start, end in starts:
        if original[cursor:start] != staged[cursor:start]:
            raise AssertionError("staged image changed bytes outside the three slots")
        cursor = end
    if original[cursor:] != staged[cursor:]:
        raise AssertionError("staged image changed bytes after the final slot")
    for site, expected in DISPATCH_CALLS:
        word, target = call_target(original, site)
        if target != expected or target & 1:
            raise ValueError(f"dispatcher call {site:#x} targets {target:#x}, expected even {expected:#x}")
        summaries.append({"dispatch_site": hex(site), "word": hex(word),
                          "target": hex(target), "target_bit0": target & 1})
    (out / "staged-image.bin").write_bytes(staged)
    (out / "three-slot.ips").write_bytes(encode_ips(sections, len(original)))
    return staged, summaries, compiler_args, sections


def make_caller_case(index: int, seed: int, selector: int,
                     x: int, y: int, calibration_a: int,
                     calibration_b: int, count: int = 1) -> dict:
    case = reader.make_case(index, 0, count, selector, 0, 0, 1, seed)
    context = bytearray(case["context_bytes"])
    a_offset, b_offset = CALIBRATION_OFFSETS[selector]
    struct.pack_into("<h", context, a_offset, calibration_a)
    struct.pack_into("<h", context, b_offset, calibration_b)
    case["context_bytes"] = bytes(context)
    record = list(case["record"])
    record[3], record[4] = x, y
    case["record"] = tuple(record)
    return case


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261112)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise SystemExit("pinned code.bin hash mismatch")

    staged, slots, compiler_args, sections = compile_and_stage(
        original, args.out / "compile")
    ips = encode_ips(sections, len(original))
    if apply_ips(original, ips) != staged:
        raise AssertionError("three-slot IPS replay failed")
    offset = min(address for address, _size, _label, _module in SLOTS) - reader.CODE_BASE
    ranges = sorted((address - reader.CODE_BASE,
                     address - reader.CODE_BASE + size)
                    for address, size, _label, _module in SLOTS)
    only_slots = original[:ranges[0][0]] == staged[:ranges[0][0]]
    only_slots &= all(original[ranges[i][1]:ranges[i+1][0]] ==
                      staged[ranges[i][1]:ranges[i+1][0]]
                      for i in range(len(ranges) - 1))
    only_slots &= original[ranges[-1][1]:] == staged[ranges[-1][1]:]
    if not only_slots:
        raise AssertionError("multi-slot patch changed bytes outside declared slots")

    samples = ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1),
               (39, 0), (40, 0), (41, 0), (-40, 0),
               (0, 39), (0, 40), (0, 41), (0, -40),
               (24, 32), (-24, 32), (24, -32), (-24, -32),
               (48, 64), (80, 0), (100, 100), (32767, -32768),
               (-32768, 32767))
    calibrations = {
        0: ((40, 145), (0, 145), (-32768, 32767)),
        1: ((40, 145), (80, 40), (-32768, 32767)),
        2: ((40, 145), (36, 36), (-32768, 32767)),
    }
    cases = []
    case_index = 0
    for seed in (args.seed, args.seed ^ 0x76E291):
        for selector in (0, 1, 2):
            for calibration_a, calibration_b in calibrations[selector]:
                for x, y in samples:
                    cases.append(make_caller_case(case_index, seed, selector,
                                                  x, y, calibration_a,
                                                  calibration_b))
                    case_index += 1
    # Include parent early-return/count gates and selector-out-of-range control
    # cases alongside all three child selector paths.
    for seed in (args.seed, args.seed ^ 0x76E291):
        for i, (count, selector) in enumerate(((0, 0), (-1, 1), (1, 3))):
            cases.append(make_caller_case(case_index, seed, selector if selector < 3 else 2,
                                          100, -100, 40, 145, count))
            if selector == 3:
                cases[-1]["selector"] = 3
                raw = bytearray(cases[-1]["context_bytes"])
                struct.pack_into("<B", raw, 0x18, 3)
                cases[-1]["context_bytes"] = bytes(raw)
            case_index += 1

    mismatches = []
    for i, case in enumerate(cases):
        reference = reader.run_one(original, case, True)
        candidate = reader.run_one(staged, case, True)
        if reference != candidate:
            mismatches.append({"case": i, "selector": case["selector"],
                               "count": case["count"], "record": case["record"],
                               "original": reference, "candidate": candidate})

    consumer_obj = args.out / "affected-tus" / "leaf_batch29_a.o"
    consumer_obj.parent.mkdir(parents=True, exist_ok=True)
    consumer_compile = compile_tu_armv6k(ROOT / "src/engine/leaf_batch29_a.cpp",
                                         consumer_obj, ROOT)
    if consumer_compile.returncode:
        raise RuntimeError(consumer_compile.stderr or "consumer TU compile failed")

    report = {
        "image_sha256": sha(original), "staged_image_sha256": sha(staged),
        "ips_sha256": sha(ips), "seed": args.seed,
        "slot_and_callsite_audit": slots, "compiled_slots": slots[:3],
        "caller_cases": len(cases), "caller_mismatches": mismatches,
        "all_selector_counts": {str(selector): sum(c["selector"] == selector and c["count"] > 0 for c in cases)
                                 for selector in (0, 1, 2)},
        "ips_replay": apply_ips(original, ips) == staged,
        "only_three_declared_slots_changed": only_slots,
        "compiler_args": compiler_args + list(consumer_compile.args),
        "consumer_tu_returncode": consumer_compile.returncode,
        "fixture_sha256": sha(json.dumps(cases, sort_keys=True, separators=(",", ":"),
                                          default=lambda x: x.hex()).encode()),
        "scope": "original 0x001078D8 reader and 0x00128610 dispatcher, controlled 0x0012A758 ring-reader seam, three production selector normalizers staged together",
        "limits": ["valid disjoint synthetic ordinary RAM only",
                   "FPSCR exception-flag parity is not claimed",
                   "physical input provenance, cadence and whole-title runtime are unverified"]
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"caller_cases": len(cases),
                      "caller_mismatches": len(mismatches),
                      "selector_counts": report["all_selector_counts"],
                      "body_bytes": {row["label"]: row.get("body_bytes")
                                     for row in slots if "label" in row},
                      "ips_replay": report["ips_replay"],
                      "only_three_declared_slots_changed": only_slots,
                      "consumer_tu_returncode": consumer_compile.returncode}, indent=2))
    return 0 if not mismatches and report["ips_replay"] and only_slots else 1


if __name__ == "__main__":
    raise SystemExit(main())
