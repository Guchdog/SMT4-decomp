#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001D3A9C MapCalc_DistanceToEntity."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h13_mapcalc_distancetoentity_candidate.cpp'
ORIG_ADDR = 0x001D3A9C
ORIG_SIZE = 32
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'sub_266D70': 0x00266D70,
    'sub_2E05BC': 0x002E05BC,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h13_mapcalc_distancetoentity.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h13_mapcalc_distancetoentity_candidate']
    raw_mut, relocs_mut = funcs['h13_mapcalc_distancetoentity_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, dist_sq: float) -> tuple[int, float]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Stub sub_266D70 at 0x00266D70:
    # vldr s0, [pc, #4]; bx lr; literal float dist_sq
    stub_1 = struct.pack('<III',
        0xED9F0A01, # vldr s0, [pc, #4]
        0xE12FFF1E, # bx lr
        struct.unpack('<I', struct.pack('<f', dist_sq))[0]
    )
    uc.mem_write(0x00266D70, stub_1)

    # Stub sub_2E05BC at 0x002E05BC:
    # vstr s0, [pc, #4]; bx lr; literal space at 0x002E05C8
    stub_2 = struct.pack('<III',
        0xED8F0A01, # vstr s0, [pc, #4]
        0xE12FFF1E, # bx lr
        0x00000000,
    )
    uc.mem_write(0x002E05BC, stub_2)

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
    passed_dist = struct.unpack('<f', uc.mem_read(0x002E05BC + 8, 4))[0]
    return ret, passed_dist

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h13_tests')

    test_sqs = [0.0, 4.0, 25.0, 100.0, 144.0]
    for sq in test_sqs:
        orig_ret, orig_dist = run_simulation(code, cand_blob, ORIG_ADDR, sq)
        cand_ret, cand_dist = run_simulation(code, cand_blob, CAND_ADDR, sq)
        mut_ret, mut_dist = run_simulation(code, mut_blob, CAND_ADDR, sq)

        if orig_ret != cand_ret or abs(orig_dist - cand_dist) > 1e-5:
            raise AssertionError(f'Mismatch for sq={sq}: orig=({orig_ret}, {orig_dist}), cand=({cand_ret}, {cand_dist})')
        if orig_ret == mut_ret:
            raise AssertionError(f'Mutation undetected for sq={sq}')

    print(f'[PASS] h13_mapcalc_distancetoentity: 100% parity across {len(test_sqs)} inputs, sqrtf validated.')

if __name__ == '__main__':
    main()
