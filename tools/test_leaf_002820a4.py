#!/usr/bin/env python3
"""Differential test for ui_func_002820a4 (0x002820a4) using Unicorn ARM.

0x002820A4 is the single-precision full-quadrant atan2(y, x) helper.  The test
compiles src/engine/leaf_batch45_a.cpp, extracts the reconstructed
ui_func_002820a4 body, resolves its two direct calls, and runs the pinned
original (extracted/exefs/code.bin) against the candidate on identical input
bit patterns.

Compared outputs:
  * the returned s0 bit pattern (float return register), continuation PC and SP;
  * callee-saved integer r4-r11 and VFP s16-s31;
  * the ordered helper call log: 0x002A4600 receives the quotient bit pattern
    and yields the class used by the caller, 0x002A462C receives the current
    numerator in s0 and its result is discarded;
  * the pinned image (must stay byte-identical during the call) and the stack
    bytes outside the private 0x100-byte call window;
  * any emulated write outside the private stack window.

Both helper stubs are deterministic: 0x002A4600 reproduces the pinned 44-byte
classifier exactly (verified against the original body before stubbing) and
0x002A462C reproduces the pinned 16-byte underflow probe, returning +0.0f.
Individual cases may force the classifier result (4 or 0) to prove that the
underflow call is driven by the helper's return value rather than by the input.

Coverage: the normal-value fast window and both of its exponent boundaries,
NaN/infinity/zero special values for every sign combination, the shared tail's
27/28 and -26/-27 exponent-delta boundaries, |y| > |x| and |y| <= |x| reduction
with simple and tan(atan(r)+-atan(1/2))-compensated quotients, both quotient
signs, the 2^32/2^-32 prefix rescale (selected by the exponent-MSB parity), and
natural plus injected classifier classes.  An independent Python model of the
recovered behavior is checked against every non-NaN case.
"""

from __future__ import annotations

import hashlib
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
SOURCE = ROOT / "src/engine/leaf_batch45_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_002820a4"

FUNC_ADDR = 0x002820A4
FUNC_SIZE = 624

IMAGE_ADDR = 0x00100000
IMAGE_MAP_SIZE = 0x00500000          # 0x00100000..0x00600000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
PRIVATE_STACK = 0x100                # scratch window either prologue may use
OVERLAY_SIZE = 0x400                 # image window replaced by each candidate

# Original call targets; both stubs sit at the pinned addresses.
STUB_CLASS = 0x002A4600              # 44-byte IEEE-754 classifier
STUB_UNDERFLOW = 0x002A462C          # 16-byte 0x10000000^2 underflow probe
STUB_NAMES = {
    STUB_CLASS: "ui_func_002a4600",
    STUB_UNDERFLOW: "ui_func_002a462c",
}
STUB_BY_SYMBOL = {name: address for address, name in STUB_NAMES.items()}

BX_LR = 0xE12FFF1E

