#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00191EAC saveLoadUI_Init."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h6_saveload_ui_init_candidate.cpp'
ORIG_ADDR = 0x00191EAC
ORIG_SIZE = 208
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'AsdTask_Create': 0x002C5978,
    'BootCalc_001c8d28': 0x001C8D28,
    'g_SaveLoadUIManager_0044de28': 0x0044DE28,
    'g_szBootC_00191f74': 0x00191F74,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h6_saveload_ui_init.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h6_saveload_ui_init_candidate']
    raw_mut, _ = funcs['h6_saveload_ui_init_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        tgt = TARGET_SYMBOLS.get(r.symbol_name, 0)
        reloc_vma = CAND_ADDR + r.offset
        if r.relocation_type == 2:
            struct.pack_into('<I', blob_cand, r.offset, tgt)
        elif r.relocation_type in (28, 29):
            w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
            struct.pack_into('<I', blob_cand, r.offset, w)

    return bytes(blob_cand), raw_cand, raw_mut, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int) -> tuple[int, bytes, bytes]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

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
    uc.mem_write(WORK_BUF, b'\x00' * 0x388)

    # Clear manager state at 0x0044DE28
    uc.mem_write(0x0044DE28, b'\x00' * 0x20)

    # Mock helpers
    # AsdMem_Alloc: return WORK_BUF
    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', WORK_BUF))
    # AsdTask_Create: return TASK_HANDLE
    uc.mem_write(0x002C5978, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', TASK_HANDLE))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=2000000, count=5000)
    ret_r0 = uc.reg_read(UC_ARM_REG_R0)
    work_out = uc.mem_read(WORK_BUF, 0x20)
    mgr_out = uc.mem_read(0x0044DE28, 0x10)
    return ret_r0, work_out, mgr_out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'build/h6_saveload_ui_init_test.json')
    args = parser.parse_args()

    with open(CODE_PATH, 'rb') as f:
        code_bytes = f.read()

    out_dir = ROOT / 'build/h6_candidates'
    blob_cand, raw_cand, blob_mut, raw_mut = build_candidates(out_dir)

    r0_orig, w_orig, m_orig = run_simulation(code_bytes, blob_cand, ORIG_ADDR)
    r0_cand, w_cand, m_cand = run_simulation(code_bytes, blob_cand, CAND_ADDR)

    matched = (w_orig == w_cand) and (m_orig == m_cand)

    # Mutation test (clears g_SaveLoadUIManager.work)
    _, _, m_mut = run_simulation(code_bytes, blob_mut, CAND_ADDR)
    mut_work_ptr = struct.unpack('<I', m_mut[4:8])[0]
    mutation_detected = (mut_work_ptr == 0)

    report = {
        'candidate': 'saveLoadUI_Init',
        'orig_size': ORIG_SIZE,
        'cand_size': len(raw_cand),
        'fits': len(raw_cand) <= ORIG_SIZE,
        'all_matched': matched,
        'mutation_detected': mutation_detected,
        'status': 'passed' if (matched and mutation_detected) else 'failed',
        'work_matched': (w_orig == w_cand),
        'mgr_matched': (m_orig == m_cand)
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'H6 saveLoadUI_Init: status={report["status"]}, matched={matched}, mut_detected={mutation_detected}')
    assert report['status'] == 'passed'

if __name__ == '__main__':
    main()
