#!/usr/bin/env python3
"""Differential test for battle_func_00292c7c (0x00292c7c) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the battle_func_00292c7c body
and runs the pinned original (extracted/exefs/code.bin) against the candidate in
separate Unicorn machines with identical fixtures. The function makes no calls,
so the only inputs are r0 (result matrix), r1 (padding-clear flag) and s0/s1/s2
(the three signed angles); the shared 256-entry float table at 0x00407FC0 is
fixture memory.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11 and d8-d15;
  * the full result page (matrix + surrounding sentinel bytes must be identical);
  * every emulated write outside the private stack.

Coverage: zero / integer / fractional angles, exact 8-bit table-index
boundaries (0, 255, 256, 511), fractional parts 0 and near 1, the exact
65536.0f reduction boundary and multi-period reductions, every sign combination
including -0.0 and all-negative, and clear_padding = 0 / 1 / 0xFFFFFFFF.
Negative controls mutate the wrap period, the index mask, a sign test, the
interpolation operand and one padding offset; each mutant must be detected.
"""

from __future__ import annotations

import math
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
SOURCE = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_00292c7c"

FUNC_ADDR = 0x00292C7C
FUNC_SIZE = 500

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000
TABLE_ADDR = 0x00400000
TABLE_SIZE = 0x00020000
RESULT_ADDR = 0x00700000
RESULT_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

TABLE_BASE = 0x00407FC0
TABLE_ENTRIES = 256

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

CALLEE_SAVED = {
    "r4": arm.UC_ARM_REG_R4,
    "r5": arm.UC_ARM_REG_R5,
    "r6": arm.UC_ARM_REG_R6,
    "r7": arm.UC_ARM_REG_R7,
    "r8": arm.UC_ARM_REG_R8,
    "r9": arm.UC_ARM_REG_R9,
    "r10": arm.UC_ARM_REG_R10,
    "r11": arm.UC_ARM_REG_R11,
}
CALLEE_SAVED_START = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}

D_REGS = {
    "d8": arm.UC_ARM_REG_D8,
    "d9": arm.UC_ARM_REG_D9,
    "d10": arm.UC_ARM_REG_D10,
    "d11": arm.UC_ARM_REG_D11,
    "d12": arm.UC_ARM_REG_D12,
    "d13": arm.UC_ARM_REG_D13,
    "d14": arm.UC_ARM_REG_D14,
    "d15": arm.UC_ARM_REG_D15,
}
D_START = {name: (0x1000 + index) for index, name in enumerate(D_REGS)}


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def find_candidate(relocate: bool = True) -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    entry = None
    for name, value in funcs.items():
        if "00292c7c" in name:
            entry = value
            break
    if entry is None:
        raise RuntimeError(
            f"battle_func_00292c7c not found in {obj_file}: {sorted(funcs)}"
        )
    code, relocs = entry
    unresolved = [rel for rel in relocs if relocate]
    if unresolved:
        raise RuntimeError(
            "unexpected relocations in candidate: "
            + ", ".join(f"{r.relocation_type}:{r.symbol_name}" for r in unresolved)
        )
    return bytes(code)


