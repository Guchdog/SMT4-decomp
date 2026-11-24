#!/usr/bin/env python3
"""Differential test for func_0014c5c0 (0x0014c5c0) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the func_0014c5c0 body,
resolves its six direct BL relocations to deterministic stubs at the pinned
original addresses, and runs the pinned original (extracted/exefs/code.bin)
against the candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log with every integer argument (all helpers take their
    arguments in r0-r3 and return in r0; 0x00282EA8 returns the float bit
    pattern in r0, matching the original's `vmov s0, r0`);
  * the full context page, the record page (including bytes a write must not
    touch) and the input sample page;
  * any write outside the context page, the record page and the private stack.

The original returns nothing; its r0 residue is not part of the contract (the
sole caller at 0x0014C448 ignores it), so r0 is not compared.

Coverage: both gate bytes in every 0/1/other form, the early return paths,
wrapping 64-bit delta totals at the sign boundaries, arbitrary signed divmod
quotients (so the hand-built 32..95 middle word is exercised independently of
the helper), the second divmod dividend observed in the call log, the
int64->float conversion result, the [0, 100] outlier clamp around every
boundary, histogram bins at 0/1/100/101, negative bins (including the
INT_MIN wrap to bin 0), the null/non-null record array, signed limit/count
orders including their sign boundaries and wrap-around entry offsets.
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
SOURCE = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_0014c5c0"

FUNC_ADDR = 0x0014C5C0
FUNC_SIZE = 480

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x300000

CTX_REGION = 0x00400000  # padding below the context absorbs negative bins
CTX_SIZE = 0x00020000
CTX_ADDR = 0x00410000
SAMPLE_ADDR = 0x00420000
SAMPLE_SIZE = 0x00001000
RECORD_ADDR = 0x00430000
RECORD_SIZE = 0x00002000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_F994 = 0x0014F994
STUB_LDIVMOD = 0x002B5B44
STUB_L2F = 0x00282EA8
STUB_BB270 = 0x002BB270
STUB_1523D8 = 0x001523D8

STUB_NAMES = {
    STUB_F994: "func_0014f994",
    STUB_LDIVMOD: "script_vm_func_002b5b44",
    STUB_L2F: "func_00282ea8",
    STUB_BB270: "engine_func_002bb270",
    STUB_1523D8: "engine_func_001523d8",
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

# AAPCS also makes d8-d15 callee-saved; the original explicitly vpush/vpops d8.
CALLEE_SAVED_FP = {
    f"d{index}": getattr(arm, f"UC_ARM_REG_D{index}") for index in range(8, 16)
}
CALLEE_SAVED_FP_START = {
    f"d{index}": (0xD800000000000000 | index) for index in range(8, 16)
}

# Context field offsets established from the ARM body.
OFF_TOTAL = 0x000
OFF_FRAME = 0x008
OFF_TICK_SUM = 0x00C
OFF_MAXIMUM = 0x010
OFF_SUM = 0x014
OFF_HISTOGRAM = 0x018
OFF_SAMPLE_TOTAL = 0x1AC
OFF_OUT_OF_RANGE = 0x1B0
OFF_ENABLE = 0x1B4
OFF_ACTIVE = 0x1F6
OFF_RECORD_ARRAY = 0x1F8
OFF_RECORD_PENDING = 0x1FC
OFF_RECORD_LIMIT = 0x200
OFF_RECORD_COUNT = 0x204


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def signed64(value: int) -> int:
    value &= 0xFFFFFFFFFFFFFFFF
    return value - (1 << 64) if value & (1 << 63) else value


def pair64(value: int) -> tuple[int, int]:
    value &= 0xFFFFFFFFFFFFFFFF
    return value & 0xFFFFFFFF, (value >> 32) & 0xFFFFFFFF


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0014c5c0" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"func_0014c5c0 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type != 28:  # R_ARM_CALL
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if name == rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        if target - pc != displacement * 4:
            raise RuntimeError("unaligned call displacement")
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | (displacement & 0xFFFFFF))
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
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
def build_ctx(case: dict) -> bytes:
    page = bytearray(CTX_SIZE)
    base = CTX_ADDR - CTX_REGION  # offset of ctx inside the compared region
    total = case.get("total", 0) & 0xFFFFFFFFFFFFFFFF
    low, high = pair64(total)
    struct.pack_into("<II", page, base + OFF_TOTAL, low, high)
    struct.pack_into("<I", page, base + OFF_FRAME, case.get("frame", 0x10) & 0xFFFFFFFF)
    struct.pack_into("<I", page, base + OFF_TICK_SUM, case.get("tick_sum", 0x20) & 0xFFFFFFFF)
    struct.pack_into("<I", page, base + OFF_MAXIMUM, case.get("maximum", 0xBF800000) & 0xFFFFFFFF)
    struct.pack_into("<I", page, base + OFF_SUM, case.get("sum", 0x41200000) & 0xFFFFFFFF)
    for index in range(101):
        struct.pack_into(
            "<I", page, base + OFF_HISTOGRAM + index * 4,
            (0x1000 + index) & 0xFFFFFFFF,
        )
    struct.pack_into("<I", page, base + OFF_SAMPLE_TOTAL, case.get("sample_total", 0x30) & 0xFFFFFFFF)
    struct.pack_into("<I", page, base + OFF_OUT_OF_RANGE, case.get("out_of_range", 0x40) & 0xFFFFFFFF)
    page[base + OFF_ENABLE] = case.get("enable", 1) & 0xFF
    page[base + OFF_ACTIVE] = case.get("active", 1) & 0xFF
    struct.pack_into("<I", page, base + OFF_RECORD_ARRAY, case.get("record_array", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, base + OFF_RECORD_PENDING, case.get("record_pending", 0x12345678) & 0xFFFFFFFF)
    struct.pack_into("<I", page, base + OFF_RECORD_LIMIT, case.get("record_limit", 4) & 0xFFFFFFFF)
    struct.pack_into("<I", page, base + OFF_RECORD_COUNT, case.get("record_count", 1) & 0xFFFFFFFF)
    return bytes(page)


def build_record_page(case: dict) -> bytes:
    page = bytearray(RECORD_SIZE)
    for index in range(RECORD_SIZE):
        page[index] = (0xA5 ^ (index & 0xFF)) & 0xFF
    return bytes(page)


def build_sample(case: dict) -> bytes:
    page = bytearray(SAMPLE_SIZE)
    delta = case.get("delta", 0x1234) & 0xFFFFFFFFFFFFFFFF
    low, high = pair64(delta)
    struct.pack_into("<II", page, 0, low, high)
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
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        # VFP instructions are undefined unless FPEXC.EN is set.
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(CTX_REGION, CTX_SIZE)
        self.uc.mem_map(SAMPLE_ADDR, SAMPLE_SIZE)
        self.uc.mem_map(RECORD_ADDR, RECORD_SIZE)
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
        self.ldiv_index = 0
        self.case: dict = {}

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        if address == STUB_F994:
            # No arguments; incoming scratch is not part of the contract.
            self.call_log.append((STUB_NAMES[address],))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("f994", 0x7777) & 0xFFFFFFFF)
        elif address == STUB_LDIVMOD:
            self.call_log.append((STUB_NAMES[address], r0, r1, r2, r3))
            self.ldiv_index += 1
            if self.ldiv_index == 1:
                quotient = self.case.get("quotient1", 0)
                remainder = self.case.get("remainder1", 0)
            else:
                quotient = self.case.get("quotient2", 0)
                remainder = self.case.get("remainder2", 0)
            q_low, q_high = pair64(quotient)
            r_low, r_high = pair64(remainder)
            uc.reg_write(arm.UC_ARM_REG_R0, q_low)
            uc.reg_write(arm.UC_ARM_REG_R1, q_high)
            uc.reg_write(arm.UC_ARM_REG_R2, r_low)
            uc.reg_write(arm.UC_ARM_REG_R3, r_high)
        elif address == STUB_L2F:
            self.call_log.append((STUB_NAMES[address], r0, r1))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("float_bits", 0) & 0xFFFFFFFF)
        elif address == STUB_BB270:
            # No declared arguments; the returned pointer feeds 0x001523D8.
            self.call_log.append((STUB_NAMES[address],))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("list", 0x00400000) & 0xFFFFFFFF)
        elif address == STUB_1523D8:
            # Sole argument is the list pointer returned by 0x002BB270.
            self.call_log.append((STUB_NAMES[address], r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("tag", 0x5A) & 0xFFFFFFFF)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.ldiv_index = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(CTX_REGION, build_ctx(case))
        self.uc.mem_write(SAMPLE_ADDR, build_sample(case))
        self.uc.mem_write(RECORD_ADDR, build_record_page(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, SAMPLE_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("entry_r2", 0x22222222))
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("entry_r3", 0x33333333))
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        for name, value in CALLEE_SAVED_FP_START.items():
            self.uc.reg_write(CALLEE_SAVED_FP[name], value)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_ctx = CTX_REGION <= address < CTX_REGION + CTX_SIZE
            in_record = RECORD_ADDR <= address < RECORD_ADDR + RECORD_SIZE
            if not (in_stack or in_ctx or in_record):
                unexpected_writes.append((address, size))

        return {
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "callee_saved_fp": {
                name: self.uc.reg_read(reg)
                for name, reg in CALLEE_SAVED_FP.items()
            },
            "call_log": list(self.call_log),
            "ctx": bytes(self.uc.mem_read(CTX_REGION, CTX_SIZE)),
            "sample": bytes(self.uc.mem_read(SAMPLE_ADDR, SAMPLE_SIZE)),
            "record": bytes(self.uc.mem_read(RECORD_ADDR, RECORD_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("pc", "sp", "callee_saved", "callee_saved_fp"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    for key in ("ctx", "sample", "record"):
        if orig[key] != cand[key]:
            first = next(
                index
                for index, (left, right) in enumerate(zip(orig[key], cand[key]))
                if left != right
            )
            address = {
                "ctx": CTX_REGION,
                "sample": SAMPLE_ADDR,
                "record": RECORD_ADDR,
            }[key] + first
            problems.append(
                f"{key} memory differs at 0x{address:08x}: "
                f"orig=0x{orig[key][first]:02x} cand=0x{cand[key][first]:02x}"
            )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "active": 1,
        "enable": 1,
        "delta": 0x0123456789ABCDEF,
        "total": 0x0011223344556677,
        "frame": 0x10,
        "tick_sum": 0x20,
        "maximum": 0xBF800000,       # -1.0f so most samples become the new max
        "sum": 0x41200000,           # 10.0f
        "sample_total": 0x30,
        "out_of_range": 0x40,
        "record_array": 0,
        "record_pending": 0x12345678,
        "record_limit": 4,
        "record_count": 1,
        "f994": 0x0000BEEF,
        "quotient1": 0x0000000123456789,
        "remainder1": 0xDEADBEEF,
        "quotient2": 0x00000000000003E8,
        "remainder2": 0x1234,
        "float_bits": 0x41200000,    # l2f returns 10.0f
        "list": RECORD_ADDR + 0x40,
        "tag": 0x5A,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- gate byte +0x1F6 (first check, before any side effect)
    for active in (0x00, 0x02, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"active byte 0x{active:02x}", active=active))
    cases.append(base_case("active 1 with record write", active=1,
                           record_array=RECORD_ADDR + 0x100,
                           record_limit=8, record_count=2))

    # --- gate byte +0x1B4 (after the total/counter/tick accumulation)
    for enable in (0x00, 0x02, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"enable byte 0x{enable:02x}", enable=enable))

    # --- wrapping 64-bit delta total
    for delta in (0, 1, 2, 0xFFFFFFFF, 0x100000000, 0x7FFFFFFFFFFFFFFF,
                  0x8000000000000000, 0xFFFFFFFFFFFFFFFF):
        cases.append(base_case(f"delta 0x{delta:016x}", delta=delta))
    for total in (0, 1, 0x7FFFFFFFFFFFFFFF, 0x8000000000000000,
                  0xFFFFFFFFFFFFFFFF, 0x0123456789ABCDEF):
        cases.append(base_case(f"total 0x{total:016x}", total=total))
        cases.append(base_case(f"total 0x{total:016x} + max delta",
                               total=total, delta=0xFFFFFFFFFFFFFFFF))

    # --- arbitrary signed divmod quotients: exposes the 32..95 middle word
    for quotient1 in (0, 1, -1, 2, 0x7FFFFFFF, 0x80000000,
                      0x7FFFFFFFFFFFFFFF, -0x8000000000000000,
                      0xFFFFFFFFFFFFFFFF, 0x0000000100000001,
                      0xFFFFFFFF00000001):
        cases.append(base_case(f"quotient1 {quotient1}", quotient1=quotient1))
        cases.append(base_case(f"quotient1 {quotient1} negative delta",
                               quotient1=quotient1, delta=0xFFFFFFFFFFFFFFFE))
        cases.append(base_case(f"quotient1 {quotient1} positive delta",
                               quotient1=quotient1, delta=0x00000001FFFFFFFF))

    # --- second divmod return values (int64 -> float input)
    for quotient2 in (0, 1, -1, 999, 1000, 1001, 1000000,
                      0x7FFFFFFFFFFFFFFF, -0x8000000000000000):
        cases.append(base_case(f"quotient2 {quotient2}", quotient2=quotient2))

    # --- float bit patterns returned by the l2f stub, covering the clamp and
    #     histogram branches (scale is 0x3CA78F51 ~= 0.02045408).
    for bits, note in (
        (0x00000000, "+0"),
        (0x80000000, "-0"),
        (0x3F800000, "1.0"),
        (0xBF800000, "-1.0"),
        (0x41200000, "10.0"),
        (0x42480000, "50.0"),
        (0x42C7FFFF, "just below 100"),
        (0x42C80000, "100.0"),
        (0x42C80001, "just above 100"),
        (0x42C90000, "100.5"),
        (0x43960000, "300.0"),
        (0x447A0000, "1000.0"),
        (0x451C4000, "2500.0"),
        (0x459C4000, "5000.0"),
        (0x461C4000, "10000.0"),
        (0xC0000000, "-2.0"),
        (0xC2C80000, "-100.0"),
        (0xC3960000, "-300.0"),
        (0xC47A0000, "-1000.0"),
        (0x7F800000, "+inf"),
        (0xFF800000, "-inf"),
        (0x7FC00000, "positive NaN"),
        (0xFFC00000, "negative NaN"),
        (0x7FFFFFFF, "largest NaN"),
        (0x4B189680, "10000000.0"),
        # Values chosen so the scaled sample lands on/next to the histogram
        # and clamp boundaries: 99.5, 100.0, just below/above 100, 101.0.
        (0x45980471, "99.5 sample"),
        (0x4598C800, "100.0 sample"),
        (0x4598C7FF, "99.99999 sample"),
        (0x4598C801, "100.00001 sample"),
        (0x459A4F1F, "101.0 sample"),
    ):
        cases.append(base_case(f"l2f bits 0x{bits:08x} ({note})",
                               float_bits=bits))

    # --- record append: null / capacity / signed order / wrapped offsets
    cases.append(base_case("record array null", record_array=0,
                           record_limit=100, record_count=0))
    cases.append(base_case("record full equal", record_array=RECORD_ADDR + 0x100,
                           record_limit=5, record_count=5))
    cases.append(base_case("record over full", record_array=RECORD_ADDR + 0x100,
                           record_limit=5, record_count=6))
    cases.append(base_case("record limit negative", record_array=RECORD_ADDR + 0x100,
                           record_limit=-1, record_count=0))
    cases.append(base_case("record limit 0 count 0", record_array=RECORD_ADDR + 0x100,
                           record_limit=0, record_count=0))
    cases.append(base_case("record limit 0 count -1", record_array=RECORD_ADDR + 0x100,
                           record_limit=0, record_count=0xFFFFFFFF))
    cases.append(base_case("record signed boundary",
                           record_array=RECORD_ADDR + 0x100,
                           record_limit=0x7FFFFFFF, record_count=0x80000000))
    cases.append(base_case("record count wraps offset",
                           record_array=RECORD_ADDR + 0x100,
                           record_limit=0x7FFFFFFF, record_count=0xFFFFFFFE))
    cases.append(base_case("record slot 20", record_array=RECORD_ADDR + 0x100,
                           record_limit=21, record_count=20))
    cases.append(base_case("record last slot", record_array=RECORD_ADDR + 0x100,
                           record_limit=0x7FFFFFFF, record_count=0x3DF))
    for pending in (0, 1, 0xFF, 0x80, 0x7FFFFFFF, 0xFFFFFFFF):
        cases.append(base_case(f"record pending 0x{pending:08x}",
                               record_array=RECORD_ADDR + 0x100,
                               record_limit=8, record_count=2,
                               record_pending=pending))
    for tag in (0, 1, 0x7F, 0x80, 0xFF, 0x1FF, 0xFFFFFFFF):
        cases.append(base_case(f"record tag 0x{tag:08x}",
                               record_array=RECORD_ADDR + 0x100,
                               record_limit=8, record_count=2, tag=tag))
    for helper in (0, 1, 0x00400000, 0x00410000, 0xFFFFFFFF):
        cases.append(base_case(f"list pointer 0x{helper:08x}",
                               record_array=RECORD_ADDR + 0x100,
                               record_limit=8, record_count=2, list=helper))

    # --- caller-clobbered scratch values must not influence behavior
    cases.append(base_case("scratch r2/r3", entry_r2=0xFFFFFFFF,
                           entry_r3=0x00000000))
    cases.append(base_case("max already above sample", maximum=0x447A0000,
                           float_bits=0x41200000))
    cases.append(base_case("max NaN", maximum=0x7FC00000,
                           float_bits=0x41200000))
    cases.append(base_case("sum NaN", sum=0x7FC00000, float_bits=0x41200000))

    # --- fixed-seed sweep over the independent operand streams
    rng = random.Random(0x14C5C0)
    float_pool = (0x00000000, 0x80000000, 0x3F800000, 0xBF800000,
                  0x41200000, 0x42C7FFFF, 0x42C80000, 0x42C80001,
                  0x42C90000, 0x4598C7FF, 0x4598C800, 0x4598C801,
                  0x459A4F1F, 0x45980471, 0x7F800000, 0xFF800000,
                  0x7FC00000, 0xFFC00000, 0xC2C80000, 0xC3960000,
                  0xC47A0000)
    for index in range(48):
        cases.append(
            base_case(
                f"random sweep {index}",
                delta=rng.getrandbits(64),
                total=rng.getrandbits(64),
                quotient1=signed64(rng.getrandbits(64)),
                remainder1=signed64(rng.getrandbits(64)),
                quotient2=signed64(rng.getrandbits(64)),
                remainder2=signed64(rng.getrandbits(64)),
                float_bits=rng.choice(float_pool),
                f994=rng.getrandbits(32),
                sample_total=rng.getrandbits(32),
                out_of_range=rng.getrandbits(32),
                frame=rng.getrandbits(32),
                tick_sum=rng.getrandbits(32),
                maximum=rng.choice(float_pool),
                sum=rng.choice(float_pool),
                active=rng.choice((1, 1, 1, 0, 2)),
                enable=rng.choice((1, 1, 1, 0, 0xFF)),
                record_array=rng.choice((0, RECORD_ADDR + 0x100)),
                record_limit=signed64(rng.getrandbits(32)),
                record_count=rng.choice((0, 1, 2, 4, 0x3DF, 0xFFFFFFF0)),
                record_pending=rng.getrandbits(32),
                tag=rng.getrandbits(32),
                list=rng.getrandbits(32),
            )
        )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
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
    print("Testing func_0014c5c0 (0x0014c5c0)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(call relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    controls = (
        ("tick_frequency", "constexpr s64 kTickFrequency = 0x0FFB0FF0;",
         "constexpr s64 kTickFrequency = 0x0FFB0FF1;"),
        ("microsecond_divisor", "constexpr s64 kMicrosecondDivisor = 1000;",
         "constexpr s64 kMicrosecondDivisor = 1001;"),
        ("histogram_limit", "constexpr s32 kHistogramLimit = 0x65;",
         "constexpr s32 kHistogramLimit = 0x64;"),
        ("range_maximum", "constexpr u32 kRangeMaximumBits = 0x42C80000u;",
         "constexpr u32 kRangeMaximumBits = 0x42C80001u;"),
        ("record_stride", "constexpr u32 kRecordStride = 8;",
         "constexpr u32 kRecordStride = 16;"),
        ("active_byte", "constexpr u32 kActiveByte = 0x1F6;",
         "constexpr u32 kActiveByte = 0x1F7;"),
        ("record_tag_offset", "constexpr u32 kRecordTag = 4;",
         "constexpr u32 kRecordTag = 6;"),
        ("tick_numerator", "constexpr s64 kTickNumerator = 0x3B9ACA0000000000LL;",
         "constexpr s64 kTickNumerator = 0x3B9ACA0000000001LL;"),
        ("value_scale", "constexpr f32 kValueScale = 0x1.4f1ea2p-6f;",
         "constexpr f32 kValueScale = 0x1.4f1ea4p-6f;"),
    )
    for name, old, new in controls:
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
