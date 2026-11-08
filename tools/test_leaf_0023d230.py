#!/usr/bin/env python3
"""Differential test for func_0023d230 (0x0023d230) using Unicorn ARM emulation."""

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
FUNC_ADDR = 0x0023d230
FUNC_SIZE = 132

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000

TAG_ADDR = 0x00490E46
OUT_ADDR = 0x00600000
OUT_SIZE = 64

TRAP_ADDR = 0x90000000

def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)

def compile_candidate():
    out_dir = ROOT / "build/test_leaf_0023d230"
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_file = out_dir / "leaf_batch30_c.o"
    src_file = ROOT / "src/engine/leaf_batch30_c.cpp"
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    for k in funcs:
        if "func_0023d230" in k or "0023d230" in k:
            return funcs[k]
    raise KeyError("func_0023d230 not found in compiled object")

def run_unicorn(code_bytes, packed_val, tag_val):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    # Enable VFP
    val = uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, val | (0xF << 20))
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

    # Map memory
    uc.mem_map(0x00230000, 0x10000)
    uc.mem_map(STACK_ADDR, STACK_SIZE)
    uc.mem_map(0x00490000, 0x10000) # Covers TAG_ADDR
    uc.mem_map(0x00600000, 0x10000) # Covers OUT_ADDR
    uc.mem_map(TRAP_ADDR, 0x1000)

    # Write code
    uc.mem_write(FUNC_ADDR, code_bytes)

    # Set tag byte
    uc.mem_write(TAG_ADDR, bytes([tag_val]))

    # Clear out buffer
    uc.mem_write(OUT_ADDR, b"\x00" * OUT_SIZE)

    # Registers
    uc.reg_write(arm.UC_ARM_REG_R0, OUT_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, packed_val)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_ADDR + 0x8000)
    uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)

    uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
    return uc.mem_read(OUT_ADDR, 24)

def main():
    orig_code = get_orig_bytes()
    cand_code, relocs = compile_candidate()
    print(f"Original size: {len(orig_code)} B, Candidate size: {len(cand_code)} B, Relocs: {len(relocs)}")

    # Test cases: (packed_color, tag_val)
    test_cases = [
        (0xFFFFFFFF, 0x42), # All 255
        (0x00000000, 0x10), # All 0
        (0x80402010, 0x7F), # Mixed values: r=0x10, g=0x20, b=0x40, a=0x80
        (0x00FF0000, 0x01), # Pure blue
        (0x0000FF00, 0x02), # Pure green
        (0x000000FF, 0x03), # Pure red
        (0xFF000000, 0x04), # Pure alpha
        (0x12345678, 0xAB), # Arbitrary pattern
        (0xDEADBEEF, 0xCD), # Arbitrary pattern 2
        (0xCAFEF00D, 0xEF), # Arbitrary pattern 3
    ]

    all_passed = True
    for i, (packed, tag) in enumerate(test_cases):
        out_orig = run_unicorn(orig_code, packed, tag)
        out_cand = run_unicorn(cand_code, packed, tag)

        hdr0_orig = struct.unpack_from("<I", out_orig, 0)[0]
        hdr0_cand = struct.unpack_from("<I", out_cand, 0)[0]
        hdr1_orig = struct.unpack_from("<I", out_orig, 4)[0]
        hdr1_cand = struct.unpack_from("<I", out_cand, 4)[0]
        floats_orig = struct.unpack_from("<4f", out_orig, 8)
        floats_cand = struct.unpack_from("<4f", out_cand, 8)

        # Check header
        hdr_match = (hdr0_orig == hdr0_cand) and (hdr1_orig == hdr1_cand)
        # Check floats with small epsilon
        flt_match = all(abs(o - c) < 1e-6 for o, c in zip(floats_orig, floats_cand))

        if hdr_match and flt_match:
            print(f"Case {i+1:2d} (packed=0x{packed:08X}, tag=0x{tag:02X}): PASS")
        else:
            print(f"Case {i+1:2d} (packed=0x{packed:08X}, tag=0x{tag:02X}): FAIL!")
            print(f"  Orig: hdr0=0x{hdr0_orig:08X}, hdr1=0x{hdr1_orig:08X}, floats={floats_orig}")
            print(f"  Cand: hdr0=0x{hdr0_cand:08X}, hdr1=0x{hdr1_cand:08X}, floats={floats_cand}")
            all_passed = False

    if all_passed:
        print("\nALL TEST CASES PASSED!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
