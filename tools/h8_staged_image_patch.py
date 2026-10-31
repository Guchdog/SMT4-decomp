#!/usr/bin/env python3
"""Stage and compose all validated H8 semantic candidates over the H7 composite image."""
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
DEFAULT_BASE = ROOT / 'build/agent-work/H7-semantic/h7-integrated-stage/code.h7-final.bin'
ORIGINAL_SHA = '1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
H7_BASE_SHA = '477ae5941b1163f56533b74128635e6deb22ddf796d4f4c18d65bdb02ddda3f8'
TEXT_BASE = 0x00100000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'AsdMem_Zero_002c4b30': 0x002C4B30,
    'AsdRes_002c4e28': 0x002C4E28,
    'AsdRes_002c5b04': 0x002C5B04,
    'engine_func_002c3b48': 0x002C3B48,
    'g_StatusBustUpWork_0044e158': 0x0044E158,
    'engine_func_002bc828': 0x002BC828,
    'engine_func_002c2210': 0x002C2210,
    'engine_func_002c20a8': 0x002C20A8,
    'engine_func_002c1ffc': 0x002C1FFC,
    'engine_func_00298fec': 0x00298FEC,
    'engine_func_002c1740': 0x002C1740,
    'engine_func_002c1774': 0x002C1774,
    'g_StatusCameraWork_0044e178': 0x0044E178,
    'StatusDown_SetDisplayMode_00292f44': 0x00292F44,
    'g_StatusContext_0044e140': 0x0044E140,
    'UiMenu_GetSortOptions_002a0fac': 0x002A0FAC,
    'qsort_002b7f0a': 0x002B7F0A,
    'qsort_tail_0027f3d4': 0x0027F3D4,
    'g_StatusDownContext_0044e190': 0x0044E190,
    'StatusDown_ItemSortByIdAsc': 0x00206CBC,
    'StatusDown_ItemSortByIdDesc': 0x002E4608,
    'StatusDown_ItemSortByTypeAsc': 0x00206C38,
    'StatusDown_ItemSortByTypeDesc': 0x002E4584,
    'engine_func_002dca98': 0x002DCA98,
    'engine_func_002c6d30': 0x002C6D30,
    'engine_func_001f61a4': 0x001F61A4,
    'engine_func_001d1bb8': 0x001D1BB8,
    'ItemTable_Get_002b9364': 0x002B9364,
    'UiPage_Setup_0029fae8': 0x0029FAE8,
    'UiPage_SetScroll_0029edfc': 0x0029EDFC,
    'UiPage_SetCursor_0029eb58': 0x0029EB58,
    'StatusDown_SortItemList_0032c4bc': 0x0032C4BC,
    'SkillTable_Get_002b9364': 0x002B9364,
    'StatusDown_SkillSortByIdAsc': 0x00206BE8,
    'StatusDown_SkillSortByIdDesc': 0x002E4534,
    'StatusDown_SkillSortByCostAsc': 0x001F60DC,
    'StatusDown_SkillSortByCostDesc': 0x002DC96C,
    'StatusDown_SkillSortByNameAsc': 0x001F6174,
    'StatusDown_SkillSortByNameDesc': 0x002DCA04,
    'AsdTask_Create_002c5978': 0x002C5978,
    'AsdTask_CreateDraw_002c4c00': 0x002C4C00,
    'UiSpriteGroup_Init_002c3344': 0x002C3344,
    'UiSpriteGroup_BindTable_002c32f8': 0x002C32F8,
    'UiAnimSprite_SetupEx_002bdb2c': 0x002BDB2C,
    'UiAnimSprite_SetMode_002bdac0': 0x002BDAC0,
    'UiAnimSprite_SetMode_002bf030': 0x002BF030,
    'engine_func_002bda1c': 0x002BDA1C,
    'engine_func_002bda10': 0x002BDA10,
    'engine_func_002bda00': 0x002BDA00,
    'engine_func_002c4450': 0x002C4450,
    'g_StatusDownSpriteTable_00407d58': 0x00407D58,
    'engine_func_002c0ba8': 0x002C0BA8,
    'engine_func_002488a8': 0x002488A8,
    'engine_func_002976ac': 0x002976AC,
    'g_GauntletAppWork_0044e1a0': 0x0044E1A0,
}

