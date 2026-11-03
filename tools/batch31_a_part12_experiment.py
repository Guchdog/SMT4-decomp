#!/usr/bin/env python3
"""Differential test for batch 31 A part 12:
- engine_func_003d7200 (0x003D7200, 40 B)
- engine_func_003d9fa0 (0x003D9FA0, 40 B)
- func_003e72fc (0x003E72FC, 40 B)
- ui_func_0033534c (0x0033534C, 44 B)
- func_003489e8 (0x003489E8, 44 B)
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

def test_engine_func_003d7200():
    print("--- Testing engine_func_003d7200 ---")
    addr = 0x003D7200
    size = 40
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part12"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_003d7200", tmp)

    sym_map = {
        "script_vm_func_00297704": 0x00297704,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, flag_val: int, arg1: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00297704:
                calls.append(("script_vm_func_00297704", r0, r1, r2))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00297704, end=0x00297704)

        arg0 = STACK_BASE + 0x1000
        uc.mem_write(arg0 + 0x730, struct.pack("<I", flag_val))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x42, 0x999),
        (STACK_BASE + 0x2000, 0x42, 0x999),
        (0, 0x100, 0x555),
    ]

    for flag, a1, hret in cases:
        r1, c1 = run_one(orig_code, flag, a1, hret)
        r2, c2 = run_one(decomp_code, flag, a1, hret)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for flag={hex(flag)}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for flag={hex(flag)}"

    print("engine_func_003d7200: PASS")

def test_engine_func_003d9fa0():
    print("--- Testing engine_func_003d9fa0 ---")
    addr = 0x003D9FA0
    size = 40
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part12"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_003d9fa0", tmp)

    sym_map = {
        "AsdMemory_func_002c23f8": 0x002C23F8,
        "engine_func_0034a444": 0x0034A444,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, alloc_ret: int, ctor_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002C23F8:
                calls.append(("AsdMemory_func_002c23f8", r0))
                uc.reg_write(UC_ARM_REG_R0, alloc_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x0034A444:
                calls.append(("engine_func_0034a444", r0))
                uc.reg_write(UC_ARM_REG_R0, ctor_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C23F8, end=0x002C23F8)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x0034A444, end=0x0034A444)

        self_ptr = STACK_BASE + 0x1000
        uc.mem_write(self_ptr + 0x1CF8, b"\x00\x00\x00\x00")

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, self_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        stored_val = struct.unpack("<I", uc.mem_read(self_ptr + 0x1CF8, 4))[0]
        return stored_val, calls

    cases = [
        (0, 0),
        (STACK_BASE + 0x2000, STACK_BASE + 0x2000),
    ]

    for aret, cret in cases:
        s1, c1 = run_one(orig_code, aret, cret)
        s2, c2 = run_one(decomp_code, aret, cret)
        assert s1 == s2 == cret, f"stored val mismatch: {hex(s1)} vs {hex(s2)}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2}"

    print("engine_func_003d9fa0: PASS")

def test_func_003e72fc():
    print("--- Testing func_003e72fc ---")
    addr = 0x003E72FC
    size = 40
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part12"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003e72fc", tmp)

    sym_map = {
        "func_002a6d58": 0x002A6D58,
        "func_003e6b28": 0x003E6B28,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, d58_ret: int, b28_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002A6D58:
                calls.append(("func_002a6d58", r0))
                uc.reg_write(UC_ARM_REG_R0, d58_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x003E6B28:
                calls.append(("func_003e6b28",))
                uc.reg_write(UC_ARM_REG_R0, b28_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002A6D58, end=0x002A6D58)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x003E6B28, end=0x003E6B28)

        arg0 = STACK_BASE + 0x1000
        sub_ptr = STACK_BASE + 0x2000
        target_ptr = STACK_BASE + 0x3000

        uc.mem_write(arg0 + 4, struct.pack("<I", sub_ptr))
        uc.mem_write(sub_ptr + 0x3C, struct.pack("<I", target_ptr))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x999),
        (1, 0x777),
        (0x42, 0x555),
    ]

    for dret, bret in cases:
        r1, c1 = run_one(orig_code, dret, bret)
        r2, c2 = run_one(decomp_code, dret, bret)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for dret={dret}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for dret={dret}"

    print("func_003e72fc: PASS")

def test_ui_func_0033534c():
    print("--- Testing ui_func_0033534c ---")
    addr = 0x0033534C
    size = 44
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part12"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_0033534c", tmp)

    sym_map = {
        "func_0020fe7c": 0x0020FE7C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, sub2_val: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x0020FE7C:
                calls.append(("func_0020fe7c", r0))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x0020FE7C, end=0x0020FE7C)

        arg0 = STACK_BASE + 0x1000
        sub1 = STACK_BASE + 0x2000

        uc.mem_write(arg0 + 8, struct.pack("<I", sub1))
        uc.mem_write(sub1 + 8, struct.pack("<I", sub2_val))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (STACK_BASE + 0x3000, 0x123),
        (0x42, 0x456),
    ]

    for s2, hret in cases:
        r1, c1 = run_one(orig_code, s2, hret)
        r2, c2 = run_one(decomp_code, s2, hret)
        assert r1 == r2 == hret, f"result mismatch: {hex(r1)} vs {hex(r2)}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2}"

    print("ui_func_0033534c: PASS")

def test_func_003489e8():
    print("--- Testing func_003489e8 ---")
    addr = 0x003489E8
    size = 44
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part12"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003489e8", tmp)

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

    print("func_003489e8: PASS")

if __name__ == "__main__":
    test_engine_func_003d7200()
    test_engine_func_003d9fa0()
    test_func_003e72fc()
    test_ui_func_0033534c()
    test_func_003489e8()
    print("\nALL 5 FUNCTIONS IN BATCH 31 A PART 12 PASSED WITH 100% DIFFERENTIAL FIDELITY!")
