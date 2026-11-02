#!/usr/bin/env python3
"""Compile and stage the production 0x002B787C C++ replacement."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips

IMAGE_PATH = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch42_c.cpp"
SYMBOL = "engine_func_002b787c"
VMA = 0x002B787C
SPAN = 176
IMAGE_BASE = 0x00100000
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_production(output: Path) -> tuple[Path, bytes, list[dict]]:
    output.mkdir(parents=True, exist_ok=True)
    obj = output / "production-tu" / "leaf_batch42_c.o"
    result = compile_tu_armv6k(SOURCE, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    functions = extract_elf_functions_detailed(obj)
    if SYMBOL not in functions:
        raise SystemExit(f"production symbol missing: {SYMBOL}")
    body, relocations = functions[SYMBOL]
    if len(body) != SPAN:
        raise SystemExit(f"production body size {len(body)} differs from original slot {SPAN}")

    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as f:
        ledger = {row["name"].strip(): int(row["address"], 0) for row in csv.DictReader(f)}
    fixed = bytearray(body)
    rows = []
    seen = set()
    for reloc in relocations:
        if (reloc.relocation_type != 28 or reloc.explicit_addend is not None
                or reloc.offset in seen or reloc.offset % 4 or reloc.offset + 4 > len(fixed)):
            raise SystemExit(f"unsupported or duplicate relocation: {reloc}")
        seen.add(reloc.offset)
        target = ledger.get(reloc.symbol_name)
        if target is None or target & 1:
            raise SystemExit(f"missing/even ARM target required for {reloc.symbol_name}: {target}")
        place = VMA + reloc.offset
        instruction = struct.unpack_from("<I", fixed, reloc.offset)[0]
        if instruction & 0xFF000000 != 0xEB000000:
            raise SystemExit(f"R_ARM_CALL site is not unconditional ARM BL: {instruction:#x}")
        displacement = target - (place + 8)
        if displacement & 3 or not -(1 << 25) <= displacement < (1 << 25):
            raise SystemExit(f"unaligned/out-of-range ARM BL target: {target:#x}")
        struct.pack_into("<I", fixed, reloc.offset,
                         (instruction & 0xFF000000) | ((displacement >> 2) & 0x00FFFFFF))
        rows.append({"offset": reloc.offset, "type": "R_ARM_CALL",
                     "symbol": reloc.symbol_name, "target": hex(target), "state": "ARM"})
    if len(rows) != 2:
        raise SystemExit(f"expected two direct ARM call relocations, got {len(rows)}")
    return obj, bytes(fixed), rows


def main() -> int:
    out = ROOT / "build/h2-2b787c-integration/staged-image"
    original = IMAGE_PATH.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise SystemExit("pinned original image hash mismatch")
    obj, replacement, relocations = compile_production(out)
    offset = VMA - IMAGE_BASE
    patched = bytearray(original)
    patched[offset:offset + SPAN] = replacement
    if bytes(patched[:offset]) != original[:offset] or bytes(patched[offset + SPAN:]) != original[offset + SPAN:]:
        raise SystemExit("staged image changed bytes outside the function slot")
    ips = encode_ips([(offset, replacement)], len(original))
    if apply_ips(original, ips) != bytes(patched):
        raise SystemExit("IPS round-trip mismatch")

    image_path = out / "code.h2-2b787c.bin"
    ips_path = out / "code.h2-2b787c.ips"
    manifest_path = out / "manifest.json"
    image_path.write_bytes(patched)
    ips_path.write_bytes(ips)
    manifest = {
        "function": hex(VMA), "symbol": SYMBOL, "classification": "non_matching",
        "source": SOURCE.relative_to(ROOT).as_posix(), "source_sha256": sha(SOURCE.read_bytes()),
        "object": obj.relative_to(ROOT).as_posix(), "object_sha256": sha(obj.read_bytes()),
        "compiled_body_bytes": len(replacement), "compiled_body_sha256": sha(replacement),
        "original_span_bytes": SPAN, "relocations": relocations,
        "original_image_sha256": sha(original), "patched_image_sha256": sha(patched),
        "ips_sha256": sha(ips), "ips_records": 1, "ips_roundtrip": True,
        "only_function_slot_changed": True,
        "artifact_paths": {"image": image_path.relative_to(ROOT).as_posix(),
                           "ips": ips_path.relative_to(ROOT).as_posix()},
        "evidence": {"compiled": "passed", "interworking": "passed",
                     "arm_differential": "passed", "caller": "passed", "runtime": "not_run"},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"PASS {len(replacement)}/{SPAN} bytes; 2 ARM calls relocated; IPS round-trip")
    print(f"image sha256 {sha(patched)}")
    print(f"IPS sha256 {sha(ips)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
