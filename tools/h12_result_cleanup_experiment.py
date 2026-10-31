#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001C87D8 Result_Cleanup."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h12_result_cleanup_candidate.cpp'
ORIG_ADDR = 0x001C87D8
ORIG_SIZE = 156
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_ResultWork_0044dc20': 0x0044DC20,
    'sub_2A755C': 0x002A755C,
    'sub_2C4360': 0x002C4360,
    'sub_2C0128': 0x002C0128,
    'sub_2A497C': 0x002A497C,
    'sub_2AEB2C': 0x002AEB2C,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h12_result_cleanup.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h12_result_cleanup_candidate']
    raw_mut, relocs_mut = funcs['h12_result_cleanup_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)
            elif r.relocation_type == 2:
                struct.pack_into('<I', blob_cand, r.offset, tgt)

    blob_mut = bytearray(raw_mut)
    for r in relocs_mut:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_mut, r.offset, w)
            elif r.relocation_type == 2:
                struct.pack_into('<I', blob_mut, r.offset, tgt)

    return bytes(blob_cand), raw_cand, bytes(blob_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, has_work: bool) -> bytes:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Stub the 5 subroutines: bx lr
    bx_lr = struct.pack('<I', 0xE12FFF1E)
    uc.mem_write(0x002A755C, bx_lr)
    uc.mem_write(0x002C4360, bx_lr)
    uc.mem_write(0x002C0128, bx_lr)
    uc.mem_write(0x002A497C, bx_lr)
    uc.mem_write(0x002AEB2C, bx_lr)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    WORK_ADDR = 0x08000000
    if has_work:
        uc.mem_write(0x0044DC20, struct.pack('<I', WORK_ADDR))
        # Set pointers inside work structure
        uc.mem_write(WORK_ADDR + 0x3564, struct.pack('<I', 0x08004000))
        uc.mem_write(WORK_ADDR + 0x3568, struct.pack('<I', 0x08005000))
        uc.mem_write(WORK_ADDR + 0x356C, struct.pack('<I', 0x08006000))
        uc.mem_write(WORK_ADDR + 0x3570, struct.pack('<I', 0x08007000))
    else:
        uc.mem_write(0x0044DC20, struct.pack('<I', 0))

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.mem_read(0x0044DC20, 4)

def main():
    image = CODE_PATH.read_bytes()
    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h12_test')

    for hw in [True, False]:
        orig = run_simulation(image, cand_blob, ORIG_ADDR, hw)
        cand = run_simulation(image, cand_blob, CAND_ADDR, hw)
        assert orig == cand, f'Mismatch in Result_Cleanup (has_work={hw}): {orig} != {cand}'

    orig = run_simulation(image, cand_blob, ORIG_ADDR, True)
    mut = run_simulation(image, mut_blob, CAND_ADDR, True)
    assert orig != mut, 'Mutation failed'
    print('h12_result_cleanup: ALL CASES PASSED')

if __name__ == '__main__':
    main()
