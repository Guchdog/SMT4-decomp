"""Offline ARM differential validation for 0x001B481C (ViewCameraWork subobject setup)."""
import argparse
import hashlib
import json
import random
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed
import unicorn
from unicorn import arm_const as a

CODE = ROOT / 'extracted/exefs/code.bin'
SRC = ROOT / 'experiments/semantic_equivalence/h4_view_subobjects_candidate.cpp'

ORIG_FUNC = 0x1B481C
ORIG_SIZE = 164
CAND = 0x1000000
STOP = 0x1008000
MOCK_LOAD_PLAYER = 0x1009000
MOCK_SET_ACTIVE  = 0x100A000
MOCK_SET_DEFAULT = 0x100B000
STACK = 0x8000000
SP = STACK + 0x2000

VIEW_WORK = 0x2010000
VIEW_SIZE = 0x1C0
SUBOBJ = 0x2020000

REGS = [a.UC_ARM_REG_R4, a.UC_ARM_REG_R5, a.UC_ARM_REG_R6, a.UC_ARM_REG_R7,
        a.UC_ARM_REG_R8, a.UC_ARM_REG_R9, a.UC_ARM_REG_R10, a.UC_ARM_REG_R11]

def sha(b):
    return hashlib.sha256(b).hexdigest()

def branch_word(site, target, is_bl=True):
    delta = target - (site + 8)
    if (site | target | delta) & 3 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError('unsafe ARM branch')
    opcode = 0xeb000000 if is_bl else 0xea000000
    return opcode | ((delta >> 2) & 0xffffff)

