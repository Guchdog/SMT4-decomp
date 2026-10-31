#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0026AAC0 Quest_UnpackEntryData."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h10_camp_quest_unpackentry_candidate.cpp'
ORIG_ADDR = 0x0026AAC0
ORIG_SIZE = 256
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'Quest_GetStaticDef_002b087c': 0x002B087C,
    'AsdMem_Zero_002c4b30': 0x002C4B30,
    'Quest_InitEntrySub_002bcf58': 0x002BCF58,
    'Quest_GetDynamicRecord_002b9364': 0x002B9364,
    'Quest_FormatTitle_0024be90': 0x0024BE90,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h10_camp_quest_unpackentry.o'
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
    raw_cand, relocs_cand = funcs['h10_camp_quest_unpackentry_candidate']
    raw_mut, _ = funcs['h10_camp_quest_unpackentry_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, qid: int) -> bytes:
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
    OUT_ADDR = DATA_BASE + 0x100
    DEF_ADDR = DATA_BASE + 0x300
    REC_ADDR = DATA_BASE + 0x500

    def_bytes = bytearray(0x80)
    def_bytes[2] = 3 # category
    struct.pack_into('<H', def_bytes, 4, 0x101)
    struct.pack_into('<H', def_bytes, 8, 0x102)
    struct.pack_into('<H', def_bytes, 0xC, 0x103)
    struct.pack_into('<H', def_bytes, 0xE, 0x104)
    struct.pack_into('<H', def_bytes, 0x10, 0x105)
    struct.pack_into('<H', def_bytes, 0x12, 0x106)
    struct.pack_into('<H', def_bytes, 0x14, 0x107)
    uc.mem_write(DEF_ADDR, bytes(def_bytes))

    rec_bytes = bytearray(0x50)
    struct.pack_into('<H', rec_bytes, 0x38, 0x0020)
    uc.mem_write(REC_ADDR, bytes(rec_bytes))

    # Mock helpers
    uc.mem_write(0x002B087C, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', DEF_ADDR))
    uc.mem_write(0x002C4B30, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BCF58, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002B9364, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', REC_ADDR))
    uc.mem_write(0x0024BE90, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_R0, qid)
    uc.reg_write(UC_ARM_REG_R1, OUT_ADDR)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.mem_read(OUT_ADDR, 0x4C)

def main():
    out_dir = ROOT / 'build/h10_experiments/unpackentry'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    for qid in [15, 42]:
        orig_out = run_simulation(image, cand_blob, ORIG_ADDR, qid)
        cand_out = run_simulation(image, cand_blob, CAND_ADDR, qid)

        matched = (orig_out == cand_out)
        print(f"H10 Quest_UnpackEntryData (qid {qid}): status={'passed' if matched else 'failed'}, matched={matched}")
        assert matched, f"Mismatch for qid {qid}"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        mut_out = run_simulation(image, bytes(mut_blob), CAND_ADDR, 15)
        mut_detected = (mut_out != cand_out)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
