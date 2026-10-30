#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00322F0C SaveLoadProcess_Close."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h6_saveload_process_close_candidate.cpp'
ORIG_ADDR = 0x00322F0C
ORIG_SIZE = 304
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'Subsystem_Reset_0026b7ec': 0x0026B7EC,
    'Subsystem_Reset_002594cc': 0x002594CC,
    'Subsystem_Reset_002594ac': 0x002594AC,
    'GetContext_002c0b94': 0x002C0B94,
    'AsdTask_Create': 0x002C5978,
    'AsdTask_SetFlags': 0x001EC8E4,
    'SaveLoadProcess_Write': 0x002EFB50,
    'g_SaveLoadContext_0043e2f0': 0x0043E2F0,
    'g_szSave_00323034': 0x00323034,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h6_saveload_process_close.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h6_saveload_process_close_candidate']
    raw_mut, _ = funcs['h6_saveload_process_close_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, slot: int, difficulty: int) -> tuple[int, bytes, bytes]:
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

    WORK_BUF = HEAP_BASE + 0x2000
    TASK_HANDLE = 0x08050000
    CTX_BUF = HEAP_BASE + 0x4000
    uc.mem_write(CTX_BUF, b'\x00\x00\x00\x01')

    # Mock helpers
    # AsdMem_Alloc: return WORK_BUF
    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', WORK_BUF))
    # Subsystem resets: return 0
    uc.mem_write(0x0026B7EC, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002594CC, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002594AC, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    # GetContext_002c0b94: return CTX_BUF
    uc.mem_write(0x002C0B94, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', CTX_BUF))
    # AsdTask_Create: return TASK_HANDLE
    uc.mem_write(0x002C5978, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', TASK_HANDLE))
    # AsdTask_SetFlags: return 0
    uc.mem_write(0x001EC8E4, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_R0, slot)
    uc.reg_write(UC_ARM_REG_R1, difficulty)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=2000000, count=5000)
    ret_r0 = uc.reg_read(UC_ARM_REG_R0)
    work_out = uc.mem_read(WORK_BUF, 0x18)
    ctx_out = uc.mem_read(0x0043E2F0, 0x10)
    return ret_r0, work_out, ctx_out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'build/h6_saveload_process_close_test.json')
    args = parser.parse_args()

    with open(CODE_PATH, 'rb') as f:
        code_bytes = f.read()

    out_dir = ROOT / 'build/h6_candidates'
    blob_cand, raw_cand, blob_mut, raw_mut = build_candidates(out_dir)

    test_cases = [
        (0, 0),
        (1, 1),
        (2, 2),
        (3, 3),
    ]
    results = []
    all_matched = True

    for slot, diff in test_cases:
        r0_orig, w_orig, c_orig = run_simulation(code_bytes, blob_cand, ORIG_ADDR, slot, diff)
        r0_cand, w_cand, c_cand = run_simulation(code_bytes, blob_cand, CAND_ADDR, slot, diff)
        matched = (r0_orig == r0_cand) and (w_orig == w_cand) and (c_orig == c_cand)
        results.append({
            'slot': slot, 'difficulty': diff,
            'r0_orig': r0_orig, 'r0_cand': r0_cand,
            'work_matched': (w_orig == w_cand),
            'ctx_matched': (c_orig == c_cand),
            'matched': matched
        })
        if not matched: all_matched = False

    # Mutation test (returns nullptr)
    r0_mut, _, _ = run_simulation(code_bytes, blob_mut, CAND_ADDR, 1, 1)
    mutation_detected = (r0_mut == 0)

    report = {
        'candidate': 'SaveLoadProcess_Close',
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
    print(f'H6 SaveLoadProcess_Close: status={report["status"]}, matched={all_matched}, mut_detected={mutation_detected}')
    assert report['status'] == 'passed'

if __name__ == '__main__':
    main()
