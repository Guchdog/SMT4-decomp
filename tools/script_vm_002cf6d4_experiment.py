#!/usr/bin/env python3
"""Differential test for script_vm_func_002cf6d4 (0x002CF6D4).

Validates that reconstructed C++ matches original ARM binary:
- Sets ctx[0x5C4] = 1
- Calls script_vm_func_002509d8()
- Queries slot offsets via camp_func_0029f260 and camp_func_0029f248
- Dispatches event script_vm_func_002900b0(id, 1)
- Calls camp_func_002bdac0(ctx + 0x34, 0, 0)
- Transitions state: ctx[8] = ctx[4], ctx[4] = 1, ctx[0x10] = 0
- Verifies preservation of non-volatile registers (r4, r5, r6, r7, r8).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys

import unicorn
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
ORIG_ADDR = 0x002CF6D4
ORIG_SIZE = 128

STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

DATA_BASE = 0x00480000
DATA_SIZE = 0x00100000

STUB_002509D8 = 0x002509D8
STUB_0029F260 = 0x0029F260
STUB_0029F248 = 0x0029F248
STUB_002900B0 = 0x002900B0
STUB_002BDAC0 = 0x002BDAC0

CAPTURE_ADDR = 0x10000000

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

SYMBOL_MAP = {
    "script_vm_func_002509d8": STUB_002509D8,
    "camp_func_0029f260": STUB_0029F260,
    "camp_func_0029f248": STUB_0029F248,
    "script_vm_func_002900b0": STUB_002900B0,
    "camp_func_002bdac0": STUB_002BDAC0,
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
    if "script_vm_func_002cf6d4" not in functions:
        raise RuntimeError("script_vm_func_002cf6d4 not in object")
    body, relocs = functions["script_vm_func_002cf6d4"]
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


def run_single(code_bytes: bytes, entry_addr: int, init_state: int, q1_val: int, q2_val: int, id_val: int):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(CAPTURE_ADDR, 0x10000)

    # Clear capture
    uc.mem_write(CAPTURE_ADDR, b"\x00" * 128)

    # Write code under test
    uc.mem_write(entry_addr, code_bytes)

    # Set up global pointer at 0x0043DD50
    CTX_PTR = 0x0043DD50
    CTX_MEM = 0x00490000
    uc.mem_write(CTX_PTR, struct.pack("<I", CTX_MEM))

    # Initialize context memory
    uc.mem_write(CTX_MEM, b"\x00" * 0x1000)
    # State fields: offset 4 = init_state, offset 8 = 0xAAAA, offset 0x10 = 0xBBBB
    uc.mem_write(CTX_MEM + 4, struct.pack("<I", init_state))
    uc.mem_write(CTX_MEM + 8, struct.pack("<I", 0xAAAA))
    uc.mem_write(CTX_MEM + 0x10, struct.pack("<I", 0xBBBB))

    # Store id at offset 0x6C4 + (q1 + q2) * 2
    sum_idx = q1_val + q2_val
    uc.mem_write(CTX_MEM + 0x6C4 + sum_idx * 2, struct.pack("<H", id_val))

    # Stubs:
    # STUB_002509D8: increment call count at CAPTURE_ADDR
    # ldr r0, [pc, #12]; ldr r1, [r0]; add r1, r1, #1; str r1, [r0]; bx lr; .word CAPTURE_ADDR
    stub_2509d8 = struct.pack(
        "<IIIIII",
        0xe59f000c, 0xe5901000, 0xe2811001, 0xe5801000, 0xe12fff1e,
        CAPTURE_ADDR
    )
    uc.mem_write(STUB_002509D8, stub_2509d8)

    # STUB_0029F260: returns q1_val
    # mov r0, #q1_val; bx lr
    uc.mem_write(STUB_0029F260, struct.pack("<II", 0xe3a00000 | (q1_val & 0xFF), 0xe12fff1e))

    # STUB_0029F248: returns q2_val
    # mov r0, #q2_val; bx lr
    uc.mem_write(STUB_0029F248, struct.pack("<II", 0xe3a00000 | (q2_val & 0xFF), 0xe12fff1e))

    # STUB_002900B0: record r0 (id) and r1 (mode) at CAPTURE_ADDR + 16, 20
    # ldr r2, [pc, #8]; str r0, [r2, #16]; str r1, [r2, #20]; bx lr; .word CAPTURE_ADDR
    stub_2900b0 = struct.pack(
        "<IIIII",
        0xe59f2008, 0xe5820010, 0xe5821014, 0xe12fff1e,
        CAPTURE_ADDR
    )
    uc.mem_write(STUB_002900B0, stub_2900b0)

    # STUB_002BDAC0: record r0, r1, r2 at CAPTURE_ADDR + 24, 28, 32
    # 0x00: ldr r3, [pc, #12] -> offset 0x14 - 0x08 = 0x0C
    # 0x04: str r0, [r3, #24]
    # 0x08: str r1, [r3, #28]
    # 0x0C: str r2, [r3, #32]
    # 0x10: bx lr
    # 0x14: CAPTURE_ADDR
    stub_2bdac0 = struct.pack(
        "<IIIIII",
        0xe59f300c, 0xe5830018, 0xe583101c, 0xe5832020, 0xe12fff1e,
        CAPTURE_ADDR
    )
    uc.mem_write(STUB_002BDAC0, stub_2bdac0)

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

    # Read modified context fields
    byte_5c4 = struct.unpack("<B", uc.mem_read(CTX_MEM + 0x5C4, 1))[0]
    st_val, prev_st, sub_st = struct.unpack("<III", uc.mem_read(CTX_MEM + 4, 12)[:8] + uc.mem_read(CTX_MEM + 0x10, 4))

    # Read captured callee calls
    called_count = struct.unpack("<I", uc.mem_read(CAPTURE_ADDR, 4))[0]
    c_2900b0_id, c_2900b0_mode = struct.unpack("<II", uc.mem_read(CAPTURE_ADDR + 16, 8))
    c_bdac0_r0, c_bdac0_r1, c_bdac0_r2 = struct.unpack("<III", uc.mem_read(CAPTURE_ADDR + 24, 12))

    regs = {
        "byte_5c4": byte_5c4,
        "state": st_val,
        "prev_state": prev_st,
        "sub_state": sub_st,
        "called_2509d8": called_count,
        "id_dispatched": c_2900b0_id,
        "mode_dispatched": c_2900b0_mode,
        "bdac0_r0": c_bdac0_r0 - CTX_MEM,  # relative offset to ctx
        "bdac0_r1": c_bdac0_r1,
        "bdac0_r2": c_bdac0_r2,
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
    parser = argparse.ArgumentParser(description="Differential test for script_vm_func_002cf6d4")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    out_dir = ROOT / "build"
    out_dir.mkdir(exist_ok=True)

    orig_bytes = load_original_bytes()
    compiled_body, relocs = compile_body(out_dir)
    staged_compiled = stage_body(compiled_body, relocs, ORIG_ADDR)

    test_cases = [
        {"name": "state_0_sum_0", "init_state": 0, "q1": 0, "q2": 0, "id": 100},
        {"name": "state_1_sum_0", "init_state": 1, "q1": 0, "q2": 0, "id": 101},
        {"name": "state_2_sum_1", "init_state": 2, "q1": 1, "q2": 0, "id": 102},
        {"name": "state_3_sum_2", "init_state": 3, "q1": 0, "q2": 2, "id": 103},
        {"name": "state_5_sum_3", "init_state": 5, "q1": 1, "q2": 2, "id": 205},
        {"name": "state_9_sum_5", "init_state": 9, "q1": 3, "q2": 2, "id": 999},
        {"name": "state_15_sum_7", "init_state": 15, "q1": 4, "q2": 3, "id": 0x1234},
        {"name": "state_42_sum_10", "init_state": 42, "q1": 6, "q2": 4, "id": 0x5678},
        {"name": "state_100_sum_8", "init_state": 100, "q1": 8, "q2": 0, "id": 0xABCD},
        {"name": "state_max_sum_12", "init_state": 0xFFFFFFFF, "q1": 7, "q2": 5, "id": 0xFFFF},
    ]

    passed = 0
    total = len(test_cases)
    results = []

    for case in test_cases:
        orig_res = run_single(
            orig_bytes, ORIG_ADDR, case["init_state"], case["q1"], case["q2"], case["id"]
        )
        comp_res = run_single(
            staged_compiled, ORIG_ADDR, case["init_state"], case["q1"], case["q2"], case["id"]
        )

        match = True
        for k in ["byte_5c4", "state", "prev_state", "sub_state", "called_2509d8",
                  "id_dispatched", "mode_dispatched", "bdac0_r0", "bdac0_r1", "bdac0_r2"]:
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
        "function": "script_vm_func_002cf6d4",
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
