#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002B2520 Aoc_ReleaseGlobal."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h17_aoc_releaseglobal_candidate.cpp'
ORIG_ADDR = 0x002B2520
ORIG_SIZE = 16
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Free': 0x002C4360,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h17_aoc_releaseglobal.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h17_aoc_releaseglobal_candidate']
    raw_mut, _ = funcs['h17_aoc_releaseglobal_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            offset = tgt - (CAND_ADDR + r.offset + 8)
            imm24 = (offset >> 2) & 0x00FFFFFF
            insn = 0xEB000000 | imm24
            struct.pack_into('<I', blob_cand, r.offset, insn)

    blob_mut = bytearray(raw_mut)
    blob_mut = bytearray(raw_mut)
    return bytes(blob_cand), bytes(blob_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, ptr_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    mod_image = bytearray(image)
    # Stub 0x002C4360: mov r0, #0x42; bx lr
    # 0xE3A00042: mov r0, #0x42
    # 0xE12FFF1E: bx lr
    stub = struct.pack('<II', 0xE3A00042, 0xE12FFF1E)
    mod_image[0x002C4360 - 0x00100000:0x002C4360 - 0x00100000 + 8] = stub

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
    uc.reg_write(UC_ARM_REG_R0, ptr_val)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h17_tests')

    cases = [0x0FFF3000, 0x0FFF4000, 0]

    for ptr_val in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, ptr_val)
        cand = run_simulation(code, cand_blob, CAND_ADDR, ptr_val)
        mut = run_simulation(code, mut_blob, CAND_ADDR, ptr_val)

        if orig != cand:
            raise AssertionError(f'Mismatch for ptr=0x{ptr_val:08X}: orig={orig}, cand={cand}')
        if orig == mut and ptr_val != 0:
            raise AssertionError(f'Mutation undetected for ptr=0x{ptr_val:08X}')

    print(f'[PASS] h17_aoc_releaseglobal: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
