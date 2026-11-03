#!/usr/bin/env python3
"""Differential test for batch 31 B part 13:
- func_0036d03c (0x0036D03C, 64 B)
- func_0036e2b8 (0x0036E2B8, 64 B)
- func_0036f338 (0x0036F338, 64 B)
- func_0037f880 (0x0037F880, 64 B)
- func_00380c70 (0x00380C70, 64 B)
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

def test_vtable_setter(name: str, addr: int, exp_vtable: int):
    print(f"--- Testing {name} ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 64)
    tmp = ROOT / "build" / "test_31b_part13"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function(name, tmp)

    def run_one(code, flag_val, has_inner):
        uc = create_emulator()
        uc.mem_write(addr, code)
        obj = 0x10082000
        sub_obj = 0x10083000
        vtable_addr = 0x10084000
        fn_addr = 0x10085000

        calls = []
        def vfunc_hook(uc, address, size, user_data):
            calls.append("vfunc")
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, vfunc_hook, None, fn_addr, fn_addr)

        # sub_obj->vtable[3] = fn_addr
        uc.mem_write(sub_obj, struct.pack("<I", vtable_addr))
        uc.mem_write(vtable_addr + 0xC, struct.pack("<I", fn_addr))

        # obj setup (flag is at offset 9, inner pointer is at 0x1C, sub_obj is at 4)
        uc.mem_write(obj, b"\x00" * 0x30)
        uc.mem_write(obj + 9, bytes([flag_val]))
        uc.mem_write(obj + 4, struct.pack("<I", sub_obj))
        uc.mem_write(obj + 0x1C, struct.pack("<I", 0x10086000 if has_inner else 0))

        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret_r0 = uc.reg_read(UC_ARM_REG_R0)
        written_vtable = struct.unpack("<I", uc.mem_read(obj, 4))[0]
        return ret_r0, written_vtable, calls

    for flag, has_in, exp_calls in [(1, True, ["vfunc"]), (0, True, []), (1, False, [])]:
        o_r0, o_vt, o_c = run_one(orig_code, flag, has_in)
        d_r0, d_vt, d_c = run_one(comp, flag, has_in)
        assert o_r0 == 0x10082000 and o_vt == exp_vtable and o_c == exp_calls
        assert d_r0 == 0x10082000 and d_vt == exp_vtable and d_c == exp_calls
    print(f"{name}: PASS")

def test_func_0036f338():
    addr = 0x0036F338
    print(f"--- Testing func_0036f338 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 64)
    tmp = ROOT / "build" / "test_31b_part13"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_0036f338", tmp)

    def run_one(code, cond_val, magic_val):
        uc = create_emulator()
        uc.mem_write(addr, code)

        holder = 0x10082000
        target = 0x10083000
        fn0_addr = 0x10084000
        fn1_addr = 0x10085000
        table_addr = 0x0044E8F0

        table_page = table_addr & ~0xFFF
        try:
            uc.mem_map(table_page, 0x2000)
        except Exception:
            pass

        uc.mem_write(table_addr, struct.pack("<II", fn0_addr, fn1_addr))
        uc.mem_write(holder, struct.pack("<I", target))
        uc.mem_write(target, struct.pack("<II", magic_val, cond_val))

        calls = []
        def fn_hook(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append((user_data, arg0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, fn_hook, "fn0", fn0_addr, fn0_addr)
        uc.hook_add(UC_HOOK_CODE, fn_hook, "fn1", fn1_addr, fn1_addr)

        uc.reg_write(UC_ARM_REG_R0, holder)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return calls

    test_cases = [
        (0, 0x80000000, []),                      # cond == 0 -> no call
        (1, 0x80000000, [("fn0", 0x10083000)]),   # magic == 0x80000000 -> fn0
        (5, 0x40000000, [("fn1", 0x10083000)]),   # magic == 0x40000000 -> fn1
        (1, 0x12345678, []),                      # other magic -> no call
    ]
    for cond, magic, exp_calls in test_cases:
        o_calls = run_one(orig_code, cond, magic)
        d_calls = run_one(comp, cond, magic)
        assert o_calls == exp_calls, f"orig failed {cond}, {hex(magic)}: {o_calls} != {exp_calls}"
        assert d_calls == exp_calls, f"comp failed {cond}, {hex(magic)}: {d_calls} != {exp_calls}"
    print("func_0036f338: PASS")

def test_func_0037f880():
    addr = 0x0037F880
    print(f"--- Testing func_0037f880 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 64)
    tmp = ROOT / "build" / "test_31b_part13"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0037f880", tmp)
    decomp_code = stage_body(comp, relocs, addr, {"func_0037da70": 0x0037DA70})

    def run_one(code, val, active_indices):
        uc = create_emulator()
        uc.mem_write(addr, code)

        obj = 0x10082000
        fn_addr = 0x0037DA70

        calls = []
        def child_hook(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append((arg0, arg1))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, child_hook, None, fn_addr, fn_addr)

        uc.mem_write(obj, b"\x00" * 0x100)
        for idx in active_indices:
            child_ptr = 0x10084000 + idx * 0x10
            uc.mem_write(obj + 0x8C + idx * 4, struct.pack("<I", child_ptr))

        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_R1, val)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        written_val = struct.unpack("<B", uc.mem_read(obj + 0x0E, 1))[0]
        return written_val, calls

    test_cases = [
        (0x42, [0, 5, 15]),
        (0xFF, []),
        (0x01, list(range(16))),
    ]

    for val, active in test_cases:
        o_val, o_calls = run_one(orig_code, val, active)
        d_val, d_calls = run_one(decomp_code, val, active)
        assert o_val == (val & 0xFF) and o_calls == [(0x10084000 + i * 0x10, val) for i in active]
        assert d_val == (val & 0xFF) and d_calls == [(0x10084000 + i * 0x10, val) for i in active]
    print("func_0037f880: PASS")

def test_func_00380c70():
    addr = 0x00380C70
    print(f"--- Testing func_00380c70 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 64)
    tmp = ROOT / "build" / "test_31b_part13"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00380c70", tmp)
    decomp_code = stage_body(comp, relocs, addr, {"func_002358dc": 0x002358DC})

    def run_one(code, flags, val10):
        uc = create_emulator()
        uc.mem_write(addr, code)

        obj = 0x10082000
        table_addr = 0x00471C20
        helper_addr = 0x002358DC
        fn_base = 0x10084000

        # Ensure page for table_addr is mapped
        table_page = table_addr & ~0xFFF
        try:
            uc.mem_map(table_page, 0x2000)
        except Exception:
            pass

        # Table of 8 functions
        table_entries = [fn_base + i * 0x10 for i in range(8)]
        uc.mem_write(table_addr, struct.pack("<8I", *table_entries))

        calls = []
        def helper_hook(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("helper", arg0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def dispatch_hook(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append((f"dispatch_{user_data}", arg0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_R0, 0xCAFE0000 + user_data)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, helper_hook, None, helper_addr, helper_addr)
        for i, target_fn in enumerate(table_entries):
            uc.hook_add(UC_HOOK_CODE, dispatch_hook, i, target_fn, target_fn)

        uc.mem_write(obj, b"\x00" * 0x30)
        uc.mem_write(obj + 0x0C, struct.pack("<I", flags))
        uc.mem_write(obj + 0x10, struct.pack("<I", val10))

        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret_r0 = uc.reg_read(UC_ARM_REG_R0)
        return ret_r0, calls

    test_cases = [
        # (flags, val10): if flags & 1 -> returns val10 directly
        (1, 0x11223344),
        (0x1F, 0x55667788),
        # if !(flags & 1): calls table[(flags & 0x38) >> 3](obj + 0x10)
        (0 << 3, 0x1000),
        (3 << 3, 0x2000),
        (7 << 3, 0x3000),
        ((4 << 3) | 0x100, 0x4000),
    ]

    for flags, val10 in test_cases:
        o_ret, o_calls = run_one(orig_code, flags, val10)
        d_ret, d_calls = run_one(decomp_code, flags, val10)
        assert o_ret == d_ret, f"ret mismatch: {hex(o_ret)} != {hex(d_ret)}"
        assert o_calls == d_calls, f"calls mismatch: {o_calls} != {d_calls}"
    print("func_00380c70: PASS")

def main():
    test_vtable_setter("func_0036d03c", 0x0036D03C, 0x00421244)
    test_vtable_setter("func_0036e2b8", 0x0036E2B8, 0x00421304)
    test_func_0036f338()
    test_func_0037f880()
    test_func_00380c70()
    print("ALL BATCH 31 B PART 13 TESTS PASSED!")

if __name__ == "__main__":
    main()
