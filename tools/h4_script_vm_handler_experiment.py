#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001B4B98 ScriptVM_NestedHandler11."""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path
import sys

import unicorn
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h4_script_vm_handler_candidate.cpp'
ORIG_ADDR = 0x001B4B98
ORIG_SIZE = 36
CAND_ADDR = 0x00600000

MOCK_GET_BOUNDS  = 0x00296F60
MOCK_CLAMP_RANGE = 0x00297004
MOCK_APPLY_STATE = 0x0028DF54

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'script_vm_handler.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, rels_cand = funcs['h4_script_vm_handler_candidate']
    raw_mut, rels_mut = funcs['h4_script_vm_handler_mutation']

    def resolve_relocs(raw, rels):
        blob = bytearray(raw)
        for r in rels:
            if 'GetBounds' in r.symbol_name:
                tgt = MOCK_GET_BOUNDS
            elif 'ClampRange' in r.symbol_name:
                tgt = MOCK_CLAMP_RANGE
            elif 'ApplyState' in r.symbol_name:
                tgt = MOCK_APPLY_STATE
            else:
                raise ValueError(f'Unknown relocation symbol {r.symbol_name}')
            w = branch_word(CAND_ADDR + r.offset, tgt, is_bl=(r.relocation_type == 28))
            struct.pack_into('<I', blob, r.offset, w)
        return bytes(blob)

    blob_cand = resolve_relocs(raw_cand, rels_cand)
    blob_mut = resolve_relocs(raw_mut, rels_mut)
    return blob_cand, raw_cand, blob_mut, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, is_cand: bool, fixture: dict) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    # Map ROM code
    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Candidate memory
    uc.mem_map(CAND_ADDR, 0x4000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, cand_blob + b'\x00' * (0x4000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    STACK_SIZE = 0x10000
    uc.mem_map(STACK_BASE, STACK_SIZE, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + STACK_SIZE - 0x1000

    calls = []

    def hook_get_bounds(uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        calls.append(('GetBounds', r0))
        uc.reg_write(UC_ARM_REG_R0, fixture.get('bounds_ret', 10))
        lr = uc.reg_read(UC_ARM_REG_LR)
        uc.reg_write(UC_ARM_REG_PC, lr)

    def hook_clamp(uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        calls.append(('ClampRange', r0, r1))
        ret = fixture.get('clamp_ret', max(r0, r1))
        uc.reg_write(UC_ARM_REG_R0, ret)
        lr = uc.reg_read(UC_ARM_REG_LR)
        uc.reg_write(UC_ARM_REG_PC, lr)

    def hook_apply(uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        calls.append(('ApplyState', r0))
        lr = uc.reg_read(UC_ARM_REG_LR)
        uc.reg_write(UC_ARM_REG_PC, lr)

    for mock_addr, hook in [
        (MOCK_GET_BOUNDS, hook_get_bounds),
        (MOCK_CLAMP_RANGE, hook_clamp),
        (MOCK_APPLY_STATE, hook_apply),
    ]:
        uc.mem_write(mock_addr, b'\x1e\xff\x2f\xe1')
        uc.hook_add(unicorn.UC_HOOK_CODE, hook, begin=mock_addr, end=mock_addr)

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    LR_MAGIC = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, LR_MAGIC)

    for reg, val in [
        (UC_ARM_REG_R4, 0x11111111),
        (UC_ARM_REG_R5, 0x22222222),
    ]:
        uc.reg_write(reg, val)

    try:
        uc.emu_start(entry, LR_MAGIC, timeout=2000000, count=500)
    except unicorn.UcError:
        pc = uc.reg_read(UC_ARM_REG_PC)
        if pc != LR_MAGIC:
            raise

    return {
        'ret_r0': uc.reg_read(UC_ARM_REG_R0),
        'calls': calls,
        'sp': uc.reg_read(UC_ARM_REG_SP),
        'r4': uc.reg_read(UC_ARM_REG_R4),
        'r5': uc.reg_read(UC_ARM_REG_R5),
    }

def run_experiment(out_dir: Path):
    image = CODE_PATH.read_bytes()
    blob_cand, raw_cand, blob_mut, raw_mut = build_candidates(out_dir)

    fixtures = [
        {'name': 'normal_range', 'bounds_ret': 10, 'clamp_ret': 10},
        {'name': 'zero_range', 'bounds_ret': 0, 'clamp_ret': 0},
        {'name': 'negative_bounds', 'bounds_ret': -5, 'clamp_ret': 0},
        {'name': 'large_bounds', 'bounds_ret': 1000, 'clamp_ret': 1000},
    ]

    results = []
    diff_count = 0

    for fix in fixtures:
        orig_out = run_simulation(image, blob_cand, ORIG_ADDR, False, fix)
        cand_out = run_simulation(image, blob_cand, CAND_ADDR, True, fix)

        diffs = []
        for k in ['ret_r0', 'calls', 'sp', 'r4', 'r5']:
            if orig_out[k] != cand_out[k]:
                diffs.append(f'{k}: orig={orig_out[k]} vs cand={cand_out[k]}')

        if diffs:
            diff_count += 1
            results.append({'fixture': fix['name'], 'status': 'fail', 'diffs': diffs})
        else:
            results.append({'fixture': fix['name'], 'status': 'pass', 'diffs': [], 'ret': cand_out['ret_r0']})

    # Mutation test
    orig_fix = fixtures[0]
    orig_res = run_simulation(image, blob_cand, ORIG_ADDR, False, orig_fix)
    mut_res = run_simulation(image, blob_mut, CAND_ADDR, True, orig_fix)
    mutation_detected = (orig_res != mut_res)

    report = {
        'status': 'passed' if diff_count == 0 and mutation_detected else 'failed',
        'fixtures_tested': len(fixtures),
        'mutation_detected': mutation_detected,
        'candidate_bytes': len(raw_cand),
        'original_bytes': ORIG_SIZE,
        'results': results,
    }

    (out_dir / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, default=ROOT / 'build/agent-work/H4-semantic/h4-script-vm-handler-candidate/run-001')
    args = parser.parse_args()
    report = run_experiment(args.out_dir)
    if report['status'] != 'passed':
        sys.exit(1)

if __name__ == '__main__':
    main()
