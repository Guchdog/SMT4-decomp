#!/usr/bin/env python3
"""Stage and compose all validated H13 semantic candidates over the H12 composite image."""
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
DEFAULT_BASE = ROOT / 'build/agent-work/H12-semantic/h12-integrated-stage/code.h12-final.bin'
ORIGINAL_SHA = '1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
H12_BASE_SHA = '2ce98e10b4ac2dbefd16b7d98aab04298e56461d3dbc3c1b51781e7f80fd21d7'
TEXT_BASE = 0x00100000

TARGET_SYMBOLS = {
    'g_PlaceWinWork_0043da28': 0x0043DA28,
    'g_PlaceWinContext_0043e140': 0x0043E140,
    'sub_2BF030': 0x002BF030,
    'g_MapFieldState_0049f91c': 0x0049F91C,
    'g_MapNaviTarget_004474d8': 0x004474D8,
    'g_MapRuntimeWork_00447060': 0x00447060,
    'sub_2C45B8': 0x002C45B8,
    'sub_2C3290': 0x002C3290,
    'sub_20FDE0': 0x0020FDE0,
    'sub_266D70': 0x00266D70,
    'sub_2E05BC': 0x002E05BC,
}

SUBSYSTEMS = [
    {
        'id': 'placewin-setvisible',
        'addr': 0x002638FC,
        'size': 20,
        'src': 'experiments/semantic_equivalence/h13_placewin_setvisible_candidate.cpp',
        'cand_fn': 'h13_placewin_setvisible_candidate',
    },
    {
        'id': 'placewin-dismiss',
        'addr': 0x002638DC,
        'size': 32,
        'src': 'experiments/semantic_equivalence/h13_placewin_dismiss_candidate.cpp',
        'cand_fn': 'h13_placewin_dismiss_candidate',
    },
    {
        'id': 'placewin-isactive',
        'addr': 0x0026394C,
        'size': 44,
        'src': 'experiments/semantic_equivalence/h13_placewin_isactive_candidate.cpp',
        'cand_fn': 'h13_placewin_isactive_candidate',
    },
    {
        'id': 'mapfield-clearactiveflag',
        'addr': 0x00208A70,
        'size': 20,
        'src': 'experiments/semantic_equivalence/h13_mapfield_clearactiveflag_candidate.cpp',
        'cand_fn': 'h13_mapfield_clearactiveflag_candidate',
    },
    {
        'id': 'mapnavi-settargetcoords',
        'addr': 0x001D2E24,
        'size': 40,
        'src': 'experiments/semantic_equivalence/h13_mapnavi_settargetcoords_candidate.cpp',
        'cand_fn': 'h13_mapnavi_settargetcoords_candidate',
    },
    {
        'id': 'mapnavi-reset',
        'addr': 0x001D2E0C,
        'size': 24,
        'src': 'experiments/semantic_equivalence/h13_mapnavi_reset_candidate.cpp',
        'cand_fn': 'h13_mapnavi_reset_candidate',
    },
    {
        'id': 'mapepl-calcscale',
        'addr': 0x00193B28,
        'size': 28,
        'src': 'experiments/semantic_equivalence/h13_mapepl_calcscale_candidate.cpp',
        'cand_fn': 'h13_mapepl_calcscale_candidate',
    },
    {
        'id': 'mapcalc-distancetoentity',
        'addr': 0x001D3A9C,
        'size': 32,
        'src': 'experiments/semantic_equivalence/h13_mapcalc_distancetoentity_candidate.cpp',
        'cand_fn': 'h13_mapcalc_distancetoentity_candidate',
    },
]

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def patch_binary(base_bin: bytes, out_dir: Path) -> tuple[bytes, dict]:
    patched = bytearray(base_bin)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {}

    for s in SUBSYSTEMS:
        sid = s['id']
        addr = s['addr']
        size = s['size']
        src_path = ROOT / s['src']
        obj_path = out_dir / f"{sid}.o"

        res = compile_tu_armv6k(src_path, obj_path, ROOT)
        if res.returncode != 0:
            raise RuntimeError(f"Compilation error for {sid}:\n{res.stderr}")

        funcs = extract_elf_functions_detailed(obj_path)
        cand_name = s['cand_fn']
        if cand_name not in funcs:
            raise RuntimeError(f"Function {cand_name} not found in {obj_path}")

        raw_code, relocs = funcs[cand_name]
        blob = bytearray(raw_code)

        # Apply relocations
        for r in relocs:
            if r.symbol_name in TARGET_SYMBOLS:
                tgt = TARGET_SYMBOLS[r.symbol_name]
                reloc_vma = addr + r.offset
                if r.relocation_type in (28, 29):
                    w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                    struct.pack_into('<I', blob, r.offset, w)
                elif r.relocation_type == 2:
                    struct.pack_into('<I', blob, r.offset, tgt)
            else:
                raise RuntimeError(f"Unresolved relocation symbol {r.symbol_name} in {sid}")

        cand_len = len(blob)
        if cand_len > size:
            raise RuntimeError(f"Subsystem {sid} exceeds window: {cand_len} > {size}")

        padded_blob = bytes(blob) + b'\x00' * (size - cand_len)
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-image', type=Path, default=DEFAULT_BASE)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'build/agent-work/H13-semantic/h13-integrated-stage')
    args = parser.parse_args()

    base_bytes = args.base_image.read_bytes()
    base_sha = hashlib.sha256(base_bytes).hexdigest()
    print(f"Base image: {args.base_image} ({len(base_bytes)} B, SHA256: {base_sha})")

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    patched_bytes, report = patch_binary(base_bytes, out_dir)
    patched_sha = hashlib.sha256(patched_bytes).hexdigest()

    out_bin = out_dir / 'code.h13-final.bin'
    out_bin.write_bytes(patched_bytes)
    print(f"Patched image: {out_bin} ({len(patched_bytes)} B, SHA256: {patched_sha})")

    # Generate IPS patch
    orig_bytes = ORIGINAL.read_bytes()
    diff_records = changed_records(orig_bytes, patched_bytes)
    ips_bytes = encode_ips(diff_records, len(orig_bytes))
    ips_sha = hashlib.sha256(ips_bytes).hexdigest()

    out_ips = out_dir / 'code.h13-final.ips'
    out_ips.write_bytes(ips_bytes)
    print(f"LayeredFS IPS patch: {out_ips} ({len(ips_bytes)} B, SHA256: {ips_sha})")

    # Roundtrip verification
    reapplied = apply_ips(orig_bytes, ips_bytes)
    assert reapplied == patched_bytes, "IPS roundtrip verification failed!"
    print("Round-trip IPS verification PASSED: apply_ips(code.bin, code.h13-final.ips) == code.h13-final.bin")

    summary_json = out_dir / 'h13_staging_summary.json'
    summary = {
        'base_image': str(args.base_image),
        'base_sha256': base_sha,
        'h13_final_sha256': patched_sha,
        'ips_sha256': ips_sha,
        'ips_size': len(ips_bytes),
        'diff_records_count': len(diff_records),
        'subsystems': report,
    }
    summary_json.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(f"Staging summary written to {summary_json}")

if __name__ == '__main__':
    main()