# Literal-pool values of the pinned function (0x002822B4..0x00282310).
SIGN_BIT = 0x80000000
INF_BITS = 0x7F800000
QNAN_BITS = 0x7FC00000
PI_OVER_TWO = 0x3FC90FDB
PI = 0x40490FDB
HALFPI_COARSE = 0x3FC90000
HALFPI_FINE = 0x39FDAA22
PI_COARSE = 0x40490000
PI_FINE = 0x3A7DAA22
ATAN_HALF_COARSE = 0x3EED6000
ATAN_HALF_FINE = 0x37CE0AC3
POLY_C0 = 0xBD65AD2D
POLY_C1 = 0x3DD5B88F
POLY_C2 = 0xBE11B50F
POLY_C3 = 0x3E4CC861
POLY_C4 = 0xBEAAAAA8
SCALE_UP = 0x4F800000
SCALE_DOWN = 0x2F800000

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
VFP_CALLEE_SAVED = [getattr(arm, f"UC_ARM_REG_S{i}") for i in range(16, 32)]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def f32_value(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def classify(bits: int) -> int:
    """Exact model of the pinned 0x002A4600 classifier body."""
    d = (bits << 1) & 0xFFFFFFFF
    result = (d << 8) & 0xFFFFFFFF
    if result != 0:
        result = 4
    if (d >> 24) != 0:
        result |= 1
    if (0xFF000000 & ~d) & 0xFFFFFFFF == 0:
        result |= 2
    if result == 1:
        result = 5
    return result


# ---------------------------------------------------------------------------
# Independent Python model of the recovered behavior
# ---------------------------------------------------------------------------
def model(y_bits: int, x_bits: int, force_class: int | None):
    """Return (s0_bits or None for NaN, call log) for one input pair."""
    log: list[tuple] = []
    y = f32_value(y_bits)
    x = f32_value(x_bits)
    y_shift = (y_bits << 1) & 0xFFFFFFFF
    x_shift = (x_bits << 1) & 0xFFFFFFFF

    fast = (((0xE8000000 + y_shift) & 0xFFFFFFFF) < 0xE5000000 and
            ((0xE8000000 + x_shift) & 0xFFFFFFFF) < 0xE5000000)
    if not fast:
        if y_shift > 0xFF000000 or x_shift > 0xFF000000:
            return None, log                     # VFP default-NaN addition
        if (((y_bits | x_bits) << 1) & 0xFFFFFFFF) == 0:
            x_bits = (x_bits | 0x7F800000) & 0xFFFFFFFF
            x = f32_value(x_bits)
        elif y_shift == 0xFF000000 and x_shift == 0xFF000000:
            y_bits &= ~0x40000000
            x_bits &= ~0x40000000
            y = f32_value(y_bits)
            x = f32_value(x_bits)
        elif y_shift == 0xFF000000 or x_shift == 0:
            y_bits = (y_bits | 0x7F800000) & 0xFFFFFFFF
            x_bits &= SIGN_BIT
        elif ((y_shift ^ x_shift) & SIGN_BIT) == 0:
            scale = f32_value(SCALE_DOWN if (x_shift & SIGN_BIT) else SCALE_UP)
            y = f32(y * scale)
            x = f32(x * scale)
            y_bits = f32_bits(y)
            x_bits = f32_bits(x)

    y_window = (y_bits << 1) & 0xFFFFFFFF
    x_window = (x_bits << 1) & 0xFFFFFFFF
    delta = (y_window >> 24) - (x_window >> 24)

    if delta > 27:
        return (PI_OVER_TWO | SIGN_BIT) if (y_bits & SIGN_BIT) else PI_OVER_TWO, log

    if delta < -26:
        if (x_bits & SIGN_BIT) == 0:
            quotient_bits = f32_bits(f32(y / x))
            klass = force_class if force_class is not None else classify(quotient_bits)
            log.append(("ui_func_002a4600", quotient_bits))
            if klass == 4:
                log.append(("ui_func_002a462c", f32_bits(y)))
            return quotient_bits, log
        return (PI | SIGN_BIT) if (y_bits & SIGN_BIT) else PI, log

    y_negative = (y_bits & SIGN_BIT) != 0
    if y_window > x_window:
        coarse = f32_value((HALFPI_COARSE | SIGN_BIT) if y_negative else HALFPI_COARSE)
        fine = f32_value((HALFPI_FINE | SIGN_BIT) if y_negative else HALFPI_FINE)
        numerator_bits = x_bits
        denominator_bits = y_bits ^ SIGN_BIT
        negated_y = f32_value(denominator_bits)
        if ((((denominator_bits - numerator_bits) & 0xFFFFFFFF) << 1) & 0xFFFFFFFF) < 0x01000000:
            negative_ratio = ((numerator_bits ^ denominator_bits) & SIGN_BIT) != 0
            half = f32_value(0xBF000000 if negative_ratio else 0x3F000000)
            ratio = f32(f32(x - f32(half * negated_y)) /
                        f32(negated_y + f32(half * x)))
            if negative_ratio:
                fine = f32(fine - f32_value(ATAN_HALF_FINE))
                coarse = f32(coarse - f32_value(ATAN_HALF_COARSE))
            else:
                fine = f32(fine + f32_value(ATAN_HALF_FINE))
                coarse = f32(coarse + f32_value(ATAN_HALF_COARSE))
        else:
            ratio = f32(x / negated_y)
    else:
        if (x_bits & SIGN_BIT) != 0:
            coarse = f32_value((PI_COARSE | SIGN_BIT) if y_negative else PI_COARSE)
            fine = f32_value((PI_FINE | SIGN_BIT) if y_negative else PI_FINE)
        else:
            coarse = 0.0
            fine = 0.0
        if ((((x_bits - y_bits) & 0xFFFFFFFF) << 1) & 0xFFFFFFFF) < 0x01000000:
            negative_ratio = ((y_bits ^ x_bits) & SIGN_BIT) != 0
            half = f32_value(0xBF000000 if negative_ratio else 0x3F000000)
            ratio = f32(f32(y - f32(half * x)) / f32(x + f32(half * y)))
            if negative_ratio:
                fine = f32(fine - f32_value(ATAN_HALF_FINE))
                coarse = f32(coarse - f32_value(ATAN_HALF_COARSE))
            else:
                fine = f32(fine + f32_value(ATAN_HALF_FINE))
                coarse = f32(coarse + f32_value(ATAN_HALF_COARSE))
        else:
            ratio = f32(y / x)

    square = f32(ratio * ratio)
    cube = f32(ratio * square)
    polynomial = f32(f32_value(POLY_C1) + f32(square * f32_value(POLY_C0)))
    polynomial = f32(f32_value(POLY_C2) + f32(square * polynomial))
    polynomial = f32(f32_value(POLY_C3) + f32(square * polynomial))
    polynomial = f32(f32_value(POLY_C4) + f32(square * polynomial))
    result = f32(fine + f32(cube * polynomial))
    result = f32(result + ratio)
    result = f32(result + coarse)
    return f32_bits(result), log


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - IMAGE_ADDR)
        return f.read(FUNC_SIZE)


