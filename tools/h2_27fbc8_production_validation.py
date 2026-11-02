"""Build and differentially validate the production 0x0027FBC8 slot image."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips
from tools.h4_axis_reader_experiment import audit_cases, observable, run

IMAGE_PATH = ROOT / "extracted/exefs/code.bin"
EXPERIMENTAL = ROOT / "experiments/semantic_equivalence/h4_axis_reader_candidate.cpp"
PRODUCTION = ROOT / "src/engine/leaf_batch41_a.cpp"
LEDGER = ROOT / "config/functions.csv"
ADDRESS = 0x0027FBC8
CALLER = 0x001FA948
HELPER = 0x0019FE4C
TEXT_BASE = 0x00100000
SPAN = 320
NOP = struct.pack("<I", 0xE320F000)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ledger_address(name: str) -> int:
    with LEDGER.open(newline="", encoding="utf-8") as stream:
        rows = [row for row in csv.DictReader(stream) if row["name"] == name]
    if len(rows) != 1:
        raise AssertionError(f"expected one ledger row for {name}, found {len(rows)}")
    return int(rows[0]["address"], 0)


def link_at_vma(body: bytes, relocations, entry: int) -> tuple[bytes, list[dict]]:
    fixed = bytearray(body)
    linked = []
    for reloc in relocations:
        target = ledger_address(reloc.symbol_name)
        if (reloc.symbol_name != "func_0019fe4c" or target != HELPER
                or target & 1 or target & 2 or reloc.relocation_type != 28
                or reloc.explicit_addend is not None or reloc.offset & 3
                or reloc.offset + 4 > len(fixed)):
            raise AssertionError(f"unsupported or unexpected relocation: {reloc}")
        instruction = struct.unpack_from("<I", fixed, reloc.offset)[0]
        if instruction & 0x0F000000 != 0x0B000000:
            raise AssertionError(f"relocation is not an ARM BL: {instruction:#010x}")
        site = entry + reloc.offset
        displacement = target - (site + 8)
        if displacement & 3 or not -(1 << 25) <= displacement < (1 << 25):
            raise AssertionError("ARM BL target is unaligned or out of range")
        resolved = (instruction & 0xFF000000) | ((displacement >> 2) & 0x00FFFFFF)
        struct.pack_into("<I", fixed, reloc.offset, resolved)
        linked.append({"site": hex(site), "instruction": hex(resolved),
                       "target": hex(target), "type": reloc.relocation_type})
    if len(linked) != 2:
        raise AssertionError(f"expected two deadzone calls, found {len(linked)}")
    return bytes(fixed), linked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--seed", type=int, default=20261102)
    args = parser.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=False)

    image = IMAGE_PATH.read_bytes()
    if sha(image) != "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558":
        raise AssertionError("reference image hash changed")
    experiment_object = out / "experimental.o"
    production_object = out / "production.o"
    for source, obj in ((EXPERIMENTAL, experiment_object), (PRODUCTION, production_object)):
        result = compile_tu_armv6k(source, obj, ROOT)
        if result.returncode:
            raise RuntimeError(result.stderr)
    experiment_body, experiment_relocs = extract_elf_functions_detailed(experiment_object)[
        "h4_axis_reader_candidate"]
    production_body, production_relocs = extract_elf_functions_detailed(production_object)[
        "script_vm_func_0027fbc8"]
    if experiment_body != production_body:
        raise AssertionError("production object body differs from the tested experimental candidate")
    experiment_calls = [(r.offset, r.relocation_type) for r in experiment_relocs]
    production_calls = [(r.offset, r.relocation_type) for r in production_relocs]
    if experiment_calls != production_calls or any(
            r.symbol_name != "func_0019fe4c" for r in production_relocs):
        raise AssertionError("production and experimental call relocation sites differ")
    body, calls = link_at_vma(production_body, production_relocs, ADDRESS)
    if len(body) > SPAN or (SPAN - len(body)) % 4:
        raise AssertionError("candidate does not fit the 320-byte ARM slot")
    slot = body + NOP * ((SPAN - len(body)) // 4)
    caller_word = struct.unpack_from("<I", image, CALLER - TEXT_BASE)[0]
    if caller_word & 0xFF000000 != 0xEB000000:
        raise AssertionError("observed camera callsite is not an unconditional ARM BL")
    caller_delta = (caller_word & 0x00FFFFFF) << 2
    if caller_delta & 0x02000000:
        caller_delta -= 0x04000000
    if CALLER + 8 + caller_delta != ADDRESS or ADDRESS & 1:
        raise AssertionError("camera caller does not target the even ARM function entry")

    offset = ADDRESS - TEXT_BASE
    staged = bytearray(image)
    staged[offset:offset + SPAN] = slot
    ips = encode_ips([(offset, slot)], len(image))
    if apply_ips(image, ips) != bytes(staged):
        raise AssertionError("slot IPS roundtrip failed")
    changed = [i for i, (old, new) in enumerate(zip(image, staged)) if old != new]
    if changed and (min(changed) < offset or max(changed) >= offset + SPAN):
        raise AssertionError("staged image changed bytes outside the target function slot")

    patched_image = bytes(staged)
    differences = []
    fault_cases = []
    for name, case in audit_cases(args.seed):
        original = run(ADDRESS, b"", case, extended=True, code_image=image)
        candidate = run(ADDRESS, b"", case, extended=True, code_image=patched_image)
        if original["fault"] or candidate["fault"]:
            fault_cases.append({"case": name, "same_fault_class": original["fault"] == candidate["fault"],
                                "original_fault": original["fault"], "candidate_fault": candidate["fault"],
                                "original_writes": original["data_writes"],
                                "candidate_writes": candidate["data_writes"]})
            continue
        if observable(original) != observable(candidate):
            differences.append({"case": name, "original": original, "candidate": candidate})

    report = {
        "status": "passed" if not differences and all(row["same_fault_class"] for row in fault_cases) else "failed",
        "seed": args.seed,
        "case_count": len(audit_cases(args.seed)),
        "difference_count": len(differences),
        "first_counterexample": differences[0] if differences else None,
        "fault_cases": fault_cases,
        "reference_sha256": sha(image),
        "experimental_source_sha256": sha(EXPERIMENTAL.read_bytes()),
        "production_source_sha256": sha(PRODUCTION.read_bytes()),
        "experimental_object_sha256": sha(experiment_object.read_bytes()),
        "production_object_sha256": sha(production_object.read_bytes()),
        "experimental_body_sha256": sha(experiment_body),
        "production_body_sha256": sha(production_body),
        "body_identical": experiment_body == production_body,
        "body_size": len(body),
        "slot_size": SPAN,
        "resolved_calls": calls,
        "camera_callsite": {"site": hex(CALLER), "word": hex(caller_word),
                             "target": hex(CALLER + 8 + caller_delta), "entry_even_arm": True},
        "staged_image_sha256": sha(patched_image),
        "ips_sha256": sha(ips),
        "ips_roundtrip": apply_ips(image, ips) == patched_image,
        "changed_bytes_within_slot": not changed or (min(changed) >= offset and max(changed) < offset + SPAN),
        "scope": "final-VMA differential over the axis reader's synthetic mapped-state cases; the two invalid output-pointer probes compare fault class and writes only; no H2 0x00254CA8 caller-domain or runtime claim",
    }
    (out / "staged-image.bin").write_bytes(patched_image)
    (out / "staged-slot.ips").write_bytes(ips)
    (out / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ("status", "case_count", "difference_count",
                                              "body_size", "staged_image_sha256", "ips_sha256")}, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
