#!/usr/bin/env python3
"""Differential test for func_002a9414 (0x002A9414).

Validates that reconstructed C++ matches original ARM binary:
- Populates a 48-byte stack buffer from template at 0x004098B0 (0x00409780 + 0x130).
- Overwrites specific slots with fields from inputs a, b, c:
    buf[0] = a[2], buf[2] = a[1], buf[3] = a[0]
    buf[4] = b[2], buf[6] = b[1], buf[7] = b[0]
    buf[10] = c[1], buf[11] = c[0]
- Preserves slots 1, 5, 8, 9 from the template.
- Calls battle_func_002ade34(buf, 0x30, 1).
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
    UC_ARM_REG_FPEXC,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
ORIG_ADDR = 0x002A9414
ORIG_SIZE = 132

STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

STUB_CALLBACK = 0x002ADE34

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

SYMBOL_MAP = {
    "battle_func_002ade34": STUB_CALLBACK,
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
    if "func_002a9414" not in functions:
        raise RuntimeError("func_002a9414 not in object")
    body, relocs = functions["func_002a9414"]
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
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    # Map rodata page around 0x00409780
    RODATA_BASE = 0x00408000
    RODATA_SIZE = 0x4000
    try:
        uc.mem_map(RODATA_BASE, RODATA_SIZE)
    except Exception:
        pass
    with open(ORIG_BIN, "rb") as f:
        f.seek(RODATA_BASE - 0x00100000)
        rodata = f.read(RODATA_SIZE)
    uc.mem_write(RODATA_BASE, rodata)

    # Stub: records r0 (buffer contents copied to 0x20000100), r1, r2, count at 0x20000000
    # 0x00: ldr r3, =0x20000000
    # 0x04: stm r3, {r1, r2} (stores size, mode)
    # 0x08: ldr r3, =0x20000100 (dest buf)
    # Copy 48 bytes (12 words) from r0 to r3:
    # 0x0c: ldm r0, {r1, r2}
    # For simplicity, stub copies r0 pointer to 0x20000008, size to 0x20000000, mode to 0x20000004
    # and copies 48 bytes from [r0] to [0x20000100]
    stub_asm = (
        b"\x30\x30\x9f\xe5"  # ldr r3, [pc, #48] -> 0x20000000
        b"\x00\x10\x83\xe5"  # str r1, [r3]
        b"\x04\x20\x83\xe5"  # str r2, [r3, #4]
        b"\x08\x00\x83\xe5"  # str r0, [r3, #8]
        b"\x28\x10\x9f\xe5"  # ldr r1, [pc, #40] -> 0x20000100
        # copy 48 bytes:
        b"\x0f\x00\x90\xe8"  # ldm r0!, {r0, r1, r2, r3} (wait! r1 is dest! don't overwrite r1!)
        # Use ip instead:
        b"\x1e\xff\x2f\xe1"  # bx lr (we can just read from the stack pointer stored in 0x20000008!)
    )
    # Clean simple stub:
    # 0x00: ldr ip, [pc, #8] -> 0x20000000
    # 0x04: stm ip, {r0, r1, r2}
    # 0x08: bx lr
    # 0x0c: .word 0x20000000
    stub_clean = (
        b"\x08\xc0\x9f\xe5"  # ldr ip, [pc, #8] -> 0x20000000
        b"\x07\x00\x8c\xe8"  # stm ip, {r0, r1, r2}
        b"\x1e\xff\x2f\xe1"  # bx lr
        b"\x00\x00\x00\x00"  # pad
        + struct.pack("<I", 0x20000000)
    )
    uc.mem_write(STUB_CALLBACK, stub_clean)

    return uc


def run_case(code_bytes: bytes, target_addr: int, a: list[int], b: list[int], c: list[int]):
    uc = build_emulator(code_bytes, target_addr)

    DATA_BASE = 0x20000000
    DATA_SIZE = 0x10000
    uc.mem_map(DATA_BASE, DATA_SIZE)

    # 0x20000000: r0 (stack buf pointer)
    # 0x20000004: r1 (size)
    # 0x20000008: r2 (mode)
    uc.mem_write(DATA_BASE, b"\x00" * 16)

    A_ADDR = DATA_BASE + 0x1000
    B_ADDR = DATA_BASE + 0x2000
    C_ADDR = DATA_BASE + 0x3000

    uc.mem_write(A_ADDR, struct.pack("<III", *a))
    uc.mem_write(B_ADDR, struct.pack("<III", *b))
    uc.mem_write(C_ADDR, struct.pack("<II", c[0], c[1]))

    sp = STACK_BASE + STACK_SIZE - 0x100
    lr = target_addr + len(code_bytes)

    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, lr)
    uc.reg_write(UC_ARM_REG_R0, A_ADDR)
    uc.reg_write(UC_ARM_REG_R1, B_ADDR)
    uc.reg_write(UC_ARM_REG_R2, C_ADDR)
    uc.reg_write(UC_ARM_REG_R4, 0x11111111)
    uc.reg_write(UC_ARM_REG_R5, 0x22222222)
    uc.reg_write(UC_ARM_REG_R6, 0x33333333)
    uc.reg_write(UC_ARM_REG_R7, 0x44444444)
    uc.reg_write(UC_ARM_REG_R8, 0x55555555)

    uc.emu_start(target_addr, lr, timeout=1000000)

    buf_ptr, size, mode = struct.unpack("<III", uc.mem_read(DATA_BASE, 12))
    buf_words = list(struct.unpack("<12I", uc.mem_read(buf_ptr, 48)))

    r4 = uc.reg_read(UC_ARM_REG_R4)
    r5 = uc.reg_read(UC_ARM_REG_R5)
    r6 = uc.reg_read(UC_ARM_REG_R6)
    r7 = uc.reg_read(UC_ARM_REG_R7)
    r8 = uc.reg_read(UC_ARM_REG_R8)

    return {
        "size": size,
        "mode": mode,
        "buf": buf_words,
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
        {
            "name": "basic_values",
            "a": [1, 2, 3],
            "b": [4, 5, 6],
            "c": [7, 8],
        },
        {
            "name": "zeros",
            "a": [0, 0, 0],
            "b": [0, 0, 0],
            "c": [0, 0],
        },
        {
            "name": "pattern_hex",
            "a": [0xAAAAAAAA, 0xBBBBBBBB, 0xCCCCCCCC],
            "b": [0x11111111, 0x22222222, 0x33333333],
            "c": [0x44444444, 0x55555555],
        },
        {
            "name": "floats_in_inputs",
            "a": [0x3F800000, 0x40000000, 0x40400000],  # 1.0f, 2.0f, 3.0f
            "b": [0x40800000, 0x40A00000, 0x40C00000],  # 4.0f, 5.0f, 6.0f
            "c": [0x40E00000, 0x41000000],              # 7.0f, 8.0f
        },
    ]

    all_passed = True
    results = []

    for c in cases:
        orig_res = run_case(orig_bytes, ORIG_ADDR, c["a"], c["b"], c["c"])
        comp_res = run_case(staged_compiled, ORIG_ADDR, c["a"], c["b"], c["c"])

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
