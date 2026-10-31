#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00121150 AsdSoundEffect2_SetBuffer."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h16_asdsoundeffect2_setbuffer_candidate.cpp'
ORIG_ADDR = 0x00121150
ORIG_SIZE = 24
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h16_asdsoundeffect2_setbuffer.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h16_asdsoundeffect2_setbuffer_candidate']
    raw_mut, _ = funcs['h16_asdsoundeffect2_setbuffer_mutation']
    return bytes(raw_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, buf_ptr: int, size_val: int) -> tuple[int, int, int]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000
    SELF_ADDR = STACK_BASE + 0x4000

    uc.mem_write(SELF_ADDR + 0x30, struct.pack('<II', 0, 0))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_R1, buf_ptr)
    uc.reg_write(UC_ARM_REG_R2, size_val)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)

    ret_r0 = uc.reg_read(UC_ARM_REG_R0)
    stored_buf, stored_sz = struct.unpack('<II', uc.mem_read(SELF_ADDR + 0x30, 8))
    return ret_r0, stored_buf, stored_sz

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h16_tests')

    cases = [
        (0x0FFF5000, 2048),
        (0x0FFF6000, 8192),
        (0, 1024),
        (0, 0),
    ]

    for buf_ptr, size_val in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, buf_ptr, size_val)
        cand = run_simulation(code, cand_blob, CAND_ADDR, buf_ptr, size_val)
        mut = run_simulation(code, mut_blob, CAND_ADDR, buf_ptr, size_val)

        if orig != cand:
            raise AssertionError(f'Mismatch for ({buf_ptr}, {size_val}): orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for ({buf_ptr}, {size_val})')

    print(f'[PASS] h16_asdsoundeffect2_setbuffer: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
