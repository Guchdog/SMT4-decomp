#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0021041C AsdSaveCommon_func_0021041c."""
from __future__ import annotations
import argparse, json, struct, sys
from pathlib import Path

import unicorn
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h6_asd_save_common_read_candidate.cpp'
ORIG_ADDR = 0x0021041C
ORIG_SIZE = 204
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c54f0': 0x002C54F0,
    'AsdMem_Free': 0x002C4360,
    'AsdMem_CopyFrom': 0x002BD610,
    'AsdSave_Read': 0x002F5348,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h6_asd_save_common_read.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h6_asd_save_common_read_candidate']
    raw_mut, _ = funcs['h6_asd_save_common_read_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        tgt = TARGET_SYMBOLS.get(r.symbol_name, 0)
        reloc_vma = CAND_ADDR + r.offset
        if r.relocation_type == 2:
            struct.pack_into('<I', blob_cand, r.offset, tgt)
        elif r.relocation_type in (28, 29):
            w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
            struct.pack_into('<I', blob_cand, r.offset, w)

    return bytes(blob_cand), raw_cand, raw_mut, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, device: int, file: int, payload_size: int) -> tuple[int, bytes]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, cand_blob + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    HEAP_BASE = 0x08000000
    uc.mem_map(HEAP_BASE, 0x100000, unicorn.UC_PROT_ALL)

    HEADER_BUF = 0x09000000
    PAYLOAD_BUF = 0x09010000
    uc.mem_map(0x09000000, 0x40000, unicorn.UC_PROT_ALL)

    # Mock helpers
    # AsdMem_Alloc(heap, flag, unused, size, align): return HEAP_BASE + 0x1000
    uc.mem_write(0x002C54F0, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', HEAP_BASE + 0x1000))
    # AsdMem_Free: return 0
    uc.mem_write(0x002C4360, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    # AsdSave_Read: write dummy pattern to buffer (r2), return 1 (success)
    # asm: mov r0, #1; bx lr
    uc.mem_write(0x002F5348, struct.pack('<II', 0xE3A00001, 0xE12FFF1E))
    # Fill staging buffer with identifiable test pattern
    uc.mem_write(HEAP_BASE + 0x1000, b'\x42' * (payload_size + 0x80))

    # Pass 5th argument on stack: payload_size
    uc.mem_write(SP_INIT, struct.pack('<I', payload_size))

    uc.reg_write(UC_ARM_REG_R0, device)
    uc.reg_write(UC_ARM_REG_R1, file)
    uc.reg_write(UC_ARM_REG_R2, HEADER_BUF)
    uc.reg_write(UC_ARM_REG_R3, PAYLOAD_BUF)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=2000000, count=200000)
    ret_r0 = uc.reg_read(UC_ARM_REG_R0)
    hdr_out = uc.mem_read(HEADER_BUF, 0x80)
    return ret_r0, hdr_out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'build/h6_asd_save_common_read_test.json')
    args = parser.parse_args()

    with open(CODE_PATH, 'rb') as f:
        code_bytes = f.read()

    out_dir = ROOT / 'build/h6_candidates'
    blob_cand, raw_cand, blob_mut, raw_mut = build_candidates(out_dir)

    test_cases = [
        (0, 1, 0x100),
        (1, 0, 0x200),
        (2, 2, 0x1000),
        (3, 1, 0x24DB0 - 0x80),
    ]

    results = []
    all_matched = True

    for dev, fil, sz in test_cases:
        r0_orig, h_orig = run_simulation(code_bytes, blob_cand, ORIG_ADDR, dev, fil, sz)
        r0_cand, h_cand = run_simulation(code_bytes, blob_cand, CAND_ADDR, dev, fil, sz)
        matched = (r0_orig == r0_cand) and (h_orig == h_cand)
        results.append({
            'device': dev, 'file': fil, 'size': sz,
            'r0_orig': r0_orig, 'r0_cand': r0_cand,
            'matched': matched
        })
        if not matched: all_matched = False

    # Mutation test
    r0_mut, _ = run_simulation(code_bytes, blob_mut, CAND_ADDR, 0, 1, 0x100)
    mutation_detected = (r0_mut != 1)

    report = {
        'candidate': 'AsdSaveCommon_func_0021041c',
        'orig_size': ORIG_SIZE,
        'cand_size': len(raw_cand),
        'fits': len(raw_cand) <= ORIG_SIZE,
        'all_matched': all_matched,
        'mutation_detected': mutation_detected,
        'status': 'passed' if (all_matched and mutation_detected) else 'failed',
        'cases': results
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'H6 AsdSaveCommon_Read: status={report["status"]}, matched={all_matched}, mut_detected={mutation_detected}')
    assert report['status'] == 'passed'

if __name__ == '__main__':
    main()
