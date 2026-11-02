"""Build and validate a Calc-plus-0x002892C0 H2 patch at final guest addresses."""
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

import tools.h2_2892c0_experiment as isolated
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import (
    apply_ips,
    build_experiment as build_calc,
    encode_ips,
    sha256,
)
from tools.semantic_experiment import arm_branch
import unicorn
from unicorn import arm_const as arm

IMAGE = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch16_c.cpp"
SYMBOL = "camp_func_002892c0"
ENTRY = 0x002892C0
CAVE = 0x003FEE64
SPAN = 124
BODY_LIMIT = 412
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
TEXT_BASE = 0x00100000
TEXT_END = 0x003FE624
TEXT_PAD_END = 0x003FF000


def decode_ips(patch: bytes) -> list[tuple[int, bytes]]:
    if not patch.startswith(b"PATCH"):
        raise ValueError("invalid IPS header")
    pos = 5
    rows = []
    while patch[pos:pos + 3] != b"EOF":
        if pos + 5 > len(patch):
            raise ValueError("truncated IPS record")
        off = int.from_bytes(patch[pos:pos + 3], "big")
        size = int.from_bytes(patch[pos + 3:pos + 5], "big")
        pos += 5
        if size == 0 or pos + size > len(patch):
            raise ValueError("unsupported or truncated IPS run-length record")
        rows.append((off, patch[pos:pos + size]))
        pos += size
    if pos + 3 != len(patch):
        raise ValueError("trailing data after IPS EOF")
    return rows


def branch_target(address: int, instruction: int) -> int:
    if instruction >> 28 != 0xE or instruction & 0x0E000000 != 0x0A000000:
        raise ValueError("entry redirect is not an unconditional ARM B")
    if instruction & 0x01000000:
        raise ValueError("entry redirect unexpectedly links")
    displacement = (instruction & 0x00FFFFFF) << 2
    if displacement & 0x02000000:
        displacement -= 0x04000000
    return address + 8 + displacement


def image_machine(image: bytes) -> unicorn.Uc:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
    uc.mem_map(TEXT_BASE, 0x400000)
    uc.mem_write(TEXT_BASE, image)
    uc.mem_map(isolated.OBJ, 0x10000)
    uc.mem_map(0x8000000, 0x100000)
    uc.mem_map(0x1000000, 0x10000)
    return uc


def make_cases() -> list[tuple[int, int, int, int, int]]:
    values = [0, 1, 2, 3, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF]
    cases = [
        (visible, count, start, 0xA55A5AA5, index)
        for count in values
        for index in values
        for start, visible in (
            (0, 0), (2, 1), (0xFFFFFFFF, 0x7FFFFFFF), (0x80000000, 0xFFFFFFFF)
        )
    ]
    rng = random.Random(2892)
    cases.extend(tuple(rng.getrandbits(32) for _ in range(5)) for _ in range(1024))
    return cases


