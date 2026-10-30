#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001B4A54 PlayerActor_UpdateVisibilityTransform."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h4_player_transform_candidate.cpp'
ORIG_ADDR = 0x001B4A54
ORIG_SIZE = 288
CAND_ADDR = 0x00600000

MOCK_TRANSLATION = 0x0028C8A8
MOCK_ROTATION    = 0x0028C880
MOCK_SCALE       = 0x002A5A54
MOCK_COMMIT      = 0x00287300

ADDR_PLAYER_WORK_PTR = 0x0044CDA0
ADDR_REPEAT_GATE_PTR = 0x0049F91C

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'player_transform.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, rels_cand = funcs['h4_player_transform_candidate']
    raw_mut, rels_mut = funcs['h4_player_transform_mutation']

    def resolve_relocs(raw, rels):
        blob = bytearray(raw)
        for r in rels:
            if 'SetTranslation' in r.symbol_name:
                tgt = MOCK_TRANSLATION
            elif 'SetRotation' in r.symbol_name:
                tgt = MOCK_ROTATION
            elif 'SetScale' in r.symbol_name:
                tgt = MOCK_SCALE
            elif 'CommitTransform' in r.symbol_name:
                tgt = MOCK_COMMIT
            elif 'PlayerActorWork' in r.symbol_name:
                struct.pack_into('<I', blob, r.offset, ADDR_PLAYER_WORK_PTR)
                continue
            elif 'RepeatGate' in r.symbol_name:
                struct.pack_into('<I', blob, r.offset, ADDR_REPEAT_GATE_PTR)
                continue
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
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0xF00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    # Map ROM code
    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Candidate memory
    uc.mem_map(CAND_ADDR, 0x8000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, cand_blob + b'\x00' * (0x8000 - len(cand_blob)))

    # Heap memory: 0x08000000..0x08300000
    HEAP_BASE = 0x08200000
    uc.mem_map(HEAP_BASE, 0x100000, unicorn.UC_PROT_ALL)

    # Stack memory
    STACK_BASE = 0x0FFF0000
    STACK_SIZE = 0x10000
    uc.mem_map(STACK_BASE, STACK_SIZE, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + STACK_SIZE - 0x1000

    # Pointers
    WORK_ADDR   = HEAP_BASE + 0x1000
    MODEL_ADDR  = HEAP_BASE + 0x2000
    BACKEND_ADDR= HEAP_BASE + 0x3000
    VISUAL_ADDR = HEAP_BASE + 0x4000
    GATE_ADDR   = HEAP_BASE + 0x5000

    ADDR_REPEAT_GATE = 0x0049F91C

    # Write global pointers
    uc.mem_write(ADDR_PLAYER_WORK_PTR, struct.pack('<I', WORK_ADDR))

    # Setup RepeatGate
    uc.mem_write(ADDR_REPEAT_GATE + 0x22, bytes([fixture.get('menu_pause', 0)]))

    # Setup Work
    # +0x10: active
    uc.mem_write(WORK_ADDR + 0x10, bytes([fixture.get('active', 1)]))
    # +0x14: pos (Vec3)
    pos = fixture.get('pos', (100.0, 200.0, 300.0))
    uc.mem_write(WORK_ADDR + 0x14, struct.pack('<3f', *pos))
    # +0x20: yaw
    uc.mem_write(WORK_ADDR + 0x20, struct.pack('<f', fixture.get('yaw', 1.57)))
    # +0x24: scale
    uc.mem_write(WORK_ADDR + 0x24, struct.pack('<I', fixture.get('scale', 1000)))
    # +0x28: dirty_flag
    uc.mem_write(WORK_ADDR + 0x28, bytes([fixture.get('dirty', 0)]))
    # +0x2C: model pointer
    if fixture.get('null_model'):
        uc.mem_write(WORK_ADDR + 0x2C, struct.pack('<I', 0))
    else:
        uc.mem_write(WORK_ADDR + 0x2C, struct.pack('<I', MODEL_ADDR))

    # Setup Model
    if not fixture.get('null_model'):
        uc.mem_write(MODEL_ADDR + 0x00, struct.pack('<I', fixture.get('flags', 0)))
        uc.mem_write(MODEL_ADDR + 0x08, struct.pack('<I', BACKEND_ADDR))
        uc.mem_write(BACKEND_ADDR + 0x2C, struct.pack('<I', VISUAL_ADDR))
        uc.mem_write(VISUAL_ADDR + 0x1F6, bytes([fixture.get('visible_1f6', 1)]))

    # Mock call log
    calls = []

    def hook_mock(uc, address, size, user_data):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        s0 = uc.reg_read(UC_ARM_REG_S0)
        s1 = uc.reg_read(UC_ARM_REG_S1)
        s2 = uc.reg_read(UC_ARM_REG_S2)
        name = user_data
        pos_read = None
        if name == 'SetTranslation':
            raw = uc.mem_read(r2, 12)
            pos_read = struct.unpack('<3f', raw)
        calls.append({
            'name': name,
            'r0': hex(r0),
            'r1': hex(r1),
            'r2': hex(r2),
            'pos': pos_read,
            's0': s0,
            's1': s1,
            's2': s2,
        })
        # Simulate bx lr
        lr = uc.reg_read(UC_ARM_REG_LR)
        uc.reg_write(UC_ARM_REG_PC, lr)

    for mock_addr, name in [
        (MOCK_TRANSLATION, 'SetTranslation'),
        (MOCK_ROTATION, 'SetRotation'),
        (MOCK_SCALE, 'SetScale'),
        (MOCK_COMMIT, 'CommitTransform'),
    ]:
        # Place bx lr stub at mock address
        uc.mem_write(mock_addr, b'\x1e\xff\x2f\xe1')
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_mock, user_data=name, begin=mock_addr, end=mock_addr)

    # Initialize registers
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    LR_MAGIC = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, LR_MAGIC)

    for reg, val in [
        (UC_ARM_REG_R4, 0x11111111),
        (UC_ARM_REG_R5, 0x22222222),
        (UC_ARM_REG_R6, 0x33333333),
        (UC_ARM_REG_R7, 0x44444444),
        (UC_ARM_REG_R8, 0x55555555),
    ]:
        uc.reg_write(reg, val)

    def hook_unmapped(uc, access, address, size, value, user_data):
        pc = uc.reg_read(UC_ARM_REG_PC)
        print(f"UNMAPPED: access={access} addr=0x{address:08X} size={size} at PC=0x{pc:08X}")
        return False

    uc.hook_add(unicorn.UC_HOOK_MEM_READ_UNMAPPED | unicorn.UC_HOOK_MEM_WRITE_UNMAPPED, hook_unmapped)

    end_addr = (CAND_ADDR + len(cand_blob)) if is_cand else (ORIG_ADDR + ORIG_SIZE)
    try:
        uc.emu_start(entry, LR_MAGIC, timeout=2000000, count=1000)
    except unicorn.UcError as e:
        pc = uc.reg_read(UC_ARM_REG_PC)
        if pc != LR_MAGIC:
            raise

    # Read modified state
    out = {
        'calls': calls,
        'sp': uc.reg_read(UC_ARM_REG_SP),
        'r4': uc.reg_read(UC_ARM_REG_R4),
        'r5': uc.reg_read(UC_ARM_REG_R5),
        'r6': uc.reg_read(UC_ARM_REG_R6),
        'flags': struct.unpack('<I', uc.mem_read(MODEL_ADDR, 4))[0] if not fixture.get('null_model') else None,
        'visible_1f6': uc.mem_read(VISUAL_ADDR + 0x1F6, 1)[0] if not fixture.get('null_model') else None,
        'dirty_flag': uc.mem_read(WORK_ADDR + 0x28, 1)[0],
    }
    return out

