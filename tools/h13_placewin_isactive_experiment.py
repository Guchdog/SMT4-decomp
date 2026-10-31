#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0026394C PlaceWin_IsActive."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h13_placewin_isactive_candidate.cpp'
ORIG_ADDR = 0x0026394C
ORIG_SIZE = 44
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h13_placewin_isactive.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h13_placewin_isactive_candidate']
    raw_mut, _ = funcs['h13_placewin_isactive_mutation']
    return raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, timer_present: bool, elapsed: float, duration: float) -> int:
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

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    HOLDER_BUF = MEM_BASE + 0x100
    TIMER_BUF = MEM_BASE + 0x200

    if timer_present:
        uc.mem_write(HOLDER_BUF + 4, struct.pack('<I', TIMER_BUF))
        uc.mem_write(TIMER_BUF + 0x38, struct.pack('<f', duration))
        uc.mem_write(TIMER_BUF + 0x48, struct.pack('<f', elapsed))
    else:
        uc.mem_write(HOLDER_BUF + 4, struct.pack('<I', 0))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, HOLDER_BUF)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h13_tests')

    cases = [
        (False, 0.0, 0.0),       # Null timer -> 1
        (True, 0.0, 5.0),        # 0.0 <= 5.0 -> 1
        (True, 4.9, 5.0),        # 4.9 <= 5.0 -> 1
        (True, 5.0, 5.0),        # 5.0 <= 5.0 -> 1
        (True, 5.0001, 5.0),     # 5.0001 > 5.0 -> 0
        (True, 10.0, 5.0),       # 10.0 > 5.0 -> 0
    ]

    for timer_present, elapsed, duration in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, timer_present, elapsed, duration)
        cand = run_simulation(code, cand_blob, CAND_ADDR, timer_present, elapsed, duration)
        mut = run_simulation(code, mut_blob, CAND_ADDR, timer_present, elapsed, duration)

        if orig != cand:
            raise AssertionError(f'Mismatch for timer={timer_present}, el={elapsed}, dur={duration}: orig={orig}, cand={cand}')
        if orig == 1 and mut == 1:
            raise AssertionError(f'Mutation undetected for timer={timer_present}')

    print(f'[PASS] h13_placewin_isactive: 100% parity across {len(cases)} cases, mutation sensitivity verified.')

if __name__ == '__main__':
    main()
