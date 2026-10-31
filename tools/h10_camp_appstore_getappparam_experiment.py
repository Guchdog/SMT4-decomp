#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00325444 AppStore_GetAppParam."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h10_camp_appstore_getappparam_candidate.cpp'
ORIG_ADDR = 0x00325444
ORIG_SIZE = 52
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'app_func_00296f60': 0x00296F60,
    'app_func_00293c98': 0x00293C98,
    'app_func_00245318': 0x00245318,
    'engine_func_002c0e9c': 0x002C0E9C,
    'app_func_0028df54': 0x0028DF54,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h10_camp_appstore_getappparam.o'
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
    raw_cand, relocs_cand = funcs['h10_camp_appstore_getappparam_candidate']
    raw_mut, _ = funcs['h10_camp_appstore_getappparam_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int) -> int:
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

    TABLE_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)
    uc.mem_write(TABLE_ADDR + 0x10, struct.pack('<H', 0x42)) # index 4 (0x10) = 0x42

    # Mock helpers
    uc.mem_write(0x00296F60, struct.pack('<II', 0xE3A00004, 0xE12FFF1E)) # returns index 4
    uc.mem_write(0x00293C98, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x00245318, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C0E9C, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', TABLE_ADDR))
    uc.mem_write(0x0028DF54, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    out_dir = ROOT / 'build/h10_experiments/appparam'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0 = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0 = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_r0 == cand_r0)
    print(f"H10 AppStore_GetAppParam: status={'passed' if matched else 'failed'}, orig={orig_r0}, cand={cand_r0}")
    assert matched, "Original and candidate outputs differ!"

if __name__ == '__main__':
    main()
