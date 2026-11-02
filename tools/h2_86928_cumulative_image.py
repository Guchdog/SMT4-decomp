#!/usr/bin/env python3
"""Overlay production 0x00286928 onto the prior reviewed H2 runtime image."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.h2_calc_code_patch import apply_ips, encode_ips
ORIGINAL = ROOT / "extracted/exefs/code.bin"
BASE = ROOT / "build/h2-8d24-integration/runtime-image/code.h2-runtime.bin"
STAGED = ROOT / "build/h2-86928-integration/staged-image/code.h2-86928.bin"
OUT = ROOT / "build/h2-86928-integration/cumulative-image"
ENTRY = 0x00286928
SPAN = 820
IMAGE_BASE = 0x00100000
ORIGINAL_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
BASE_SHA = "f87b3149c03a58cc16eb3e903f0102b6f7ce47fdb3523740e992c3824f94e940"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ips_records(original: bytes, final: bytes) -> list[tuple[int, bytes]]:
    """Encode every changed run, splitting only to respect IPS's 16-bit length."""
    records = []
    cursor = 0
    size = len(original)
    while cursor < size:
        if original[cursor] == final[cursor]:
            cursor += 1
            continue
        start = cursor
        while cursor < size and original[cursor] != final[cursor]:
            cursor += 1
        payload = final[start:cursor]
        for offset in range(0, len(payload), 0xFFFF):
            records.append((start + offset, payload[offset:offset + 0xFFFF]))
    return records


def main() -> int:
    original, base, staged = ORIGINAL.read_bytes(), BASE.read_bytes(), STAGED.read_bytes()
    if sha(original) != ORIGINAL_SHA or sha(base) != BASE_SHA:
        raise SystemExit("pinned original or reviewed H2 base image hash mismatch")
    if len(original) != len(base) or len(base) != len(staged):
        raise SystemExit("code image lengths differ")
    offset = ENTRY - IMAGE_BASE
    replacement = staged[offset:offset + SPAN]
    if len(replacement) != SPAN:
        raise SystemExit("staged function slot lies outside code image")
    final = bytearray(base)
    final[offset:offset + SPAN] = replacement
    final = bytes(final)
    if final[:offset] != base[:offset] or final[offset + SPAN:] != base[offset + SPAN:]:
        raise SystemExit("cumulative image differs from prior H2 base outside helper slot")

    records = ips_records(original, final)
    ips = encode_ips(records, len(original))
    if apply_ips(original, ips) != final:
        raise SystemExit("cumulative original-based IPS round-trip failed")
    OUT.mkdir(parents=True, exist_ok=True)
    image_path = OUT / "code.h2-86928-runtime.bin"
    ips_path = OUT / "code.h2-86928-runtime.ips"
    manifest_path = OUT / "manifest.json"
    image_path.write_bytes(final)
    ips_path.write_bytes(ips)
    manifest = {
        "base_image": str(BASE.relative_to(ROOT)), "base_sha256": sha(base),
        "overlaid_function": hex(ENTRY), "slot_bytes": SPAN,
        "replacement_sha256": sha(replacement), "original_sha256": sha(original),
        "patched_sha256": sha(final), "ips_sha256": sha(ips),
        "ips_record_count": len(records), "ips_roundtrip": True,
        "only_new_slot_differs_from_base": True,
        "artifact_paths": {"image": str(image_path.relative_to(ROOT)),
                           "ips": str(ips_path.relative_to(ROOT))},
        "note": "Prior H2 base image has its own source-identity caveats; this manifest identifies exact bytes, not a source rebuild claim."
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"PASS cumulative H2 image; overlay {hex(ENTRY)} only; {len(records)} original-based IPS records")
    print(f"image sha256 {sha(final)}")
    print(f"IPS sha256 {sha(ips)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
