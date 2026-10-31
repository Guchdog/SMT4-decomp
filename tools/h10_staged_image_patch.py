#!/usr/bin/env python3
"""Stage and compose all validated H10 semantic candidates over the H9 composite image."""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips

ORIGINAL = ROOT / 'extracted/exefs/code.bin'
DEFAULT_BASE = ROOT / 'build/agent-work/H9-semantic/h9-integrated-stage/code.h9-final.bin'
ORIGINAL_SHA = '1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
H9_BASE_SHA = '0043ccce8b7bf4a53bbe5312414b27d8c0184345cf674a7e11c1759d0af667ac'
TEXT_BASE = 0x00100000

TARGET_SYMBOLS = {
    'g_GameWork_0043e2a8': 0x0043E2A8,
    'camp_func_002971e4': 0x002971E4,
    'camp_func_002a0f68': 0x002A0F68,
    'sound_func_002b8b78': 0x002B8B78,
    'g_CampWork_0043dd68': 0x0043DD68,
    'Quest_GetMainEntry_002ae3f0': 0x002AE3F0,
    'Quest_GetSubTable_002aa224': 0x002AA224,
    'engine_func_002c0ec4': 0x002C0EC4,
    'engine_func_002c0e9c': 0x002C0E9C,
    'engine_func_002c0e4c': 0x002C0E4C,
    'Quest_FindEntry_002b48dc': 0x002B48DC,
    'g_QuestTableMgr_00433158': 0x00433158,
    'Quest_GetStaticDef_002b087c': 0x002B087C,
    'AsdMem_Zero_002c4b30': 0x002C4B30,
    'Quest_InitEntrySub_002bcf58': 0x002BCF58,
    'Quest_GetDynamicRecord_002b9364': 0x002B9364,
    'Quest_FormatTitle_0024be90': 0x0024BE90,
    'app_func_00242a80': 0x00242A80,
    'app_func_00293c98': 0x00293C98,
    'g_AppStoreWork_00439ca8': 0x00439CA8,
    'app_func_00296f60': 0x00296F60,
    'app_func_00245318': 0x00245318,
    'app_func_0028df54': 0x0028DF54,
}

SUBSYSTEMS = [
    {
        'id': 'camp-burroughs-getsavedata',
        'addr': 0x002A0FAC,
        'size': 24,
        'src': 'experiments/semantic_equivalence/h10_camp_burroughs_getsavedata_candidate.cpp',
        'cand_fn': 'h10_camp_burroughs_getsavedata_candidate',
    },
    {
        'id': 'camp-burroughs-appdispatch',
        'addr': 0x002A0EA8,
        'size': 168,
        'src': 'experiments/semantic_equivalence/h10_camp_burroughs_appdispatch_candidate.cpp',
        'cand_fn': 'h10_camp_burroughs_appdispatch_candidate',
    },
    {
        'id': 'camp-quest-resetselection',
        'addr': 0x0026A004,
        'size': 40,
        'src': 'experiments/semantic_equivalence/h10_camp_quest_resetselection_candidate.cpp',
        'cand_fn': 'h10_camp_quest_resetselection_candidate',
    },
    {
        'id': 'camp-quest-evaltarget',
        'addr': 0x0026A86C,
        'size': 152,
        'src': 'experiments/semantic_equivalence/h10_camp_quest_evaltarget_candidate.cpp',
        'cand_fn': 'h10_camp_quest_evaltarget_candidate',
    },
    {
        'id': 'camp-quest-getavailability',
        'addr': 0x0026A9FC,
        'size': 196,
        'src': 'experiments/semantic_equivalence/h10_camp_quest_getavailability_candidate.cpp',
        'cand_fn': 'h10_camp_quest_getavailability_candidate',
    },
    {
        'id': 'camp-quest-unpackentry',
        'addr': 0x0026AAC0,
        'size': 256,
        'src': 'experiments/semantic_equivalence/h10_camp_quest_unpackentry_candidate.cpp',
        'cand_fn': 'h10_camp_quest_unpackentry_candidate',
    },
    {
        'id': 'camp-appstore-setflag',
        'addr': 0x003253D8,
        'size': 56,
        'src': 'experiments/semantic_equivalence/h10_camp_appstore_setflag_candidate.cpp',
        'cand_fn': 'h10_camp_appstore_setflag_candidate',
    },
    {
        'id': 'camp-appstore-getappparam',
        'addr': 0x00325444,
        'size': 52,
        'src': 'experiments/semantic_equivalence/h10_camp_appstore_getappparam_candidate.cpp',
        'cand_fn': 'h10_camp_appstore_getappparam_candidate',
    },
]

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

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

