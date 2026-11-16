#!/usr/bin/env python3
"""Differential test for camp_func_00298bdc (0x00298bdc) using Unicorn ARM.

Compiles src/engine/leaf_batch33_c.cpp, extracts the camp_func_00298bdc body,
resolves its direct calls to deterministic stubs at the pinned original
addresses, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and the restored callee-saved r4-r11;
  * the ordered call log with every register argument (the scratch pointer is
    normalised to "<stack>"; no helper takes a stack argument);
  * the full camp work block, the 0x0043DA90 global page, the fallback record
    page and the category record page, byte for byte;
  * every emulated write must stay in the private stack or the work block.

Coverage:
  * the three-read row-count rule: second >= first keeps the first, second <
    first takes the third, non-positive counts skip the loop;
  * duplicate and distinct categories, category 23 (last in-bounds marker) and
    the negative fallback category;
  * every mask shape: zero, single bit, bit 0 only, first/second/third set-bit
    ordinal matches, no match, and a bit-10 match;
  * the signed 0x18 frame wrap boundary with 0x16/0x17/0x7fffffff/0x80000000/
    0xfffffffe/0xffffffff counters, including a zero denominator;
  * the final scroll+selected row selection with positive, negative and
    wrap-around sums and in/out-of-range final categories;
  * negative controls mutate the mask end, frame limit, fallback mask offset
    and record mask offset; each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch33_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_00298bdc"

FUNC_ADDR = 0x00298BDC
FUNC_SIZE = 408

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00100000      # covers 0x00298BDC through the 0x002C615C stub
DATA_ADDR = 0x0043C000
DATA_SIZE = 0x00004000      # contains the 0x0043DA90 global
WORK_ADDR = 0x00500000
WORK_SIZE = 0x00020000
ALT_ADDR = 0x00600000
ALT_SIZE = 0x00001000
CAT_ADDR = 0x00610000
CAT_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

GLOBAL_ADDR = 0x0043DA90
ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_29F0F4 = 0x0029F0F4
STUB_29F248 = 0x0029F248
STUB_29F260 = 0x0029F260
STUB_2C4B30 = 0x002C4B30
STUB_2B66EC = 0x002B66EC
STUB_2A89E4 = 0x002A89E4
STUB_2B0788 = 0x002B0788
STUB_2C615C = 0x002C615C
STUB_26DD68 = 0x0026DD68

STUB_NAMES = {
    STUB_29F0F4: "camp_func_0029f0f4",
    STUB_29F248: "camp_func_0029f248",
    STUB_29F260: "camp_func_0029f260",
    STUB_2C4B30: "engine_func_002c4b30",
    STUB_2B66EC: "script_vm_func_002b66ec",
    STUB_2A89E4: "camp_func_002a89e4",
    STUB_2B0788: "ui_func_002b0788",
    STUB_2C615C: "ui_func_002c615c",
    STUB_26DD68: "script_vm_func_0026dd68",
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

# Camp work-block layout recovered from the ARM listing.
CURSOR_OFFSET = 0x1DC
VISIBLE_CATEGORY_BASE = 0xE40
VISIBLE_ROW_STRIDE = 8
FRAME_BASE = 0x2494
ROLLING_INDEX_BASE = 0x24F8
VALUE_BASE = 0x255C
CATEGORY_STRIDE = 4
CATEGORY_PAGE_STRIDE = 0x200
CAT_MASK_OFFSET = 0x44
FALLBACK_MASK_OFFSET = 0x72
VISIBLE_ROW_SLOTS = 64
CATEGORY_STATE_SLOTS = 24   # categories 0..23 share the work tables

COMMIT_DEFAULT = 0x2600DD68


def _pattern(size: int, seed: int) -> bytes:
    block = bytes((index * 7 + seed) & 0xFF for index in range(256))
    return (block * (size // 256))[:size]


# ------------------------------------------------------------------- fixtures
def build_work(case: dict) -> bytes:
    page = bytearray(_pattern(WORK_SIZE, 0x5A))

    fill = case.get("fill_category", 0)
    for row in range(VISIBLE_ROW_SLOTS):
        struct.pack_into(
            "<i", page, VISIBLE_CATEGORY_BASE + row * VISIBLE_ROW_STRIDE, fill
        )
    for row, category in enumerate(case.get("rows", [])):
        struct.pack_into(
            "<i",
            page,
            VISIBLE_CATEGORY_BASE + row * VISIBLE_ROW_STRIDE,
            category,
        )

    for category in range(CATEGORY_STATE_SLOTS):
        struct.pack_into("<I", page, FRAME_BASE + category * CATEGORY_STRIDE, 0)
        struct.pack_into(
            "<I", page, ROLLING_INDEX_BASE + category * CATEGORY_STRIDE, 0
        )
        struct.pack_into("<I", page, VALUE_BASE + category * CATEGORY_STRIDE, 0)

    for category, frame in case.get("frames", {}).items():
        struct.pack_into(
            "<I", page, FRAME_BASE + category * CATEGORY_STRIDE,
            frame & 0xFFFFFFFF,
        )
    for category, rolling in case.get("rolling", {}).items():
        struct.pack_into(
            "<I", page, ROLLING_INDEX_BASE + category * CATEGORY_STRIDE,
            rolling & 0xFFFFFFFF,
        )
    for category, value in case.get("values", {}).items():
        struct.pack_into(
            "<I", page, VALUE_BASE + category * CATEGORY_STRIDE,
            value & 0xFFFFFFFF,
        )

    # Explicit word overrides relative to the work block (used for the final
    # row index that falls before the visible table).
    for offset, value in case.get("work_words", {}).items():
        if not 0 <= offset <= WORK_SIZE - 4:
            raise ValueError(f"work override 0x{offset:x} outside the fixture")
        struct.pack_into("<I", page, offset, value & 0xFFFFFFFF)
    return bytes(page)


def build_categories(case: dict) -> bytes:
    page = bytearray(_pattern(CAT_SIZE, 0x33))
    masks = case.get("masks", {})
    for category in range(CATEGORY_STATE_SLOTS):
        struct.pack_into(
            "<H",
            page,
            category * CATEGORY_PAGE_STRIDE + CAT_MASK_OFFSET,
            masks.get(category, 0) & 0xFFFF,
        )
    for category, mask in masks.items():
        if not 0 <= category < CATEGORY_STATE_SLOTS:
            raise ValueError(f"category {category} outside the fixture")
        struct.pack_into(
            "<H",
            page,
            category * CATEGORY_PAGE_STRIDE + CAT_MASK_OFFSET,
            mask & 0xFFFF,
        )
    return bytes(page)


def build_fallback(case: dict) -> bytes:
    page = bytearray(_pattern(ALT_SIZE, 0x77))
    struct.pack_into(
        "<H", page, FALLBACK_MASK_OFFSET, case.get("fallback_mask", 0) & 0xFFFF
    )
    return bytes(page)


def build_data(work_pointer: int) -> bytes:
    page = bytearray(_pattern(DATA_SIZE, 0xC3))
    struct.pack_into("<I", page, GLOBAL_ADDR - DATA_ADDR, work_pointer)
    return bytes(page)


# ---------------------------------------------------------------- compilation
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    functions = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in functions.items():
        if "00298bdc" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"camp_func_00298bdc not found in {obj_file}: {sorted(functions)}"
        )

    code_raw, relocations = candidate
    code = bytearray(code_raw)
    for rel in relocations:
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


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch33_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_source = OUT_DIR / f"mutant_{name}.cpp"
    mutant_source.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_source, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


# -------------------------------------------------------------------- runner
class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(ALT_ADDR, ALT_SIZE)
        self.uc.mem_map(CAT_ADDR, CAT_SIZE)
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
        self.rowcount_values: list = []
        self.rowcount_index = 0
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _log(self, address: int, *args, stack: int = 0) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(stack))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    @staticmethod
    def _signed(value: int) -> int:
        return value - (1 << 32) if value & 0x80000000 else value

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)

        if address == STUB_29F0F4:
            self._log(address, r0)
            if self.rowcount_index >= len(self.rowcount_values):
                raise AssertionError("row-count script exhausted")
            value = self.rowcount_values[self.rowcount_index]
            self.rowcount_index += 1
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        elif address == STUB_29F248:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("selected", 0) & 0xFFFFFFFF
            )
        elif address == STUB_29F260:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("scroll", 0) & 0xFFFFFFFF
            )
        elif address == STUB_2C4B30:
            self._log(address, r0, r1)
            uc.mem_write(r0, b"\x00" * r1)
        elif address == STUB_2B66EC:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, ALT_ADDR)
        elif address == STUB_2A89E4:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                CAT_ADDR + (r0 & 0xFFFF) * CATEGORY_PAGE_STRIDE,
            )
        elif address == STUB_2B0788:
            self._log(address, r0)
            bit = r0 & 0xFFFF
            uc.reg_write(arm.UC_ARM_REG_R0, 0xB0000000 | (bit << 8) | bit)
        elif address == STUB_2C615C:
            self._log(address, r0, r1)
            numerator = self._signed(r0)
            denominator = self._signed(r1)
            if denominator == 0:
                quotient = 0
                remainder = r0  # the pinned helper returns the numerator word
            else:
                quotient = abs(numerator) // abs(denominator)
                if (numerator < 0) != (denominator < 0):
                    quotient = -quotient
                remainder = numerator - quotient * denominator
            uc.reg_write(arm.UC_ARM_REG_R0, quotient & 0xFFFFFFFF)
            uc.reg_write(arm.UC_ARM_REG_R1, remainder & 0xFFFFFFFF)
        elif address == STUB_26DD68:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                self.case.get("commit_return", COMMIT_DEFAULT) & 0xFFFFFFFF,
            )
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for name, args in log:
            out = []
            for arg in args:
                if (
                    isinstance(arg, int)
                    and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE
                ):
                    out.append("<stack>")
                else:
                    out.append(arg)
            normalised.append((name, tuple(out)))
        return normalised

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.rowcount_values = list(case.get("rowcounts", [0, 0]))
        self.rowcount_index = 0

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DATA_ADDR, build_data(WORK_ADDR))
        self.uc.mem_write(WORK_ADDR, build_work(case))
        self.uc.mem_write(ALT_ADDR, build_fallback(case))
        self.uc.mem_write(CAT_ADDR, build_categories(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0xDEADBEEF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, write_size in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_work = WORK_ADDR <= address < WORK_ADDR + WORK_SIZE
            if not (in_stack or in_work):
                unexpected_writes.append((address, write_size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "fixtures": {
                "work": bytes(self.uc.mem_read(WORK_ADDR, WORK_SIZE)),
                "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
                "alt": bytes(self.uc.mem_read(ALT_ADDR, ALT_SIZE)),
                "categories": bytes(self.uc.mem_read(CAT_ADDR, CAT_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list:
    problems = []
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
            offset = next(
                (
                    index
                    for index, (left, right) in enumerate(
                        zip(value, cand["fixtures"][key])
                    )
                    if left != right
                ),
                None,
            )
            problems.append(
                f"fixture {key} differs at byte {offset}: "
                f"orig={value[offset] if offset is not None else None:#x} "
                f"cand={cand['fixtures'][key][offset] if offset is not None else None}"
            )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


# --------------------------------------------------------------------- cases
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "rowcounts": [0, 0],
        "rows": [],
        "masks": {},
        "frames": {},
        "rolling": {},
        "values": {},
        "selected": 0,
        "scroll": 0,
        "work_words": {},
    }
    case.update(overrides)
    return case


def make_cases() -> list:
    cases: list = []

    # --- row-count rule -----------------------------------------------------
    cases.append(base_case("count zero"))
    cases.append(base_case("count negative", rowcounts=[-1, 0]))
    cases.append(
        base_case(
            "second smaller, third wins", rowcounts=[3, 1, 2],
            rows=[1, 2, 3], masks={1: 0x0002, 2: 0x0004},
        )
    )
    cases.append(
        base_case(
            "second equal, first wins", rowcounts=[2, 2],
            rows=[1, 2], masks={1: 0x0002, 2: 0x0004},
        )
    )
    cases.append(
        base_case(
            "second greater, first wins", rowcounts=[2, 3],
            rows=[1, 2], masks={1: 0x0002, 2: 0x0004},
        )
    )
    cases.append(
        base_case(
            "first negative, third wins", rowcounts=[-1, -5, 2],
            rows=[0, 1], masks={0: 0x0002},
        )
    )

    # --- mask shapes --------------------------------------------------------
    cases.append(base_case("mask zero", rowcounts=[1, 1], rows=[0],
                           masks={0: 0x0000}))
    cases.append(base_case("single mask bit", rowcounts=[1, 1], rows=[0],
                           masks={0: 0x0002}))
    cases.append(base_case("mask bit zero only", rowcounts=[1, 1], rows=[0],
                           masks={0: 0x0001}))
    cases.append(base_case("second set bit matches", rowcounts=[1, 1],
                           rows=[0], masks={0: 0x0006}, rolling={0: 1}))
    cases.append(base_case("no set bit matches", rowcounts=[1, 1], rows=[0],
                           masks={0: 0x0006}, rolling={0: 2},
                           values={0: 0x1234ABCD}))
    cases.append(base_case("bit ten matches", rowcounts=[1, 1], rows=[0],
                           masks={0: 0x07FE}, rolling={0: 9}))
    cases.append(base_case("all bits, no match", rowcounts=[1, 1], rows=[0],
                           masks={0: 0x07FE}, rolling={0: 10},
                           values={0: 0xFEEDFACE}))
    cases.append(base_case("mask duplicate row skipped", rowcounts=[2, 2],
                           rows=[0, 0], masks={0: 0x0002},
                           frames={0: 5}, values={0: 0xAA}))
    cases.append(base_case("two distinct categories", rowcounts=[2, 2],
                           rows=[0, 1], masks={0: 0x0002, 1: 0x0004}))
    cases.append(base_case("category 23 boundary", rowcounts=[1, 1],
                           rows=[23], masks={23: 0x0002},
                           frames={23: 3}, rolling={23: 0}))
    cases.append(base_case("negative category fallback", rowcounts=[1, 1],
                           rows=[-1], masks={}, fallback_mask=0x0008,
                           frames={-1: 1}))
    cases.append(base_case("negative category fallback zero", rowcounts=[1, 1],
                           rows=[-1], fallback_mask=0x0000,
                           values={-1: 0x55AA55AA}))

    # --- frame counter signed 0x18 boundary ---------------------------------
    for frame in (0x16, 0x17, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFE, 0xFFFFFFFF):
        cases.append(
            base_case(
                f"frame 0x{frame:08x}", rowcounts=[1, 1], rows=[0],
                masks={0: 0x0002}, frames={0: frame},
            )
        )
    cases.append(
        base_case(
            "frame wrap zero denominator", rowcounts=[1, 1], rows=[0],
            masks={0: 0x0002}, frames={0: 0x17}, rolling={0: 0},
        )
    )
    cases.append(
        base_case(
            "frame wrap ordinals", rowcounts=[1, 1], rows=[0],
            masks={0: 0x000E}, frames={0: 0x17}, rolling={0: 3},
        )
    )

    # --- final row selection ------------------------------------------------
    cases.append(
        base_case(
            "selected row in loop", rowcounts=[4, 4],
            rows=[0, 1, 2, 3], masks={0: 0x2, 1: 0x4, 2: 0x8, 3: 0x10},
            scroll=1, selected=2,
        )
    )
    cases.append(
        base_case(
            "final index negative", rowcounts=[1, 1], rows=[0],
            masks={0: 0x0002}, scroll=-1, selected=0,
            work_words={VISIBLE_CATEGORY_BASE - VISIBLE_ROW_STRIDE: 0},
        )
    )
    cases.append(
        base_case(
            "final index negative both", rowcounts=[0, 0],
            scroll=-3, selected=-4, masks={0: 0x0002},
            work_words={
                VISIBLE_CATEGORY_BASE - 7 * VISIBLE_ROW_STRIDE: 0,
            },
        )
    )
    cases.append(
        base_case(
            "final index far row", rowcounts=[0, 0], fill_category=2,
            masks={2: 0x0004}, values={2: 0x11223344},
            scroll=40, selected=10,
        )
    )
    cases.append(
        base_case(
            "final category negative", rowcounts=[0, 0], fill_category=-1,
            fallback_mask=0x0000, values={-1: 0x00112233},
        )
    )
    cases.append(
        base_case(
            "final category outside marker range", rowcounts=[0, 0],
            fill_category=100, selected=7,
            work_words={VALUE_BASE + 100 * CATEGORY_STRIDE: 0x76543210},
        )
    )
    cases.append(
        base_case(
            "final category 23", rowcounts=[0, 0], fill_category=23,
            values={23: 0x0BADF00D},
        )
    )
    cases.append(
        base_case(
            "visited value reused at end", rowcounts=[1, 1], rows=[0],
            masks={0: 0x0004}, scroll=0, selected=0,
        )
    )
    cases.append(
        base_case(
            "row sum wraps mod 2^32", rowcounts=[0, 0],
            scroll=0x7FFFFFFF, selected=1, masks={0: 0x0002},
        )
    )
    cases.append(
        base_case(
            "row sum shift wraps mod 2^32", rowcounts=[0, 0],
            scroll=0x20000000, selected=0, masks={0: 0x0002},
        )
    )
    cases.append(
        base_case(
            "commit return value", rowcounts=[0, 0],
            commit_return=0xFFFFFFFF,
        )
    )
    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases: list) -> int:
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
    print("Testing camp_func_00298bdc (0x00298bdc)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("mask_end", "constexpr s32 kMaskBitEnd = 0xBu;",
         "constexpr s32 kMaskBitEnd = 0xAu;"),
        ("frame_limit", "constexpr s32 kFrameWrapLimit = 0x18;",
         "constexpr s32 kFrameWrapLimit = 0x17;"),
        ("fallback_mask_offset", "constexpr u32 kFallbackMaskOffset = 0x72u;",
         "constexpr u32 kFallbackMaskOffset = 0x70u;"),
        ("record_mask_offset", "constexpr u32 kRecordMaskOffset = 0x44u;",
         "constexpr u32 kRecordMaskOffset = 0x42u;"),
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
