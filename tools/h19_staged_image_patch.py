#!/usr/bin/env python3
"""Stage and compose Milestone H19 full executable link and CRT start over the H18 composite image."""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips

def changed_records(original: bytes, modified: bytes) -> list[tuple[int, bytes]]:
    records = []
    i = 0
    n = len(original)
    while i < n:
        if original[i] != modified[i]:
            start = i
            while i < n and original[i] != modified[i]:
                i += 1
            records.append((start, modified[start:i]))
        else:
            i += 1
    return records

ORIGINAL = ROOT / 'extracted/exefs/code.bin'
DEFAULT_BASE = ROOT / 'build/agent-work/H18-semantic/h18-integrated-stage/code.h18-final.bin'
TEXT_BASE = 0x00100000

CRT_SUBSYSTEMS = [
    {
        'id': 'crt-start',
        'addr': 0x00100000,
        'size': 36,
        'src': 'src/crt/start.cpp',
        'cand_fn': '__start',
    },
    {
        'id': 'crt-init-bss',
        'addr': 0x00100024,
        'size': 36,
        'src': 'src/crt/start.cpp',
        'cand_fn': '__init_bss',
    },
]

def patch_binary(base_bin: bytes, out_dir: Path) -> tuple[bytes, dict]:
    patched = bytearray(base_bin)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {}

    src_path = ROOT / 'src/crt/start.cpp'
    obj_path = out_dir / "crt_start.o"
    res = compile_tu_armv6k(src_path, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation error for CRT start:\n{res.stderr}")

    funcs = extract_elf_functions_detailed(obj_path)

    for s in CRT_SUBSYSTEMS:
        sid = s['id']
        addr = s['addr']
        size = s['size']
        cand_name = s['cand_fn']

        if cand_name not in funcs:
            raise RuntimeError(f"Function {cand_name} not found in {obj_path}")

        raw_code, relocs = funcs[cand_name]
        cand_len = len(raw_code)
        if cand_len > size:
            raise RuntimeError(f"Subsystem {sid} exceeds window: {cand_len} > {size}")

        padded_blob = bytes(raw_code) + b'\x00' * (size - cand_len)
        file_off = addr - TEXT_BASE
        patched[file_off : file_off + size] = padded_blob

        report[sid] = {
            'vma': f"{addr:#010x}",
            'window_size': size,
            'compiled_size': cand_len,
            'headroom_bytes': size - cand_len,
            'relocations_resolved': len(relocs),
        }

    return bytes(patched), report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-image', type=Path, default=DEFAULT_BASE)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'build/agent-work/H19-semantic/h19-integrated-stage')
    args = parser.parse_args()

    base_bin = args.base_image.read_bytes()
    orig_bin = ORIGINAL.read_bytes()

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    patched_bin, report = patch_binary(base_bin, out_dir)

    out_bin = out_dir / 'code.h19-final.bin'
    out_bin.write_bytes(patched_bin)

    recs = changed_records(orig_bin, patched_bin)
    ips_data = encode_ips(recs, len(orig_bin))
    out_ips = out_dir / 'code.h19-final.ips'
    out_ips.write_bytes(ips_data)

    roundtrip = apply_ips(orig_bin, ips_data)
    assert roundtrip == patched_bin, "Roundtrip IPS verification failed!"

    final_sha = hashlib.sha256(patched_bin).hexdigest()
    ips_sha = hashlib.sha256(ips_data).hexdigest()

    meta = {
        'milestone': 'H19',
        'name': 'Full Executable Link & Reconstructed Image Synthesis',
        'base_image': str(args.base_image),
        'final_bin_sha256': final_sha,
        'final_ips_sha256': ips_sha,
        'final_ips_size_bytes': len(ips_data),
        'subsystems': report,
    }

    meta_path = out_dir / 'h19-staged-summary.json'
    meta_path.write_text(json.dumps(meta, indent=2), encoding='utf-8')

    print("=== Milestone H19 Full Executable Staging Complete ===")
    print(f"Final binary: {out_bin} ({len(patched_bin)} bytes, SHA: {final_sha})")
    print(f"Final IPS:    {out_ips} ({len(ips_data)} bytes, SHA: {ips_sha})")
    print(f"Summary JSON: {meta_path}")

if __name__ == '__main__':
    main()
