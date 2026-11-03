#!/usr/bin/env python3
"""Differential test for batch 30 functions:
- ui_func_002dba40 (0x002DBA40, 148 B)
- script_vm_func_002fb4c0 (0x002FB4C0, 140 B)
- engine_func_002ed47c (0x002ED47C, 144 B)
- script_vm_func_002eb59c (0x002EB59C, 152 B)
- script_vm_func_002e11bc (0x002E11BC, 148 B)
- script_vm_func_002d5780 (0x002D5780, 136 B)
"""

from __future__ import annotations

import argparse
from pathlib import Path
import struct
import sys

from unicorn import (
    Uc,
    UC_ARCH_ARM,
    UC_MODE_ARM,
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
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
    UC_ARM_REG_S0,
    UC_ARM_REG_S1,
    UC_ARM_REG_S2,
    UC_ARM_REG_S3,
    UC_ARM_REG_S4,
    UC_ARM_REG_S16,
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
        f.seek(addr - 0x00100000)
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

def base_emulator(code_bytes: bytes, target_addr: int) -> Uc:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.ctl_set_cpu_model(UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_write(target_addr, code_bytes)
    # Map division runtime function
    uc.mem_write(0x002C615C, load_original_bytes(0x002C615C, 0x200))
    return uc

def test_002dba40():
    print("--- Testing ui_func_002dba40 ---")
    addr = 0x002DBA40
    size = 148
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_002dba40", ROOT / "build")
    syms = {
        "engine_func_00296f60": 0x00296F60,
        "ui_func_00293c98": 0x00293C98,
        "battle_func_0028df54": 0x0028DF54,
        "ui_func_002c615c": 0x002C615C,
    }
    staged = stage_body(comp, relocs, addr, syms)

    def run_one(c_bytes, hp, max_hp, thresh):
        uc = base_emulator(c_bytes, addr)
        DATA_BASE = 0x20000000
        uc.mem_map(DATA_BASE, 0x40000)
        CTX = 0x20001000
        TABLE = 0x20004000

        # stubs
        # 0x296f60 returns thresh
        uc.mem_write(0x00296F60, b"\x00\x00\xa0\xe3\x1e\xff\x2f\xe1") # mov r0, #0; bx lr
        # Patch mov r0, thresh
        uc.mem_write(0x00296F60, struct.pack("<I", 0xe3a00000 | (thresh & 0xff)) + b"\x1e\xff\x2f\xe1")
        # 0x293c98 returns CTX
        uc.mem_write(0x00293C98, (
            b"\x04\x00\x9f\xe5"
            b"\x00\x00\x90\xe5"
            b"\x1e\xff\x2f\xe1"
            + struct.pack("<I", DATA_BASE)
        ))
        uc.mem_write(DATA_BASE, struct.pack("<I", CTX))
        uc.mem_write(CTX + 0x1FC0, struct.pack("<I", TABLE))

        # 0x28df54 callback
        uc.mem_write(0x0028DF54, (
            b"\x08\x10\x9f\xe5"
            b"\x00\x00\x81\xe5"
            b"\x1e\xff\x2f\xe1"
            b"\x00\x00\x00\x00"
            + struct.pack("<I", DATA_BASE + 0x10)
        ))
        uc.mem_write(DATA_BASE + 0x10, struct.pack("<I", 0xDEADBEEF))

        # Setup entity 0
        uc.mem_write(TABLE, struct.pack("<I", 0x11))
        uc.mem_write(TABLE + 0x1B4, struct.pack("<H", hp))
        uc.mem_write(TABLE + 0x1B6, struct.pack("<h", max_hp))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "cb": struct.unpack("<I", uc.mem_read(DATA_BASE + 0x10, 4))[0],
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
        }

    # Test cases:
    # 1. Hit: 30/100 = 30% <= 50% -> cb=1
    o1 = run_one(orig, 30, 100, 50)
    c1 = run_one(staged, 30, 100, 50)
    assert o1 == c1 and o1["cb"] == 1, f"002dba40 hit failed: {o1} vs {c1}"

    # 2. Miss: 60/100 = 60% > 50% -> cb=0
    o2 = run_one(orig, 60, 100, 50)
    c2 = run_one(staged, 60, 100, 50)
    assert o2 == c2 and o2["cb"] == 0, f"002dba40 miss failed: {o2} vs {c2}"
    print("ui_func_002dba40: PASS")

def test_002fb4c0():
    print("--- Testing script_vm_func_002fb4c0 ---")
    addr = 0x002FB4C0
    size = 140
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_002fb4c0", ROOT / "build")
    syms = {
        "engine_func_00289640": 0x00289640,
        "battle_func_0028df3c": 0x0028DF3C,
        "battle_func_0028df0c": 0x0028DF0C,
        "script_vm_func_0027605c": 0x0027605C,
        "script_vm_func_00270298": 0x00270298,
        "battle_func_002b91c4": 0x002B91C4,
    }
    staged = stage_body(comp, relocs, addr, syms)

    def run_one(c_bytes, mode):
        uc = base_emulator(c_bytes, addr)
        DATA_BASE = 0x20000000
        uc.mem_map(DATA_BASE, 0x1000)

        # 0x289640 returns mode
        uc.mem_write(0x00289640, struct.pack("<I", 0xe3a00000 | (mode & 0xff)) + b"\x1e\xff\x2f\xe1")

        def make_recorder(addr_stub, off):
            uc.mem_write(addr_stub, (
                b"\x08\x10\x9f\xe5"
                b"\x00\x00\x81\xe5"
                b"\x1e\xff\x2f\xe1"
                b"\x00\x00\x00\x00"
                + struct.pack("<I", DATA_BASE + off)
            ))
        make_recorder(0x0028DF3C, 0x00)
        make_recorder(0x0028DF0C, 0x04)
        make_recorder(0x00270298, 0x08)
        make_recorder(0x002B91C4, 0x0C)
        # 0x0027605c nop
        uc.mem_write(0x0027605C, b"\x1e\xff\x2f\xe1")

        for off in range(0, 0x10, 4):
            uc.mem_write(DATA_BASE + off, struct.pack("<I", 0xDEADBEEF))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "df3c": struct.unpack("<I", uc.mem_read(DATA_BASE + 0x00, 4))[0],
            "df0c": struct.unpack("<I", uc.mem_read(DATA_BASE + 0x04, 4))[0],
            "0298": struct.unpack("<I", uc.mem_read(DATA_BASE + 0x08, 4))[0],
            "91c4": struct.unpack("<I", uc.mem_read(DATA_BASE + 0x0C, 4))[0],
            "r4": uc.reg_read(UC_ARM_REG_R4),
        }

    for mode in [0, 1, 2, 3, 5]:
        o = run_one(orig, mode)
        c = run_one(staged, mode)
        assert o == c, f"002fb4c0 mode {mode} failed: {o} vs {c}"
    print("script_vm_func_002fb4c0: PASS")