def image_bytes() -> bytes:
    return ORIG_BIN.read_bytes()


def sign_extend_24(value: int) -> int:
    return value - 0x1000000 if value & 0x800000 else value


def compile_variant(src_file: Path, obj_file: Path) -> bytes:
    result = compile_tu_armv6k(Path(src_file), Path(obj_file), ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed for {src_file}: {result.stderr}")

    funcs = extract_elf_functions_detailed(Path(obj_file))
    entry = funcs.get("ui_func_002820a4")
    if entry is None:
        raise RuntimeError(
            "ui_func_002820a4 not found in object: " + ", ".join(sorted(funcs))
        )

    raw, relocs = entry
    code = bytearray(raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):      # R_ARM_CALL / R_ARM_JUMP24
            target = STUB_BY_SYMBOL.get(rel.symbol_name)
            if target is None:
                raise RuntimeError(f"unexpected call relocation: {rel}")
            inst = struct.unpack_from("<I", code, rel.offset)[0]
            addend = sign_extend_24(inst & 0x00FFFFFF) << 2
            place = FUNC_ADDR + rel.offset
            disp = (target + addend - place) >> 2
            struct.pack_into(
                "<I", code, rel.offset, (inst & 0xFF000000) | (disp & 0x00FFFFFF)
            )
        else:
            raise RuntimeError(f"unsupported relocation: {rel}")

    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return compile_variant(SOURCE, OUT_DIR / "leaf_batch45_a.o")


def compile_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_variant(mutant_src, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Pinned helper bodies
# ---------------------------------------------------------------------------
def verify_helper_bodies() -> None:
    """Check that the deterministic stubs match the pinned helper bodies."""
    machine = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    machine.mem_map(IMAGE_ADDR, IMAGE_MAP_SIZE)
    machine.mem_map(STACK_ADDR, STACK_SIZE)
    machine.mem_map(TRAP_ADDR, 0x1000)
    machine.mem_write(IMAGE_ADDR, image_bytes())
    machine.reg_write(arm.UC_ARM_REG_C1_C0_2, 0xF00000)
    machine.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

    patterns = [
        0x00000000, 0x80000000, 0x00000001, 0x00000002, 0x007FFFFF, 0x00800000,
        0x3F800000, 0xBF800000, 0x7F7FFFFF, 0xFF7FFFFF, 0x7F800000, 0xFF800000,
        0x7F800001, 0x7FC00000, 0xFFC00001, 0x7FFFFFFF, 0x0C000000, 0x4F800000,
        0x2F800000, 0x3EED6000,
    ]
    for bits in patterns:
        machine.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        machine.reg_write(arm.UC_ARM_REG_R0, bits)
        machine.emu_start(STUB_CLASS, TRAP_ADDR, timeout=1_000_000)
        got = machine.reg_read(arm.UC_ARM_REG_R0)
        assert got == classify(bits), (
            f"classifier model mismatch for 0x{bits:08x}: "
            f"pinned 0x{got:x}, model 0x{classify(bits):x}"
        )
        machine.ctl_flush_tb()

    machine.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
    machine.reg_write(arm.UC_ARM_REG_S0, 0x3F800000)
    machine.emu_start(STUB_UNDERFLOW, TRAP_ADDR, timeout=1_000_000)
    assert machine.reg_read(arm.UC_ARM_REG_S0) == 0, "0x2a462c must return +0.0"
    machine.ctl_flush_tb()


# ---------------------------------------------------------------------------
# Emulated machine
# ---------------------------------------------------------------------------
class Machine:
    """One Unicorn machine with deterministic stubs at the pinned addresses."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(IMAGE_ADDR, IMAGE_MAP_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(IMAGE_ADDR, image_bytes())
        # VFP needs CPACR/FPEXC enabled in Unicorn's ARM model.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0xF00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.orig_code = get_orig_bytes()
        self.image = image_bytes()

        self._stack_pattern = bytes(
            (index * 37 + 0x5A) & 0xFF for index in range(STACK_SIZE)
        )
        self.call_log: list[tuple] = []
        self.writes: list[tuple[int, int]] = []
        self.case: dict = {}
        self._install_stubs()

    def _install_stubs(self) -> None:
        bx_lr = struct.pack("<I", BX_LR)
        self.uc.mem_write(STUB_CLASS, bx_lr)
        self.uc.mem_write(STUB_UNDERFLOW, bx_lr)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_class,
                         begin=STUB_CLASS, end=STUB_CLASS)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_underflow,
                         begin=STUB_UNDERFLOW, end=STUB_UNDERFLOW)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    # -- stubs ----------------------------------------------------------
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _log(self, address: int, *args) -> None:
        # Neither helper receives architected stack arguments.
        self.call_log.append((STUB_NAMES[address],) + args + self._stack_words(0))

    def _on_class(self, uc, address, size, user_data) -> None:
        bits = uc.reg_read(arm.UC_ARM_REG_R0)
        self._log(address, bits)
        forced = self.case.get("force_class")
        uc.reg_write(arm.UC_ARM_REG_R0,
                     forced if forced is not None else classify(bits))

    def _on_underflow(self, uc, address, size, user_data) -> None:
        bits = uc.reg_read(arm.UC_ARM_REG_S0)
        self._log(address, bits)
        # Pinned body: 2^-127 * 2^-127 underflows to +0.0; result is discarded.
        uc.reg_write(arm.UC_ARM_REG_S0, 0)

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    # -- execution ------------------------------------------------------
    def run(self, candidate: bytes | None, case: dict) -> dict:
        uc = self.uc
        self.case = case
        self.call_log = []
        self.writes = []

        uc.mem_write(FUNC_ADDR, self.image[FUNC_ADDR - IMAGE_ADDR:
                                             FUNC_ADDR - IMAGE_ADDR + OVERLAY_SIZE])
        uc.mem_write(FUNC_ADDR, self.orig_code if candidate is None else candidate)
        uc.ctl_flush_tb()
        uc.mem_write(STACK_ADDR, self._stack_pattern)
        image_before = hashlib.sha256(bytes(
            uc.mem_read(IMAGE_ADDR, len(self.image)))).digest()

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_S0, case["y"])
        uc.reg_write(arm.UC_ARM_REG_S1, case["x"])
        for name, value in CALLEE_SAVED_START.items():
            uc.reg_write(CALLEE_SAVED[name], value)
        for index, reg in enumerate(VFP_CALLEE_SAVED):
            uc.reg_write(reg, 0x3F000000 + index)

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError as exc:
            raise RuntimeError(
                f"Crash at PC=0x{uc.reg_read(arm.UC_ARM_REG_PC):08x}: {exc}"
            ) from exc
        finally:
            uc.ctl_flush_tb()

        image_after = hashlib.sha256(bytes(
            uc.mem_read(IMAGE_ADDR, len(self.image)))).digest()
        outside = [
            (address, size) for address, size in self.writes
            if not (ENTRY_SP - PRIVATE_STACK <= address < ENTRY_SP)
        ]
        return {
            "s0": uc.reg_read(arm.UC_ARM_REG_S0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "callee_saved_vfp": [
                uc.reg_read(reg) for reg in VFP_CALLEE_SAVED
            ],
            "call_log": list(self.call_log),
            "stack_guard": (
                bytes(uc.mem_read(STACK_ADDR, ENTRY_SP - PRIVATE_STACK - STACK_ADDR)),
                bytes(uc.mem_read(ENTRY_SP, STACK_ADDR + STACK_SIZE - ENTRY_SP)),
            ),
            "image_unchanged": image_before == image_after,
            "writes_outside": outside,
        }


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def case(name: str, y: int, x: int, force_class: int | None = None) -> dict:
    return {"name": name, "y": y & 0xFFFFFFFF, "x": x & 0xFFFFFFFF,
            "force_class": force_class}


def build_cases() -> list[dict]:
    zero = 0x00000000
    nzero = SIGN_BIT
    one = f32_bits(1.0)
    none = f32_bits(-1.0)
    tiny = f32_bits(2.0 ** -100)
    huge = f32_bits(2.0 ** 100)
    max_finite = 0x7F7FFFFF
    min_normal = 0x00800000
    min_subnormal = 0x00000001
    max_subnormal = 0x007FFFFF
    inf_bits = INF_BITS
    ninf_bits = INF_BITS | SIGN_BIT
    snan = 0x7F800001
    nsnan = 0xFF800001
    qnan = QNAN_BITS

    cases: list[dict] = []

    # --- normal-value fast window, every quadrant and both reduction paths
    for y, x in [
        (1.0, 1.0), (1.0, 1.5), (1.5, 1.0), (3.0, 4.0), (4.0, 3.0),
        (1.0, -1.0), (-1.0, 1.0), (-1.0, -1.0), (-1.5, 1.0), (1.0, -1.5),
        (-1.0, -1.5), (-1.5, -1.0), (0.75, 1.0), (1.0, 0.75), (-1.0, 0.75),
        (-1.0, 0.9), (0.9, 1.0), (-0.9, 1.0), (2.0, 0.25), (4.0, 1.0),
        (-4.0, 1.0), (1.0, 4.0), (-1.0, 4.0), (1.0, -4.0), (-1.0, -4.0),
        (1.0, 2.0), (1.0, -2.0), (3.0, 3.0), (3.0, -4.0), (-3.0, 4.0),
        (123456.0, 789.0), (-123456.0, 789.0), (0.001, -1e6), (1e30, 1e30),
        (-1e30, -1e30), (1e30, -1e30), (1e-30, 1e-30), (2.0 ** 125, 2.0 ** -100),
    ]:
        cases.append(case(f"quadrant y={y!r} x={x!r}", f32_bits(y), f32_bits(x)))

    # --- compensated/simple boundary of the |y| > |x| branch
    cases.append(case("path1 compensation low edge", one, 0xBF000001))
    cases.append(case("path1 compensation high edge", one, 0xBF000000))
    cases.append(case("path2 compensation low edge", one, 0x3FFFFFFF))
    cases.append(case("path2 compensation high edge", one, 0x40000000))

    # --- exponent-delta boundaries around +27 and -26
    for exponent in (25, 26, 27, 28, 29):
        value = f32_bits(2.0 ** (exponent - 127))
        cases.append(case(f"delta +{exponent}", one, value))
        cases.append(case(f"delta -{exponent}", value, one))
        cases.append(case(f"delta +{exponent} negative x", one, value | SIGN_BIT))
        cases.append(case(f"delta +{exponent} negative y", none, value))
        cases.append(case(f"delta -{exponent} negative x", value | SIGN_BIT, one))

    # --- NaN / infinity / zero special values
    for y, x, label in [
        (qnan, one, "qnan y"),
        (one, qnan, "qnan x"),
        (qnan, qnan, "qnan both"),
        (snan, one, "snan y"),
        (nsnan, one, "signalling nan y"),
        (one, snan, "snan x"),
        (qnan, inf_bits, "qnan y inf x"),
        (qnan, ninf_bits, "qnan y -inf x"),
        (ninf_bits, qnan, "-inf y qnan x"),
        (zero, zero, "0/0"),
        (nzero, zero, "-0/0"),
        (zero, nzero, "0/-0"),
        (nzero, nzero, "-0/-0"),
        (zero, one, "0/1"),
        (nzero, one, "-0/1"),
        (zero, none, "0/-1"),
        (nzero, none, "-0/-1"),
        (one, zero, "1/0"),
        (none, zero, "-1/0"),
        (one, nzero, "1/-0"),
        (none, nzero, "-1/-0"),
        (min_subnormal, zero, "min subnormal / 0"),
        (zero, min_subnormal, "0 / min subnormal"),
        (nzero, min_subnormal, "-0 / min subnormal"),
        (min_subnormal, nzero, "min subnormal / -0"),
        (inf_bits, one, "inf/1"),
        (ninf_bits, one, "-inf/1"),
        (inf_bits, none, "inf/-1"),
        (ninf_bits, none, "-inf/-1"),
        (one, inf_bits, "1/inf"),
        (one, ninf_bits, "1/-inf"),
        (none, inf_bits, "-1/inf"),
        (none, ninf_bits, "-1/-inf"),
        (inf_bits, inf_bits, "inf/inf"),
        (ninf_bits, inf_bits, "-inf/inf"),
        (inf_bits, ninf_bits, "inf/-inf"),
        (ninf_bits, ninf_bits, "-inf/-inf"),
        (inf_bits, zero, "inf/0"),
        (ninf_bits, zero, "-inf/0"),
        (inf_bits, nzero, "inf/-0"),
        (zero, inf_bits, "0/inf"),
        (nzero, inf_bits, "-0/inf"),
        (zero, ninf_bits, "0/-inf"),
        (nzero, ninf_bits, "-0/-inf"),
        (f32_bits(3.0), inf_bits, "3/inf rescale"),
        (f32_bits(3.0), ninf_bits, "3/-inf rescale"),
        (one, inf_bits, "1/inf no rescale"),
        (one, ninf_bits, "1/-inf no rescale"),
        (f32_bits(-1.0), ninf_bits, "-1/-inf no rescale"),
        (max_finite, inf_bits, "max finite/inf"),
        (inf_bits, max_finite, "inf/max finite"),
        (inf_bits, min_normal, "inf/min normal"),
        (ninf_bits, min_normal, "-inf/min normal"),
        (min_subnormal, one, "min subnormal/1"),
        (max_subnormal, one, "max subnormal/1"),
        (nzero, min_normal, "-0/min normal"),
    ]:
        cases.append(case(label, y, x))

    # --- prefix rescale selected by the exponent-MSB parity
    prefix_values = [
        ("exp 23", f32_bits(2.0 ** -104)),
        ("exp 24", f32_bits(2.0 ** -103)),
        ("exp 252", f32_bits(2.0 ** 125)),
        ("exp 253", f32_bits(2.0 ** 126)),
        ("max finite", max_finite),
        ("min normal", min_normal),
        ("min subnormal", min_subnormal),
    ]
    for label, value in prefix_values:
        cases.append(case(f"{label} over exp 27", value, f32_bits(2.0 ** -100)))
        cases.append(case(f"{label} over 1.0", value, one))
        cases.append(case(f"1.0 over {label}", one, value))
        cases.append(case(f"{label} over itself", value, value))
        cases.append(case(f"{label} over negative itself", value, value | SIGN_BIT))
    cases.append(case("subnormal y over subnormal x", min_subnormal, max_subnormal))
    cases.append(case("tiny 0 quotient", zero, huge))
    cases.append(case("tiny 0 quotient negative", nzero, huge))

    # --- natural and injected classifier classes in the tiny-ratio path
    cases.append(case("subnormal quotient raises underflow", tiny, huge))
    cases.append(case("negative subnormal quotient raises underflow",
                      tiny | SIGN_BIT, huge))
    cases.append(case("subnormal quotient negative x", tiny, huge | SIGN_BIT))
    cases.append(case("normal quotient", tiny, one))
    cases.append(case("zero quotient", zero, huge))
    cases.append(case("forced class 4 on normal quotient", tiny, one, force_class=4))
    cases.append(case("forced class 0 on subnormal quotient", tiny, huge,
                      force_class=0))
    cases.append(case("forced class 5 on subnormal quotient", tiny, huge,
                      force_class=5))

    return cases


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------
def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("s0", "pc", "sp", "callee_saved", "callee_saved_vfp",
                "call_log", "stack_guard", "image_unchanged", "writes_outside"):
        if orig[key] != cand[key]:
            problems.append(f"{key}: orig={orig[key]!r} cand={cand[key]!r}")
    if orig["sp"] != ENTRY_SP:
        problems.append(f"SP not restored: 0x{orig['sp']:08x}")
    if orig["pc"] != TRAP_ADDR:
        problems.append(f"PC not at trap: 0x{orig['pc']:08x}")
    if orig["writes_outside"] or cand["writes_outside"]:
        problems.append("write outside the private stack window")
    if not orig["image_unchanged"] or not cand["image_unchanged"]:
        problems.append("pinned image modified by the call")
    return problems


def check_model(case_data: dict, cand: dict) -> None:
    expected, expected_log = model(case_data["y"], case_data["x"],
                                   case_data["force_class"])
    if expected is not None:
        assert cand["s0"] == expected, (
            f"model result mismatch on {case_data['name']}: "
            f"0x{cand['s0']:08x} != 0x{expected:08x}"
        )
    assert cand["call_log"] == expected_log, (
        f"model call log mismatch on {case_data['name']}: "
        f"{cand['call_log']} != {expected_log}"
    )


def main() -> None:
    print("Testing ui_func_002820a4 (0x002820a4)...")
    verify_helper_bodies()
    print("  [PASS] stub bodies match the pinned 0x002a4600/0x002a462c code")

    cand_code = compile_candidate()
    orig_code = get_orig_bytes()
    print(f"  original: {len(orig_code)} B, candidate: {len(cand_code)} B")

    machine = Machine()
    cases = build_cases()
    passed = 0
    for case_data in cases:
        res_orig = machine.run(None, case_data)
        res_cand = machine.run(cand_code, case_data)
        problems = compare(res_orig, res_cand)
        if problems:
            print(f"  [FAIL] {case_data['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        check_model(case_data, res_cand)
        passed += 1
        print(f"  [PASS] {case_data['name']}  "
              f"(s0=0x{res_cand['s0']:08x}, {len(res_cand['call_log'])} calls)")

    print("\nNegative controls:")
    mutants = [
        ("nan_returns_y",
         "            return y + x;                       // NaN propagates through VADD",
         "            return y;"),
        ("both_zero_no_rewrite",
         "            x_bits |= kQuietBits;\n            x = F32FromBits(x_bits);",
         "            x = F32FromBits(x_bits);"),
        ("both_inf_marker_dropped",
         "            y_bits &= ~kInfinityBit;",
         "            y_bits |= kInfinityBit;"),
        ("scaling_parity_inverted",
         "        } else if (((y_shift ^ x_shift) & kSignBit) == 0) {",
         "        } else if (((y_shift ^ x_shift) & kSignBit) != 0) {"),
        ("tiny_path_x_sign_inverted",
         "        if ((x_bits & kSignBit) == 0) {",
         "        if ((x_bits & kSignBit) != 0) {"),
        ("tiny_path_pi_sign_dropped",
         "        return (y_bits & kSignBit) ? -kPi : kPi;",
         "        return kPi;"),
        ("scaling_direction_inverted",
         "            const f32 scale = (x_shift & kSignBit) ? kScaleDown : kScaleUp;",
         "            const f32 scale = (x_shift & kSignBit) ? kScaleUp : kScaleDown;"),
        ("delta_upper_return_sign_dropped",
         "        return (y_bits & kSignBit) ? -kPiOverTwo : kPiOverTwo;",
         "        return kPiOverTwo;"),
        ("delta_lower_boundary_off_by_one",
         "    if (exponent_delta < -26) {",
         "    if (exponent_delta < -25) {"),
        ("underflow_class_compare",
         "            if (ui_func_002a4600(F32ToBits(quotient)) == 4u) {",
         "            if (ui_func_002a4600(F32ToBits(quotient)) == 5u) {"),
        ("quadrant_choice_inverted",
         "    if (y_window > x_window) {",
         "    if (y_window < x_window) {"),
        ("path2_compensation_test_reversed",
         "        if (((x_bits - y_bits) << 1) < 0x01000000u) {",
         "        if (((y_bits - x_bits) << 1) < 0x01000000u) {"),
        ("atan_half_correction_sign_flipped",
         "            ratio = (x - half * negated_y) / (negated_y + half * x);\n"
         "            if (negative_ratio) {\n"
         "                angle_fine -= kAtanHalfFine;",
         "            ratio = (x - half * negated_y) / (negated_y + half * x);\n"
         "            if (negative_ratio) {\n"
         "                angle_fine += kAtanHalfFine;"),
        ("pi_offset_sign_flipped",
         "            angle_coarse = y_negative ? -kPiCoarse : kPiCoarse;",
         "            angle_coarse = y_negative ? kPiCoarse : -kPiCoarse;"),
        ("half_pi_offset_sign_flipped",
         "        angle_coarse = y_negative ? -kHalfPiCoarse : kHalfPiCoarse;",
         "        angle_coarse = y_negative ? kHalfPiCoarse : -kHalfPiCoarse;"),
        ("polynomial_low_coefficient",
         "    f32 polynomial = kPolyC1 + square * kPolyC0;",
         "    f32 polynomial = kPolyC1 + square * kPolyC1;"),
        ("final_coarse_before_ratio",
         "    f32 result = angle_fine + cube * polynomial;\n"
         "    result += ratio;\n"
         "    result += angle_coarse;",
         "    f32 result = angle_fine + cube * polynomial;\n"
         "    result += angle_coarse;\n"
         "    result += ratio;"),
    ]
    for name, old, new in mutants:
        mutant_code = compile_mutant(name, old, new)
        detected = False
        for case_data in cases:
            res_orig = machine.run(None, case_data)
            res_mut = machine.run(mutant_code, case_data)
            if compare(res_orig, res_mut):
                detected = True
                break
        assert detected, f"negative control not detected: {name}"
        print(f"  [PASS] mutant detected: {name}")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
