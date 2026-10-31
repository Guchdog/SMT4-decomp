#!/usr/bin/env python3
"""Stage and compose all validated H7 semantic candidates over the H6 composite image."""
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
DEFAULT_BASE = ROOT / 'build/agent-work/H6-semantic/h6-integrated-stage/code.h6-final.bin'
ORIGINAL_SHA = '1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
BASE_SHA = '1677aac91a81740ab03dde2010e0df0dea4ce3b9b7265a7339bdf2ef22333587'
TEXT_BASE = 0x00100000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'AsdMem_Alloc_002c54f0': 0x002C54F0,
    'AsdMem_Zero_002c4b30': 0x002C4B30,
    'AsdRes_Load_002c5e2c': 0x002C5E2C,
    'AsdTask_Create_002c5978': 0x002C5978,
    'AsdTask_CreateDraw_002c4c00': 0x002C4C00,
    'UiSpriteGroup_Init_002c3344': 0x002C3344,
    'UiSpriteGroup_BindTable_002c32f8': 0x002C32F8,
    'UiAnimSprite_Setup_002bf0a8': 0x002BF0A8,
    'UiAnimSprite_SetupEx_002bdb2c': 0x002BDB2C,
    'UiAnimSprite_SetMode_002bf030': 0x002BF030,
    'UiAnimSprite_SetMode_002bdac0': 0x002BDAC0,
    'UiAnimSprite_SetAnim_002bf030': 0x002BF030,
    'engine_func_002bdc08': 0x002BDC08,
    'engine_func_002bdbcc': 0x002BDBCC,
    'NameMain_Helper_003986c8': 0x003986C8,
    'camp_func_00289b4c': 0x00289B4C,
    'camp_func_0028d974': 0x0028D974,
    'camp_func_00289ae8': 0x00289AE8,
    'camp_func_002b8b78': 0x002B8B78,
    'FlowScript_Create_002972f8': 0x002972F8,
    'FlowScript_Helper_002971e4': 0x002971E4,
    'camp_func_00282e6c': 0x00282E6C,
    'g_ComWinWork_0043e0f8': 0x0043E0F8,
    'g_ComWinSpriteTable_004038f0': 0x004038F0,
    'g_ComWinContext_004e2f68': 0x004E2F68,
    'g_InfoWinWork_0043e128': 0x0043E128,
    'g_InfoWinSpriteTable_00403aa8': 0x00403AA8,
    'g_GuestWinWork_0043e110': 0x0043E110,
    'g_GuestWinSpriteTable_00403a38': 0x00403A38,
    'g_NameMainManager_0044d180': 0x0044D180,
    'g_OnesRoomManager_0044d1c8': 0x0044D1C8,
    'g_EventFadeWork_0043e088': 0x0043E088,
    'g_EventEffectWork_0043dee8': 0x0043DEE8,
}

STRING_MAPS = {
    'h7_ui_comwin_init': {
        0x0: 0x0010A900,  # "ComWin Calc"
        0xC: 0x0010A910,  # "ComWin DrawUpLeft"
        0x1E: 0x0010A924, # "ComWin DrawUpRight"
    },
    'h7_ui_infowin_init': {
        0x0: 0x0010B168,  # "InfoWin Calc"
        0xD: 0x0010B17C,  # "InfoWin DrawUpLeft"
        0x1F: 0x0010B190, # "InfoWin DrawUpRight"
    },
    'h7_ui_guestwin_init': {
        0x0: 0x0010B4C8,  # "GuestWin Calc"
        0xE: 0x0010B4DC,  # "GuestWin DrawUpLeft"
        0x20: 0x0010B4F0, # "GuestWin DrawUpRight"
    },
    'h7_script_namemain_init': {
        0x0: 0x0040579C,  # "NameMainProc"
        0xD: 0x004057AC,  # "NameDrawUp"
        0x18: 0x004057B8, # "NameDrawDown"
    },
    'h7_script_onesroom_init': {
        0x0: 0x001D3A40,  # "ones_room/onesRoom.bf"
        0x17: 0x001D3A58, # "ones_room/onesRoom.mbm"
        0x2F: 0x001D3A78, # "onesRoom C"
    },
    'h7_script_eventcmd_fade': {
        0x0: 0x0025972C,  # "EventMessUnderFade_Proc"
        0x18: 0x00259748, # "EventMessUnderFade_Draw"
    },
    'h7_script_eventeffect_init': {
        0x0: 0x0030A6A8,  # "BlinkFade Calc"
        0xF: 0x0030A6BC,  # "BlinkFade DrawUpLeft"
        0x22: 0x0030A6D4, # "BlinkFade DrawUpRight"
    },
}