def test_002ed47c():
    print("--- Testing engine_func_002ed47c ---")
    addr = 0x002ED47C
    size = 144
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_002ed47c", ROOT / "build")
    syms = {
        "engine_func_00286880": 0x00286880,
        "engine_func_0028686c": 0x0028686C,
        "engine_func_00296f60": 0x00296F60,
        "engine_func_00289640": 0x00289640,
        "engine_func_00286928": 0x00286928,
        "battle_func_002b8574": 0x002B8574,
    }
    staged = stage_body(comp, relocs, addr, syms)

    def run_one(c_bytes, r5_code, mode):
        uc = base_emulator(c_bytes, addr)
        DATA_BASE = 0x20000000
        uc.mem_map(DATA_BASE, 0x1000)
        PTR_BLOCK = 0x20000100
        # 0x0043E188 is within CODE_BASE (0x00100000..0x00480000), already mapped
        uc.mem_write(0x0043E188 + 4, struct.pack("<I", PTR_BLOCK))

        uc.mem_write(PTR_BLOCK + 4, struct.pack("<I", 0x77777777))
        uc.mem_write(PTR_BLOCK + 0xC, struct.pack("<I", 0x1))
        uc.mem_write(PTR_BLOCK + 0xA10, struct.pack("<B", 0xFF))

        # Stubs
        uc.mem_write(0x00286880, struct.pack("<I", 0xe3a00000 | (r5_code & 0xff)) + b"\x1e\xff\x2f\xe1")
        uc.mem_write(0x0028686C, b"\x12\x00\xa0\xe3\x1e\xff\x2f\xe1") # mov r0, #0x12; bx lr
        uc.mem_write(0x00296F60, b"\x34\x00\xa0\xe3\x1e\xff\x2f\xe1") # mov r0, #0x34; bx lr
        uc.mem_write(0x00289640, struct.pack("<I", 0xe3a00000 | (mode & 0xff)) + b"\x1e\xff\x2f\xe1")
        # 0x286928 returns r0 + r1 + r2 + r3
        uc.mem_write(0x00286928, (
            b"\x01\x00\x80\xe0" # add r0, r0, r1
            b"\x02\x00\x80\xe0" # add r0, r0, r2
            b"\x03\x00\x80\xe0" # add r0, r0, r3
            b"\x1e\xff\x2f\xe1" # bx lr
        ))
        # 0x2b8574 records r0
        uc.mem_write(0x002B8574, (
            b"\x08\x10\x9f\xe5"
            b"\x00\x00\x81\xe5"
            b"\x1e\xff\x2f\xe1"
            b"\x00\x00\x00\x00"
            + struct.pack("<I", DATA_BASE)
        ))
        uc.mem_write(DATA_BASE, struct.pack("<I", 0xDEADBEEF))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)
        uc.reg_write(UC_ARM_REG_R7, 0x44444444)
        uc.reg_write(UC_ARM_REG_R8, 0x55555555)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "b8574": struct.unpack("<I", uc.mem_read(DATA_BASE, 4))[0],
            "flag": struct.unpack("<I", uc.mem_read(PTR_BLOCK + 0xC, 4))[0],
            "byte_a10": struct.unpack("<B", uc.mem_read(PTR_BLOCK + 0xA10, 1))[0],
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
            "r8": uc.reg_read(UC_ARM_REG_R8),
        }

    for r5 in [0x14, 0x10]:
        for mode in [0, 1]:
            o = run_one(orig, r5, mode)
            c = run_one(staged, r5, mode)
            assert o == c, f"002ed47c (r5={r5}, mode={mode}) failed: {o} vs {c}"
    print("engine_func_002ed47c: PASS")

