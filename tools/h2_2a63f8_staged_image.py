#!/usr/bin/env python3
"""Stage the H2 0x002A63F8 C++ predicate into the reviewed run-013 image."""
from __future__ import annotations

import argparse
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

SOURCE = ROOT / "src/engine/leaf_batch17_c.cpp"
BASE = ROOT / "build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/code.combined.bin"
BASE_MANIFEST = BASE.with_name("manifest.json")
BASE_SHA = "7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
FUNCTION = 0x002A63F8
RESOLVER = 0x002B96F0
SPAN = 24
TEXT = 0x00100000
NOP = struct.pack("<I", 0xE320F000)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(output: Path) -> dict:
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    original = (ROOT / "extracted/exefs/code.bin").read_bytes()
    if sha(original) != IMAGE_SHA:
        raise ValueError("pinned original image hash mismatch")
    base = BASE.read_bytes()
    if sha(base) != BASE_SHA:
        raise ValueError("reviewed H2 run-013 base image hash mismatch")
    base_manifest = json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))
    if base_manifest.get("patched_sha256") != BASE_SHA or base_manifest.get("original_sha256") != IMAGE_SHA:
        raise ValueError("run-013 manifest identity mismatch")
    output.mkdir(parents=True)
    result = compile_tu_armv6k(SOURCE, output / "candidate.o", ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    body, relocs = extract_elf_functions_detailed(output / "candidate.o")["ui_func_002a63f8"]
    if len(body) > SPAN or len(body) % 4:
        raise ValueError(f"compiled body size {len(body)} does not fit the {SPAN}-byte slot")
    fixed = bytearray(body)
    relocation_rows = []
    for rel in relocs:
        if (rel.relocation_type != 28 or rel.symbol_name != "engine_func_002b96f0"
                or rel.explicit_addend is not None):
            raise ValueError(f"unsupported predicate relocation: {rel}")
        ins = struct.unpack_from("<I", fixed, rel.offset)[0]
        if ins & 0x0F000000 != 0x0B000000:
            raise ValueError(f"expected ARM BL at body+{rel.offset:#x}, got {ins:#010x}")
        delta = RESOLVER - (FUNCTION + rel.offset + 8)
        struct.pack_into("<I", fixed, rel.offset, (ins & 0xFF000000) | ((delta >> 2) & 0xFFFFFF))
        relocation_rows.append({"offset": hex(rel.offset), "type": rel.relocation_type,
                                "target": hex(RESOLVER), "instruction": "ARM BL"})
    if len(relocs) != 1:
        raise ValueError(f"expected one resolver call relocation, got {relocs}")
    replacement = bytes(fixed) + NOP * ((SPAN - len(fixed)) // 4)
    offset = FUNCTION - TEXT
    staged = bytearray(base)
    staged[offset:offset + SPAN] = replacement
    staged_bytes = bytes(staged)
    changed = {i for i, (a, b) in enumerate(zip(base, staged_bytes)) if a != b}
    if not changed <= set(range(offset, offset + SPAN)):
        raise ValueError("staged changes escaped the predicate slot")
    if staged_bytes[offset:offset + SPAN] != replacement:
        raise ValueError("staged slot differs from compiled candidate plus NOP padding")
    patch = encode_ips([(offset, replacement)], len(base))
    if apply_ips(base, patch) != staged_bytes:
        raise ValueError("IPS round-trip mismatch")
    image_path, ips_path = output / "code.h2-resource-flag.bin", output / "code.h2-resource-flag.ips"
    image_path.write_bytes(staged_bytes)
    ips_path.write_bytes(patch)
    manifest = {
        "schema_version": 1, "function": hex(FUNCTION), "symbol": "ui_func_002a63f8",
        "classification": "non_matching", "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": sha(SOURCE.read_bytes()), "object": str((output / "candidate.o").relative_to(ROOT)),
        "object_sha256": sha((output / "candidate.o").read_bytes()),
        "compiled_body_bytes": len(body), "compiled_body_sha256": sha(body),
        "slot_bytes": SPAN, "replacement_sha256": sha(replacement),
        "tail_policy": "ARM NOP padding after compiled body", "relocations": relocation_rows,
        "base_image": str(BASE.relative_to(ROOT)), "base_image_sha256": sha(base),
        "original_code_image_sha256": sha(original), "patched_image_sha256": sha(staged_bytes),
        "ips_sha256": sha(patch), "changed_byte_count": len(changed),
        "changed_ranges": [{"address": hex(FUNCTION), "offset": hex(offset), "length": SPAN,
                            "replacement_sha256": sha(replacement)}],
        "only_function_slot_changed": True, "ips_roundtrip": True,
        "artifact_paths": {"image": str(image_path.relative_to(ROOT)), "ips": str(ips_path.relative_to(ROOT))},
        "evidence": {"compiled": "passed", "interworking": "passed: ARM BL to even resolver 0x002B96F0",
                     "offline_differential": "pending", "caller": "pending", "review": "pending", "runtime": "not_run"},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
