#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0022FCC8 Shop_CheckHasSpecialStockItem."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h11_shop_checkhasspecial_candidate.cpp'
ORIG_ADDR = 0x0022FCC8
ORIG_SIZE = 48
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'shop_func_0026f0d8': 0x0026F0D8,
    'shop_func_002b902c': 0x002B902C,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h11_shop_checkhasspecial.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h11_shop_checkhasspecial_candidate']
    raw_mut, _ = funcs['h11_shop_checkhasspecial_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)
    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, ret1: int, ret2: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    stub1 = struct.pack('<II', 0xE3A00000 | (ret1 & 0xFF), 0xE12FFF1E)
    uc.mem_write(0x0026F0D8, stub1)
    stub2 = struct.pack('<II', 0xE3A00000 | (ret2 & 0xFF), 0xE12FFF1E)
    uc.mem_write(0x002B902C, stub2)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, 0)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    with open(CODE_PATH, 'rb') as f:
        image = f.read()

    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h11_differential')

    cases = [(0, 0), (1, 0), (0, 1), (1, 1)]
    for r1, r2 in cases:
        orig = run_simulation(image, cand_blob, ORIG_ADDR, r1, r2)
        cand = run_simulation(image, cand_blob, CAND_ADDR, r1, r2)
        assert orig == cand, f'Mismatch in Shop_CheckHasSpecial ({r1}, {r2}): {orig} != {cand}'

    orig = run_simulation(image, cand_blob, ORIG_ADDR, 0, 0)
    mut = run_simulation(image, mut_blob, CAND_ADDR, 0, 0)
    assert orig != mut, 'Mutation failed'
    print('h11_shop_checkhasspecial: ALL CASES PASSED')

if __name__ == '__main__':
    main()
