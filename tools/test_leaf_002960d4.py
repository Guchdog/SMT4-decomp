#!/usr/bin/env python3
"""Differential test for camp_func_002960d4 (0x002960d4) using Unicorn ARM emulation."""

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
FUNC_ADDR = 0x002960d4
FUNC_SIZE = 128

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000

# Mock addresses for external calls
TBB_GET_GLOBAL_SUBTABLE = 0x002C0EC4
TBB_GET_PAYLOAD_DATA    = 0x002C0E9C
CAMP_GET_RECORD         = 0x002B9364

SUBTABLE_1_PTR = 0x00600000
SUBTABLE_2_PTR = 0x00600100
PAYLOAD_1_PTR  = 0x00601000
PAYLOAD_2_PTR  = 0x00602000
RECORD_PTR     = 0x00603000

TRAP_ADDR = 0x90000000

def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)

def compile_candidate():
    out_dir = ROOT / "build/test_leaf_002960d4"
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_file = out_dir / "leaf_batch30_c.o"
    src_file = ROOT / "src/engine/leaf_batch30_c.cpp"
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    for k in funcs:
        if "camp_func_002960d4" in k or "002960d4" in k:
            return funcs[k]
    raise KeyError("camp_func_002960d4 not found in compiled object")

def apply_relocations(code_bytes, relocs):
    fixed = bytearray(code_bytes)
    # Pad to FUNC_SIZE if needed
    if len(fixed) < FUNC_SIZE:
        fixed.extend(b"\x00\x00\xa0\xe1" * ((FUNC_SIZE - len(fixed)) // 4))

    for rel in relocs:
        offset = rel.offset
        sym = rel.symbol_name
        target = 0
        if "Tbb_GetGlobalSubTable" in sym or sym == "ui_func_002c0ec4":
            target = TBB_GET_GLOBAL_SUBTABLE
        elif "Tbb_GetPayloadData" in sym or sym == "ui_func_002c0e9c":
            target = TBB_GET_PAYLOAD_DATA
        elif "camp_func_002b9364" in sym or "func_002b9364" in sym:
            target = CAMP_GET_RECORD
        else:
            raise ValueError(f"Unknown symbol relocation: {sym}")

        if rel.relocation_type in (28, 10):  # R_ARM_CALL / R_ARM_THM_CALL
            pc = FUNC_ADDR + offset + 8
            disp = (target - pc) >> 2
            insn = struct.unpack_from("<I", fixed, offset)[0]
            insn = (insn & 0xFF000000) | (disp & 0x00FFFFFF)
            struct.pack_into("<I", fixed, offset, insn)
    return bytes(fixed)

def setup_emulator(code_bytes, rec_byte3, table1_vals, table2_vals):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)

    # Map code & stack
    uc.mem_map(0x00290000, 0x10000)
    uc.mem_map(STACK_ADDR, STACK_SIZE)
    uc.mem_map(0x002B0000, 0x20000) # Covers 0x002B9364, 0x002C0EC4, 0x002C0E9C
    uc.mem_map(0x00600000, 0x10000) # Heap / Mock data
    uc.mem_map(TRAP_ADDR, 0x1000)

    # Write code
    uc.mem_write(FUNC_ADDR, code_bytes)

    # Write mock table 1 (u32 array) at PAYLOAD_1_PTR
    p1_data = struct.pack(f"<{len(table1_vals)}I", *table1_vals)
    uc.mem_write(PAYLOAD_1_PTR, p1_data)

    # Write mock table 2 (u16 array) at PAYLOAD_2_PTR
    p2_data = struct.pack(f"<{len(table2_vals)}H", *table2_vals)
    uc.mem_write(PAYLOAD_2_PTR, p2_data)

    # Write mock record at RECORD_PTR
    rec_data = bytearray(16)
    rec_data[3] = rec_byte3
    uc.mem_write(RECORD_PTR, bytes(rec_data))

    # Helper implementations (ARM bx lr):
    # 1. Tbb_GetGlobalSubTable: if r1 == 1 return SUBTABLE_1_PTR else SUBTABLE_2_PTR
    # mov r0, SUBTABLE_1_PTR (or 2); bx lr
    # 2. Tbb_GetPayloadData: if r0 == SUBTABLE_1_PTR return PAYLOAD_1_PTR else PAYLOAD_2_PTR
    # 3. CAMP_GET_RECORD: return RECORD_PTR

    def hook_code(uc, address, size, user_data):
        if address == TBB_GET_GLOBAL_SUBTABLE:
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            uc.reg_write(arm.UC_ARM_REG_R0, SUBTABLE_1_PTR if r1 == 1 else SUBTABLE_2_PTR)
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            uc.reg_write(arm.UC_ARM_REG_PC, lr)
        elif address == TBB_GET_PAYLOAD_DATA:
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            uc.reg_write(arm.UC_ARM_REG_R0, PAYLOAD_1_PTR if r0 == SUBTABLE_1_PTR else PAYLOAD_2_PTR)
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            uc.reg_write(arm.UC_ARM_REG_PC, lr)
        elif address == CAMP_GET_RECORD:
            uc.reg_write(arm.UC_ARM_REG_R0, RECORD_PTR)
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            uc.reg_write(arm.UC_ARM_REG_PC, lr)

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_code)
    # Put bx lr stubs at mock helper addresses
    stub = b"\x1e\xff\x2f\xe1"  # bx lr
    uc.mem_write(TBB_GET_GLOBAL_SUBTABLE, stub)
    uc.mem_write(TBB_GET_PAYLOAD_DATA, stub)
    uc.mem_write(CAMP_GET_RECORD, stub)

    return uc

