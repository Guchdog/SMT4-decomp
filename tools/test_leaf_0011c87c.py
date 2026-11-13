#!/usr/bin/env python3
"""Differential test for func_0011c87c (0x0011c87c) using Unicorn ARM.

The candidate in ``src/engine/leaf_batch34_c.cpp`` is compiled with the pinned
ARMv6K pipeline, its nine direct-call relocations are resolved to deterministic
stubs at the original addresses, and the pinned original (``code.bin``, 704 B
including the literal pool) is compared against the candidate in separate
Unicorn machines with identical fixtures.

The stubs deliberately return caller-controlled values (calendar timestamps,
fixed-point results, signed divmod quotient/remainder and system ticks) so the
test proves that the candidate forwards every helper argument and consumes every
helper result, including the r2:r3 remainder of 0x002B5B44 and the destination
pointer returned by 0x002B5B94.

Compared outputs:
  * the full 64-bit return value (r0 and r1), continuation PC, final SP and
    callee-saved r4-r11;
  * the ordered call log with every helper argument, including stack arguments
    and the 64-bit values read through the calendar/fixed-point pointers;
  * the complete 0x00440000 data page (0x0044E630 clock), the complete shared
    page (0x1FF81000 selector and both 0x20-byte DATETIME records), the shadow
    page and any write outside the fixture pages and the private stack.

Coverage includes the selector parity, both slots, zero/negative/large clock and
calendar values, a third calendar call distinct from the first, tick deltas
below/equal/above the snapshot, frequency signs and zero, the 3,600,000 ms clamp
at and around zero, nonzero residual fields, off-spec divmod quotient/remainder
pairs and a fixed-seed random sweep.  Negative controls mutate the magic, the
shift, both divisors, the clamp condition, the selector mask, the field offsets,
the signed high-multiply, the wrapping accumulation and the returned-pointer
use.
"""

from __future__ import annotations

import random
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
SOURCE = ROOT / "src/engine/leaf_batch34_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_0011c87c"

FUNC_ADDR = 0x0011C87C
FUNC_SIZE = 704

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000
DATA_ADDR = 0x00440000
DATA_SIZE = 0x00020000
SHADOW_ADDR = 0x00730000
SHADOW_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
SHARED_ADDR = 0x1FF80000
SHARED_SIZE = 0x00002000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

CLOCK_ADDR = 0x0044E630
SELECTOR_ADDR = 0x1FF81000
DATETIME_0 = 0x1FF81020
DATETIME_1 = 0x1FF81040

STUB_MAKE_TIME = 0x002B5B94
STUB_FIXED_POINT = 0x002B5F90
STUB_DIVMOD = 0x002B5B44
STUB_TICK = 0x001240C0

