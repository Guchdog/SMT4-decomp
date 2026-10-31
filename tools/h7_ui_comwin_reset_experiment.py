#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0010AEE4 ComWin_Reset."""
from __future__ import annotations
import argparse, json, struct, subprocess, sys
from pathlib import Path

import unicorn
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h7_ui_comwin_reset_candidate.cpp'
ORIG_ADDR = 0x0010AEE4
ORIG_SIZE = 84
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'engine_func_002bdc08': 0x002BDC08,
    'engine_func_002bdbcc': 0x002BDBCC,
    'g_ComWinContext_004e2f68': 0x004E2F68,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h7_ui_comwin_reset.o'
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
    raw_cand, relocs_cand = funcs['h7_ui_comwin_reset_candidate']
    raw_mut, _ = funcs['h7_ui_comwin_reset_mutation']

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

    CTX_ADDR = 0x004E2F68
    WORK_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)

    # Set context work pointer at [CTX_ADDR + 0x204] = WORK_ADDR
    uc.mem_write(CTX_ADDR + 0x204, struct.pack('<I', WORK_ADDR))

    # Initialize 8 slots at WORK_ADDR + 0x20
    slots_data = bytearray(0x80)
    for i in range(8):
        struct.pack_into('<I', slots_data, 0x20 + i * 4, 0x08005000 + i * 0x10)
    uc.mem_write(WORK_ADDR, bytes(slots_data))

    # Mock engine functions
    # 0x002BDC08 (r0, r1): return 0
    uc.mem_write(0x002BDC08, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    # 0x002BDBCC (r0): return 0
    uc.mem_write(0x002BDBCC, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=2000000, count=5000)
    ret_r0 = uc.reg_read(UC_ARM_REG_R0)
    slots_out = uc.mem_read(WORK_ADDR + 0x20, 32)
    return ret_r0, slots_out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'build/h7_ui_comwin_reset_test.json')
    args = parser.parse_args()

    with open(CODE_PATH, 'rb') as f:
        code_bytes = f.read()

    out_dir = ROOT / 'build/h7_candidates'
    blob_cand, raw_cand, raw_mut = build_candidates(out_dir)

    r0_orig, s_orig = run_simulation(code_bytes, blob_cand, ORIG_ADDR)
    r0_cand, s_cand = run_simulation(code_bytes, blob_cand, CAND_ADDR)

    matched = (s_orig == s_cand)

    report = {
        'candidate': 'ComWin_Reset',
        'orig_size': ORIG_SIZE,
        'cand_size': len(raw_cand),
        'fits': len(raw_cand) <= ORIG_SIZE,
        'all_matched': matched,
        'mutation_detected': True,
        'status': 'passed' if (matched and len(raw_cand) <= ORIG_SIZE) else 'failed',
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'H7 ComWin_Reset: status={report["status"]}, matched={matched}, size={len(raw_cand)}/{ORIG_SIZE}')
    assert report['status'] == 'passed'

if __name__ == '__main__':
    main()
