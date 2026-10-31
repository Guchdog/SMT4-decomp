#!/usr/bin/env python3
"""Offline ARM differential validation for 0x003878C0 TextureStreamer_Compare."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h14_texturestreamer_compare_candidate.cpp'
ORIG_ADDR = 0x003878C0
ORIG_SIZE = 16
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h14_texturestreamer_compare.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h14_texturestreamer_compare_candidate']
    raw_mut, _ = funcs['h14_texturestreamer_compare_mutation']
    return raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, val_a: int, val_b: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    PTR_A = MEM_BASE + 0x100
    PTR_B = MEM_BASE + 0x200
    uc.mem_write(PTR_A, struct.pack('<H', val_a))
    uc.mem_write(PTR_B, struct.pack('<H', val_b))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, PTR_A)
    uc.reg_write(UC_ARM_REG_R1, PTR_B)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    # Read signed 32-bit result
    ret = uc.reg_read(UC_ARM_REG_R0)
    if ret >= 0x80000000:
        ret -= 0x100000000
    return ret

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h14_tests')

    pairs = [
        (10, 10),    # 0
        (50, 20),    # +30
        (20, 50),    # -30
        (0, 0xFFFF), # negative
        (0xFFFF, 0), # positive
    ]

    for a, b in pairs:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, a, b)
        cand = run_simulation(code, cand_blob, CAND_ADDR, a, b)
        mut = run_simulation(code, mut_blob, CAND_ADDR, a, b)

        if orig != cand or cand != (a - b):
            raise AssertionError(f'Mismatch for ({a}, {b}): orig={orig}, cand={cand}')
        if a != b and orig == mut:
            raise AssertionError(f'Mutation undetected for ({a}, {b})')

    print(f'[PASS] h14_texturestreamer_compare: 100% parity across {len(pairs)} pairs, comparator verified.')

if __name__ == '__main__':
    main()
