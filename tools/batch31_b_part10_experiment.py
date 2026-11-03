#!/usr/bin/env python3
"""Differential test for batch 31 B part 10:
- battle_func_003d8acc (0x003D8ACC, 60 B)
- func_003e84f0 (0x003E84F0, 60 B)
- ui_func_00300150 (0x00300150, 64 B)
- camp_func_0031b960 (0x0031B960, 64 B compound: 0x0031b960 + 0x0031b978)
- script_vm_func_0031bfcc (0x0031BFCC, 64 B)
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
SOURCE = ROOT / "src/engine/leaf_batch31_b.cpp"

with open(ORIG_BIN, "rb") as f:
    ORIG_DATA = f.read()

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch31_b.o"
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
    uc.mem_write(CODE_BASE, ORIG_DATA)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    try:
        val = uc.reg_read(UC_ARM_REG_C1_C0_2)
        uc.reg_write(UC_ARM_REG_C1_C0_2, val | (0xF << 20))
        uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    except Exception:
        pass
    return uc

def test_battle_func_003d8acc():
    print("--- Testing battle_func_003d8acc (0x003d8acc) ---")
    addr = 0x003D8ACC
    orig_code = load_original_bytes(addr, 60)
    tmp = ROOT / "build" / "test_31b_part10"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("battle_func_003d8acc", tmp)

    def run_one(code, flags):
        uc = create_emulator()
        uc.mem_write(addr, code)
        obj = 0x10082000
        uc.mem_write(obj + 0x688, struct.pack("<fff", 1.0, 2.0, 3.0))
        uc.mem_write(obj + 0x694, struct.pack("<I", 0x12345678))
        uc.mem_write(obj + 0x634, struct.pack("<I", flags))
        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        v = struct.unpack("<fff", uc.mem_read(obj + 0x688, 12))
        w694 = struct.unpack("<I", uc.mem_read(obj + 0x694, 4))[0]
        fl_out = struct.unpack("<I", uc.mem_read(obj + 0x634, 4))[0]
        return v, w694, fl_out

    for fl in [0, 0x20, 0x100, 0xFFFFFFDF]:
        o_v, o_w, o_fl = run_one(orig_code, fl)
        d_v, d_w, d_fl = run_one(comp, fl)
        assert o_v == (0.0, 0.0, 0.0) and o_w == 0 and o_fl == (fl | 0x20)
        assert d_v == (0.0, 0.0, 0.0) and d_w == 0 and d_fl == (fl | 0x20)
    print("battle_func_003d8acc: PASS")

def test_func_003e84f0():
    print("--- Testing func_003e84f0 (0x003e84f0) ---")
    addr = 0x003E84F0
    orig_code = load_original_bytes(addr, 60)
    tmp = ROOT / "build" / "test_31b_part10"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003e84f0", tmp)

    sym_map = {"func_002a6d94": 0x002A6D94}
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, ret_ok, off, inner_off):
        uc = create_emulator()
        uc.mem_write(addr, code)

        def stub_hook(uc, address, size, user_data):
            out_ptr = uc.reg_read(UC_ARM_REG_R1)
            uc.mem_write(out_ptr, struct.pack("<I", off))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_R0, 1 if ret_ok else 0)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_hook, None, 0x002A6D94, 0x002A6D94)
        obj = 0x10082000
        if ret_ok:
            uc.mem_write(obj + off + 4, struct.pack("<I", inner_off))
        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        return uc.reg_read(UC_ARM_REG_R0)

    # When ret_ok == False -> returns 0x004765D8
    r_orig = run_one(orig_code, False, 0, 0)
    r_decomp = run_one(decomp_code, False, 0, 0)
    assert r_orig == 0x004765D8 and r_decomp == 0x004765D8

    # When ret_ok == True -> returns obj + off + inner_off
    obj = 0x10082000
    r_orig = run_one(orig_code, True, 0x50, 0x20)
    r_decomp = run_one(decomp_code, True, 0x50, 0x20)
    assert r_orig == (obj + 0x50 + 0x20) and r_decomp == (obj + 0x50 + 0x20)
    print("func_003e84f0: PASS")

def test_ui_func_00300150():
    print("--- Testing ui_func_00300150 (0x00300150) ---")
    addr = 0x00300150
    orig_code = load_original_bytes(addr, 64)
    tmp = ROOT / "build" / "test_31b_part10"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_00300150", tmp)

    sym_map = {
        "engine_func_00296f60": 0x00296F60,
        "ui_func_00293c98": 0x00293C98,
        "ui_func_00282b94": 0x00282B94,
        "battle_func_0028df54": 0x0028DF54,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, has_target, target_s16):
        uc = create_emulator()
        uc.mem_write(addr, code)
        fake_p = 0x10084000
        fake_u = 0x10085000
        fake_target = 0x10086000

        calls = []

        def stub_296f60(uc, address, size, user_data):
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_R0, fake_p)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_293c98(uc, address, size, user_data):
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_R0, fake_u)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_282b94(uc, address, size, user_data):
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_R0, fake_target if has_target else 0)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_28df54(uc, address, size, user_data):
            arg = uc.reg_read(UC_ARM_REG_R0)
            # Sign extend 32-bit register
            if arg & 0x80000000:
                arg -= 0x100000000
            calls.append(arg)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_296f60, None, 0x00296F60, 0x00296F60)
        uc.hook_add(UC_HOOK_CODE, stub_293c98, None, 0x00293C98, 0x00293C98)
        uc.hook_add(UC_HOOK_CODE, stub_282b94, None, 0x00282B94, 0x00282B94)
        uc.hook_add(UC_HOOK_CODE, stub_28df54, None, 0x0028DF54, 0x0028DF54)

        if has_target:
            uc.mem_write(fake_target + 0x1B6, struct.pack("<h", target_s16))

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        r0 = uc.reg_read(UC_ARM_REG_R0)
        return r0, calls

    for has_tgt, s16_val in [(True, 42), (True, -5), (False, 0)]:
        o_r0, o_calls = run_one(orig_code, has_tgt, s16_val)
        d_r0, d_calls = run_one(decomp_code, has_tgt, s16_val)
        exp_arg = s16_val if has_tgt else 0
        assert o_r0 == 1 and o_calls == [exp_arg]
        assert d_r0 == 1 and d_calls == [exp_arg]
    print("ui_func_00300150: PASS")

def test_camp_func_0031b960():
    print("--- Testing camp_func_0031b960 compound (0x0031b960) ---")
    addr = 0x0031B960
    orig_code = load_original_bytes(addr, 64)
    tmp = ROOT / "build" / "test_31b_part10"
    tmp.mkdir(parents=True, exist_ok=True)
    comp_a, _ = compile_function("camp_func_0031b960", tmp)
    comp_b, _ = compile_function("camp_func_0031b978", tmp)

    # Sub-function 1: 0x0031B960
    def run_sub1(code, ptr_val):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.mem_write(0x0044CDF0, struct.pack("<I", ptr_val))
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        return uc.reg_read(UC_ARM_REG_R0)

    for ptr, exp in [(0x10084000, 1), (0, 0)]:
        o_r0 = run_sub1(orig_code[:24], ptr)
        d_r0 = run_sub1(comp_a, ptr)
        assert o_r0 == exp and d_r0 == exp

    # Sub-function 2: 0x0031B978
    sub2_addr = 0x0031B978
    def run_sub2(code, count):
        uc = create_emulator()
        uc.mem_write(sub2_addr, code)
        obj = 0x10082000
        uc.mem_write(0x00432CC8, struct.pack("<I", obj))
        uc.mem_write(obj + 0x760, struct.pack("<i", count))
        uc.mem_write(obj + 0x14C, struct.pack("<I", 0))
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(sub2_addr, 0x003E0000, timeout=1000000)
        c_out = struct.unpack("<i", uc.mem_read(obj + 0x760, 4))[0]
        v14c = struct.unpack("<I", uc.mem_read(obj + 0x14C, 4))[0]
        return c_out, v14c

    for c in [5, 1, 0, -1]:
        o_c, o_v = run_sub2(orig_code[24:], c)
        d_c, d_v = run_sub2(comp_b, c)
        exp_c = c - 1
        exp_v = 3 if exp_c < 0 else 0
        assert o_c == exp_c and o_v == exp_v
        assert d_c == exp_c and d_v == exp_v
    print("camp_func_0031b960 compound: PASS")

def test_script_vm_func_0031bfcc():
    print("--- Testing script_vm_func_0031bfcc (0x0031bfcc) ---")
    addr = 0x0031BFCC
    orig_code = load_original_bytes(addr, 64)
    tmp = ROOT / "build" / "test_31b_part10"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_0031bfcc", tmp)

    sym_map = {
        "battle_func_002bf41c": 0x002BF41C,
        "battle_func_002c45b8": 0x002C45B8,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, has_ptr, bf_ret):
        uc = create_emulator()
        uc.mem_write(addr, code)
        calls = []

        def stub_bf41c(uc, address, size, user_data):
            calls.append("bf41c")
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_R0, 1 if bf_ret else 0)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_c45b8(uc, address, size, user_data):
            calls.append("c45b8")
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_bf41c, None, 0x002BF41C, 0x002BF41C)
        uc.hook_add(UC_HOOK_CODE, stub_c45b8, None, 0x002C45B8, 0x002C45B8)

        obj = 0x10082000
        ptr_val = 0x10083000
        if has_ptr:
            uc.mem_write(0x0043E088, struct.pack("<I", ptr_val))
            uc.mem_write(ptr_val, struct.pack("<I", obj))
        else:
            uc.mem_write(0x0043E088, struct.pack("<I", 0))

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        return calls

    for has_p, bf in [(True, True), (True, False), (False, False)]:
        o_calls = run_one(orig_code, has_p, bf)
        d_calls = run_one(decomp_code, has_p, bf)
        assert o_calls == d_calls
    print("script_vm_func_0031bfcc: PASS")

def main():
    test_battle_func_003d8acc()
    test_func_003e84f0()
    test_ui_func_00300150()
    test_camp_func_0031b960()
    test_script_vm_func_0031bfcc()
    print("ALL BATCH 31 B PART 10 TESTS PASSED!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
