#!/usr/bin/env python3
"""Differential test for batch 31 C part 1:
- battle_func_00201040 (0x00201040, 168 B)
- camp_func_002010e8 (0x002010E8, 164 B)
- script_vm_func_0020118c (0x0020118C, 168 B)
- ui_func_00212394 (0x00212394, 168 B)
- script_vm_func_002143cc (0x002143CC, 160 B)
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
SOURCE = ROOT / "src/engine/leaf_batch31_c.cpp"

with open(ORIG_BIN, "rb") as f:
    ORIG_DATA = f.read()

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch31_c.o"
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

def test_battle_func_00201040():
    addr = 0x00201040
    print(f"--- Testing battle_func_00201040 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 168)
    tmp = ROOT / "build" / "test_31c_part01"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("battle_func_00201040", tmp)

    FN_2BF41C = 0x002BF41C
    FN_2B756C = 0x002B756C
    FN_2B7510 = 0x002B7510
    FN_2B74C4 = 0x002B74C4
    sym_map = {
        "func_002bf41c": FN_2BF41C,
        "func_002b756c": FN_2B756C,
        "func_002b7510": FN_2B7510,
        "func_002b74c4": FN_2B74C4,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, has_mgr: bool, count: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        holder = 0x0043DED0
        mgr = 0x10082000 if has_mgr else 0
        uc.mem_write(holder, struct.pack("<I", mgr))

        calls = []
        def f_41c(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("41c", arg0))
            # return 1 for odd items, 0 for even
            ret = 1 if (arg0 & 1) else 0
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_56c(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("56c", arg0))
            # return 4 for item == 3, 0 otherwise
            ret = 4 if arg0 == 0x10083003 else 0
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_510(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("510", arg0, arg1))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_4c4(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("4c4", arg0, arg1))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_41c, None, FN_2BF41C, FN_2BF41C)
        uc.hook_add(UC_HOOK_CODE, f_56c, None, FN_2B756C, FN_2B756C)
        uc.hook_add(UC_HOOK_CODE, f_510, None, FN_2B7510, FN_2B7510)
        uc.hook_add(UC_HOOK_CODE, f_4c4, None, FN_2B74C4, FN_2B74C4)

        if has_mgr:
            mem = bytearray(0x80)
            struct.pack_into("<i", mem, 0x2C, count)
            # pointers in items1 (0x04..0x28)
            for i in range(max(0, count)):
                struct.pack_into("<I", mem, 0x04 + i * 4, 0x10083000 + i)
            # pointers in items2 (0x34..0x5C)
            for i in range(10):
                struct.pack_into("<I", mem, 0x34 + i * 4, 0x10084000 + i)
            uc.mem_write(mgr, bytes(mem))

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return calls

    for has_mgr in [False, True]:
        for cnt in [0, -1, 3]:
            o_calls = run_one(orig_code, has_mgr, cnt)
            d_calls = run_one(decomp_code, has_mgr, cnt)
            assert o_calls == d_calls, f"calls mismatch (has_mgr={has_mgr}, cnt={cnt}): orig {o_calls} vs decomp {d_calls}"

    print("battle_func_00201040: PASS")

def test_camp_func_002010e8():
    addr = 0x002010E8
    print(f"--- Testing camp_func_002010e8 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 164)
    tmp = ROOT / "build" / "test_31c_part01"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_002010e8", tmp)

    FN_2546C4 = 0x002546C4
    FN_2AC2F4 = 0x002AC2F4
    FN_2C0E9C = 0x002C0E9C
    FN_2C0E4C = 0x002C0E4C
    sym_map = {
        "script_vm_func_002546c4": FN_2546C4,
        "Tbb_GetSubTable": FN_2AC2F4,
        "Tbb_GetPayloadData": FN_2C0E9C,
        "Tbb_GetRowCount": FN_2C0E4C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, outer_count, row_count):
        uc = create_emulator()
        uc.mem_write(addr, code)

        tbb = 0x10082000
        payload = 0x10083000

        # Create row_count entries of 0x2C bytes
        mem = bytearray(0x2C * max(1, row_count))
        for r in range(row_count):
            mem[r * 0x2C + 0x2A] = 1 # non-zero flag
            struct.pack_into("<h", mem, r * 0x2C + 0x20, 100 + r)
        uc.mem_write(payload, bytes(mem))

        sub_table_ptr = 0x10085000
        first_word_ptr = 0x10086000

        def f_6c4(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, outer_count)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        last_sub_idx = 0
        def f_2f4(uc, address, size, user_data):
            nonlocal last_sub_idx
            last_sub_idx = uc.reg_read(UC_ARM_REG_R1)
            uc.reg_write(UC_ARM_REG_R0, sub_table_ptr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_e9c(uc, address, size, user_data):
            if last_sub_idx == 0:
                ret = payload
            else:
                # Return first word buffer with target value
                val = 100 if last_sub_idx == 2 else 999
                uc.mem_write(first_word_ptr, struct.pack("<I", val))
                ret = first_word_ptr
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_e4c(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, row_count)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_6c4, None, FN_2546C4, FN_2546C4)
        uc.hook_add(UC_HOOK_CODE, f_2f4, None, FN_2AC2F4, FN_2AC2F4)
        uc.hook_add(UC_HOOK_CODE, f_e9c, None, FN_2C0E9C, FN_2C0E9C)
        uc.hook_add(UC_HOOK_CODE, f_e4c, None, FN_2C0E4C, FN_2C0E4C)

        uc.reg_write(UC_ARM_REG_R0, tbb)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        out_payload = uc.mem_read(payload, 0x2C * max(1, row_count))
        return out_payload

    for oc, rc in [(0, 0), (1, 2), (4, 2)]:
        o_p = run_one(orig_code, oc, rc)
        d_p = run_one(decomp_code, oc, rc)
        assert o_p == d_p, f"payload mismatch (oc={oc}, rc={rc})"

    print("camp_func_002010e8: PASS")

def test_script_vm_func_0020118c():
    addr = 0x0020118C
    print(f"--- Testing script_vm_func_0020118c ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 168)
    tmp = ROOT / "build" / "test_31c_part01"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_0020118c", tmp)

    FN_2B49D8 = 0x002B49D8
    FN_2546C4 = 0x002546C4
    FN_2C0EC4 = 0x002C0EC4
    FN_2C0E9C = 0x002C0E9C
    FN_2C0E4C = 0x002C0E4C
    sym_map = {
        "script_vm_func_002b49d8": FN_2B49D8,
        "script_vm_func_002546c4": FN_2546C4,
        "Tbb_GetGlobalSubTable": FN_2C0EC4,
        "Tbb_GetPayloadData": FN_2C0E9C,
        "Tbb_GetRowCount": FN_2C0E4C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, outer_count, row_count):
        uc = create_emulator()
        uc.mem_write(addr, code)

        payload = 0x10083000
        mem = bytearray(0x2C * max(1, row_count))
        for r in range(row_count):
            mem[r * 0x2C + 0x2A] = 1
            struct.pack_into("<h", mem, r * 0x2C + 0x20, 100 + r)
        uc.mem_write(payload, bytes(mem))

        sub_table_ptr = 0x10085000
        first_word_ptr = 0x10086000

        calls = []
        def f_9d8(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("9d8", arg0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_6c4(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, outer_count)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        last_sub_idx = 0
        def f_ec4(uc, address, size, user_data):
            nonlocal last_sub_idx
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("ec4", arg0, arg1))
            last_sub_idx = arg1
            uc.reg_write(UC_ARM_REG_R0, sub_table_ptr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_e9c(uc, address, size, user_data):
            if last_sub_idx == 0:
                ret = payload
            else:
                val = 100 if last_sub_idx == 2 else 999
                uc.mem_write(first_word_ptr, struct.pack("<I", val))
                ret = first_word_ptr
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_e4c(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, row_count)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_9d8, None, FN_2B49D8, FN_2B49D8)
        uc.hook_add(UC_HOOK_CODE, f_6c4, None, FN_2546C4, FN_2546C4)
        uc.hook_add(UC_HOOK_CODE, f_ec4, None, FN_2C0EC4, FN_2C0EC4)
        uc.hook_add(UC_HOOK_CODE, f_e9c, None, FN_2C0E9C, FN_2C0E9C)
        uc.hook_add(UC_HOOK_CODE, f_e4c, None, FN_2C0E4C, FN_2C0E4C)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        out_payload = uc.mem_read(payload, 0x2C * max(1, row_count))
        return out_payload, calls

    for oc, rc in [(0, 0), (1, 2), (4, 2)]:
        o_p, o_calls = run_one(orig_code, oc, rc)
        d_p, d_calls = run_one(decomp_code, oc, rc)
        assert o_p == d_p, f"payload mismatch (oc={oc}, rc={rc})"
        assert o_calls == d_calls, f"calls mismatch (oc={oc}, rc={rc})"

    print("script_vm_func_0020118c: PASS")

def test_ui_func_00212394():
    addr = 0x00212394
    print(f"--- Testing ui_func_00212394 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 168)
    tmp = ROOT / "build" / "test_31c_part01"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_00212394", tmp)

    FN_2BF460 = 0x002BF460
    sym_map = {"ui_func_002bf460": FN_2BF460}
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, rx, ry, rw, rh, off_x, off_y, arg3, text):
        uc = create_emulator()
        uc.mem_write(addr, code)

        rect_ptr = 0x10082000
        text_ptr = 0x10083000
        uc.mem_write(rect_ptr, struct.pack("<ffff", rx, ry, rw, rh))
        uc.mem_write(text_ptr, text.encode("ascii") + b"\x00")

        calls = []
        def f_460(uc, address, size, user_data):
            a0 = uc.reg_read(UC_ARM_REG_R0)
            a1 = uc.reg_read(UC_ARM_REG_R1)
            a2 = uc.reg_read(UC_ARM_REG_R2)
            a3 = uc.reg_read(UC_ARM_REG_R3)
            sp = uc.reg_read(UC_ARM_REG_SP)
            a4, a5 = struct.unpack("<II", uc.mem_read(sp, 8))
            calls.append((a0, a1, a2, a3, a4, a5))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_460, None, FN_2BF460, FN_2BF460)

        sp = STACK_BASE + 0x8000
        uc.mem_write(sp, struct.pack("<I", text_ptr))

        uc.reg_write(UC_ARM_REG_R0, rect_ptr)
        uc.reg_write(UC_ARM_REG_R1, off_x)
        uc.reg_write(UC_ARM_REG_R2, off_y)
        uc.reg_write(UC_ARM_REG_R3, arg3)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return calls

    test_cases = [
        (10.0, 20.0, 30.0, 40.0, 5, 10, 0x99, "123"),
        (0.0, 0.0, 0.0, 0.0, 0, 0, 0x12, "0 9"),
        (100.0, 200.0, 50.0, 50.0, -10, -20, 0x00, ""),
    ]

    for rx, ry, rw, rh, ox, oy, a3, txt in test_cases:
        o_calls = run_one(orig_code, rx, ry, rw, rh, ox, oy, a3, txt)
        d_calls = run_one(decomp_code, rx, ry, rw, rh, ox, oy, a3, txt)
        assert o_calls == d_calls, f"calls mismatch for '{txt}': orig {o_calls} vs decomp {d_calls}"

    print("ui_func_00212394: PASS")

def test_script_vm_func_002143cc():
    addr = 0x002143CC
    print(f"--- Testing script_vm_func_002143cc ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 160)
    tmp = ROOT / "build" / "test_31c_part01"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_002143cc", tmp)

    FN_296F60 = 0x00296F60
    FN_289640 = 0x00289640
    FN_254514 = 0x00254514
    FN_28EFE0 = 0x0028EFE0
    FN_2C0128 = 0x002C0128
    FN_2B49D8 = 0x002B49D8
    FN_2544FC = 0x002544FC
    FN_25506C = 0x0025506C
    FN_348C74 = 0x00348C74

    sym_map = {
        "engine_func_00296f60": FN_296F60,
        "engine_func_00289640": FN_289640,
        "ui_func_00254514": FN_254514,
        "script_vm_func_0028efe0": FN_28EFE0,
        "script_vm_func_002c0128": FN_2C0128,
        "script_vm_func_002b49d8": FN_2B49D8,
        "ui_func_002544fc": FN_2544FC,
        "script_vm_func_0025506c": FN_25506C,
        "engine_func_00348c74": FN_348C74,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, f89640_ret, f5506c_ret):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def make_hook(name, ret_val=0):
            def h(uc, address, size, user_data):
                a0 = uc.reg_read(UC_ARM_REG_R0)
                a1 = uc.reg_read(UC_ARM_REG_R1)
                a2 = uc.reg_read(UC_ARM_REG_R2)
                calls.append((name, a0, a1, a2))
                uc.reg_write(UC_ARM_REG_R0, ret_val)
                lr = uc.reg_read(UC_ARM_REG_LR)
                uc.reg_write(UC_ARM_REG_PC, lr)
            return h

        uc.hook_add(UC_HOOK_CODE, make_hook("296f60", 0x1234), None, FN_296F60, FN_296F60)
        uc.hook_add(UC_HOOK_CODE, make_hook("289640", f89640_ret), None, FN_289640, FN_289640)
        uc.hook_add(UC_HOOK_CODE, make_hook("254514"), None, FN_254514, FN_254514)
        uc.hook_add(UC_HOOK_CODE, make_hook("28efe0"), None, FN_28EFE0, FN_28EFE0)
        uc.hook_add(UC_HOOK_CODE, make_hook("2c0128"), None, FN_2C0128, FN_2C0128)
        uc.hook_add(UC_HOOK_CODE, make_hook("2b49d8", 0x10085000), None, FN_2B49D8, FN_2B49D8)
        uc.hook_add(UC_HOOK_CODE, make_hook("2544fc", 5), None, FN_2544FC, FN_2544FC)
        uc.hook_add(UC_HOOK_CODE, make_hook("25506c", f5506c_ret), None, FN_25506C, FN_25506C)
        uc.hook_add(UC_HOOK_CODE, make_hook("348c74"), None, FN_348C74, FN_348C74)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, calls

    for ret_89, ret_55 in [(0, 1), (0, 0), (1, 1), (1, 0)]:
        o_ret, o_calls = run_one(orig_code, ret_89, ret_55)
        d_ret, d_calls = run_one(decomp_code, ret_89, ret_55)
        assert o_ret == d_ret, f"ret mismatch: orig {o_ret} vs decomp {d_ret}"
        assert o_calls == d_calls, f"calls mismatch: orig {o_calls} vs decomp {d_calls}"

    print("script_vm_func_002143cc: PASS")

if __name__ == "__main__":
    test_battle_func_00201040()
    test_camp_func_002010e8()
    test_script_vm_func_0020118c()
    test_ui_func_00212394()
    test_script_vm_func_002143cc()
    print("\nALL 5 FUNCTIONS IN LEAF_BATCH31_C PART 01 PASSED DIFFERENTIAL VERIFICATION!")
