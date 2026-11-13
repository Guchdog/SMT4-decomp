#!/usr/bin/env python3
"""Differential test for engine_func_00300710 (0x00300710) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the engine_func_00300710 body
and the unlisted 0x003008C8 helper that shares its ledger span, resolves the
direct calls of the former to deterministic stubs, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared observables:
  * return r0, continuation PC, final SP, callee-saved r4-r11 (both compared
    between runs and checked against the entry state because this is an
    isolated call);
  * the ordered call log with every register argument, the 21-word stack block
    of 0x002553EC and the three stack words of 0x00250800;
  * every fixture page (UI context, slot table, 276-byte unit table, script-VM
    slot, alternate tables, helper object) byte for byte;
  * any emulated write outside the private stack.

Coverage:
  * selector 0/1/2 and every other 32-bit value (0 -> +0x1BA, 1 -> +0x1B8,
    2 -> multiplier, default 0), with signed s16 stat boundaries and a wrapped
    32-bit product before the /100;
  * all four rows accepted/skipped through the 0x41 flag mask, negative and
    non-negative s16 indices, and per-row i*8 fields;
  * null and non-null 0x0027EB98 results, arbitrary 0x0043427C slot words;
  * ordering probes: the UI notification rewrites the slot-table pointer, the
    current row index and the unit-table pointer after the gate reads, so a
    candidate that hoists any of those loads is rejected.

The 0x003008C8 helper is tested separately against the original 248-byte block
at 0x003008C8: guard byte, non-positive count, odd/even pair unrolling, both
entry checks, exhaustion and signed values.

Negative controls mutate the live flag, row stride, action command, stat
offsets, scale divisor, unit-table offset, index offset and four helper
constants/offsets; every mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch45_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_00300710"

FUNC_ADDR = 0x00300710
FUNC_SIZE = 688
HELPER_ADDR = 0x003008C8
HELPER_SIZE = 0x000000F8  # 0x3008C8..0x3009C0, including the two literals

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function, the helper and every stub
VM_SLOT_ADDR = 0x00430000
VM_SLOT_SIZE = 0x00008000
UI_ADDR = 0x00710000
UI_SIZE = 0x00004000
ROWS_ADDR = 0x00720000
ROWS_SIZE = 0x00001000
UNITS_ADDR = 0x00740000
UNITS_SIZE = 0x00001000
ALT_ROWS_ADDR = 0x00750000
ALT_ROWS_SIZE = 0x00001000
ALT_UNITS_ADDR = 0x00760000
ALT_UNITS_SIZE = 0x00001000
OBJECT_ADDR = 0x00770000
OBJECT_SIZE = 0x00008000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Direct-call targets. Stubs live at the original addresses so the pinned
# bytes and the relocated candidate resolve to the same helpers.
STUB_296F60 = 0x00296F60
STUB_293C98 = 0x00293C98
STUB_27EB98 = 0x0027EB98
STUB_250960 = 0x00250960
STUB_2553EC = 0x002553EC
STUB_250800 = 0x00250800

STUB_NAMES = {
    STUB_296F60: "engine_func_00296f60",
    STUB_293C98: "ui_func_00293c98",
    STUB_27EB98: "script_vm_func_0027eb98",
    STUB_250960: "func_00250960",
    STUB_2553EC: "battle_func_002553ec",
    STUB_250800: "battle_func_00250800",
}

# Architected stack words observed by each helper.
STACK_ARGS = {
    STUB_296F60: 0,
    STUB_293C98: 0,
    STUB_27EB98: 0,
    STUB_250960: 0,
    STUB_2553EC: 21,
    STUB_250800: 3,
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

# Row layout and helper layout, mirrored from the C++ constants.
ROW_STRIDE = 648
ROW_FLAGS = 0x000
ROW_INDEX = 0x008
ROW_B4 = 0x1B4
ROW_B6 = 0x1B6
ROW_B8 = 0x1B8
ROW_BA = 0x1BA
UI_SLOT_TABLE = 0x1FC0
UI_UNIT_TABLE = 0x1E98
VM_SLOT = 0x0043427C

OBJ_COUNT = 0x5758
OBJ_GUARD = 0x575D
OBJ_VALUE = 0x577C
OBJ_FLAG = 0x5788
OBJ_STRIDE = 44


def get_orig_bytes(offset: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(offset - 0x00100000)
        return f.read(size)


def pattern(size: int, seed: int) -> bytes:
    out = bytearray(size)
    value = seed & 0xFF
    for index in range(size):
        value = (value * 37 + 11) & 0xFF
        out[index] = value
    return bytes(out)


PATTERN_VM_SLOT = pattern(VM_SLOT_SIZE, 0x11)
PATTERN_UI = pattern(UI_SIZE, 0x22)
PATTERN_ROWS = pattern(ROWS_SIZE, 0x33)
PATTERN_UNITS = pattern(UNITS_SIZE, 0x44)
PATTERN_ALT_ROWS = pattern(ALT_ROWS_SIZE, 0x55)
PATTERN_ALT_UNITS = pattern(ALT_UNITS_SIZE, 0x66)
PATTERN_OBJECT = pattern(OBJECT_SIZE, 0x77)


def elf_function(obj_file: Path, needle: str) -> tuple[bytes, tuple]:
    funcs = extract_elf_functions_detailed(obj_file)
    for name, value in funcs.items():
        if needle in name:
            return value
    raise RuntimeError(f"{needle} not found in {obj_file}: {sorted(funcs)}")


def relocate_main(obj_file: Path) -> bytes:
    raw, relocs = elf_function(obj_file, "00300710")
    code = bytearray(raw)
    for rel in relocs:
        target = None
        for address in STUB_NAMES:
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved relocation: {rel.symbol_name}")
        if rel.relocation_type != 28:  # R_ARM_CALL
            raise RuntimeError(
                f"unexpected relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        condition = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, condition | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate_baseline() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    main_code = relocate_main(obj_file)
    helper_code, helper_relocs = elf_function(obj_file, "003008c8")
    if helper_relocs:
        raise RuntimeError(f"helper unexpectedly has relocations: {helper_relocs}")
    return main_code, helper_code


def compile_mutant(
    name: str, old: str, new: str
) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    res = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {res.stderr}")
    return relocate_main(obj_file), elf_function(obj_file, "003008c8")[0]


# --------------------------------------------------------------------- fixtures
def make_row(flags=0, index=0, b4=0x10, b6=0x20, b8=0x30, ba=0x40):
    return {
        "flags": flags,
        "index": index,
        "b4": b4,
        "b6": b6,
        "b8": b8,
        "ba": ba,
    }


def build_rows(base: bytes, rows: list[dict]) -> bytes:
    page = bytearray(base)
    for i, row in enumerate(rows):
        offset = i * ROW_STRIDE
        struct.pack_into("<I", page, offset + ROW_FLAGS, row["flags"] & 0xFFFFFFFF)
        struct.pack_into("<h", page, offset + ROW_INDEX, row["index"])
        struct.pack_into("<h", page, offset + ROW_B4, row["b4"])
        struct.pack_into("<h", page, offset + ROW_B6, row["b6"])
        struct.pack_into("<h", page, offset + ROW_B8, row["b8"])
        struct.pack_into("<h", page, offset + ROW_BA, row["ba"])
    return bytes(page)


def build_main_fixtures(case: dict) -> dict:
    vm_slot = bytearray(PATTERN_VM_SLOT)
    struct.pack_into("<I", vm_slot, VM_SLOT - VM_SLOT_ADDR, case.get("vm_word", 0x0043427C))

    ui = bytearray(PATTERN_UI)
    struct.pack_into("<I", ui, UI_SLOT_TABLE, ROWS_ADDR)
    struct.pack_into("<I", ui, UI_UNIT_TABLE, UNITS_ADDR)

    return {
        "vm_slot": bytes(vm_slot),
        "ui": bytes(ui),
        "rows": build_rows(PATTERN_ROWS, case.get("rows", [])),
        "units": PATTERN_UNITS,
        "alt_rows": build_rows(PATTERN_ALT_ROWS, case.get("alt_rows", [])),
        "alt_units": PATTERN_ALT_UNITS,
    }


class MainRunner:
    """Unicorn machine with deterministic stubs at the original call targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (VM_SLOT_ADDR, VM_SLOT_SIZE),
            (UI_ADDR, UI_SIZE),
            (ROWS_ADDR, ROWS_SIZE),
            (UNITS_ADDR, UNITS_SIZE),
            (ALT_ROWS_ADDR, ALT_ROWS_SIZE),
            (ALT_UNITS_ADDR, ALT_UNITS_SIZE),
            (OBJECT_ADDR, OBJECT_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.notify_count = 0
        self.draw_count = 0
        self.case: dict = {}

    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_296F60:
            self._log(address, r0)
            if r0 == 0:
                result = self.case.get("multiplier", 100)
            elif r0 == 1:
                result = self.case.get("selector", 0)
            else:
                result = 0xBAD00000 | r0
            uc.reg_write(arm.UC_ARM_REG_R0, result & 0xFFFFFFFF)
        elif address == STUB_293C98:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, UI_ADDR)
        elif address == STUB_27EB98:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("context", 0x11223344) & 0xFFFFFFFF
            )
        elif address == STUB_250960:
            self._log(address, r0)
            if self.notify_count == 0:
                if self.case.get("probe_slot_table", False):
                    uc.mem_write(UI_ADDR + UI_SLOT_TABLE, struct.pack("<I", ALT_ROWS_ADDR))
                if self.case.get("probe_index", False):
                    uc.mem_write(ROWS_ADDR + ROW_INDEX, struct.pack("<h", 7))
            self.notify_count += 1
        elif address == STUB_2553EC:
            self._log(address, r0, r1, r2, r3)
            if self.draw_count == 0 and self.case.get("probe_unit_table", False):
                uc.mem_write(UI_ADDR + UI_UNIT_TABLE, struct.pack("<I", ALT_UNITS_ADDR))
            self.draw_count += 1
        elif address == STUB_250800:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub 0x{address:08x}")

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
        fixtures = build_main_fixtures(case)
        self.call_log = []
        self.writes = []
        self.notify_count = 0
        self.draw_count = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(VM_SLOT_ADDR, fixtures["vm_slot"])
        self.uc.mem_write(UI_ADDR, fixtures["ui"])
        self.uc.mem_write(ROWS_ADDR, fixtures["rows"])
        self.uc.mem_write(UNITS_ADDR, fixtures["units"])
        self.uc.mem_write(ALT_ROWS_ADDR, fixtures["alt_rows"])
        self.uc.mem_write(ALT_UNITS_ADDR, fixtures["alt_units"])
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected = [
            (address, size)
            for address, size in self.writes
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        ]

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "fixtures": {
                "vm_slot": bytes(self.uc.mem_read(VM_SLOT_ADDR, VM_SLOT_SIZE)),
                "ui": bytes(self.uc.mem_read(UI_ADDR, UI_SIZE)),
                "rows": bytes(self.uc.mem_read(ROWS_ADDR, ROWS_SIZE)),
                "units": bytes(self.uc.mem_read(UNITS_ADDR, UNITS_SIZE)),
                "alt_rows": bytes(self.uc.mem_read(ALT_ROWS_ADDR, ALT_ROWS_SIZE)),
                "alt_units": bytes(self.uc.mem_read(ALT_UNITS_ADDR, ALT_UNITS_SIZE)),
            },
            "unexpected_writes": unexpected,
        }


