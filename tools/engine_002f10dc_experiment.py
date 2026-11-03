#!/usr/bin/env python3
"""Differential test for engine_func_002f10dc (0x002F10DC).

Validates that reconstructed C++ matches original ARM binary:
- Calls ui_func_00293c98() to get ctx.
- Calls engine_func_00296f60(0) -> p0, engine_func_00296f60(1) -> p1.
- Calls engine_func_00289640():
  - If non-zero: reads mgr from [0x004398D4], returns (mgr[0x80] == 4 ? 1 : 0).
  - If zero:
    - Calls script_vm_func_003c8148(mgr, ctx).
    - Sets ctx[0x13c] = p0, ctx[0x140] = p1.
    - Calls script_vm_func_003c7eac(mgr).
    - Calls engine_func_0027e9d0(mgr).
    - Returns 0.
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
ORIG_ADDR = 0x002F10DC
ORIG_SIZE = 132

STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

STUB_GET_CTX = 0x00293C98
STUB_GET_P = 0x00296F60
STUB_CHECK = 0x00289640
STUB_F1 = 0x003C8148
STUB_F2 = 0x003C7EAC
STUB_F3 = 0x0027E9D0

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

SYMBOL_MAP = {
    "ui_func_00293c98": STUB_GET_CTX,
    "engine_func_00296f60": STUB_GET_P,
    "engine_func_00289640": STUB_CHECK,
    "script_vm_func_003c8148": STUB_F1,
    "script_vm_func_003c7eac": STUB_F2,
    "engine_func_0027e9d0": STUB_F3,
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
    if "engine_func_002f10dc" not in functions:
        raise RuntimeError("engine_func_002f10dc not in object")
    body, relocs = functions["engine_func_002f10dc"]
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
    # ui_func_00293c98: returns ctx addr stored at 0x20000000
    stub_ctx = (
        b"\x04\x00\x9f\xe5"  # ldr r0, [pc, #4]
        b"\x00\x00\x90\xe5"  # ldr r0, [r0]
        b"\x1e\xff\x2f\xe1"  # bx lr
        + struct.pack("<I", 0x20000000)
    )

    # engine_func_00296f60: if r0 == 0 returns *(0x20000004), else *(0x20000008)
    stub_p = (
        b"\x0c\x10\x9f\xe5"  # ldr r1, [pc, #12] -> 0x20000004
        b"\x00\x10\x81\xe0"  # add r1, r1, r0, lsl #2
        b"\x00\x00\x91\xe5"  # ldr r0, [r1]
        b"\x1e\xff\x2f\xe1"  # bx lr
        b"\x00\x00\x00\x00"  # pad
        + struct.pack("<I", 0x20000004)
    )

    # engine_func_00289640: returns *(0x2000000c)
    stub_check = (
        b"\x04\x00\x9f\xe5"  # ldr r0, [pc, #4]
        b"\x00\x00\x90\xe5"  # ldr r0, [r0]
        b"\x1e\xff\x2f\xe1"  # bx lr
        + struct.pack("<I", 0x2000000C)
    )

    # script_vm_func_003c8148: logs into 0x20000100 (tag 1, mgr, ctx)
    # script_vm_func_003c7eac: logs into 0x20000110 (tag 2, mgr)
    # engine_func_0027e9d0: logs into 0x20000120 (tag 3, mgr)
    stub_f1 = (
        b"\x08\x20\x9f\xe5"  # ldr r2, =0x20000100
        b"\x03\x00\x82\xe8"  # stm r2, {r0, r1}
        b"\x1e\xff\x2f\xe1"  # bx lr
        b"\x00\x00\x00\x00"  # pad
        + struct.pack("<I", 0x20000100)
    )
    stub_f2 = (
        b"\x04\x10\x9f\xe5"  # ldr r1, =0x20000110
        b"\x00\x00\x81\xe5"  # str r0, [r1]
        b"\x1e\xff\x2f\xe1"  # bx lr
        + struct.pack("<I", 0x20000110)
    )
    stub_f3 = (
        b"\x04\x10\x9f\xe5"  # ldr r1, =0x20000120
        b"\x00\x00\x81\xe5"  # str r0, [r1]
        b"\x1e\xff\x2f\xe1"  # bx lr
        + struct.pack("<I", 0x20000120)
    )

    uc.mem_write(STUB_GET_CTX, stub_ctx)
    uc.mem_write(STUB_GET_P, stub_p)
    uc.mem_write(STUB_CHECK, stub_check)
    uc.mem_write(STUB_F1, stub_f1)
    uc.mem_write(STUB_F2, stub_f2)
    uc.mem_write(STUB_F3, stub_f3)

    return uc


def run_case(code_bytes: bytes, target_addr: int, check_val: int, mgr_val: int, p0: int, p1: int):
    uc = build_emulator(code_bytes, target_addr)

    DATA_BASE = 0x20000000
    DATA_SIZE = 0x20000
    uc.mem_map(DATA_BASE, DATA_SIZE)

    CTX_ADDR = 0x20001000
    MGR_ADDR = 0x20002000

    # 0x004398D4 page:
    GLOBAL_PAGE = 0x00439000
    GLOBAL_ADDR = 0x004398D4
    try:
        uc.mem_map(GLOBAL_PAGE, 0x1000)
    except Exception:
        pass
    uc.mem_write(GLOBAL_ADDR, struct.pack("<I", MGR_ADDR))

    # Control addresses:
    uc.mem_write(DATA_BASE + 0, struct.pack("<I", CTX_ADDR))
    uc.mem_write(DATA_BASE + 4, struct.pack("<I", p0))
    uc.mem_write(DATA_BASE + 8, struct.pack("<I", p1))
    uc.mem_write(DATA_BASE + 12, struct.pack("<I", check_val))

    # Clear logs and ctx slots:
    uc.mem_write(DATA_BASE + 0x100, b"\x00" * 64)
    uc.mem_write(CTX_ADDR + 0x13C, struct.pack("<II", 0, 0))
    uc.mem_write(MGR_ADDR + 0x80, struct.pack("<I", mgr_val))

    sp = STACK_BASE + STACK_SIZE - 0x100
    lr = target_addr + len(code_bytes)

    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, lr)
    uc.reg_write(UC_ARM_REG_R4, 0x11111111)
    uc.reg_write(UC_ARM_REG_R5, 0x22222222)
    uc.reg_write(UC_ARM_REG_R6, 0x33333333)
    uc.reg_write(UC_ARM_REG_R7, 0x44444444)
    uc.reg_write(UC_ARM_REG_R8, 0x55555555)

    uc.emu_start(target_addr, lr, timeout=2000000)

    ret = uc.reg_read(UC_ARM_REG_R0)
    ctx_p0, ctx_p1 = struct.unpack("<II", uc.mem_read(CTX_ADDR + 0x13C, 8))
    f1_log = struct.unpack("<II", uc.mem_read(DATA_BASE + 0x100, 8))
    f2_log = struct.unpack("<I", uc.mem_read(DATA_BASE + 0x110, 4))[0]
    f3_log = struct.unpack("<I", uc.mem_read(DATA_BASE + 0x120, 4))[0]

    r4 = uc.reg_read(UC_ARM_REG_R4)
    r5 = uc.reg_read(UC_ARM_REG_R5)
    r6 = uc.reg_read(UC_ARM_REG_R6)
    r7 = uc.reg_read(UC_ARM_REG_R7)
    r8 = uc.reg_read(UC_ARM_REG_R8)

    return {
        "ret": ret,
        "ctx_p0": ctx_p0,
        "ctx_p1": ctx_p1,
        "f1_log": f1_log,
        "f2_log": f2_log,
        "f3_log": f3_log,
        "r4": r4,
        "r5": r5,
        "r6": r6,
        "r7": r7,
        "r8": r8,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    orig_bytes = load_original_bytes()
    out_dir = ROOT / "build"
    compiled_bytes, relocs = compile_body(out_dir)
    staged_compiled = stage_body(compiled_bytes, relocs, ORIG_ADDR)

    cases = [
        # Check non-zero, mgr[0x80] == 4 -> ret = 1
        {"name": "check_true_mgr_4", "check_val": 1, "mgr_val": 4, "p0": 10, "p1": 20},
        # Check non-zero, mgr[0x80] != 4 -> ret = 0
        {"name": "check_true_mgr_3", "check_val": 1, "mgr_val": 3, "p0": 10, "p1": 20},
        {"name": "check_true_mgr_0", "check_val": 1, "mgr_val": 0, "p0": 10, "p1": 20},
        # Check zero -> initializes slots and calls 3 helpers, returns 0
        {"name": "check_false_init", "check_val": 0, "mgr_val": 4, "p0": 100, "p1": 200},
        {"name": "check_false_p_zero", "check_val": 0, "mgr_val": 99, "p0": 0, "p1": 0},
    ]

    all_passed = True
    results = []

    for c in cases:
        orig_res = run_case(orig_bytes, ORIG_ADDR, c["check_val"], c["mgr_val"], c["p0"], c["p1"])
        comp_res = run_case(staged_compiled, ORIG_ADDR, c["check_val"], c["mgr_val"], c["p0"], c["p1"])

        passed = orig_res == comp_res
        if not passed:
            all_passed = False

        results.append({
            "name": c["name"],
            "orig": orig_res,
            "comp": comp_res,
            "passed": passed,
        })

    if args.json:
        print(json.dumps({"passed": all_passed, "cases": results}, indent=2))
    else:
        for r in results:
            status = "PASS" if r["passed"] else "FAIL"
            print(f"[{status}] {r['name']}: orig={r['orig']} comp={r['comp']}")
        print(f"Overall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
