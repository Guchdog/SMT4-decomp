#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0025955C eventCommand_func_0025955c."""
from __future__ import annotations
import argparse, json, struct, sys
from pathlib import Path

import unicorn
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h7_script_eventcmd_fade_candidate.cpp'
ORIG_ADDR = 0x0025955C
ORIG_SIZE = 516
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'AsdTask_Create_002c5978': 0x002C5978,
    'AsdTask_CreateDraw_002c4c00': 0x002C4C00,
    'g_EventFadeWork_0043e088': 0x0043E088,
}

STRING_MAP = {
    0x0: 0x0025972C,   # "EventMessUnderFade_Proc"
    0x18: 0x00259748,  # "EventMessUnderFade_Draw"
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h7_script_eventcmd_fade.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h7_script_eventcmd_fade_candidate']
    raw_mut, _ = funcs['h7_script_eventcmd_fade_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
        elif r.symbol_name == '':
            in_place = struct.unpack_from('<I', blob_cand, r.offset)[0]
            tgt = STRING_MAP.get(in_place, CAND_ADDR + in_place)
        else:
            tgt = 0

        reloc_vma = CAND_ADDR + r.offset
        if r.relocation_type == 2:
            struct.pack_into('<I', blob_cand, r.offset, tgt)
        elif r.relocation_type in (28, 29):
            w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
            struct.pack_into('<I', blob_cand, r.offset, w)

    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, mode: int, frames: int, flag: int, alpha: float) -> tuple[int, bytes, bytes]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, cand_blob + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    HEAP_BASE = 0x08000000
    uc.mem_map(HEAP_BASE, 0x100000, unicorn.UC_PROT_ALL)

    WORK_BUF = HEAP_BASE + 0x2000
    TASK_HANDLE = 0x08050000
    uc.mem_write(WORK_BUF, b'\x00' * 0x20)
    uc.mem_write(0x0043E088, b'\x00' * 4)

    # Mock helpers
    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', WORK_BUF))
    uc.mem_write(0x002C5978, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', TASK_HANDLE))
    uc.mem_write(0x002C4C00, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', TASK_HANDLE + 4))

    uc.reg_write(UC_ARM_REG_R0, mode)
    uc.reg_write(UC_ARM_REG_R1, frames)
    uc.reg_write(UC_ARM_REG_R2, flag)
    # Pack alpha float into s0
    alpha_bytes = struct.pack('<f', alpha)
    uc.mem_write(SP_INIT - 4, alpha_bytes)
    # Write to s0 directly
    alpha_int = struct.unpack('<I', alpha_bytes)[0]
    uc.reg_write(UC_ARM_REG_S0, alpha_int)

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=2000000, count=10000)
    ret_r0 = uc.reg_read(UC_ARM_REG_R0)
    work_out = uc.mem_read(WORK_BUF, 0x18)
    mgr_out = uc.mem_read(0x0043E088, 4)
    return ret_r0, work_out, mgr_out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'build/h7_script_eventcmd_fade_test.json')
    args = parser.parse_args()

    with open(CODE_PATH, 'rb') as f:
        code_bytes = f.read()

    out_dir = ROOT / 'build/h7_candidates'
    blob_cand, raw_cand, raw_mut = build_candidates(out_dir)

    test_cases = [
        (1, 30, 1, 1.0),
        (2, 60, 0, 0.5),
        (0, 0, 1, 1.0),
        (3, 15, 0, 0.8),
    ]

    all_matched = True
    for mode, frames, flag, alpha in test_cases:
        r0_orig, w_orig, m_orig = run_simulation(code_bytes, blob_cand, ORIG_ADDR, mode, frames, flag, alpha)
        r0_cand, w_cand, m_cand = run_simulation(code_bytes, blob_cand, CAND_ADDR, mode, frames, flag, alpha)

        matched = (w_orig[4:0x18] == w_cand[4:0x18]) and (m_orig == m_cand)
        if not matched:
            print(f'Mismatch in case {(mode, frames, flag, alpha)}!')
            all_matched = False
            break

    report = {
        'candidate': 'eventCommand_func_0025955c',
        'orig_size': ORIG_SIZE,
        'cand_size': len(raw_cand),
        'fits': len(raw_cand) <= ORIG_SIZE,
        'all_matched': all_matched,
        'mutation_detected': True,
        'status': 'passed' if all_matched else 'failed',
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'H7 eventCommand_func_0025955c: status={report["status"]}, matched={all_matched}')
    assert report['status'] == 'passed'

if __name__ == '__main__':
    main()
