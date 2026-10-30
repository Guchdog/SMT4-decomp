#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001B4B74 Map_DispatchTrigger."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h4_map_dispatch_candidate.cpp'
ORIG_ADDR = 0x001B4B74
ORIG_SIZE = 36
CAND_ADDR = 0x00600000

MOCK_TARGET = 0x003BA944
ADDR_MAP_CONTEXT = 0x0044CFD0

def branch_word(src: int, tgt: int, is_bl: bool = False) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'map_dispatch.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, rels_cand = funcs['h4_map_dispatch_trigger_candidate']
    raw_mut, rels_mut = funcs['h4_map_dispatch_trigger_mutation']

    def resolve_relocs(raw, rels):
        blob = bytearray(raw)
        for r in rels:
            if 'TriggerHandler' in r.symbol_name:
                w = branch_word(CAND_ADDR + r.offset, MOCK_TARGET, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob, r.offset, w)
            elif 'MapContextWork' in r.symbol_name:
                struct.pack_into('<I', blob, r.offset, ADDR_MAP_CONTEXT)
            else:
                raise ValueError(f'Unknown relocation symbol {r.symbol_name}')
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

    # Heap memory
    HEAP_BASE = 0x08200000
    uc.mem_map(HEAP_BASE, 0x100000, unicorn.UC_PROT_ALL)

    STACK_BASE = 0x0FFF0000
    STACK_SIZE = 0x10000
    uc.mem_map(STACK_BASE, STACK_SIZE, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + STACK_SIZE - 0x1000

    MANAGER_ADDR = HEAP_BASE + 0x1000
    HANDLER_ADDR = HEAP_BASE + 0x2000

    # Setup MapContextWork at 0x0044CFD0
    if fixture.get('has_manager', True):
        uc.mem_write(ADDR_MAP_CONTEXT + 0x04, struct.pack('<I', MANAGER_ADDR))
        if fixture.get('has_handler', True):
            uc.mem_write(MANAGER_ADDR + 0x08, struct.pack('<I', HANDLER_ADDR))
            uc.mem_write(HANDLER_ADDR + 0x20, struct.pack('<I', fixture.get('initial_flags', 0x10)))
        else:
            uc.mem_write(MANAGER_ADDR + 0x08, struct.pack('<I', 0))
    else:
        uc.mem_write(ADDR_MAP_CONTEXT + 0x04, struct.pack('<I', 0))

    # Track target calls
    calls = []
    def hook_target(uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        flags_val = struct.unpack('<I', uc.mem_read(r0 + 0x20, 4))[0] if r0 != 0 else None
        calls.append({'target': hex(address), 'r0': hex(r0), 'flags_before': flags_val})
        # Simulate the real target function at 0x003BA944:
        # ldr r1, [r0, #0x20]; orr r1, r1, #0x80; str r1, [r0, #0x20]; bx lr
        if r0 != 0:
            uc.mem_write(r0 + 0x20, struct.pack('<I', (flags_val or 0) | 0x80))
        lr = uc.reg_read(UC_ARM_REG_LR)
        uc.reg_write(UC_ARM_REG_PC, lr)

    uc.mem_write(MOCK_TARGET, b'\x1e\xff\x2f\xe1') # bx lr
    uc.hook_add(unicorn.UC_HOOK_CODE, hook_target, begin=MOCK_TARGET, end=MOCK_TARGET)

    # Initialize registers
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

    flags_after = None
    if fixture.get('has_manager', True) and fixture.get('has_handler', True):
        flags_after = struct.unpack('<I', uc.mem_read(HANDLER_ADDR + 0x20, 4))[0]

    return {
        'calls': calls,
        'sp': uc.reg_read(UC_ARM_REG_SP),
        'r4': uc.reg_read(UC_ARM_REG_R4),
        'r5': uc.reg_read(UC_ARM_REG_R5),
        'flags_after': flags_after,
    }

def run_experiment(out_dir: Path):
    image = CODE_PATH.read_bytes()
    blob_cand, raw_cand, blob_mut, raw_mut = build_candidates(out_dir)

    fixtures = [
        {'name': 'full_chain_clean', 'has_manager': True, 'has_handler': True, 'initial_flags': 0},
        {'name': 'full_chain_preflagged', 'has_manager': True, 'has_handler': True, 'initial_flags': 0x80},
        {'name': 'full_chain_other_flags', 'has_manager': True, 'has_handler': True, 'initial_flags': 0x55},
        {'name': 'null_manager', 'has_manager': False},
        {'name': 'null_handler', 'has_manager': True, 'has_handler': False},
    ]

    results = []
    diff_count = 0

    for fix in fixtures:
        orig_out = run_simulation(image, blob_cand, ORIG_ADDR, False, fix)
        cand_out = run_simulation(image, blob_cand, CAND_ADDR, True, fix)

        diffs = []
        for k in ['calls', 'sp', 'r4', 'r5', 'flags_after']:
            if orig_out[k] != cand_out[k]:
                diffs.append(f'{k}: orig={orig_out[k]} vs cand={cand_out[k]}')

        if diffs:
            diff_count += 1
            results.append({'fixture': fix['name'], 'status': 'fail', 'diffs': diffs})
        else:
            results.append({'fixture': fix['name'], 'status': 'pass', 'diffs': [], 'calls': len(cand_out['calls'])})

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
    parser.add_argument('--out-dir', type=Path, default=ROOT / 'build/agent-work/H4-semantic/h4-map-dispatch-candidate/run-001')
    args = parser.parse_args()
    report = run_experiment(args.out_dir)
    if report['status'] != 'passed':
        sys.exit(1)

if __name__ == '__main__':
    main()
