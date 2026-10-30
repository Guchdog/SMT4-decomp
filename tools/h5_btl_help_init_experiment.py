#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001D2528 btlHelp_Init."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h5_btl_help_init_candidate.cpp'
ORIG_ADDR = 0x001D2528
ORIG_SIZE = 232
CAND_ADDR = 0x00600000

MOCK_DESTROY = 0x002BF41C
MOCK_CREATE = 0x002C4C00
MOCK_ALLOC = 0x002C4B84
MOCK_CALC = 0x001B5398
ADDR_HELP_MGR = 0x00435D78

def branch_word(src: int, tgt: int, is_bl: bool = False) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'btl_help_init.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, rels_cand = funcs['h5_btl_help_init_candidate']
    raw_mut, rels_mut = funcs['h5_btl_help_init_mutation']

    def resolve_relocs(raw, rels):
        blob = bytearray(raw)
        for r in rels:
            if 'Task_Destroy' in r.symbol_name:
                w = branch_word(CAND_ADDR + r.offset, MOCK_DESTROY, is_bl=True)
                struct.pack_into('<I', blob, r.offset, w)
            elif 'Task_Create' in r.symbol_name:
                w = branch_word(CAND_ADDR + r.offset, MOCK_CREATE, is_bl=True)
                struct.pack_into('<I', blob, r.offset, w)
            elif 'Mem_Alloc' in r.symbol_name:
                w = branch_word(CAND_ADDR + r.offset, MOCK_ALLOC, is_bl=True)
                struct.pack_into('<I', blob, r.offset, w)
            elif 'btlHelp_Calc' in r.symbol_name:
                struct.pack_into('<I', blob, r.offset, MOCK_CALC)
            elif 'g_BtlHelpManager' in r.symbol_name:
                struct.pack_into('<I', blob, r.offset, ADDR_HELP_MGR)
            elif r.symbol_name == '':
                # String constant "btlHelp Calc" in original binary at 0x001d25c8
                struct.pack_into('<I', blob, r.offset, 0x001D25C8)
            else:
                pass
        return bytes(blob)

    blob_cand = resolve_relocs(raw_cand, rels_cand)
    blob_mut = resolve_relocs(raw_mut, rels_mut)
    return blob_cand, raw_cand, blob_mut, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, existing_task: int) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x4000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, cand_blob + b'\x00' * (0x4000 - len(cand_blob)))

    HEAP_BASE = 0x08200000
    uc.mem_map(HEAP_BASE, 0x20000, unicorn.UC_PROT_ALL)

    WORK_ADDR = HEAP_BASE + 0x1000
    PARENT_ADDR = HEAP_BASE + 0x2000
    TASK_HANDLE = HEAP_BASE + 0x3000
    BUF_ADDR = HEAP_BASE + 0x4000

    uc.mem_write(WORK_ADDR + 0x00, struct.pack('<I', PARENT_ADDR))
    uc.mem_write(WORK_ADDR + 0x4C, struct.pack('<I', existing_task))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    created_tasks = []
    allocs = []

    def hook_destroy(uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        lr = uc.reg_read(UC_ARM_REG_LR)
        # Return 0 if no error/task destroyed, non-zero if active/not destroyed
        uc.reg_write(UC_ARM_REG_R0, 0 if r0 == 0 else 1)
        uc.reg_write(UC_ARM_REG_PC, lr)

    def hook_create(uc, address, size, user_data):
        lr = uc.reg_read(UC_ARM_REG_LR)
        r0_name_ptr = uc.reg_read(UC_ARM_REG_R0)
        try:
            name = uc.mem_read(r0_name_ptr, 12).split(b'\x00')[0].decode('ascii', errors='ignore')
        except:
            name = ''
        created_tasks.append(name)
        uc.reg_write(UC_ARM_REG_R0, TASK_HANDLE)
        uc.reg_write(UC_ARM_REG_PC, lr)

    def hook_alloc(uc, address, size, user_data):
        lr = uc.reg_read(UC_ARM_REG_LR)
        size_arg = uc.reg_read(UC_ARM_REG_R3)
        allocs.append(size_arg)
        # Pre-fill buffer with 0xFF to check zeroing
        uc.mem_write(BUF_ADDR, b'\xFF' * 16)
        uc.reg_write(UC_ARM_REG_R0, BUF_ADDR)
        uc.reg_write(UC_ARM_REG_PC, lr)

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_destroy, begin=MOCK_DESTROY, end=MOCK_DESTROY + 4)
    uc.hook_add(unicorn.UC_HOOK_CODE, hook_create, begin=MOCK_CREATE, end=MOCK_CREATE + 4)
    uc.hook_add(unicorn.UC_HOOK_CODE, hook_alloc, begin=MOCK_ALLOC, end=MOCK_ALLOC + 4)

    uc.reg_write(UC_ARM_REG_R0, WORK_ADDR)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=2000000, count=500)

    task_after = struct.unpack('<I', uc.mem_read(WORK_ADDR + 0x4C, 4))[0]
    buf_ptr = struct.unpack('<I', uc.mem_read(ADDR_HELP_MGR, 4))[0]
    buf_bytes = uc.mem_read(BUF_ADDR, 12) if len(allocs) > 0 else b''

    return {
        'task_after': hex(task_after),
        'created_tasks': created_tasks,
        'allocs': allocs,
        'buf_ptr': hex(buf_ptr),
        'buf_zeroed': buf_bytes == b'\x00' * 12,
        'sp_preserved': uc.reg_read(UC_ARM_REG_SP) == SP_INIT
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'build/h5_help_init_test.json')
    args = parser.parse_args()

    with open(CODE_PATH, 'rb') as f:
        code_bytes = f.read()

    out_dir = ROOT / 'build/h5_candidates'
    blob_cand, raw_cand, blob_mut, raw_mut = build_candidates(out_dir)

    fixtures = [
        {'name': 'fresh_init_no_prior_task', 'existing_task': 0},
        {'name': 'init_with_prior_task', 'existing_task': 0x08209999},
    ]

    results = []
    all_matched = True

    for f in fixtures:
        res_orig = run_simulation(code_bytes, blob_cand, ORIG_ADDR, f['existing_task'])
        res_cand = run_simulation(code_bytes, blob_cand, CAND_ADDR, f['existing_task'])
        matched = (
            res_orig['task_after'] == res_cand['task_after'] and
            res_orig['created_tasks'] == res_cand['created_tasks'] and
            res_orig['allocs'] == res_cand['allocs'] and
            res_orig['buf_zeroed'] == res_cand['buf_zeroed'] and
            res_cand['sp_preserved']
        )
        results.append({'fixture': f['name'], 'orig': res_orig, 'cand': res_cand, 'matched': matched})
        if not matched: all_matched = False

    res_mut = run_simulation(code_bytes, blob_mut, CAND_ADDR, 0)
    mutation_detected = (res_mut['task_after'] != results[0]['orig']['task_after'])

    report = {
        'status': 'passed' if (all_matched and mutation_detected) else 'failed',
        'function': 'btlHelp_Init',
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

    print(f"btlHelp_Init: status={report['status']} (matched={all_matched}, mut_detected={mutation_detected})")
    if not (all_matched and mutation_detected):
        sys.exit(1)

if __name__ == '__main__':
    main()
