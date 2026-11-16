#!/usr/bin/env python3
"""Differential test for camp_func_001e034c (0x001e034c) using Unicorn ARM.

``src/engine/leaf_batch34_c.cpp`` is compiled with the project's pinned ARMv6K
flags, the candidate's direct ``bl`` relocations are retargeted to deterministic
stubs placed at the original addresses, and the pinned original
(``extracted/exefs/code.bin``) is executed against the candidate in separate
Unicorn machines with identical fixtures.

Compared outputs
  * return ``r0`` (the value left by the tail ``Unite_Init`` call), continuation
    PC and final SP;
  * the callee-saved core registers r4-r11;
  * the ordered call log with every argument of every helper:
      0x002B9364(slot_id, work-list word at call time),
      0x0029EC14(id),
      0x0029D080(list pointer, signed count, u16 value) and its result-driven
      branch,
      0x0029FAE8(cursor, signed total, visible rows, cols, stack row, stack
      repeat),
      Unite_Init(units, signed count, descriptor low, descriptor high,
      fallback);
  * the full observable memory: the work window that holds the 24-entry unit
    list and the cursor, the two source-record pages, the slot page, the 1 MiB
    helper-entry page and the global-pointer page;
  * the set of CPU writes (address, width) outside the private stack, plus any
    write outside the pages the function is allowed to touch.

Contract checks (independent of the candidate) verify the *original* body
against a small reference model of the recovered filter order: source order
(primary then secondary), skip zero ids, skip entries without flag bit 0x20,
skip ids already collected, skip ids already present in the slot record list.

Coverage
  * zero, one and sixteen collected ids (the 8+8 maximum) and the empty case
    (total = 0 passed to both tail helpers);
  * duplicates inside one source list and across the two lists;
  * ids rejected because the slot record already lists them (first, middle and
    last record entry) and a completely full slot record list;
  * every bit pattern of the entry flag byte around bit 0x20 (0x00, 0x10, 0x20,
    0x21, 0x7F, 0x80, 0xDF, 0xFF) and all-entries-invalid;
  * u16 id boundaries 0x0001, 0x00FF, 0x0100, 0x7FFE, 0x7FFF, 0x8000, 0xFFFF,
    proving the ids are zero-extended into the helper arguments and the list;
  * the source unit-id field at +0x46 for 0x0000, 0x7FFF, 0x8000, 0xFFFF and
    mixed values, which exercises both descriptor masks;
  * slot ids 0, 1, 0x7FFF, 0x8000, 0xFFFF, 0x80000000, 0xFFFFFFFF and
    0x12345678, covering the ``slot_id << 2`` wrapping and the bit-17 mask.

Negative controls mutate the entry-flag mask, the descriptor id mask, the
descriptor reserved bit, the per-source loop bound and the number of cleared
list words; each mutant must be detected by at least one case.
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
OUT_DIR = ROOT / "build/test_leaf_001e034c"

FUNC_ADDR = 0x001E034C
FUNC_SIZE = 516

# One 3 MiB code window covers the original body (0x1e034c) and every stub, the
# highest being 0x002b9364.
CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000

GLOBAL_ADDR = 0x00430000  # holds the camp work pointer at +0xDD68
GLOBAL_SIZE = 0x00020000
GLOBAL_POINTER_OFFSET = 0xDD68

WORK_ADDR = 0x00500000
WORK_SIZE = 0x00010000
WORK_LIST_OFFSET = 0x9020
WORK_LIST_CAPACITY = 0x18
WORK_CURSOR_OFFSET = 0x9204
WORK_WINDOW_OFFSET = 0x8F00
WORK_WINDOW_SIZE = 0x0500

PRIMARY_ADDR = 0x00600000
SECONDARY_ADDR = 0x00610000
RECORD_ADDR = 0x00700000
ENTRY_ADDR = 0x00800000
ENTRY_STRIDE = 0x10
ENTRY_SIZE = 0x00100000  # 65536 slots: one per u16 id
SRC_PAGE_SIZE = 0x1000

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Direct-call targets taken from the pinned body.
STUB_RECORD = 0x002B9364    # camp_func_002b9364(u32 slot_id) -> record
STUB_ENTRY = 0x0029EC14     # camp_func_0029ec14(u32 id) -> entry
STUB_CONTAINS = 0x0029D080  # camp_func_0029d080(list, count, value) -> 0/1
STUB_CURSOR = 0x0029FAE8    # camp_func_0029fae8(cursor, ...)
STUB_UNITE = 0x0029B3CC     # Unite_Init(units, count, descriptor, fallback)

STUB_NAMES = {
    STUB_RECORD: "camp_func_002b9364",
    STUB_ENTRY: "camp_func_0029ec14",
    STUB_CONTAINS: "camp_func_0029d080",
    STUB_CURSOR: "camp_func_0029fae8",
    STUB_UNITE: "Unite_Init",
}

# Symbol-name fragments in the candidate object -> stub address.
STUB_BY_SYMBOL = (
    ("002b9364", STUB_RECORD),
    ("0029ec14", STUB_ENTRY),
    ("0029d080", STUB_CONTAINS),
    ("0029fae8", STUB_CURSOR),
    ("Unite_Init", STUB_UNITE),
)

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

# Source record offsets used by the body.
SRC_UNIT_LIST = 0x34
SRC_UNIT_ID = 0x46
RECORD_UNIT_LIST = 0x3C

# Entry flag byte (+3) values.
FLAG_VALID = 0x20
DEFAULT_FLAGS = FLAG_VALID

# ---------------------------------------------------------------------- fixtures
SRC_FILL = 0xA5
RECORD_FILL = 0x3C
WORK_FILL = 0xCD
CURSOR_FILL = 0x5A
GLOBAL_FILL = 0x5E

ENTRY_TEMPLATE = bytearray(ENTRY_SIZE)
for _slot in range(ENTRY_SIZE // ENTRY_STRIDE):
    _base = _slot * ENTRY_STRIDE
    ENTRY_TEMPLATE[_base + 0] = _slot & 0xFF
    ENTRY_TEMPLATE[_base + 1] = (_slot >> 8) & 0xFF
    ENTRY_TEMPLATE[_base + 2] = 0x5A
    ENTRY_TEMPLATE[_base + 3] = DEFAULT_FLAGS
    ENTRY_TEMPLATE[_base + 4] = _slot & 0xFF


def build_source(ids, unit_id: int) -> bytes:
    page = bytearray(bytes([SRC_FILL]) * SRC_PAGE_SIZE)
    for index, value in enumerate(ids):
        struct.pack_into("<H", page, SRC_UNIT_LIST + index * 2, value & 0xFFFF)
    struct.pack_into("<H", page, SRC_UNIT_ID, unit_id & 0xFFFF)
    return bytes(page)


def build_record(ids) -> bytes:
    page = bytearray(bytes([RECORD_FILL]) * SRC_PAGE_SIZE)
    for index, value in enumerate(ids):
        struct.pack_into("<H", page, RECORD_UNIT_LIST + index * 2, value & 0xFFFF)
    return bytes(page)


def build_work() -> bytes:
    page = bytearray(bytes([WORK_FILL]) * WORK_SIZE)
    page[WORK_CURSOR_OFFSET:WORK_CURSOR_OFFSET + 0x10] = (
        bytes([CURSOR_FILL]) * 0x10
    )
    return bytes(page)


def build_entries(flags: dict) -> bytes:
    page = bytearray(ENTRY_TEMPLATE)
    for slot, value in flags.items():
        page[slot * ENTRY_STRIDE + 3] = value & 0xFF
    return bytes(page)


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    functions = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in functions.items():
        if "001e034c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"camp_func_001e034c not found in {obj_file}: {sorted(functions)}"
        )

    raw, relocations = candidate
    code = bytearray(raw)
    for rel in relocations:
        target = None
        for fragment, address in STUB_BY_SYMBOL:
            if fragment in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved relocation: {rel.symbol_name}")
        if rel.relocation_type not in (28, 29):
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


def signed(value: int) -> int:
    return value - (1 << 32) if value & 0x80000000 else value


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(PRIMARY_ADDR, SRC_PAGE_SIZE)
        self.uc.mem_map(SECONDARY_ADDR, SRC_PAGE_SIZE)
        self.uc.mem_map(RECORD_ADDR, SRC_PAGE_SIZE)
        self.uc.mem_map(ENTRY_ADDR, ENTRY_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        # The camp work pointer used by the body.
        global_page = bytearray(bytes([GLOBAL_FILL]) * GLOBAL_SIZE)
        struct.pack_into("<I", global_page, GLOBAL_POINTER_OFFSET, WORK_ADDR)
        self.uc.mem_write(GLOBAL_ADDR, bytes(global_page))

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_RECORD:
            # Log the work-list word seen *before* the body clears the list, so
            # the recorded order proves 0x002B9364 runs first.
            list_word = struct.unpack(
                "<I", uc.mem_read(WORK_ADDR + WORK_LIST_OFFSET, 4)
            )[0]
            self.call_log.append((STUB_NAMES[address], r0, list_word))
            uc.reg_write(arm.UC_ARM_REG_R0, RECORD_ADDR)
        elif address == STUB_ENTRY:
            self.call_log.append((STUB_NAMES[address], r0))
            uc.reg_write(
                arm.UC_ARM_REG_R0, ENTRY_ADDR + (r0 & 0xFFFF) * ENTRY_STRIDE
            )
        elif address == STUB_CONTAINS:
            count = signed(r1)
            value = r2 & 0xFFFF
            self.call_log.append((STUB_NAMES[address], r0, count, r2))
            found = 0
            if count > 0:
                raw = uc.mem_read(r0, count * 2)
                entries = struct.unpack("<%dH" % count, raw)
                found = 1 if value in entries else 0
            uc.reg_write(arm.UC_ARM_REG_R0, found)
        elif address == STUB_CURSOR:
            sp = uc.reg_read(arm.UC_ARM_REG_SP)
            stack0, stack1 = struct.unpack("<II", uc.mem_read(sp, 8))
            self.call_log.append(
                (
                    STUB_NAMES[address],
                    r0,
                    signed(r1),
                    signed(r2),
                    signed(r3),
                    signed(stack0),
                    signed(stack1),
                )
            )
        elif address == STUB_UNITE:
            low, high = struct.unpack("<II", uc.mem_read(r2, 8))
            self.call_log.append(
                (STUB_NAMES[address], r0, signed(r1), low, high, r3)
            )
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(WORK_ADDR, build_work())
        self.uc.mem_write(
            PRIMARY_ADDR,
            build_source(case["primary"], case["primary_unit"]),
        )
        self.uc.mem_write(
            SECONDARY_ADDR,
            build_source(case["secondary"], case["secondary_unit"]),
        )
        self.uc.mem_write(RECORD_ADDR, build_record(case["record"]))
        self.uc.mem_write(ENTRY_ADDR, build_entries(case["flags"]))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case["slot_id"])
        self.uc.reg_write(arm.UC_ARM_REG_R1, PRIMARY_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, SECONDARY_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size in self.writes:
            if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
                continue
            unexpected_writes.append((address, size))

        work_window = bytes(
            self.uc.mem_read(
                WORK_ADDR + WORK_WINDOW_OFFSET,
                WORK_WINDOW_SIZE,
            )
        )
        list_bytes = work_window[
            WORK_LIST_OFFSET - WORK_WINDOW_OFFSET:
            WORK_LIST_OFFSET - WORK_WINDOW_OFFSET + WORK_LIST_CAPACITY * 2
        ]
        units = list(struct.unpack("<%dH" % WORK_LIST_CAPACITY, list_bytes))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "units": units,
            "writes": sorted(unexpected_writes),
            "memory": {
                "work": work_window,
                "primary": bytes(self.uc.mem_read(PRIMARY_ADDR, SRC_PAGE_SIZE)),
                "secondary": bytes(
                    self.uc.mem_read(SECONDARY_ADDR, SRC_PAGE_SIZE)
                ),
                "record": bytes(self.uc.mem_read(RECORD_ADDR, SRC_PAGE_SIZE)),
                "entries": bytes(self.uc.mem_read(ENTRY_ADDR, ENTRY_SIZE)),
            },
        }


def reference_units(case: dict) -> list[int]:
    """Independent model of the recovered filter order."""
    record = set(case["record"])
    collected: list[int] = []
    for ids in (case["primary"], case["secondary"]):
        for unit in ids:
            if unit == 0:
                continue
            if not (case["flags"].get(unit, DEFAULT_FLAGS) & FLAG_VALID):
                continue
            if unit in collected:
                continue
            if unit in record:
                continue
            collected.append(unit)
    return collected


def compare(orig: dict, cand: dict) -> list[str]:
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
    if orig["writes"] != cand["writes"]:
        problems.append(
            "write set:\n    orig="
            + repr(orig["writes"])
            + "\n    cand="
            + repr(cand["writes"])
        )
    for key, value in orig["memory"].items():
        if value != cand["memory"][key]:
            problems.append(f"{key} memory was modified differently")
    if orig["units"] != cand["units"]:
        problems.append(
            "unit list:\n    orig="
            + repr(orig["units"])
            + "\n    cand="
            + repr(cand["units"])
        )
    return problems


def check_contract(case: dict, orig: dict) -> list[str]:
    """Verify the pinned original against the recovered reference model."""
    problems = []
    expected = reference_units(case)
    padded = expected + [0] * (WORK_LIST_CAPACITY - len(expected))
    if orig["units"] != padded:
        problems.append(
            f"original unit list {orig['units']} != reference {padded}"
        )

    cursor_calls = [c for c in orig["call_log"] if c[0] == "camp_func_0029fae8"]
    if len(cursor_calls) != 1:
        problems.append(f"expected one cursor call, got {cursor_calls}")
    else:
        call = cursor_calls[0]
        expected_cursor = (
            "camp_func_0029fae8",
            WORK_ADDR + WORK_CURSOR_OFFSET,
            len(expected),
            8,
            1,
            1,
            1,
        )
        if call != expected_cursor:
            problems.append(f"cursor call {call} != {expected_cursor}")

    unite_calls = [c for c in orig["call_log"] if c[0] == "Unite_Init"]
    if len(unite_calls) != 1:
        problems.append(f"expected one Unite_Init call, got {unite_calls}")
    else:
        call = unite_calls[0]
        expected_low = (
            (case["primary_unit"] & 0x7FFF)
            | ((case["secondary_unit"] & 0x7FFF) << 15)
            | 0x40000000
        )
        expected_high = 1 | (
            (case["slot_id"] << 2) & ~0x00020000 & 0xFFFFFFFF
        )
        expected_call = (
            "Unite_Init",
            WORK_ADDR + WORK_LIST_OFFSET,
            len(expected),
            expected_low & 0xFFFFFFFF,
            expected_high & 0xFFFFFFFF,
            0,
        )
        if call != expected_call:
            problems.append(f"Unite_Init call {call} != {expected_call}")

    # The body must resolve the slot record before it clears the work list.
    record_calls = [c for c in orig["call_log"] if c[0] == "camp_func_002b9364"]
    if len(record_calls) != 1:
        problems.append(f"expected one record lookup, got {record_calls}")
    elif record_calls[0][2] != int.from_bytes(bytes([WORK_FILL]) * 4, "little"):
        problems.append(
            "record lookup did not observe the uncleared work list: "
            f"{record_calls[0]}"
        )
    return problems


def case(
    name: str,
    primary=(1, 0, 2, 0, 3, 0, 4, 0),
    secondary=(5, 0, 6, 0, 7, 0, 8, 0),
    primary_unit: int = 0x1234,
    secondary_unit: int = 0x2345,
    record=(0, 0, 0, 0, 0, 0, 0, 0),
    flags: dict | None = None,
    slot_id: int = 1,
) -> dict:
    return {
        "name": name,
        "primary": tuple(primary),
        "secondary": tuple(secondary),
        "primary_unit": primary_unit,
        "secondary_unit": secondary_unit,
        "record": tuple(record),
        "flags": dict(flags or {}),
        "slot_id": slot_id & 0xFFFFFFFF,
    }


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- list sizes -----------------------------------------------------------
    cases.append(case(
        "maximum: eight plus eight distinct ids",
        primary=(1, 2, 3, 4, 5, 6, 7, 8),
        secondary=(9, 10, 11, 12, 13, 14, 15, 16),
    ))
    cases.append(case(
        "single id per source",
        primary=(21, 0, 0, 0, 0, 0, 0, 0),
        secondary=(22, 0, 0, 0, 0, 0, 0, 0),
    ))
    cases.append(case(
        "empty: both sources all zero",
        primary=(0,) * 8,
        secondary=(0,) * 8,
    ))
    cases.append(case(
        "primary empty, secondary full",
        primary=(0,) * 8,
        secondary=(31, 32, 33, 34, 35, 36, 37, 38),
    ))
    cases.append(case(
        "primary full, secondary empty",
        primary=(41, 42, 43, 44, 45, 46, 47, 48),
        secondary=(0,) * 8,
    ))
    cases.append(case(
        "only the last slot of each source is used",
        primary=(0, 0, 0, 0, 0, 0, 0, 51),
        secondary=(0, 0, 0, 0, 0, 0, 0, 52),
    ))

    # --- duplicates -----------------------------------------------------------
    cases.append(case(
        "duplicate ids inside the primary list",
        primary=(61, 61, 61, 62, 62, 61, 62, 61),
        secondary=(0,) * 8,
    ))
    cases.append(case(
        "duplicate ids across both sources",
        primary=(71, 72, 73, 0, 0, 0, 0, 0),
        secondary=(73, 72, 74, 71, 0, 0, 0, 0),
    ))
    cases.append(case(
        "all sixteen slots hold the same id",
        primary=(81,) * 8,
        secondary=(81,) * 8,
    ))

    # --- slot record rejection ------------------------------------------------
    cases.append(case(
        "ids already listed by the slot record",
        primary=(91, 92, 93, 94, 0, 0, 0, 0),
        secondary=(95, 96, 0, 0, 0, 0, 0, 0),
        record=(91, 93, 95, 0, 0, 0, 0, 0),
    ))
    cases.append(case(
        "slot record matches the last entry only",
        primary=(101, 102, 103, 104, 105, 106, 107, 108),
        secondary=(0,) * 8,
        record=(0, 0, 0, 0, 0, 0, 0, 108),
    ))
    cases.append(case(
        "slot record full and equal to the primary list",
        primary=(111, 112, 113, 114, 115, 116, 117, 118),
        secondary=(119, 120, 0, 0, 0, 0, 0, 0),
        record=(111, 112, 113, 114, 115, 116, 117, 118),
    ))

    # --- entry flags ----------------------------------------------------------
    cases.append(case(
        "entry flag bit 0x20 clear for selected ids",
        primary=(121, 122, 123, 124, 125, 126, 127, 128),
        secondary=(129, 130, 0, 0, 0, 0, 0, 0),
        flags={
            121: 0x00, 122: 0x10, 123: 0xDF, 124: 0x7F,
            125: 0x21, 126: 0xFF, 127: 0x80, 128: 0x20,
            129: 0x3F, 130: 0x40,
        },
    ))
    cases.append(case(
        "all entry flags clear",
        primary=(131, 132, 133, 134, 135, 136, 137, 138),
        secondary=(139, 140, 141, 142, 143, 144, 145, 146),
        flags={value: 0x00 for value in range(131, 147)},
    ))
    cases.append(case(
        "only bit 0x20 set in every flag",
        primary=(151, 152, 0, 0, 0, 0, 0, 0),
        secondary=(153, 0, 0, 0, 0, 0, 0, 0),
        flags={151: 0x20, 152: 0x20, 153: 0x20},
    ))

    # --- u16 id boundaries ----------------------------------------------------
    cases.append(case(
        "u16 id boundaries",
        primary=(0x0001, 0x00FF, 0x0100, 0x7FFE, 0x7FFF, 0x8000, 0xFFFF, 0xFFFE),
        secondary=(0x8001, 0x4000, 0x0002, 0, 0, 0, 0, 0),
    ))
    cases.append(case(
        "high ids rejected by the slot record",
        primary=(0xFFFF, 0x8000, 0x7FFF, 0xFFFE, 0, 0, 0, 0),
        secondary=(0, 0, 0, 0, 0, 0, 0, 0),
        record=(0xFFFF, 0, 0, 0, 0, 0, 0, 0x7FFF),
    ))

    # --- source unit-id field (+0x46) ----------------------------------------
    for primary_unit, secondary_unit in (
        (0x0000, 0x0000),
        (0x7FFF, 0x7FFF),
        (0x8000, 0x8000),
        (0xFFFF, 0xFFFF),
        (0x0001, 0x7FFE),
        (0x8000, 0x7FFF),
        (0x7FFF, 0x8000),
        (0x1234, 0xABCD),
    ):
        cases.append(case(
            f"unit ids {primary_unit:#06x}/{secondary_unit:#06x}",
            primary=(161, 162, 0, 0, 0, 0, 0, 0),
            secondary=(163, 0, 0, 0, 0, 0, 0, 0),
            primary_unit=primary_unit,
            secondary_unit=secondary_unit,
        ))

    # --- slot id --------------------------------------------------------------
    for slot_id in (
        0, 1, 2, 0x7FFF, 0x7FFF0000, 0x8000, 0xFFFF, 0x80000000,
        0xFFFFFFFF, 0x12345678, 0x40000000, 0x00008000,
    ):
        cases.append(case(
            f"slot id {slot_id:#010x}",
            primary=(171, 0, 0, 0, 0, 0, 0, 0),
            secondary=(172, 0, 0, 0, 0, 0, 0, 0),
            slot_id=slot_id,
        ))

    # --- combined -------------------------------------------------------------
    cases.append(case(
        "combined filters",
        primary=(0x7FFF, 0, 0x8000, 0x0001, 0, 0x00FF, 0xFFFF, 0),
        secondary=(0x8000, 0x7FFF, 0x0100, 0, 0x00FF, 0, 0x8001, 0x0002),
        primary_unit=0xFFFF,
        secondary_unit=0x8000,
        record=(0x0001, 0, 0, 0, 0, 0, 0, 0x8001),
        flags={
            0x7FFF: 0x00,
            0x8000: 0x20,
            0x0001: 0x20,
            0x00FF: 0x10,
            0xFFFF: 0x7F,
            0x0100: 0x21,
            0x8001: 0x20,
            0x0002: 0x20,
        },
        slot_id=0xDEADBEEF,
    ))
    return cases


def run_case_set(
    orig_runner: Runner,
    cand_runner: Runner,
    orig_code: bytes,
    cand_code: bytes,
    cases: list[dict],
) -> int:
    passed = 0
    for item in cases:
        orig = orig_runner.run(orig_code, item)
        cand = cand_runner.run(cand_code, item)
        problems = check_contract(item, orig)
        problems += compare(orig, cand)
        if problems:
            print(f"  [FAIL] {item['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(
            f"  [PASS] {item['name']}  "
            f"({len(orig['call_log'])} calls, {len(reference_units(item))} ids)"
        )
    return passed


def main() -> None:
    print("Testing camp_func_001e034c (0x001e034c)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")

    cases = make_cases()
    orig_runner = Runner()
    cand_runner = Runner()
    passed = run_case_set(orig_runner, cand_runner, orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        ("entry_flag", "constexpr u8 kCampUnitEntryValid = 0x20;",
         "constexpr u8 kCampUnitEntryValid = 0x10;"),
        ("id_mask", "constexpr u32 kCampUniteIdFieldMask = 0x7FFF;",
         "constexpr u32 kCampUniteIdFieldMask = 0x3FFF;"),
        ("reserved_bit", "constexpr u32 kCampUniteIdReservedBit = 0x00020000;",
         "constexpr u32 kCampUniteIdReservedBit = 0x00000000;"),
        ("source_count", "constexpr u32 kCampSourceUnitCount = 8;",
         "constexpr u32 kCampSourceUnitCount = 7;"),
        ("cleared_words", "constexpr u32 kCampUnitListWords = 12;",
         "constexpr u32 kCampUnitListWords = 6;"),
    )
    for name, old, new in mutants:
        mutant_code = compile_candidate_mutant(name, old, new)
        # A fresh machine is required for every distinct code image: Unicorn
        # keeps translated blocks for FUNC_ADDR and does not re-translate them
        # when the same address is overwritten with a different body.
        mutant_runner = Runner()
        detected = False
        for item in cases:
            orig = orig_runner.run(orig_code, item)
            bad = mutant_runner.run(mutant_code, item)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
