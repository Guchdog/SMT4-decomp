#!/usr/bin/env python3
"""Differential test for battle_func_002bc3c8 (0x002bc3c8) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the battle_func_002bc3c8 body,
resolves its direct calls to deterministic stubs and its two command-stream
globals to the pinned addresses, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * PC at the return trap, final SP, and callee-saved r4-r11;
  * r0 on every path except the documented early return, where the original
    only leaves the dead address 0x004652A0 in r0;
  * the ordered call log: acquire(dead r0), writer(node, entry, entry fields),
    flush(dead r0), release(dead r0);
  * the full command buffer, replay-entry table, render-node page, render-state
    page and command-cursor page.

Coverage: the unchanged-offset early path (zero and non-zero offsets), both
`offset & 8` rounding branches, every combination of command-stream room
(equal/greater cursor, marker only, marker + one/two/three records), unsigned
cursor wrap, 32-bit count/offset wrap, writer absent/present, writer mutations
of node->cursor_0C / node->count_20 to prove the post-call reloads, all four
flush-gate combinations, and the entry flags bit-0/bit-1/bit-2 masks.

Negative controls mutate the aligned round-up, a record word, and the entry
enabled bit; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_002bc3c8"

FUNC_ADDR = 0x002BC3C8
FUNC_SIZE = 424

# One 2 MiB code page covers the function at 0x2BC3C8 and every stub
# (0x13AF78/0x13AF88/0x2AA8B0/0x2BA5F8) below 0x300000.
CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000

STATE_ADDR = 0x004C6000
STATE_SIZE = 0x00001000
CURSOR_ADDR = 0x00465000
CURSOR_SIZE = 0x00001000
CMD_ADDR = 0x00500000
CMD_SIZE = 0x00010000
NODE_ADDR = 0x00600000
NODE_SIZE = 0x00001000
ENTRY_ADDR = 0x00610000
ENTRY_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

RENDER_STATE = 0x004C6290
GPU_CURSOR = 0x004652A0
GPU_END = 0x004652A4

ENTRY_STRIDE = 28
ENTRY_BASE_OFFSET = 0x200

ENTRY_STATE_NODE = RENDER_STATE + 0x9C
ENTRY_STATE_OWNER = RENDER_STATE + 0xA0

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2AA8B0 = 0x002AA8B0
STUB_13AF78 = 0x0013AF78
STUB_2BA5F8 = 0x002BA5F8
STUB_13AF88 = 0x0013AF88

STUB_NAMES = {
    STUB_2AA8B0: "battle_func_002aa8b0",
    STUB_13AF78: "battle_func_0013af78",
    STUB_2BA5F8: "battle_func_002ba5f8",
    STUB_13AF88: "battle_func_0013af88",
}

# Every helper takes at most two register arguments and no stack words.
STACK_ARGS = {address: 0 for address in STUB_NAMES}

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

OWNER_OTHER = 0x00555554


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "002bc3c8" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"battle_func_002bc3c8 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = None
            for address, name in STUB_NAMES.items():
                if f"{address:08x}" in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            offset = target - pc
            if offset & 3:
                raise RuntimeError(f"unaligned call target 0x{target:08x}")
            displacement = offset >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            if "g_GpuCommandCursor" in rel.symbol_name:
                target = GPU_CURSOR
            elif "g_GpuCommandEnd" in rel.symbol_name:
                target = GPU_END
            else:
                raise RuntimeError(f"unresolved data relocation: {rel.symbol_name}")
            struct.pack_into("<I", code, rel.offset, target)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
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
def build_case_pages(case: dict) -> dict:
    base_offset = case.get("base_offset", 0x400)
    cursor_offset = case.get("cursor_offset", 0x500)
    limit_offset = case.get("limit_offset", cursor_offset + 0x800)
    offset = (cursor_offset - base_offset) & 0xFFFFFFFF

    cmd = bytearray(CMD_SIZE)
    # Distinct non-zero sentinel so untouched record slots are visible.
    for index in range(0, CMD_SIZE, 4):
        struct.pack_into("<I", cmd, index, 0xC1D00000 | (index & 0xFFFC))

    node = bytearray(NODE_SIZE)
    for index in range(0, NODE_SIZE, 4):
        struct.pack_into("<I", node, index, 0xB0B00000 | (index & 0xFFFC))
    struct.pack_into("<I", node, 0x04, (CMD_ADDR + base_offset) & 0xFFFFFFFF)
    struct.pack_into("<I", node, 0x08, CMD_SIZE)
    struct.pack_into("<I", node, 0x0C, 0xDEADBEEF)
    struct.pack_into("<I", node, 0x10, 0x10101010)
    struct.pack_into("<I", node, 0x14, case["committed"] & 0xFFFFFFFF)
    struct.pack_into("<I", node, 0x18,
                     (ENTRY_ADDR + case.get("entry_base", ENTRY_BASE_OFFSET))
                     & 0xFFFFFFFF)
    struct.pack_into("<I", node, 0x1C, 0x1C1C1C1C)
    struct.pack_into("<I", node, 0x20, case.get("count", 3) & 0xFFFFFFFF)
    struct.pack_into("<I", node, 0x30, 0x30303030)
    struct.pack_into("<I", node, 0x34,
                     (NODE_ADDR + 0x800) if case.get("writer", False) else 0)
    struct.pack_into("<I", node, 0x38, 0x38383838)
    node[0x3C] = 0x3C
    node[0x3D] = case.get("enabled", 0) & 0xFF

    owner = case.get("owner", "other")
    if owner == "node":
        owner_value = NODE_ADDR
    elif owner == "null":
        owner_value = 0
    else:
        owner_value = OWNER_OTHER

    state = bytearray(STATE_SIZE)
    state_base = RENDER_STATE - STATE_ADDR
    struct.pack_into("<I", state, state_base + 0x9C, NODE_ADDR)
    struct.pack_into("<I", state, state_base + 0xA0, owner_value)
    state[state_base + 0x11] = case.get("flush_byte", 0) & 0xFF
    state[state_base + 0x12] = case.get("gate", 0) & 0xFF

    entry = bytearray(ENTRY_SIZE)
    for index in range(0, ENTRY_SIZE, 4):
        struct.pack_into("<I", entry, index, 0xE7E00000 | (index & 0xFFFC))
    entry_flags = case.get("entry_flags", 0xFFFFFFFF) & 0xFFFFFFFF
    entry_off = case.get("entry_base", ENTRY_BASE_OFFSET) + \
        ((case.get("count", 3) * ENTRY_STRIDE) & 0xFFFFFFFF)
    if 0 <= entry_off <= ENTRY_SIZE - 4:
        struct.pack_into("<I", entry, entry_off + 0x0C, entry_flags)

    cursor_page = bytearray(CURSOR_SIZE)
    struct.pack_into("<I", cursor_page, GPU_CURSOR - CURSOR_ADDR,
                     (CMD_ADDR + cursor_offset) & 0xFFFFFFFF)
    struct.pack_into("<I", cursor_page, GPU_END - CURSOR_ADDR,
                     (CMD_ADDR + limit_offset) & 0xFFFFFFFF)

    return {
        "cmd": bytes(cmd),
        "node": bytes(node),
        "state": bytes(state),
        "entry": bytes(entry),
        "cursor": bytes(cursor_page),
        "offset": offset,
    }


def read_u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


def write_u32(uc, address: int, value: int) -> None:
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


class BC3C8Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (STATE_ADDR, STATE_SIZE),
            (CURSOR_ADDR, CURSOR_SIZE),
            (CMD_ADDR, CMD_SIZE),
            (NODE_ADDR, NODE_SIZE),
            (ENTRY_ADDR, ENTRY_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )

        self.call_log: list = []
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

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)

        if address == STUB_13AF78:
            self._log(address, r0)
        elif address == STUB_2AA8B0:
            node = r0
            entry = r1
            kind = uc.mem_read(entry, 1)[0]
            start = read_u32(uc, entry + 0x04)
            length = read_u32(uc, entry + 0x08)
            flags = read_u32(uc, entry + 0x0C)
            self._log(address, node, entry, kind, start, length, flags)
            # Observable effects of the real 0x002AA8B0: OR bit 2 into the
            # entry flags, rewrite the entry length, release the writer slot.
            write_u32(uc, entry + 0x0C, flags | 4)
            write_u32(uc, entry + 0x08, length + 0x10)
            write_u32(uc, node + 0x30, 0)
            write_u32(uc, node + 0x34, 0)
            if self.case.get("writer_advance_cursor", False):
                write_u32(uc, node + 0x0C, read_u32(uc, node + 0x0C) + 4)
            if self.case.get("writer_bump_count", False):
                write_u32(uc, node + 0x20, read_u32(uc, node + 0x20) + 1)
        elif address == STUB_2BA5F8:
            self._log(address, r0)
            uc.mem_write(RENDER_STATE + 0x18, b"\x01")
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("flush_ret", 0x2BA5F801)
            )
        elif address == STUB_13AF88:
            self._log(address, r0)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

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
        self.case = case
        pages = build_case_pages(case)

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(STATE_ADDR, pages["state"])
        self.uc.mem_write(CURSOR_ADDR, pages["cursor"])
        self.uc.mem_write(CMD_ADDR, pages["cmd"])
        self.uc.mem_write(NODE_ADDR, pages["node"])
        self.uc.mem_write(ENTRY_ADDR, pages["entry"])
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x44444444)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "memory": {
                "cmd": bytes(self.uc.mem_read(CMD_ADDR, CMD_SIZE)),
                "node": bytes(self.uc.mem_read(NODE_ADDR, NODE_SIZE)),
                "state": bytes(self.uc.mem_read(STATE_ADDR, STATE_SIZE)),
                "entry": bytes(self.uc.mem_read(ENTRY_ADDR, ENTRY_SIZE)),
                "cursor": bytes(self.uc.mem_read(CURSOR_ADDR, CURSOR_SIZE)),
            },
        }


def compare(orig: dict, cand: dict, case: dict) -> list[str]:
    problems = []
    compared = ("pc", "sp", "callee_saved")
    for key in compared:
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if case.get("early_return", False):
        # The routine is void: r0 is dead, and the original happens to leave the
        # literal-pool address 0x004652A0 there.  Record the observation only.
        if orig["ret"] != 0x004652A0:
            problems.append(
                f"original early-return r0 changed: 0x{orig['ret']:08x} != 0x004652a0"
            )
    elif orig["ret"] != cand["ret"]:
        problems.append(f"ret:\n    orig=0x{orig['ret']:08x}\n    cand=0x{cand['ret']:08x}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    for name, value in orig["memory"].items():
        if value != cand["memory"][name]:
            first = next(
                index for index, (a, b) in enumerate(zip(value, cand["memory"][name]))
                if a != b
            )
            problems.append(
                f"memory {name} differs first at +0x{first:04x}: "
                f"orig=0x{value[first]:02x} cand=0x{cand['memory'][name][first]:02x}"
            )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "base_offset": 0x400,
        "cursor_offset": 0x500,
        "committed": 0x100,
        "limit_offset": 0x500 + 0x800,
        "count": 3,
        "entry_base": ENTRY_BASE_OFFSET,
        "entry_flags": 0xFFFFFFFF,
        "writer": False,
        "enabled": 0,
        "owner": "other",
        "gate": 0,
        "flush_byte": 0,
    }
    case.update(overrides)
    return case


def changed_offset_case(name: str, **overrides) -> dict:
    case = base_case(name, **overrides)
    if "committed" not in overrides:
        case["committed"] = 0x10  # differ from the default offset 0x100
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- unchanged-offset early path, r0 is dead
    early = changed_offset_case("early return: offset 0x100 == committed")
    early["committed"] = 0x100
    early["early_return"] = True
    cases.append(early)

    early_zero = base_case("early return: offset 0 == committed", base_offset=0x400,
                           cursor_offset=0x400, committed=0)
    early_zero["early_return"] = True
    cases.append(early_zero)

    early_unaligned = base_case(
        "early return: offset 0x108 == committed", base_offset=0x400,
        cursor_offset=0x508, committed=0x108)
    early_unaligned["early_return"] = True
    cases.append(early_unaligned)

    # --- room for the complete record sequence
    cases.append(changed_offset_case("aligned offset, all four records"))
    cases.append(changed_offset_case(
        "aligned offset, writer + enabled", writer=True, enabled=1))
    cases.append(changed_offset_case(
        "aligned offset, entry flags 0x10000003, enabled 0",
        entry_flags=0x10000003))
    cases.append(changed_offset_case(
        "aligned offset, entry flags 0, enabled 0xFF",
        entry_flags=0, enabled=0xFF))

    # --- unaligned offset 0x108: no marker, only the three records
    cases.append(changed_offset_case(
        "unaligned offset 0x108, all three records",
        base_offset=0x400, cursor_offset=0x508))
    cases.append(changed_offset_case(
        "unaligned offset 0x108, writer", base_offset=0x400,
        cursor_offset=0x508, writer=True, enabled=1))

    # --- command-stream room boundaries (cursor at 0x500, offset 0x100)
    for extra, label in (
        (0x00, "no room at all"),
        (0x08, "marker only"),
        (0x10, "marker + 1 record"),
        (0x18, "marker + 2 records"),
        (0x20, "marker + 3 records"),
    ):
        cases.append(changed_offset_case(
            f"room {label} (end = cursor + 0x{extra:02x})",
            limit_offset=0x500 + extra))
    cases.append(changed_offset_case(
        "end below cursor (unsigned skip)", limit_offset=0x4F8))
    cases.append(changed_offset_case(
        "end below cursor by 1", limit_offset=0x4FF))

    # unaligned room boundaries: only the three records, no marker
    for extra, label in (
        (0x00, "no room"),
        (0x08, "1 record"),
        (0x10, "2 records"),
        (0x18, "3 records"),
    ):
        cases.append(changed_offset_case(
            f"unaligned 0x108 room {label} (end = cursor + 0x{extra:02x})",
            base_offset=0x400, cursor_offset=0x508,
            limit_offset=0x508 + extra))

    # --- unsigned offset wrap: base above cursor
    cases.append(changed_offset_case(
        "offset wrap 0xFFFFFF00", base_offset=0x600, cursor_offset=0x500))
    cases.append(changed_offset_case(
        "offset wrap 0xFFFFFFF8 (bit 3 set)", base_offset=0x608,
        cursor_offset=0x500))

    # --- state owner / flush gate combinations
    cases.append(changed_offset_case(
        "owner is node, gate 0, flush byte 0xFF", owner="node",
        gate=0, flush_byte=0xFF))
    cases.append(changed_offset_case(
        "owner is node, gate 1, flush byte 1", owner="node",
        gate=1, flush_byte=1))
    cases.append(changed_offset_case(
        "owner is node, gate 1, flush byte 0x80", owner="node",
        gate=1, flush_byte=0x80))
    cases.append(changed_offset_case(
        "owner is node, gate 1, flush byte 0 -> flush", owner="node",
        gate=1, flush_byte=0))
    cases.append(changed_offset_case(
        "owner is node, gate 0x80, flush byte 0 -> flush", owner="node",
        gate=0x80, flush_byte=0, flush_ret=0xABCDEF01))
    cases.append(changed_offset_case(
        "owner is node, gate 0xFF, flush byte 0 -> flush ret 0",
        owner="node", gate=0xFF, flush_byte=0, flush_ret=0))
    cases.append(changed_offset_case("owner null", owner="null"))
    cases.append(changed_offset_case("owner other pointer", owner="other"))

    # --- writer re-read stress: the original reloads node->cursor_0C and
    #     node->count_20 after the callback.
    cases.append(changed_offset_case(
        "writer advances node cursor", writer=True,
        writer_advance_cursor=True))
    cases.append(changed_offset_case(
        "writer bumps node count", writer=True, writer_bump_count=True))
    cases.append(changed_offset_case(
        "writer advances cursor and bumps count", writer=True,
        writer_advance_cursor=True, writer_bump_count=True, count=7))

    # --- 32-bit count arithmetic (28 * count wraps modulo 2^32)
    cases.append(changed_offset_case("count 0", count=0))
    cases.append(changed_offset_case("count 1", count=1))
    cases.append(changed_offset_case("count 0x40000001 wraps to index 1",
                                     count=0x40000001))
    cases.append(changed_offset_case("count 0xFFFFFFFF wraps to index -1",
                                     count=0xFFFFFFFF, entry_base=0x1000))
    cases.append(changed_offset_case("count 0x80000002 wraps to index 2",
                                     count=0x80000002))

    cases.append(changed_offset_case(
        "writer present, entry flags 0x10000003, enabled 1",
        writer=True, entry_flags=0x10000003, enabled=1))
    cases.append(changed_offset_case(
        "writer present, entry flags 0xFFFFFFFE, enabled 0",
        writer=True, entry_flags=0xFFFFFFFE, enabled=0))

    # --- record word / flags negative-control sensitivity on the boundary
    cases.append(changed_offset_case(
        "entry flags bit 1 set, bit 2 set, enabled 0",
        entry_flags=0xFFFFFFFE))
    cases.append(changed_offset_case(
        "entry flags bit 1 set, bit 2 set, enabled 1",
        entry_flags=0xFFFFFFFE, enabled=1))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = BC3C8Runner().run(orig_code, case)
        cand = BC3C8Runner().run(cand_code, case)
        problems = compare(orig, cand, case)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing battle_func_002bc3c8 (0x002bc3c8)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          "(relocations resolved).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("aligned_round_up", "constexpr u32 kOffsetAddAligned = 0x18;",
         "constexpr u32 kOffsetAddAligned = 0x20;"),
        ("record_word_a", "constexpr u32 kRecordWordA = 0x000F0111;",
         "constexpr u32 kRecordWordA = 0x000F0112;"),
        ("entry_enabled_bit", "constexpr u32 kEntryEnabledBit = 1u;",
         "constexpr u32 kEntryEnabledBit = 2u;"),
        ("marker_word", "constexpr u32 kMarkerWord = 0x0008025E;",
         "constexpr u32 kMarkerWord = 0x0008025F;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = BC3C8Runner().run(orig_code, case)
            bad = BC3C8Runner().run(mutant_code, case)
            if compare(orig, bad, case):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
