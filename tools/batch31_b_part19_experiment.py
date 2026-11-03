#!/usr/bin/env python3
"""Differential test for batch 31 B part 19:
- func_003f5e40 (0x003F5E40, 76 B)
- camp_func_00311d20 (0x00311D20, 80 B)
- ui_func_0034f648 (0x0034F648, 80 B)
- engine_func_00357be4 (0x00357BE4, 80 B)
- func_0038007c (0x0038007C, 80 B)
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
        inst = struct.unpack_from("<I", data, reloc.offset)[0]
        if inst == 0:
            struct.pack_into("<I", data, reloc.offset, stub_addr)
            continue
        rel_off = stub_addr - (target_addr + reloc.offset + 8)
        if (inst & 0xFE000000) == 0xFA000000:
            h = (rel_off >> 1) & 1
            imm24 = (rel_off >> 2) & 0x00FFFFFF
            inst = 0xFA000000 | (h << 24) | imm24
        else:
            imm24 = (rel_off >> 2) & 0x00FFFFFF
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

def test_func_003f5e40():
    addr = 0x003F5E40
    print(f"--- Testing func_003f5e40 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 76)
    tmp = ROOT / "build" / "test_31b_part19"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003f5e40", tmp)
    assert not relocs
    decomp_code = comp

    FREE_FN_ADDR = 0x10086000
    PTR_HOLDER = 0x0044E930 # +4 is 0x0044E934

    test_cases = [
        (True, True, True),   # has_free_fn, has_node, has_field_4
        (True, True, False),  # has_free_fn, has_node, no field_4
        (False, True, True),  # no free_fn
        (True, False, False), # no node
    ]

    def run_one(code, has_free_fn, has_node, has_field_4):
        uc = create_emulator()
        uc.mem_write(addr, code)

        free_fn = FREE_FN_ADDR if has_free_fn else 0
        uc.mem_write(PTR_HOLDER + 4, struct.pack("<I", free_fn))

        freed = []
        def free_hook(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            freed.append(arg0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        if has_free_fn:
            uc.hook_add(UC_HOOK_CODE, free_hook, None, FREE_FN_ADDR, FREE_FN_ADDR)

        node = 0x10082000 if has_node else 0
        if has_node:
            p0 = 0x10083000
            p1 = 0x10084000 if has_field_4 else 0
            uc.mem_write(node, struct.pack("<II", p0, p1))

        uc.reg_write(UC_ARM_REG_R0, node)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        return freed

    for has_free, has_node, has_f4 in test_cases:
        o_freed = run_one(orig_code, has_free, has_node, has_f4)
        d_freed = run_one(decomp_code, has_free, has_node, has_f4)
        assert o_freed == d_freed, f"Mismatch for case ({has_free}, {has_node}, {has_f4}): orig {o_freed} vs decomp {d_freed}"

    print("func_003f5e40: PASS")

def test_camp_func_00311d20():
    addr = 0x00311D20
    print(f"--- Testing camp_func_00311d20 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 80)
    tmp = ROOT / "build" / "test_31b_part19"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_00311d20", tmp)

    FN_2B49D8 = 0x002B49D8
    FN_2B48DC = 0x002B48DC
    sym_map = {
        "script_vm_func_002b49d8": FN_2B49D8,
        "script_vm_func_002b48dc": FN_2B48DC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, arg0, arg1):
        uc = create_emulator()
        uc.mem_write(addr, code)

        table_addr = 0x10082000
        # total size: 4 + 8 * 5 = 44 (0x2C)
        uc.mem_write(table_addr, struct.pack("<I", 44))

        f_9d8_calls = []
        def f_9d8(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            f_9d8_calls.append(r0)
            uc.reg_write(UC_ARM_REG_R0, table_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        f_8dc_calls = []
        def f_8dc(uc, address, size, user_data):
            key_ptr = uc.reg_read(UC_ARM_REG_R0)
            base_ptr = uc.reg_read(UC_ARM_REG_R1)
            num = uc.reg_read(UC_ARM_REG_R2)
            elem_sz = uc.reg_read(UC_ARM_REG_R3)
            sp = uc.reg_read(UC_ARM_REG_SP)
            compar = struct.unpack("<I", uc.mem_read(sp, 4))[0]
            key_bytes = uc.mem_read(key_ptr, 4)
            k0, k1 = struct.unpack("<HH", key_bytes)
            f_8dc_calls.append((k0, k1, base_ptr, num, elem_sz, compar))
            uc.reg_write(UC_ARM_REG_R0, 0x10089999)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_9d8, None, FN_2B49D8, FN_2B49D8)
        uc.hook_add(UC_HOOK_CODE, f_8dc, None, FN_2B48DC, FN_2B48DC)

        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, f_9d8_calls, f_8dc_calls

    for a0, a1 in [(0x1234, 0x5678), (0, 0), (0xFFFF, 0xABCD)]:
        o_ret, o_9d8, o_8dc = run_one(orig_code, a0, a1)
        d_ret, d_9d8, d_8dc = run_one(decomp_code, a0, a1)
        assert o_ret == d_ret, f"ret mismatch: orig {o_ret} vs decomp {d_ret}"
        assert o_9d8 == d_9d8, f"f_9d8 mismatch: orig {o_9d8} vs decomp {d_9d8}"
        assert o_8dc == d_8dc, f"f_8dc mismatch: orig {o_8dc} vs decomp {d_8dc}"

    print("camp_func_00311d20: PASS")

def test_ui_func_0034f648():
    addr = 0x0034F648
    print(f"--- Testing ui_func_0034f648 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 80)
    tmp = ROOT / "build" / "test_31b_part19"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_0034f648", tmp)

    FN_2C5F58 = 0x002C5F58
    FN_34E01C = 0x0034E01C
    sym_map = {
        "ui_func_002c5f58": FN_2C5F58,
        "ui_func_0034e01c": FN_34E01C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code):
        uc = create_emulator()
        uc.mem_write(addr, code)

        obj = 0x10082000
        uc.mem_write(obj, b"\xBB" * 0xC0)

        calls = []
        def f_vec_ctor(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            arg2 = uc.reg_read(UC_ARM_REG_R2)
            arg3 = uc.reg_read(UC_ARM_REG_R3)
            calls.append((arg0, arg1, arg2, arg3))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_vec_ctor, None, FN_2C5F58, FN_2C5F58)

        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        mem = uc.mem_read(obj, 0xB0)
        return mem, calls

    o_mem, o_calls = run_one(orig_code)
    d_mem, d_calls = run_one(decomp_code)
    assert o_calls == d_calls, f"calls mismatch: orig {o_calls} vs decomp {d_calls}"
    assert o_mem == d_mem, "mem mismatch"
    print("ui_func_0034f648: PASS")

def test_engine_func_00357be4():
    addr = 0x00357BE4
    print(f"--- Testing engine_func_00357be4 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 80)
    tmp = ROOT / "build" / "test_31b_part19"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_00357be4", tmp)

    FN_357B2C = 0x00357B2C
    FN_359D8C = 0x00359D8C
    sym_map = {
        "engine_func_00357b2c": FN_357B2C,
        "ui_func_00359d8c": FN_359D8C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    test_cases = [
        # (ret_7b2c, ret_9d8c)
        (-1, 0x1234),
        (-100, 0x1234),
        (0, 42),
        (1, 100),
        (0x7FFFFFFF, 999),
    ]

    def run_one(code, ret_7b2c, ret_9d8c, a0, a1, a2, a3, a4, a5):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def f_7b2c(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            arg2 = uc.reg_read(UC_ARM_REG_R2)
            arg3 = uc.reg_read(UC_ARM_REG_R3)
            sp = uc.reg_read(UC_ARM_REG_SP)
            arg4 = struct.unpack("<I", uc.mem_read(sp, 4))[0]
            calls.append(("7b2c", arg0, arg1, arg2, arg3, arg4))
            uc.reg_write(UC_ARM_REG_R0, ret_7b2c & 0xFFFFFFFF)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_9d8c(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            arg2 = uc.reg_read(UC_ARM_REG_R2)
            calls.append(("9d8c", arg0, arg1, arg2))
            uc.reg_write(UC_ARM_REG_R0, ret_9d8c & 0xFFFFFFFF)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_7b2c, None, FN_357B2C, FN_357B2C)
        uc.hook_add(UC_HOOK_CODE, f_9d8c, None, FN_359D8C, FN_359D8C)

        sp = STACK_BASE + 0x8000
        # push 5th and 6th args on stack
        uc.mem_write(sp, struct.pack("<II", a4, a5))

        uc.reg_write(UC_ARM_REG_R0, a0)
        uc.reg_write(UC_ARM_REG_R1, a1)
        uc.reg_write(UC_ARM_REG_R2, a2)
        uc.reg_write(UC_ARM_REG_R3, a3)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, calls

    for ret_7b2c, ret_9d8c in test_cases:
        a0, a1, a2, a3, a4, a5 = 10, 20, 30, 40, 50, 60
        o_ret, o_calls = run_one(orig_code, ret_7b2c, ret_9d8c, a0, a1, a2, a3, a4, a5)
        d_ret, d_calls = run_one(decomp_code, ret_7b2c, ret_9d8c, a0, a1, a2, a3, a4, a5)
        assert o_ret == d_ret, f"ret mismatch: orig {hex(o_ret)} vs decomp {hex(d_ret)}"
        assert o_calls == d_calls, f"calls mismatch: orig {o_calls} vs decomp {d_calls}"

    print("engine_func_00357be4: PASS")

def test_func_0038007c():
    addr = 0x0038007C
    print(f"--- Testing func_0038007c ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 80)
    tmp = ROOT / "build" / "test_31b_part19"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0038007c", tmp)

    FN_37C314 = 0x0037C314
    sym_map = {"func_0037c314": FN_37C314}
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    test_cases = [
        # (flag_ca, flag_90, has_target, flag_c9)
        (1, 0, True, 0),    # flag_ca != 0 -> do nothing
        (0, 4, True, 0),    # flag_90 == 4 -> clear c5
        (0, 0, False, 0),   # no target -> flag_90 = 4, clear c5
        (0, 0, True, 1),    # target != null, flag_c9 != 0 -> no call, flag_90 = 4, clear c5
        (0, 0, True, 0),    # target != null, flag_c9 == 0 -> call(target, 1), flag_90 = 4, clear c5
        (0, 2, True, 0),    # flag_90 = 2 -> call(target, 1), flag_90 = 4, clear c5
    ]

    def run_one(code, flag_ca, flag_90, has_target, flag_c9):
        uc = create_emulator()
        uc.mem_write(addr, code)

        obj = 0x10082000
        target = 0x10084000 if has_target else 0

        mem = bytearray(0x150)
        mem[0xCA] = flag_ca
        mem[0x90] = flag_90
        mem[0xC9] = flag_c9
        mem[0xC5] = 0xAA # sentinel
        struct.pack_into("<I", mem, 0x134, target)
        uc.mem_write(obj, bytes(mem))

        calls = []
        def f_37c314(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append((arg0, arg1))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_37c314, None, FN_37C314, FN_37C314)

        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        out_90 = uc.mem_read(obj + 0x90, 1)[0]
        out_c5 = uc.mem_read(obj + 0xC5, 1)[0]
        return out_90, out_c5, calls

    for flag_ca, flag_90, has_target, flag_c9 in test_cases:
        o_90, o_c5, o_calls = run_one(orig_code, flag_ca, flag_90, has_target, flag_c9)
        d_90, d_c5, d_calls = run_one(decomp_code, flag_ca, flag_90, has_target, flag_c9)
        assert o_90 == d_90, f"flag_90 mismatch: orig {o_90} vs decomp {d_90}"
        assert o_c5 == d_c5, f"flag_c5 mismatch: orig {o_c5} vs decomp {d_c5}"
        assert o_calls == d_calls, f"calls mismatch: orig {o_calls} vs decomp {d_calls}"

    print("func_0038007c: PASS")

if __name__ == "__main__":
    test_func_003f5e40()
    test_camp_func_00311d20()
    test_ui_func_0034f648()
    test_engine_func_00357be4()
    test_func_0038007c()
    print("\nALL 5 FUNCTIONS IN PART 19 PASSED DIFFERENTIAL VERIFICATION!")
