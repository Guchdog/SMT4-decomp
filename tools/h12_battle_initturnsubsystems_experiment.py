#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00123050 Battle_InitTurnSubsystems."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h12_battle_initturnsubsystems_candidate.cpp'
ORIG_ADDR = 0x00123050
ORIG_SIZE = 64
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_BattleTurnWork_0044e32c': 0x0044E32C,
    'sub_136FA4': 0x00136FA4,
    'sub_132FB8': 0x00132FB8,
    'sub_1423C0': 0x001423C0,
    'sub_13348C': 0x0013348C,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h12_battle_initturnsubsystems.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h12_battle_initturnsubsystems_candidate']
    raw_mut, _ = funcs['h12_battle_initturnsubsystems_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, arg_ptr: int) -> tuple[int, bytes]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Stub the 4 subroutines: bx lr
    bx_lr = struct.pack('<I', 0xE12FFF1E)
    uc.mem_write(0x00136FA4, bx_lr)
    uc.mem_write(0x00132FB8, bx_lr)
    uc.mem_write(0x001423C0, bx_lr)
    uc.mem_write(0x0013348C, bx_lr)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, arg_ptr)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    ret_val = uc.reg_read(UC_ARM_REG_R0)
    mem_out = uc.mem_read(0x0044E32C, 4)
    return ret_val, mem_out

def main():
    image = CODE_PATH.read_bytes()
    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h12_test')

    cases = [0x08001000, 0x08002400, 0x08005000]
    for arg in cases:
        orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR, arg)
        cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR, arg)
        assert orig_r0 == cand_r0, f'Return mismatch: {orig_r0} != {cand_r0}'
        assert orig_mem == cand_mem, f'Memory mismatch at 0x0044E32C'

    orig_r0, _ = run_simulation(image, cand_blob, ORIG_ADDR, cases[0])
    mut_r0, _ = run_simulation(image, mut_blob, CAND_ADDR, cases[0])
    assert orig_r0 != mut_r0, 'Mutation check failed'
    print('h12_battle_initturnsubsystems: ALL CASES PASSED')

if __name__ == '__main__':
    main()
