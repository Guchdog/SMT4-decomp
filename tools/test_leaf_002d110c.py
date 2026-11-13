#!/usr/bin/env python3
"""Differential test for func_002d110c (0x002D110C, 444 bytes) using Unicorn ARM.

Compiles ``src/engine/leaf_batch41_c.cpp``, extracts the ``func_002d110c`` body,
resolves its five direct calls to deterministic stubs at their original
addresses, and runs the pinned original (``extracted/exefs/code.bin``) and the
candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * continuation PC and final SP; the packed-return r0 on the early-exit path;
  * callee-saved r4-r11;
  * the ordered call log with all four register arguments, two architected
    stack words per call, and the helper return values;
  * owner, state/display, and the shared 0x004EA91C colour block memory;
  * any emulated write outside the stack, display record, or colour block.

The function is ``void``: on the normal path the original leaves r0 holding
whatever the final 0x00269768 call left there, so r0 is only compared when the
signed early-exit path explicitly writes zero.

Coverage: both default-initialisation triggers (zero count, zero frame), every
skip-initialise form, signed count<frame boundaries (including INT_MIN/INT_MAX
and negative/negative), equality, zero/non-zero sample colours, zero/negative
curve samples, and distinct owner colours. Negative controls mutate a default,
the signed comparison, the colour packing and one call argument; each mutant
must be detected.
"""

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
SOURCE = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_002d110c"

FUNC_ADDR = 0x002D110C
FUNC_SIZE = 444

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x3F0000
GLOBAL_ADDR = 0x004E0000
GLOBAL_SIZE = 0x00010000
OWNER_ADDR = 0x00710000
OWNER_SIZE = 0x00001000
STATE_ADDR = 0x00720000
STATE_SIZE = 0x00002000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Colour block layout: previous + 0x100 is current, +0x110 a saved copy.
COLOR_BASE = 0x004EA81C
COLOR_CURRENT = COLOR_BASE + 0x100
COLOR_PREVIOUS = COLOR_BASE + 0x110
COLOR_WINDOW_OFFSET = COLOR_BASE - GLOBAL_ADDR
COLOR_WINDOW_SIZE = 0x140

STUB_2698F4 = 0x002698F4
STUB_257614 = 0x00257614
STUB_269768 = 0x00269768

STUB_NAMES = {
    STUB_2698F4: "func_002698f4",
    STUB_257614: "func_00257614",
    STUB_269768: "func_00269768",
}

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

# The literal 0x3B808081 used by the real 0x00257614 conversion.
COLOR_STEP = struct.unpack("<f", struct.pack("<I", 0x3B808081))[0]


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "002d110c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"func_002d110c not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    addresses = {name: address for address, name in STUB_NAMES.items()}
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):  # PC24 / CALL / JUMP24
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = addresses.get(rel.symbol_name)
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        displacement = (target - (FUNC_ADDR + rel.offset + 8)) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    res = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def build_owner(case: dict) -> bytes:
    page = bytearray(OWNER_SIZE)
    for offset in range(0, OWNER_SIZE, 4):
        struct.pack_into("<I", page, offset, (0xA5A50000 | offset) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x10, case.get("color", 0x11223344) & 0xFFFFFFFF)
    struct.pack_into("<i", page, 0x1C, case.get("frame", 0))
    struct.pack_into("<I", page, 0x24, STATE_ADDR)
    return bytes(page)


def build_state(case: dict) -> bytes:
    page = bytearray(STATE_SIZE)
    for offset in range(0, STATE_SIZE, 4):
        struct.pack_into("<I", page, offset, (0x5A5A0000 | offset) & 0xFFFFFFFF)
    for index in range(0x10):
        page[0x24 + index] = (0x10 + index) & 0xFF
    struct.pack_into("<I", page, 0x28, case.get("value28", 0x89ABCDEF))
    for index in range(0x2C):
        page[0x34 + index] = (0x80 + index) & 0xFF
    for index in range(0x58):
        page[0x60 + index] = (0x30 + index) & 0xFF
    struct.pack_into("<i", page, 0xB8, case.get("count", 0))
    for index in range(0x28):
        page[0xC0 + index] = (0xD0 + index) & 0xFF
    return bytes(page)


