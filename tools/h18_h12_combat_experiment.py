#!/usr/bin/env python3
"""Offline ARM differential validation for H12 Combat promoted module (0x00129C58)."""
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
SRC_PATH = ROOT / 'src/semantic/h12_combat_promoted.cpp'
ORIG_ADDR = 0x00129C58
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_BattleSmirkWork_00471a70': 0x00471A70,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h12_combat_promoted.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h12_battle_getunitsmirkstate_promoted']
    raw_mut, relocs_mut = funcs['h12_battle_getunitsmirkstate_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, smirk_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    SUB_BUF = 0x08002000
    uc.mem_write(0x00471A70 + 0x1C, struct.pack('<I', SUB_BUF))
    uc.mem_write(SUB_BUF + 0x75, struct.pack('b', smirk_val))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    res = uc.reg_read(UC_ARM_REG_R0)
    if res >= 0x80000000:
        res -= 0x100000000
    return res

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h18_tests')

    cases = [0, 1, -1, 5, -128, 127]
    for val in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, val)
        cand = run_simulation(code, cand_blob, CAND_ADDR, val)
        mut = run_simulation(code, mut_blob, CAND_ADDR, val)
        assert orig == cand, f'Mismatch for smirk {val}: orig={orig}, cand={cand}'
        assert orig != mut, f'Mutation undetected for {val}'

    print('[PASS] H18 Combat Promoted Module: 100% parity across vectors, mutations detected.')

if __name__ == '__main__':
    main()
