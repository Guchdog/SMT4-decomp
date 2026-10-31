#!/usr/bin/env python3
"""Stage and compose all validated H16 semantic candidates over the H15 composite image."""
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
DEFAULT_BASE = ROOT / 'build/agent-work/H15-semantic/h15-integrated-stage/code.h15-final.bin'
TEXT_BASE = 0x00100000

TARGET_SYMBOLS = {
    'g_sound_sub_00141924': 0x00141924,
    'g_sound_sub_001419bc': 0x001419BC,
    'g_SoundCtx_0044e190': 0x0044E190,
}

SUBSYSTEMS = [
    {
        'id': 'asdsoundeffect-setbuffer',
        'addr': 0x00110C2C,
        'size': 24,
        'src': 'experiments/semantic_equivalence/h16_asdsoundeffect_setbuffer_candidate.cpp',
        'cand_fn': 'h16_asdsoundeffect_setbuffer_candidate',
    },
    {
        'id': 'asdsoundeffect-getbuffersize',
        'addr': 0x00110C44,
        'size': 28,
        'src': 'experiments/semantic_equivalence/h16_asdsoundeffect_getbuffersize_candidate.cpp',
        'cand_fn': 'h16_asdsoundeffect_getbuffersize_candidate',
    },
    {
        'id': 'asdsoundeffect2-setbuffer',
        'addr': 0x00121150,
        'size': 24,
        'src': 'experiments/semantic_equivalence/h16_asdsoundeffect2_setbuffer_candidate.cpp',
        'cand_fn': 'h16_asdsoundeffect2_setbuffer_candidate',
    },
    {
        'id': 'asdsound-getdatasize',
        'addr': 0x00121F20,
        'size': 32,
        'src': 'experiments/semantic_equivalence/h16_asdsound_getdatasize_candidate.cpp',
        'cand_fn': 'h16_asdsound_getdatasize_candidate',
    },
    {
        'id': 'asdsound-getsamplebytes',
        'addr': 0x00122094,
        'size': 48,
        'src': 'experiments/semantic_equivalence/h16_asdsound_getsamplebytes_candidate.cpp',
        'cand_fn': 'h16_asdsound_getsamplebytes_candidate',
    },
    {
        'id': 'asddata-getbase',
        'addr': 0x00128F34,
        'size': 16,
        'src': 'experiments/semantic_equivalence/h16_asddata_getbase_candidate.cpp',
        'cand_fn': 'h16_asddata_getbase_candidate',
    },
    {
        'id': 'asddata-getcount',
        'addr': 0x00128F44,
        'size': 20,
        'src': 'experiments/semantic_equivalence/h16_asddata_getcount_candidate.cpp',
        'cand_fn': 'h16_asddata_getcount_candidate',
    },
    {
        'id': 'statusdown-setactivesoundid',
        'addr': 0x00215A44,
        'size': 28,
        'src': 'experiments/semantic_equivalence/h16_statusdown_setactivesoundid_candidate.cpp',
        'cand_fn': 'h16_statusdown_setactivesoundid_candidate',
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
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'build/agent-work/H16-semantic/h16-integrated-stage')
    args = parser.parse_args()

    base_bytes = args.base_image.read_bytes()
    base_sha = hashlib.sha256(base_bytes).hexdigest()
    print(f"Base image: {args.base_image} ({len(base_bytes)} B, SHA256: {base_sha})")

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    patched_bytes, report = patch_binary(base_bytes, out_dir)
    patched_sha = hashlib.sha256(patched_bytes).hexdigest()

    out_bin = out_dir / 'code.h16-final.bin'
    out_bin.write_bytes(patched_bytes)
    print(f"Patched image: {out_bin} ({len(patched_bytes)} B, SHA256: {patched_sha})")

    # Generate IPS patch
    orig_bytes = ORIGINAL.read_bytes()
    diff_records = changed_records(orig_bytes, patched_bytes)
    ips_bytes = encode_ips(diff_records, len(orig_bytes))
    ips_sha = hashlib.sha256(ips_bytes).hexdigest()

    out_ips = out_dir / 'code.h16-final.ips'
    out_ips.write_bytes(ips_bytes)
    print(f"LayeredFS IPS patch: {out_ips} ({len(ips_bytes)} B, SHA256: {ips_sha})")

    # Roundtrip verification
    reapplied = apply_ips(orig_bytes, ips_bytes)
    assert reapplied == patched_bytes, "IPS roundtrip verification failed!"
    print("Round-trip IPS verification PASSED: apply_ips(code.bin, code.h16-final.ips) == code.h16-final.bin")

    summary_json = out_dir / 'h16_staging_summary.json'
    summary = {
        'base_image': str(args.base_image),
        'base_sha256': base_sha,
        'h16_final_sha256': patched_sha,
        'ips_sha256': ips_sha,
        'ips_size': len(ips_bytes),
        'diff_records_count': len(diff_records),
        'subsystems': report,
    }
    summary_json.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(f"Staging summary written to {summary_json}")

if __name__ == '__main__':
    main()
