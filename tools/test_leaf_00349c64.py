#!/usr/bin/env python3
"""Differential test for engine_func_00349c64 (0x00349C64) using Unicorn ARM."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
SRC_CPP = ROOT / "src/engine/leaf_batch45_a.cpp"
FUNC_ADDR = 0x00349C64
FUNC_SIZE = 8
FUNC_NAME = "engine_func_00349c64"

MEM_BASE = 0x20000000
MEM_SIZE = 0x00010000
STACK_TOP = 0x2000F000
TRAP_ADDR = 0x001F0000


class Runner:
    def __init__(self, code: bytes):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(MEM_BASE, MEM_SIZE)
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))

    def run(self, r0_init: int, r1_init: int) -> dict:
        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr == TRAP_ADDR:
                uc.emu_stop()

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        try:
            self.uc.reg_write(arm.UC_ARM_REG_R0, r0_init & 0xFFFFFFFF)
            self.uc.reg_write(arm.UC_ARM_REG_R1, r1_init & 0xFFFFFFFF)
            self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
            self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=1000)
        finally:
            self.uc.hook_del(hook)

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
        }


def build_cases() -> list[tuple[str, dict]]:
    return [
        ("zero_args", {"r0_init": 0, "r1_init": 0}),
        ("nonzero_args", {"r0_init": 0xDEADBEEF, "r1_init": 0x12345678}),
        ("max_args", {"r0_init": 0xFFFFFFFF, "r1_init": 0xFFFFFFFF}),
    ]


def run_suite(orig_code: bytes, cand_code: bytes) -> list[str]:
    failures: list[str] = []
    for name, kwargs in build_cases():
        orig = Runner(orig_code).run(**kwargs)
        cand = Runner(cand_code).run(**kwargs)
        if orig != cand:
            failures.append(f"{name}: orig={orig} cand={cand}")
    return failures


def run_negative_controls(orig_code: bytes, cpp_text: str, work_dir: Path) -> None:
    anchor = "extern \"C\" u32 engine_func_00349c64() {\n    return 1u;\n}"
    mutations = [
        ("ret_0", "return 0u;"),
        ("ret_2", "return 2u;"),
        ("ret_neg1", "return 0xFFFFFFFFu;"),
        ("ret_0x10", "return 0x10u;"),
        ("ret_0xff", "return 0xFFu;"),
    ]
    assert anchor in cpp_text, "mutation anchor missing"
    for mut_name, new_body in mutations:
        mut_cpp = work_dir / f"mut_{mut_name}.cpp"
        mut_obj = work_dir / f"mut_{mut_name}.o"
        mut_cpp.write_text(
            cpp_text.replace(anchor, f"extern \"C\" u32 engine_func_00349c64() {{\n    {new_body}\n}}", 1),
            encoding="utf-8",
        )
        compile_tu_armv6k(mut_cpp, mut_obj, ROOT)
        funcs = extract_elf_functions_detailed(mut_obj)
        cand_code = funcs[FUNC_NAME][0]
        failures = run_suite(orig_code, cand_code)
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_00349c64"
    work_dir.mkdir(parents=True, exist_ok=True)

    orig_code = ORIG_BIN.read_bytes()[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]

    obj_path = work_dir / "leaf_batch45_a.o"
    compile_tu_armv6k(SRC_CPP, obj_path, ROOT)
    funcs = extract_elf_functions_detailed(obj_path)
    cand_code = funcs[FUNC_NAME][0]

    failures = run_suite(orig_code, cand_code)
    if failures:
        for f in failures[:5]:
            print("FAIL:", f)
        return 1

    run_negative_controls(orig_code, SRC_CPP.read_text(encoding="utf-8"), work_dir)
    cases = build_cases()
    print(f"ALL PASS: {len(cases)} cases + 5 negative controls (cand_size={len(cand_code)}B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
