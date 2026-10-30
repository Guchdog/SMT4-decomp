#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002F4AA4 btlTargetSelect_DrawUp."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h5_btl_target_select_draw_up_candidate.cpp'
ORIG_ADDR = 0x002F4AA4
ORIG_SIZE = 76
CAND_ADDR = 0x00600000

MOCK_GET_WORK = 0x002C0AC8
MOCK_DRAW_M1 = 0x00342B54
MOCK_DRAW_M2 = 0x0034946C

def branch_word(src: int, tgt: int, is_bl: bool = False) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'btl_target_select_draw_up.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, rels_cand = funcs['h5_btl_target_select_draw_up_candidate']
    raw_mut, rels_mut = funcs['h5_btl_target_select_draw_up_mutation']

    def resolve_relocs(raw, rels):
        blob = bytearray(raw)
        for r in rels:
            if 'GetWork' in r.symbol_name:
                w = branch_word(CAND_ADDR + r.offset, MOCK_GET_WORK, is_bl=True)
                struct.pack_into('<I', blob, r.offset, w)
            elif 'DrawMode1' in r.symbol_name:
                w = branch_word(CAND_ADDR + r.offset, MOCK_DRAW_M1, is_bl=True)
                struct.pack_into('<I', blob, r.offset, w)
            elif 'DrawMode2' in r.symbol_name:
                w = branch_word(CAND_ADDR + r.offset, MOCK_DRAW_M2, is_bl=True)
                struct.pack_into('<I', blob, r.offset, w)
            else:
                raise ValueError(f'Unknown relocation symbol {r.symbol_name}')
        return bytes(blob)

    blob_cand = resolve_relocs(raw_cand, rels_cand)
    blob_mut = resolve_relocs(raw_mut, rels_mut)
    return blob_cand, raw_cand, blob_mut, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, mode: int) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x2000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, cand_blob + b'\x00' * (0x2000 - len(cand_blob)))

    HEAP_BASE = 0x08200000
    uc.mem_map(HEAP_BASE, 0x10000, unicorn.UC_PROT_ALL)

    WORK_ADDR = HEAP_BASE + 0x1000
    OBJ0_ADDR = HEAP_BASE + 0x2000
    OBJ1_ADDR = HEAP_BASE + 0x3000

    uc.mem_write(WORK_ADDR + 0x00, struct.pack('<I', OBJ0_ADDR))
    uc.mem_write(WORK_ADDR + 0x04, struct.pack('<I', OBJ1_ADDR))
    uc.mem_write(WORK_ADDR + 0x08, bytes([mode]))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    calls = []
    def hook_get_work(uc, address, size, user_data):
        lr = uc.reg_read(UC_ARM_REG_LR)
        uc.reg_write(UC_ARM_REG_R0, WORK_ADDR)
        uc.reg_write(UC_ARM_REG_PC, lr)

    def hook_draw_m1(uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        lr = uc.reg_read(UC_ARM_REG_LR)
        calls.append(('mode1', hex(r0)))
        uc.reg_write(UC_ARM_REG_PC, lr)

    def hook_draw_m2(uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        lr = uc.reg_read(UC_ARM_REG_LR)
        calls.append(('mode2', hex(r0)))
        uc.reg_write(UC_ARM_REG_PC, lr)

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_get_work, begin=MOCK_GET_WORK, end=MOCK_GET_WORK + 4)
    uc.hook_add(unicorn.UC_HOOK_CODE, hook_draw_m1, begin=MOCK_DRAW_M1, end=MOCK_DRAW_M1 + 4)
    uc.hook_add(unicorn.UC_HOOK_CODE, hook_draw_m2, begin=MOCK_DRAW_M2, end=MOCK_DRAW_M2 + 4)

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=1000000, count=500)
    return {'return_value': uc.reg_read(UC_ARM_REG_R0), 'calls': calls, 'sp_preserved': uc.reg_read(UC_ARM_REG_SP) == SP_INIT}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'build/h5_target_select_draw_test.json')
    args = parser.parse_args()

    with open(CODE_PATH, 'rb') as f:
        code_bytes = f.read()

    out_dir = ROOT / 'build/h5_candidates'
    blob_cand, raw_cand, blob_mut, raw_mut = build_candidates(out_dir)

    modes = [0, 1, 2, 3]
    results = []
    all_matched = True

    for m in modes:
        res_orig = run_simulation(code_bytes, blob_cand, ORIG_ADDR, m)
        res_cand = run_simulation(code_bytes, blob_cand, CAND_ADDR, m)
        matched = (res_orig['calls'] == res_cand['calls'] and res_orig['return_value'] == res_cand['return_value'] and res_cand['sp_preserved'])
        results.append({'mode': m, 'orig': res_orig, 'cand': res_cand, 'matched': matched})
        if not matched: all_matched = False

    res_mut = run_simulation(code_bytes, blob_mut, CAND_ADDR, 1)
    mutation_detected = (res_mut['calls'] != results[1]['orig']['calls'])

    report = {
        'status': 'passed' if (all_matched and mutation_detected) else 'failed',
        'function': 'btlTargetSelect_DrawUp',
        'address': hex(ORIG_ADDR),
        'candidate_size': len(raw_cand),
        'original_size': ORIG_SIZE,
        'fits': len(raw_cand) <= ORIG_SIZE,
        'all_matched': all_matched,
        'mutation_detected': mutation_detected,
        'fixtures': results
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as out_f:
        json.dump(report, out_f, indent=2)

    print(f"btlTargetSelect_DrawUp: status={report['status']} (matched={all_matched}, mut_detected={mutation_detected})")
    if not (all_matched and mutation_detected):
        sys.exit(1)

if __name__ == '__main__':
    main()
