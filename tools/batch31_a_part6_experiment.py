#!/usr/bin/env python3
"""Differential test for batch 31 A part 6:
- func_00360cbc (0x00360CBC, 28 B)
- func_0037e7b0 (0x0037E7B0, 28 B)
- script_vm_func_0030f904 (0x0030F904, 32 B)
- func_00338638 (0x00338638, 32 B)
- func_00355fc0 (0x00355FC0, 32 B)
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
    UC_ARM_REG_S0,
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

def test_func_00360cbc():
    print("--- Testing func_00360cbc ---")
    addr = 0x00360CBC
    size = 28
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part6"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00360cbc", tmp)

    sym_map = {
        "func_00360c80": 0x00360C80,
        "engine_func_002bce48": 0x002BCE48,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, arg: int, stub_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00360C80:
                calls.append(("func_00360c80", r0))
                uc.reg_write(UC_ARM_REG_R0, stub_ret & 0xFFFFFFFF)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002BCE48:
                calls.append(("engine_func_002bce48", r0))
                uc.reg_write(UC_ARM_REG_R0, 0x55)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00360C80, end=0x00360C80)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002BCE48, end=0x002BCE48)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0),
        (1, 10),
        (0x1234, -1),
        (0x5678, -100),
        (0xABCD, 0x80000000),
        (0xDEAD, 0x7FFFFFFF),
    ]

    for arg, sret in cases:
        r1, c1 = run_one(orig_code, arg, sret)
        r2, c2 = run_one(decomp_code, arg, sret)
        assert r1 == r2, f"result mismatch: {r1} vs {r2} for arg={arg}, sret={sret}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for arg={arg}, sret={sret}"

    print("func_00360cbc: PASS")

def test_func_0037e7b0():
    print("--- Testing func_0037e7b0 ---")
    addr = 0x0037E7B0
    size = 28
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part6"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0037e7b0", tmp)

    sym_map = {
        "func_00235ddc": 0x00235DDC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, obj: int, mode: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00235DDC:
                calls.append(("func_00235ddc", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00235DDC, end=0x00235DDC)

        target_buf = STACK_BASE + 0x1000
        uc.mem_write(target_buf + 0x98, b"\xFF\xFF\xFF\xFF")

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_R1, mode)
        uc.reg_write(UC_ARM_REG_R2, target_buf)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        val = struct.unpack("<I", uc.mem_read(target_buf + 0x98, 4))[0]
        return res, val, calls

    cases = [
        (0x12345678, 2),
        (0x23456789, 0),
        (0x3456789A, 1),
        (0x456789AB, 3),
        (0x56789ABC, 2),
    ]

    for obj, mode in cases:
        r1, v1, c1 = run_one(orig_code, obj, mode)
        r2, v2, c2 = run_one(decomp_code, obj, mode)
        assert r1 == r2 == 0, f"res mismatch: {r1} vs {r2}"
        assert v1 == v2 == 0, f"target[0x98] mismatch: {v1} vs {v2}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for mode={mode}"

    print("func_0037e7b0: PASS")

def test_script_vm_func_0030f904():
    print("--- Testing script_vm_func_0030f904 ---")
    addr = 0x0030F904
    size = 32
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part6"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_0030f904", tmp)

    sym_map = {
        "ui_func_0039cb84": 0x0039CB84,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, obj_ptr: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x0039CB84:
                calls.append(("ui_func_0039cb84", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x0039CB84, end=0x0039CB84)

        # 0x0044CDF0 holds the pointer to obj
        uc.mem_write(0x0044CDF0, struct.pack("<I", obj_ptr))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        return calls

    cases = [
        0,
        0x10020000,
        0x10050000,
    ]

    for ptr in cases:
        c1 = run_one(orig_code, ptr)
        c2 = run_one(decomp_code, ptr)
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for ptr={hex(ptr)}"

    print("script_vm_func_0030f904: PASS")

def test_func_00338638():
    print("--- Testing func_00338638 ---")
    addr = 0x00338638
    size = 32
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part6"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00338638", tmp)

    sym_map = {
        "ui_func_0027fbbc": 0x0027FBBC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, sub_ptr: int, fval_ret: float):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x0027FBBC:
                calls.append(("ui_func_0027fbbc", r0))
                # Write float to s0
                fbytes = struct.pack("<f", fval_ret)
                fint = struct.unpack("<I", fbytes)[0]
                uc.reg_write(UC_ARM_REG_S0, fint)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x0027FBBC, end=0x0027FBBC)

        p = STACK_BASE + 0x2000
        uc.mem_write(p + 0x4394, struct.pack("<I", sub_ptr))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, p)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        s0 = uc.reg_read(UC_ARM_REG_S0)
        s0_bytes = struct.pack("<I", s0)
        res_float = struct.unpack("<f", s0_bytes)[0]
        return res_float, calls

    cases = [
        (0, 0.0),
        (STACK_BASE + 0x1000, 3.14159),
        (STACK_BASE + 0x1000, -42.5),
        (STACK_BASE + 0x1000, 100.0),
    ]

    for sub_ptr, fval in cases:
        r1, c1 = run_one(orig_code, sub_ptr, fval)
        r2, c2 = run_one(decomp_code, sub_ptr, fval)
        assert abs(r1 - r2) < 1e-5, f"float mismatch: {r1} vs {r2}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for sub_ptr={hex(sub_ptr)}"

    print("func_00338638: PASS")

def test_func_00355fc0():
    print("--- Testing func_00355fc0 ---")
    addr = 0x00355FC0
    size = 32
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part6"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00355fc0", tmp)

    sym_map = {}
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, self_ptr: int, method_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        method_target = 0x00290000
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == method_target:
                calls.append(("vtable_slot3", r0))
                uc.reg_write(UC_ARM_REG_R0, method_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=method_target, end=method_target)

        if self_ptr != 0:
            vtable_ptr = STACK_BASE + 0x2000
            # self points to vtable
            uc.mem_write(self_ptr, struct.pack("<I", vtable_ptr))
            # vtable[3] points to method_target
            uc.mem_write(vtable_ptr + 0xC, struct.pack("<I", method_target))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, self_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0),
        (STACK_BASE + 0x1000, 0x1234),
        (STACK_BASE + 0x1000, 0xCAFEBABE),
        (STACK_BASE + 0x1000, 0),
    ]

    for self_ptr, ret in cases:
        r1, c1 = run_one(orig_code, self_ptr, ret)
        r2, c2 = run_one(decomp_code, self_ptr, ret)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for self={hex(self_ptr)}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for self={hex(self_ptr)}"

    print("func_00355fc0: PASS")

if __name__ == "__main__":
    test_func_00360cbc()
    test_func_0037e7b0()
    test_script_vm_func_0030f904()
    test_func_00338638()
    test_func_00355fc0()
    print("\nALL 5 FUNCTIONS IN BATCH 31 A PART 6 PASSED WITH 100% DIFFERENTIAL FIDELITY!")
