#!/usr/bin/env python3
"""Differential test for batch 31 A part 19:
- func_003596c4 (0x003596C4, 60 B)
- func_00359700 (0x00359700, 60 B)
- func_00359b94 (0x00359B94, 60 B)
- func_003604c0 (0x003604C0, 60 B)
- func_003604fc (0x003604FC, 60 B)
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
    UC_ARM_REG_R3,
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
SOURCE = ROOT / "src/engine/leaf_batch31_a.cpp"

def load_original_bytes(addr: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(addr - CODE_BASE)
        return f.read(size)

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch31_a.o"
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
    uc.mem_map(STACK_BASE, STACK_SIZE)
    try:
        val = uc.reg_read(UC_ARM_REG_C1_C0_2)
        uc.reg_write(UC_ARM_REG_C1_C0_2, val | (0xF << 20))
        uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    except Exception:
        pass
    return uc

def test_func_003596c4():
    print("--- Testing func_003596c4 ---")
    addr = 0x003596C4
    size = 60
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part19"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003596c4", tmp)

    sym_map = {
        "func_0035997c": 0x0035997C,
        "func_00359504": 0x00359504,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, p_4c: int, p_48: int, a0: int, hret_7c: int, hret_04: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        uc.mem_write(0x0047384C, struct.pack("<I", p_4c))
        uc.mem_write(0x00473848, struct.pack("<I", p_48))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x0035997C:
                calls.append(("func_0035997c", r0))
                uc.reg_write(UC_ARM_REG_R0, hret_7c)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x00359504:
                calls.append(("func_00359504", r0))
                uc.reg_write(UC_ARM_REG_R0, hret_04)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x0035997C, end=0x0035997C)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00359504, end=0x00359504)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, a0)
        uc.reg_write(UC_ARM_REG_LR, 0x00350000)

        uc.emu_start(addr, 0x00350000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0x1000, 0, 0x123, 0xAAA, 0xBBB),
        (0x1000, 0x2000, 0x123, 0xAAA, 0xBBB),
        (0, 0x2000, 0x456, 0xAAA, 0xBBB),
        (0, 0, 0x789, 0xAAA, 0xBBB),
    ]

    for p4c, p48, a0, h7c, h04 in cases:
        r_orig, c_orig = run_one(orig_code, p4c, p48, a0, h7c, h04)
        r_decomp, c_decomp = run_one(decomp_code, p4c, p48, a0, h7c, h04)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("func_003596c4: PASS")

def test_func_00359700():
    print("--- Testing func_00359700 ---")
    addr = 0x00359700
    size = 60
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part19"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00359700", tmp)

    sym_map = {
        "func_00359a04": 0x00359A04,
        "func_0035958c": 0x0035958C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, p_4c: int, p_48: int, a0: int, hret_04: int, hret_8c: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        uc.mem_write(0x0047384C, struct.pack("<I", p_4c))
        uc.mem_write(0x00473848, struct.pack("<I", p_48))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00359A04:
                calls.append(("func_00359a04", r0))
                uc.reg_write(UC_ARM_REG_R0, hret_04)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x0035958C:
                calls.append(("func_0035958c", r0))
                uc.reg_write(UC_ARM_REG_R0, hret_8c)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00359A04, end=0x00359A04)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x0035958C, end=0x0035958C)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, a0)
        uc.reg_write(UC_ARM_REG_LR, 0x00350000)

        uc.emu_start(addr, 0x00350000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0x1000, 0, 0x123, 0xAAA, 0xBBB),
        (0x1000, 0x2000, 0x123, 0xAAA, 0xBBB),
        (0, 0x2000, 0x456, 0xAAA, 0xBBB),
        (0, 0, 0x789, 0xAAA, 0xBBB),
    ]

    for p4c, p48, a0, h04, h8c in cases:
        r_orig, c_orig = run_one(orig_code, p4c, p48, a0, h04, h8c)
        r_decomp, c_decomp = run_one(decomp_code, p4c, p48, a0, h04, h8c)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("func_00359700: PASS")

def test_func_00359b94():
    print("--- Testing func_00359b94 ---")
    addr = 0x00359B94
    size = 60
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part19"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00359b94", tmp)

    sym_map = {
        "func_00359a98": 0x00359A98,
        "func_00359620": 0x00359620,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, p_4c: int, p_48: int, a0: int, hret_98: int, hret_20: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        uc.mem_write(0x0047384C, struct.pack("<I", p_4c))
        uc.mem_write(0x00473848, struct.pack("<I", p_48))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00359A98:
                calls.append(("func_00359a98", r0))
                uc.reg_write(UC_ARM_REG_R0, hret_98)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x00359620:
                calls.append(("func_00359620", r0))
                uc.reg_write(UC_ARM_REG_R0, hret_20)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00359A98, end=0x00359A98)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00359620, end=0x00359620)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, a0)
        uc.reg_write(UC_ARM_REG_LR, 0x00350000)

        uc.emu_start(addr, 0x00350000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0x1000, 0, 0x123, 0xAAA, 0xBBB),
        (0x1000, 0x2000, 0x123, 0xAAA, 0xBBB),
        (0, 0x2000, 0x456, 0xAAA, 0xBBB),
        (0, 0, 0x789, 0xAAA, 0xBBB),
    ]

    for p4c, p48, a0, h98, h20 in cases:
        r_orig, c_orig = run_one(orig_code, p4c, p48, a0, h98, h20)
        r_decomp, c_decomp = run_one(decomp_code, p4c, p48, a0, h98, h20)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("func_00359b94: PASS")

def test_func_003604c0():
    print("--- Testing func_003604c0 ---")
    addr = 0x003604C0
    size = 60
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part19"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003604c0", tmp)

    sym_map = {
        "func_00360834": 0x00360834,
        "engine_func_002bce48": 0x002BCE48,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, hret: int, bce_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        obj_ptr = STACK_BASE + 0x2000
        uc.mem_write(0x0040B6F0, struct.pack("<I", obj_ptr))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            sp = uc.reg_read(UC_ARM_REG_SP)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00360834:
                arg4 = struct.unpack("<I", uc.mem_read(sp, 4))[0]
                calls.append(("func_00360834", r0, r1, r2, r3, arg4))
                uc.reg_write(UC_ARM_REG_R0, hret)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002BCE48:
                calls.append(("engine_func_002bce48", r0))
                uc.reg_write(UC_ARM_REG_R0, bce_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00360834, end=0x00360834)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002BCE48, end=0x002BCE48)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, 10)
        uc.reg_write(UC_ARM_REG_R1, 20)
        uc.reg_write(UC_ARM_REG_R2, 30)
        uc.reg_write(UC_ARM_REG_R3, 40)
        uc.reg_write(UC_ARM_REG_LR, 0x00360000)

        uc.emu_start(addr, 0x00360000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x55),
        (10, 0x55),
        (-1, 0x99),
        (-50, 0x88),
    ]

    for hret, bceret in cases:
        r_orig, c_orig = run_one(orig_code, hret, bceret)
        r_decomp, c_decomp = run_one(decomp_code, hret, bceret)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("func_003604c0: PASS")

def test_func_003604fc():
    print("--- Testing func_003604fc ---")
    addr = 0x003604FC
    size = 60
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part19"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003604fc", tmp)

    sym_map = {
        "func_00360890": 0x00360890,
        "engine_func_002bce48": 0x002BCE48,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, hret: int, bce_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        obj_ptr = STACK_BASE + 0x2000
        uc.mem_write(0x0040B6F0, struct.pack("<I", obj_ptr))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            sp = uc.reg_read(UC_ARM_REG_SP)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00360890:
                arg4 = struct.unpack("<I", uc.mem_read(sp, 4))[0]
                calls.append(("func_00360890", r0, r1, r2, r3, arg4))
                uc.reg_write(UC_ARM_REG_R0, hret)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002BCE48:
                calls.append(("engine_func_002bce48", r0))
                uc.reg_write(UC_ARM_REG_R0, bce_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00360890, end=0x00360890)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002BCE48, end=0x002BCE48)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, 10)
        uc.reg_write(UC_ARM_REG_R1, 20)
        uc.reg_write(UC_ARM_REG_R2, 30)
        uc.reg_write(UC_ARM_REG_R3, 40)
        uc.reg_write(UC_ARM_REG_LR, 0x00360000)

        uc.emu_start(addr, 0x00360000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x55),
        (10, 0x55),
        (-1, 0x99),
        (-50, 0x88),
    ]

    for hret, bceret in cases:
        r_orig, c_orig = run_one(orig_code, hret, bceret)
        r_decomp, c_decomp = run_one(decomp_code, hret, bceret)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("func_003604fc: PASS")

if __name__ == "__main__":
    test_func_003596c4()
    test_func_00359700()
    test_func_00359b94()
    test_func_003604c0()
    test_func_003604fc()
    print("ALL PART 19 TESTS PASSED!")
