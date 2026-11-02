"""Integrate the production 0x002C615C C++ divmod entry and compare real callers."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import h1_interpolation_divide_experiment as direct
from tools import h1_preview_full_composition_experiment as preview
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips, sha256
from tools.semantic_experiment import arm_branch

IMAGE = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch32_c.cpp"
SYMBOL = "ui_func_002c615c"
ENTRY = 0x002C615C
SPAN = 556
CAVE = 0x003FE624
CAVE_CAPACITY = 0x9DC
TEXT_BASE = 0x00100000
TEXT_END = 0x003FE624
TEXT_PAD_END = 0x003FF000
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def branch_target(address: int, instruction: int) -> int:
    if instruction >> 28 != 0xE or instruction & 0x0E000000 != 0x0A000000:
        raise ValueError("entry redirect is not an unconditional ARM B")
    if instruction & 0x01000000:
        raise ValueError("entry redirect unexpectedly links")
    displacement = (instruction & 0x00FFFFFF) << 2
    if displacement & 0x02000000:
        displacement -= 0x04000000
    return address + 8 + displacement


def interior_entry_census(image: bytes) -> dict:
    end = ENTRY + SPAN
    branches, pointers = [], []
    for off in range(0, len(image) - 3, 4):
        word = struct.unpack_from("<I", image, off)[0]
        source = TEXT_BASE + off
        if word & 0x0E000000 == 0x0A000000 and word >> 28 != 0xF:
            immediate = word & 0x00FFFFFF
            if immediate & 0x00800000:
                immediate -= 0x01000000
            target = source + 8 + (immediate << 2)
            if ENTRY < target < end and not ENTRY <= source < end:
                branches.append((source, target, word))
        if word & 3 == 0 and ENTRY < word < end and not ENTRY <= source < end:
            pointers.append((source, word))
    # These six direct entries are the pinned 0x002C6C10 fast-path shim. Keep
    # the old divide body in place so its branch targets remain executable.
    expected = {
        0x002C6190, 0x002C61B8, 0x002C61E8,
        0x002C621C, 0x002C6240, 0x002C6264,
    }
    found = {target for _source, target, _word in branches}
    if found != expected or pointers:
        raise ValueError(f"unexpected interior-entry census: {branches!r}, {pointers!r}")
    return {
        "external_direct_branch_targets": [hex(x) for x in sorted(found)],
        "branch_sources": [
            {"source": hex(source), "target": hex(target), "instruction": hex(word)}
            for source, target, word in branches
        ],
        "external_aligned_absolute_pointers": [],
        "preservation_policy": "redirect only the original entry; retain all 556 original bytes so fast-path interior entries remain valid",
    }


def build_images(out: Path, image: bytes) -> tuple[bytes, bytes, dict]:
    base = bytearray(image)
    cave_off = CAVE - TEXT_BASE
    if CAVE != TEXT_END or CAVE + CAVE_CAPACITY != TEXT_PAD_END:
        raise ValueError("pinned executable text-tail layout changed")
    if any(base[cave_off:cave_off + CAVE_CAPACITY]):
        raise ValueError("reviewed executable cave is not zero-filled")

    source_hash = sha(SOURCE.read_bytes())
    object_path = out / "production_leaf_batch32_c.o"
    result = compile_tu_armv6k(SOURCE, object_path, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "production division TU failed to compile")
    functions = extract_elf_functions_detailed(object_path)
    if SYMBOL not in functions:
        raise ValueError("production division symbol was not found")
    body, relocations = functions[SYMBOL]
    if not body or len(body) > CAVE_CAPACITY or len(body) & 3 or relocations:
        raise ValueError(f"unsupported production body layout: {len(body)} bytes, {relocations}")
    if sha(SOURCE.read_bytes()) != source_hash:
        raise RuntimeError("production source changed during compilation")

    entry_branch = arm_branch(ENTRY, CAVE)
    target = branch_target(ENTRY, struct.unpack("<I", entry_branch)[0])
    if target != CAVE or target & 1:
        raise ValueError("ARM interworking/branch-target check failed")
    final = bytearray(image)
    entry_off = ENTRY - TEXT_BASE
    final[entry_off:entry_off + 4] = entry_branch
    final[cave_off:cave_off + len(body)] = body
    ips = encode_ips([(entry_off, entry_branch), (cave_off, body)], len(image))
    if apply_ips(image, ips) != bytes(final):
        raise ValueError("IPS roundtrip did not reproduce the final image")
    return body, bytes(final), {
        "production_source_sha256": source_hash,
        "production_object_sha256": sha(object_path.read_bytes()),
        "body_sha256": sha(body),
        "body_bytes": len(body),
        "relocations": 0,
        "entry_branch": entry_branch.hex(),
        "branch_target": hex(target),
        "entry_file_offset": hex(entry_off),
        "cave_vma": hex(CAVE),
        "cave_file_offset": hex(cave_off),
        "ips_sha256": sha(ips),
        "ips_records": [
            {"offset": hex(offset), "length": len(data), "sha256": sha(data)}
            for offset, data in ((entry_off, entry_branch), (cave_off, body))
        ],
        "interior_entry_audit": interior_entry_census(image),
    }


def compare_direct(a: dict, b: dict, label: str) -> dict:
    errors = []
    for key in ("r0", "r1", "fault", "pc", "preserved_after", "sp_after", "data"):
        if a[key] != b[key]:
            errors.append(f"{key} differs")
    if a["preserved_after"] != a["preserved_before"]:
        errors.append("original callee-saved state changed")
    if b["preserved_after"] != b["preserved_before"]:
        errors.append("candidate callee-saved state changed")
    if a["sp_after"] != a["sp_before"] or b["sp_after"] != b["sp_before"]:
        errors.append("SP not restored")
    return {"label": label, "passed": not errors, "errors": errors,
            "r0": hex(a["r0"]), "r1": hex(a["r1"]),
            "original_stack_changed": a["stack"] != bytes([0xCC]) * direct.STACK_SIZE,
            "candidate_stack_changed": b["stack"] != bytes([0xCC]) * direct.STACK_SIZE,
            "stack_residue_equal": a["stack"] == b["stack"],
            "stack_residue_compared": False}


def compare_preview(a: dict, b: dict, label: str) -> dict:
    errors = []
    for key in ("fault", "pc", "r0", "preserved_after", "d8_d15_after", "fpscr",
                "object_after_hex", "_data_snapshot", "caller_stack_hex"):
        if a[key] != b[key]:
            errors.append(f"{key} differs")
    if a["preserved_after"] != a["preserved_before"]:
        errors.append("original callee-saved state changed")
    if b["preserved_after"] != b["preserved_before"]:
        errors.append("patched callee-saved state changed")
    original_calls, patched_calls = preview.call_names(a["calls"]), preview.call_names(b["calls"])
    if original_calls != patched_calls:
        errors.append("direct-callee trace/arguments differ")
    divide_calls = [call for call in b["calls"] if call["name"] == "divide"]
    if not divide_calls or any(int(call["args"][1], 16) == 0 for call in divide_calls):
        errors.append("real preview caller did not exercise positive-duration divide")
    return {"label": label, "passed": not errors, "errors": errors,
            "divide_calls": divide_calls, "call_count": len(b["calls"])}


def run(out: Path, seed: int, samples: int) -> dict:
    if out.exists():
        raise FileExistsError(f"refusing to reuse output directory: {out}")
    out.mkdir(parents=True)
    image = IMAGE.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise ValueError("pinned original code image hash mismatch")
    body, patched, build = build_images(out, image)
    (out / "code.production.bin").write_bytes(patched)
    # Reconstruct the same two-record IPS from the emitted final image.
    entry_branch = bytes.fromhex(build["entry_branch"])
    ips = encode_ips([(ENTRY - TEXT_BASE, entry_branch),
                      (CAVE - TEXT_BASE, body)], len(image))
    (out / "code.production.ips").write_bytes(ips)
    if sha(ips) != build["ips_sha256"] or apply_ips(image, ips) != patched:
        raise ValueError("serialized IPS identity/roundtrip mismatch")

    direct_cases = direct.cases(seed, samples)
    direct_rows = []
    for label, numerator, denominator in direct_cases:
        original = direct.Machine(image, None).run(numerator, denominator, None)
        candidate = direct.Machine(patched, None).run(numerator, denominator, None)
        row = compare_direct(original, candidate, label)
        direct_rows.append(row)
        if not row["passed"]:
            raise AssertionError(f"direct case failed: {row}")

    preview_rows = []
    helper_rows = [(1, 2, 3, 4, 8, 0)]
    preview_cases = [
        preview.case_data(
            "preview interpolation direction zero, original real callees",
            preview.fixture(helper_table=preview.HELPER_ROWS, progress=1, direction=0),
            helper_rows,
        ),
        preview.case_data(
            "preview interpolation direction one, original real callees",
            preview.fixture(helper_table=preview.HELPER_ROWS, progress=1, direction=1),
            helper_rows,
        ),
    ]
    for case in preview_cases:
        original = preview.Machine(image, None).run(case["data"], case["entry_ptr"])
        candidate = preview.Machine(patched, None).run(case["data"], case["entry_ptr"])
        row = compare_preview(original, candidate, case["name"])
        preview_rows.append(row)
        if not row["passed"]:
            raise AssertionError(f"preview caller case failed: {row}")

    # The entry points into the legacy interior are preserved by the trampoline.
    # A wrong cave target is a sensitivity control for the final-address patch.
    bad = bytearray(patched)
    bad[ENTRY - TEXT_BASE:ENTRY - TEXT_BASE + 4] = arm_branch(ENTRY, CAVE + 4)
    mutant = direct.Machine(bytes(bad), None).run(4096, 2, None)
    baseline = direct.Machine(image, None).run(4096, 2, None)
    negative = (mutant["fault"] is not None or mutant["r0"] != baseline["r0"] or
                mutant["r1"] != baseline["r1"])
    if not negative:
        raise AssertionError("wrong final-address target control escaped")

    report = {
        "schema": 1,
        "scope": "pinned original image plus production 0x002C615C trampoline; original legacy interior entries retained",
        "original_sha256": sha(image),
        "patched_sha256": sha(patched),
        "runner_sha256": sha(Path(__file__).read_bytes()),
        "production": build,
        "direct_cases": len(direct_rows),
        "direct_passed": sum(row["passed"] for row in direct_rows),
        "direct_first_mismatch": None,
        "zero_divisor_cases": sum(denominator == 0 for _label, _numerator, denominator in direct_cases),
        "direct_stack_residue_matches": sum(row["stack_residue_equal"] for row in direct_rows),
        "preview_caller_cases": preview_rows,
        "negative_control_detected": negative,
        "negative_control": "entry branch to candidate body +4",
        "runtime": "not_run",
        "limits": [
            "Caller composition executes the pinned original 0x002BF9F0 preview helper and all other pinned callees; fixtures are synthetic ordinary memory.",
            "The H2 0x0029F278 caller was not executed; its divide call and two-register result use remain supported by static contract only.",
            "Below-SP scratch bytes differ and are reported separately; invalid pointers, concurrency, MMIO, timing and runtime behavior are not established.",
            "The production C++ helper is placed in the standalone original-image code cave. The accumulated five-callback H2 patch allocates that shared tail and is not merged here.",
        ],
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261025)
    parser.add_argument("--samples", type=int, default=256)
    args = parser.parse_args()
    report = run(args.output, args.seed, args.samples)
    print(json.dumps({"direct": f"{report['direct_passed']}/{report['direct_cases']}",
                      "preview_callers": len(report["preview_caller_cases"]),
                      "negative_control_detected": report["negative_control_detected"],
                      "patched_sha256": report["patched_sha256"],
                      "report": str(args.output / "report.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
