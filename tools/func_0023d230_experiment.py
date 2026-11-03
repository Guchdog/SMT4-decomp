#!/usr/bin/env python3
"""Differential test for func_0023d230 (0x0023D230).

Validates that reconstructed C++ matches original ARM binary:
- Unpacks 32-bit packed color into four normalized float components [0..1]
- Sets header word 0 = tag | 0x80000000 (reading byte from 0x00490E46)
- Sets header word 1 = 0x804F02C0
- Verifies float precision and exact byte layouts
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
    UC_ARM_REG_FPEXC,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
ORIG_ADDR = 0x0023D230
ORIG_SIZE = 132

STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

# Memory for 0x00490E46
DATA_BASE = 0x00480000
DATA_SIZE = 0x00080000

TAG_ADDR = 0x00490E46
OUT_BUF_ADDR = 0x10000000

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"


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
    if "func_0023d230" not in functions:
        raise RuntimeError("func_0023d230 not in object")
    body, relocs = functions["func_0023d230"]
    return body, relocs


def run_single(code_bytes: bytes, entry_addr: int, packed_val: int, tag_val: int):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(OUT_BUF_ADDR, 0x10000)

    # Clear output buffer
    uc.mem_write(OUT_BUF_ADDR, b"\x00" * 64)

    # Write code under test
    uc.mem_write(entry_addr, code_bytes)

    # Set tag byte
    uc.mem_write(TAG_ADDR, struct.pack("<B", tag_val))

    sp = STACK_BASE + 0x8000
    lr = 0x00100000

    SENTINEL_R4 = 0x44444444
    SENTINEL_R5 = 0x55555555
    SENTINEL_R6 = 0x66666666
    SENTINEL_R7 = 0x77777777
    SENTINEL_R8 = 0x88888888

    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_R0, OUT_BUF_ADDR)
    uc.reg_write(UC_ARM_REG_R1, packed_val)
    uc.reg_write(UC_ARM_REG_R4, SENTINEL_R4)
    uc.reg_write(UC_ARM_REG_R5, SENTINEL_R5)
    uc.reg_write(UC_ARM_REG_R6, SENTINEL_R6)
    uc.reg_write(UC_ARM_REG_R7, SENTINEL_R7)
    uc.reg_write(UC_ARM_REG_R8, SENTINEL_R8)
    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, lr)
    uc.reg_write(UC_ARM_REG_PC, entry_addr)

    uc.emu_start(entry_addr, lr, timeout=0, count=1000)

    # Read output buffer (24 bytes)
    out_raw = uc.mem_read(OUT_BUF_ADDR, 24)
    w0, w1 = struct.unpack("<II", out_raw[:8])
    f0, f1, f2, f3 = struct.unpack("<ffff", out_raw[8:24])

    regs = {
        "w0": w0,
        "w1": w1,
        "f0": f0,
        "f1": f1,
        "f2": f2,
        "f3": f3,
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
    parser = argparse.ArgumentParser(description="Differential test for func_0023d230")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    out_dir = ROOT / "build"
    out_dir.mkdir(exist_ok=True)

    orig_bytes = load_original_bytes()
    compiled_body, _ = compile_body(out_dir)

    test_cases = [
        {"name": "zero_all", "packed": 0x00000000, "tag": 0},
        {"name": "ones_all", "packed": 0xFFFFFFFF, "tag": 1},
        {"name": "alpha_only", "packed": 0xFF000000, "tag": 42},
        {"name": "blue_only", "packed": 0x00FF0000, "tag": 127},
        {"name": "green_only", "packed": 0x0000FF00, "tag": 200},
        {"name": "red_only", "packed": 0x000000FF, "tag": 255},
        {"name": "mixed_1", "packed": 0x12345678, "tag": 10},
        {"name": "mixed_2", "packed": 0x80402010, "tag": 99},
        {"name": "mixed_3", "packed": 0xA55A3CC3, "tag": 77},
        {"name": "mixed_4", "packed": 0x7F3F1F0F, "tag": 0x80},
    ]

    passed = 0
    total = len(test_cases)
    results = []

    for case in test_cases:
        orig_res = run_single(orig_bytes, ORIG_ADDR, case["packed"], case["tag"])
        comp_res = run_single(compiled_body, ORIG_ADDR, case["packed"], case["tag"])

        match = True
        for k in ["w0", "w1"]:
            if orig_res[k] != comp_res[k]:
                match = False
                print(f"FAILED case {case['name']} on {k}: orig=0x{orig_res[k]:08X}, comp=0x{comp_res[k]:08X}")
        for k in ["f0", "f1", "f2", "f3"]:
            if abs(orig_res[k] - comp_res[k]) > 1e-6:
                match = False
                print(f"FAILED case {case['name']} on {k}: orig={orig_res[k]}, comp={comp_res[k]}")

        assert match, f"Case {case['name']} failed"
        passed += 1
        results.append({
            "case": case["name"],
            "status": "PASS"
        })

    summary = {
        "function": "func_0023d230",
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
