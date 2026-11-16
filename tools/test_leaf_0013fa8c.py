#!/usr/bin/env python3
"""Differential test for func_0013fa8c (0x0013fa8c) using Unicorn ARM.

Compiles ``src/engine/leaf_batch34_c.cpp``, extracts the ``func_0013fa8c`` body
and runs it against the pinned original (``extracted/exefs/code.bin``) in two
separate Unicorn machines with identical fixtures.

The routine has no direct or indirect calls; its observable behaviour is the
returned byte size, the words it writes through the arena cursor and the cursor
advance itself.  The comparison therefore covers:

  * return ``r0``, continuation PC, final SP and callee-saved ``r4``-``r11``;
  * the full global-arena page, descriptor page, object page, destination page
    and caller arena page (sentinel-filled, so untouched bytes are compared);
  * every emulated write address (must stay inside the fixture pages or the
    private stack).

Coverage: signed entry counts (zero, negative, positive), flag bit 0 (count
only), bit 1 (repeat count) and unrelated flag bits, repeat counts of 0/1/15/
16/31/32/33/40 and negative repeats (32-bit wrap of the running total), the ARM
variable-shift mask at 32+, pair indices crossing the 16-bit truncation, the
six-word header and one six-word block per remaining unit, arena allocations
that fit exactly, fall one byte short, are already past the limit, and the
shared global arena fallback (fit, exact fit, rejected), zero-offset cursors and
negative self-relative displacements.  The large 21,700-entry case exercises
the pair-word ``uxth`` wrap and the full block loop.

Negative controls mutate the pair base, the first header word, the limit
comparison, the repeat flag and the block word; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_0013fa8c"

FUNC_ADDR = 0x0013FA8C
FUNC_SIZE = 524

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00100000
GLOBAL_ADDR = 0x00460000  # holds the shared arena pointers below
GLOBAL_SIZE = 0x00010000
DESC_ADDR = 0x00700000
DESC_SIZE = 0x00020000
OBJ_ADDR = 0x00720000
OBJ_SIZE = 0x00010000
DST_ADDR = 0x00740000
DST_SIZE = 0x001C0000
ARENA_ADDR = 0x00900000
ARENA_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

GLOBAL_CURSOR = 0x004652A0
GLOBAL_LIMIT = 0x004652A4

DESC_COUNT_OFF = 0x38
DESC_ANCHOR_OFF = 0x3C
DEFAULT_ARRAY_OFF = 0x80
DESC_FILL = 0xCC

OBJ_STRIDE = 0x40
OBJ_FLAGS_OFF = 0x08
OBJ_REPEAT_OFF = 0x28

ARENA_CURSOR_OFF = 0x08
ARENA_LIMIT_OFF = 0x04

DEFAULT_CURSOR = 0x200
DEFAULT_LIMIT = DST_SIZE - 0x40

HEADER_WORDS = 6

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

PAGE_NAMES = ("globals", "desc", "obj", "dst", "arena")


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0013fa8c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"func_0013fa8c not found in {obj_file}: {sorted(funcs)}"
        )
    code_raw, relocs = candidate
    if relocs:
        raise RuntimeError(
            "unexpected relocations in func_0013fa8c: "
            f"{[(rel.offset, rel.relocation_type, rel.symbol_name) for rel in relocs]}"
        )
    return bytes(code_raw)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    code = relocate_candidate(obj_file)
    if len(code) > FUNC_SIZE:
        raise RuntimeError(
            f"candidate is {len(code)} bytes, larger than the {FUNC_SIZE}-byte slot"
        )
    return code


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
    code = relocate_candidate(obj_file)
    if len(code) > FUNC_SIZE:
        raise RuntimeError(f"mutant {name} does not fit the {FUNC_SIZE}-byte slot")
    return code


# --------------------------------------------------------------------- fixtures
def build_fixtures(case: dict) -> dict[str, bytes]:
    """Builds the five fixture pages for one case (same bytes for both runs)."""
    entries = [(flags & 0xFFFFFFFF, repeat & 0xFFFFFFFF)
               for flags, repeat in case.get("entries", ())]
    array_off = case.get("array_offset", DEFAULT_ARRAY_OFF)
    obj_base = case.get("obj_base", OBJ_ADDR)

    desc = bytearray(bytes([DESC_FILL]) * DESC_SIZE)
    obj_page = bytearray(b"\xA5" * OBJ_SIZE)

    # Distinct (flags, repeat) pairs share one object record.
    object_addresses: dict[tuple[int, int], int] = {}
    for key in entries:
        if key not in object_addresses:
            object_addresses[key] = obj_base + len(object_addresses) * OBJ_STRIDE

    object_bytes = bytearray(b"\xA5" * (max(1, len(object_addresses)) * OBJ_STRIDE))
    for (flags, repeat), address in object_addresses.items():
        off = address - obj_base
        object_bytes[off:off + 4] = b"\x5A\xA5\x3C\xC3"
        struct.pack_into("<I", object_bytes, off + OBJ_FLAGS_OFF, flags)
        struct.pack_into("<I", object_bytes, off + OBJ_REPEAT_OFF, repeat)

    if obj_base == OBJ_ADDR:
        obj_page[:len(object_bytes)] = object_bytes
    else:
        start = obj_base - DESC_ADDR
        if start < 0 or start + len(object_bytes) > DESC_SIZE:
            raise RuntimeError("object block outside the descriptor page")
        desc[start:start + len(object_bytes)] = object_bytes
        if start < array_off + 4 * len(entries) and array_off < start + len(object_bytes):
            raise RuntimeError("object block overlaps the element array")

    for index, key in enumerate(entries):
        slot_address = DESC_ADDR + array_off + 4 * index
        delta = (object_addresses[key] - slot_address) & 0xFFFFFFFF
        struct.pack_into("<I", desc, array_off + 4 * index, delta)
    if array_off + 4 * len(entries) > DESC_SIZE:
        raise RuntimeError("element array outside the descriptor page")

    struct.pack_into("<I", desc, DESC_COUNT_OFF,
                     case.get("count", len(entries)) & 0xFFFFFFFF)
    anchor = case.get("array_delta")
    if anchor is None:
        anchor = (array_off - DESC_ANCHOR_OFF) & 0xFFFFFFFF
    struct.pack_into("<I", desc, DESC_ANCHOR_OFF, anchor & 0xFFFFFFFF)

    arena = bytearray(b"\x5A" * ARENA_SIZE)
    cursor = case.get("cursor", DEFAULT_CURSOR)
    limit = case.get("limit", DEFAULT_LIMIT)
    struct.pack_into("<I", arena, ARENA_CURSOR_OFF,
                     0 if cursor is None else (DST_ADDR + cursor) & 0xFFFFFFFF)
    struct.pack_into("<I", arena, ARENA_LIMIT_OFF, (DST_ADDR + limit) & 0xFFFFFFFF)

    globals_page = bytearray(b"\x77" * GLOBAL_SIZE)
    global_cursor = case.get("global_cursor", DST_ADDR + 0x100)
    global_limit = case.get("global_limit", DST_ADDR + DEFAULT_LIMIT)
    struct.pack_into("<I", globals_page, GLOBAL_CURSOR - GLOBAL_ADDR,
                     global_cursor & 0xFFFFFFFF)
    struct.pack_into("<I", globals_page, GLOBAL_LIMIT - GLOBAL_ADDR,
                     global_limit & 0xFFFFFFFF)

    dst = bytearray((b"\xA5\x5A" * ((DST_SIZE + 1) // 2))[:DST_SIZE])

    return {
        "globals": bytes(globals_page),
        "desc": bytes(desc),
        "obj": bytes(obj_page),
        "dst": bytes(dst),
        "arena": bytes(arena),
    }


class LeafRunner:
    """One Unicorn ARM machine with the pinned-original or candidate bytes."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(DESC_ADDR, DESC_SIZE)
        self.uc.mem_map(OBJ_ADDR, OBJ_SIZE)
        self.uc.mem_map(DST_ADDR, DST_SIZE)
        self.uc.mem_map(ARENA_ADDR, ARENA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.writes: list[tuple[int, int]] = []

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def run(self, code: bytes, case: dict) -> dict:
        pages = build_fixtures(case)
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(GLOBAL_ADDR, pages["globals"])
        self.uc.mem_write(DESC_ADDR, pages["desc"])
        self.uc.mem_write(OBJ_ADDR, pages["obj"])
        self.uc.mem_write(DST_ADDR, pages["dst"])
        self.uc.mem_write(ARENA_ADDR, pages["arena"])
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, ARENA_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, DESC_ADDR)
        # r2/r3 are forward-compatible junk: the routine must not read them.
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0xF0000002)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0xF0000003)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=30_000_000)
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
            "pages": {
                "globals": bytes(self.uc.mem_read(GLOBAL_ADDR, GLOBAL_SIZE)),
                "desc": bytes(self.uc.mem_read(DESC_ADDR, DESC_SIZE)),
                "obj": bytes(self.uc.mem_read(OBJ_ADDR, OBJ_SIZE)),
                "dst": bytes(self.uc.mem_read(DST_ADDR, DST_SIZE)),
                "arena": bytes(self.uc.mem_read(ARENA_ADDR, ARENA_SIZE)),
            },
            "writes": list(self.writes),
        }


