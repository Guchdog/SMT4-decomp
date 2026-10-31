#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00215A44 StatusDown_SetActiveSoundId."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h16_statusdown_setactivesoundid_candidate.cpp'
ORIG_ADDR = 0x00215A44
ORIG_SIZE = 28
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_SoundCtx_0044e190': 0x0044E190,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h16_statusdown_setactivesoundid.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h16_statusdown_setactivesoundid_candidate']
    raw_mut, relocs_mut = funcs['h16_statusdown_setactivesoundid_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, sound_id: int, ctx_ptr: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    # Write pointer at 0x0044E190
    uc.mem_write(0x0044E190, struct.pack('<I', ctx_ptr))
    if ctx_ptr != 0:
        uc.mem_write(ctx_ptr + 0x47E, struct.pack('<H', 0))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, sound_id)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)

    if ctx_ptr != 0:
        return struct.unpack('<H', uc.mem_read(ctx_ptr + 0x47E, 2))[0]
    return 0

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h16_tests')

    cases = [
        (0x0123, 0x0FFF2000),
        (0x4567, 0x0FFF2000),
        (0xFFFF, 0x0FFF2000),
        (0x0000, 0x0FFF2000),
        (0x1234, 0), # null ctx
    ]

    for sound_id, ctx_ptr in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, sound_id, ctx_ptr)
        cand = run_simulation(code, cand_blob, CAND_ADDR, sound_id, ctx_ptr)
        mut = run_simulation(code, mut_blob, CAND_ADDR, sound_id, ctx_ptr)

        if orig != cand:
            raise AssertionError(f'Mismatch for ({sound_id}, {ctx_ptr}): orig={orig}, cand={cand}')
        if orig == mut and ctx_ptr != 0:
            raise AssertionError(f'Mutation undetected for ({sound_id}, {ctx_ptr})')

    print(f'[PASS] h16_statusdown_setactivesoundid: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
