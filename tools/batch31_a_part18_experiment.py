#!/usr/bin/env python3
"""Differential test for batch 31 A part 18:
- func_00337558 (0x00337558, 60 B)
- ui_func_00338988 (0x00338988, 60 B)
- func_00359088 (0x00359088, 60 B)
- nn_sdk_func_003591e4 (0x003591E4, 60 B)
- func_00359288 (0x00359288, 60 B)
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

def test_func_00337558():
    print("--- Testing func_00337558 ---")
    addr = 0x00337558
    size = 60
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part18"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00337558", tmp)

    sym_map = {
        "battle_func_002931cc": 0x002931CC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, flag_a0: int, flag_a8: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        obj_ptr = STACK_BASE + 0x1000
        uc.mem_write(obj_ptr + 0x44A0, struct.pack("<I", flag_a0))
        uc.mem_write(obj_ptr + 0x44A8, struct.pack("<I", flag_a8))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002931CC:
                calls.append(("battle_func_002931cc", r0))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002931CC, end=0x002931CC)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, obj_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x00330000)

        uc.emu_start(addr, 0x00330000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0x40, 0, 0x99),
        (0x40, 0x20000, 0x99),
        (0, 0x20000, 0x99),
        (0, 0, 0x777),
        (0x10, 0x10, 0x888),
    ]

    for fa0, fa8, hret in cases:
        r_orig, c_orig = run_one(orig_code, fa0, fa8, hret)
        r_decomp, c_decomp = run_one(decomp_code, fa0, fa8, hret)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("func_00337558: PASS")

def test_ui_func_00338988():
    print("--- Testing ui_func_00338988 ---")
    addr = 0x00338988
    size = 60
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part18"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_00338988", tmp)

    sym_map = {
        "ui_func_00288990": 0x00288990,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, has_sub: bool):
        uc = create_emulator()
        uc.mem_write(addr, code)

        obj_ptr = STACK_BASE + 0x1000
        sub_ptr = STACK_BASE + 0x6000
        vtable_ptr = STACK_BASE + 0x7000
        dtor_ptr = 0x002C9990

        if has_sub:
            uc.mem_write(obj_ptr + 0x4394, struct.pack("<I", sub_ptr))
            uc.mem_write(sub_ptr, struct.pack("<I", vtable_ptr))
            uc.mem_write(vtable_ptr + 4, struct.pack("<I", dtor_ptr))
        else:
            uc.mem_write(obj_ptr + 0x4394, b"\x00\x00\x00\x00")

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00288990:
                calls.append(("ui_func_00288990", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == dtor_ptr:
                calls.append(("dtor", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00288990, end=0x00288990)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=dtor_ptr, end=dtor_ptr)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, obj_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x00330000)

        uc.emu_start(addr, 0x00330000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        final_slot = struct.unpack("<I", uc.mem_read(obj_ptr + 0x4394, 4))[0]
        return res, final_slot, calls

    for has_sub in [False, True]:
        r_orig, s_orig, c_orig = run_one(orig_code, has_sub)
        r_decomp, s_decomp, c_decomp = run_one(decomp_code, has_sub)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)}"
        assert s_orig == s_decomp, f"slot mismatch: {hex(s_orig)} vs {hex(s_decomp)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("ui_func_00338988: PASS")

def test_func_00359088():
    print("--- Testing func_00359088 ---")
    addr = 0x00359088
    size = 60
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part18"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00359088", tmp)

    sym_map = {
        "func_003597bc": 0x003597BC,
        "func_00359344": 0x00359344,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, p_4c: int, p_48: int, a0: int, hret_bc: int, hret_44: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        uc.mem_write(0x0047384C, struct.pack("<I", p_4c))
        uc.mem_write(0x00473848, struct.pack("<I", p_48))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x003597BC:
                calls.append(("func_003597bc", r0))
                uc.reg_write(UC_ARM_REG_R0, hret_bc)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x00359344:
                calls.append(("func_00359344", r0))
                uc.reg_write(UC_ARM_REG_R0, hret_44)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x003597BC, end=0x003597BC)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00359344, end=0x00359344)

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

    for p4c, p48, a0, hbc, h44 in cases:
        r_orig, c_orig = run_one(orig_code, p4c, p48, a0, hbc, h44)
        r_decomp, c_decomp = run_one(decomp_code, p4c, p48, a0, hbc, h44)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("func_00359088: PASS")

def test_nn_sdk_func_003591e4():
    print("--- Testing nn_sdk_func_003591e4 ---")
    addr = 0x003591E4
    size = 60
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part18"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("nn_sdk_func_003591e4", tmp)

    sym_map = {
        "nn_sdk_func_002c1570": 0x002C1570,
        "engine_func_002c3290": 0x002C3290,
        "nn_sdk_func_002c153c": 0x002C153C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, ret_570: int, ret_290: int, ret_53c: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002C1570:
                calls.append(("nn_sdk_func_002c1570",))
                uc.reg_write(UC_ARM_REG_R0, ret_570)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002C3290:
                calls.append(("engine_func_002c3290", r0))
                uc.reg_write(UC_ARM_REG_R0, ret_290)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002C153C:
                calls.append(("nn_sdk_func_002c153c", r0, r1, r2, r3))
                uc.reg_write(UC_ARM_REG_R0, ret_53c)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C1570, end=0x002C1570)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C3290, end=0x002C3290)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C153C, end=0x002C153C)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00350000)

        uc.emu_start(addr, 0x00350000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (-1, 0x10, 0x77),
        (-500, 0x10, 0x77),
        (0, 0x20, 0x88),
        (1, 0x30, 0x99),
    ]

    for r570, r290, r53c in cases:
        r_orig, c_orig = run_one(orig_code, r570, r290, r53c)
        r_decomp, c_decomp = run_one(decomp_code, r570, r290, r53c)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("nn_sdk_func_003591e4: PASS")

def test_func_00359288():
    print("--- Testing func_00359288 ---")
    addr = 0x00359288
    size = 60
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part18"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00359288", tmp)

    sym_map = {
        "func_00359940": 0x00359940,
        "func_003594c8": 0x003594C8,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, p_4c: int, p_48: int, a0: int, hret_40: int, hret_c8: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        uc.mem_write(0x0047384C, struct.pack("<I", p_4c))
        uc.mem_write(0x00473848, struct.pack("<I", p_48))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00359940:
                calls.append(("func_00359940", r0))
                uc.reg_write(UC_ARM_REG_R0, hret_40)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x003594C8:
                calls.append(("func_003594c8", r0))
                uc.reg_write(UC_ARM_REG_R0, hret_c8)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00359940, end=0x00359940)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x003594C8, end=0x003594C8)

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

    for p4c, p48, a0, h40, hc8 in cases:
        r_orig, c_orig = run_one(orig_code, p4c, p48, a0, h40, hc8)
        r_decomp, c_decomp = run_one(decomp_code, p4c, p48, a0, h40, hc8)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("func_00359288: PASS")

if __name__ == "__main__":
    test_func_00337558()
    test_ui_func_00338988()
    test_func_00359088()
    test_nn_sdk_func_003591e4()
    test_func_00359288()
    print("ALL PART 18 TESTS PASSED!")
