#!/usr/bin/env python3
"""Differential test for batch 31 A part 15:
- engine_func_003e0dbc (0x003E0DBC, 44 B)
- func_003619cc (0x003619CC, 48 B)
- script_vm_func_00361b7c (0x00361B7C, 48 B)
- ui_func_00384dc8 (0x00384DC8, 48 B)
- battle_func_00394c6c (0x00394C6C, 48 B)
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

def test_engine_func_003e0dbc():
    print("--- Testing engine_func_003e0dbc ---")
    addr = 0x003E0DBC
    size = 44
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part15"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_003e0dbc", tmp)

    sym_map = {
        "func_002c1a48": 0x002C1A48,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, a0: int, a1: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002C1A48:
                calls.append(("func_002c1a48", r0, r1, r2))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C1A48, end=0x002C1A48)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, a0)
        uc.reg_write(UC_ARM_REG_R1, a1)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)

        uc.emu_start(addr, 0x003E0000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0x11111111, 0, 0),
        (0x11111111, 0x22222222, 0),
        (0x11111111, 0x22222222, 1),
        (0x11111111, 0x22222222, 0x12345678),
    ]

    for a0, a1, hret in cases:
        r_orig, c_orig = run_one(orig_code, a0, a1, hret)
        r_decomp, c_decomp = run_one(decomp_code, a0, a1, hret)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)} for a1={hex(a1)}, hret={hex(hret)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("engine_func_003e0dbc: PASS")

def test_func_003619cc():
    print("--- Testing func_003619cc ---")
    addr = 0x003619CC
    size = 48
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part15"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003619cc", tmp)

    sym_map = {
        "func_002a8190": 0x002A8190,
        "engine_func_002bce48": 0x002BCE48,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, helper_ret: int, bce_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002A8190:
                calls.append(("func_002a8190", r0))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002BCE48:
                calls.append(("engine_func_002bce48", r0))
                uc.reg_write(UC_ARM_REG_R0, bce_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002A8190, end=0x002A8190)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002BCE48, end=0x002BCE48)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00360000)

        uc.emu_start(addr, 0x00360000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x77),
        (0x1234, 0x77),
        (0xC8A0CFFC, 0x77),
        (0xFFFFFFFF, 0x55),
        (0x80000000, 0x66),
        (0xE0E046BC, 0x88),
    ]

    for hret, bceret in cases:
        r_orig, c_orig = run_one(orig_code, hret, bceret)
        r_decomp, c_decomp = run_one(decomp_code, hret, bceret)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)} for hret={hex(hret)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("func_003619cc: PASS")

def test_script_vm_func_00361b7c():
    print("--- Testing script_vm_func_00361b7c ---")
    addr = 0x00361B7C
    size = 48
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part15"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_00361b7c", tmp)

    sym_map = {
        "func_002c1320": 0x002C1320,
        "engine_func_002bce48": 0x002BCE48,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, helper_ret: int, bce_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002C1320:
                calls.append(("func_002c1320", r0, r1))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002BCE48:
                calls.append(("engine_func_002bce48", r0))
                uc.reg_write(UC_ARM_REG_R0, bce_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C1320, end=0x002C1320)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002BCE48, end=0x002BCE48)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00360000)

        uc.emu_start(addr, 0x00360000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x77),
        (10, 0x77),
        (0xC8A0CFFC, 0x77),
        (0xFFFFFFFB, 0x55),
        (0x80000000, 0x66),
    ]

    for hret, bceret in cases:
        r_orig, c_orig = run_one(orig_code, hret, bceret)
        r_decomp, c_decomp = run_one(decomp_code, hret, bceret)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)} for hret={hex(hret)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("script_vm_func_00361b7c: PASS")

def test_ui_func_00384dc8():
    print("--- Testing ui_func_00384dc8 ---")
    addr = 0x00384DC8
    size = 48
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part15"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_00384dc8", tmp)

    sym_map = {
        "func_002c1b64": 0x002C1B64,
        "func_002c1abc": 0x002C1ABC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, val: int, abc_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        global_ptr = STACK_BASE + 0x2000
        obj_ptr = STACK_BASE + 0x3000
        # Write global at 0x0044EA00
        uc.mem_write(0x0044EA00, struct.pack("<I", obj_ptr))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002C1B64:
                calls.append(("func_002c1b64", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002C1ABC:
                calls.append(("func_002c1abc", r0))
                uc.reg_write(UC_ARM_REG_R0, abc_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C1B64, end=0x002C1B64)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C1ABC, end=0x002C1ABC)

        arg_struct = STACK_BASE + 0x1000
        uc.mem_write(arg_struct + 4, struct.pack("<i", val))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg_struct)
        uc.reg_write(UC_ARM_REG_LR, 0x00380000)

        uc.emu_start(addr, 0x00380000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x55),
        (1, 0x55),
        (2, 0x55),
        (-1, 0x55),
        (-100, 0x55),
        (3, 0x99),
        (100, 0xABC),
    ]

    for val, abc_ret in cases:
        r_orig, c_orig = run_one(orig_code, val, abc_ret)
        r_decomp, c_decomp = run_one(decomp_code, val, abc_ret)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)} for val={val}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("ui_func_00384dc8: PASS")

def test_battle_func_00394c6c():
    print("--- Testing battle_func_00394c6c ---")
    addr = 0x00394C6C
    size = 48
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part15"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("battle_func_00394c6c", tmp)

    sym_map = {
        "engine_func_002c583c": 0x002C583C,
        "func_002c1fa4": 0x002C1FA4,
        "func_002e1470": 0x002E1470,
        "func_001ffa64": 0x001FFA64,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, c583c_ret: int, ffa64_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002C583C:
                calls.append(("engine_func_002c583c", r0))
                uc.reg_write(UC_ARM_REG_R0, c583c_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002C1FA4:
                calls.append(("func_002c1fa4", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002E1470:
                calls.append(("func_002e1470", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x001FFA64:
                calls.append(("func_001ffa64",))
                uc.reg_write(UC_ARM_REG_R0, ffa64_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C583C, end=0x002C583C)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C1FA4, end=0x002C1FA4)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002E1470, end=0x002E1470)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x001FFA64, end=0x001FFA64)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00390000)

        uc.emu_start(addr, 0x00390000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (1, 0x123),
        (5, 0x123),
        (0, 0x777),
    ]

    for c583c_ret, ffa64_ret in cases:
        r_orig, c_orig = run_one(orig_code, c583c_ret, ffa64_ret)
        r_decomp, c_decomp = run_one(decomp_code, c583c_ret, ffa64_ret)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)} for c583c_ret={c583c_ret}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("battle_func_00394c6c: PASS")

if __name__ == "__main__":
    test_engine_func_003e0dbc()
    test_func_003619cc()
    test_script_vm_func_00361b7c()
    test_ui_func_00384dc8()
    test_battle_func_00394c6c()
    print("ALL PART 15 TESTS PASSED!")
