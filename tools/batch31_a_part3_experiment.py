#!/usr/bin/env python3
"""Differential test for batch 31 A part 3:
- func_003d6634 (0x003D6634, 24 B)
- script_vm_func_00308c7c (0x00308C7C, 28 B)
- script_vm_func_0030f518 (0x0030F518, 28 B)
- script_vm_func_0031074c (0x0031074C, 28 B)
- func_0034b3a0 (0x0034B3A0, 28 B)
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

def test_func_003d6634():
    print("--- Testing func_003d6634 ---")
    addr = 0x003D6634
    size = 24
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part3"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003d6634", tmp)

    sym_map = {
        "camp_func_002a06dc": 0x002A06DC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    DATA_PAGE = 0x08000000

    def run_one(code: bytes, sub: int):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.mem_map(DATA_PAGE, 0x10000)

        # Write sub at DATA_PAGE + 0x730
        uc.mem_write(DATA_PAGE + 0x730, struct.pack("<I", sub))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            calls.append((r0, r1))
            uc.reg_write(UC_ARM_REG_R0, 0x08003000)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002A06DC, end=0x002A06DC)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, DATA_PAGE)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    for s in (0, 0x08001000, 0xDEADBEEF):
        r1, c1 = run_one(orig_code, s)
        r2, c2 = run_one(decomp_code, s)
        assert r1 == r2, f"result mismatch for {hex(s)}: {hex(r1)} vs {hex(r2)}"
        assert c1 == c2, f"calls mismatch for {hex(s)}: {c1} vs {c2}"

    print("func_003d6634: PASS")

def test_script_vm_func_00308c7c():
    print("--- Testing script_vm_func_00308c7c ---")
    addr = 0x00308C7C
    size = 28
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part3"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_00308c7c", tmp)

    sym_map = {
        "script_vm_func_00308d00": 0x00308D00,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, obj_val: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        # 0x00447E28 is in CODE_BASE + CODE_SIZE
        uc.mem_write(0x00447E28, struct.pack("<I", obj_val))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            calls.append(r0)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00308D00, end=0x00308D00)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        return calls

    for val in (0, 0x08001000, 0x55AA1234):
        c1 = run_one(orig_code, val)
        c2 = run_one(decomp_code, val)
        assert c1 == c2, f"calls mismatch for {hex(val)}: {c1} vs {c2}"

    print("script_vm_func_00308c7c: PASS")

def test_script_vm_func_0030f518():
    print("--- Testing script_vm_func_0030f518 ---")
    addr = 0x0030F518
    size = 28
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part3"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_0030f518", tmp)

    sym_map = {
        "script_vm_func_00308d00": 0x00308D00,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, obj_val: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        uc.mem_write(0x00447060, struct.pack("<I", obj_val))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            calls.append(r0)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00308D00, end=0x00308D00)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        return calls

    for val in (0, 0x08002000, 0xFEEDFACE):
        c1 = run_one(orig_code, val)
        c2 = run_one(decomp_code, val)
        assert c1 == c2, f"calls mismatch for {hex(val)}: {c1} vs {c2}"

    print("script_vm_func_0030f518: PASS")

def test_script_vm_func_0031074c():
    print("--- Testing script_vm_func_0031074c ---")
    addr = 0x0031074C
    size = 28
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part3"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_0031074c", tmp)

    sym_map = {
        "script_vm_func_00289a48": 0x00289A48,
        "script_vm_func_00289a18": 0x00289A18,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, a48_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00289A48:
                calls.append(("a48",))
                uc.reg_write(UC_ARM_REG_R0, a48_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x00289A18:
                calls.append(("a18", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00289A48, end=0x00289A48)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00289A18, end=0x00289A18)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    for ret in (0, 1, 5, -1):
        r1, c1 = run_one(orig_code, ret)
        r2, c2 = run_one(decomp_code, ret)
        assert r1 == r2 == 1, f"res mismatch: {r1} vs {r2}"
        assert c1 == c2, f"calls mismatch for ret={ret}: {c1} vs {c2}"

    print("script_vm_func_0031074c: PASS")

def test_func_0034b3a0():
    print("--- Testing func_0034b3a0 ---")
    addr = 0x0034B3A0
    size = 28
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part3"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0034b3a0", tmp)

    decomp_code = stage_body(comp, relocs, addr, {})

    CB_STUB = 0x00250000

    def run_one(code: bytes, p0: int, p1: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        # Write callback pointer at 0x0044E994
        uc.mem_write(0x0044E994, struct.pack("<I", CB_STUB))

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            calls.append(r0)
            uc.reg_write(UC_ARM_REG_R0, r0 ^ 0x55)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=CB_STUB, end=CB_STUB)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, p0)
        uc.reg_write(UC_ARM_REG_R1, p1)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    for p0, p1 in ((123, 0), (0, 0x08001000), (0x1000, 0x08002000)):
        r1, c1 = run_one(orig_code, p0, p1)
        r2, c2 = run_one(decomp_code, p0, p1)
        assert r1 == r2, f"result mismatch: {r1} vs {r2}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2}"

    print("func_0034b3a0: PASS")

if __name__ == "__main__":
    test_func_003d6634()
    test_script_vm_func_00308c7c()
    test_script_vm_func_0030f518()
    test_script_vm_func_0031074c()
    test_func_0034b3a0()
    print("\nALL 5 FUNCTIONS IN BATCH 31 A PART 3 PASSED WITH 100% DIFFERENTIAL FIDELITY!")
