#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001EE5A4 StatusDown_PopulateSkillList."""
from __future__ import annotations
import argparse, json, struct, subprocess, sys
from pathlib import Path

import unicorn
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h8_ui_statusdown_skilllist_candidate.cpp'
ORIG_ADDR = 0x001EE5A4
ORIG_SIZE = 548
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Zero_002c4b30': 0x002C4B30,
    'SkillTable_Get_002b9364': 0x002B9364,
    'UiPage_Setup_0029fae8': 0x0029FAE8,
    'UiMenu_GetSortOptions_002a0fac': 0x002A0FAC,
    'qsort_002b7f0a': 0x002B7F0A,
    'g_StatusDownContext_0044e190': 0x0044E190,
    'StatusDown_SkillSortByIdAsc': 0x00206BE8,
    'StatusDown_SkillSortByIdDesc': 0x002E4534,
    'StatusDown_SkillSortByCostAsc': 0x001F60DC,
    'StatusDown_SkillSortByCostDesc': 0x002DC96C,
    'StatusDown_SkillSortByNameAsc': 0x001F6174,
    'StatusDown_SkillSortByNameDesc': 0x002DCA04,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h8_ui_statusdown_skilllist.o'
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
    raw_cand, relocs_cand = funcs['h8_ui_statusdown_skilllist_candidate']
    raw_mut, _ = funcs['h8_ui_statusdown_skilllist_mutation']

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

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, cand_blob + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    CTX_ADDR = 0x0044E190
    WORK_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x20000, unicorn.UC_PROT_ALL)
    uc.mem_write(CTX_ADDR, struct.pack('<I', WORK_ADDR))

    # Mock SkillTable_Get (returns 0 to finish loop quickly)
    uc.mem_write(0x002B9364, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C4B30, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x0029FAE8, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    # Mock UiMenu_GetSortOptions (returns pointer with mode_byte at offset 0x15)
    OPT_ADDR = 0x08009000
    uc.mem_write(OPT_ADDR + 0x15, b'\x01')
    uc.mem_write(0x002A0FAC, struct.pack('<II', 0xE59F0000, 0xE12FFF1E))
    uc.mem_write(0x002A0FAC + 8, struct.pack('<I', OPT_ADDR))

    uc.mem_write(0x002B7F0A, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_R0, 0x08008000)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=1500)
    flag = uc.mem_read(WORK_ADDR + 0x410, 1)
    return 0, bytes(flag)

def main():
    out_dir = ROOT / 'build/h8_experiments/skilllist'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_mem == cand_mem)
    print(f"H8 StatusDown_PopulateSkillList: status={'passed' if matched else 'failed'}, matched={matched}")
    assert matched, "Original and candidate outputs differ!"

if __name__ == '__main__':
    main()