def run_function(uc, key, index, stat_val):
    uc.reg_write(arm.UC_ARM_REG_R0, key)
    uc.reg_write(arm.UC_ARM_REG_R1, index)
    uc.reg_write(arm.UC_ARM_REG_R2, stat_val)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_ADDR + 0x8000)
    uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)

    uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
    return uc.reg_read(arm.UC_ARM_REG_R0)

def main():
    orig_code = get_orig_bytes()
    cand_raw, relocs = compile_candidate()
    cand_code = apply_relocations(cand_raw, relocs)

    table1 = [100, 250, 500, 1000, 2000, 5000]
    table2 = [110, 120, 130, 140, 150, 160, 170, 180, 190, 200]
    rec_byte3 = 20

    # Test cases: (key, index, stat_val)
    test_cases = [
        # diff <= 0: stat_val <= rec[3] - 1 (<= 19) -> scale = 100
        (1, 1, 10),  # diff = 10 - 20 + 1 = -9 <= 0 -> 100 * 100 / 100 = 100
        (1, 2, 19),  # diff = 19 - 20 + 1 = 0 <= 0 -> 250 * 100 / 100 = 250
        (1, 3, 0),   # stat_val = 0 -> diff = -19 <= 0 -> 500
        # diff in 1..10
        (1, 1, 20),  # diff = 20 - 20 + 1 = 1 -> table2[0] = 110 -> 100 * 110 / 100 = 110
        (1, 2, 21),  # diff = 2 -> table2[1] = 120 -> 250 * 120 / 100 = 300
        (1, 4, 24),  # diff = 5 -> table2[4] = 150 -> 1000 * 150 / 100 = 1500
        (1, 5, 29),  # diff = 10 -> table2[9] = 200 -> 2000 * 200 / 100 = 4000
        # diff > 10 clamped to 10
        (1, 5, 30),  # diff = 11 -> clamped to 10 -> table2[9] = 200 -> 4000
        (1, 6, 100), # diff = 81 -> clamped to 10 -> table2[9] = 200 -> 5000 * 200 / 100 = 10000
        (2, 3, -5),  # negative stat_val -> diff <= 0 -> 500
    ]

    all_passed = True
    for i, (key, index, stat_val) in enumerate(test_cases):
        uc_orig = setup_emulator(orig_code, rec_byte3, table1, table2)
        res_orig = run_function(uc_orig, key, index, stat_val)

        uc_cand = setup_emulator(cand_code, rec_byte3, table1, table2)
        res_cand = run_function(uc_cand, key, index, stat_val)

        if res_orig == res_cand:
            print(f"Case {i+1:2d} (key={key}, idx={index}, stat={stat_val}): PASS [res={res_cand}]")
        else:
            print(f"Case {i+1:2d} (key={key}, idx={index}, stat={stat_val}): FAIL! [orig={res_orig}, cand={res_cand}]")
            all_passed = False

    if all_passed:
        print("\nALL TEST CASES PASSED!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
