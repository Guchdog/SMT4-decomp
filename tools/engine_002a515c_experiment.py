#!/usr/bin/env python3
"""Differential test for engine_func_002a515c (0x002A515C).

Validates that reconstructed C++ matches original ARM binary across all
branch combinations:
- ctx == nullptr -> returns 0, target unmodified
- ctx != nullptr, sub == nullptr -> returns 1, target unmodified
- ctx != nullptr, sub != nullptr, func_002ae16c(sub) == 0 -> returns 1, target unmodified
- ctx != nullptr, sub != nullptr, func_002ae16c(sub) != 0, slot_index == 0 ->
  returns func_002ae074(sub->f8, table[0], target), target[2] (y) += ctx->offset
- slot_index != 0 -> returns func_002ae074(sub->f8, table[slot], target), target[2] unmodified
- verifies register preservation (r4, r5, r6, r7, r8).
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
ORIG_ADDR = 0x002A515C
ORIG_SIZE = 128

STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

DATA_BASE = 0x00480000
DATA_SIZE = 0x00100000

STUB_CHECK_ACTIVE = 0x002AE16C
STUB_DISPATCH = 0x002AE074

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

SYMBOL_MAP = {
    "engine_func_002ae16c": STUB_CHECK_ACTIVE,
    "engine_func_002ae074": STUB_DISPATCH,
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
    if "engine_func_002a515c" not in functions:
        raise RuntimeError("engine_func_002a515c not in object")
    body, relocs = functions["engine_func_002a515c"]
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


def run_single(code_bytes: bytes, entry_addr: int, ctx_exists: bool,
               sub_exists: bool, sub_active: int, slot_index: int,
               init_y: float, offset_val: float):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)

    # Write code under test
    uc.mem_write(entry_addr, code_bytes)

    # Stubs:
    # STUB_CHECK_ACTIVE (0x002AE16C): reads r0. Returns sub_active in r0.
    # mov r0, #sub_active; bx lr
    uc.mem_write(STUB_CHECK_ACTIVE, struct.pack("<II", 0xe3a00000 | (sub_active & 0xFF), 0xe12fff1e))

    # STUB_DISPATCH (0x002AE074): reads r0 (field8), r1 (table[slot]), r2 (target).
    # Returns r0 + r1 + 0x1000
    # add r0, r0, r1; add r0, r0, #0x1000; bx lr
    uc.mem_write(STUB_DISPATCH, struct.pack("<III", 0xe0800001, 0xe2800a01, 0xe12fff1e))

    # Set up memory addresses:
    # Global ctx pointer at 0x0043DFC0
    # Global table at 0x0043E048
    PTR_CTX = 0x0043DFC0
    TABLE_ADDR = 0x0043E048
    # Populate table with some entries
    for i in range(8):
        uc.mem_write(TABLE_ADDR + i * 4, struct.pack("<I", 0x10 + i * 4))

    CTX_MEM = 0x00480000
    SUB_MEM = 0x00481000
    TARGET_MEM = 0x00482000

    if ctx_exists:
        uc.mem_write(PTR_CTX, struct.pack("<I", CTX_MEM))
        # Context struct:
        # offset +0x5E4: pointer to sub
        # offset +0x640: float offset_val
        if sub_exists:
            uc.mem_write(CTX_MEM + 0x5E4, struct.pack("<I", SUB_MEM))
            # Sub struct:
            # offset +8: field8 pointer
            uc.mem_write(SUB_MEM + 8, struct.pack("<I", 0x5000))
        else:
            uc.mem_write(CTX_MEM + 0x5E4, struct.pack("<I", 0))

        uc.mem_write(CTX_MEM + 0x640, struct.pack("<f", offset_val))
    else:
        uc.mem_write(PTR_CTX, struct.pack("<I", 0))

    # Target struct:
    # offset +8: float y
    uc.mem_write(TARGET_MEM + 8, struct.pack("<f", init_y))

    sp = STACK_BASE + 0x8000
    lr = 0x00100000  # exit address

    SENTINEL_R4 = 0x44444444
    SENTINEL_R5 = 0x55555555
    SENTINEL_R6 = 0x66666666
    SENTINEL_R7 = 0x77777777
    SENTINEL_R8 = 0x88888888

    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_R0, TARGET_MEM)
    uc.reg_write(UC_ARM_REG_R1, slot_index)
    uc.reg_write(UC_ARM_REG_R4, SENTINEL_R4)
    uc.reg_write(UC_ARM_REG_R5, SENTINEL_R5)
    uc.reg_write(UC_ARM_REG_R6, SENTINEL_R6)
    uc.reg_write(UC_ARM_REG_R7, SENTINEL_R7)
    uc.reg_write(UC_ARM_REG_R8, SENTINEL_R8)
    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, lr)
    uc.reg_write(UC_ARM_REG_PC, entry_addr)

    uc.emu_start(entry_addr, lr, timeout=0, count=1000)

    # Read modified target y
    target_y = struct.unpack("<f", uc.mem_read(TARGET_MEM + 8, 4))[0]

    regs = {
        "r0": uc.reg_read(UC_ARM_REG_R0),
        "target_y": target_y,
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
    parser = argparse.ArgumentParser(description="Differential test for engine_func_002a515c")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    out_dir = ROOT / "build"
    out_dir.mkdir(exist_ok=True)

    orig_bytes = load_original_bytes()
    compiled_body, relocs = compile_body(out_dir)
    staged_compiled = stage_body(compiled_body, relocs, ORIG_ADDR)

    test_cases = [
        # Null context
        {"name": "null_ctx", "ctx": False, "sub": False, "active": 0, "slot": 0, "init_y": 10.0, "offset": 5.0},
        {"name": "null_ctx_slot1", "ctx": False, "sub": False, "active": 0, "slot": 1, "init_y": 20.0, "offset": 5.0},
        # Null sub
        {"name": "null_sub", "ctx": True, "sub": False, "active": 0, "slot": 0, "init_y": 15.0, "offset": 2.5},
        {"name": "null_sub_slot2", "ctx": True, "sub": False, "active": 0, "slot": 2, "init_y": 15.0, "offset": 2.5},
        # Inactive sub
        {"name": "inactive_sub", "ctx": True, "sub": True, "active": 0, "slot": 0, "init_y": 30.0, "offset": 7.0},
        {"name": "inactive_sub_slot3", "ctx": True, "sub": True, "active": 0, "slot": 3, "init_y": 30.0, "offset": 7.0},
        # Active sub, slot 0 (applies offset)
        {"name": "active_slot0_pos", "ctx": True, "sub": True, "active": 1, "slot": 0, "init_y": 100.0, "offset": 25.5},
        {"name": "active_slot0_neg", "ctx": True, "sub": True, "active": 1, "slot": 0, "init_y": 50.0, "offset": -15.25},
        {"name": "active_slot0_zero", "ctx": True, "sub": True, "active": 1, "slot": 0, "init_y": 0.0, "offset": 0.0},
        {"name": "active_slot0_neg_init", "ctx": True, "sub": True, "active": 1, "slot": 0, "init_y": -120.5, "offset": 45.25},
        {"name": "active_slot0_large", "ctx": True, "sub": True, "active": 1, "slot": 0, "init_y": 100000.0, "offset": 50000.0},
        # Active sub, slots 1-7 (does not apply offset)
        {"name": "active_slot1", "ctx": True, "sub": True, "active": 1, "slot": 1, "init_y": 100.0, "offset": 25.5},
        {"name": "active_slot2", "ctx": True, "sub": True, "active": 1, "slot": 2, "init_y": 42.0, "offset": 100.0},
        {"name": "active_slot3", "ctx": True, "sub": True, "active": 1, "slot": 3, "init_y": -5.0, "offset": 10.0},
        {"name": "active_slot4", "ctx": True, "sub": True, "active": 1, "slot": 4, "init_y": 1.234, "offset": 5.678},
        {"name": "active_slot5", "ctx": True, "sub": True, "active": 1, "slot": 5, "init_y": 99.9, "offset": -20.0},
        {"name": "active_slot6", "ctx": True, "sub": True, "active": 1, "slot": 6, "init_y": -999.0, "offset": 12.0},
        {"name": "active_slot7", "ctx": True, "sub": True, "active": 1, "slot": 7, "init_y": 0.0, "offset": -50.0},
    ]

    passed = 0
    total = len(test_cases)
    results = []

    for case in test_cases:
        orig_res = run_single(
            orig_bytes, ORIG_ADDR, case["ctx"], case["sub"],
            case["active"], case["slot"], case["init_y"], case["offset"]
        )
        comp_res = run_single(
            staged_compiled, ORIG_ADDR, case["ctx"], case["sub"],
            case["active"], case["slot"], case["init_y"], case["offset"]
        )

        match_r0 = (orig_res["r0"] == comp_res["r0"])
        match_y = abs(orig_res["target_y"] - comp_res["target_y"]) < 1e-4

        if not (match_r0 and match_y):
            print(f"FAILED case {case['name']}: orig r0={orig_res['r0']}, y={orig_res['target_y']} | comp r0={comp_res['r0']}, y={comp_res['target_y']}")
        assert match_r0 and match_y, f"Case {case['name']} failed"
        passed += 1
        results.append({
            "case": case["name"],
            "expected_r0": orig_res["r0"],
            "got_r0": comp_res["r0"],
            "expected_y": orig_res["target_y"],
            "got_y": comp_res["target_y"],
            "status": "PASS"
        })

    summary = {
        "function": "engine_func_002a515c",
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
