#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00215938 Battle_ResetUnitStateBuffer."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h12_battle_resetunitstatebuffer_candidate.cpp'
ORIG_ADDR = 0x00215938
ORIG_SIZE = 32
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_BattleUnitTable_00478000': 0x00478000,
    'sub_2BCF58': 0x002BCF58,
}

def branch_word(src: int, tgt: int, is_bl: bool = False) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h12_battle_resetunitstatebuffer.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h12_battle_resetunitstatebuffer_candidate']
    raw_mut, _ = funcs['h12_battle_resetunitstatebuffer_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)
            elif r.relocation_type == 2:
                struct.pack_into('<I', blob_cand, r.offset, tgt)
    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, idx: int, src_data: bytes) -> bytes:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Mock sub_2BCF58 (memcpy: r0=dst, r1=src, r2=len):
    # loop: ldrb r3, [r1], #1; strb r3, [r0], #1; subs r2, r2, #1; bne loop; bx lr
    mock_memcpy = struct.pack('<IIIII',
        0xE4D13001,  # ldrb r3, [r1], #1
        0xE4C03001,  # strb r3, [r0], #1
        0xE2522001,  # subs r2, r2, #1
        0x1AFFFFFC,  # bne -4
        0xE12FFF1E   # bx lr
    )
    uc.mem_write(0x002BCF58, mock_memcpy)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    SRC_ADDR = 0x08002000
    uc.mem_write(SRC_ADDR, src_data)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, idx)
    uc.reg_write(UC_ARM_REG_R1, SRC_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    dest_addr = 0x00478000 + idx * 328 + 0x2C
    return uc.mem_read(dest_addr, 0x90)

def main():
    image = CODE_PATH.read_bytes()
    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h12_test')

    data_sample = bytes([(i * 7 + 13) & 0xFF for i in range(0x90)])
    cases = [0, 1, 3]
    for idx in cases:
        orig = run_simulation(image, cand_blob, ORIG_ADDR, idx, data_sample)
        cand = run_simulation(image, cand_blob, CAND_ADDR, idx, data_sample)
        assert orig == cand, f'Mismatch in Battle_ResetUnitStateBuffer ({idx})'

    orig = run_simulation(image, cand_blob, ORIG_ADDR, 0, data_sample)
    mut = run_simulation(image, mut_blob, CAND_ADDR, 0, data_sample)
    assert orig != mut, 'Mutation failed'
    print('h12_battle_resetunitstatebuffer: ALL CASES PASSED')

if __name__ == '__main__':
    main()
