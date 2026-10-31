#!/usr/bin/env python3
"""Offline ARM differential validation for 0x003A7AD8 bibleDevil_Init."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h9_camp_bibledevil_init_candidate.cpp'
ORIG_ADDR = 0x003A7AD8
ORIG_SIZE = 668
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'AsdTask_Create_002c5978': 0x002C5978,
    'AsdTask_CreateDraw_002c4c00': 0x002C4C00,
    'unite_func_00232800': 0x00232800,
    'engine_func_002c23f8': 0x002C23F8,
    'unite_func_002333bc': 0x002333BC,
    'unite_func_0022d5c8': 0x0022D5C8,
    'unite_func_003aad60': 0x003AAD60,
    'unite_func_0022df7c': 0x0022DF7C,
    'unite_func_002338ac': 0x002338AC,
    'unite_func_00233600': 0x00233600,
    'unite_func_00233804': 0x00233804,
    'camp_func_0029f10c': 0x0029F10C,
    'unite_func_002e32c8': 0x002E32C8,
    'camp_func_0022d33c': 0x0022D33C,
    'g_BibleDevilHandle_0043d9c8': 0x0043D9C8,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h9_camp_bibledevil_init.o'
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
    raw_cand, relocs_cand = funcs['h9_camp_bibledevil_init_candidate']
    raw_mut, _ = funcs['h9_camp_bibledevil_init_mutation']

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

    WORK_STRUCT = 0x08000000
    uc.mem_map(WORK_STRUCT, 0x20000, unicorn.UC_PROT_ALL)
    uc.mem_write(WORK_STRUCT, b'\x00' * 0x10000)
    VTBL = 0x08010000
    uc.mem_write(VTBL, struct.pack('<16I', *[0x00100004]*16))
    uc.mem_write(WORK_STRUCT, struct.pack('<I', VTBL))

    HANDLE_ADDR = 0x0043D9C8
    uc.mem_write(HANDLE_ADDR, b'\x00' * 8)

    # Mock helpers
    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08005000))
    uc.mem_write(0x002C5978, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002000))
    uc.mem_write(0x002C4C00, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002100))
    uc.mem_write(0x00232800, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C23F8, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08006000))
    uc.mem_write(0x002333BC, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x0022D5C8, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x003AAD60, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x0022DF7C, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002338AC, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x00233600, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x00233804, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x0029F10C, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002E32C8, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x0022D33C, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_R0, WORK_STRUCT)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    handle_val = uc.mem_read(HANDLE_ADDR, 4)
    work_val = uc.mem_read(WORK_STRUCT, 0x20)
    return struct.unpack('<I', handle_val)[0], bytes(work_val)

def main():
    out_dir = ROOT / 'build/h9_experiments/bibledevil'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_r0 == cand_r0 and orig_mem == cand_mem)
    print(f"H9 bibleDevil_Init: status={'passed' if matched else 'failed'}, matched={matched}")
    assert matched, "Original and candidate outputs differ!"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        mut_r0, mut_mem = run_simulation(image, bytes(mut_blob), CAND_ADDR)
        mut_detected = (mut_r0 != cand_r0 or mut_mem != cand_mem)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