STUB_NAMES = {
    STUB_MAKE_TIME: "make_calendar_ms",
    STUB_FIXED_POINT: "fixed_point_scale",
    STUB_DIVMOD: "signed_divmod_64",
    STUB_TICK: "svcGetSystemTick",
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

MASK64 = (1 << 64) - 1
SIGN64 = 1 << 63


def wrap_s64(value: int) -> int:
    value &= MASK64
    return value - (1 << 64) if value & SIGN64 else value


def u64_of(low: int, high: int) -> int:
    return ((high & 0xFFFFFFFF) << 32) | (low & 0xFFFFFFFF)


def s64_of(low: int, high: int) -> int:
    return wrap_s64(u64_of(low, high))


def s32_of(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value & 0x80000000 else value


def high64_signed(a: int, b: int) -> int:
    """High 64 bits of the signed 64x64 product (Python ints are exact)."""
    return (wrap_s64(a) * wrap_s64(b)) >> 64


def model_fixed_point(a: int, mul: int, shift: int) -> int:
    """Model of 0x002B5F90: signed high product >> shift, +1 when a < 0."""
    result = high64_signed(a, mul) >> shift
    if wrap_s64(a) < 0:
        result += 1
    return wrap_s64(result)


def trunc_divmod(a: int, b: int) -> tuple[int, int]:
    """__aeabi_ldivmod: quotient truncates toward zero, remainder follows a."""
    a = wrap_s64(a)
    b = wrap_s64(b)
    if b == 0:
        return 0, 0
    quotient = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        quotient = -quotient
    return wrap_s64(quotient), wrap_s64(a - quotient * b)


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0011c87c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"func_0011c87c not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        name = rel.symbol_name
        if "002b5b94" in name:
            target = STUB_MAKE_TIME
        elif "002b5f90" in name:
            target = STUB_FIXED_POINT
        elif "002b5b44" in name:
            target = STUB_DIVMOD
        elif "GetSystemTick" in name:
            target = STUB_TICK
        else:
            raise RuntimeError(f"unresolved call relocation: {name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        condition = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, condition | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
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


def default_record() -> dict:
    return {"n": 0, "s": 0, "f": 0x0FFB0FF0, "b": 0, "u": 0}


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "clock": 0,
        "times": [0, 3155760000000, 0],
        "time_shadow": [False, False, False],
        "selector": 0,
        "dt0": default_record(),
        "dt1": {
            "n": 0x1111111122222222,
            "s": 0x3333333344444444,
            "f": 0x55556666,
            "b": 0x7777777788888888,
            "u": 0x9999AAAA,
        },
        "ticks": [0],
        "b_results": None,
        "divmod_results": None,
    }
    case.update(overrides)
    return case


def build_data(case: dict) -> bytes:
    page = bytearray([0x5A] * DATA_SIZE)
    struct.pack_into("<Q", page, CLOCK_ADDR - DATA_ADDR, case["clock"] & MASK64)
    return bytes(page)


def build_shared(case: dict) -> bytes:
    page = bytearray([0x3C] * SHARED_SIZE)

    def put_record(base: int, record: dict) -> None:
        offset = base - SHARED_ADDR
        struct.pack_into("<Q", page, offset + 0x00, record["n"] & MASK64)
        struct.pack_into("<Q", page, offset + 0x08, record["s"] & MASK64)
        struct.pack_into("<I", page, offset + 0x10, record["f"] & 0xFFFFFFFF)
        struct.pack_into("<I", page, offset + 0x14, record.get("u", 0) & 0xFFFFFFFF)
        struct.pack_into("<Q", page, offset + 0x18, record["b"] & MASK64)

    put_record(DATETIME_0, case["dt0"])
    put_record(DATETIME_1, case["dt1"])
    struct.pack_into(
        "<I", page, SELECTOR_ADDR - SHARED_ADDR, case["selector"] & 0xFFFFFFFF
    )
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(SHADOW_ADDR, SHADOW_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(SHARED_ADDR, SHARED_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in (STUB_MAKE_TIME, STUB_FIXED_POINT, STUB_DIVMOD):
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )

        # Revision wrapper for svc #0x28 reached by the candidate; the original
        # executes the same SVC inline.
        self.uc.mem_write(
            STUB_TICK,
            struct.pack("<III", 0xE1A00000, 0xEF000028, 0xE12FFF1E),
        )
        self.uc.hook_add(unicorn.UC_HOOK_INTR, self._on_interrupt)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.time_index = 0
        self.fixed_index = 0
        self.divmod_index = 0

    @staticmethod
    def _normalise(value: int):
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        if DATA_ADDR <= value < DATA_ADDR + DATA_SIZE:
            return "<data>"
        if SHARED_ADDR <= value < SHARED_ADDR + SHARED_SIZE:
            return "<shared>"
        if SHADOW_ADDR <= value < SHADOW_ADDR + SHADOW_SIZE:
            return "<shadow>"
        return value

    def _log(self, name: str, *args) -> None:
        self.call_log.append((name, args))

    def _read_u64(self, address: int) -> int:
        return struct.unpack("<Q", self.uc.mem_read(address, 8))[0]

    def _write_u64(self, address: int, value: int) -> None:
        self.uc.mem_write(address, struct.pack("<Q", value & MASK64))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        sp = uc.reg_read(arm.UC_ARM_REG_SP)

        if address == STUB_MAKE_TIME:
            words = struct.unpack("<IIII", uc.mem_read(sp, 16))
            hours, minutes, seconds, millis = (s32_of(w) for w in words)
            index = self.time_index
            self.time_index += 1
            self._log(
                STUB_NAMES[address],
                self._normalise(r0),
                s32_of(r1),
                s32_of(r2),
                s32_of(r3),
                hours,
                minutes,
                seconds,
                millis,
            )
            value = self.case["times"][min(index, len(self.case["times"]) - 1)]
            shadow = self.case["time_shadow"]
            if index < len(shadow) and shadow[index]:
                shadow_addr = SHADOW_ADDR + index * 0x10
                self._write_u64(shadow_addr, value)
                uc.mem_write(r0, struct.pack("<Q", 0xDEADBEEFDEADBEEF))
                uc.reg_write(arm.UC_ARM_REG_R0, shadow_addr)
            else:
                self._write_u64(r0, value)
        elif address == STUB_FIXED_POINT:
            value = s64_of(*struct.unpack("<II", uc.mem_read(r0, 8)))
            mul = s64_of(r2, r3)
            shift = struct.unpack("<I", uc.mem_read(sp, 4))[0]
            index = self.fixed_index
            self.fixed_index += 1
            self._log(STUB_NAMES[address], value, mul, shift)
            results = self.case["b_results"]
            if results is not None:
                result = results[min(index, len(results) - 1)]
            else:
                result = model_fixed_point(value, mul, shift)
            result &= MASK64
            uc.reg_write(arm.UC_ARM_REG_R0, result & 0xFFFFFFFF)
            uc.reg_write(arm.UC_ARM_REG_R1, (result >> 32) & 0xFFFFFFFF)
        elif address == STUB_DIVMOD:
            dividend = s64_of(r0, r1)
            divisor = s64_of(r2, r3)
            index = self.divmod_index
            self.divmod_index += 1
            self._log(STUB_NAMES[address], dividend, divisor)
            results = self.case["divmod_results"]
            if results is not None:
                quotient, remainder = results[min(index, len(results) - 1)]
            else:
                quotient, remainder = trunc_divmod(dividend, divisor)
            quotient &= MASK64
            remainder &= MASK64
            uc.reg_write(arm.UC_ARM_REG_R0, quotient & 0xFFFFFFFF)
            uc.reg_write(arm.UC_ARM_REG_R1, (quotient >> 32) & 0xFFFFFFFF)
            uc.reg_write(arm.UC_ARM_REG_R2, remainder & 0xFFFFFFFF)
            uc.reg_write(arm.UC_ARM_REG_R3, (remainder >> 32) & 0xFFFFFFFF)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _on_interrupt(self, uc, intno, user_data) -> None:
        if intno != 2:  # pragma: no cover - diagnostic path
            raise RuntimeError(f"unexpected ARM interrupt {intno}")
        ticks = self.case["ticks"]
        value = ticks[0] if ticks else 0
        self._log(STUB_NAMES[STUB_TICK], wrap_s64(value))
        value &= MASK64
        uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R1, (value >> 32) & 0xFFFFFFFF)

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.time_index = 0
        self.fixed_index = 0
        self.divmod_index = 0

        self.uc.mem_write(FUNC_ADDR, code + b"\x00" * (FUNC_SIZE - len(code)))
        self.uc.mem_write(DATA_ADDR, build_data(case))
        self.uc.mem_write(SHARED_ADDR, build_shared(case))
        self.uc.mem_write(SHADOW_ADDR, b"\x00" * SHADOW_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case.get("r0", 0x11111111))
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("r1", 0x22222222))
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("r2", 0x33333333))
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("r3", 0x44444444))
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        allowed = ((STACK_ADDR, STACK_SIZE), (DATA_ADDR, DATA_SIZE),
                   (SHARED_ADDR, SHARED_SIZE), (SHADOW_ADDR, SHADOW_SIZE))
        unexpected_writes = [
            (address, size)
            for address, size, _value in self.writes
            if not any(start <= address < start + length for start, length in allowed)
        ]

        return {
            "ret_lo": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "ret_hi": self.uc.reg_read(arm.UC_ARM_REG_R1),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "shared": bytes(self.uc.mem_read(SHARED_ADDR, SHARED_SIZE)),
            "shadow": bytes(self.uc.mem_read(SHADOW_ADDR, SHADOW_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret_lo", "ret_hi", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"])
            + "\n    cand=" + repr(cand["call_log"])
        )
    for page in ("data", "shared", "shadow"):
        if orig[page] != cand[page]:
            differing = [
                index
                for index, (left, right) in enumerate(zip(orig[page], cand[page]))
                if left != right
            ]
            problems.append(f"{page} page differs at offsets {differing[:16]}")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def make_cases() -> list[dict]:
    cases: list[dict] = []

    realistic_record = {
        "n": 3700000000000,
        "s": 0x0000000100000000,
        "f": 0x0FFB0FF0,
        "b": 0,
        "u": 0xFFB0FF0,
    }
    cases.append(
        base_case("realistic 2017-ish snapshot, DATETIME_0",
                  clock=0, selector=0, dt0=realistic_record,
                  ticks=[0x0000000100000000 + 268111])
    )
    cases.append(
        base_case("realistic snapshot selected through DATETIME_1",
                  clock=0, selector=1, dt1=realistic_record,
                  ticks=[0x0000000100000000 + 536223])
    )

    # Selector parity: bit 0 chooses the record, the other bits are ignored.
    for selector in (0x00000000, 0x00000001, 0x00000002, 0x00000003,
                     0x7FFFFFFE, 0x7FFFFFFF, 0x80000000, 0x80000001,
                     0xFFFFFFFE, 0xFFFFFFFF):
        cases.append(base_case(f"selector 0x{selector:08x}", selector=selector))

    # Clock boundaries.
    for clock in (0x0000000000000000, 0x0000000000000001,
                  0x00000000FFFFFFFF, 0x0000000100000000,
                  0x7FFFFFFFFFFFFFFF, 0x8000000000000000,
                  0xFFFFFFFFFFFFFFFF, 0x0123456789ABCDEF):
        cases.append(base_case(f"clock 0x{clock:016x}", clock=clock))

    # Calendar values: the first and third calls are independent.
    for times in (
        [0, 0, 0],
        [0, 1, 0],
        [-1, 1, 0],
        [1, -1, 1],
        [0x7FFFFFFFFFFFFFFF, 1, 0x7FFFFFFFFFFFFFFF],
        [0x8000000000000000, 0, 0x8000000000000000],
        [0xFFFFFFFFFFFFFFFF, 0xFFFFFFFFFFFFFFFF, 0xFFFFFFFFFFFFFFFF],
        [0, 3155760000000, 5],
        [-3155760000000, 3155760000000, -5],
        [0x123456789ABCDEF0, 0x0FEDCBA987654321, 0x00FEDCBA98765432],
    ):
        cases.append(base_case(f"times {times}", times=times))

    # 0x002B5B94 returns the destination pointer; read through it.
    for shadow in ([True, False, False], [False, True, False],
                   [False, False, True], [True, True, True]):
        cases.append(
            base_case(f"time return pointer shadow {shadow}",
                      times=[0x1111, 3155760000000, 0x2222], time_shadow=shadow)
        )

    # Tick delta versus the snapshot tick (below, equal, above, wrap).
    for tick, snapshot in (
        (0x0000000100000000, 0x0000000100000000),
        (0x0000000100000000, 0x00000000FFFFFFFF),
        (0x0000000100000000, 0x0000000100000001),
        (0x0000000000000000, 0x0000000000000001),
        (0x0000000000000000, 0xFFFFFFFFFFFFFFFF),
        (0xFFFFFFFFFFFFFFFF, 0x0000000000000000),
        (0x7FFFFFFFFFFFFFFF, 0x8000000000000000),
        (0x8000000000000000, 0x7FFFFFFFFFFFFFFF),
        (0x123456789ABCDEF0, 0x0123456789ABCDEF),
    ):
        record = dict(default_record())
        record["s"] = snapshot
        cases.append(
            base_case(
                f"tick 0x{tick:016x} snapshot 0x{snapshot:016x}",
                clock=0x12345678,
                dt0=record,
                ticks=[tick],
            )
        )

    # Tick frequency: positive, zero, negative, sign boundaries.
    for frequency in (0x0FFB0FF0, 0x00000001, 0x00000000, 0x7FFFFFFF,
                      0x80000000, 0xFFFFFFFF, 0x0000FFFF):
        record = dict(default_record())
        record["f"] = frequency
        cases.append(
            base_case(f"frequency 0x{frequency:08x}", dt0=record,
                      ticks=[0x0000000000001000])
        )

    # Nonzero residual field in the selected record.
    for residual in (0x0000000000000001, 0x00000000FFFFFFFF,
                     0xFFFFFFFFFFFFFFFF, 0x8000000000000000,
                     0x0123456789ABCDEF):
        record = dict(default_record())
        record["b"] = residual
        cases.append(
            base_case(f"residual 0x{residual:016x}", dt0=record,
                      ticks=[0x0000000000001000])
        )

    # Off-spec fixed-point results: the candidate must forward them.
    for results in ([0, 0], [-1, 1], [0x7FFFFFFFFFFFFFFF, 0x8000000000000000],
                    [0x8000000000000000, 0x7FFFFFFFFFFFFFFF],
                    [0x0123456789ABCDEF, 0xFEDCBA9876543210]):
        cases.append(
            base_case(f"fixed-point results {results}", b_results=results,
                      ticks=[0x0000000000002000])
        )

    # The 3,600,000 ms clamp: with delta == 2^32 the middle-word product
    # reduces to H1 == Q1, so the divmod quotient drives the clamp directly.
    delta = 1 << 32
    for quotient in (0, 3599999, 3600000, 3600001, 0x7FFFFFFF, 0x80000000,
                     0xFFFFFFFF, 0x100000000, -1, -(1 << 40),
                     0x7FFFFFFFFFFFFFFF, 0x8000000000000000):
        results = [(wrap_s64(quotient), 0), (0, 0), (0, 0)]
        cases.append(
            base_case(
                f"clamp quotient {wrap_s64(quotient)}",
                dt0=default_record(),
                ticks=[delta],
                divmod_results=results,
            )
        )

    # Off-spec divmod outputs: quotient and remainder forwarded verbatim.
    for results in (
        [(-1, -1), (-1, -1), (-1, -1)],
        [(0, 0), (0, 0), (0, 0)],
        [(0x7FFFFFFFFFFFFFFF, 0x7FFFFFFFFFFFFFFF),
         (0x8000000000000000, 0x8000000000000000),
         (0x0123456789ABCDEF, 0x1111111111111111)],
        [(12345, 67890), (-12345, -67890), (0xFFFFFFFF00000000, 3)],
    ):
        cases.append(
            base_case(f"divmod results {results}", divmod_results=results,
                      ticks=[0x0000000000003000])
        )

    # Both helper result streams together.
    cases.append(
        base_case("combined helper overrides",
                  times=[0x1000, 0x2000, 0x3000],
                  time_shadow=[False, True, False],
                  clock=0x4000,
                  selector=1,
                  dt0={"n": 1, "s": 2, "f": 3, "b": 4, "u": 5},
                  dt1={"n": 0x500000006, "s": 0x700000008, "f": 9,
                       "b": 0xA0000000B, "u": 0xC},
                  ticks=[0x0000000D0000000E],
                  b_results=[0x1111111111111111, 0x2222222222222222],
                  divmod_results=[(0x3333333333333333, 0x4444444444444444),
                                  (0x5555555555555555, 0x6666666666666666),
                                  (0x7777777777777777, 0x8888888888888888)])
    )

    # Caller-clobbered registers are not part of the contract but are logged.
    cases.append(
        base_case("arbitrary r0-r3", r0=0xDEADBEEF, r1=0x0BADF00D,
                  r2=0x13579BDF, r3=0x2468ACE0, ticks=[0x99999999])
    )

    # Fixed-seed sweep over the independent inputs.
    rng = random.Random(0x11C87C)
    for index in range(32):
        record0 = {
            "n": rng.getrandbits(64),
            "s": rng.getrandbits(64),
            "f": rng.getrandbits(32),
            "b": rng.getrandbits(64),
            "u": rng.getrandbits(32),
        }
        record1 = {
            "n": rng.getrandbits(64),
            "s": rng.getrandbits(64),
            "f": rng.getrandbits(32),
            "b": rng.getrandbits(64),
            "u": rng.getrandbits(32),
        }
        case = base_case(
            f"sweep {index:02d}",
            clock=rng.getrandbits(64),
            times=[wrap_s64(rng.getrandbits(64)) for _ in range(3)],
            selector=rng.getrandbits(32),
            dt0=record0,
            dt1=record1,
            ticks=[rng.getrandbits(64)],
        )
        if index % 3 == 0:
            case["b_results"] = [wrap_s64(rng.getrandbits(64)),
                                 wrap_s64(rng.getrandbits(64))]
        if index % 4 == 0:
            case["divmod_results"] = [
                (wrap_s64(rng.getrandbits(64)), wrap_s64(rng.getrandbits(64)))
                for _ in range(3)
            ]
        if index % 5 == 0:
            case["time_shadow"] = [bool(rng.getrandbits(1)) for _ in range(3)]
        cases.append(case)

    return cases


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
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing func_0011c87c (0x0011c87c)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          f"(relocations resolved).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("fraction_magic",
         "constexpr s64 kFractionMagic = static_cast<s64>(0x431BDE82D7B634DBull);",
         "constexpr s64 kFractionMagic = static_cast<s64>(0x431BDE82D7B634DCull);"),
        ("fraction_shift", "constexpr u32 kFractionShift = 18;",
         "constexpr u32 kFractionShift = 17;"),
        ("tick_numerator", "constexpr u32 kTickRateNumerator = 1000;",
         "constexpr u32 kTickRateNumerator = 1001;"),
        ("hour_ms", "constexpr u32 kMillisecondsPerHour = 3600000;",
         "constexpr u32 kMillisecondsPerHour = 3600001;"),
        ("clamp_condition",
         "(hour_remainder > 0) ? static_cast<u32>(hour_remainder) : 0u;",
         "(hour_remainder != 0) ? static_cast<u32>(hour_remainder) : 0u;"),
        ("selector_mask", "((selector & 1u) * kDateTimeSize)",
         "((selector & 2u) * kDateTimeSize)"),
        ("tick_field_offset",
         "const u32 snapshot_tick_low = LoadVolatileU32(record + 0x08);",
         "const u32 snapshot_tick_low = LoadVolatileU32(record + 0x0C);"),
        ("signed_high_product",
         "MultiplyMiddleSigned(tick_delta, static_cast<u64>(tick_scale))",
         "MultiplyHighSigned(tick_delta, static_cast<u64>(tick_scale))"),
        ("middle_word",
         "return static_cast<s64>((low >> 32) | (high << 32));",
         "return static_cast<s64>((low >> 31) | (high << 32));"),
        ("clock_subtract", "    combined -= static_cast<u64>(first_q);",
         "    combined += static_cast<u64>(first_q);"),
        ("span_divisor",
         "signed_divmod_64(static_cast<s64>(combined), span_q).remainder;",
         "signed_divmod_64(static_cast<s64>(combined), first_q).remainder;"),
        ("now_term", "static_cast<u64>(residual_ms) + snapshot_now;",
         "static_cast<u64>(residual_ms);"),
        ("residual_offset",
         "const u32 residual_high = LoadVolatileU32(record + 0x1C);",
         "const u32 residual_high = LoadVolatileU32(record + 0x18);"),
        ("hour_shift", "static_cast<u64>(hour_fraction) << 32",
         "static_cast<u64>(hour_fraction) << 31"),
        ("third_calendar",
         "scale_arg = epoch_2100 - epoch_2000_again;",
         "scale_arg = epoch_2100 - epoch_2000;"),
        ("returned_pointer_use",
         "const u64 epoch_2000 = static_cast<u64>(*calendar);",
         "const u64 epoch_2000 = static_cast<u64>(calendar_storage);"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
