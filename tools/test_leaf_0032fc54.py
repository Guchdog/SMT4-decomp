#!/usr/bin/env python3
"""Differential test for func_0032fc54 (0x0032fc54) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts func_0032fc54, and runs the
pinned original (extracted/exefs/code.bin) against the candidate in separate
Unicorn machines with identical fixtures.

The function issues no direct calls: it reads six global function-pointer slots
and dispatches through them (`ldr/ldr/blx`).  The harness models that exactly by
placing deterministic stubs at the six pinned slot targets, filling the slot
words with those targets, and optionally remapping a slot to an alternate stub
(the "indirect target" control).  The stubs log the target address and the
seven-word descriptor read through r0, then return a garbage value in r0 so any
use of the renderer result would show up as a divergence.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log: target address, all seven descriptor words, and
    whether r0 pointed into the private stack;
  * the 0x38-byte request block, destination page, 0x40B828 byte-table page,
    slot/stub page and guard page (must be unmodified);
  * any emulated write outside the private stack.

Coverage: all four error returns and their precedence, both index bounds with
wrap-around values, both flag bits, zero/non-zero table-byte pairs for each
index, every size-class boundary (0x00, 0x01, 0x100, 0x101, 0x200, 0x201, 0x400,
0x401, 0xFFFFFFFF), mode 0/1/2/0xFFFFFFFF, odd/even shift inputs, all six slots,
and slot remapping.  Negative controls mutate a boundary, a bound, both flag
bits, a slot address, a return code, the halving shift, the second descriptor
pair, the table row stride and the mode gate.
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
OUT_DIR = ROOT / "build/test_leaf_0032fc54"

FUNC_ADDR = 0x0032FC54
FUNC_SIZE = 672

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers 0x0032FC54
PLACE_ADDR = 0x00160000  # slot words and stub targets
PLACE_SIZE = 0x00010000
TABLE_ADDR = 0x0040B000  # pinned page containing the table at 0x0040B828
TABLE_SIZE = 0x00001000
REQUEST_ADDR = 0x00710000
REQUEST_SIZE = 0x00001000
DEST_ADDR = 0x00720000
DEST_SIZE = 0x00001000
GUARD_ADDR = 0x00730000
GUARD_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
REQUEST_SIZE_BYTES = 0x38

# Slot words read by the original literal pool.  The pinned image contents are
# the six renderers below.
SLOT_SMALL_FIRST = 0x001672A4
SLOT_SMALL_NEXT = 0x001672A8
SLOT_MEDIUM_FIRST = 0x0016B01C
SLOT_MEDIUM_NEXT = 0x0016B020
SLOT_LARGE_FIRST = 0x0016352C
SLOT_LARGE_NEXT = 0x00163530

TARGET_SMALL_FIRST = 0x00167244
TARGET_SMALL_NEXT = 0x00167274
TARGET_MEDIUM_FIRST = 0x0016AFBC
TARGET_MEDIUM_NEXT = 0x0016AFEC
TARGET_LARGE_FIRST = 0x001634CC
TARGET_LARGE_NEXT = 0x001634FC

DEFAULT_SLOTS = {
    SLOT_SMALL_FIRST: TARGET_SMALL_FIRST,
    SLOT_SMALL_NEXT: TARGET_SMALL_NEXT,
    SLOT_MEDIUM_FIRST: TARGET_MEDIUM_FIRST,
    SLOT_MEDIUM_NEXT: TARGET_MEDIUM_NEXT,
    SLOT_LARGE_FIRST: TARGET_LARGE_FIRST,
    SLOT_LARGE_NEXT: TARGET_LARGE_NEXT,
}

TARGET_NAMES = {
    TARGET_SMALL_FIRST: "func_00167244",
    TARGET_SMALL_NEXT: "func_00167274",
    TARGET_MEDIUM_FIRST: "func_0016afbc",
    TARGET_MEDIUM_NEXT: "func_0016afec",
    TARGET_LARGE_FIRST: "func_001634cc",
    TARGET_LARGE_NEXT: "func_001634fc",
}

# Alternate targets used to prove the dispatch really follows the slot word.
ALT_BASE = 0x00168000
ALT_TARGETS = [ALT_BASE + 0x40 * index for index in range(6)]
for index, address in enumerate(ALT_TARGETS):
    TARGET_NAMES[address] = f"alt_target_{index}"

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

# Table rows are 0x25 bytes each, indexed by the raw request index.  The page is
# copied verbatim from the pinned image.
TABLE_PAGE_BASE = 0x0040B000


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def get_table_page() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(TABLE_PAGE_BASE - 0x00100000)
        return f.read(TABLE_SIZE)


def extract_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0032fc54" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"func_0032fc54 not found in {obj_file}: {sorted(funcs)}")
    code, relocs = candidate
    if relocs:
        raise RuntimeError(
            "unexpected relocations in func_0032fc54: "
            f"{[(r.offset, r.relocation_type, r.symbol_name) for r in relocs]}"
        )
    return code


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return extract_candidate(obj_file)


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
    return extract_candidate(obj_file)


def build_request(case: dict) -> bytes:
    page = bytearray(REQUEST_SIZE)
    values = (
        case.get("word_00", 0x11111111),
        case.get("word_04", 0x22222222),
        case.get("word_08", 0x33333333),
        case.get("word_0C", DEST_ADDR + 0x010),
        case.get("word_10", DEST_ADDR + 0x400),
        case.get("word_14", DEST_ADDR + 0x800),
        case.get("word_18", 0x12345679),
        case.get("word_1C", 0xFFFFFFFE),
        case.get("extent", 0x100),
        case.get("extent", 0x100),
        case.get("index_first", 0x14),
        case.get("index_second", 0x24),
        case.get("flags", 0),
        case.get("mode", 1),
    )
    if "extent_second" in case:
        values = values[:9] + (case["extent_second"],) + values[10:]
    struct.pack_into("<14I", page, 0, *[value & 0xFFFFFFFF for value in values])
    return bytes(page)


class FC54Runner:
    """One Unicorn machine with deterministic indirect-call stubs."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(PLACE_ADDR, PLACE_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
        self.uc.mem_map(REQUEST_ADDR, REQUEST_SIZE)
        self.uc.mem_map(DEST_ADDR, DEST_SIZE)
        self.uc.mem_map(GUARD_ADDR, GUARD_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in TARGET_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.slot_values: dict = dict(DEFAULT_SLOTS)
        self.table_page = get_table_page()

    # ------------------------------------------------------------------ stubs
    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        descriptor = struct.unpack("<7I", uc.mem_read(r0, 0x1C))
        self.call_log.append(
            (
                TARGET_NAMES[address],
                descriptor,
                STACK_ADDR <= r0 < STACK_ADDR + STACK_SIZE,
            )
        )
        # The original discards every renderer result; a candidate that used it
        # would diverge from this sentinel.
        uc.reg_write(arm.UC_ARM_REG_R0, 0xDEAD0000 | (address & 0xFFFF))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.slot_values = dict(DEFAULT_SLOTS)
        for slot, target in case.get("slot_overrides", {}).items():
            self.slot_values[slot] = target

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(REQUEST_ADDR, build_request(case))
        self.uc.mem_write(DEST_ADDR, b"\x5A" * DEST_SIZE)
        self.uc.mem_write(TABLE_ADDR, self.table_page)
        self.uc.mem_write(GUARD_ADDR, b"\xA5" * GUARD_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        place = bytearray(PLACE_SIZE)
        for address in TARGET_NAMES:
            offset = address - PLACE_ADDR
            struct.pack_into("<I", place, offset, 0xE12FFF1E)  # bx lr
        for slot, target in self.slot_values.items():
            struct.pack_into("<I", place, slot - PLACE_ADDR, target)
        self.uc.mem_write(PLACE_ADDR, bytes(place))

        self.writes = []
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, REQUEST_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x0BADF00D)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x0BADF00E)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x0BADF00F)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not in_stack:
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "fixtures": {
                "request": bytes(self.uc.mem_read(REQUEST_ADDR, REQUEST_SIZE_BYTES)),
                "dest": bytes(self.uc.mem_read(DEST_ADDR, DEST_SIZE)),
                "table": bytes(self.uc.mem_read(TABLE_ADDR, TABLE_SIZE)),
                "place": bytes(self.uc.mem_read(PLACE_ADDR, PLACE_SIZE)),
                "guard": bytes(self.uc.mem_read(GUARD_ADDR, GUARD_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"]) + "\n    cand="
            + repr(cand["call_log"])
        )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "word_00": 0x11111111,
        "word_04": 0x22222222,
        "word_08": 0x33333333,
        "word_0C": DEST_ADDR + 0x010,
        "word_10": DEST_ADDR + 0x400,
        "word_14": DEST_ADDR + 0x800,
        "word_18": 0x12345679,
        "word_1C": 0xFFFFFFFE,
        "extent": 0x100,
        "index_first": 0x14,
        "index_second": 0x24,
        "flags": 0,
        "mode": 1,
    }
    case.update(overrides)
    return case


def expected_target_names(case: dict) -> list[str]:
    slots = dict(DEFAULT_SLOTS)
    slots.update(case.get("slot_overrides", {}))
    extent = case.get("extent", 0x100)
    if extent <= 0x100:
        first, nxt = slots[SLOT_SMALL_FIRST], slots[SLOT_SMALL_NEXT]
    elif extent <= 0x200:
        first, nxt = slots[SLOT_MEDIUM_FIRST], slots[SLOT_MEDIUM_NEXT]
    else:
        first, nxt = slots[SLOT_LARGE_FIRST], slots[SLOT_LARGE_NEXT]

    flags = case.get("flags", 0)
    mode = case.get("mode", 1)
    first_index = case.get("index_first", 0x14)
    second_index = case.get("index_second", 0x24)

    if mode == 0 or not (0x0C <= first_index <= 0x30) or not (
        0x0C <= second_index <= 0x30
    ):
        return []

    def byte_pairs(index: int) -> tuple[int, int]:
        table = get_table_page()
        offset = 0x0040B828 - TABLE_PAGE_BASE + index
        return table[offset], table[offset + 0x25]

    result: list[int] = []
    if mode != 1:
        return result
    if extent > 0x400:
        return result
    primary_a, primary_b = byte_pairs(first_index)
    secondary_a, secondary_b = byte_pairs(second_index)
    if flags & 1 and primary_a != 0 and primary_b != 0:
        result.append(first)
    if flags & 2 and secondary_a != 0 and secondary_b != 0:
        result.append(nxt)
        result.append(nxt)
    return [TARGET_NAMES[target] for target in result]


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- error returns and precedence -----------------------------------
    cases.append(base_case("mode 0 is not ready", mode=0))
    cases.append(
        base_case(
            "mode 0 precedes extent and index checks",
            mode=0,
            extent=0x200,
            extent_second=0x201,
            index_first=0x0B,
            index_second=0x40,
        )
    )
    cases.append(base_case("mode 2 is not the ready value", mode=2))
    cases.append(
        base_case("mode 0xFFFFFFFF is not the ready value", mode=0xFFFFFFFF)
    )
    cases.append(
        base_case("extent mismatch", extent=0x100, extent_second=0x101)
    )
    cases.append(
        base_case(
            "extent mismatch signed boundary",
            extent=0xFFFFFFFF,
            extent_second=0x7FFFFFFF,
        )
    )
    cases.append(base_case("extent mismatch precedes index checks",
                           extent=0x100, extent_second=0x100 + 1,
                           index_first=0x0B, index_second=0x40))
    for index in (0x0B, 0x31, 0xFFFFFFFF, 0x8000000B, 0x0000000B):
        cases.append(base_case(f"first index 0x{index:08x} rejected",
                               index_first=index))
    for index in (0x0B, 0x31, 0xFFFFFFFF, 0x8000000B, 0x0000000B):
        cases.append(base_case(f"second index 0x{index:08x} rejected",
                               index_second=index, flags=3))
    cases.append(base_case("both indices invalid", index_first=0x31,
                           index_second=0x31))

    # --- flag combinations and table-byte gates --------------------------
    cases.append(base_case("flags 0 makes no calls", flags=0, extent=0x100))
    cases.append(base_case("flags 1 primary draw", flags=1, extent=0x100))
    cases.append(base_case("flags 2 secondary pair", flags=2, extent=0x200))
    cases.append(base_case("flags 3 all three draws", flags=3, extent=0x400))
    cases.append(base_case("flags 0xFFFFFFFF all three draws",
                           flags=0xFFFFFFFF, extent=0x100))
    cases.append(base_case("flags 0x80000003 only bits 0 and 1 count",
                           flags=0x80000003, extent=0x100))
    cases.append(base_case("flags 1 zero row pair", flags=1, index_first=0x0D))
    cases.append(base_case("flags 3 second index zero row pair", flags=3,
                           index_second=0x0D))
    cases.append(base_case("flags 3 first index zero row pair", flags=3,
                           index_first=0x0D))
    cases.append(base_case("flags 2 both zero row pairs", flags=2,
                           index_first=0x0D, index_second=0x0D))
    cases.append(base_case("flags 3 zero rows plus oversized extent", flags=3,
                           index_first=0x0D, index_second=0x0D, extent=0x401))
    cases.append(base_case("flags 1 zero rows plus oversized extent", flags=1,
                           index_first=0x0D, extent=0x401))
    cases.append(base_case("flags 2 zero rows plus oversized extent", flags=2,
                           index_second=0x0D, extent=0x401))
    cases.append(base_case("flags 3 secondary oversized extent", flags=3,
                           index_first=0x0D, extent=0x401))
    cases.append(base_case("flags 3 primary oversized extent", flags=3,
                           index_second=0x0D, extent=0x401))

    # --- size classes and boundaries -------------------------------------
    for extent in (0x000, 0x001, 0x0FF, 0x100, 0x101, 0x1FF, 0x200, 0x201,
                   0x3FF, 0x400, 0x401, 0x7FFFFFFF, 0xFFFFFFFF):
        cases.append(base_case(f"flags 3 extent 0x{extent:08x}", flags=3,
                               extent=extent))
    for extent in (0x100, 0x101, 0x200, 0x201, 0x400, 0x401):
        cases.append(base_case(f"flags 1 extent 0x{extent:08x}", flags=1,
                               extent=extent))
        cases.append(base_case(f"flags 2 extent 0x{extent:08x}", flags=2,
                               extent=extent))

    # --- mode gate without extent error ----------------------------------
    cases.append(base_case("mode 2 suppresses calls", flags=3, mode=2))
    cases.append(base_case("mode 0xFFFFFFFF suppresses calls", flags=3,
                           mode=0xFFFFFFFF))
    cases.append(base_case("mode 2 oversized extent still errors", flags=3,
                           mode=2, extent=0x401))
    cases.append(base_case("mode 2 both flags and zero rows", flags=3, mode=2,
                           index_first=0x0D, index_second=0x0D))

    # --- field wiring and shift boundaries -------------------------------
    for word_18, word_1C in (
        (0x00000000, 0x00000000),
        (0x00000001, 0x00000001),
        (0xFFFFFFFF, 0xFFFFFFFF),
        (0x80000001, 0x7FFFFFFF),
        (0x12345679, 0xFFFFFFFE),
    ):
        cases.append(base_case(f"shift input 0x{word_18:08x}/0x{word_1C:08x}",
                               flags=3, word_18=word_18, word_1C=word_1C))
    for index_first, index_second in ((0x0C, 0x0C), (0x13, 0x14), (0x14, 0x13),
                                      (0x30, 0x30), (0x1F, 0x2F)):
        cases.append(base_case(
            f"indices 0x{index_first:02x}/0x{index_second:02x}", flags=3,
            index_first=index_first, index_second=index_second))
    cases.append(base_case("distinct descriptor values", flags=3,
                           word_00=0xA0000001, word_04=0xA0000002,
                           word_08=0xA0000003, word_0C=0xA0000004,
                           word_10=0xA0000005, word_14=0xA0000006))

    # --- indirect-target controls ----------------------------------------
    for index, slot in enumerate(DEFAULT_SLOTS):
        cases.append(base_case(
            f"slot 0x{slot:08x} remapped", flags=3, extent=0x100,
            slot_overrides={slot: ALT_TARGETS[index]}))
    cases.append(base_case(
        "all six slots remapped", flags=3, extent=0x100,
        slot_overrides={slot: ALT_TARGETS[index]
                        for index, slot in enumerate(DEFAULT_SLOTS)}))
    cases.append(base_case(
        "medium first slot remapped", flags=3, extent=0x200,
        slot_overrides={SLOT_MEDIUM_FIRST: ALT_TARGETS[2]}))
    cases.append(base_case(
        "large next slot remapped", flags=3, extent=0x400,
        slot_overrides={SLOT_LARGE_NEXT: ALT_TARGETS[5]}))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = FC54Runner().run(orig_code, case)
        cand = FC54Runner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)

        expected_names = expected_target_names(case)
        actual_names = [entry[0] for entry in orig["call_log"]]
        if actual_names != expected_names:
            print(f"  [FAIL] {case['name']}")
            print(f"    expected targets {expected_names}, got {actual_names}")
            raise SystemExit(1)
        if any(not entry[2] for entry in orig["call_log"]):
            print(f"  [FAIL] {case['name']}: descriptor not on the stack")
            raise SystemExit(1)

        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing func_0032fc54 (0x0032fc54)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(no relocations)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutations = (
        ("extent_small_max", "constexpr u32 kExtentSmallMax = 0x100;",
         "constexpr u32 kExtentSmallMax = 0x0FF;"),
        ("index_min", "constexpr u32 kIndexMin = 0x0C;",
         "constexpr u32 kIndexMin = 0x0B;"),
        ("flag_primary", "constexpr u32 kFlagPrimary = 1;",
         "constexpr u32 kFlagPrimary = 4;"),
        ("flag_secondary", "constexpr u32 kFlagSecondary = 2;",
         "constexpr u32 kFlagSecondary = 8;"),
        ("slot_small_next", "constexpr u32 kSlotSmallNext = 0x001672A8;",
         "constexpr u32 kSlotSmallNext = 0x001672A4;"),
        ("error_too_large", "constexpr s32 kErrorExtentTooLarge = -5;",
         "constexpr s32 kErrorExtentTooLarge = -4;"),
        ("halve_shift", "args.word_08 = request->word_18 >> 1;",
         "args.word_08 = request->word_18 >> 2;"),
        ("third_descriptor_word0", "args.word_00 = request->word_08;",
         "args.word_00 = request->word_04;"),
        ("table_row_stride", "constexpr u32 kTableRowStride = 0x25;",
         "constexpr u32 kTableRowStride = 0x24;"),
        ("mode_ready", "constexpr u32 kModeReady = 1;",
         "constexpr u32 kModeReady = 2;"),
    )
    for name, old, new in mutations:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = FC54Runner().run(orig_code, case)
            bad = FC54Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
