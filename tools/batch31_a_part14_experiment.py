#!/usr/bin/env python3
"""Differential test for batch 31 A part 14:
- func_00370220 (0x00370220, 44 B)
- func_00376b20 (0x00376B20, 44 B)
- func_0037bc48 (0x0037BC48, 44 B)
- engine_func_0039493c (0x0039493C, 44 B)
- engine_func_003a6614 (0x003A6614, 44 B)
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

def test_func_00370220():
    print("--- Testing func_00370220 ---")
    addr = 0x00370220
    size = 44
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part14"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00370220", tmp)

    sym_map = {
        "script_vm_func_002c3568": 0x002C3568,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, rel_val: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002C3568:
                ptr_val = struct.unpack("<I", uc.mem_read(r0, 4))[0]
                calls.append(("script_vm_func_002c3568", ptr_val))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C3568, end=0x002C3568)

        base_ptr = STACK_BASE + 0x1000
        uc.mem_write(base_ptr + 0x2C, b"\xFF\xFF\xFF\xFF")
        uc.mem_write(base_ptr + 8, struct.pack("<i", rel_val))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, base_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        val_2c = struct.unpack("<I", uc.mem_read(base_ptr + 0x2C, 4))[0]
        return res, val_2c, calls

    cases = [
        (0, 0x999),
        (0x20, 0x777),
        (-0x10, 0x555),
    ]

    for rel_val, hret in cases:
        r1, v1, c1 = run_one(orig_code, rel_val, hret)
        r2, v2, c2 = run_one(decomp_code, rel_val, hret)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for rel={rel_val}"
        assert v1 == v2 == 0, f"offset 0x2c mismatch: {hex(v1)} vs {hex(v2)}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for rel={rel_val}"

    print("func_00370220: PASS")

def test_func_00376b20():
    print("--- Testing func_00376b20 ---")
    addr = 0x00376B20
    size = 44
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part14"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00376b20", tmp)

    sym_map = {
        "func_00379bd4": 0x00379BD4,
        "func_002bdbc4": 0x002BDBC4,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, b9d4_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x00379BD4:
                calls.append(("func_00379bd4", r0))
                uc.reg_write(UC_ARM_REG_R0, b9d4_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002BDBC4:
                calls.append(("func_002bdbc4", r0))
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x00379BD4, end=0x00379BD4)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002BDBC4, end=0x002BDBC4)

        self_ptr = STACK_BASE + 0x1000
        arg1_ptr = STACK_BASE + 0x2000

        uc.mem_write(self_ptr, b"\x00\x00\x00\x00")
        uc.mem_write(arg1_ptr + 8, b"\x00\x00\x00\x00")

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, self_ptr)
        uc.reg_write(UC_ARM_REG_R1, arg1_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        self_val = struct.unpack("<I", uc.mem_read(self_ptr, 4))[0]
        arg1_8_val = struct.unpack("<I", uc.mem_read(arg1_ptr + 8, 4))[0]
        return self_val, arg1_8_val, calls

    cases = [
        0,
        1,
        42,
    ]

    for b9d4 in cases:
        s1, a1, c1 = run_one(orig_code, b9d4)
        s2, a2, c2 = run_one(decomp_code, b9d4)
        assert s1 == s2 == (STACK_BASE + 0x2000), f"self slot mismatch: {hex(s1)} vs {hex(s2)}"
        assert a1 == a2 == (STACK_BASE + 0x1000), f"inner[8] mismatch: {hex(a1)} vs {hex(a2)}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for b9d4={b9d4}"

    print("func_00376b20: PASS")

def test_func_0037bc48():
    print("--- Testing func_0037bc48 ---")
    addr = 0x0037BC48
    size = 44
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part14"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0037bc48", tmp)

    sym_map = {
        "func_0037b824": 0x0037B824,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, flag: int, helper_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x0037B824:
                calls.append(("func_0037b824", r0, r1))
                uc.reg_write(UC_ARM_REG_R0, helper_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x0037B824, end=0x0037B824)

        self_ptr = STACK_BASE + 0x1000
        uc.mem_write(self_ptr + 0x260, b"\xAA")
        uc.mem_write(self_ptr + 0x261, bytes([flag & 0xFF]))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, self_ptr)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        b260 = uc.mem_read(self_ptr + 0x260, 1)[0]
        b261 = uc.mem_read(self_ptr + 0x261, 1)[0]
        return res, b260, b261, calls

    cases = [
        (0, 0x123),
        (1, 0x456),
        (0xFF, 0x789),
    ]

    for f, hret in cases:
        r1, b0_1, b1_1, c1 = run_one(orig_code, f, hret)
        r2, b0_2, b1_2, c2 = run_one(decomp_code, f, hret)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for flag={f}"
        assert b0_1 == b0_2, f"b260 mismatch: {b0_1} vs {b0_2}"
        assert b1_1 == b1_2, f"b261 mismatch: {b1_1} vs {b1_2}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for flag={f}"

    print("func_0037bc48: PASS")

def test_engine_func_0039493c():
    print("--- Testing engine_func_0039493c ---")
    addr = 0x0039493C
    size = 44
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part14"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_0039493c", tmp)

    sym_map = {
        "engine_func_002c583c": 0x002C583C,
        "func_002d5fbc": 0x002D5FBC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, c58_ret: int, d5f_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002C583C:
                calls.append(("engine_func_002c583c", r0))
                uc.reg_write(UC_ARM_REG_R0, c58_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)
            elif address == 0x002D5FBC:
                calls.append(("func_002d5fbc", r0))
                uc.reg_write(UC_ARM_REG_R0, d5f_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002C583C, end=0x002C583C)
        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002D5FBC, end=0x002D5FBC)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        return res, calls

    cases = [
        (0, 0x999),
        (STACK_BASE + 0x1000, 0x777),
        (1, 0x555),
    ]

    for c58, d5f in cases:
        r1, c1 = run_one(orig_code, c58, d5f)
        r2, c2 = run_one(decomp_code, c58, d5f)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for c58={c58}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for c58={c58}"

    print("engine_func_0039493c: PASS")

def test_engine_func_003a6614():
    print("--- Testing engine_func_003a6614 ---")
    addr = 0x003A6614
    size = 44
    orig_code = load_original_bytes(addr, size)

    tmp = ROOT / "build" / "test_31a_part14"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_003a6614", tmp)

    sym_map = {
        "script_vm_func_002a497c": 0x002A497C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code: bytes, initial_count: int, a49_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def stub_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            if address == 0x002A497C:
                calls.append(("script_vm_func_002a497c", r0))
                uc.reg_write(UC_ARM_REG_R0, a49_ret)
                uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, begin=0x002A497C, end=0x002A497C)

        # 0x0044E06C holds count (0x0044E068 + 4)
        uc.mem_write(0x0044E06C, struct.pack("<i", initial_count))

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00370000)

        uc.emu_start(addr, 0x00370000, timeout=10000000)
        res = uc.reg_read(UC_ARM_REG_R0)
        final_count = struct.unpack("<i", uc.mem_read(0x0044E06C, 4))[0]
        return res, final_count, calls

    cases = [
        (2, 0x999),  # 2 - 1 = 1 > 0 -> returns 1
        (1, 0x777),  # 1 - 1 = 0 <= 0 -> calls script_vm_func_002a497c(0x17)
        (0, 0x555),  # 0 - 1 = -1 <= 0 -> calls script_vm_func_002a497c(0x17)
        (5, 0x333),  # 5 - 1 = 4 > 0 -> returns 1
    ]

    for init_c, a49 in cases:
        r1, fc1, c1 = run_one(orig_code, init_c, a49)
        r2, fc2, c2 = run_one(decomp_code, init_c, a49)
        assert r1 == r2, f"result mismatch: {hex(r1)} vs {hex(r2)} for init_c={init_c}"
        assert fc1 == fc2 == (init_c - 1), f"final count mismatch: {fc1} vs {fc2}"
        assert c1 == c2, f"calls mismatch: {c1} vs {c2} for init_c={init_c}"

    print("engine_func_003a6614: PASS")

if __name__ == "__main__":
    test_func_00370220()
    test_func_00376b20()
    test_func_0037bc48()
    test_engine_func_0039493c()
    test_engine_func_003a6614()
    print("\nALL 5 FUNCTIONS IN BATCH 31 A PART 14 PASSED WITH 100% DIFFERENTIAL FIDELITY!")
