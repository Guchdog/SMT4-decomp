#!/usr/bin/env python3
"""Differential test for batch 31 B part 5:
- func_003f6b2c (0x003F6B2C, 24 B)
- func_00379b14 (0x00379B14, 28 B)
- func_003f62d0 (0x003F62D0, 32 B)
- camp_func_0033c908 (0x0033C908, 36 B)
- func_003954a4 (0x003954A4, 36 B)
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
)
from unicorn.arm_const import (
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_R0,
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
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

def test_clear_static_func(name: str, addr: int, target_ptr: int, size: int):
    print(f"--- Testing {name} ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31b_part5"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function(name, tmp)

    def run_one(code):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.mem_write(target_ptr, struct.pack("<II", 0x11223344, 0x55667788))
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        w0, w1 = struct.unpack("<II", uc.mem_read(target_ptr, 8))
        return w0, w1

    orig_0, orig_1 = run_one(orig_code)
    decomp_0, decomp_1 = run_one(comp)
    assert orig_0 == 0 and orig_1 == 0, f"orig: {orig_0}, {orig_1}"
    assert decomp_0 == 0 and decomp_1 == 0, f"decomp: {decomp_0}, {decomp_1}"
    print(f"{name}: PASS")

def test_func_00379b14():
    print("--- Testing func_00379b14 (0x00379b14) ---")
    addr = 0x00379B14
    orig_code = load_original_bytes(addr, 28)
    tmp = ROOT / "build" / "test_31b_part5"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_00379b14", tmp)

    def run_one(code, test_float):
        uc = create_emulator()
        uc.mem_write(addr, code)
        obj_addr = 0x10082000
        uc.mem_write(obj_addr + 0xb0, struct.pack("<I", 0xDEADBEEF))
        uc.reg_write(UC_ARM_REG_R0, obj_addr)
        raw_int = struct.unpack("<I", struct.pack("<f", test_float))[0]
        uc.reg_write(UC_ARM_REG_D0, raw_int)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        f_out = struct.unpack("<f", uc.mem_read(obj_addr + 0xb0, 4))[0]
        return f_out

    for val in [-10.0, -0.5, 0.0, 1.5, 100.25]:
        orig_val = run_one(orig_code, val)
        decomp_val = run_one(comp, val)
        expected = max(0.0, val)
        assert abs(orig_val - expected) < 1e-5, f"val {val}: orig {orig_val} != {expected}"
        assert abs(decomp_val - expected) < 1e-5, f"val {val}: decomp {decomp_val} != {expected}"
    print("func_00379b14: PASS (max(0.0f, val))")

def test_camp_func_0033c908():
    print("--- Testing camp_func_0033c908 (0x0033c908) ---")
    addr = 0x0033C908
    orig_code = load_original_bytes(addr, 36)
    tmp = ROOT / "build" / "test_31b_part5"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("camp_func_0033c908", tmp)

    def run_one(code):
        uc = create_emulator()
        uc.mem_write(addr, code)
        obj_addr = 0x10082000
        uc.mem_write(obj_addr + 0x390, struct.pack("<IIIII", 1, 2, 3, 4, 5))
        uc.reg_write(UC_ARM_REG_R0, obj_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        words = struct.unpack("<IIIII", uc.mem_read(obj_addr + 0x390, 20))
        return words

    orig_words = run_one(orig_code)
    decomp_words = run_one(comp)
    assert orig_words == (0, 0, 0, 0, 0), f"orig: {orig_words}"
    assert decomp_words == (0, 0, 0, 0, 0), f"decomp: {decomp_words}"
    print("camp_func_0033c908: PASS")

def test_func_003954a4():
    print("--- Testing func_003954a4 (0x003954a4) ---")
    addr = 0x003954A4
    orig_code = load_original_bytes(addr, 36)
    tmp = ROOT / "build" / "test_31b_part5"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_003954a4", tmp)

    def run_one(code, flags):
        uc = create_emulator()
        uc.mem_write(addr, code)
        obj_addr = 0x10082000
        uc.mem_write(obj_addr + 0x70, struct.pack("<IIII", flags, 0x11111111, 0x22222222, 0x33333333))
        uc.reg_write(UC_ARM_REG_R0, obj_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        f_out, w1, w2, w3 = struct.unpack("<IIII", uc.mem_read(obj_addr + 0x70, 16))
        return f_out, (w1, w2, w3)

    for fl in [0, 1, 0xFF, 0x101]:
        o_fl, o_words = run_one(orig_code, fl)
        d_fl, d_words = run_one(comp, fl)
        assert o_fl == (fl & ~1) and o_words == (0, 0, 0), f"orig: {o_fl}, {o_words}"
        assert d_fl == (fl & ~1) and d_words == (0, 0, 0), f"decomp: {d_fl}, {d_words}"
    print("func_003954a4: PASS")

def main():
    test_clear_static_func("func_003f6b2c", 0x003F6B2C, 0x0044E990, 24)
    test_func_00379b14()
    test_clear_static_func("func_003f62d0", 0x003F62D0, 0x0044E960, 32)
    test_camp_func_0033c908()
    test_func_003954a4()
    print("ALL BATCH 31 B PART 5 TESTS PASSED!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
