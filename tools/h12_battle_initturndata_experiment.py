#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00136FA4 Battle_InitTurnData."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h12_battle_initturndata_candidate.cpp'
ORIG_ADDR = 0x00136FA4
ORIG_SIZE = 40
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_BattleStateWork_004655c0': 0x004655C0,
    'sub_1422F8': 0x001422F8,
}

def branch_word(src: int, tgt: int, is_bl: bool = False) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h12_battle_initturndata.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h12_battle_initturndata_candidate']
    raw_mut, _ = funcs['h12_battle_initturndata_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, init_flags: int) -> tuple[int, int]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Stub tail call sub_1422F8: bx lr
    bx_lr = struct.pack('<I', 0xE12FFF1E)
    uc.mem_write(0x001422F8, bx_lr)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    ARG_PTR = 0x08001000
    STATE_ADDR = 0x08002000
    uc.mem_write(0x004655C0, struct.pack('<I', STATE_ADDR))
    uc.mem_write(STATE_ADDR + 0x770, struct.pack('<I', init_flags))
    uc.mem_write(ARG_PTR, struct.pack('<I', 0))

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, ARG_PTR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    arg_val = struct.unpack('<I', uc.mem_read(ARG_PTR, 4))[0]
    flag_val = struct.unpack('<I', uc.mem_read(STATE_ADDR + 0x770, 4))[0]
    return arg_val, flag_val

def main():
    image = CODE_PATH.read_bytes()
    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h12_test')

    cases = [0x00000000, 0x00002000, 0x00010000, 0x00013000, 0xFFFFFFFF]
    for flags in cases:
        orig_arg, orig_flags = run_simulation(image, cand_blob, ORIG_ADDR, flags)
        cand_arg, cand_flags = run_simulation(image, cand_blob, CAND_ADDR, flags)
        assert orig_arg == cand_arg, f'Mismatch in Battle_InitTurnData arg ({flags:#x}): {orig_arg} != {cand_arg}'
        assert orig_flags == cand_flags, f'Mismatch in Battle_InitTurnData flags ({flags:#x}): {orig_flags:#x} != {cand_flags:#x}'

    orig_arg, orig_flags = run_simulation(image, cand_blob, ORIG_ADDR, 0)
    mut_arg, mut_flags = run_simulation(image, mut_blob, CAND_ADDR, 0)
    assert orig_arg != mut_arg or orig_flags != mut_flags, 'Mutation failed'
    print('h12_battle_initturndata: ALL CASES PASSED')

if __name__ == '__main__':
    main()
