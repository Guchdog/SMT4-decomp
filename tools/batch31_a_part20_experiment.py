#!/usr/bin/env python3
"""Differential test for batch 31 A part 20:
- func_00360538 (0x00360538, 60 B)
- engine_func_00360574 (0x00360574, 60 B)
- func_003605b0 (0x003605B0, 60 B)
- func_0037e7f8 (0x0037E7F8, 60 B)
- func_0037fc8c (0x0037FC8C, 60 B)
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
    UC_HOOK_INTR,
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

def test_func_00360538():
    print("--- Testing func_00360538 ---")
    addr = 0x00360538
    size = 60
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part20"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00360538", tmp)

    sym_map = {
        "func_003608ec": 0x003608EC,
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
            if address == 0x003608EC:
                arg4 = struct.unpack("<I", uc.mem_read(sp, 4))[0]
                calls.append(("func_003608ec", r0, r1, r2, r3, arg4))
                uc.reg_write(UC_ARM_REG_R0, hret)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002BCE48:
                calls.append(("engine_func_002bce48", r0))
                uc.reg_write(UC_ARM_REG_R0, bce_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x003608EC, end=0x003608EC)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002BCE48, end=0x002BCE48)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, 1)
        uc.reg_write(UC_ARM_REG_R1, 2)
        uc.reg_write(UC_ARM_REG_R2, 3)
        uc.reg_write(UC_ARM_REG_R3, 4)
        uc.reg_write(UC_ARM_REG_LR, 0x00360000)

        uc.emu_start(addr, 0x00360000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x55),
        (5, 0x55),
        (-1, 0x99),
        (-10, 0x88),
    ]

    for hret, bceret in cases:
        r_orig, c_orig = run_one(orig_code, hret, bceret)
        r_decomp, c_decomp = run_one(decomp_code, hret, bceret)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("func_00360538: PASS")

def test_engine_func_00360574():
    print("--- Testing engine_func_00360574 ---")
    addr = 0x00360574
    size = 60
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part20"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_00360574", tmp)

    sym_map = {
        "func_003609e0": 0x003609E0,
        "engine_func_002bce48": 0x002BCE48,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, flag_val: int, handle_val: int, svc_ret: int, bce_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        uc.mem_write(0x00471BA8, bytes([flag_val]))
        arg_ptr = STACK_BASE + 0x1000
        uc.mem_write(arg_ptr, struct.pack("<I", handle_val))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x003609E0:
                calls.append(("func_003609e0",))
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002BCE48:
                calls.append(("engine_func_002bce48", r0))
                uc.reg_write(UC_ARM_REG_R0, bce_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x003609E0, end=0x003609E0)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002BCE48, end=0x002BCE48)

        # Hook svc instruction (0xef000023)
        def svc_hook(uc, address, size, user_data):
            inst = struct.unpack("<I", uc.mem_read(address, 4))[0]
            if inst == 0xEF000023:
                r0 = uc.reg_read(UC_ARM_REG_R0)
                calls.append(("svcCloseHandle", r0))
                uc.reg_write(UC_ARM_REG_R0, svc_ret)
                uc.reg_write(UC_ARM_REG_PC, address + 4)

        uc.hook_add(UC_HOOK_CODE, svc_hook)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x00360000)

        uc.emu_start(addr, 0x00360000, timeout=10000000)
        final_flag = uc.mem_read(0x00471BA8, 1)[0]
        return final_flag, calls

    cases = [
        (0, 0x1234, 0, 0x55),
        (1, 0x5678, 0, 0x55),
        (1, 0x9ABC, -1, 0x99),
    ]

    for fval, hval, sret, bceret in cases:
        ff_orig, c_orig = run_one(orig_code, fval, hval, sret, bceret)
        ff_decomp, c_decomp = run_one(decomp_code, fval, hval, sret, bceret)
        assert ff_orig == ff_decomp, f"flag mismatch: {ff_orig} vs {ff_decomp}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("engine_func_00360574: PASS")

def test_func_003605b0():
    print("--- Testing func_003605b0 ---")
    addr = 0x003605B0
    size = 60
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part20"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003605b0", tmp)

    sym_map = {
        "func_00360948": 0x00360948,
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
            if address == 0x00360948:
                arg4 = struct.unpack("<I", uc.mem_read(sp, 4))[0]
                calls.append(("func_00360948", r0, r1, r2, r3, arg4))
                uc.reg_write(UC_ARM_REG_R0, hret)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002BCE48:
                calls.append(("engine_func_002bce48", r0))
                uc.reg_write(UC_ARM_REG_R0, bce_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00360948, end=0x00360948)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002BCE48, end=0x002BCE48)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, 100)
        uc.reg_write(UC_ARM_REG_R1, 200)
        uc.reg_write(UC_ARM_REG_R2, 300)
        uc.reg_write(UC_ARM_REG_R3, 400)
        uc.reg_write(UC_ARM_REG_LR, 0x00360000)

        uc.emu_start(addr, 0x00360000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x55),
        (5, 0x55),
        (-1, 0x99),
        (-10, 0x88),
    ]

    for hret, bceret in cases:
        r_orig, c_orig = run_one(orig_code, hret, bceret)
        r_decomp, c_decomp = run_one(decomp_code, hret, bceret)
        assert r_orig == r_decomp, f"result mismatch: {hex(r_orig)} vs {hex(r_decomp)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("func_003605b0: PASS")

def test_func_0037e7f8():
    print("--- Testing func_0037e7f8 ---")
    addr = 0x0037E7F8
    size = 60
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part20"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0037e7f8", tmp)

    sym_map = {
        "func_00235dbc": 0x00235DBC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, has_sub: bool, c6_val: int, c5_val: int, a1_val: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        obj_ptr = STACK_BASE + 0x1000
        sub_ptr = STACK_BASE + 0x2000
        tgt_ptr = STACK_BASE + 0x5000

        uc.mem_write(obj_ptr + 0xE, b"\x00")
        if has_sub:
            uc.mem_write(obj_ptr + 0x98, struct.pack("<I", sub_ptr))
            uc.mem_write(sub_ptr + 0xC6, bytes([c6_val]))
            uc.mem_write(sub_ptr + 0xC5, bytes([c5_val]))
            uc.mem_write(sub_ptr + 0x134, struct.pack("<I", tgt_ptr))
        else:
            uc.mem_write(obj_ptr + 0x98, b"\x00\x00\x00\x00")

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00235DBC:
                calls.append(("func_00235dbc", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00235DBC, end=0x00235DBC)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, obj_ptr)
        uc.reg_write(UC_ARM_REG_R1, a1_val)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        obj_e = uc.mem_read(obj_ptr + 0xE, 1)[0]
        final_c5 = uc.mem_read(sub_ptr + 0xC5, 1)[0] if has_sub else 0
        return obj_e, final_c5, calls

    cases = [
        (False, 0, 0, 1),
        (True, 0, 0, 1),
        (True, 1, 1, 1),
        (True, 1, 0, 0),
        (True, 1, 0, 1),
        (True, 1, 1, 0),
    ]

    for hsub, c6, c5, a1 in cases:
        oe_orig, fc5_orig, c_orig = run_one(orig_code, hsub, c6, c5, a1)
        oe_decomp, fc5_decomp, c_decomp = run_one(decomp_code, hsub, c6, c5, a1)
        assert oe_orig == oe_decomp, f"obj_e mismatch: {oe_orig} vs {oe_decomp}"
        assert fc5_orig == fc5_decomp, f"final_c5 mismatch: {fc5_orig} vs {fc5_decomp}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("func_0037e7f8: PASS")

def test_func_0037fc8c():
    print("--- Testing func_0037fc8c ---")
    addr = 0x0037FC8C
    size = 60
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part20"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0037fc8c", tmp)

    sym_map = {
        "func_002a3428": 0x002A3428,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, a1_present: bool, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        arg0 = STACK_BASE + 0x1000
        arg1 = STACK_BASE + 0x2000
        vtable_ptr = STACK_BASE + 0x3000
        fn_ptr = 0x002C9990

        if a1_present:
            uc.mem_write(arg1, struct.pack("<I", vtable_ptr))
            uc.mem_write(vtable_ptr, struct.pack("<I", fn_ptr))
            uc.mem_write(arg1 + 0xC0, b"\xFF\xFF\xFF\xFF")

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == fn_ptr:
                calls.append(("vtable_fn", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002A3428:
                calls.append(("func_002a3428", r0, r1))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=fn_ptr, end=fn_ptr)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002A3428, end=0x002A3428)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1 if a1_present else 0)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        c0_val = struct.unpack("<I", uc.mem_read(arg1 + 0xC0, 4))[0] if a1_present else 0
        return c0_val, calls

    for a1_pres in [True]:
        c0_orig, c_orig = run_one(orig_code, a1_pres, 0x777)
        c0_decomp, c_decomp = run_one(decomp_code, a1_pres, 0x777)
        assert c0_orig == c0_decomp, f"c0 mismatch: {hex(c0_orig)} vs {hex(c0_decomp)}"
        assert c_orig == c_decomp, f"calls mismatch: {c_orig} vs {c_decomp}"
    print("func_0037fc8c: PASS")

if __name__ == "__main__":
    test_func_00360538()
    test_engine_func_00360574()
    test_func_003605b0()
    test_func_0037e7f8()
    test_func_0037fc8c()
    print("ALL PART 20 TESTS PASSED!")
