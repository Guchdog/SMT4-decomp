#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0028DE4C Battle_IsUnitDefeated."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h12_battle_isunitdefeated_candidate.cpp'
ORIG_ADDR = 0x0028DE4C
ORIG_SIZE = 56
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h12_battle_isunitdefeated.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h12_battle_isunitdefeated_candidate']
    raw_mut, _ = funcs['h12_battle_isunitdefeated_mutation']
    return raw_cand, raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, flags: int, hp: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    UNIT_ADDR = 0x08001000
    uc.mem_write(UNIT_ADDR + 0x44A0, struct.pack('<I', flags))
    uc.mem_write(UNIT_ADDR + 0xC4, struct.pack('<i', hp))

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, UNIT_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    image = CODE_PATH.read_bytes()
    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h12_test')

    cases = [
        (0x02, 100),       # bit 1 set -> 0
        (0x02000000, 100), # bit 25 set -> 1
        (0x02000002, 100), # both set -> bit 1 takes precedence -> 0
        (0x00, 0),         # hp == 0 -> 0
        (0x00, -10),       # hp < 0 -> 1
        (0x00, 100),       # alive and active -> 0
        (0x01, 500),       # other flags -> 0
    ]
    for flags, hp in cases:
        orig = run_simulation(image, cand_blob, ORIG_ADDR, flags, hp)
        cand = run_simulation(image, cand_blob, CAND_ADDR, flags, hp)
        assert orig == cand, f'Mismatch in Battle_IsUnitDefeated (flags={flags:#x}, hp={hp}): {orig} != {cand}'

    orig = run_simulation(image, cand_blob, ORIG_ADDR, 0x00, -10)
    mut = run_simulation(image, mut_blob, CAND_ADDR, 0x00, -10)
    assert orig != mut, 'Mutation failed'
    print('h12_battle_isunitdefeated: ALL CASES PASSED')

if __name__ == '__main__':
    main()
