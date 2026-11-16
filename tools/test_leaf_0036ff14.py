#!/usr/bin/env python3
"""Differential test for func_0036ff14 (0x0036ff14) using Unicorn ARM.

The candidate in src/engine/leaf_batch41_c.cpp is compiled, its four direct
calls are relocated to deterministic stubs at the original ROM targets, and the
pinned original (extracted/exefs/code.bin) runs against the candidate in
separate machines on identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log with every register argument, the architected stack
    word of 0x003E2E40, the resolved name string and the identity of the
    indirect allocator target;
  * the full slot/container/entry/blob/allocator/vtable/low-page/data pages;
  * every non-stack emulated write, in order.

Coverage: signed loop bounds 0/-1/1/2/3, unresolved and already-resolved
entries, primary hit, retry hit, double failure (flag 0x10), signed result
boundaries 0/1/0x7FFFFFFF/0x80000000/-1, a null relative name, a zero table
offset (the original then reads the pointer at absolute 0x40), pre-seeded kind
bytes, a cached blob pointer, a null allocator argument selecting the global
default, a null allocation, zero/0xFFFFFFFF sizes and lengths, and two distinct
indirect allocator targets.

Negative controls mutate the count, value, sentinel, failure-flag, allocator
slot and table-pointer offsets; each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_0036ff14"

FUNC_ADDR = 0x0036FF14
FUNC_SIZE = 432

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # function plus every direct-call and stub target
DATA_ADDR = 0x00470000
DATA_SIZE = 0x00010000  # contains the 0x00471C40 global
SLOT_ADDR = 0x00710000
SLOT_SIZE = 0x00001000
CONTAINER_ADDR = 0x00720000
CONTAINER_SIZE = 0x00010000
ENTRY_ADDR = 0x00730000
ENTRY_SIZE = 0x00010000
TABLE_ADDR = 0x00740000
TABLE_SIZE = 0x00001000
BLOB_ADDR = 0x00750000
BLOB_SIZE = 0x00010000
ALLOC_ADDR = 0x00760000
ALLOC_SIZE = 0x00001000
VTABLE_ADDR = 0x00770000
VTABLE_SIZE = 0x00001000
ARENA_ADDR = 0x00780000
ARENA_SIZE = 0x00010000
LOW_ADDR = 0x00000000
LOW_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

DEFAULT_ALLOCATOR_GLOBAL = 0x00471C40

# Original direct-call targets; the stubs live at the same addresses so both
# the original bytes and the relocated candidate resolve to them.
STUB_3E2594 = 0x003E2594
STUB_3E2EEC = 0x003E2EEC
STUB_3E2E40 = 0x003E2E40

# Two allocator interface methods so the indirect target itself is compared.
STUB_ALLOC_A = 0x001FF000
STUB_ALLOC_B = 0x001FF100

STUB_NAMES = {
    STUB_3E2594: "engine_func_003e2594",
    STUB_3E2EEC: "func_003e2eec",
    STUB_3E2E40: "func_003e2e40",
    STUB_ALLOC_A: "allocator_A",
    STUB_ALLOC_B: "allocator_B",
}

DIRECT_STUBS = (STUB_3E2594, STUB_3E2EEC, STUB_3E2E40)
ALLOC_STUBS = (STUB_ALLOC_A, STUB_ALLOC_B)

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

MASK32 = 0xFFFFFFFF
DEFAULT_COUNT = 1
DEFAULT_PRIMARY_INDEX = 0x0C
DEFAULT_SECONDARY_INDEX = 0x10
DEFAULT_SIZE = 0x120
DEFAULT_USED = 0x100
DEFAULT_ALLOC = ARENA_ADDR + 0x800
DEFAULT_BLOB = 0x00000000


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0036ff14" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"func_0036ff14 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    seen = set()
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address in DIRECT_STUBS:
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        if target & 3:
            raise RuntimeError(f"unaligned direct-call target 0x{target:08x}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
        )
        seen.add(target)
    if seen != set(DIRECT_STUBS):
        raise RuntimeError(f"missing call relocations, saw {sorted(seen)}")
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


# ------------------------------------------------------------------ fixtures
def write_u32(page: bytearray, base: int, address: int, value: int) -> None:
    struct.pack_into("<I", page, address - base, value & MASK32)


def write_u8(page: bytearray, base: int, address: int, value: int) -> None:
    page[address - base] = value & 0xFF


def entry_address(index: int) -> int:
    return ENTRY_ADDR + 0x800 + index * 0x100


def entry_slot_address(index: int) -> int:
    return ENTRY_ADDR + index * 4


def build_entry_page(case: dict) -> bytes:
    """Slot array plus one record per configured entry."""
    page = bytearray([0xCC]) * ENTRY_SIZE
    entries = case.get("entries", ())
    for index, entry in enumerate(entries):
        record = entry_address(index)
        name_offset = entry.get("name_offset", 0x40)
        write_u32(page, ENTRY_ADDR, record + 0x00, name_offset)
        page[record - ENTRY_ADDR + 0x05] = entry.get("kind", 0x5A)
        write_u32(page, ENTRY_ADDR, record + 0x08, entry.get("value", 0))
        if name_offset:
            name = entry.get("name", b"name%d" % index) + b"\x00"
            start = record - ENTRY_ADDR + name_offset
            page[start : start + len(name)] = name
        if case.get("slot_zero") and index == 0:
            slot_offset = 0
        else:
            slot_offset = record - entry_slot_address(index)
        write_u32(page, ENTRY_ADDR, entry_slot_address(index), slot_offset)
    return bytes(page)


def build_container_page(case: dict) -> bytes:
    page = bytearray([0xCC]) * CONTAINER_SIZE
    array_offset = case.get(
        "array_offset", entry_slot_address(0) - (CONTAINER_ADDR + 0x18)
    )
    table_offset = case.get(
        "table_offset", (CONTAINER_ADDR + 0x2000) - (CONTAINER_ADDR + 0x84)
    )
    write_u32(page, CONTAINER_ADDR, CONTAINER_ADDR + 0x14,
              case.get("count", DEFAULT_COUNT))
    write_u32(page, CONTAINER_ADDR, CONTAINER_ADDR + 0x18, array_offset)
    write_u32(page, CONTAINER_ADDR, CONTAINER_ADDR + 0x0C,
              case.get("primary_index", DEFAULT_PRIMARY_INDEX))
    write_u32(page, CONTAINER_ADDR, CONTAINER_ADDR + 0x10,
              case.get("secondary_index", DEFAULT_SECONDARY_INDEX))
    write_u32(page, CONTAINER_ADDR, CONTAINER_ADDR + 0x84, table_offset)
    write_u32(page, CONTAINER_ADDR, CONTAINER_ADDR + 0x7C,
              case.get("blob", DEFAULT_BLOB))
    write_u32(page, CONTAINER_ADDR, CONTAINER_ADDR + 0x80,
              case.get("blob_length", 0xDEADBEEF))
    # Table block addressed by the relative +0x84 offset.
    write_u32(page, CONTAINER_ADDR, CONTAINER_ADDR + 0x2000 + 0x40,
              case.get("table", TABLE_ADDR))
    return bytes(page)


def build_data_page(case: dict) -> bytes:
    page = bytearray([0xCC]) * DATA_SIZE
    write_u32(
        page,
        DATA_ADDR,
        DEFAULT_ALLOCATOR_GLOBAL,
        case.get("global_allocator", ALLOC_ADDR),
    )
    return bytes(page)


def build_low_page(case: dict) -> bytes:
    page = bytearray(LOW_SIZE)
    write_u32(page, LOW_ADDR, 0x40, case.get("low_table", TABLE_ADDR))
    for index, value in enumerate(case.get("low_slots", ())):
        write_u32(page, LOW_ADDR, index * 4, value)
    return bytes(page)


def build_allocator_page(case: dict) -> bytes:
    page = bytearray([0xCC]) * ALLOC_SIZE
    write_u32(page, ALLOC_ADDR, ALLOC_ADDR, VTABLE_ADDR)
    return bytes(page)


def build_vtable_page(case: dict) -> bytes:
    page = bytearray([0xCC]) * VTABLE_SIZE
    write_u32(page, VTABLE_ADDR, VTABLE_ADDR + 0x00, 0x11111111)
    write_u32(page, VTABLE_ADDR, VTABLE_ADDR + 0x04, 0x22222222)
    write_u32(page, VTABLE_ADDR, VTABLE_ADDR + 0x08,
              case.get("alloc_stub", STUB_ALLOC_A))
    write_u32(page, VTABLE_ADDR, VTABLE_ADDR + 0x0C, 0x33333333)
    return bytes(page)


def read_c_string(uc, address: int, limit: int = 24) -> bytes:
    if address == 0:
        return b""
    out = bytearray()
    try:
        for index in range(limit):
            byte = uc.mem_read(address + index, 1)[0]
            if byte == 0:
                break
            out.append(byte)
    except Exception:
        return b"<unmapped>"
    return bytes(out)


class Runner:
    """One Unicorn machine with deterministic stubs at the ROM targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(SLOT_ADDR, SLOT_SIZE)
        self.uc.mem_map(CONTAINER_ADDR, CONTAINER_SIZE)
        self.uc.mem_map(ENTRY_ADDR, ENTRY_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
        self.uc.mem_map(BLOB_ADDR, BLOB_SIZE)
        self.uc.mem_map(ALLOC_ADDR, ALLOC_SIZE)
        self.uc.mem_map(VTABLE_ADDR, VTABLE_SIZE)
        self.uc.mem_map(ARENA_ADDR, ARENA_SIZE)
        self.uc.mem_map(LOW_ADDR, LOW_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in DIRECT_STUBS + ALLOC_STUBS:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.lookup_index = 0

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", bytes(raw))

    def _is_stack(self, value: int) -> bool:
        return STACK_ADDR <= value < STACK_ADDR + STACK_SIZE

    def _normalise(self, value: int) -> object:
        return "<stack>" if self._is_stack(value) else value

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _next_lookup(self) -> int:
        script = self.case.get("lookups", ())
        if self.lookup_index < len(script):
            result = script[self.lookup_index]
        else:
            result = -1
        self.lookup_index += 1
        return result & MASK32

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_3E2594:
            name = read_c_string(uc, r3)
            self._log(address, self._normalise(r0), r1, r2, r3, name)
            value = self._next_lookup()
            uc.mem_write(r0, struct.pack("<i", value - 0x100000000
                                         if value & 0x80000000 else value))
            uc.mem_write(r0 + 4, bytes([self.lookup_index & 0xFF]))
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_3E2EEC:
            self._log(address, r0, r1, r2)
            uc.reg_write(arm.UC_ARM_REG_R0,
                         self.case.get("size", DEFAULT_SIZE) & MASK32)
        elif address == STUB_3E2E40:
            used = self.case.get("used", DEFAULT_USED) & MASK32
            self._log(address, r0, r1, r2, r3, self._stack_words(1)[0])
            if r3 != 0:
                payload = struct.pack("<I", used) + b"\xA5" * 12
                uc.mem_write(r3, payload)
            uc.reg_write(arm.UC_ARM_REG_R0, used)
        elif address in ALLOC_STUBS:
            self._log(address, r0, r1, r2)
            buffer = self.case.get("alloc_result", DEFAULT_ALLOC)
            uc.reg_write(arm.UC_ARM_REG_R0, buffer & MASK32)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.lookup_index = 0

        self.uc.mem_write(SLOT_ADDR, b"\x00" * SLOT_SIZE)
        self.uc.mem_write(SLOT_ADDR, struct.pack("<I", CONTAINER_ADDR))
        self.uc.mem_write(CONTAINER_ADDR, build_container_page(case))
        self.uc.mem_write(ENTRY_ADDR, build_entry_page(case))
        self.uc.mem_write(TABLE_ADDR, b"\x5A" * TABLE_SIZE)
        self.uc.mem_write(BLOB_ADDR, b"\x00" * BLOB_SIZE)
        self.uc.mem_write(ARENA_ADDR, b"\x00" * ARENA_SIZE)
        self.uc.mem_write(ALLOC_ADDR, build_allocator_page(case))
        self.uc.mem_write(VTABLE_ADDR, build_vtable_page(case))
        self.uc.mem_write(DATA_ADDR, build_data_page(case))
        self.uc.mem_write(LOW_ADDR, build_low_page(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.uc.mem_write(FUNC_ADDR, b"\x00" * 0x400)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.ctl_flush_tb()
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SLOT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1,
                          case.get("allocator", ALLOC_ADDR) & MASK32)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        non_stack_writes = [
            (address, size, value)
            for address, size, value in self.writes
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        ]

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self.call_log,
            "writes": non_stack_writes,
            "pages": {
                "slot": bytes(self.uc.mem_read(SLOT_ADDR, SLOT_SIZE)),
                "container": bytes(self.uc.mem_read(CONTAINER_ADDR,
                                                   CONTAINER_SIZE)),
                "entry": bytes(self.uc.mem_read(ENTRY_ADDR, ENTRY_SIZE)),
                "blob": bytes(self.uc.mem_read(BLOB_ADDR, BLOB_SIZE)),
                "alloc": bytes(self.uc.mem_read(ALLOC_ADDR, ALLOC_SIZE)),
                "vtable": bytes(self.uc.mem_read(VTABLE_ADDR, VTABLE_SIZE)),
                "arena": bytes(self.uc.mem_read(ARENA_ADDR, ARENA_SIZE)),
                "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
                "low": bytes(self.uc.mem_read(LOW_ADDR, LOW_SIZE)),
            },
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"])
            + "\n    cand=" + repr(cand["call_log"])
        )
    if orig["writes"] != cand["writes"]:
        problems.append(
            "non-stack writes:\n    orig=" + repr(orig["writes"])
            + "\n    cand=" + repr(cand["writes"])
        )
    for key, value in orig["pages"].items():
        if value != cand["pages"][key]:
            problems.append(f"page {key} differs")
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "count": DEFAULT_COUNT,
        "primary_index": DEFAULT_PRIMARY_INDEX,
        "secondary_index": DEFAULT_SECONDARY_INDEX,
        "allocator": ALLOC_ADDR,
        "blob": DEFAULT_BLOB,
        "size": DEFAULT_SIZE,
        "used": DEFAULT_USED,
        "alloc_result": DEFAULT_ALLOC,
        "alloc_stub": STUB_ALLOC_A,
        "lookups": (0x11,),
        "entries": ({"kind": 0x00, "value": 0xFFFFFFFF},),
    }
    case.update(overrides)
    return case


def resolved(value: int, **extra) -> dict:
    entry = {"kind": 0x00, "value": value & MASK32}
    entry.update(extra)
    return entry


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- loop bounds (signed count) with a cached and with a null blob
    cases.append(base_case("count 0 cached blob", count=0, blob=0x12345678))
    cases.append(base_case("count 0 serialize", count=0))
    cases.append(base_case("count -1 sorted before loop", count=-1))
    cases.append(base_case("count 0x80000000 signed negative", count=-0x80000000))

    # --- skip paths: already resolved or a non-sentinel neighbour
    cases.append(base_case("entry already resolved", entries=(resolved(7),),
                           blob=0x1000))
    cases.append(base_case("entry 0xFFFFFFFE is not the sentinel",
                           entries=(resolved(0xFFFFFFFE),), blob=0x1000))
    cases.append(base_case("entry zero is not the sentinel",
                           entries=({"kind": 0x77, "value": 0},), blob=0x1000))

    # --- primary hit, every signed boundary of the returned value
    for value in (0, 1, 0x7FFFFFFF):
        cases.append(base_case(
            f"primary hit {value:#x}",
            entries=({"kind": 0x99, "value": 0xFFFFFFFF},),
            lookups=(value,),
        ))
    cases.append(base_case(
        "primary hit clears seeded kind byte",
        entries=({"kind": 0x80, "value": 0xFFFFFFFF},),
        lookups=(0x1234,),
    ))

    # --- primary failure, retry hit; also every negative result form
    for second in (0, 1, 0x7FFFFFFF):
        cases.append(base_case(
            f"retry hit {second:#x}",
            entries=({"kind": 0x5A, "value": 0xFFFFFFFF},),
            lookups=(-1, second),
        ))
    cases.append(base_case(
        "primary 0x80000000 then retry 3",
        entries=({"kind": 0x5A, "value": 0xFFFFFFFF},),
        lookups=(0x80000000, 3),
    ))
    cases.append(base_case(
        "primary -1 then retry 0x80000000 fails",
        entries=({"kind": 0x5A, "value": 0xFFFFFFFF},),
        lookups=(-1, 0x80000000),
    ))

    # --- double failure sets 0x10 and stores -1
    cases.append(base_case(
        "double failure",
        entries=({"kind": 0xA5, "value": 0xFFFFFFFF},
                 {"kind": 0x00, "value": 0xFFFFFFFF}),
        count=2,
        lookups=(-1, -1, -2, -3),
    ))
    cases.append(base_case(
        "double failure with cached blob",
        entries=({"kind": 0xA5, "value": 0xFFFFFFFF},),
        lookups=(-1, 0x80000000),
        blob=0x1234,
    ))

    # --- mixed multi-entry walk: last index is the loop bound
    cases.append(base_case(
        "mixed three entries",
        entries=(
            {"kind": 0x11, "value": 0xFFFFFFFF},
            {"kind": 0x22, "value": 0x44},
            {"kind": 0x33, "value": 0xFFFFFFFF},
        ),
        count=3,
        lookups=(0x10, -1, -1),
    ))
    cases.append(base_case(
        "mixed two entries, retry then primary",
        entries=(
            {"kind": 0x11, "value": 0xFFFFFFFF},
            {"kind": 0x22, "value": 0xFFFFFFFF},
        ),
        count=2,
        lookups=(-1, -1, 0x21, 0x22),
    ))
    cases.append(base_case(
        "count 3 but only the last entry is unresolved",
        entries=(
            {"kind": 0x11, "value": 1},
            {"kind": 0x22, "value": 2},
            {"kind": 0x33, "value": 0xFFFFFFFF},
        ),
        count=3,
        lookups=(9,),
    ))

    # --- relative name: null name and custom strings
    cases.append(base_case(
        "null relative name",
        entries=({"kind": 0x00, "value": 0xFFFFFFFF, "name_offset": 0},),
        lookups=(5,),
    ))
    cases.append(base_case(
        "custom name strings",
        entries=(
            {"kind": 0x00, "value": 0xFFFFFFFF, "name": b"alpha"},
            {"kind": 0x00, "value": 0xFFFFFFFF, "name": b"beta/gamma"},
        ),
        count=2,
        lookups=(-1, -1, 0x30, 0x31),
    ))

    # --- zero relative offsets: the original reads absolute low addresses
    cases.append(base_case(
        "zero table offset reads low page",
        entries=({"kind": 0x00, "value": 0xFFFFFFFF},),
        table_offset=0,
        low_table=TABLE_ADDR,
        lookups=(0x77,),
    ))
    cases.append(base_case(
        "zero table offset with a null low pointer",
        entries=({"kind": 0x00, "value": 0xFFFFFFFF},),
        table_offset=0,
        low_table=0,
        lookups=(0x77,),
    ))
    cases.append(base_case(
        "zero array offset reads low slots",
        entries=({"kind": 0x00, "value": 0xFFFFFFFF},),
        array_offset=0,
        low_slots=(entry_address(0),),
        lookups=(0x42,),
    ))
    cases.append(base_case(
        "zero slot offset reads absolute address 8",
        entries=({"kind": 0x00, "value": 0xFFFFFFFF},),
        slot_zero=True,
        lookups=(0x42,),
    ))

    # --- serialization tail variations
    cases.append(base_case("tail serialize baseline"))
    cases.append(base_case("tail size 0", size=0, used=0))
    cases.append(base_case("tail size 0xFFFFFFFF", size=0xFFFFFFFF,
                           used=0xFFFFFFFF))
    cases.append(base_case("tail used 0", used=0))
    cases.append(base_case("tail used negative", used=0xFFFFFFFF))
    cases.append(base_case("null allocation result", alloc_result=0))
    cases.append(base_case("allocator B indirect target",
                           alloc_stub=STUB_ALLOC_B))
    cases.append(base_case("null allocator argument uses global default",
                           allocator=0))
    cases.append(base_case("global default allocator B",
                           allocator=0, alloc_stub=STUB_ALLOC_B))
    cases.append(base_case(
        "tail table offset selects block",
        entries=({"kind": 0x00, "value": 0xFFFFFFFF},),
        lookups=(0x55,),
        table=0x00740040,
    ))
    cases.append(base_case(
        "primary and secondary indexes forwarded",
        primary_index=0x11223344,
        secondary_index=0x55667788,
        entries=({"kind": 0x00, "value": 0xFFFFFFFF},),
        lookups=(-1, 0x99),
    ))
    cases.append(base_case(
        "cached blob keeps length untouched",
        blob=0xDEADBEEF,
        blob_length=0xCAFEBABE,
        entries=({"kind": 0x00, "value": 0xFFFFFFFF},),
        lookups=(0x11,),
    ))
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
    print("Testing func_0036ff14 (0x0036ff14)...")
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
        ("count_offset", "constexpr u32 kEntryCountOffset = 0x14;",
         "constexpr u32 kEntryCountOffset = 0x18;"),
        ("value_offset", "constexpr u32 kEntryValueOffset = 0x08;",
         "constexpr u32 kEntryValueOffset = 0x0C;"),
        ("sentinel", "constexpr u32 kUnresolvedValue = 0xFFFFFFFF;",
         "constexpr u32 kUnresolvedValue = 0xFFFFFFFE;"),
        ("failure_flag", "constexpr u32 kLookupFailedFlag = 0x10;",
         "constexpr u32 kLookupFailedFlag = 0x20;"),
        ("allocator_slot", "constexpr u32 kAllocatorSlot = 2;",
         "constexpr u32 kAllocatorSlot = 3;"),
        ("table_pointer_offset", "constexpr u32 kTablePointerOffset = 0x40;",
         "constexpr u32 kTablePointerOffset = 0x44;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            try:
                bad = Runner().run(mutant_code, case)
            except RuntimeError:
                # A mutant that faults where the original completes is a
                # different observable outcome.
                detected = True
                break
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
