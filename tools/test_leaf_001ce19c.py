#!/usr/bin/env python3
"""Differential test for camp_func_001ce19c (0x001ce19c) using Unicorn ARM.

Compiles ``src/engine/leaf_batch34_c.cpp``, extracts the reconstructed
``camp_func_001ce19c`` body, resolves its direct calls to deterministic stubs at
the original addresses, and runs the pinned original
(``extracted/exefs/code.bin``) against the candidate in separate Unicorn
machines with identical fixtures.

Compared outputs:
  * continuation PC, final SP and the callee-saved registers r4-r11;
  * the ordered call log: every helper with its register arguments, the
    architected stack words, the buffer digest shipped to 0x0029DB94, the three
    patched menu halfwords and whether the commit buffer is the one that was
    just built;
  * the complete work page (row count, timer, cursor, row records) and the
    selected-actor page;
  * every write outside the private stack (as an unordered set: plain stores
    to independent fields may legitimately be reordered).

Coverage: row count ``-1/0`` (early exit) and positive counts, inactive rows,
zero masks (clear path) with matching and non-matching actor flags, non-zero
masks whose id does and does not equal the actor's sign-extended first halfword
(including the ``0x7FFF``/``0x8000``/``0xFFFF`` boundaries), every set-bit
ordinal 0..9 with single- and multi-bit masks, masks with no bit in 1..10
(ordinal zero / divide-by-zero forwarding), cursor values 0, 1, 3, 5, 8, 9 and
``0xFFFFFFFF`` wrap, timer boundaries ``-1/0/0x17/0x18/0x19/0x7FFFFFFF`` and
the signed ``0x80000000`` case, multi-row ordering and stride, and a stub that
shrinks the row count to prove the count is re-read every iteration.

Negative controls mutate the row stride, the row base, the timer threshold, one
menu-buffer slot, and the count-reload structure; each mutant must be detected.
"""

from __future__ import annotations

import hashlib
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
OUT_DIR = ROOT / "build/test_leaf_001ce19c"

FUNC_ADDR = 0x001CE19C
FUNC_SIZE = 520

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the function and every stub below 0x400000
WORK_ADDR = 0x00710000
WORK_SIZE = 0x00008000
ACTOR_ADDR = 0x00720000
ACTOR_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets; stubs are placed at the same addresses so both
# the original bytes and the relocated candidate resolve to them.
STUB_ACTOR = 0x0029AF4C        # Status_GetSelectedActorPtr
STUB_BIT_LOOKUP = 0x002B0788   # ui_func_002b0788
STUB_SET_SELECTION = 0x00317FA4  # func_00317fa4
STUB_MENU_BUILD = 0x0026AAC0   # camp_func_0026aac0
STUB_MENU_COMMIT = 0x0029DB94  # camp_func_0029db94
STUB_SET_MODE = 0x0026ABC0     # Status_SetMode1E71
STUB_MENU_PLAY = 0x0029D924    # camp_func_0029d924
STUB_DIVMOD = 0x002C615C       # ui_func_002c615c

STUB_NAMES = {
    STUB_ACTOR: "Status_GetSelectedActorPtr",
    STUB_BIT_LOOKUP: "ui_func_002b0788",
    STUB_SET_SELECTION: "func_00317fa4",
    STUB_MENU_BUILD: "camp_func_0026aac0",
    STUB_MENU_COMMIT: "camp_func_0029db94",
    STUB_SET_MODE: "Status_SetMode1E71",
    STUB_MENU_PLAY: "camp_func_0029d924",
    STUB_DIVMOD: "ui_func_002c615c",
}

