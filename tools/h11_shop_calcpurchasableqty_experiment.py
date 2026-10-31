#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00230DB0 Shop_CalcPurchasableQty."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h11_shop_calcpurchasableqty_candidate.cpp'
ORIG_ADDR = 0x00230DB0
ORIG_SIZE = 100
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'sub_22EBBC': 0x0022EBBC,
    'sub_2C615C': 0x002C615C,
    'sub_2B9100': 0x002B9100,
    'sub_28FDE4': 0x0028FDE4,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h11_shop_calcpurchasableqty.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h11_shop_calcpurchasableqty_candidate']
    raw_mut, _ = funcs['h11_shop_calcpurchasableqty_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)
    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, stock: int, max_bag: int, cur_bag: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Mock sub_22EBBC -> returns 0
    uc.mem_write(0x0022EBBC, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    # Mock sub_2C615C -> returns stock
    uc.mem_write(0x002C615C, struct.pack('<III', 0xE59F0000, 0xE12FFF1E, stock & 0xFFFFFFFF))
    # Mock sub_2B9100 -> returns max_bag
    uc.mem_write(0x002B9100, struct.pack('<III', 0xE59F0000, 0xE12FFF1E, max_bag & 0xFFFFFFFF))
    # Mock sub_28FDE4 -> returns cur_bag
    uc.mem_write(0x0028FDE4, struct.pack('<III', 0xE59F0000, 0xE12FFF1E, cur_bag & 0xFFFFFFFF))

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, 0x08000000)
    uc.reg_write(UC_ARM_REG_R1, 0x10)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    val = uc.reg_read(UC_ARM_REG_R0)
    if val >= 0x80000000:
        val -= 0x100000000
    return val

def main():
    with open(CODE_PATH, 'rb') as f:
        image = f.read()

    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h11_differential')

    cases = [
        (10, 50, 20),  # stock 10, remaining 30 -> 10
        (40, 50, 20),  # stock 40, remaining 30 -> 30
        (150, 50, 20), # stock 150 clamped to 99, remaining 30 -> 30
        (-5, 50, 20),  # stock -5 -> 0
        (10, 50, 55),  # stock 10, remaining -5 -> -5 or 0
    ]

    for stock, m_bag, c_bag in cases:
        orig = run_simulation(image, cand_blob, ORIG_ADDR, stock, m_bag, c_bag)
        cand = run_simulation(image, cand_blob, CAND_ADDR, stock, m_bag, c_bag)
        assert orig == cand, f'Mismatch in Shop_CalcPurchasableQty ({stock}, {m_bag}, {c_bag}): {orig} != {cand}'

    orig = run_simulation(image, cand_blob, ORIG_ADDR, 10, 50, 20)
    mut = run_simulation(image, mut_blob, CAND_ADDR, 10, 50, 20)
    assert orig != mut, 'Mutation failed'
    print('h11_shop_calcpurchasableqty: ALL CASES PASSED')

if __name__ == '__main__':
    main()
