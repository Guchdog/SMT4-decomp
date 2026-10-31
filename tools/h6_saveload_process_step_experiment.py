#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002EF9AC SaveLoadProcess_Step."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h6_saveload_process_step_candidate.cpp'
ORIG_ADDR = 0x002EF9AC
ORIG_SIZE = 420
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'SaveLoadProcess_GetWork_002c0ac8': 0x002C0AC8,
    'AsdMem_Alloc_002c54f0': 0x002C54F0,
    'SaveLoad_DispatchWorker_00247c64': 0x00247C64,
    'Worker_IsComplete_001a1bf8': 0x001A1BF8,
    'Worker_GetError_002ced0c': 0x002CED0C,
    'SaveHelper_0026b844': 0x0026B844,
    'SaveHelper_0026b830': 0x0026B830,
    'SaveHelper_0026b734': 0x0026B734,
    'Metadata_Copy_002bcf58': 0x002BCF58,
    'Data_Deserialize_002adb40': 0x002ADB40,
    'GetContext_002c0b94': 0x002C0B94,
    'g_SaveLoadContext_0043e2f0': 0x0043E2F0,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h6_saveload_process_step.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h6_saveload_process_step_candidate']
    raw_mut, _ = funcs['h6_saveload_process_step_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name == '':
            in_place = struct.unpack_from('<I', blob_cand, r.offset)[0]
            tgt = CAND_ADDR + in_place
        else:
            tgt = TARGET_SYMBOLS.get(r.symbol_name, 0)
        reloc_vma = CAND_ADDR + r.offset
        if r.relocation_type == 2:
            struct.pack_into('<I', blob_cand, r.offset, tgt)
        elif r.relocation_type in (28, 29):
            w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
            struct.pack_into('<I', blob_cand, r.offset, w)

    return bytes(blob_cand), raw_cand, raw_mut, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, initial_state: int, worker_done: int, worker_err: int) -> tuple[int, int, bytes]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, cand_blob + b'\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    HEAP_BASE = 0x08000000
    uc.mem_map(HEAP_BASE, 0x100000, unicorn.UC_PROT_ALL)

    WORK_BUF = HEAP_BASE + 0x2000
    DATA_BUF = HEAP_BASE + 0x4000
    CTX_BUF = HEAP_BASE + 0x6000
    uc.mem_write(DATA_BUF, b'\x00' * 0x30000)
    uc.mem_write(CTX_BUF, b'\x00' * 0x100)

    # Setup work structure
    # task (+0), state (+4), buffer (+8), file_size (+0xC), slot (+0x10)
    uc.mem_write(WORK_BUF, struct.pack('<IIIII', 0, initial_state, DATA_BUF, 0x24DB0, 1))

    # Mock helpers
    # SaveLoadProcess_GetWork_002c0ac8: return WORK_BUF
    uc.mem_write(0x002C0AC8, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', WORK_BUF))
    # AsdMem_Alloc: return DATA_BUF
    uc.mem_write(0x002C54F0, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', DATA_BUF))
    # SaveLoad_DispatchWorker_00247c64: return 0
    uc.mem_write(0x00247C64, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    # Worker_IsComplete_001a1bf8: return worker_done
    uc.mem_write(0x001A1BF8, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', worker_done))
    # Worker_GetError_002ced0c: return worker_err
    uc.mem_write(0x002CED0C, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', worker_err))
    # SaveHelper_0026b844, 0026b830, 0026b734
    uc.mem_write(0x0026B844, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x0026B830, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x0026B734, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    # Metadata_Copy_002bcf58
    uc.mem_write(0x002BCF58, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    # Data_Deserialize_002adb40
    uc.mem_write(0x002ADB40, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    # GetContext_002c0b94: return CTX_BUF
    uc.mem_write(0x002C0B94, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', CTX_BUF))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=2000000, count=5000)
    ret_r0 = uc.reg_read(UC_ARM_REG_R0)
    post_state = struct.unpack('<I', uc.mem_read(WORK_BUF + 4, 4))[0]
    ctx_out = uc.mem_read(0x0043E2F0, 0x10)
    return ret_r0, post_state, ctx_out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'build/h6_saveload_process_step_test.json')
    args = parser.parse_args()

    with open(CODE_PATH, 'rb') as f:
        code_bytes = f.read()

    out_dir = ROOT / 'build/h6_candidates'
    blob_cand, raw_cand, blob_mut, raw_mut = build_candidates(out_dir)

    test_cases = [
        (4, 0, 0),  # state 4 -> state 5 (worker dispatch)
        (5, 0, 0),  # state 5 (worker not done) -> state 5
        (5, 1, 0),  # state 5 (worker done, no error) -> state 6
        (5, 1, 1),  # state 5 (worker done, error) -> state 7
        (6, 0, 0),  # state 6 (success terminal)
        (7, 0, 0),  # state 7 (error terminal)
    ]

    results = []
    all_matched = True

    for s, wd, we in test_cases:
        r0_orig, st_orig, c_orig = run_simulation(code_bytes, blob_cand, ORIG_ADDR, s, wd, we)
        r0_cand, st_cand, c_cand = run_simulation(code_bytes, blob_cand, CAND_ADDR, s, wd, we)
        matched = (r0_orig == r0_cand) and (st_orig == st_cand) and (c_orig == c_cand)
        results.append({
            'init_state': s, 'worker_done': wd, 'worker_err': we,
            'r0_orig': r0_orig, 'r0_cand': r0_cand,
            'st_orig': st_orig, 'st_cand': st_cand,
            'matched': matched
        })
        if not matched: all_matched = False

    # Mutation test (returns 0x55)
    r0_mut, _, _ = run_simulation(code_bytes, blob_mut, CAND_ADDR, 4, 0, 0)
    mutation_detected = (r0_mut == 0x55)

    report = {
        'candidate': 'SaveLoadProcess_Step',
        'orig_size': ORIG_SIZE,
        'cand_size': len(raw_cand),
        'fits': len(raw_cand) <= ORIG_SIZE,
        'all_matched': all_matched,
        'mutation_detected': mutation_detected,
        'status': 'passed' if (all_matched and mutation_detected) else 'failed',
        'cases': results
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'H6 SaveLoadProcess_Step: status={report["status"]}, matched={all_matched}, mut_detected={mutation_detected}')
    assert report['status'] == 'passed'

if __name__ == '__main__':
    main()
