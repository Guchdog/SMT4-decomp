#!/usr/bin/env python3
"""Stage and compose all validated H18 canonical promoted modules over the H17 composite image."""
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
DEFAULT_BASE = ROOT / 'build/agent-work/H17-semantic/h17-integrated-stage/code.h17-final.bin'
TEXT_BASE = 0x00100000

TARGET_SYMBOLS = {
    'g_GameWork_0043e2a8': 0x0043E2A8,
    'shop_func_0026f0d8': 0x0026F0D8,
    'shop_func_002b902c': 0x002B902C,
    'g_BattleSmirkWork_00471a70': 0x00471A70,
    'g_AsdGpuWork_00471b48': 0x00471B48,
    'sub_2C0AC8': 0x002C0AC8,
}

SUBSYSTEMS = [
    {
        'id': 'h10-burroughs',
        'addr': 0x002A0FAC,
        'size': 24,
        'src': 'src/semantic/h10_burroughs_promoted.cpp',
        'cand_fn': 'h10_camp_burroughs_getsavedata_promoted',
    },
    {
        'id': 'h11-shops',
        'addr': 0x0022FC98,
        'size': 48,
        'src': 'src/semantic/h11_shops_promoted.cpp',
        'cand_fn': 'h11_shop_checkhasnew_promoted',
    },
    {
        'id': 'h12-combat',
        'addr': 0x00129C58,
        'size': 24,
        'src': 'src/semantic/h12_combat_promoted.cpp',
        'cand_fn': 'h12_battle_getunitsmirkstate_promoted',
    },
    {
        'id': 'h13-exploration',
        'addr': 0x0026394C,
        'size': 44,
        'src': 'src/semantic/h13_exploration_promoted.cpp',
        'cand_fn': 'h13_placewin_isactive_promoted',
    },
    {
        'id': 'h14-graphics',
        'addr': 0x002C3B88,
        'size': 16,
        'src': 'src/semantic/h14_graphics_promoted.cpp',
        'cand_fn': 'h14_asdgpu_heapsize_promoted',
    },
    {
        'id': 'h15-ui',
        'addr': 0x00126084,
        'size': 16,
        'src': 'src/semantic/h15_ui_promoted.cpp',
        'cand_fn': 'h15_uidialog_getstate_promoted',
    },
    {
        'id': 'h16-sound',
        'addr': 0x00110C44,
        'size': 28,
        'src': 'src/semantic/h16_sound_promoted.cpp',
        'cand_fn': 'h16_asdsoundeffect_getbuffersize_promoted',
    },
    {
        'id': 'h17-cec-aoc',
        'addr': 0x002A17C0,
        'size': 20,
        'src': 'src/semantic/h17_cec_aoc_promoted.cpp',
        'cand_fn': 'h17_aoc_resultisready_promoted',
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-image', type=Path, default=DEFAULT_BASE)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'build/agent-work/H18-semantic/h18-integrated-stage')
    args = parser.parse_args()

    base_bin = args.base_image.read_bytes()
    orig_bin = ORIGINAL.read_bytes()

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    patched_bin, report = patch_binary(base_bin, out_dir)

    out_bin = out_dir / 'code.h18-final.bin'
    out_bin.write_bytes(patched_bin)

    recs = changed_records(orig_bin, patched_bin)
    ips_data = encode_ips(recs, len(orig_bin))
    out_ips = out_dir / 'code.h18-final.ips'
    out_ips.write_bytes(ips_data)

    roundtrip = apply_ips(orig_bin, ips_data)
    assert roundtrip == patched_bin, "Roundtrip IPS verification failed!"

    final_sha = hashlib.sha256(patched_bin).hexdigest()
    ips_sha = hashlib.sha256(ips_data).hexdigest()

    meta = {
        'milestone': 'H18',
        'name': 'Canonical Module Promotion (experiments/ -> src/semantic/)',
        'base_image': str(args.base_image),
        'final_bin_sha256': final_sha,
        'final_ips_sha256': ips_sha,
        'final_ips_size_bytes': len(ips_data),
        'subsystems': report,
    }

    meta_path = out_dir / 'h18-staged-summary.json'
    meta_path.write_text(json.dumps(meta, indent=2), encoding='utf-8')

    print("=== Milestone H18 Canonical Promoted Staging Complete ===")
    print(f"Final binary: {out_bin} ({len(patched_bin)} bytes, SHA: {final_sha})")
    print(f"Final IPS:    {out_ips} ({len(ips_data)} bytes, SHA: {ips_sha})")
    print(f"Summary JSON: {meta_path}")

if __name__ == '__main__':
    main()
