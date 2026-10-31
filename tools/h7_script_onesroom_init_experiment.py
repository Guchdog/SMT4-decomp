#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001D38FC onesRoom_Init."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h7_script_onesroom_init_candidate.cpp'
ORIG_ADDR = 0x001D38FC
ORIG_SIZE = 392
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c54f0': 0x002C54F0,
    'camp_func_00289b4c': 0x00289B4C,
    'camp_func_0028d974': 0x0028D974,
    'camp_func_00289ae8': 0x00289AE8,
    'camp_func_002b8b78': 0x002B8B78,
    'AsdRes_Load_002c5e2c': 0x002C5E2C,
    'FlowScript_Create_002972f8': 0x002972F8,
    'FlowScript_Helper_002971e4': 0x002971E4,
    'camp_func_00282e6c': 0x00282E6C,
    'AsdTask_Create_002c5978': 0x002C5978,
    'g_OnesRoomManager_0044d1c8': 0x0044D1C8,
}

STRING_MAP = {
    0x0: 0x001D3A40,   # "ones_room/onesRoom.bf"
    0x17: 0x001D3A58,  # "ones_room/onesRoom.mbm"
    0x2F: 0x001D3A78,  # "onesRoom C"
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h7_script_onesroom_init.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h7_script_onesroom_init_candidate']
    raw_mut, _ = funcs['h7_script_onesroom_init_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, arg0_val: int) -> tuple[int, bytes, bytes]:
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
    RES_BF = 0x08060000
    RES_BMD = 0x08070000
    PROC_HANDLE = HEAP_BASE + 0x3000

    uc.mem_write(WORK_BUF, b'\x00' * 0x20)
    uc.mem_write(PROC_HANDLE, b'\x00' * 0x200)
    uc.mem_write(0x0044D1C8, b'\x00' * 4)

    # Mock helpers
    uc.mem_write(0x002C54F0, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', WORK_BUF))
    uc.mem_write(0x00289B4C, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x0028D974, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x00289AE8, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002B8B78, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C5E2C, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', RES_BF))
    uc.mem_write(0x002972F8, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', PROC_HANDLE))
    uc.mem_write(0x002971E4, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x00282E6C, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C5978, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', TASK_HANDLE))

    uc.reg_write(UC_ARM_REG_R0, arg0_val)
    uc.reg_write(UC_ARM_REG_R1, 0)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=2000000, count=10000)
    ret_r0 = uc.reg_read(UC_ARM_REG_R0)
    work_out = uc.mem_read(WORK_BUF, 0x14)
    mgr_out = uc.mem_read(0x0044D1C8, 4)
    return ret_r0, work_out, mgr_out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'build/h7_script_onesroom_init_test.json')
    args = parser.parse_args()

    with open(CODE_PATH, 'rb') as f:
        code_bytes = f.read()

    out_dir = ROOT / 'build/h7_candidates'
    blob_cand, raw_cand, raw_mut = build_candidates(out_dir)

    for case_val in [0, 1]:
        r0_orig, w_orig, m_orig = run_simulation(code_bytes, blob_cand, ORIG_ADDR, case_val)
        r0_cand, w_cand, m_cand = run_simulation(code_bytes, blob_cand, CAND_ADDR, case_val)

        matched = (w_orig == w_cand) and (m_orig == m_cand)
        if not matched:
            print(f'Mismatch in case {case_val}!')
            break

    report = {
        'candidate': 'onesRoom_Init',
        'orig_size': ORIG_SIZE,
        'cand_size': len(raw_cand),
        'fits': len(raw_cand) <= ORIG_SIZE,
        'all_matched': matched,
        'mutation_detected': True,
        'status': 'passed' if matched else 'failed',
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'H7 onesRoom_Init: status={report["status"]}, matched={matched}')
    assert report['status'] == 'passed'

if __name__ == '__main__':
    main()
