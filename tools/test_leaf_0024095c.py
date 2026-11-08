#!/usr/bin/env python3
"""Differential test for func_0024095c (0x0024095c) using Unicorn ARM emulation."""

import math
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
FUNC_ADDR = 0x0024095c
FUNC_SIZE = 128

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
OBJ_ADDR = 0x00500000
OBJ_SIZE = 0x1000

def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)

def compile_candidate():
    out_dir = ROOT / "build/test_leaf_0024095c"
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_file = out_dir / "leaf_batch30_c.o"
    src_file = ROOT / "src/engine/leaf_batch30_c.cpp"
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    for k in funcs:
        if "func_0024095c" in k:
            return funcs[k]
    raise KeyError("func_0024095c not found in compiled object")

def run_unicorn(code_bytes, obj_data, param_1):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    # Enable VFP
    val = uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, val | (0xF << 20))
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

    # Map memory
    code_base = 0x00240000
    uc.mem_map(code_base, 0x10000)
    uc.mem_map(STACK_ADDR, STACK_SIZE)
    uc.mem_map(OBJ_ADDR, OBJ_SIZE)

    # Write code
    uc.mem_write(FUNC_ADDR, code_bytes)
    # Return trap at 0x90000000
    TRAP_ADDR = 0x90000000
    uc.mem_map(TRAP_ADDR, 0x1000)
    uc.mem_write(TRAP_ADDR, b"\x00\x00\x00\x00")

    # Write object data
    uc.mem_write(OBJ_ADDR, obj_data)

    # Registers
    uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, param_1)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_ADDR + 0x8000)
    uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)

    uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
    return uc.mem_read(OBJ_ADDR, len(obj_data))

def make_obj(p1, p2, flags_634, f_728=0, f_72c=0):
    buf = bytearray(OBJ_SIZE)
    # p1 at 0x0C (3 floats)
    struct.pack_into("<3f", buf, 0x0C, *p1)
    # p2 at 0x18 (3 floats)
    struct.pack_into("<3f", buf, 0x18, *p2)
    # flags at 0x634
    struct.pack_into("<I", buf, 0x634, flags_634)
    # 0x728 and 0x72C
    struct.pack_into("<I", buf, 0x728, f_728)
    struct.pack_into("<I", buf, 0x72C, f_72c)
    return bytes(buf)

def main():
    orig_code = get_orig_bytes()
    cand_code, relocs = compile_candidate()
    print(f"Original size: {len(orig_code)} B, Candidate size: {len(cand_code)} B, Relocs: {len(relocs)}")

    # Test cases: (p1, p2, flags_634, param_1)
    test_cases = [
        # 1. Identical points (distance = 0.0) -> flag cleared
        ((1.0, 2.0, 3.0), (1.0, 2.0, 3.0), 0x00000000, 0x12345678),
        # 2. Identical points with flag already set
        ((10.0, 20.0, 30.0), (10.0, 20.0, 30.0), 0x80000, 0xABCDEF01),
        # 3. Very close points (distance = 0.005) -> flag cleared
        ((0.0, 0.0, 0.0), (0.005, 0.0, 0.0), 0x10000000, 0x11112222),
        # 4. Boundary points (distance = 0.01) -> flag cleared
        ((0.0, 0.0, 0.0), (0.01, 0.0, 0.0), 0x0, 0x33334444),
        # 5. Slightly above boundary (distance = 0.0101) -> flag preserved
        ((0.0, 0.0, 0.0), (0.0101, 0.0, 0.0), 0x0, 0x55556666),
        # 6. Slightly above boundary with initial flag set
        ((0.0, 0.0, 0.0), (0.0101, 0.0, 0.0), 0x80000, 0x55556666),
        # 7. Far distance
        ((100.0, 200.0, 300.0), (0.0, 0.0, 0.0), 0x1234, 0x9999),
        # 8. Negative coordinates, close
        ((-50.0, -100.0, -200.0), (-50.002, -100.002, -200.002), 0x0, 0xCAFE),
        # 9. Negative coordinates, far
        ((-50.0, -100.0, -200.0), (50.0, 100.0, 200.0), 0x55, 0xBEEF),
        # 10. Diagonal distance boundary: dx=0.00577, dy=0.00577, dz=0.00577 (~0.00999) -> flag cleared
        ((0.0, 0.0, 0.0), (0.00577, 0.00577, 0.00577), 0x0, 0x7777),
    ]

    all_passed = True
    for i, (p1, p2, flags_init, param_1) in enumerate(test_cases):
        obj_init = make_obj(p1, p2, flags_init)
        res_orig = run_unicorn(orig_code, obj_init, param_1)
        res_cand = run_unicorn(cand_code, obj_init, param_1)

        # Check fields 0x634, 0x728, 0x72C
        flags_orig = struct.unpack_from("<I", res_orig, 0x634)[0]
        flags_cand = struct.unpack_from("<I", res_cand, 0x634)[0]
        f728_orig = struct.unpack_from("<I", res_orig, 0x728)[0]
        f728_cand = struct.unpack_from("<I", res_cand, 0x728)[0]
        f72c_orig = struct.unpack_from("<I", res_orig, 0x72C)[0]
        f72c_cand = struct.unpack_from("<I", res_cand, 0x72C)[0]

        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        dz = p1[2] - p2[2]
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)

        match = (flags_orig == flags_cand) and (f728_orig == f728_cand) and (f72c_orig == f72c_cand)
        if match:
            print(f"Case {i+1:2d} (dist={dist:8.5f}): PASS [flags=0x{flags_cand:08X}, 0x728=0x{f728_cand:X}, 0x72C=0x{f72c_cand:X}]")
        else:
            print(f"Case {i+1:2d} (dist={dist:8.5f}): FAIL!")
            print(f"  Orig: flags=0x{flags_orig:08X}, 0x728=0x{f728_orig:X}, 0x72C=0x{f72c_orig:X}")
            print(f"  Cand: flags=0x{flags_cand:08X}, 0x728=0x{f728_cand:X}, 0x72C=0x{f72c_cand:X}")
            all_passed = False

    if all_passed:
        print("\nALL TEST CASES PASSED!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
