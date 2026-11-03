#!/usr/bin/env python3
"""Differential test for engine_func_002c3734 (0x002C3734).

Validates that reconstructed C++ matches original ARM binary across all modes:
- mode == 0: dispatches with sub_r0 = base + 0x88, r3_idx = 0
- mode == 1: dispatches with sub_r0 = base + 0xC4, r3_idx = 0
- mode == 2, flag == 1: returns immediately, no dispatch
- mode == 2, flag != 1: dispatches with sub_r0 = base + 0x100, r3_idx = 1
- checks all passed arguments: r0, r1, r2, r3, s0, s1, s2, s3, s4, stack[0]
- verifies register preservation.
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
    UC_ARM_REG_S0,
    UC_ARM_REG_S1,
    UC_ARM_REG_S2,
    UC_ARM_REG_S3,
    UC_ARM_REG_S4,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
ORIG_ADDR = 0x002C3734
ORIG_SIZE = 128

STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

# Base memory at 0x004E39E0 covers up to 0x004E4000
# Need to map memory region around 0x004E0000
DATA_REGION_BASE = 0x00480000
DATA_REGION_SIZE = 0x00080000  # covers up to 0x00500000, including 0x004E39E0

STUB_BATTLE = 0x00119670
CAPTURE_ADDR = 0x10000000

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

SYMBOL_MAP = {
    "battle_func_00119670": STUB_BATTLE,
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
    if "engine_func_002c3734" not in functions:
        raise RuntimeError("engine_func_002c3734 not in object")
    body, relocs = functions["engine_func_002c3734"]
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


def run_single(code_bytes: bytes, entry_addr: int, mode: int, param: int, flag_84: int):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(DATA_REGION_BASE, DATA_REGION_SIZE)
    uc.mem_map(CAPTURE_ADDR, 0x10000)

    # Clear capture memory
    uc.mem_write(CAPTURE_ADDR, b"\x00" * 64)

    # Write code under test
    uc.mem_write(entry_addr, code_bytes)

    # Set up base memory data at 0x004E39E0
    BASE = 0x004E39E0
    # Flag at BASE + 0x84
    uc.mem_write(BASE + 0x84, struct.pack("<I", flag_84))

    # r3_idx == 0:
    # BASE + 0x174: vec3 = [10.0, 20.0, 30.0]
    # BASE + 0x180: s3 = 40.0
    # BASE + 0x1A4: s4 = 50.0
    # BASE + 0x1B0: r2_val = 0x11112222
    uc.mem_write(BASE + 0x174, struct.pack("<ffff", 10.0, 20.0, 30.0, 40.0))
    uc.mem_write(BASE + 0x1A4, struct.pack("<f", 50.0))
    uc.mem_write(BASE + 0x1B0, struct.pack("<I", 0x11112222))

    # r3_idx == 1:
    # BASE + 16 + 0x174 = BASE + 0x184: vec3 = [11.0, 21.0, 31.0]
    # BASE + 16 + 0x180 = BASE + 0x190: s3 = 41.0
    # BASE + 4 + 0x1A4 = BASE + 0x1A8: s4 = 51.0
    # BASE + 4 + 0x1B0 = BASE + 0x1B4: r2_val = 0x33334444
    uc.mem_write(BASE + 0x184, struct.pack("<ffff", 11.0, 21.0, 31.0, 41.0))
    uc.mem_write(BASE + 0x1A8, struct.pack("<f", 51.0))
    uc.mem_write(BASE + 0x1B4, struct.pack("<I", 0x33334444))

    # battle_func_00119670 stub:
    # Records call count (1) at CAPTURE_ADDR
    # Records r0, r1, r2, r3 at CAPTURE_ADDR + 4, 8, 12, 16
    # Records stack arg [sp] at CAPTURE_ADDR + 20
    # Records s0, s1, s2, s3, s4 at CAPTURE_ADDR + 24..40
    # Code in ARM:
    # push {r4, r5}
    # ldr r4, =CAPTURE_ADDR
    # mov r5, #1
    # str r5, [r4]
    # str r0, [r4, #4]
    # str r1, [r4, #8]
    # str r2, [r4, #12]
    # str r3, [r4, #16]
    # ldr r5, [sp, #8]  (because we pushed {r4, r5})
    # str r5, [r4, #20]
    # vstr s0, [r4, #24]
    # vstr s1, [r4, #28]
    # vstr s2, [r4, #32]
    # vstr s3, [r4, #36]
    # vstr s4, [r4, #40]
    # pop {r4, r5}
    # bx lr
    stub_asm = [
        0xe92d0030,  # push {r4, r5}
        0xe59f4038,  # ldr r4, [pc, #56] -> CAPTURE_ADDR
        0xe3a05001,  # mov r5, #1
        0xe5845000,  # str r5, [r4]
        0xe5840004,  # str r0, [r4, #4]
        0xe5841008,  # str r1, [r4, #8]
        0xe584200c,  # str r2, [r4, #12]
        0xe5843010,  # str r3, [r4, #16]
        0xe59d5008,  # ldr r5, [sp, #8]
        0xe5845014,  # str r5, [r4, #20]
        0xedc40a06,  # vstr s0, [r4, #24]
        0xedc40a07,  # vstr s1, [r4, #28]
        0xedc41a08,  # vstr s2, [r4, #32]
        0xedc41a09,  # vstr s3, [r4, #36]
        0xedc42a0a,  # vstr s4, [r4, #40]
        0xe8bd0030,  # pop {r4, r5}
        0xe12fff1e,  # bx lr
        CAPTURE_ADDR,
    ]
    stub_bytes = b"".join(struct.pack("<I", x) for x in stub_asm)
    uc.mem_write(STUB_BATTLE, stub_bytes)

    sp = STACK_BASE + 0x8000
    lr = 0x00100000

    SENTINEL_R4 = 0x44444444
    SENTINEL_R5 = 0x55555555
    SENTINEL_R6 = 0x66666666
    SENTINEL_R7 = 0x77777777
    SENTINEL_R8 = 0x88888888

    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_R0, mode)
    uc.reg_write(UC_ARM_REG_R1, param)
    uc.reg_write(UC_ARM_REG_R4, SENTINEL_R4)
    uc.reg_write(UC_ARM_REG_R5, SENTINEL_R5)
    uc.reg_write(UC_ARM_REG_R6, SENTINEL_R6)
    uc.reg_write(UC_ARM_REG_R7, SENTINEL_R7)
    uc.reg_write(UC_ARM_REG_R8, SENTINEL_R8)
    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, lr)
    uc.reg_write(UC_ARM_REG_PC, entry_addr)

    uc.emu_start(entry_addr, lr, timeout=0, count=1000)

    # Read captured state
    called = struct.unpack("<I", uc.mem_read(CAPTURE_ADDR, 4))[0]
    if called == 1:
        c_r0, c_r1, c_r2, c_r3, c_stk = struct.unpack("<IIIII", uc.mem_read(CAPTURE_ADDR + 4, 20))
        c_s0, c_s1, c_s2, c_s3, c_s4 = struct.unpack("<fffff", uc.mem_read(CAPTURE_ADDR + 24, 20))
    else:
        c_r0 = c_r1 = c_r2 = c_r3 = c_stk = 0
        c_s0 = c_s1 = c_s2 = c_s3 = c_s4 = 0.0

    regs = {
        "called": called,
        "r0": c_r0,
        "r1": c_r1,
        "r2": c_r2,
        "r3": c_r3,
        "stack_arg": c_stk,
        "s0": c_s0,
        "s1": c_s1,
        "s2": c_s2,
        "s3": c_s3,
        "s4": c_s4,
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
    parser = argparse.ArgumentParser(description="Differential test for engine_func_002c3734")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    out_dir = ROOT / "build"
    out_dir.mkdir(exist_ok=True)

    orig_bytes = load_original_bytes()
    compiled_body, relocs = compile_body(out_dir)
    staged_compiled = stage_body(compiled_body, relocs, ORIG_ADDR)

    test_cases = [
        # Mode 0
        {"name": "mode_0_param_0", "mode": 0, "param": 0, "flag": 0},
        {"name": "mode_0_param_123", "mode": 0, "param": 123, "flag": 1},
        {"name": "mode_0_param_0x9999", "mode": 0, "param": 0x9999, "flag": 2},
        {"name": "mode_0_param_max", "mode": 0, "param": 0xFFFFFFFF, "flag": 0},
        # Mode 1
        {"name": "mode_1_param_0", "mode": 1, "param": 0, "flag": 0},
        {"name": "mode_1_param_456", "mode": 1, "param": 456, "flag": 1},
        {"name": "mode_1_param_0xABCD", "mode": 1, "param": 0xABCD, "flag": 5},
        {"name": "mode_1_param_max", "mode": 1, "param": 0xFFFFFFFF, "flag": 0},
        # Mode 2 with flag == 1 (early exit, no dispatch)
        {"name": "mode_2_flag_1_param_0", "mode": 2, "param": 0, "flag": 1},
        {"name": "mode_2_flag_1_param_99", "mode": 2, "param": 99, "flag": 1},
        {"name": "mode_2_flag_1_param_0x7FFFFFFF", "mode": 2, "param": 0x7FFFFFFF, "flag": 1},
        # Mode 2 with flag != 1 (dispatches with idx 1)
        {"name": "mode_2_flag_0_param_0", "mode": 2, "param": 0, "flag": 0},
        {"name": "mode_2_flag_0_param_777", "mode": 2, "param": 777, "flag": 0},
        {"name": "mode_2_flag_2_param_888", "mode": 2, "param": 888, "flag": 2},
        {"name": "mode_2_flag_3_param_0x12345678", "mode": 2, "param": 0x12345678, "flag": 3},
        {"name": "mode_2_flag_100_param_999", "mode": 2, "param": 999, "flag": 100},
        {"name": "mode_2_flag_neg_param_42", "mode": 2, "param": 42, "flag": 0xFFFFFFFF},
    ]

    passed = 0
    total = len(test_cases)
    results = []

    for case in test_cases:
        orig_res = run_single(
            orig_bytes, ORIG_ADDR, case["mode"], case["param"], case["flag"]
        )
        comp_res = run_single(
            staged_compiled, ORIG_ADDR, case["mode"], case["param"], case["flag"]
        )

        match = True
        for k in ["called", "r0", "r1", "r2", "r3", "stack_arg"]:
            if orig_res[k] != comp_res[k]:
                match = False
                print(f"FAILED case {case['name']} on {k}: orig={orig_res[k]}, comp={comp_res[k]}")
        for k in ["s0", "s1", "s2", "s3", "s4"]:
            if abs(orig_res[k] - comp_res[k]) > 1e-4:
                match = False
                print(f"FAILED case {case['name']} on {k}: orig={orig_res[k]}, comp={comp_res[k]}")

        assert match, f"Case {case['name']} failed"
        passed += 1
        results.append({
            "case": case["name"],
            "status": "PASS"
        })

    summary = {
        "function": "engine_func_002c3734",
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
