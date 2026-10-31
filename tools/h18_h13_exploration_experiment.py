#!/usr/bin/env python3
"""Offline ARM differential validation for H13 Exploration promoted module (0x0026394C)."""
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
SRC_PATH = ROOT / 'src/semantic/h13_exploration_promoted.cpp'
ORIG_ADDR = 0x0026394C
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h13_exploration_promoted.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h13_placewin_isactive_promoted']
    raw_mut, relocs_mut = funcs['h13_placewin_isactive_mutation']
    return bytes(raw_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, has_timer: bool, elapsed: float, duration: float) -> int:
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

    HOLDER_ADDR = 0x0FFF2000
    TIMER_ADDR = 0x0FFF3000

    if has_timer:
        uc.mem_write(HOLDER_ADDR + 4, struct.pack('<I', TIMER_ADDR))
        uc.mem_write(TIMER_ADDR + 0x38, struct.pack('<f', duration))
        uc.mem_write(TIMER_ADDR + 0x48, struct.pack('<f', elapsed))
    else:
        uc.mem_write(HOLDER_ADDR + 4, struct.pack('<I', 0))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, HOLDER_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h18_tests')

    cases = [
        (False, 0.0, 0.0),
        (True, 1.0, 2.0),
        (True, 2.0, 2.0),
        (True, 3.0, 2.0),
    ]
    for has_timer, elapsed, duration in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, has_timer, elapsed, duration)
        cand = run_simulation(code, cand_blob, CAND_ADDR, has_timer, elapsed, duration)
        mut = run_simulation(code, mut_blob, CAND_ADDR, has_timer, elapsed, duration)
        assert orig == cand, f'Mismatch for ({has_timer}, {elapsed}, {duration}): orig={orig}, cand={cand}'
        if orig != 0:
            assert orig != mut, f'Mutation undetected'

    print('[PASS] H18 Exploration Promoted Module: 100% parity across vectors, mutations detected.')

if __name__ == '__main__':
    main()
