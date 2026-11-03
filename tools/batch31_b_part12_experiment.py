#!/usr/bin/env python3
"""Differential test for batch 31 B part 12:
- func_00368820 (0x00368820, 64 B)
- func_0036a25c (0x0036A25C, 64 B)
- func_0036ac80 (0x0036AC80, 64 B)
- func_0036aed4 (0x0036AED4, 64 B)
- func_0036b570 (0x0036B570, 64 B)
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
    UC_ARM_REG_D1,
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

def test_func_00368820():
    print("--- Testing func_00368820 (0x00368820) ---")
    addr = 0x00368820
    orig_code = load_original_bytes(addr, 64)
    tmp = ROOT / "build" / "test_31b_part12"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_00368820", tmp)

    def run_one(code, dt, old_val, a, b):
        uc = create_emulator()
        uc.mem_write(addr, code)
        obj = 0x10082000
        callback_addr = 0x10084000
        ctx_addr = 0x10085000

        calls = []
        def cb_hook(uc, address, size, user_data):
            # Check float args in s0, s1, s2
            d0_raw = uc.reg_read(UC_ARM_REG_D0)
            d1_raw = uc.reg_read(UC_ARM_REG_D1)
            s0_val = struct.unpack("<f", struct.pack("<I", d0_raw & 0xFFFFFFFF))[0]
            s1_val = struct.unpack("<f", struct.pack("<I", (d0_raw >> 32) & 0xFFFFFFFF))[0]
            s2_val = struct.unpack("<f", struct.pack("<I", d1_raw & 0xFFFFFFFF))[0]
            calls.append((s0_val, s1_val, s2_val))
            # Return s2 * 2.0f in s0
            ret_f = s2_val * 2.0
            ret_raw = struct.unpack("<I", struct.pack("<f", ret_f))[0]
            uc.reg_write(UC_ARM_REG_D0, (d0_raw & ~0xFFFFFFFF) | ret_raw)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, cb_hook, None, callback_addr, callback_addr)

        uc.mem_write(obj + 0x38, struct.pack("<f", old_val))
        uc.mem_write(obj + 0x3C, struct.pack("<f", -999.0))
        uc.mem_write(obj + 0x44, struct.pack("<ff", a, b))
        uc.mem_write(obj + 0x4C, struct.pack("<II", callback_addr, ctx_addr))
        uc.mem_write(obj + 0x58, b"\x00")

        uc.reg_write(UC_ARM_REG_R0, obj)
        raw_dt = struct.unpack("<I", struct.pack("<f", dt))[0]
        uc.reg_write(UC_ARM_REG_D0, raw_dt)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        f38 = struct.unpack("<f", uc.mem_read(obj + 0x38, 4))[0]
        f3c = struct.unpack("<f", uc.mem_read(obj + 0x3C, 4))[0]
        b58 = struct.unpack("<B", uc.mem_read(obj + 0x58, 1))[0]
        return f38, f3c, b58, calls

    for dt, old, a, b in [(0.5, 1.0, 2.0, 3.0), (0.016, 10.0, 0.1, 0.2)]:
        o_38, o_3c, o_58, o_calls = run_one(orig_code, dt, old, a, b)
        d_38, d_3c, d_58, d_calls = run_one(comp, dt, old, a, b)
        assert abs(o_38 - (old + dt) * 2.0) < 1e-4 and abs(o_3c - old) < 1e-4 and o_58 == 1
        assert abs(d_38 - (old + dt) * 2.0) < 1e-4 and abs(d_3c - old) < 1e-4 and d_58 == 1
        assert o_calls == d_calls
    print("func_00368820: PASS")

def test_vtable_setter(name: str, addr: int, exp_vtable: int, flag_offset: int, inner_offset: int):
    print(f"--- Testing {name} ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 64)
    tmp = ROOT / "build" / "test_31b_part12"
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

        # obj setup
        uc.mem_write(obj, b"\x00" * 0x30)
        uc.mem_write(obj + flag_offset, bytes([flag_val]))
        uc.mem_write(obj + 4, struct.pack("<I", sub_obj))
        uc.mem_write(obj + inner_offset, struct.pack("<I", 0x10086000 if has_inner else 0))

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

def main():
    test_func_00368820()
    test_vtable_setter("func_0036a25c", 0x0036A25C, 0x00421104, 8, 0x0C)
    test_vtable_setter("func_0036ac80", 0x0036AC80, 0x0042114C, 8, 0x0C)
    test_vtable_setter("func_0036aed4", 0x0036AED4, 0x00421194, 9, 0x1C)
    test_vtable_setter("func_0036b570", 0x0036B570, 0x004211F4, 8, 0x0C)
    print("ALL BATCH 31 B PART 12 TESTS PASSED!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
