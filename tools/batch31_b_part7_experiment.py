#!/usr/bin/env python3
"""Differential test for batch 31 B part 7:
- nn_sdk_func_003f5a3c (0x003F5A3C, 44 B)
- nn_sdk_func_003f5e08 (0x003F5E08, 44 B)
- nn_sdk_func_003f6c40 (0x003F6C40, 44 B)
- func_003e0df8 (0x003E0DF8, 48 B)
- func_003e0e7c (0x003E0E7C, 48 B)
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

def test_setter(name: str, addr: int, target_ptr: int):
    print(f"--- Testing {name} ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 44)
    tmp = ROOT / "build" / "test_31b_part7"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function(name, tmp)

    def run_one(code, a0, a1):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.mem_write(target_ptr, b"\x00" * 8)
        uc.reg_write(UC_ARM_REG_R0, a0)
        uc.reg_write(UC_ARM_REG_R1, a1)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        r0 = uc.reg_read(UC_ARM_REG_R0)
        mem = struct.unpack("<II", uc.mem_read(target_ptr, 8))
        return r0, mem

    for v0, v1 in [(0x12345678, 0x9ABCDEF0), (0, 0), (0xFFFFFFFF, 1)]:
        o_r0, o_mem = run_one(orig_code, v0, v1)
        d_r0, d_mem = run_one(comp, v0, v1)
        assert o_r0 == target_ptr and o_mem == (v0, v1), f"orig: {hex(o_r0)} != {hex(target_ptr)}"
        assert d_r0 == target_ptr and d_mem == (v0, v1), f"decomp: {hex(d_r0)} != {hex(target_ptr)}" 
    print(f"{name}: PASS")

def test_span_extractor(name: str, addr: int, err_code: int):
    print(f"--- Testing {name} ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 48)
    tmp = ROOT / "build" / "test_31b_part7"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function(name, tmp)

    def run_one(code, byte_len):
        uc = create_emulator()
        uc.mem_write(addr, code)
        range_addr = 0x10082000
        out_addr = 0x10083000
        start_ptr = 0x10084000
        end_ptr = start_ptr + byte_len
        uc.mem_write(range_addr, struct.pack("<II", start_ptr, end_ptr))
        uc.mem_write(out_addr, struct.pack("<II", 0xDEADBEEF, 0xCAFEBABE))
        uc.reg_write(UC_ARM_REG_R0, range_addr)
        uc.reg_write(UC_ARM_REG_R1, out_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        r0 = uc.reg_read(UC_ARM_REG_R0)
        out_mem = struct.unpack("<II", uc.mem_read(out_addr, 8))
        return r0, out_mem

    # Count <= 256 elements (byte_len <= 512):
    for num_elem in [0, 1, 10, 256]:
        byte_len = num_elem * 2
        o_r0, o_mem = run_one(orig_code, byte_len)
        d_r0, d_mem = run_one(comp, byte_len)
        assert o_r0 == 0 and o_mem == (num_elem, 0x10084000), f"orig: {o_r0}, {o_mem}"
        assert d_r0 == 0 and d_mem == (num_elem, 0x10084000), f"decomp: {d_r0}, {d_mem}"

    # Count > 256 elements (byte_len > 512):
    for num_elem in [257, 500, 1000]:
        byte_len = num_elem * 2
        o_r0, o_mem = run_one(orig_code, byte_len)
        d_r0, d_mem = run_one(comp, byte_len)
        assert o_r0 == err_code, f"orig: {hex(o_r0)} != {hex(err_code)}"
        assert d_r0 == err_code, f"decomp: {hex(d_r0)} != {hex(err_code)}"
    print(f"{name}: PASS")

def main():
    test_setter("nn_sdk_func_003f5a3c", 0x003F5A3C, 0x0044E918)
    test_setter("nn_sdk_func_003f5e08", 0x003F5E08, 0x0044E930)
    test_setter("nn_sdk_func_003f6c40", 0x003F6C40, 0x0044E990)
    test_span_extractor("func_003e0df8", 0x003E0DF8, 0xE0E046C7)
    test_span_extractor("func_003e0e7c", 0x003E0E7C, 0xE0E046C8)
    print("ALL BATCH 31 B PART 7 TESTS PASSED!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