def compile_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    res = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {res.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    for name_key, value in funcs.items():
        if "00292c7c" in name_key:
            code, relocs = value
            if relocs:
                raise RuntimeError("mutant has relocations")
            return bytes(code)
    raise RuntimeError("mutant function missing")


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def build_table() -> bytes:
    """Deterministic 256-entry fixture; values include inexact fractions."""
    page = bytearray(TABLE_SIZE)
    for k in range(TABLE_ENTRIES):
        f0 = math.sin(k * 0.7) * 1.25 - 0.3
        f1 = math.cos(k * 1.3) * 0.75 + 0.11
        f2 = ((k * 7 + 3) % 31) * 0.5 - 2.0
        f3 = ((k * 11 + 5) % 17) * 0.0625 - 0.5
        struct.pack_into(
            "<ffff", page, (TABLE_BASE - TABLE_ADDR) + k * 16, f0, f1, f2, f3
        )
    return bytes(page)


def build_result() -> bytes:
    page = bytearray(RESULT_SIZE)
    for index in range(0, RESULT_SIZE, 4):
        struct.pack_into("<I", page, index, 0xA5A50000 | (index & 0xFFFF))
    return bytes(page)


class Runner:
    """One Unicorn ARMv6K machine; no calls, only the stack and result writes."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # Both bodies use VFP (vldr/vabs/vcvt/vmla...): enable CP10/CP11 and
        # FPEXC.EN.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
        self.uc.mem_map(RESULT_ADDR, RESULT_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.writes: list = []
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def run(self, code: bytes, case: dict) -> dict:
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(TABLE_ADDR, build_table())
        self.uc.mem_write(RESULT_ADDR, build_result())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, RESULT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["clear"] & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        for name, value in D_START.items():
            self.uc.reg_write(D_REGS[name], value)
        self.uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(case["a0"]))
        self.uc.reg_write(arm.UC_ARM_REG_S1, f32_bits(case["a1"]))
        self.uc.reg_write(arm.UC_ARM_REG_S2, f32_bits(case["a2"]))

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_result = RESULT_ADDR <= address < RESULT_ADDR + RESULT_SIZE
            if not (in_stack or in_result):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "dregs": {name: self.uc.reg_read(reg) for name, reg in D_REGS.items()},
            "result": bytes(self.uc.mem_read(RESULT_ADDR, RESULT_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "dregs"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["result"] != cand["result"]:
        first = next(
            index
            for index in range(len(orig["result"]))
            if orig["result"][index] != cand["result"][index]
        )
        problems.append(
            f"result page differs at byte 0x{first:04x}\n"
            f"    orig={orig['result'][first:first + 0x40]!r}\n"
            f"    cand={cand['result'][first:first + 0x40]!r}"
        )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def case(name: str, a0: float, a1: float, a2: float, clear: int = 0) -> dict:
    return {"name": name, "a0": a0, "a1": a1, "a2": a2, "clear": clear}


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # Baseline / integer / fractional / mixed signs.
    cases.append(case("all zero clear=0", 0.0, 0.0, 0.0, 0))
    cases.append(case("all zero clear=1", 0.0, 0.0, 0.0, 1))
    cases.append(case("unit integers", 1.0, 2.0, 3.0, 1))
    cases.append(case("fractions", 1.5, 2.25, 3.75, 0))
    cases.append(case("x negative", -1.5, 2.25, 3.75, 1))
    cases.append(case("y negative", 1.5, -2.25, 3.75, 1))
    cases.append(case("z negative", 1.5, 2.25, -3.75, 1))
    cases.append(case("all negative", -1.5, -2.25, -3.75, 0))
    cases.append(case("negative zero", -0.0, 0.0, -0.0, 1))
    cases.append(case("small denormal-ish", 1e-20, -1e-20, 0.5, 0))

    # 8-bit index boundaries and fractional-part boundaries.
    for angle in (254.0, 254.5, 255.0, 255.5, 255.9999, 256.0, 256.5,
                  257.25, 511.75, 512.0, -255.5, -256.5):
        cases.append(case(f"index boundary {angle}", angle, angle * 0.5 + 0.25,
                          angle * 0.25 + 0.125, 1))

    # Below the reduction period, then the period boundaries and multiples.
    for angle in (32767.5, 32768.0, 40000.25, 50000.5, 65534.75,
                  65535.0, 65535.5, 65535.9375, 65536.0, 65536.5, 65537.25,
                  70000.0, 131071.5, 131072.0, 200000.5, 1000000.25,
                  4194304.5, 8388608.0,
                  -32768.5, -40000.25, -65536.0, -70000.5, -1000000.25):
        cases.append(case(f"wrap {angle}", angle, 3.5, -7.25, 1))

    # Independent per-angle index/frac combinations.
    cases.append(case("mixed axes", 255.5, 0.25, 65535.9375, 1))
    cases.append(case("mixed axes 2", 65536.25, 256.5, -511.5, 0))
    cases.append(case("flags", 12.25, -13.5, 14.75, 2))
    cases.append(case("flags max", -12.25, 13.5, -14.75, 0xFFFFFFFF))
    cases.append(case("flags high bit", 42.5, 43.5, 44.5, 0x80000000))
    return cases


def run_cases(orig_code: bytes, cand_code: bytes, cases: list[dict]) -> int:
    passed = 0
    for item in cases:
        orig = Runner().run(orig_code, item)
        cand = Runner().run(cand_code, item)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {item['name']}")
            for problem in problems:
                print(f"    {problem}")
            return passed
        passed += 1
        print(f"  [PASS] {item['name']}")
    return passed


def main() -> None:
    print("Testing battle_func_00292c7c (0x00292c7c)...")
    orig_code = get_orig_bytes()
    cand_code = find_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B (no relocs).")

    cases = make_cases()
    passed = run_cases(orig_code, cand_code, cases)
    if passed != len(cases):
        raise SystemExit(1)

    print("\nNegative controls:")
    for name, old, new in (
        # Halving kPeriod is deliberately not a control: 32768 is a multiple of
        # 256, so the 8-bit index and the fractional part are unchanged.
        ("wrap_bound", "constexpr s32 kPeriodBits = 0x47800000;",
         "constexpr s32 kPeriodBits = 0x47000000;"),
        ("table_index_mask", "u8 const index_x = static_cast<u8>(int_x);",
         "u8 const index_x = static_cast<u8>(int_x >> 1);"),
        ("sign_test", "bool const negative_z = angle2 < 0.0f;",
         "bool const negative_z = angle2 <= 0.0f;"),
        ("interpolation_operand",
         "f32 b = lerp(ex.f1, frac_x, ex.f3);",
         "f32 b = lerp(ex.f1, frac_x, ex.f2);"),
        ("padding_offset", "out[3] = 0.0f;   // +0x0C",
         "out[2] = 0.0f;   // +0x0C"),
    ):
        mutant_code = compile_mutant(name, old, new)
        detected = False
        for item in cases:
            orig = Runner().run(orig_code, item)
            bad = Runner().run(mutant_code, item)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
