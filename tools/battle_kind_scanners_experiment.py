#!/usr/bin/env python3
"""Differential test for battle entity kind scanners:
- battle_func_002f05ac (0x002F05AC, target kind 2)
- battle_func_002f6f08 (0x002F6F08, target kind 1)
- battle_func_002f6f90 (0x002F6F90, target kind 2 with non-zero check)
- battle_func_002fed1c (0x002FED1C, target kind 3)
- battle_func_002ff180 (0x002FF180, target kind 4)

Validates that reconstructed C++ matches original ARM binary:
- Calls engine_func_00296f60(0) to get slot index.
- Scans up to 109 entity records of 648 bytes in ui_func_00293c98()[0x1fc0].
- For each record, checks (flags & 0x51) == 0x11.
- Reads u16 val from elem + 0x1F2 + index * 2.
- Checks kind match. If match: calls battle_func_0028df54(1) and returns 1.
- If loop finishes with no match: calls battle_func_0028df54(0) and returns 1.
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

STUB_GET_INDEX = 0x00296F60
STUB_GET_CTX = 0x00293C98
STUB_CALLBACK = 0x0028DF54

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

SYMBOL_MAP = {
    "engine_func_00296f60": STUB_GET_INDEX,
    "ui_func_00293c98": STUB_GET_CTX,
    "battle_func_0028df54": STUB_CALLBACK,
}

FUNCTIONS = [
    {"name": "battle_func_002f05ac", "addr": 0x002F05AC, "size": 136, "target_kind": 2},
    {"name": "battle_func_002f6f08", "addr": 0x002F6F08, "size": 136, "target_kind": 1},
    {"name": "battle_func_002f6f90", "addr": 0x002F6F90, "size": 140, "target_kind": 2},
    {"name": "battle_func_002fed1c", "addr": 0x002FED1C, "size": 136, "target_kind": 3},
    {"name": "battle_func_002ff180", "addr": 0x002FF180, "size": 136, "target_kind": 4},
]


def load_original_bytes(addr: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(addr - 0x00100000)
        return f.read(size)


def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    obj = out / "leaf_batch30_c.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    functions = extract_elf_functions_detailed(obj)
    if func_name not in functions:
        raise RuntimeError(f"{func_name} not in object")
    body, relocs = functions[func_name]
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
    stub_asm_index = (
        b"\x04\x00\x9f\xe5"  # ldr r0, [pc, #4]
        b"\x00\x00\x90\xe5"  # ldr r0, [r0]
        b"\x1e\xff\x2f\xe1"  # bx lr
        + struct.pack("<I", 0x20000000)
    )
    stub_asm_ctx = (
        b"\x04\x00\x9f\xe5"  # ldr r0, [pc, #4]
        b"\x00\x00\x90\xe5"  # ldr r0, [r0]
        b"\x1e\xff\x2f\xe1"  # bx lr
        + struct.pack("<I", 0x20000004)
    )
    stub_asm_cb = (
        b"\x10\x10\x9f\xe5"  # ldr r1, [pc, #16]
        b"\x00\x00\x81\xe5"  # str r0, [r1]
        b"\x04\x20\x91\xe5"  # ldr r2, [r1, #4]
        b"\x01\x20\x82\xe2"  # add r2, r2, #1
        b"\x04\x20\x81\xe5"  # str r2, [r1, #4]
        b"\x1e\xff\x2f\xe1"  # bx lr
        + struct.pack("<I", 0x20000008)
    )
    uc.mem_write(STUB_GET_INDEX, stub_asm_index)
    uc.mem_write(STUB_GET_CTX, stub_asm_ctx)
    uc.mem_write(STUB_CALLBACK, stub_asm_cb)

    return uc


def run_case(code_bytes: bytes, target_addr: int, index: int, entities: dict[int, tuple[int, int]]):
    uc = build_emulator(code_bytes, target_addr)

    DATA_BASE = 0x20000000
    DATA_SIZE = 0x40000  # 256KB
    uc.mem_map(DATA_BASE, DATA_SIZE)

    CTX_ADDR = 0x20001000
    TABLE_ADDR = 0x20004000

    uc.mem_write(DATA_BASE + 0, struct.pack("<I", index))
    uc.mem_write(DATA_BASE + 4, struct.pack("<I", CTX_ADDR))
    uc.mem_write(DATA_BASE + 8, struct.pack("<I", 0xDEADBEEF))
    uc.mem_write(DATA_BASE + 12, struct.pack("<I", 0))

    uc.mem_write(CTX_ADDR + 0x1FC0, struct.pack("<I", TABLE_ADDR))

    for idx in range(109):
        flags, val = entities.get(idx, (0, 0))
        elem_addr = TABLE_ADDR + idx * 648
        uc.mem_write(elem_addr, struct.pack("<I", flags))
        uc.mem_write(elem_addr + 0x1F2 + index * 2, struct.pack("<H", val))

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
    cb_val = struct.unpack("<I", uc.mem_read(DATA_BASE + 8, 4))[0]
    cb_count = struct.unpack("<I", uc.mem_read(DATA_BASE + 12, 4))[0]
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    out_dir = ROOT / "build"
    all_passed = True
    overall_results = {}

    for fn in FUNCTIONS:
        orig_bytes = load_original_bytes(fn["addr"], fn["size"])
        compiled_bytes, relocs = compile_function(fn["name"], out_dir)
        staged_compiled = stage_body(compiled_bytes, relocs, fn["addr"])

        target_kind = fn["target_kind"]
        val_match = (target_kind << 10) | 0x2A  # kind in bits 10..15, low 10 bits arbitrary
        val_mismatch = ((target_kind + 1) << 10) | 0x2A

        cases = [
            # 1. Empty table -> cb_val=0, ret=1
            {"name": "empty_table", "index": 0, "entities": {}},
            # 2. Entity 0 matches -> cb_val=1, ret=1
            {"name": "match_idx0", "index": 0, "entities": {0: (0x11, val_match)}},
            # 3. Entity 0 value mismatch -> cb_val=0, ret=1
            {"name": "mismatch_idx0", "index": 0, "entities": {0: (0x11, val_mismatch)}},
            # 4. Entity 0 flags filtered (0x40 set) -> cb_val=0, ret=1
            {"name": "flag_0x40_filtered", "index": 0, "entities": {0: (0x51, val_match)}},
            # 5. Entity 108 (last index) matches with non-zero index (index=2)
            {"name": "match_last_idx108_idx2", "index": 2, "entities": {108: (0x11, val_match)}},
            # 6. Entity 50 matches with index=5
            {"name": "match_idx50_idx5", "index": 5, "entities": {50: (0x211, val_match)}},
        ]

        fn_results = []
        for c in cases:
            orig_res = run_case(orig_bytes, fn["addr"], c["index"], c["entities"])
            comp_res = run_case(staged_compiled, fn["addr"], c["index"], c["entities"])

            passed = orig_res == comp_res
            if not passed:
                all_passed = False

            fn_results.append({
                "name": c["name"],
                "orig": orig_res,
                "comp": comp_res,
                "passed": passed,
            })

        overall_results[fn["name"]] = fn_results
        if not args.json:
            fn_pass = all(r["passed"] for r in fn_results)
            print(f"[{'PASS' if fn_pass else 'FAIL'}] {fn['name']}: {len(fn_results)} cases verified")

    if args.json:
        print(json.dumps({"passed": all_passed, "functions": overall_results}, indent=2))
    else:
        print(f"\nOverall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
