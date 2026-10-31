#!/usr/bin/env python3
"""Stage and compose all validated H11 semantic candidates over the H10 composite image."""
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
DEFAULT_BASE = ROOT / 'build/agent-work/H10-semantic/h10-integrated-stage/code.h10-final.bin'
ORIGINAL_SHA = '1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
H10_BASE_SHA = '8233530ba0df84acc66bf6196153403d257e8bbfa1aca1537fafcabc51bdc4e3'
TEXT_BASE = 0x00100000

TARGET_SYMBOLS = {
    'shop_func_0026f0d8': 0x0026F0D8,
    'shop_func_002b902c': 0x002B902C,
    'sub_2B66EC': 0x002B66EC,
    'sub_2AE64C': 0x002AE64C,
    'sub_22EBBC': 0x0022EBBC,
    'sub_2C615C': 0x002C615C,
    'sub_2B9100': 0x002B9100,
    'sub_28FDE4': 0x0028FDE4,
    'sub_2BBD40': 0x002BBD40,
}

SUBSYSTEMS = [
    {
        'id': 'shop-setselecteditem',
        'addr': 0x0022A60C,
        'size': 52,
        'src': 'experiments/semantic_equivalence/h11_shop_setselecteditem_candidate.cpp',
        'cand_fn': 'h11_shop_setselecteditem_candidate',
    },
    {
        'id': 'shop-checkhasnew',
        'addr': 0x0022FC98,
        'size': 48,
        'src': 'experiments/semantic_equivalence/h11_shop_checkhasnew_candidate.cpp',
        'cand_fn': 'h11_shop_checkhasnew_candidate',
    },
    {
        'id': 'shop-checkhasspecial',
        'addr': 0x0022FCC8,
        'size': 48,
        'src': 'experiments/semantic_equivalence/h11_shop_checkhasspecial_candidate.cpp',
        'cand_fn': 'h11_shop_checkhasspecial_candidate',
    },
    {
        'id': 'shop-pushitemrecord',
        'addr': 0x00230680,
        'size': 108,
        'src': 'experiments/semantic_equivalence/h11_shop_pushitemrecord_candidate.cpp',
        'cand_fn': 'h11_shop_pushitemrecord_candidate',
    },
    {
        'id': 'shop-isequipslotmatch',
        'addr': 0x00230D24,
        'size': 140,
        'src': 'experiments/semantic_equivalence/h11_shop_isequipslotmatch_candidate.cpp',
        'cand_fn': 'h11_shop_isequipslotmatch_candidate',
    },
    {
        'id': 'shop-calcpurchasableqty',
        'addr': 0x00230DB0,
        'size': 100,
        'src': 'experiments/semantic_equivalence/h11_shop_calcpurchasableqty_candidate.cpp',
        'cand_fn': 'h11_shop_calcpurchasableqty_candidate',
    },
    {
        'id': 'terminal-setunlockflag',
        'addr': 0x00263734,
        'size': 68,
        'src': 'experiments/semantic_equivalence/h11_terminal_setunlockflag_candidate.cpp',
        'cand_fn': 'h11_terminal_setunlockflag_candidate',
    },
    {
        'id': 'terminal-isunlocked',
        'addr': 0x00263778,
        'size': 60,
        'src': 'experiments/semantic_equivalence/h11_terminal_isunlocked_candidate.cpp',
        'cand_fn': 'h11_terminal_isunlocked_candidate',
    },
]

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidate_patch(sub: dict, out_dir: Path) -> bytes:
    src_path = ROOT / sub['src']
    obj_path = out_dir / f"{sub['id']}.o"
    res = compile_tu_armv6k(src_path, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Build failed for {sub['id']}: {res.stderr}")

    funcs = extract_elf_functions_detailed(obj_path)
    cand_fn = sub['cand_fn']
    if cand_fn not in funcs:
        raise RuntimeError(f"Symbol {cand_fn} not found in {obj_path}")

    raw_code, relocs = funcs[cand_fn]
    cand_size = len(raw_code)
    window_size = sub['size']
    if cand_size > window_size:
        raise RuntimeError(f"Window overflow in {sub['id']}: compiled {cand_size} B > window {window_size} B")

    blob = bytearray(window_size)
    blob[:cand_size] = raw_code
    # NOP padding (0xE1A00000)
    for p in range(cand_size, window_size, 4):
        struct.pack_into('<I', blob, p, 0xE1A00000)

    # Special handling for shop-isequipslotmatch local rodata
    if sub['id'] == 'shop-isequipslotmatch':
        table_offset = 80 # inside 140-byte window
        table_bytes = bytes([0, 2, 6, 8, 10, 12, 4])
        blob[table_offset:table_offset+len(table_bytes)] = table_bytes
        table_addr = sub['addr'] + table_offset

    for r in relocs:
        reloc_vma = sub['addr'] + r.offset
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob, r.offset, w)
            elif r.relocation_type == 2:
                struct.pack_into('<I', blob, r.offset, tgt)
        elif r.relocation_type == 2 and sub['id'] == 'shop-isequipslotmatch':
            struct.pack_into('<I', blob, r.offset, table_addr)
        else:
            raise RuntimeError(f"Unresolved relocation in {sub['id']}: {r.symbol_name} (type {r.relocation_type})")

    return bytes(blob)

