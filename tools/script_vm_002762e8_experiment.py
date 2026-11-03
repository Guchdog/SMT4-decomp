#!/usr/bin/env python3
"""Differential test for script_vm_func_002762e8 (0x002762E8).

Validates that reconstructed C++ matches original ARM binary:
- Calls engine_func_002c2b1c() to get base_ctx pointer.
- Reads signed 8-bit count from base_ctx + 0xDE3.
- Iterates i from 0 to count-1:
  - If base_ctx[0xDE4 + i] == 0, skip.
  - If *(s16*)(base_ctx + 0xE04 + i*2) != target_id, skip.
  - Sets base_ctx[0xDE4 + i] = 0.
  - If *(s16*)(base_ctx + 0xDF4 + i*2) != 0, calls script_vm_func_002899c4(val, 1, 1).
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
ORIG_ADDR = 0x002762E8
ORIG_SIZE = 132

STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

STUB_GET_CTX = 0x002C2B1C
STUB_CALLBACK = 0x002899C4

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

SYMBOL_MAP = {
    "engine_func_002c2b1c": STUB_GET_CTX,
    "script_vm_func_002899c4": STUB_CALLBACK,
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
    if "script_vm_func_002762e8" not in functions:
        raise RuntimeError("script_vm_func_002762e8 not in object")
    body, relocs = functions["script_vm_func_002762e8"]
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

    # engine_func_002c2b1c: returns 0x20001000
    stub_asm_ctx = (
        b"\x04\x00\x9f\xe5"  # ldr r0, [pc, #4]
        b"\x00\x00\x90\xe5"  # ldr r0, [r0]
        b"\x1e\xff\x2f\xe1"  # bx lr
        + struct.pack("<I", 0x20000000)
    )

    # script_vm_func_002899c4: logs calls into 0x20000100 (array of [r0, r1, r2])
    # 0x20000004: call count
    stub_asm_cb = (
        b"\x20\x30\x9f\xe5"  # ldr r3, [pc, #32] (0x20000004)
        b"\x00\xc0\x93\xe5"  # ldr r12, [r3] (count)
        b"\x20\xe0\x9f\xe5"  # ldr lr, [pc, #32] (0x20000100 log base)
        b"\x0c\xe1\x8e\xe0"  # add lr, lr, r12, lsl #4 (each log is 16 bytes)
        b"\x00\x00\x8e\xe5"  # str r0, [lr]
        b"\x04\x10\x8e\xe5"  # str r1, [lr, #4]
        b"\x08\x20\x8e\xe5"  # str r2, [lr, #8]
        b"\x01\xc0\x8c\xe2"  # add r12, r12, #1
        b"\x00\xc0\x83\xe5"  # str r12, [r3]
        b"\x1e\xff\x2f\xe1"  # bx lr (Wait! lr was overwritten! Need stack or use ip!)
        # Let's fix: don't clobber lr
    )
    # Safer stub using only r3 and ip:
    # 0x00: ldr r3, =0x20000004
    # 0x04: ldr ip, [r3]
    # 0x08: ldr r3, =0x20000100
    # 0x0c: add r3, r3, ip, lsl #4
    # 0x10: stm r3, {r0, r1, r2}
    # 0x14: add ip, ip, #1
    # 0x18: ldr r3, =0x20000004
    # 0x1c: str ip, [r3]
    # 0x20: bx lr
    stub_cb_clean = (
        b"\x1c\x30\x9f\xe5"  # ldr r3, [pc, #28] -> 0x20000004 (at 0x2899e8)
        b"\x00\xc0\x93\xe5"  # ldr ip, [r3]
        b"\x18\x30\x9f\xe5"  # ldr r3, [pc, #24] -> 0x20000100 (at 0x2899ec)
        b"\x0c\x32\x83\xe0"  # add r3, r3, ip, lsl #4 (16 bytes per log)
        b"\x07\x00\x83\xe8"  # stm r3, {r0, r1, r2}
        b"\x01\xc0\x8c\xe2"  # add ip, ip, #1
        b"\x04\x30\x9f\xe5"  # ldr r3, [pc, #4] -> 0x20000004 (at 0x2899e8)
        b"\x00\xc0\x83\xe5"  # str ip, [r3]
        b"\x1e\xff\x2f\xe1"  # bx lr
        + struct.pack("<II", 0x20000004, 0x20000100)
    )

    uc.mem_write(STUB_GET_CTX, stub_asm_ctx)
    uc.mem_write(STUB_CALLBACK, stub_cb_clean)

    return uc


def run_case(code_bytes: bytes, target_addr: int, target_id: int, count: int, entries: list[tuple[int, int, int]]):
    uc = build_emulator(code_bytes, target_addr)

    DATA_BASE = 0x20000000
    DATA_SIZE = 0x20000
    uc.mem_map(DATA_BASE, DATA_SIZE)

    CTX_ADDR = 0x20001000

    uc.mem_write(DATA_BASE + 0, struct.pack("<I", CTX_ADDR))
    uc.mem_write(DATA_BASE + 4, struct.pack("<I", 0))  # call count

    # Initialize context
    uc.mem_write(CTX_ADDR + 0xDE3, struct.pack("<b", count))

    # entries: list of (active: u8, val: s16, id: s16)
    for idx, (active, val, eid) in enumerate(entries):
        uc.mem_write(CTX_ADDR + 0xDE4 + idx, struct.pack("<B", active))
        uc.mem_write(CTX_ADDR + 0xDF4 + idx * 2, struct.pack("<h", val))
        uc.mem_write(CTX_ADDR + 0xE04 + idx * 2, struct.pack("<h", eid))

    sp = STACK_BASE + STACK_SIZE - 0x100
    lr = target_addr + len(code_bytes)

    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, lr)
    uc.reg_write(UC_ARM_REG_R0, target_id)
    uc.reg_write(UC_ARM_REG_R4, 0x11111111)
    uc.reg_write(UC_ARM_REG_R5, 0x22222222)
    uc.reg_write(UC_ARM_REG_R6, 0x33333333)
    uc.reg_write(UC_ARM_REG_R7, 0x44444444)
    uc.reg_write(UC_ARM_REG_R8, 0x55555555)

    uc.emu_start(target_addr, lr, timeout=2000000)

    call_count = struct.unpack("<I", uc.mem_read(DATA_BASE + 4, 4))[0]
    calls = []
    for c in range(call_count):
        arg0, arg1, arg2 = struct.unpack("<iii", uc.mem_read(DATA_BASE + 0x100 + c * 16, 12))
        calls.append((arg0, arg1, arg2))

    active_bytes = list(uc.mem_read(CTX_ADDR + 0xDE4, 8))
    r4 = uc.reg_read(UC_ARM_REG_R4)
    r5 = uc.reg_read(UC_ARM_REG_R5)
    r6 = uc.reg_read(UC_ARM_REG_R6)
    r7 = uc.reg_read(UC_ARM_REG_R7)
    r8 = uc.reg_read(UC_ARM_REG_R8)

    return {
        "call_count": call_count,
        "calls": calls,
        "active": active_bytes,
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
        # 1. Count = 0 -> no loop
        {"name": "count_0", "target_id": 42, "count": 0, "entries": []},
        # 2. Count = -1 -> no loop
        {"name": "count_negative", "target_id": 42, "count": -1, "entries": []},
        # 3. One inactive entry
        {"name": "inactive_entry", "target_id": 42, "count": 1, "entries": [(0, 100, 42)]},
        # 4. One active matching entry with non-zero val
        {"name": "active_matching_entry", "target_id": 42, "count": 1, "entries": [(1, 100, 42)]},
        # 5. One active matching entry with val == 0 (clears active, but doesn't call cb)
        {"name": "matching_zero_val", "target_id": 42, "count": 1, "entries": [(1, 0, 42)]},
        # 6. One active non-matching entry
        {"name": "active_mismatch", "target_id": 42, "count": 1, "entries": [(1, 100, 99)]},
        # 7. Multiple entries, matching multiple with same target_id
        {"name": "multiple_matches", "target_id": 15, "count": 4, "entries": [
            (1, 10, 15),
            (1, 20, 99),
            (0, 30, 15),
            (1, 40, 15),
        ]},
        # 8. Negative target_id / s16 handling (-5)
        {"name": "negative_id", "target_id": -5, "count": 2, "entries": [
            (1, 77, -5),
            (1, 88, 5),
        ]},
    ]

    all_passed = True
    results = []

    for c in cases:
        orig_res = run_case(orig_bytes, ORIG_ADDR, c["target_id"], c["count"], c["entries"])
        comp_res = run_case(staged_compiled, ORIG_ADDR, c["target_id"], c["count"], c["entries"])

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
