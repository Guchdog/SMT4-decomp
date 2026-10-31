#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00230680 Shop_PushItemRecord."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h11_shop_pushitemrecord_candidate.cpp'
ORIG_ADDR = 0x00230680
ORIG_SIZE = 108
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h11_shop_pushitemrecord.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h11_shop_pushitemrecord_candidate']
    raw_mut, _ = funcs['h11_shop_pushitemrecord_mutation']
    return raw_cand, raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, items: list[tuple[int, int, int, int]]) -> bytes:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    BUF_ADDR = 0x08000000
    uc.mem_map(BUF_ADDR, 0x2000, unicorn.UC_PROT_ALL)

    RETURN_ADDR = 0x00100004
    for item_id, f1, f2, f3 in items:
        uc.reg_write(UC_ARM_REG_SP, SP_INIT)
        # Push 5th arg to stack at [sp]
        uc.mem_write(SP_INIT, struct.pack('<I', f3))
        uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
        uc.reg_write(UC_ARM_REG_R0, BUF_ADDR)
        uc.reg_write(UC_ARM_REG_R1, item_id)
        uc.reg_write(UC_ARM_REG_R2, f1)
        uc.reg_write(UC_ARM_REG_R3, f2)
        uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)

    return uc.mem_read(BUF_ADDR, 0x1010)

def main():
    with open(CODE_PATH, 'rb') as f:
        image = f.read()

    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h11_differential')

    items = [
        (0x1234, 1, 0, 0x45),
        (0x5678, 0, 1, 0x7A),
        (0x0ABC, 1, 1, 0xFF),
    ]

    orig_out = run_simulation(image, cand_blob, ORIG_ADDR, items)
    cand_out = run_simulation(image, cand_blob, CAND_ADDR, items)
    assert orig_out == cand_out, 'Mismatch in Shop_PushItemRecord'

    mut_out = run_simulation(image, mut_blob, CAND_ADDR, items)
    assert orig_out != mut_out, 'Mutation failed'
    print('h11_shop_pushitemrecord: ALL CASES PASSED')

if __name__ == '__main__':
    main()
