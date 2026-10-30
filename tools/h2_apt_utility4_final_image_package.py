#!/usr/bin/env python3
"""Build an original-based IPS for the reviewed H2 image plus APT candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_apt_utility4_inplace_experiment import (
    ENTRY, ENTRY_SIZE, SOURCE, TEXT, WRAPPER, compose_in_place,
    resolve_call_relocation, sha256, verify_call_target,
    verify_original_callers, verify_original_dependencies,
)
from tools.h2_calc_code_patch import apply_ips, encode_ips
from tools.semantic_experiment_support import load_pinned_reference

BASE_H2_SHA256 = "acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446"
BASE_MANIFEST_SHA256 = "577c89588e031dc3eb1878d474cade85d5fe62f1f41c27816c4d7e92cd304d27"
EXPECTED_PATCHED_SHA256 = "788530a1b1ad7d4f361228cbd0e4b87885b37606a8f3485c52e5390ae3223179"


def contiguous_records(original: bytes, final: bytes) -> list[tuple[int, bytes]]:
    if len(original) != len(final):
        raise ValueError("image length changed")
    records = []
    index = 0
    while index < len(original):
        if original[index] == final[index]:
            index += 1
            continue
        start = index
        index += 1
        while index < len(original) and original[index] != final[index]:
            index += 1
        records.append((start, final[start:index]))
    return records


def delta_is_authorized(before: bytes, after: bytes,
                        ranges: list[tuple[int, int]]) -> bool:
    if len(before) != len(after):
        return False
    ordered = sorted(ranges)
    return all(before[index] == after[index] or any(start <= index < end
                                                     for start, end in ordered)
               for index in range(len(before)))


def overlaps(start: int, end: int, other_ranges: list[tuple[int, int]]) -> bool:
    return any(start < other_end and end > other_start
               for other_start, other_end in other_ranges)


def build_package(code_path: Path, base_image_path: Path,
                  base_manifest_path: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    base_image = base_image_path.read_bytes()
    manifest_bytes = base_manifest_path.read_bytes()
    base_manifest = json.loads(manifest_bytes)
    if sha256(base_image) != BASE_H2_SHA256 or sha256(manifest_bytes) != BASE_MANIFEST_SHA256:
        raise ValueError("reviewed H2 image or manifest identity mismatch")
    if base_manifest.get("patched_sha256") != BASE_H2_SHA256:
        raise ValueError("base manifest does not identify the selected H2 image")
    if len(base_image) != len(pinned.image):
        raise ValueError("base image length differs from pinned original")
    verify_original_callers(base_image, pinned.image)
    verify_original_dependencies(base_image, pinned.image)

    entry_offset = ENTRY - TEXT
    if base_image[entry_offset:entry_offset + ENTRY_SIZE] != pinned.image[entry_offset:entry_offset + ENTRY_SIZE]:
        raise ValueError("base H2 image already modifies the APT entry")
    base_ranges = []
    for row in base_manifest["ips_records"]:
        start = int(row["offset"], 16)
        end = start + row["length"]
        if sha256(base_image[start:end]) != row["sha256"]:
            raise ValueError(f"base manifest record mismatch at {start:#x}")
        base_ranges.append((start, end))
    candidate_start = entry_offset
    candidate_end = candidate_start + ENTRY_SIZE
    if overlaps(candidate_start, candidate_end, base_ranges):
        raise ValueError("candidate entry overlaps a declared H2 patch record")

    source_hash = sha256(SOURCE.read_bytes())
    object_path = output / "candidate.o"
    build = compile_tu_armv6k(SOURCE, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    body, relocations = extract_elf_functions_detailed(object_path)["candidate_002c0efc"]
    linked_body, applied = resolve_call_relocation(body, relocations, ENTRY)
    verify_call_target(linked_body, relocations[0], ENTRY, WRAPPER)
    if len(linked_body) != 40:
        raise ValueError(f"candidate body size changed from reviewed 40 bytes: {len(linked_body)}")
    candidate_image = compose_in_place(base_image, linked_body)
    allowed = base_ranges + [(candidate_start, candidate_start + len(linked_body))]
    if not delta_is_authorized(pinned.image, base_image, base_ranges):
        raise ValueError("selected H2 base contains changes outside its manifest records")
    if not delta_is_authorized(pinned.image, candidate_image, allowed):
        raise ValueError("final candidate image contains an unauthorized original-relative byte")

    records = contiguous_records(pinned.image, candidate_image)
    ips = encode_ips(records, len(pinned.image))
    if apply_ips(pinned.image, ips) != candidate_image:
        raise ValueError("original-based IPS round trip failed")
    expected_image_sha = sha256(candidate_image)
    if expected_image_sha != EXPECTED_PATCHED_SHA256:
        raise ValueError("composed candidate hash differs from caller/differential evidence")

    image_path = output / "code.h2-apt-utility4-inplace.bin"
    ips_path = output / "code.h2-apt-utility4-inplace.ips"
    image_path.write_bytes(candidate_image)
    ips_path.write_bytes(ips)
    added_changes = sum(1 for i, (a, b) in enumerate(zip(base_image, candidate_image)) if a != b)
    report = {
        "kind": "experimental offline H2 image; not runtime-verified or promoted",
        "original_sha256": sha256(pinned.image),
        "base_h2_image_sha256": sha256(base_image),
        "base_h2_manifest_sha256": sha256(manifest_bytes),
        "candidate_source_sha256": source_hash,
        "candidate_object_sha256": sha256(object_path.read_bytes()),
        "candidate_body_sha256": sha256(linked_body),
        "candidate_body_hex": linked_body.hex(),
        "candidate_entry_vma": hex(ENTRY),
        "candidate_entry_size": ENTRY_SIZE,
        "candidate_body_size": len(linked_body),
        "candidate_call_relocations": applied,
        "final_image_sha256": expected_image_sha,
        "ips_sha256": sha256(ips),
        "ips_records": [{"offset": hex(offset), "length": len(payload),
                         "sha256": sha256(payload)} for offset, payload in records],
        "ips_record_count": len(records),
        "changed_bytes_added_to_base": added_changes,
        "authorized_ranges": [{"start": hex(start), "end": hex(end), "kind": "reviewed H2 base"}
                              for start, end in base_ranges]
                             + [{"start": hex(candidate_start),
                                 "end": hex(candidate_start + len(linked_body)),
                                 "kind": "in-place APT candidate"}],
        "round_trip_passed": True,
        "output_image": image_path.name,
        "output_ips": ips_path.name,
        "compile_command": build.args,
        "limits": ["Original wrapper and APT service behavior remain dependencies.",
                   "Offline differential and caller evidence use controlled wrapper/helper hooks.",
                   "No emulator runtime, Thumb or indirect caller validation is included.",
                   "This package does not close H2 or change the source ledger."],
    }
    (output / "manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", type=Path, required=True)
    parser.add_argument("--base-image", type=Path, required=True)
    parser.add_argument("--base-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_package(args.code, args.base_image, args.base_manifest, args.output)
    print(json.dumps({"image_sha256": result["final_image_sha256"],
                      "ips_sha256": result["ips_sha256"],
                      "records": result["ips_record_count"],
                      "round_trip": result["round_trip_passed"]}))
