#!/usr/bin/env python3
"""Place the reviewed 0x002B88C4 C++ body into the reviewed H2 run-013 image."""
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

SOURCE = ROOT / "src/engine/leaf_batch32_c.cpp"
BASE = ROOT / "build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/code.combined.bin"
BASE_MANIFEST = ROOT / "build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/manifest.json"
BASE_SHA = "7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
CALLER = 0x002B88C4
SPAN = 220
HELPER = 0x002BF6D0
TEXT = 0x00100000
NOP = struct.pack("<I", 0xE320F000)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(output: Path, jobs: int) -> dict:
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    output.mkdir(parents=True)
    original = (ROOT / "extracted/exefs/code.bin").read_bytes()
    if sha(original) != IMAGE_SHA:
        raise ValueError("pinned original image hash mismatch")
    base = BASE.read_bytes()
    if sha(base) != BASE_SHA:
        raise ValueError("reviewed H2 base image hash mismatch")
    base_manifest = json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))
    if base_manifest.get("patched_sha256") != BASE_SHA or base_manifest.get("original_sha256") != IMAGE_SHA:
        raise ValueError("run-013 manifest identity mismatch")
    result = compile_tu_armv6k(SOURCE, output / "candidate.o", ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    obj = output / "candidate.o"
    body, relocs = extract_elf_functions_detailed(obj)["camp_func_002b88c4"]
    if len(body) > SPAN or len(body) % 4:
        raise ValueError(f"compiled body size {len(body)} does not fit slot {SPAN}")
    fixed = bytearray(body)
    relocation_rows = []
    for rel in relocs:
        if rel.relocation_type != 28 or rel.symbol_name != "camp_func_002bf6d0" or rel.explicit_addend is not None:
            raise ValueError(f"unsupported caller relocation: {rel}")
        ins = struct.unpack_from("<I", fixed, rel.offset)[0]
        if ins & 0x0F000000 != 0x0B000000:
            raise ValueError(f"expected ARM BL at body+{rel.offset:#x}, got {ins:#010x}")
        delta = HELPER - (CALLER + rel.offset + 8)
        struct.pack_into("<I", fixed, rel.offset, 0xEB000000 | ((delta >> 2) & 0xFFFFFF))
        relocation_rows.append({"offset": hex(rel.offset), "type": rel.relocation_type,
                                "target": hex(HELPER), "instruction": "BL ARM"})
    if len(relocs) != 1:
        raise ValueError(f"expected exactly one helper call relocation, got {len(relocs)}")
    replacement = bytes(fixed) + NOP * ((SPAN - len(fixed)) // 4)
    offset = CALLER - TEXT
    staged = bytearray(base)
    staged[offset:offset + SPAN] = replacement
    staged_bytes = bytes(staged)
    changed = {i for i, (a, b) in enumerate(zip(base, staged_bytes)) if a != b}
    allowed = set(range(offset, offset + SPAN))
    if not changed <= allowed:
        raise ValueError(f"unexpected staged byte change at {min(changed - allowed):#x}")
    if staged_bytes[offset:offset + SPAN] != replacement:
        raise ValueError("staged function slot does not match replacement")
    patch = encode_ips([(offset, replacement)], len(base))
    if apply_ips(base, patch) != staged_bytes:
        raise ValueError("IPS round-trip mismatch")
    image_path, ips_path = output / "code.h2-touch-region.bin", output / "code.h2-touch-region.ips"
    image_path.write_bytes(staged_bytes)
    ips_path.write_bytes(patch)
    manifest = {
        "schema_version": 1, "function": hex(CALLER), "symbol": "camp_func_002b88c4",
        "classification": "non_matching", "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": sha(SOURCE.read_bytes()), "object": str(obj.relative_to(ROOT)),
        "object_sha256": sha(obj.read_bytes()), "compiled_body_bytes": len(body),
        "compiled_body_sha256": sha(body), "replacement_sha256": sha(replacement),
        "slot_bytes": SPAN, "tail_policy": "ARM NOP padding after compiled function body",
        "relocations": relocation_rows, "base_image": str(BASE.relative_to(ROOT)),
        "base_image_sha256": sha(base), "original_code_image_sha256": sha(original),
        "patched_image_sha256": sha(staged_bytes), "ips_sha256": sha(patch),
        "changed_byte_count": len(changed), "changed_ranges": [{"address": hex(CALLER), "offset": hex(offset),
                                                                  "length": SPAN, "replacement_sha256": sha(replacement)}],
        "only_function_slot_changed": True, "ips_roundtrip": True,
        "artifact_paths": {"image": str(image_path.relative_to(ROOT)), "ips": str(ips_path.relative_to(ROOT))},
        "evidence": {"compiled": "passed", "interworking": "passed: ARM BL to even target 0x002BF6D0",
                     "staged_differential": "pending", "caller": "pending", "runtime": "not_run"},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=1)
    args = parser.parse_args()
    build(args.output.resolve(), args.jobs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