# Symbol-name and address-substring spellings used by the compiler relocations.
CALL_TARGETS = {
    "Status_GetSelectedActorPtr": STUB_ACTOR,
    "ui_func_002b0788": STUB_BIT_LOOKUP,
    "func_00317fa4": STUB_SET_SELECTION,
    "camp_func_0026aac0": STUB_MENU_BUILD,
    "camp_func_0029db94": STUB_MENU_COMMIT,
    "Status_SetMode1E71": STUB_SET_MODE,
    "camp_func_0029d924": STUB_MENU_PLAY,
    "ui_func_002c615c": STUB_DIVMOD,
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

# Work block offsets (mirrored from the listing, deliberately not shared with
# the source under test so a wrong constant is visible).
ROW_COUNT = 0x5758
TIMER = 0x591C
SELECTION = 0x5920
ROW_BASE = 0x5700
ROW_STRIDE = 0x2C
ROW_ID = 0x60
ROW_F62 = 0x62
ROW_F64 = 0x64
ROW_FLAGS = 0x66
ROW_ACTIVE = 0x88
MENU_SLOT_A = 0x2A
MENU_SLOT_B = 0x2C
MENU_SLOT_C = 0x44
MENU_BUILD_SIZE = 0x604


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "001ce19c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"camp_func_001ce19c not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = CALL_TARGETS.get(rel.symbol_name)
        if target is None:
            for name, address in CALL_TARGETS.items():
                if f"{address:08x}" in rel.symbol_name:
                    target = address
                    break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        displacement = (target - (FUNC_ADDR + rel.offset + 8)) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate() -> bytes:
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
def make_row(**overrides) -> dict:
    row = {
        "active": 1,
        "id": 0x0100,
        "f62": 0x1122,
        "f64": 0x3344,
        "flags": 0,
    }
    row.update(overrides)
    return row


def build_work(case: dict) -> bytes:
    page = bytearray(WORK_SIZE)
    struct.pack_into("<i", page, ROW_COUNT, case["count"])
    struct.pack_into("<i", page, TIMER, case.get("timer", 0))
    struct.pack_into("<I", page, SELECTION, case.get("selection", 0) & 0xFFFFFFFF)
    for index, row in enumerate(case["rows"]):
        base = ROW_BASE + index * ROW_STRIDE
        page[base + ROW_ACTIVE] = row["active"] & 0xFF
        struct.pack_into("<H", page, base + ROW_ID, row["id"] & 0xFFFF)
        struct.pack_into("<H", page, base + ROW_F62, row["f62"] & 0xFFFF)
        struct.pack_into("<H", page, base + ROW_F64, row["f64"] & 0xFFFF)
        struct.pack_into("<H", page, base + ROW_FLAGS, row["flags"] & 0xFFFF)
    return bytes(page)


def build_actor(case: dict) -> bytes:
    page = bytearray(ACTOR_SIZE)
    struct.pack_into("<h", page, 0, case.get("actor_head", 0))
    struct.pack_into("<H", page, 0x14, case.get("actor_flags", 0) & 0xFFFF)
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(ACTOR_ADDR, ACTOR_SIZE)
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
        self.build_buffer = 0

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    @staticmethod
    def _digest(raw: bytes) -> str:
        return hashlib.sha256(raw).hexdigest()[:16]

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_ACTOR:
            self.call_log.append(("Status_GetSelectedActorPtr",))
            uc.reg_write(arm.UC_ARM_REG_R0, ACTOR_ADDR)
        elif address == STUB_BIT_LOOKUP:
            value = r0 - (1 << 32) if r0 & 0x80000000 else r0
            self.call_log.append(("ui_func_002b0788", value))
            uc.reg_write(arm.UC_ARM_REG_R0, (0xB0770000 | r0) & 0xFFFFFFFF)
        elif address == STUB_SET_SELECTION:
            self.call_log.append(("func_00317fa4", r0))
        elif address == STUB_MENU_BUILD:
            # Reproduce the observed helper contract: clear 0x604 bytes and
            # stamp the resolved id at +0x46 so the digest is id-sensitive.
            ident = r0 & 0xFFFF
            buffer = r1
            self.build_buffer = buffer
            self.call_log.append(("camp_func_0026aac0", ident, buffer != 0))
            self.uc.mem_write(buffer, b"\x00" * MENU_BUILD_SIZE)
            self.uc.mem_write(buffer + 0x46, struct.pack("<H", ident))
        elif address == STUB_MENU_COMMIT:
            raw = bytes(self.uc.mem_read(r0, MENU_BUILD_SIZE))
            slot_a = struct.unpack_from("<H", raw, MENU_SLOT_A)[0]
            slot_b = struct.unpack_from("<H", raw, MENU_SLOT_B)[0]
            slot_c = struct.unpack_from("<H", raw, MENU_SLOT_C)[0]
            self.call_log.append(
                (
                    "camp_func_0029db94",
                    self._digest(raw),
                    slot_a,
                    slot_b,
                    slot_c,
                    r1,
                    r2,
                    r0 == self.build_buffer,
                )
            )
        elif address == STUB_SET_MODE:
            self.call_log.append(("Status_SetMode1E71", r0 & 0xFF))
        elif address == STUB_MENU_PLAY:
            self.call_log.append(("camp_func_0029d924", r0))
            delta = self.case.get("count_delta_on_play", 0)
            if delta:
                current = struct.unpack(
                    "<i", self.uc.mem_read(WORK_ADDR + ROW_COUNT, 4)
                )[0]
                self.uc.mem_write(
                    WORK_ADDR + ROW_COUNT,
                    struct.pack("<i", current + delta),
                )
        elif address == STUB_DIVMOD:
            numerator = r0
            denominator = r1
            if denominator == 0:
                quotient = 0
                remainder = numerator
            else:
                quotient = (numerator // denominator) & 0xFFFFFFFF
                remainder = (numerator % denominator) & 0xFFFFFFFF
            self.call_log.append(
                ("ui_func_002c615c", numerator, denominator, quotient, remainder)
            )
            uc.reg_write(arm.UC_ARM_REG_R0, quotient)
            uc.reg_write(arm.UC_ARM_REG_R1, remainder)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.build_buffer = 0
        self.work = build_work(case)

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(WORK_ADDR, self.work)
        self.uc.mem_write(ACTOR_ADDR, build_actor(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, WORK_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not in_stack:
                unexpected_writes.append((address, size, value))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "work": bytes(self.uc.mem_read(WORK_ADDR, WORK_SIZE)),
            "actor": bytes(self.uc.mem_read(ACTOR_ADDR, ACTOR_SIZE)),
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
    if orig["work"] != cand["work"]:
        first = next(
            (i for i, (a, b) in enumerate(zip(orig["work"], cand["work"])) if a != b),
            None,
        )
        problems.append(f"work page differs (first byte offset {first})")
    if orig["actor"] != cand["actor"]:
        problems.append("actor page was modified differently")
    if sorted(orig["unexpected_writes"]) != sorted(cand["unexpected_writes"]):
        problems.append(
            "unexpected writes:\n    orig="
            f"{orig['unexpected_writes']}\n    cand={cand['unexpected_writes']}"
        )
    return problems


# --------------------------------------------------------------------- cases
def base_case(name: str, rows=None, **overrides) -> dict:
    case = {
        "name": name,
        "count": len(rows) if rows is not None else 0,
        "timer": 0,
        "selection": 0,
        "actor_head": 0,
        "actor_flags": 0,
        "rows": rows if rows is not None else [],
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []
    r = make_row

    # --- row count gate -----------------------------------------------------
    cases.append(base_case("count -1 early exit", count=-1, rows=[r()]))
    cases.append(base_case("count 0 early exit", count=0, rows=[r()]))

    # --- inactive rows ------------------------------------------------------
    cases.append(base_case("single inactive row", rows=[r(active=0)]))
    cases.append(
        base_case("four rows all inactive", rows=[r(active=0) for _ in range(4)])
    )
    cases.append(base_case("active byte 0xFF is active", rows=[r(active=0xFF)]))

    # --- zero mask / clear-selection path ----------------------------------
    cases.append(base_case("zero mask, actor flags equal", rows=[r(flags=0)]))
    cases.append(
        base_case("zero mask, actor flags differ", rows=[r(flags=0)],
                  actor_flags=0x20)
    )
    cases.append(
        base_case("zero mask, actor flags 0xFFFF", rows=[r(flags=0)],
                  actor_flags=0xFFFF)
    )

    # --- masked rows: id comparison ---------------------------------------
    cases.append(
        base_case(
            "masked row id match",
            rows=[r(id=0x0042, flags=0x0002)],
            actor_head=0x0042,
            actor_flags=0x20,
        )
    )
    cases.append(
        base_case(
            "masked row id mismatch",
            rows=[r(id=0x0042, flags=0x0002)],
            actor_head=0x0043,
            actor_flags=0x20,
        )
    )
    cases.append(
        base_case(
            "actor head 0x7FFF matches id 0x7FFF",
            rows=[r(id=0x7FFF, flags=0x0002)],
            actor_head=0x7FFF,
        )
    )
    cases.append(
        base_case(
            "actor head 0x8000 does not match id 0x8000",
            rows=[r(id=0x8000, flags=0x0002)],
            actor_head=-0x8000,
        )
    )
    cases.append(
        base_case(
            "actor head 0xFFFF does not match id 0xFFFF",
            rows=[r(id=0xFFFF, flags=0x0002)],
            actor_head=-1,
        )
    )
    cases.append(
        base_case(
            "actor head 0x0000 matches id 0x0000",
            rows=[r(id=0x0000, flags=0x0002)],
            actor_head=0,
        )
    )

    # --- masked rows: cursor / ordinal selection --------------------------
    for selection in (0, 1, 2, 3, 5, 8, 9, 0xFFFFFFFF):
        cases.append(
            base_case(
                f"ten options cursor {selection:#x}",
                rows=[r(id=0x0007, flags=0x7FE)],
                actor_head=0x0007,
                actor_flags=0x30,
                selection=selection,
            )
        )
    for flags, selection in (
        (0x0002, 0),
        (0x0006, 0),
        (0x0006, 1),
        (0x0006, 2),
        (0x3FE, 0),
        (0x3FE, 8),
        (0x400, 0),
        (0x7FE, 0),
    ):
        cases.append(
            base_case(
                f"flags {flags:#06x} cursor {selection}",
                rows=[r(id=0x0101, flags=flags)],
                actor_head=0x0101,
                selection=selection,
            )
        )

    # --- masked row whose mask has no bits 1..10 (ordinal zero) -----------
    cases.append(
        base_case(
            "mask bit0 only, timer expired, divide by zero",
            rows=[r(id=0x0102, flags=0x0001)],
            actor_head=0x0102,
            timer=0x18,
        )
    )
    cases.append(
        base_case(
            "mask bit15 only, timer expired, divide by zero",
            rows=[r(id=0x0102, flags=0x8000)],
            actor_head=0x0102,
            timer=0x18,
        )
    )
    cases.append(
        base_case(
            "mask bits 0 and 12..15, timer expired",
            rows=[r(id=0x0102, flags=0xF001)],
            actor_head=0x0102,
            timer=0x18,
            selection=0xFFFFFFFF,
        )
    )

    # --- actor flags equal to the mask suppresses the commit --------------
    cases.append(
        base_case(
            "mask equals actor flags, no commit",
            rows=[r(id=0x0103, flags=0x0006)],
            actor_head=0x0103,
            actor_flags=0x0006,
            selection=0,
        )
    )
    cases.append(
        base_case(
            "mask equals actor flags, cursor on second bit",
            rows=[r(id=0x0103, flags=0x0006)],
            actor_head=0x0103,
            actor_flags=0x0006,
            selection=1,
            timer=0x18,
        )
    )

    # --- timer boundary and cursor wrap -----------------------------------
    for timer in (-1, 0, 0x17, 0x18, 0x19, 0x7FFFFFFF, -0x80000000):
        cases.append(
            base_case(
                f"timer {timer:#010x}",
                rows=[r(id=0x0104, flags=0x7FE)],
                actor_head=0x0104,
                actor_flags=0x40,
                selection=4,
                timer=timer,
            )
        )
    for selection in (0, 9, 0xFFFFFFFF, 0xFFFFFFFE):
        cases.append(
            base_case(
                f"timer expired selection {selection:#x}",
                rows=[r(id=0x0105, flags=0x7FE)],
                actor_head=0x0105,
                selection=selection,
                timer=0x18,
            )
        )
    cases.append(
        base_case(
            "single-bit mask timer reset",
            rows=[r(id=0x0105, flags=0x0002)],
            actor_head=0x0105,
            timer=0x18,
        )
    )

    # --- multi-row ordering / stride --------------------------------------
    cases.append(
        base_case(
            "three rows mixed order",
            rows=[
                r(id=0x0200, flags=0, f62=1, f64=2),
                r(id=0x0201, flags=0x0004, f62=3, f64=4),
                r(id=0x0202, flags=0x0002, f62=5, f64=6),
            ],
            actor_head=0x0201,
            actor_flags=0x50,
            timer=0x18,
        )
    )
    cases.append(
        base_case(
            "third row only active",
            rows=[
                r(id=0x0300, active=0),
                r(id=0x0301, active=0),
                r(id=0x0302, flags=0x0002, f62=0xAAAA, f64=0xBBBB),
            ],
            actor_head=0x0302,
            actor_flags=0x60,
            timer=0x18,
        )
    )
    cases.append(
        base_case(
            "count smaller than row table",
            count=2,
            rows=[
                r(id=0x0400, flags=0x0002),
                r(id=0x0401, flags=0x0002),
                r(id=0x0402, flags=0x0002),
            ],
            actor_head=0x0400,
            actor_flags=0x70,
            timer=0x18,
        )
    )

    # --- helpers shrink the row count: proves the per-iteration re-read ----
    cases.append(
        base_case(
            "play shrinks count by one",
            count=3,
            rows=[
                r(id=0x0500, flags=0x0002),
                r(id=0x0501, flags=0x0002),
                r(id=0x0502, flags=0x0002),
            ],
            actor_head=0x0500,
            actor_flags=0x80,
            timer=0x18,
            count_delta_on_play=-1,
        )
    )
    cases.append(
        base_case(
            "play shrinks count below cursor",
            count=2,
            rows=[r(id=0x0503, flags=0x0002), r(id=0x0504, flags=0x0002)],
            actor_head=0x0503,
            actor_flags=0x90,
            count_delta_on_play=-2,
        )
    )
    cases.append(
        base_case(
            "play clears count",
            count=4,
            rows=[r(id=0x0505, flags=0x0002) for _ in range(4)],
            actor_head=0x0505,
            actor_flags=0xA0,
            count_delta_on_play=-4,
        )
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
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing camp_func_001ce19c (0x001ce19c)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("row_stride", "constexpr s32 kCampRowStride = 0x2c;",
         "constexpr s32 kCampRowStride = 0x30;"),
        ("row_base", "constexpr u32 kCampRowBase = 0x5700;",
         "constexpr u32 kCampRowBase = 0x5704;"),
        ("timer_limit", "constexpr s32 kCampTimerLimit = 0x18;",
         "constexpr s32 kCampTimerLimit = 0x17;"),
        ("menu_slot_a", "constexpr u32 kCampMenuSlotA = 0x2a;",
         "constexpr u32 kCampMenuSlotA = 0x2c;"),
        ("count_reload",
         "for (s32 row = 0; CampRowCount(work) > row; ++row) {",
         "const s32 camp_row_limit = CampRowCount(work);\n"
         "    for (s32 row = 0; camp_row_limit > row; ++row) {"),
        ("actor_sign_extend",
         "static_cast<s32>(static_cast<s16>(CampLoadU16(actor, 0)))",
         "static_cast<s32>(CampLoadU16(actor, 0))"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                print(f"  [PASS] {name} mutant detected by {case['name']!r}")
                break
        if not detected:
            raise SystemExit(f"  [FAIL] negative control {name} was not detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
