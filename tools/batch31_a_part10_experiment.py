#!/usr/bin/env python3
"""Differential test for batch 31 A part 10:
- func_003e70a4 (0x003E70A4, 36 B)
- engine_func_00302674 (0x00302674, 40 B)
- ui_func_003408c4 (0x003408C4, 40 B)
- ui_func_0034752c (0x0034752C, 40 B)
- func_0034a1f0 (0x0034A1F0, 40 B)
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

def test_func_003e70a4():
    print("--- Testing func_003e70a4 ---")
    addr = 0x003E70A4
    size = 36
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part10"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003e70a4", tmp)

    sym_map = {
        "engine_func_003e71c4": 0x003E71C4,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, sub_ptr: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x003E71C4:
                calls.append(("engine_func_003e71c4", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x003E71C4, end=0x003E71C4)

        self_ptr = STACK_BASE + 0x1000
        uc.mem_write(self_ptr + 4, struct.pack("<I", sub_ptr))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, self_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        0,
        STACK_BASE + 0x2000,
        1,
    ]

    for sub_ptr in cases:
        r1, c1 = run_one(orig_code, sub_ptr)
        r2, c2 = run_one(decomp_code, sub_ptr)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for sub_ptr={hex(sub_ptr)}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for sub_ptr={hex(sub_ptr)}"

    print("func_003e70a4: PASS")

def test_engine_func_00302674():
    print("--- Testing engine_func_00302674 ---")
    addr = 0x00302674
    size = 40
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part10"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_00302674", tmp)

    sym_map = {
        "ui_func_00257390": 0x00257390,
        "effP2A_func_00249324": 0x00249324,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, old_val: int, new_arg: int, new_obj: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00257390:
                calls.append(("ui_func_00257390", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x00249324:
                calls.append(("effP2A_func_00249324", r0))
                uc.reg_write(UC_ARM_REG_R0, new_obj)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00257390, end=0x00257390)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00249324, end=0x00249324)

        self_ptr = STACK_BASE + 0x1000
        uc.mem_write(self_ptr + 0x44, struct.pack("<I", old_val))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, self_ptr)
        uc.reg_write(UC_ARM_REG_R1, new_arg)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        slot_val = struct.unpack("<I", uc.mem_read(self_ptr + 0x44, 4))[0]
        return slot_val, calls

    cases = [
        (0, 0x1234, 0x55555555),
        (STACK_BASE + 0x2000, 0x9999, 0x66666666),
    ]

    for old, new_arg, new_obj in cases:
        s1, c1 = run_one(orig_code, old, new_arg, new_obj)
        s2, c2 = run_one(decomp_code, old, new_arg, new_obj)
        assert s1 == s2 == new_obj, f"slot mismatch: {hex(s1)} vs {hex(s2)}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2}"

    print("engine_func_00302674: PASS")

def test_ui_func_003408c4():
    print("--- Testing ui_func_003408c4 ---")
    addr = 0x003408C4
    size = 40
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part10"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_003408c4", tmp)

    sym_map = {
        "ui_func_00380b4c": 0x00380B4C,
        "ui_func_002c5f58": 0x002C5F58,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, arg0: int, base_ret: int, res_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00380B4C:
                calls.append(("ui_func_00380b4c", r0))
                uc.reg_write(UC_ARM_REG_R0, base_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002C5F58:
                calls.append(("ui_func_002c5f58", r0, r1, r2, r3))
                uc.reg_write(UC_ARM_REG_R0, res_ret)
                # LR for blx has bit 0 set or clear; mask off bit 0 to return to ARM
                uc.reg_write(UC_ARM_REG_PC, lr & ~1)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00380B4C, end=0x00380B4C)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C5F58, end=0x002C5F58)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0x10, STACK_BASE + 0x1000, STACK_BASE + 0x2000),
        (0x20, STACK_BASE + 0x3000, STACK_BASE + 0x4000),
    ]

    for arg0, base_ret, res_ret in cases:
        r1, c1 = run_one(orig_code, arg0, base_ret, res_ret)
        r2, c2 = run_one(decomp_code, arg0, base_ret, res_ret)
        assert r1 == r2 == (res_ret - 0x20), f"result mismatch: {hex(r1)} vs {hex(r2)}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2}"

    print("ui_func_003408c4: PASS")

def test_ui_func_0034752c():
    print("--- Testing ui_func_0034752c ---")
    addr = 0x0034752C
    size = 40
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part10"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_0034752c", tmp)

    sym_map = {
        "ui_func_00380b4c": 0x00380B4C,
        "ui_func_002c5f58": 0x002C5F58,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, arg0: int, base_ret: int, res_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00380B4C:
                calls.append(("ui_func_00380b4c", r0))
                uc.reg_write(UC_ARM_REG_R0, base_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002C5F58:
                calls.append(("ui_func_002c5f58", r0, r1, r2, r3))
                uc.reg_write(UC_ARM_REG_R0, res_ret)
                uc.reg_write(UC_ARM_REG_PC, lr & ~1)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00380B4C, end=0x00380B4C)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C5F58, end=0x002C5F58)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0x10, STACK_BASE + 0x1000, STACK_BASE + 0x2000),
        (0x20, STACK_BASE + 0x3000, STACK_BASE + 0x4000),
    ]

    for arg0, base_ret, res_ret in cases:
        r1, c1 = run_one(orig_code, arg0, base_ret, res_ret)
        r2, c2 = run_one(decomp_code, arg0, base_ret, res_ret)
        assert r1 == r2 == (res_ret - 0x20), f"result mismatch: {hex(r1)} vs {hex(r2)}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2}"

    print("ui_func_0034752c: PASS")

def test_func_0034a1f0():
    print("--- Testing func_0034a1f0 ---")
    addr = 0x0034A1F0
    size = 40
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part10"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0034a1f0", tmp)

    sym_map = {
        "func_0034a138": 0x0034A138,
        "engine_func_002b2520": 0x002B2520,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, self_ptr: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x0034A138:
                calls.append(("func_0034a138", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002B2520:
                calls.append(("engine_func_002b2520", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x0034A138, end=0x0034A138)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002B2520, end=0x002B2520)

        uc.mem_write(self_ptr, b"\x00\x00\x00\x00")

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, self_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        vtable_val = struct.unpack("<I", uc.mem_read(self_ptr, 4))[0]
        return vtable_val, calls

    cases = [
        STACK_BASE + 0x1000,
        STACK_BASE + 0x2000,
    ]

    for self_ptr in cases:
        v1, c1 = run_one(orig_code, self_ptr)
        v2, c2 = run_one(decomp_code, self_ptr)
        assert v1 == v2 == 0x00420514, f"vtable mismatch: {hex(v1)} vs {hex(v2)}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2}"

    print("func_0034a1f0: PASS")

if __name__ == "__main__":
    test_func_003e70a4()
    test_engine_func_00302674()
    test_ui_func_003408c4()
    test_ui_func_0034752c()
    test_func_0034a1f0()
    print("\nALL 5 FUNCTIONS IN BATCH 31 A PART 10 PASSED WITH 100% DIFFERENTIAL FIDELITY!")
