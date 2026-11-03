#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0028D974 ButtonHelp_Init."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed
from tools.local_section_relocations import resolve_local_sections

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h9_camp_buttonhelp_init_candidate.cpp'
ORIG_ADDR = 0x0028D974
ORIG_SIZE = 736
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'AsdMem_Zero_002c4b30': 0x002C4B30,
    'AsdTask_Create_002c5978': 0x002C5978,
    'AsdTask_CreateDraw_002c4c00': 0x002C4C00,
    'UiSpriteGroup_Init_002c3344': 0x002C3344,
    'UiSpriteGroup_BindTable_002c32f8': 0x002C32F8,
    'UiAnimSprite_SetupEx_002bdb2c': 0x002BDB2C,
    'QuestUi_SetTextPair_00262448': 0x00262448,
    'UiAnimSprite_SetText_00296154': 0x00296154,
    'AsdText_CreateDefault_002bda1c': 0x002BDA1C,
    'AsdText_SetAlpha_002bda10': 0x002BDA10,
    'AsdText_SetColorAndScale_002bda00': 0x002BDA00,
    'scrScriptProcess_func_002972f8': 0x002972F8,
    'g_ButtonHelpManager_0043da28': 0x0043DA28,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h9_camp_buttonhelp_init.o'
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
    raw_cand, relocs_cand = funcs['h9_camp_buttonhelp_init_candidate']
    raw_mut, _ = funcs['h9_camp_buttonhelp_init_mutation']

    blob_cand = bytearray(raw_cand)
    local_offsets = resolve_local_sections(obj_path, 'h9_camp_buttonhelp_init_candidate', CAND_ADDR, blob_cand, ORIG_SIZE)
    for r in relocs_cand:
        if r.offset in local_offsets:
            continue
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type == 2:
                struct.pack_into('<I', blob_cand, r.offset, tgt)
            elif r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)

    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, init_refcount: int = 0) -> tuple[int, bytes]:
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
    MGR_ADDR = 0x0043DA28
    uc.mem_write(MGR_ADDR, struct.pack('<B3sIII', init_refcount, b'\x00'*3, WORK_ADDR if init_refcount else 0, 0x1234, 0x5678))

    # Mock helpers
    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', WORK_ADDR))
    zero_stub = (
        0xe3510000, 0x012fff1e, 0xe3a02000, 0xe4c02001, 0xe2511001, 0x1afffffc, 0xe12fff1e
    )
    uc.mem_write(0x002C4B30, struct.pack('<7I', *zero_stub))
    uc.mem_write(0x002C5978, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002000))
    uc.mem_write(0x002C4C00, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002100))
    uc.mem_write(0x002BDA1C, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002200))
    uc.mem_write(0x002972F8, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002300))

    for a in [0x002C3344, 0x002C32F8, 0x002BDB2C, 0x00262448, 0x00296154, 0x002BDA10, 0x002BDA00]:
        uc.mem_write(a, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=2000)
    mgr_val = uc.mem_read(MGR_ADDR, 0x10)
    work_val = uc.mem_read(WORK_ADDR, 0x564)
    return struct.unpack('<I', mgr_val[:4])[0], bytes(mgr_val + work_val)

def main():
    out_dir = ROOT / 'build/h9_experiments/buttonhelp'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    # Case 1: uninitialized (refcount = 0)
    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR, init_refcount=0)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR, init_refcount=0)
    matched0 = (orig_r0 == cand_r0 and orig_mem == cand_mem)

    # Case 2: already initialized (refcount = 1)
    orig_r1, orig_mem1 = run_simulation(image, cand_blob, ORIG_ADDR, init_refcount=1)
    cand_r1, cand_mem1 = run_simulation(image, cand_blob, CAND_ADDR, init_refcount=1)
    matched1 = (orig_r1 == cand_r1 and orig_mem1 == cand_mem1)

    matched = matched0 and matched1
    status_str = 'passed' if matched else 'failed'
    print(f"H9 ButtonHelp_Init: status={status_str}, matched={matched} (case0={matched0}, case1={matched1})")
    assert matched, "Original and candidate outputs differ!"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        mut_r0, mut_mem = run_simulation(image, bytes(mut_blob), CAND_ADDR)
        mut_detected = (mut_r0 != cand_r0 or mut_mem != cand_mem)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"
    print("Negative control (mutation detected): PASSED")

if __name__ == '__main__':
    main()
