#!/usr/bin/env python3
"""Differential test for engine_func_00152b0c (0x00152b0c) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the engine_func_00152b0c body,
resolves its direct calls to deterministic stubs placed at the pinned targets,
and runs the pinned original (extracted/exefs/code.bin) against the candidate in
separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC and final SP;
  * callee-saved r4-r11 (r12 is caller-saved; the original happens to preserve
    it through its push list, the candidate does not -- see the function record);
  * the ordered call log with every register argument of each helper;
  * every byte written outside the private stack, as an address->byte map (this
    normalises the original's two `strb` gate writes against the candidate's
    single `strh`);
  * the full table page, frame-sync page, action record, pending records, entry
    page and container page.

Fixture control (case dictionary):
  * state                 - action +0x0C
  * pending               - None or {"record": i, "gate": w, "side": w}
  * entries               - list of container indices (None -> null container)
  * vectors               - {container index: [word | ("entry", i), ...]}
  * count                 - explicit signed entry count (default len(entries))
  * container_table       - (slot 0, slot 1) container-table words
  * token                 - (slot 0, slot 1) token-table words
  * registry/work         - (slot 0, slot 1) table words
  * sync_counts           - (slot 0, slot 1) signed frame counters
  * registered/inited     - (slot 0, slot 1) gate bytes at +0x04/+0x05
  * after_detach          - writes applied by the 0x2C028C stub before it returns
  * after_retire          - writes applied by one 0x2ABDB0 call
  * retire_mutation_call  - 0-based index of the 0x2ABDB0 call that mutates
  * expect_fault          - both machines must fault at the same point
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
OUT_DIR = ROOT / "build/test_leaf_00152b0c"

FUNC_ADDR = 0x00152B0C
FUNC_SIZE = 600

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x300000
TABLE_ADDR = 0x00460000
TABLE_SIZE = 0x00010000
SYNC_ADDR = 0x004D0000
SYNC_SIZE = 0x00010000
ACTION_ADDR = 0x00700000
ACTION_SIZE = 0x00001000
PENDING_ADDR = 0x00701000
PENDING_SIZE = 0x00001000
ENTRIES_ADDR = 0x00702000
ENTRIES_SIZE = 0x00001000
CONTAINERS_ADDR = 0x00703000
CONTAINERS_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Pinned globals (literal pool 0x152D50..0x152D63).
WORK_TABLE = 0x00464B7C
REGISTRY_TABLE = 0x00464B84
TOKEN_TABLE = 0x00464B8C
CONTAINER_TABLE = 0x00464B94
FRAME_SYNC = 0x004DAD80
FRAME_SYNC_STRIDE = 0x18
SLOT_STRIDE = 4

# Original direct-call targets; stubs live at the same addresses so both the
# original bytes and the relocated candidate resolve to them.
STUB_2A3068 = 0x002A3068
STUB_2C028C = 0x002C028C
STUB_2ABDB0 = 0x002ABDB0
STUB_NAMES = {
    STUB_2A3068: "battle_func_002a3068",
    STUB_2C028C: "engine_func_002c028c",
    STUB_2ABDB0: "engine_func_002abdb0",
}

# Fixture layout inside the private pages.
ENTRY_BASE = 0x100
ENTRY_STRIDE = 0x40
CONTAINER_BASE = 0x100
CONTAINER_STRIDE = 0x100
VECTOR_BASE = 0x800
VECTOR_STRIDE = 0x100
VECTOR_WORDS = 32
CONTAINER_COUNT = 3

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
SCRATCH_12_START = 0xCCCCCCCC


def entry_address(index: int) -> int:
    return ENTRIES_ADDR + ENTRY_BASE + index * ENTRY_STRIDE


def container_address(index: int) -> int:
    return CONTAINERS_ADDR + CONTAINER_BASE + index * CONTAINER_STRIDE


def vector_address(index: int) -> int:
    return CONTAINERS_ADDR + VECTOR_BASE + index * VECTOR_STRIDE


def pending_address(index: int) -> int:
    return PENDING_ADDR + 0x100 * (index + 1)


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def get_symbol_value(obj_file: Path, symbol: str) -> int:
    data = Path(obj_file).read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    symtab = [section for section in sections if section[1] == 2][0]
    strtab = sections[symtab[6]]
    for index in range(symtab[5] // 16):
        st_name, st_value = struct.unpack_from(
            "<II", data, symtab[4] + index * 16
        )
        name = data[strtab[4] + st_name :].split(b"\x00")[0].decode(
            "ascii", errors="replace"
        )
        if name in (symbol, f"_{symbol}"):
            return st_value
    raise RuntimeError(f"symbol {symbol} not found in {obj_file}")


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00152b0c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_00152b0c not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    func_value = get_symbol_value(obj_file, "engine_func_00152b0c")
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = None
            for address, name in STUB_NAMES.items():
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
        elif rel.relocation_type == 2:  # R_ARM_ABS32 jump table -> .text
            if rel.symbol_name not in ("", ".text"):
                raise RuntimeError(
                    f"unexpected ABS32 relocation against {rel.symbol_name!r}"
                )
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into(
                "<I", code, rel.offset, FUNC_ADDR + (addend - func_value)
            )
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name!r}"
            )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    res = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures


def build_pages(case: dict) -> dict[int, bytes]:
    table_page = bytearray(TABLE_SIZE)
    sync_page = bytearray(SYNC_SIZE)
    action_page = bytearray(ACTION_SIZE)
    pending_page = bytearray(PENDING_SIZE)
    entries_page = bytearray(ENTRIES_SIZE)
    containers_page = bytearray(CONTAINERS_SIZE)

    entries_spec = case.get("entries", [0])
    vectors = case.get("vectors", {0: []})
    count = case.get("count", len(entries_spec))
    state = case.get("state", 2)
    pending = case.get("pending")

    # Entry objects and the entry pointer array.
    for index, container_index in enumerate(entries_spec):
        struct.pack_into("<I", entries_page, index * SLOT_STRIDE, entry_address(index))
        base = ENTRY_BASE + index * ENTRY_STRIDE
        entries_page[base + 0x00] = 0xC0 | index
        entries_page[base + 0x04] = 0x40 | index
        struct.pack_into(
            "<I",
            entries_page,
            base + 0x0C,
            0 if container_index is None else container_address(container_index),
        )
        entries_page[base + 0x10] = 0x51
        entries_page[base + 0x3C] = 0x7E

    # Containers and their pointer vectors.
    for index in range(CONTAINER_COUNT):
        values = vectors.get(index, [])
        vector_offset = VECTOR_BASE + index * VECTOR_STRIDE
        for position, value in enumerate(values):
            if isinstance(value, tuple) and value[0] == "entry":
                word = entry_address(value[1])
            else:
                word = int(value) & 0xFFFFFFFF
            struct.pack_into(
                "<I", containers_page, vector_offset + position * SLOT_STRIDE, word
            )
        base = CONTAINER_BASE + index * CONTAINER_STRIDE
        struct.pack_into("<I", containers_page, base + 0x00, 0xC0DE0000 | index)
        struct.pack_into("<I", containers_page, base + 0x04, 0x0000A000 | index)
        struct.pack_into("<I", containers_page, base + 0x14, 0xC0FFEE00 | index)
        begin = vector_address(index) + case.get("begin_offsets", {}).get(index, 0)
        end = vector_address(index) + case.get("end_offsets", {}).get(
            index, SLOT_STRIDE * len(values)
        )
        struct.pack_into("<I", containers_page, base + 0x18, begin)
        struct.pack_into("<I", containers_page, base + 0x1C, end)
        struct.pack_into("<I", containers_page, base + 0x20, VECTOR_WORDS)
        struct.pack_into("<I", containers_page, base + 0x24, 0x1234ABCD)

    # Pending transition records; record 0/1/2 always exist.
    default_records = {0: (0x1111, 0), 1: (0x2222, 1), 2: (0x3333, 0)}
    records = dict(default_records)
    for index, spec in case.get("pending_records", {}).items():
        records[index] = (spec.get("gate", 0), spec.get("side", 0))
    if pending is not None:
        records[pending["record"]] = (
            pending.get("gate", 0),
            pending.get("side", 0),
        )
    for index, (gate, side) in records.items():
        base = 0x100 * (index + 1)
        struct.pack_into("<I", pending_page, base + 0x00, gate & 0xFFFFFFFF)
        struct.pack_into("<I", pending_page, base + 0x04, 0x55AA0000 | index)
        struct.pack_into("<I", pending_page, base + 0x08, side & 0xFFFFFFFF)
        struct.pack_into("<I", pending_page, base + 0x0C, 0xAA550000 | index)

    # Action record.
    struct.pack_into("<i", action_page, 0x00, 0x0BADF00D)
    struct.pack_into("<I", action_page, 0x04, 0x00000042)
    struct.pack_into("<i", action_page, 0x0C, state)
    struct.pack_into("<I", action_page, 0x10, case.get("word_10", 0xAAAA0000))
    struct.pack_into(
        "<I",
        action_page,
        0x14,
        0 if pending is None else pending_address(pending["record"]),
    )
    struct.pack_into("<I", action_page, 0x18, case.get("saved_18", 0xBBBB0000))
    struct.pack_into("<I", action_page, 0x1C, 0xCCCC0000)
    struct.pack_into("<I", action_page, 0x20, 0xDDDD0000)
    struct.pack_into("<I", action_page, 0x24, ENTRIES_ADDR)
    struct.pack_into("<i", action_page, 0x28, count)
    struct.pack_into("<I", action_page, 0x2C, 0xEEEE0000)

    # Slot tables.  Defaults give a first-container match on slot 0.
    tables = {
        WORK_TABLE: case.get("work", (0x00600010, 0x00600014)),
        REGISTRY_TABLE: case.get("registry", (0x00600020, 0x00600024)),
        TOKEN_TABLE: case.get("token", (0x00600030, 0x00600034)),
        CONTAINER_TABLE: case.get(
            "container_table",
            (container_address(0), container_address(1)),
        ),
    }
    for base, (slot0, slot1) in tables.items():
        struct.pack_into(
            "<II", table_page, base - TABLE_ADDR, slot0 & 0xFFFFFFFF,
            slot1 & 0xFFFFFFFF
        )

    # Frame-sync slots.
    counts = case.get("sync_counts", (5, 6))
    registered = case.get("registered", (1, 1))
    inited = case.get("inited", (1, 1))
    for slot in (0, 1):
        offset = (FRAME_SYNC - SYNC_ADDR) + slot * FRAME_SYNC_STRIDE
        struct.pack_into("<i", sync_page, offset + 0x00, counts[slot])
        sync_page[offset + 0x04] = registered[slot] & 0xFF
        sync_page[offset + 0x05] = inited[slot] & 0xFF
        sync_page[offset + 0x08] = 0x30 | slot
        sync_page[offset + 0x14] = 0x40 | slot

    return {
        TABLE_ADDR: bytes(table_page),
        SYNC_ADDR: bytes(sync_page),
        ACTION_ADDR: bytes(action_page),
        PENDING_ADDR: bytes(pending_page),
        ENTRIES_ADDR: bytes(entries_page),
        CONTAINERS_ADDR: bytes(containers_page),
    }


class Runner:
    """One Unicorn machine with deterministic stubs at the pinned targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
        self.uc.mem_map(SYNC_ADDR, SYNC_SIZE)
        self.uc.mem_map(ACTION_ADDR, ACTION_SIZE)
        self.uc.mem_map(PENDING_ADDR, PENDING_SIZE)
        self.uc.mem_map(ENTRIES_ADDR, ENTRIES_SIZE)
        self.uc.mem_map(CONTAINERS_ADDR, CONTAINERS_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.write_bytes: dict[int, int] = {}
        self.retire_calls = 0
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
            return
        masked = value & ((1 << (8 * size)) - 1)
        for byte in range(size):
            self.write_bytes[address + byte] = (masked >> (8 * byte)) & 0xFF

    def _apply(self, writes) -> None:
        if not writes:
            return
        for address, value, size in writes:
            raw = int(value).to_bytes(size, "little", signed=value < 0)
            self.uc.mem_write(address, raw)

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)

        if address == STUB_2A3068:
            self.call_log.append(("battle_func_002a3068", r0))
            block = FRAME_SYNC + r0 * FRAME_SYNC_STRIDE
            uc.mem_write(block + 0x04, b"\x01\x00")
            uc.reg_write(arm.UC_ARM_REG_R0, block)
        elif address == STUB_2C028C:
            self.call_log.append(("engine_func_002c028c", r0, r1))
            self._apply(self.case.get("after_detach"))
        elif address == STUB_2ABDB0:
            self.call_log.append(("engine_func_002abdb0", r0, r1))
            index = self.retire_calls
            self.retire_calls += 1
            if index == self.case.get("retire_mutation_call", -1):
                self._apply(self.case.get("after_retire"))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x002ABDB0)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.write_bytes = {}
        self.retire_calls = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        for address, page in build_pages(case).items():
            self.uc.mem_write(address, page)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.write_bytes = {}

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, ACTION_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_R12, SCRATCH_12_START)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        faulted = False
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError:
            faulted = True

        result = {
            "faulted": faulted,
            "writes": sorted(self.write_bytes.items()),
            "call_log": list(self.call_log),
            "pages": {
                "tables": bytes(self.uc.mem_read(TABLE_ADDR, TABLE_SIZE)),
                "frame_sync": bytes(self.uc.mem_read(SYNC_ADDR, SYNC_SIZE)),
                "action": bytes(self.uc.mem_read(ACTION_ADDR, ACTION_SIZE)),
                "pending": bytes(self.uc.mem_read(PENDING_ADDR, PENDING_SIZE)),
                "entries": bytes(self.uc.mem_read(ENTRIES_ADDR, ENTRIES_SIZE)),
                "containers": bytes(self.uc.mem_read(CONTAINERS_ADDR, CONTAINERS_SIZE)),
            },
        }
        if not faulted:
            result["ret"] = self.uc.reg_read(arm.UC_ARM_REG_R0)
            result["pc"] = self.uc.reg_read(arm.UC_ARM_REG_PC)
            result["sp"] = self.uc.reg_read(arm.UC_ARM_REG_SP)
            result["callee_saved"] = {
                name: self.uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            }
        return result


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    if orig["faulted"] != cand["faulted"]:
        problems.append(f"fault: orig={orig['faulted']} cand={cand['faulted']}")
    if orig["faulted"]:
        # Both machines fault; the faulting PC necessarily differs between two
        # different code layouts, so only the effects before the fault are
        # compared.
        for key in ("writes",):
            if orig[key] != cand[key]:
                problems.append(f"{key} differ before the fault")
        for name, value in orig["pages"].items():
            if value != cand["pages"][name]:
                problems.append(f"page {name} differs before the fault")
        return problems

    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"]) + "\n    cand="
            + repr(cand["call_log"])
        )
    if orig["writes"] != cand["writes"]:
        left = dict(orig["writes"])
        right = dict(cand["writes"])
        only_orig = sorted(set(left) - set(right))
        only_cand = sorted(set(right) - set(left))
        differing = sorted(
            address
            for address in set(left) & set(right)
            if left[address] != right[address]
        )
        problems.append(
            "writes differ: only_orig="
            f"{[(hex(a), hex(left[a])) for a in only_orig[:8]]} "
            f"only_cand={[(hex(a), hex(right[a])) for a in only_cand[:8]]} "
            f"differing={[(hex(a), hex(left[a]), hex(right[a])) for a in differing[:8]]}"
        )
    for name, value in orig["pages"].items():
        if value != cand["pages"][name]:
            first = next(
                index
                for index, (a, b) in enumerate(zip(value, cand["pages"][name]))
                if a != b
            )
            problems.append(
                f"page {name} differs at +0x{first:x}: "
                f"orig={value[first]:02x} cand={cand['pages'][name][first]:02x}"
            )
    return problems