def run_experiment(out_dir: Path):
    image = CODE_PATH.read_bytes()
    blob_cand, raw_cand, blob_mut, raw_mut = build_candidates(out_dir)

    fixtures = [
        {'name': 'paused_visible', 'menu_pause': 1, 'active': 1, 'flags': 0, 'visible_1f6': 1, 'dirty': 0},
        {'name': 'paused_hidden', 'menu_pause': 1, 'active': 1, 'flags': 2, 'visible_1f6': 0, 'dirty': 0},
        {'name': 'unpaused_active_hidden', 'menu_pause': 0, 'active': 1, 'flags': 2, 'visible_1f6': 0, 'dirty': 1, 'pos': (10.0, 20.0, 30.0), 'yaw': 3.14, 'scale': 500},
        {'name': 'unpaused_active_visible', 'menu_pause': 0, 'active': 1, 'flags': 0, 'visible_1f6': 1, 'dirty': 1, 'pos': (100.0, 200.0, 300.0), 'yaw': 0.785, 'scale': 1200},
        {'name': 'unpaused_inactive_visible', 'menu_pause': 0, 'active': 0, 'flags': 0, 'visible_1f6': 1, 'dirty': 0},
        {'name': 'unpaused_inactive_hidden', 'menu_pause': 0, 'active': 0, 'flags': 2, 'visible_1f6': 0, 'dirty': 0},
        {'name': 'unpaused_inactive_dirty', 'menu_pause': 0, 'active': 0, 'flags': 0, 'visible_1f6': 1, 'dirty': 1, 'pos': (5.0, 6.0, 7.0), 'yaw': 1.0, 'scale': 800},
        {'name': 'null_model', 'null_model': True},
    ]

    results = []
    diff_count = 0

    for fix in fixtures:
        orig_out = run_simulation(image, blob_cand, ORIG_ADDR, False, fix)
        cand_out = run_simulation(image, blob_cand, CAND_ADDR, True, fix)

        diffs = []
        for k in ['calls', 'sp', 'r4', 'r5', 'r6', 'flags', 'visible_1f6', 'dirty_flag']:
            if orig_out[k] != cand_out[k]:
                diffs.append(f'{k}: orig={orig_out[k]} vs cand={cand_out[k]}')

        if diffs:
            diff_count += 1
            results.append({'fixture': fix['name'], 'status': 'fail', 'diffs': diffs})
        else:
            results.append({'fixture': fix['name'], 'status': 'pass', 'diffs': [], 'calls': len(cand_out['calls'])})

    # Mutation check: run with blob_mut on unpaused_active_hidden fixture
    orig_fix = fixtures[2] # unpaused_active_hidden
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
    parser.add_argument('--out-dir', type=Path, default=ROOT / 'build/agent-work/H4-semantic/h4-player-transform-candidate/run-001')
    args = parser.parse_args()
    report = run_experiment(args.out_dir)
    if report['status'] != 'passed':
        sys.exit(1)

if __name__ == '__main__':
    main()
