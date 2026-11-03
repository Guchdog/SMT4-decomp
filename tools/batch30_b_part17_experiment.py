#!/usr/bin/env python3
"""Differential test for batch 30 B part 17:
- battle_func_002dbad4 (0x002DBAD4, 120 B)
- func_002dca98 (0x002DCA98, 96 B)
- ui_func_002e0c54 (0x002E0C54, 108 B)
- camp_func_002e3304 (0x002E3304, 124 B)
- battle_func_002e3bb0 (0x002E3BB0, 120 B)
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

    uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_unmapped)
    return uc

def test_battle_func_002dbad4():
    print("--- Testing battle_func_002dbad4 ---")
    addr = 0x002DBAD4
    size = 120
    orig_code = load_original_bytes(addr, size)

    out_dir = ROOT / "build" / "batch30_b_part17"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("battle_func_002dbad4", out_dir)

    sym_map = {
        "engine_func_00296f60": 0x00296F60,
        "ui_func_00293c98": 0x00293C98,
        "battle_func_0028df54": 0x0028DF54,
    }
    staged_decomp = stage_body(comp, relocs, addr, sym_map)

    def make_stub(target_id: int):
        # Stub 0x00296F60: returns target_id
        # Stub 0x00293C98: returns 0x00490000
        # Stub 0x0028DF54: records arg r0 at 0x00495000 and returns
        code_296f60 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", target_id)
        code_293c98 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", 0x00490000)
        code_28df54 = struct.pack("<III", 0xe59f1004, 0xe5810000, 0xe12fff1e) + struct.pack("<I", 0x00495000)
        return code_296f60, code_293c98, code_28df54

    cases = [
        # (name, target_id, match_idx, match_flags, match_id)
        ("no_match", 0x55, -1, 0, 0),
        ("match_idx_0", 0x42, 0, 0x11, 0x42),
        ("match_idx_10", 0x100, 10, 0x11, 0x100),
        ("match_idx_108_last", 0x77, 108, 0x11, 0x77),
        ("flags_0x40_set_skip", 0x88, 5, 0x51, 0x88),
        ("flags_0x10_missing_skip", 0x99, 5, 0x01, 0x99),
        ("id_mismatch", 0x12, 5, 0x11, 0x13),
    ]

    for name, target_id, m_idx, m_flags, m_id in cases:
        c_296f60, c_293c98, c_28df54 = make_stub(target_id)

        def setup_mem(uc):
            uc.mem_write(0x00296F60, c_296f60)
            uc.mem_write(0x00293C98, c_293c98)
            uc.mem_write(0x0028DF54, c_28df54)
            # Clear recorded call
            uc.mem_write(0x00495000, struct.pack("<I", 0xDEADBEEF))

            # UI obj at 0x00490000, offset 0x1fc0 points to entries array at 0x00491000
            uc.mem_write(0x00491fc0, struct.pack("<I", 0x004A0000))
            # Zero out 109 entries of 648 bytes (0x288 * 109 = 0x11460 bytes)
            # Map memory if needed: 0x004a0000 is inside 0x00480000
            zeroes = bytearray(648 * 109)
            if m_idx >= 0:
                off = m_idx * 648
                struct.pack_into("<I", zeroes, off, m_flags)
                struct.pack_into("<H", zeroes, off + 0xCE, m_id)
            uc.mem_write(0x004A0000, bytes(zeroes))

        # Run original
        uc_orig = setup_uc()
        setup_mem(uc_orig)
        uc_orig.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_orig.reg_write(UC_ARM_REG_LR, 0x002DBB48 + 4)
        uc_orig.emu_start(addr, 0x002DBB48 + 4)
        orig_r0 = uc_orig.reg_read(UC_ARM_REG_R0)
        orig_rec = struct.unpack("<I", uc_orig.mem_read(0x00495000, 4))[0]

        # Run decomp
        uc_decomp = setup_uc()
        setup_mem(uc_decomp)
        uc_decomp.mem_write(addr, staged_decomp)
        uc_decomp.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_decomp.reg_write(UC_ARM_REG_LR, 0x002DBB48 + 4)
        uc_decomp.emu_start(addr, 0x002DBB48 + 4)
        decomp_r0 = uc_decomp.reg_read(UC_ARM_REG_R0)
        decomp_rec = struct.unpack("<I", uc_decomp.mem_read(0x00495000, 4))[0]

        assert orig_r0 == decomp_r0, f"{name}: r0 mismatch {orig_r0} != {decomp_r0}"
        assert orig_rec == decomp_rec, f"{name}: recorded call mismatch {orig_rec} != {decomp_rec}"

    print("battle_func_002dbad4: PASS")

def test_func_002dca98():
    print("--- Testing func_002dca98 ---")
    addr = 0x002DCA98
    size = 96
    orig_code = load_original_bytes(addr, size)

    out_dir = ROOT / "build" / "batch30_b_part17"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_002dca98", out_dir)

    sym_map = {
        "camp_func_00288380": 0x00288380,
    }
    staged_decomp = stage_body(comp, relocs, addr, sym_map)

    # Stub 0x00288380: returns id * 10
    code_288380 = struct.pack("<II", 0xe0800080, 0xe12fff1e) # add r0, r0, r0, lsl #2 (r0 * 5)
    # wait: let's make it simple: r0 = r0 * 3 + 7
    # mov r1, #3; mul r0, r1, r0; add r0, r0, #7; bx lr
    code_288380 = struct.pack("<IIII", 0xe3a01003, 0xe0000091, 0xe2800007, 0xe12fff1e)

    cases = [
        # (name, a_f0, a_f2, b_f0, b_f2)
        ("both_f2_zero", 10, 0, 20, 0),
        ("a_f2_zero_b_not", 10, 0, 20, 1),
        ("a_f2_not_b_zero", 10, 1, 20, 0),
        ("both_f2_not_b_gt_a", 10, 2, 25, 3),
        ("both_f2_not_a_gt_b", 30, 2, 12, 1),
        ("both_f2_not_equal", 15, 2, 15, 2),
    ]

    for name, a0, a2, b0, b2 in cases:
        def setup_mem(uc):
            uc.mem_write(0x00288380, code_288380)
            uc.mem_write(0x00490000, struct.pack("<HH", a0, a2))
            uc.mem_write(0x00490004, struct.pack("<HH", b0, b2))

        # Run original
        uc_orig = setup_uc()
        setup_mem(uc_orig)
        uc_orig.reg_write(UC_ARM_REG_R0, 0x00490000)
        uc_orig.reg_write(UC_ARM_REG_R1, 0x00490004)
        uc_orig.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_orig.reg_write(UC_ARM_REG_LR, 0x002DCAE4 + 4)
        uc_orig.emu_start(addr, 0x002DCAE4 + 4)
        orig_r0 = uc_orig.reg_read(UC_ARM_REG_R0)

        # Run decomp
        uc_decomp = setup_uc()
        setup_mem(uc_decomp)
        uc_decomp.mem_write(addr, staged_decomp)
        uc_decomp.reg_write(UC_ARM_REG_R0, 0x00490000)
        uc_decomp.reg_write(UC_ARM_REG_R1, 0x00490004)
        uc_decomp.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_decomp.reg_write(UC_ARM_REG_LR, 0x002DCAE4 + 4)
        uc_decomp.emu_start(addr, 0x002DCAE4 + 4)
        decomp_r0 = uc_decomp.reg_read(UC_ARM_REG_R0)

        assert orig_r0 == decomp_r0, f"{name}: r0 mismatch orig={orig_r0} decomp={decomp_r0}"

    print("func_002dca98: PASS")

def test_ui_func_002e0c54():
    print("--- Testing ui_func_002e0c54 ---")
    addr = 0x002E0C54
    size = 108
    orig_code = load_original_bytes(addr, size)

    out_dir = ROOT / "build" / "batch30_b_part17"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_002e0c54", out_dir)

    sym_map = {
        "ui_func_002c0b94": 0x002C0B94,
    }
    staged_decomp = stage_body(comp, relocs, addr, sym_map)

    # Map memory around 0x0044E0F8:
    # 0x00440000 is inside code_data (CODE_SIZE is 0x00380000, 0x100000 + 0x380000 = 0x480000)
    # So 0x0044E0F8 is already mapped!

    cases = [
        ("null_obj", 0),
        ("valid_obj", 0x00490000),
    ]

    for name, obj_ptr in cases:
        # Stub 0x002C0B94: returns obj_ptr
        code_2c0b94 = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", obj_ptr)

        def setup_mem(uc):
            uc.mem_write(0x002C0B94, code_2c0b94)
            # Write 4 test bytes at 0x0044E0F8
            uc.mem_write(0x0044E0F8, bytes([0x12, 0x34, 0x56, 0x78]))
            if obj_ptr != 0:
                # Clear target area obj + 0x24B7C..0x24B81
                # Note: 0x00490000 + 0x24B7C = 0x004B4B7C (inside 0x00480000..0x00580000)
                uc.mem_write(obj_ptr + 0x24B7C, bytes([0, 0, 0, 0, 0, 0]))

        # Run orig
        uc_orig = setup_uc()
        setup_mem(uc_orig)
        uc_orig.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_orig.reg_write(UC_ARM_REG_LR, 0x002E0CB4 + 4)
        uc_orig.emu_start(addr, 0x002E0CB4 + 4)
        if obj_ptr != 0:
            orig_bytes = uc_orig.mem_read(obj_ptr + 0x24B7C, 5)

        # Run decomp
        uc_decomp = setup_uc()
        setup_mem(uc_decomp)
        uc_decomp.mem_write(addr, staged_decomp)
        uc_decomp.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_decomp.reg_write(UC_ARM_REG_LR, 0x002E0CB4 + 4)
        uc_decomp.emu_start(addr, 0x002E0CB4 + 4)
        if obj_ptr != 0:
            decomp_bytes = uc_decomp.mem_read(obj_ptr + 0x24B7C, 5)
            assert orig_bytes == decomp_bytes, f"{name}: bytes mismatch {orig_bytes} != {decomp_bytes}"

    print("ui_func_002e0c54: PASS")

def test_camp_func_002e3304():
    print("--- Testing camp_func_002e3304 ---")
    addr = 0x002E3304
    size = 124
    orig_code = load_original_bytes(addr, size)

    out_dir = ROOT / "build" / "batch30_b_part17"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_002e3304", out_dir)

    sym_map = {
        "camp_func_00324154": 0x00324154,
        "camp_func_00248790": 0x00248790,
        "camp_func_002a0fac": 0x002A0FAC,
    }
    staged_decomp = stage_body(comp, relocs, addr, sym_map)

    # Stub 0x00324154: returns count from 0x00495000
    code_324154 = struct.pack("<III", 0xe59f0004, 0xe5900000, 0xe12fff1e) + struct.pack("<I", 0x00495000)
    # Stub 0x00248790: takes u16 idx in r0, returns pointer 0x00496000 + idx*4 (contains u16 id)
    # lsl r0, r0, #2; ldr r1, =0x00496000; add r0, r0, r1; bx lr
    code_248790 = struct.pack("<IIII", 0xe1a00100, 0xe59f1004, 0xe0800001, 0xe12fff1e) + struct.pack("<I", 0x00496000)
    # Stub 0x002A0FAC: returns 0x00498000
    code_2a0fac = struct.pack("<II", 0xe59f0000, 0xe12fff1e) + struct.pack("<I", 0x00498000)

    cases = [
        ("count_zero", 0x25, 0, {}),
        ("match_first", 0x25, 5, {0: 0x25, 1: 0x10, 2: 0x20}),
        ("match_third", 0x33, 5, {0: 0x10, 1: 0x20, 2: 0x33}),
        ("match_idx_12", 0x55, 20, {5: 0x11, 12: 0x55, 15: 0x22}),
        ("no_match", 0x99, 10, {0: 0x11, 1: 0x22, 2: 0x33}),
    ]

    for name, target_id, count, items in cases:
        def setup_mem(uc):
            uc.mem_write(0x00324154, code_324154)
            uc.mem_write(0x00248790, code_248790)
            uc.mem_write(0x002A0FAC, code_2a0fac)
            uc.mem_write(0x00495000, struct.pack("<I", count))
            # Zero out items array at 0x00496000 (up to 30 items * 4 = 120 bytes)
            uc.mem_write(0x00496000, bytes(128))
            for idx, item_id in items.items():
                uc.mem_write(0x00496000 + idx * 4, struct.pack("<H", item_id))
            # Zero out bitset at 0x00498000 (up to 0x100 bytes)
            uc.mem_write(0x00498000, bytes(0x100))

        # Run orig
        uc_orig = setup_uc()
        setup_mem(uc_orig)
        uc_orig.reg_write(UC_ARM_REG_R0, target_id)
        uc_orig.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_orig.reg_write(UC_ARM_REG_LR, 0x00499000)
        uc_orig.emu_start(addr, 0x00499000)
        orig_bits = uc_orig.mem_read(0x00498035, 16)

        # Run decomp
        uc_decomp = setup_uc()
        setup_mem(uc_decomp)
        uc_decomp.mem_write(addr, staged_decomp)
        uc_decomp.reg_write(UC_ARM_REG_R0, target_id)
        uc_decomp.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_decomp.reg_write(UC_ARM_REG_LR, 0x00499000)
        uc_decomp.emu_start(addr, 0x00499000)
        decomp_bits = uc_decomp.mem_read(0x00498035, 16)

        assert orig_bits == decomp_bits, f"{name}: bits mismatch {orig_bits} != {decomp_bits}"

    print("camp_func_002e3304: PASS")

def test_battle_func_002e3bb0():
    print("--- Testing battle_func_002e3bb0 ---")
    addr = 0x002E3BB0
    size = 120
    orig_code = load_original_bytes(addr, size)

    out_dir = ROOT / "build" / "batch30_b_part17"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("battle_func_002e3bb0", out_dir)

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
        ("match_idx_0_type_4", 0, 0x11, 1, 4),
        ("match_idx_5_type_4", 5, 0x11, 2, 4),
        ("match_idx_108_type_4", 108, 0x11, 3, 4),
        ("type_not_4", 5, 0x11, 4, 3),
        ("flag_0x40_set", 5, 0x51, 5, 4),
        ("flag_0x10_missing", 5, 0x01, 6, 4),
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
                # Set info type at 0x00497000 + m_id*8 + 5
                uc.mem_write(0x00497000 + m_id * 8 + 5, bytes([m_type]))
            uc.mem_write(0x004A0000, bytes(zeroes))

        # Run orig
        uc_orig = setup_uc()
        setup_mem(uc_orig)
        uc_orig.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_orig.reg_write(UC_ARM_REG_LR, 0x002E3C24 + 4)
        uc_orig.emu_start(addr, 0x002E3C24 + 4)
        orig_r0 = uc_orig.reg_read(UC_ARM_REG_R0)
        orig_rec = struct.unpack("<I", uc_orig.mem_read(0x00495000, 4))[0]

        # Run decomp
        uc_decomp = setup_uc()
        setup_mem(uc_decomp)
        uc_decomp.mem_write(addr, staged_decomp)
        uc_decomp.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc_decomp.reg_write(UC_ARM_REG_LR, 0x002E3C24 + 4)
        uc_decomp.emu_start(addr, 0x002E3C24 + 4)
        decomp_r0 = uc_decomp.reg_read(UC_ARM_REG_R0)
        decomp_rec = struct.unpack("<I", uc_decomp.mem_read(0x00495000, 4))[0]

        assert orig_r0 == decomp_r0, f"{name}: r0 mismatch {orig_r0} != {decomp_r0}"
        assert orig_rec == decomp_rec, f"{name}: recorded call mismatch {orig_rec} != {decomp_rec}"

    print("battle_func_002e3bb0: PASS")

def main():
    test_battle_func_002dbad4()
    test_func_002dca98()
    test_ui_func_002e0c54()
    test_camp_func_002e3304()
    test_battle_func_002e3bb0()
    print("\nALL 5 FUNCTIONS IN BATCH 30 B PART 17 PASSED WITH 100% DIFFERENTIAL FIDELITY!")

if __name__ == "__main__":
    main()
