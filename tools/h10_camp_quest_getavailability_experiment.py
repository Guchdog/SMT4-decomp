#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0026A9FC Quest_GetAvailability."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h10_camp_quest_getavailability_candidate.cpp'
ORIG_ADDR = 0x0026A9FC
ORIG_SIZE = 196
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'Quest_GetMainEntry_002ae3f0': 0x002AE3F0,
    'Quest_GetSubTable_002aa224': 0x002AA224,
    'engine_func_002c0ec4': 0x002C0EC4,
    'engine_func_002c0e9c': 0x002C0E9C,
    'engine_func_002c0e4c': 0x002C0E4C,
    'Quest_FindEntry_002b48dc': 0x002B48DC,
    'g_QuestTableMgr_00433158': 0x00433158,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h10_camp_quest_getavailability.o'
    cmd = [
        r'C:\msys64\clang64\bin\clang++.exe',
        '--target=armv6k-none-eabihf', '-mcpu=mpcore', '-mfpu=vfpv2', '-mfloat-abi=hard',
        '-Oz', '-std=c++20', '-fno-exceptions', '-fno-rtti', '-ffreestanding',
        '-nostdinc', '-nostdinc++',
        '-isystem', str(ROOT / 'include/freestanding'),
        '-isystem', r'C:\msys64\clang64\lib\clang\23\include',
        f'-I{ROOT / "include"}',
        '-c', str(SRC_PATH), '-o', str(obj_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h10_camp_quest_getavailability_candidate']
    raw_mut, _ = funcs['h10_camp_quest_getavailability_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type == 2:
                struct.pack_into('<I', blob_cand, r.offset, tgt)
            elif r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)

    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, qid: int, flags38: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    ENTRY_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)
    entry_bytes = bytearray(0x50)
    struct.pack_into('<I', entry_bytes, 0x38, flags38)
    uc.mem_write(ENTRY_ADDR, bytes(entry_bytes))
    uc.mem_write(0x00433158, struct.pack('<I', ENTRY_ADDR))

    # Mock helpers
    uc.mem_write(0x002AE3F0, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', ENTRY_ADDR))
    uc.mem_write(0x002AA224, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', ENTRY_ADDR))
    uc.mem_write(0x002B48DC, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', ENTRY_ADDR))

    uc.reg_write(UC_ARM_REG_R0, qid)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    out_dir = ROOT / 'build/h10_experiments/getavailability'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    test_cases = [
        (10, 0x00000000), # main quest available
        (10, 0x80000000), # main quest unavailable (bit 31 set)
        (500, 0x00000000), # challenge quest available
        (500, 0x40000000), # challenge quest unavailable (bit 30 set)
    ]

    for qid, f38 in test_cases:
        orig_res = run_simulation(image, cand_blob, ORIG_ADDR, qid, f38)
        cand_res = run_simulation(image, cand_blob, CAND_ADDR, qid, f38)

        matched = (orig_res == cand_res)
        print(f"H10 Quest_GetAvailability (qid {qid}, f38 {hex(f38)}): orig={orig_res}, cand={cand_res}, matched={matched}")
        assert matched, f"Mismatch for qid {qid}"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        mut_res = run_simulation(image, bytes(mut_blob), CAND_ADDR, 10, 0)
        mut_detected = (mut_res != cand_res)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
