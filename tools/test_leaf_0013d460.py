#!/usr/bin/env python3
"""Differential test for func_0013d460 (0x0013d460) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the func_0013d460 body,
resolves its two direct calls to deterministic stubs, and runs the pinned
original (extracted/exefs/code.bin) against the candidate in separate Unicorn
machines with identical fixtures.

Compared outputs:
  * return r0 (the original leaves the final stream->cursor there), continuation
    PC, final SP and the callee-saved r4-r11;
  * the ordered call log: r0-r3 for 0x0014B6C0 and r0-r2 for 0x002B43B0 (its r3
    input is dead: the callee overwrites r3 before reading it);
  * the complete stream, packed, request and range fixture pages;
  * any emulated write outside the private stack and the stream page.

Coverage: all three flag-byte gates (zero, positive, negative signed byte at
bits 8..15), the count_04 zero/non-zero tail runs, the block-C gate on
packed->count_28 including its null/zero/negative forms, range-present spans
(flat, unaligned, negative, wrap-around) and range-absent walks, signed
count_bc values including zero and negatives, both entry walks with null list
owners and null resolvents (the typed walk faults at 0x0C in both bodies),
type words 2/3 vs all others, word_10 zero/non-zero, alignment units 0/1/2/3/4/
8/32 and non-power masks, cursor wrap boundaries, max_unit high-water values,
and helpers that advance the shared cursor or rewrite the list owner between
iterations.

Negative controls mutate the preamble alignment, the 0x2C block, the 0x88
stride, the 0x68 type header, the flag-byte shift, the entry-list offset and
the final 8-byte tail; each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch34_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_0013d460"

FUNC_ADDR = 0x0013D460
FUNC_SIZE = 1240

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers 0x0013D460 and both stub targets
STREAM_ADDR = 0x00800000
STREAM_SIZE = 0x00010000
PACKED_ADDR = 0x00810000
PACKED_SIZE = 0x00010000
REQUEST_ADDR = 0x00820000
REQUEST_SIZE = 0x00010000
RANGE_ADDR = 0x00830000
RANGE_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_B6C0 = 0x0014B6C0
STUB_43B0 = 0x002B43B0

STUB_NAMES = {
    STUB_B6C0: "emit_0014b6c0",
    STUB_43B0: "emit_002b43b0",
}

# Meaningful register arguments logged for each helper.  0x002B43B0's r3 is
# dead on entry, so it is deliberately not compared.
STUB_ARG_REGS = {STUB_B6C0: 4, STUB_43B0: 3}

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

# Entry lists live inside the packed page.  +0x2C points at LIST_TYPED and
# +0xC0 at LIST_RANGE; each 16-byte entry stores its self-relative record word
# at +0x28 and the record's type word at +0x0C.
LIST_RANGE_BASE = 0x400
LIST_TYPED_BASE = 0x800
LIST_SPARE_BASE = 0xC00
ENTRY_STRIDE = 0x10
ENTRY_INNER = 0x28
ENTRY_TYPE = 0x0C
DEFAULT_INNER = 0x10

PACKED_COUNT_28 = 0x28
PACKED_REL_2C = 0x2C
PACKED_B4 = 0xB4
PACKED_BC = 0xBC
PACKED_REL_C0 = 0xC0
PACKED_CC = 0xCC

# Request field offsets.
REQ_FLAGS = 0x00
REQ_COUNT_04 = 0x04
REQ_STRIDE_08 = 0x08
REQ_ENTRY_STRIDE_0C = 0x0C
REQ_WORD_10 = 0x10
REQ_RANGE_14 = 0x14
REQ_COUNT_1C = 0x1C


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0013d460" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"func_0013d460 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = None
            for address in STUB_NAMES:
                if f"{address:08x}" in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            if (target - pc) & 3:
                raise RuntimeError(f"unaligned call target 0x{target:08x}")
            if not -(1 << 23) <= displacement < (1 << 23):
                raise RuntimeError(f"call target out of BL range: 0x{target:08x}")
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into("<I", code, rel.offset, cond | (displacement & 0xFFFFFF))
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
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


# --------------------------------------------------------------------- fixtures
def build_stream(case: dict) -> bytes:
    page = bytearray(STREAM_SIZE)
    struct.pack_into("<I", page, 0, case.get("cursor", 0x100) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 4, case.get("unit", 4) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 8, case.get("max_unit", 0x40) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0xC, 0x5A5A000C)
    return bytes(page)


def write_list(page: bytearray, base: int, entries) -> None:
    for index, item in enumerate(entries):
        inner = item.get("inner", DEFAULT_INNER) & 0xFFFFFFFF
        entry = base + index * ENTRY_STRIDE
        struct.pack_into("<I", page, entry + ENTRY_INNER, inner)
        if inner != 0:
            record = entry + ENTRY_INNER + inner
            struct.pack_into(
                "<I", page, record + ENTRY_TYPE, item.get("type", 0) & 0xFFFFFFFF
            )
            # Non-type bytes around the record make out-of-bounds reads visible.
            struct.pack_into("<I", page, record + 0x10, 0x600D0000 | index)
            struct.pack_into("<I", page, record + 0x18, 0x0BAD0000 | index)


def build_packed(case: dict) -> bytes:
    page = bytearray(PACKED_SIZE)
    for offset in (0x00, 0x10, 0x20, 0x1000, 0x2000, 0x3800):
        struct.pack_into("<I", page, offset, 0xA5A50000 | offset)

    struct.pack_into("<I", page, PACKED_COUNT_28,
                     case.get("count_28", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, PACKED_B4, case.get("count_b4", 2) & 0xFFFFFFFF)
    struct.pack_into("<I", page, PACKED_BC, case.get("count_bc", 2) & 0xFFFFFFFF)
    struct.pack_into("<I", page, PACKED_CC, case.get("count_cc", 5) & 0xFFFFFFFF)

    rel_2c = case.get("rel_2c", LIST_TYPED_BASE - PACKED_REL_2C)
    struct.pack_into("<I", page, PACKED_REL_2C, 0 if rel_2c is None else rel_2c)
    rel_c0 = case.get("rel_c0", LIST_RANGE_BASE - PACKED_REL_C0)
    struct.pack_into("<I", page, PACKED_REL_C0, 0 if rel_c0 is None else rel_c0)

    for key, base in (("list_typed", LIST_TYPED_BASE),
                      ("list_range", LIST_RANGE_BASE),
                      ("list_spare", LIST_SPARE_BASE)):
        entries = case.get(key)
        if entries is not None:
            write_list(page, base, entries)
    return bytes(page)


def build_request(case: dict) -> bytes:
    page = bytearray(REQUEST_SIZE)
    struct.pack_into("<I", page, REQ_FLAGS, case.get("flags", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, REQ_COUNT_04,
                     case.get("count_04", 4) & 0xFFFFFFFF)
    struct.pack_into("<I", page, REQ_STRIDE_08,
                     case.get("stride_08", 2) & 0xFFFFFFFF)
    struct.pack_into("<I", page, REQ_ENTRY_STRIDE_0C,
                     case.get("entry_stride_0C", 3) & 0xFFFFFFFF)
    struct.pack_into("<I", page, REQ_WORD_10,
                     case.get("word_10", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, REQ_RANGE_14,
                     (RANGE_ADDR if case.get("range_present", True) else 0)
                     & 0xFFFFFFFF)
    struct.pack_into("<I", page, REQ_COUNT_1C,
                     case.get("count_1C", 3) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x18, 0x18181818)
    return bytes(page)


def build_range(case: dict) -> bytes:
    page = bytearray(RANGE_SIZE)
    begin = case.get("range_begin", 0x1000) & 0xFFFFFFFF
    end = case.get("range_end", 0x1010) & 0xFFFFFFFF
    struct.pack_into("<I", page, 0x164, begin)
    struct.pack_into("<I", page, 0x168, end)
    struct.pack_into("<I", page, 0x100, 0x1234ABCD)
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(STREAM_ADDR, STREAM_SIZE)
        self.uc.mem_map(PACKED_ADDR, PACKED_SIZE)
        self.uc.mem_map(REQUEST_ADDR, REQUEST_SIZE)
        self.uc.mem_map(RANGE_ADDR, RANGE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_UNMAPPED, self._on_unmapped)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.fault = None
        self.case: dict = {}
        self.b6c0_calls = 0
        self.type_calls = 0

    # ------------------------------------------------------------------ stubs
    def _on_unmapped(self, uc, access, address, size, value, user_data) -> bool:
        if self.fault is None:
            self.fault = (address, size, access)
        return False

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
            return  # private stack scratch, different frame layouts
        self.writes.append((address, size, value))

    def _bump_cursor(self, delta: int) -> None:
        if delta:
            current = struct.unpack("<I", self.uc.mem_read(STREAM_ADDR, 4))[0]
            self.uc.mem_write(
                STREAM_ADDR, struct.pack("<I", (current + delta) & 0xFFFFFFFF)
            )

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        args = tuple(
            uc.reg_read(register)
            for register in (
                arm.UC_ARM_REG_R0,
                arm.UC_ARM_REG_R1,
                arm.UC_ARM_REG_R2,
                arm.UC_ARM_REG_R3,
            )[: STUB_ARG_REGS[address]]
        )
        self.call_log.append((STUB_NAMES[address], args))

        if address == STUB_B6C0:
            self.b6c0_calls += 1
            self._bump_cursor(self.case.get("loop_advance", 0))
            mutate = self.case.get("b6c0_mutate_after")
            if mutate is not None and self.b6c0_calls == 1:
                self.uc.mem_write(
                    PACKED_ADDR + PACKED_REL_C0,
                    struct.pack("<I", mutate & 0xFFFFFFFF),
                )
        elif address == STUB_43B0:
            self.type_calls += 1
            self._bump_cursor(self.case.get("type_advance", 0))
            mutate = self.case.get("type_mutate_after")
            if mutate is not None and self.type_calls == 1:
                self.uc.mem_write(
                    PACKED_ADDR + PACKED_REL_2C,
                    struct.pack("<I", mutate & 0xFFFFFFFF),
                )

    # -------------------------------------------------------------- execution
    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for name, args in log:
            out = []
            for arg in args:
                if isinstance(arg, int) and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE:
                    out.append("<stack>")
                else:
                    out.append(arg)
            normalised.append((name, tuple(out)))
        return normalised

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.fault = None
        self.case = case
        self.b6c0_calls = 0
        self.type_calls = 0

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(STREAM_ADDR, build_stream(case))
        self.uc.mem_write(PACKED_ADDR, build_packed(case))
        self.uc.mem_write(REQUEST_ADDR, build_request(case))
        self.uc.mem_write(RANGE_ADDR, build_range(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, STREAM_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, PACKED_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, REQUEST_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        # The incoming ip word is never read: a distinctive value proves it.
        self.uc.reg_write(arm.UC_ARM_REG_R12, 0xA5A5A5A5)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError:
            if self.fault is None:
                raise

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stream = STREAM_ADDR <= address < STREAM_ADDR + STREAM_SIZE
            if not in_stream:
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "fixtures": {
                "stream": bytes(self.uc.mem_read(STREAM_ADDR, STREAM_SIZE)),
                "packed": bytes(self.uc.mem_read(PACKED_ADDR, PACKED_SIZE)),
                "request": bytes(self.uc.mem_read(REQUEST_ADDR, REQUEST_SIZE)),
                "range": bytes(self.uc.mem_read(RANGE_ADDR, RANGE_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
            "fault": self.fault,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems: list[str] = []
    if (orig["fault"] is None) != (cand["fault"] is None):
        problems.append(f"fault presence: orig={orig['fault']} cand={cand['fault']}")
    if orig["fault"] is not None:
        if orig["fault"][0] != cand["fault"][0]:
            problems.append(
                f"fault address: orig=0x{orig['fault'][0]:08x} "
                f"cand=0x{cand['fault'][0]:08x}"
            )
        if orig["call_log"] != cand["call_log"]:
            problems.append(
                "call_log before fault:\n    orig="
                + repr(orig["call_log"])
                + "\n    cand="
                + repr(cand["call_log"])
            )
        return problems

    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            first = next(
                index
                for index, (left, right) in enumerate(zip(value, cand["fixtures"][key]))
                if left != right
            )
            problems.append(
                f"fixture {key} differs at +0x{first:x}: "
                f"orig=0x{value[first]:02x} cand=0x{cand['fixtures'][key][first]:02x}"
            )
    if orig["unexpected_writes"] != cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


# ----------------------------------------------------------------------- cases
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "cursor": 0x100,
        "unit": 4,
        "max_unit": 0x40,
        "flags": 0,
        "count_04": 4,
        "stride_08": 2,
        "entry_stride_0C": 3,
        "word_10": 0,
        "count_1C": 3,
        "count_b4": 2,
        "count_bc": 2,
        "count_cc": 5,
        "count_28": 0,
        "range_present": True,
        "range_begin": 0x1000,
        "range_end": 0x1010,
        "list_range": [{"type": 5}, {"type": 6}],
        "list_typed": [{"type": 2}, {"type": 1}],
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- baseline and the two tail layouts
    cases.append(base_case("range present baseline"))
    for count_04 in (0, 1, 2, 4, 0xFFFFFFFF, 0x40000000):
        cases.append(base_case(f"count_04={count_04:#x}", count_04=count_04))
        cases.append(base_case(f"count_04={count_04:#x}, range absent",
                               count_04=count_04, range_present=False))

    # --- preamble 4*stride and stride_08 extremes
    for stride in (0, 1, 2, 3, 0x40000000, 0xFFFFFFFF):
        cases.append(base_case(f"stride_08={stride:#x}", stride_08=stride))
        cases.append(base_case(f"stride_08={stride:#x}, selector",
                               stride_08=stride, flags=0x00000100,
                               count_28=2))

    # --- block-C per-entry stride (request+0x0C) extremes
    for stride in (0, 1, 2, 3, 0x40000000, 0xFFFFFFFF):
        cases.append(base_case(f"entry_stride_0C={stride:#x}",
                               entry_stride_0C=stride,
                               flags=0x00000100, count_28=3,
                               list_typed=[{"type": 2}, {"type": 1},
                                           {"type": 0}]))
        cases.append(base_case(f"entry_stride_0C={stride:#x}, range absent",
                               entry_stride_0C=stride,
                               flags=0x00000100, count_28=3,
                               range_present=False,
                               list_typed=[{"type": 2}, {"type": 1},
                                           {"type": 0}]))

    # --- range span rounding and 32-bit wrap
    for begin, end in (
        (0x1000, 0x1000), (0x1000, 0x1001), (0x1000, 0x1004),
        (0x1000, 0x1010), (0x1001, 0x1010), (0x1010, 0x1000),
        (0x1000, 0x0FFF), (0x80000000, 0x7FFFFFFF),
        (0xFFFFFFFC, 0x00000004), (0xFFFFFFFF, 0x00000000),
    ):
        cases.append(base_case(f"range span {begin:#x}->{end:#x}",
                               range_begin=begin, range_end=end))

    # --- five initial reservations: counts and wrap
    for b4, cc in ((0, 0), (1, 1), (3, 7), (0xFFFFFFFF, 0xFFFFFFFF),
                   (0x40000000, 0x20000000), (0x11111111, 0x22222222)):
        cases.append(base_case(f"counts b4={b4:#x} cc={cc:#x}",
                               count_b4=b4, count_cc=cc))

    # --- range-absent entry walk: every signed bound
    for count in (0, 1, 2, 3, 4, -1, -2, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"count_bc={count}", range_present=False,
                               count_bc=count,
                               list_range=[{"type": 5 + i} for i in range(4)]))
    cases.append(base_case("range absent null list owner", range_present=False,
                           count_bc=2, rel_c0=None))
    cases.append(base_case("range absent null entries", range_present=False,
                           count_bc=3,
                           list_range=[{"inner": 0}, {"inner": 0}, {"inner": 0}]))
    cases.append(base_case("range absent mixed null entries", range_present=False,
                           count_bc=3,
                           list_range=[{"type": 1}, {"inner": 0}, {"type": 2}]))
    cases.append(base_case("range absent word_10 non-zero", range_present=False,
                           word_10=0xDEADBEEF))
    cases.append(base_case("range absent word_10 bit0", range_present=False,
                           word_10=0x00000001, count_bc=3))
    cases.append(base_case("range absent helper advances cursor",
                           range_present=False, loop_advance=0x40))
    cases.append(base_case("range absent helper rewrites owner",
                           range_present=False, count_bc=3,
                           list_range=[{"type": 1}, {"type": 2}, {"type": 3}],
                           list_spare=[{"type": 7}, {"type": 8}, {"type": 9}],
                           b6c0_mutate_after=LIST_SPARE_BASE - PACKED_REL_C0))

    # --- block C gate on the flag byte and packed->count_28
    for flags in (0x00000000, 0x00000100, 0x00007F00, 0x00008000,
                  0x0000FF00, 0xFFFF00FF, 0x00000080, 0xFFFFFFFF,
                  0x0000FE00):
        cases.append(base_case(f"flags={flags:#010x}", flags=flags,
                               count_28=2,
                               list_typed=[{"type": 2}, {"type": 3}]))
    for count in (0, 1, 2, 3, 4, -1, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"count_28={count}", flags=0x00000100,
                               count_28=count,
                               list_typed=[{"type": t} for t in (2, 3, 1, 0)]))

    # --- typed-entry loop
    cases.append(base_case("typed all non-matching", flags=0x00000100,
                           count_28=4,
                           list_typed=[{"type": 0}, {"type": 1}, {"type": 4},
                                       {"type": 0xFFFFFFFF}]))
    cases.append(base_case("typed all matching", flags=0x00000100, count_28=3,
                           list_typed=[{"type": 2}, {"type": 3}, {"type": 2}]))
    cases.append(base_case("typed null list owner faults", flags=0x00000100,
                           count_28=2, rel_2c=None))
    cases.append(base_case("typed null entry faults", flags=0x00000100,
                           count_28=2,
                           list_typed=[{"inner": 0}, {"type": 2}]))
    cases.append(base_case("typed helper advances cursor", flags=0x00000100,
                           count_28=2, type_advance=0x30,
                           list_typed=[{"type": 2}, {"type": 3}]))
    cases.append(base_case("typed helper rewrites owner", flags=0x00000100,
                           count_28=3,
                           list_typed=[{"type": 2}, {"type": 3}, {"type": 2}],
                           list_spare=[{"type": 5}, {"type": 3}, {"type": 3}],
                           type_mutate_after=LIST_SPARE_BASE - PACKED_REL_2C))
    cases.append(base_case("typed loop with range absent", flags=0x00000100,
                           range_present=False, count_bc=1,
                           list_typed=[{"type": 2}, {"type": 3}]))

    # --- alignment unit, cursor and max_unit boundaries
    for unit in (0, 1, 2, 3, 4, 8, 16, 0x20, 0x40, 0xFFFFFFFE):
        cases.append(base_case(f"unit={unit:#x}", unit=unit))
        cases.append(base_case(f"unit={unit:#x}, range absent", unit=unit,
                               range_present=False, flags=0x00000100,
                               count_28=2))
    for cursor in (0, 1, 3, 4, 5, 0x100, 0xFFFFFFF0, 0xFFFFFFFF,
                   0xFFFFFFE0, 0x7FFFFFFF):
        cases.append(base_case(f"cursor={cursor:#x}", cursor=cursor))
        cases.append(base_case(f"cursor={cursor:#x}, range absent",
                               cursor=cursor, range_present=False))
    for max_unit in (0, 1, 0x10, 0x1F, 0x20, 0x21, 0xFFFFFFFF):
        cases.append(base_case(f"max_unit={max_unit:#x}", max_unit=max_unit))
        cases.append(base_case(f"max_unit={max_unit:#x}, unit 0x20",
                               max_unit=max_unit, unit=0x20))

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
        suffix = "fault" if orig["fault"] is not None else (
            f"{len(orig['call_log'])} calls")
        print(f"  [PASS] {case['name']}  ({suffix})")
        passed += 1
    return passed


def main() -> None:
    print("Testing func_0013d460 (0x0013d460)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          "(call relocations resolved).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("preamble_alignment", "constexpr u32 kPreambleAlignment = 0x20;",
         "constexpr u32 kPreambleAlignment = 0x1F;"),
        ("flag_block", "constexpr u32 kFlagBlockBytes = 0x2C;",
         "constexpr u32 kFlagBlockBytes = 0x28;"),
        ("initial_stride", "constexpr u32 kInitialStrideBytes = 0x88;",
         "constexpr u32 kInitialStrideBytes = 0x87;"),
        ("type_header", "constexpr u32 kTypeHeader = 0x68;",
         "constexpr u32 kTypeHeader = 0x67;"),
        ("selector_shift", "constexpr u32 kFlagsByteShift = 8;",
         "constexpr u32 kFlagsByteShift = 7;"),
        ("entry_list", "constexpr u32 kEntryListRange = 0xC0;",
         "constexpr u32 kEntryListRange = 0xC4;"),
        ("final_tail", "constexpr u32 kFinalSpanBytes = 8;",
         "constexpr u32 kFinalSpanBytes = 9;"),
        ("marker", "const u32 marker = (word_10 != 0) ? 1u : 0u;",
         "const u32 marker = 1u;"),
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
