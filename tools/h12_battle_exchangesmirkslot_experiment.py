#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00129C70 Battle_ExchangeSmirkSlot."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h12_battle_exchangesmirkslot_candidate.cpp'
ORIG_ADDR = 0x00129C70
ORIG_SIZE = 76
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_BattleSmirkWork_00471a70': 0x00471A70,
    'sub_2C3AA8': 0x002C3AA8,
    'sub_2C3A24': 0x002C3A24,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h12_battle_exchangesmirkslot.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h12_battle_exchangesmirkslot_candidate']
    raw_mut, _ = funcs['h12_battle_exchangesmirkslot_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, val: int, slot: int) -> tuple[int, bytes]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Stub lock/unlock: bx lr
    bx_lr = struct.pack('<I', 0xE12FFF1E)
    uc.mem_write(0x002C3AA8, bx_lr)
    uc.mem_write(0x002C3A24, bx_lr)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    SUB_ADDR = 0x08002000
    uc.mem_write(0x00471A70 + 0x1C, struct.pack('<I', SUB_ADDR))

    # Initialize 7 slots at SUB_ADDR + 0x10 with values [10, 20, 30, 40, 50, 60, 70]
    initial_slots = struct.pack('<IIIIIII', 10, 20, 30, 40, 50, 60, 70)
    uc.mem_write(SUB_ADDR + 0x10, initial_slots)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, val)
    uc.reg_write(UC_ARM_REG_R1, slot)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    ret_val = uc.reg_read(UC_ARM_REG_R0)
    slots_mem = uc.mem_read(SUB_ADDR + 0x10, 28)
    return ret_val, slots_mem

def main():
    image = CODE_PATH.read_bytes()
    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h12_test')

    cases = [(99, 0), (88, 3), (77, 6), (66, 7), (55, 10)]
    for val, slot in cases:
        orig_r0, orig_m = run_simulation(image, cand_blob, ORIG_ADDR, val, slot)
        cand_r0, cand_m = run_simulation(image, cand_blob, CAND_ADDR, val, slot)
        assert orig_r0 == cand_r0, f'Mismatch in ExchangeSmirkSlot ret ({val}, {slot}): {orig_r0} != {cand_r0}'
        assert orig_m == cand_m, f'Mismatch in ExchangeSmirkSlot mem ({val}, {slot})'

    orig_r0, _ = run_simulation(image, cand_blob, ORIG_ADDR, 99, 0)
    mut_r0, _ = run_simulation(image, mut_blob, CAND_ADDR, 99, 0)
    assert orig_r0 != mut_r0, 'Mutation check failed'
    print('h12_battle_exchangesmirkslot: ALL CASES PASSED')

if __name__ == '__main__':
    main()
