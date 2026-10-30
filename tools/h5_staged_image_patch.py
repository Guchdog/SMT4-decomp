#!/usr/bin/env python3
"""Stage and compose all validated H5 semantic candidates over the H4 composite image."""
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
DEFAULT_BASE = ROOT / 'build/agent-work/H4-semantic/h4-integrated-stage/code.h4-final.bin'
ORIGINAL_SHA = '1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
BASE_SHA = '3e0e4ae440cce5e3644f3f8c19f69806bbfd81fee4e285723bd6979625e37dca'
TEXT_BASE = 0x00100000

TARGET_SYMBOLS = {
    'Unit_Lookup_002ae3f0': 0x002AE3F0,
    'SubParty_Lookup_002b9364': 0x002B9364,
    'TargetSelect_GetWork_002c0ac8': 0x002C0AC8,
    'TargetSelect_DrawMode1_00342b54': 0x00342B54,
    'TargetSelect_DrawMode2_0034946c': 0x0034946C,
    'TargetSelect_UpdateAnim_002bf9f0': 0x002BF9F0,
    'TargetSelect_Mode1Calc_003428a4': 0x003428A4,
    'Task_Destroy_002bf41c': 0x002BF41C,
    'Task_Create_002c4c00': 0x002C4C00,
    'Mem_Alloc_002c4b84': 0x002C4B84,
    'btlHelp_Calc_001b5398': 0x001B5398,
    'g_BtlHelpManager_00435d78': 0x00435D78,
    'btlTalk_Calc_001b71b8': 0x001B71B8,
    'g_pBtlTalkBuffer_00439b58': 0x00439B58,
    'g_TalkHost_00439ca8': 0x00439CA8,
    'Talk_Setup_002c4450': 0x002C4450,
    'Talk_Register_00267f68': 0x00267F68,
    'SubObject_CheckState_002b2530': 0x002B2530,
    'Free_002c4360': 0x002C4360,
    'g_CombatSubWork_00447e28': 0x00447E28,
    'g_CombatChannelContext_004c6290': 0x004C6290,
}

STRING_LITERAL_MAPPING = {
    'h5_btl_help_init': 0x001D25C8,  # "btlHelp Calc" in original binary
    'h5_btl_talk_init': 0x001D2730,  # "btlTalk Calc" in original binary
}

CANDIDATES = [
    {
        'id': 'h5_btl_unit_check_party_active',
        'source': 'experiments/semantic_equivalence/h5_btl_unit_check_party_active_candidate.cpp',
        'function': 'h5_btl_unit_check_party_active_candidate',
        'vma': 0x001D29C8,
        'window_size': 240,
    },
    {
        'id': 'h5_btl_is_demon_unit',
        'source': 'experiments/semantic_equivalence/h5_btl_is_demon_unit_candidate.cpp',
        'function': 'h5_btl_is_demon_unit_candidate',
        'vma': 0x002AE464,
        'window_size': 16,
    },
    {
        'id': 'h5_btl_target_select_draw_up',
        'source': 'experiments/semantic_equivalence/h5_btl_target_select_draw_up_candidate.cpp',
        'function': 'h5_btl_target_select_draw_up_candidate',
        'vma': 0x002F4AA4,
        'window_size': 76,
    },
    {
        'id': 'h5_btl_target_select_calc',
        'source': 'experiments/semantic_equivalence/h5_btl_target_select_calc_candidate.cpp',
        'function': 'h5_btl_target_select_calc_candidate',
        'vma': 0x002E06BC,
        'window_size': 236,
    },
    {
        'id': 'h5_btl_help_init',
        'source': 'experiments/semantic_equivalence/h5_btl_help_init_candidate.cpp',
        'function': 'h5_btl_help_init_candidate',
        'vma': 0x001D2528,
        'window_size': 232,
    },
    {
        'id': 'h5_btl_talk_init',
        'source': 'experiments/semantic_equivalence/h5_btl_talk_init_candidate.cpp',
        'function': 'h5_btl_talk_init_candidate',
        'vma': 0x001D2610,
        'window_size': 308,
    },
    {
        'id': 'h5_btl_release_state',
        'source': 'experiments/semantic_equivalence/h5_btl_release_state_candidate.cpp',
        'function': 'h5_btl_release_state_candidate',
        'vma': 0x002B8A80,
        'window_size': 92,
    },
    {
        'id': 'h5_btl_set_channel_param',
        'source': 'experiments/semantic_equivalence/h5_btl_set_channel_param_candidate.cpp',
        'function': 'h5_btl_set_channel_param_candidate',
        'vma': 0x0011311C,
        'window_size': 52,
    },
]

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

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

