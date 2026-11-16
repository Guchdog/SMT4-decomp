#!/usr/bin/env python3
"""Differential test for battle_func_00336e20 (0x00336E20, 444 bytes) with Unicorn ARM.

Compiles ``src/engine/leaf_batch41_c.cpp``, extracts the
``battle_func_00336e20`` body, resolves its direct calls to deterministic stubs
at their original addresses, and runs the pinned original
(``extracted/exefs/code.bin``) and the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * final r0, continuation PC, final SP, and callee-saved r4-r11;
  * the ordered call log: all register arguments plus the architected stack
    words of each helper (2 for 0x00245330, 1 for 0x00240660, none for the
    others), and the comparator pointer handed to the sort routine;
  * every non-stack emulated write, including its width (the original writes
    the context flag word as 32 bits and each entry state word as 16 bits);
  * the full context, owner, entry-array, global-slot/table and record pages.

The 0x002B7F0A sort entry (ledger name camp_func_002b7f08) is stubbed with a
deterministic queue reversal so that the second pass must consume the sorted
array; the distance comparator body at 0x0019D76C is never executed.  The real
0x00240744, 0x002406AC, 0x00245330, 0x00240660 and 0x0024095C bodies are
replaced by logging stubs.

Coverage: zero/one/many queued entries, empty scan window, the index 3/0x36
decoys outside 4..0x35, entries failing either queued flag bit, already-done
entries, all 50 entries, both 0x10-selected coordinate layouts, s16 table
boundaries (0, -1, INT16_MIN, INT16_MAX), a nonzero context flag word, a
context-pointer swap discovered by the reloaded final call, and helper-time
flag mutations that prove the coordinate selection is latched while the third
helper's 6/7 kind comes from a fresh load.  Negative controls mutate the scan
bounds, entry stride, done bit, selected table offset, comparator address, and
helper kind; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_00336e20"

FUNC_ADDR = 0x00336E20
FUNC_SIZE = 444

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x3F0000
DATA_ADDR = 0x00430000
DATA_SIZE = 0x00010000
OWNER_ADDR = 0x00600000
OWNER_SIZE = 0x00020000
ENTRY_ADDR = 0x00620000
ENTRY_SIZE = 0x00010000
CONTEXT_ADDR = 0x00700000
CONTEXT_SIZE = 0x00001000
CONTEXT_ALT = CONTEXT_ADDR + CONTEXT_SIZE
RECORD_ADDR = 0x00702000
RECORD_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

GLOBAL_CONTEXT_SLOT = 0x004342C8
GLOBAL_RECORD_SLOT = 0x00435D18
LAYOUT_TABLE = 0x00439A20
ENTRY_ARRAY_POINTER = 0x1E98

ENTRY_STRIDE = 0x114
SCAN_FIRST = 4
SCAN_LIMIT = 0x36
ENTRY_FLAGS_OFFSET = 0x50
ENTRY_STATE_OFFSET = 0x58

STUB_40744 = 0x00240744
STUB_406AC = 0x002406AC
STUB_45330 = 0x00245330
STUB_40660 = 0x00240660
STUB_4095C = 0x0024095C
STUB_SORT = 0x002B7F0A  # Thumb entry; ledger name camp_func_002b7f08

STUB_NAMES = {
    STUB_40744: "func_00240744",
    STUB_406AC: "func_002406ac",
    STUB_45330: "func_00245330",
    STUB_40660: "func_00240660",
    STUB_4095C: "func_0024095c",
    STUB_SORT: "camp_func_002b7f08",
}

# Symbol name -> stub address (the sort symbol resolves to its Thumb entry).
SYMBOLS = {
    "func_00240744": STUB_40744,
    "func_002406ac": STUB_406AC,
    "func_00245330": STUB_45330,
    "func_00240660": STUB_40660,
    "func_0024095c": STUB_4095C,
    "camp_func_002b7f08": STUB_SORT,
}

# Number of architected stack words each helper receives.
STACK_ARGS = {
    STUB_40744: 0,
    STUB_406AC: 0,
    STUB_45330: 2,  # table t4, zero
    STUB_40660: 1,  # 0x0D
    STUB_4095C: 0,
    STUB_SORT: 0,
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

DEFAULT_TABLE = {
    0x00: 11,
    0x04: -22,
    0x08: 33,
    0x0C: -44,
    0x10: 55,
    0x14: -66,
    0x18: 77,
}


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00336e20" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"battle_func_00336e20 not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = SYMBOLS.get(rel.symbol_name)
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        if target == STUB_SORT:
            # BLX (immediate) for Thumb code: cond=1111 101H,
            # target = Align(PC,4) + (imm24 << 2) + (H << 1).
            offset = target - pc
            if offset & 1:
                raise RuntimeError(f"unaligned Thumb call target 0x{target:08x}")
            imm24 = (offset >> 2) & 0x00FFFFFF
            h_bit = (offset >> 1) & 1
            instruction = 0xFA000000 | (h_bit << 24) | imm24
        else:
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            instruction = cond | (displacement & 0x00FFFFFF)
        struct.pack_into("<I", code, rel.offset, instruction)
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
def build_owner() -> bytes:
    page = bytearray(OWNER_SIZE)
    for offset in range(0, OWNER_SIZE, 4):
        struct.pack_into("<I", page, offset, (0xA5A50000 | offset) & 0xFFFFFFFF)
    struct.pack_into("<I", page, ENTRY_ARRAY_POINTER, ENTRY_ADDR)
    return bytes(page)


def build_entries(case: dict) -> bytes:
    page = bytearray(ENTRY_SIZE)
    for index in range(ENTRY_SIZE):
        page[index] = (0x30 + (index & 0x3F)) & 0xFF
    entries = {
        SCAN_FIRST - 1: (0x0003, 0x0000),  # index 3 decoy, outside the window
        SCAN_LIMIT: (0x0003, 0x0000),      # index 0x36 decoy, outside the window
    }
    entries.update(case.get("entries", {}))
    for index, (flags, state) in entries.items():
        if index < 0 or index > SCAN_LIMIT + 1:
            continue
        base = index * ENTRY_STRIDE
        struct.pack_into("<I", page, base + ENTRY_FLAGS_OFFSET, flags & 0xFFFFFFFF)
        struct.pack_into("<H", page, base + ENTRY_STATE_OFFSET, state & 0xFFFF)
    return bytes(page)


def build_context(page_index: int, case: dict) -> bytes:
    page = bytearray(CONTEXT_SIZE)
    for offset in range(0, CONTEXT_SIZE, 4):
        struct.pack_into("<I", page, offset, (0xC0C00000 | (page_index << 12) | offset) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x634, case.get("ctx_flags", 0) & 0xFFFFFFFF)
    return bytes(page)


def build_data(case: dict) -> bytes:
    page = bytearray(DATA_SIZE)
    for offset in range(0, DATA_SIZE, 4):
        struct.pack_into("<I", page, offset, (0x5A5A0000 | offset) & 0xFFFFFFFF)
    context = CONTEXT_ALT if case.get("context_swap") else CONTEXT_ADDR
    struct.pack_into("<I", page, GLOBAL_CONTEXT_SLOT - DATA_ADDR, context)
    struct.pack_into("<I", page, GLOBAL_RECORD_SLOT - DATA_ADDR, RECORD_ADDR)
    table = dict(DEFAULT_TABLE)
    table.update(case.get("table", {}))
    for offset, value in table.items():
        struct.pack_into("<h", page, LAYOUT_TABLE - DATA_ADDR + offset, value)
    return bytes(page)


def build_record() -> bytes:
    page = bytearray(RECORD_SIZE)
    for offset in range(0, RECORD_SIZE, 4):
        struct.pack_into("<I", page, offset, (0xA0000000 | offset) & 0xFFFFFFFF)
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(OWNER_ADDR, OWNER_SIZE)
        self.uc.mem_map(ENTRY_ADDR, ENTRY_SIZE)
        self.uc.mem_map(CONTEXT_ADDR, CONTEXT_SIZE * 2)
        self.uc.mem_map(RECORD_ADDR, RECORD_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            if address == STUB_SORT:
                self.uc.mem_write(address, struct.pack("<H", 0x4770))  # thumb bx lr
            else:
                self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], tuple(args) + self._stack_words(STACK_ARGS[address]))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _clear_selected_bit(self, entry: int) -> None:
        address = entry + ENTRY_FLAGS_OFFSET
        current = struct.unpack("<I", self.uc.mem_read(address, 4))[0]
        self.uc.mem_write(address, struct.pack("<I", current & ~0x10))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_40744:
            self._log(address, r0)
            if self.case.get("context_swap"):
                uc.mem_write(
                    GLOBAL_CONTEXT_SLOT, struct.pack("<I", CONTEXT_ALT)
                )
        elif address == STUB_SORT:
            base = "<stack>" if STACK_ADDR <= r0 < STACK_ADDR + STACK_SIZE else r0
            self._log(address, base, r1, r2, r3)
            if 2 <= r1 <= 50:
                raw = bytearray(uc.mem_read(r0, 4 * r1))
                words = [bytes(raw[i * 4 : i * 4 + 4]) for i in range(r1)]
                words.reverse()
                uc.mem_write(r0, b"".join(words))
        elif address == STUB_406AC:
            self._log(address, r0, r1, r2, r3)
            if self.case.get("mutate_after_first"):
                self._clear_selected_bit(r1)
        elif address == STUB_45330:
            self._log(address, r0, r1, r2, r3)
            if self.case.get("mutate_on_second"):
                self._clear_selected_bit(r2)
        elif address == STUB_40660:
            self._log(address, r0, r1, r2, r3)
        elif address == STUB_4095C:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x5C000000 | (r1 & 0xFFFF))
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DATA_ADDR, build_data(case))
        self.uc.mem_write(OWNER_ADDR, build_owner())
        self.uc.mem_write(ENTRY_ADDR, build_entries(case))
        self.uc.mem_write(CONTEXT_ADDR, build_context(0, case))
        self.uc.mem_write(CONTEXT_ALT, build_context(1, case))
        self.uc.mem_write(RECORD_ADDR, build_record())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OWNER_ADDR)
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

        non_stack_writes = [
            write
            for write in self.writes
            if not (STACK_ADDR <= write[0] < STACK_ADDR + STACK_SIZE)
        ]

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "non_stack_writes": non_stack_writes,
            "memory": {
                "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
                "owner": bytes(self.uc.mem_read(OWNER_ADDR, OWNER_SIZE)),
                "entries": bytes(self.uc.mem_read(ENTRY_ADDR, ENTRY_SIZE)),
                "context0": bytes(self.uc.mem_read(CONTEXT_ADDR, CONTEXT_SIZE)),
                "context1": bytes(self.uc.mem_read(CONTEXT_ALT, CONTEXT_SIZE)),
                "record": bytes(self.uc.mem_read(RECORD_ADDR, RECORD_SIZE)),
            },
        }


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
    if orig["non_stack_writes"] != cand["non_stack_writes"]:
        problems.append(
            "non-stack writes:\n    orig="
            + repr(orig["non_stack_writes"])
            + "\n    cand="
            + repr(cand["non_stack_writes"])
        )
    for key, value in orig["memory"].items():
        if value != cand["memory"][key]:
            problems.append(f"memory {key} was modified differently")
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "entries": {},
        "table": {},
        "ctx_flags": 0,
        "context_swap": False,
        "mutate_after_first": False,
        "mutate_on_second": False,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- scan window / queue shapes -----------------------------------------
    cases.append(base_case("no eligible entries"))
    cases.append(base_case("single entry at first index", entries={4: (0x0003, 0)}))
    cases.append(
        base_case("single entry at last index, selected layout",
                  entries={SCAN_LIMIT - 1: (0x0013, 0)})
    )
    cases.append(
        base_case("index 3 and 0x36 decoys are outside the window",
                  entries={3: (0x0003, 0), SCAN_LIMIT: (0x0003, 0)})
    )
    cases.append(
        base_case("three entries, alternating layouts",
                  entries={4: (0x0003, 0), 5: (0x0013, 0), 6: (0x0003, 0)})
    )
    cases.append(
        base_case("queue counts at index 3/4 and 0x35/0x36",
                  entries={3: (0x0003, 0), 4: (0x0003, 0),
                           SCAN_LIMIT - 1: (0x0003, 0),
                           SCAN_LIMIT: (0x0003, 0)})
    )

    # --- done bit and per-bit filtering -------------------------------------
    cases.append(base_case("done bit already set skips dispatch",
                           entries={4: (0x0003, 0x0800)}))
    cases.append(base_case("mixed done bits",
                           entries={4: (0x0003, 0),
                                    5: (0x0003, 0x0800),
                                    6: (0x0013, 0)}))
    cases.append(base_case("state high bits preserved",
                           entries={4: (0x0003, 0x07FF)}))
    cases.append(base_case("flag bit0 only, bit1 only, neither",
                           entries={4: (0x0001, 0),
                                    5: (0x0002, 0),
                                    6: (0x0000, 0),
                                    7: (0x0003, 0)}))
    cases.append(base_case("all ones flags, done state",
                           entries={4: (0xFFFFFFFF, 0xFFFF)}))
    cases.append(base_case("all ones flags, clear state",
                           entries={4: (0xFFFFFFFF, 0)}))

    # --- full window ---------------------------------------------------------
    cases.append(
        base_case("all 50 entries eligible",
                  entries={index: (0x0003, 0) for index in range(SCAN_FIRST, SCAN_LIMIT)})
    )
    cases.append(
        base_case("all 50 entries, alternating layouts",
                  entries={
                      index: (0x0013 if index & 1 else 0x0003, 0)
                      for index in range(SCAN_FIRST, SCAN_LIMIT)
                  })
    )

    # --- coordinate-table boundaries, both layouts --------------------------
    boundary_sets = [
        {0x00: 0, 0x04: 0, 0x08: 0, 0x0C: 0, 0x10: 0, 0x14: 0, 0x18: 0},
        {0x00: -0x8000, 0x04: 0x7FFF, 0x08: -1, 0x0C: 0x7FFF,
         0x10: -0x8000, 0x14: -1, 0x18: 0x7FFF},
        {0x00: 0x7FFF, 0x04: -0x8000, 0x08: 0x7FFF, 0x0C: -0x8000,
         0x10: 0x7FFF, 0x14: -0x8000, 0x18: -0x8000},
        {0x00: -1, 0x04: -1, 0x08: -0x8000, 0x0C: -1,
         0x10: -1, 0x14: 0x7FFF, 0x18: -1},
    ]
    for index, table in enumerate(boundary_sets):
        cases.append(
            base_case(f"plain layout table boundary set {index}",
                      entries={4: (0x0003, 0)}, table=table)
        )
        cases.append(
            base_case(f"selected layout table boundary set {index}",
                      entries={4: (0x0013, 0)}, table=table)
        )

    # --- row scaling with negative t0 and t3 --------------------------------
    cases.append(
        base_case("row scaling over 50 entries",
                  entries={i: (0x0003, 0) for i in range(SCAN_FIRST, SCAN_LIMIT)},
                  table={0x00: -0x8000, 0x18: 0x7FFF})
    )
    cases.append(
        base_case("row scaling 50 selected entries",
                  entries={i: (0x0013, 0) for i in range(SCAN_FIRST, SCAN_LIMIT)},
                  table={0x0C: 0x7FFF, 0x18: -0x8000})
    )

    # --- context flag word and reload --------------------------------------
    cases.append(base_case("context flag word has other bits",
                           entries={4: (0x0003, 0)}, ctx_flags=0xFFFFFFFF))
    cases.append(base_case("context pointer swapped by 0x00240744",
                           entries={4: (0x0003, 0)}, context_swap=True))
    cases.append(base_case("context swapped with selected entry",
                           entries={4: (0x0013, 0)}, context_swap=True))

    # --- helper-time flag mutation (fresh load for the third call) ----------
    cases.append(base_case("selected bit cleared after first helper",
                           entries={4: (0x0013, 0)}, mutate_after_first=True))
    cases.append(base_case("selected bit cleared on second helper",
                           entries={4: (0x0013, 0)}, mutate_on_second=True))
    cases.append(base_case("selected bit cleared with plain entry",
                           entries={4: (0x0003, 0)}, mutate_on_second=True))

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
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls, "
              f"{len(orig['non_stack_writes'])} writes)")
    return passed


def main() -> None:
    print("Testing battle_func_00336e20 (0x00336E20)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(call relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("first_entry", "constexpr s32 kFirstEntry = 4;",
         "constexpr s32 kFirstEntry = 5;"),
        ("entry_stride", "constexpr u32 kEntryStride = 0x114;",
         "constexpr u32 kEntryStride = 0x110;"),
        ("done_bit", "constexpr u16 kEntryDone = 0x0800;",
         "constexpr u16 kEntryDone = 0x0400;"),
        ("selected_table_offset", "coordinate0 = table_s16(0x0C);",
         "coordinate0 = table_s16(0x08);"),
        ("comparator_address",
         "constexpr u32 kDistanceComparator = 0x0019D76C;",
         "constexpr u32 kDistanceComparator = 0x0019D770;"),
        ("helper_kind",
         "(entry->flags_50 & kEntrySelectedBit) != 0 ? 7 : 6,",
         "(entry->flags_50 & kEntrySelectedBit) != 0 ? 6 : 7,"),
        ("stack_value", "constexpr s32 kStackValue = 0x0D;",
         "constexpr s32 kStackValue = 0x0E;"),
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