def validate_pair(base_image: bytes, patched_image: bytes, out: Path) -> dict:
    old, new = image_machine(base_image), image_machine(patched_image)
    cases = make_cases()
    for i, (visible, count, start, end, index) in enumerate(cases):
        left = isolated.run(old, ENTRY, (visible, count, start, end), index)
        right = isolated.run(new, ENTRY, (visible, count, start, end), index)
        if left != right:
            raise AssertionError(f"final-address direct mismatch case {i}: {left!r} != {right!r}")
        if left["ret"] != 1 or left["entries"] != [(isolated.OBJ, index)]:
            raise AssertionError(f"unexpected direct ABI/result at case {i}")
    caller_count = 0
    for disabled in (0, 1, 0x80):
        for visible, count, start, end, index in cases[:120]:
            left = isolated.run(old, isolated.WRAPPER, (visible, count, start, end), index, disabled)
            right = isolated.run(new, isolated.WRAPPER, (visible, count, start, end), index, disabled)
            if left != right:
                raise AssertionError(f"final-address caller mismatch case {caller_count}")
            if len(left["entries"]) != (0 if disabled else 1):
                raise AssertionError("original wrapper helper-entry count changed")
            caller_count += 1

    bad = bytearray(patched_image)
    entry_off = ENTRY - TEXT_BASE
    bad[entry_off:entry_off + 4] = arm_branch(ENTRY, CAVE + 4)
    mutant = image_machine(bytes(bad))
    detected = False
    for visible, count, start, end, index in cases:
        left = isolated.run(old, ENTRY, (visible, count, start, end), index)
        right = isolated.run(mutant, ENTRY, (visible, count, start, end), index)
        if left != right:
            detected = True
            break
    if not detected:
        raise AssertionError("final-address wrong-target control escaped")

    report = {
        "base_calc_image_sha256": sha256(base_image),
        "patched_image_sha256": sha256(patched_image),
        "direct_cases": len(cases),
        "original_wrapper_cases": caller_count,
        "negative_control_detected": detected,
        "negative_control": "entry branch to candidate body + 4",
        "address": hex(ENTRY),
        "candidate_vma": hex(CAVE),
        "caller": "pinned original 0x0029EDFC on both images",
        "runtime": "not_run",
        "limits": [
            "The base image already contains the independently validated Calc-only H2 patch; this run isolates the helper delta over that base.",
            "Other TitleConfig callbacks, input timing, invalid pointers, concurrent access, MMIO, and whole-game behavior are not covered.",
        ],
    }
    (out / "final-address-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "build/agent-work/H2-semantic/h2-titleconfig-002892c0-integration/run002",
    )
    out = parser.parse_args().out_dir
    if not out.is_absolute():
        out = ROOT / out
    if out.exists():
        raise FileExistsError(f"refusing to reuse output directory: {out}")
    out.mkdir(parents=True)
    image = IMAGE.read_bytes()
    if sha256(image) != IMAGE_SHA:
        raise ValueError("pinned original code image hash mismatch")
    source_hash = sha256(SOURCE.read_bytes())
    calc_out = out / "calc-base"
    calc_report = build_calc(IMAGE, calc_out, seed=7, samples=32)
    if not calc_report["passed"]:
        raise RuntimeError("Calc-only base did not pass its frozen differential")
    base_image = (calc_out / "code.experimental.bin").read_bytes()

    obj_path = out / "leaf_batch16_c.o"
    build = compile_tu_armv6k(SOURCE, obj_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "production helper TU failed to compile")
    functions = extract_elf_functions_detailed(obj_path)
    if SYMBOL not in functions:
        raise ValueError("production helper symbol missing")
    body, relocations = functions[SYMBOL]
    if relocations:
        raise ValueError(f"production helper has unsupported relocations: {relocations}")
    if not body or len(body) > BODY_LIMIT or len(body) & 3:
        raise ValueError(f"helper body size/alignment is invalid: {len(body)}")
    if sha256(SOURCE.read_bytes()) != source_hash:
        raise RuntimeError("production source changed during build")

    cave_offset = CAVE - TEXT_BASE
    entry_offset = ENTRY - TEXT_BASE
    if CAVE & 3 or CAVE < TEXT_END or CAVE + len(body) > TEXT_PAD_END:
        raise ValueError("candidate is outside the reviewed aligned executable cave")
    if any(base_image[cave_offset:cave_offset + BODY_LIMIT]):
        raise ValueError("reserved helper cave region is not zero in Calc base image")
    entry_branch = arm_branch(ENTRY, CAVE)
    target = branch_target(ENTRY, struct.unpack("<I", entry_branch)[0])
    if target != CAVE or target & 1:
        raise ValueError("ARM interworking/branch-target check failed")

    patched = bytearray(base_image)
    patched[entry_offset:entry_offset + 4] = entry_branch
    patched[cave_offset:cave_offset + len(body)] = body
    records = decode_ips((calc_out / "code.ips").read_bytes())
    records.extend(((entry_offset, entry_branch), (cave_offset, body)))
    records.sort(key=lambda row: row[0])
    for (left_off, left_data), (right_off, _right_data) in zip(records, records[1:]):
        if left_off + len(left_data) > right_off:
            raise ValueError("combined patch records overlap")
    combined_ips = encode_ips(records, len(image))
    if apply_ips(image, combined_ips) != bytes(patched):
        raise ValueError("serialized combined IPS does not reproduce patched image")

    (out / "code.combined.bin").write_bytes(patched)
    (out / "code.combined.ips").write_bytes(combined_ips)
    report = validate_pair(base_image, bytes(patched), out)
    manifest = {
        "schema": 1,
        "scope": "Calc-only H2 base plus 0x002892C0 production C++ helper",
        "original_sha256": sha256(image),
        "calc_base_sha256": sha256(base_image),
        "combined_sha256": sha256(bytes(patched)),
        "combined_ips_sha256": sha256(combined_ips),
        "calc_base_ips_sha256": sha256((calc_out / "code.ips").read_bytes()),
        "production_source_sha256": source_hash,
        "production_object_sha256": sha256(obj_path.read_bytes()),
        "integration_runner_sha256": sha256(Path(__file__).read_bytes()),
        "helper_body_sha256": sha256(body),
        "helper_body_bytes": len(body),
        "helper_relocations": 0,
        "entry_vma": hex(ENTRY),
        "entry_file_offset": hex(entry_offset),
        "candidate_vma": hex(CAVE),
        "candidate_file_offset": hex(cave_offset),
        "candidate_reserved_bytes": BODY_LIMIT,
        "entry_branch": entry_branch.hex(),
        "branch_target": hex(target),
        "ips_records": [
            {"offset": hex(off), "length": len(data), "sha256": sha256(data)}
            for off, data in records
        ],
        "calc_base_cases_passed": calc_report["cases_passed"],
        "helper_direct_cases": report["direct_cases"],
        "helper_wrapper_cases": report["original_wrapper_cases"],
        "negative_control_detected": report["negative_control_detected"],
        "runtime": "not_run",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
