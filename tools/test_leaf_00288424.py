#!/usr/bin/env python3
"""Differential test for engine_func_00288424 (0x00288424) using Unicorn ARM.

0x00288424 is the single-precision ``tanf(x)`` helper used by the camera
billboard path (see ui_func_0032b0b4).  The test compiles
src/engine/leaf_batch45_b.cpp, extracts the reconstructed
engine_func_00288424 body, resolves its four direct calls and runs the pinned
original (extracted/exefs/code.bin) against the candidate on identical input
bit patterns.

The four callees are executed at their pinned addresses (deterministic pinned
bodies), with entry hooks that log the arguments and allow per-case injection:

  * 0x003EB4F4 ``ui_func_003eb4f4(u32* out_integer, u32 value_bits)`` -- the
    generic large-magnitude reduction.  Only the value bits are logged (the
    out-pointer differs between the two stack frames).  Injection forces the
    written quadrant and the returned s0 so the otherwise hard-to-reach
    quadrant == -1 sub-paths (infinity/NaN/subnormal reduced value) can be
    exercised on both implementations.
  * 0x002A4600 ``ui_func_002a4600(u32 value_bits)`` -- the 44-byte IEEE-754
    class of the tiny reduced value; the hook can force its return value.
  * 0x002A462C ``ui_func_002a462c(f32 value)`` -- the 16-byte underflow probe
    reached only for class 4; its incoming s0 is logged.
  * 0x002A464E ``func_002a464e_errno_set(s32 value)`` -- the Thumb helper that
    stores its argument through *__errno_location() (EDOM).  The hook logs the
    stored value and returns to LR in ARM state; the store itself is external
    and is modelled by the log entry only.

Compared outputs: returned s0 bits, PC, SP, callee-saved r4-r11 and s16-s31,
the ordered helper call log, the stack bytes outside the private 0x100-byte
call window, the pinned image (must stay byte-identical) and any write outside
the private stack window.

Coverage: the three magnitude windows and their exact bit boundaries
(2^-12 and pi/4 as (bits << 1) compares, 12867.5712890625 as a magnitude
compare), all four quadrants incl. exact quarter-turn ties, +/-0, subnormals,
min/max finite, +/-infinity and every NaN class, plus injected helper results
for each quadrant == -1 sub-branch and both quadrants of the polynomial tail.
An independent Python model (f32-rounded) is checked on every case whose
reduction is evaluable without the generic helper.
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
SOURCE = ROOT / "src/engine/leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_00288424"

FUNC_ADDR = 0x00288424
FUNC_SIZE = 432

IMAGE_ADDR = 0x00100000
IMAGE_MAP_SIZE = 0x00500000          # 0x00100000..0x00600000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
PRIVATE_STACK = 0x100                # scratch window either prologue may use
OVERLAY_SIZE = 0x400                 # image window replaced by each candidate

HELPER_REDUCE = 0x003EB4F4           # generic reduction (pinned body runs)
HELPER_CLASS = 0x002A4600            # IEEE-754 classifier
HELPER_PROBE = 0x002A462C            # underflow probe
HELPER_ERRNO = 0x002A464E            # Thumb *__errno_location() = r0

HELPER_NAMES = {
    HELPER_REDUCE: "ui_func_003eb4f4",
    HELPER_CLASS: "ui_func_002a4600",
    HELPER_PROBE: "ui_func_002a462c",
    HELPER_ERRNO: "func_002a464e_errno_set",
}
SYMBOL_TO_ADDR = {name: addr for addr, name in HELPER_NAMES.items()}

# Literal-pool values of the pinned function (0x00288594..0x002885D0).
SIGN_BIT = 0x80000000
PI_OVER_FOUR_SHIFT = 0x7E921FB6      # (bits of pi/4) << 1
TINY_SHIFT = 0x73000000              # (bits of 2^-12) << 1
REDUCTION_LIMIT = 0x46490E49         # bits of 12867.5712890625f
TWO_OVER_PI = 0x3F22F983
ROUND_MAGIC = 0x4B000000
HALF_PI_PART0 = 0x3FC90000
HALF_PI_PART1 = 0x39FDA000
HALF_PI_PART2 = 0x33A22000
HALF_PI_PART3 = 0x2C34611A
TAN_C0 = 0x3B066D0C
TAN_C1 = 0x3C22E9BB
TAN_C2 = 0x3CCE768A
TAN_C3 = 0x3D59B5AC
TAN_C4 = 0x3E08A135
TAN_C5 = 0x3EAAAA29
NEG_ONE = 0xBF800000
INF_BITS = 0x7F800000
QNAN_BITS = 0x7FC00000

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


def is_nan(bits: int) -> bool:
    return ((bits << 1) & 0xFFFFFFFF) > 0xFF000000


# ---------------------------------------------------------------------------
# Independent Python model of the recovered behavior
# ---------------------------------------------------------------------------
def model(bits: int, force_class, inject):
    """Return (s0_bits | None, call_log | None).

    ``None`` for s0 means the generic 0x003EB4F4 reduction is required and the
    exact result is only validated differentially.  ``None`` for the log means
    the helper's pinned side effects are not modelled.
    """
    log: list[tuple] = []
    x = f32_value(bits)
    x_shift = (bits << 1) & 0xFFFFFFFF

    if x_shift >= PI_OVER_FOUR_SHIFT:
        if (bits & 0x7FFFFFFF) >= REDUCTION_LIMIT:
            log.append(("ui_func_003eb4f4", bits))
            if inject is not None:
                quad = inject["quadrant"] & 0xFFFFFFFF   # s32 read by the body
                if quad >= 0x80000000:
                    quad -= 0x100000000
                reduced = f32_value(inject["reduced_bits"])
            else:
                if x_shift < 0xFF000000:
                    # The pinned helper's finite reduction is not modelled.
                    return None, None
                quad = -1                # non-finite: writes -1, keeps s0
                reduced = x
        else:
            scaled = f32(x * f32_value(TWO_OVER_PI))
            if bits & SIGN_BIT:
                biased = f32(scaled - f32_value(ROUND_MAGIC))
                rounded = f32(biased + f32_value(ROUND_MAGIC))
            else:
                biased = f32(scaled + f32_value(ROUND_MAGIC))
                rounded = f32(biased - f32_value(ROUND_MAGIC))
            quad = int(rounded) & 3      # two's complement for negatives
            reduced = f32(x - f32(rounded * f32_value(HALF_PI_PART0)))
            reduced = f32(reduced - f32(rounded * f32_value(HALF_PI_PART1)))
            reduced = f32(reduced - f32(rounded * f32_value(HALF_PI_PART2)))
            reduced = f32(reduced - f32(rounded * f32_value(HALF_PI_PART3)))
    else:
        quad = -1 if x_shift < TINY_SHIFT else 0
        reduced = x

    if quad < 0:
        magnitude = (f32_bits(reduced) << 1) & 0xFFFFFFFF
        if magnitude > 0xFF000000:
            return None, log             # NaN add is compared differentially
        if magnitude == 0xFF000000:
            log.append(("func_002a464e_errno_set", 1))
            return QNAN_BITS, log        # VFP default NaN from 0/0
        klass = force_class if force_class is not None else classify(f32_bits(reduced))
        log.append(("ui_func_002a4600", f32_bits(reduced)))
        if klass == 4:
            log.append(("ui_func_002a462c", f32_bits(reduced)))
        return f32_bits(reduced), log

    square = f32(reduced * reduced)
    poly = f32(f32_value(TAN_C0) + f32(square * f32_value(TAN_C1)))
    poly = f32(f32_value(TAN_C2) + f32(square * poly))
    poly = f32(f32_value(TAN_C3) + f32(square * poly))
    poly = f32(f32_value(TAN_C4) + f32(square * poly))
    poly = f32(f32_value(TAN_C5) + f32(square * poly))
    tangent = f32(reduced + f32(reduced * f32(poly * square)))
    if (quad & 1) == 0:
        return f32_bits(tangent), log
    if tangent == 0.0:                   # -1/+-0 gives -+infinity
        return (INF_BITS if struct.pack("<f", tangent)[3] & 0x80 else
                0xFF800000), log
    return f32_bits(f32(f32_value(NEG_ONE) / tangent)), log


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
    entry = funcs.get("engine_func_00288424")
    if entry is None:
        raise RuntimeError(
            "engine_func_00288424 not found in object: " + ", ".join(sorted(funcs))
        )

    raw, relocs = entry
    code = bytearray(raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):      # R_ARM_CALL / R_ARM_JUMP24
            target = SYMBOL_TO_ADDR.get(rel.symbol_name)
            if target is None:
                raise RuntimeError(f"unexpected call relocation: {rel}")
            inst = struct.unpack_from("<I", code, rel.offset)[0]
            place = FUNC_ADDR + rel.offset
            if target & 2:
                # 0x002A464E is Thumb: BL cannot encode this target, so replace
                # the emitted BL with an unconditional BLX immediate.  The
                # entry hook returns to LR in ARM state for both runs.
                offset = (target & ~3) - (place + 8)
                if offset % 4 != 0 or not -(1 << 25) <= offset < (1 << 25):
                    raise RuntimeError(f"BLX target out of range: {rel}")
                blx = (0xFA000000 | (1 << 24) | ((offset >> 2) & 0x00FFFFFF))
                struct.pack_into("<I", code, rel.offset, blx)
                continue
            addend = sign_extend_24(inst & 0x00FFFFFF) << 2
            disp = (target + addend - place) >> 2
            struct.pack_into(
                "<I", code, rel.offset, (inst & 0xFF000000) | (disp & 0x00FFFFFF)
            )
        else:
            raise RuntimeError(f"unsupported relocation: {rel}")

    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return compile_variant(SOURCE, OUT_DIR / "leaf_batch45_b.o")


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
    """Check the classifier/probe stubs and the reduction helper's contracts."""
    machine = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    machine.mem_map(IMAGE_ADDR, IMAGE_MAP_SIZE)
    machine.mem_map(STACK_ADDR, STACK_SIZE)
    machine.mem_map(TRAP_ADDR, 0x1000)
    machine.mem_write(IMAGE_ADDR, image_bytes())
    machine.reg_write(arm.UC_ARM_REG_C1_C0_2, 0xF00000)
    machine.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

    patterns = [
        0x00000000, 0x80000000, 0x00000001, 0x00000002, 0x007FFFFF, 0x00800000,
        0x39800000, 0x3F490FDB, 0x3F800000, 0xBF800000, 0x7F7FFFFF, 0xFF7FFFFF,
        0x7F800000, 0xFF800000, 0x7F800001, 0x7FC00000, 0xFFC00001, 0x7FFFFFFF,
        0x0C000000, 0x4F800000, 0x2F800000,
    ]
    for bits in patterns:
        machine.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        machine.reg_write(arm.UC_ARM_REG_R0, bits)
        machine.emu_start(HELPER_CLASS, TRAP_ADDR, timeout=1_000_000)
        got = machine.reg_read(arm.UC_ARM_REG_R0)
        assert got == classify(bits), (
            f"classifier model mismatch for 0x{bits:08x}: "
            f"pinned 0x{got:x}, model 0x{classify(bits):x}"
        )
        machine.ctl_flush_tb()

    machine.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
    machine.reg_write(arm.UC_ARM_REG_S0, 0x3F800000)
    machine.emu_start(HELPER_PROBE, TRAP_ADDR, timeout=1_000_000)
    assert machine.reg_read(arm.UC_ARM_REG_S0) == 0, "0x2a462c must return +0.0"
    machine.ctl_flush_tb()

    # The wrapper relies on the reduction helper for non-finite input: it must
    # write quadrant 0xFFFFFFFF and leave s0 equal to the incoming value.
    for bits in (0x7F800000, 0xFF800000, 0x7FC00000, 0x7F800001, 0x7FFFFFFF):
        scratch = STACK_ADDR + 0x100
        machine.mem_write(scratch, b"\x00\x00\x00\x00")
        machine.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        machine.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        machine.reg_write(arm.UC_ARM_REG_R0, scratch)
        machine.reg_write(arm.UC_ARM_REG_R1, bits)
        machine.reg_write(arm.UC_ARM_REG_S0, bits)
        machine.emu_start(HELPER_REDUCE, TRAP_ADDR, timeout=1_000_000)
        written = struct.unpack("<I", machine.mem_read(scratch, 4))[0]
        returned = machine.reg_read(arm.UC_ARM_REG_S0)
        assert written == 0xFFFFFFFF, (
            f"reduction helper quadrant for 0x{bits:08x}: 0x{written:08x}"
        )
        assert returned == bits, (
            f"reduction helper s0 for 0x{bits:08x}: 0x{returned:08x}"
        )
        machine.ctl_flush_tb()


