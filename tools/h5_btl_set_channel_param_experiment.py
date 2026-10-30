#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0011311C Btl_SetChannelParameter."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h5_btl_set_channel_param_candidate.cpp'
ORIG_ADDR = 0x0011311C
ORIG_SIZE = 52
CAND_ADDR = 0x00600000

ADDR_CTX = 0x004C6290

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'btl_set_channel_param.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, rels_cand = funcs['h5_btl_set_channel_param_candidate']
    raw_mut, rels_mut = funcs['h5_btl_set_channel_param_mutation']

    def resolve_relocs(raw, rels):
        blob = bytearray(raw)
        for r in rels:
            if 'g_CombatChannelContext' in r.symbol_name:
                struct.pack_into('<I', blob, r.offset, ADDR_CTX)
            else:
                pass
        return bytes(blob)

    blob_cand = resolve_relocs(raw_cand, rels_cand)
    blob_mut = resolve_relocs(raw_mut, rels_mut)
    return blob_cand, raw_cand, blob_mut, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, mode: int, val: int) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x2000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, cand_blob + b'\x00' * (0x2000 - len(cand_blob)))

    # Context memory is within mapped space
    uc.mem_write(ADDR_CTX + 0x15C, struct.pack('<I', 0x11111111))
    uc.mem_write(ADDR_CTX + 0x160, struct.pack('<I', 0x22222222))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_R0, mode)
    uc.reg_write(UC_ARM_REG_R1, val)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=1000000, count=50)

    c0 = struct.unpack('<I', uc.mem_read(ADDR_CTX + 0x15C, 4))[0]
    c1 = struct.unpack('<I', uc.mem_read(ADDR_CTX + 0x160, 4))[0]

    return {
        'channel0': hex(c0),
        'channel1': hex(c1),
        'sp_preserved': uc.reg_read(UC_ARM_REG_SP) == SP_INIT
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'build/h5_set_channel_param_test.json')
    args = parser.parse_args()

    with open(CODE_PATH, 'rb') as f:
        code_bytes = f.read()

    out_dir = ROOT / 'build/h5_candidates'
    blob_cand, raw_cand, blob_mut, raw_mut = build_candidates(out_dir)

    fixtures = [
        {'name': 'mode_0x400_channel0', 'mode': 0x400, 'val': 0x55AA55AA},
        {'name': 'mode_0x401_channel1', 'mode': 0x401, 'val': 0x33CC33CC},
        {'name': 'mode_0x402_both', 'mode': 0x402, 'val': 0x77EE77EE},
        {'name': 'mode_other_no_change', 'mode': 0x100, 'val': 0x99999999},
    ]

    results = []
    all_matched = True

    for f in fixtures:
        res_orig = run_simulation(code_bytes, blob_cand, ORIG_ADDR, f['mode'], f['val'])
        res_cand = run_simulation(code_bytes, blob_cand, CAND_ADDR, f['mode'], f['val'])
        matched = (
            res_orig['channel0'] == res_cand['channel0'] and
            res_orig['channel1'] == res_cand['channel1'] and
            res_cand['sp_preserved']
        )
        results.append({'fixture': f['name'], 'orig': res_orig, 'cand': res_cand, 'matched': matched})
        if not matched: all_matched = False

    res_mut = run_simulation(code_bytes, blob_mut, CAND_ADDR, 0x400, 0x55AA55AA)
    mutation_detected = (res_mut['channel0'] != results[0]['orig']['channel0'])

    report = {
        'status': 'passed' if (all_matched and mutation_detected) else 'failed',
        'function': 'Btl_SetChannelParameter',
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

    print(f"Btl_SetChannelParameter: status={report['status']} (matched={all_matched}, mut_detected={mutation_detected})")
    if not (all_matched and mutation_detected):
        sys.exit(1)

if __name__ == '__main__':
    main()
