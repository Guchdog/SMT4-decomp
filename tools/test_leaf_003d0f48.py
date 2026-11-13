#!/usr/bin/env python3
"""Differential test for engine_func_003d0f48 (0x003D0F48) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the engine_func_003d0f48 body,
resolves its direct calls (including the BLX into the Thumb routine at
0x002B7F0A) to deterministic stubs placed at the original addresses, and runs
the pinned original (extracted/exefs/code.bin) against the candidate in
separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log, with every meaningful register argument, of
    0x002C4450 (byte fill), 0x002A8A08 (camp base getter), 0x002A89E4
    (record), the three 0x0029EE4C predicate calls, 0x002B9364 (lookup),
    0x002C684C (allocation), 0x002B7F0A (sort base/count/size/comparator) and
    0x00250FB4 (release);
  * every byte of the context cell, work object, 4-record table, camp base,
    lookup page, allocation arena and output object;
  * the sorted list of every emulated written byte outside the private stack;
  * faulting cases must fault in both bodies.

Coverage: all four table record flag combinations (bits 1, 4 and 5) in every
order, slot counts 0/1/2/3/5/30/255, negative slot indices (-1, -128), slot
indices 0/29/30/31/127 (the LSL-by-register boundary at shift 31/32/128), null
and non-null record and lookup results, each of the three predicate bits,
pre-set and zero 64-bit masks, all three marker bytes cleared from 0xFF, stable
ordering of equal sort keys, allocation failure and a null lookup record.

Negative controls mutate the hidden/inactive flag constants, the marker limit,
the second predicate bit, the scratch value byte, the high-word sign fill, the
comparator literal and the 0xFF scratch poison.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import capstone
import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch45_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_003d0f48"

FUNC_ADDR = 0x003D0F48
FUNC_SIZE = 688

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers 0x3D0F48 and every stub up to 0x32B580
CTX_ADDR = 0x00700000
CTX_SIZE = 0x00001000
WORK_ADDR = 0x00710000
WORK_SIZE = 0x00010000
TABLE_ADDR = 0x00730000
TABLE_SIZE = 0x00010000
CAMP_ADDR = 0x00750000
CAMP_SIZE = 0x00040000
ABILITY_ADDR = 0x007A0000
ABILITY_SIZE = 0x00010000
ARENA_ADDR = 0x007B0000
ARENA_SIZE = 0x00010000
FLAGS_ADDR = 0x007C0000
FLAGS_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original call targets.  Stubs live at the same addresses, so the pinned bytes
# and the relocated candidate both resolve to them.
STUB_2C4450 = 0x002C4450  # byte fill (tail-calls 0x002C3B4C)
STUB_2A8A08 = 0x002A8A08  # camp base getter (r0 ignored)
STUB_2A89E4 = 0x002A89E4  # record for a signed slot index
STUB_29EE4C = 0x0029EE4C  # u16 flag-bit predicate
STUB_2B9364 = 0x002B9364  # u16 id lookup
STUB_2C684C = 0x002C684C  # AsdMemory allocation
STUB_2B7F0A = 0x002B7F0A  # Thumb sort body (symbol 0x002B7F08)
STUB_2B7F08 = 0x002B7F08
STUB_250FB4 = 0x00250FB4  # null-guarded release wrapper

STUB_NAMES = {
    STUB_2C4450: "camp_func_002c4450",
    STUB_2A8A08: "camp_func_002a8a08",
    STUB_2A89E4: "camp_func_002a89e4",
    STUB_29EE4C: "camp_func_0029ee4c",
    STUB_2B9364: "camp_func_002b9364",
    STUB_2C684C: "AsdMemory_func_002c684c",
    STUB_2B7F0A: "func_002b7f0a",
    STUB_250FB4: "ui_func_00250fb4",
}
SYMBOL_TO_ADDRESS = {name: address for address, name in STUB_NAMES.items()}

COMPARED_PAGES = (
    ("ctx", CTX_ADDR, CTX_SIZE),
    ("work", WORK_ADDR, WORK_SIZE),
    ("table", TABLE_ADDR, TABLE_SIZE),
    ("camp", CAMP_ADDR, CAMP_SIZE),
    ("ability", ABILITY_ADDR, ABILITY_SIZE),
    ("arena", ARENA_ADDR, ARENA_SIZE),
    ("flags", FLAGS_ADDR, FLAGS_SIZE),
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

CONTEXT_TABLE_OFFSET = 0x1FC0
CONTEXT_MASK_OFFSET = 0x1FD0
CONTEXT_MARKER_OFFSET = 0x1FE0
TABLE_STRIDE = 0x288
TABLE_COUNT = 4
SLOT_LIST_OFFSET = 0x90F0
SLOT_COUNT_OFFSET = 0x910B  # only 27 slot bytes precede the count byte
CAMP_RECORD_BASE = 0x90
CAMP_RECORD_STRIDE = 0x604
RECORD_FLAG_OFFSET = 0x44
RECORD_ID_OFFSET = 0x46
RECORD_VALUE_OFFSET = 0x48
COMPARATOR = 0x0032B580

MARKER_DEFAULT = bytes((0x11, 0x22, 0x33))
FLAGS_FILL = 0x5A
ARENA_FILL = 0xCC


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


# ------------------------------------------------------------------ relocation
def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "003d0f48" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"engine_func_003d0f48 not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        target = SYMBOL_TO_ADDRESS.get(rel.symbol_name)
        if target is None:
            raise RuntimeError(
                f"unresolved relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unexpected relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        pc = FUNC_ADDR + rel.offset + 8
        offset = target - pc
        if rel.symbol_name == "func_002b7f0a":
            # R_ARM_CALL to a Thumb symbol: the linker emits BLX (immediate).
            if offset & 1:
                raise RuntimeError(f"unaligned Thumb target 0x{target:08x}")
            instruction = (
                0xFA000000
                | ((offset >> 2) & 0x00FFFFFF)
                | ((offset & 2) << 23)
            )
            struct.pack_into("<I", code, rel.offset, instruction)
        else:
            if offset & 3:
                raise RuntimeError(f"unaligned ARM target 0x{target:08x}")
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | ((offset >> 2) & 0x00FFFFFF)
            )
    return bytes(code), bytes(code_raw)


def compile_candidate_baseline() -> tuple[bytes, bytes, int]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    code, raw = relocate_candidate(obj_file)
    return code, raw, len(raw)


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
    code, _raw = relocate_candidate(obj_file)
    return code


# -------------------------------------------------------------------- fixtures
def camp_record_offset(index: int) -> int:
    return CAMP_RECORD_BASE + index * CAMP_RECORD_STRIDE


def ability_offset(lookup_id: int) -> int:
    return (lookup_id & 7) * 0x40


def build_ctx() -> bytes:
    return struct.pack("<I", WORK_ADDR)


def build_work(case: dict) -> bytes:
    page = bytearray(WORK_SIZE)
    struct.pack_into("<I", page, CONTEXT_TABLE_OFFSET, TABLE_ADDR)
    struct.pack_into("<I", page, CONTEXT_MASK_OFFSET, case.get("mask_low", 0) & 0xFFFFFFFF)
    struct.pack_into(
        "<I", page, CONTEXT_MASK_OFFSET + 4, case.get("mask_high", 0) & 0xFFFFFFFF
    )
    page[CONTEXT_MARKER_OFFSET : CONTEXT_MARKER_OFFSET + 3] = MARKER_DEFAULT
    page[CONTEXT_MARKER_OFFSET + 3 : CONTEXT_MARKER_OFFSET + 8] = b"\xA5" * 5
    return bytes(page)


def build_table(case: dict) -> bytes:
    page = bytearray(TABLE_SIZE)
    page[:] = b"\x5A" * TABLE_SIZE
    words = case.get("table_flags", [0, 0, 0, 0])
    for index in range(TABLE_COUNT):
        word = words[index] if index < len(words) else 0
        struct.pack_into("<I", page, index * TABLE_STRIDE, word & 0xFFFFFFFF)
    return bytes(page)


def build_camp(case: dict) -> bytes:
    page = bytearray(CAMP_SIZE)
    # The 0x604-byte record table starts at +0x90 and its 24th entry lands on
    # the slot list at +0x90F0, so record fixtures are written first and the
    # slot window second, exactly like the real layout.
    records = case.get("records", {})
    for index, fields in records.items():
        base = camp_record_offset(index)
        struct.pack_into("<H", page, base + RECORD_FLAG_OFFSET, fields.get("flags", 0) & 0xFFFF)
        struct.pack_into("<H", page, base + RECORD_ID_OFFSET, fields.get("id", 0x100 + index) & 0xFFFF)
        page[base + RECORD_VALUE_OFFSET] = fields.get("value", 0x40 + index) & 0xFF

    window = case.get("scan_bytes", 0)
    for position in range(window):
        page[SLOT_LIST_OFFSET + position] = 0x80  # negative slot: skipped
    slots = case.get("slots", [])
    for position, value in enumerate(slots):
        page[SLOT_LIST_OFFSET + position] = value & 0xFF
    for position, value in case.get("slot_overrides", {}).items():
        page[SLOT_LIST_OFFSET + position] = value & 0xFF
    page[SLOT_COUNT_OFFSET] = case.get("count", window or len(slots)) & 0xFF
    return bytes(page)


def build_ability(case: dict) -> bytes:
    page = bytearray(ABILITY_SIZE)
    for index in range(8):
        page[index * 0x40 + 2] = 0x10 + index
    for lookup_id, value in case.get("ability_keys", {}).items():
        page[ability_offset(lookup_id) + 2] = value & 0xFF
    return bytes(page)


def build_flags() -> bytes:
    return bytes((FLAGS_FILL,)) * FLAGS_SIZE


class D0F48Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        for _name, address, size in COMPARED_PAGES:
            self.uc.mem_map(address, size)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        arm_stubs = (
            STUB_2C4450,
            STUB_2A8A08,
            STUB_2A89E4,
            STUB_29EE4C,
            STUB_2B9364,
            STUB_2C684C,
            STUB_250FB4,
        )
        for address in arm_stubs:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address)
        for address in (STUB_2B7F08, STUB_2B7F0A):
            self.uc.mem_write(address, struct.pack("<H", 0x4770))  # thumb bx lr
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE,
            self._on_stub,
            begin=STUB_2B7F08,
            end=STUB_2B7F0A + 1,
        )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.alloc_cursor = 0
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append(address)

    def _record_for(self, index: int) -> int:
        null_records = self.case.get("null_records", ())
        if index in null_records:
            return 0
        return CAMP_ADDR + camp_record_offset(index)

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2C4450:
            self._log(address, r0 - WORK_ADDR, r1, r2)
            fill = r2 & 0xFF
            uc.mem_write(r0, bytes((fill,)) * (r1 & 0xFFFFFFFF))
        elif address == STUB_2A8A08:
            # The getter ignores r0 (`ldr r0,[pc]; ldr r0,[r0,#4]; add #0x8c`),
            # so the incoming register value is not part of its contract.
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, CAMP_ADDR)
        elif address == STUB_2A89E4:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self._record_for(r0))
        elif address == STUB_29EE4C:
            self._log(address, r0 - CAMP_ADDR, r1)
            word = struct.unpack("<H", uc.mem_read(r0 + RECORD_FLAG_OFFSET, 2))[0]
            shift = r1 & 0xFF
            bit = (1 << shift) if shift < 32 else 0
            uc.reg_write(arm.UC_ARM_REG_R0, 1 if (word & bit) else 0)
        elif address == STUB_2B9364:
            self._log(address, r0)
            if r0 in self.case.get("null_ids", ()):
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, ABILITY_ADDR + ability_offset(r0))
        elif address == STUB_2C684C:
            self._log(address, r0)
            if self.case.get("alloc_null", False):
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                pointer = ARENA_ADDR + self.alloc_cursor
                self.alloc_cursor += (r0 + 0xFF) & ~0xFF
                uc.reg_write(arm.UC_ARM_REG_R0, pointer)
        elif address in (STUB_2B7F08, STUB_2B7F0A):
            self._log(address, r0 - ARENA_ADDR, r1, r2, r3)
            self._sort(uc, r0, r1, r2)
        elif address == STUB_250FB4:
            self._log(address, r0 - ARENA_ADDR if r0 else 0)
            # 0x00250FB4 is `cmp r0,#0; beq +; b 0x002C4360`; the release path
            # in this stub leaves the observed r0 at the sentinel.
            if r0 != 0:
                uc.reg_write(arm.UC_ARM_REG_R0, 0x00250FB4)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _sort(self, uc, base: int, count: int, size: int) -> None:
        """Stable insertion sort with the 0x0032B580 comparator's key.

        0x0032B580 compares the byte at +1 first and the byte at +2 as the
        tie-breaker, both unsigned, so the scratch entries end up ordered by
        (byte +1, byte +2) and equal keys keep their collected order.
        """
        signed_count = count - (1 << 32) if count & 0x80000000 else count
        if signed_count <= 0 or size == 0:
            return
        entries = [bytearray(uc.mem_read(base + i * size, size)) for i in range(signed_count)]
        for i in range(1, len(entries)):
            current = entries[i]
            key = (current[1], current[2])
            j = i - 1
            while j >= 0 and (entries[j][1], entries[j][2]) > key:
                entries[j + 1] = entries[j]
                j -= 1
            entries[j + 1] = current
        for i, entry in enumerate(entries):
            uc.mem_write(base + i * size, bytes(entry))

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.alloc_cursor = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(CTX_ADDR, build_ctx())
        self.uc.mem_write(WORK_ADDR, build_work(case))
        self.uc.mem_write(TABLE_ADDR, build_table(case))
        self.uc.mem_write(CAMP_ADDR, build_camp(case))
        self.uc.mem_write(ABILITY_ADDR, build_ability(case))
        self.uc.mem_write(ARENA_ADDR, bytes((ARENA_FILL,)) * ARENA_SIZE)
        self.uc.mem_write(FLAGS_ADDR, build_flags())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, FLAGS_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        fault = None
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=10_000_000)
        except unicorn.UcError as error:
            fault = error.errno

        pages = {}
        for name, address, size in COMPARED_PAGES:
            pages[name] = bytes(self.uc.mem_read(address, size))

        # Report which fixture pages were written (and any write that landed
        # outside them) instead of exact byte addresses: a compiler may legally
        # widen, split or drop a store that leaves memory unchanged.
        written = set()
        for address in self.writes:
            if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
                continue
            for name, page_start, page_size in COMPARED_PAGES:
                if page_start <= address < page_start + page_size:
                    written.add(name)
                    break
            else:
                written.add(f"0x{address:08x}")
        written = sorted(written)

        result = {
            "fault": fault,
            "call_log": list(self.call_log),
            "pages": pages,
            "written": written,
        }
        if fault is None:
            result.update(
                {
                    "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
                    "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
                    "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
                    "callee_saved": {
                        name: self.uc.reg_read(register)
                        for name, register in CALLEE_SAVED.items()
                    },
                }
            )
        return result


def compare(orig: dict, cand: dict) -> list[str]:
    problems: list[str] = []
    if orig["fault"] != cand["fault"]:
        problems.append(f"fault: orig={orig['fault']} cand={cand['fault']}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"]) + "\n    cand="
            + repr(cand["call_log"])
        )
    for name, _address, _size in COMPARED_PAGES:
        if orig["pages"][name] != cand["pages"][name]:
            left = orig["pages"][name]
            right = cand["pages"][name]
            first = next(
                (i for i in range(len(left)) if left[i] != right[i]), None
            )
            problems.append(
                f"page {name} differs first at +0x{first:x} "
                f"(orig=0x{left[first]:02x} cand=0x{right[first]:02x})"
            )
    if orig["written"] != cand["written"]:
        problems.append(
            f"written pages differ: orig={orig['written']} cand={cand['written']}"
        )
    if orig["fault"] is None:
        for key in ("ret", "pc", "sp", "callee_saved"):
            if orig[key] != cand[key]:
                problems.append(f"{key}: orig={orig[key]!r} cand={cand[key]!r}")
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {"name": name}
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- first loop: the leading flag word of the four table records
    cases.append(base_case("table flags clear", table_flags=[0, 0, 0, 0], slots=[]))
    cases.append(base_case("table bit1 first record", table_flags=[0x02, 0, 0, 0], slots=[]))
    cases.append(base_case("table bit5 first record", table_flags=[0x20, 0, 0, 0], slots=[]))
    cases.append(base_case("table bit4 first record", table_flags=[0x10, 0, 0, 0], slots=[]))
    cases.append(
        base_case(
            "table all records skipped",
            table_flags=[0x32, 0x12, 0x22, 0x02],
            slots=[],
        )
    )
    cases.append(
        base_case(
            "table high bits ignored",
            table_flags=[0x80000000, 0xFFFFFFFF, 0x00000010, 0x00000020],
            slots=[],
        )
    )
    cases.append(
        base_case(
            "table unrelated bits",
            table_flags=[0x04, 0x08, 0x40, 0x80],
            slots=[],
        )
    )
    cases.append(
        base_case(
            "table mixed per record",
            table_flags=[0x00, 0x02, 0x10, 0x20],
            slots=[],
        )
    )

    # --- slot counts and the three marker positions
    cases.append(base_case("count 0", slots=[], count=0))
    cases.append(base_case("count 0 allocation failure", slots=[], count=0, alloc_null=True))
    cases.append(
        base_case(
            "count 1 one record",
            slots=[0],
            records={0: {"flags": 0, "id": 0x101, "value": 0x41}},
        )
    )
    cases.append(
        base_case(
            "count 2 two records",
            slots=[0, 1],
            records={
                0: {"flags": 0, "id": 0x101, "value": 0x41},
                1: {"flags": 0, "id": 0x102, "value": 0x42},
            },
        )
    )
    cases.append(
        base_case(
            "count 3 three records",
            slots=[0, 1, 2],
            records={
                0: {"flags": 0, "id": 0x101, "value": 0x41},
                1: {"flags": 0, "id": 0x102, "value": 0x42},
                2: {"flags": 0, "id": 0x103, "value": 0x43},
            },
        )
    )
    cases.append(
        base_case(
            "count 5 clamps to three",
            slots=[0, 1, 2, 3, 4],
            records={index: {"flags": 0, "id": 0x101 + index, "value": 0x50 + index} for index in range(5)},
        )
    )
    cases.append(
        base_case(
            "count 30 mixed",
            scan_bytes=30,
            slots=list(range(24)),
            slot_overrides={24: 0, 25: 1, 26: 2, 28: 3, 29: 4},
            records={index: {"flags": 0, "id": 0x101 + index, "value": 0x30 + index} for index in range(24)},
        )
    )
    cases.append(
        base_case(
            "count 255 maximum",
            scan_bytes=255,
            slot_overrides={position: position % 24 for position in range(28, 255)},
            records={index: {"flags": 0, "id": 0x101 + index, "value": 0x60 + index} for index in range(24)},
        )
    )

    # --- signed slot indices and the LSL-by-register boundaries
    cases.append(
        base_case(
            "negative slot indices",
            slots=[0xFF, 0x80, 0, 0x81],
            records={0: {"flags": 0, "id": 0x101, "value": 0x41}},
        )
    )
    for index in (0, 23, 29, 127):
        cases.append(
            base_case(
                f"record index {index}",
                slots=[index],
                records={index: {"flags": 0, "id": 0x200 + index, "value": 0x40}},
            )
        )
    cases.append(
        base_case(
            "record indices 29,30,31",
            slots=[29, 30, 31],
            records={index: {"flags": 0, "id": 0x200 + index, "value": 0x40 + index} for index in (29, 30, 31)},
        )
    )
    # The published byte is the *slot position* + 1, so the shift boundary is
    # reached from long scanned windows.  Position 27 always reads the count
    # byte, which is negative for these counts.
    for position in (29, 30, 31, 127):
        cases.append(
            base_case(
                f"slot position {position} shift boundary",
                scan_bytes=128,
                count=128,
                slot_overrides={position: 0},
                records={0: {"flags": 0, "id": 0x101, "value": 0x41}},
                mask_low=0x00000001,
                mask_high=0x00000002,
            )
        )

    # --- the three predicate bits of the record's +0x44 word
    for bits, name in (
        (0x0001, "predicate bit 1"),
        (0x0004, "predicate bit 2"),
        (0x0400, "predicate bit 10"),
        (0x0005, "predicate bits 1 and 2"),
        (0x0401, "predicate bits 1 and 10"),
        (0x0405, "predicate bits 1, 2 and 10"),
        (0x8000, "predicate unrelated bit"),
        (0xFFFF & ~(0x0001 | 0x0004 | 0x0400), "predicate other bits"),
    ):
        cases.append(
            base_case(
                name,
                slots=[0, 1],
                records={
                    0: {"flags": bits, "id": 0x101, "value": 0x41},
                    1: {"flags": 0, "id": 0x102, "value": 0x42},
                },
            )
        )

    # --- null record and null lookup results
    cases.append(
        base_case(
            "null record for slot 5",
            slots=[5, 0],
            null_records=(5,),
            records={0: {"flags": 0, "id": 0x101, "value": 0x41}},
        )
    )
    cases.append(
        base_case(
            "all records null",
            slots=[1, 2],
            null_records=(1, 2),
        )
    )
    cases.append(
        base_case(
            "null lookup record",
            slots=[0],
            records={0: {"flags": 0, "id": 0x700, "value": 0x41}},
            null_ids=(0x700,),
        )
    )
    cases.append(
        base_case(
            "allocation failure with count",
            slots=[0],
            alloc_null=True,
            records={0: {"flags": 0, "id": 0x101, "value": 0x41}},
        )
    )

    # --- ordering: sort by byte +1 then byte +2, stable for equal keys
    cases.append(
        base_case(
            "sort reorders three entries",
            slots=[5, 1, 3],
            records={
                5: {"flags": 0, "id": 0x105, "value": 0x90},
                1: {"flags": 0, "id": 0x101, "value": 0x10},
                3: {"flags": 0, "id": 0x103, "value": 0x50},
            },
            ability_keys={0x101: 0x20, 0x103: 0x30, 0x105: 0x10},
        )
    )
    cases.append(
        base_case(
            "sort tie breaks on byte +2",
            slots=[7, 2],
            records={
                7: {"flags": 0, "id": 0x107, "value": 0x40},
                2: {"flags": 0, "id": 0x102, "value": 0x40},
            },
            ability_keys={0x107: 0x99, 0x102: 0x11},
        )
    )
    cases.append(
        base_case(
            "sort keeps equal keys stable",
            slots=[4, 2],
            records={
                4: {"flags": 0, "id": 0x104, "value": 0x40},
                2: {"flags": 0, "id": 0x102, "value": 0x40},
            },
            ability_keys={0x104: 0x77, 0x102: 0x77},
        )
    )
    cases.append(
        base_case(
            "sort clamp keeps smallest three",
            slots=[9, 4, 8, 1],
            records={
                9: {"flags": 0, "id": 0x109, "value": 0x90},
                4: {"flags": 0, "id": 0x104, "value": 0x40},
                8: {"flags": 0, "id": 0x108, "value": 0x80},
                1: {"flags": 0, "id": 0x101, "value": 0x10},
            },
            ability_keys={0x109: 0x09, 0x104: 0x04, 0x108: 0x08, 0x101: 0x01},
        )
    )

    # --- mask and marker pre-state
    cases.append(
        base_case(
            "pre-set 64-bit mask",
            slots=[0, 1],
            mask_low=0x12345679,
            mask_high=0x9ABCDEF0,
            records={
                0: {"flags": 0, "id": 0x101, "value": 0x41},
                1: {"flags": 0, "id": 0x102, "value": 0x42},
            },
        )
    )
    cases.append(
        base_case(
            "mask filled for slot 30",
            slots=[30],
            mask_low=0x80000000,
            mask_high=0xFFFFFFFF,
            records={30: {"flags": 0, "id": 0x11E, "value": 0x40}},
        )
    )
    cases.append(
        base_case(
            "marker bytes overwritten with 0xFF",
            slots=[1, 2],
            records={
                1: {"flags": 0, "id": 0x101, "value": 0x41},
                2: {"flags": 0, "id": 0x102, "value": 0x42},
            },
        )
    )

    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases: list[dict]) -> int:
    passed = 0
    for case in cases:
        orig = D0F48Runner().run(orig_code, case)
        cand = D0F48Runner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        kind = "fault" if orig["fault"] is not None else f"{len(orig['call_log'])} calls"
        print(f"  [PASS] {case['name']}  ({kind})")
    return passed


def main() -> None:
    print("Testing engine_func_003d0f48 (0x003D0F48)...")
    orig_code = get_orig_bytes()
    cand_code, cand_raw, raw_size = compile_candidate_baseline()

    # The BLX into the Thumb sort body must land on 0x002B7F0A in the candidate.
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    md.detail = True
    blx_targets = [
        i.operands[0].imm
        for i in md.disasm(cand_code, FUNC_ADDR)
        if i.mnemonic == "blx"
    ]
    assert blx_targets == [STUB_2B7F0A], f"candidate BLX targets {blx_targets}"

    identical = sum(
        1 for left, right in zip(orig_code, cand_raw) if left == right
    )
    print(
        f"Original {len(orig_code)} B, candidate body {raw_size} B "
        f"({identical}/{len(orig_code)} bytes identical, not an acceptance gate)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        ("hidden_flag", "constexpr u32 kFlagHidden = 0x20u;",
         "constexpr u32 kFlagHidden = 0x40u;"),
        ("inactive_flag", "constexpr u32 kFlagInactive = 0x10u;",
         "constexpr u32 kFlagInactive = 0x00u;"),
        ("marker_limit", "constexpr u32 kMarkerLimit = 3;",
         "constexpr u32 kMarkerLimit = 2;"),
        ("second_predicate", "constexpr u32 kPredicateSecond = 0xAu;",
         "constexpr u32 kPredicateSecond = 0x9u;"),
        ("sort_value_byte",
         "entry[kEntryValueOffset] = record[kRecordValueOffset];",
         "entry[kEntryValueOffset] = record[kRecordValueOffset + 1u];"),
        ("mask_sign_fill", "return (bit & 0x80000000u) != 0u ? 0xFFFFFFFFu : 0u;",
         "return 0u;"),
        ("comparator_literal", "constexpr u32 kComparator = 0x0032B580u;",
         "constexpr u32 kComparator = 0x0032B584u;"),
        ("scratch_poison", "constexpr u32 kEntryInitIndex = 0xFFu;",
         "constexpr u32 kEntryInitIndex = 0xFEu;"),
    )
    for name, old, new in mutants:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = D0F48Runner().run(orig_code, case)
            mutant = D0F48Runner().run(mutant_code, case)
            if compare(orig, mutant):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