# ------------------------------------------------------------------------ cases


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "state": 2,
        "pending": None,
        "entries": [0],
        "vectors": {0: []},
        "sync_counts": (5, 6),
        "registered": (1, 1),
        "inited": (1, 1),
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- state dispatch and early exits -----------------------------------
    for state in (0, 3, 6, -1, -0x80000000, 0x7FFFFFFF):
        cases.append(base_case(f"state {state} returns before any access", state=state))
    cases.append(
        base_case("state 1, zero token gate", state=1, token=(0, 0x00600034))
    )
    cases.append(
        base_case("state 1, non-zero token gate", state=1,
                  token=(0x0BADF00D, 0x00600034))
    )
    cases.append(
        base_case("state 1, token gate 0xFFFFFFFF", state=1,
                  token=(0xFFFFFFFF, 0x00600034))
    )
    cases.append(
        base_case("state 2, zero container gate",
                  container_table=(0, container_address(1)))
    )
    cases.append(base_case("state 2 baseline", state=2))
    cases.append(
        base_case("state 4, zero token gate", state=4, token=(0x00600030, 0))
    )
    cases.append(
        base_case("state 4, token gate non-zero", state=4,
                  token=(0x00600030, 0x99))
    )
    cases.append(
        base_case("state 5, zero container gate", state=5,
                  container_table=(container_address(0), 0))
    )
    cases.append(base_case("state 5, container gate non-zero", state=5))

    # --- pending record paths ---------------------------------------------
    cases.append(
        base_case("pending gate zero", state=0,
                  pending={"record": 0, "gate": 0, "side": 0})
    )
    cases.append(
        base_case("pending gate non-zero side 0", state=0,
                  pending={"record": 0, "gate": 0x11, "side": 0})
    )
    cases.append(
        base_case("pending gate non-zero side 1", state=0,
                  pending={"record": 1, "gate": 0x22, "side": 1})
    )
    cases.append(
        base_case("pending side 2 treated as non-zero", state=2,
                  pending={"record": 2, "gate": 0x33, "side": 2})
    )

    # --- slot determination -----------------------------------------------
    cases.append(
        base_case("entry container matches slot 1",
                  container_table=(0x00555555, container_address(0)))
    )
    cases.append(
        base_case("no container match", container_table=(0x00555555, 0x00666666))
    )
    cases.append(base_case("entry 0 container null", entries=[None]))
    cases.append(
        base_case("entry 0 container null with null table entry",
                  entries=[None], container_table=(0, container_address(1)),
                  expect_fault=True)
    )

    # --- removal loop ------------------------------------------------------
    cases.append(
        base_case("count 0 skips loop", count=0, vectors={0: [("entry", 0)]})
    )
    cases.append(
        base_case("count -1 skips loop", count=-1, vectors={0: [("entry", 0)]})
    )
    cases.append(
        base_case("count INT_MIN skips loop", count=-0x80000000,
                  vectors={0: [("entry", 0)]})
    )
    cases.append(
        base_case("entry found in the middle",
                  vectors={0: [0xA, ("entry", 0), 0xB]})
    )
    cases.append(
        base_case("entry found last", vectors={0: [0xA, ("entry", 0)]})
    )
    cases.append(base_case("entry only element", vectors={0: [("entry", 0)]}))
    cases.append(base_case("entry absent", vectors={0: [0xA, 0xB, 0xC]}))
    cases.append(
        base_case("duplicates after the match",
                  vectors={0: [("entry", 0), ("entry", 0), 0xC, ("entry", 0)]})
    )
    cases.append(
        base_case("vector all equal", vectors={0: [("entry", 0)] * 4})
    )
    cases.append(
        base_case("two entries in one container", entries=[0, 0], count=2,
                  vectors={0: [("entry", 0), 0xD, ("entry", 1), 0xE]})
    )
    cases.append(
        base_case("second entry has null container", entries=[0, None], count=2,
                  vectors={0: [("entry", 0)]})
    )
    cases.append(
        base_case("three entries three containers", entries=[0, 1, 2], count=3,
                  vectors={0: [("entry", 0)], 1: [("entry", 1), 0xF],
                           2: []})
    )
    cases.append(
        base_case("three entries but count 2", entries=[0, 1, 2], count=2,
                  vectors={0: [("entry", 0)], 1: [("entry", 1)], 2: [0x77]})
    )
    cases.append(
        base_case("count 5 over 2 entries", entries=[0, 1], count=2,
                  vectors={0: [0x1], 1: [0x2]})
    )
    cases.append(
        base_case("begin equals end but vector storage non-empty",
                  begin_offsets={0: 0x10}, end_offsets={0: 0x10},
                  vectors={0: [0xAB]})
    )

    # --- unregister block and reloads -------------------------------------
    cases.append(
        base_case("owner vector non-empty skips unregister",
                  vectors={0: [0xBEEF]})
    )
    cases.append(
        base_case("detach mutates both tables",
                  after_detach=[
                      (REGISTRY_TABLE, 0x00DEAD00, 4),
                      (WORK_TABLE, 0x00DEAD04, 4),
                  ])
    )
    cases.append(
        base_case("detach mutates only the registry table",
                  after_detach=[(REGISTRY_TABLE + SLOT_STRIDE, 0x00BEEF00, 4)],
                  pending={"record": 1, "gate": 1, "side": 1},
                  container_table=(0x00555555, container_address(0)))
    )

    # --- sync slot selection and counters ---------------------------------
    cases.append(
        base_case("inner retire mutates pending to side 1",
                  retire_mutation_call=0,
                  after_retire=[
                      (ACTION_ADDR + 0x14, pending_address(1), 4),
                  ])
    )
    cases.append(
        base_case("inner retire mutates state to 3",
                  retire_mutation_call=0,
                  after_retire=[(ACTION_ADDR + 0x0C, 3, 4)])
    )
    cases.append(
        base_case("inner retire mutates state to 2",
                  retire_mutation_call=0,
                  after_retire=[(ACTION_ADDR + 0x0C, 2, 4)])
    )
    cases.append(
        base_case("sync retire mutates state to 3",
                  vectors={0: [0xBEEF]}, retire_mutation_call=0,
                  after_retire=[(ACTION_ADDR + 0x0C, 3, 4)])
    )
    cases.append(
        base_case("sync retire mutates state to INT_MIN",
                  vectors={0: [0xBEEF]}, retire_mutation_call=0,
                  after_retire=[(ACTION_ADDR + 0x0C, -0x80000000, 4)])
    )
    cases.append(
        base_case("sync retire mutates pending from null",
                  state=2, retire_mutation_call=0,
                  after_retire=[(ACTION_ADDR + 0x14, pending_address(2), 4)])
    )
    cases.append(
        base_case("sync retire clears pending",
                  pending={"record": 0, "gate": 1, "side": 1},
                  retire_mutation_call=0,
                  after_retire=[(ACTION_ADDR + 0x14, 0, 4)])
    )
    cases.append(
        base_case("counter wrap slot 0", sync_counts=(0, 6))
    )
    cases.append(
        base_case("counter INT_MIN slot 0", sync_counts=(-0x80000000, 6))
    )
    cases.append(
        base_case("counter 0 slot 1", state=5, sync_counts=(5, 0))
    )
    cases.append(
        base_case("counter 0x80000000 slot 1", state=4,
                  sync_counts=(5, -0x80000000))
    )
    cases.append(
        base_case("gate bytes start zero", registered=(0, 0), inited=(0, 0))
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
        print(
            f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls, "
            f"{len(orig['writes'])} bytes written)"
        )
    return passed


MUTANTS = (
    ("container_table_address",
     "constexpr u32 kContainerTableAddress = 0x00464B94;  // slot containers",
     "constexpr u32 kContainerTableAddress = 0x00464B98;  // slot containers"),
    ("state4_token_offset",
     "gate = load_word(kTokenTableAddress + kSlotStride);",
     "gate = load_word(kTokenTableAddress);"),
    ("sync_slot_state_bound",
     "sync_slot = action->state_0C >= kStateSlot1Min ? 1 : 0;",
     "sync_slot = action->state_0C > kStateSlot1Min ? 1 : 0;"),
    ("sync_slot_selection",
     "FrameSyncSlot* const sync = frame_sync_slot(sync_slot);",
     "FrameSyncSlot* const sync = frame_sync_slot(0);"),
    ("end_moved_clear",
     "if (previous_end != new_end) {",
     "if (previous_end == new_end) {"),
    ("saved_pending",
     "action->saved_18 = final_pending;",
     "action->saved_18 = nullptr;"),
)


def main() -> None:
    print("Testing engine_func_00152b0c (0x00152b0c)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in MUTANTS:
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
