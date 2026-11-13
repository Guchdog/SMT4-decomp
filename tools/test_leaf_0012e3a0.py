#!/usr/bin/env python3
"""Differential test for func_0012e3a0 (0x0012e3a0) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the func_0012e3a0 body,
resolves its three direct calls to deterministic stubs, and runs the pinned
original (extracted/exefs/code.bin) against the candidate in separate Unicorn
machines with identical fixtures.

Compared outputs:
  * continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every register argument plus the two architected
    stack words of 0x002B4454;
  * the stream cursor/unit page, the full packet page, the range page and the
    opaque word2 target page;
  * any emulated write outside the private stack and the two writable fixtures.

r0 is not part of the contract: the original is a void builder that leaves in r0
whatever the last flag test/helper happened to produce, and both callers ignore
it.  The runner still records it for diagnostics but the comparison does not
treat it as an observable result.

Coverage: both range-present and range-absent layouts, aligned/unaligned/
negative spans, every signed loop bound including zero and negative counts,
zero/non-zero 0x002B4454 stack words, null and non-null list owners, null entry
resolvents, all flag-byte forms (including 0x80), type words 2/3 vs all other
values, count wrap-around, alignment units 0/1/2/4/8/32 and a non-power-of-two
mask, cursors at wrap boundaries, and helpers that advance the shared cursor or
rewrite the list owner between iterations.

Negative controls mutate a reservation stride, the flag-byte shift, the type
header size and the final tail size; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_0012e3a0"

FUNC_ADDR = 0x0012E3A0
FUNC_SIZE = 772

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers 0x12E3A0 and every stub below 0x300000
STREAM_ADDR = 0x00800000
STREAM_SIZE = 0x00010000
PACKED_ADDR = 0x00810000
PACKED_SIZE = 0x00010000
RANGE_ADDR = 0x00820000
RANGE_SIZE = 0x00010000
EXTRA_ADDR = 0x00830000
EXTRA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_4454 = 0x002B4454
STUB_B6C0 = 0x0014B6C0
STUB_43B0 = 0x002B43B0

STUB_NAMES = {
    STUB_4454: "reserve_002b4454",
    STUB_B6C0: "emit_0014b6c0",
    STUB_43B0: "emit_002b43b0",
}

# Architected stack words each helper receives.
STACK_ARGS = {STUB_4454: 2, STUB_B6C0: 0, STUB_43B0: 0}

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

# List owners live inside the packet page: +0x2C points at LIST_A, +0xC0 at
# LIST_B.  Each 16-byte entry stores its self-relative record word at +0x28.
LIST_A_BASE = 0x400
LIST_B_BASE = 0x800
LIST_C_BASE = 0xC00
ENTRY_STRIDE = 0x10
ENTRY_INNER = 0x28
ENTRY_TYPE = 0x0C
DEFAULT_INNER = 0x10

PACKED_B4 = 0xB4
PACKED_BC = 0xBC
PACKED_CC = 0xCC
PACKED_REL_2C = 0x2C
PACKED_REL_C0 = 0xC0
PACKED_COUNT_28 = 0x28


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0012e3a0" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"func_0012e3a0 not found in {obj_file}: {sorted(funcs)}")

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
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
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
    struct.pack_into("<I", page, 8, 0x5A5A0008)
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
            page[record + ENTRY_TYPE + 4] = 0xC0 | (index & 0x3F)


def build_packed(case: dict) -> bytes:
    page = bytearray(PACKED_SIZE)
    for offset in (0x10, 0x20, 0x1000, 0x2000, 0x3800):
        struct.pack_into("<I", page, offset, 0xA5A50000 | offset)

    struct.pack_into("<I", page, PACKED_B4, case.get("count_b4", 2) & 0xFFFFFFFF)
    struct.pack_into("<I", page, PACKED_BC, case.get("count_bc", 2) & 0xFFFFFFFF)
    struct.pack_into("<I", page, PACKED_CC, case.get("count_cc", 5) & 0xFFFFFFFF)
    struct.pack_into("<I", page, PACKED_COUNT_28,
                     case.get("count_28", 2) & 0xFFFFFFFF)

    rel_2c = case.get("rel_2c", LIST_A_BASE - PACKED_REL_2C)
    struct.pack_into("<I", page, PACKED_REL_2C, 0 if rel_2c is None else rel_2c)
    rel_c0 = case.get("rel_c0", LIST_B_BASE - PACKED_REL_C0)
    struct.pack_into("<I", page, PACKED_REL_C0, 0 if rel_c0 is None else rel_c0)

    list_a = case.get("list_a")
    if list_a is not None:
        write_list(page, LIST_A_BASE, list_a)
    list_b = case.get("list_b")
    if list_b is not None:
        write_list(page, LIST_B_BASE, list_b)
    list_c = case.get("list_c")
    if list_c is not None:
        write_list(page, LIST_C_BASE, list_c)
    return bytes(page)


def build_range(case: dict):
    if not case.get("range_present", True):
        return None
    page = bytearray(RANGE_SIZE)
    begin = case.get("range_begin", 0x1000) & 0xFFFFFFFF
    end = case.get("range_end", 0x1010) & 0xFFFFFFFF
    struct.pack_into("<I", page, 0x164, begin)
    struct.pack_into("<I", page, 0x168, end)
    struct.pack_into("<I", page, 0x100, 0x1234ABCD)
    return bytes(page)


def read_c_string(uc, address: int, limit: int = 32) -> bytes:  # pragma: no cover
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class E3A0Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(STREAM_ADDR, STREAM_SIZE)
        self.uc.mem_map(PACKED_ADDR, PACKED_SIZE)
        self.uc.mem_map(RANGE_ADDR, RANGE_SIZE)
        self.uc.mem_map(EXTRA_ADDR, EXTRA_SIZE)
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
        self.b6c0_calls = 0
        self.type_calls = 0

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _bump_cursor(self, delta: int) -> None:
        if delta:
            current = struct.unpack(
                "<I", self.uc.mem_read(STREAM_ADDR, 4)
            )[0]
            self.uc.mem_write(
                STREAM_ADDR, struct.pack("<I", (current + delta) & 0xFFFFFFFF)
            )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        self.call_log.append(
            (STUB_NAMES[address], (r0, r1, r2, r3) + self._stack_words(STACK_ARGS[address]))
        )

        if address == STUB_4454:
            self._bump_cursor(self.case.get("reserve_advance", 0))
            new_unit = self.case.get("reserve_unit")
            if new_unit is not None:
                self.uc.mem_write(STREAM_ADDR + 4,
                                  struct.pack("<I", new_unit & 0xFFFFFFFF))
        elif address == STUB_B6C0:
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
        self.case = case
        self.b6c0_calls = 0
        self.type_calls = 0

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(STREAM_ADDR, build_stream(case))
        self.uc.mem_write(PACKED_ADDR, build_packed(case))
        range_page = build_range(case)
        self.uc.mem_write(RANGE_ADDR, range_page if range_page else b"\x00" * RANGE_SIZE)
        self.uc.mem_write(EXTRA_ADDR, b"\x00" * EXTRA_SIZE)
        self.uc.mem_write(EXTRA_ADDR, struct.pack("<I", 0xE0E0E0E0))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        word2 = case.get("word2", 0)
        range_ptr = RANGE_ADDR if case.get("range_present", True) else 0
        stack = struct.pack(
            "<IIII",
            case.get("word0", 0x11111111) & 0xFFFFFFFF,
            case.get("word1", 0x22222222) & 0xFFFFFFFF,
            word2 & 0xFFFFFFFF,
            range_ptr,
        )
        self.uc.mem_write(ENTRY_SP, stack)
        self.uc.mem_write(ENTRY_SP + 0x10, struct.pack("<I", 0xE7E7E7E7))

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, STREAM_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, PACKED_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("flags", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("count4", 4) & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_stream = STREAM_ADDR <= address < STREAM_ADDR + STREAM_SIZE
            in_packed = PACKED_ADDR <= address < PACKED_ADDR + PACKED_SIZE
            if not (in_stack or in_stream or in_packed):
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
                "range": bytes(self.uc.mem_read(RANGE_ADDR, RANGE_SIZE)),
                "extra": bytes(self.uc.mem_read(EXTRA_ADDR, EXTRA_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
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
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} was modified differently")
    if orig["unexpected_writes"] != cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "cursor": 0x100,
        "unit": 4,
        "count_b4": 2,
        "count_bc": 2,
        "count_cc": 5,
        "count_28": 2,
        "count4": 4,
        "flags": 0,
        "word0": 0x11111111,
        "word1": 0x22222222,
        "word2": 0,
        "range_present": True,
        "list_a": [{"type": 2}, {"type": 1}],
        "list_b": [{"type": 5}, {"type": 6}],
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- baseline: range present, no type loop, no helper side effects
    cases.append(base_case("range present baseline"))
    cases.append(base_case("range present, flat span", range_begin=0x2000,
                           range_end=0x2000))
    for begin, end in (
        (0x1000, 0x100F),   # +15 -> rounded down to +12
        (0x1001, 0x1010),   # +15
        (0x1000, 0x1001),   # +1 -> 0
        (0x1000, 0x1002),   # +2 -> 0
        (0x1000, 0x1003),   # +3 -> 0
        (0x1000, 0x1004),   # +4
        (0x1000, 0x0FFF),   # -1 -> 0xFFFFFFFC
        (0x1000, 0x0FFE),   # -2
        (0x1000, 0x0FFD),   # -3
        (0x1010, 0x1000),   # -0x10
        (0x80000000, 0x7FFFFFFF),  # wrap-around negative
    ):
        cases.append(base_case(f"range span {begin:#x}->{end:#x}",
                               range_begin=begin, range_end=end))
    cases.append(base_case("range present huge counts", count_b4=0xFFFFFFFF,
                           count_cc=0xFFFFFFFF))
    cases.append(base_case("range present count wrap", count_b4=0x40000000,
                           count_cc=0x20000000))

    # --- range absent: the 0x0014B6C0 loop and the +8 tail
    for count in (0, 1, 2, 3):
        cases.append(base_case(f"range absent count_bc={count}",
                               range_present=False, count_bc=count,
                               list_b=[{"type": 5 + i} for i in range(4)]))
    for count in (-1, -2, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"range absent signed count_bc={count}",
                               range_present=False, count_bc=count))
    cases.append(base_case("range absent null list owner", range_present=False,
                           count_bc=2, rel_c0=None))
    cases.append(base_case("range absent null entries", range_present=False,
                           count_bc=2,
                           list_b=[{"inner": 0}, {"inner": 0}]))
    cases.append(base_case("range absent mixed null entries", range_present=False,
                           count_bc=3,
                           list_b=[{"type": 1}, {"inner": 0}, {"type": 2}]))
    cases.append(base_case("range absent word2 non-zero", range_present=False,
                           word2=0xDEADBEEF))
    cases.append(base_case("range absent helper advances cursor",
                           range_present=False, loop_advance=0x40))
    cases.append(base_case("range absent helper rewrites owner",
                           range_present=False, count_bc=3,
                           list_b=[{"type": 1}, {"type": 2}, {"type": 3}],
                           list_c=[{"type": 7}, {"type": 8}, {"type": 9}],
                           b6c0_mutate_after=LIST_C_BASE - PACKED_REL_C0))

    # --- r3 count4 layouts
    for count4 in (0, 1, 2, 4, 0xFFFFFFFF, 0x40000000):
        cases.append(base_case(f"count4={count4:#x}", count4=count4))
        cases.append(base_case(f"count4={count4:#x}, range absent",
                               count4=count4, range_present=False))

    # --- flag byte at bits 8..15 gates the type loop
    cases.append(base_case("flags 0x00000100", flags=0x00000100))
    cases.append(base_case("flags 0x00007f00", flags=0x00007F00))
    cases.append(base_case("flags 0x00008000", flags=0x00008000))
    cases.append(base_case("flags 0x0000ff00", flags=0x0000FF00))
    cases.append(base_case("flags 0xffff00ff (byte 0)", flags=0xFFFF00FF))
    cases.append(base_case("flags 0x00000080 (byte 0)", flags=0x00000080))
    cases.append(base_case("flags 0xffffffff", flags=0xFFFFFFFF))
    cases.append(base_case("flags 0x00000200", flags=0x00000200,
                           list_a=[{"type": 2}, {"type": 3}]))

    # --- type loop populations and signed bound
    for count in (0, 1, 2, 3, 4, -1, 0x80000000):
        cases.append(base_case(f"type count_28={count}", count_28=count,
                               flags=0x00000100,
                               list_a=[{"type": t} for t in (2, 3, 1, 0)]))
    cases.append(base_case("type list all non-matching", flags=0x00000100,
                           count_28=4,
                           list_a=[{"type": 0}, {"type": 1}, {"type": 4},
                                   {"type": 0xFFFFFFFF}]))
    cases.append(base_case("type list all matching", flags=0x00000100,
                           count_28=3,
                           list_a=[{"type": 2}, {"type": 3}, {"type": 2}]))
    # A null type-loop entry is a fault in the original: it dereferences the
    # null element at 0x0012E600.  That invalid-input domain is intentionally
    # not exercised (see the function record).
    cases.append(base_case("type list owner absent, loop skipped",
                           flags=0x00000000, count_28=2, rel_2c=None))
    cases.append(base_case("type helper advances cursor", flags=0x00000100,
                           count_28=2, type_advance=0x30,
                           list_a=[{"type": 2}, {"type": 3}]))
    cases.append(base_case("type helper rewrites owner", flags=0x00000100,
                           count_28=3,
                           list_a=[{"type": 2}, {"type": 3}, {"type": 2}],
                           list_c=[{"type": 5}, {"type": 3}, {"type": 3}],
                           type_mutate_after=LIST_C_BASE - PACKED_REL_2C))
    cases.append(base_case("type loop with range absent", flags=0x00000100,
                           range_present=False, count_bc=1,
                           list_a=[{"type": 2}, {"type": 3}]))

    # --- alignment unit and cursor boundaries
    for unit in (0, 1, 2, 3, 4, 8, 16, 0x20):
        cases.append(base_case(f"unit {unit}", unit=unit))
        cases.append(base_case(f"unit {unit}, range absent", unit=unit,
                               range_present=False))
    for cursor in (0, 1, 3, 4, 5, 0x100, 0xFFFFFFF0, 0xFFFFFFFF):
        cases.append(base_case(f"cursor {cursor:#x}", cursor=cursor))
        cases.append(base_case(f"cursor {cursor:#x}, range absent",
                               cursor=cursor, range_present=False))

    # --- 0x002B4454 stack words and cursor/unit side effects
    cases.append(base_case("reserve stack words distinct", word0=0xCAFEBABE,
                           word1=0x0BADF00D))
    cases.append(base_case("reserve stack words distinct, range absent",
                           word0=0xCAFEBABE, word1=0x0BADF00D,
                           range_present=False))
    cases.append(base_case("reserve advances cursor", reserve_advance=0x28))
    cases.append(base_case("reserve changes unit", reserve_unit=8))
    cases.append(base_case("reserve advances cursor and changes unit",
                           reserve_advance=0x28, reserve_unit=0x20,
                           range_present=False))
    cases.append(base_case("reserve changes unit to zero", reserve_unit=0))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = E3A0Runner().run(orig_code, case)
        cand = E3A0Runner().run(cand_code, case)
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
    print("Testing func_0012e3a0 (0x0012e3a0)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("initial_stride", "constexpr u32 kInitialStrideBytes = 0x88;",
         "constexpr u32 kInitialStrideBytes = 0x87;"),
        ("flag_shift", "constexpr u32 kFlagsByteShift = 8;",
         "constexpr u32 kFlagsByteShift = 7;"),
        ("type_header", "constexpr u32 kTypeHeader = 0x68;",
         "constexpr u32 kTypeHeader = 0x67;"),
        ("range_tail", "constexpr u32 kRangeTail = 8;",
         "constexpr u32 kRangeTail = 9;"),
        ("entry_stride", "constexpr u32 kEntryStride = 0x10;",
         "constexpr u32 kEntryStride = 0x0C;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = E3A0Runner().run(orig_code, case)
            bad = E3A0Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
