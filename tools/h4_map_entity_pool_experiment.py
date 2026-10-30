"""Offline ARM differential validation for 0x001B45E0 (Map_ClearEntityPool)."""
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
SRC = ROOT / 'experiments/semantic_equivalence/h4_map_entity_pool_candidate.cpp'

ORIG_FUNC = 0x1B45E0
ORIG_SIZE = 132
CAND = 0x1000000
STOP = 0x1008000
MOCK_RELEASE = 0x1009000
STACK = 0x8000000
SP = STACK + 0x2000

POOL_MEM = 0x2010000
ENTITY_STRIDE = 72
ENTITY_COUNT = 24
POOL_SIZE = ENTITY_STRIDE * ENTITY_COUNT

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
    raw_cand, rels_cand = funcs['h4_map_entity_pool_candidate']
    raw_mut, rels_mut = funcs['h4_map_entity_pool_mutation']

    if len(raw_cand) > ORIG_SIZE:
        raise ValueError(f'Candidate size {len(raw_cand)} exceeds original {ORIG_SIZE}')

    def resolve_relocs(raw, rels):
        blob = bytearray(raw)
        for r in rels:
            w = branch_word(CAND + r.offset, MOCK_RELEASE, is_bl=True)
            struct.pack_into('<I', blob, r.offset, w)
        return bytes(blob)

    blob_cand = resolve_relocs(raw_cand, rels_cand)
    blob_mut = resolve_relocs(raw_mut, rels_mut)
    return blob_cand, raw_cand, blob_mut, raw_mut

def run_simulation(image, cand_blob, entry, is_cand, entity_resources, entity_states):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(a.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x100000, 0x480000, 7)
    uc.mem_write(0x100000, image)

    uc.mem_map(CAND, 0x8000, 7)
    uc.mem_write(CAND, cand_blob)

    uc.mem_map(STOP, 0x1000, 7)
    uc.mem_map(MOCK_RELEASE, 0x1000, 7)
    uc.mem_map(0x2000000, 0x20000, 3)
    uc.mem_map(STACK, 0x4000, 3)

    # Return instruction for MOCK_RELEASE: bx lr
    uc.mem_write(MOCK_RELEASE, struct.pack('<I', 0xe12fff1e))

    if not is_cand:
        # Patch original call to 0x002A7AA0 at 0x001B4608
        uc.mem_write(0x1B4608, struct.pack('<I', branch_word(0x1B4608, MOCK_RELEASE, is_bl=True)))

    # Set up global pointer *0x00447E70 = POOL_MEM
    uc.mem_write(0x447E70, struct.pack('<I', POOL_MEM))

    # Initialize entity pool memory
    pool_buf = bytearray(POOL_SIZE)
    for i in range(ENTITY_COUNT):
        offset = i * ENTITY_STRIDE
        pool_buf[offset + 0x14] = entity_states[i] & 0xFF
        struct.pack_into('<I', pool_buf, offset + 0x3C, entity_resources[i])
    uc.mem_write(POOL_MEM, bytes(pool_buf))

    released_list = []

    def hook_release(uc, address, size, user_data):
        r0 = uc.reg_read(a.UC_ARM_REG_R0)
        released_list.append(r0)

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_release, None, MOCK_RELEASE, MOCK_RELEASE + 4)

    for i, r in enumerate(REGS):
        uc.reg_write(r, 0x66770000 + i * 0x101)

    uc.reg_write(a.UC_ARM_REG_SP, SP)
    uc.reg_write(a.UC_ARM_REG_LR, STOP)

    try:
        uc.emu_start(entry, STOP, timeout=5000000, count=5000)
    except unicorn.UcError as e:
        return {'fault': str(e), 'released': released_list}

    reg_vals = [uc.reg_read(r) for r in REGS]
    sp_val = uc.reg_read(a.UC_ARM_REG_SP)
    pool_after = uc.mem_read(POOL_MEM, POOL_SIZE)

    return {
        'fault': None,
        'regs': reg_vals,
        'sp': sp_val,
        'released': released_list,
        'pool_sha': sha(pool_after)
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out-dir', type=Path, default=ROOT / 'build/agent-work/H4-semantic/h4-map-entity-pool-candidate/001/output')
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    code_bytes = CODE.read_bytes()
    obj_path = args.out_dir / 'h4_map_entity_pool_candidate.o'
    cand_blob, cand_raw, mut_blob, mut_raw = build_candidate(SRC, obj_path)

    test_fixtures = [
        {
            'id': 'all_resources_active',
            'resources': [0x08100000 + i * 0x100 for i in range(24)],
            'states': [0xAA] * 24
        },
        {
            'id': 'alternating_resources',
            'resources': [(0x08200000 + i * 0x100) if (i % 2 == 0) else 0 for i in range(24)],
            'states': [0x55] * 24
        },
        {
            'id': 'no_resources',
            'resources': [0] * 24,
            'states': [0xFF] * 24
        },
        {
            'id': 'random_sparse',
            'resources': [random.choice([0, random.randint(0x1000, 0xFFFFFFFF)]) for _ in range(24)],
            'states': [random.randint(0, 0xFF) for _ in range(24)]
        },
        {
            'id': 'only_last_entry',
            'resources': [0] * 23 + [0x08999999],
            'states': [0] * 23 + [0x42]
        }
    ]

    all_passed = True
    results = []

    for fix in test_fixtures:
        orig = run_simulation(code_bytes, cand_blob, ORIG_FUNC, False, fix['resources'], fix['states'])
        cand = run_simulation(code_bytes, cand_blob, CAND, True, fix['resources'], fix['states'])

        diffs = []
        if orig['fault'] != cand['fault']:
            diffs.append(f"fault: orig={orig['fault']} vs cand={cand['fault']}")
        if orig['regs'] != cand['regs']:
            diffs.append("register mismatch in r4-r11")
        if orig['sp'] != cand['sp']:
            diffs.append(f"sp mismatch: {orig['sp']} vs {cand['sp']}")
        if orig['released'] != cand['released']:
            diffs.append(f"released mismatch: {orig['released']} vs {cand['released']}")
        if orig['pool_sha'] != cand['pool_sha']:
            diffs.append("memory mismatch in entity pool")

        status = 'pass' if not diffs else 'fail'
        if diffs:
            all_passed = False
        results.append({'fixture': fix['id'], 'status': status, 'diffs': diffs, 'released_count': len(orig['released'])})

    # Mutation negative control
    mut = run_simulation(code_bytes, mut_blob, CAND, True, test_fixtures[0]['resources'], test_fixtures[0]['states'])
    orig_ref = run_simulation(code_bytes, cand_blob, ORIG_FUNC, False, test_fixtures[0]['resources'], test_fixtures[0]['states'])
    mutation_detected = (mut['pool_sha'] != orig_ref['pool_sha'] or mut['released'] != orig_ref['released'])

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