def build_global() -> bytes:
    page = bytearray(GLOBAL_SIZE)
    for offset in range(0, GLOBAL_SIZE, 4):
        struct.pack_into("<I", page, offset, (0x3F800000 ^ offset) & 0xFFFFFFFF)
    struct.pack_into("<4f", page, 0xA91C, 0.125, 0.25, 0.5, 0.75)
    struct.pack_into("<4f", page, 0xA92C, 1.5, 2.0, 2.5, 3.0)
    return bytes(page)


def read_c_string(uc, address: int, limit: int = 32) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(OWNER_ADDR, OWNER_SIZE)
        self.uc.mem_map(STATE_ADDR, STATE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int = 2) -> tuple:
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _write_color(self, word: int) -> None:
        low = word & 0xFF
        low_mid = (word >> 8) & 0xFF
        high_mid = (word >> 16) & 0xFF
        high = (word >> 24) & 0xFF
        values = (
            high * COLOR_STEP,
            high_mid * COLOR_STEP,
            low_mid * COLOR_STEP,
            low * COLOR_STEP,
        )
        self.uc.mem_write(COLOR_CURRENT, struct.pack("<4f", *values))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        stack = self._stack_words(2)

        if address == STUB_2698F4:
            self.call_log.append((STUB_NAMES[address], (r0, r1, r2, r3) + stack))
            if self.case.get("sample_zero", False):
                sample = 0
            else:
                mixed = (r0 ^ (r1 << 1) ^ (r2 * 3) ^ (r3 * 5)) & 0xFFFFFFFF
                sample = (
                    (0x20 + (mixed & 0x1F))
                    | ((0x40 + ((mixed >> 5) & 0x1F)) << 8)
                    | ((0x60 + ((mixed >> 10) & 0x1F)) << 16)
                    | ((0x80 + ((mixed >> 15) & 0x1F)) << 24)
                )
            uc.reg_write(arm.UC_ARM_REG_R0, sample)
        elif address == STUB_257614:
            self.call_log.append((STUB_NAMES[address], (r0,) + stack))
            self._write_color(r0)
        elif address == STUB_269768:
            if self.case.get("curve_zero", False):
                result = 0.0
            else:
                base = ((r0 >> 2) & 0x3F) * 0.5
                result = base + (r1 & 0x0F) * 0.25 + (r2 & 0x0F) * 0.125
                if self.case.get("curve_negative", False):
                    result = -result - 0.5
            bits = f32_bits(result)
            self.call_log.append(
                (STUB_NAMES[address], (r0, r1, r2) + stack + (bits,))
            )
            uc.reg_write(arm.UC_ARM_REG_S0, bits)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(OWNER_ADDR, build_owner(case))
        self.uc.mem_write(STATE_ADDR, build_state(case))
        self.uc.mem_write(GLOBAL_ADDR, build_global())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        # Unicorn leaves the VFP unit disabled until FPEXC.EN is set; without
        # this every vldr/vmul/vcvt raises UC_ERR_INSN_INVALID.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)  # CPACR CP10/11
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)    # FPEXC.EN
        self.uc.reg_write(arm.UC_ARM_REG_R0, OWNER_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        display_start = STATE_ADDR + 0xC0
        display_end = display_start + 0x28
        color_start = COLOR_CURRENT
        color_end = COLOR_PREVIOUS + 0x10
        unexpected_writes = []
        for address, size, _value in self.writes:
            regions = (
                (STACK_ADDR, STACK_ADDR + STACK_SIZE),
                (display_start, display_end),
                (color_start, color_end),
            )
            if not any(start <= address < end for start, end in regions):
                unexpected_writes.append((address, size))

        return {
            "r0": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "memory": {
                "owner": bytes(self.uc.mem_read(OWNER_ADDR, OWNER_SIZE)),
                "state": bytes(self.uc.mem_read(STATE_ADDR, STATE_SIZE)),
                "color": bytes(
                    self.uc.mem_read(
                        GLOBAL_ADDR + COLOR_WINDOW_OFFSET, COLOR_WINDOW_SIZE
                    )
                ),
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict, case: dict) -> list[str]:
    problems = []
    if case.get("expect_early", False) and orig["r0"] != cand["r0"]:
        problems.append(f"r0:\n    orig={orig['r0']:#x}\n    cand={cand['r0']:#x}")
    for key in ("pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    for key, value in orig["memory"].items():
        if value != cand["memory"][key]:
            problems.append(f"memory {key} was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "count": 0,
        "frame": 0,
        "color": 0x11223344,
        "value28": 0x89ABCDEF,
        "sample_zero": False,
        "curve_zero": False,
        "curve_negative": False,
        "expect_early": False,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- default-initialisation triggers -------------------------------------
    cases.append(base_case("zero count ignores frame", count=0,
                           frame=0x12345678, color=0x00000000))
    cases.append(base_case("zero count and zero frame", count=0, frame=0,
                           color=0xFFFFFFFF))
    cases.append(base_case("nonzero count, zero frame initialises", count=7,
                           frame=0, color=0x80402010))
    cases.append(base_case("count 1, zero frame initialises", count=1, frame=0))

    # --- skip-initialise normal paths ----------------------------------------
    cases.append(base_case("count 10 > frame 5", count=10, frame=5))
    cases.append(base_case("negative count > negative frame", count=-5,
                           frame=-10))
    cases.append(base_case("INT_MAX count > INT_MIN frame", count=0x7FFFFFFF,
                           frame=-0x80000000))
    cases.append(base_case("positive count > INT_MIN frame", count=5,
                           frame=-0x80000000))
    cases.append(base_case("equality count == frame", count=5, frame=5))
    cases.append(base_case("negative equality", count=-1, frame=-1))
    cases.append(base_case("INT_MIN equality", count=-0x80000000,
                           frame=-0x80000000))

    # --- signed count < frame early exits ------------------------------------
    cases.append(base_case("count 5 < frame 10", count=5, frame=10,
                           expect_early=True))
    cases.append(base_case("count 1 < frame 2", count=1, frame=2,
                           expect_early=True))
    cases.append(base_case("INT_MIN count < INT_MAX frame",
                           count=-0x80000000, frame=0x7FFFFFFF,
                           expect_early=True))
    cases.append(base_case("negative count < zero frame (after init)",
                           count=-5, frame=0, expect_early=True))
    cases.append(base_case("INT_MIN count < zero frame (after init)",
                           count=-0x80000000, frame=0, expect_early=True))
    cases.append(base_case("INT_MIN count < negative frame",
                           count=-0x80000000, frame=-1, expect_early=True))

    # --- colour / helper result variants -------------------------------------
    for color in (0x00000000, 0xFFFFFFFF, 0x00FF00FF, 0xFF00FF00,
                  0x12345678, 0xDEADBEEF):
        cases.append(base_case(f"owner colour 0x{color:08x}", count=3, frame=3,
                               color=color))
    cases.append(base_case("zero sample colour", count=3, frame=3,
                           sample_zero=True, color=0xFFFFFFFF))
    cases.append(base_case("zero curve results", count=4, frame=2,
                           curve_zero=True, color=0x80808080))
    cases.append(base_case("negative curve results", count=4, frame=2,
                           curve_negative=True, color=0x40404040))
    cases.append(base_case("zero sample with zero curve", count=2, frame=2,
                           sample_zero=True, curve_zero=True, color=0))

    # --- default values preserved when initialisation is skipped ------------
    cases.append(base_case("skip initialise keeps display values", count=9,
                           frame=1, value28=0x01020304))
    cases.append(base_case("skip initialise then early exit, INT_MAX frame",
                           count=9, frame=0x7FFFFFFF, value28=0xCAFEBABE,
                           expect_early=True))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, case)
        cand = Runner().run(cand_code, case)
        problems = compare(orig, cand, case)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing func_002d110c (0x002D110C)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(call relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("init_default", "constexpr f32 kInitValue10 = 200.0f;",
         "constexpr f32 kInitValue10 = 201.0f;"),
        ("signed_compare", "if (count < frame) {",
         "if (count <= frame) {"),
        ("color_component",
         "display->color_00[0] = static_cast<u8>(scaled3);",
         "display->color_00[0] = static_cast<u8>(scaled2);"),
        ("sample_argument", "func_00257614(owner->color_10);",
         "func_00257614(state->value_28);"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant_code, case)
            if compare(orig, bad, case):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
