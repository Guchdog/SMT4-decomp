#!/usr/bin/env python3
"""Differential test for ui_func_00195424 (0x00195424) using Unicorn ARM.

Compiles src/engine/leaf_batch44_b.cpp, extracts the ui_func_00195424 body,
resolves its two direct calls to deterministic stubs and runs the pinned
original (extracted/exefs/code.bin) against the candidate in separate Unicorn
machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * callee-saved VFP registers d8-d15 and the FPSCR;
  * the ordered call log including the exact single-precision bit patterns
    passed to the 16-bit-units atan2 helper (0x00360F48) and the signed
    numerator/denominator pairs passed to the integer divide helper
    (0x002C615C);
  * the whole self block (0x000..0x5FF, so every store and every untouched
    sentinel is checked);
  * any emulated write outside the private stack and the self block.

Coverage: state bytes 0, 1, 2 and out-of-range values; both r1 (mirror)
paths; every state-1 sign arm of +0x124 / +0x120 / +0x128 and of the +0x130
bit 0 flag; NaN / infinities / signed-zero inputs for the VFP compares;
fractional, NaN, infinite and saturating values for the `vcvt.s32.f32`
denominator; quarter-turn / wrap boundaries of the state-2 angle arithmetic
and the 16-bit truncation; state-2 NaN/infinite vector components.

Note on `vcvt.s32.f32`: on VFPv2 (ARMv6K) the conversion truncates toward zero
and saturates out-of-range values, and clang emits the same `vcvt.s32.f32` for
a C++ `static_cast<s32>(float)`.  The fractional denominator cases pin that
behavior (e.g. 1.5f -> 1, not 2).

Negative controls mutate the degree scale, a state-2 source offset, the +0x130
flag mask, the +0x128 sign selection and one +/-90 bias; each mutant must be
detected.
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
SOURCE = ROOT / "src/engine/leaf_batch44_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_00195424"

FUNC_ADDR = 0x00195424
FUNC_SIZE = 408

IMAGE_ADDR = 0x00100000
IMAGE_SIZE = 0x00500000
SELF_ADDR = 0x00440000
SELF_SIZE = 0x00000600
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

STUB_ATAN2 = 0x00360F48
STUB_IDIV = 0x002C615C
STUB_NAMES = {
    STUB_ATAN2: "func_00360f48",
    STUB_IDIV: "ui_func_002c615c",
}

# Object offsets used by the routine.
OFF_FIRST_ANGLE = 0x04
OFF_HEADING = 0x0C
OFF_X = 0x120
OFF_Y = 0x124
OFF_Z = 0x128
OFF_FLAGS = 0x130
OFF_STATE = 0x1D8
OFF_SOURCE_X = 0x2D4
OFF_SOURCE_Y = 0x2D8
OFF_DIVISOR = 0x34C

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
VFP_CALLEE_SAVED = {f"d{n}": getattr(arm, f"UC_ARM_REG_D{n}") for n in range(8, 16)}
VFP_CALLEE_SAVED_START = {
    f"d{n}": 0xD0D0D0D000000000 | n for n in range(8, 16)
}


# --------------------------------------------------------------------- helpers
def f32(value: float) -> float:
    """Round a Python double to the nearest binary32 value."""
    return struct.unpack("<f", struct.pack("<f", value))[0]


def fbits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def bits_float(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def vcvt_s32(value: float) -> int:
    """VFPv2 `vcvt.s32.f32`: truncate toward zero, saturate, NaN -> 0."""
    if math.isnan(value):
        return 0
    if value >= 2147483648.0:
        return 0x7FFFFFFF
    if value < -2147483648.0:
        return -0x80000000
    return int(value)


def sdiv_quotient(numerator: int, denominator: int) -> int:
    """`__aeabi_idivmod` quotient: truncation toward zero."""
    if denominator == 0:
        return 0
    quotient = abs(numerator) // abs(denominator)
    if (numerator < 0) != (denominator < 0):
        quotient = -quotient
    return quotient


def sdiv_remainder(numerator: int, denominator: int) -> int:
    if denominator == 0:
        return numerator
    return numerator - sdiv_quotient(numerator, denominator) * denominator


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00195424" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"ui_func_00195424 not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = None
            for address, name in STUB_NAMES.items():
                if f"{address:08x}" in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            condition = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, condition | (displacement & 0x00FFFFFF)
            )
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch44_b.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "state": 1,
        "mirrored": 0,
        "x_120": 1.0,
        "y_124": 1.0,
        "z_128": 1.0,
        "flags": 0,
        "source_x_2d4": 0.0,
        "source_y_2d8": 0.0,
        "divisor_34c": 7.0,
        "atan2_result": 0x2000,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- state dispatch: 0 and values >= 3 do nothing -----------------------
    cases.append(base_case("state 0 is a no-op", state=0))
    cases.append(base_case("state 3 is a no-op", state=3))
    cases.append(base_case("state 0x7F is a no-op", state=0x7F))
    cases.append(base_case("state 0xFF is a no-op", state=0xFF))

    # --- state 2: heading from the +0x120/+0x124 vector ---------------------
    cases.append(base_case("state 2 quarter offset, mirror 0", state=2))
    cases.append(base_case("state 2 quarter offset, mirror 1",
                           state=2, mirrored=1))
    cases.append(base_case("state 2 angle 0x4000 -> 0 degrees", state=2,
                           atan2_result=0x4000))
    cases.append(base_case("state 2 angle 0x4000 -> 0 degrees, mirror 1",
                           state=2, atan2_result=0x4000, mirrored=1))
    cases.append(base_case("state 2 angle 0x0000 -> 270 degrees", state=2,
                           atan2_result=0x0000))
    cases.append(base_case("state 2 angle 0xFFFF wraps to 269 degrees",
                           state=2, atan2_result=0xFFFF))
    cases.append(base_case("state 2 angle 0x8000 -> 180 degrees", state=2,
                           atan2_result=0x8000))
    cases.append(base_case("state 2 angle 0xC000 -> 90 degrees", state=2,
                           atan2_result=0xC000))
    cases.append(base_case("state 2 angle 0x3FFF -> 359 degrees", state=2,
                           atan2_result=0x3FFF))
    for mirrored in (0, 1):
        cases.append(base_case(
            f"state 2 negative vector, mirror {mirrored}", state=2,
            mirrored=mirrored, x_120=-13.5, y_124=-44.25,
            source_x_2d4=-90.125, source_y_2d8=-0.5,
            atan2_result=0x1234))
        cases.append(base_case(
            f"state 2 fractional vector, mirror {mirrored}", state=2,
            mirrored=mirrored, x_120=0.1, y_124=-0.2,
            source_x_2d4=1.0e-6, source_y_2d8=-3.5e-7,
            atan2_result=0x7654))
        cases.append(base_case(
            f"state 2 NaN vector, mirror {mirrored}", state=2,
            mirrored=mirrored, x_120=float("nan"), y_124=1.0,
            source_x_2d4=0.0, source_y_2d8=0.0,
            atan2_result=0x0102))
        cases.append(base_case(
            f"state 2 infinite vector, mirror {mirrored}", state=2,
            mirrored=mirrored, x_120=float("inf"), y_124=float("-inf"),
            source_x_2d4=0.0, source_y_2d8=0.0,
            atan2_result=0xFE01))
    cases.append(base_case("state 2 negative zero result, mirror 1", state=2,
                           mirrored=1, atan2_result=0x4000))

    # --- state 1 heading arms ----------------------------------------------
    cases.append(base_case("state 1 both positive, flags clear"))
    cases.append(base_case("state 1 vertical positive, horizontal negative",
                           x_120=-1.0))
    cases.append(base_case("state 1 vertical zero, horizontal positive",
                           y_124=0.0))
    cases.append(base_case("state 1 vertical negative, horizontal positive",
                           y_124=-1.0))
    cases.append(base_case("state 1 vertical negative, horizontal negative",
                           y_124=-1.0, x_120=-1.0))
    cases.append(base_case("state 1 vertical negative zero takes <= arm",
                           y_124=-0.0))
    cases.append(base_case("state 1 horizontal negative zero takes <= arm",
                           x_120=-0.0))
    cases.append(base_case("state 1 NaN vertical takes <= arm",
                           y_124=float("nan"), flags=1))
    cases.append(base_case("state 1 NaN horizontal takes <= arm",
                           x_120=float("nan")))
    cases.append(base_case("state 1 both NaN", y_124=float("nan"),
                           x_120=float("nan"), flags=1))
    cases.append(base_case("state 1 vertical +inf", y_124=float("inf")))
    cases.append(base_case("state 1 vertical -inf", y_124=float("-inf")))
    cases.append(base_case("state 1 horizontal +inf", x_120=float("inf")))
    cases.append(base_case("state 1 horizontal -inf", x_120=float("-inf")))

    # --- denominator conversion boundaries ---------------------------------
    for divisor, label in (
        (0.0, "0.0"),
        (0.4, "0.4 truncates to 0"),
        (-0.4, "-0.4 truncates to 0"),
        (1.0, "1.0"),
        (-1.0, "-1.0"),
        (1.5, "1.5 truncates to 1"),
        (2.5, "2.5 truncates to 2"),
        (-1.5, "-1.5 truncates to -1"),
        (7.9, "7.9 truncates to 7"),
        (-7.9, "-7.9 truncates to -7"),
        (360.0, "360"),
        (1000.0, "1000"),
        (2147483648.0, "2^31 saturates"),
        (-2147483648.0, "-2^31"),
        (2147483520.0, "2^31-128"),
        (float("inf"), "+inf saturates"),
        (float("-inf"), "-inf saturates"),
        (float("nan"), "NaN converts to 0"),
    ):
        cases.append(base_case(f"state 1 divisor {label}", divisor_34c=divisor))
        cases.append(base_case(
            f"state 1 divisor {label}, vertical negative", divisor_34c=divisor,
            y_124=-2.0))
        cases.append(base_case(
            f"state 1 divisor {label}, flags set", divisor_34c=divisor,
            flags=1, z_128=1.0))

    # --- state 1 +0x04 arm: every sign combination -------------------------
    for y_124 in (1.0, 0.0, -1.0, float("nan")):
        for z_128 in (1.0, 0.0, -1.0, float("nan")):
            cases.append(base_case(
                f"state 1 flags set y={y_124!r} z={z_128!r}",
                y_124=y_124, z_128=z_128, flags=1))
    cases.append(base_case("state 1 flag byte 0x02 does not update +0x04",
                           flags=0x02))
    cases.append(base_case("state 1 flag byte 0xFF updates +0x04",
                           flags=0xFF))
    cases.append(base_case("state 1 flag byte 0x01 updates +0x04",
                           flags=0x01))
    cases.append(base_case("state 1 flags set, horizontal negative",
                           x_120=-1.0, flags=1))
    cases.append(base_case("state 1 flags set, vertical negative, z positive",
                           y_124=-1.0, z_128=1.0, flags=1))
    cases.append(base_case("state 1 flags set, vertical negative, z negative",
                           y_124=-1.0, z_128=-1.0, flags=1))
    cases.append(base_case("state 2 ignores the +0x130 flag byte", state=2,
                           flags=0xFF))
    return cases


# ------------------------------------------------------------------ emulation
class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(IMAGE_ADDR, IMAGE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        # Enable the VFP coprocessor (CP10/CP11) as the tests of the other
        # VFP-using routines do.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.atan2_result = 0

    # ------------------------------------------------------------------ stubs
    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        if address == STUB_ATAN2:
            y_bits = uc.reg_read(arm.UC_ARM_REG_S0)
            x_bits = uc.reg_read(arm.UC_ARM_REG_S1)
            self.call_log.append(("func_00360f48", y_bits, x_bits))
            uc.reg_write(arm.UC_ARM_REG_R0, self.atan2_result & 0xFFFF)
            return
        if address == STUB_IDIV:
            numerator = uc.reg_read(arm.UC_ARM_REG_R0)
            denominator = uc.reg_read(arm.UC_ARM_REG_R1)
            numerator = signed32(numerator)
            denominator = signed32(denominator)
            self.call_log.append(
                ("ui_func_002c615c", numerator, denominator)
            )
            quotient = sdiv_quotient(numerator, denominator)
            remainder = sdiv_remainder(numerator, denominator)
            uc.reg_write(arm.UC_ARM_REG_R0, quotient & 0xFFFFFFFF)
            uc.reg_write(arm.UC_ARM_REG_R1, remainder & 0xFFFFFFFF)
            return
        raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.atan2_result = case["atan2_result"]

        self.uc.mem_write(FUNC_ADDR, code)

        page = bytearray(SELF_SIZE)
        # Deterministic fill so untouched bytes are compared too.
        for index in range(SELF_SIZE):
            page[index] = (index * 37 + 0x5A) & 0xFF
        struct.pack_into("<I", page, 0x00, 0x00112233)
        struct.pack_into("<i", page, OFF_FIRST_ANGLE, case.get("first_04", -12345))
        struct.pack_into("<i", page, OFF_HEADING, case.get("heading_0c", 0x0BADF00D))
        struct.pack_into("<i", page, 0x10, 0x2468ACE0)
        struct.pack_into("<f", page, OFF_X, f32(case["x_120"]))
        struct.pack_into("<f", page, OFF_Y, f32(case["y_124"]))
        struct.pack_into("<f", page, OFF_Z, f32(case["z_128"]))
        page[OFF_FLAGS] = case["flags"] & 0xFF
        page[OFF_STATE] = case["state"] & 0xFF
        struct.pack_into("<f", page, OFF_SOURCE_X, f32(case["source_x_2d4"]))
        struct.pack_into("<f", page, OFF_SOURCE_Y, f32(case["source_y_2d8"]))
        struct.pack_into("<f", page, OFF_DIVISOR, f32(case["divisor_34c"]))
        self.uc.mem_write(SELF_ADDR, bytes(page))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_ADDR + STACK_SIZE - 0x100)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["mirrored"] & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        for name, value in VFP_CALLEE_SAVED_START.items():
            self.uc.reg_write(VFP_CALLEE_SAVED[name], value)
        self.uc.reg_write(arm.UC_ARM_REG_FPSCR, 0)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_self = SELF_ADDR <= address < SELF_ADDR + SELF_SIZE
            if not (in_stack or in_self):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            # FPSCR NZCV bits are scratch compare state (the compiler legally
            # merges the two compares of the unchanged +0x124 field, leaving a
            # different last-compare flag), so only the cumulative exception
            # bits are compared.  IOC (bit 0) is excluded as well: the original
            # uses the signaling `vcmpe.f32`, which raises it for a quiet NaN
            # operand, while clang emits the quiet `vcmp.f32` for the equivalent
            # C++ `>` (same branch result, no invalid-operation flag).
            "fpscr_flags": self.uc.reg_read(arm.UC_ARM_REG_FPSCR) & 0xFE,
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "vfp_callee_saved": {
                name: self.uc.reg_read(reg)
                for name, reg in VFP_CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "self_page": bytes(self.uc.mem_read(SELF_ADDR, SELF_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def signed32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value & 0x80000000 else value


# ----------------------------------------------------------------- comparison
def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "fpscr_flags"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for name, value in orig["vfp_callee_saved"].items():
        if value != cand["vfp_callee_saved"][name]:
            problems.append(
                f"vfp {name}:\n    orig={value!r}\n    "
                f"cand={cand['vfp_callee_saved'][name]!r}"
            )
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    if orig["self_page"] != cand["self_page"]:
        words_orig = struct.unpack("<384I", orig["self_page"])
        words_cand = struct.unpack("<384I", cand["self_page"])
        diffs = [
            (index * 4, words_orig[index], words_cand[index])
            for index in range(len(words_orig))
            if words_orig[index] != words_cand[index]
        ]
        problems.append(f"self page differs at {diffs[:8]}")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


# --------------------------------------------------- independent expectations
def expected_state2(case: dict) -> dict:
    delta_x = f32(f32(case["x_120"]) - f32(case["source_x_2d4"]))
    delta_y = f32(f32(case["y_124"]) - f32(case["source_y_2d8"]))
    angle = case["atan2_result"] & 0xFFFF
    turn = (angle - 0x4000) & 0xFFFF
    degrees = (turn * 0x168) >> 16
    heading = -degrees if case["mirrored"] else degrees
    return {"heading": heading, "ret": heading, "delta_x": delta_x, "delta_y": delta_y}


def check_state2_case(case: dict, result: dict) -> None:
    expected = expected_state2(case)
    page = result["self_page"]
    heading = struct.unpack_from("<i", page, OFF_HEADING)[0]
    assert heading == expected["heading"], (
        f"state 2 heading on {case['name']}: {heading} != {expected['heading']}"
    )
    assert signed32(result["ret"]) == expected["heading"], (
        f"state 2 return on {case['name']}"
    )
    assert struct.unpack_from("<i", page, OFF_FIRST_ANGLE)[0] == case.get("first_04", -12345), (
        f"state 2 wrote +0x04 on {case['name']}"
    )
    assert len(result["call_log"]) == 1, (
        f"state 2 call count on {case['name']}: {result['call_log']}"
    )
    name, y_bits, x_bits = result["call_log"][0]
    assert name == "func_00360f48", f"state 2 call target on {case['name']}"
    # The original subtracts in single precision; NaN payload propagation is
    # emulator-defined, so NaN results are only checked for NaN-ness.
    for observed, value, label in (
        (y_bits, f32(case["y_124"]) - f32(case["source_y_2d8"]), "y"),
        (x_bits, f32(case["x_120"]) - f32(case["source_x_2d4"]), "x"),
    ):
        if math.isnan(value):
            assert math.isnan(bits_float(observed)), (
                f"state 2 NaN {label} argument on {case['name']}"
            )
        else:
            assert observed == fbits(f32(value)), (
                f"state 2 {label} argument on {case['name']}: "
                f"0x{observed:08x} != 0x{fbits(f32(value)):08x}"
            )


def check_state1_case(case: dict, result: dict) -> None:
    y = f32(case["y_124"])
    x = f32(case["x_120"])
    z = f32(case["z_128"])
    divisor = vcvt_s32(f32(case["divisor_34c"]))
    y_positive = y > 0.0
    x_positive = x > 0.0
    numerator = 90 if x_positive else -90

    expected_calls = [("ui_func_002c615c", numerator, divisor)]
    if y_positive:
        step = sdiv_quotient(numerator, divisor)
    else:
        step = sdiv_quotient(numerator, divisor) + numerator

    flags = case["flags"] & 0xFF
    if flags & 1:
        if y_positive:
            second_numerator = -90 if z > 0.0 else 90
            second = sdiv_quotient(second_numerator, divisor)
        elif z > 0.0:
            second_numerator = -90
            second = sdiv_quotient(second_numerator, divisor) - 90
        else:
            second_numerator = 90
            second = sdiv_quotient(second_numerator, divisor) + 90
        expected_calls.append(("ui_func_002c615c", second_numerator, divisor))
        ret = second
    else:
        second = case.get("first_04", -12345)
        ret = flags

    page = result["self_page"]
    heading = struct.unpack_from("<i", page, OFF_HEADING)[0]
    assert heading == step, (
        f"state 1 heading on {case['name']}: {heading} != {step}"
    )
    first = struct.unpack_from("<i", page, OFF_FIRST_ANGLE)[0]
    assert first == second, (
        f"state 1 +0x04 on {case['name']}: {first} != {second}"
    )
    assert signed32(result["ret"]) == ret, (
        f"state 1 return on {case['name']}: {signed32(result['ret'])} != {ret}"
    )
    assert result["call_log"] == expected_calls, (
        f"state 1 calls on {case['name']}:\n  got  {result['call_log']}\n"
        f"  want {expected_calls}"
    )


def check_inert_case(case: dict, result: dict) -> None:
    page = result["self_page"]
    assert result["call_log"] == [], (
        f"state {case['state']} call log on {case['name']}: {result['call_log']}"
    )
    assert signed32(result["ret"]) == case["state"], (
        f"state {case['state']} return on {case['name']}: {signed32(result['ret'])}"
    )
    assert struct.unpack_from("<i", page, OFF_HEADING)[0] == case.get("heading_0c", 0x0BADF00D), (
        f"state {case['state']} wrote +0x0C on {case['name']}"
    )
    assert struct.unpack_from("<i", page, OFF_FIRST_ANGLE)[0] == case.get("first_04", -12345), (
        f"state {case['state']} wrote +0x04 on {case['name']}"
    )


def check_expectations(case: dict, result: dict) -> None:
    if case["state"] == 2:
        check_state2_case(case, result)
    elif case["state"] == 1:
        check_state1_case(case, result)
    else:
        check_inert_case(case, result)


# ----------------------------------------------------------------------- main
def run_case_set(orig_code: bytes, cand_code: bytes, cases: list[dict]) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, case)
        cand = Runner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        check_expectations(case, cand)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing ui_func_00195424 (0x00195424)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"  original: {len(orig_code)} B, candidate: {len(cand_code)} B")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("degree_scale", "turn * 0x168u", "turn * 0x169u"),
        ("source_offset", "LoadF32(self, 0x2D4)", "LoadF32(self, 0x2D8)"),
        ("flag_mask", "(flags & 1u) == 0", "(flags & 2u) == 0"),
        ("second_sign", "> 0.0f ? -90 : 90;", "> 0.0f ? 90 : -90;"),
        ("second_bias", "LoadF32(self, 0x34C))) - 90;",
         "LoadF32(self, 0x34C))) + 90;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant_code, case)
            if compare(orig, bad) or _expectation_fails(case, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


def _expectation_fails(case: dict, result: dict) -> bool:
    try:
        check_expectations(case, result)
    except AssertionError:
        return True
    return False


if __name__ == "__main__":
    main()
