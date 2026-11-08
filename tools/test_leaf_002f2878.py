#!/usr/bin/env python3
"""Differential test for camp_func_002f2878 (0x002f2878) using Unicorn ARM emulation."""

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
FUNC_ADDR = 0x002f2878
FUNC_SIZE = 128

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000

HELPER_FLAG = 0x0029ED08
HELPER_REC  = 0x002B9364

RECORD_A_PTR = 0x00601000
RECORD_B_PTR = 0x00602000

ARGS_PTR = 0x00600000
TRAP_ADDR = 0x90000000

def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)

def compile_candidate():
    out_dir = ROOT / "build/test_leaf_002f2878"
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_file = out_dir / "leaf_batch30_c.o"
    src_file = ROOT / "src/engine/leaf_batch30_c.cpp"
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    for k in funcs:
        if "camp_func_002f2878" in k or "002f2878" in k:
            return funcs[k]
    raise KeyError("camp_func_002f2878 not found in compiled object")

def apply_relocations(code_bytes, relocs):
    fixed = bytearray(code_bytes)
    if len(fixed) < FUNC_SIZE:
        fixed.extend(b"\x00\x00\xa0\xe1" * ((FUNC_SIZE - len(fixed)) // 4))

    for rel in relocs:
        offset = rel.offset
        sym = rel.symbol_name
        target = 0
        if "camp_func_0029ed08" in sym or "0029ed08" in sym:
            target = HELPER_FLAG
        elif "camp_func_002b9364" in sym or "002b9364" in sym:
            target = HELPER_REC
        else:
            raise ValueError(f"Unknown symbol relocation: {sym}")

        if rel.relocation_type in (28, 10):
            pc = FUNC_ADDR + offset + 8
            disp = (target - pc) >> 2
            insn = struct.unpack_from("<I", fixed, offset)[0]
            insn = (insn & 0xFF000000) | (disp & 0x00FFFFFF)
            struct.pack_into("<I", fixed, offset, insn)
    return bytes(fixed)

def setup_emulator(code_bytes, flag_a, flag_b, rec_a, rec_b, val_a, val_b):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)

    # Map regions
    uc.mem_map(0x002F0000, 0x10000)
    uc.mem_map(STACK_ADDR, STACK_SIZE)
    uc.mem_map(0x00290000, 0x10000) # For HELPER_FLAG
    uc.mem_map(0x002B0000, 0x10000) # For HELPER_REC
    uc.mem_map(0x00600000, 0x10000) # For args and records
    uc.mem_map(TRAP_ADDR, 0x1000)

    # Write code
    uc.mem_write(FUNC_ADDR, code_bytes)

    # Write args
    arg_a_addr = ARGS_PTR
    arg_b_addr = ARGS_PTR + 4
    uc.mem_write(arg_a_addr, struct.pack("<H", val_a))
    uc.mem_write(arg_b_addr, struct.pack("<H", val_b))

    # Write records (u16 id, u8 f2, u8 f3)
    rec_a_bytes = struct.pack("<HBB", rec_a[0], rec_a[1], rec_a[2])
    rec_b_bytes = struct.pack("<HBB", rec_b[0], rec_b[1], rec_b[2])
    uc.mem_write(RECORD_A_PTR, rec_a_bytes)
    uc.mem_write(RECORD_B_PTR, rec_b_bytes)

    # Mock helpers
    def hook_code(uc, address, size, user_data):
        if address == HELPER_FLAG:
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            flag = flag_a if r0 == val_a else flag_b
            uc.reg_write(arm.UC_ARM_REG_R0, flag)
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            uc.reg_write(arm.UC_ARM_REG_PC, lr)
        elif address == HELPER_REC:
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            rec_ptr = RECORD_A_PTR if r0 == val_a else RECORD_B_PTR
            uc.reg_write(arm.UC_ARM_REG_R0, rec_ptr)
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            uc.reg_write(arm.UC_ARM_REG_PC, lr)

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_code)
    stub = b"\x1e\xff\x2f\xe1"  # bx lr
    uc.mem_write(HELPER_FLAG, stub)
    uc.mem_write(HELPER_REC, stub)

    return uc, arg_a_addr, arg_b_addr

def run_function(uc, arg_a_addr, arg_b_addr):
    uc.reg_write(arm.UC_ARM_REG_R0, arg_a_addr)
    uc.reg_write(arm.UC_ARM_REG_R1, arg_b_addr)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_ADDR + 0x8000)
    uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)

    uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
    res = uc.reg_read(arm.UC_ARM_REG_R0)
    # Sign-extend 32-bit
    if res >= 0x80000000:
        res -= 0x100000000
    return res

def main():
    orig_code = get_orig_bytes()
    cand_raw, relocs = compile_candidate()
    cand_code = apply_relocations(cand_raw, relocs)

    # Test cases: (flag_a, flag_b, (id_a, f2_a, f3_a), (id_b, f2_b, f3_b), val_a, val_b)
    test_cases = [
        # Case 1: flag_b has bits not in flag_a -> return 1
        (0x0001, 0x0003, (10, 5, 20), (20, 5, 20), 101, 102),
        # Case 2: flag_a has bits not in flag_b -> return -1
        (0x0007, 0x0003, (10, 5, 20), (20, 5, 20), 101, 102),
        # Case 3: flag_a == flag_b, f2 differs: f2_b > f2_a -> return > 0
        (0x0005, 0x0005, (10, 5, 20), (20, 8, 20), 101, 102),
        # Case 4: flag_a == flag_b, f2 differs: f2_b < f2_a -> return < 0
        (0x0005, 0x0005, (10, 9, 20), (20, 3, 20), 101, 102),
        # Case 5: flag_a == flag_b, f2 identical, f3 differs: f3_a > f3_b -> return > 0
        (0x0005, 0x0005, (10, 5, 30), (20, 5, 10), 101, 102),
        # Case 6: flag_a == flag_b, f2 identical, f3 differs: f3_a < f3_b -> return < 0
        (0x0005, 0x0005, (10, 5, 10), (20, 5, 40), 101, 102),
        # Case 7: flags, f2, f3 all identical: id_b > id_a -> return > 0
        (0x0005, 0x0005, (100, 5, 20), (250, 5, 20), 101, 102),
        # Case 8: flags, f2, f3 all identical: id_b < id_a -> return < 0
        (0x0005, 0x0005, (500, 5, 20), (120, 5, 20), 101, 102),
        # Case 9: completely identical records -> return 0
        (0x0005, 0x0005, (300, 5, 20), (300, 5, 20), 101, 102),
        # Case 10: high bit flags (e.g. 0x80000000)
        (0x80000000, 0xC0000000, (1, 1, 1), (2, 2, 2), 1, 2),
    ]

    all_passed = True
    for i, (fa, fb, rec_a, rec_b, va, vb) in enumerate(test_cases):
        uc_orig, a_orig, b_orig = setup_emulator(orig_code, fa, fb, rec_a, rec_b, va, vb)
        res_orig = run_function(uc_orig, a_orig, b_orig)

        uc_cand, a_cand, b_cand = setup_emulator(cand_code, fa, fb, rec_a, rec_b, va, vb)
        res_cand = run_function(uc_cand, a_cand, b_cand)

        if res_orig == res_cand:
            print(f"Case {i+1:2d}: PASS [res={res_cand}]")
        else:
            print(f"Case {i+1:2d}: FAIL! [orig={res_orig}, cand={res_cand}]")
            all_passed = False

    if all_passed:
        print("\nALL TEST CASES PASSED!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
