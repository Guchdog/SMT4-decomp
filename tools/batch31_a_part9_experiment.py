#!/usr/bin/env python3
"""Differential test for batch 31 A part 9:
- func_0037a3fc (0x0037A3FC, 36 B)
- script_vm_func_0039f834 (0x0039F834, 36 B)
- func_003af184 (0x003AF184, 36 B)
- func_003e7038 (0x003E7038, 36 B)
- func_003e7080 (0x003E7080, 36 B)
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

def test_func_0037a3fc():
    print("--- Testing func_0037a3fc ---")
    addr = 0x0037A3FC
    size = 36
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part9"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0037a3fc", tmp)

    sym_map = {
        "engine_func_0037a420": 0x0037A420,
        "engine_func_002c3628": 0x002C3628,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, arg0: int, arg1: int, ret_420: int, ret_628: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x0037A420:
                calls.append(("engine_func_0037a420", r0))
                uc.reg_write(UC_ARM_REG_R0, ret_420)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002C3628:
                calls.append(("engine_func_002c3628", r0))
                uc.reg_write(UC_ARM_REG_R0, ret_628)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x0037A420, end=0x0037A420)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C3628, end=0x002C3628)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0x111, 0x200, 0, 0x999),
        (0x111, 0x300, 5, 0x999),
        (0x222, 0x400, 0x80000000, 0x999),
        (0x333, 0x500, 0, 0x42),
    ]

    for a0, a1, r420, r628 in cases:
        r1, c1 = run_one(orig_code, a0, a1, r420, r628)
        r2, c2 = run_one(decomp_code, a0, a1, r420, r628)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2}"

    print("func_0037a3fc: PASS")

def test_script_vm_func_0039f834():
    print("--- Testing script_vm_func_0039f834 ---")
    addr = 0x0039F834
    size = 36
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part9"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_0039f834", tmp)

    sym_map = {
        "script_vm_func_002c0ba8": 0x002C0BA8,
        "battle_func_002931cc": 0x002931CC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, ret_ba8: int, ret_1cc: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002C0BA8:
                calls.append(("script_vm_func_002c0ba8", r0))
                uc.reg_write(UC_ARM_REG_R0, ret_ba8)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002931CC:
                calls.append(("battle_func_002931cc", r0))
                uc.reg_write(UC_ARM_REG_R0, ret_1cc)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C0BA8, end=0x002C0BA8)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002931CC, end=0x002931CC)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x999),
        (1, 0x777),
        (0x400, 0x555),
        (0, 0),
    ]

    for rba8, r1cc in cases:
        r1, c1 = run_one(orig_code, rba8, r1cc)
        r2, c2 = run_one(decomp_code, rba8, r1cc)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2}"

    print("script_vm_func_0039f834: PASS")

def test_func_003af184():
    print("--- Testing func_003af184 ---")
    addr = 0x003AF184
    size = 36
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part9"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003af184", tmp)

    sym_map = {
        "func_002dc3bc": 0x002DC3BC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, obj_ptr: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002DC3BC:
                calls.append(("func_002dc3bc", r0))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002DC3BC, end=0x002DC3BC)

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

    print("func_003af184: PASS")

def test_func_003e7038():
    print("--- Testing func_003e7038 ---")
    addr = 0x003E7038
    size = 36
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part9"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003e7038", tmp)

    sym_map = {
        "func_003e70f8": 0x003E70F8,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, sub_ptr: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x003E70F8:
                calls.append(("func_003e70f8", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x003E70F8, end=0x003E70F8)

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

    print("func_003e7038: PASS")

def test_func_003e7080():
    print("--- Testing func_003e7080 ---")
    addr = 0x003E7080
    size = 36
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part9"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003e7080", tmp)

    sym_map = {
        "func_003e7128": 0x003E7128,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, sub_ptr: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x003E7128:
                calls.append(("func_003e7128", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x003E7128, end=0x003E7128)

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

    print("func_003e7080: PASS")

if __name__ == "__main__":
    test_func_0037a3fc()
    test_script_vm_func_0039f834()
    test_func_003af184()
    test_func_003e7038()
    test_func_003e7080()
    print("\nALL 5 FUNCTIONS IN BATCH 31 A PART 9 PASSED WITH 100% DIFFERENTIAL FIDELITY!")
