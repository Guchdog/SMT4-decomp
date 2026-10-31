#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002D931C StatusDown_Init."""
from __future__ import annotations
import argparse, json, struct, subprocess, sys
from pathlib import Path

import unicorn
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h8_ui_statusdown_init_candidate.cpp'
ORIG_ADDR = 0x002D931C
ORIG_SIZE = 764
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'AsdMem_Zero_002c4b30': 0x002C4B30,
    'AsdTask_Create_002c5978': 0x002C5978,
    'AsdTask_CreateDraw_002c4c00': 0x002C4C00,
    'UiSpriteGroup_Init_002c3344': 0x002C3344,
    'UiSpriteGroup_BindTable_002c32f8': 0x002C32F8,
    'UiAnimSprite_SetupEx_002bdb2c': 0x002BDB2C,
    'UiAnimSprite_SetMode_002bdac0': 0x002BDAC0,
    'UiAnimSprite_SetMode_002bf030': 0x002BF030,
    'engine_func_002bda1c': 0x002BDA1C,
    'engine_func_002bda10': 0x002BDA10,
    'engine_func_002bda00': 0x002BDA00,
    'engine_func_002c4450': 0x002C4450,
    'g_StatusDownContext_0044e190': 0x0044E190,
    'g_StatusDownSpriteTable_00407d58': 0x00407D58,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h8_ui_statusdown_init.o'
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
    raw_cand, relocs_cand = funcs['h8_ui_statusdown_init_candidate']
    raw_mut, _ = funcs['h8_ui_statusdown_init_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        tgt = TARGET_SYMBOLS.get(r.symbol_name, 0)
        reloc_vma = CAND_ADDR + r.offset
        if r.relocation_type == 2:
            struct.pack_into('<I', blob_cand, r.offset, tgt)
        elif r.relocation_type in (28, 29):
            w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
            struct.pack_into('<I', blob_cand, r.offset, w)

    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int) -> tuple[int, bytes]:
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

    CTX_ADDR = 0x0044E190
    WORK_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x20000, unicorn.UC_PROT_ALL)
    uc.mem_write(CTX_ADDR, struct.pack('<I', WORK_ADDR))

    # Mock helpers
    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', WORK_ADDR))
    uc.mem_write(0x002C4B30, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C5978, struct.pack('<II', 0xE3A00001, 0xE12FFF1E))
    uc.mem_write(0x002C4C00, struct.pack('<II', 0xE3A00002, 0xE12FFF1E))
    uc.mem_write(0x002C3344, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C32F8, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BDB2C, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BDAC0, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BF030, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BF0A8, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BDA1C, struct.pack('<II', 0xE3A00003, 0xE12FFF1E))
    uc.mem_write(0x002BDA10, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BDA00, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C4450, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    flag = uc.mem_read(WORK_ADDR + 0x2392, 1)
    return 0, bytes(flag)

def main():
    out_dir = ROOT / 'build/h8_experiments/statusdown_init'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_mem == cand_mem)
    print(f"H8 StatusDown_Init: status={'passed' if matched else 'failed'}, matched={matched}")
    assert matched, "Original and candidate outputs differ!"

if __name__ == '__main__':
    main()
