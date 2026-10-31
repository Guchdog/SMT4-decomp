#!/usr/bin/env python3
"""Offline ARM differential validation for H11 Shops promoted module (0x0022FC98)."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'src/semantic/h11_shops_promoted.cpp'
ORIG_ADDR = 0x0022FC98
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
    obj_path = out_dir / 'h11_shops_promoted.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h11_shop_checkhasnew_promoted']
    raw_mut, relocs_mut = funcs['h11_shop_checkhasnew_mutation']

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

    return bytes(blob_cand), bytes(blob_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, ret_f6: int, ret_f7: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    # Stub 0x0026F0D8: mov r0, #ret_f6; bx lr
    stub_f6 = struct.pack('<II', 0xE3A00000 | (ret_f6 & 0xFF), 0xE12FFF1E)
    uc.mem_write(0x0026F0D8, stub_f6)

    # Stub 0x002B902C: mov r0, #ret_f7; bx lr
    stub_f7 = struct.pack('<II', 0xE3A00000 | (ret_f7 & 0xFF), 0xE12FFF1E)
    uc.mem_write(0x002B902C, stub_f7)

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h18_tests')

    cases = [(0, 0), (1, 0), (0, 1), (1, 1)]
    for f6, f7 in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, f6, f7)
        cand = run_simulation(code, cand_blob, CAND_ADDR, f6, f7)
        mut = run_simulation(code, mut_blob, CAND_ADDR, f6, f7)
        assert orig == cand, f'Mismatch for ({f6}, {f7}): orig={orig}, cand={cand}'
        assert orig != mut, f'Mutation undetected for ({f6}, {f7})'

    print('[PASS] H18 Shops Promoted Module: 100% parity across vectors, mutations detected.')

if __name__ == '__main__':
    main()
