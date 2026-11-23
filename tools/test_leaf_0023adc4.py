#!/usr/bin/env python3
"""Differential test for engine_func_0023adc4 (0x0023adc4) using Unicorn ARM.

Compiles ``src/engine/leaf_batch41_c.cpp``, extracts the
``engine_func_0023adc4`` body (the compiler already places the whole literal
pool inside the symbol, so the body carries no relocations), and runs the
pinned original (``extracted/exefs/code.bin``) against the candidate in
separate Unicorn machines with identical fixtures.

Compared observables per case:
  * continuation PC, final SP, r4-r11 and d8-d15 (the ARM prologue saves
    only r4/r5);
  * the three output floats (raw bits) and the complete 64 KiB work page
    (source, record holders, rect, frame, output and every untouched byte);
  * the complete 512 KiB data window containing 0x00433D98, so a stray write
    to the enemy-draw global or anywhere else is detected;
  * every write outside the private stack must land inside the 12 output
    bytes.  The original stages and overwrites out->x / out->y more often than
    the reconstruction, so only the final contents are contractual.
  * r0 is *not* compared.  It is caller-saved and not a return value; the
    original happens to leave the source pointer there on the ``flag1c == 0``
    tail and the s16 at source+0x18 on the other, but no caller reads it and
    the reconstruction legitimately reuses the register.

Fixture helpers are absent: the function is a leaf with no calls, so there is
no call log and no indirect target to resolve.  ``0x00433D98`` is supplied as
a runtime float word (negative controls move the address to the neighbouring
word).

Coverage: both ``flag1c`` values and every ``flag1d`` combination; the
``first > second`` comparison true / false / equal / NaN / infinity; branch A
wrapping halfword-minus-s32 subtraction, INT_MIN/INT_MAX frame words and
``vcvt.s32.f32`` saturation of the ratio to both 32-bit limits; branch B
zero-extended halfword boundaries 0 / 0x7FFF / 0xFFFF with +/-0.0, huge and
NaN offsets; signed 16-bit rect boundaries; scale 0, +/-0.0, 1, -1, 0.5, 3.5;
positive, negative and zero global y; a -0.0 x result.  Negative controls
mutate the 143.0f bias, 0.5f, 2.0f, the 0.0f staging store, the global
address, the comparison, the halfword shift, the ``flag1d`` guard, the frame
word choice, the per-branch x offset, the saturation limits and the wrapping
extent.
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
OUT_DIR = ROOT / "build/test_leaf_0023adc4"

FUNC_ADDR = 0x0023ADC4
FUNC_SIZE = 456

RODATA_ADDR = 0x003FF000
RODATA_SIZE = 0x0002C000  # ends where the data segment starts
DATA_ADDR = 0x0042B000
DATA_SIZE = 0x00080000  # contains the 0x00433D98 global
RODATA_FILE_OFFSET = 0x002FF000

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000
WORK_ADDR = 0x00500000
WORK_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

GLOBAL_Y = 0x00433D98

SRC = WORK_ADDR + 0x1000
HOLDER4 = WORK_ADDR + 0x2000  # [HOLDER4 + 0x10] = RECT
HOLDER8 = WORK_ADDR + 0x2100  # [HOLDER8 + 0x0C] = FRAME
RECT = WORK_ADDR + 0x3000
FRAME = WORK_ADDR + 0x4000
OUT = WORK_ADDR + 0x5000

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
VFP_SAVED = {
    "d8": arm.UC_ARM_REG_D8,
    "d9": arm.UC_ARM_REG_D9,
    "d10": arm.UC_ARM_REG_D10,
    "d11": arm.UC_ARM_REG_D11,
    "d12": arm.UC_ARM_REG_D12,
    "d13": arm.UC_ARM_REG_D13,
    "d14": arm.UC_ARM_REG_D14,
    "d15": arm.UC_ARM_REG_D15,
}
VFP_SAVED_START = {
    "d8": 0x1122334455667788,
    "d9": 0x2233445566778899,
    "d10": 0x33445566778899AA,
    "d11": 0x445566778899AABB,
    "d12": 0x5566778899AABBCC,
    "d13": 0x66778899AABBCCDD,
    "d14": 0x778899AABBCCDDEE,
    "d15": 0x8899AABBCCDDEEFF,
}
S_SCRATCH_START = {
    "s1": 0x3F800000,
    "s2": 0xBF800000,
    "s3": 0x40000000,
    "s4": 0xC0000000,
    "s5": 0x3F000000,
    "s6": 0xBF000000,
    "s7": 0x40400000,
    "s8": 0xC0400000,
    "s9": 0x40800000,
}

ALLOWED_WRITES = {OUT + 0, OUT + 4, OUT + 8}


# ---------------------------------------------------------------------------
# Float / ARM conversion helpers
# ---------------------------------------------------------------------------
def bits_to_float(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def float_to_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def f32(value: float) -> float:
    """Round a Python double to single precision (RNE)."""
    if value != value or math.isinf(value):
        return value
    return struct.unpack("<f", struct.pack("<f", value))[0]


def fadd(a: float, b: float) -> float:
    return f32(a + b)


def fsub(a: float, b: float) -> float:
    return f32(a - b)


def fmul(a: float, b: float) -> float:
    return f32(a * b)


def s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value & 0x80000000 else value


def arm_vcvt_s32_f32(value: float) -> int:
    """vcvt.s32.f32: truncation toward zero, ARM saturation, NaN -> 0."""
    if value != value:
        return 0
    if math.isinf(value):
        return 0x7FFFFFFF if value > 0 else -0x80000000
    truncated = math.trunc(value)
    if truncated > 0x7FFFFFFF:
        return 0x7FFFFFFF
    if truncated < -0x80000000:
        return -0x80000000
    return truncated


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def extract_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    entry = None
    for name, value in funcs.items():
        if "0023adc4" in name:
            entry = value
            break
    if entry is None:
        raise RuntimeError(
            f"engine_func_0023adc4 not found in {obj_file}: {sorted(funcs)}"
        )
    code, relocs = entry
    if relocs:
        raise RuntimeError(
            "unexpected relocations in engine_func_0023adc4: "
            f"{[(r.relocation_type, r.symbol_name) for r in relocs]}"
        )
    return code


def compile_candidate(src: Path, obj: Path) -> bytes:
    obj.parent.mkdir(parents=True, exist_ok=True)
    result = compile_tu_armv6k(src, obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"compilation failed for {src}:\n{result.stderr}")
    return extract_candidate(obj)


def compile_candidate_baseline() -> bytes:
    return compile_candidate(SOURCE, OUT_DIR / "leaf_batch41_c.o")


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant = OUT_DIR / f"mutant_{name}.cpp"
    mutant.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def build_work(case: dict) -> bytes:
    buffer = bytearray(b"\x5A" * WORK_SIZE)

    def put_u32(base: int, offset: int, value: int) -> None:
        struct.pack_into("<I", buffer, base - WORK_ADDR + offset, value & 0xFFFFFFFF)

    def put_u16(base: int, offset: int, value: int) -> None:
        struct.pack_into("<H", buffer, base - WORK_ADDR + offset, value & 0xFFFF)

    def put_s16(base: int, offset: int, value: int) -> None:
        struct.pack_into("<h", buffer, base - WORK_ADDR + offset, value)

    # Source (r0).
    put_u32(SRC, 0x04, HOLDER4)
    put_u32(SRC, 0x08, HOLDER8)
    put_u32(SRC, 0x10, case["offset10"])
    put_u32(SRC, 0x14, case["offset14"])
    put_s16(SRC, 0x18, case["offset18"])
    put_s16(SRC, 0x1A, case["offset1a"])
    buffer[SRC - WORK_ADDR + 0x1C] = case["flag1c"] & 0xFF
    buffer[SRC - WORK_ADDR + 0x1D] = case["flag1d"] & 0xFF

    # Record holders.
    put_u32(HOLDER4, 0x10, RECT)
    put_u32(HOLDER8, 0x0C, FRAME)

    # Rect record.
    put_s16(RECT, 0x12, case["field12"])
    put_s16(RECT, 0x14, case["field14"])
    put_s16(RECT, 0x16, case["field16"])
    put_s16(RECT, 0x20, case["field20"])
    put_s16(RECT, 0x22, case["field22"])
    put_u16(RECT, 0x24, case["field24"])
    put_u16(RECT, 0x26, case["field26"])

    # Frame record.
    put_u32(FRAME, 0x14, case["frame14"])
    put_u32(FRAME, 0x18, case["frame18"])

    # Output starts as a marker so untouched floats would be visible.
    buffer[OUT - WORK_ADDR:OUT - WORK_ADDR + 12] = b"\xA5" * 12
    return bytes(buffer)


def build_data(case: dict) -> bytes:
    buffer = bytearray(b"\xCC" * DATA_SIZE)
    struct.pack_into(
        "<I", buffer, GLOBAL_Y - DATA_ADDR, case["global_y"] & 0xFFFFFFFF
    )
    return bytes(buffer)


# ---------------------------------------------------------------------------
# Independent model
# ---------------------------------------------------------------------------
def model_run(case: dict) -> dict:
    off10 = bits_to_float(case["offset10"])
    off14 = bits_to_float(case["offset14"])
    scale = bits_to_float(case["scale"])
    global_y = bits_to_float(case["global_y"])

    field12 = case["field12"]
    field14 = case["field14"]
    field16 = case["field16"]
    field20 = case["field20"]
    field22 = case["field22"]
    field24 = case["field24"]
    field26 = case["field26"]

    span = fsub(fadd(f32(float(field14)), 143.0), f32(float(field16)))

    if case["flag1c"] != 0:
        first = f32(float(s32(case["frame14"])))
        second = f32(float(s32(case["frame18"])))
        wrapped = s32((field26 - (case["frame18"] & 0xFFFFFFFF)) & 0xFFFFFFFF)
        extent = fmul(f32(float(wrapped)), 0.5)
        extent = fadd(extent, f32(float(case["offset1a"])))
        extent = fadd(extent, f32(float(field22)))
        extent = fadd(extent, second)
    else:
        first = fadd(f32(float(field24)), fmul(f32(math.fabs(off10)), 2.0))
        second = fadd(f32(float(field26)), fmul(f32(math.fabs(off14)), 2.0))
        extent = f32(float(s32((field22 + field26) & 0xFFFFFFFF)))

    if first > second:
        ratio = arm_vcvt_s32_f32(fmul(fsub(first, second), 0.5))
    else:
        ratio = 0

    y = fadd(0.0, fsub(fsub(span, extent), f32(float(ratio))))
    if case["flag1c"] == 0 and case["flag1d"] == 0:
        y = fadd(y, fmul(off14, 2.0))
    y = fadd(fmul(y, scale), global_y)

    horizontal = s32(
        ((field12 & 0xFFFFFFFF) - ((field20 + (field24 >> 1)) & 0xFFFFFFFF))
        & 0xFFFFFFFF
    )
    x = fsub(0.0, f32(float(horizontal)))
    if case["flag1c"] != 0:
        x = fadd(x, f32(float(case["offset18"])))
    else:
        x = fadd(x, off10)
    x = fmul(x, scale)

    ret = s32(case["offset18"]) if case["flag1c"] != 0 else SRC
    return {
        "out": struct.pack("<III", float_to_bits(x), float_to_bits(y), 0),
        "observed_r0": ret & 0xFFFFFFFF,
    }


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
def write_u32(uc, address: int, value: int) -> None:
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


class Machine:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        with open(ORIG_BIN, "rb") as handle:
            handle.seek(RODATA_FILE_OFFSET)
            self.rodata = handle.read(RODATA_SIZE)
        self.uc.mem_write(RODATA_ADDR, self.rodata)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.writes: list = []

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
            return
        self.writes.append((address, size, value & ((1 << (8 * size)) - 1)))

    def run(self, code: bytes, case: dict) -> dict:
        uc = self.uc
        uc.mem_write(CODE_ADDR, b"\x00" * CODE_SIZE)
        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(DATA_ADDR, build_data(case))
        uc.mem_write(WORK_ADDR, build_work(case))
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        uc.ctl_flush_tb()

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, SRC)
        uc.reg_write(arm.UC_ARM_REG_R1, OUT)
        for name, value in S_SCRATCH_START.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), value)
        uc.reg_write(arm.UC_ARM_REG_S0, case["scale"])
        for name, value in CALLEE_SAVED_START.items():
            uc.reg_write(CALLEE_SAVED[name], value)
        for name, value in VFP_SAVED_START.items():
            uc.reg_write(VFP_SAVED[name], value)

        self.writes = []
        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "vfp_saved": {
                name: uc.reg_read(register)
                for name, register in VFP_SAVED.items()
            },
            "out": bytes(uc.mem_read(OUT, 12)),
            "work": bytes(uc.mem_read(WORK_ADDR, WORK_SIZE)),
            "data": bytes(uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "writes": list(self.writes),
            "global_y": struct.unpack("<I", uc.mem_read(GLOBAL_Y, 4))[0],
        }


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "offset10": float_to_bits(3.5),
        "offset14": float_to_bits(-2.25),
        "offset18": 12,
        "offset1a": -9,
        "flag1c": 0,
        "flag1d": 0,
        "field12": 120,
        "field14": 30,
        "field16": 11,
        "field20": 44,
        "field22": -17,
        "field24": 320,
        "field26": 240,
        "frame14": 0x00010002,
        "frame18": 0x00020003,
        "scale": float_to_bits(1.0),
        "global_y": float_to_bits(0.0),
    }
    case.update(overrides)
    return case


def make_cases() -> list:
    cases: list = []

    # --- branch selection and both flag bytes -----------------------------
    cases.append(base_case("flag1c 0 / flag1d 0"))
    cases.append(base_case("flag1c 0 / flag1d 1", flag1d=1))
    cases.append(base_case("flag1c 1 / flag1d 0", flag1c=1))
    cases.append(base_case("flag1c 1 / flag1d 1", flag1c=1, flag1d=1))
    cases.append(base_case("flag1c 0xFF / flag1d 0xFF", flag1c=0xFF, flag1d=0xFF))

    # --- branch B comparison true / false / equal -------------------------
    cases.append(
        base_case("B first > second", field24=0xFFFF, field26=0,
                  offset10=float_to_bits(0.0), offset14=float_to_bits(0.0))
    )
    cases.append(
        base_case("B first < second", field24=0, field26=0xFFFF,
                  offset10=float_to_bits(0.0), offset14=float_to_bits(0.0))
    )
    cases.append(
        base_case("B first == second", field24=0x7FFF, field26=0x7FFF,
                  offset10=float_to_bits(-0.0), offset14=float_to_bits(0.0))
    )
    cases.append(
        base_case("B equal with offsets", field24=100, field26=40,
                  offset10=float_to_bits(7.5), offset14=float_to_bits(-7.5))
    )
    cases.append(
        base_case("B |offset| sign indifference", field24=0, field26=0,
                  offset10=float_to_bits(-123.25), offset14=float_to_bits(123.25))
    )

    # --- branch B extremes causing saturation -----------------------------
    cases.append(
        base_case("B +inf offset saturates ratio", field24=0xFFFF, field26=0,
                  offset10=float_to_bits(float("inf")),
                  offset14=float_to_bits(0.0))
    )
    cases.append(
        base_case("B -inf offset saturates ratio", field24=0xFFFF, field26=0,
                  offset10=float_to_bits(float("-inf")),
                  offset14=float_to_bits(0.0))
    )
    cases.append(
        base_case("B 1e30 offset saturates ratio", field24=0xFFFF, field26=0,
                  offset10=float_to_bits(1e30), offset14=float_to_bits(0.0))
    )
    cases.append(
        base_case("B NaN offset skips ratio", field24=0xFFFF, field26=0,
                  offset10=float_to_bits(float("nan")),
                  offset14=float_to_bits(0.0))
    )
    cases.append(
        base_case("B equal NaN pair", field24=0, field26=0,
                  offset10=float_to_bits(float("nan")),
                  offset14=float_to_bits(float("nan")))
    )

    # --- branch A: frame words, wrapping subtraction, saturation ----------
    cases.append(
        base_case("A first > second", flag1c=1, frame14=1000, frame18=-1000)
    )
    cases.append(
        base_case("A first < second", flag1c=1, frame14=-1000, frame18=1000)
    )
    cases.append(
        base_case("A first == second", flag1c=1, frame14=77, frame18=77)
    )
    cases.append(
        base_case("A INT_MAX/INT_MIN pair", flag1c=1, frame14=0x7FFFFFFF,
                  frame18=0x80000000, field26=0xFFFF)
    )
    cases.append(
        base_case("A ratio saturates high", flag1c=1, frame14=0x7FFFFFFF,
                  frame18=0x80000000, field26=0, offset1a=0, field22=0)
    )
    cases.append(
        base_case("A wrapped subtraction negative", flag1c=1, frame18=0x7FFFFFFF,
                  frame14=0, field26=0xFFFF)
    )
    cases.append(
        base_case("A wrapped subtraction with frame18 = -1", flag1c=1,
                  frame18=0xFFFFFFFF, frame14=0, field26=0xFFFF)
    )
    cases.append(
        base_case("A extent uses negative s16s", flag1c=1, field22=-32768,
                  field26=0, offset1a=-32768, frame18=0x1234, frame14=0x4321)
    )

    # --- rect signed / halfword boundaries --------------------------------
    for field12, field20, field24 in (
        (-32768, 32767, 0xFFFF),
        (32767, -32768, 0xFFFF),
        (0, 0, 0),
        (0, 0, 1),
        (-1, 0, 0),
        (-1, 0, 1),
        (32767, 32767, 0xFFFF),
    ):
        cases.append(
            base_case(
                f"rect 0x{field12 & 0xFFFF:04x}/0x{field20 & 0xFFFF:04x}/"
                f"0x{field24:04x}",
                field12=field12,
                field20=field20,
                field24=field24,
            )
        )
    cases.append(
        base_case("rect +0x14/+0x16 s16 extremes", field14=-32768, field16=32767)
    )
    cases.append(
        base_case("rect +0x14/+0x16 opposite", field14=32767, field16=-32768)
    )

    # --- output signed-zero and scale -------------------------------------
    cases.append(
        base_case("x -0.0 result", field12=0, field20=0, field24=0,
                  flag1c=0, offset10=float_to_bits(-0.0),
                  scale=float_to_bits(1.0))
    )
    for scale in (0.0, -0.0, 1.0, -1.0, 0.5, 3.5, -7.25):
        cases.append(
            base_case(
                f"scale {scale!r}",
                scale=float_to_bits(scale),
                global_y=float_to_bits(-12.5),
            )
        )
    cases.append(
        base_case("scale inf", scale=float_to_bits(float("inf")),
                  global_y=float_to_bits(0.0))
    )
    cases.append(
        base_case("scale nan", scale=float_to_bits(float("nan")),
                  global_y=float_to_bits(0.0))
    )

    # --- global y ----------------------------------------------------------
    for value in (0.0, 100.5, -3.25, 1e20):
        cases.append(
            base_case(f"global y {value!r}", global_y=float_to_bits(value))
        )
    cases.append(base_case("global y 0x7FC00000", global_y=0x7FC00000))

    # --- branch B offset10 used for x -------------------------------------
    cases.append(
        base_case("B x uses offset10", offset10=float_to_bits(1000.5),
                  field12=-32768, field24=0xFFFF)
    )
    cases.append(
        base_case("A x uses offset18", flag1c=1, offset18=32767,
                  offset1a=-32768, field12=32767, field24=0xFFFF)
    )
    cases.append(
        base_case("combined wrap and flags", flag1c=0, flag1d=0,
                  offset10=float_to_bits(-0.0), offset14=float_to_bits(-0.0),
                  field12=-32768, field20=32767, field22=32767,
                  field24=0xFFFF, field26=0, scale=float_to_bits(-0.0),
                  global_y=float_to_bits(-0.0))
    )
    return cases


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------
def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("pc", "sp", "callee_saved", "vfp_saved", "out", "global_y"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for key in ("work", "data"):
        if orig[key] != cand[key]:
            for index in range(0, len(orig[key]), 4):
                if orig[key][index:index + 4] != cand[key][index:index + 4]:
                    base = WORK_ADDR if key == "work" else DATA_ADDR
                    problems.append(
                        f"{key} differs first at 0x{base + index:08x}: "
                        f"orig={orig[key][index:index + 4].hex()} "
                        f"cand={cand[key][index:index + 4].hex()}"
                    )
                    break
    return problems


def check_result(case: dict, result: dict, model: dict) -> None:
    name = case["name"]
    assert result["pc"] == TRAP_ADDR, f"did not return on {name}"
    assert result["sp"] == ENTRY_SP, f"SP not restored on {name}"
    assert result["callee_saved"] == CALLEE_SAVED_START, (
        f"callee-saved registers clobbered on {name}: {result['callee_saved']}"
    )
    assert result["vfp_saved"] == VFP_SAVED_START, (
        f"VFP callee-saved registers clobbered on {name}: {result['vfp_saved']}"
    )
    assert result["out"] == model["out"], (
        f"output differs from model on {name}:\n"
        f"    actual={result['out'].hex()}\n    model={model['out'].hex()}"
    )
    for write in result["writes"]:
        assert write[0] in ALLOWED_WRITES, (
            f"write outside the output floats on {name}: 0x{write[0]:08x}"
        )


def run_case_set(orig_code, cand_code, cases, orig_machine, cand_machine) -> int:
    passed = 0
    for case in cases:
        orig = orig_machine.run(orig_code, case)
        cand = cand_machine.run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        model = model_run(case)
        check_result(case, orig, model)
        check_result(case, cand, model)
        passed += 1
        print(f"  [PASS] {case['name']}")
    return passed


def main() -> None:
    print("Testing engine_func_0023adc4 (0x0023adc4)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"  original: {len(orig_code)} B, candidate: {len(cand_code)} B "
        "(no relocations)"
    )

    cases = make_cases()
    orig_machine = Machine()
    cand_machine = Machine()
    passed = run_case_set(orig_code, cand_code, cases, orig_machine, cand_machine)

    print("\nNegative controls:")
    for name, old, new in (
        ("vertical_bias", "constexpr f32 kVerticalBias = 143.0f;",
         "constexpr f32 kVerticalBias = 142.0f;"),
        ("half", "constexpr f32 kHalf = 0.5f;          // literal 0x3F000000 at 0x0023AF78",
         "constexpr f32 kHalf = 0.25f;         // literal 0x3F000000 at 0x0023AF78"),
        ("two", "constexpr f32 kTwo = 2.0f;           // literal 0x40000000 at 0x0023AF7C",
         "constexpr f32 kTwo = 3.0f;           // literal 0x40000000 at 0x0023AF7C"),
        ("zero", "constexpr f32 kZero = 0.0f;          // literal 0x00000000 at 0x0023AF84",
         "constexpr f32 kZero = 1.0f;          // literal 0x00000000 at 0x0023AF84"),
        ("global_address", "constexpr u32 kEnemyDrawGlobal = 0x00433D98u;",
         "constexpr u32 kEnemyDrawGlobal = 0x00433D94u;"),
        ("comparison", "if (first > second) {", "if (first < second) {"),
        ("halfword_shift", "(static_cast<u32>(rect->field24) >> 1)",
         "(static_cast<u32>(rect->field24) >> 2)"),
        ("flag1d_guard",
         "if (source->flag1c == 0u && source->flag1d == 0u) {",
         "if (source->flag1c == 0u) {"),
        ("frame_word_swap", "first = static_cast<f32>(frame->field14);",
         "first = static_cast<f32>(frame->field18);"),
        ("x_offset_branch", "x = x + static_cast<f32>(source->offset18);",
         "x = x + static_cast<f32>(source->offset1a);"),
        ("saturation_high", "        return 0x7FFFFFFF;", "        return 0;"),
        ("extent_scale", "f32 sum = static_cast<f32>(wrapped) * kHalf;",
         "f32 sum = static_cast<f32>(wrapped) * kTwo;"),
        ("staged_zero", "    out->z = kZero;\n", "    out->z = kHalf;\n"),
    ):
        try:
            mutant_code = compile_candidate_mutant(name, old, new)
        except RuntimeError as error:
            raise SystemExit(f"negative control failed to build: {error}")
        detected = False
        reason = ""
        for case in cases:
            good = orig_machine.run(orig_code, case)
            bad = cand_machine.run(mutant_code, case)
            if compare(good, bad):
                detected = True
                reason = f" ({case['name']})"
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected{reason}")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