# ---------------------------------------------------------------------------
# Emulated machine
# ---------------------------------------------------------------------------
class Machine:
    """One Unicorn machine with instrumented pinned helpers."""

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
        self._install_hooks()

    def _install_hooks(self) -> None:
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_reduce,
                         begin=HELPER_REDUCE, end=HELPER_REDUCE)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_class,
                         begin=HELPER_CLASS, end=HELPER_CLASS)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_probe,
                         begin=HELPER_PROBE, end=HELPER_PROBE)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_errno,
                         begin=HELPER_ERRNO, end=HELPER_ERRNO)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    def _return_to_caller(self) -> None:
        lr = self.uc.reg_read(arm.UC_ARM_REG_LR)
        cpsr = self.uc.reg_read(arm.UC_ARM_REG_CPSR)
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, cpsr & ~0x20)   # ARM state
        self.uc.reg_write(arm.UC_ARM_REG_PC, lr)

    # -- hooks ----------------------------------------------------------
    def _log(self, address: int, *args) -> None:
        # No helper receives architected stack arguments.
        self.call_log.append((HELPER_NAMES[address],) + args)

    def _on_reduce(self, uc, address, size, user_data) -> None:
        bits = uc.reg_read(arm.UC_ARM_REG_R1)
        self._log(address, bits)
        inject = self.case.get("inject")
        if inject is not None:
            out_ptr = uc.reg_read(arm.UC_ARM_REG_R0)
            uc.mem_write(
                out_ptr,
                struct.pack("<I", inject["quadrant"] & 0xFFFFFFFF))
            uc.reg_write(arm.UC_ARM_REG_S0, inject["reduced_bits"])
            self._return_to_caller()

    def _on_class(self, uc, address, size, user_data) -> None:
        bits = uc.reg_read(arm.UC_ARM_REG_R0)
        self._log(address, bits)
        forced = self.case.get("force_class")
        if forced is not None:
            uc.reg_write(arm.UC_ARM_REG_R0, forced)
            self._return_to_caller()

    def _on_probe(self, uc, address, size, user_data) -> None:
        self._log(address, uc.reg_read(arm.UC_ARM_REG_S0))

    def _on_errno(self, uc, address, size, user_data) -> None:
        self._log(address, uc.reg_read(arm.UC_ARM_REG_R0))
        self._return_to_caller()

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
        uc.reg_write(arm.UC_ARM_REG_S0, case["x"])
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
def case(name: str, x: int, force_class=None, inject=None) -> dict:
    return {"name": name, "x": x & 0xFFFFFFFF,
            "force_class": force_class, "inject": inject}


