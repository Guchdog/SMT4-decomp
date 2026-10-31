#!/usr/bin/env python3
"""Stage and compose all validated H12 semantic candidates over the H11 composite image."""
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
DEFAULT_BASE = ROOT / 'build/agent-work/H11-semantic/h11-integrated-stage/code.h11-final.bin'
ORIGINAL_SHA = '1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
H11_BASE_SHA = '0520e88c5fb70e16e8c5071d097fb6d3de3c9c55e57aaef8d59fbbe998a9d843'
TEXT_BASE = 0x00100000

TARGET_SYMBOLS = {
    'g_BattleTurnWork_0044e32c': 0x0044E32C,
    'sub_136FA4': 0x00136FA4,
    'sub_132FB8': 0x00132FB8,
    'sub_1423C0': 0x001423C0,
    'sub_13348C': 0x0013348C,
    'g_BattleSmirkWork_00471a70': 0x00471A70,
    'sub_2C3AA8': 0x002C3AA8,
    'sub_2C3A24': 0x002C3A24,
    'g_BattleStateWork_004655c0': 0x004655C0,
    'sub_1422F8': 0x001422F8,
    'g_ResultWork_0044dc20': 0x0044DC20,
    'sub_2A755C': 0x002A755C,
    'sub_2C4360': 0x002C4360,
    'sub_2C0128': 0x002C0128,
    'sub_2A497C': 0x002A497C,
    'sub_2AEB2C': 0x002AEB2C,
    'g_BattleUnitTable_00478000': 0x00478000,
    'sub_2BCF58': 0x002BCF58,
}

SUBSYSTEMS = [
    {
        'id': 'battle-initturnsubsystems',
        'addr': 0x00123050,
        'size': 64,
        'src': 'experiments/semantic_equivalence/h12_battle_initturnsubsystems_candidate.cpp',
        'cand_fn': 'h12_battle_initturnsubsystems_candidate',
    },
    {
        'id': 'battle-getunitsmirkstate',
        'addr': 0x00129C58,
        'size': 24,
        'src': 'experiments/semantic_equivalence/h12_battle_getunitsmirkstate_candidate.cpp',
        'cand_fn': 'h12_battle_getunitsmirkstate_candidate',
    },
    {
        'id': 'battle-getsmirkactor',
        'addr': 0x00129CBC,
        'size': 20,
        'src': 'experiments/semantic_equivalence/h12_battle_getsmirkactor_candidate.cpp',
        'cand_fn': 'h12_battle_getsmirkactor_candidate',
    },
    {
        'id': 'battle-exchangesmirkslot',
        'addr': 0x00129C70,
        'size': 76,
        'src': 'experiments/semantic_equivalence/h12_battle_exchangesmirkslot_candidate.cpp',
        'cand_fn': 'h12_battle_exchangesmirkslot_candidate',
    },
    {
        'id': 'battle-initturndata',
        'addr': 0x00136FA4,
        'size': 40,
        'src': 'experiments/semantic_equivalence/h12_battle_initturndata_candidate.cpp',
        'cand_fn': 'h12_battle_initturndata_candidate',
    },
    {
        'id': 'result-cleanup',
        'addr': 0x001C87D8,
        'size': 156,
        'src': 'experiments/semantic_equivalence/h12_result_cleanup_candidate.cpp',
        'cand_fn': 'h12_result_cleanup_candidate',
    },
    {
        'id': 'battle-isunitdefeated',
        'addr': 0x0028DE4C,
        'size': 56,
        'src': 'experiments/semantic_equivalence/h12_battle_isunitdefeated_candidate.cpp',
        'cand_fn': 'h12_battle_isunitdefeated_candidate',
    },
    {
        'id': 'battle-resetunitstatebuffer',
        'addr': 0x00215938,
        'size': 32,
        'src': 'experiments/semantic_equivalence/h12_battle_resetunitstatebuffer_candidate.cpp',
        'cand_fn': 'h12_battle_resetunitstatebuffer_candidate',
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
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'build/agent-work/H12-semantic/h12-integrated-stage')
    args = parser.parse_args()

    base_bytes = args.base_image.read_bytes()
    base_sha = hashlib.sha256(base_bytes).hexdigest()
    print(f"Base image: {args.base_image} ({len(base_bytes)} B, SHA256: {base_sha})")

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    patched_bytes, report = patch_binary(base_bytes, out_dir)
    patched_sha = hashlib.sha256(patched_bytes).hexdigest()

    out_bin = out_dir / 'code.h12-final.bin'
    out_bin.write_bytes(patched_bytes)
    print(f"Patched image: {out_bin} ({len(patched_bytes)} B, SHA256: {patched_sha})")

    # Generate IPS patch
    orig_bytes = ORIGINAL.read_bytes()
    diff_records = changed_records(orig_bytes, patched_bytes)
    ips_bytes = encode_ips(diff_records, len(orig_bytes))
    ips_sha = hashlib.sha256(ips_bytes).hexdigest()

    out_ips = out_dir / 'code.h12-final.ips'
    out_ips.write_bytes(ips_bytes)
    print(f"LayeredFS IPS patch: {out_ips} ({len(ips_bytes)} B, SHA256: {ips_sha})")

    # Roundtrip verification
    reapplied = apply_ips(orig_bytes, ips_bytes)
    assert reapplied == patched_bytes, "IPS roundtrip verification failed!"
    print("Round-trip IPS verification PASSED: apply_ips(code.bin, code.h12-final.ips) == code.h12-final.bin")

    summary_json = out_dir / 'h12_staging_summary.json'
    summary = {
        'base_image': str(args.base_image),
        'base_sha256': base_sha,
        'h12_final_sha256': patched_sha,
        'ips_sha256': ips_sha,
        'ips_size': len(ips_bytes),
        'diff_records_count': len(diff_records),
        'subsystems': report,
    }
    summary_json.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(f"Staging summary written to {summary_json}")

if __name__ == '__main__':
    main()
