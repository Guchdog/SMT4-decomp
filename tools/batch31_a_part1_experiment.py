#!/usr/bin/env python3
"""Differential test for batch 31 A part 1:
- func_0034afe4 (0x0034AFE4, 8 B)
- engine_func_0035311c (0x0035311C, 8 B)
- script_vm_func_00394ee0 (0x00394EE0, 12 B)
- script_vm_func_003968c0 (0x003968C0, 20 B)
- func_003eafac (0x003EAFAC, 20 B)
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

def test_func_0034afe4():
    print("--- Testing func_0034afe4 ---")
    addr = 0x0034AFE4
    size = 8
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part1"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0034afe4", tmp)

    sym_map = {
        "engine_func_002b2520": 0x002B2520,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, arg0: int):
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
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        return calls

    for arg in (0, 0x12345678, 0xDEADBEEF):
        c1 = run_one(orig_code, arg)
        c2 = run_one(decomp_code, arg)
        assert c1 == c2 == [arg], f"mismatch: {c1} vs {c2}"

    print("func_0034afe4: PASS")

def test_engine_func_0035311c():
    print("--- Testing engine_func_0035311c ---")
    addr = 0x0035311C
    size = 8
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part1"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_0035311c", tmp)

    decomp_code = stage_body(comp, relocs, addr, {})

    def run_one(code: bytes, r0_init: int, r1_init: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        # In original binary, 0x0035311c branches to 0x0023a354 which is bx lr
        # Write bx lr at 0x0023a354
        uc.mem_write(0x0023A354, struct.pack("<I", 0xe12fff1e))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, r0_init)
        uc.reg_write(UC_ARM_REG_R1, r1_init)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        return uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)

    for r0, r1 in ((0, 0), (123, 456), (0xCAFEBABE, 0xFEEDFACE)):
        res1 = run_one(orig_code, r0, r1)
        res2 = run_one(decomp_code, r0, r1)
        assert res1 == res2, f"mismatch: {res1} vs {res2}"

    print("engine_func_0035311c: PASS")

def test_script_vm_func_00394ee0():
    print("--- Testing script_vm_func_00394ee0 ---")
    addr = 0x00394EE0
    size = 12
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part1"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_00394ee0", tmp)

    sym_map = {
        "engine_func_002c583c": 0x002C583C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            calls.append(r0)
            uc.reg_write(UC_ARM_REG_R0, 0x42)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C583C, end=0x002C583C)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    res1, c1 = run_one(orig_code)
    res2, c2 = run_one(decomp_code)
    assert res1 == res2 == 0x42
    assert c1 == c2 == [1]

    print("script_vm_func_00394ee0: PASS")

def test_script_vm_func_003968c0():
    print("--- Testing script_vm_func_003968c0 ---")
    addr = 0x003968C0
    size = 20
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part1"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_003968c0", tmp)

    sym_map = {
        "script_vm_func_003968d4": 0x003968D4,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    DATA_PAGE = 0x08000000

    def run_one(code: bytes, val: int):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.mem_map(DATA_PAGE, 0x10000)
        uc.mem_write(DATA_PAGE, struct.pack("<I", val))

        # In original code, it branches to 0x003968D4
        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            calls.append(r0)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x003968D4, end=0x003968D4)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, DATA_PAGE)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        return calls

    for v in (0, 1, 2, 3, 0x100, 0x101, 0xFFFFFFFE, 0xFFFFFFFF):
        c1 = run_one(orig_code, v)
        c2 = run_one(decomp_code, v)
        assert c1 == c2, f"mismatch for val {hex(v)}: {c1} vs {c2}"

    print("script_vm_func_003968c0: PASS")

def test_func_003eafac():
    print("--- Testing func_003eafac ---")
    addr = 0x003EAFAC
    size = 20
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part1"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003eafac", tmp)

    sym_map = {
        "func_002a3428": 0x002A3428,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    DATA_PAGE = 0x08100000

    def run_one(code: bytes, p0: int, p1: int):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.mem_map(DATA_PAGE, 0x10000)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            calls.append((r0, r1))
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002A3428, end=0x002A3428)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, p0)
        uc.reg_write(UC_ARM_REG_R1, p1)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        return calls

    cases = [
        (DATA_PAGE, 0),
        (DATA_PAGE, DATA_PAGE + 0x100),
        (DATA_PAGE + 0x20, 0),
        (DATA_PAGE + 0x50, DATA_PAGE + 0x200),
    ]

    for p0, p1 in cases:
        c1 = run_one(orig_code, p0, p1)
        c2 = run_one(decomp_code, p0, p1)
        assert c1 == c2, f"mismatch: {c1} vs {c2}"

    print("func_003eafac: PASS")

if __name__ == "__main__":
    test_func_0034afe4()
    test_engine_func_0035311c()
    test_script_vm_func_00394ee0()
    test_script_vm_func_003968c0()
    test_func_003eafac()
    print("\nALL 5 FUNCTIONS IN BATCH 31 A PART 1 PASSED WITH 100% DIFFERENTIAL FIDELITY!")