def build_candidate(src_path, obj_path):
    result = compile_tu_armv6k(src_path, obj_path, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, rels_cand = funcs['h4_view_subobjects_candidate']
    raw_mut, rels_mut = funcs['h4_view_subobjects_mutation']

    if len(raw_cand) > ORIG_SIZE:
        raise ValueError(f'Candidate size {len(raw_cand)} exceeds original {ORIG_SIZE}')

    def resolve_relocs(raw, rels):
        blob = bytearray(raw)
        for r in rels:
            if 'load_player' in r.symbol_name:
                tgt = MOCK_LOAD_PLAYER
            elif 'active' in r.symbol_name:
                tgt = MOCK_SET_ACTIVE
            elif 'default' in r.symbol_name:
                tgt = MOCK_SET_DEFAULT
            else:
                raise ValueError(f'Unknown relocation symbol {r.symbol_name}')
            is_bl = (r.relocation_type == 28)
            w = branch_word(CAND + r.offset, tgt, is_bl=is_bl)
            struct.pack_into('<I', blob, r.offset, w)
        return bytes(blob)

    blob_cand = resolve_relocs(raw_cand, rels_cand)
    blob_mut = resolve_relocs(raw_mut, rels_mut)
    return blob_cand, raw_cand, blob_mut, raw_mut

def run_simulation(image, cand_blob, entry, is_cand, field_198, sub_channels):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(a.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x100000, 0x480000, 7)
    uc.mem_write(0x100000, image)

    uc.mem_map(CAND, 0x8000, 7)
    uc.mem_write(CAND, cand_blob)

    uc.mem_map(STOP, 0x1000, 7)
    uc.mem_map(MOCK_LOAD_PLAYER, 0x1000, 7)
    uc.mem_map(MOCK_SET_ACTIVE, 0x1000, 7)
    uc.mem_map(MOCK_SET_DEFAULT, 0x1000, 7)
    uc.mem_map(0x2000000, 0x30000, 3)
    uc.mem_map(STACK, 0x4000, 3)

    # Return instruction for mocks: bx lr (0xe12fff1e)
    ret_code = struct.pack('<I', 0xe12fff1e)
    uc.mem_write(MOCK_LOAD_PLAYER, ret_code)
    uc.mem_write(MOCK_SET_ACTIVE, ret_code)
    uc.mem_write(MOCK_SET_DEFAULT, ret_code)

    if not is_cand:
        # Patch original call sites to point to mock routines
        uc.mem_write(0x1B4830, struct.pack('<I', branch_word(0x1B4830, MOCK_LOAD_PLAYER, is_bl=True)))
        uc.mem_write(0x1B4874, struct.pack('<I', branch_word(0x1B4874, MOCK_SET_ACTIVE, is_bl=True)))
        uc.mem_write(0x1B48A8, struct.pack('<I', branch_word(0x1B48A8, MOCK_SET_DEFAULT, is_bl=True)))

    # Set up global pointer *0x00447E88 = VIEW_WORK
    uc.mem_write(0x447E88, struct.pack('<I', VIEW_WORK))

    # Initialize VIEW_WORK
    work_bytes = bytearray(0x5A for _ in range(VIEW_SIZE))
    struct.pack_into('<I', work_bytes, 0x194, SUBOBJ)
    work_bytes[0x198] = field_198 & 0xFF
    for i in range(min(6, len(sub_channels))):
        struct.pack_into('<I', work_bytes, 0x19C + i * 4, sub_channels[i])
    uc.mem_write(VIEW_WORK, bytes(work_bytes))

    # Call recording trace
    call_log = []

    def hook_mock(uc, address, size, user_data):
        r0 = uc.reg_read(a.UC_ARM_REG_R0)
        r1 = uc.reg_read(a.UC_ARM_REG_R1)
        r2 = uc.reg_read(a.UC_ARM_REG_R2)
        r3 = uc.reg_read(a.UC_ARM_REG_R3)
        if address == MOCK_LOAD_PLAYER:
            call_log.append(('LOAD_PLAYER', r0, r1))
        elif address == MOCK_SET_ACTIVE:
            call_log.append(('SET_ACTIVE', r0, r1, r2, r3))
        elif address == MOCK_SET_DEFAULT:
            call_log.append(('SET_DEFAULT', r0, r1, r2))

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_mock, None, MOCK_LOAD_PLAYER, MOCK_LOAD_PLAYER + 4)
    uc.hook_add(unicorn.UC_HOOK_CODE, hook_mock, None, MOCK_SET_ACTIVE, MOCK_SET_ACTIVE + 4)
    uc.hook_add(unicorn.UC_HOOK_CODE, hook_mock, None, MOCK_SET_DEFAULT, MOCK_SET_DEFAULT + 4)

    # Initialize registers with canary values
    for i, r in enumerate(REGS):
        uc.reg_write(r, 0x11220000 + i * 0x101)

    uc.reg_write(a.UC_ARM_REG_SP, SP)
    uc.reg_write(a.UC_ARM_REG_LR, STOP)

    # Run emulation
    try:
        uc.emu_start(entry, STOP, timeout=5000000, count=500)
    except unicorn.UcError as e:
        return {'fault': str(e), 'calls': call_log}

    reg_vals = [uc.reg_read(r) for r in REGS]
    sp_val = uc.reg_read(a.UC_ARM_REG_SP)
    view_after = uc.mem_read(VIEW_WORK, VIEW_SIZE)

    return {
        'fault': None,
        'regs': reg_vals,
        'sp': sp_val,
        'calls': call_log,
        'view_sha': sha(view_after)
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out-dir', type=Path, default=ROOT / 'build/agent-work/H4-semantic/h4-view-subobjects-candidate/001/output')
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    code_bytes = CODE.read_bytes()
    obj_path = args.out_dir / 'h4_view_subobjects_candidate.o'
    cand_blob, cand_raw, mut_blob, mut_raw = build_candidate(SRC, obj_path)

    test_fixtures = [
        {'id': 'field198_zero', 'field_198': 0, 'sub_channels': [0x1111, 0x2222, 0x3333, 0, 0, 0]},
        {'id': 'field198_one',  'field_198': 1, 'sub_channels': [0xAAAA, 0xBBBB, 0xCCCC, 0, 0, 0]},
        {'id': 'field198_0xff', 'field_198': 0xFF, 'sub_channels': [0x1000, 0x2000, 0x3000, 0, 0, 0]},
        {'id': 'field198_rand1','field_198': 0, 'sub_channels': [random.randint(0, 0xFFFFFFFF) for _ in range(6)]},
        {'id': 'field198_rand2','field_198': 42, 'sub_channels': [random.randint(0, 0xFFFFFFFF) for _ in range(6)]},
        {'id': 'field198_rand3','field_198': 128, 'sub_channels': [random.randint(0, 0xFFFFFFFF) for _ in range(6)]},
    ]

    all_passed = True
    results = []

    for fix in test_fixtures:
        orig = run_simulation(code_bytes, cand_blob, ORIG_FUNC, False, fix['field_198'], fix['sub_channels'])
        cand = run_simulation(code_bytes, cand_blob, CAND, True, fix['field_198'], fix['sub_channels'])

        diffs = []
        if orig['fault'] != cand['fault']:
            diffs.append(f"fault: orig={orig['fault']} vs cand={cand['fault']}")
        if orig['regs'] != cand['regs']:
            diffs.append("register mismatch in r4-r11")
        if orig['sp'] != cand['sp']:
            diffs.append(f"sp mismatch: {orig['sp']} vs {cand['sp']}")
        if orig['calls'] != cand['calls']:
            diffs.append(f"call trace mismatch: {orig['calls']} vs {cand['calls']}")
        if orig['view_sha'] != cand['view_sha']:
            diffs.append("view memory mismatch")

        status = 'pass' if not diffs else 'fail'
        if diffs:
            all_passed = False
        results.append({'fixture': fix['id'], 'status': status, 'diffs': diffs, 'calls': len(orig['calls'])})

    # Mutation negative control
    mut = run_simulation(code_bytes, mut_blob, CAND, True, 1, [0xAAAA, 0xBBBB, 0xCCCC, 0, 0, 0])
    orig_ref = run_simulation(code_bytes, cand_blob, ORIG_FUNC, False, 1, [0xAAAA, 0xBBBB, 0xCCCC, 0, 0, 0])
    mutation_detected = (mut['calls'] != orig_ref['calls'])

    summary = {
        'status': 'passed' if (all_passed and mutation_detected) else 'failed',
        'fixtures_tested': len(test_fixtures),
        'mutation_detected': mutation_detected,
        'candidate_bytes': len(cand_raw),
        'original_bytes': ORIG_SIZE,
        'candidate_sha256': sha(cand_raw),
        'results': results
    }

    report_path = args.out_dir / 'differential_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))
    return 0 if (all_passed and mutation_detected) else 1

if __name__ == '__main__':
    sys.exit(main())
