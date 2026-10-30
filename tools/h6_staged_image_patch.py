#!/usr/bin/env python3
"""Stage and compose all validated H6 semantic candidates over the H5 composite image."""
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
DEFAULT_BASE = ROOT / 'build/agent-work/H5-semantic/h5-integrated-stage/code.h5-final.bin'
ORIGINAL_SHA = '1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
BASE_SHA = '48b73ed0246547dfe6397d6300b61fcbd885688ee70ef28f9b713db1d741ec5d'
TEXT_BASE = 0x00100000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c54f0': 0x002C54F0,
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'AsdMem_Free': 0x002C4360,
    'AsdMem_CopyFrom': 0x002BD610,
    'AsdSave_Read': 0x002F5348,
    'AsdSave_Write': 0x002F5584,
    'Subsystem_Reset_0026b7ec': 0x0026B7EC,
    'Subsystem_Reset_002594cc': 0x002594CC,
    'Subsystem_Reset_002594ac': 0x002594AC,
    'GetContext_002c0b94': 0x002C0B94,
    'AsdTask_Create': 0x002C5978,
    'AsdTask_SetFlags': 0x001EC8E4,
    'SaveLoadProcess_Step': 0x002EF9AC,
    'SaveLoadProcess_Write': 0x002EFB50,
    'SaveLoadProcess_GetWork_002c0ac8': 0x002C0AC8,
    'SaveLoad_DispatchWorker_00247c64': 0x00247C64,
    'Worker_IsComplete_001a1bf8': 0x001A1BF8,
    'Worker_GetError_002ced0c': 0x002CED0C,
    'SaveHelper_0026b844': 0x0026B844,
    'SaveHelper_0026b830': 0x0026B830,
    'SaveHelper_0026b734': 0x0026B734,
    'SaveHelper_002e0c54': 0x002E0C54,
    'Metadata_Copy_002bcf58': 0x002BCF58,
    'Data_Deserialize_002adb40': 0x002ADB40,
    'Data_Serialize_002adb40': 0x002ADB40,
    'memcpy': 0x002C5FF4,
    'AsdTask_AddCallback': 0x002C4C00,
    'Step_002ef890': 0x002EF890,
    'Draw_00311350': 0x00311350,
    'BootCalc_001c8d28': 0x001C8D28,
    'g_SaveLoadContext_0043e2f0': 0x0043E2F0,
    'g_SaveLoadUIManager_0044de28': 0x0044DE28,
    'g_szLoad_0026b99c': 0x0026B99C,
    'g_szSave_00323034': 0x00323034,
    'g_szBoot_00322ee4': 0x00322EE4,
    'g_szBootUpDraw_00322ef0': 0x00322EF0,
    'g_szBootUpDraw_R_00322efc': 0x00322EFC,
    'g_szBootC_00191f74': 0x00191F74,
}

CANDIDATES = [
    {
        'id': 'h6_asd_save_common_read',
        'source': 'experiments/semantic_equivalence/h6_asd_save_common_read_candidate.cpp',
        'function': 'h6_asd_save_common_read_candidate',
        'vma': 0x0021041C,
        'window_size': 204,
    },
    {
        'id': 'h6_asd_save_common_write',
        'source': 'experiments/semantic_equivalence/h6_asd_save_common_write_candidate.cpp',
        'function': 'h6_asd_save_common_write_candidate',
        'vma': 0x002104E8,
        'window_size': 200,
    },
    {
        'id': 'h6_saveload_process_init',
        'source': 'experiments/semantic_equivalence/h6_saveload_process_init_candidate.cpp',
        'function': 'h6_saveload_process_init_candidate',
        'vma': 0x0026B874,
        'window_size': 304,
    },
    {
        'id': 'h6_saveload_process_step',
        'source': 'experiments/semantic_equivalence/h6_saveload_process_step_candidate.cpp',
        'function': 'h6_saveload_process_step_candidate',
        'vma': 0x002EF9AC,
        'window_size': 420,
    },
    {
        'id': 'h6_saveload_process_write',
        'source': 'experiments/semantic_equivalence/h6_saveload_process_write_candidate.cpp',
        'function': 'h6_saveload_process_write_candidate',
        'vma': 0x002EFB50,
        'window_size': 456,
    },
    {
        'id': 'h6_saveload_process_read',
        'source': 'experiments/semantic_equivalence/h6_saveload_process_read_candidate.cpp',
        'function': 'h6_saveload_process_read_candidate',
        'vma': 0x00322D70,
        'window_size': 412,
    },
    {
        'id': 'h6_saveload_process_close',
        'source': 'experiments/semantic_equivalence/h6_saveload_process_close_candidate.cpp',
        'function': 'h6_saveload_process_close_candidate',
        'vma': 0x00322F0C,
        'window_size': 304,
    },
    {
        'id': 'h6_saveload_ui_init',
        'source': 'experiments/semantic_equivalence/h6_saveload_ui_init_candidate.cpp',
        'function': 'h6_saveload_ui_init_candidate',
        'vma': 0x00191EAC,
        'window_size': 208,
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

def stage_h6(base_path: Path, output_dir: Path) -> dict:
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
            elif r.symbol_name == '':
                in_place = struct.unpack_from('<I', blob, r.offset)[0]
                tgt = vma + in_place
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

        # Preserve trailing literal pool / strings; write only candidate code + relocations
        patched_image[offset:offset + len(blob)] = blob

        candidate_reports.append({
            'id': c_id,
            'vma': hex(vma),
            'offset': hex(offset),
            'compiled_size': len(raw_code),
            'window_size': win_size,
            'padding_nop_bytes': win_size - len(raw_code),
            'relocations_count': len(resolved_relocs),
            'relocations': resolved_relocs,
        })

    final_bin = bytes(patched_image)
    final_bin_path = output_dir / 'code.h6-final.bin'
    final_bin_path.write_bytes(final_bin)
    final_sha = sha(final_bin)

    # Generate IPS mod patch relative to ORIGINAL
    diff_records = changed_records(original, final_bin)
    ips_bytes = encode_ips(diff_records, len(original))
    ips_path = output_dir / 'code.h6-final.ips'
    ips_path.write_bytes(ips_bytes)
    ips_sha = sha(ips_bytes)

    # Verify round-trip IPS application
    round_trip_bin = apply_ips(original, ips_bytes)
    assert sha(round_trip_bin) == final_sha, f'Round-trip IPS failed: {sha(round_trip_bin)} != {final_sha}'

    manifest = {
        'original_sha256': ORIGINAL_SHA,
        'base_sha256': BASE_SHA,
        'final_h6_sha256': final_sha,
        'ips_sha256': ips_sha,
        'ips_size': len(ips_bytes),
        'candidates_count': len(candidate_reports),
        'candidates': candidate_reports,
        'round_trip_verified': True,
    }

    manifest_path = output_dir / 'staging-manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest

def main():
    parser = argparse.ArgumentParser(description='Stage and compose H6 semantic candidates.')
    parser.add_argument('--base', type=Path, default=DEFAULT_BASE)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'build/agent-work/H6-semantic/h6-integrated-stage')
    args = parser.parse_args()

    m = stage_h6(args.base, args.output_dir)
    print(f'H6 Final Bin SHA-256: {m["final_h6_sha256"]}')
    print(f'H6 Final IPS SHA-256: {m["ips_sha256"]} ({m["ips_size"]} bytes)')
    print('Round-trip verification PASSED.')

if __name__ == '__main__':
    main()
