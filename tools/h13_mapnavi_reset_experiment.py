#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001D2E0C MapNavi_Reset."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h13_mapnavi_reset_candidate.cpp'
ORIG_ADDR = 0x001D2E0C
ORIG_SIZE = 24
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_MapRuntimeWork_00447060': 0x00447060,
    'sub_2C45B8': 0x002C45B8,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h13_mapnavi_reset.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h13_mapnavi_reset_candidate']
    raw_mut, relocs_mut = funcs['h13_mapnavi_reset_mutation']

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

    blob_mut = bytearray(raw_mut)
    for r in relocs_mut:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_mut, r.offset, w)
            elif r.relocation_type == 2:
                struct.pack_into('<I', blob_mut, r.offset, tgt)

    return bytes(blob_cand), bytes(blob_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int) -> tuple[int, int]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Stub sub_2C45B8: records r0, r1 to 0x00447070, then bx lr
    stub = struct.pack('<IIIII',
        0xE59F2008, # ldr r2, [pc, #8] -> 0x00447070
        0xE5820000, # str r0, [r2]
        0xE5821004, # str r1, [r2, #4]
        0xE12FFF1E, # bx lr
        0x00447070, # literal
    )
    uc.mem_write(0x002C45B8, stub)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    PTR1 = MEM_BASE + 0x4000
    PTR2 = MEM_BASE + 0x5000
    uc.mem_write(0x00447060, struct.pack('<I', PTR1))
    uc.mem_write(PTR1, struct.pack('<I', PTR2))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    call_r0 = struct.unpack('<I', uc.mem_read(0x00447070, 4))[0]
    call_r1 = struct.unpack('<I', uc.mem_read(0x00447074, 4))[0]
    return call_r0, call_r1

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h13_tests')

    orig = run_simulation(code, cand_blob, ORIG_ADDR)
    cand = run_simulation(code, cand_blob, CAND_ADDR)
    mut = run_simulation(code, mut_blob, CAND_ADDR)

    if orig != cand:
        raise AssertionError(f'Mismatch: orig={orig}, cand={cand}')
    if orig == mut:
        raise AssertionError('Mutation undetected')

    print(f'[PASS] h13_mapnavi_reset: parity verified (work=0x{cand[0]:08X}, flag={cand[1]}), mutation detected.')

if __name__ == '__main__':
    main()
