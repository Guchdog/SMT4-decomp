#!/usr/bin/env python3
"""Differential test for func_00250108 (0x00250108) using Unicorn ARM emulation."""

import struct
import sys
from pathlib import Path
import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
FUNC_ADDR = 0x00250108
FUNC_SIZE = 480

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
MATRIX_ADDR = 0x00600000
VECTOR_ADDR = 0x00601000
TRAP_ADDR = 0x90000000

def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)

def compile_candidate():
    out_dir = ROOT / "build/test_leaf_00250108"
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_file = out_dir / "leaf_batch45_a.o"
    src_file = ROOT / "src/engine/leaf_batch45_a.cpp"
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    for k in funcs:
        if "func_00250108" in k or "00250108" in k:
            return funcs[k][0], funcs[k][1]
    raise KeyError("func_00250108 not found in compiled object")

def run_unicorn(code_bytes, initial_matrix, scale_vector, mode):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    val = uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, val | (0xF << 20))
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00250000, 0x10000)
    uc.mem_map(STACK_ADDR, STACK_SIZE)
    uc.mem_map(0x00600000, 0x10000) # Covers MATRIX_ADDR and VECTOR_ADDR
    uc.mem_map(TRAP_ADDR, 0x1000)

    uc.mem_write(FUNC_ADDR, code_bytes)

    # Write matrix (16 floats = 64 bytes)
    mat_bytes = struct.pack("<16f", *initial_matrix)
    uc.mem_write(MATRIX_ADDR, mat_bytes)

    # Write vector (3 floats = 12 bytes)
    vec_bytes = struct.pack("<3f", *scale_vector)
    uc.mem_write(VECTOR_ADDR, vec_bytes)

    uc.reg_write(arm.UC_ARM_REG_R0, MATRIX_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, VECTOR_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R2, mode)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_ADDR + 0x8000)
    uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)

    uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
    return struct.unpack("<16f", uc.mem_read(MATRIX_ADDR, 64))

def main():
    orig_code = get_orig_bytes()
    cand_code, relocs = compile_candidate()
    print(f"Original size: {len(orig_code)} B, Candidate size: {len(cand_code)} B, Relocs: {len(relocs)}")

    mat_identity = [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0
    ]

    mat_arbitrary = [
        1.0,  2.0,  3.0,  4.0,
        5.0,  6.0,  7.0,  8.0,
        9.0, 10.0, 11.0, 12.0,
       13.0, 14.0, 15.0, 16.0
    ]

    # Test cases: (name, initial_mat, vec, mode)
    test_cases = [
        # Mode 0: MakeScale
        ("Mode 0: scale (1,1,1) on zero mat", [0.0]*16, (1.0, 1.0, 1.0), 0),
        ("Mode 0: scale (2,3,4) on arbitrary mat", mat_arbitrary, (2.0, 3.0, 4.0), 0),
        ("Mode 0: scale (-1.5, 0.5, 10.0) on arbitrary mat", mat_arbitrary, (-1.5, 0.5, 10.0), 0),
        ("Mode 0: scale (0, 5, 0)", mat_arbitrary, (0.0, 5.0, 0.0), 0),

        # Mode 1: ScaleRows (Pre-multiply by scale)
        ("Mode 1: identity * scale (2,3,4)", mat_identity, (2.0, 3.0, 4.0), 1),
        ("Mode 1: arbitrary * scale (2,3,4)", mat_arbitrary, (2.0, 3.0, 4.0), 1),
        ("Mode 1: arbitrary * scale (-1, 0.5, 2)", mat_arbitrary, (-1.0, 0.5, 2.0), 1),
        ("Mode 1: arbitrary * scale (0, 0, 0)", mat_arbitrary, (0.0, 0.0, 0.0), 1),

        # Mode 2: ScaleColumns (Post-multiply by scale)
        ("Mode 2: identity * scale (2,3,4)", mat_identity, (2.0, 3.0, 4.0), 2),
        ("Mode 2: arbitrary * scale (2,3,4)", mat_arbitrary, (2.0, 3.0, 4.0), 2),
        ("Mode 2: arbitrary * scale (-1, 0.5, 2)", mat_arbitrary, (-1.0, 0.5, 2.0), 2),
        ("Mode 2: arbitrary * scale (0, 0, 0)", mat_arbitrary, (0.0, 0.0, 0.0), 2),

        # Invalid modes: No-op
        ("Mode 3 (out of range)", mat_arbitrary, (2.0, 3.0, 4.0), 3),
        ("Mode 4 (out of range)", mat_arbitrary, (2.0, 3.0, 4.0), 4),
        ("Mode 100 (out of range)", mat_arbitrary, (2.0, 3.0, 4.0), 100),
    ]

    all_passed = True
    for i, (name, init_m, vec, mode) in enumerate(test_cases):
        res_orig = run_unicorn(orig_code, init_m, vec, mode)
        res_cand = run_unicorn(cand_code, init_m, vec, mode)

        match = all(abs(o - c) < 1e-6 for o, c in zip(res_orig, res_cand))
        if match:
            print(f"Case {i+1:2d} ({name}): PASS")
        else:
            print(f"Case {i+1:2d} ({name}): FAIL!")
            print(f"  Orig: {res_orig}")
            print(f"  Cand: {res_cand}")
            all_passed = False

    if all_passed:
        print("\nALL TEST CASES PASSED!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