def stage_candidates(out_dir: Path, base_bin: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_dir = out_dir / 'obj'
    obj_dir.mkdir(parents=True, exist_ok=True)

    base_bytes = bytearray(base_bin.read_bytes())
    manifest = []
    total_cand_sz = 0
    total_orig_sz = 0

    for sub in SUBSYSTEMS:
        src = ROOT / sub['src']
        obj = obj_dir / f"{sub['id']}.o"
        res = compile_tu_armv6k(src, obj, ROOT)
        if res.returncode != 0:
            raise RuntimeError(f"Failed to compile {src}: {res.stderr}")

        funcs = extract_elf_functions_detailed(obj)
        cand_name = sub['cand_fn']
        raw, relocs = funcs[cand_name]
        cand_sz = len(raw)
        win_sz = sub['size']
        addr = sub['addr']

        margin = win_sz - cand_sz
        if margin < 0:
            raise RuntimeError(f"Candidate {cand_name} overflows window by {-margin} bytes!")

        blob = bytearray(raw)

        # Apply relocations
        for r in relocs:
            if r.symbol_name in TARGET_SYMBOLS:
                tgt = TARGET_SYMBOLS[r.symbol_name]
                site = addr + r.offset
                if r.relocation_type == 28: # R_ARM_CALL
                    word = branch_word(site, tgt, is_bl=True)
                    struct.pack_into('<I', blob, r.offset, word)
                elif r.relocation_type == 29: # R_ARM_JUMP24
                    word = branch_word(site, tgt, is_bl=False)
                    struct.pack_into('<I', blob, r.offset, word)
                elif r.relocation_type == 2: # R_ARM_ABS32
                    struct.pack_into('<I', blob, r.offset, tgt)

        # Pad remaining window with NOP (0xE1A00000)
        blob.extend(b'\x00\x00\xa0\xe1' * (margin // 4))

        off = addr - TEXT_BASE
        base_bytes[off:off+win_sz] = blob

        total_cand_sz += cand_sz
        total_orig_sz += win_sz

        manifest.append({
            'subsystem': sub['id'],
            'address': f"0x{addr:08X}",
            'window_size': win_sz,
            'cand_size': cand_sz,
            'margin_nop': margin,
            'relocs_applied': len(relocs)
        })

    out_bin = out_dir / 'code.h10-final.bin'
    out_bin.write_bytes(base_bytes)

    # Generate IPS patch
    orig_bytes = ORIGINAL.read_bytes()
    diff_records = changed_records(orig_bytes, bytes(base_bytes))
    ips_bytes = encode_ips(diff_records, len(orig_bytes))
    out_ips = out_dir / 'code.h10-final.ips'
    out_ips.write_bytes(ips_bytes)

    # Round-trip verification
    patched_check = apply_ips(orig_bytes, ips_bytes)
    assert patched_check == bytes(base_bytes), "IPS round-trip verification failed!"

    bin_sha = hashlib.sha256(bytes(base_bytes)).hexdigest()
    ips_sha = hashlib.sha256(ips_bytes).hexdigest()

    report = {
        'base_bin': str(base_bin),
        'output_bin': str(out_bin),
        'output_bin_sha256': bin_sha,
        'output_ips': str(out_ips),
        'output_ips_sha256': ips_sha,
        'output_ips_size': len(ips_bytes),
        'total_cand_size': total_cand_sz,
        'total_window_size': total_orig_sz,
        'total_headroom': total_orig_sz - total_cand_sz,
        'manifest': manifest
    }

    report_path = out_dir / 'report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"H10 Composite staging SUCCESSFUL:")
    print(f"  Bin SHA-256: {bin_sha}")
    print(f"  IPS SHA-256: {ips_sha} ({len(ips_bytes)} bytes)")
    print(f"  Reconstructed C++: {total_cand_sz} B / {total_orig_sz} B (+{total_orig_sz - total_cand_sz} B margin)")
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path, default=DEFAULT_BASE)
    parser.add_argument('--out-dir', type=Path, default=ROOT / 'build/agent-work/H10-semantic/h10-integrated-stage')
    args = parser.parse_args()
    stage_candidates(args.out_dir, args.base)
