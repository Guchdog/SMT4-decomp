#!/usr/bin/env python3
"""Differential test for batch 31 B part 14:
- camp_func_003aaef0 (0x003AAEF0, 64 B compound)
- ui_func_003bbed4 (0x003BBED4, 64 B)
- func_003e68bc (0x003E68BC, 64 B)
- func_003e6934 (0x003E6934, 64 B)
- func_003f6228 (0x003F6228, 64 B)
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
        compile_tu_armv6k(source, obj)
        COMPILED_FUNCTIONS = extract_elf_functions_detailed(obj)
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

def unmapped_hook(uc, access, address, size, value, user_data):
    aligned = address & ~0xFFF
    uc.mem_map(aligned, 0x1000)
    return True

def create_emulator() -> Uc:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, unmapped_hook)

    val = uc.reg_read(UC_ARM_REG_C1_C0_2)
    val |= (0xF << 20)
    uc.reg_write(UC_ARM_REG_C1_C0_2, val)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    return uc

def test_camp_func_003aaef0():
    addr = 0x003AAEF0
    print(f"--- Testing camp_func_003aaef0 ({hex(addr)}) ---")
    tmp = ROOT / "build" / "test_31b_part14"
    tmp.mkdir(parents=True, exist_ok=True)
    comp_a, _ = compile_function("camp_func_003aaef0", tmp)
    comp_b, _ = compile_function("camp_func_003aaf08", tmp)

    orig_bytes_a = load_original_bytes(0x003AAEF0, 24)
    orig_bytes_b = load_original_bytes(0x003AAF08, 40)

    # Sub-function A: 0x003AAEF0
    def run_a(code):
        uc = create_emulator()
        uc.mem_write(0x003AAEF0, code)

        target_obj = 0x10082000
        ptr_addr = 0x0043D9E4
        page = ptr_addr & ~0xFFF
        try:
            uc.mem_map(page, 0x2000)
        except Exception:
            pass

        uc.mem_write(ptr_addr, struct.pack("<I", target_obj))
        uc.mem_write(target_obj + 0x1D, b"\x00")

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(0x003AAEF0, 0x003E0000, timeout=1000000)

        return struct.unpack("<B", uc.mem_read(target_obj + 0x1D, 1))[0]

    oa = run_a(orig_bytes_a)
    da = run_a(comp_a)
    assert oa == 4 and da == 4, f"Sub A mismatch: {oa} != {da}"

    # Sub-function B: 0x003AAF08
    def run_b(code):
        uc = create_emulator()
        uc.mem_write(0x003AAF08, code)

        ptr_addr = 0x0043D9C8
        page = ptr_addr & ~0xFFF
        try:
            uc.mem_map(page, 0x2000)
        except Exception:
            pass

        holder = 0x10082000
        sub_obj = 0x10083000
        vtable = 0x10084000
        fn_addr = 0x10085000

        uc.mem_write(ptr_addr, struct.pack("<I", holder))
        uc.mem_write(holder, struct.pack("<I", sub_obj))
        uc.mem_write(sub_obj, struct.pack("<I", vtable))
        uc.mem_write(vtable + 0xC, struct.pack("<I", fn_addr))

        calls = []
        def vfunc_hook(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(arg0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, vfunc_hook, None, fn_addr, fn_addr)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(0x003AAF08, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, calls

    ob, o_calls = run_b(orig_bytes_b)
    db, d_calls = run_b(comp_b)
    assert ob == 0 and db == 0
    assert o_calls == [0x10083000] and d_calls == [0x10083000]
    print("camp_func_003aaef0: PASS")

def test_ui_func_003bbed4():
    addr = 0x003BBED4
    print(f"--- Testing ui_func_003bbed4 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 64)
    tmp = ROOT / "build" / "test_31b_part14"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_003bbed4", tmp)

    sym_map = {
        "ui_func_00357a28": 0x00357A28,
        "engine_func_0022af30": 0x0022AF30,
        "func_002d5508": 0x002D5508,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, engine_ret):
        uc = create_emulator()
        uc.mem_write(addr, code)

        ctx_ptr_addr = 0x0043DDB8
        page = ctx_ptr_addr & ~0xFFF
        try:
            uc.mem_map(page, 0x2000)
        except Exception:
            pass

        ctx_obj = 0x10082000
        p_obj = 0x10083000
        uc.mem_write(ctx_ptr_addr, struct.pack("<I", ctx_obj))

        calls = []
        def fn_357a28(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("357a28", arg0))
            uc.reg_write(UC_ARM_REG_R0, p_obj)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def fn_22af30(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("22af30", arg0, arg1))
            uc.reg_write(UC_ARM_REG_R0, engine_ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def fn_2d5508(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("2d5508", arg0))
            uc.reg_write(UC_ARM_REG_R0, 0xCAFE1234)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, fn_357a28, None, 0x00357A28, 0x00357A28)
        uc.hook_add(UC_HOOK_CODE, fn_22af30, None, 0x0022AF30, 0x0022AF30)
        uc.hook_add(UC_HOOK_CODE, fn_2d5508, None, 0x002D5508, 0x002D5508)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, calls

    for ret_val in [0, 1]:
        o_ret, o_calls = run_one(orig_code, ret_val)
        d_ret, d_calls = run_one(decomp_code, ret_val)
        assert o_ret == d_ret, f"ret mismatch: {hex(o_ret)} != {hex(d_ret)}"
        assert o_calls == d_calls, f"calls mismatch: {o_calls} != {d_calls}"
    print("ui_func_003bbed4: PASS")

def test_resource_finder(name: str, addr: int, target_tag: int):
    print(f"--- Testing {name} ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 64)
    tmp = ROOT / "build" / "test_31b_part14"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function(name, tmp)

    def run_one(code, match_slot):
        uc = create_emulator()
        uc.mem_write(addr, code)

        obj = 0x10082000
        uc.mem_write(obj, b"\x00" * 0x40)

        # 3 candidate slots: offset 0x14, 0x20, 0x2C
        slots = [0x14, 0x20, 0x2C]
        for i, off in enumerate(slots):
            tag = target_tag if i == match_slot else 0x1234
            uc.mem_write(obj + off, struct.pack("<H", tag))
            uc.mem_write(obj + off + 4, struct.pack("<I", 0x20000000 + i * 0x100))

        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return uc.reg_read(UC_ARM_REG_R0)

    for slot in [0, 1, 2]:
        exp = 0x20000000 + slot * 0x100
        o_ret = run_one(orig_code, slot)
        d_ret = run_one(comp, slot)
        assert o_ret == exp and d_ret == exp, f"slot {slot} mismatch: {hex(o_ret)} != {hex(d_ret)}"
    print(f"{name}: PASS")

def test_func_003f6228():
    addr = 0x003F6228
    print(f"--- Testing func_003f6228 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 64)
    tmp = ROOT / "build" / "test_31b_part14"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_003f6228", tmp)

    def run_one(code, has_cb, has_obj, has_sub):
        uc = create_emulator()
        uc.mem_write(addr, code)

        cb_storage = 0x0044E948
        page = cb_storage & ~0xFFF
        try:
            uc.mem_map(page, 0x2000)
        except Exception:
            pass

        cb_addr = 0x10084000
        obj = 0x10082000 if has_obj else 0
        sub_obj = 0x10083000 if has_sub else 0

        uc.mem_write(cb_storage + 4, struct.pack("<I", cb_addr if has_cb else 0))
        if has_obj:
            uc.mem_write(obj, b"\x00" * 0x20)
            uc.mem_write(obj + 4, struct.pack("<I", sub_obj))

        calls = []
        def cb_hook(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(arg0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, cb_hook, None, cb_addr, cb_addr)

        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return calls

    test_cases = [
        (False, True, True, []),
        (True, False, True, []),
        (True, True, False, [0x10082000]),
        (True, True, True, [0x10083000, 0x10082000]),
    ]

    for has_cb, has_obj, has_sub, exp_calls in test_cases:
        o_calls = run_one(orig_code, has_cb, has_obj, has_sub)
        d_calls = run_one(comp, has_cb, has_obj, has_sub)
        assert o_calls == exp_calls and d_calls == exp_calls, f"mismatch: {o_calls} != {d_calls}"
    print("func_003f6228: PASS")

def main():
    test_camp_func_003aaef0()
    test_ui_func_003bbed4()
    test_resource_finder("func_003e68bc", 0x003E68BC, 0x4002)
    test_resource_finder("func_003e6934", 0x003E6934, 0x4001)
    test_func_003f6228()
    print("ALL BATCH 31 B PART 14 TESTS PASSED!")

if __name__ == "__main__":
    main()
