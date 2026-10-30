#!/usr/bin/env python3
"""Install the readable H2 FillPair implementation in its original slot."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import struct
import sys

import capstone

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips

ORIGINAL = ROOT / "extracted/exefs/code.bin"
BASE = ROOT / "build/agent-work/H2-semantic/h2-config-mapper-production-integration/run-008/checks/production-mapper-patch/code.h2-mappers.bin"
BASE_MANIFEST = ROOT / "build/agent-work/H2-semantic/h2-config-mapper-production-integration/run-008/checks/production-mapper-patch/manifest.json"
SOURCE = ROOT / "src/engine/leaf_matching.cpp"
FUNCTIONS = ROOT / "config/functions.csv"
ORIGINAL_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
BASE_SHA256 = "97b6c2ab9ea7f15904bbee3ad42115599bd3529220dbfba818a77bbbcfbe321c"
TEXT_VMA = 0x00100000
ADDRESS = 0x0027EDF8
SIZE = 24
SYMBOL = "camp_func_0027edf8"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_function_spans(path: Path) -> dict[int, int]:
    spans = {}
    with path.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            spans[int(row["address"], 16)] = int(row["size"], 10)
    return spans


def direct_branch_target(word: int, address: int) -> int | None:
    if (word >> 25) & 7 != 0b101:
        return None
    immediate = word & 0x00FFFFFF
    if immediate & 0x00800000:
        immediate -= 0x01000000
    if (word >> 28) == 0xF:
        h = (word >> 24) & 1
        return (address + 8 + (immediate << 2) + (h << 1)) | 1
    return address + 8 + (immediate << 2)


def audit_interior_references(image: bytes, functions_csv: Path = FUNCTIONS) -> dict:
    spans = read_function_spans(functions_csv)
    if spans.get(ADDRESS) != SIZE:
        raise ValueError("FillPair's ledger span differs from the reviewed 24-byte slot")
    end = ADDRESS + SIZE
    branches, pointers = [], []
    for start, size in spans.items():
        if start == ADDRESS:
            continue
        offset = start - TEXT_VMA
        if offset < 0 or offset + size > len(image):
            raise ValueError(f"function span is outside code image: {start:#x}")
        for off in range(offset, offset + size, 4):
            target = direct_branch_target(struct.unpack_from("<I", image, off)[0], TEXT_VMA + off)
            if target is not None and ADDRESS < (target & ~1) < end:
                branches.append({"source": hex(TEXT_VMA + off), "target": hex(target & ~1)})
    for off in range(0, len(image) - 3, 4):
        value = struct.unpack_from("<I", image, off)[0] & ~1
        if ADDRESS < value < end:
            pointers.append({"file_offset": hex(off), "target": hex(value)})
    if branches or pointers:
        raise ValueError(f"external references enter FillPair interior: {branches=} {pointers=}")
    return {
        "ledger_functions_scanned": len(spans),
        "direct_branch_interior_hits": branches,
        "aligned_absolute_pointer_interior_hits": pointers,
        "scope": "direct ARM B/BL/BLX in ledgered text plus aligned words in code.bin",
    }


def validate_body(body: bytes, address: int = ADDRESS) -> dict:
    if len(body) != SIZE or len(body) & 3:
        raise ValueError(f"FillPair body must occupy the original {SIZE}-byte slot")
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    instructions = list(decoder.disasm(body, address))
    if sum(item.size for item in instructions) != SIZE:
        raise ValueError("FillPair body has an undecodable instruction")
    if [item.mnemonic for item in instructions] != ["uxtb", "orr", "orr", "str", "str", "bx"]:
        raise ValueError("FillPair no longer compiles to the reviewed six-instruction body")
    if instructions[-1].op_str != "lr":
        raise ValueError("FillPair body does not return through lr")
    return {"size": len(body), "instructions": [
        {"address": hex(item.address), "mnemonic": item.mnemonic, "operands": item.op_str}
        for item in instructions
    ]}


def build(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    original = ORIGINAL.read_bytes()
    base = BASE.read_bytes()
    if sha256(original) != ORIGINAL_SHA256:
        raise ValueError("pinned original code image identity changed")
    if sha256(base) != BASE_SHA256:
        raise ValueError("mapper-extended H2 base image identity changed")
    interior_scan = audit_interior_references(original)
    obj_path = output / "leaf_matching.production.o"
    compilation = compile_tu_armv6k(SOURCE, obj_path, ROOT)
    if compilation.returncode:
        raise RuntimeError(compilation.stderr or "production TU compilation failed")
    functions = extract_elf_functions_detailed(obj_path)
    if SYMBOL not in functions:
        raise ValueError(f"missing production symbol {SYMBOL}")
    body, relocations = functions[SYMBOL]
    if relocations:
        raise ValueError(f"FillPair has unexpected ELF relocations: {relocations}")
    body_layout = validate_body(body)
    offset = ADDRESS - TEXT_VMA
    patched = bytearray(base)
    patched[offset:offset + SIZE] = body
    ips = encode_ips([(offset, body)], len(base))
    if apply_ips(base, ips) != bytes(patched):
        raise ValueError("generated IPS does not reproduce the patched H2 image")
    patched_path = output / "code.h2-fill-pair.bin"
    ips_path = output / "code.h2-fill-pair.ips"
    patched_path.write_bytes(patched)
    ips_path.write_bytes(ips)
    manifest = json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))
    manifest["patched_sha256"] = sha256(patched)
    manifest["ips_sha256"] = sha256(ips)
    manifest.setdefault("patch_chain", []).append({
        "base_sha256": sha256(base), "ips_sha256": sha256(ips),
        "result_sha256": sha256(patched), "kind": "production UiConfig_FillPair replacement",
    })
    manifest.setdefault("placements", {})["fill_pair"] = {
        "vma": hex(ADDRESS), "bytes": SIZE, "original_span": SIZE,
    }
    manifest.setdefault("production_symbols", {})["fill_pair_sha256"] = sha256(body)
    manifest["fill_pair_replacement"] = {
        "schema": 1,
        "base_image": str(BASE),
        "base_image_sha256": sha256(base),
        "original_image_sha256": sha256(original),
        "address": hex(ADDRESS),
        "size": SIZE,
        "symbol": SYMBOL,
        "source": str(SOURCE),
        "source_sha256": sha256(SOURCE.read_bytes()),
        "object": str(obj_path),
        "object_sha256": sha256(obj_path.read_bytes()),
        "body_hex": body.hex(),
        "body_layout": body_layout,
        "interior_reference_audit": interior_scan,
        "ips": str(ips_path),
        "ips_sha256": sha256(ips),
        "patched_image": str(patched_path),
        "patched_image_sha256": sha256(patched),
        "compile_command": compilation.args,
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = build(args.output.resolve())
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
