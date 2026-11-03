#!/usr/bin/env python3
"""Differential test for batch 31 B part 1:
- func_003e4eb0 (0x003E4EB0, 12 B)
- func_003e5194 (0x003E5194, 12 B)
- func_003e51a8 (0x003E51A8, 12 B)
- func_003e5224 (0x003E5224, 12 B)
- func_003e6024 (0x003E6024, 12 B)
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

def load_original_bytes(addr: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(addr - CODE_BASE)
        return f.read(size)

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
    uc.mem_map(STACK_BASE, STACK_SIZE)
    try:
        val = uc.reg_read(UC_ARM_REG_C1_C0_2)
        uc.reg_write(UC_ARM_REG_C1_C0_2, val | (0xF << 20))
        uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    except Exception:
        pass
    return uc

def test_getter(func_name: str, addr: int, expected_val: int):
    print(f"--- Testing {func_name} ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 12)

    tmp = ROOT / "build" / "test_31b_part1"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function(func_name, tmp)

    def run_one(code: bytes):
        uc = create_emulator()
        uc.mem_write(addr, code)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)

        uc.emu_start(addr, 0x003E0000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res

    r_orig = run_one(orig_code)
    r_decomp = run_one(comp)
    assert r_orig == expected_val, f"orig mismatch: {hex(r_orig)} vs {hex(expected_val)}"
    assert r_decomp == expected_val, f"decomp mismatch: {hex(r_decomp)} vs {hex(expected_val)}"
    print(f"{func_name}: PASS ({hex(r_decomp)})")

if __name__ == "__main__":
    test_getter("func_003e4eb0", 0x003E4EB0, 0x0044E870)
    test_getter("func_003e5194", 0x003E5194, 0x00472140)
    test_getter("func_003e51a8", 0x003E51A8, 0x00472238)
    test_getter("func_003e5224", 0x003E5224, 0x004722A0)
    test_getter("func_003e6024", 0x003E6024, 0x00472030)
    print("ALL BATCH 31 B PART 1 TESTS PASSED!")
