#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00152D7C AsdEffect_LockEnter."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h14_asdeffect_lockenter_candidate.cpp'
ORIG_ADDR = 0x00152D7C
ORIG_SIZE = 48
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_AsdEffectLockWork_00465120': 0x00465120,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h14_asdeffect_lockenter.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h14_asdeffect_lockenter_candidate']
    raw_mut, relocs_mut = funcs['h14_asdeffect_lockenter_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            struct.pack_into('<I', blob_cand, r.offset, tgt)

    blob_mut = bytearray(raw_mut)
    for r in relocs_mut:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            struct.pack_into('<I', blob_mut, r.offset, tgt)

    return bytes(blob_cand), bytes(blob_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, init_depth: int, init_saved: int, init_eff: int, new_id: int) -> tuple[int, int, int]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    INNER_BUF = MEM_BASE + 0x1000
    uc.mem_write(INNER_BUF + 0x38, struct.pack('<H', init_eff))

    # Setup 0x00465120
    uc.mem_write(0x00465120, struct.pack('<HH', init_saved, init_depth))
    uc.mem_write(0x00465120 + 8, struct.pack('<I', INNER_BUF))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, new_id)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)

    out_saved, out_depth = struct.unpack('<HH', uc.mem_read(0x00465120, 4))
    out_eff = struct.unpack('<H', uc.mem_read(INNER_BUF + 0x38, 2))[0]
    return out_depth, out_saved, out_eff

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h14_tests')

    cases = [
        (0, 0, 0x1111, 0x2222), # depth 0 -> saves 0x1111, depth becomes 1, eff becomes 0x2222
        (1, 0x1111, 0x2222, 0x3333), # depth 1 -> keeps saved 0x1111, depth becomes 2, eff becomes 0x3333
        (5, 0xAAAA, 0xBBBB, 0xCCCC), # depth 5 -> keeps saved 0xAAAA, depth becomes 6, eff becomes 0xCCCC
    ]

    for init_d, init_s, init_e, new_id in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, init_d, init_s, init_e, new_id)
        cand = run_simulation(code, cand_blob, CAND_ADDR, init_d, init_s, init_e, new_id)
        mut = run_simulation(code, mut_blob, CAND_ADDR, init_d, init_s, init_e, new_id)

        if orig != cand:
            raise AssertionError(f'Mismatch for d={init_d}: orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for d={init_d}')

    print(f'[PASS] h14_asdeffect_lockenter: 100% parity across {len(cases)} cases, mutation sensitivity confirmed.')

if __name__ == '__main__':
    main()
