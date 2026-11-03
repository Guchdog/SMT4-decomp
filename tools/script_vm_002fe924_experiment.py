#!/usr/bin/env python3
"""Differential test for script_vm_func_002fe924 (0x002FE924).

Validates that reconstructed C++ matches original ARM binary:
- Calls engine_func_00296f60(0) to get val.
- Checks flag at 0x0049F91C + 0x251.
- State toggle:
  - If val != 0 and flag == 0:
    - Sets flag = 1.
    - Calls script_vm_func_00275e38(), script_vm_func_00289ae8(), script_vm_func_002b8b78(0x90).
  - If val == 0 and flag != 0:
    - Sets flag = 0.
    - Calls ui_func_0025a318(), script_vm_func_00275a18().
- Returns 1.
- Preserves non-volatile registers (r4..r8).
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
ORIG_ADDR = 0x002FE924
ORIG_SIZE = 132

STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

STUB_GET_VAL = 0x00296F60
STUB_UI_25A318 = 0x0025A318
STUB_VM_275A18 = 0x00275A18
STUB_VM_275E38 = 0x00275E38
STUB_VM_289AE8 = 0x00289AE8
STUB_VM_2B8B78 = 0x002B8B78

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

SYMBOL_MAP = {
    "engine_func_00296f60": STUB_GET_VAL,
    "ui_func_0025a318": STUB_UI_25A318,
    "script_vm_func_00275a18": STUB_VM_275A18,
    "script_vm_func_00275e38": STUB_VM_275E38,
    "script_vm_func_00289ae8": STUB_VM_289AE8,
    "script_vm_func_002b8b78": STUB_VM_2B8B78,
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
    if "script_vm_func_002fe924" not in functions:
        raise RuntimeError("script_vm_func_002fe924 not in object")
    body, relocs = functions["script_vm_func_002fe924"]
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
    # engine_func_00296f60: returns val stored at 0x20000000
    stub_val = (
        b"\x04\x00\x9f\xe5"  # ldr r0, [pc, #4]
        b"\x00\x00\x90\xe5"  # ldr r0, [r0]
        b"\x1e\xff\x2f\xe1"  # bx lr
        + struct.pack("<I", 0x20000000)
    )

    # Log helper for stubs: each stub writes a tag to 0x20000100 + idx*4
    # 0x25a318 -> tag 1 at 0x20000100
    # 0x275a18 -> tag 2 at 0x20000104
    # 0x275e38 -> tag 3 at 0x20000108
    # 0x289ae8 -> tag 4 at 0x2000010c
    # 0x2b8b78 -> tag 5 + r0 stored at 0x20000110 and 0x20000114
    def make_log_stub(tag: int, addr: int):
        return (
            b"\x08\x10\x9f\xe5"  # ldr r1, [pc, #8] -> addr
            b"\x08\x20\x9f\xe5"  # ldr r2, [pc, #8] -> tag
            b"\x00\x20\x81\xe5"  # str r2, [r1]
            b"\x1e\xff\x2f\xe1"  # bx lr
            + struct.pack("<II", addr, tag)
        )

    stub_2b8b78 = (
        b"\x10\x10\x9f\xe5"  # ldr r1, [pc, #16] -> addr
        b"\x10\x20\x9f\xe5"  # ldr r2, [pc, #16] -> 5
        b"\x00\x20\x81\xe5"  # str r2, [r1]
        b"\x04\x00\x81\xe5"  # str r0, [r1, #4]
        b"\x1e\xff\x2f\xe1"  # bx lr
        b"\x00\x00\x00\x00"  # pad
        + struct.pack("<II", 0x20000110, 5)
    )

    uc.mem_write(STUB_GET_VAL, stub_val)
    uc.mem_write(STUB_UI_25A318, make_log_stub(1, 0x20000100))
    uc.mem_write(STUB_VM_275A18, make_log_stub(2, 0x20000104))
    uc.mem_write(STUB_VM_275E38, make_log_stub(3, 0x20000108))
    uc.mem_write(STUB_VM_289AE8, make_log_stub(4, 0x2000010C))
    uc.mem_write(STUB_VM_2B8B78, stub_2b8b78)

    return uc


def run_case(code_bytes: bytes, target_addr: int, val: int, initial_flag: int):
    uc = build_emulator(code_bytes, target_addr)

    DATA_BASE = 0x20000000
    DATA_SIZE = 0x10000
    uc.mem_map(DATA_BASE, DATA_SIZE)

    # 0x0049F91C page:
    FLAG_PAGE = 0x0049F000
    FLAG_ADDR = 0x0049F91C + 0x251
    try:
        uc.mem_map(FLAG_PAGE, 0x2000)
    except Exception:
        pass

    uc.mem_write(DATA_BASE + 0, struct.pack("<I", val))
    uc.mem_write(DATA_BASE + 0x100, b"\x00" * 32)
    uc.mem_write(FLAG_ADDR, struct.pack("<B", initial_flag))

    sp = STACK_BASE + STACK_SIZE - 0x100
    lr = target_addr + len(code_bytes)

    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, lr)
    uc.reg_write(UC_ARM_REG_R4, 0x11111111)
    uc.reg_write(UC_ARM_REG_R5, 0x22222222)
    uc.reg_write(UC_ARM_REG_R6, 0x33333333)
    uc.reg_write(UC_ARM_REG_R7, 0x44444444)
    uc.reg_write(UC_ARM_REG_R8, 0x55555555)

    uc.emu_start(target_addr, lr, timeout=1000000)

    ret = uc.reg_read(UC_ARM_REG_R0)
    final_flag = struct.unpack("<B", uc.mem_read(FLAG_ADDR, 1))[0]
    logs = list(struct.unpack("<6I", uc.mem_read(DATA_BASE + 0x100, 24)))

    r4 = uc.reg_read(UC_ARM_REG_R4)
    r5 = uc.reg_read(UC_ARM_REG_R5)
    r6 = uc.reg_read(UC_ARM_REG_R6)
    r7 = uc.reg_read(UC_ARM_REG_R7)
    r8 = uc.reg_read(UC_ARM_REG_R8)

    return {
        "ret": ret,
        "final_flag": final_flag,
        "logs": logs,
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
        # 1. val != 0 and flag == 0 -> toggle ON: flag becomes 1, calls 3, 4, 5 (arg 0x90)
        {"name": "turn_on", "val": 1, "initial_flag": 0},
        # 2. val != 0 and flag == 1 -> already on, no calls
        {"name": "already_on", "val": 1, "initial_flag": 1},
        # 3. val == 0 and flag == 1 -> toggle OFF: flag becomes 0, calls 1, 2
        {"name": "turn_off", "val": 0, "initial_flag": 1},
        # 4. val == 0 and flag == 0 -> already off, no calls
        {"name": "already_off", "val": 0, "initial_flag": 0},
        # 5. arbitrary non-zero val (e.g. 42)
        {"name": "turn_on_large_val", "val": 42, "initial_flag": 0},
    ]

    all_passed = True
    results = []

    for c in cases:
        orig_res = run_case(orig_bytes, ORIG_ADDR, c["val"], c["initial_flag"])
        comp_res = run_case(staged_compiled, ORIG_ADDR, c["val"], c["initial_flag"])

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