def stage_composite_image(base_bin: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(base_bin, 'rb') as f:
        image = bytearray(f.read())

    patches = {}
    patch_records = []
    total_window = 0
    total_compiled = 0

    print("=== Composing Milestone H11 Candidates into Staged Image ===")
    for sub in SUBSYSTEMS:
        patch_bytes = build_candidate_patch(sub, out_dir)
        offset = sub['addr'] - TEXT_BASE
        image[offset:offset+len(patch_bytes)] = patch_bytes
        patches[offset] = patch_bytes
        total_window += sub['size']

        rec = {
            'id': sub['id'],
            'vma': f"0x{sub['addr']:08X}",
            'offset': f"0x{offset:08X}",
            'size': sub['size'],
            'sha256': hashlib.sha256(patch_bytes).hexdigest()
        }
        patch_records.append(rec)
        print(f"Patched [{sub['id']:<26}] @ 0x{sub['addr']:08X} ({sub['size']:3d} B) SHA: {rec['sha256'][:16]}...")

    final_bin = out_dir / 'code.h11-final.bin'
    with open(final_bin, 'wb') as f:
        f.write(image)

    final_sha = hashlib.sha256(image).hexdigest()
    print(f"\nStaged H11 final image generated: {final_bin}")
    print(f"H11 Final Binary SHA-256: {final_sha}")

    # Generate IPS from original game code.bin to H11 staged image
    orig_bytes = ORIGINAL.read_bytes()
    diff_records = changed_records(orig_bytes, bytes(image))
    ips_bytes = encode_ips(diff_records, len(orig_bytes))
    final_ips = out_dir / 'code.h11-final.ips'
    final_ips.write_bytes(ips_bytes)
    ips_sha = hashlib.sha256(ips_bytes).hexdigest()
    print(f"LayeredFS IPS mod generated: {final_ips} ({len(ips_bytes):,d} bytes, SHA: {ips_sha})")

    # Round-trip verification
    applied = apply_ips(orig_bytes, ips_bytes)
    assert applied == bytes(image), "IPS round-trip verification failed!"
    print("IPS patch verified: 100% byte parity with staged composite binary.")

    manifest = {
        'milestone': 'H11',
        'description': 'Shops, Black Market, and Terminals',
        'base_image': str(base_bin),
        'final_binary_sha256': final_sha,
        'ips_patch_sha256': ips_sha,
        'total_window_bytes': total_window,
        'patches': patch_records
    }
    with open(out_dir / 'h11_stage_manifest.json', 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    return final_bin, final_sha, final_ips, ips_sha

def main():
    parser = argparse.ArgumentParser(description='Stage H11 composite binary and IPS mod.')
    parser.add_argument('--base', type=Path, default=DEFAULT_BASE, help='Base binary image (default: H10 staged final)')
    parser.add_argument('--out', type=Path, default=ROOT / 'build/agent-work/H11-semantic/h11-integrated-stage', help='Output stage dir')
    args = parser.parse_args()

    stage_composite_image(args.base, args.out)

if __name__ == '__main__':
    main()
