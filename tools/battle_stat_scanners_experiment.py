#!/usr/bin/env python3
"""Differential test for battle entity stat scanners:
- ui_func_002f033c (0x002F033C, 148 B)
- ui_func_002f0520 (0x002F0520, 140 B)
- ui_func_002f6cf0 (0x002F6CF0, 148 B)
- engine_func_002ff050 (0x002FF050, 148 B)

Validates that reconstructed C++ matches original ARM binary:
- Evaluates individual and collective entity stats (HP percentages, averages, level thresholds).
- Preserves non-volatile registers (r4, r5, r6, r7, r8).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys

from unicorn import (
    Uc,
    UC_ARCH_ARM,
    UC_MODE_ARM,
)
from unicorn.arm_const import (
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

STUB_GET_P = 0x00296F60
STUB_GET_CTX = 0x00293C98
STUB_CALLBACK = 0x0028DF54
STUB_DIV = 0x002C615C

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

SYMBOL_MAP = {
    "engine_func_00296f60": STUB_GET_P,
    "ui_func_00293c98": STUB_GET_CTX,
    "battle_func_0028df54": STUB_CALLBACK,
    "ui_func_002c615c": STUB_DIV,
}


def load_original_bytes(addr: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(addr - 0x00100000)
        return f.read(size)


COMPILED_FUNCTIONS = None

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
    body, relocs = COMPILED_FUNCTIONS[func_name]
    return body, relocs


def stage_body(body: bytes, relocs, target_addr: int) -> bytes:
    data = bytearray(body)
    for reloc in relocs:
        sym = reloc.symbol_name
        if sym not in SYMBOL_MAP:
            raise RuntimeError(f"Unmapped relocation: {sym}")
        stub_addr = SYMBOL_MAP[sym]
        rel_off = stub_addr - (target_addr + reloc.offset + 8)
        imm24 = (rel_off >> 2) & 0x00FFFFFF
        inst = struct.unpack_from("<I", data, reloc.offset)[0]
        inst = (inst & 0xFF000000) | imm24
        struct.pack_into("<I", data, reloc.offset, inst)
    return bytes(data)


def build_emulator(code_bytes: bytes, target_addr: int) -> Uc:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_write(target_addr, code_bytes)

    # Stubs
    # engine_func_00296f60: if r0 == 0 returns *(0x20000000), else *(0x20000004)
    stub_p = (
        b"\x0c\x10\x9f\xe5"  # ldr r1, [pc, #12] -> 0x20000000
        b"\x00\x10\x81\xe0"  # add r1, r1, r0, lsl #2
        b"\x00\x00\x91\xe5"  # ldr r0, [r1]
        b"\x1e\xff\x2f\xe1"  # bx lr
        b"\x00\x00\x00\x00"  # pad
        + struct.pack("<I", 0x20000000)
    )

    stub_ctx = (
        b"\x04\x00\x9f\xe5"  # ldr r0, [pc, #4]
        b"\x00\x00\x90\xe5"  # ldr r0, [r0]
        b"\x1e\xff\x2f\xe1"  # bx lr
        + struct.pack("<I", 0x20000008)
    )

    stub_cb = (
        b"\x10\x10\x9f\xe5"  # ldr r1, [pc, #16]
        b"\x00\x00\x81\xe5"  # str r0, [r1]
        b"\x04\x20\x91\xe5"  # ldr r2, [r1, #4]
        b"\x01\x20\x82\xe2"  # add r2, r2, #1
        b"\x04\x20\x81\xe5"  # str r2, [r1, #4]
        b"\x1e\xff\x2f\xe1"  # bx lr
        + struct.pack("<I", 0x2000000C)
    )

    uc.mem_write(STUB_GET_P, stub_p)
    uc.mem_write(STUB_GET_CTX, stub_ctx)
    uc.mem_write(STUB_CALLBACK, stub_cb)
    uc.mem_write(STUB_DIV, load_original_bytes(STUB_DIV, 0x200))

    return uc


def run_test(func_name: str, addr: int, size: int, p0: int, p1: int, setup_entities_fn):
    out_dir = ROOT / "build"
    orig_bytes = load_original_bytes(addr, size)
    comp_bytes, relocs = compile_function(func_name, out_dir)
    staged_comp = stage_body(comp_bytes, relocs, addr)

    def run_one(bytes_to_run):
        uc = build_emulator(bytes_to_run, addr)
        DATA_BASE = 0x20000000
        DATA_SIZE = 0x40000
        uc.mem_map(DATA_BASE, DATA_SIZE)

        CTX_ADDR = 0x20001000
        TABLE_ADDR = 0x20004000

        uc.mem_write(DATA_BASE + 0, struct.pack("<I", p0))
        uc.mem_write(DATA_BASE + 4, struct.pack("<I", p1))
        uc.mem_write(DATA_BASE + 8, struct.pack("<I", CTX_ADDR))
        uc.mem_write(DATA_BASE + 12, struct.pack("<I", 0xDEADBEEF))
        uc.mem_write(DATA_BASE + 16, struct.pack("<I", 0))

        uc.mem_write(CTX_ADDR + 0x1FC0, struct.pack("<I", TABLE_ADDR))

        setup_entities_fn(uc, TABLE_ADDR)

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(bytes_to_run)

        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)
        uc.reg_write(UC_ARM_REG_R7, 0x44444444)
        uc.reg_write(UC_ARM_REG_R8, 0x55555555)

        uc.emu_start(addr, lr, timeout=3000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        cb_val = struct.unpack("<I", uc.mem_read(DATA_BASE + 12, 4))[0]
        cb_count = struct.unpack("<I", uc.mem_read(DATA_BASE + 16, 4))[0]
        r4 = uc.reg_read(UC_ARM_REG_R4)
        r5 = uc.reg_read(UC_ARM_REG_R5)
        r6 = uc.reg_read(UC_ARM_REG_R6)
        r7 = uc.reg_read(UC_ARM_REG_R7)
        r8 = uc.reg_read(UC_ARM_REG_R8)

        return {
            "ret": ret,
            "cb_val": cb_val,
            "cb_count": cb_count,
            "r4": r4,
            "r5": r5,
            "r6": r6,
            "r7": r7,
            "r8": r8,
        }

    orig_res = run_one(orig_bytes)
    comp_res = run_one(staged_comp)
    return orig_res == comp_res, orig_res, comp_res


def main():
    all_passed = True

    # 1. Test ui_func_002f033c (checks if any entity HP pct >= threshold)
    def setup_hp_test_hit(uc, table):
        # Entity 0: active (flags=0x11), curr=80, max=100 -> pct = 80 >= 50
        uc.mem_write(table, struct.pack("<I", 0x11))
        uc.mem_write(table + 0x1B4, struct.pack("<H", 80))
        uc.mem_write(table + 0x1B6, struct.pack("<h", 100))

    passed, o, c = run_test("ui_func_002f033c", 0x002F033C, 148, 50, 0, setup_hp_test_hit)
    print(f"[{'PASS' if passed else 'FAIL'}] ui_func_002f033c hit: {o == c}")
    if not passed: all_passed = False

    def setup_hp_test_miss(uc, table):
        # Entity 0: active, curr=20, max=100 -> pct = 20 < 50
        uc.mem_write(table, struct.pack("<I", 0x11))
        uc.mem_write(table + 0x1B4, struct.pack("<H", 20))
        uc.mem_write(table + 0x1B6, struct.pack("<h", 100))

    passed, o, c = run_test("ui_func_002f033c", 0x002F033C, 148, 50, 0, setup_hp_test_miss)
    print(f"[{'PASS' if passed else 'FAIL'}] ui_func_002f033c miss: {o == c}")
    if not passed: all_passed = False

    # 2. Test ui_func_002f0520 (checks threshold <= avg(elem+0x1cc))
    def setup_avg_test(uc, table):
        # 2 entities: 100 and 200 -> avg = 150
        uc.mem_write(table, struct.pack("<I", 0x11))
        uc.mem_write(table + 0x1CC, struct.pack("<H", 100))
        uc.mem_write(table + 648, struct.pack("<I", 0x11))
        uc.mem_write(table + 648 + 0x1CC, struct.pack("<H", 200))

    passed, o, c = run_test("ui_func_002f0520", 0x002F0520, 140, 150, 0, setup_avg_test)
    print(f"[{'PASS' if passed else 'FAIL'}] ui_func_002f0520 avg_150_thresh_150: {o == c}")
    if not passed: all_passed = False

    passed, o, c = run_test("ui_func_002f0520", 0x002F0520, 140, 151, 0, setup_avg_test)
    print(f"[{'PASS' if passed else 'FAIL'}] ui_func_002f0520 avg_150_thresh_151: {o == c}")
    if not passed: all_passed = False

    # 3. Test ui_func_002f6cf0 (checks sum_curr*100 / sum_max <= threshold)
    def setup_party_hp(uc, table):
        # 2 entities: curr 50/100, curr 50/100 -> total 100/200 = 50%
        uc.mem_write(table, struct.pack("<I", 0x11))
        uc.mem_write(table + 0x1B4, struct.pack("<h", 50))
        uc.mem_write(table + 0x1B6, struct.pack("<h", 100))
        uc.mem_write(table + 648, struct.pack("<I", 0x11))
        uc.mem_write(table + 648 + 0x1B4, struct.pack("<h", 50))
        uc.mem_write(table + 648 + 0x1B6, struct.pack("<h", 100))

    passed, o, c = run_test("ui_func_002f6cf0", 0x002F6CF0, 148, 50, 0, setup_party_hp)
    print(f"[{'PASS' if passed else 'FAIL'}] ui_func_002f6cf0 50pct_thresh_50: {o == c}")
    if not passed: all_passed = False

    passed, o, c = run_test("ui_func_002f6cf0", 0x002F6CF0, 148, 49, 0, setup_party_hp)
    print(f"[{'PASS' if passed else 'FAIL'}] ui_func_002f6cf0 50pct_thresh_49: {o == c}")
    if not passed: all_passed = False

    # 4. Test engine_func_002ff050 (checks val0 == p0 and val1 >= p1)
    def setup_type_lvl(uc, table):
        # Entity 0: type=7, lvl=45
        uc.mem_write(table, struct.pack("<I", 0x11))
        uc.mem_write(table + 0xCE, struct.pack("<H", 7))
        uc.mem_write(table + 0x1CC, struct.pack("<H", 45))

    passed, o, c = run_test("engine_func_002ff050", 0x002FF050, 148, 7, 40, setup_type_lvl)
    print(f"[{'PASS' if passed else 'FAIL'}] engine_func_002ff050 hit: {o == c}")
    if not passed: all_passed = False

    passed, o, c = run_test("engine_func_002ff050", 0x002FF050, 148, 7, 50, setup_type_lvl)
    print(f"[{'PASS' if passed else 'FAIL'}] engine_func_002ff050 miss_lvl: {o == c}")
    if not passed: all_passed = False

    passed, o, c = run_test("engine_func_002ff050", 0x002FF050, 148, 8, 40, setup_type_lvl)
    print(f"[{'PASS' if passed else 'FAIL'}] engine_func_002ff050 miss_type: {o == c}")
    if not passed: all_passed = False

    print(f"\nOverall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
