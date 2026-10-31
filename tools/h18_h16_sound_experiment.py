#!/usr/bin/env python3
"""Offline ARM differential validation for H16 Sound promoted module (0x00110C44)."""
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
SRC_PATH = ROOT / 'src/semantic/h16_sound_promoted.cpp'
ORIG_ADDR = 0x00110C44
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h16_sound_promoted.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h16_asdsoundeffect_getbuffersize_promoted']
    raw_mut, relocs_mut = funcs['h16_asdsoundeffect_getbuffersize_mutation']
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

    CONFIG_ADDR = 0x0FFF2000
    uc.mem_write(CONFIG_ADDR + 0x44, struct.pack('<I', rate))
    uc.mem_write(CONFIG_ADDR + 0x5D, struct.pack('B', channels))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, CONFIG_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h18_tests')

    cases = [(32000, 2), (44100, 1), (16000, 2), (22050, 1)]
    for r, c in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, r, c)
        cand = run_simulation(code, cand_blob, CAND_ADDR, r, c)
        mut = run_simulation(code, mut_blob, CAND_ADDR, r, c)
        assert orig == cand, f'Mismatch for ({r}, {c}): orig={orig}, cand={cand}'
        assert orig != mut, f'Mutation undetected for ({r}, {c})'

    print('[PASS] H18 Sound Promoted Module: 100% parity across vectors, mutations detected.')

if __name__ == '__main__':
    main()
