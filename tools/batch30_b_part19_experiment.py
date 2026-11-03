#!/usr/bin/env python3
"""Differential test for batch 30 B part 19:
- battle_func_002f6d84 (0x002F6D84, 120 B)
- battle_func_002f6dfc (0x002F6DFC, 116 B)
- ui_func_002f701c (0x002F701C, 96 B)
- battle_func_002f7108 (0x002F7108, 96 B)
- engine_func_002fb54c (0x002FB54C, 124 B)
"""

from __future__ import annotations

from pathlib import Path
import struct
import sys

from unicorn import (
    Uc,
    UC_ARCH_ARM,
    UC_MODE_ARM,
    UC_HOOK_MEM_UNMAPPED,
    UC_HOOK_CODE,
)
from unicorn.arm_const import (
    UC_CPU_ARM_11MPCORE,
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_R4,
    UC_ARM_REG_R5,
    UC_ARM_REG_R6,
    UC_ARM_REG_R7,
    UC_ARM_REG_R8,
    UC_ARM_REG_SB,
    UC_ARM_REG_SL,
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

COMPILED_FUNCTIONS = None
SOURCE = ROOT / "src/engine/leaf_batch30_b.cpp"

def load_original_bytes(addr: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(addr - CODE_BASE)
        return f.read(size)

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch30_b.o"
        result = compile_tu_armv6k(source, obj, ROOT)
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        COMPILED_FUNCTIONS = extract_elf_functions_detailed(obj)
    if func_name not in COMPILED_FUNCTIONS:
        raise RuntimeError(f"{func_name} not in object")
    return COMPILED_FUNCTIONS[func_name]

def stage_body(body: bytes, relocs, target_addr: int, symbol_map: dict[str, int]) -> bytes:
    data = bytearray(body)
    for reloc in relocs:
        sym = reloc.symbol_name
        if sym not in symbol_map:
            raise RuntimeError(f"Unmapped relocation: {sym}")
        stub_addr = symbol_map[sym]
        rel_off = stub_addr - (target_addr + reloc.offset + 8)
        imm24 = (rel_off >> 2) & 0x00FFFFFF
        inst = struct.unpack_from("<I", data, reloc.offset)[0]
        inst = (inst & 0xFF000000) | imm24
        struct.pack_into("<I", data, reloc.offset, inst)
    return bytes(data)

def setup_uc() -> Uc:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.ctl_set_cpu_model(UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(CODE_BASE, CODE_SIZE)
    with open(ORIG_BIN, "rb") as f:
        code_data = f.read(CODE_SIZE)
    uc.mem_write(CODE_BASE, code_data)

    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(0x00480000, 0x00100000)
    uc.mem_map(0x00580000, 0x00100000)

    def hook_unmapped(uc, access, address, size, value, user_data):
        page = address & ~0xFFF
        print(f"CRASH: unmapped at 0x{address:08x}, pc=0x{uc.reg_read(UC_ARM_REG_PC):08x}")
        try:
            uc.mem_map(page, 0x1000)
            return True
        except Exception:
            return False

    def hook_code(uc, address, size, user_data):
        if address == 0x002C615C:
            num = struct.unpack("<i", struct.pack("<I", uc.reg_read(UC_ARM_REG_R0)))[0]
            den = struct.unpack("<i", struct.pack("<I", uc.reg_read(UC_ARM_REG_R1)))[0]
            res = int(num / den) if den != 0 else 0
            uc.reg_write(UC_ARM_REG_R0, res & 0xFFFFFFFF)

    uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_unmapped)
    uc.hook_add(UC_HOOK_CODE, hook_code)
    return uc

def test_battle_func_002f6d84():
    print("--- Testing battle_func_002f6d84 ---")
    addr = 0x002F6D84
    size = 120
    orig_code = load_original_bytes(addr, size)

    out_dir = ROOT / "build" / "batch30_b_part19"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("battle_func_002f6d84", out_dir)

    sym_map = {
        "ui_func_00293c98": 0x00293C98,
        "camp_func_002b9364": 0x002B9364,
        "battle_func_0028df54": 0x0028DF54,
    }
    staged_decomp = stage_body(comp, relocs, addr, sym_map)

    # Stub 0x00293C98: returns 0x00490000
    code_293c98 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", 0x00490000)
    # Stub 0x002B9364: returns 0x00497000 + id*8
    code_2b9364 = struct.pack("<IIII", 0xe1a00180, 0xe59f1004, 0xe0800001, 0xe12fff1e) + struct.pack("<I", 0x00497000)
    # Stub 0x0028DF54: records arg r0 at 0x00495000 and returns
    code_28df54 = struct.pack("<III", 0xe59f1004, 0xe5810000, 0xe12fff1e) + struct.pack("<I", 0x00495000)

    cases = [
        # (name, match_idx, flags, id, info_type)
        ("no_match_empty", -1, 0, 0, 0),
        ("match_idx_0_type_5", 0, 0x11, 1, 5),
        ("match_idx_5_type_5", 5, 0x11, 2, 5),
        ("match_idx_108_type_5", 108, 0x11, 3, 5),
        ("type_not_5", 5, 0x11, 4, 4),
        ("flag_0x40_set", 5, 0x51, 5, 5),
        ("flag_0x10_missing", 5, 0x01, 6, 5),
    ]

    for name, m_idx, m_flags, m_id, m_type in cases:
        def setup_mem(uc):
            uc.mem_write(0x00293C98, code_293c98)
            uc.mem_write(0x002B9364, code_2b9364)
            uc.mem_write(0x0028DF54, code_28df54)
            uc.mem_write(0x00495000, struct.pack("<I", 0xDEADBEEF))

            uc.mem_write(0x00491fc0, struct.pack("<I", 0x004A0000))
            zeroes = bytearray(648 * 109)
            if m_idx >= 0:
                off = m_idx * 648
                struct.pack_into("<I", zeroes, off, m_flags)
                struct.pack_into("<H", zeroes, off + 0xCE, m_id)
                uc.mem_write(0x00497000 + m_id * 8 + 5, bytes([m_type]))
            uc.mem_write(0x004A0000, bytes(zeroes))

        RET_ADDR = 0x00499000
        # Run orig
        uc_orig = setup_uc()
        setup_mem(uc_orig)
        uc_orig.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_orig.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_orig.emu_start(addr, RET_ADDR)
        orig_r0 = uc_orig.reg_read(UC_ARM_REG_R0)
        orig_rec = struct.unpack("<I", uc_orig.mem_read(0x00495000, 4))[0]

        # Run decomp
        uc_decomp = setup_uc()
        setup_mem(uc_decomp)
        uc_decomp.mem_write(addr, staged_decomp)
        uc_decomp.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_decomp.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_decomp.emu_start(addr, RET_ADDR)
        decomp_r0 = uc_decomp.reg_read(UC_ARM_REG_R0)
        decomp_rec = struct.unpack("<I", uc_decomp.mem_read(0x00495000, 4))[0]

        assert orig_r0 == decomp_r0, f"{name}: r0 mismatch {orig_r0} != {decomp_r0}"
        assert orig_rec == decomp_rec, f"{name}: recorded call mismatch {orig_rec} != {decomp_rec}"

    print("battle_func_002f6d84: PASS")

def test_battle_func_002f6dfc():
    print("--- Testing battle_func_002f6dfc ---")
    addr = 0x002F6DFC
    size = 116
    orig_code = load_original_bytes(addr, size)

    out_dir = ROOT / "build" / "batch30_b_part19"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("battle_func_002f6dfc", out_dir)

    sym_map = {
        "ui_func_00293c98": 0x00293C98,
        "battle_func_00247170": 0x00247170,
        "battle_func_0028df54": 0x0028DF54,
    }
    staged_decomp = stage_body(comp, relocs, addr, sym_map)

    # Stub 0x00293C98: returns 0x00490000
    code_293c98 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", 0x00490000)
    # Stub 0x0028DF54: records arg r0 at 0x00495000
    code_28df54 = struct.pack("<III", 0xe59f1004, 0xe5810000, 0xe12fff1e) + struct.pack("<I", 0x00495000)

    cases = [
        # (name, match_idx, flags, func_ret)
        ("no_match_empty", -1, 0, 0),
        ("match_idx_0_true", 0, 0x11, 1),
        ("match_idx_5_true", 5, 0x11, 1),
        ("match_idx_108_true", 108, 0x11, 1),
        ("func_ret_false", 5, 0x11, 0),
        ("flag_0x40_set", 5, 0x51, 1),
        ("flag_0x10_missing", 5, 0x01, 1),
    ]

    for name, m_idx, m_flags, f_ret in cases:
        # Stub 0x00247170: returns f_ret
        code_247170 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", f_ret)

        def setup_mem(uc):
            uc.mem_write(0x00293C98, code_293c98)
            uc.mem_write(0x00247170, code_247170)
            uc.mem_write(0x0028DF54, code_28df54)
            uc.mem_write(0x00495000, struct.pack("<I", 0xDEADBEEF))

            uc.mem_write(0x00491fc0, struct.pack("<I", 0x004A0000))
            zeroes = bytearray(648 * 109)
            if m_idx >= 0:
                off = m_idx * 648
                struct.pack_into("<I", zeroes, off, m_flags)
            uc.mem_write(0x004A0000, bytes(zeroes))

        RET_ADDR = 0x00499000
        # Run orig
        uc_orig = setup_uc()
        setup_mem(uc_orig)
        uc_orig.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_orig.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_orig.emu_start(addr, RET_ADDR)
        orig_r0 = uc_orig.reg_read(UC_ARM_REG_R0)
        orig_rec = struct.unpack("<I", uc_orig.mem_read(0x00495000, 4))[0]

        # Run decomp
        uc_decomp = setup_uc()
        setup_mem(uc_decomp)
        uc_decomp.mem_write(addr, staged_decomp)
        uc_decomp.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_decomp.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_decomp.emu_start(addr, RET_ADDR)
        decomp_r0 = uc_decomp.reg_read(UC_ARM_REG_R0)
        decomp_rec = struct.unpack("<I", uc_decomp.mem_read(0x00495000, 4))[0]

        assert orig_r0 == decomp_r0, f"{name}: r0 mismatch {orig_r0} != {decomp_r0}"
        assert orig_rec == decomp_rec, f"{name}: recorded call mismatch {orig_rec} != {decomp_rec}"

    print("battle_func_002f6dfc: PASS")

def test_ui_func_002f701c():
    print("--- Testing ui_func_002f701c ---")
    addr = 0x002F701C
    size = 96
    orig_code = load_original_bytes(addr, size)

    out_dir = ROOT / "build" / "batch30_b_part19"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_002f701c", out_dir)

    sym_map = {
        "engine_func_00296f60": 0x00296F60,
        "ui_func_00293c98": 0x00293C98,
        "battle_func_00249b0c": 0x00249B0C,
        "ui_func_002c615c": 0x002C615C,
        "battle_func_0028df54": 0x0028DF54,
    }
    staged_decomp = stage_body(comp, relocs, addr, sym_map)

    # Stub 0x00293C98: returns 0x00490000
    code_293c98 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", 0x00490000)
    # Stub 0x0028DF54: records arg r0 at 0x00495000
    code_28df54 = struct.pack("<III", 0xe59f1004, 0xe5810000, 0xe12fff1e) + struct.pack("<I", 0x00495000)
    # Stub 0x002C615C: bx lr
    code_2c615c = struct.pack("<I", 0xe12fff1e)

    cases = [
        # (name, threshold, sub_ptr, cur, max_val, expected_match)
        ("null_sub", 50, 0, 10, 100, False),
        ("pct_le_threshold", 50, 0x00492000, 40, 100, True), # 40 <= 50
        ("pct_eq_threshold", 50, 0x00492000, 50, 100, True), # 50 <= 50
        ("pct_gt_threshold", 50, 0x00492000, 60, 100, False), # 60 > 50
        ("zero_cur", 10, 0x00492000, 0, 100, True),
    ]

    for name, thresh, sub_ptr, cur, max_val, exp_match in cases:
        # Stub 0x00296F60: returns thresh
        code_296f60 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", thresh)
        # Stub 0x00249B0C: returns sub_ptr
        code_249b0c = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", sub_ptr)

        def setup_mem(uc):
            uc.mem_write(0x00296F60, code_296f60)
            uc.mem_write(0x00293C98, code_293c98)
            uc.mem_write(0x00249B0C, code_249b0c)
            uc.mem_write(0x002C615C, code_2c615c)
            uc.mem_write(0x0028DF54, code_28df54)
            uc.mem_write(0x00495000, struct.pack("<I", 0xDEADBEEF))

            if sub_ptr != 0:
                uc.mem_write(sub_ptr, bytes(0x200))
                # offset 0xCC + 0xE8 = 0x1B4 (u16 cur)
                # offset 0xCC + 0xEA = 0x1B6 (s16 max)
                uc.mem_write(sub_ptr + 0x1B4, struct.pack("<H", cur))
                uc.mem_write(sub_ptr + 0x1B6, struct.pack("<h", max_val))

        RET_ADDR = 0x00499000
        # Run orig
        uc_orig = setup_uc()
        setup_mem(uc_orig)
        uc_orig.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_orig.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_orig.emu_start(addr, RET_ADDR)
        orig_r0 = uc_orig.reg_read(UC_ARM_REG_R0)
        orig_rec = struct.unpack("<I", uc_orig.mem_read(0x00495000, 4))[0]

        # Run decomp
        uc_decomp = setup_uc()
        setup_mem(uc_decomp)
        uc_decomp.mem_write(addr, staged_decomp)
        uc_decomp.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_decomp.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_decomp.emu_start(addr, RET_ADDR)
        decomp_r0 = uc_decomp.reg_read(UC_ARM_REG_R0)
        decomp_rec = struct.unpack("<I", uc_decomp.mem_read(0x00495000, 4))[0]

        assert orig_r0 == decomp_r0, f"{name}: r0 mismatch {orig_r0} != {decomp_r0}"
        assert orig_rec == decomp_rec, f"{name}: recorded call mismatch {orig_rec} != {decomp_rec}"
        expected = 1 if exp_match else 0
        assert orig_rec == expected, f"{name}: expected {expected} got {orig_rec}"

    print("ui_func_002f701c: PASS")

def test_battle_func_002f7108():
    print("--- Testing battle_func_002f7108 ---")
    addr = 0x002F7108
    size = 96
    orig_code = load_original_bytes(addr, size)

    out_dir = ROOT / "build" / "batch30_b_part19"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("battle_func_002f7108", out_dir)

    sym_map = {
        "engine_func_00296f60": 0x00296F60,
        "script_vm_func_0027eb98": 0x0027EB98,
        "battle_func_0028df54": 0x0028DF54,
    }
    staged_decomp = stage_body(comp, relocs, addr, sym_map)

    # Stub 0x0027EB98: returns sub_obj pointer 0x00492000
    code_27eb98 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", 0x00492000)
    # Stub 0x0028DF54: records arg r0 at 0x00495000
    code_28df54 = struct.pack("<III", 0xe59f1004, 0xe5810000, 0xe12fff1e) + struct.pack("<I", 0x00495000)

    cases = [
        # (name, idx, val, expected_match)
        ("shift_is_2", 0, (2 << 10) | 0x3F, True),
        ("shift_is_2_other_idx", 5, (2 << 10) | 0x12, True),
        ("shift_is_0", 0, 0x123, True),
        ("shift_is_1", 0, (1 << 10) | 0x12, False),
        ("shift_is_3", 0, (3 << 10) | 0x12, False),
    ]

    for name, idx, val, exp_match in cases:
        # Stub 0x00296F60: returns idx
        code_296f60 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", idx)

        def setup_mem(uc):
            uc.mem_write(0x00296F60, code_296f60)
            uc.mem_write(0x0027EB98, code_27eb98)
            uc.mem_write(0x0028DF54, code_28df54)
            # Global 0x0043427C: points to base 0x00491000
            uc.mem_write(0x0043427C, struct.pack("<I", 0x00491000))
            # sub_obj at 0x00492000: offset 0x28 points to arr at 0x00493000
            uc.mem_write(0x00492028, struct.pack("<I", 0x00493000))
            # arr at 0x00493000: zero out 0x200 bytes
            uc.mem_write(0x00493000, bytes(0x200))
            # offset: arr + idx*2 + 0x100 + 0x26 = arr + 0x126 + idx*2
            uc.mem_write(0x00493000 + 0x126 + idx * 2, struct.pack("<H", val))
            uc.mem_write(0x00495000, struct.pack("<I", 0xDEADBEEF))

        RET_ADDR = 0x00499000
        # Run orig
        uc_orig = setup_uc()
        setup_mem(uc_orig)
        uc_orig.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_orig.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_orig.emu_start(addr, RET_ADDR)
        orig_r0 = uc_orig.reg_read(UC_ARM_REG_R0)
        orig_rec = struct.unpack("<I", uc_orig.mem_read(0x00495000, 4))[0]

        # Run decomp
        uc_decomp = setup_uc()
        setup_mem(uc_decomp)
        uc_decomp.mem_write(addr, staged_decomp)
        uc_decomp.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_decomp.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_decomp.emu_start(addr, RET_ADDR)
        decomp_r0 = uc_decomp.reg_read(UC_ARM_REG_R0)
        decomp_rec = struct.unpack("<I", uc_decomp.mem_read(0x00495000, 4))[0]

        assert orig_r0 == decomp_r0, f"{name}: r0 mismatch {orig_r0} != {decomp_r0}"
        assert orig_rec == decomp_rec, f"{name}: recorded call mismatch {orig_rec} != {decomp_rec}"
        expected = 1 if exp_match else 0
        assert orig_rec == expected, f"{name}: expected {expected} got {orig_rec}"

    print("battle_func_002f7108: PASS")

def test_engine_func_002fb54c():
    print("--- Testing engine_func_002fb54c ---")
    addr = 0x002FB54C
    size = 124
    orig_code = load_original_bytes(addr, size)

    out_dir = ROOT / "build" / "batch30_b_part19"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_002fb54c", out_dir)

    sym_map = {
        "func_00289640": 0x00289640,
        "engine_func_00289640": 0x00289640,
        "engine_func_002c1f28": 0x002C1F28,
        "script_vm_func_00287990": 0x00287990,
        "engine_func_00296f60": 0x00296F60,
        "script_vm_func_0029c660": 0x0029C660,
        "camp_func_002b8ce4": 0x002B8CE4,
    }
    staged_decomp = stage_body(comp, relocs, addr, sym_map)

    # Stubs
    code_287990 = struct.pack("<II", 0xe3a00001, 0xe12fff1e)
    # 0x0029C660: records r0, r1, r2 at 0x00495004
    code_29c660 = struct.pack("<IIII", 0xe59f3008, 0xe8830007, 0xe12fff1e, 0x00000000) + struct.pack("<I", 0x00495004)

    cases = [
        # (name, f_289640, f_2c1f28, f_2b8ce4, f_296f60)
        ("path_a_c1f28_true", 1, 1, 0, 0),
        ("path_a_c1f28_false_b8ce4_true", 1, 0, 1, 0),
        ("path_a_c1f28_false_b8ce4_false", 1, 0, 0, 0),
        ("path_b_c1f28_true", 0, 1, 0, 0),
        ("path_b_c1f28_false", 0, 0, 0, 0x77),
    ]

    for name, v_289640, v_2c1f28, v_2b8ce4, v_296f60 in cases:
        code_289640 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", v_289640)
        code_2c1f28 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", v_2c1f28)
        code_2b8ce4 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", v_2b8ce4)
        code_296f60 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", v_296f60)

        def setup_mem(uc):
            uc.mem_write(0x00289640, code_289640)
            uc.mem_write(0x002C1F28, code_2c1f28)
            uc.mem_write(0x00287990, code_287990)
            uc.mem_write(0x00296F60, code_296f60)
            uc.mem_write(0x0029C660, code_29c660)
            uc.mem_write(0x002B8CE4, code_2b8ce4)
            uc.mem_write(0x00495000, bytes(32))

        RET_ADDR = 0x00499000
        # Run orig
        uc_orig = setup_uc()
        setup_mem(uc_orig)
        uc_orig.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_orig.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_orig.emu_start(addr, RET_ADDR)
        orig_r0 = uc_orig.reg_read(UC_ARM_REG_R0)
        orig_rec = uc_orig.mem_read(0x00495000, 32)

        # Run decomp
        uc_decomp = setup_uc()
        setup_mem(uc_decomp)
        uc_decomp.mem_write(addr, staged_decomp)
        uc_decomp.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_decomp.reg_write(UC_ARM_REG_LR, RET_ADDR)
        uc_decomp.emu_start(addr, RET_ADDR)
        decomp_r0 = uc_decomp.reg_read(UC_ARM_REG_R0)
        decomp_rec = uc_decomp.mem_read(0x00495000, 32)

        assert orig_r0 == decomp_r0, f"{name}: r0 mismatch {orig_r0} != {decomp_r0}"
        assert orig_rec == decomp_rec, f"{name}: call log mismatch {orig_rec} != {decomp_rec}"

    print("engine_func_002fb54c: PASS")

def main():
    test_battle_func_002f6d84()
    test_battle_func_002f6dfc()
    test_ui_func_002f701c()
    test_battle_func_002f7108()
    test_engine_func_002fb54c()
    print("\nALL 5 FUNCTIONS IN BATCH 30 B PART 19 PASSED WITH 100% DIFFERENTIAL FIDELITY!")

if __name__ == "__main__":
    main()
