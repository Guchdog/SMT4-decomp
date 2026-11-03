#!/usr/bin/env python3
"""Differential test for engine_func_0022b9d0 (0x0022B9D0).

Validates that reconstructed C++ matches original ARM binary:
- Reads coordinates from src + 0x50 (floats x, y).
- Computes limits:
    limit_x = (float)((int)(src_x - 400.0f))
    limit_y = (float)((int)(src_y - 240.0f))
- Clamps out[0] into [0, limit_x] (if out[0] <= 0 -> 0; if out[0] > limit_x -> limit_x).
- Clamps out[1] into [0, limit_y] (if out[1] <= 0 -> 0; if out[1] > limit_y -> limit_y).
- Preserves non-volatile registers.
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
ORIG_ADDR = 0x0022B9D0
ORIG_SIZE = 132

STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

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
    if "engine_func_0022b9d0" not in functions:
        raise RuntimeError("engine_func_0022b9d0 not in object")
    body, relocs = functions["engine_func_0022b9d0"]
    return body, relocs


def build_emulator(code_bytes: bytes, target_addr: int) -> Uc:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_write(target_addr, code_bytes)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    return uc


def run_case(code_bytes: bytes, target_addr: int, src_xy: tuple[float, float], in_xy: tuple[float, float]):
    uc = build_emulator(code_bytes, target_addr)

    DATA_BASE = 0x20000000
    DATA_SIZE = 0x10000
    uc.mem_map(DATA_BASE, DATA_SIZE)

    SRC_ADDR = DATA_BASE + 0x1000
    OUT_ADDR = DATA_BASE + 0x2000

    uc.mem_write(SRC_ADDR + 0x50, struct.pack("<ff", src_xy[0], src_xy[1]))
    uc.mem_write(OUT_ADDR, struct.pack("<ff", in_xy[0], in_xy[1]))

    sp = STACK_BASE + STACK_SIZE - 0x100
    lr = target_addr + len(code_bytes)

    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, lr)
    uc.reg_write(UC_ARM_REG_R0, SRC_ADDR)
    uc.reg_write(UC_ARM_REG_R1, OUT_ADDR)
    uc.reg_write(UC_ARM_REG_R4, 0x11111111)
    uc.reg_write(UC_ARM_REG_R5, 0x22222222)
    uc.reg_write(UC_ARM_REG_R6, 0x33333333)
    uc.reg_write(UC_ARM_REG_R7, 0x44444444)
    uc.reg_write(UC_ARM_REG_R8, 0x55555555)

    uc.emu_start(target_addr, lr, timeout=1000000)

    out_x, out_y = struct.unpack("<ff", uc.mem_read(OUT_ADDR, 8))
    r4 = uc.reg_read(UC_ARM_REG_R4)
    r5 = uc.reg_read(UC_ARM_REG_R5)
    r6 = uc.reg_read(UC_ARM_REG_R6)
    r7 = uc.reg_read(UC_ARM_REG_R7)
    r8 = uc.reg_read(UC_ARM_REG_R8)

    return {
        "out_x": round(out_x, 4),
        "out_y": round(out_y, 4),
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

    cases = [
        {"name": "inside_bounds", "src": (500.0, 300.0), "in": (50.0, 30.0)},
        {"name": "negative_inputs", "src": (500.0, 300.0), "in": (-20.0, -10.0)},
        {"name": "zeros", "src": (500.0, 300.0), "in": (0.0, 0.0)},
        {"name": "exceeds_limits", "src": (500.0, 300.0), "in": (150.0, 100.0)},
        {"name": "fractional_src_truncate", "src": (500.8, 300.9), "in": (100.5, 60.5)},
        {"name": "src_below_screen_dim", "src": (350.0, 200.0), "in": (20.0, 15.0)},
        {"name": "fractional_in_inside", "src": (600.0, 400.0), "in": (123.25, 87.75)},
        {"name": "exact_bounds", "src": (500.0, 300.0), "in": (100.0, 60.0)},
        {"name": "large_values", "src": (1000.0, 800.0), "in": (550.0, 450.0)},
        {"name": "x_exceeds_y_negative", "src": (500.0, 300.0), "in": (200.0, -5.0)},
    ]

    all_passed = True
    results = []

    for c in cases:
        orig_res = run_case(orig_bytes, ORIG_ADDR, c["src"], c["in"])
        comp_res = run_case(compiled_bytes, ORIG_ADDR, c["src"], c["in"])

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
