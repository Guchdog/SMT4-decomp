#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002B8A80 Btl_ReleaseState."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h5_btl_release_state_candidate.cpp'
ORIG_ADDR = 0x002B8A80
ORIG_SIZE = 92
CAND_ADDR = 0x00600000

MOCK_CHECK_STATE = 0x002B2530
MOCK_FREE = 0x002C4360
ADDR_GLOBAL_SLOT = 0x00447E28

def branch_word(src: int, tgt: int, is_bl: bool = False) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'btl_release_state.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, rels_cand = funcs['h5_btl_release_state_candidate']
    raw_mut, rels_mut = funcs['h5_btl_release_state_mutation']

    def resolve_relocs(raw, rels):
        blob = bytearray(raw)
        for r in rels:
            if 'SubObject_CheckState' in r.symbol_name:
                w = branch_word(CAND_ADDR + r.offset, MOCK_CHECK_STATE, is_bl=True)
                struct.pack_into('<I', blob, r.offset, w)
            elif 'Free' in r.symbol_name:
                w = branch_word(CAND_ADDR + r.offset, MOCK_FREE, is_bl=True)
                struct.pack_into('<I', blob, r.offset, w)
            elif 'g_CombatSubWork' in r.symbol_name:
                struct.pack_into('<I', blob, r.offset, ADDR_GLOBAL_SLOT)
            else:
                pass
        return bytes(blob)

    blob_cand = resolve_relocs(raw_cand, rels_cand)
    blob_mut = resolve_relocs(raw_mut, rels_mut)
    return blob_cand, raw_cand, blob_mut, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, fixture: dict) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x2000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, cand_blob + b'\x00' * (0x2000 - len(cand_blob)))

    HEAP_BASE = 0x08200000
    uc.mem_map(HEAP_BASE, 0x10000, unicorn.UC_PROT_ALL)

    WORK_ADDR = HEAP_BASE + 0x1000
    SUBOBJ_ADDR = HEAP_BASE + 0x2000

    if fixture.get('has_work', True):
        uc.mem_write(ADDR_GLOBAL_SLOT, struct.pack('<I', WORK_ADDR))
        uc.mem_write(WORK_ADDR + 0x00, struct.pack('<I', SUBOBJ_ADDR))
        uc.mem_write(WORK_ADDR + 0x0C, bytes([fixture.get('flag', 1)]))
    else:
        uc.mem_write(ADDR_GLOBAL_SLOT, struct.pack('<I', 0))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    freed = []
    def hook_check_state(uc, address, size, user_data):
        lr = uc.reg_read(UC_ARM_REG_LR)
        # Returns 0 if ready/idle, non-zero if busy
        uc.reg_write(UC_ARM_REG_R0, fixture.get('sub_state', 0))
        uc.reg_write(UC_ARM_REG_PC, lr)

    def hook_free(uc, address, size, user_data):
        lr = uc.reg_read(UC_ARM_REG_LR)
        ptr = uc.reg_read(UC_ARM_REG_R0)
        freed.append(hex(ptr))
        uc.reg_write(UC_ARM_REG_PC, lr)

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_check_state, begin=MOCK_CHECK_STATE, end=MOCK_CHECK_STATE + 4)
    uc.hook_add(unicorn.UC_HOOK_CODE, hook_free, begin=MOCK_FREE, end=MOCK_FREE + 4)

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=1000000, count=500)

    global_after = struct.unpack('<I', uc.mem_read(ADDR_GLOBAL_SLOT, 4))[0]

    return {
        'return_value': uc.reg_read(UC_ARM_REG_R0),
        'freed': freed,
        'global_after': hex(global_after),
        'sp_preserved': uc.reg_read(UC_ARM_REG_SP) == SP_INIT
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'build/h5_release_state_test.json')
    args = parser.parse_args()

    with open(CODE_PATH, 'rb') as f:
        code_bytes = f.read()

    out_dir = ROOT / 'build/h5_candidates'
    blob_cand, raw_cand, blob_mut, raw_mut = build_candidates(out_dir)

    fixtures = [
        {'name': 'normal_dealloc', 'has_work': True, 'sub_state': 0, 'flag': 1},
        {'name': 'busy_subobj', 'has_work': True, 'sub_state': 1, 'flag': 1},
        {'name': 'flag_zero_skip', 'has_work': True, 'sub_state': 0, 'flag': 0},
        {'name': 'null_work', 'has_work': False, 'sub_state': 0, 'flag': 1},
    ]

    results = []
    all_matched = True

    for f in fixtures:
        res_orig = run_simulation(code_bytes, blob_cand, ORIG_ADDR, f)
        res_cand = run_simulation(code_bytes, blob_cand, CAND_ADDR, f)
        matched = (
            res_orig['return_value'] == res_cand['return_value'] and
            res_orig['freed'] == res_cand['freed'] and
            res_orig['global_after'] == res_cand['global_after'] and
            res_cand['sp_preserved']
        )
        results.append({'fixture': f['name'], 'orig': res_orig, 'cand': res_cand, 'matched': matched})
        if not matched: all_matched = False

    res_mut = run_simulation(code_bytes, blob_mut, CAND_ADDR, fixtures[0])
    mutation_detected = (res_mut['return_value'] != results[0]['orig']['return_value'])

    report = {
        'status': 'passed' if (all_matched and mutation_detected) else 'failed',
        'function': 'Btl_ReleaseState',
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

    print(f"Btl_ReleaseState: status={report['status']} (matched={all_matched}, mut_detected={mutation_detected})")
    if not (all_matched and mutation_detected):
        sys.exit(1)

if __name__ == '__main__':
    main()
