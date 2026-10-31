#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00121F20 AsdSound_GetDataSize."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h16_asdsound_getdatasize_candidate.cpp'
ORIG_ADDR = 0x00121F20
ORIG_SIZE = 32
CAND_ADDR = 0x00600000

STUB_TARGET = 0x00141924

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h16_asdsound_getdatasize.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h16_asdsound_getdatasize_candidate']
    raw_mut, _ = funcs['h16_asdsound_getdatasize_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name == 'g_sound_sub_00141924':
            # Relative branch or absolute target
            # bl instruction encoding in ARM:
            offset = STUB_TARGET - (CAND_ADDR + r.offset + 8)
            imm24 = (offset >> 2) & 0x00FFFFFF
            insn = 0xEB000000 | imm24
            struct.pack_into('<I', blob_cand, r.offset, insn)

    return bytes(blob_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, count_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    mod_image = bytearray(image)
    # Stub 0x00141924 with `bx lr` (0xE12FFF1E)
    struct.pack_into('<I', mod_image, STUB_TARGET - 0x00100000, 0xE12FFF1E)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, bytes(mod_image))

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, 0x0FFF1234) # this
    uc.reg_write(UC_ARM_REG_R1, count_val)   # obj -> stub returns count_val in r0

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h16_tests')

    cases = [0, 1, 2, 5, 10, 255]

    for count_val in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, count_val)
        cand = run_simulation(code, cand_blob, CAND_ADDR, count_val)
        mut = run_simulation(code, mut_blob, CAND_ADDR, count_val)

        expected = (4 + (count_val * 4) + 3) & ~3
        if orig != cand or cand != expected:
            raise AssertionError(f'Mismatch for {count_val}: orig={orig}, cand={cand}, expected={expected}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for {count_val}')

    print(f'[PASS] h16_asdsound_getdatasize: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
