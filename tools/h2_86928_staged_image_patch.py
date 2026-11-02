#!/usr/bin/env python3
"""Build a reproducible IPS and staged code image for H2 helper 0x00286928."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.h2_calc_code_patch import apply_ips, encode_ips

IMAGE = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch45_a.cpp"
SYMBOL = "engine_func_00286928"
VMA = 0x00286928
SPAN = 820
IMAGE_BASE = 0x00100000
ORIGINAL_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
ARM_NOP = struct.pack("<I", 0xE320F000)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_function(output: Path) -> tuple[Path, bytes, list[dict]]:
    output.mkdir(parents=True, exist_ok=True)
    build_dir = output / "production-tu"
    subprocess.run([sys.executable, str(ROOT / "tools/build_check.py"),
                    "--tu", str(SOURCE), "--out-dir", str(build_dir), "-j", "1"],
                   check=True, cwd=ROOT)
    obj = build_dir / "engine/leaf_batch45_a.o"
    functions = extract_elf_functions_detailed(obj)
    if SYMBOL not in functions:
        raise SystemExit(f"production symbol missing from {obj}: {SYMBOL}")
    body, relocations = functions[SYMBOL]
    if len(body) != 812 or len(body) > SPAN or (SPAN - len(body)) % 4:
        raise SystemExit(f"unexpected production body size {len(body)} for {SPAN}-byte slot")
    ledger = {row["name"]: int(row["address"], 0)
              for row in csv.DictReader((ROOT / "config/functions.csv").open(encoding="utf-8"))}
    fixed = bytearray(body)
    resolved = []
    seen = set()
    for reloc in relocations:
        if (reloc.relocation_type != 28 or reloc.explicit_addend is not None
                or reloc.offset in seen or reloc.offset % 4
                or reloc.offset + 4 > len(fixed)):
            raise SystemExit(f"unsupported/duplicate relocation: {reloc}")
        seen.add(reloc.offset)
        target = ledger.get(reloc.symbol_name)
        if target is None:
            raise SystemExit(f"call target missing from function ledger: {reloc.symbol_name}")
        if target & 1:
            raise SystemExit(f"R_ARM_CALL targets Thumb address {target:#x}: {reloc.symbol_name}")
        place = VMA + reloc.offset
        instruction = struct.unpack_from("<I", fixed, reloc.offset)[0]
        if instruction & 0xFF000000 != 0xEB000000:
            raise SystemExit(f"R_ARM_CALL site is not unconditional ARM BL: {instruction:#x}")
        displacement = target - (place + 8)
        if displacement & 3 or not -(1 << 25) <= displacement < (1 << 25):
            raise SystemExit(f"ARM BL target is unaligned/out of range: {target:#x}")
        struct.pack_into("<I", fixed, reloc.offset,
                         (instruction & 0xFF000000) | ((displacement >> 2) & 0x00FFFFFF))
        resolved.append({"offset": reloc.offset, "type": "R_ARM_CALL",
                         "symbol": reloc.symbol_name, "target": hex(target),
                         "state": "ARM"})
    if len(resolved) != 22:
        raise SystemExit(f"expected 22 direct call relocations, got {len(resolved)}")
    return obj, bytes(fixed), resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/h2-86928-integration/staged-image")
    args = parser.parse_args()
    out = args.output.resolve()
    original = IMAGE.read_bytes()
    if sha(original) != ORIGINAL_SHA256:
        raise SystemExit("pinned original image hash mismatch")
    obj, body, relocation_rows = compile_function(out)
    offset = VMA - IMAGE_BASE
    replacement = body + ARM_NOP * ((SPAN - len(body)) // 4)
    patched = bytearray(original)
    patched[offset:offset + SPAN] = replacement
    if bytes(patched[:offset]) != original[:offset] or bytes(patched[offset + SPAN:]) != original[offset + SPAN:]:
        raise SystemExit("staged image differs from original outside the function slot")
    patch = encode_ips([(offset, replacement)], len(original))
    if apply_ips(original, patch) != bytes(patched):
        raise SystemExit("IPS round trip mismatch")
    if replacement[-8:] != ARM_NOP * 2:
        raise SystemExit("expected two ARM NOP words in the 8-byte function tail")

    image_path = out / "code.h2-86928.bin"
    ips_path = out / "code.h2-86928.ips"
    manifest_path = out / "manifest.json"
    image_path.write_bytes(patched)
    ips_path.write_bytes(patch)
    manifest = {
        "function": hex(VMA), "symbol": SYMBOL, "classification": "non_matching",
        "source": str(SOURCE.relative_to(ROOT)), "source_sha256": sha(SOURCE.read_bytes()),
        "object": str(obj.relative_to(ROOT)), "object_sha256": sha(obj.read_bytes()),
        "compiled_body_bytes": len(body), "compiled_body_sha256": sha(body),
        "slot_bytes": SPAN, "tail_policy": "two ARM NOPs (8 bytes)",
        "relocations": relocation_rows,
        "original_image_sha256": sha(original), "patched_image_sha256": sha(patched),
        "ips_sha256": sha(patch), "ips_roundtrip": True,
        "only_function_slot_changed": True,
        "artifact_paths": {"image": str(image_path.relative_to(ROOT)),
                           "ips": str(ips_path.relative_to(ROOT))},
        "evidence": {"compiled": "passed", "arm_interworking": "passed",
                     "arm_differential": "pending", "caller": "pending", "runtime": "not_run"}
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"PASS {len(body)}/{SPAN} bytes; 22 ARM calls relocated to even ledger targets; IPS round-trip")
    print(f"image sha256 {sha(patched)}")
    print(f"IPS sha256 {sha(patch)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