def test_002eb59c():
    print("--- Testing script_vm_func_002eb59c ---")
    addr = 0x002EB59C
    size = 152
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_002eb59c", ROOT / "build")
    syms = {
        "script_vm_func_002711e0": 0x002711E0,
    }
    staged = stage_body(comp, relocs, addr, syms)

    def run_one(c_bytes, flag284):
        uc = base_emulator(c_bytes, addr)
        # Map 0x0049F000 (0x00447000 is inside CODE_BASE, already mapped)
        uc.mem_map(0x0049F000, 0x2000)

        G_SYS = 0x0049F91C
        R4_OBJ = 0x00447100
        uc.mem_write(0x00447E28, struct.pack("<I", R4_OBJ))

        # Setup G_SYS
        uc.mem_write(G_SYS + 0x284, struct.pack("<B", flag284))
        uc.mem_write(G_SYS + 0x8, struct.pack("<I", 0x12345678))
        uc.mem_write(G_SYS + 0x90, struct.pack("<f", 10.0))
        uc.mem_write(G_SYS + 0x94, struct.pack("<fff", 1.0, 2.0, 3.0))

        # Setup R4_OBJ
        uc.mem_write(R4_OBJ + 0x2C, struct.pack("<f", 4.0))
        uc.mem_write(R4_OBJ + 0x30, struct.pack("<f", 5.0))

        # Stub 0x2711e0: write 0xABCD into G_SYS + 0x2F4
        uc.mem_write(0x002711E0, (
            b"\x04\x10\x9f\xe5"
            b"\x00\x10\x80\xe5"
            b"\x1e\xff\x2f\xe1"
            + struct.pack("<I", 0xABCD)
        ))

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "flag284": struct.unpack("<B", uc.mem_read(G_SYS + 0x284, 1))[0],
            "flag2f8": struct.unpack("<B", uc.mem_read(G_SYS + 0x2F8, 1))[0],
            "u2fc": struct.unpack("<I", uc.mem_read(G_SYS + 0x2FC, 4))[0],
            "u300": struct.unpack("<I", uc.mem_read(G_SYS + 0x300, 4))[0],
            "u304": struct.unpack("<I", uc.mem_read(G_SYS + 0x304, 4))[0],
            "vec_308": struct.unpack("<fff", uc.mem_read(G_SYS + 0x308, 12)),
            "f_314": struct.unpack("<ff", uc.mem_read(G_SYS + 0x314, 8)),
            "f_31c": struct.unpack("<ff", uc.mem_read(G_SYS + 0x31C, 8)),
            "vec_324": struct.unpack("<fff", uc.mem_read(G_SYS + 0x324, 12)),
            "f_330": struct.unpack("<ff", uc.mem_read(G_SYS + 0x330, 8)),
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
        }

    for f in [1, 0]:
        o = run_one(orig, f)
        c = run_one(staged, f)
        assert o == c, f"002eb59c (flag={f}) failed: {o} vs {c}"
    print("script_vm_func_002eb59c: PASS")

