#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00263734 Terminal_SetUnlockFlag."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h11_terminal_setunlockflag_candidate.cpp'
ORIG_ADDR = 0x00263734
ORIG_SIZE = 68
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'sub_2BBD40': 0x002BBD40,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h11_terminal_setunlockflag.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h11_terminal_setunlockflag_candidate']
    raw_mut, _ = funcs['h11_terminal_setunlockflag_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)
    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, initial_bits: bytes, ops: list[tuple[int, int]]) -> bytes:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    WORK_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)
    uc.mem_write(WORK_ADDR + 8, initial_bits)

    # Mock sub_2BBD40 -> return WORK_ADDR
    stub = struct.pack('<III', 0xE59F0000, 0xE12FFF1E, WORK_ADDR)
    uc.mem_write(0x002BBD40, stub)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    RETURN_ADDR = 0x00100004
    for term_id, state in ops:
        uc.reg_write(UC_ARM_REG_SP, SP_INIT)
        uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
        uc.reg_write(UC_ARM_REG_R0, term_id)
        uc.reg_write(UC_ARM_REG_R1, state)
        uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)

    return uc.mem_read(WORK_ADDR + 8, 4)

def main():
    with open(CODE_PATH, 'rb') as f:
        image = f.read()

    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h11_differential')

    init_b = b'\x00\x00\x00\x00'
    ops = [
        (0, 1),
        (7, 1),
        (18, 1),
        (7, 0),
        (35, 1), # out of bounds
    ]

    orig_out = run_simulation(image, cand_blob, ORIG_ADDR, init_b, ops)
    cand_out = run_simulation(image, cand_blob, CAND_ADDR, init_b, ops)
    assert orig_out == cand_out, f'Mismatch in Terminal_SetUnlockFlag: {orig_out.hex()} != {cand_out.hex()}'

    mut_out = run_simulation(image, mut_blob, CAND_ADDR, init_b, ops)
    assert orig_out != mut_out, 'Mutation failed'
    print('h11_terminal_setunlockflag: ALL CASES PASSED')

if __name__ == '__main__':
    main()
