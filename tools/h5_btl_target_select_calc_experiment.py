#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002E06BC btlTargetSelect_Calc."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h5_btl_target_select_calc_candidate.cpp'
ORIG_ADDR = 0x002E06BC
ORIG_SIZE = 236
CAND_ADDR = 0x00600000

MOCK_GET_WORK = 0x002C0AC8
MOCK_UPDATE_ANIM = 0x002BF9F0
MOCK_MODE1_CALC = 0x003428A4

def branch_word(src: int, tgt: int, is_bl: bool = False) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'btl_target_select_calc.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, rels_cand = funcs['h5_btl_target_select_calc_candidate']
    raw_mut, rels_mut = funcs['h5_btl_target_select_calc_mutation']

    def resolve_relocs(raw, rels):
        blob = bytearray(raw)
        for r in rels:
            if 'GetWork' in r.symbol_name:
                w = branch_word(CAND_ADDR + r.offset, MOCK_GET_WORK, is_bl=True)
                struct.pack_into('<I', blob, r.offset, w)
            elif 'UpdateAnim' in r.symbol_name:
                w = branch_word(CAND_ADDR + r.offset, MOCK_UPDATE_ANIM, is_bl=True)
                struct.pack_into('<I', blob, r.offset, w)
            elif 'Mode1Calc' in r.symbol_name:
                w = branch_word(CAND_ADDR + r.offset, MOCK_MODE1_CALC, is_bl=True)
                struct.pack_into('<I', blob, r.offset, w)
            else:
                raise ValueError(f'Unknown relocation symbol {r.symbol_name}')
        return bytes(blob)

    blob_cand = resolve_relocs(raw_cand, rels_cand)
    blob_mut = resolve_relocs(raw_mut, rels_mut)
    return blob_cand, raw_cand, blob_mut, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, fixture: dict) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x4000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, cand_blob + b'\x00' * (0x4000 - len(cand_blob)))

    HEAP_BASE = 0x08200000
    uc.mem_map(HEAP_BASE, 0x10000, unicorn.UC_PROT_ALL)

    WORK_ADDR = HEAP_BASE + 0x1000
    OBJ0_ADDR = HEAP_BASE + 0x2000
    OBJ1_ADDR = HEAP_BASE + 0x3000

    uc.mem_write(WORK_ADDR + 0x00, struct.pack('<I', OBJ0_ADDR))
    uc.mem_write(WORK_ADDR + 0x04, struct.pack('<I', OBJ1_ADDR))
    uc.mem_write(WORK_ADDR + 0x08, bytes([fixture.get('mode', 2)]))
    uc.mem_write(WORK_ADDR + 0x30, struct.pack('<I', fixture.get('state', 0)))

    # Initial float values on obj1
    uc.mem_write(OBJ1_ADDR + 0x58, struct.pack('<f', fixture.get('f58', 10.0)))
    uc.mem_write(OBJ1_ADDR + 0x5C, struct.pack('<f', fixture.get('f5c', 100.0)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    anim_called = []
    mode1_called = []
    def hook_get_work(uc, address, size, user_data):
        lr = uc.reg_read(UC_ARM_REG_LR)
        uc.reg_write(UC_ARM_REG_R0, WORK_ADDR)
        uc.reg_write(UC_ARM_REG_PC, lr)

    def hook_update_anim(uc, address, size, user_data):
        lr = uc.reg_read(UC_ARM_REG_LR)
        anim_called.append(True)
        uc.reg_write(UC_ARM_REG_PC, lr)

    def hook_mode1_calc(uc, address, size, user_data):
        lr = uc.reg_read(UC_ARM_REG_LR)
        mode1_called.append(True)
        uc.reg_write(UC_ARM_REG_PC, lr)

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_get_work, begin=MOCK_GET_WORK, end=MOCK_GET_WORK + 4)
    uc.hook_add(unicorn.UC_HOOK_CODE, hook_update_anim, begin=MOCK_UPDATE_ANIM, end=MOCK_UPDATE_ANIM + 4)
    uc.hook_add(unicorn.UC_HOOK_CODE, hook_mode1_calc, begin=MOCK_MODE1_CALC, end=MOCK_MODE1_CALC + 4)

    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=2000000, count=500)

    f58_res = struct.unpack('<f', uc.mem_read(OBJ1_ADDR + 0x58, 4))[0]
    f5c_res = struct.unpack('<f', uc.mem_read(OBJ1_ADDR + 0x5C, 4))[0]
    flag0 = struct.unpack('<I', uc.mem_read(OBJ0_ADDR + 0x120, 4))[0]
    flag1 = struct.unpack('<I', uc.mem_read(OBJ1_ADDR + 0x54, 4))[0]

    return {
        'return_value': uc.reg_read(UC_ARM_REG_R0),
        'f58': f58_res,
        'f5c': f5c_res,
        'flag0': flag0,
        'flag1': flag1,
        'anim_called': len(anim_called) > 0,
        'mode1_called': len(mode1_called) > 0,
        'sp_preserved': uc.reg_read(UC_ARM_REG_SP) == SP_INIT
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'build/h5_target_select_calc_test.json')
    args = parser.parse_args()

    with open(CODE_PATH, 'rb') as f:
        code_bytes = f.read()

    out_dir = ROOT / 'build/h5_candidates'
    blob_cand, raw_cand, blob_mut, raw_mut = build_candidates(out_dir)

    fixtures = [
        {'name': 'mode2_step_normal', 'mode': 2, 'state': 0, 'f58': 10.0, 'f5c': 100.0},
        {'name': 'mode2_f58_wrap', 'mode': 2, 'state': 0, 'f58': 29.5, 'f5c': 100.0},
        {'name': 'mode2_f5c_wrap', 'mode': 2, 'state': 0, 'f58': 10.0, 'f5c': 355.0},
        {'name': 'mode1_calc', 'mode': 1, 'state': 0x71, 'f58': 10.0, 'f5c': 100.0},
        {'name': 'mode0_idle', 'mode': 0, 'state': 0x71, 'f58': 10.0, 'f5c': 100.0},
    ]

    results = []
    all_matched = True

    for f in fixtures:
        res_orig = run_simulation(code_bytes, blob_cand, ORIG_ADDR, f)
        res_cand = run_simulation(code_bytes, blob_cand, CAND_ADDR, f)
        matched = (
            abs(res_orig['f58'] - res_cand['f58']) < 0.001 and
            abs(res_orig['f5c'] - res_cand['f5c']) < 0.001 and
            res_orig['flag0'] == res_cand['flag0'] and
            res_orig['flag1'] == res_cand['flag1'] and
            res_orig['anim_called'] == res_cand['anim_called'] and
            res_orig['mode1_called'] == res_cand['mode1_called'] and
            res_cand['sp_preserved']
        )
        results.append({'fixture': f['name'], 'orig': res_orig, 'cand': res_cand, 'matched': matched})
        if not matched: all_matched = False

    res_mut = run_simulation(code_bytes, blob_mut, CAND_ADDR, fixtures[0])
    mutation_detected = abs(res_mut['f58'] - results[0]['orig']['f58']) > 0.1

    report = {
        'status': 'passed' if (all_matched and mutation_detected) else 'failed',
        'function': 'btlTargetSelect_Calc',
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

    print(f"btlTargetSelect_Calc: status={report['status']} (matched={all_matched}, mut_detected={mutation_detected})")
    if not (all_matched and mutation_detected):
        sys.exit(1)

if __name__ == '__main__':
    main()
