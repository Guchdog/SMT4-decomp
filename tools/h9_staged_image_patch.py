#!/usr/bin/env python3
"""Stage and compose all validated H9 semantic candidates over the H8 composite image."""
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
DEFAULT_BASE = ROOT / 'build/agent-work/H8-semantic/h8-integrated-stage/code.h8-final.bin'
ORIGINAL_SHA = '1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
H8_BASE_SHA = 'bddb53a22a86d9759eb138164ddbc6652f00e5066446c2ef6c85c3a6bb8e3b6d'
TEXT_BASE = 0x00100000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'AsdMem_Zero_002c4b30': 0x002C4B30,
    'AsdTask_Create_002c5978': 0x002C5978,
    'AsdTask_CreateDraw_002c4c00': 0x002C4C00,
    'engine_func_002c0ba8': 0x002C0BA8,
    'engine_func_002976ac': 0x002976AC,
    'g_UniteEffectWork_0043dd90': 0x0043DD90,
    'g_BibleMainWork_0043da10': 0x0043DA10,
    'unite_func_00232800': 0x00232800,
    'unite_func_00233600': 0x00233600,
    'shop_func_002333d4': 0x002333D4,
    'engine_func_002c23f8': 0x002C23F8,
    'unite_func_002333bc': 0x002333BC,
    'unite_func_003ab0d0': 0x003AB0D0,
    'unite_func_00233804': 0x00233804,
    'camp_func_0029f10c': 0x0029F10C,
    'bibleLegionDraw_func_003ad300': 0x003AD300,
    'g_BibleLegionSkillHandle_0043d9f8': 0x0043D9F8,
    'UiSpriteGroup_Init_002c3344': 0x002C3344,
    'UiSpriteGroup_BindTable_002c32f8': 0x002C32F8,
    'camp_func_002bdb2c': 0x002BDB2C,
    'battle_func_002af854': 0x002AF854,
    'g_BibleLegionDrawManager_0043d9e0': 0x0043D9E0,
    'UiAnimSprite_SetupEx_002bdb2c': 0x002BDB2C,
    'UiAnimSprite_SetMode_002bdac0': 0x002BDAC0,
    'g_SortMenuManager_0043dd20': 0x0043DD20,
    'ui_Tbb_GetGlobalSubTable_001b9a90': 0x001B9A90,
    'ui_Tbb_GetRowCount_001b9aa4': 0x001B9AA4,
    'Battle_GetTalkEntry_00215fa8': 0x00215FA8,
    'qsort_002b7f0a': 0x002B7F0A,
    'g_UniteCtrlRoster_0043dd40': 0x0043DD40,
    'unite_func_0022d5c8': 0x0022D5C8,
    'unite_func_003aad60': 0x003AAD60,
    'unite_func_0022df7c': 0x0022DF7C,
    'unite_func_002338ac': 0x002338AC,
    'unite_func_002e32c8': 0x002E32C8,
    'camp_func_0022d33c': 0x0022D33C,
    'g_BibleDevilHandle_0043d9c8': 0x0043D9C8,
    'UiAnimSprite_SetMode_002bf030': 0x002BF030,
    'g_ButtonHelpManager_0043da28': 0x0043DA28,
}

SUBSYSTEMS = [
    {
        'id': 'camp-uniteeffect-init',
        'addr': 0x002E315C,
        'size': 344,
        'src': 'experiments/semantic_equivalence/h9_camp_uniteeffect_init_candidate.cpp',
        'cand_fn': 'h9_camp_uniteeffect_init_candidate',
    },
    {
        'id': 'camp-biblemain-init',
        'addr': 0x00269CC8,
        'size': 352,
        'src': 'experiments/semantic_equivalence/h9_camp_biblemain_init_candidate.cpp',
        'cand_fn': 'h9_camp_biblemain_init_candidate',
    },
    {
        'id': 'camp-biblelegionskill-init',
        'addr': 0x003AB770,
        'size': 592,
        'src': 'experiments/semantic_equivalence/h9_camp_biblelegionskill_init_candidate.cpp',
        'cand_fn': 'h9_camp_biblelegionskill_init_candidate',
    },
    {
        'id': 'camp-biblelegiondraw-init',
        'addr': 0x003AD300,
        'size': 596,
        'src': 'experiments/semantic_equivalence/h9_camp_biblelegiondraw_init_candidate.cpp',
        'cand_fn': 'h9_camp_biblelegiondraw_init_candidate',
    },
    {
        'id': 'camp-sortmenu-init',
        'addr': 0x0029E63C,
        'size': 644,
        'src': 'experiments/semantic_equivalence/h9_camp_sortmenu_init_candidate.cpp',
        'cand_fn': 'h9_camp_sortmenu_init_candidate',
    },
    {
        'id': 'camp-unitectrl-roster',
        'addr': 0x003C9EBC,
        'size': 664,
        'src': 'experiments/semantic_equivalence/h9_camp_unitectrl_roster_candidate.cpp',
        'cand_fn': 'h9_camp_unitectrl_roster_candidate',
    },
    {
        'id': 'camp-bibledevil-init',
        'addr': 0x003A7AD8,
        'size': 668,
        'src': 'experiments/semantic_equivalence/h9_camp_bibledevil_init_candidate.cpp',
        'cand_fn': 'h9_camp_bibledevil_init_candidate',
    },
    {
        'id': 'camp-buttonhelp-init',
        'addr': 0x0028D974,
        'size': 736,
        'src': 'experiments/semantic_equivalence/h9_camp_buttonhelp_init_candidate.cpp',
        'cand_fn': 'h9_camp_buttonhelp_init_candidate',
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

    out_bin = out_dir / 'code.h9-final.bin'
    out_bin.write_bytes(base_bytes)

    # Generate IPS patch
    orig_bytes = ORIGINAL.read_bytes()
    diff_records = changed_records(orig_bytes, bytes(base_bytes))
    ips_bytes = encode_ips(diff_records, len(orig_bytes))
    out_ips = out_dir / 'code.h9-final.ips'
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

    print(f"H9 Composite staging SUCCESSFUL:")
    print(f"  Bin SHA-256: {bin_sha}")
    print(f"  IPS SHA-256: {ips_sha} ({len(ips_bytes)} bytes)")
    print(f"  Reconstructed C++: {total_cand_sz} B / {total_orig_sz} B (+{total_orig_sz - total_cand_sz} B margin)")
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path, default=DEFAULT_BASE)
    parser.add_argument('--out-dir', type=Path, default=ROOT / 'build/agent-work/H9-semantic/h9-integrated-stage')
    args = parser.parse_args()
    stage_candidates(args.out_dir, args.base)
