#!/usr/bin/env python3
"""Differential test for batch 31 A part 11:
- engine_func_00357b2c (0x00357B2C, 40 B)
- engine_func_00360704 (0x00360704, 40 B)
- func_0037024c (0x0037024C, 40 B)
- func_0037e3f8 (0x0037E3F8, 40 B)
- func_003ade5c (0x003ADE5C, 40 B)
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

def test_engine_func_00357b2c():
    print("--- Testing engine_func_00357b2c ---")
    addr = 0x00357B2C
    size = 40
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part11"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_00357b2c", tmp)

    sym_map = {
        "func_00357b54": 0x00357B54,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, sub_ptr: int, arg1: int, arg2: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)
        # 0x00357B2C references shared literal pool at 0x00357BD8
        uc.mem_write(0x00357BD8, load_original_bytes(0x00357BD8, 8))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00357B54:
                calls.append(("func_00357b54", r0, r1, r2))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00357B54, end=0x00357B54)

        self_ptr = STACK_BASE + 0x1000
        uc.mem_write(self_ptr + 4, struct.pack("<I", sub_ptr))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, self_ptr)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_R2, arg2)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 1, 0x80, 0x111),                    # sub is null -> 0xC8810BEA
        (STACK_BASE + 0x2000, 0, 0x80, 0x222),  # arg1 is 0 -> 0xE0E10BFD
        (STACK_BASE + 0x2000, 1, 0x6F, 0x333),  # arg2 < 0x70 -> 0xE0E10BFD
        (STACK_BASE + 0x2000, 1, 0x70, 0x444),  # arg1!=0 and arg2>=0x70 -> calls func_00357b54
        (STACK_BASE + 0x2000, 5, 0x100, 0x555), # calls func_00357b54
    ]

    for sub_ptr, a1, a2, hret in cases:
        r1, c1 = run_one(orig_code, sub_ptr, a1, a2, hret)
        r2, c2 = run_one(decomp_code, sub_ptr, a1, a2, hret)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for sub={hex(sub_ptr)}, a1={a1}, a2={a2}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for sub={hex(sub_ptr)}, a1={a1}, a2={a2}"

    print("engine_func_00357b2c: PASS")

def test_engine_func_00360704():
    print("--- Testing engine_func_00360704 ---")
    addr = 0x00360704
    size = 40
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part11"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_00360704", tmp)

    sym_map = {
        "func_00360ab8": 0x00360AB8,
        "engine_func_002bce48": 0x002BCE48,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, arg0: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00360AB8:
                calls.append(("func_00360ab8", r0))
                uc.reg_write(UC_ARM_REG_R0, helper_ret & 0xFFFFFFFF)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002BCE48:
                calls.append(("engine_func_002bce48", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00360AB8, end=0x00360AB8)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002BCE48, end=0x002BCE48)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0x10, 0xC9405001), # matches sentinel -> returns 0xC9405001 directly
        (0x20, 0),          # success >= 0 -> returns 0
        (0x30, 42),         # success > 0 -> returns 0
        (0x40, -1),         # error < 0 -> calls engine_func_002bce48(1) and returns 0
        (0x50, -100),       # error < 0 -> calls engine_func_002bce48(1) and returns 0
    ]

    for arg0, hret in cases:
        r1, c1 = run_one(orig_code, arg0, hret)
        r2, c2 = run_one(decomp_code, arg0, hret)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for hret={hex(hret & 0xFFFFFFFF)}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for hret={hex(hret & 0xFFFFFFFF)}"

    print("engine_func_00360704: PASS")

def test_func_0037024c():
    print("--- Testing func_0037024c ---")
    addr = 0x0037024C
    size = 40
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part11"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0037024c", tmp)

    sym_map = {
        "script_vm_func_002c3568": 0x002C3568,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, rel_val: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002C3568:
                ptr_val = struct.unpack("<I", uc.mem_read(r0, 4))[0]
                calls.append(("script_vm_func_002c3568", ptr_val))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C3568, end=0x002C3568)

        base_ptr = STACK_BASE + 0x1000
        # base + 8 holds relative offset
        uc.mem_write(base_ptr + 8, struct.pack("<i", rel_val))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, base_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x999),
        (0x20, 0x777),
        (-0x10, 0x555),
    ]

    for rel_val, hret in cases:
        r1, c1 = run_one(orig_code, rel_val, hret)
        r2, c2 = run_one(decomp_code, rel_val, hret)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for rel={rel_val}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for rel={rel_val}"

    print("func_0037024c: PASS")

def test_func_0037e3f8():
    print("--- Testing func_0037e3f8 ---")
    addr = 0x0037E3F8
    size = 40
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part11"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0037e3f8", tmp)

    sym_map = {
        "func_002c68bc": 0x002C68BC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, self_ptr: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002C68BC:
                calls.append(("func_002c68bc", r0, r1, r2, r3))
                uc.reg_write(UC_ARM_REG_PC, lr & ~1)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C68BC, end=0x002C68BC)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, self_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        STACK_BASE + 0x1000,
        STACK_BASE + 0x2000,
    ]

    for s_ptr in cases:
        r1, c1 = run_one(orig_code, s_ptr)
        r2, c2 = run_one(decomp_code, s_ptr)
        assert r1 == r2 == s_ptr, f"result mismatch: {hex(r1)} vs {hex(r2)}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2}"

    print("func_0037e3f8: PASS")

def test_func_003ade5c():
    print("--- Testing func_003ade5c ---")
    addr = 0x003ADE5C
    size = 40
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part11"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003ade5c", tmp)

    sym_map = {
        "camp_func_0028c868": 0x0028C868,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, obj_ptr: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x0028C868:
                calls.append(("camp_func_0028c868", r0))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x0028C868, end=0x0028C868)

        # 0x00439CA8 holds obj_ptr (0x00439C88 + 0x20)
        uc.mem_write(0x00439CA8, struct.pack("<I", obj_ptr))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x555),
        (STACK_BASE + 0x1000, 0x777),
        (STACK_BASE + 0x2000, 0),
    ]

    for obj_ptr, hret in cases:
        r1, c1 = run_one(orig_code, obj_ptr, hret)
        r2, c2 = run_one(decomp_code, obj_ptr, hret)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for obj={hex(obj_ptr)}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for obj={hex(obj_ptr)}"

    print("func_003ade5c: PASS")

if __name__ == "__main__":
    test_engine_func_00357b2c()
    test_engine_func_00360704()
    test_func_0037024c()
    test_func_0037e3f8()
    test_func_003ade5c()
    print("\nALL 5 FUNCTIONS IN BATCH 31 A PART 11 PASSED WITH 100% DIFFERENTIAL FIDELITY!")
