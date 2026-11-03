#!/usr/bin/env python3
"""Differential test for batch 31 B part 15:
- func_003f6368 (0x003F6368, 64 B)
- engine_func_00341c04 (0x00341C04, 68 B)
- engine_func_00351e24 (0x00351E24, 68 B)
- func_00362374 (0x00362374, 68 B)
- func_00376c88 (0x00376C88, 68 B)
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

def test_func_003f6368():
    addr = 0x003F6368
    print(f"--- Testing func_003f6368 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 64)
    tmp = ROOT / "build" / "test_31b_part15"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_003f6368", tmp)

    def run_one(code, has_cb, has_obj, has_sub):
        uc = create_emulator()
        uc.mem_write(addr, code)

        cb_storage = 0x0044E960
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
            uc.mem_write(obj, b"\x00" * 0x30)
            uc.mem_write(obj + 0x10, struct.pack("<I", sub_obj))

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
    print("func_003f6368: PASS")

def test_engine_func_00341c04():
    addr = 0x00341C04
    print(f"--- Testing engine_func_00341c04 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 68)
    tmp = ROOT / "build" / "test_31b_part15"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_00341c04", tmp)

    fmt_str_addr = 0x10087000
    sym_map = {
        "ui_func_002be7fc": 0x002BE7FC,
        "engine_func_0029bddc": 0x0029BDDC,
        "engine_func_002a06c8": 0x002A06C8,
        "": fmt_str_addr,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code):
        uc = create_emulator()
        uc.mem_write(addr, code)

        obj = 0x10082000
        name_str = 0x10083000
        uc.mem_write(name_str, b"model_test\x00")
        uc.mem_write(obj, b"\x00" * 0x40)
        uc.mem_write(fmt_str_addr, b"%s.bam\x00")

        calls = []
        def sprintf_hook(uc, address, size, user_data):
            buf = uc.reg_read(UC_ARM_REG_R0)
            fmt = uc.reg_read(UC_ARM_REG_R1)
            arg = uc.reg_read(UC_ARM_REG_R2)
            fmt_str = uc.mem_read(fmt, 7).split(b"\x00")[0].decode("ascii", errors="ignore")
            arg_str = uc.mem_read(arg, 16).split(b"\x00")[0].decode("ascii", errors="ignore")
            calls.append(("sprintf", fmt_str, arg_str))
            uc.mem_write(buf, (arg_str + ".bam\x00").encode("ascii"))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def bddc_hook(uc, address, size, user_data):
            buf = uc.reg_read(UC_ARM_REG_R0)
            flag = uc.reg_read(UC_ARM_REG_R1)
            b_str = uc.mem_read(buf, 20).split(b"\x00")[0].decode("ascii", errors="ignore")
            calls.append(("bddc", b_str, flag))
            uc.reg_write(UC_ARM_REG_R0, 0x20004000)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def a06c8_hook(uc, address, size, user_data):
            handle = uc.reg_read(UC_ARM_REG_R0)
            val = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("a06c8", handle, val))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, sprintf_hook, None, 0x002BE7FC, 0x002BE7FC)
        uc.hook_add(UC_HOOK_CODE, bddc_hook, None, 0x0029BDDC, 0x0029BDDC)
        uc.hook_add(UC_HOOK_CODE, a06c8_hook, None, 0x002A06C8, 0x002A06C8)

        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_R1, name_str)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        written_handle = struct.unpack("<I", uc.mem_read(obj + 0x28, 4))[0]
        return written_handle, calls

    o_h, o_calls = run_one(orig_code)
    d_h, d_calls = run_one(decomp_code)
    assert o_h == 0x20004000 and d_h == 0x20004000
    assert o_calls == d_calls
    print("engine_func_00341c04: PASS")

def test_engine_func_00351e24():
    addr = 0x00351E24
    print(f"--- Testing engine_func_00351e24 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 68)
    tmp = ROOT / "build" / "test_31b_part15"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_00351e24", tmp)

    sym_map = {
        "engine_func_002c5fbc": 0x002C5FBC,
        "camp_func_0035a1a0": 0x0035A1A0,
        "func_001466bc": 0x001466BC,
        "func_00351ef8": 0x00351EF8,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, has_res):
        uc = create_emulator()
        uc.mem_write(addr, code)

        calls = []
        def f_2c5fbc(uc, address, size, user_data):
            calls.append("2c5fbc")
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_35a1a0(uc, address, size, user_data):
            calls.append("35a1a0")
            uc.reg_write(UC_ARM_REG_R0, 0x10085000 if has_res else 0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_1466bc(uc, address, size, user_data):
            calls.append("1466bc")
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_351ef8(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("351ef8", arg0, arg1))
            uc.reg_write(UC_ARM_REG_R0, 0x1234)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_2c5fbc, None, 0x002C5FBC, 0x002C5FBC)
        uc.hook_add(UC_HOOK_CODE, f_35a1a0, None, 0x0035A1A0, 0x0035A1A0)
        uc.hook_add(UC_HOOK_CODE, f_1466bc, None, 0x001466BC, 0x001466BC)
        uc.hook_add(UC_HOOK_CODE, f_351ef8, None, 0x00351EF8, 0x00351EF8)

        uc.reg_write(UC_ARM_REG_R0, 0x1111)
        uc.reg_write(UC_ARM_REG_R1, 0x2222)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, calls

    for has_res in [False, True]:
        o_ret, o_calls = run_one(orig_code, has_res)
        d_ret, d_calls = run_one(decomp_code, has_res)
        assert o_ret == d_ret and o_calls == d_calls, f"mismatch: {hex(o_ret)} != {hex(d_ret)}"
    print("engine_func_00351e24: PASS")

def test_func_00362374():
    addr = 0x00362374
    print(f"--- Testing func_00362374 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 68)
    tmp = ROOT / "build" / "test_31b_part15"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_00362374", tmp)

    def run_one(code, has_sub, has_val14):
        uc = create_emulator()
        uc.mem_write(addr, code)

        obj = 0x10082000
        sub_obj = 0x10083000 if has_sub else 0
        val14 = 0x10084000 if has_val14 else 0
        vtable = 0x10085000
        fn_addr = 0x10086000

        uc.mem_write(obj, b"\x00" * 0x30)
        uc.mem_write(obj + 0x10, struct.pack("<I", sub_obj))
        uc.mem_write(obj + 0x14, struct.pack("<I", val14))

        if has_sub:
            uc.mem_write(sub_obj, struct.pack("<I", vtable))
            uc.mem_write(vtable + 0xC, struct.pack("<I", fn_addr))

        calls = []
        def vfunc_hook(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(arg0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, vfunc_hook, None, fn_addr, fn_addr)

        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        w_vt = struct.unpack("<I", uc.mem_read(obj, 4))[0]
        w_18 = struct.unpack("<I", uc.mem_read(obj + 0x18, 4))[0]
        return ret, w_vt, w_18, calls

    for has_s, has_v, exp_calls in [(True, True, [0x10083000]), (False, True, []), (True, False, [])]:
        o_ret, o_vt, o_18, o_calls = run_one(orig_code, has_s, has_v)
        d_ret, d_vt, d_18, d_calls = run_one(comp, has_s, has_v)
        assert o_ret == 0x10082000
        assert o_ret == d_ret and o_vt == 0x00420C4C and d_vt == 0x00420C4C
        assert o_18 == (0x10084000 if has_v else 0) and d_18 == (0x10084000 if has_v else 0)
        assert o_calls == exp_calls and d_calls == exp_calls
    print("func_00362374: PASS")

def test_func_00376c88():
    addr = 0x00376C88
    print(f"--- Testing func_00376c88 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 68)
    tmp = ROOT / "build" / "test_31b_part15"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_00376c88", tmp)

    sym_map = {
        "func_00379ed4": 0x00379ED4,
        "func_00379afc": 0x00379AFC,
        "engine_func_002bf774": 0x002BF774,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, has_r4):
        uc = create_emulator()
        uc.mem_write(addr, code)

        dst_obj = 0x10082000
        src_obj = 0x10083000
        r4_obj = 0x10084000 if has_r4 else 0

        uc.mem_write(dst_obj, b"\x00" * 0x30)
        uc.mem_write(src_obj, b"\x00" * 0x30)
        uc.mem_write(src_obj + 4, struct.pack("<I", r4_obj))

        calls = []
        def f_ed4(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("ed4", arg0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_afc(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("afc", arg0, arg1))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_bf774(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            arg2 = uc.reg_read(UC_ARM_REG_R2)
            calls.append(("bf774", arg0, arg1, arg2))
            uc.reg_write(UC_ARM_REG_R0, 0xFEED)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_ed4, None, 0x00379ED4, 0x00379ED4)
        uc.hook_add(UC_HOOK_CODE, f_afc, None, 0x00379AFC, 0x00379AFC)
        uc.hook_add(UC_HOOK_CODE, f_bf774, None, 0x002BF774, 0x002BF774)

        uc.reg_write(UC_ARM_REG_R0, dst_obj)
        uc.reg_write(UC_ARM_REG_R1, src_obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, calls

    for has_r4 in [False, True]:
        o_ret, o_calls = run_one(orig_code, has_r4)
        d_ret, d_calls = run_one(decomp_code, has_r4)
        assert o_ret == d_ret and o_calls == d_calls, f"mismatch: {hex(o_ret)} != {hex(d_ret)}"
    print("func_00376c88: PASS")

def main():
    test_func_003f6368()
    test_engine_func_00341c04()
    test_engine_func_00351e24()
    test_func_00362374()
    test_func_00376c88()
    print("ALL BATCH 31 B PART 15 TESTS PASSED!")

if __name__ == "__main__":
    main()
