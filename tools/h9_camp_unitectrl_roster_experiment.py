#!/usr/bin/env python3
"""Offline ARM differential validation for 0x003C9EBC UniteCtrl_RosterPopulate."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h9_camp_unitectrl_roster_candidate.cpp'
ORIG_ADDR = 0x003C9EBC
ORIG_SIZE = 664
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'ui_Tbb_GetGlobalSubTable_001b9a90': 0x001B9A90,
    'ui_Tbb_GetRowCount_001b9aa4': 0x001B9AA4,
    'Battle_GetTalkEntry_00215fa8': 0x00215FA8,
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'qsort_002b7f0a': 0x002B7F0A,
    'g_UniteCtrlRoster_0043dd40': 0x0043DD40,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h9_camp_unitectrl_roster.o'
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
    raw_cand, relocs_cand = funcs['h9_camp_unitectrl_roster_candidate']
    raw_mut, _ = funcs['h9_camp_unitectrl_roster_mutation']

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

    ROSTER_ADDR = 0x08000000
    uc.mem_map(ROSTER_ADDR, 0x10000, unicorn.UC_PROT_ALL)
    uc.mem_write(ROSTER_ADDR, b'\x00' * 0x200)

    # Mock helpers
    uc.mem_write(0x001B9A90, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08005000))
    uc.mem_write(0x001B9AC4, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x001B9AA4, struct.pack('<II', 0xE3A00000, 0xE12FFF1E)) # 0 rows initially for simple test
    uc.mem_write(0x00215FA8, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08006000))
    uc.mem_write(0x08006000, struct.pack('<HBBI', 0x12, 1, 2, 1))

    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08007000))
    uc.mem_write(0x002B7F0A, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_R0, ROSTER_ADDR)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    counts = uc.mem_read(ROSTER_ADDR, 0x38)
    return struct.unpack('<I', counts[:4])[0], bytes(counts)

def main():
    out_dir = ROOT / 'build/h9_experiments/unitectrl'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_r0 == cand_r0 and orig_mem == cand_mem)
    print(f"H9 UniteCtrl_RosterPopulate: status={'passed' if matched else 'failed'}, matched={matched}")
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
