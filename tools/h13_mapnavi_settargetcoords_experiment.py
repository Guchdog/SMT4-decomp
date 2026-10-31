#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001D2E24 MapNavi_SetTargetCoords."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h13_mapnavi_settargetcoords_candidate.cpp'
ORIG_ADDR = 0x001D2E24
ORIG_SIZE = 40
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_MapNaviTarget_004474d8': 0x004474D8,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h13_mapnavi_settargetcoords.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h13_mapnavi_settargetcoords_candidate']
    raw_mut, relocs_mut = funcs['h13_mapnavi_settargetcoords_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, x: int, y: int) -> bytes:
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

    TARGET_BUF = MEM_BASE + 0x3000
    # g_MapNaviTarget_004474d8 is at 0x004474D8
    uc.mem_write(0x004474D8, struct.pack('<I', TARGET_BUF))
    # Fill target buffer with 0xAA
    uc.mem_write(TARGET_BUF, b'\xAA' * 32)

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, x)
    uc.reg_write(UC_ARM_REG_R1, y)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    return uc.mem_read(TARGET_BUF, 16)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h13_tests')

    vectors = [(0, 0), (100, 200), (0x1234, 0x5678), (0xFFFF, 0x7FFF)]
    for x, y in vectors:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, x, y)
        cand = run_simulation(code, cand_blob, CAND_ADDR, x, y)
        mut = run_simulation(code, mut_blob, CAND_ADDR, x, y)

        if orig != cand:
            raise AssertionError(f'Mismatch for ({x}, {y}): orig={orig.hex()}, cand={cand.hex()}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for ({x}, {y})')

        # Check fields: target_x at +4, target_y at +6, angle at +8 (=0), active at +0xA (=1)
        tx, ty, angle, act = struct.unpack_from('<HHHB', orig, 4)
        if tx != x or ty != y or angle != 0 or act != 1:
            raise AssertionError(f'Field check failed: tx={tx}, ty={ty}, angle={angle}, act={act}')

    print(f'[PASS] h13_mapnavi_settargetcoords: 100% parity across {len(vectors)} vectors, field values verified.')

if __name__ == '__main__':
    main()
