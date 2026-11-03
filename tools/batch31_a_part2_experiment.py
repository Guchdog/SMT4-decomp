#!/usr/bin/env python3
"""Differential test for batch 31 A part 2:
- engine_func_0033858c (0x0033858C, 24 B)
- func_00349740 (0x00349740, 24 B)
- func_00351e98 (0x00351E98, 24 B)
- func_00351ee0 (0x00351EE0, 24 B)
- func_003c0a90 (0x003C0A90, 24 B)
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

def test_engine_func_0033858c():
    print("--- Testing engine_func_0033858c ---")
    addr = 0x0033858C
    size = 24
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part2"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_0033858c", tmp)

    sym_map = {
        "ui_func_00297920": 0x00297920,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    DATA_PAGE = 0x08000000

    def run_one(code: bytes, sub_ptr: int):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.mem_map(DATA_PAGE, 0x10000)

        # Write sub_ptr at DATA_PAGE + 0x4394
        uc.mem_write(DATA_PAGE + 0x4394, struct.pack("<I", sub_ptr))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            calls.append(r0)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00297920, end=0x00297920)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, DATA_PAGE)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        return calls

    for sub in (0, 0x12345678, 0xDEADBEEF):
        c1 = run_one(orig_code, sub)
        c2 = run_one(decomp_code, sub)
        assert c1 == c2, f"mismatch for sub {hex(sub)}: {c1} vs {c2}"

    print("engine_func_0033858c: PASS")

def test_func_00349740():
    print("--- Testing func_00349740 ---")
    addr = 0x00349740
    size = 24
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part2"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00349740", tmp)

    sym_map = {
        "engine_func_002b2520": 0x002B2520,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, arg: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            calls.append(r0)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002B2520, end=0x002B2520)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        return calls

    for a in (0, 0x1000, 0x55AA55AA):
        c1 = run_one(orig_code, a)
        c2 = run_one(decomp_code, a)
        assert c1 == c2 == [a], f"mismatch: {c1} vs {c2}"

    print("func_00349740: PASS")

def test_func_00351e98():
    print("--- Testing func_00351e98 ---")
    addr = 0x00351E98
    size = 24
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part2"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00351e98", tmp)

    sym_map = {
        "func_00352150": 0x00352150,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, p: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            calls.append(r0)
            uc.reg_write(UC_ARM_REG_R0, 0)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00352150, end=0x00352150)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, p)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    for ptr in (0, 0x08001000, 0x12345678):
        r1, c1 = run_one(orig_code, ptr)
        r2, c2 = run_one(decomp_code, ptr)
        assert r1 == r2, f"result mismatch for {hex(ptr)}: {hex(r1)} vs {hex(r2)}"
        assert c1 == c2, f"calls mismatch for {hex(ptr)}: {c1} vs {c2}"

    print("func_00351e98: PASS")

def test_func_00351ee0():
    print("--- Testing func_00351ee0 ---")
    addr = 0x00351EE0
    size = 24
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part2"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00351ee0", tmp)

    sym_map = {
        "func_003521c8": 0x003521C8,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, p: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            calls.append(r0)
            uc.reg_write(UC_ARM_REG_R0, 0)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x003521C8, end=0x003521C8)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, p)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    for ptr in (0, 0x08001000, 0x12345678):
        r1, c1 = run_one(orig_code, ptr)
        r2, c2 = run_one(decomp_code, ptr)
        assert r1 == r2, f"result mismatch for {hex(ptr)}: {hex(r1)} vs {hex(r2)}"
        assert c1 == c2, f"calls mismatch for {hex(ptr)}: {c1} vs {c2}"

    print("func_00351ee0: PASS")

def test_func_003c0a90():
    print("--- Testing func_003c0a90 ---")
    addr = 0x003C0A90
    size = 24
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part2"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003c0a90", tmp)

    sym_map = {
        "Tbb_GetSubTable": 0x002AC2F4,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    DATA_PAGE = 0x08000000

    def run_one(code: bytes, sub: int):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.mem_map(DATA_PAGE, 0x10000)

        # Write sub at DATA_PAGE + 8
        uc.mem_write(DATA_PAGE + 8, struct.pack("<I", sub))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            calls.append((r0, r1))
            uc.reg_write(UC_ARM_REG_R0, 0x08002000)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002AC2F4, end=0x002AC2F4)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, DATA_PAGE)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    for s in (0, 0x08001000, 0x55AA1234):
        r1, c1 = run_one(orig_code, s)
        r2, c2 = run_one(decomp_code, s)
        assert r1 == r2, f"result mismatch for {hex(s)}: {hex(r1)} vs {hex(r2)}"
        assert c1 == c2, f"calls mismatch for {hex(s)}: {c1} vs {c2}"

    print("func_003c0a90: PASS")

if __name__ == "__main__":
    test_engine_func_0033858c()
    test_func_00349740()
    test_func_00351e98()
    test_func_00351ee0()
    test_func_003c0a90()
    print("\nALL 5 FUNCTIONS IN BATCH 31 A PART 2 PASSED WITH 100% DIFFERENTIAL FIDELITY!")