def stage_h5(base_path: Path, output_dir: Path) -> dict:
    original = ORIGINAL.read_bytes()
    base = base_path.read_bytes()

    if sha(original) != ORIGINAL_SHA:
        raise ValueError(f'Original binary hash mismatch: expected {ORIGINAL_SHA}, got {sha(original)}')
    if base_path == DEFAULT_BASE and sha(base) != BASE_SHA:
        raise ValueError(f'Base composite binary hash mismatch: expected {BASE_SHA}, got {sha(base)}')
    if len(original) != len(base):
        raise ValueError(f'Base size {len(base)} != original size {len(original)}')

    output_dir.mkdir(parents=True, exist_ok=True)
    obj_dir = output_dir / 'objects'
    obj_dir.mkdir(parents=True, exist_ok=True)

    patched_image = bytearray(base)
    candidate_reports = []

    for cand in CANDIDATES:
        c_id = cand['id']
        src_path = ROOT / cand['source']
        obj_path = obj_dir / f'{c_id}.o'
        vma = cand['vma']
        win_size = cand['window_size']
        offset = vma - TEXT_BASE

        # Compile candidate
        res = compile_tu_armv6k(src_path, obj_path, ROOT)
        if res.returncode != 0:
            raise RuntimeError(f'Compilation failed for {c_id}: {res.stderr}')

        funcs = extract_elf_functions_detailed(obj_path)
        func_name = cand['function']
        if func_name not in funcs:
            raise KeyError(f'Function {func_name} not found in {obj_path}')

        raw_code, relocs = funcs[func_name]
        if len(raw_code) > win_size:
            raise ValueError(f'{c_id} size {len(raw_code)} exceeds window size {win_size}')

        # Relocate symbols
        blob = bytearray(raw_code)
        resolved_relocs = []
        for r in relocs:
            if r.symbol_name in TARGET_SYMBOLS:
                tgt = TARGET_SYMBOLS[r.symbol_name]
            elif r.symbol_name == '' and c_id in STRING_LITERAL_MAPPING:
                tgt = STRING_LITERAL_MAPPING[c_id]
            else:
                raise KeyError(f'Relocation symbol {r.symbol_name} in {c_id} not recognized')

            reloc_vma = vma + r.offset

            if r.relocation_type == 2:  # R_ARM_ABS32
                struct.pack_into('<I', blob, r.offset, tgt)
                w = tgt
            elif r.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
                if tgt & 1 != 0 or reloc_vma & 3 != 0:
                    raise ValueError(f'Interworking alignment violation at 0x{reloc_vma:08X} -> 0x{tgt:08X}')
                is_bl = (r.relocation_type == 28)
                w = branch_word(reloc_vma, tgt, is_bl=is_bl)
                struct.pack_into('<I', blob, r.offset, w)
            else:
                raise ValueError(f'Unsupported relocation type {r.relocation_type} for symbol {r.symbol_name}')

            resolved_relocs.append({
                'symbol': r.symbol_name,
                'offset': r.offset,
                'relocation_type': r.relocation_type,
                'target_vma': hex(tgt),
                'word': hex(w),
            })

        # Pad remaining window with NOP (0xE1A00000 = mov r0, r0)
        if len(blob) < win_size:
            pad_len = win_size - len(blob)
            assert pad_len % 4 == 0, f'Padding length {pad_len} must be 4-byte aligned'
            blob.extend(b'\x00\x00\xa0\xe1' * (pad_len // 4))

        assert len(blob) == win_size, f'Final blob length {len(blob)} != window size {win_size}'
        patched_image[offset:offset + win_size] = blob

        candidate_reports.append({
            'id': c_id,
            'vma': hex(vma),
            'offset': hex(offset),
            'compiled_size': len(raw_code),
            'window_size': win_size,
            'padding_nop_bytes': win_size - len(raw_code),
            'relocations_resolved': len(resolved_relocs),
            'relocations': resolved_relocs,
        })

    final_bin = bytes(patched_image)
    ips_payload = encode_ips(changed_records(original, final_bin), len(original))
    round_trip = apply_ips(original, ips_payload)

    if round_trip != final_bin:
        raise ValueError('IPS round-trip verification failed: patched binary does not match applied IPS')

    final_bin_path = output_dir / 'code.h5-final.bin'
    final_ips_path = output_dir / 'code.h5-final.ips'
    final_bin_path.write_bytes(final_bin)
    final_ips_path.write_bytes(ips_payload)

    return {
        'status': 'staged',
        'original_sha': sha(original),
        'base_sha': sha(base),
        'final_sha': sha(final_bin),
        'ips_sha': sha(ips_payload),
        'final_size': len(final_bin),
        'ips_size': len(ips_payload),
        'candidates_count': len(candidate_reports),
        'candidates': candidate_reports,
        'final_bin_path': str(final_bin_path),
        'final_ips_path': str(final_ips_path),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path, default=DEFAULT_BASE)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'build/agent-work/H5-semantic/h5-integrated-stage')
    parser.add_argument('--report', type=Path, default=ROOT / 'build/agent-work/H5-semantic/h5-integrated-stage/stage-report.json')
    args = parser.parse_args()

    report = stage_h5(args.base, args.output_dir)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with open(args.report, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"Staged {report['candidates_count']} candidates successfully.")
    print(f"Final binary SHA: {report['final_sha']}")
    print(f"IPS patch SHA:    {report['ips_sha']}")

if __name__ == '__main__':
    main()