SUBSYSTEMS = [
    {
        'id': 'ui-status-bustup',
        'addr': 0x00223A90,
        'size': 248,
        'src': 'experiments/semantic_equivalence/h8_ui_status_bustup_candidate.cpp',
        'cand_fn': 'h8_ui_status_bustup_candidate',
    },
    {
        'id': 'ui-status-camera',
        'addr': 0x00258E38,
        'size': 480,
        'src': 'experiments/semantic_equivalence/h8_ui_status_camera_candidate.cpp',
        'cand_fn': 'h8_ui_status_camera_candidate',
    },
    {
        'id': 'ui-status-affinity',
        'addr': 0x00293E4C,
        'size': 520,
        'src': 'experiments/semantic_equivalence/h8_ui_status_affinity_candidate.cpp',
        'cand_fn': 'h8_ui_status_affinity_candidate',
    },
    {
        'id': 'ui-statusdown-itemsort',
        'addr': 0x0032C4BC,
        'size': 372,
        'src': 'experiments/semantic_equivalence/h8_ui_statusdown_itemsort_candidate.cpp',
        'cand_fn': 'h8_ui_statusdown_itemsort_candidate',
    },
    {
        'id': 'ui-statusdown-itemlist',
        'addr': 0x001EE7C8,
        'size': 384,
        'src': 'experiments/semantic_equivalence/h8_ui_statusdown_itemlist_candidate.cpp',
        'cand_fn': 'h8_ui_statusdown_itemlist_candidate',
    },
    {
        'id': 'ui-statusdown-skilllist',
        'addr': 0x001EE5A4,
        'size': 548,
        'src': 'experiments/semantic_equivalence/h8_ui_statusdown_skilllist_candidate.cpp',
        'cand_fn': 'h8_ui_statusdown_skilllist_candidate',
    },
    {
        'id': 'ui-statusdown-init',
        'addr': 0x002D931C,
        'size': 764,
        'src': 'experiments/semantic_equivalence/h8_ui_statusdown_init_candidate.cpp',
        'cand_fn': 'h8_ui_statusdown_init_candidate',
    },
    {
        'id': 'camp-gauntletmenu-init',
        'addr': 0x002E2454,
        'size': 764,
        'src': 'experiments/semantic_equivalence/h8_camp_gauntletmenu_init_candidate.cpp',
        'cand_fn': 'h8_camp_gauntletmenu_init_candidate',
    },
]

def changed_records(before: bytes, after: bytes) -> list[tuple[int, bytes]]:
    out = []
    i = 0
    while i < len(before):
        if before[i] == after[i]:
            i += 1
            continue
        start = i
        i += 1
        while i < len(before) and before[i] != after[i] and i - start < 0xFFFF:
            i += 1
        out.append((start, after[start:i]))
    return out

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def stage_candidates(out_dir: Path, base_bin: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    base_bytes = bytearray(base_bin.read_bytes())

    manifest = []
    total_cand_sz = 0
    total_orig_sz = 0

    for sub in SUBSYSTEMS:
        addr = sub['addr']
        win_sz = sub['size']
        src_path = ROOT / sub['src']
        obj_path = out_dir / f"{sub['id']}.o"

        res = compile_tu_armv6k(src_path, obj_path, ROOT)
        if res.returncode != 0:
            raise RuntimeError(f"Compile failed for {sub['id']}: {res.stderr}")

        funcs = extract_elf_functions_detailed(obj_path)
        raw, relocs = funcs[sub['cand_fn']]
        cand_sz = len(raw)
        margin = win_sz - cand_sz
        if margin < 0:
            raise ValueError(f"Function {sub['id']} overflows window by {-margin} bytes!")

        blob = bytearray(raw)
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

    out_bin = out_dir / 'code.h8-final.bin'
    out_bin.write_bytes(base_bytes)

    # Generate IPS patch
    orig_bytes = ORIGINAL.read_bytes()
    diff_records = changed_records(orig_bytes, bytes(base_bytes))
    ips_bytes = encode_ips(diff_records, len(orig_bytes))
    out_ips = out_dir / 'code.h8-final.ips'
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

    print(f"H8 Composite staging SUCCESSFUL:")
    print(f"  Bin SHA-256: {bin_sha}")
    print(f"  IPS SHA-256: {ips_sha} ({len(ips_bytes)} bytes)")
    print(f"  Reconstructed C++: {total_cand_sz} B / {total_orig_sz} B (+{total_orig_sz - total_cand_sz} B margin)")
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path, default=DEFAULT_BASE)
    parser.add_argument('--out-dir', type=Path, default=ROOT / 'build/agent-work/H8-semantic/h8-integrated-stage')
    args = parser.parse_args()
    stage_candidates(args.out_dir, args.base)
