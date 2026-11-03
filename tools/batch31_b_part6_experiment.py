#!/usr/bin/env python3
"""Differential test for batch 31 B part 6:
- engine_func_003d6610 (0x003D6610, 36 B)
- func_00302770 (0x00302770, 40 B)
- func_003f65e8 (0x003F65E8, 40 B)
- func_00376fb4 (0x00376FB4, 44 B)
- func_0037f7e0 (0x0037F7E0, 44 B)
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

def test_engine_func_003d6610():
    print("--- Testing engine_func_003d6610 (0x003d6610) ---")
    addr = 0x003D6610
    orig_code = load_original_bytes(addr, 36)
    tmp = ROOT / "build" / "test_31b_part6"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("engine_func_003d6610", tmp)

    def run_one(code):
        uc = create_emulator()
        uc.mem_write(addr, code)
        obj_addr = 0x10082000
        for i in range(8):
            uc.mem_write(obj_addr + i*4, struct.pack("<I", 0x41000000 + i))
        uc.reg_write(UC_ARM_REG_R0, obj_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        floats = struct.unpack("<6f", uc.mem_read(obj_addr + 0xc, 24))
        return floats

    orig_floats = run_one(orig_code)
    decomp_floats = run_one(comp)
    assert orig_floats == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    assert decomp_floats == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    print("engine_func_003d6610: PASS")

def test_func_00302770():
    print("--- Testing func_00302770 (0x00302770) ---")
    addr = 0x00302770
    orig_code = load_original_bytes(addr, 40)
    tmp = ROOT / "build" / "test_31b_part6"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_00302770", tmp)

    def run_one(code):
        uc = create_emulator()
        uc.mem_write(addr, code)
        dst_addr = 0x10082000
        src_addr = 0x10083000
        uc.mem_write(src_addr, struct.pack("<fff", 1.5, 2.5, 3.5))
        uc.reg_write(UC_ARM_REG_R0, dst_addr)
        uc.reg_write(UC_ARM_REG_R1, src_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        return struct.unpack("<ffff", uc.mem_read(dst_addr + 0x20, 16))

    orig_vals = run_one(orig_code)
    decomp_vals = run_one(comp)
    assert orig_vals == (1.5, 2.5, 3.5, 1.0)
    assert decomp_vals == (1.5, 2.5, 3.5, 1.0)
    print("func_00302770: PASS")

def test_func_003f65e8():
    print("--- Testing func_003f65e8 (0x003f65e8) ---")
    addr = 0x003F65E8
    orig_code = load_original_bytes(addr, 40)
    tmp = ROOT / "build" / "test_31b_part6"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_003f65e8", tmp)

    def run_one(code):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.mem_write(0x0044E978, struct.pack("<II", 0x11111111, 0x22222222))
        try:
            uc.mem_map(0x004D4000, 0x2000)
        except Exception:
            pass
        uc.mem_write(0x004D4674 + 8, struct.pack("<I", 0x12345678))
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        w0, w1 = struct.unpack("<II", uc.mem_read(0x0044E978, 8))
        w2 = struct.unpack("<I", uc.mem_read(0x004D4674 + 8, 4))[0]
        return (w0, w1, w2)

    orig_res = run_one(orig_code)
    decomp_res = run_one(comp)
    assert orig_res == (0, 0, 0xFFFFFFFF), f"orig: {orig_res}"
    assert decomp_res == (0, 0, 0xFFFFFFFF), f"decomp: {decomp_res}"
    print("func_003f65e8: PASS")

def test_func_00376fb4():
    print("--- Testing func_00376fb4 (0x00376fb4) ---")
    addr = 0x00376FB4
    orig_code = load_original_bytes(addr, 44)
    tmp = ROOT / "build" / "test_31b_part6"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_00376fb4", tmp)

    def run_one(code):
        uc = create_emulator()
        uc.mem_write(addr, code)
        obj_addr = 0x10082000
        uc.mem_write(obj_addr + 0x18, b"\xFF" * 20)
        uc.reg_write(UC_ARM_REG_R0, obj_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        w18, w1c, w20 = struct.unpack("<III", uc.mem_read(obj_addr + 0x18, 12))
        f24 = struct.unpack("<f", uc.mem_read(obj_addr + 0x24, 4))[0]
        b28, b29 = struct.unpack("<BB", uc.mem_read(obj_addr + 0x28, 2))
        return (w18, w1c, w20, f24, b28, b29)

    orig_res = run_one(orig_code)
    decomp_res = run_one(comp)
    assert orig_res == (0, 0, 0, 0.5, 1, 0), f"orig: {orig_res}"
    assert decomp_res == (0, 0, 0, 0.5, 1, 0), f"decomp: {decomp_res}"
    print("func_00376fb4: PASS")

def test_func_0037f7e0():
    print("--- Testing func_0037f7e0 (0x0037f7e0) ---")
    addr = 0x0037F7E0
    orig_code = load_original_bytes(addr, 44)
    tmp = ROOT / "build" / "test_31b_part6"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_0037f7e0", tmp)

    def run_one(code, obj_addr, idx):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.reg_write(UC_ARM_REG_R0, obj_addr)
        uc.reg_write(UC_ARM_REG_R1, idx)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        return uc.reg_read(UC_ARM_REG_R0)

    obj = 0x10082000
    for idx in [-5, 0, 5, 15, 16, 20, 31, 32, 50]:
        r_orig = run_one(orig_code, obj, idx)
        r_decomp = run_one(comp, obj, idx)
        assert r_orig == r_decomp, f"idx {idx}: orig {hex(r_orig)} != decomp {hex(r_decomp)}"
    print("func_0037f7e0: PASS")

def main():
    test_engine_func_003d6610()
    test_func_00302770()
    test_func_003f65e8()
    test_func_00376fb4()
    test_func_0037f7e0()
    print("ALL BATCH 31 B PART 6 TESTS PASSED!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
