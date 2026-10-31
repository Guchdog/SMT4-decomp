#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0026A004 Quest_ResetSelection."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h10_camp_quest_resetselection_candidate.cpp'
ORIG_ADDR = 0x0026A004
ORIG_SIZE = 40
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_CampWork_0043dd68': 0x0043DD68,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h10_camp_quest_resetselection.o'
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
    raw_cand, relocs_cand = funcs['h10_camp_quest_resetselection_candidate']
    raw_mut, _ = funcs['h10_camp_quest_resetselection_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, cat: int) -> tuple[int, bytes]:
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

    WORK_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x0043DD68, struct.pack('<I', WORK_ADDR))

    work_bytes = bytearray(0x500)
    work_bytes[0x420] = 0x55
    struct.pack_into('<I', work_bytes, 0x400, 0xAAAAAAAA)
    struct.pack_into('<I', work_bytes, 0x3FC, 0xBBBBBBBB)
    uc.mem_write(WORK_ADDR, bytes(work_bytes))

    uc.reg_write(UC_ARM_REG_R0, cat)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    mem = uc.mem_read(WORK_ADDR + 0x3F0, 0x40)
    return 0, bytes(mem)

def main():
    out_dir = ROOT / 'build/h10_experiments/resetselection'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    for cat in [1, 2, 5]:
        _, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR, cat)
        _, cand_mem = run_simulation(image, cand_blob, CAND_ADDR, cat)

        matched = (orig_mem == cand_mem)
        print(f"H10 Quest_ResetSelection (cat {cat}): status={'passed' if matched else 'failed'}, matched={matched}")
        assert matched, f"Mismatch for cat {cat}"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        _, mut_mem = run_simulation(image, bytes(mut_blob), CAND_ADDR, 1)
        mut_detected = (mut_mem != cand_mem)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
