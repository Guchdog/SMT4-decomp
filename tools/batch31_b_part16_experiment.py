#!/usr/bin/env python3
"""Differential test for batch 31 B part 16:
- func_00377924 (0x00377924, 68 B)
- func_0038e480 (0x0038E480, 68 B compound: func_0038e480 + func_0038e4b4)
- engine_func_003bbd74 (0x003BBD74, 68 B)
- func_003e46a4 (0x003E46A4, 68 B)
- nn_sdk_func_003f6318 (0x003F6318, 68 B)
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
    UC_ARM_REG_D0,
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

def test_func_00377924():
    addr = 0x00377924
    print(f"--- Testing func_00377924 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 68)
    tmp = ROOT / "build" / "test_31b_part16"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_00377924", tmp)

    def run_one(code, val, start, span, scale, max_v):
        uc = create_emulator()
        uc.mem_write(addr, code)

        params = 0x10082000
        out_ptr = 0x10083000

        uc.mem_write(params, b"\x00" * 0x70)
        uc.mem_write(params + 0x4C, struct.pack("<f", start))
        uc.mem_write(params + 0x50, struct.pack("<f", span))
        uc.mem_write(params + 0x58, struct.pack("<f", scale))
        uc.mem_write(params + 0x5C, struct.pack("<f", max_v))
        uc.mem_write(out_ptr, struct.pack("<f", -999.0))

        raw_val = struct.unpack("<I", struct.pack("<f", val))[0]
        uc.reg_write(UC_ARM_REG_D0, raw_val)
        uc.reg_write(UC_ARM_REG_R1, params)
        uc.reg_write(UC_ARM_REG_R3, out_ptr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return struct.unpack("<f", uc.mem_read(out_ptr, 4))[0]

    test_cases = [
        (5.0, 10.0, 2.0, 3.0, 20.0),    # val <= start -> 0.0
        (15.0, 10.0, 2.0, 3.0, 20.0),   # (15 - 10)/2 * 3 = 7.5 <= 20.0
        (30.0, 10.0, 2.0, 3.0, 10.0),   # (30 - 10)/2 * 3 = 30.0 > 10.0 -> clamped to 10.0
    ]

    for v, st, sp, sc, mv in test_cases:
        ov = run_one(orig_code, v, st, sp, sc, mv)
        dv = run_one(comp, v, st, sp, sc, mv)
        assert abs(ov - dv) < 1e-4, f"mismatch: {ov} != {dv}"
    print("func_00377924: PASS")

def test_func_0038e480():
    addr = 0x0038E480
    print(f"--- Testing func_0038e480 ({hex(addr)}) ---")
    tmp = ROOT / "build" / "test_31b_part16"
    tmp.mkdir(parents=True, exist_ok=True)
    comp_a, relocs_a = compile_function("func_0038e480", tmp)
    comp_b, _ = compile_function("func_0038e4b4", tmp)

    orig_bytes_a = load_original_bytes(0x0038E480, 52)
    orig_bytes_b = load_original_bytes(0x0038E4B4, 16)

    sym_map = {
        "engine_func_002bac34": 0x002BAC34,
        "engine_func_002b2520": 0x002B2520,
    }
    decomp_a = stage_body(comp_a, relocs_a, 0x0038E480, sym_map)

    def run_a(code):
        uc = create_emulator()
        uc.mem_write(0x0038E480, code)

        glob_storage = 0x00432FC8
        page = glob_storage & ~0xFFF
        try:
            uc.mem_map(page, 0x2000)
        except Exception:
            pass

        obj = 0x10082000
        glob_obj = 0x10083000
        uc.mem_write(glob_storage, struct.pack("<I", glob_obj))
        uc.mem_write(obj, b"\x00" * 0x20)

        calls = []
        def f_ac34(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("ac34", arg0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_2520(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("2520", arg0))
            uc.reg_write(UC_ARM_REG_R0, 0x12345678)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_ac34, None, 0x002BAC34, 0x002BAC34)
        uc.hook_add(UC_HOOK_CODE, f_2520, None, 0x002B2520, 0x002B2520)

        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(0x0038E480, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        vt = struct.unpack("<I", uc.mem_read(obj, 4))[0]
        return ret, vt, calls

    o_ret, o_vt, o_calls = run_a(orig_bytes_a)
    d_ret, d_vt, d_calls = run_a(decomp_a)
    assert o_ret == 0x12345678 and d_ret == 0x12345678
    assert o_vt == 0x00421EE0 and d_vt == 0x00421EE0
    assert o_calls == [("ac34", 0x10083000 + 0x88), ("2520", 0x10082000)]
    assert d_calls == o_calls

    # Sub B
    def run_b(code, va, vb):
        uc = create_emulator()
        uc.mem_write(0x0038E4B4, code)

        pa = 0x10082000
        pb = 0x10082004
        uc.mem_write(pa, struct.pack("<H", va))
        uc.mem_write(pb, struct.pack("<H", vb))

        uc.reg_write(UC_ARM_REG_R0, pa)
        uc.reg_write(UC_ARM_REG_R1, pb)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(0x0038E4B4, 0x003E0000, timeout=1000000)

        return uc.reg_read(UC_ARM_REG_R0)

    for va, vb in [(10, 5), (5, 10), (0xFFFF, 0), (100, 100)]:
        ob = run_b(orig_bytes_b, va, vb)
        db = run_b(comp_b, va, vb)
        assert ob == db, f"sub B mismatch: {ob} != {db}"
    print("func_0038e480: PASS")

def test_engine_func_003bbd74():
    addr = 0x003BBD74
    print(f"--- Testing engine_func_003bbd74 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 68)
    tmp = ROOT / "build" / "test_31b_part16"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_003bbd74", tmp)

    sym_map = {
        "engine_func_0021f43c": 0x0021F43C,
        "engine_func_002f5020": 0x002F5020,
        "AsdCec_func_002eb924": 0x002EB924,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, f43c_ret, eb924_first_ret):
        uc = create_emulator()
        uc.mem_write(addr, code)

        obj = 0x10082000
        inner_obj = 0x10083000

        calls = []
        def f_43c(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("43c", arg0))
            uc.reg_write(UC_ARM_REG_R0, f43c_ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_5020(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("5020", arg0))
            uc.reg_write(UC_ARM_REG_R0, inner_obj)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        call_idx = [0]
        def f_b924(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("b924", arg0, arg1))
            call_idx[0] += 1
            if call_idx[0] == 1:
                uc.reg_write(UC_ARM_REG_R0, eb924_first_ret)
            else:
                uc.reg_write(UC_ARM_REG_R0, 0xCAFE)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_43c, None, 0x0021F43C, 0x0021F43C)
        uc.hook_add(UC_HOOK_CODE, f_5020, None, 0x002F5020, 0x002F5020)
        uc.hook_add(UC_HOOK_CODE, f_b924, None, 0x002EB924, 0x002EB924)

        uc.reg_write(UC_ARM_REG_R0, obj)
        uc.reg_write(UC_ARM_REG_R1, 0x42)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, calls

    for f_ret, b_ret in [(0, 0), (1, 0x55), (1, 0)]:
        o_ret, o_calls = run_one(orig_code, f_ret, b_ret)
        d_ret, d_calls = run_one(decomp_code, f_ret, b_ret)
        assert o_ret == d_ret and o_calls == d_calls, f"mismatch: {hex(o_ret)} != {hex(d_ret)}"
    print("engine_func_003bbd74: PASS")

def test_func_003e46a4():
    addr = 0x003E46A4
    print(f"--- Testing func_003e46a4 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 68)
    tmp = ROOT / "build" / "test_31b_part16"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_003e46a4", tmp)

    sym_map = {
        "func_002ac0c4": 0x002AC0C4,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code):
        uc = create_emulator()
        uc.mem_write(addr, code)

        obj = 0x10082000
        uc.mem_write(obj, b"\x00" * 0x50)
        uc.mem_write(obj + 0x30, struct.pack("<fff", 1.0, 2.0, 3.0))
        uc.mem_write(obj + 0x3C, struct.pack("<I", 0x100))

        calls = []
        def f_c0c4(uc, address, size, user_data):
            raw_s0 = uc.reg_read(UC_ARM_REG_D0) & 0xFFFFFFFF
            val = struct.unpack("<f", struct.pack("<I", raw_s0))[0]
            calls.append(val)
            # return val * 2.0
            ret_val = val * 2.0
            ret_raw = struct.unpack("<I", struct.pack("<f", ret_val))[0]
            uc.reg_write(UC_ARM_REG_D0, ret_raw)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_c0c4, None, 0x002AC0C4, 0x002AC0C4)

        uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_R1, obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        v0, v1, v2 = struct.unpack("<fff", uc.mem_read(obj + 0x30, 12))
        flags = struct.unpack("<I", uc.mem_read(obj + 0x3C, 4))[0]
        return ret, v0, v1, v2, flags, calls

    o_ret, o_v0, o_v1, o_v2, o_fl, o_calls = run_one(orig_code)
    d_ret, d_v0, d_v1, d_v2, d_fl, d_calls = run_one(decomp_code)

    assert o_ret == 1 and d_ret == 1
    assert o_calls == [1.0, 2.0, 3.0] and d_calls == [1.0, 2.0, 3.0]
    assert o_v0 == 2.0 and o_v1 == 4.0 and o_v2 == 6.0
    assert d_v0 == 2.0 and d_v1 == 4.0 and d_v2 == 6.0
    assert o_fl == 0x900 and d_fl == 0x900
    print("func_003e46a4: PASS")

def test_nn_sdk_func_003f6318():
    addr = 0x003F6318
    print(f"--- Testing nn_sdk_func_003f6318 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 68)
    tmp = ROOT / "build" / "test_31b_part16"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("nn_sdk_func_003f6318", tmp)

    sym_map = {
        "nn_sdk_func_0017f8f4": 0x0017F8F4,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, low, high):
        uc = create_emulator()
        uc.mem_write(addr, code)

        target = 0x0044E960
        page = target & ~0xFFF
        try:
            uc.mem_map(page, 0x2000)
        except Exception:
            pass
        uc.mem_write(target, b"\x00" * 8)

        calls = []
        def f_8f4(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            calls.append(("8f4", r0, r1, r2))
            uc.mem_write(r0, struct.pack("<I", 1))
            uc.mem_write(r1, struct.pack("<I", 1))
            uc.mem_write(r2, struct.pack("<I", 0))
            uc.reg_write(UC_ARM_REG_R0, 0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_8f4, None, 0x0017F8F4, 0x0017F8F4)

        uc.reg_write(UC_ARM_REG_R0, low)
        uc.reg_write(UC_ARM_REG_R1, high)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        w_low, w_high = struct.unpack("<II", uc.mem_read(target, 8))
        return ret, w_low, w_high, len(calls)

    o_ret, o_l, o_h, o_nc = run_one(orig_code, 0x11223344, 0x55667788)
    d_ret, d_l, d_h, d_nc = run_one(decomp_code, 0x11223344, 0x55667788)

    assert o_ret == 0x0044E960 and d_ret == 0x0044E960
    assert o_l == 0x11223344 and d_l == 0x11223344
    assert o_h == 0x55667788 and d_h == 0x55667788
    assert o_nc == 1 and d_nc == 1
    print("nn_sdk_func_003f6318: PASS")

def main():
    test_func_00377924()
    test_func_0038e480()
    test_engine_func_003bbd74()
    test_func_003e46a4()
    test_nn_sdk_func_003f6318()
    print("ALL BATCH 31 B PART 16 TESTS PASSED!")

if __name__ == "__main__":
    main()
