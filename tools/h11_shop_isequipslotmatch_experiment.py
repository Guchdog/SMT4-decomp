#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00230D24 Shop_IsEquipSlotMatch."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h11_shop_isequipslotmatch_candidate.cpp'
ORIG_ADDR = 0x00230D24
ORIG_SIZE = 140
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'sub_2B66EC': 0x002B66EC,
    'sub_2AE64C': 0x002AE64C,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h11_shop_isequipslotmatch.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h11_shop_isequipslotmatch_candidate']
    raw_mut, _ = funcs['h11_shop_isequipslotmatch_mutation']

    blob_cand = bytearray(raw_cand)
    RODATA_ADDR = 0x08000500
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)
        elif r.relocation_type == 2: # R_ARM_ABS32 to local rodata
            struct.pack_into('<I', blob_cand, r.offset, RODATA_ADDR)
    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, cat: int, item_id: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    TABLE_ADDR = 0x08000000
    uc.mem_map(TABLE_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    # Equipment table entries at offsets 0, 2, 4, 6, 8, 10, 12:
    # 0: 0x100, 2: 0x200, 4: 0x800 (cat 8), 6: 0x300, 8: 0x400, 10: 0x500, 12: 0x600
    table_data = struct.pack('<HHHHHHH', 0x100, 0x200, 0x800, 0x300, 0x400, 0x500, 0x600)
    uc.mem_write(TABLE_ADDR, table_data)

    # Write local rodata table for candidate
    RODATA_ADDR = 0x08000500
    uc.mem_write(RODATA_ADDR, bytes([0, 2, 6, 8, 10, 12, 4]))

    # Mock sub_2B66EC: return TABLE_ADDR
    stub_b6 = struct.pack('<III', 0xE59F0000, 0xE12FFF1E, TABLE_ADDR) # ldr r0, [pc]; bx lr; .word TABLE_ADDR
    uc.mem_write(0x002B66EC, stub_b6)

    # Mock sub_2AE64C: return cat
    stub_ae = struct.pack('<II', 0xE3A00000 | (cat & 0xFF), 0xE12FFF1E)
    uc.mem_write(0x002AE64C, stub_ae)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, 0)
    uc.reg_write(UC_ARM_REG_R1, item_id)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    with open(CODE_PATH, 'rb') as f:
        image = f.read()

    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h11_differential')

    cases = [
        (2, 0x100), # cat 2 matches offset 0
        (2, 0x999), # mismatch
        (3, 0x200), # cat 3 matches offset 2
        (4, 0x300), # cat 4 matches offset 6
        (5, 0x400), # cat 5 matches offset 8
        (6, 0x500), # cat 6 matches offset 10
        (7, 0x600), # cat 7 matches offset 12
        (8, 0x800), # cat 8 matches offset 4
        (1, 0x100), # out of range cat
        (9, 0x100), # out of range cat
    ]

    for cat, item_id in cases:
        orig = run_simulation(image, cand_blob, ORIG_ADDR, cat, item_id)
        cand = run_simulation(image, cand_blob, CAND_ADDR, cat, item_id)
        assert orig == cand, f'Mismatch in Shop_IsEquipSlotMatch (cat={cat}, id={item_id}): {orig} != {cand}'

    orig = run_simulation(image, cand_blob, ORIG_ADDR, 2, 0x100)
    mut = run_simulation(image, mut_blob, CAND_ADDR, 2, 0x100)
    assert orig != mut, 'Mutation failed'
    print('h11_shop_isequipslotmatch: ALL CASES PASSED')

if __name__ == '__main__':
    main()
