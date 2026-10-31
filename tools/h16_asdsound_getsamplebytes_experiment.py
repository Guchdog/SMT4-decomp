#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00122094 AsdSound_GetSampleBytes."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h16_asdsound_getsamplebytes_candidate.cpp'
ORIG_ADDR = 0x00122094
ORIG_SIZE = 48
CAND_ADDR = 0x00600000

STUB_TARGET = 0x001419BC

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h16_asdsound_getsamplebytes.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h16_asdsound_getsamplebytes_candidate']
    raw_mut, _ = funcs['h16_asdsound_getsamplebytes_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name == 'g_sound_sub_001419bc':
            offset = STUB_TARGET - (CAND_ADDR + r.offset + 8)
            imm24 = (offset >> 2) & 0x00FFFFFF
            insn = 0xEB000000 | imm24
            struct.pack_into('<I', blob_cand, r.offset, insn)

    return bytes(blob_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, sample_count: int, success: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    mod_image = bytearray(image)
    # Stub 0x001419BC:
    # str r0, [r1, #0x10]
    # mov r0, r2 (success)
    # bx lr
    # Instructions:
    # 0xE5810010: str r0, [r1, #0x10]
    # 0xE1A00002: mov r0, r2
    # 0xE12FFF1E: bx lr
    stub_bytes = struct.pack('<III', 0xE5810010, 0xE1A00002, 0xE12FFF1E)
    mod_image[STUB_TARGET - 0x00100000:STUB_TARGET - 0x00100000 + 12] = stub_bytes

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
    uc.reg_write(UC_ARM_REG_R0, 0x0FFF1234)   # this
    uc.reg_write(UC_ARM_REG_R1, sample_count) # obj passed as r0 into stub
    uc.reg_write(UC_ARM_REG_R2, success)      # stub returns success flag

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h16_tests')

    cases = [
        (10, 1),
        (50, 1),
        (100, 1),
        (200, 0), # failure returns 0
    ]

    for sample_count, success in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, sample_count, success)
        cand = run_simulation(code, cand_blob, CAND_ADDR, sample_count, success)
        mut = run_simulation(code, mut_blob, CAND_ADDR, sample_count, success)

        expected = (sample_count * 5) << 13 if success else 0
        if orig != cand or cand != expected:
            raise AssertionError(f'Mismatch for ({sample_count}, {success}): orig={orig}, cand={cand}, expected={expected}')
        if orig == mut and expected != 0:
            raise AssertionError(f'Mutation undetected for ({sample_count}, {success})')

    print(f'[PASS] h16_asdsound_getsamplebytes: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
