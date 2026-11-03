#!/usr/bin/env python3
"""Differential test for batch 31 A part 8:
- camp_func_0030f5ec (0x0030F5EC, 36 B)
- func_00357698 (0x00357698, 36 B)
- func_00359184 (0x00359184, 36 B)
- func_0035bb24 (0x0035BB24, 36 B)
- func_0035bb74 (0x0035BB74, 36 B)
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

def test_camp_func_0030f5ec():
    print("--- Testing camp_func_0030f5ec ---")
    addr = 0x0030F5EC
    size = 36
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part8"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_0030f5ec", tmp)

    sym_map = {
        "func_002cbfcc": 0x002CBFCC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, arg0: int, obj_ptr: int, flag_byte: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002CBFCC:
                calls.append(("func_002cbfcc", r0))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002CBFCC, end=0x002CBFCC)

        # 0x00447E28 holds obj_ptr
        uc.mem_write(0x00447E28, struct.pack("<I", obj_ptr))
        if obj_ptr != 0:
            uc.mem_write(obj_ptr + 0x3C, bytes([flag_byte & 0xFF]))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0x1234, 0, 0, 0x999),
        (0x5678, STACK_BASE + 0x1000, 0, 0x999),
        (0xABCD, STACK_BASE + 0x1000, 1, 0x777),
        (0xCAFE, STACK_BASE + 0x1000, 0xFF, 0x555),
    ]

    for arg0, obj_ptr, flag, hret in cases:
        r1, c1 = run_one(orig_code, arg0, obj_ptr, flag, hret)
        r2, c2 = run_one(decomp_code, arg0, obj_ptr, flag, hret)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for arg0={hex(arg0)}, flag={flag}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for flag={flag}"

    print("camp_func_0030f5ec: PASS")

def test_func_00357698():
    print("--- Testing func_00357698 ---")
    addr = 0x00357698
    size = 36
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part8"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00357698", tmp)

    sym_map = {
        "engine_func_00155bd8": 0x00155BD8,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, obj_offset8_val: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00155BD8:
                calls.append(("engine_func_00155bd8", r0, r1))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00155BD8, end=0x00155BD8)

        obj = STACK_BASE + 0x1000
        uc.mem_write(obj + 8, struct.pack("<I", obj_offset8_val))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x888),
        (STACK_BASE + 0x2000, 0x1234),
        (0x1, 0xCAFE),
    ]

    for off8, hret in cases:
        r1, c1 = run_one(orig_code, off8, hret)
        r2, c2 = run_one(decomp_code, off8, hret)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for off8={hex(off8)}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for off8={hex(off8)}"

    print("func_00357698: PASS")

def test_func_00359184():
    print("--- Testing func_00359184 ---")
    addr = 0x00359184
    size = 36
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part8"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00359184", tmp)

    sym_map = {
        "func_0015f740": 0x0015F740,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, obj_ptr: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x0015F740:
                calls.append(("func_0015f740", r0))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x0015F740, end=0x0015F740)

        # 0x00473848 holds obj_ptr
        uc.mem_write(0x00473848, struct.pack("<I", obj_ptr))

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

    print("func_00359184: PASS")

def test_func_0035bb24():
    print("--- Testing func_0035bb24 ---")
    addr = 0x0035BB24
    size = 36
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part8"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0035bb24", tmp)

    sym_map = {
        "func_0035c048": 0x0035C048,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, cur: int, max_val: int, arg1: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x0035C048:
                calls.append(("func_0035c048", r0, r1, r2))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x0035C048, end=0x0035C048)

        self_ptr = STACK_BASE + 0x1000
        uc.mem_write(self_ptr + 0x10, struct.pack("<II", cur, max_val))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, self_ptr)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        new_cur = struct.unpack("<I", uc.mem_read(self_ptr + 0x10, 4))[0]
        return res, new_cur, calls

    cases = [
        (0, 1, 0x12, 0x999),   # cur+1 == 1 == max -> returns 6, no call
        (2, 5, 0x34, 0x888),   # cur+1 == 3 != 5 -> calls func_0035c048(self, 0x34, 4)
        (4, 5, 0x56, 0x777),   # cur+1 == 5 == max -> returns 6, no call
        (9, 5, 0x78, 0x666),   # cur+1 == 10 != 5 -> calls helper
    ]

    for cur, max_val, arg1, hret in cases:
        r1, nc1, c1 = run_one(orig_code, cur, max_val, arg1, hret)
        r2, nc2, c2 = run_one(decomp_code, cur, max_val, arg1, hret)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for cur={cur}, max={max_val}"
        assert nc1 == nc2 == cur + 1, f"new cur mismatch: {nc1} vs {nc2}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for cur={cur}, max={max_val}"

    print("func_0035bb24: PASS")

def test_func_0035bb74():
    print("--- Testing func_0035bb74 ---")
    addr = 0x0035BB74
    size = 36
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part8"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0035bb74", tmp)

    sym_map = {
        "func_0035c048": 0x0035C048,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, cur: int, max_val: int, arg1: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x0035C048:
                calls.append(("func_0035c048", r0, r1, r2))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x0035C048, end=0x0035C048)

        self_ptr = STACK_BASE + 0x1000
        uc.mem_write(self_ptr + 0x10, struct.pack("<II", cur, max_val))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, self_ptr)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        new_cur = struct.unpack("<I", uc.mem_read(self_ptr + 0x10, 4))[0]
        return res, new_cur, calls

    cases = [
        (0, 1, 0x12, 0x999),   # cur+1 == 1 == max -> returns 6, no call
        (2, 5, 0x34, 0x888),   # cur+1 == 3 != 5 -> calls func_0035c048(self, 0x34, 2)
        (4, 5, 0x56, 0x777),   # cur+1 == 5 == max -> returns 6, no call
        (9, 5, 0x78, 0x666),   # cur+1 == 10 != 5 -> calls helper
    ]

    for cur, max_val, arg1, hret in cases:
        r1, nc1, c1 = run_one(orig_code, cur, max_val, arg1, hret)
        r2, nc2, c2 = run_one(decomp_code, cur, max_val, arg1, hret)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for cur={cur}, max={max_val}"
        assert nc1 == nc2 == cur + 1, f"new cur mismatch: {nc1} vs {nc2}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for cur={cur}, max={max_val}"

    print("func_0035bb74: PASS")

if __name__ == "__main__":
    test_camp_func_0030f5ec()
    test_func_00357698()
    test_func_00359184()
    test_func_0035bb24()
    test_func_0035bb74()
    print("\nALL 5 FUNCTIONS IN BATCH 31 A PART 8 PASSED WITH 100% DIFFERENTIAL FIDELITY!")