class HelperRunner:
    """Machine for the 0x003008C8 block; it takes one object pointer."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (OBJECT_ADDR, OBJECT_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.writes: list = []

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def run(self, code: bytes, object_page: bytes) -> dict:
        self.uc.mem_write(HELPER_ADDR, code)
        self.uc.mem_write(OBJECT_ADDR, object_page)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJECT_ADDR)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(HELPER_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Helper crash at PC=0x{pc:08x}: {error}") from error

        unexpected = [
            (address, size)
            for address, size in self.writes
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        ]
        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "object": bytes(self.uc.mem_read(OBJECT_ADDR, OBJECT_SIZE)),
            "unexpected_writes": unexpected,
        }


# ---------------------------------------------------------------------- cases
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "multiplier": 100,
        "selector": 0,
        "context": 0x11223344,
        "vm_word": 0x0043427C,
        "rows": [make_row(flags=1, index=0, b4=0x10, b6=0x20, b8=0x30, ba=0x40)],
    }
    case.update(overrides)
    return case


def make_main_cases() -> list[dict]:
    cases: list[dict] = []

    cases.append(base_case("baseline selector 0"))

    # selector: 0 -> +0x1BA, 1 -> +0x1B8, 2 -> multiplier, default -> 0
    for selector in (0, 1, 2, 3, -1, 0x7FFFFFFF, 0xFFFFFFFF):
        cases.append(
            base_case(
                f"selector {selector}",
                selector=selector,
                multiplier=100,
                rows=[make_row(flags=1, index=0, b8=0x0123, ba=0x0456)],
            )
        )

    # multiplier boundaries and wrapped signed products
    for multiplier in (
        0,
        1,
        99,
        100,
        101,
        -100,
        -1,
        0x7FFFFFFF,
        0x80000000,
        0x40000000,
        0xFFFFFFFF,
    ):
        for stat in (-0x8000, 0x7FFF, 0, -1, 1):
            cases.append(
                base_case(
                    f"mult 0x{multiplier & 0xFFFFFFFF:08x} stat {stat}",
                    multiplier=multiplier,
                    selector=0,
                    rows=[make_row(flags=1, index=0, ba=stat)],
                )
            )
    cases.append(
        base_case(
            "wrapped product negative",
            multiplier=0x7FFFFFFF,
            selector=0,
            rows=[make_row(flags=1, index=0, ba=0x7FFF)],
        )
    )
    cases.append(
        base_case(
            "wrapped product fast offset",
            multiplier=0x7FFFFFFF,
            selector=1,
            rows=[make_row(flags=1, index=0, b8=-0x8000)],
        )
    )

    # flag gate: bit0 must be set, bit6 must be clear
    for flags in (0x00, 0x01, 0x40, 0x41, 0xFF, 0xFFFFFFFF, 0x11, 0x03, 0x21):
        cases.append(
            base_case(f"flags 0x{flags:08x}", rows=[make_row(flags=flags, index=0)])
        )

    # signed index gate and accepted boundaries
    for index in (-1, -0x8000, 0, 1, 2, 0x7FFF):
        cases.append(
            base_case(f"index {index}", rows=[make_row(flags=1, index=index)])
        )

    # four-row coverage: each row alone and all four together
    for row_index in range(4):
        rows = [make_row(flags=0, index=row_index) for _ in range(4)]
        rows[row_index] = make_row(flags=1, index=row_index, b4=0x100 + row_index)
        cases.append(base_case(f"only row {row_index}", rows=rows))
    cases.append(
        base_case(
            "all four rows",
            rows=[
                make_row(flags=1, index=0, b4=0x10),
                make_row(flags=1, index=1, b4=0x11),
                make_row(flags=0x41, index=2, b4=0x12),
                make_row(flags=1, index=3, b4=0x13),
            ],
        )
    )
    cases.append(
        base_case(
            "mixed gate combinations",
            rows=[
                make_row(flags=0x01, index=4, b4=1, b6=2, b8=3, ba=4),
                make_row(flags=0x00, index=5),
                make_row(flags=0x41, index=6),
                make_row(flags=0x11, index=7, b4=-1, b6=-2, b8=-3, ba=-4),
            ],
        )
    )

    # script-VM context: null and non-null results, arbitrary slot words
    for context in (0, 0xFFFFFFFF, 0x12345678):
        cases.append(base_case(f"context 0x{context:08x}", context=context))
    for word in (0, 0xFFFFFFFF, 0x0043427C, 0xDEADBEEF):
        cases.append(base_case(f"vm slot word 0x{word:08x}", vm_word=word))

    # ordering probes: notifications rewrite pointers after the gate reads
    second_rows = [
        make_row(flags=1, index=0, b4=0xA0),
        make_row(flags=1, index=1, b4=0xA1),
        make_row(flags=1, index=2, b4=0xA2),
        make_row(flags=1, index=3, b4=0xA3),
    ]
    cases.append(
        base_case(
            "probe slot-table re-read",
            rows=second_rows,
            alt_rows=[
                make_row(flags=1, index=9, b4=0xB0, b6=0xB1, b8=0xB2, ba=0xB3),
                make_row(flags=1, index=10, b4=0xB4),
                make_row(flags=1, index=11, b4=0xB5),
                make_row(flags=1, index=12, b4=0xB6),
            ],
            probe_slot_table=True,
        )
    )
    cases.append(
        base_case(
            "probe unit-table re-read",
            rows=second_rows,
            probe_unit_table=True,
        )
    )
    cases.append(
        base_case(
            "probe index re-read",
            rows=[make_row(flags=1, index=0, b4=0xC0)],
            probe_index=True,
        )
    )
    cases.append(
        base_case(
            "probe all pointers",
            rows=second_rows,
            alt_rows=[
                make_row(flags=1, index=1, b4=0xD0),
                make_row(flags=1, index=2, b4=0xD1),
            ],
            probe_slot_table=True,
            probe_unit_table=True,
        )
    )

    # all rows rejected: only the four prefix calls remain
    cases.append(
        base_case(
            "no accepted rows",
            rows=[
                make_row(flags=0),
                make_row(flags=0x40),
                make_row(flags=0x41),
                make_row(flags=1, index=-1),
            ],
        )
    )

    # 32-bit signed values in every forwarded field
    cases.append(
        base_case(
            "extreme forwarded fields",
            multiplier=0x80000000,
            selector=2,
            rows=[
                make_row(
                    flags=1,
                    index=0x7FFF,
                    b4=-0x8000,
                    b6=0x7FFF,
                    b8=-0x8000,
                    ba=0x7FFF,
                )
            ],
        )
    )
    return cases


def make_helper_cases() -> list[dict]:
    cases: list[dict] = []

    def helper_case(name, guard=1, count=0, flags=None, values=None):
        return {
            "name": name,
            "guard": guard,
            "count": count,
            "flags": flags or {},
            "values": values or {},
        }

    cases.append(helper_case("guard zero", guard=0, count=4, flags={0: 1}))
    cases.append(helper_case("count zero", count=0))
    cases.append(helper_case("count negative", count=-1))
    cases.append(helper_case("count 1 no flag", count=1, flags={0: 0}))
    cases.append(helper_case("count 1 entry 0", count=1, flags={0: 1}, values={0: 0xAABBCCDD}))
    cases.append(helper_case("count 2 no flags", count=2, flags={0: 0, 1: 0}))
    cases.append(helper_case("count 2 entry 0", count=2, flags={0: 1}, values={0: 0x11223344}))
    cases.append(helper_case("count 2 entry 1", count=2, flags={1: 1}, values={1: 0x55667788}))
    cases.append(helper_case("count 3 entry 0", count=3, flags={0: 1}, values={0: 1}))
    cases.append(helper_case("count 3 entry 1", count=3, flags={1: 1}, values={1: 2}))
    cases.append(helper_case("count 3 entry 2", count=3, flags={2: 1}, values={2: 3}))
    cases.append(helper_case("count 4 entry 2", count=4, flags={2: 1}, values={2: 4}))
    cases.append(helper_case("count 4 entry 3", count=4, flags={3: 1}, values={3: 5}))
    cases.append(helper_case("count 5 entry 4", count=5, flags={4: 1}, values={4: 6}))
    cases.append(helper_case("count 6 entry 5", count=6, flags={5: 1}, values={5: 7}))
    cases.append(
        helper_case(
            "first flag wins",
            count=4,
            flags={1: 1, 2: 1, 3: 1},
            values={1: 0x99, 2: 0x88, 3: 0x77},
        )
    )
    cases.append(
        helper_case(
            "signed values",
            count=2,
            flags={0: 1},
            values={0: 0xFFFFFFFF},
        )
    )
    cases.append(
        helper_case(
            "sign bit value",
            count=2,
            flags={1: 1},
            values={1: 0x80000000},
        )
    )
    cases.append(helper_case("guard zero nonzero count", guard=0, count=6, flags={5: 1}))
    cases.append(helper_case("count large empty", count=7, flags={}))
    return cases


def build_helper_object(case: dict) -> bytes:
    page = bytearray(PATTERN_OBJECT)
    page[OBJ_GUARD] = case["guard"] & 0xFF
    struct.pack_into("<i", page, OBJ_COUNT, case["count"])
    # Start from an all-clear flag array so "no flag" cases really exhaust the
    # scan; the values keep the pattern fill to catch wrong value offsets.
    for index in range(max(case["count"], 0) + 3):
        page[OBJ_FLAG + index * OBJ_STRIDE] = 0
    for index, flag in case["flags"].items():
        page[OBJ_FLAG + index * OBJ_STRIDE] = flag & 0xFF
    for index, value in case["values"].items():
        struct.pack_into("<I", page, OBJ_VALUE + index * OBJ_STRIDE, value & 0xFFFFFFFF)
    return bytes(page)


# ------------------------------------------------------------------- compares
def compare_main(orig: dict, cand: dict) -> list[str]:
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
            problems.append(f"fixture {key} differs")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def compare_helper(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["object"] != cand["object"]:
        problems.append("object page differs")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def check_abi(result: dict, label: str) -> None:
    if result["sp"] != ENTRY_SP:
        raise AssertionError(f"{label}: SP 0x{result['sp']:08x} != 0x{ENTRY_SP:08x}")
    if result["callee_saved"] != CALLEE_SAVED_START:
        raise AssertionError(
            f"{label}: callee-saved not restored: {result['callee_saved']!r}"
        )


def run_main_cases(orig_code, cand_code, cases, label="") -> int:
    passed = 0
    for case in cases:
        orig = MainRunner().run(orig_code, case)
        cand = MainRunner().run(cand_code, case)
        problems = compare_main(orig, cand)
        if problems:
            print(f"  [FAIL] {label}{case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        check_abi(orig, f"{label}{case['name']} original")
        check_abi(cand, f"{label}{case['name']} candidate")
        passed += 1
        print(
            f"  [PASS] {label}{case['name']}  "
            f"({len(orig['call_log'])} calls, {orig['ret']:#x})"
        )
    return passed


def run_helper_cases(orig_code, cand_code, cases, label="") -> int:
    passed = 0
    for case in cases:
        object_page = build_helper_object(case)
        orig = HelperRunner().run(orig_code, object_page)
        cand = HelperRunner().run(cand_code, object_page)
        problems = compare_helper(orig, cand)
        if problems:
            print(f"  [FAIL] {label}{case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        check_abi(orig, f"{label}{case['name']} original")
        check_abi(cand, f"{label}{case['name']} candidate")
        passed += 1
        print(f"  [PASS] {label}{case['name']}  (-> 0x{orig['ret']:08x})")
    return passed


def main() -> None:
    print("Testing engine_func_00300710 (0x00300710) and 0x003008C8...")
    orig_main = get_orig_bytes(FUNC_ADDR, FUNC_SIZE)
    orig_helper = get_orig_bytes(HELPER_ADDR, HELPER_SIZE)
    cand_main, cand_helper = compile_candidate_baseline()
    print(
        f"Original main {len(orig_main)} B / helper {len(orig_helper)} B; "
        f"candidate main {len(cand_main)} B / helper {len(cand_helper)} B."
    )

    main_cases = make_main_cases()
    helper_cases = make_helper_cases()
    passed_main = run_main_cases(orig_main, cand_main, main_cases)
    passed_helper = run_helper_cases(
        orig_helper, cand_helper, helper_cases, label="helper: "
    )

    print("\nNegative controls:")
    mutants = (
        ("row_live_flag", "constexpr u32 kRowLiveFlag = 1u;",
         "constexpr u32 kRowLiveFlag = 2u;", "main"),
        ("row_stride", "constexpr u32 kRowStride = 648u;",
         "constexpr u32 kRowStride = 640u;", "main"),
        ("action_command", "constexpr u32 kActionCommand = 0x010001B5u;",
         "constexpr u32 kActionCommand = 0x010001B4u;", "main"),
        ("stat_slow_offset", "constexpr u32 kRowStatSlowOffset = 0x1BAu;",
         "constexpr u32 kRowStatSlowOffset = 0x1B8u;", "main"),
        ("scale_divisor", "return product / 100;", "return product / 101;",
         "main"),
        ("unit_table_offset", "constexpr u32 kUiUnitTable = 0x1E98u;",
         "constexpr u32 kUiUnitTable = 0x1E9Cu;", "main"),
        ("row_index_offset", "constexpr u32 kRowIndexOffset = 0x08u;",
         "constexpr u32 kRowIndexOffset = 0x0Au;", "main"),
        ("helper_stride", "constexpr u32 kEntryStride = 44u;",
         "constexpr u32 kEntryStride = 40u;", "helper"),
        ("helper_value_offset", "constexpr u32 kEntryValueOffset = 0x577Cu;",
         "constexpr u32 kEntryValueOffset = 0x5778u;", "helper"),
        ("helper_flag_offset", "constexpr u32 kEntryFlagOffset = 0x5788u;",
         "constexpr u32 kEntryFlagOffset = 0x5784u;", "helper"),
        ("helper_guard_offset", "constexpr u32 kGuardOffset = 0x575Du;",
         "constexpr u32 kGuardOffset = 0x575Cu;", "helper"),
    )
    for name, old, new, kind in mutants:
        mutant_main, mutant_helper = compile_mutant(name, old, new)
        detected = False
        if kind == "main":
            for case in main_cases:
                orig = MainRunner().run(orig_main, case)
                bad = MainRunner().run(mutant_main, case)
                if compare_main(orig, bad):
                    detected = True
                    break
        else:
            for case in helper_cases:
                object_page = build_helper_object(case)
                orig = HelperRunner().run(orig_helper, object_page)
                bad = HelperRunner().run(mutant_helper, object_page)
                if compare_helper(orig, bad):
                    detected = True
                    break
        if not detected:
            raise AssertionError(f"negative control failed: {name} was not detected")
        print(f"  [PASS] {name} mutant is detected")

    print(
        f"\nAll {passed_main}/{len(main_cases)} main and "
        f"{passed_helper}/{len(helper_cases)} helper differential cases PASSED."
    )


if __name__ == "__main__":
    main()