CANDIDATES = [
    {
        'id': 'h7_ui_comwin_init',
        'source': 'experiments/semantic_equivalence/h7_ui_comwin_init_candidate.cpp',
        'function': 'h7_ui_comwin_init_candidate',
        'vma': 0x0010A748,
        'window_size': 504,
        'opt': '-O2',
    },
    {
        'id': 'h7_ui_comwin_reset',
        'source': 'experiments/semantic_equivalence/h7_ui_comwin_reset_candidate.cpp',
        'function': 'h7_ui_comwin_reset_candidate',
        'vma': 0x0010AEE4,
        'window_size': 84,
        'opt': '-Oz',
    },
    {
        'id': 'h7_ui_infowin_init',
        'source': 'experiments/semantic_equivalence/h7_ui_infowin_init_candidate.cpp',
        'function': 'h7_ui_infowin_init_candidate',
        'vma': 0x0010AF84,
        'window_size': 560,
        'opt': '-O2',
    },
    {
        'id': 'h7_ui_guestwin_init',
        'source': 'experiments/semantic_equivalence/h7_ui_guestwin_init_candidate.cpp',
        'function': 'h7_ui_guestwin_init_candidate',
        'vma': 0x0010B350,
        'window_size': 448,
        'opt': '-O2',
    },
    {
        'id': 'h7_script_namemain_init',
        'source': 'experiments/semantic_equivalence/h7_script_namemain_init_candidate.cpp',
        'function': 'h7_script_namemain_init_candidate',
        'vma': 0x001D374C,
        'window_size': 408,
        'opt': '-O2',
    },
    {
        'id': 'h7_script_onesroom_init',
        'source': 'experiments/semantic_equivalence/h7_script_onesroom_init_candidate.cpp',
        'function': 'h7_script_onesroom_init_candidate',
        'vma': 0x001D38FC,
        'window_size': 392,
        'opt': '-O2',
    },
    {
        'id': 'h7_script_eventcmd_fade',
        'source': 'experiments/semantic_equivalence/h7_script_eventcmd_fade_candidate.cpp',
        'function': 'h7_script_eventcmd_fade_candidate',
        'vma': 0x0025955C,
        'window_size': 516,
        'opt': '-O2',
    },
    {
        'id': 'h7_script_eventeffect_init',
        'source': 'experiments/semantic_equivalence/h7_script_eventeffect_init_candidate.cpp',
        'function': 'h7_script_eventeffect_init_candidate',
        'vma': 0x0030A4FC,
        'window_size': 504,
        'opt': '-O2',
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

def stage_h7(base_path: Path, output_dir: Path) -> dict:
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
        if cand['opt'] == '-Oz':
            import subprocess
            cmd = [
                r'C:\msys64\clang64\bin\clang++.exe',
                '--target=armv6k-none-eabihf', '-mcpu=mpcore', '-mfpu=vfpv2', '-mfloat-abi=hard',
                '-Oz', '-std=c++20', '-fno-exceptions', '-fno-rtti', '-ffreestanding',
                '-nostdinc', '-nostdinc++',
                '-isystem', str(ROOT / 'include/freestanding'),
                '-isystem', r'C:\msys64\clang64\lib\clang\23\include',
                f'-I{ROOT / "include"}',
                '-c', str(src_path), '-o', str(obj_path)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
        else:
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
        str_map = STRING_MAPS.get(c_id, {})
        for r in relocs:
            if r.symbol_name in TARGET_SYMBOLS:
                tgt = TARGET_SYMBOLS[r.symbol_name]
            elif r.symbol_name == '':
                in_place = struct.unpack_from('<I', blob, r.offset)[0]
                if in_place in str_map:
                    tgt = str_map[in_place]
                else:
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

        # Overwrite candidate code into binary image
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
    final_bin_path = output_dir / 'code.h7-final.bin'
    final_bin_path.write_bytes(final_bin)
    final_sha = sha(final_bin)

    # Generate IPS mod patch relative to ORIGINAL
    diff_records = changed_records(original, final_bin)
    ips_bytes = encode_ips(diff_records, len(original))
    ips_path = output_dir / 'code.h7-final.ips'
    ips_path.write_bytes(ips_bytes)
    ips_sha = sha(ips_bytes)

    # Verify IPS round-trip
    roundtrip = apply_ips(original, ips_bytes)
    if roundtrip != final_bin:
        raise ValueError('IPS roundtrip verification failed!')

    manifest = {
        'status': 'passed',
        'milestone': 'H7',
        'base_binary': str(base_path),
        'base_sha256': BASE_SHA,
        'final_binary': str(final_bin_path),
        'final_sha256': final_sha,
        'ips_patch': str(ips_path),
        'ips_sha256': ips_sha,
        'ips_patch_size': len(ips_bytes),
        'candidates_count': len(candidate_reports),
        'total_original_bytes': sum(c['window_size'] for c in candidate_reports),
        'total_compiled_bytes': sum(c['compiled_size'] for c in candidate_reports),
        'total_margin_bytes': sum(c['padding_nop_bytes'] for c in candidate_reports),
        'candidates': candidate_reports,
    }

    manifest_path = output_dir / 'staging-manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path, default=DEFAULT_BASE)
    parser.add_argument('--out', type=Path, default=ROOT / 'build/agent-work/H7-semantic/h7-integrated-stage')
    args = parser.parse_args()

    manifest = stage_h7(args.base, args.out)
    print(f'H7 Staged Image Patch SUCCESS:')
    print(f'  Final binary: {manifest["final_binary"]} ({manifest["final_sha256"]})')
    print(f'  IPS patch:    {manifest["ips_patch"]} ({manifest["ips_sha256"]}, {manifest["ips_patch_size"]} bytes)')
    print(f'  Candidates:   {manifest["candidates_count"]} reconstructed subsystems')
    print(f'  Compiled:     {manifest["total_compiled_bytes"]} B / {manifest["total_original_bytes"]} B (+{manifest["total_margin_bytes"]} B margin)')

if __name__ == '__main__':
    main()
