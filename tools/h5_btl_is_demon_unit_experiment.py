#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002AE464 Btl_IsDemonUnit."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h5_btl_is_demon_unit_candidate.cpp'
ORIG_ADDR = 0x002AE464
ORIG_SIZE = 16
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'btl_is_demon_unit.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h5_btl_is_demon_unit_candidate']
    raw_mut, _ = funcs['h5_btl_is_demon_unit_mutation']
    return raw_cand, raw_cand, raw_mut, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, unit_id: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, cand_blob + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_R0, unit_id)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=1000000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'build/h5_is_demon_unit_test.json')
    args = parser.parse_args()

    with open(CODE_PATH, 'rb') as f:
        code_bytes = f.read()

    out_dir = ROOT / 'build/h5_candidates'
    blob_cand, raw_cand, blob_mut, raw_mut = build_candidates(out_dir)

    test_ids = [0, 1, 100, 399, 400, 401, 402, 500, 800, 0xFFFF]
    results = []
    all_matched = True

    for uid in test_ids:
        res_orig = run_simulation(code_bytes, blob_cand, ORIG_ADDR, uid)
        res_cand = run_simulation(code_bytes, blob_cand, CAND_ADDR, uid)
        matched = (res_orig == res_cand)
        results.append({'unit_id': uid, 'orig': res_orig, 'cand': res_cand, 'matched': matched})
        if not matched: all_matched = False

    # Mutation test (should return 0 always)
    res_mut = run_simulation(code_bytes, blob_mut, CAND_ADDR, 500)
    mutation_detected = (res_mut != 1)

    report = {
        'status': 'passed' if (all_matched and mutation_detected) else 'failed',
        'function': 'Btl_IsDemonUnit',
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

    print(f"Btl_IsDemonUnit: status={report['status']} (matched={all_matched}, mut_detected={mutation_detected})")
    if not (all_matched and mutation_detected):
        sys.exit(1)

if __name__ == '__main__':
    main()
