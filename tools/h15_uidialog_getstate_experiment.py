#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00126084 UiDialog_GetState."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h15_uidialog_getstate_candidate.cpp'
ORIG_ADDR = 0x00126084
ORIG_SIZE = 16
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'sub_2C0AC8': 0x002C0AC8,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h15_uidialog_getstate.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h15_uidialog_getstate_candidate']
    raw_mut, relocs_mut = funcs['h15_uidialog_getstate_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, state_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)
    CTX_BUF = MEM_BASE + 0x1000
    uc.mem_write(CTX_BUF + 0x8C, struct.pack('<b', state_val))

    # Stub sub_2C0AC8: returns CTX_BUF in r0
    # ldr r0, =CTX_BUF; bx lr
    stub = struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', CTX_BUF)
    uc.mem_write(0x002C0AC8, stub)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    ret = uc.reg_read(UC_ARM_REG_R0)
    if ret >= 0x80000000:
        ret -= 0x100000000
    return ret

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h15_tests')

    vals = [0, 1, 42, -1, -50]
    for v in vals:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, v)
        cand = run_simulation(code, cand_blob, CAND_ADDR, v)
        mut = run_simulation(code, mut_blob, CAND_ADDR, v)

        if orig != cand or cand != v:
            raise AssertionError(f'Mismatch for v={v}: orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for v={v}')

    print(f'[PASS] h15_uidialog_getstate: 100% parity across {len(vals)} states, sign-extension verified.')

if __name__ == '__main__':
    main()
