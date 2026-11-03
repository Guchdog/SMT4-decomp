#!/usr/bin/env python3
"""Differential test for battle_func_002b89fc (0x002B89FC).

Validates that reconstructed C++ matches original ARM binary:
- Returns 0 if main container is null
- Returns 1 if ui_func_002b2530(*main) != 0
- Returns 1 if main[0x18] == 0
- If main[0x18] != 0:
  - Sets main[0x18] = 1
  - If sub (main[0x1C]) != null, calls script_vm_func_002a72fc and engine_func_002b2520, clears main[0x1C]
  - Calls engine_func_002c4360(main), clears *p_main
  - Returns 0
- Verifies preservation of non-volatile registers (r4, r5, r6, r7, r8).
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
ORIG_ADDR = 0x002B89FC
ORIG_SIZE = 132

STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

STUB_CHECK_HANDLE = 0x002B2530
STUB_STOP_SUB = 0x002A72FC
STUB_FREE_SUB = 0x002B2520
STUB_FREE_MAIN = 0x002C4360

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

SYMBOL_MAP = {
    "ui_func_002b2530": STUB_CHECK_HANDLE,
    "script_vm_func_002a72fc": STUB_STOP_SUB,
    "engine_func_002b2520": STUB_FREE_SUB,
    "engine_func_002c4360": STUB_FREE_MAIN,
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
    if "battle_func_002b89fc" not in functions:
        raise RuntimeError("battle_func_002b89fc not in object")
    body, relocs = functions["battle_func_002b89fc"]
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


def run_single(code_bytes: bytes, entry_addr: int, has_main: bool,
               handle_active: int, flag_18: int, has_sub: bool):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    DATA_PAGE = 0x20000000
    uc.mem_map(DATA_PAGE, 0x100000)

    CAPTURE_ADDR = DATA_PAGE + 0x80000
    uc.mem_write(CAPTURE_ADDR, b"\x00" * 64)

    # Global pointer at 0x0044DB88 + 4 = 0x0044DB8C
    # In CODE_BASE region, 0x0044DB88 is mapped within CODE_BASE (size 0x380000, covers up to 0x00480000)
    P_MAIN = 0x0044DB8C
    MAIN_MEM = DATA_PAGE + 0x1000
    SUB_MEM = DATA_PAGE + 0x2000

    # Write code under test
    uc.mem_write(entry_addr, code_bytes)

    if has_main:
        uc.mem_write(P_MAIN, struct.pack("<I", MAIN_MEM))
        uc.mem_write(MAIN_MEM, b"\x00" * 0x40)
        # Handle at MAIN_MEM + 0: 0x12345678
        uc.mem_write(MAIN_MEM, struct.pack("<I", 0x12345678))
        # Flag at MAIN_MEM + 0x18
        uc.mem_write(MAIN_MEM + 0x18, struct.pack("<B", flag_18))
        if has_sub:
            uc.mem_write(MAIN_MEM + 0x1C, struct.pack("<I", SUB_MEM))
        else:
            uc.mem_write(MAIN_MEM + 0x1C, struct.pack("<I", 0))
    else:
        uc.mem_write(P_MAIN, struct.pack("<I", 0))

    # STUB_CHECK_HANDLE (0x002B2530): returns handle_active in r0
    uc.mem_write(STUB_CHECK_HANDLE, struct.pack("<II", 0xe3a00000 | (handle_active & 0xFF), 0xe12fff1e))

    # STUB_STOP_SUB (0x002A72FC): increments counter at CAPTURE_ADDR + 0
    # ldr r1, =CAPTURE_ADDR; ldr r2, [r1]; add r2, r2, #1; str r2, [r1]; bx lr
    stub_stop = struct.pack(
        "<IIIIII",
        0xe59f100c, 0xe5912000, 0xe2822001, 0xe5812000, 0xe12fff1e,
        CAPTURE_ADDR
    )
    uc.mem_write(STUB_STOP_SUB, stub_stop)

    # STUB_FREE_SUB (0x002B2520): increments counter at CAPTURE_ADDR + 4
    stub_free_sub = struct.pack(
        "<IIIIII",
        0xe59f100c, 0xe5912004, 0xe2822001, 0xe5812004, 0xe12fff1e,
        CAPTURE_ADDR
    )
    uc.mem_write(STUB_FREE_SUB, stub_free_sub)

    # STUB_FREE_MAIN (0x002C4360): increments counter at CAPTURE_ADDR + 8
    stub_free_main = struct.pack(
        "<IIIIII",
        0xe59f100c, 0xe5912008, 0xe2822001, 0xe5812008, 0xe12fff1e,
        CAPTURE_ADDR
    )
    uc.mem_write(STUB_FREE_MAIN, stub_free_main)

    sp = STACK_BASE + 0x8000
    lr = 0x00100000

    SENTINEL_R4 = 0x44444444
    SENTINEL_R5 = 0x55555555
    SENTINEL_R6 = 0x66666666
    SENTINEL_R7 = 0x77777777
    SENTINEL_R8 = 0x88888888

    uc.reg_write(UC_ARM_REG_R4, SENTINEL_R4)
    uc.reg_write(UC_ARM_REG_R5, SENTINEL_R5)
    uc.reg_write(UC_ARM_REG_R6, SENTINEL_R6)
    uc.reg_write(UC_ARM_REG_R7, SENTINEL_R7)
    uc.reg_write(UC_ARM_REG_R8, SENTINEL_R8)
    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, lr)
    uc.reg_write(UC_ARM_REG_PC, entry_addr)

    uc.emu_start(entry_addr, lr, timeout=0, count=1000)

    # Read modified state
    p_main_after = struct.unpack("<I", uc.mem_read(P_MAIN, 4))[0]
    sub_after = struct.unpack("<I", uc.mem_read(MAIN_MEM + 0x1C, 4))[0] if has_main else 0
    flag_after = struct.unpack("<B", uc.mem_read(MAIN_MEM + 0x18, 1))[0] if has_main else 0
    cnt_stop, cnt_free_sub, cnt_free_main = struct.unpack("<III", uc.mem_read(CAPTURE_ADDR, 12))

    regs = {
        "r0": uc.reg_read(UC_ARM_REG_R0),
        "p_main_after": p_main_after,
        "sub_after": sub_after,
        "flag_after": flag_after,
        "cnt_stop": cnt_stop,
        "cnt_free_sub": cnt_free_sub,
        "cnt_free_main": cnt_free_main,
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
    parser = argparse.ArgumentParser(description="Differential test for battle_func_002b89fc")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    out_dir = ROOT / "build"
    out_dir.mkdir(exist_ok=True)

    orig_bytes = load_original_bytes()
    compiled_body, relocs = compile_body(out_dir)
    staged_compiled = stage_body(compiled_body, relocs, ORIG_ADDR)

    test_cases = [
        # Main is null -> returns 0
        {"name": "null_main", "main": False, "h_act": 0, "f18": 0, "sub": False},
        # Handle check active -> returns 1
        {"name": "handle_active", "main": True, "h_act": 1, "f18": 1, "sub": True},
        # Flag 18 == 0 -> returns 1
        {"name": "flag18_zero", "main": True, "h_act": 0, "f18": 0, "sub": True},
        # Successful teardown with sub
        {"name": "teardown_with_sub", "main": True, "h_act": 0, "f18": 1, "sub": True},
        {"name": "teardown_with_sub_f2", "main": True, "h_act": 0, "f18": 2, "sub": True},
        {"name": "teardown_with_sub_f255", "main": True, "h_act": 0, "f18": 255, "sub": True},
        # Successful teardown without sub
        {"name": "teardown_no_sub", "main": True, "h_act": 0, "f18": 1, "sub": False},
        {"name": "teardown_no_sub_f99", "main": True, "h_act": 0, "f18": 99, "sub": False},
    ]

    passed = 0
    total = len(test_cases)
    results = []

    for case in test_cases:
        orig_res = run_single(
            orig_bytes, ORIG_ADDR, case["main"], case["h_act"], case["f18"], case["sub"]
        )
        comp_res = run_single(
            staged_compiled, ORIG_ADDR, case["main"], case["h_act"], case["f18"], case["sub"]
        )

        match = True
        for k in ["r0", "p_main_after", "sub_after", "flag_after", "cnt_stop", "cnt_free_sub", "cnt_free_main"]:
            if orig_res[k] != comp_res[k]:
                match = False
                print(f"FAILED case {case['name']} on {k}: orig={orig_res[k]}, comp={comp_res[k]}")

        assert match, f"Case {case['name']} failed"
        passed += 1
        results.append({
            "case": case["name"],
            "status": "PASS"
        })

    summary = {
        "function": "battle_func_002b89fc",
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