WRITE_RANGES = (
    (GLOBAL_ADDR, GLOBAL_SIZE),
    (DESC_ADDR, DESC_SIZE),
    (OBJ_ADDR, OBJ_SIZE),
    (DST_ADDR, DST_SIZE),
    (ARENA_ADDR, ARENA_SIZE),
    (STACK_ADDR, STACK_SIZE),
)


def in_write_ranges(address: int) -> bool:
    return any(base <= address < base + size for base, size in WRITE_RANGES)


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp"):
        if orig[key] != cand[key]:
            problems.append(f"{key}: orig=0x{orig[key]:08x} cand=0x{cand[key]:08x}")
    if orig["callee_saved"] != cand["callee_saved"]:
        problems.append(
            "callee_saved:\n    orig=" + repr(orig["callee_saved"])
            + "\n    cand=" + repr(cand["callee_saved"])
        )
    for name in PAGE_NAMES:
        left = orig["pages"][name]
        right = cand["pages"][name]
        if left != right:
            first = next(i for i, (a, b) in enumerate(zip(left, right)) if a != b)
            problems.append(
                f"{name} page differs at +0x{first:x}: "
                f"orig={left[first:first + 16].hex()} cand={right[first:first + 16].hex()}"
            )
    for address, size in cand["writes"]:
        if not in_write_ranges(address):
            problems.append(f"candidate wrote outside the fixtures at 0x{address:08x}")
    for address, size in orig["writes"]:
        if not in_write_ranges(address):
            problems.append(f"original wrote outside the fixtures at 0x{address:08x}")
    return problems