def test_002e11bc():
    print("--- Testing script_vm_func_002e11bc ---")
    addr = 0x002E11BC
    size = 148
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_002e11bc", ROOT / "build")
    syms = {
        "script_vm_func_00254c6c": 0x00254C6C,
        "script_vm_func_002e1180": 0x002E1180,
    }
    staged = stage_body(comp, relocs, addr, syms)

    def run_one(c_bytes, count, flag):
        uc = base_emulator(c_bytes, addr)
        DATA_BASE = 0x20000000
        uc.mem_map(DATA_BASE, 0x10000)

        OBJ = DATA_BASE + 0x100
        INNER = DATA_BASE + 0x200
        P2C = DATA_BASE + 0x400
        P28 = DATA_BASE + 0x600
        ARRAY = DATA_BASE + 0x800
        TARGET = DATA_BASE + 0xA00

        uc.mem_write(OBJ + 8, struct.pack("<I", INNER))
        uc.mem_write(INNER + 0x68, struct.pack("<i", count))
        uc.mem_write(INNER + 0x2C, struct.pack("<I", P2C))

        uc.mem_write(P2C + 0x150, struct.pack("<I", 1))
        uc.mem_write(P2C + 0x28, struct.pack("<I", P28))
        uc.mem_write(P2C + 0x154, struct.pack("<I", 2)) # idx = 2

        uc.mem_write(P28 + 0x28, struct.pack("<I", 3)) # stride = 3 -> idx*stride = 6
        uc.mem_write(P28 + 0x1C, struct.pack("<I", ARRAY))

        uc.mem_write(ARRAY + 6 * 4, struct.pack("<I", TARGET))
        uc.mem_write(TARGET + 0x58, b"\x00")
        uc.mem_write(TARGET + 0x4C, struct.pack("<I", 0))

        # Stubs
        uc.mem_write(0x00254C6C, b"\x1e\xff\x2f\xe1")
        uc.mem_write(0x002E1180, b"\x1e\xff\x2f\xe1")

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, OBJ)
        uc.reg_write(UC_ARM_REG_R1, flag)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "b58": struct.unpack("<B", uc.mem_read(TARGET + 0x58, 1))[0],
            "u4c": struct.unpack("<I", uc.mem_read(TARGET + 0x4C, 4))[0],
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
        }

    for cnt in [0, 5]:
        for flg in [0, 1]:
            o = run_one(orig, cnt, flg)
            c = run_one(staged, cnt, flg)
            assert o == c, f"002e11bc (cnt={cnt}, flg={flg}) failed: {o} vs {c}"
    print("script_vm_func_002e11bc: PASS")

def test_002d5780():
    print("--- Testing script_vm_func_002d5780 ---")
    addr = 0x002D5780
    size = 136
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_002d5780", ROOT / "build")
    syms = {
        "script_vm_func_0029bdb4": 0x0029BDB4,
        "script_vm_func_0028c8d0": 0x0028C8D0,
    }
    staged = stage_body(comp, relocs, addr, syms)

    def run_one(c_bytes, count, vol):
        uc = base_emulator(c_bytes, addr)
        DATA_BASE = 0x20000000
        uc.mem_map(DATA_BASE, 0x10000)

        OBJ = DATA_BASE + 0x100
        INNER = DATA_BASE + 0x200
        P2C = DATA_BASE + 0x400
        P28 = DATA_BASE + 0x600
        ARRAY = DATA_BASE + 0x800
        TARGET = DATA_BASE + 0xA00

        uc.mem_write(OBJ + 8, struct.pack("<I", INNER))
        uc.mem_write(INNER + 0x68, struct.pack("<i", count))
        uc.mem_write(INNER + 0x74, struct.pack("<f", 0.5)) # scale_factor = 0.5
        uc.mem_write(INNER + 0x2C, struct.pack("<I", P2C))

        uc.mem_write(P2C + 0x150, struct.pack("<I", 1))
        uc.mem_write(P2C + 0x28, struct.pack("<I", P28))
        uc.mem_write(P2C + 0x154, struct.pack("<I", 1))

        uc.mem_write(P28 + 0x28, struct.pack("<I", 2))
        uc.mem_write(P28 + 0x1C, struct.pack("<I", ARRAY))

        uc.mem_write(ARRAY + 2 * 4, struct.pack("<I", TARGET))
        uc.mem_write(TARGET + 0x40, struct.pack("<f", 0.0))

        # Stubs
        uc.mem_write(0x0029BDB4, b"\x1e\xff\x2f\xe1")
        uc.mem_write(0x0028C8D0, b"\x1e\xff\x2f\xe1")

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, OBJ)
        uc.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", vol))[0])
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "vol80": struct.unpack("<f", uc.mem_read(INNER + 0x80, 4))[0] if count > 0 else 0,
            "target40": struct.unpack("<f", uc.mem_read(TARGET + 0x40, 4))[0],
            "r4": uc.reg_read(UC_ARM_REG_R4),
        }

    for cnt in [0, 4]:
        for vol in [0.8, 1.2]:
            o = run_one(orig, cnt, vol)
            c = run_one(staged, cnt, vol)
            assert o == c, f"002d5780 (cnt={cnt}, vol={vol}) failed: {o} vs {c}"
    print("script_vm_func_002d5780: PASS")

def main():
    test_002dba40()
    test_002fb4c0()
    test_002ed47c()
    test_002eb59c()
    test_002e11bc()
    test_002d5780()
    print("\nALL 6 FUNCTIONS PASSED DIFFERENTIAL VERIFICATION!")

if __name__ == "__main__":
    main()
