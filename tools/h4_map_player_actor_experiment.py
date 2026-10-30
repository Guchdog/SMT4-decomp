"""Offline ARM differential validation for 0x001B45C8 (Map_GetPlayerActor)."""
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
SRC = ROOT / 'experiments/semantic_equivalence/h4_map_player_actor_candidate.cpp'

ORIG_FUNC = 0x1B45C8
ORIG_SIZE = 24
CAND = 0x1000000
STOP = 0x1008000
MOCK_LOOKUP = 0x1009000
STACK = 0x8000000
SP = STACK + 0x2000

MAP_WORK = 0x2010000

REGS = [a.UC_ARM_REG_R4, a.UC_ARM_REG_R5, a.UC_ARM_REG_R6, a.UC_ARM_REG_R7,
        a.UC_ARM_REG_R8, a.UC_ARM_REG_R9, a.UC_ARM_REG_R10, a.UC_ARM_REG_R11]

def sha(b):
    return hashlib.sha256(b).hexdigest()

def branch_word(site, target, is_bl=False):
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
    raw_cand, rels_cand = funcs['h4_map_player_actor_candidate']
    raw_mut, rels_mut = funcs['h4_map_player_actor_mutation']

    if len(raw_cand) > ORIG_SIZE:
        raise ValueError(f'Candidate size {len(raw_cand)} exceeds original {ORIG_SIZE}')

    def resolve_relocs(raw, rels):
        blob = bytearray(raw)
        for r in rels:
            w = branch_word(CAND + r.offset, MOCK_LOOKUP, is_bl=False)
            struct.pack_into('<I', blob, r.offset, w)
        return bytes(blob)

    blob_cand = resolve_relocs(raw_cand, rels_cand)
    blob_mut = resolve_relocs(raw_mut, rels_mut)
    return blob_cand, raw_cand, blob_mut, raw_mut

def run_simulation(image, cand_blob, entry, is_cand, player_handle):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(a.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x100000, 0x480000, 7)
    uc.mem_write(0x100000, image)

    uc.mem_map(CAND, 0x8000, 7)
    uc.mem_write(CAND, cand_blob)

    uc.mem_map(STOP, 0x1000, 7)
    uc.mem_map(MOCK_LOOKUP, 0x1000, 7)
    uc.mem_map(0x2000000, 0x20000, 3)
    uc.mem_map(STACK, 0x4000, 3)

    # In MOCK_LOOKUP: return actor pointer based on handle; returns via bx lr
    # Simulated mock code: add r0, r0, #0x08000000; bx lr
    # 0xe2800408 (add r0, r0, #0x08000000), 0xe12fff1e (bx lr)
    mock_code = struct.pack('<II', 0xe2800408, 0xe12fff1e)
    uc.mem_write(MOCK_LOOKUP, mock_code)

    if not is_cand:
        # Patch original tail-call branch at 0x001B45D8 to jump to MOCK_LOOKUP
        uc.mem_write(0x1B45D8, struct.pack('<I', branch_word(0x1B45D8, MOCK_LOOKUP, is_bl=False)))

    # Set up global pointer *0x00447E28 = MAP_WORK
    uc.mem_write(0x447E28, struct.pack('<I', MAP_WORK))

    # Set up MAP_WORK->player_actor_handle (offset +0x00)
    uc.mem_write(MAP_WORK, struct.pack('<I', player_handle))

    call_log = []

    def hook_lookup(uc, address, size, user_data):
        r0 = uc.reg_read(a.UC_ARM_REG_R0)
        r1 = uc.reg_read(a.UC_ARM_REG_R1)
        call_log.append((r0, r1))

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_lookup, None, MOCK_LOOKUP, MOCK_LOOKUP + 4)

    for i, r in enumerate(REGS):
        uc.reg_write(r, 0x55660000 + i * 0x101)

    uc.reg_write(a.UC_ARM_REG_SP, SP)
    uc.reg_write(a.UC_ARM_REG_LR, STOP)

    try:
        uc.emu_start(entry, STOP, timeout=2000000, count=50)
    except unicorn.UcError as e:
        return {'fault': str(e), 'calls': call_log}

    r0_ret = uc.reg_read(a.UC_ARM_REG_R0)
    reg_vals = [uc.reg_read(r) for r in REGS]
    sp_val = uc.reg_read(a.UC_ARM_REG_SP)

    return {
        'fault': None,
        'r0': r0_ret,
        'regs': reg_vals,
        'sp': sp_val,
        'calls': call_log
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out-dir', type=Path, default=ROOT / 'build/agent-work/H4-semantic/h4-map-player-actor-candidate/001/output')
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    code_bytes = CODE.read_bytes()
    obj_path = args.out_dir / 'h4_map_player_actor_candidate.o'
    cand_blob, cand_raw, mut_blob, mut_raw = build_candidate(SRC, obj_path)

    test_fixtures = [
        {'id': 'handle_zero', 'handle': 0},
        {'id': 'handle_sample1', 'handle': 0x00100001},
        {'id': 'handle_sample2', 'handle': 0x00200045},
        {'id': 'handle_max', 'handle': 0xFFFFFFFF},
        {'id': 'handle_rand1', 'handle': random.randint(1, 0xFFFFFFFE)},
        {'id': 'handle_rand2', 'handle': random.randint(1, 0xFFFFFFFE)},
    ]

    all_passed = True
    results = []

    for fix in test_fixtures:
        orig = run_simulation(code_bytes, cand_blob, ORIG_FUNC, False, fix['handle'])
        cand = run_simulation(code_bytes, cand_blob, CAND, True, fix['handle'])

        diffs = []
        if orig['fault'] != cand['fault']:
            diffs.append(f"fault: orig={orig['fault']} vs cand={cand['fault']}")
        if orig['r0'] != cand['r0']:
            diffs.append(f"return r0 mismatch: {orig['r0']} vs {cand['r0']}")
        if orig['regs'] != cand['regs']:
            diffs.append("register mismatch in r4-r11")
        if orig['sp'] != cand['sp']:
            diffs.append(f"sp mismatch: {orig['sp']} vs {cand['sp']}")
        if orig['calls'] != cand['calls']:
            diffs.append(f"call trace mismatch: {orig['calls']} vs {cand['calls']}")

        status = 'pass' if not diffs else 'fail'
        if diffs:
            all_passed = False
        results.append({'fixture': fix['id'], 'status': status, 'diffs': diffs, 'calls': len(orig['calls'])})

    # Mutation negative control
    mut = run_simulation(code_bytes, mut_blob, CAND, True, 0x00100001)
    orig_ref = run_simulation(code_bytes, cand_blob, ORIG_FUNC, False, 0x00100001)
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
