#!/usr/bin/env python3
"""Differential test for batch 31 B part 3:
- func_003e6134 (0x003E6134, 12 B)
- func_003bcfc8 (0x003BCFC8, 16 B)
- func_003409d4 (0x003409D4, 24 B)
- func_00348ac0 (0x00348AC0, 24 B)
- script_vm_func_0035a220 (0x0035A220, 24 B)
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
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
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
    # Map read-only original binary data for tables (like 0x00465768)
    uc.mem_write(CODE_BASE, ORIG_DATA)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    try:
        val = uc.reg_read(UC_ARM_REG_C1_C0_2)
        uc.reg_write(UC_ARM_REG_C1_C0_2, val | (0xF << 20))
        uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    except Exception:
        pass
    return uc

def test_func_003e6134():
    print("--- Testing func_003e6134 (0x003e6134) ---")
    addr = 0x003E6134
    orig_code = load_original_bytes(addr, 12)
    tmp = ROOT / "build" / "test_31b_part3"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_003e6134", tmp)

    def run_one(code):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        return uc.reg_read(UC_ARM_REG_R0)

    r_orig = run_one(orig_code)
    r_decomp = run_one(comp)
    assert r_orig == 0x0044E858, f"orig: {hex(r_orig)}"
    assert r_decomp == 0x0044E858, f"decomp: {hex(r_decomp)}"
    print("func_003e6134: PASS (0x0044E858)")

def test_func_003bcfc8():
    print("--- Testing func_003bcfc8 (0x003bcfc8) ---")
    addr = 0x003BCFC8
    orig_code = load_original_bytes(addr, 16)
    tmp = ROOT / "build" / "test_31b_part3"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_003bcfc8", tmp)

    def run_one(code, test_float):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        # Put float in s0 (lower 32 bits of d0)
        raw_int = struct.unpack("<I", struct.pack("<f", test_float))[0]
        uc.reg_write(UC_ARM_REG_D0, raw_int)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        d0_out = uc.reg_read(UC_ARM_REG_D0) & 0xFFFFFFFF
        return struct.unpack("<f", struct.pack("<I", d0_out))[0]

    for val in [0.0, 1.0, 2.0, -4.0, 10.5]:
        r_orig = run_one(orig_code, val)
        r_decomp = run_one(comp, val)
        assert abs(r_orig - val * 1.25) < 1e-5, f"orig: {r_orig} != {val * 1.25}"
        assert abs(r_decomp - r_orig) < 1e-5, f"decomp: {r_decomp} != {r_orig}"
    print("func_003bcfc8: PASS (val * 1.25f)")

def test_func_003409d4():
    print("--- Testing func_003409d4 (0x003409d4) ---")
    addr = 0x003409D4
    orig_code = load_original_bytes(addr, 24)
    tmp = ROOT / "build" / "test_31b_part3"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_003409d4", tmp)

    def run_one(code):
        uc = create_emulator()
        uc.mem_write(addr, code)
        obj_addr = 0x10082000
        # Initialize memory with sentinel values
        uc.mem_write(obj_addr + 4, struct.pack("<I", 0xDEADBEEF))
        uc.mem_write(obj_addr + 8, struct.pack("<I", 0xCAFEBABE))
        uc.reg_write(UC_ARM_REG_R0, obj_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        w4 = struct.unpack("<I", uc.mem_read(obj_addr + 4, 4))[0]
        w8 = struct.unpack("<I", uc.mem_read(obj_addr + 8, 4))[0]
        return w4, w8

    orig_4, orig_8 = run_one(orig_code)
    decomp_4, decomp_8 = run_one(comp)
    assert orig_4 == 0 and orig_8 == 0, f"orig: {orig_4}, {orig_8}"
    assert decomp_4 == 0 and decomp_8 == 0, f"decomp: {decomp_4}, {decomp_8}"
    print("func_003409d4: PASS")

def test_func_00348ac0():
    print("--- Testing func_00348ac0 (0x00348ac0) ---")
    addr = 0x00348AC0
    orig_code = load_original_bytes(addr, 24)
    tmp = ROOT / "build" / "test_31b_part3"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_00348ac0", tmp)

    def run_one(code):
        uc = create_emulator()
        uc.mem_write(addr, code)
        obj_addr = 0x10082000
        uc.mem_write(obj_addr + 4, struct.pack("<I", 0xDEADBEEF))
        uc.mem_write(obj_addr + 8, struct.pack("<I", 0xCAFEBABE))
        uc.reg_write(UC_ARM_REG_R0, obj_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        w4 = struct.unpack("<I", uc.mem_read(obj_addr + 4, 4))[0]
        f8 = struct.unpack("<f", uc.mem_read(obj_addr + 8, 4))[0]
        return w4, f8

    orig_4, orig_8 = run_one(orig_code)
    decomp_4, decomp_8 = run_one(comp)
    assert orig_4 == 0 and orig_8 == 1.0, f"orig: {orig_4}, {orig_8}"
    assert decomp_4 == 0 and decomp_8 == 1.0, f"decomp: {decomp_4}, {decomp_8}"
    print("func_00348ac0: PASS")

def test_script_vm_func_0035a220():
    print("--- Testing script_vm_func_0035a220 (0x0035a220) ---")
    addr = 0x0035A220
    orig_code = load_original_bytes(addr, 24)
    tmp = ROOT / "build" / "test_31b_part3"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("script_vm_func_0035a220", tmp)

    def run_one(code, idx):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.reg_write(UC_ARM_REG_R0, idx)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        return uc.reg_read(UC_ARM_REG_R0)

    for idx in range(10):
        r_orig = run_one(orig_code, idx)
        r_decomp = run_one(comp, idx)
        assert r_orig == r_decomp, f"idx {idx}: orig {hex(r_orig)} != decomp {hex(r_decomp)}"
    print("script_vm_func_0035a220: PASS")

def main():
    test_func_003e6134()
    test_func_003bcfc8()
    test_func_003409d4()
    test_func_00348ac0()
    test_script_vm_func_0035a220()
    print("ALL BATCH 31 B PART 3 TESTS PASSED!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
