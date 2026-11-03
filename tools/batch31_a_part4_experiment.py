#!/usr/bin/env python3
"""Differential test for batch 31 A part 4:
- func_003604a4 (0x003604A4, 28 B)
- func_003605ec (0x003605EC, 28 B)
- func_003606b0 (0x003606B0, 28 B)
- func_003606cc (0x003606CC, 28 B)
- func_003606e8 (0x003606E8, 28 B)
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

def run_pattern_test(func_name: str, addr: int, target_stub: int, stub_name: str):
    print(f"--- Testing {func_name} ---")
    size = 28
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part4"
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
        (0, 0),             # succeeded (0)
        (5, 100),           # succeeded (positive)
        (0x1234, -1),       # failed (negative) -> calls bce48(1)
        (0xABCD, -500),     # failed (negative) -> calls bce48(1)
        (0xFF, 0x80000000), # failed (bit 31 set) -> calls bce48(1)
        (0x20, 0x7FFFFFFF), # succeeded (bit 31 clear)
    ]

    for arg, sret in cases:
        r1, c1 = run_one(orig_code, arg, sret)
        r2, c2 = run_one(decomp_code, arg, sret)
        assert r1 == r2, f"result mismatch: {r1} vs {r2} for ret={sret}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for ret={sret}"

    print(f"{func_name}: PASS")

if __name__ == "__main__":
    run_pattern_test("func_003604a4", 0x003604A4, 0x003607F8, "func_003607f8")
    run_pattern_test("func_003605ec", 0x003605EC, 0x003609A4, "func_003609a4")
    run_pattern_test("func_003606b0", 0x003606B0, 0x00360A10, "func_00360a10")
    run_pattern_test("func_003606cc", 0x003606CC, 0x00360A4C, "func_00360a4c")
    run_pattern_test("func_003606e8", 0x003606E8, 0x00360A7C, "func_00360a7c")
    print("\nALL 5 FUNCTIONS IN BATCH 31 A PART 4 PASSED WITH 100% DIFFERENTIAL FIDELITY!")