def injected(quadrant: int, reduced_bits: int) -> dict:
    return {"quadrant": quadrant & 0xFFFFFFFF,
            "reduced_bits": reduced_bits & 0xFFFFFFFF}


def build_cases() -> list[dict]:
    def b(value: float) -> int:
        return f32_bits(value)

    tiny = 1 << 0                     # min subnormal
    max_sub = 0x007FFFFF
    min_normal = 0x00800000
    max_finite = 0x7F7FFFFF
    inf = INF_BITS
    ninf = INF_BITS | SIGN_BIT
    qnan = QNAN_BITS
    nqnan = QNAN_BITS | SIGN_BIT
    snan = 0x7F800001
    nsnan = 0xFF800001

    cases: list[dict] = []

    # --- tiny window |x| < 2^-12 (quadrant -1, returns x unchanged)
    for bits, label in [
        (0x00000000, "+0"), (SIGN_BIT, "-0"), (tiny, "min subnormal"),
        (0x00000100, "subnormal"), (0x007FFFFF, "max subnormal"),
        (0x36800000, "2^-18"), (0x38D00000, "just under 2^-12"),
        (0x39800000 | SIGN_BIT, "-2^-12"),
    ]:
        cases.append(case(f"tiny {label}", bits))

    # --- exact 2^-12 boundary and the 2^-12..pi/4 window
    cases.append(case("2^-12 lower edge (2^-12 - ulp)", 0x397FFFFF))
    cases.append(case("2^-12 exact (quadrant 0)", 0x39800000))
    cases.append(case("-2^-12 exact (quadrant 0)", 0x39800000 | SIGN_BIT))
    for value in (0.001, 0.01, 0.1, 0.25, 0.5, 0.6, 0.7, 0.78, -0.1, -0.5,
                  -0.78):
        cases.append(case(f"small {value!r}", b(value)))
    cases.append(case("pi/4 - ulp (small window)", 0x3F490FDA))
    cases.append(case("pi/4 - ulp negative", 0x3F490FDA | SIGN_BIT))

    # --- pi/4 exact boundary (first reduction case, q = 1)
    cases.append(case("pi/4 exact", 0x3F490FDB))
    cases.append(case("pi/4 exact negative", 0x3F490FDB | SIGN_BIT))
    cases.append(case("pi/4 + ulp", 0x3F490FDC))

    # --- fast reduction window, every quadrant and both signs
    for value in (0.8, 0.9, 1.0, 1.2, 1.5, 1.5707964, 2.0, 2.5, 3.0,
                  3.1415927, 3.5, 4.0, 4.712389, 5.0, 6.0, 6.2831855,
                  7.0, 10.0, 100.0, 1000.0, 4096.0, 8192.0, 10000.0,
                  12867.0, 12867.5):
        cases.append(case(f"reduce {value!r}", b(value)))
        cases.append(case(f"reduce -{value!r}", b(value) | SIGN_BIT))

    # exact quarter-turn ties of q = round(x * 2/pi) (x*2/pi = k + 1/2)
    for multiplier, label in [(0.5, "0.5"), (1.5, "1.5"), (2.5, "2.5"),
                              (3.5, "3.5"), (-0.5, "-0.5"), (-1.5, "-1.5")]:
        x = f32(multiplier * f32_value(0x3FC90FDB))   # (k+0.5) * pi/2
        cases.append(case(f"quarter-turn tie {label}", b(x)))

    # huge-argument boundary of the 2^23 trick
    cases.append(case("reduction limit - ulp", 0x46490E48))
    cases.append(case("reduction limit - ulp negative", 0x46490E48 | SIGN_BIT))
    cases.append(case("reduction limit exact (generic helper)", REDUCTION_LIMIT))
    cases.append(case("reduction limit exact negative",
                      REDUCTION_LIMIT | SIGN_BIT))
    cases.append(case("reduction limit + ulp", 0x46490E4A))

    # --- huge finite values (generic helper, real pinned body)
    for value in (1.0e5, -1.0e5, 1.0e7, 1.0e10, -1.0e10, 1.0e20, 1.0e30,
                  -1.0e30, 3.0e38):
        cases.append(case(f"huge {value!r}", b(value)))
    cases.append(case("max finite", max_finite))
    cases.append(case("max finite negative", max_finite | SIGN_BIT))
    cases.append(case("min normal", min_normal))
    cases.append(case("max subnormal", max_sub))

    # --- non-finite values (helper writes quadrant -1, leaves s0)
    for bits, label in [
        (inf, "+inf"), (ninf, "-inf"), (qnan, "qnan"), (nqnan, "-qnan"),
        (snan, "snan"), (nsnan, "-snan"), (0x7FFFFFFF, "max NaN"),
        (0xFF800000, "-inf alt"),
    ]:
        cases.append(case(f"non-finite {label}", bits))

    # --- injected reduction results: exercise every quadrant >= 0 and the
    #     quadrant == -1 sub-branches without depending on the helper's value.
    cases.append(case("inject quadrant 0 finite", inf,
                      inject=injected(0, b(0.3))))
    cases.append(case("inject quadrant 1 finite", inf,
                      inject=injected(1, b(0.3))))
    cases.append(case("inject quadrant 2 finite", inf,
                      inject=injected(2, b(-0.3))))
    cases.append(case("inject quadrant 3 finite", inf,
                      inject=injected(3, b(-0.3))))
    cases.append(case("inject quadrant -1 normal", inf,
                      inject=injected(-1, b(0.25))))
    cases.append(case("inject quadrant -1 subnormal", inf,
                      inject=injected(-1, 0x00000001)))
    cases.append(case("inject quadrant -1 negative subnormal", inf,
                      inject=injected(-1, 0x80000001)))
    cases.append(case("inject quadrant -1 +inf", inf,
                      inject=injected(-1, inf)))
    cases.append(case("inject quadrant -1 -inf", inf,
                      inject=injected(-1, ninf)))
    cases.append(case("inject quadrant -1 qnan", inf,
                      inject=injected(-1, qnan)))
    cases.append(case("inject quadrant -1 snan", inf,
                      inject=injected(-1, snan)))
    cases.append(case("inject quadrant 1 zero", inf,
                      inject=injected(1, 0x00000000)))
    cases.append(case("inject quadrant 3 negative zero", inf,
                      inject=injected(3, SIGN_BIT)))

    # --- classifier class forcing on the tiny path
    cases.append(case("forced class 4 (normal tiny)", b(0.0001), force_class=4))
    cases.append(case("forced class 5 (subnormal tiny)", 0x00000001,
                      force_class=5))
    cases.append(case("forced class 0 (subnormal tiny)", 0x00000001,
                      force_class=0))
    cases.append(case("forced class 3 (tiny)", 0x00000001, force_class=3))
    cases.append(case("natural class 4 (min subnormal)", 0x00000001))
    cases.append(case("natural class 4 (max subnormal)", 0x007FFFFF))
    cases.append(case("natural class 5 (2^-12 - ulp normal)",
                      0x397FFFFF))

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
    expected, expected_log = model(case_data["x"], case_data["force_class"],
                                   case_data["inject"])
    if expected is not None:
        assert cand["s0"] == expected, (
            f"model result mismatch on {case_data['name']}: "
            f"0x{cand['s0']:08x} != 0x{expected:08x}"
        )
    if expected_log is not None:
        assert cand["call_log"] == expected_log, (
            f"model call log mismatch on {case_data['name']}: "
            f"{cand['call_log']} != {expected_log}"
        )


