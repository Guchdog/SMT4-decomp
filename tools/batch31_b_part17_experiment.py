#!/usr/bin/env python3
"""Differential test for batch 31 B part 17:
- func_003f752c (0x003F752C, 68 B compound: 0x3f752c, 0x3f7534, 0x3f7558)
- ui_func_00355f78 (0x00355F78, 72 B)
- func_0037c424 (0x0037C424, 72 B)
- engine_func_00324010 (0x00324010, 76 B)
- nn_sdk_func_00351b7c (0x00351B7C, 76 B)
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
    UC_HOOK_INTR,
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

def test_func_003f752c():
    print("--- Testing func_003f752c compound (0x003F752C, 68 B) ---")
    tmp = ROOT / "build" / "test_31b_part17"
    tmp.mkdir(parents=True, exist_ok=True)
    comp_a, relocs_a = compile_function("func_003f752c", tmp)
    comp_b, _ = compile_function("func_003f7534", tmp)
    comp_c, _ = compile_function("func_003f7558", tmp)

    orig_bytes_a = load_original_bytes(0x003F752C, 8)
    orig_bytes_b = load_original_bytes(0x003F7534, 36)
    orig_bytes_c = load_original_bytes(0x003F7558, 24)

    sym_map = {"nn_sdk_func_002c4244": 0x002C4244}
    decomp_a = stage_body(comp_a, relocs_a, 0x003F752C, sym_map)

    # Sub A
    def run_a(code):
        uc = create_emulator()
        uc.mem_write(0x003F752C, code)
        obj = 0x10082000
        inner = 0x10083000
        uc.mem_write(obj, b"\x00" * 0x20)
        uc.mem_write(obj + 0x10, struct.pack("<I", inner))

        calls = []
        def f_4244(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(arg0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_4244, None, 0x002C4244, 0x002C4244)
        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(0x003F752C, 0x003E0000, timeout=1000000)
        return calls

    oa = run_a(orig_bytes_a)
    da = run_a(decomp_a)
    assert oa == [0x10083000] and da == [0x10083000]

    # Sub B
    def run_b(code):
        uc = create_emulator()
        uc.mem_write(0x003F7534, code)
        obj = 0x10082000
        uc.mem_write(obj, b"\xFF" * 0x30)
        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(0x003F7534, 0x003E0000, timeout=1000000)
        return uc.mem_read(obj, 0x10)

    ob = run_b(orig_bytes_b)
    db = run_b(comp_b)
    assert ob == db and struct.unpack("<IIII", ob) == (0, 0x10082020, 0x10082020, 0x80000001)

    # Sub C
    def run_c(code):
        uc = create_emulator()
        uc.mem_write(0x003F7558, code)
        obj = 0x10082000
        uc.mem_write(obj, b"\xFF" * 0x30)
        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(0x003F7558, 0x003E0000, timeout=1000000)
        return uc.mem_read(obj, 0x0C)

    oc = run_c(orig_bytes_c)
    dc = run_c(comp_c)
    assert oc == dc and struct.unpack("<III", oc) == (0, 0x10082004, 0x10082004)
    print("func_003f752c: PASS")

def test_ui_func_00355f78():
    addr = 0x00355F78
    print(f"--- Testing ui_func_00355f78 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 72)
    tmp = ROOT / "build" / "test_31b_part17"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("ui_func_00355f78", tmp)

    def run_one(code, has_obj, method_ret):
        uc = create_emulator()
        uc.mem_write(addr, code)

        out_ptr = 0x10082000
        obj = 0x10083000 if has_obj else 0
        vtable = 0x10084000
        fn_addr = 0x10085000

        uc.mem_write(out_ptr, struct.pack("<I", 0xDEADBEEF))
        if has_obj:
            uc.mem_write(obj, struct.pack("<I", vtable))
            uc.mem_write(vtable, struct.pack("<I", fn_addr))

        calls = []
        def m0_hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            calls.append(("m0", r0, r2, r3))
            uc.mem_write(r1, struct.pack("<I", 0x7777))
            uc.reg_write(UC_ARM_REG_R0, method_ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, m0_hook, None, fn_addr, fn_addr)

        uc.reg_write(UC_ARM_REG_R0, out_ptr)
        uc.reg_write(UC_ARM_REG_R1, obj)
        uc.reg_write(UC_ARM_REG_R2, 0)
        uc.reg_write(UC_ARM_REG_R3, 0x33)
        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.mem_write(sp, struct.pack("<I", 0x44))
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        out_val = struct.unpack("<I", uc.mem_read(out_ptr, 4))[0]
        return ret, out_val, calls

    for has_o, m_ret in [(False, 0), (True, 0), (True, 0x80000001)]:
        o_ret, o_val, o_calls = run_one(orig_code, has_o, m_ret)
        d_ret, d_val, d_calls = run_one(comp, has_o, m_ret)
        assert o_ret == d_ret and o_val == d_val and o_calls == d_calls, f"mismatch: {hex(o_ret)} != {hex(d_ret)}"
    print("ui_func_00355f78: PASS")

def test_func_0037c424():
    addr = 0x0037C424
    print(f"--- Testing func_0037c424 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 72)
    tmp = ROOT / "build" / "test_31b_part17"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0037c424", tmp)

    sym_map = {"func_00360320": 0x00360320}
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, flag_val, count_val):
        uc = create_emulator()
        uc.mem_write(addr, code)

        obj = 0x10082000
        uc.mem_write(obj, b"\x00" * 0x50)
        uc.mem_write(obj + 0x40, struct.pack("<I", flag_val))
        uc.mem_write(obj + 8, struct.pack("<i", count_val))

        items = [0x10083000 + i * 0x10 for i in range(max(0, count_val))]
        for i, it in enumerate(items):
            uc.mem_write(obj + i * 4, struct.pack("<I", it if i % 2 == 0 else 0))

        calls = []
        def f_320(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append((arg0, arg1))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_320, None, 0x00360320, 0x00360320)
        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return calls

    for f, c in [(1, 5), (0, 0), (2, 4), (0, -1)]:
        o_calls = run_one(orig_code, f, c)
        d_calls = run_one(decomp_code, f, c)
        assert o_calls == d_calls, f"mismatch: {o_calls} != {d_calls}"
    print("func_0037c424: PASS")

def test_engine_func_00324010():
    addr = 0x00324010
    print(f"--- Testing engine_func_00324010 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 76)
    tmp = ROOT / "build" / "test_31b_part17"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_00324010", tmp)

    sym_map = {
        "engine_func_00296f60": 0x00296F60,
        "engine_func_002c1f28": 0x002C1F28,
        "func_00221b78": 0x00221B78,
        "engine_func_002c4360": 0x002C4360,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, has_ptr, has_a, c1f28_ret):
        uc = create_emulator()
        uc.mem_write(addr, code)

        ptr = 0x10082000 if has_ptr else 0
        a = 0x10083000 if has_a else 0
        b = 0x10084000

        if has_ptr:
            uc.mem_write(ptr, struct.pack("<II", a, b))

        calls = []
        def f_6f60(uc, address, size, user_data):
            calls.append("6f60")
            uc.reg_write(UC_ARM_REG_R0, ptr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_1f28(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("1f28", arg0))
            uc.reg_write(UC_ARM_REG_R0, c1f28_ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_1b78(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("1b78", arg0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_4360(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("4360", arg0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_6f60, None, 0x00296F60, 0x00296F60)
        uc.hook_add(UC_HOOK_CODE, f_1f28, None, 0x002C1F28, 0x002C1F28)
        uc.hook_add(UC_HOOK_CODE, f_1b78, None, 0x00221B78, 0x00221B78)
        uc.hook_add(UC_HOOK_CODE, f_4360, None, 0x002C4360, 0x002C4360)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return uc.reg_read(UC_ARM_REG_R0), calls

    for hp, ha, cr in [(False, False, 0), (True, False, 0), (True, True, 0), (True, True, 1)]:
        o_ret, o_calls = run_one(orig_code, hp, ha, cr)
        d_ret, d_calls = run_one(decomp_code, hp, ha, cr)
        assert o_ret == d_ret and o_calls == d_calls, f"mismatch: {o_ret} != {d_ret}"
    print("engine_func_00324010: PASS")

def test_nn_sdk_func_00351b7c():
    addr = 0x00351B7C
    print(f"--- Testing nn_sdk_func_00351b7c ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 76)
    tmp = ROOT / "build" / "test_31b_part17"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("nn_sdk_func_00351b7c", tmp)

    sym_map = {
        "engine_func_00360608": 0x00360608,
        "nn_sdk_func_003607dc": 0x003607DC,
        "engine_func_00360780": 0x00360780,
        "engine_func_002c5468": 0x002C5468,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, svc_ret):
        uc = create_emulator()
        uc.mem_write(addr, code)

        h_storage = 0x0044E9E8
        page = h_storage & ~0xFFF
        try:
            uc.mem_map(page, 0x2000)
        except Exception:
            pass
        uc.mem_write(h_storage, struct.pack("<I", 0x1234))

        calls = []
        def f_608(uc, address, size, user_data):
            calls.append("608")
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_7dc(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("7dc", arg0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_780(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("780", arg0))
            uc.mem_write(arg0, struct.pack("<I", 0x5678))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_5468(uc, address, size, user_data):
            calls.append("5468")
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def svc_hook(uc, intno, user_data):
            if intno == 2:  # SVC in Unicorn
                r0 = uc.reg_read(UC_ARM_REG_R0)
                calls.append(("svc", r0))
                uc.reg_write(UC_ARM_REG_R0, svc_ret)

        uc.hook_add(UC_HOOK_CODE, f_608, None, 0x00360608, 0x00360608)
        uc.hook_add(UC_HOOK_CODE, f_7dc, None, 0x003607DC, 0x003607DC)
        uc.hook_add(UC_HOOK_CODE, f_780, None, 0x00360780, 0x00360780)
        uc.hook_add(UC_HOOK_CODE, f_5468, None, 0x002C5468, 0x002C5468)
        uc.hook_add(UC_HOOK_INTR, svc_hook)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return calls

    for s_ret in [0, 0x80000001]:
        o_calls = run_one(orig_code, s_ret)
        d_calls = run_one(decomp_code, s_ret)
        assert o_calls == d_calls, f"mismatch: {o_calls} != {d_calls}"
    print("nn_sdk_func_00351b7c: PASS")

def main():
    test_func_003f752c()
    test_ui_func_00355f78()
    test_func_0037c424()
    test_engine_func_00324010()
    test_nn_sdk_func_00351b7c()
    print("ALL BATCH 31 B PART 17 TESTS PASSED!")

if __name__ == "__main__":
    main()
