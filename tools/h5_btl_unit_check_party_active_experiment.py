#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001D29C8 btlUnit_CheckPartyActive."""
from __future__ import annotations
import argparse, hashlib, json, struct, sys
from pathlib import Path

import unicorn
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h5_btl_unit_check_party_active_candidate.cpp'
ORIG_ADDR = 0x001D29C8
ORIG_SIZE = 240
CAND_ADDR = 0x00600000

MOCK_UNIT_LOOKUP = 0x002AE3F0
MOCK_SUBPARTY_LOOKUP = 0x002B9364

def branch_word(src: int, tgt: int, is_bl: bool = False) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'btl_unit_check_party_active.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, rels_cand = funcs['h5_btl_unit_check_party_active_candidate']
    raw_mut, rels_mut = funcs['h5_btl_unit_check_party_active_mutation']

    def resolve_relocs(raw, rels):
        blob = bytearray(raw)
        for r in rels:
            if 'Unit_Lookup' in r.symbol_name:
                w = branch_word(CAND_ADDR + r.offset, MOCK_UNIT_LOOKUP, is_bl=True)
                struct.pack_into('<I', blob, r.offset, w)
            elif 'SubParty_Lookup' in r.symbol_name:
                w = branch_word(CAND_ADDR + r.offset, MOCK_SUBPARTY_LOOKUP, is_bl=True)
                struct.pack_into('<I', blob, r.offset, w)
            else:
                raise ValueError(f'Unknown relocation symbol {r.symbol_name}')
        return bytes(blob)

    blob_cand = resolve_relocs(raw_cand, rels_cand)
    blob_mut = resolve_relocs(raw_mut, rels_mut)
    return blob_cand, raw_cand, blob_mut, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, is_cand: bool, fixture: dict) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    # ROM code
    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Candidate memory
    uc.mem_map(CAND_ADDR, 0x4000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, cand_blob + b'\x00' * (0x4000 - len(cand_blob)))

    # Heap memory
    HEAP_BASE = 0x08200000
    uc.mem_map(HEAP_BASE, 0x100000, unicorn.UC_PROT_ALL)

    STACK_BASE = 0x0FFF0000
    STACK_SIZE = 0x10000
    uc.mem_map(STACK_BASE, STACK_SIZE, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + STACK_SIZE - 0x1000

    WORK_ADDR = HEAP_BASE + 0x1000
    PARTY_ADDR = HEAP_BASE + 0x2000
    RESERVE_ADDR = HEAP_BASE + 0x3000
    GUEST_ADDR = HEAP_BASE + 0x4000
    SUBPARTY_ADDR = HEAP_BASE + 0x5000
    UNIT_RECORD_ADDR = HEAP_BASE + 0x6000

    # Setup work structure
    uc.mem_write(WORK_ADDR + 0x278, struct.pack('<I', PARTY_ADDR if fixture.get('has_party', True) else 0))
    uc.mem_write(WORK_ADDR + 0x27C, struct.pack('<I', RESERVE_ADDR if fixture.get('has_reserve', False) else 0))
    uc.mem_write(WORK_ADDR + 0x284, struct.pack('<I', GUEST_ADDR if fixture.get('has_guest', False) else 0))
    uc.mem_write(WORK_ADDR + 0xCE, struct.pack('<H', fixture.get('sub_party_id', 1)))

    # Setup slots
    for i in range(8):
        uid = fixture.get('party_slots', [0]*8)[i]
        uc.mem_write(PARTY_ADDR + 0x34 + i * 2, struct.pack('<H', uid))
        uid_res = fixture.get('reserve_slots', [0]*8)[i]
        uc.mem_write(RESERVE_ADDR + 0x34 + i * 2, struct.pack('<H', uid_res))
        uid_gst = fixture.get('guest_slots', [0]*8)[i]
        uc.mem_write(SUBPARTY_ADDR + 0x3C + i * 2, struct.pack('<H', uid_gst))

    # Unit lookup returns UNIT_RECORD_ADDR + (unit_id * 0x40)
    # Unit status at offset +0x23
    for uid, status in fixture.get('unit_status_map', {}).items():
        rec = UNIT_RECORD_ADDR + (uid * 0x40)
        uc.mem_write(rec + 0x23, bytes([status]))

    def hook_unit_lookup(uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        lr = uc.reg_read(UC_ARM_REG_LR)
        if r0 in fixture.get('unit_status_map', {}):
            rec = UNIT_RECORD_ADDR + (r0 * 0x40)
            uc.reg_write(UC_ARM_REG_R0, rec)
        else:
            uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_PC, lr)

    def hook_subparty_lookup(uc, address, size, user_data):
        lr = uc.reg_read(UC_ARM_REG_LR)
        uc.reg_write(UC_ARM_REG_R0, SUBPARTY_ADDR)
        uc.reg_write(UC_ARM_REG_PC, lr)

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_unit_lookup, begin=MOCK_UNIT_LOOKUP, end=MOCK_UNIT_LOOKUP + 4)
    uc.hook_add(unicorn.UC_HOOK_CODE, hook_subparty_lookup, begin=MOCK_SUBPARTY_LOOKUP, end=MOCK_SUBPARTY_LOOKUP + 4)

    # Set initial registers
    uc.reg_write(UC_ARM_REG_R0, WORK_ADDR)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=5000000, count=5000)

    res_r0 = uc.reg_read(UC_ARM_REG_R0)
    sp_final = uc.reg_read(UC_ARM_REG_SP)
    return {'return_value': res_r0, 'sp_preserved': sp_final == SP_INIT}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'build/h5_party_active_test.json')
    args = parser.parse_args()

    with open(CODE_PATH, 'rb') as f:
        code_bytes = f.read()

    out_dir = ROOT / 'build/h5_candidates'
    blob_cand, raw_cand, blob_mut, raw_mut = build_candidates(out_dir)

    fixtures = [
        {'name': 'party_slot0_alive', 'has_party': True, 'party_slots': [10, 0, 0, 0, 0, 0, 0, 0], 'unit_status_map': {10: 3}},
        {'name': 'party_slot3_alive', 'has_party': True, 'party_slots': [1, 2, 3, 4, 0, 0, 0, 0], 'unit_status_map': {1: 1, 2: 1, 3: 1, 4: 3}},
        {'name': 'party_all_dead', 'has_party': True, 'party_slots': [1, 2, 0, 0, 0, 0, 0, 0], 'unit_status_map': {1: 1, 2: 2}},
        {'name': 'reserve_alive', 'has_party': True, 'has_reserve': True, 'party_slots': [1, 0, 0, 0, 0, 0, 0, 0], 'reserve_slots': [5, 0, 0, 0, 0, 0, 0, 0], 'unit_status_map': {1: 1, 5: 3}},
        {'name': 'guest_alive', 'has_party': True, 'has_guest': True, 'party_slots': [1, 0, 0, 0, 0, 0, 0, 0], 'guest_slots': [8, 0, 0, 0, 0, 0, 0, 0], 'unit_status_map': {1: 1, 8: 3}},
        {'name': 'empty_party', 'has_party': False, 'has_reserve': False, 'has_guest': False},
    ]

    results = []
    all_matched = True
    for f in fixtures:
        res_orig = run_simulation(code_bytes, blob_cand, ORIG_ADDR, False, f)
        res_cand = run_simulation(code_bytes, blob_cand, CAND_ADDR, True, f)
        matched = (res_orig['return_value'] == res_cand['return_value'] and res_orig['sp_preserved'] and res_cand['sp_preserved'])
        results.append({'fixture': f['name'], 'orig': res_orig, 'cand': res_cand, 'matched': matched})
        if not matched: all_matched = False

    # Mutation test
    res_mut = run_simulation(code_bytes, blob_mut, CAND_ADDR, True, fixtures[0])
    mutation_detected = (res_mut['return_value'] != results[0]['orig']['return_value'])

    report = {
        'status': 'passed' if (all_matched and mutation_detected) else 'failed',
        'function': 'btlUnit_CheckPartyActive',
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

    print(f"btlUnit_CheckPartyActive: status={report['status']} (matched={all_matched}, mut_detected={mutation_detected})")
    if not (all_matched and mutation_detected):
        sys.exit(1)

if __name__ == '__main__':
    main()
