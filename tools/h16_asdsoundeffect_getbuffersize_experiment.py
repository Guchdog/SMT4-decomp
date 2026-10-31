#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00110C44 AsdSoundEffect_GetBufferSize."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h16_asdsoundeffect_getbuffersize_candidate.cpp'
ORIG_ADDR = 0x00110C44
ORIG_SIZE = 28
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h16_asdsoundeffect_getbuffersize.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h16_asdsoundeffect_getbuffersize_candidate']
    raw_mut, _ = funcs['h16_asdsoundeffect_getbuffersize_mutation']
    return bytes(raw_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, rate: int, channels: int) -> int:
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

    uc.mem_write(SELF_ADDR + 0x44, struct.pack('<I', rate))
    uc.mem_write(SELF_ADDR + 0x5D, struct.pack('<B', channels))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h16_tests')

    cases = [
        (11025, 1),
        (22050, 2),
        (44100, 2),
        (48000, 2),
        (32000, 1),
    ]

    for rate, channels in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, rate, channels)
        cand = run_simulation(code, cand_blob, CAND_ADDR, rate, channels)
        mut = run_simulation(code, mut_blob, CAND_ADDR, rate, channels)

        expected = ((rate * channels * 5) << 7) + 0x20
        if orig != cand or cand != expected:
            raise AssertionError(f'Mismatch for ({rate}, {channels}): orig={orig}, cand={cand}, expected={expected}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for ({rate}, {channels})')

    print(f'[PASS] h16_asdsoundeffect_getbuffersize: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
