#!/usr/bin/env python3
"""Stage and compose all validated H4 semantic candidates over the H1/H2/H3 composite image."""
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
DEFAULT_BASE = ROOT / 'build/agent-work/H3-semantic/h3-title-entry/in-place-patch-run002/code.h3-final.bin'
ORIGINAL_SHA = '1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
BASE_SHA = 'af2bc749364703ac11d1b663527a1ea339c571e14f89e0aa4e919c58f71436d8'
TEXT_BASE = 0x00100000

TARGET_SYMBOLS = {
    'h4_original_deadzone': 0x0019FE4C,
    'AsdMem_Alloc_002c23f8': 0x002C23F8,
    'ui_subobject_constructor_00294a98': 0x00294A98,
    'ui_subobject_load_player_00294a64': 0x00294A64,
    'ui_subobject_set_channel_active_00343e90': 0x00343E90,
    'ui_subobject_set_channel_default_002946f4': 0x002946F4,
    'ActorManager_Lookup_002c45b8': 0x002C45B8,
    'Resource_Release_002a7aa0': 0x002A7AA0,
}

CANDIDATES = [
    {
        'id': 'h4_axis_reader',
        'source': 'experiments/semantic_equivalence/h4_axis_reader_candidate.cpp',
        'function': 'h4_axis_reader_candidate',
        'vma': 0x0027FBC8,
        'window_size': 320,
    },
    {
        'id': 'h4_view_init',
        'source': 'experiments/semantic_equivalence/h4_view_init_candidate.cpp',
        'function': 'h4_view_init_candidate',
        'vma': 0x001B4664,
        'window_size': 440,
    },
    {
        'id': 'h4_view_subobjects',
        'source': 'experiments/semantic_equivalence/h4_view_subobjects_candidate.cpp',
        'function': 'h4_view_subobjects_candidate',
        'vma': 0x001B481C,
        'window_size': 164,
    },
    {
        'id': 'h4_map_player_actor',
        'source': 'experiments/semantic_equivalence/h4_map_player_actor_candidate.cpp',
        'function': 'h4_map_player_actor_candidate',
        'vma': 0x001B45C8,
        'window_size': 24,
    },
    {
        'id': 'h4_map_entity_pool',
        'source': 'experiments/semantic_equivalence/h4_map_entity_pool_candidate.cpp',
        'function': 'h4_map_entity_pool_candidate',
        'vma': 0x001B45E0,
        'window_size': 132,
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

def stage_h4(base_path: Path, output_dir: Path) -> dict:
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
            if r.symbol_name not in TARGET_SYMBOLS:
                raise KeyError(f'Relocation symbol {r.symbol_name} in {c_id} not recognized')
            tgt = TARGET_SYMBOLS[r.symbol_name]
            is_bl = (r.relocation_type == 28)
            reloc_vma = vma + r.offset
            
            # Check ARM/Thumb interworking bit (must be 0 for ARM)
            if tgt & 1 != 0 or reloc_vma & 3 != 0:
                raise ValueError(f'Interworking alignment violation at 0x{reloc_vma:08X} -> 0x{tgt:08X}')
            
            w = branch_word(reloc_vma, tgt, is_bl=is_bl)
            struct.pack_into('<I', blob, r.offset, w)
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
        
        # Apply in-place
        patched_image[offset:offset + win_size] = blob
        
        candidate_reports.append({
            'id': c_id,
            'vma': hex(vma),
            'offset': hex(offset),
            'candidate_bytes': len(raw_code),
            'window_bytes': win_size,
            'source_sha256': sha(src_path.read_bytes()),
            'object_sha256': sha(obj_path.read_bytes()),
            'relocations': resolved_relocs,
        })
    
    final_image = bytes(patched_image)
    image_sha = sha(final_image)
    
    # Generate IPS patch
    records = changed_records(original, final_image)
    ips = encode_ips(records, len(original))
    if apply_ips(original, ips) != final_image:
        raise ValueError('IPS round trip verification failed')
    
    ips_sha = sha(ips)
    
    # Write files
    image_file = output_dir / 'code.h4-final.bin'
    ips_file = output_dir / 'code.h4-final.ips'
    image_file.write_bytes(final_image)
    ips_file.write_bytes(ips)
    
    manifest = {
        'status': 'passed',
        'scope': 'H1/H2/H3 composite base plus in-place H4 candidates',
        'original_sha256': ORIGINAL_SHA,
        'base_sha256': sha(base),
        'final_image_sha256': image_sha,
        'ips_sha256': ips_sha,
        'ips_records': len(records),
        'candidates': candidate_reports,
        'image_path': str(image_file),
        'ips_path': str(ips_file),
    }
    
    (output_dir / 'report.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=DEFAULT_BASE, help='Path to composite base image')
    parser.add_argument('--output', type=Path, required=True, help='Output directory')
    args = parser.parse_args()
    
    manifest = stage_h4(args.base, args.output)
    print(json.dumps({
        'status': manifest['status'],
        'candidates_staged': len(manifest['candidates']),
        'final_image_sha256': manifest['final_image_sha256'],
        'ips_sha256': manifest['ips_sha256'],
        'ips_records': manifest['ips_records'],
    }, indent=2))

if __name__ == '__main__':
    main()
