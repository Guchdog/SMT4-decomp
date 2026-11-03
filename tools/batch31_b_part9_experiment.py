#!/usr/bin/env python3
"""Differential test for batch 31 B part 9:
- func_003e6af4 (0x003E6AF4, 52 B)
- func_003f9044 (0x003F9044, 52 B)
- func_003e646c (0x003E646C, 56 B)
- camp_func_003ea4f8 (0x003EA4F8, 56 B)
- func_003d71c4 (0x003D71C4, 60 B)
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
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
    UC_ARM_REG_D0,
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
SOURCE = ROOT / "src/engine/leaf_batch31_b.cpp"

with open(ORIG_BIN, "rb") as f:
    ORIG_DATA = f.read()

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch31_b.o"
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

def hook_unmapped(uc, access, address, size, value, user_data):
    aligned = address & ~0xFFF
    try:
        uc.mem_map(aligned, 0x1000)
    except Exception:
        pass
    return True

def create_emulator():
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_unmapped)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, ORIG_DATA)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    try:
        val = uc.reg_read(UC_ARM_REG_C1_C0_2)
        uc.reg_write(UC_ARM_REG_C1_C0_2, val | (0xF << 20))
        uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    except Exception:
        pass
    return uc

def test_func_003e6af4():
    print("--- Testing func_003e6af4 (0x003e6af4) ---")
    addr = 0x003E6AF4
    orig_code = load_original_bytes(addr, 52)
    tmp = ROOT / "build" / "test_31b_part9"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003e6af4", tmp)

    sym_map = {"func_002a6d94": 0x002A6D94}
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, ret_ok, out_val):
        uc = create_emulator()
        uc.mem_write(addr, code)

        def stub_hook(uc, address, size, user_data):
            out_ptr = uc.reg_read(UC_ARM_REG_R1)
            uc.mem_write(out_ptr, struct.pack("<I", out_val))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_R0, 1 if ret_ok else 0)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, None, 0x002A6D94, 0x002A6D94)
        obj = 0x10082000
        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        return uc.reg_read(UC_ARM_REG_R0)

    for ret_ok, out_val, exp in [
        (True, 0x00000100, 1),
        (True, 0x12340178, 1),
        (True, 0x00000200, 0),
        (True, 0x00000000, 0),
        (False, 0x00000100, 0),
    ]:
        r_orig = run_one(orig_code, ret_ok, out_val)
        r_decomp = run_one(decomp_code, ret_ok, out_val)
        assert r_orig == exp and r_decomp == exp
    print("func_003e6af4: PASS")

def test_func_003f9044():
    print("--- Testing func_003f9044 (0x003f9044) ---")
    addr = 0x003F9044
    orig_code = load_original_bytes(addr, 52)
    tmp = ROOT / "build" / "test_31b_part9"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003f9044", tmp)

    sym_map = {"func_003f89f8": 0x003F89F8}
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, b1, b2, scale, base):
        uc = create_emulator()
        uc.mem_write(addr, code)
        data_addr = 0x10084000
        uc.mem_write(data_addr, bytes([0, b1, b2, 0]))

        def stub_hook(uc, address, size, user_data):
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_R0, data_addr)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, None, 0x003F89F8, 0x003F89F8)
        obj = 0x10082000
        uc.mem_write(obj + 8, struct.pack("<ff", scale, base))
        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        d0_raw = uc.reg_read(UC_ARM_REG_D0) & 0xFFFFFFFF
        return struct.unpack("<f", struct.pack("<I", d0_raw))[0]

    for b1, b2, scale, base in [
        (0, 0, 1.0, 0.0),
        (10, 0, 2.0, 5.0),
        (0xFF, 0x0F, 0.5, -10.0),
        (0x20, 0x34, 1.5, 100.0),
    ]:
        int_val = b1 | ((b2 & 0xF) << 8)
        expected = base + (int_val * scale)
        r_orig = run_one(orig_code, b1, b2, scale, base)
        r_decomp = run_one(decomp_code, b1, b2, scale, base)
        assert abs(r_orig - expected) < 1e-4 and abs(r_decomp - expected) < 1e-4
    print("func_003f9044: PASS")

def test_func_003e646c():
    print("--- Testing func_003e646c (0x003e646c) ---")
    addr = 0x003E646C
    orig_code = load_original_bytes(addr, 56)
    tmp = ROOT / "build" / "test_31b_part9"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003e646c", tmp)

    sym_map = {"func_002a6d94": 0x002A6D94}
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, ret_ok, off, inner_off):
        uc = create_emulator()
        uc.mem_write(addr, code)

        def stub_hook(uc, address, size, user_data):
            out_ptr = uc.reg_read(UC_ARM_REG_R1)
            uc.mem_write(out_ptr, struct.pack("<I", off))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_R0, 1 if ret_ok else 0)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, None, 0x002A6D94, 0x002A6D94)
        obj = 0x10082000
        if ret_ok:
            uc.mem_write(obj + off + 4, struct.pack("<I", inner_off))
        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        return uc.reg_read(UC_ARM_REG_R0)

    # When ret_ok == False -> returns 0x004765DD
    r_orig = run_one(orig_code, False, 0, 0)
    r_decomp = run_one(decomp_code, False, 0, 0)
    assert r_orig == 0x004765DD and r_decomp == 0x004765DD

    # When ret_ok == True -> returns obj + off + inner_off
    obj = 0x10082000
    r_orig = run_one(orig_code, True, 0x40, 0x10)
    r_decomp = run_one(decomp_code, True, 0x40, 0x10)
    assert r_orig == (obj + 0x40 + 0x10) and r_decomp == (obj + 0x40 + 0x10)
    print("func_003e646c: PASS")

def test_camp_func_003ea4f8():
    print("--- Testing camp_func_003ea4f8 (0x003ea4f8) ---")
    addr = 0x003EA4F8
    orig_code = load_original_bytes(addr, 56)
    tmp = ROOT / "build" / "test_31b_part9"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_003ea4f8", tmp)

    sym_map = {
        "Tbb_GetGlobalSubTable": 0x002C0EC4,
        "Tbb_GetPayloadData": 0x002C0E9C,
        "Tbb_GetRowCount": 0x002C0E4C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, sub_idx, entry_idx, row_count):
        uc = create_emulator()
        uc.mem_write(addr, code)
        fake_table = 0x10084000
        fake_payload = 0x10085000

        def stub_table(uc, address, size, user_data):
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_R0, fake_table)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_payload(uc, address, size, user_data):
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_R0, fake_payload)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_rows(uc, address, size, user_data):
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_R0, row_count)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_table, None, 0x002C0EC4, 0x002C0EC4)
        uc.hook_add(UC_HOOK_CODE, stub_payload, None, 0x002C0E9C, 0x002C0E9C)
        uc.hook_add(UC_HOOK_CODE, stub_rows, None, 0x002C0E4C, 0x002C0E4C)

        uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_R1, sub_idx)
        uc.reg_write(UC_ARM_REG_R2, entry_idx)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        return uc.reg_read(UC_ARM_REG_R0)

    fake_payload = 0x10085000
    for e_idx, rows, exp in [
        (0, 10, fake_payload),
        (5, 10, fake_payload + 5 * 32),
        (9, 10, fake_payload + 9 * 32),
        (10, 10, 0),
        (15, 10, 0),
    ]:
        r_orig = run_one(orig_code, 1, e_idx, rows)
        r_decomp = run_one(decomp_code, 1, e_idx, rows)
        assert r_orig == exp and r_decomp == exp
    print("camp_func_003ea4f8: PASS")

def test_func_003d71c4():
    print("--- Testing func_003d71c4 (0x003d71c4) ---")
    addr = 0x003D71C4
    orig_code = load_original_bytes(addr, 60)
    tmp = ROOT / "build" / "test_31b_part9"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_003d71c4", tmp)

    def run_one(code, initial_flags):
        uc = create_emulator()
        uc.mem_write(addr, code)
        obj = 0x10082000
        # Initialize
        uc.mem_write(obj + 0x738, struct.pack("<fff", 1.0, 2.0, 3.0))
        uc.mem_write(obj + 0x634, struct.pack("<I", initial_flags))
        uc.mem_write(obj + 0x764, struct.pack("<fff", 4.0, 5.0, 6.0))
        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        v1 = struct.unpack("<fff", uc.mem_read(obj + 0x738, 12))
        flags = struct.unpack("<I", uc.mem_read(obj + 0x634, 4))[0]
        v2 = struct.unpack("<fff", uc.mem_read(obj + 0x764, 12))
        return v1, flags, v2

    for fl in [0, 0x00800000, 0xFFFFFFFF, 0x12803456]:
        o_v1, o_fl, o_v2 = run_one(orig_code, fl)
        d_v1, d_fl, d_v2 = run_one(comp, fl)
        assert o_v1 == (0.0, 0.0, 0.0) and o_fl == (fl & ~0x00800000) and o_v2 == (0.0, 0.0, 0.0)
        assert d_v1 == (0.0, 0.0, 0.0) and d_fl == (fl & ~0x00800000) and d_v2 == (0.0, 0.0, 0.0)
    print("func_003d71c4: PASS")

def main():
    test_func_003e6af4()
    test_func_003f9044()
    test_func_003e646c()
    test_camp_func_003ea4f8()
    test_func_003d71c4()
    print("ALL BATCH 31 B PART 9 TESTS PASSED!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
