#!/usr/bin/env python3
"""Stage the typed touch registrar and indexed manager resolver into H2 run-013."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips

BASE = ROOT / "build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/code.combined.bin"
BASE_MANIFEST = BASE.with_name("manifest.json")
BASE_SHA = "7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291"
ORIGINAL_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
TEXT = 0x00100000
CALLER, CALLER_SPAN = 0x002B88C4, 220
RESOLVER, RESOLVER_SPAN = 0x002BF6D0, 64
MANAGER, DIVIDER = 0x002B0188, 0x002C615C
NOP = struct.pack("<I", 0xE320F000)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_body(source: Path, symbol: str, out: Path, address: int, span: int,
                 targets: dict[str, int]) -> tuple[bytes, list[dict], list[str]]:
    obj = out / f"{symbol}.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or f"compile failed: {source}")
    body, relocs = extract_elf_functions_detailed(obj)[symbol]
    if len(body) > span or len(body) % 4:
        raise ValueError(f"{symbol} body {len(body)} does not fit {span}-byte slot")
    fixed = bytearray(body)
    resolved = []
    for rel in relocs:
        if rel.relocation_type != 28 or rel.explicit_addend is not None or rel.symbol_name not in targets:
            raise ValueError(f"unsupported relocation for {symbol}: {rel}")
        target = targets[rel.symbol_name]
        place = address + rel.offset
        delta = target - (place + 8)
        if target & 1 or delta & 3 or not -(1 << 25) <= delta < (1 << 25):
            raise ValueError(f"invalid ARM BL target {place:#x}->{target:#x}")
        ins = struct.unpack_from("<I", fixed, rel.offset)[0]
        if ins & 0x0F000000 != 0x0B000000:
            raise ValueError(f"expected ARM BL at {place:#x}, got {ins:#010x}")
        word = 0xEB000000 | ((delta >> 2) & 0xFFFFFF)
        struct.pack_into("<I", fixed, rel.offset, word)
        resolved.append({"offset": rel.offset, "symbol": rel.symbol_name,
                         "target": hex(target), "target_bit0": target & 1,
                         "type": "R_ARM_CALL", "word": hex(word)})
    if len(relocs) != len(targets) or {r["symbol"] for r in resolved} != set(targets):
        raise ValueError(f"unexpected calls for {symbol}: {resolved}")
    return bytes(fixed), resolved, list(result.args)


def payload(body: bytes, span: int) -> bytes:
    if (span - len(body)) % 4:
        raise ValueError("slot tail cannot be NOP padded")
    return body + NOP * ((span - len(body)) // 4)


def build(output: Path) -> dict:
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    original = (ROOT / "extracted/exefs/code.bin").read_bytes()
    base = BASE.read_bytes()
    base_manifest = json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))
    if sha(original) != ORIGINAL_SHA or sha(base) != BASE_SHA:
        raise ValueError("pinned original or reviewed base image hash mismatch")
    if base_manifest.get("patched_sha256") != BASE_SHA or base_manifest.get("original_sha256") != ORIGINAL_SHA:
        raise ValueError("run-013 manifest identity mismatch")

    resolver_body, resolver_relocs, resolver_args = compile_body(
        ROOT / "src/engine/leaf_batch27_b.cpp", "camp_func_002bf6d0",
        output / "compile-resolver", RESOLVER, RESOLVER_SPAN,
        {"ui_func_002b0188": MANAGER, "ui_func_002c615c": DIVIDER})
    caller_body, caller_relocs, caller_args = compile_body(
        ROOT / "src/engine/leaf_batch32_c.cpp", "camp_func_002b88c4",
        output / "compile-caller", CALLER, CALLER_SPAN,
        {"camp_func_002bf6d0": RESOLVER})
    slots = [(CALLER, CALLER_SPAN, payload(caller_body, CALLER_SPAN), caller_body,
              caller_relocs, "camp_func_002b88c4"),
             (RESOLVER, RESOLVER_SPAN, payload(resolver_body, RESOLVER_SPAN), resolver_body,
              resolver_relocs, "camp_func_002bf6d0")]
    staged = bytearray(base)
    for address, span, replacement, *_ in slots:
        off = address - TEXT
        staged[off:off + span] = replacement
    staged_bytes = bytes(staged)
    changed = {i for i, (a, b) in enumerate(zip(base, staged_bytes)) if a != b}
    allowed = set().union(*(set(range(addr - TEXT, addr - TEXT + span)) for addr, span, *_ in slots))
    if not changed <= allowed:
        raise ValueError(f"unexpected changed byte outside slots at {min(changed - allowed):#x}")
    records = [(addr - TEXT, replacement) for addr, _, replacement, *_ in slots]
    ips = encode_ips(records, len(base))
    if apply_ips(base, ips) != staged_bytes:
        raise ValueError("two-slot IPS round-trip mismatch")
    image_path, ips_path = output / "code.h2-touch-region-bf6d0.bin", output / "code.h2-touch-region-bf6d0.ips"
    image_path.write_bytes(staged_bytes)
    ips_path.write_bytes(ips)
    manifest = {
        "schema_version": 1, "base_image": str(BASE.relative_to(ROOT)), "base_image_sha256": sha(base),
        "original_image_sha256": sha(original), "patched_image_sha256": sha(staged_bytes),
        "ips_sha256": sha(ips), "image_size": len(base), "changed_byte_count": len(changed),
        "only_declared_slots_changed": True, "ips_roundtrip": True, "runtime": "not_run",
        "slots": [{"address": hex(addr), "span": span, "symbol": symbol,
                    "source_sha256": sha((ROOT / ("src/engine/leaf_batch32_c.cpp" if symbol.endswith("b88c4") else "src/engine/leaf_batch27_b.cpp")).read_bytes()),
                    "body_sha256": sha(body), "body_bytes": len(body),
                    "replacement_sha256": sha(replacement), "relocations": relocs}
                   for addr, span, replacement, body, relocs, symbol in slots],
        "compiler_args": {"caller": caller_args, "resolver": resolver_args},
        "artifacts": {"image": str(image_path.relative_to(ROOT)), "ips": str(ips_path.relative_to(ROOT))},
        "evidence": {"staged_differential": "pending", "caller": "pending", "compiled": "passed",
                     "interworking": "passed: all ARM BL targets are even"}}
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
