#!/usr/bin/env python3
"""Differential test for engine_func_001493a0 (0x001493a0) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the engine_func_001493a0 body,
resolves its direct calls (0x002C39A4 screen address and 0x002BC300 physical
translation) to deterministic stubs at the original addresses, relocates the
two compiler-generated `.rodata` tables, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and the callee-saved registers r4-r11;
  * the ordered helper call log (stub name and every register argument);
  * the descriptor page (including both type-size words, the stream size, the
    option-size word and every record slot), both type buffers, the stream
    buffer, the option block, the optional-state page and the low page used by
    the null state paths;
  * any emulated write outside the private stack and the fixture pages.

Coverage: counts 0, negative and 32-bit boundary, one and many records, both
presence classes, every tag (0x1400/0x1401/0x1402/0x1406 and unknown), every
scaling branch, the argument switch byte, all four element-value branches
(zero low word, small exponent, in-range exponent, over-range exponent, with
and without the sign bit), nibble-map spill past +0x2C and +0x20, all four
optional-state tags and both selector defaults, and every null/zero-relative
state path.  Negative controls mutate a type-header word, the absent-block
constant, the tag mapping, the option-block tag index and the option size.
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
from tools.test_leaf_003aa014 import elf_sections

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch34_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_001493a0"

FUNC_ADDR = 0x001493A0
FUNC_SIZE = 1660
FUNC_SYMBOL = "engine_func_001493a0"

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the function and both helper stubs

LOW_ADDR = 0x00000000
LOW_SIZE = 0x00001000
DESC_ADDR = 0x00710000
DESC_SIZE = 0x00040000
TYPE0_ADDR = 0x00750000
TYPE_SIZE = 0x00004000
TYPE1_ADDR = 0x00754000
STREAM_ADDR = 0x00758000
STREAM_SIZE = 0x00004000
OPTION_ADDR = 0x0075C000
OPTION_SIZE = 0x00002000
STATE_ADDR = 0x00760000
STATE_SIZE = 0x00002000
ELEM_ADDR = 0x00764000
ELEM_SIZE = 0x00004000
RODATA_ADDR = 0x00770000
CST16_ADDR = 0x00771000
RODATA_SIZE = 0x00002000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_SCREEN = 0x002C39A4
STUB_PHYS = 0x002BC300
STUB_NAMES = {STUB_SCREEN: "engine_func_002c39a4",
              STUB_PHYS: "engine_func_002bc300"}
SCREEN_RETURN = 0x00420000

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

# The compiler bakes the six-entry tag selector into `.rodata+0x3C` and the
# four option words into `.rodata.cst16` (selector order {5, 3, 8, 0}).  The
# runner patches both absolute references above.

# Optional-state tags exercised by the final section.
STATE_TAGS = (0x80000000, 0x10000000, 0x20000000, 0x40000000,
              0x00000000, 0xDEADBEEF)


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    entry = None
    for name, value in funcs.items():
        if FUNC_SYMBOL in name or FUNC_ADDR.to_bytes(4, "big").hex() in name.lower():
            entry = value
            break
    if entry is None:
        raise RuntimeError(f"{FUNC_SYMBOL} not found in {obj_file}")

    code_raw, relocs = entry
    code = bytearray(code_raw)
    sections = elf_sections(obj_file)
    rodata = sections.get(".rodata", b"")
    cst16 = sections.get(".rodata.cst16", b"")
    abs32 = []
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            if "002c39a4" in rel.symbol_name.lower():
                target = STUB_SCREEN
            elif "002bc300" in rel.symbol_name.lower():
                target = STUB_PHYS
            else:
                raise RuntimeError(f"unresolved call: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            original = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into("<I", code, rel.offset,
                             (original & 0xFF000000) |
                             (((target - pc) >> 2) & 0x00FFFFFF))
        elif rel.relocation_type == 2:
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            abs32.append(addend)
            if addend == 0x3C:
                if addend > len(rodata):
                    raise RuntimeError("tag table lies outside .rodata")
                target = RODATA_ADDR + 0x3C
            elif addend == 0:
                if len(cst16) < 16:
                    raise RuntimeError("missing .rodata.cst16 table")
                target = CST16_ADDR
            else:
                raise RuntimeError(f"unknown rodata addend 0x{addend:x}")
            struct.pack_into("<I", code, rel.offset, target)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type}")

    if sorted(abs32) != [0, 0x3C]:
        raise RuntimeError(f"unexpected rodata relocations: {abs32}")

    return bytes(code), rodata, cst16


def compile_source(src: Path, obj_name: str) -> tuple[bytes, bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / obj_name
    result = compile_tu_armv6k(src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_baseline() -> tuple[bytes, bytes, bytes]:
    return compile_source(SOURCE, "leaf_batch34_c.o")


def compile_candidate_mutant(name: str, old: str, new: str
                             ) -> tuple[bytes, bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_source(mutant_src, f"mutant_{name}.o")


# --------------------------------------------------------------------- fixtures
def fill_words(size: int, seed: int) -> bytearray:
    page = bytearray(size)
    for offset in range(0, size, 4):
        struct.pack_into("<I", page, offset,
                         0xA5A50000 | ((seed + offset) & 0xFFFF))
    return page


def put32(page: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", page, offset, value & 0xFFFFFFFF)


def build_descriptor(case: dict) -> tuple[bytes, bytes]:
    page = fill_words(DESC_SIZE, 0x0100)
    elements = fill_words(ELEM_SIZE, 0x0200)
    put32(page, 0x0C, TYPE0_ADDR)
    put32(page, 0x10, TYPE1_ADDR)
    put32(page, 0x1C, STREAM_ADDR)
    put32(page, 0x24, OPTION_ADDR)
    put32(page, 0x30, case.get("switch_byte", 0) & 0xFFFFFFFF)
    put32(page, 0x34, case.get("count", 0) & 0xFFFFFFFF)

    elem_cursor = 0x100
    records = case.get("records", [])
    for index, record in enumerate(records):
        base = 0x38 + index * 0x1C
        put32(page, base + 0x00, record.get("nibble", 0x5))
        put32(page, base + 0x04, record.get("tag", 0x1400))
        page[base + 0x08] = record.get("byte", 0) & 0xFF
        page[base + 0x09] = record.get("presence", 1) & 0xFF
        array = record.get("array")
        if array is None:
            put32(page, base + 0x0C, record.get("arg0", 0x11110000 + index))
        else:
            put32(page, base + 0x0C, ELEM_ADDR + elem_cursor)
            for word_index, word in enumerate(array):
                put32(elements, elem_cursor + 4 * word_index, word)
            elem_cursor += 4 * max(len(array), 1) + 0x10
            elements[elem_cursor - 0x10:elem_cursor] = b"\x00" * 0x10
        put32(page, base + 0x10, record.get("arg1", 0x22220000 + index))
    return bytes(page), bytes(elements)


def build_state(case: dict) -> tuple[bytes, bytes, int]:
    state_page = fill_words(STATE_SIZE, 0x0300)
    low_page = bytearray(LOW_SIZE)
    mode = case.get("state_mode", "valid")
    tag = case.get("state_tag", 0x80000000)

    # The optional header lives at STATE_ADDR (its +0x08 word is the state
    # pointer).  The state object lives at +0x100; its +0x44 field is a
    # self-relative displacement to the tag word at +0x184.
    state_object = STATE_ADDR + 0x100
    tag_offset = 0x184
    put32(state_page, tag_offset, tag)
    put32(low_page, 0x00, tag)
    put32(low_page, 0x144, tag)
    put32(state_page, 0x08, state_object)
    put32(state_page, 0x100, 0x40000001)
    put32(state_page, 0x144, tag_offset - 0x144)

    option = STATE_ADDR
    if mode == "valid":
        pass
    elif mode == "rejected":
        put32(state_page, 0x100, 0x40000000)
    elif mode == "valid_zero_relative":
        put32(state_page, 0x144, 0)
    elif mode == "null_word":
        # optional +0x08 is zero -> the state word is zero, so low[0x44] is
        # read and its displacement lands on low[0x144].
        put32(state_page, 0x08, 0)
        put32(low_page, 0x44, 0x100)
    elif mode == "null_zero_relative":
        put32(state_page, 0x08, 0)
        put32(low_page, 0x44, 0)
    elif mode == "opt_null_state":
        put32(low_page, 0x08, state_object)
        option = 0
    elif mode == "opt_null_zero":
        put32(low_page, 0x08, 0)
        put32(low_page, 0x44, 0)
        option = 0
    else:  # pragma: no cover
        raise AssertionError(f"unknown state mode {mode}")

    return bytes(state_page), bytes(low_page), option


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(LOW_ADDR, LOW_SIZE)
        self.uc.mem_map(DESC_ADDR, DESC_SIZE)
        self.uc.mem_map(TYPE0_ADDR, TYPE_SIZE)
        self.uc.mem_map(TYPE1_ADDR, TYPE_SIZE)
        self.uc.mem_map(STREAM_ADDR, STREAM_SIZE)
        self.uc.mem_map(OPTION_ADDR, OPTION_SIZE)
        self.uc.mem_map(STATE_ADDR, STATE_SIZE)
        self.uc.mem_map(ELEM_ADDR, ELEM_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub,
                begin=address, end=address,
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.call_log: list = []
        self.writes: list = []

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append((STUB_NAMES[address], r0))
        if address == STUB_SCREEN:
            uc.reg_write(arm.UC_ARM_REG_R0, SCREEN_RETURN)
        else:
            uc.reg_write(arm.UC_ARM_REG_R0,
                         (r0 ^ 0x0BADF00D) & 0xFFFFFFFF)

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def run(self, code: bytes, rodata: bytes, cst16: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.uc.mem_write(FUNC_ADDR, code)
        descriptor, elements = build_descriptor(case)
        state_page, low_page, optional = build_state(case)
        self.uc.mem_write(LOW_ADDR, bytes(low_page))
        self.uc.mem_write(DESC_ADDR, bytes(descriptor))
        self.uc.mem_write(TYPE0_ADDR, bytes(fill_words(TYPE_SIZE, 0x0400)))
        self.uc.mem_write(TYPE1_ADDR, bytes(fill_words(TYPE_SIZE, 0x0500)))
        self.uc.mem_write(STREAM_ADDR, bytes(fill_words(STREAM_SIZE, 0x0600)))
        self.uc.mem_write(OPTION_ADDR, bytes(fill_words(OPTION_SIZE, 0x0700)))
        self.uc.mem_write(STATE_ADDR, bytes(state_page))
        self.uc.mem_write(ELEM_ADDR, bytes(elements))
        self.uc.mem_write(RODATA_ADDR, rodata + b"\x00" * (RODATA_SIZE - len(rodata)))
        self.uc.mem_write(CST16_ADDR, cst16)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, DESC_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, optional)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=20_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        allowed = (
            (STACK_ADDR, STACK_ADDR + STACK_SIZE),
            (DESC_ADDR, DESC_ADDR + DESC_SIZE),
            (TYPE0_ADDR, TYPE0_ADDR + TYPE_SIZE),
            (TYPE1_ADDR, TYPE1_ADDR + TYPE_SIZE),
            (STREAM_ADDR, STREAM_ADDR + STREAM_SIZE),
            (OPTION_ADDR, OPTION_ADDR + OPTION_SIZE),
        )
        unexpected = []
        for address, size in self.writes:
            if not any(lo <= address < hi for lo, hi in allowed):
                unexpected.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "desc": bytes(self.uc.mem_read(DESC_ADDR, DESC_SIZE)),
            "type0": bytes(self.uc.mem_read(TYPE0_ADDR, TYPE_SIZE)),
            "type1": bytes(self.uc.mem_read(TYPE1_ADDR, TYPE_SIZE)),
            "stream": bytes(self.uc.mem_read(STREAM_ADDR, STREAM_SIZE)),
            "option": bytes(self.uc.mem_read(OPTION_ADDR, OPTION_SIZE)),
            "state": bytes(self.uc.mem_read(STATE_ADDR, STATE_SIZE)),
            "low": bytes(self.uc.mem_read(LOW_ADDR, LOW_SIZE)),
            "unexpected_writes": unexpected,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}: orig={orig[key]!r} cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            f"call_log:\n    orig={orig['call_log']!r}\n"
            f"    cand={cand['call_log']!r}")
    for key in ("desc", "type0", "type1", "stream", "option", "state", "low"):
        if orig[key] != cand[key]:
            first = next(
                (i for i in range(0, len(orig[key]), 4)
                 if orig[key][i:i + 4] != cand[key][i:i + 4]), None)
            problems.append(f"{key} memory differs (first word offset {first})")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}")
    return problems


def record(**overrides) -> dict:
    base = {"nibble": 0x5, "tag": 0x1400, "byte": 0, "presence": 1,
            "arg0": 0x11111111, "arg1": 0x22222222}
    base.update(overrides)
    return base


def base_case(title: str, **overrides) -> dict:
    case = {
        "name": title,
        "count": 0,
        "switch_byte": 0,
        "records": [],
        "state_mode": "valid",
        "state_tag": 0x80000000,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- counts that skip every record loop (signed test and 32-bit wrap)
    for count in (0, 0xFFFFFFFF, 0xFFFFFFFE, 0x80000000):
        cases.append(base_case(f"count 0x{count:08x}", count=count))

    # --- one present record: every tag and scaling branch
    for tag in (0x1400, 0x1401, 0x1402, 0x1406, 0x13FF, 0x1403, 0x0000):
        for byte in (0, 1, 0x7F, 0x80, 0xFF):
            cases.append(base_case(
                f"present tag 0x{tag:04x} byte 0x{byte:02x}",
                count=1,
                records=[record(tag=tag, byte=byte)],
                switch_byte=0,
            ))

    # --- argument switch byte and presence forms
    for switch in (0, 1, 0xFF, 0x100):
        cases.append(base_case(
            f"argument switch 0x{switch:08x}", count=1, switch_byte=switch,
            records=[record(tag=0x1401, arg0=0xAAAA0001, arg1=0xBBBB0002)]))
    for presence in (0x02, 0x80, 0xFF):
        cases.append(base_case(
            f"presence 0x{presence:02x}", count=1,
            records=[record(presence=presence)]))

    # --- nibble values and their neighbours
    for nibble in (0x0, 0x1, 0x7, 0x8, 0xF):
        cases.append(base_case(
            f"nibble 0x{nibble:x}", count=1,
            records=[record(nibble=nibble)]))

    # --- one absent record: element counts 0..4
    for elements in ([], [0x00000000], [0x80000000],
                     [0x00000000, 0x80000000],
                     [0x00100000, 0x20000000, 0x60000000, 0xDEADBEEF],
                     [0x20400123, 0x5F800001, 0x7FFFFFFF, 0xFFFFFFFF]):
        cases.append(base_case(
            f"absent elements {len(elements)}", count=1,
            records=[record(presence=0, byte=len(elements), array=elements)]))

    # --- every element-value branch in one four-element record
    element_sets = [
        [0x00000000, 0x80000000, 0x00100000, 0x20000000],
        [0x60000000, 0x5FC00001, 0x20400000, 0x5FBF1234],
        [0x7FFFFFFF, 0xFFFFFFFF, 0x007FFFFF, 0x00800000],
        [0x20FFFFFF, 0x5FFFFFFF, 0x21000000, 0x61000000],
    ]
    for index, elements in enumerate(element_sets):
        cases.append(base_case(
            f"element branches {index}", count=1,
            records=[record(presence=0, byte=4, array=elements)]))

    # --- mixed present/absent, several counts
    for count in (2, 3, 5, 8, 9, 16):
        records = []
        for index in range(count):
            if index % 3 == 0:
                records.append(record(presence=0, byte=0, nibble=index & 0xF))
            else:
                records.append(record(tag=(0x1400, 0x1401, 0x1402, 0x1406,
                                           0x0000)[index % 5],
                                      byte=index * 7, nibble=index & 0xF))
        cases.append(base_case(f"mixed count {count}", count=count,
                               records=records))

    # --- all absent at the nibble-map spill boundaries and at the 8-bit
    # register-shift wrap used by the +0x2C bit set.
    for count in (9, 33, 240, 256):
        records = [record(presence=0, byte=0, nibble=0xF) for _ in range(count)]
        cases.append(base_case(f"all absent count {count}", count=count,
                               records=records))

    # --- all present at the nibble-map spill boundary
    records = [record(presence=1, nibble=0xA, tag=0x1402,
                      byte=0x40 + index) for index in range(33)]
    cases.append(base_case("all present count 33", count=33, records=records))

    # --- optional-state resolution: mode x tag
    for mode in ("valid", "rejected", "valid_zero_relative", "null_word",
                 "null_zero_relative", "opt_null_state", "opt_null_zero"):
        for tag in STATE_TAGS:
            cases.append(base_case(
                f"state {mode} tag 0x{tag:08x}", count=2,
                records=[record(), record(presence=0, byte=1,
                                          array=[0x20400000])],
                state_mode=mode, state_tag=tag))

    return cases


def run_case_set(orig_code, cand_code, rodata, cst16, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, rodata, cst16, case)
        cand = Runner().run(cand_code, rodata, cst16, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
    print(f"  {passed} differential cases passed")
    return passed


def main() -> None:
    print("Testing engine_func_001493a0 (0x001493a0)...")
    orig_code = get_orig_bytes()
    cand_code, rodata, cst16 = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          f"(relocations resolved).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, rodata, cst16, cases)

    print("\nNegative controls:")
    mutants = (
        ("type_word_04", "constexpr u32 kTypeWord04 = 0x000b02b9u;",
         "constexpr u32 kTypeWord04 = 0x000b02b8u;"),
        ("absent_block", "constexpr u32 kAbsentBlockWord1 = 0x803f0232u;",
         "constexpr u32 kAbsentBlockWord1 = 0x803f0233u;"),
        ("tag_mapping", "if (relative == 5u) {",
         "if (relative == 4u) {"),
        ("tag_scale", "} else if (tag == kTagBase + 6u) {",
         "} else if (tag == kTagBase + 5u) {"),
        ("option_index", "const u32 shift = (handled + 0x10u) & 0xffu;",
         "const u32 shift = (handled + 0x11u) & 0xffu;"),
        ("option_size", "constexpr u32 kOptionSize = 0x78u;",
         "constexpr u32 kOptionSize = 0x79u;"),
    )
    for name, old, new in mutants:
        mutant_code, mutant_rodata, mutant_cst16 = compile_candidate_mutant(
            name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, rodata, cst16, case)
            bad = Runner().run(mutant_code, mutant_rodata, mutant_cst16, case)
            if compare(orig, bad):
                detected = True
                break
        if not detected:
            print(f"  [FAIL] mutant {name} was not detected")
            raise SystemExit(1)
        print(f"  [PASS] mutant {name} detected")

    print(f"\nAll {passed} differential test cases and "
          f"{len(mutants)} negative controls PASSED!")


if __name__ == "__main__":
    main()
