#!/usr/bin/env python3
"""Differential test for batch 30 B part 6:
- func_0024b9d0 (0x0024B9D0, 116 B)
- func_00250960 (0x00250960, 120 B)
- engine_func_00253eb0 (0x00253EB0, 116 B)
- camp_func_00254298 (0x00254298, 96 B)
- func_00254a64 (0x00254A64, 96 B)
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
    UC_ARM_REG_R7,
    UC_ARM_REG_R8,
    UC_ARM_REG_SB,
    UC_ARM_REG_SL,
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
SOURCE = ROOT / "src/engine/leaf_batch30_b.cpp"

def load_original_bytes(addr: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(addr - CODE_BASE)
        return f.read(size)

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch30_b.o"
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


def test_0024b9d0():
    print("--- Testing func_0024b9d0 ---")
    addr = 0x0024B9D0
    size = 116
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_0024b9d0", ROOT / "build")
    staged = stage_body(comp, relocs, addr, {})

    OBJ = 0x20001000
    SUB = 0x20002000
    BASE = 0x20005000

    def run_one(c_bytes, w, h, f4, slot_idx):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # clear base area
        uc.mem_write(BASE, b"\x00" * 0x2000)

        uc.mem_write(OBJ + 0x20, struct.pack("<I", SUB))
        uc.mem_write(OBJ + 0x18, struct.pack("<I", BASE))
        uc.mem_write(OBJ + 4, struct.pack("<i", f4))

        uc.mem_write(SUB + 0xC0, struct.pack("<ii", w, h))

        pos = BASE + slot_idx * 40

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, OBJ)
        uc.reg_write(UC_ARM_REG_R1, pos)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)

        mem = uc.mem_read(BASE, 0x2000)
        r4 = uc.reg_read(UC_ARM_REG_R4)
        return mem, r4

    cases = [
        (0, 5, 0, 0),    # count <= 0 -> no write
        (-1, 5, 0, 0),   # count < 0 -> no write
        (1, 1, 0, 0),    # count == 1
        (2, 2, 1, 3),    # count == 4
        (3, 4, 2, 1),    # count == 12
    ]

    for w, h, f4, s_idx in cases:
        orig_mem, orig_r4 = run_one(orig, w, h, f4, s_idx)
        comp_mem, comp_r4 = run_one(staged, w, h, f4, s_idx)
        assert orig_mem == comp_mem, "Memory mismatch in func_0024b9d0"
        assert orig_r4 == comp_r4, f"Register mismatch r4: orig={orig_r4}, comp={comp_r4}"

    print("func_0024b9d0: PASS")


def test_00250960():
    print("--- Testing func_00250960 ---")
    addr = 0x00250960
    size = 120
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_00250960", ROOT / "build")
    symbol_map = {"battle_func_00245e2c": 0x00245E2C}
    staged = stage_body(comp, relocs, addr, symbol_map)

    CTX = 0x20001000
    P1 = 0x20010000
    P2 = 0x20030000

    def run_one(c_bytes, mock_val):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Clear P1 and P2 buffers
        uc.mem_write(P1, b"\xaa" * (109 * 648 + 0x100))
        uc.mem_write(P2, b"\xbb" * (109 * 276 + 0x100))

        uc.mem_write(CTX + 0x1FC0, struct.pack("<I", P1))
        uc.mem_write(CTX + 0x1E98, struct.pack("<I", P2))

        def on_5e2c(uc, address, size, user_data):
            assert uc.reg_read(UC_ARM_REG_R0) == 1
            uc.reg_write(UC_ARM_REG_R0, mock_val & 0xFFFFFFFF)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h_mock = uc.hook_add(UC_HOOK_CODE, on_5e2c, None, 0x00245E2C, 0x00245E2C)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, CTX)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=2000000)
        uc.hook_del(h_exit)
        uc.hook_del(h_mock)

        p1_mem = uc.mem_read(P1, 109 * 648 + 0x100)
        p2_mem = uc.mem_read(P2, 109 * 276 + 0x100)
        r4 = uc.reg_read(UC_ARM_REG_R4)
        return p1_mem, p2_mem, r4

    cases = [0x1234, -5, 0, 0x7FFF]

    for val in cases:
        orig_p1, orig_p2, orig_r4 = run_one(orig, val)
        comp_p1, comp_p2, comp_r4 = run_one(staged, val)
        assert orig_p1 == comp_p1, "Mismatch in P1 memory"
        assert orig_p2 == comp_p2, "Mismatch in P2 memory"
        assert orig_r4 == comp_r4, f"Mismatch r4: orig={orig_r4}, comp={comp_r4}"

    print("func_00250960: PASS")


def test_00253eb0():
    print("--- Testing engine_func_00253eb0 ---")
    addr = 0x00253EB0
    size = 116
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_00253eb0", ROOT / "build")
    symbol_map = {"engine_func_002c2b1c": 0x002C2B1C}
    staged = stage_body(comp, relocs, addr, symbol_map)

    BASE = 0x20002000
    ARG0 = 0x20001000

    def run_one(c_bytes, target_val, slots_data):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # clear table area
        uc.mem_write(BASE, b"\x00" * 0x2000)

        uc.mem_write(ARG0 + 0x13A, struct.pack("<h", target_val))

        for i, (flags, val) in enumerate(slots_data):
            slot = BASE + i * 20
            uc.mem_write(slot + 0xF20, struct.pack("<B", flags))
            uc.mem_write(slot + 0xF26, struct.pack("<h", val))

        def on_2c2b1c(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, BASE)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h_mock = uc.hook_add(UC_HOOK_CODE, on_2c2b1c, None, 0x002C2B1C, 0x002C2B1C)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, ARG0)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h_mock)

        mem = uc.mem_read(BASE + 0xF20, 16 * 20)
        r4 = uc.reg_read(UC_ARM_REG_R4)
        return mem, r4

    cases = [
        (42, [(5, 42)] + [(0, 0)] * 15), # match at 0
        (42, [(5, 10)] * 5 + [(5, 42)] + [(0, 0)] * 10), # match at 5
        (42, [(1, 42)] * 16), # flags missing bit 2 (value 4) -> no match
        (42, [(4, 42)] * 16), # flags missing bit 0 (value 1) -> no match
        (42, [(5, 100)] * 16), # values don't match
    ]

    for tgt, s_data in cases:
        orig_mem, orig_r4 = run_one(orig, tgt, s_data)
        comp_mem, comp_r4 = run_one(staged, tgt, s_data)
        assert orig_mem == comp_mem, "Mismatch in engine_func_00253eb0 memory"
        assert orig_r4 == comp_r4, f"Mismatch r4: orig={orig_r4}, comp={comp_r4}"

    print("engine_func_00253eb0: PASS")


def test_00254298():
    print("--- Testing camp_func_00254298 ---")
    addr = 0x00254298
    size = 96
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("camp_func_00254298", ROOT / "build")
    symbol_map = {
        "camp_func_002c0ec4": 0x002C0EC4,
        "camp_func_002c0e9c": 0x002C0E9C,
        "camp_func_002c0e4c": 0x002C0E4C,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    RES1 = 0x20001000
    BASE = 0x20002000

    def run_one(c_bytes, target_id, count, ids_in_table):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # clear table area
        uc.mem_write(BASE, b"\x00" * (count * 64 + 64))

        for i, tid in enumerate(ids_in_table):
            uc.mem_write(BASE + i * 64, struct.pack("<H", tid))

        def on_2c0ec4(uc, address, size, user_data):
            assert uc.reg_read(UC_ARM_REG_R0) == 0x24
            assert uc.reg_read(UC_ARM_REG_R1) == 1
            uc.reg_write(UC_ARM_REG_R0, RES1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_2c0e9c(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, BASE)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_2c0e4c(uc, address, size, user_data):
            assert uc.reg_read(UC_ARM_REG_R0) == RES1
            uc.reg_write(UC_ARM_REG_R0, count)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h1 = uc.hook_add(UC_HOOK_CODE, on_2c0ec4, None, 0x002C0EC4, 0x002C0EC4)
        h2 = uc.hook_add(UC_HOOK_CODE, on_2c0e9c, None, 0x002C0E9C, 0x002C0E9C)
        h3 = uc.hook_add(UC_HOOK_CODE, on_2c0e4c, None, 0x002C0E4C, 0x002C0E4C)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, target_id)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h1)
        uc.hook_del(h2)
        uc.hook_del(h3)

        r0 = uc.reg_read(UC_ARM_REG_R0)
        regs = [uc.reg_read(getattr(sys.modules[__name__], f"UC_ARM_REG_R{i}")) for i in range(4, 7)]
        return r0, regs

    cases = [
        (10, 0, []),
        (10, 5, [10, 20, 30, 40, 50]), # match at index 0
        (40, 5, [10, 20, 30, 40, 50]), # match at index 3
        (99, 5, [10, 20, 30, 40, 50]), # no match
    ]

    for tid, cnt, tids in cases:
        orig_r0, orig_regs = run_one(orig, tid, cnt, tids)
        comp_r0, comp_regs = run_one(staged, tid, cnt, tids)
        assert orig_r0 == comp_r0, f"Mismatch r0: orig={hex(orig_r0)}, comp={hex(comp_r0)}"
        assert orig_regs == comp_regs, f"Mismatch regs: orig={orig_regs}, comp={comp_regs}"

    print("camp_func_00254298: PASS")


def test_00254a64():
    print("--- Testing func_00254a64 ---")
    addr = 0x00254A64
    size = 96
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_00254a64", ROOT / "build")
    staged = stage_body(comp, relocs, addr, {})

    def run_one(c_bytes, val_in):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, val_in)
        uc.reg_write(UC_ARM_REG_R3, 0xCAFEBABE)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)

        r3 = uc.reg_read(UC_ARM_REG_R3)
        return r3

    cases = [
        0x12345678,                                 # bit 31 clear
        0x80000000 | (0x10 << 10) | 400,            # cat 0x10 != 0x11
        0x80000000 | (0x11 << 10) | 50,             # cat 0x11, code 50 (< 100)
        0x80000000 | (0x11 << 10) | 120,            # cat 0x11, code 120 (100..179)
        0x80000000 | (0x11 << 10) | 250,            # cat 0x11, code 250 (180..339)
        0x80000000 | (0x11 << 10) | 350,            # cat 0x11, code 350 (340..359)
        0x80000000 | (0x11 << 10) | 360,            # cat 0x11, code 360 (>= 360) -> 0x185!
        0x80000000 | (0x11 << 10) | 500,            # cat 0x11, code 500 (>= 360) -> 0x185!
    ]

    for v in cases:
        orig_r3 = run_one(orig, v)
        comp_r3 = run_one(staged, v)
        assert orig_r3 == comp_r3, f"Mismatch r3: val={hex(v)} -> orig={hex(orig_r3)}, comp={hex(comp_r3)}"

    print("func_00254a64: PASS")


if __name__ == "__main__":
    test_0024b9d0()
    test_00250960()
    test_00253eb0()
    test_00254298()
    test_00254a64()
    print("\nALL 5 FUNCTIONS PASSED 100% DIFFERENTIAL VERIFICATION!")
