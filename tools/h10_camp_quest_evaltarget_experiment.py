#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0026A86C Quest_EvaluateTargetCondition."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h10_camp_quest_evaltarget_candidate.cpp'
ORIG_ADDR = 0x0026A86C
ORIG_SIZE = 152
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h10_camp_quest_evaltarget.o'
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
    raw_cand, relocs_cand = funcs['h10_camp_quest_evaltarget_candidate']
    raw_mut, _ = funcs['h10_camp_quest_evaltarget_mutation']
    return bytes(raw_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, entry_bytes: bytes, cond_bytes: bytes) -> int:
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

    DATA_BASE = 0x08000000
    uc.mem_map(DATA_BASE, 0x10000, unicorn.UC_PROT_ALL)
    ENTRY_ADDR = DATA_BASE + 0x100
    COND_ADDR = DATA_BASE + 0x200
    uc.mem_write(ENTRY_ADDR, entry_bytes)
    uc.mem_write(COND_ADDR, cond_bytes)

    uc.reg_write(UC_ARM_REG_R0, ENTRY_ADDR)
    uc.reg_write(UC_ARM_REG_R1, COND_ADDR)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    out_dir = ROOT / 'build/h10_experiments/evaltarget'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    cases = [
        # Case 1: type 5, cond 0, matching target
        (0x00052800, 0, 0x00005000, 0, 0),
        # Case 2: type 5, cond 0, non-matching target
        (0x00052800, 0, 0x00008000, 0, 0),
        # Case 3: type 6, cond 3, f38 with 0xA000
        (0x0006A000, 3, 0, 0x0000, 1),
        # Case 4: type 2 (invalid type)
        (0x00020000, 0, 0, 0, 0),
    ]

    for f38, cond_type, c28, c36, c43 in cases:
        eb = bytearray(0x50)
        struct.pack_into('<I', eb, 0x38, f38)
        cb = bytearray(0x50)
        cb[0x23] = cond_type
        struct.pack_into('<I', cb, 0x28, c28)
        struct.pack_into('<H', cb, 0x36, c36)
        cb[0x43] = c43

        orig_res = run_simulation(image, cand_blob, ORIG_ADDR, bytes(eb), bytes(cb))
        cand_res = run_simulation(image, cand_blob, CAND_ADDR, bytes(eb), bytes(cb))

        matched = (orig_res == cand_res)
        print(f"H10 Quest_EvaluateTargetCondition ({hex(f38)}, cond {cond_type}): orig={orig_res}, cand={cand_res}, matched={matched}")
        assert matched, f"Mismatch: {orig_res} vs {cand_res}"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        mut_res = run_simulation(image, bytes(mut_blob), CAND_ADDR, bytes(eb), bytes(cb))
        mut_detected = (mut_res != cand_res)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
