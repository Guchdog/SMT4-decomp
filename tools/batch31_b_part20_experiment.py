#!/usr/bin/env python3
"""Differential test for batch 31 B part 20:
- func_0038b334 (0x0038B334, 80 B compound: 0x38b334, 0x38b368)
- engine_func_003ac930 (0x003AC930, 80 B compound: 0x3ac930, 0x3ac958)
- ui_func_003beaf0 (0x003BEAF0, 80 B)
- ui_func_003bed80 (0x003BED80, 80 B)
- func_003e51c4 (0x003E51C4, 80 B)
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
    UC_ARM_REG_S0,
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

def test_func_0038b334():
    print("--- Testing func_0038b334 compound (0x0038B334, 80 B) ---")
    tmp = ROOT / "build" / "test_31b_part20"
    tmp.mkdir(parents=True, exist_ok=True)
    comp_a, relocs_a = compile_function("func_0038b334", tmp)
    comp_b, relocs_b = compile_function("func_0038b368", tmp)

    orig_a = load_original_bytes(0x0038B334, 52)
    orig_b = load_original_bytes(0x0038B368, 28)

    FN_2BAC34 = 0x002BAC34
    FN_2B2520 = 0x002B2520
    sym_map_a = {
        "func_002bac34": FN_2BAC34,
        "func_002b2520": FN_2B2520,
    }
    decomp_a = stage_body(comp_a, relocs_a, 0x0038B334, sym_map_a)
    decomp_b = comp_b

    # Sub A test
    def run_a(code):
        uc = create_emulator()
        uc.mem_write(0x0038B334, code)

        obj = 0x10082000
        singleton_holder = 0x00432FC8
        singleton_inst = 0x10083000

        uc.mem_write(obj, struct.pack("<I", 0x11111111))
        uc.mem_write(singleton_holder, struct.pack("<I", singleton_inst))

        calls = []
        def f_ac34(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("ac34", arg0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_2520(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("2520", arg0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_ac34, None, FN_2BAC34, FN_2BAC34)
        uc.hook_add(UC_HOOK_CODE, f_2520, None, FN_2B2520, FN_2B2520)

        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(0x0038B334, 0x003E0000, timeout=1000000)

        vt = struct.unpack("<I", uc.mem_read(obj, 4))[0]
        return vt, calls

    oa_vt, oa_calls = run_a(orig_a)
    da_vt, da_calls = run_a(decomp_a)
    assert oa_vt == da_vt == 0x00421E0C, f"vtable mismatch: orig {hex(oa_vt)} vs decomp {hex(da_vt)}"
    assert oa_calls == da_calls, f"calls mismatch: orig {oa_calls} vs decomp {da_calls}"

    # Sub B test
    def run_b(code):
        uc = create_emulator()
        uc.mem_write(0x0038B368, code)

        obj = 0x10082000
        uc.mem_write(obj, b"\xFF" * 0x20)

        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(0x0038B368, 0x003E0000, timeout=1000000)

        return uc.mem_read(obj, 0x10)

    ob_mem = run_b(orig_b)
    db_mem = run_b(decomp_b)
    assert ob_mem == db_mem
    expected = b"\x00" * 14 + b"\xFF\xFF"
    assert ob_mem == expected, f"cleared bytes mismatch: {ob_mem.hex()}"

    print("func_0038b334: PASS")

def test_engine_func_003ac930():
    print("--- Testing engine_func_003ac930 compound (0x003AC930, 80 B) ---")
    tmp = ROOT / "build" / "test_31b_part20"
    tmp.mkdir(parents=True, exist_ok=True)
    comp_a, relocs_a = compile_function("engine_func_003ac930", tmp)
    comp_b, relocs_b = compile_function("engine_func_003ac958", tmp)

    orig_a = load_original_bytes(0x003AC930, 40)
    orig_b = load_original_bytes(0x003AC958, 40)

    FN_2C4360 = 0x002C4360
    sym_map_a = {"engine_func_002c4360": FN_2C4360}
    decomp_a = stage_body(comp_a, relocs_a, 0x003AC930, sym_map_a)
    decomp_b = comp_b

    # Sub A
    def run_a(code, has_obj: bool):
        uc = create_emulator()
        uc.mem_write(0x003AC930, code)

        holder = 0x0043D990
        obj = 0x10082000 if has_obj else 0
        uc.mem_write(holder, struct.pack("<I", obj))

        calls = []
        def f_4360(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(arg0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_4360, None, FN_2C4360, FN_2C4360)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(0x003AC930, 0x003E0000, timeout=1000000)

        out_ptr = struct.unpack("<I", uc.mem_read(holder, 4))[0]
        return out_ptr, calls

    for has_obj in [True, False]:
        oa_ptr, oa_calls = run_a(orig_a, has_obj)
        da_ptr, da_calls = run_a(decomp_a, has_obj)
        assert oa_ptr == da_ptr == 0, f"holder not cleared: orig {oa_ptr} vs decomp {da_ptr}"
        assert oa_calls == da_calls, f"calls mismatch: orig {oa_calls} vs decomp {da_calls}"

    # Sub B
    def run_b(code):
        uc = create_emulator()
        uc.mem_write(0x003AC958, code)

        holder = 0x0043D9C8
        p_obj = 0x10082000
        obj = 0x10083000
        vtable = 0x10084000
        vmethod = 0x10085000

        uc.mem_write(holder, struct.pack("<I", p_obj))
        uc.mem_write(p_obj, struct.pack("<I", obj))
        uc.mem_write(obj, struct.pack("<I", vtable))
        # method 5 is at vtable + 0x14
        uc.mem_write(vtable + 0x14, struct.pack("<I", vmethod))

        calls = []
        def f_vmethod(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(arg0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_vmethod, None, vmethod, vmethod)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(0x003AC958, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, calls

    ob_ret, ob_calls = run_b(orig_b)
    db_ret, db_calls = run_b(decomp_b)
    assert ob_ret == db_ret == 0
    assert ob_calls == db_calls == [0x10083000]

    print("engine_func_003ac930: PASS")

def test_ui_func_003beaf0():
    addr = 0x003BEAF0
    print(f"--- Testing ui_func_003beaf0 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 80)
    tmp = ROOT / "build" / "test_31b_part20"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_003beaf0", tmp)

    FN_293C98 = 0x00293C98
    FN_282B94 = 0x00282B94
    FN_2475E4 = 0x002475E4
    sym_map = {
        "ui_func_00293c98": FN_293C98,
        "ui_func_00282b94": FN_282B94,
        "camp_func_002475e4": FN_2475E4,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, mock_byte_1d):
        uc = create_emulator()
        uc.mem_write(addr, code)

        ctx1 = 0x10082000
        ctx2 = 0x10083000

        call_seq = []
        call_count_93c98 = 0
        def f_93c98(uc, address, size, user_data):
            nonlocal call_count_93c98
            call_count_93c98 += 1
            ret = ctx1 if call_count_93c98 == 1 else ctx2
            call_seq.append(f"ctx_{call_count_93c98}")
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_2b94(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            call_seq.append(("2b94", arg0, arg1))
            uc.reg_write(UC_ARM_REG_R0, 0x42)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_75e4(uc, address, size, user_data):
            buf_ptr = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            arg2 = uc.reg_read(UC_ARM_REG_R2)
            call_seq.append(("75e4", arg1, arg2))
            uc.mem_write(buf_ptr + 0x1D, bytes([mock_byte_1d]))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_93c98, None, FN_293C98, FN_293C98)
        uc.hook_add(UC_HOOK_CODE, f_2b94, None, FN_282B94, FN_282B94)
        uc.hook_add(UC_HOOK_CODE, f_75e4, None, FN_2475E4, FN_2475E4)

        uc.reg_write(UC_ARM_REG_R0, 0x1234)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        s0 = uc.reg_read(UC_ARM_REG_S0)
        val = struct.unpack("<f", struct.pack("<I", s0))[0]
        return val, call_seq

    for b in [0, 50, 100, 255]:
        ov, o_seq = run_one(orig_code, b)
        dv, d_seq = run_one(decomp_code, b)
        assert abs(ov - dv) < 1e-6, f"float mismatch for {b}: orig {ov} vs decomp {dv}"
        assert o_seq == d_seq, f"seq mismatch: orig {o_seq} vs decomp {d_seq}"

    print("ui_func_003beaf0: PASS")

def test_ui_func_003bed80():
    addr = 0x003BED80
    print(f"--- Testing ui_func_003bed80 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 80)
    tmp = ROOT / "build" / "test_31b_part20"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_003bed80", tmp)

    FN_293C98 = 0x00293C98
    FN_282B94 = 0x00282B94
    FN_2475E4 = 0x002475E4
    sym_map = {
        "ui_func_00293c98": FN_293C98,
        "ui_func_00282b94": FN_282B94,
        "camp_func_002475e4": FN_2475E4,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, mock_byte_1e):
        uc = create_emulator()
        uc.mem_write(addr, code)

        ctx1 = 0x10082000
        ctx2 = 0x10083000

        call_seq = []
        call_count_93c98 = 0
        def f_93c98(uc, address, size, user_data):
            nonlocal call_count_93c98
            call_count_93c98 += 1
            ret = ctx1 if call_count_93c98 == 1 else ctx2
            call_seq.append(f"ctx_{call_count_93c98}")
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_2b94(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            call_seq.append(("2b94", arg0, arg1))
            uc.reg_write(UC_ARM_REG_R0, 0x42)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_75e4(uc, address, size, user_data):
            buf_ptr = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            arg2 = uc.reg_read(UC_ARM_REG_R2)
            call_seq.append(("75e4", arg1, arg2))
            uc.mem_write(buf_ptr + 0x1E, bytes([mock_byte_1e]))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_93c98, None, FN_293C98, FN_293C98)
        uc.hook_add(UC_HOOK_CODE, f_2b94, None, FN_282B94, FN_282B94)
        uc.hook_add(UC_HOOK_CODE, f_75e4, None, FN_2475E4, FN_2475E4)

        uc.reg_write(UC_ARM_REG_R0, 0x1234)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        s0 = uc.reg_read(UC_ARM_REG_S0)
        val = struct.unpack("<f", struct.pack("<I", s0))[0]
        return val, call_seq

    for b in [0, 50, 100, 255]:
        ov, o_seq = run_one(orig_code, b)
        dv, d_seq = run_one(decomp_code, b)
        assert abs(ov - dv) < 1e-6, f"float mismatch for {b}: orig {ov} vs decomp {dv}"
        assert o_seq == d_seq, f"seq mismatch: orig {o_seq} vs decomp {d_seq}"

    print("ui_func_003bed80: PASS")

def test_func_003e51c4():
    addr = 0x003E51C4
    print(f"--- Testing func_003e51c4 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 80)
    tmp = ROOT / "build" / "test_31b_part20"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003e51c4", tmp)

    FN_3E4450 = 0x003E4450
    FN_3E4508 = 0x003E4508
    FN_225FA0 = 0x00225FA0
    sym_map = {
        "func_003e4450": FN_3E4450,
        "ui_func_003e4508": FN_3E4508,
        "func_00225fa0": FN_225FA0,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, vx, vy, vz):
        uc = create_emulator()
        uc.mem_write(addr, code)

        vec_ptr = 0x10082000
        uc.mem_write(vec_ptr, struct.pack("<fff", vx, vy, vz))

        calls = []
        def make_hook(name):
            def h(uc, address, size, user_data):
                a0 = uc.reg_read(UC_ARM_REG_R0)
                a1 = uc.reg_read(UC_ARM_REG_R1)
                a2 = uc.reg_read(UC_ARM_REG_R2)
                s0 = uc.reg_read(UC_ARM_REG_S0)
                fval = struct.unpack("<f", struct.pack("<I", s0))[0]
                calls.append((name, a0, a1, a2, fval))
                lr = uc.reg_read(UC_ARM_REG_LR)
                uc.reg_write(UC_ARM_REG_PC, lr)
            return h

        uc.hook_add(UC_HOOK_CODE, make_hook("4450"), None, FN_3E4450, FN_3E4450)
        uc.hook_add(UC_HOOK_CODE, make_hook("4508"), None, FN_3E4508, FN_3E4508)
        uc.hook_add(UC_HOOK_CODE, make_hook("5fa0"), None, FN_225FA0, FN_225FA0)

        sp = STACK_BASE + 0x8000
        # push 5th arg (vec_ptr) on stack
        uc.mem_write(sp, struct.pack("<I", vec_ptr))

        uc.reg_write(UC_ARM_REG_R0, 0x11)
        uc.reg_write(UC_ARM_REG_R1, 0x22)
        uc.reg_write(UC_ARM_REG_R2, 0x33)
        uc.reg_write(UC_ARM_REG_R3, 0x44)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, calls

    for vx, vy, vz in [(1.0, 2.0, 3.0), (-0.5, 0.0, 99.5)]:
        o_ret, o_calls = run_one(orig_code, vx, vy, vz)
        d_ret, d_calls = run_one(decomp_code, vx, vy, vz)
        assert o_ret == d_ret == 1, f"ret mismatch: orig {o_ret} vs decomp {d_ret}"
        for (oname, oa0, oa1, oa2, of), (dname, da0, da1, da2, df) in zip(o_calls, d_calls):
            assert oname == dname and (oa0, oa1, oa2) == (da0, da1, da2)
            assert abs(of - df) < 1e-6, f"float arg mismatch: {of} vs {df}"

    print("func_003e51c4: PASS")

if __name__ == "__main__":
    test_func_0038b334()
    test_engine_func_003ac930()
    test_ui_func_003beaf0()
    test_ui_func_003bed80()
    test_func_003e51c4()
    print("\nALL 5 FUNCTIONS IN PART 20 PASSED DIFFERENTIAL VERIFICATION!")
