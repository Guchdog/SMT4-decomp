#!/usr/bin/env python3
"""Differential test for batch 30 part 13:
- engine_func_0026ea7c (0x0026EA7C, 152 B)
- script_vm_func_002701c4 (0x002701C4, 152 B)
- script_vm_func_00275984 (0x00275984, 152 B)
- ui_func_002b8070 (0x002B8070, 148 B)
- func_002d54c4 (0x002D54C4, 152 B)
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
    UC_CPU_ARM_11MPCORE,
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_R4,
    UC_ARM_REG_R5,
    UC_ARM_REG_R6,
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
    UC_ARM_REG_S0,
    UC_ARM_REG_S1,
    UC_ARM_REG_S2,
    UC_ARM_REG_S3,
    UC_ARM_REG_S4,
    UC_ARM_REG_S5,
    UC_ARM_REG_S6,
    UC_ARM_REG_S7,
    UC_ARM_REG_S8,
    UC_ARM_REG_S9,
    UC_ARM_REG_S10,
    UC_ARM_REG_S11,
    UC_ARM_REG_D8,
    UC_ARM_REG_D9,
    UC_ARM_REG_D10,
    UC_ARM_REG_D11,
    UC_ARM_REG_D12,
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
SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

def load_original_bytes(addr: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(addr - CODE_BASE)
        return f.read(size)

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch30_c.o"
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

def setup_uc() -> Uc:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.ctl_set_cpu_model(UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(CODE_BASE, CODE_SIZE)
    with open(ORIG_BIN, "rb") as f:
        code_data = f.read(CODE_SIZE)
    uc.mem_write(CODE_BASE, code_data)

    uc.mem_map(0x00480000, 0x00100000)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(0x20000000, 0x00100000)

    def hook_unmapped(uc, access, address, size, value, user_data):
        page = address & ~0xFFF
        try:
            uc.mem_map(page, 0x1000)
        except Exception:
            pass
        return True

    uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_unmapped)
    return uc

def test_0026ea7c():
    print("--- Testing engine_func_0026ea7c ---")
    addr = 0x0026EA7C
    size = 152
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_0026ea7c", ROOT / "build")
    symbol_map = {}
    staged = stage_body(comp, relocs, addr, symbol_map)

    OUT_ADDR = 0x20001000

    def run_one(c_bytes, mode, v_floats):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        uc.mem_write(OUT_ADDR, b"\x00" * 16)

        s_regs = [
            UC_ARM_REG_S0, UC_ARM_REG_S1, UC_ARM_REG_S2,
            UC_ARM_REG_S3, UC_ARM_REG_S4, UC_ARM_REG_S5,
            UC_ARM_REG_S6, UC_ARM_REG_S7, UC_ARM_REG_S8,
            UC_ARM_REG_S9, UC_ARM_REG_S10, UC_ARM_REG_S11,
        ]
        for reg, flt in zip(s_regs, v_floats):
            # Write float bit pattern into S register
            flt_bits = struct.unpack("<I", struct.pack("<f", flt))[0]
            uc.reg_write(reg, flt_bits)

        sp = STACK_BASE + STACK_SIZE - 0x100
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00100000)
        uc.reg_write(UC_ARM_REG_R0, mode)
        uc.reg_write(UC_ARM_REG_R1, OUT_ADDR)

        uc.emu_start(addr, 0x00100000, timeout=200000)

        out_floats = struct.unpack("<3f", uc.mem_read(OUT_ADDR, 12))
        return [round(f, 5) for f in out_floats]

    test_vectors = [
        # (x0, y0, z0,  x1, y1, z1,  x2, y2, z2,  x3, y3, z3)
        (1.0, 2.0, 3.0,  5.0, 6.0, 7.0,  9.0, 10.0, 11.0,  13.0, 14.0, 15.0),
        (-4.0, 1.5, 0.0,  2.0, -3.5, 8.0,  6.0, 7.5, -2.0,  -8.0, -1.5, 4.0),
    ]

    for mode in (0, 1, 2):
        for vec in test_vectors:
            o = run_one(orig, mode, vec)
            c = run_one(staged, mode, vec)
            assert o == c, f"0026ea7c mismatch for mode={mode}: {o} vs {c}"
    print("engine_func_0026ea7c: PASS")

def test_002701c4():
    print("--- Testing script_vm_func_002701c4 ---")
    addr = 0x002701C4
    size = 140
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_002701c4", ROOT / "build")
    symbol_map = {
        "ui_func_0026b844": 0x0026B844,
        "func_002bcf58": 0x002BCF58,
        "ui_func_0026b830": 0x0026B830,
        "func_002adb40": 0x002ADB40,
        "ui_func_002c0b94": 0x002C0B94,
        "ui_func_002e0b50": 0x002E0B50,
        "func_002c5a6c": 0x002C5A6C,
        "ui_func_0026e594": 0x0026E594,
        "engine_func_002c4360": 0x002C4360,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    P10_ADDR = 0x20005000
    P14_ADDR = 0x20006000
    P18_ADDR = 0x20007000
    OBJ_PTR = 0x20008000
    OBJ_ADDR = 0x20009000

    def run_one(c_bytes, has_p10):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        calls = []
        def make_stub(target, name, arity, ret_val=0):
            uc.mem_write(target, b"\x1e\xff\x2f\xe1")
            def hook(u, a, s, ud):
                if arity == 0:
                    calls.append(name)
                elif arity == 1:
                    calls.append((name, u.reg_read(UC_ARM_REG_R0)))
                elif arity == 2:
                    calls.append((name, u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
                elif arity == 3:
                    calls.append((name, u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1), u.reg_read(UC_ARM_REG_R2)))
                u.reg_write(UC_ARM_REG_R0, ret_val)
            uc.hook_add(UC_HOOK_CODE, hook, None, target, target)

        make_stub(0x0026B844, "26b844", 0, 0x11111111)
        make_stub(0x002BCF58, "2bcf58", 3)
        make_stub(0x0026B830, "26b830", 0, 0x22222222)
        make_stub(0x002ADB40, "2adb40", 2)
        make_stub(0x002C0B94, "2c0b94", 0, 0x33333333)
        make_stub(0x002E0B50, "2e0b50", 0)
        make_stub(0x002C5A6C, "2c5a6c", 0)
        make_stub(0x0026E594, "26e594", 1)
        make_stub(0x002C4360, "free", 1)

        # 0x0044DE28 setup
        uc.mem_write(0x0044DE28, b"\x00" * 0x30)
        p10 = P10_ADDR if has_p10 else 0
        uc.mem_write(0x0044DE28 + 0x10, struct.pack("<3I", p10, P14_ADDR, P18_ADDR))

        # 0x00433158 -> OBJ_PTR -> OBJ_ADDR
        uc.mem_write(0x00433158, struct.pack("<I", OBJ_PTR))
        uc.mem_write(OBJ_PTR, struct.pack("<I", OBJ_ADDR))

        sp = STACK_BASE + STACK_SIZE - 0x100
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00100000)
        uc.reg_write(UC_ARM_REG_R4, 0xAAAAAAAA)

        uc.emu_start(addr, 0x00100000, timeout=200000)

        p10_res, p14_res, p18_res = struct.unpack("<3I", uc.mem_read(0x0044DE28 + 0x10, 12))
        return {
            "p10": p10_res,
            "p14": p14_res,
            "p18": p18_res,
            "calls": calls,
            "r4": uc.reg_read(UC_ARM_REG_R4),
        }

    for has_p in (True, False):
        o = run_one(orig, has_p)
        c = run_one(staged, has_p)
        assert o == c, f"002701c4 mismatch for has_p={has_p}: {o} vs {c}"
    print("script_vm_func_002701c4: PASS")

def test_00275984():
    print("--- Testing script_vm_func_00275984 ---")
    addr = 0x00275984
    size = 148
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_00275984", ROOT / "build")
    symbol_map = {
        "script_vm_func_002920e4": 0x002920E4,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    MGR_ADDR = 0x20001000

    def run_one(c_bytes, flag9, flag8, count):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # 0x00448C20 -> MGR_ADDR
        uc.mem_write(0x00448C20, struct.pack("<I", MGR_ADDR))

        # Setup manager
        mgr_buf = bytearray(0x100)
        mgr_buf[8] = flag8
        mgr_buf[9] = flag9
        struct.pack_into("<I", mgr_buf, 4, count)

        # Setup entries at stride 32:
        # entry 0: active (0xC=1, 0x1C=0, 0x14=0), id=100, pos=(1.0, 2.0, 3.0)
        # entry 1: inactive (0xC=0)
        # entry 2: active (0xC=1, 0x1C=0, 0x14=0), id=200, pos=(4.0, 5.0, 6.0)
        if count >= 1:
            mgr_buf[0 * 32 + 0x0C] = 1
            struct.pack_into("<I", mgr_buf, 0 * 32 + 0x10, 100)
            struct.pack_into("<3f", mgr_buf, 0 * 32 + 0x20, 1.0, 2.0, 3.0)
        if count >= 3:
            mgr_buf[2 * 32 + 0x0C] = 1
            struct.pack_into("<I", mgr_buf, 2 * 32 + 0x10, 200)
            struct.pack_into("<3f", mgr_buf, 2 * 32 + 0x20, 4.0, 5.0, 6.0)

        uc.mem_write(MGR_ADDR, bytes(mgr_buf))

        calls = []
        uc.mem_write(0x002920E4, b"\x1e\xff\x2f\xe1")
        def on_spawn(u, a, s, ud):
            id_val = u.reg_read(UC_ARM_REG_R0)
            # read s0, s1, s2
            s0_b = u.reg_read(UC_ARM_REG_S0)
            s1_b = u.reg_read(UC_ARM_REG_S1)
            s2_b = u.reg_read(UC_ARM_REG_S2)
            f0 = struct.unpack("<f", struct.pack("<I", s0_b))[0]
            f1 = struct.unpack("<f", struct.pack("<I", s1_b))[0]
            f2 = struct.unpack("<f", struct.pack("<I", s2_b))[0]
            calls.append((id_val, round(f0, 2), round(f1, 2), round(f2, 2)))
            u.reg_write(UC_ARM_REG_R0, id_val + 0x5000)
        uc.hook_add(UC_HOOK_CODE, on_spawn, None, 0x002920E4, 0x002920E4)

        sp = STACK_BASE + STACK_SIZE - 0x100
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00100000)
        uc.reg_write(UC_ARM_REG_R4, 0xAAAAAAAA)
        uc.reg_write(UC_ARM_REG_R5, 0xBBBBBBBB)
        uc.reg_write(UC_ARM_REG_R6, 0xCCCCCCCC)

        uc.emu_start(addr, 0x00100000, timeout=200000)

        out_mgr = bytes(uc.mem_read(MGR_ADDR, 0x100))
        return {
            "calls": calls,
            "mgr_8": out_mgr[8],
            "e0_14": struct.unpack_from("<I", out_mgr, 0 * 32 + 0x14)[0] if count >= 1 else 0,
            "e2_14": struct.unpack_from("<I", out_mgr, 2 * 32 + 0x14)[0] if count >= 3 else 0,
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
        }

    cases = [
        (0, 1, 3), # flag9 is 0 -> return
        (1, 0, 3), # flag8 is 0 -> return
        (1, 1, 0), # count 0 -> clears flag8, return
        (1, 1, 3), # count 3 -> spawns icons for e0 and e2
    ]

    for c_tuple in cases:
        o = run_one(orig, *c_tuple)
        c = run_one(staged, *c_tuple)
        assert o == c, f"00275984 mismatch for {c_tuple}: {o} vs {c}"
    print("script_vm_func_00275984: PASS")

def test_002b8070():
    print("--- Testing ui_func_002b8070 ---")
    addr = 0x002B8070
    size = 96
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_002b8070", ROOT / "build")
    symbol_map = {
        "ui_func_002b8524": 0x002B8524,
        "ui_func_002b8104": 0x002B8104,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    def run_one(c_bytes, v_floats):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        calls = []
        uc.mem_write(0x002B8524, b"\x1e\xff\x2f\xe1")
        def on_8524(u, a, s, ud):
            calls.append("8524")
        uc.hook_add(UC_HOOK_CODE, on_8524, None, 0x002B8524, 0x002B8524)

        uc.mem_write(0x002B8104, b"\x1e\xff\x2f\xe1")
        def on_8104(u, a, s, ud):
            r0 = u.reg_read(UC_ARM_REG_R0)
            r1 = u.reg_read(UC_ARM_REG_R1)
            r2 = u.reg_read(UC_ARM_REG_R2)
            r3 = u.reg_read(UC_ARM_REG_R3)
            s_regs = [
                UC_ARM_REG_S0, UC_ARM_REG_S1, UC_ARM_REG_S2,
                UC_ARM_REG_S3, UC_ARM_REG_S4, UC_ARM_REG_S5,
                UC_ARM_REG_S6, UC_ARM_REG_S7, UC_ARM_REG_S8,
            ]
            flts = []
            for sr in s_regs:
                b = u.reg_read(sr)
                f = struct.unpack("<f", struct.pack("<I", b))[0]
                flts.append(round(f, 3))
            calls.append(("8104", r0, r1, r2, r3, flts))
        uc.hook_add(UC_HOOK_CODE, on_8104, None, 0x002B8104, 0x002B8104)

        s_regs = [
            UC_ARM_REG_S0, UC_ARM_REG_S1, UC_ARM_REG_S2,
            UC_ARM_REG_S3, UC_ARM_REG_S4, UC_ARM_REG_S5,
            UC_ARM_REG_S6, UC_ARM_REG_S7, UC_ARM_REG_S8,
        ]
        for sr, flt in zip(s_regs, v_floats):
            b = struct.unpack("<I", struct.pack("<f", flt))[0]
            uc.reg_write(sr, b)

        sp = STACK_BASE + STACK_SIZE - 0x100
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00100000)
        uc.reg_write(UC_ARM_REG_R4, 0xAAAAAAAA)

        uc.emu_start(addr, 0x00100000, timeout=200000)

        return {
            "calls": calls,
            "r4": uc.reg_read(UC_ARM_REG_R4),
        }

    test_v = [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5]
    o = run_one(orig, test_v)
    c = run_one(staged, test_v)
    assert o == c, f"002b8070 mismatch: {o} vs {c}"
    print("ui_func_002b8070: PASS")

def test_002d54c4():
    print("--- Testing func_002d54c4 ---")
    addr = 0x002D54C4
    size = 64
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_002d54c4", ROOT / "build")
    symbol_map = {
        "func_002b2530": 0x002B2530,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    R4_ADDR = 0x20001000
    P_ADDR = 0x20002000

    def run_one(c_bytes, has_r4, b2530_ret, f5_val):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # 0x00432CC8 -> R4_ADDR or 0
        r4_ptr = R4_ADDR if has_r4 else 0
        uc.mem_write(0x00432CC8, struct.pack("<I", r4_ptr))

        if has_r4:
            uc.mem_write(R4_ADDR, struct.pack("<I", P_ADDR))
            uc.mem_write(R4_ADDR + 5, bytes([f5_val]))

        uc.mem_write(0x002B2530, b"\x1e\xff\x2f\xe1")
        def on_2530(u, a, s, ud):
            u.reg_write(UC_ARM_REG_R0, b2530_ret)
        uc.hook_add(UC_HOOK_CODE, on_2530, None, 0x002B2530, 0x002B2530)

        sp = STACK_BASE + STACK_SIZE - 0x100
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00100000)
        uc.reg_write(UC_ARM_REG_R4, 0xAAAAAAAA)

        uc.emu_start(addr, 0x00100000, timeout=200000)

        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "r4": uc.reg_read(UC_ARM_REG_R4),
        }

    cases = [
        (False, 0, 0), # r4 is null -> returns 0
        (True, 1, 1),  # func_002b2530 returns 1 -> returns 1
        (True, 0, 0),  # func_002b2530 returns 0, f5 == 0 -> returns 1
        (True, 0, 1),  # func_002b2530 returns 0, f5 != 0 -> returns 0
    ]

    for c_tuple in cases:
        o = run_one(orig, *c_tuple)
        c = run_one(staged, *c_tuple)
        assert o == c, f"002d54c4 mismatch for {c_tuple}: {o} vs {c}"
    print("func_002d54c4: PASS")

if __name__ == "__main__":
    test_0026ea7c()
    test_002701c4()
    test_00275984()
    test_002b8070()
    test_002d54c4()
    print("\nALL 5 FUNCTIONS IN BATCH 13 PASSED DIFFERENTIAL VERIFICATION!")
