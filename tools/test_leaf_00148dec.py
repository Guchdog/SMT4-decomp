#!/usr/bin/env python3
"""Differential test for engine_func_00148dec (0x00148dec) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the engine_func_00148dec body,
resolves its single direct call (0x002C3290, strlen) to a deterministic stub,
and runs the pinned original (extracted/exefs/code.bin) against the candidate in
separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0 (the final maximum alignment), continuation PC, final SP and the
    callee-saved registers r4-r11;
  * the ordered 0x002C3290 call log (the exact name pointer, including null);
  * the full layout-cursor and type-record pages;
  * any emulated write outside the private stack and the cursor page.

Coverage: every header-tag case (including unknown and signed-boundary tags),
all three pointer-child tag maps, the +0x0C sub-record counts and inner tag, the
name length (including the null name), cursor offsets/alignments/maxima that
force four-byte alignment and 32-bit wrap, and mixed nested cases.  Negative
controls mutate a header size, the alignment mask, the table header, a child
size and an inner size; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_00148dec"

FUNC_ADDR = 0x00148DEC
FUNC_SIZE = 1208
FUNC_SYMBOL = "engine_func_00148dec"

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the function and the 0x002C3290 stub
CTX_ADDR = 0x00710000
CTX_SIZE = 0x00001000
TYPE_ADDR = 0x00720000
TYPE_SIZE = 0x00010000
SLOT_ADDR = 0x00730000
SLOT_SIZE = 0x00001000
RODATA_ADDR = 0x00740000
RODATA_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_STRLEN = 0x002C3290

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

# Fixed layout inside the type page.
RECORD_OFF = 0x000
SUB_OFF = 0x200
INNER_OFF = 0x280
CHILD_OFF = 0x300
TAIL_OFF = 0x340
NAME_OFF = 0x400

REL_SUB = SUB_OFF - (RECORD_OFF + 0x0C)
REL_NAME = NAME_OFF - (RECORD_OFF + 0x10)
REL_CHILD = CHILD_OFF - (RECORD_OFF + 0x14)
REL_TAIL = TAIL_OFF - (RECORD_OFF + 0x18)
REL_INNER = INNER_OFF - (SUB_OFF + 0x04)

ALL_HEADER_TAGS = [
    0x00000000, 0x00020000, 0x00040000, 0x00080000, 0x00100000,
    0x00200000, 0x00400000, 0x00400001, 0x00800000, 0x00800001,
    0x00800002, 0x00800004, 0x01000000, 0x02000000, 0x04000000,
    0x08000000, 0x10000000, 0x20000000, 0x40000000, 0x80000000,
]
UNKNOWN_TAGS = [
    0x00000001, 0x00000003, 0x00800003, 0x00400002, 0x01000001,
    0x04000001, 0x07FFFFFF, 0x3FFFFFFF, 0x7FFFFFFF, 0xDEADBEEF,
    0xFFFFFFFE, 0xFFFFFFFF,
]
CHILD_TAGS = [0x00000000, 0x04000000, 0x08000000, 0x10000000,
              0x20000000, 0x40000000, 0x80000000, 0x00000001]
TAIL_TAGS = [0x10000000, 0x20000000, 0x40000000, 0x80000000,
             0x00000000, 0x4000000, 0xFFFFFFFF]
INNER_TAGS = [0x00000000, 0x20000000, 0x40000000, 0x80000000,
              0x10000000, 0x00000001, 0xFFFFFFFF]


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if FUNC_ADDR.to_bytes(4, "big").hex() in name.lower() or (
            FUNC_SYMBOL in name
        ):
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"{FUNC_SYMBOL} not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            if "002c3290" not in rel.symbol_name.lower():
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (STUB_STRLEN - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into("<I", code, rel.offset, cond | (displacement & 0xFFFFFF))
        elif rel.relocation_type == 2:  # R_ARM_ABS32 into .rodata jump table
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into("<I", code, rel.offset, RODATA_ADDR + addend)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    rodata = elf_sections(obj_file).get(".rodata", b"")
    return bytes(code), rodata


def compile_source(src: Path, obj_name: str) -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / obj_name
    result = compile_tu_armv6k(src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_baseline() -> tuple[bytes, bytes]:
    return compile_source(SOURCE, "leaf_batch34_c.o")


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_source(mutant_src, f"mutant_{name}.o")


# --------------------------------------------------------------------- fixtures
def sentinel(offset: int) -> int:
    return 0xA5A50000 | ((offset >> 2) & 0xFFFF)


def build_type(case: dict) -> bytes:
    page = bytearray(TYPE_SIZE)
    for offset in range(0, TYPE_SIZE, 4):
        struct.pack_into("<I", page, offset, sentinel(offset))

    def put(offset: int, value: int) -> None:
        struct.pack_into("<I", page, offset, value & 0xFFFFFFFF)

    put(RECORD_OFF + 0x00, case.get("tag", 0))
    put(RECORD_OFF + 0x0C, 0 if case.get("no_sub", True) else REL_SUB + case.get("rel_sub_bias", 0))
    put(RECORD_OFF + 0x10, 0 if case.get("no_name", True) else REL_NAME)
    put(RECORD_OFF + 0x14, 0 if case.get("no_child", True) else REL_CHILD)
    put(RECORD_OFF + 0x18, 0 if case.get("no_tail", True) else REL_TAIL)

    put(SUB_OFF + 0x04, 0 if case.get("no_inner", True) else REL_INNER)
    put(SUB_OFF + 0x14, case.get("count_14", 0))
    put(SUB_OFF + 0x1C, case.get("count_1c", 0))
    put(INNER_OFF + 0x00, case.get("inner_tag", 0))
    put(CHILD_OFF + 0x00, case.get("child_tag", 0))
    put(TAIL_OFF + 0x00, case.get("tail_tag", 0))

    if not case.get("no_name", True):
        text = case.get("name", b"name")
        page[NAME_OFF:NAME_OFF + len(text)] = text
        page[NAME_OFF + len(text)] = 0
    return bytes(page)


def build_ctx(case: dict) -> bytes:
    page = bytearray(CTX_SIZE)
    struct.pack_into(
        "<III",
        page,
        0,
        case.get("offset", 0x10) & 0xFFFFFFFF,
        case.get("alignment", 4) & 0xFFFFFFFF,
        case.get("max_alignment", 8) & 0xFFFFFFFF,
    )
    return bytes(page)


def read_c_string(uc, address: int, limit: int = 64) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class Runner:
    """One Unicorn machine with the strlen stub at its original address."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(CTX_ADDR, CTX_SIZE)
        self.uc.mem_map(TYPE_ADDR, TYPE_SIZE)
        self.uc.mem_map(SLOT_ADDR, SLOT_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        self.uc.mem_write(STUB_STRLEN, struct.pack("<I", 0xE12FFF1E))  # bx lr
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_strlen,
            begin=STUB_STRLEN, end=STUB_STRLEN,
        )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []

    def _on_strlen(self, uc, address: int, size: int, user_data) -> None:
        pointer = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("engine_func_002c3290", pointer))
        if pointer == 0:
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        else:
            uc.reg_write(arm.UC_ARM_REG_R0, len(read_c_string(uc, pointer)))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def run(self, code: bytes, rodata: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(CTX_ADDR, build_ctx(case))
        self.uc.mem_write(TYPE_ADDR, build_type(case))
        self.uc.mem_write(
            SLOT_ADDR, struct.pack("<I", TYPE_ADDR + RECORD_OFF)
        )
        self.uc.mem_write(RODATA_ADDR, rodata)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, SLOT_ADDR)  # slot holds the record pointer
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
        for address, size in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_ctx = CTX_ADDR <= address < CTX_ADDR + CTX_SIZE
            if not (in_stack or in_ctx):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "ctx": bytes(self.uc.mem_read(CTX_ADDR, CTX_SIZE)),
            "type": bytes(self.uc.mem_read(TYPE_ADDR, TYPE_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}: orig={orig[key]!r} cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            f"call_log: orig={orig['call_log']!r} cand={cand['call_log']!r}"
        )
    if orig["ctx"] != cand["ctx"]:
        problems.append("layout cursor memory differs")
    if orig["type"] != cand["type"]:
        problems.append("type record memory differs")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(title: str, **overrides) -> dict:
    case = {
        "name": title,
        "tag": 0,
        "no_sub": True,
        "no_name": True,
        "no_child": True,
        "no_tail": True,
        "no_inner": True,
        "offset": 0x10,
        "alignment": 4,
        "max_alignment": 8,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- every header tag plus unknown and signed-boundary tags
    for tag in ALL_HEADER_TAGS:
        cases.append(base_case(f"header tag 0x{tag:08x}", tag=tag))
    for tag in UNKNOWN_TAGS:
        cases.append(base_case(f"unknown tag 0x{tag:08x}", tag=tag))

    # --- cursor offset/alignment/maximum boundaries (alignment and wrap)
    for offset in (0, 1, 2, 3, 4, 5, 0xFFFFFFFC, 0xFFFFFFFD, 0xFFFFFFFF):
        for alignment in (0, 1, 2, 4, 8, 0xFFFFFFFF):
            cases.append(
                base_case(
                    f"offset 0x{offset:08x} alignment 0x{alignment:08x}",
                    tag=0x00200000, offset=offset, alignment=alignment,
                    max_alignment=0x10,
                )
            )
    for maximum in (0, 1, 3, 4, 8, 0xFFFFFFFF):
        cases.append(
            base_case(f"max alignment 0x{maximum:08x}",
                      tag=0x00100000, max_alignment=maximum)
        )

    # --- pointer record: name only, empty and non-empty
    for name in (b"", b"x", b"name123", b"fifteen-chars!!"):
        cases.append(
            base_case(
                f"pointer name {name!r}",
                tag=0x04000000, no_name=False, name=name,
            )
        )

    # --- pointer record: null name and each resolved name length
    cases.append(base_case("pointer null name", tag=0x04000000, no_name=True))

    # --- pointer record: child and tail tags (every mapped value)
    for child_tag in CHILD_TAGS:
        cases.append(
            base_case(
                f"pointer child 0x{child_tag:08x}",
                tag=0x04000000, no_name=True, no_child=False,
                child_tag=child_tag,
            )
        )
    for tail_tag in TAIL_TAGS:
        cases.append(
            base_case(
                f"pointer tail 0x{tail_tag:08x}",
                tag=0x04000000, no_name=True, no_tail=False,
                tail_tag=tail_tag,
            )
        )
    cases.append(
        base_case(
            "pointer all children present",
            tag=0x04000000, no_name=False, name=b"abc",
            no_child=False, child_tag=0x04000000,
            no_tail=False, tail_tag=0x40000000,
        )
    )
    cases.append(
        base_case(
            "pointer all children absent",
            tag=0x04000000, no_name=True, no_child=True, no_tail=True,
        )
    )

    # --- sub-record: counts, inner tag, null selections
    for count_14, count_1c in (
        (0, 0), (1, 0), (0, 1), (1, 1), (0x10, 0x20),
        (0xFFFFFFFF, 1), (1, 0xFFFFFFFF), (0x7FFFFFFF, 1),
        (0x80000000, 0x80000000), (0x3FFFFFFF, 0x40000000),
        (0xFFFFFFFF, 0xFFFFFFFF),
    ):
        cases.append(
            base_case(
                f"sub counts 0x{count_14:08x}/0x{count_1c:08x}",
                tag=0x00000000, no_sub=False, no_inner=True,
                count_14=count_14, count_1c=count_1c,
            )
        )
    for inner_tag in INNER_TAGS:
        cases.append(
            base_case(
                f"sub inner tag 0x{inner_tag:08x}",
                tag=0x00080000, no_sub=False, no_inner=False,
                count_14=5, count_1c=7, inner_tag=inner_tag,
            )
        )

    # --- combined nested case exercising all eight reservations
    cases.append(
        base_case(
            "all reservations populated",
            tag=0x04000000, no_name=False, name=b"nested",
            no_child=False, child_tag=0x20000000,
            no_tail=False, tail_tag=0x10000000,
            no_sub=False, no_inner=False, inner_tag=0x40000000,
            count_14=9, count_1c=3,
            offset=0xFFFFFFFE, alignment=0xFFFFFFFF, max_alignment=3,
        )
    )
    cases.append(
        base_case(
            "all reservations populated non-pointer",
            tag=0x00100000, no_sub=False, no_inner=False,
            inner_tag=0x80000000, count_14=0x20, count_1c=0x40,
            offset=7, alignment=0, max_alignment=0xFFFFFFFF,
        )
    )
    return cases


def run_case_set(orig_code, cand_code, rodata, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, rodata, case)
        cand = Runner().run(cand_code, rodata, case)
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
    print("Testing engine_func_00148dec (0x00148dec)...")
    orig_code = get_orig_bytes()
    cand_code, rodata = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B (relocated).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, rodata, cases)

    print("\nNegative controls:")
    mutants = (
        ("header_0x54", "case 0x00100000u: return 0x54;",
         "case 0x00100000u: return 0x55;"),
        ("align_mask",
         "constexpr u32 Align4(u32 value) {\n    return (value + 3u) & ~u32{3};",
         "constexpr u32 Align4(u32 value) {\n    return (value + 2u) & ~u32{3};"),
        ("table_header", "table_size = 0x24u + ((count_14 + count_1c) << 2);",
         "table_size = 0x25u + ((count_14 + count_1c) << 2);"),
        ("child_size_0x28", "case 0x40000000u: return 0x28;",
         "case 0x40000000u: return 0x29;"),
        ("inner_size_0x10",
         "constexpr u32 InnerSizeForTag(u32 tag) {\n"
         "    switch (tag) {\n"
         "        case 0x00000000u: return 0x08;\n"
         "        case 0x20000000u: return 0x08;\n"
         "        case 0x40000000u: return 0x10;",
         "constexpr u32 InnerSizeForTag(u32 tag) {\n"
         "    switch (tag) {\n"
         "        case 0x00000000u: return 0x08;\n"
         "        case 0x20000000u: return 0x08;\n"
         "        case 0x40000000u: return 0x11;"),
    )
    for name, old, new in mutants:
        mutant_code, mutant_rodata = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, rodata, case)
            cand = Runner().run(mutant_code, mutant_rodata, case)
            if compare(orig, cand):
                detected = True
                break
        if not detected:
            print(f"  [FAIL] mutant {name} was not detected")
            raise SystemExit(1)
        print(f"  [PASS] mutant {name} detected")

    print(f"\nAll {passed} differential test cases and 5 negative controls PASSED!")


if __name__ == "__main__":
    main()
