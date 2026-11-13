#!/usr/bin/env python3
"""Differential test for func_003d58c4 (0x003D58C4) using Unicorn ARM.

The routine is the "interpolation update" half of a larger scene/UI object.  It
reads a gate flag at ``self+0x634`` (bit 20), asks 0x00227414 five times for a
fraction ``value / self->denominator_680``, and writes ten single-precision
fields with ``base + (target - base) * fraction`` (VFP ``vsub`` + ``vmla``).
The original then tail-branches to 0x003D74C4(self, value).

The runner compiles ``src/engine/leaf_batch41_c.cpp``, extracts
``func_003d58c4``, resolves its five R_ARM_CALL and one R_ARM_JUMP24
relocations to deterministic stubs at the original targets, and runs the pinned
original (``extracted/exefs/code.bin``) against the candidate in separate
Unicorn machines with identical fixtures.

Compared per case:
  * continuation PC, final SP, callee-saved r4-r11 and s16-s31;
  * the ordered call log: 0x00227414 mode/denominator/value/return bits and the
    0x003D74C4 (self, value) tail-call arguments;
  * every emulated write outside the private stack (sorted by address; the
    original and the compiler are free to schedule non-aliasing stores in a
    different order);
  * the complete ``self`` page and the complete BSS float page, including every
    byte the routine must not touch.

Coverage:
  * gate flag: 0, 0x000FFFFF, 0x100000, 0x200000, 0x00080000, 0x80100000,
    0xFFFFFFFF;
  * denominator: 1, 2, 3, 4, 8, 1000000, -1, -2, 0, INT_MIN;
  * value: 0, +-1, +-7, INT_MAX, INT_MIN, value == denominator (t = 1.0);
  * floating-point tracks: zeros, negative zeros, mixed signs, very large and
    very small finite values, denormals, infinities, quiet/signalling NaNs and
    max finite values;
  * helper rewrites between calls: the denominator is re-read before each of the
    five calls, the +0x62C base is re-read after the call that computes its
    delta, and the BSS track is re-read after the first call.

An independent expected model validates both the original and the candidate:
ordered call log, the exact set of written fields, all untouched bytes and the
non-fused (two-rounding) VFP arithmetic.  Cases whose arithmetic must produce a
NaN or infinity skip only the expensive per-field float comparison and remain
fully differential.

Negative controls recompile mutated source (gate mask/polarity, BSS addresses,
lerp direction, dropped/scaled stores, wrong scalar base, fifth-call mode and a
shifted struct offset); every mutant must be detected.

``r0`` at return is not compared: the function is ``void`` and the only static
caller (0x003D787C) ignores the result.
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
OUT_DIR = ROOT / "build/test_leaf_003d58c4"

FUNC_NAME = "func_003d58c4"
FUNC_ADDR = 0x003D58C4
FUNC_SIZE = 408

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000          # target plus both direct-call stubs
SELF_ADDR = 0x00500000
SELF_SIZE = 0x00001000
BSS_ADDR = 0x00493000
BSS_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
SENTINEL = 0xCDCDCDCD

STUB_227414 = 0x00227414
STUB_3D74C4 = 0x003D74C4
STUB_BY_SYMBOL = {
    "ui_func_00227414": STUB_227414,
    "func_003d74c4": STUB_3D74C4,
}

# --- "self" field offsets recovered from the ARM listing -------------------
OFF_FROM_5AC = 0x5AC            # three lanes, targets of the first vector lerp
OFF_TO_5DC = 0x5DC              # scalar target -> +0x698
OFF_TO_5E8 = 0x5E8              # scalar target -> +0x5A4
OFF_TO_5EC = 0x5EC              # scalar target -> +0x6A8
OFF_BASE_5F0 = 0x5F0            # three lanes, base of the first vector lerp
OFF_BASE_620 = 0x620            # scalar base -> +0x698
OFF_BASE_62C = 0x62C            # scalar base -> +0x5A4
OFF_BASE_630 = 0x630            # scalar base -> +0x6A8
OFF_FLAGS = 0x634               # gate word, bit 20
OFF_OUT_658 = 0x658             # BSS scalar result
OFF_DENOM = 0x680               # signed denominator, re-read per call
OFF_OUT_698 = 0x698
OFF_OUT_6A8 = 0x6A8
OFF_OUT_6CC = 0x6CC
OFF_OUT_6D0 = 0x6D0
OFF_OUT_6D4 = 0x6D4
OFF_OUT_6E4 = 0x6E4
OFF_OUT_6E8 = 0x6E8
OFF_OUT_6EC = 0x6EC

OFF_OUT_5A4 = 0x5A4
OUTPUT_OFFSETS = (
    OFF_OUT_5A4,
    OFF_OUT_658,
    OFF_OUT_698,
    OFF_OUT_6A8,
    OFF_OUT_6CC,
    OFF_OUT_6D0,
    OFF_OUT_6D4,
    OFF_OUT_6E4,
    OFF_OUT_6E8,
    OFF_OUT_6EC,
)

GATE_FLAG = 0x100000

# --- BSS float addresses ---------------------------------------------------
TRACK_A_FROM = 0x00493518        # literal 0x00493524 minus 0xC
TRACK_A_TO = 0x00493524          # literal at 0x003D5A54
TRACK_B_FROM = 0x00493530        # literal 0x0049353C minus 0xC
TRACK_B_TO = 0x0049353C          # literal at 0x003D5A58

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


# ---------------------------------------------------------------------------
# Float helpers.  Every operation rounds to binary32, matching VFP when VMLA
# is expanded as VMUL + VADD (Unicorn's VMLA is non-fused; verified separately).
# ---------------------------------------------------------------------------
F32_INFINITY_THRESHOLD = 2.0 ** 128 - 2.0 ** 103


def f32_bits(value: float) -> int:
    if value == value and abs(value) >= F32_INFINITY_THRESHOLD:
        return 0xFF800000 if value < 0 else 0x7F800000
    return struct.unpack("<I", struct.pack("<f", value))[0]


def bits_f32(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def is_special(bits: int) -> bool:
    return (bits & 0x7F800000) == 0x7F800000


def vsub_bits(minuend: int, subtrahend: int) -> int:
    return f32_bits(bits_f32(minuend) - bits_f32(subtrahend))


def lerp_bits(base: int, target: int, fraction: int) -> int:
    """base + (target - base) * fraction, as VSUB + non-fused VMLA."""
    delta = vsub_bits(target, base)
    product = f32_bits(bits_f32(delta) * bits_f32(fraction))
    return f32_bits(bits_f32(product) + bits_f32(base))


def helper_fraction_bits(denominator: int, value: int) -> int:
    """0x00227414 mode 0: +0.0f for a zero denominator, else value / denom."""
    denominator = s32(denominator)
    value = s32(value)
    if denominator == 0:
        return 0x00000000
    numerator_f32 = bits_f32(f32_bits(float(value)))
    denominator_f32 = bits_f32(f32_bits(float(denominator)))
    return f32_bits(numerator_f32 / denominator_f32)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def make_case(name: str, *, flags: int = 0, denominator: int = 2,
              value: int = 1, track_a_from: int = 0x40000000,
              track_a_to: int = 0x40800000,
              track_b_from: tuple = (0xBF800000, 0x3F800000, 0x00000000),
              track_b_to: tuple = (0x40200000, 0xC0200000, 0x40400000),
              from_5ac: tuple = (0x3F800000, 0x40000000, 0x40400000),
              base_5f0: tuple = (0x40800000, 0x41000000, 0x41800000),
              to_5dc: int = 0x41000000, base_620: int = 0x40000000,
              to_5e8: int = 0x41800000, base_62c: int = 0x40800000,
              to_5ec: int = 0xC1800000, base_630: int = 0xC0800000,
              rewrite: dict | None = None) -> dict:
    return {
        "name": name,
        "flags": flags & 0xFFFFFFFF,
        "denominator": s32(denominator),
        "value": s32(value),
        "track_a_from": track_a_from,
        "track_a_to": track_a_to,
        "track_b_from": tuple(track_b_from),
        "track_b_to": tuple(track_b_to),
        "from_5ac": tuple(from_5ac),
        "base_5f0": tuple(base_5f0),
        "to_5dc": to_5dc,
        "base_620": base_620,
        "to_5e8": to_5e8,
        "base_62c": base_62c,
        "to_5ec": to_5ec,
        "base_630": base_630,
        "rewrite": rewrite,
    }


def build_self_page(case: dict) -> bytearray:
    page = bytearray(b"\x5A" * SELF_SIZE)
    struct.pack_into("<I", page, OFF_FLAGS, case["flags"])
    struct.pack_into("<i", page, OFF_DENOM, case["denominator"])
    for index, bits in enumerate(case["from_5ac"]):
        struct.pack_into("<I", page, OFF_FROM_5AC + 4 * index, bits)
    for index, bits in enumerate(case["base_5f0"]):
        struct.pack_into("<I", page, OFF_BASE_5F0 + 4 * index, bits)
    struct.pack_into("<I", page, OFF_TO_5DC, case["to_5dc"])
    struct.pack_into("<I", page, OFF_BASE_620, case["base_620"])
    struct.pack_into("<I", page, OFF_TO_5E8, case["to_5e8"])
    struct.pack_into("<I", page, OFF_BASE_62C, case["base_62c"])
    struct.pack_into("<I", page, OFF_TO_5EC, case["to_5ec"])
    struct.pack_into("<I", page, OFF_BASE_630, case["base_630"])
    for offset in OUTPUT_OFFSETS:
        struct.pack_into("<I", page, offset, SENTINEL)
    return page


def build_bss_page(case: dict) -> bytearray:
    page = bytearray(b"\x33" * BSS_SIZE)
    struct.pack_into("<I", page, TRACK_A_FROM - BSS_ADDR, case["track_a_from"])
    struct.pack_into("<I", page, TRACK_A_TO - BSS_ADDR, case["track_a_to"])
    for index, bits in enumerate(case["track_b_from"]):
        struct.pack_into("<I", page, TRACK_B_FROM - BSS_ADDR + 4 * index, bits)
    for index, bits in enumerate(case["track_b_to"]):
        struct.pack_into("<I", page, TRACK_B_TO - BSS_ADDR + 4 * index, bits)
    return page


# ---------------------------------------------------------------------------
# Independent expected model
# ---------------------------------------------------------------------------
def expected_run(case: dict) -> tuple:
    """Return (call log, expected self page, expected BSS page)."""
    page = build_self_page(case)
    bss = build_bss_page(case)
    log: list = []
    calls = 0
    rewrite = case.get("rewrite")

    def read_u32(offset: int) -> int:
        return struct.unpack_from("<I", page, offset)[0]

    def read_s32(offset: int) -> int:
        return struct.unpack_from("<i", page, offset)[0]

    def write_bits(offset: int, bits: int) -> None:
        struct.pack_into("<I", page, offset, bits & 0xFFFFFFFF)

    def call_fraction() -> int:
        nonlocal calls
        calls += 1
        denominator = read_s32(OFF_DENOM)
        value = case["value"]
        result = helper_fraction_bits(denominator, value)
        log.append(("ui_func_00227414", 0, denominator, value, result))
        if rewrite is not None and calls == rewrite["call"]:
            if rewrite["kind"] == "denominator":
                write_bits(OFF_DENOM, rewrite["bits"])
            elif rewrite["kind"] == "base_62c":
                write_bits(OFF_BASE_62C, rewrite["bits"])
            elif rewrite["kind"] == "track_a":
                struct.pack_into("<I", bss, TRACK_A_FROM - BSS_ADDR,
                                 rewrite["bits"] & 0xFFFFFFFF)
            else:
                raise AssertionError(f"unknown rewrite {rewrite!r}")
        return result

    if (read_u32(OFF_FLAGS) & GATE_FLAG) == 0:
        fraction_0 = call_fraction()

        # BSS scalar track A.
        write_bits(OFF_OUT_658, lerp_bits(read_u32_from(bss, TRACK_A_FROM),
                                          read_u32_from(bss, TRACK_A_TO),
                                          fraction_0))

        # +0x5AC toward +0x5F0.
        for lane in range(3):
            write_bits(OFF_OUT_6CC + 4 * lane,
                       lerp_bits(read_u32(OFF_BASE_5F0 + 4 * lane),
                                 read_u32(OFF_FROM_5AC + 4 * lane),
                                 fraction_0))

        # BSS three-lane track B.
        for lane in range(3):
            write_bits(OFF_OUT_6E4 + 4 * lane,
                       lerp_bits(read_u32_from(bss, TRACK_B_FROM + 4 * lane),
                                 read_u32_from(bss, TRACK_B_TO + 4 * lane),
                                 fraction_0))

        # +0x5E8 toward +0x62C: delta uses the pre-call base, the result uses
        # the post-call reload of the same field.
        delta = vsub_bits(read_u32(OFF_TO_5E8), read_u32(OFF_BASE_62C))
        fraction = call_fraction()
        product = f32_bits(bits_f32(delta) * bits_f32(fraction))
        write_bits(OFF_OUT_5A4,
                   f32_bits(bits_f32(product) + bits_f32(read_u32(OFF_BASE_62C))))

        # +0x5EC toward +0x630.
        delta = vsub_bits(read_u32(OFF_TO_5EC), read_u32(OFF_BASE_630))
        fraction = call_fraction()
        product = f32_bits(bits_f32(delta) * bits_f32(fraction))
        write_bits(OFF_OUT_6A8,
                   f32_bits(bits_f32(product) + bits_f32(read_u32(OFF_BASE_630))))

        # +0x5DC toward +0x620.
        delta = vsub_bits(read_u32(OFF_TO_5DC), read_u32(OFF_BASE_620))
        fraction = call_fraction()
        product = f32_bits(bits_f32(delta) * bits_f32(fraction))
        write_bits(OFF_OUT_698,
                   f32_bits(bits_f32(product) + bits_f32(read_u32(OFF_BASE_620))))

        # Fifth fraction, result discarded.
        call_fraction()

        log.append(("func_003d74c4", SELF_ADDR, case["value"]))

    return log, page, bss


def read_u32_from(page: bytearray, address: int) -> int:
    return struct.unpack_from("<I", page, address - BSS_ADDR)[0]


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def sign_extend_24(value: int) -> int:
    return value - 0x1000000 if value & 0x800000 else value


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    entry = funcs.get(FUNC_NAME)
    if entry is None:
        raise RuntimeError(
            f"{FUNC_NAME} not found in {obj_file}: {sorted(funcs)}"
        )

    raw, relocs = entry
    code = bytearray(raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = STUB_BY_SYMBOL.get(rel.symbol_name)
            if target is None:
                raise RuntimeError(f"unexpected call relocation: {rel}")
            instruction = struct.unpack_from("<I", code, rel.offset)[0]
            addend = sign_extend_24(instruction & 0x00FFFFFF) << 2
            place = FUNC_ADDR + rel.offset
            displacement = (target + addend - place) >> 2
            struct.pack_into(
                "<I", code, rel.offset,
                (instruction & 0xFF000000) | (displacement & 0x00FFFFFF),
            )
        else:
            raise RuntimeError(f"unsupported relocation: {rel}")
    return bytes(code)


def compile_variant(src_file: Path, obj_file: Path) -> bytes:
    result = compile_tu_armv6k(src_file, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed for {src_file}: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return compile_variant(SOURCE, OUT_DIR / "leaf_batch41_c.o")


def compile_mutant(name: str, old: str, new: str, count: int = 1) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != count:
        raise RuntimeError(
            f"mutation anchor {old!r} occurs {text.count(old)} times, "
            f"expected {count}"
        )
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_variant(mutant_src, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
class Machine:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (SELF_ADDR, SELF_SIZE),
            (BSS_ADDR, BSS_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)

        self.orig_code = get_orig_bytes()
        self.call_log: list = []
        self.writes: list = []
        self.helper_calls = 0
        self.case: dict = {}

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for address, hook in (
            (STUB_227414, self._on_227414),
            (STUB_3D74C4, self._on_3d74c4),
        ):
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, hook, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value & ((1 << (8 * size)) - 1)))

    def _on_227414(self, uc, address, size, user_data) -> None:
        mode = uc.reg_read(arm.UC_ARM_REG_R0) & 0xFFFFFFFF
        denominator = s32(uc.reg_read(arm.UC_ARM_REG_R1))
        value = s32(uc.reg_read(arm.UC_ARM_REG_R2))
        if mode == 0:
            result = helper_fraction_bits(denominator, value)
        elif mode == 1:
            # Never selected by 0x003D58C4; kept deterministic so a mutated
            # candidate that changes the mode fails through the call log.
            result = 0x3F800000
        else:
            result = 0x00000000
        self.call_log.append(
            ("ui_func_00227414", mode, denominator, value, result)
        )
        uc.reg_write(arm.UC_ARM_REG_S0, result)

        self.helper_calls += 1
        rewrite = self.case.get("rewrite")
        if rewrite is not None and self.helper_calls == rewrite["call"]:
            kind = rewrite["kind"]
            if kind == "denominator":
                uc.mem_write(SELF_ADDR + OFF_DENOM,
                             struct.pack("<I", rewrite["bits"]))
            elif kind == "base_62c":
                uc.mem_write(SELF_ADDR + OFF_BASE_62C,
                             struct.pack("<I", rewrite["bits"]))
            elif kind == "track_a":
                uc.mem_write(TRACK_A_FROM,
                             struct.pack("<I", rewrite["bits"]))
            else:
                raise AssertionError(f"unknown rewrite {rewrite!r}")

    def _on_3d74c4(self, uc, address, size, user_data) -> None:
        self.call_log.append(
            ("func_003d74c4",
             uc.reg_read(arm.UC_ARM_REG_R0) & 0xFFFFFFFF,
             s32(uc.reg_read(arm.UC_ARM_REG_R1)))
        )

    def run(self, candidate: bytes | None, case: dict) -> dict:
        uc = self.uc
        self.case = case
        self.call_log = []
        self.helper_calls = 0

        uc.mem_write(FUNC_ADDR, self.orig_code if candidate is None else candidate)
        uc.mem_write(SELF_ADDR, bytes(build_self_page(case)))
        uc.mem_write(BSS_ADDR, bytes(build_bss_page(case)))
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []
        uc.ctl_flush_tb()

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R1, case["value"] & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R2, 0x33333333)
        uc.reg_write(arm.UC_ARM_REG_R3, 0x44444444)
        for name, register in CALLEE_SAVED.items():
            uc.reg_write(register, CALLEE_SAVED_START[name])
        for index in range(32):
            uc.reg_write(getattr(arm, f"UC_ARM_REG_S{index}"),
                         0x3F000000 + index)

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError as error:
            pc = uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "call_log": list(self.call_log),
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "callee_saved_vfp": [
                uc.reg_read(getattr(arm, f"UC_ARM_REG_S{index}"))
                for index in range(16, 32)
            ],
            "writes": sorted(
                write for write in self.writes
                if not STACK_ADDR <= write[0] < STACK_ADDR + STACK_SIZE
            ),
            "self": bytes(uc.mem_read(SELF_ADDR, SELF_SIZE)),
            "bss": bytes(uc.mem_read(BSS_ADDR, BSS_SIZE)),
        }


# ---------------------------------------------------------------------------
# Case table
# ---------------------------------------------------------------------------
def build_cases() -> list[dict]:
    return [
        # -- gate flag ------------------------------------------------------
        make_case("gate clear", flags=0),
        make_case("gate 0x000FFFFF", flags=0x000FFFFF),
        make_case("gate 0x00080000", flags=0x00080000),
        make_case("gate 0x200000", flags=0x200000),
        make_case("gate 0x100000", flags=0x100000),
        make_case("gate 0x80100000", flags=0x80100000),
        make_case("gate 0xFFFFFFFF", flags=0xFFFFFFFF),
        make_case("gate single low bit", flags=0x00000001),

        # -- denominator / value boundaries ---------------------------------
        make_case("den=1 value=0", denominator=1, value=0),
        make_case("den=1 value=1", denominator=1, value=1),
        make_case("den=2 value=1", denominator=2, value=1),
        make_case("den=4 value=3", denominator=4, value=3),
        make_case("den=3 value=2", denominator=3, value=2),
        make_case("den=8 value=7", denominator=8, value=7),
        make_case("den=8 value=-7", denominator=8, value=-7),
        make_case("den=1000000 value=-1000000",
                  denominator=1000000, value=-1000000),
        make_case("den=0 value=5", denominator=0, value=5),
        make_case("den=0 value=-5", denominator=0, value=-5),
        make_case("den=-2 value=1", denominator=-2, value=1),
        make_case("den=2 value=-1", denominator=2, value=-1),
        make_case("den=INT_MIN value=INT_MAX",
                  denominator=-0x80000000, value=0x7FFFFFFF),
        make_case("den=-1 value=INT_MIN",
                  denominator=-1, value=-0x80000000),
        make_case("den=INT_MIN value=INT_MIN",
                  denominator=-0x80000000, value=-0x80000000),
        make_case("fraction exactly one", denominator=4, value=4),
        make_case("fraction negative one", denominator=4, value=-4),

        # -- self tracks ----------------------------------------------------
        make_case("self tracks zero",
                  from_5ac=(0, 0, 0), base_5f0=(0, 0, 0),
                  to_5dc=0, base_620=0, to_5e8=0, base_62c=0,
                  to_5ec=0, base_630=0),
        make_case("self tracks negative",
                  from_5ac=(0xC0000000, 0xBF800000, 0xC0800000),
                  base_5f0=(0x3F800000, 0x40000000, 0x40400000),
                  to_5dc=0xC0A00000, base_620=0x41200000,
                  to_5e8=0xC1200000, base_62c=0x41A00000,
                  to_5ec=0x41800000, base_630=0xC1880000),
        make_case("self tracks tiny",
                  from_5ac=(0x00000001, 0x80000001, 0x007FFFFF),
                  base_5f0=(0x00000002, 0x80000002, 0x00800000),
                  to_5dc=0x00000003, base_620=0x80000003,
                  to_5e8=0x007FFFFE, base_62c=0x807FFFFE,
                  to_5ec=0x00000004, base_630=0x80000004),
        make_case("self tracks huge",
                  from_5ac=(0x7F7FFFFF, 0xFF7FFFFF, 0x7F000000),
                  base_5f0=(0xFF7FFFFF, 0x7F7FFFFF, 0xFF000000),
                  to_5dc=0x7F7FFFFF, base_620=0xFF7FFFFF,
                  to_5e8=0x7F000000, base_62c=0xFF000000,
                  to_5ec=0xFF7FFFFF, base_630=0x7F7FFFFF),
        make_case("signed zeros",
                  from_5ac=(0x80000000, 0, 0x80000000),
                  base_5f0=(0, 0x80000000, 0),
                  to_5dc=0x80000000, base_620=0,
                  to_5e8=0, base_62c=0x80000000,
                  to_5ec=0x80000000, base_630=0),

        # -- BSS tracks -----------------------------------------------------
        make_case("bss tracks zero",
                  track_a_from=0, track_a_to=0,
                  track_b_from=(0, 0, 0), track_b_to=(0, 0, 0)),
        make_case("bss tracks negative",
                  track_a_from=0xC2C80000, track_a_to=0x42C80000,
                  track_b_from=(0xC0000000, 0xBF800000, 0x80000000),
                  track_b_to=(0x40000000, 0x3F800000, 0)),
        make_case("bss tracks special",
                  track_a_from=0x7F800000, track_a_to=0xFF800000,
                  track_b_from=(0x7FC00001, 0xFFC00002, 0x7F800001),
                  track_b_to=(0xFF800002, 0x7FC00003, 0xFFC00004)),

        # -- special self values -------------------------------------------
        make_case("self infinities",
                  from_5ac=(0x7F800000, 0xFF800000, 0x7F800000),
                  base_5f0=(0xFF800000, 0x7F800000, 0xFF800000),
                  to_5dc=0x7F800000, base_620=0xFF800000,
                  to_5e8=0xFF800000, base_62c=0x7F800000,
                  to_5ec=0x7F800000, base_630=0xFF800000),
        make_case("self NaN payloads",
                  from_5ac=(0x7FC00001, 0xFFC00002, 0x7F800001),
                  base_5f0=(0x7FC00003, 0xFFC00004, 0x7FC00005),
                  to_5dc=0x7FC00006, base_620=0xFFC00007,
                  to_5e8=0x7FC00008, base_62c=0xFFC00009,
                  to_5ec=0x7FC0000A, base_630=0xFFC0000B),

        # -- helper rewrites between calls ---------------------------------
        make_case("denominator rewritten on call 2",
                  denominator=2, value=3,
                  rewrite={"kind": "denominator", "call": 2,
                           "bits": 0x40800000}),  # 4.0f
        make_case("denominator rewritten on call 1",
                  denominator=2, value=3,
                  rewrite={"kind": "denominator", "call": 1,
                           "bits": 0xC0000000}),  # -2.0f
        make_case("base 0x62C rewritten on call 2",
                  denominator=4, value=3,
                  rewrite={"kind": "base_62c", "call": 2,
                           "bits": 0x42C80000}),  # 100.0f
        make_case("BSS track A rewritten on call 1",
                  track_a_from=0x40000000, track_a_to=0x40800000,
                  rewrite={"kind": "track_a", "call": 1,
                           "bits": 0xC1200000}),  # -10.0f
    ]


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------
def check_expected(case: dict, result: dict) -> None:
    log, page, bss = expected_run(case)
    assert result["call_log"] == log, (
        f"expected call log mismatch on {case['name']}:\n"
        f"  Expected: {log}\n  Actual:   {result['call_log']}"
    )
    if case_outputs_are_nan_free(case):
        if result["self"] != bytes(page):
            differing = [
                offset for offset in range(SELF_SIZE)
                if result["self"][offset] != bytes(page)[offset]
            ]
            raise AssertionError(
                f"self page mismatch on {case['name']} at "
                f"{[hex(offset) for offset in differing[:16]]}"
            )
    else:
        # The expected model cannot reproduce ARM's NaN-payload selection, so
        # only the untouched bytes are compared for NaN/infinity fixtures.
        # The original-vs-candidate comparison still covers every output bit.
        for offset in range(SELF_SIZE):
            if any(base <= offset < base + 4 for base in OUTPUT_OFFSETS):
                continue
            assert result["self"][offset] == bytes(page)[offset], (
                f"self byte 0x{offset:x} mismatch on {case['name']}"
            )
    assert result["bss"] == bytes(bss), (
        f"BSS page mismatch on {case['name']}"
    )


def case_outputs_are_nan_free(case: dict) -> bool:
    values = [
        case["track_a_from"], case["track_a_to"],
        case["to_5dc"], case["base_620"],
        case["to_5e8"], case["base_62c"],
        case["to_5ec"], case["base_630"],
    ]
    values += list(case["track_b_from"]) + list(case["track_b_to"])
    values += list(case["from_5ac"]) + list(case["base_5f0"])
    return not any(is_special(bits) for bits in values)


def compare(orig: dict, cand: dict, name: str) -> None:
    for key in ("pc", "sp", "callee_saved", "callee_saved_vfp",
                "call_log", "writes", "self", "bss"):
        assert orig[key] == cand[key], (
            f"{key} mismatch on {name}:\n"
            f"  Orig: {orig[key]!r}\n  Cand: {cand[key]!r}"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def safe_run(machine: Machine, candidate: bytes, case: dict):
    try:
        return machine.run(candidate, case)
    except RuntimeError as error:
        return ("crash", str(error))


def main() -> None:
    print("Testing func_003d58c4 (0x003d58c4)...")
    candidate = compile_candidate()
    print(f"  original: {FUNC_SIZE} B, candidate: {len(candidate)} B")

    cases = build_cases()
    machine = Machine()
    passed = 0
    for case in cases:
        res_orig = machine.run(None, case)
        res_cand = machine.run(candidate, case)
        compare(res_orig, res_cand, case["name"])
        check_expected(case, res_orig)
        check_expected(case, res_cand)
        assert res_orig["pc"] == TRAP_ADDR, (
            f"original did not stop at trap on {case['name']}"
        )
        assert res_cand["pc"] == TRAP_ADDR, (
            f"candidate did not stop at trap on {case['name']}"
        )
        assert res_orig["sp"] == res_cand["sp"] == ENTRY_SP, (
            f"SP mismatch on {case['name']}"
        )
        passed += 1
        print(f"  [PASS] {case['name']}  "
              f"({len(res_orig['call_log'])} calls, "
              f"{len(res_orig['writes'])} stores)")

    print("\nNegative controls:")
    mutants = [
        (
            "gate_mask",
            "constexpr u32 kUpdateBlockedFlag = 0x100000;",
            "constexpr u32 kUpdateBlockedFlag = 0x200000;",
            1,
        ),
        (
            "gate_polarity",
            "if ((self->flags_634 & kUpdateBlockedFlag) != 0) {",
            "if ((self->flags_634 & kUpdateBlockedFlag) == 0) {",
            1,
        ),
        (
            "track_a_from_address",
            "constexpr u32 kTrackAScalarFrom = 0x00493518;",
            "constexpr u32 kTrackAScalarFrom = 0x0049351C;",
            1,
        ),
        (
            "track_b_to_address",
            "constexpr u32 kTrackBVectorTo = 0x0049353C;",
            "constexpr u32 kTrackBVectorTo = 0x00493540;",
            1,
        ),
        (
            "vector_direction",
            "vmla_f32(self->base_5f0[0], self->from_5ac[0] - self->base_5f0[0], t0);",
            "vmla_f32(self->from_5ac[0], self->base_5f0[0] - self->from_5ac[0], t0);",
            1,
        ),
        (
            "scalar_gain",
            "self->out_698 = vmla_f32(self->base_620, delta, t);",
            "self->out_698 = self->base_620 + delta;",
            1,
        ),
        (
            "scalar_base",
            "self->out_6a8 = vmla_f32(self->base_630, delta, t);",
            "self->out_6a8 = vmla_f32(self->base_620, delta, t);",
            1,
        ),
        (
            "fifth_call_mode",
            "// 0x003D5A30..0x003D5A34: fifth fraction; the result is discarded.\n"
            "    ui_func_00227414(0, self->denominator_680, value);",
            "// 0x003D5A30..0x003D5A34: fifth fraction; the result is discarded.\n"
            "    ui_func_00227414(1, self->denominator_680, value);",
            1,
        ),
        (
            "track_a_base_value",
            "self->out_658 = vmla_f32(track_a_from, track_a_to - track_a_from, t0);",
            "self->out_658 = vmla_f32(track_a_to, track_a_to - track_a_from, t0);",
            1,
        ),
        (
            "dropped_bss_lane",
            "self->out_6e8 = vmla_f32(track_b_from_y, track_b_to_y - track_b_from_y, t0);",
            "self->out_6e8 = track_b_from_y;",
            1,
        ),
        (
            "vmla_to_vmls",
            '__asm__("vmla.f32 %0, %1, %2"',
            '__asm__("vmls.f32 %0, %1, %2"',
            1,
        ),
        (
            "denominator_offset",
            "u8 pad_65c[0x24];",
            "u8 pad_65c[0x28];",
            1,
        ),
        (
            "scalar_direction",
            "const f32 delta = self->to_5e8 - self->base_62c;",
            "const f32 delta = self->base_62c - self->to_5e8;",
            1,
        ),
    ]
    for name, old, new, count in mutants:
        mutant = compile_mutant(name, old, new, count)
        detected = False
        for case in cases:
            baseline = machine.run(None, case)
            mutated = safe_run(machine, mutant, case)
            if baseline != mutated:
                detected = True
                break
        assert detected, f"negative control not detected: {name}"
        print(f"  [PASS] mutant detected: {name}")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
