#!/usr/bin/env python3
"""Differential test for batch 31 B part 4:
- script_vm_func_0035a270 (0x0035A270, 24 B)
- func_00380420 (0x00380420, 24 B)
- func_003f59f0 (0x003F59F0, 24 B)
- func_003f5dc8 (0x003F5DC8, 24 B)
- func_003f61d8 (0x003F61D8, 24 B)
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
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
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

def test_script_vm_func_0035a270():
    print("--- Testing script_vm_func_0035a270 (0x0035a270) ---")
    addr = 0x0035A270
    orig_code = load_original_bytes(addr, 24)
    tmp = ROOT / "build" / "test_31b_part4"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("script_vm_func_0035a270", tmp)

    def run_one(code, idx):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.reg_write(UC_ARM_REG_R0, idx)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        return uc.reg_read(UC_ARM_REG_R0)

    for idx in range(15):
        r_orig = run_one(orig_code, idx)
        r_decomp = run_one(comp, idx)
        assert r_orig == r_decomp, f"idx {idx}: orig {hex(r_orig)} != decomp {hex(r_decomp)}"
    print("script_vm_func_0035a270: PASS")

def test_func_00380420():
    print("--- Testing func_00380420 (0x00380420) ---")
    addr = 0x00380420
    orig_code = load_original_bytes(addr, 24)
    tmp = ROOT / "build" / "test_31b_part4"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_00380420", tmp)

    def run_one(code):
        uc = create_emulator()
        uc.mem_write(addr, code)
        obj_addr = 0x10082000
        uc.mem_write(obj_addr + 0x10, struct.pack("<I", 0xDEADBEEF))
        uc.mem_write(obj_addr + 0x14, struct.pack("<I", 0xCAFEBABE))
        uc.reg_write(UC_ARM_REG_R0, obj_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        w10 = struct.unpack("<I", uc.mem_read(obj_addr + 0x10, 4))[0]
        w14 = struct.unpack("<I", uc.mem_read(obj_addr + 0x14, 4))[0]
        return w10, w14

    orig_10, orig_14 = run_one(orig_code)
    decomp_10, decomp_14 = run_one(comp)
    assert orig_10 == 0 and orig_14 == 0, f"orig: {orig_10}, {orig_14}"
    assert decomp_10 == 0 and decomp_14 == 0, f"decomp: {decomp_10}, {decomp_14}"
    print("func_00380420: PASS")

def test_clear_static_func(name: str, addr: int, target_ptr: int):
    print(f"--- Testing {name} ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 24)
    tmp = ROOT / "build" / "test_31b_part4"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function(name, tmp)

    def run_one(code):
        uc = create_emulator()
        uc.mem_write(addr, code)
        # Ensure target_ptr is mapped and written
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

def main():
    test_script_vm_func_0035a270()
    test_func_00380420()
    test_clear_static_func("func_003f59f0", 0x003F59F0, 0x0044E918)
    test_clear_static_func("func_003f5dc8", 0x003F5DC8, 0x0044E930)
    test_clear_static_func("func_003f61d8", 0x003F61D8, 0x0044E948)
    print("ALL BATCH 31 B PART 4 TESTS PASSED!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
