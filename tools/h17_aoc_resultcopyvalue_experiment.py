#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002A17E4 Aoc_ResultCopyValue."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h17_aoc_resultcopyvalue_candidate.cpp'
ORIG_ADDR = 0x002A17E4
ORIG_SIZE = 24
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h17_aoc_resultcopyvalue.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h17_aoc_resultcopyvalue_candidate']
    raw_mut, _ = funcs['h17_aoc_resultcopyvalue_mutation']
    return bytes(raw_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, inner_ptr: int, inner_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000
    TARGET_ADDR = STACK_BASE + 0x1000

    uc.mem_write(TARGET_ADDR, struct.pack('<I', inner_ptr))
    if inner_ptr != 0:
        uc.mem_write(inner_ptr, struct.pack('<I', inner_val))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, TARGET_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return struct.unpack('<I', uc.mem_read(TARGET_ADDR, 4))[0]

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h17_tests')

    cases = [
        (0x0FFF3000, 0x12345678),
        (0x0FFF4000, 0x55AA55AA),
        (0, 0),
    ]

    for inner_ptr, inner_val in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, inner_ptr, inner_val)
        cand = run_simulation(code, cand_blob, CAND_ADDR, inner_ptr, inner_val)
        mut = run_simulation(code, mut_blob, CAND_ADDR, inner_ptr, inner_val)

        expected = inner_val if inner_ptr != 0 else 0
        if orig != cand or cand != expected:
            raise AssertionError(f'Mismatch for ({inner_ptr}, {inner_val}): orig={orig}, cand={cand}, expected={expected}')
        if orig == mut and expected != 0:
            raise AssertionError(f'Mutation undetected for ({inner_ptr}, {inner_val})')

    print(f'[PASS] h17_aoc_resultcopyvalue: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
