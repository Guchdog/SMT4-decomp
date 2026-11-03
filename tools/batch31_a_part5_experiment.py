#!/usr/bin/env python3
"""Differential test for batch 31 A part 5:
- engine_func_0036072c (0x0036072C, 28 B)
- func_00360748 (0x00360748, 28 B)
- func_00360764 (0x00360764, 28 B)
- func_003607c0 (0x003607C0, 28 B)
- nn_sdk_func_003607dc (0x003607DC, 28 B)
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

def test_engine_func_0036072c():
    print("--- Testing engine_func_0036072c ---")
    addr = 0x0036072C
    size = 28
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part5"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_0036072c", tmp)

    sym_map = {
        "func_00360b18": 0x00360B18,
        "engine_func_002bce48": 0x002BCE48,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, b18_ret: int, byte_written: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00360B18:
                calls.append(("b18",))
                uc.mem_write(r0, bytes([byte_written & 0xFF]))
                uc.reg_write(UC_ARM_REG_R0, b18_ret & 0xFFFFFFFF)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002BCE48:
                calls.append(("bce48", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00360B18, end=0x00360B18)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002BCE48, end=0x002BCE48)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        # Sign extend 32-bit register
        if res & 0x80000000:
            res -= 0x100000000
        return res, calls

    cases = [
        (0, 42),
        (100, 0),
        (-1, 0x7F),
        (-500, 0xFE),  # -2 signed
        (0x80000000, 0x80), # -128 signed
    ]

    for ret, bw in cases:
        r1, c1 = run_one(orig_code, ret, bw)
        r2, c2 = run_one(decomp_code, ret, bw)
        assert r1 == r2, f"res mismatch: {r1} vs {r2} for ret={ret}, bw={bw}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for ret={ret}, bw={bw}"

    print("engine_func_0036072c: PASS")

def run_pattern_test(func_name: str, addr: int, target_stub: int, stub_name: str):
    print(f"--- Testing {func_name} ---")
    size = 28
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part5"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function(func_name, tmp)

    sym_map = {
        stub_name: target_stub,
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
            if address == target_stub:
                calls.append((stub_name, r0))
                uc.reg_write(UC_ARM_REG_R0, stub_ret & 0xFFFFFFFF)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002BCE48:
                calls.append(("bce48", r0))
                uc.reg_write(UC_ARM_REG_R0, 0x99)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=target_stub, end=target_stub)
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
        (5, 100),
        (0x1234, -1),
        (0xABCD, -500),
        (0xFF, 0x80000000),
        (0x20, 0x7FFFFFFF),
    ]

    for arg, sret in cases:
        r1, c1 = run_one(orig_code, arg, sret)
        r2, c2 = run_one(decomp_code, arg, sret)
        assert r1 == r2, f"result mismatch: {r1} vs {r2} for ret={sret}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for ret={sret}"

    print(f"{func_name}: PASS")

if __name__ == "__main__":
    test_engine_func_0036072c()
    run_pattern_test("func_00360748", 0x00360748, 0x00360B54, "func_00360b54")
    run_pattern_test("func_00360764", 0x00360764, 0x00360B90, "func_00360b90")
    run_pattern_test("func_003607c0", 0x003607C0, 0x00360C08, "func_00360c08")
    run_pattern_test("nn_sdk_func_003607dc", 0x003607DC, 0x00360C44, "func_00360c44")
    print("\nALL 5 FUNCTIONS IN BATCH 31 A PART 5 PASSED WITH 100% DIFFERENTIAL FIDELITY!")