# ------------------------------------------------------------------------ cases
def make_cases() -> list[dict]:
    cases: list[dict] = []

    cases.append({"name": "empty descriptor, arena fits", "entries": []})
    cases.append({"name": "negative entry count", "entries": [], "count": -1})
    cases.append({"name": "zero entry count with array present",
                  "entries": [(0, 0)], "count": 0})
    cases.append({"name": "single plain entry", "entries": [(0, 0)]})
    cases.append({"name": "single skip entry (bit 0)", "entries": [(1, 0)]})
    cases.append({"name": "bit 0 wins over bit 1", "entries": [(3, 7)]})
    cases.append({"name": "single repeat entry, repeat 1", "entries": [(2, 1)]})
    cases.append({"name": "single repeat entry, repeat 2", "entries": [(2, 2)]})
    cases.append({"name": "single repeat entry, repeat 3", "entries": [(2, 3)]})
    cases.append({"name": "repeat count zero", "entries": [(2, 0)]})
    cases.append({"name": "unrelated flag bits are plain pairs",
                  "entries": [(0x10, 0), (0x80000000, 0)]})
    cases.append({"name": "all bits set skips", "entries": [(0xFFFFFFFF, 9)]})
    cases.append({"name": "top bits with bit 1", "entries": [(0xFFFFFFFE, 2)]})
    cases.append({"name": "mixed flags",
                  "entries": [(1, 0), (0, 0), (2, 2), (2, 0), (0x10, 0)]})
    cases.append({"name": "mixed flags with skip between pairs",
                  "entries": [(2, 1), (1, 0xFFFFFFFF), (0, 0), (2, 4)]})

    for repeat in (15, 16, 31, 32, 33, 40):
        cases.append({"name": f"shift boundary repeat {repeat}",
                      "entries": [(2, repeat)]})

    cases.append({"name": "negative repeat", "entries": [(2, -1)]})
    cases.append({"name": "negative repeat wraps total to zero",
                  "entries": [(0, 0), (2, -1)]})
    cases.append({"name": "negative repeat wraps to small total",
                  "entries": [(2, -2), (0, 0), (0, 0)]})

    cases.append({"name": "arena exact fit", "entries": [],
                  "limit": DEFAULT_CURSOR + 4 * HEADER_WORDS})
    cases.append({"name": "arena one byte short", "entries": [],
                  "limit": DEFAULT_CURSOR + 4 * HEADER_WORDS - 1})
    cases.append({"name": "arena already past the limit", "entries": [],
                  "limit": DEFAULT_CURSOR - 1})
    cases.append({"name": "arena cursor at page base", "entries": [],
                  "cursor": 0})
    cases.append({"name": "arena limit at the top of the address space",
                  "entries": [], "limit": 0xFFFFFFFF - DST_ADDR})
    cases.append({"name": "arena rejected after pairs and blocks",
                  "entries": [(2, 2)], "limit": DEFAULT_CURSOR + 4 * 14 - 1})

    cases.append({"name": "global arena fallback fits", "entries": [],
                  "cursor": None,
                  "global_cursor": DST_ADDR + 0x100,
                  "global_limit": DST_ADDR + 0x1000})
    cases.append({"name": "global arena fallback exact fit", "entries": [],
                  "cursor": None,
                  "global_cursor": DST_ADDR + 0x100,
                  "global_limit": DST_ADDR + 0x100 + 4 * HEADER_WORDS})
    cases.append({"name": "global arena fallback rejected", "entries": [],
                  "cursor": None,
                  "global_cursor": DST_ADDR + 0x100,
                  "global_limit": DST_ADDR + 0x100 + 4 * HEADER_WORDS - 1})
    cases.append({"name": "global arena rejected after pairs and blocks",
                  "entries": [(2, 2)], "cursor": None,
                  "global_cursor": DST_ADDR + 0x100,
                  "global_limit": DST_ADDR + 0x100 + 4 * 14 - 1})

    cases.append({"name": "objects below the array (negative delta)",
                  "entries": [(0, 0), (2, 3)], "array_offset": 0x1000,
                  "obj_base": DESC_ADDR + 0x400})

    huge_entries = [(0, 0)] * 21700
    cases.append({"name": "21700 plain entries (pair-word wrap)", "entries":
                  huge_entries, "cursor": 0x200,
                  "limit": DST_SIZE - 0x40})

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = LeafRunner().run(orig_code, case)
        cand = LeafRunner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        size = orig["ret"]
        print(f"  [PASS] {case['name']}  (size={size}, "
              f"writes={len(orig['writes'])})")
    return passed


def main() -> None:
    print("Testing func_0013fa8c (0x0013fa8c)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          "(no relocations).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        ("pair_base", "constexpr u32 kPairWordBase = 0x00000205;",
         "constexpr u32 kPairWordBase = 0x00000204;"),
        ("header_word0", "constexpr u32 kHeaderWord0 = 0x76543210;",
         "constexpr u32 kHeaderWord0 = 0x76543211;"),
        ("limit_compare", "if (cursor + size <= limit) {",
         "if (cursor + size < limit) {"),
        ("repeat_flag", "constexpr u32 kFlagRepeat = 0x02;",
         "constexpr u32 kFlagRepeat = 0x04;"),
        ("block_word1", "constexpr u32 kBlockWord1 = 0x803f0232;",
         "constexpr u32 kBlockWord1 = 0x803f0233;"),
    )
    for name, old, new in mutants:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = LeafRunner().run(orig_code, case)
            bad = LeafRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
