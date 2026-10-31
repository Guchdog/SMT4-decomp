#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002C31BC AsdRes_GetContext."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h14_asdres_getcontext_candidate.cpp'
ORIG_ADDR = 0x002C31BC
ORIG_SIZE = 28
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_AsdResManager_00465170': 0x00465170,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h14_asdres_getcontext.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h14_asdres_getcontext_candidate']
    raw_mut, _ = funcs['h14_asdres_getcontext_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            struct.pack_into('<I', blob_cand, r.offset, tgt)

    return bytes(blob_cand), raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, flag: int, active_ctx: int, default_ctx: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    # 0x00465170: flag at +0, active_ctx at +8, default_ctx at +0xC
    uc.mem_write(0x00465170, bytes([flag]))
    uc.mem_write(0x00465170 + 8, struct.pack('<II', active_ctx, default_ctx))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h14_tests')

    cases = [
        (0, 0x11112222, 0x33334444), # flag 0 -> default_ctx 0x33334444
        (1, 0x11112222, 0x33334444), # flag 1 -> active_ctx 0x11112222
        (0xFF, 0xAAAABBBB, 0xCCCCDDDD), # flag 255 -> active_ctx 0xAAAABBBB
    ]

    for flag, act, dflt in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, flag, act, dflt)
        cand = run_simulation(code, cand_blob, CAND_ADDR, flag, act, dflt)
        mut = run_simulation(code, mut_blob, CAND_ADDR, flag, act, dflt)

        if orig != cand:
            raise AssertionError(f'Mismatch for flag={flag}: orig=0x{orig:08X}, cand=0x{cand:08X}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for flag={flag}')

    print(f'[PASS] h14_asdres_getcontext: 100% parity across {len(cases)} cases, context routing verified.')

if __name__ == '__main__':
    main()
