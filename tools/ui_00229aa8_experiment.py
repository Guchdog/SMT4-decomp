#!/usr/bin/env python3
"""Differential test for ui_func_00229aa8 (0x00229AA8).

Validates that reconstructed C++ matches original ARM binary across all branches:
- node == nullptr -> uses default_idx
- node != nullptr -> uses *(s16*)(node + 0x6E)
- flag != 0 -> returns 0
- elem_flags bit 0 not set -> returns 0
- elem_flags bit 22 set -> returns 0
- timer > 0 -> returns 0
- timer <= 0 -> returns 1
- verifies preservation of non-volatile registers (r4, r5, r6, r7, r8).
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
    UC_ARM_REG_PC,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
ORIG_ADDR = 0x00229AA8
ORIG_SIZE = 132

STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

STUB_00282B94 = 0x00282B94

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

SYMBOL_MAP = {
    "ui_func_00282b94": STUB_00282B94,
}


def load_original_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(ORIG_ADDR - 0x00100000)
        return f.read(ORIG_SIZE)


def compile_body(out: Path, source: Path = SOURCE):
    obj = out / "leaf_batch30_c.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    functions = extract_elf_functions_detailed(obj)
    if "ui_func_00229aa8" not in functions:
        raise RuntimeError("ui_func_00229aa8 not in object")
    body, relocs = functions["ui_func_00229aa8"]
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
        branch_ins = 0xEB000000 | imm24
        struct.pack_into("<I", data, reloc.offset, branch_ins)
    return bytes(data)


def run_single(code_bytes: bytes, entry_addr: int, has_node: bool, node_idx: int,
               default_idx: int, flag_val: int, elem_flags: int, timer_val: int):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    DATA_PAGE = 0x20000000
    uc.mem_map(DATA_PAGE, 0x100000)

    # Write code under test
    uc.mem_write(entry_addr, code_bytes)

    # Layout in DATA_PAGE:
    # 0x100: OBJ_PTR (holds pointer to INNER_MEM)
    # 0x1000: INNER_MEM (holds pointer at +0x1FC0 to ENTITY_TABLE)
    # 0x10000: ENTITY_TABLE (records of 648 bytes)
    # 0x40000: TABLE_MEM (table with flags at +0x9D4 + idx * 10)
    # 0x60000: NODE_MEM (holds s16 at +0x6E)

    OBJ_PTR = DATA_PAGE + 0x100
    INNER_MEM = DATA_PAGE + 0x1000
    ENTITY_TABLE = DATA_PAGE + 0x10000
    TABLE_MEM = DATA_PAGE + 0x40000
    NODE_MEM = DATA_PAGE + 0x60000

    uc.mem_write(OBJ_PTR, struct.pack("<I", INNER_MEM))
    uc.mem_write(INNER_MEM + 0x1FC0, struct.pack("<I", ENTITY_TABLE))

    if has_node:
        uc.mem_write(NODE_MEM + 0x6E, struct.pack("<h", node_idx))
        ret_node = NODE_MEM
        effective_idx = node_idx
    else:
        ret_node = 0
        effective_idx = default_idx

    # Write flag at TABLE_MEM + 0x9D4 + effective_idx * 10
    uc.mem_write(TABLE_MEM + 0x9D4 + effective_idx * 10, struct.pack("<H", flag_val))

    # Write entity record at ENTITY_TABLE + effective_idx * 648
    elem_addr = ENTITY_TABLE + effective_idx * 648
    uc.mem_write(elem_addr, struct.pack("<I", elem_flags))
    uc.mem_write(elem_addr + 0xC8, struct.pack("<i", timer_val))

    # STUB_00282B94: returns ret_node in r0
    # ldr r0, [pc]; bx lr; .word ret_node
    stub_bytes = struct.pack("<III", 0xe59f0000, 0xe12fff1e, ret_node)
    uc.mem_write(STUB_00282B94, stub_bytes)

    sp = STACK_BASE + 0x8000
    lr = 0x00100000

    SENTINEL_R4 = 0x44444444
    SENTINEL_R5 = 0x55555555
    SENTINEL_R6 = 0x66666666
    SENTINEL_R7 = 0x77777777
    SENTINEL_R8 = 0x88888888

    uc.reg_write(UC_ARM_REG_R0, OBJ_PTR)
    uc.reg_write(UC_ARM_REG_R1, TABLE_MEM)
    uc.reg_write(UC_ARM_REG_R2, default_idx)
    uc.reg_write(UC_ARM_REG_R4, SENTINEL_R4)
    uc.reg_write(UC_ARM_REG_R5, SENTINEL_R5)
    uc.reg_write(UC_ARM_REG_R6, SENTINEL_R6)
    uc.reg_write(UC_ARM_REG_R7, SENTINEL_R7)
    uc.reg_write(UC_ARM_REG_R8, SENTINEL_R8)
    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, lr)
    uc.reg_write(UC_ARM_REG_PC, entry_addr)

    uc.emu_start(entry_addr, lr, timeout=0, count=1000)

    regs = {
        "r0": uc.reg_read(UC_ARM_REG_R0),
        "r4": uc.reg_read(UC_ARM_REG_R4),
        "r5": uc.reg_read(UC_ARM_REG_R5),
        "r6": uc.reg_read(UC_ARM_REG_R6),
        "r7": uc.reg_read(UC_ARM_REG_R7),
        "r8": uc.reg_read(UC_ARM_REG_R8),
    }

    assert regs["r4"] == SENTINEL_R4, f"r4 clobbered: {hex(regs['r4'])}"
    assert regs["r5"] == SENTINEL_R5, f"r5 clobbered: {hex(regs['r5'])}"
    assert regs["r6"] == SENTINEL_R6, f"r6 clobbered: {hex(regs['r6'])}"
    assert regs["r7"] == SENTINEL_R7, f"r7 clobbered: {hex(regs['r7'])}"
    assert regs["r8"] == SENTINEL_R8, f"r8 clobbered: {hex(regs['r8'])}"

    return regs


def main():
    parser = argparse.ArgumentParser(description="Differential test for ui_func_00229aa8")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    out_dir = ROOT / "build"
    out_dir.mkdir(exist_ok=True)

    orig_bytes = load_original_bytes()
    compiled_body, relocs = compile_body(out_dir)
    staged_compiled = stage_body(compiled_body, relocs, ORIG_ADDR)

    test_cases = [
        # Branch 1: flag != 0 -> returns 0
        {"name": "flag_nonzero_no_node", "node": False, "n_idx": 0, "def_idx": 0, "flag": 1, "elem_f": 1, "timer": 0},
        {"name": "flag_nonzero_with_node", "node": True, "n_idx": 2, "def_idx": 0, "flag": 5, "elem_f": 1, "timer": 0},
        # Branch 2: flag == 0, elem_flags bit 0 is 0 -> returns 0
        {"name": "elem_bit0_clear", "node": False, "n_idx": 0, "def_idx": 1, "flag": 0, "elem_f": 0, "timer": 0},
        {"name": "elem_bit0_clear_other_bits", "node": True, "n_idx": 3, "def_idx": 0, "flag": 0, "elem_f": 0x100, "timer": -5},
        # Branch 3: flag == 0, elem_flags bit 22 is 1 -> returns 0
        {"name": "elem_bit22_set", "node": False, "n_idx": 0, "def_idx": 2, "flag": 0, "elem_f": 0x400001, "timer": 0},
        {"name": "elem_bit22_set_neg_timer", "node": True, "n_idx": 4, "def_idx": 0, "flag": 0, "elem_f": 0x400001, "timer": -10},
        # Branch 4: flag == 0, valid elem_flags, timer > 0 -> returns 0
        {"name": "timer_positive_1", "node": False, "n_idx": 0, "def_idx": 0, "flag": 0, "elem_f": 1, "timer": 1},
        {"name": "timer_positive_100", "node": True, "n_idx": 5, "def_idx": 0, "flag": 0, "elem_f": 0x101, "timer": 100},
        # Branch 5: flag == 0, valid elem_flags, timer <= 0 -> returns 1
        {"name": "timer_zero_no_node", "node": False, "n_idx": 0, "def_idx": 1, "flag": 0, "elem_f": 1, "timer": 0},
        {"name": "timer_zero_with_node", "node": True, "n_idx": 6, "def_idx": 0, "flag": 0, "elem_f": 1, "timer": 0},
        {"name": "timer_neg_1", "node": False, "n_idx": 0, "def_idx": 2, "flag": 0, "elem_f": 1, "timer": -1},
        {"name": "timer_neg_large", "node": True, "n_idx": 7, "def_idx": 0, "flag": 0, "elem_f": 0x2001, "timer": -9999},
    ]

    passed = 0
    total = len(test_cases)
    results = []

    for case in test_cases:
        orig_res = run_single(
            orig_bytes, ORIG_ADDR, case["node"], case["n_idx"], case["def_idx"],
            case["flag"], case["elem_f"], case["timer"]
        )
        comp_res = run_single(
            staged_compiled, ORIG_ADDR, case["node"], case["n_idx"], case["def_idx"],
            case["flag"], case["elem_f"], case["timer"]
        )

        match = (orig_res["r0"] == comp_res["r0"])
        if not match:
            print(f"FAILED case {case['name']}: orig={orig_res['r0']}, comp={comp_res['r0']}")

        assert match, f"Case {case['name']} failed"
        passed += 1
        results.append({
            "case": case["name"],
            "expected_r0": orig_res["r0"],
            "got_r0": comp_res["r0"],
            "status": "PASS"
        })

    summary = {
        "function": "ui_func_00229aa8",
        "address": f"0x{ORIG_ADDR:08X}",
        "total_cases": total,
        "passed_cases": passed,
        "status": "PASS" if passed == total else "FAIL",
    }

    if args.json:
        print(json.dumps({"summary": summary, "results": results}, indent=2))
    else:
        print(f"Differential test passed: {passed}/{total} cases matched original binary exactly!")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