def main() -> None:
    print("Testing engine_func_00288424 (0x00288424)...")
    verify_helper_bodies()
    print("  [PASS] pinned 0x002a4600/0x002a462c/0x003eb4f4 contracts match")

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
        ("tiny_limit_shifted",
         "quadrant = ((bits << 1) < kTinyShift) ? -1 : 0;",
         "quadrant = ((bits << 1) <= kTinyShift) ? -1 : 0;"),
        # Note: shifting the pi/4 boundary itself is unobservable -- at exactly
        # pi/4 both the small-window and the reduction-window formulas return
        # 0x3F800000 bit-exactly.  Disabling the whole reduction window is the
        # observable form of this boundary.
        ("reduction_window_disabled",
         "if ((bits << 1) >= kPiOverFourShift) {",
         "if ((bits << 1) >= 0x7F800000u) {"),
        ("reduction_limit_off_by_one",
         "if ((bits & 0x7FFFFFFFu) >= kReductionLimit) {",
         "if ((bits & 0x7FFFFFFFu) > kReductionLimit) {"),
        ("negative_rounding_direction",
         "const f32 biased = scaled - kRoundMagic;\n                rounded = biased + kRoundMagic;",
         "const f32 biased = scaled + kRoundMagic;\n                rounded = biased - kRoundMagic;"),
        ("quadrant_mask_dropped",
         "quadrant = static_cast<s32>(rounded) & 3;",
         "quadrant = static_cast<s32>(rounded);"),
        ("reduction_part_skipped",
         "reduced = reduced - rounded * kHalfPiPart2;",
         "reduced = reduced - rounded * kHalfPiPart1;"),
        ("infinity_subnormal_probe_dropped",
         "if (ui_func_002a4600(F32ToBits(reduced)) == 4u) {\n            (void)ui_func_002a462c(reduced);\n        }",
         "if (ui_func_002a4600(F32ToBits(reduced)) == 5u) {\n            (void)ui_func_002a462c(reduced);\n        }"),
        ("errno_value_changed",
         "(void)func_002a464e_errno_set(1);",
         "(void)func_002a464e_errno_set(2);"),
        ("nan_and_inf_confused",
         "if (magnitude > 0xFF000000u) {\n            return reduced + reduced;",
         "if (magnitude >= 0xFF000000u) {\n            return reduced + reduced;"),
        ("odd_quadrant_inverted",
         "if ((quadrant & 1) == 0) {",
         "if ((quadrant & 1) != 0) {"),
        ("polynomial_coefficient",
         "f32 poly = kTanC0 + square * kTanC1;",
         "f32 poly = kTanC0 + square * kTanC0;"),
        ("reciprocal_sign_flipped",
         "return -1.0f / tangent;",
         "return 1.0f / tangent;"),
        ("helper_result_ignored",
         "reduced = ui_func_003eb4f4(reinterpret_cast<u32*>(&quadrant), bits);",
         "reduced = x;"),
        ("small_window_quadrant",
         "quadrant = ((bits << 1) < kTinyShift) ? -1 : 0;",
         "quadrant = 0;"),
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
