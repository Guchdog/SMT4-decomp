#!/usr/bin/env python3
"""Differential test for func_00150654 (0x00150654) using Unicorn ARM emulation.

Compiles ``src/engine/leaf_batch41_c.cpp``, extracts the ``func_00150654`` body,
resolves every relocation to a deterministic stub (or to the candidate's local
``LoadUntabled`` helper) and runs the pinned original (``extracted/exefs/code.bin``)
against the candidate on separate Unicorn ARM machines with identical fixtures.

Compared observables per case:
  * return r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log with every register argument plus the architected
    stack words of each helper (none of these helpers receives stack arguments:
    the original's prologue only spills callee-saved registers and the largest
    argument list is four registers);
  * the complete observable memory: the whole 1 MiB data window (scene,
    context, render state, unit, draw group, entry slots, draw entries, item
    tables, items, type-info chain nodes, command buffer and the
    ``g_GpuCommandCursor`` global) plus the low 4 KiB page that the
    zero-relative-offset fallbacks read;
  * any write outside the private stack.

The VFP copy helpers 0x002A1B98 / 0x002A1AC8 are stubbed in Python with their
exact word permutations, because this Unicorn build cannot execute VFP.

Coverage: null draw group, empty and overflowing slot counts, both matrix
emitters, every type-info chain shape (immediate match, multi-link match, null
head, null after one link, chain continuing through address 0), a null unit, an
already bound context, zero relative offsets on all three tables, item indexes
0..3, helpers that advance the cursor global, a 0x00153A58 callee that rewrites
the entry slot, and randomised fixtures from two registered seeds.  Four
directed mutants (position tag, type identity, group table offset,
render-state mask) must each be detected.
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
OUT_DIR = ROOT / "build/test_leaf_00150654"

FUNC_ADDR = 0x00150654
FUNC_SIZE = 440

# ---------------------------------------------------------------------------
# Emulated address space
# ---------------------------------------------------------------------------
CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000          # 0x150654 plus the helper stubs at 0x15/0x2a
LOW_ADDR = 0x00000000
LOW_SIZE = 0x00001000           # zero-relative-offset fallbacks
DATA_ADDR = 0x00400000
DATA_SIZE = 0x00100000          # fixtures, command buffer, cursor global
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Direct-call stub targets (the original branch destinations).
STUB_2A1B98 = 0x002A1B98
STUB_2A1AC8 = 0x002A1AC8
STUB_153A58 = 0x00153A58
STUB_153D64 = 0x00153D64
STUB_153E50 = 0x00153E50
STUB_153C74 = 0x00153C74
# Candidate-local noinline load helper.
STUB_LOAD_UNTABLED = 0x00150E00
# Target of the unit vtable slot at +0x08.
STUB_TYPE_QUERY = 0x0015F000

STUB_NAMES = {
    STUB_2A1B98: "func_002a1b98",
    STUB_2A1AC8: "func_002a1ac8",
    STUB_153A58: "func_00153a58",
    STUB_153D64: "engine_func_00153d64",
    STUB_153E50: "engine_func_00153e50",
    STUB_153C74: "ui_func_00153c74",
    STUB_TYPE_QUERY: "type_query",
}

# Every helper is called with r0-r3 only.
STACK_ARGS = {address: 0 for address in STUB_NAMES}

# Fixture objects (inside the data window).
SCENE = 0x00430000
CONTEXT = 0x00430100
RENDER_STATE = 0x00430200
UNIT = 0x00430300
VTABLE = 0x00430400
GROUP = 0x00430500
ENTRY_TABLE = 0x00430600
ENTRIES = (0x00430700, 0x00430800, 0x00430900)
ITEM_TABLES = (0x00430A00, 0x00430B00, 0x00430C00)
ITEMS = (0x00430D00, 0x00430E00, 0x00430F00)
CHAIN_NODES = (0x00431000, 0x00431010, 0x00431020)
CMD_BUFFER = 0x00450000
CMD_BUFFER_SIZE = 0x2000
CURSOR_GLOBAL = 0x004652A0

COMPONENT_TYPE_INFO = 0x00472288
MAX_ENTRIES = 3
ITEM_SLOTS = 4

BX_LR = 0xE12FFF1E

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


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def sign_extend_24(value: int) -> int:
    return value - 0x1000000 if value & 0x800000 else value


def _relocate(object_file: Path) -> tuple[bytes, dict[int, bytes]]:
    funcs = extract_elf_functions_detailed(object_file)
    if "func_00150654" not in funcs:
        raise RuntimeError(
            f"func_00150654 not found in {object_file}: {sorted(funcs)}")
    raw, relocs = funcs["func_00150654"]
    code = bytearray(raw)

    helper_name = None
    helper_code = None
    for symbol, (helper_raw, helper_relocs) in funcs.items():
        if "LoadUntabled" in symbol:
            if helper_relocs:
                raise RuntimeError(
                    f"helper relocations unsupported: {helper_relocs}")
            helper_name, helper_code = symbol, bytes(helper_raw)
            break
    if helper_name is None:
        raise RuntimeError(f"LoadUntabled helper not found in {object_file}")

    targets = {
        "func_002a1b98": STUB_2A1B98,
        "func_002a1ac8": STUB_2A1AC8,
        "func_00153a58": STUB_153A58,
        "engine_func_00153d64": STUB_153D64,
        "engine_func_00153e50": STUB_153E50,
        "ui_func_00153c74": STUB_153C74,
        helper_name: STUB_LOAD_UNTABLED,
    }

    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):  # PC24 / CALL / JUMP24
            if rel.symbol_name not in targets:
                raise RuntimeError(f"unexpected call relocation: {rel}")
            target = targets[rel.symbol_name]
            instruction = struct.unpack_from("<I", code, rel.offset)[0]
            # REL relocation: the addend is encoded in the instruction itself.
            addend = sign_extend_24(instruction & 0x00FFFFFF) << 2
            place = FUNC_ADDR + rel.offset
            displacement = (target + addend - place) >> 2
            if ((place + 8 + (displacement << 2)) & 0xFFFFFFFF) != target:
                raise RuntimeError(f"bad call patch for {rel.symbol_name}")
            struct.pack_into(
                "<I", code, rel.offset,
                (instruction & 0xFF000000) | (displacement & 0x00FFFFFF))
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            if rel.symbol_name != "g_GpuCommandCursor":
                raise RuntimeError(f"unexpected abs32 relocation: {rel}")
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if addend != 0:
                raise RuntimeError(f"unexpected cursor global addend {addend}")
            struct.pack_into("<I", code, rel.offset, CURSOR_GLOBAL)
        else:
            raise RuntimeError(f"unsupported relocation: {rel}")

    return bytes(code), {STUB_LOAD_UNTABLED: helper_code}


def compile_candidate() -> tuple[bytes, dict[int, bytes]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    object_file = OUT_DIR / "leaf_batch41_c.o"
    result = compile_tu_armv6k(SOURCE, object_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return _relocate(object_file)


def compile_mutant(name: str, old: str, new: str) -> tuple[bytes, dict[int, bytes]]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(
            f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    object_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, object_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return _relocate(object_file)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def write_u32(uc, address: int, value: int) -> None:
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


def read_u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


def build_low_page(case: dict) -> bytes:
    page = bytearray(LOW_SIZE)
    for offset in range(0, LOW_SIZE, 4):
        struct.pack_into("<I", page, offset, 0x10000000 + offset)
    low = case["low_words"]
    struct.pack_into("<I", page, 0x00, low.get(0x00, 0))
    struct.pack_into("<I", page, 0x04, low.get(0x04, 0))
    struct.pack_into("<I", page, 0x08, low.get(0x08, 0x0BAD0008))
    struct.pack_into("<I", page, 0x0C, low.get(0x0C, 0x0BAD000C))
    struct.pack_into("<I", page, 0x10, low.get(0x10, 0))
    return bytes(page)


class Machine:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(LOW_ADDR, LOW_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", BX_LR))
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.submit_index = 0

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address])))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _maybe_bump_cursor(self) -> None:
        if self.case["bump_on_copy"]:
            write_u32(self.uc, CURSOR_GLOBAL,
                      (read_u32(self.uc, CURSOR_GLOBAL) + 8) & 0xFFFFFFFF)

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2A1B98:
            self._log(address, r0, r1)
            words = struct.unpack("<3I", uc.mem_read(r1, 12))
            uc.mem_write(r0, struct.pack("<4I", 0, words[2], words[1], words[0]))
            self._maybe_bump_cursor()
        elif address == STUB_2A1AC8:
            self._log(address, r0, r1, r2)
            words = struct.unpack("<12I", uc.mem_read(r1, 48))
            out = [0] * 13
            out[1] = r2
            out[0] = words[3]
            out[2], out[3], out[4] = words[2], words[1], words[0]
            out[5], out[6], out[7], out[8] = words[7], words[6], words[5], words[4]
            out[9], out[10], out[11], out[12] = (
                words[11], words[10], words[9], words[8])
            uc.mem_write(r0, struct.pack("<13I", *out))
            self._maybe_bump_cursor()
        elif address == STUB_153A58:
            self._log(address, r0, r1, r2, r3)
            if self.case["slot_rewrite"] is not None:
                slot, value = self.case["slot_rewrite"]
                write_u32(uc, slot, value)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x153A5800)
        elif address == STUB_153D64:
            self._log(address, r0, r1)
            # The original binds the unit into [context+0x1C].
            write_u32(uc, r0 + 0x1C, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x153D6400)
        elif address == STUB_153E50:
            self._log(address, r0, r1)
            write_u32(uc, r0 + 0x1C, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x153E5000)
        elif address == STUB_153C74:
            self._log(address, r0, r1)
            self.submit_index += 1
            uc.reg_write(arm.UC_ARM_REG_R0, 0x153C7400 | self.submit_index)
        elif address == STUB_TYPE_QUERY:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["chain_head"])
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, blobs: dict, case: dict) -> dict:
        uc = self.uc
        self.call_log = []
        self.writes = []
        self.submit_index = 0
        self.case = case

        # Wipe every mutable region so cases never leak into each other.
        uc.mem_write(DATA_ADDR, b"\x00" * DATA_SIZE)
        uc.mem_write(LOW_ADDR, build_low_page(case))
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        uc.mem_write(FUNC_ADDR, code)
        for address, blob in blobs.items():
            uc.mem_write(address, blob)
        # Unicorn 2.1.4 keeps translated blocks across mem_write.
        uc.ctl_flush_tb()

        # Command-buffer sentinel: any byte the case leaves unwritten stays 0xCC.
        uc.mem_write(CMD_BUFFER, b"\xCC" * CMD_BUFFER_SIZE)

        # Scene -> context -> render state.
        write_u32(uc, SCENE + 0x08, CONTEXT)
        write_u32(uc, CONTEXT + 0x08, RENDER_STATE)
        write_u32(uc, CONTEXT + 0x1C,
                  (UNIT if case["unit"] else 0) if case["context_bound"]
                  else 0x0043FFFF)
        write_u32(uc, RENDER_STATE + 0x14, case["state"])

        # Unit -> vtable (+0x00) and the 3x4 matrix source (+0x8C).
        write_u32(uc, UNIT + 0x00, VTABLE)
        write_u32(uc, VTABLE + 0x08, STUB_TYPE_QUERY)
        for index in range(12):
            write_u32(uc, UNIT + 0x8C + index * 4,
                      0x0A000000 | (case["matrix_seed"] + index))

        # Type-info chain nodes.
        for address, value in case["chain_links"].items():
            write_u32(uc, address, value)

        # Draw-group record: three position words, slot count, relative table.
        for index in range(3):
            write_u32(uc, GROUP + 0x20 + index * 4,
                      0x0B000000 | (case["position_seed"] + index))
        write_u32(uc, GROUP + 0x2C, case["count"])
        write_u32(uc, GROUP + 0x30,
                  0 if case["zero_table_offset"] else ENTRY_TABLE - (GROUP + 0x30))

        # Entry slots and the per-entry draw entries / item tables.
        for index in range(MAX_ENTRIES):
            slot = ENTRY_TABLE + index * 4
            entry = ENTRIES[index]
            if case["zero_entry_offset"] and index == 0:
                write_u32(uc, slot, 0)
            else:
                write_u32(uc, slot, entry - slot)

            write_u32(uc, entry + 0x00, case["matrix_counts"][index])
            write_u32(uc, entry + 0x04, 0x40 + index * 4)
            write_u32(uc, entry + 0x08, 0x0100 + index)

            item_table = ITEM_TABLES[index]
            if case["zero_item_table_offset"] and index == 0:
                write_u32(uc, entry + 0x10, 0)
            else:
                write_u32(uc, entry + 0x10, item_table - (entry + 0x10))
            for item_index in range(ITEM_SLOTS):
                item_slot = item_table + item_index * 4
                if item_index != case["item_index"]:
                    write_u32(uc, item_slot, 0x77770000 + item_index)
                elif case["zero_item_offset"]:
                    write_u32(uc, item_slot, 0)
                else:
                    write_u32(uc, item_slot, ITEMS[index] - item_slot)

        write_u32(uc, CURSOR_GLOBAL,
                  (CMD_BUFFER + case["cursor_offset"]) & 0xFFFFFFFF)

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, SCENE)
        uc.reg_write(arm.UC_ARM_REG_R1, UNIT if case["unit"] else 0)
        uc.reg_write(arm.UC_ARM_REG_R2, 0 if case["null_group"] else GROUP)
        uc.reg_write(arm.UC_ARM_REG_R3, case["item_index"])
        for name, register in CALLEE_SAVED.items():
            uc.reg_write(register, CALLEE_SAVED_START[name])

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            inside_data = DATA_ADDR <= address < DATA_ADDR + DATA_SIZE
            inside_low = LOW_ADDR <= address < LOW_ADDR + LOW_SIZE
            inside_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not (inside_data or inside_low or inside_stack):
                unexpected_writes.append((address, size))

        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "data": bytes(uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "low": bytes(uc.mem_read(LOW_ADDR, LOW_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "count": 2,
        "matrix_counts": [1, 0, 3],
        "item_index": 0,
        "unit": True,
        "null_group": False,
        "context_bound": False,
        "state": 0xFFFFFFFF,
        "cursor_offset": 0,
        "chain_head": COMPONENT_TYPE_INFO,
        "chain_links": {},
        "zero_table_offset": False,
        "zero_entry_offset": False,
        "zero_item_table_offset": False,
        "zero_item_offset": False,
        "low_words": {},
        "bump_on_copy": False,
        "slot_rewrite": None,
        "matrix_seed": 0x100,
        "position_seed": 0x200,
    }
    case.update(overrides)
    return case


def make_cases() -> list:
    cases = []

    # --- both emitters, empty and overflowing tables
    cases.append(base_case("positive: one skinned entry and one single matrix"))
    cases.append(base_case("positive: all entries skinned",
                           matrix_counts=[2, 3, 1]))
    cases.append(base_case("positive: no component, all single matrix",
                           chain_head=0, matrix_counts=[1, 2, 3]))
    cases.append(base_case("boundary: empty slot table", count=0))
    cases.append(base_case("boundary: single entry, nonzero cursor",
                           count=1, matrix_counts=[1, 0, 0],
                           cursor_offset=0x400))
    cases.append(base_case("boundary: slot count 3 with mixed matrix counts",
                           count=3, matrix_counts=[0, 1, 0]))
    cases.append(base_case("boundary: 0x40000000 slots wrap to an empty table",
                           count=0x40000000))
    cases.append(base_case("boundary: 0x80000000 slots wrap to an empty table",
                           count=0x80000000))

    # --- argument guard
    cases.append(base_case("negative control: null draw group", null_group=True))

    # --- type-info chain shapes
    cases.append(base_case("chain: immediate match (no chain read)"))
    cases.append(base_case("chain: match after one link",
                           chain_head=CHAIN_NODES[0],
                           chain_links={CHAIN_NODES[0]: COMPONENT_TYPE_INFO}))
    cases.append(base_case("chain: match after two links",
                           chain_head=CHAIN_NODES[0],
                           chain_links={CHAIN_NODES[0]: CHAIN_NODES[1],
                                        CHAIN_NODES[1]: COMPONENT_TYPE_INFO}))
    cases.append(base_case("chain: null after one link",
                           chain_head=CHAIN_NODES[0],
                           chain_links={CHAIN_NODES[0]: 0}))
    cases.append(base_case("chain: null head reads address 0", chain_head=0))
    cases.append(base_case("chain: null head continues through address 0",
                           chain_head=0,
                           chain_links={CHAIN_NODES[0]: COMPONENT_TYPE_INFO},
                           low_words={0x00: CHAIN_NODES[0]}))
    cases.append(base_case("chain: unknown type identity is never matched",
                           chain_head=CHAIN_NODES[2],
                           chain_links={CHAIN_NODES[2]: CHAIN_NODES[1],
                                        CHAIN_NODES[1]: 0x00472289}))

    # --- unit / context binding
    cases.append(base_case("unit: null unit skips the vtable call",
                           unit=False, matrix_counts=[1, 0, 0]))
    cases.append(base_case("unit: already bound context skips the bind call",
                           context_bound=True))
    cases.append(base_case("unit: already bound context with a null unit",
                           context_bound=True, unit=False))

    # --- zero relative offsets (latent low reads)
    cases.append(base_case("null-offset: zero group table offset",
                           zero_table_offset=True,
                           low_words={0x00: 0, 0x04: 0, 0x10: 0}))
    cases.append(base_case("null-offset: zero entry slot offset",
                           zero_entry_offset=True, count=1,
                           low_words={0x00: 0, 0x10: 0}))
    cases.append(base_case("null-offset: zero entry slot with a count word",
                           zero_entry_offset=True, count=1,
                           low_words={0x00: 2, 0x10: 0}))
    cases.append(base_case("null-offset: zero item table offset",
                           zero_item_table_offset=True, count=1))
    cases.append(base_case("null-offset: zero item slot offset",
                           zero_item_offset=True, count=1))

    # --- item indexes, cursor and ordering behaviour
    for index in range(ITEM_SLOTS):
        cases.append(base_case(f"item index {index}", item_index=index))
    cases.append(base_case("item index 3 with three entries",
                           item_index=3, count=3))
    cases.append(base_case("ordering: copy helpers advance the cursor global",
                           bump_on_copy=True))
    cases.append(base_case("ordering: cursor bump with a single-matrix entry",
                           bump_on_copy=True, count=1, matrix_counts=[0, 0, 0]))
    cases.append(base_case("ordering: 0x00153a58 rewrites the entry slot",
                           slot_rewrite=(ENTRY_TABLE,
                                         ENTRIES[1] - ENTRY_TABLE)))
    cases.append(base_case("ordering: rewritten slot points at a zero entry",
                           slot_rewrite=(ENTRY_TABLE, 0), count=1,
                           low_words={0x00: 0, 0x10: 0}))

    # --- render-state word preservation
    for state in (0x00000000, 0x00000006, 0xA5A5A5A5, 0xFFFFFFF9):
        cases.append(base_case(
            f"state word 0x{state:08x}", state=state, count=1,
            matrix_counts=[0, 0, 0]))

    # --- randomised fixtures from two registered seeds
    for seed in (20261113, 20261114):
        generator = random.Random(seed)
        for index in range(6):
            count = generator.randint(1, MAX_ENTRIES)
            matrix_counts = [generator.randint(0, 3)
                             for _ in range(MAX_ENTRIES)]
            unit = generator.random() < 0.8
            shape = generator.choice(
                ["match", "one_link", "two_links", "null", "null_head"])
            chain_head = COMPONENT_TYPE_INFO
            links = {}
            if shape == "one_link":
                chain_head = CHAIN_NODES[0]
                links[CHAIN_NODES[0]] = COMPONENT_TYPE_INFO
            elif shape == "two_links":
                chain_head = CHAIN_NODES[0]
                links[CHAIN_NODES[0]] = CHAIN_NODES[1]
                links[CHAIN_NODES[1]] = COMPONENT_TYPE_INFO
            elif shape == "null":
                chain_head = CHAIN_NODES[0]
                links[CHAIN_NODES[0]] = 0
            elif shape == "null_head":
                chain_head = 0
            cases.append(base_case(
                f"random seed {seed} case {index} "
                f"(count={count}, chain={shape}, unit={unit})",
                count=count,
                matrix_counts=matrix_counts,
                unit=unit,
                context_bound=generator.random() < 0.5,
                state=generator.getrandbits(32),
                cursor_offset=generator.randrange(0, 0x800, 4),
                item_index=generator.randrange(ITEM_SLOTS),
                chain_head=chain_head,
                chain_links=links,
                bump_on_copy=generator.random() < 0.25,
            ))
    return cases


# ---------------------------------------------------------------------------
# Independent expectations derived from the ARM contract
# ---------------------------------------------------------------------------
def read_data_u32(data: bytes, address: int) -> int:
    return struct.unpack_from("<I", data, address - DATA_ADDR)[0]


def resolve_chain(case: dict) -> bool:
    """AsdTypeMatch(unit, 0x00472288): true when the unit survives."""
    if not case["unit"]:
        return False
    current = case["chain_head"]
    for _ in range(8):
        if current == COMPONENT_TYPE_INFO:
            return True
        if current == 0:
            current = case["low_words"].get(0x00, 0)
        else:
            current = case["chain_links"].get(current, 0)
        if current == 0:
            return False
    return False


def check_expectations(case: dict, result: dict) -> None:
    name = case["name"]
    words = struct.unpack_from(
        f"<{CMD_BUFFER_SIZE // 4}I", result["data"], CMD_BUFFER - DATA_ADDR)
    initial_cursor = (CMD_BUFFER + case["cursor_offset"]) & 0xFFFFFFFF
    bump = 8 if case["bump_on_copy"] else 0

    if case["null_group"]:
        assert result["ret"] == SCENE, f"null-group return on {name}"
        assert read_data_u32(result["data"], CURSOR_GLOBAL) == initial_cursor, (
            f"null-group cursor changed on {name}")
        return

    # Position record at the initial cursor.
    base = (initial_cursor - CMD_BUFFER) // 4
    seed = case["position_seed"]
    assert words[base + 0] == 0x80000006, f"position tag on {name}"
    assert words[base + 1] == 0x804F02C0, f"position marker on {name}"
    assert words[base + 2] == 0, f"position word 0 on {name}"
    assert words[base + 3] == (0x0B000000 | (seed + 2)), f"position z on {name}"
    assert words[base + 4] == (0x0B000000 | (seed + 1)), f"position y on {name}"
    assert words[base + 5] == (0x0B000000 | seed), f"position x on {name}"
    cursor = (initial_cursor + bump + 0x18) & 0xFFFFFFFF

    matched = resolve_chain(case)

    # Context binding happens before the loop.
    binds = [entry for entry in result["call_log"]
             if entry[0] in ("engine_func_00153d64", "engine_func_00153e50")]
    if case["context_bound"]:
        assert binds == [], f"unexpected bind on {name}: {binds}"
    else:
        expected_bind = ("engine_func_00153e50" if matched
                         else "engine_func_00153d64")
        assert [entry[0] for entry in binds] == [expected_bind], (
            f"bind helper on {name}: {binds}")
        assert binds[0][1][0] == CONTEXT, f"bind context on {name}"
        assert binds[0][1][1] == (UNIT if case["unit"] else 0), (
            f"bind argument on {name}")

    # An empty table (count == 0 or a wrapping count) skips the loop entirely.
    if case["count"] == 0 or ((case["count"] << 2) & 0xFFFFFFFF) == 0:
        assert result["ret"] == case["count"], f"empty-table return on {name}"
        assert read_data_u32(result["data"], CURSOR_GLOBAL) == cursor, (
            f"empty-table cursor on {name}")
        assert not [entry for entry in result["call_log"]
                    if entry[0] in ("func_00153a58", "ui_func_00153c74")], (
            f"unexpected loop calls on {name}")
        return

    side_effects = (case["bump_on_copy"] or case["slot_rewrite"] is not None
                    or case["zero_table_offset"] or case["zero_entry_offset"])
    if not side_effects:
        if case["unit"]:
            source = [0x0A000000 | (case["matrix_seed"] + k)
                      for k in range(12)]
        else:
            # A null unit makes unit+0x8C resolve into the low page.
            source = [0x10000000 + 0x8C + k * 4 for k in range(12)]
        for index in range(case["count"]):
            skinned = matched and case["matrix_counts"][index] != 0
            if skinned:
                continue
            base = (cursor - CMD_BUFFER) // 4
            assert words[base + 0] == 0x80000019, f"matrix tag on {name}"
            assert words[base + 1] == 0x000F02C0, f"matrix marker on {name}"
            assert words[base + 2] == source[3], f"matrix w0 on {name}"
            assert words[base + 3] == 0x00BF02C1, f"matrix tag word on {name}"
            assert words[base + 4] == source[2], f"matrix w1 on {name}"
            assert words[base + 5] == source[1], f"matrix w2 on {name}"
            assert words[base + 6] == source[0], f"matrix w3 on {name}"
            assert words[base + 7] == source[7], f"matrix w4 on {name}"
            assert words[base + 8] == source[6], f"matrix w5 on {name}"
            assert words[base + 9] == source[5], f"matrix w6 on {name}"
            assert words[base + 10] == source[4], f"matrix w7 on {name}"
            assert words[base + 11] == source[11], f"matrix w8 on {name}"
            assert words[base + 12] == source[10], f"matrix w9 on {name}"
            assert words[base + 13] == source[9], f"matrix w10 on {name}"
            assert words[base + 14] == source[8], f"matrix w11 on {name}"
            cursor = (cursor + 0x40) & 0xFFFFFFFF

        # The render-state bits are cleared only when a single-matrix block ran.
        ran_single = any(not (matched and case["matrix_counts"][index] != 0)
                         for index in range(case["count"]))
        expected_state = ((case["state"] & ~6) & 0xFFFFFFFF if ran_single
                          else case["state"])
        assert read_data_u32(result["data"], RENDER_STATE + 0x14) == \
            expected_state, f"render state on {name}"

        # Every slot submits exactly one item to 0x00153C74.
        offset_flags = (case["zero_entry_offset"]
                        or case["zero_item_table_offset"]
                        or case["zero_item_offset"])
        submits = [entry for entry in result["call_log"]
                   if entry[0] == "ui_func_00153c74"]
        if not offset_flags:
            assert len(submits) == case["count"], f"submit count on {name}"
            for index, submit in enumerate(submits):
                assert submit[1][0] == CONTEXT, f"submit context on {name}"
                assert submit[1][1] == ITEMS[index], (
                    f"submit item {index} on {name}: 0x{submit[1][1]:08x}")

        skinned_calls = [entry for entry in result["call_log"]
                         if entry[0] == "func_00153a58"]
        expected_skinned = sum(
            1 for index in range(case["count"])
            if matched and case["matrix_counts"][index] != 0)
        assert len(skinned_calls) == expected_skinned, (
            f"skinned call count on {name}: {len(skinned_calls)}")

    if not side_effects:
        assert read_data_u32(result["data"], CURSOR_GLOBAL) == cursor, (
            f"final cursor on {name}: "
            f"0x{read_data_u32(result['data'], CURSOR_GLOBAL):08x} "
            f"!= 0x{cursor:08x}")


# ---------------------------------------------------------------------------
# Comparison and driver
# ---------------------------------------------------------------------------
def compare(orig: dict, cand: dict) -> list:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(
                f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"]) +
            "\n    cand=" + repr(cand["call_log"]))
    if orig["data"] != cand["data"]:
        offset = next(i for i in range(DATA_SIZE)
                      if orig["data"][i] != cand["data"][i])
        problems.append(
            f"data differs at 0x{(DATA_ADDR + offset):08x}: "
            f"orig=0x{orig['data'][offset]:02x} cand=0x{cand['data'][offset]:02x}")
    if orig["low"] != cand["low"]:
        offset = next(i for i in range(LOW_SIZE)
                      if orig["low"][i] != cand["low"][i])
        problems.append(f"low page differs at 0x{offset:x}")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}")
    return problems


def run_case_set(orig_code, cand_code, cand_blobs, cases) -> int:
    passed = 0
    runner = Machine()
    for case in cases:
        orig = runner.run(orig_code, {}, case)
        cand = runner.run(cand_code, cand_blobs, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        # ABI against the initial state, not only against each other.
        assert cand["pc"] == TRAP_ADDR, f"continuation PC on {case['name']}"
        assert cand["sp"] == ENTRY_SP, f"SP on {case['name']}"
        assert cand["callee_saved"] == CALLEE_SAVED_START, (
            f"callee-saved on {case['name']}: {cand['callee_saved']}")
        check_expectations(case, cand)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing func_00150654 (0x00150654)...")
    orig_code = get_orig_bytes()
    cand_code, cand_blobs = compile_candidate()
    print(f"  original {len(orig_code)} B, candidate {len(cand_code)} B, "
          f"helpers {sorted(hex(key) for key in cand_blobs)}")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cand_blobs, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("position_tag", "constexpr u32 kPositionTag = 0x80000006;",
         "constexpr u32 kPositionTag = 0x80000007;"),
        ("component_type", "constexpr u32 kComponentTypeInfo = 0x00472288;",
         "constexpr u32 kComponentTypeInfo = 0x00472289;"),
        ("group_table_offset",
         "constexpr u32 kGroupEntryTableOffset = 0x30;",
         "constexpr u32 kGroupEntryTableOffset = 0x2C;"),
        ("render_state_mask", "constexpr u32 kRenderStateMask = 0x06;",
         "constexpr u32 kRenderStateMask = 0x02;"),
    ):
        mutant_code, mutant_blobs = compile_mutant(name, old, new)
        detected = False
        reason = ""
        runner = Machine()
        for case in cases:
            good = runner.run(orig_code, {}, case)
            try:
                bad = runner.run(mutant_code, mutant_blobs, case)
            except RuntimeError:
                detected = True
                reason = " (mutant faults where the original returns)"
                break
            if compare(good, bad):
                detected = True
                reason = f" ({case['name']})"
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected{reason}")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
