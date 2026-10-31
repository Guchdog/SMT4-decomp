#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001FF814 CampCec_CopyCardData."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h17_campcec_copycarddata_candidate.cpp'
ORIG_ADDR = 0x001FF814
ORIG_SIZE = 28
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h17_campcec_copycarddata.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h17_campcec_copycarddata_candidate']
    raw_mut, _ = funcs['h17_campcec_copycarddata_mutation']
    return bytes(raw_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, w0: int, w1: int, w2: int) -> tuple[int, int, int]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000
    SRC_ADDR = STACK_BASE + 0x1000
    INNER_ADDR = STACK_BASE + 0x2000
    DST_ADDR = STACK_BASE + 0x3000

    uc.mem_write(SRC_ADDR + 0x2C, struct.pack('<I', INNER_ADDR))
    uc.mem_write(INNER_ADDR + 0x7C, struct.pack('<II', w0, w1))
    uc.mem_write(INNER_ADDR + 0x84, struct.pack('<I', w2))
    uc.mem_write(DST_ADDR, struct.pack('<III', 0, 0, 0))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, SRC_ADDR)
    uc.reg_write(UC_ARM_REG_R1, 0)
    uc.reg_write(UC_ARM_REG_R2, DST_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)

    res = struct.unpack('<III', uc.mem_read(DST_ADDR, 12))
    return res

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h17_tests')

    cases = [
        (0x11111111, 0x22222222, 0x33333333),
        (0x55AA55AA, 0xAA55AA55, 0x12345678),
        (0xFFFFFFFF, 0x00000000, 0x80000001),
    ]

    for w0, w1, w2 in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, w0, w1, w2)
        cand = run_simulation(code, cand_blob, CAND_ADDR, w0, w1, w2)
        mut = run_simulation(code, mut_blob, CAND_ADDR, w0, w1, w2)

        expected = (w0, w1, w2)
        if orig != cand or cand != expected:
            raise AssertionError(f'Mismatch for ({w0}, {w1}, {w2}): orig={orig}, cand={cand}, expected={expected}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for ({w0}, {w1}, {w2})')

    print(f'[PASS] h17_campcec_copycarddata: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
