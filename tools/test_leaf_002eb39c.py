#!/usr/bin/env python3
"""Differential test for ui_func_002eb39c (0x002EB39C) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts ui_func_002eb39c, retargets its
seven direct calls to deterministic stubs, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

The original calls 0x002BE7FC with `blx` (it is Thumb code); the harness
rewrites every original call target and every candidate relocation to the same
ARM stub, so the callee's instruction set does not affect what is observed.

Compared outputs:
  * continuation PC, final SP, and the preserved callee-saved registers r4-r11;
  * the ordered call log with every register argument (the function has no
    stack arguments to its callees);
  * the strings written by each 0x2BE7FC "formatter" stub (destination offset,
    format, value and resolved text);
  * the full reticle-record page, the work pointer page, the source-record page
    and the string pages;
  * every emulated write outside the private stack and the reticle record.

The original function is `void`: it leaves r0 with the last computed word and
that word is not a contract, so r0 is not compared.

Coverage: the projected-word branch on both sides of the 0x43520000 signed
boundary (including 0x43520000 itself, 0, negative float bit patterns,
+infinity and a positive NaN pattern), null/non-null results of the string
lookups and of ui_func_0027dd78, every unit-record byte/u16 value (zero,
0xFFFF, 0x7FFF, 0x8000, 0x0400) and every caller byte (0x00/0x7F/0x80/0xFF),
plus 32-bit wrap values for the position and the depth words. Negative
controls mutate the threshold, the u16 scale shift and the if-branch depth
offset; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_002eb39c"

FUNC_ADDR = 0x002EB39C
FUNC_SIZE = 472
FUNC_NAME = "ui_func_002eb39c"

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000
GLOBAL_ADDR = 0x00439000
GLOBAL_SIZE = 0x00001000
WORK_ADDR = 0x00710000
WORK_SIZE = 0x00001000
RECORD_ADDR = 0x00720000
RECORD_SIZE = 0x00001000
UNIT_ADDR = 0x00730000
UNIT_SIZE = 0x00001000
STRING_ADDR = 0x00740000
STRING_SIZE = 0x00002000
RODATA_ADDR = 0x00760000
RODATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

WORK_POINTER_CELL = 0x00439C60
ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x200

STUB_BASE = 0x00110000
STUB_STRIDE = 8
STUB_TARGETS = {
    0x002B087C: "battle_func_002b087c",
    0x002BD25C: "script_vm_func_002bd25c",
    0x002BD020: "script_vm_func_002bd020",
    0x002BE7FC: "ui_func_002be7fc",
    0x0029EC6C: "ui_func_0029ec6c",
    0x0027DD78: "ui_func_0027dd78",
    0x0026330C: "ui_func_0026330c",
}
STUB_ADDRS = {
    target: STUB_BASE + index * STUB_STRIDE
    for index, target in enumerate(sorted(STUB_TARGETS))
}
ADDR_BY_STUB = {address: target for target, address in STUB_ADDRS.items()}

STRING_ONE = STRING_ADDR + 0x000
STRING_TWO = STRING_ADDR + 0x100
STRING_NULL = STRING_ADDR + 0x180

THRESHOLD_BITS = 0x43520000
DEPTH_IF_OFFSET = 0x78
DEPTH_ELSE_A = 0x70
DEPTH_ELSE_B = 0xD8

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


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def elf_sections(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    e_shstrndx = struct.unpack_from("<H", data, 50)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    result: dict[str, bytes] = {}
    for section in sections:
        end = shstrtab.find(b"\x00", section[0])
        name = shstrtab[section[0] : end].decode("ascii", errors="replace")
        result[name] = data[section[4] : section[4] + section[5]]
    return result


def s24(value: int) -> int:
    value &= 0x00FFFFFF
    return value - 0x01000000 if value & 0x00800000 else value


def encode_bl(pc: int, target: int) -> int:
    return 0xEB000000 | (((target - (pc + 8)) >> 2) & 0x00FFFFFF)


def patch_original(raw: bytes) -> bytearray:
    code = bytearray(raw)
    for offset in range(0, len(code), 4):
        instruction = struct.unpack_from("<I", code, offset)[0]
        pc = FUNC_ADDR + offset
        cond = instruction >> 28
        if cond == 0xF:
            # BLX (immediate) is the only cond=1111 form reached here.
            if (instruction & 0xFE000000) != 0xFA000000:
                continue
            h_bit = (instruction >> 24) & 1
            target = pc + 8 + (s24(instruction) << 2) + (h_bit << 1)
        else:
            if (instruction & 0x0E000000) != 0x0A000000:
                continue
            target = pc + 8 + (s24(instruction) << 2)
        if target in STUB_ADDRS:
            struct.pack_into("<I", code, offset, encode_bl(pc, STUB_ADDRS[target]))
    return code


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    functions = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in functions.items():
        if "002eb39c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"{FUNC_NAME} not found in {obj_file}: {sorted(functions)}")

    raw, relocations = candidate
    code = bytearray(raw)
    sections = elf_sections(obj_file)
    rodata_base = {
        ".rodata": RODATA_ADDR,
        ".rodata.str1.1": RODATA_ADDR + 0x8000,
        ".rodata.str1.4": RODATA_ADDR + 0x9000,
    }
    rodata_pages: dict[int, bytes] = {}
    for rel in relocations:
        if rel.relocation_type in (28, 29):
            target = None
            for address, name in STUB_TARGETS.items():
                if f"{address:08x}" in rel.symbol_name.lower():
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset
            instruction = struct.unpack_from("<I", code, rel.offset)[0]
            cond = instruction & 0xF0000000
            displacement = ((STUB_ADDRS[target] - (pc + 8)) >> 2) & 0x00FFFFFF
            struct.pack_into("<I", code, rel.offset, cond | 0x0B000000 | displacement)
        elif rel.relocation_type == 2:  # R_ARM_ABS32 to a string literal
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            base = None
            for name, address in rodata_base.items():
                if name in rel.symbol_name:
                    base = address
                    break
            if base is None:
                # The "%s" literal is referenced through a section symbol, so
                # the relocation name is empty; it lives in .rodata.str1.1.
                base = rodata_base[".rodata.str1.1"]
            struct.pack_into("<I", code, rel.offset, base + addend)
            if rel.symbol_name and rel.symbol_name in sections:
                rodata_pages[base] = sections[rel.symbol_name]
            elif ".rodata.str1.1" in sections:
                rodata_pages[base] = sections[".rodata.str1.1"]
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )

    rodata = bytearray(RODATA_SIZE)
    for base, payload in rodata_pages.items():
        span = min(len(payload), RODATA_ADDR + RODATA_SIZE - base)
        rodata[base - RODATA_ADDR : base - RODATA_ADDR + span] = payload[:span]
    return bytes(code), bytes(rodata)


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_source = OUT_DIR / f"mutant_{name}.cpp"
    mutant_source.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_source, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def read_c_string(uc, address: int, limit: int = 64) -> bytes:
    out = bytearray()
    for index in range(limit):
        try:
            byte = uc.mem_read(address + index, 1)[0]
        except Exception:
            break
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


def build_unit(case: dict) -> bytes:
    page = bytearray(UNIT_SIZE)
    page[2] = case.get("unit_byte2", 0x5A) & 0xFF
    fields = case.get("unit_fields")
    if fields is None:
        fields = (0x0000, 0x7FFF, 0x8000, 0xFFFF, 0x0400, 0x0C00, 0x5555, 0x3FFF)
    for index, value in enumerate(fields):
        struct.pack_into("<H", page, 0x24 + index * 2, value & 0xFFFF)
    # Fillers that must stay untouched.
    page[0] = 0xC7
    page[1] = 0x3D
    for offset in range(0x34, 0x40, 4):
        struct.pack_into("<I", page, offset, 0xA5A50000 | offset)
    return bytes(page)


def build_record(case: dict) -> bytes:
    page = bytearray(RECORD_SIZE)
    struct.pack_into("<I", page, 0x68, case.get("preexisting_68", 0x11223344))
    struct.pack_into("<I", page, 0x6C, case.get("preexisting_6C", 0x55667788))
    struct.pack_into("<f", page, DEPTH_ELSE_A, case.get("depth70", 2.5))
    struct.pack_into("<f", page, DEPTH_IF_OFFSET, case.get("depth78", 1.25))
    struct.pack_into("<f", page, DEPTH_ELSE_B, case.get("depthD8", -4.5))
    # Text buffers and neighbouring filler.
    page[0x04:0x0C] = b"\xDE\xAD\xBE\xEF\xCA\xFE\xBA\xBE"
    page[0x2C:0x34] = b"\x11\x22\x33\x44\x55\x66\x77\x88"
    page[0xE4] = 0x7E
    struct.pack_into("<I", page, 0xF4, 0x99887766)
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at relocated addresses."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(RECORD_ADDR, RECORD_SIZE)
        self.uc.mem_map(UNIT_ADDR, UNIT_SIZE)
        self.uc.mem_map(STRING_ADDR, STRING_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))

        for address in STUB_ADDRS.values():
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _format_text(self, value: int) -> bytes:
        if value == 0:
            return b"<null>"
        return read_c_string(self.uc, value)

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        target = ADDR_BY_STUB[address]
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if target == 0x002B087C:
            self.call_log.append(("battle_func_002b087c", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, UNIT_ADDR)
        elif target == 0x002BD25C:
            self.call_log.append(("script_vm_func_002bd25c", r0))
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                0 if self.case.get("null_text_one") else STRING_ONE,
            )
        elif target == 0x002BD020:
            self.call_log.append(("script_vm_func_002bd020", r0, r1))
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                0 if self.case.get("null_text_two") else STRING_TWO,
            )
        elif target == 0x002BE7FC:
            fmt = read_c_string(uc, r1)
            if fmt == b"%s":
                text = b"<null>" if r2 == 0 else read_c_string(uc, r2)
            else:
                text = fmt
            self.call_log.append(
                ("ui_func_002be7fc", r0 - RECORD_ADDR, fmt, r2, text)
            )
            uc.mem_write(r0, text + b"\x00")
            uc.reg_write(arm.UC_ARM_REG_R0, len(text))
        elif target == 0x0029EC6C:
            self.call_log.append(("ui_func_0029ec6c", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("ret_29ec6c", 1) & 0xFF)
        elif target == 0x0027DD78:
            self.call_log.append(("ui_func_0027dd78", r0))
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                0 if self.case.get("null_context") else WORK_ADDR + 0x200,
            )
        elif target == 0x0026330C:
            # r0 = output, r1 = index, r2 = context, r3 = source vector.
            source = struct.unpack("<3I", uc.mem_read(r3, 12)) if r3 else (0, 0, 0)
            self.call_log.append(
                ("ui_func_0026330c", r0 == ENTRY_SP or STACK_ADDR <= r0 < STACK_ADDR + STACK_SIZE,
                 r1, r2, source)
            )
            projected = self.case.get("projected", (0x42C80000, 0x40000000, 0))
            uc.mem_write(r0, struct.pack("<3I", *projected))
        else:  # pragma: no cover - guarded by registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, rodata: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(RODATA_ADDR, rodata)
        self.uc.mem_write(GLOBAL_ADDR, b"\x00" * GLOBAL_SIZE)
        self.uc.mem_write(WORK_ADDR, b"\x00" * WORK_SIZE)
        self.uc.mem_write(RECORD_ADDR, b"\x00" * RECORD_SIZE)
        self.uc.mem_write(UNIT_ADDR, b"\x00" * UNIT_SIZE)
        self.uc.mem_write(STRING_ADDR, b"\x00" * STRING_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        struct.pack_into("<I", self.uc.mem_read(WORK_POINTER_CELL, 4), 0, WORK_ADDR)
        self.uc.mem_write(WORK_POINTER_CELL, struct.pack("<I", WORK_ADDR))
        self.uc.mem_write(WORK_ADDR, struct.pack("<III", RECORD_ADDR, 0, 0))
        self.uc.mem_write(UNIT_ADDR, build_unit(case))
        self.uc.mem_write(RECORD_ADDR, build_record(case))

        text_one = case.get("text_one", b"Alpha")
        text_two = case.get("text_two", b"Beta")
        self.uc.mem_write(STRING_ONE, text_one + b"\x00")
        self.uc.mem_write(STRING_TWO, text_two + b"\x00")
        self.uc.mem_write(STRING_NULL, b"\x00")

        b0 = case.get("b0", 0)
        b1 = case.get("b1", 0)
        b2 = case.get("b2", 0)
        b3 = case.get("b3", 0)
        b4 = case.get("b4", 0)
        b5 = case.get("b5", 0)
        position = case.get("position", (0x40000000, 0xC0000000, 0xDEADBEEF))
        self.uc.mem_write(ENTRY_SP, struct.pack("<4I", b2, b3, b4, b5))
        position_addr = STACK_ADDR + 0x1000
        self.uc.mem_write(position_addr, struct.pack("<3I", *position))

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, position_addr)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("unit_id", 0x0123) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, b0)
        self.uc.reg_write(arm.UC_ARM_REG_R3, b1)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        self.writes = []
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_record = RECORD_ADDR <= address < RECORD_ADDR + RECORD_SIZE
            if not (in_stack or in_record):
                unexpected_writes.append((address, size))

        return {
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "record": bytes(self.uc.mem_read(RECORD_ADDR, RECORD_SIZE)),
            "work": bytes(self.uc.mem_read(WORK_ADDR, 0x40)),
            "unit": bytes(self.uc.mem_read(UNIT_ADDR, UNIT_SIZE)),
            "strings": bytes(self.uc.mem_read(STRING_ADDR, 0x200)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("pc", "sp", "callee_saved", "call_log"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for key in ("record", "work", "unit", "strings"):
        if orig[key] != cand[key]:
            index = next(
                (i for i, (a, b) in enumerate(zip(orig[key], cand[key])) if a != b),
                -1,
            )
            problems.append(
                f"{key} differs at byte 0x{index:x}: "
                f"orig=0x{orig[key][index]:02x} cand=0x{cand[key][index]:02x}"
                if index >= 0
                else f"{key} differs in length"
            )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "unit_id": 0x0123,
        "position": (0x40000000, 0xC0000000, 0xDEADBEEF),
        "projected": (0x42C80000, 0x40000000, 0),
        "text_one": b"Alpha",
        "text_two": b"Beta",
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- projected first word around the signed 0x43520000 boundary.
    boundaries = (
        ("threshold exactly", 0x43520000),
        ("threshold + 1", 0x43520001),
        ("threshold - 1", 0x434FFFFF),
        ("zero", 0x00000000),
        ("positive small", 0x00000001),
        ("large positive", 0x7F7FFFFF),
        ("+infinity", 0x7F800000),
        ("positive NaN", 0x7FC00000),
        ("negative zero", 0x80000000),
        ("negative one", 0xBF800000),
        ("most negative float", 0xFF7FFFFF),
        ("negative NaN", 0xFFC00000),
    )
    for label, bits in boundaries:
        cases.append(
            base_case(f"projected {label} 0x{bits:08x}",
                      projected=(bits, 0x40000000, 0x12345678))
        )

    # --- null and non-null string lookups; null/non-null projector context.
    cases.append(base_case("first text null", null_text_one=True))
    cases.append(base_case("second text null", null_text_two=True))
    cases.append(base_case("both text null", null_text_one=True,
                           null_text_two=True))
    cases.append(base_case("projector context null", null_context=True))
    cases.append(base_case("empty strings", text_one=b"", text_two=b""))
    cases.append(base_case("long strings", text_one=b"A" * 40,
                           text_two=b"B" * 55))

    # --- entity predicate return values.
    for value in (0, 1, 0x80, 0xFF, 0x1FF):
        cases.append(base_case(f"entity predicate 0x{value:x}",
                               ret_29ec6c=value))

    # --- record fields: every boundary width.
    cases.append(
        base_case(
            "unit fields all zero",
            unit_fields=(0, 0, 0, 0, 0, 0, 0, 0),
            unit_byte2=0x00,
        )
    )
    cases.append(
        base_case(
            "unit fields all max",
            unit_fields=(0xFFFF,) * 8,
            unit_byte2=0xFF,
        )
    )
    cases.append(
        base_case(
            "unit fields signed boundaries",
            unit_fields=(0x7FFF, 0x8000, 0x0400, 0x03FF, 0xFC00, 0x0010,
                         0x8001, 0xFFFE),
            unit_byte2=0x80,
        )
    )
    for byte in (0x00, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"unit byte2 0x{byte:02x}", unit_byte2=byte))

    # --- six caller bytes, including sign-bit values.
    byte_sets = (
        (0x00, 0x01, 0x7F, 0x80, 0xFE, 0xFF),
        (0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF),
        (0x10, 0x20, 0x30, 0x40, 0x50, 0x60),
    )
    for index, values in enumerate(byte_sets):
        cases.append(
            base_case(
                f"caller bytes set {index}",
                b0=values[0], b1=values[1], b2=values[2],
                b3=values[3], b4=values[4], b5=values[5],
            )
        )

    # --- unit ids: 16-bit truncation of the passed word.
    for unit_id in (0x0000, 0x0123, 0xFFFF, 0x1234ABCD, 0xFFFF0000):
        cases.append(base_case(f"unit id 0x{unit_id:08x}", unit_id=unit_id))

    # --- position and depth words: 32-bit wrap values.
    for position in (
        (0x00000000, 0xFFFFFFFF, 0x80000000),
        (0x7FFFFFFF, 0x80000000, 0x7FFFFFFF),
        (0xFFFFFFFF, 0x00000001, 0x00000000),
    ):
        cases.append(
            base_case(
                "position 0x%08x/0x%08x/0x%08x" % position,
                position=position,
            )
        )
    cases.append(
        base_case(
            "depth words extremes",
            depth70=3.0e38,
            depth78=-3.0e38,
            depthD8=1.0e-30,
            projected=(0x43520001, 0x40000000, 0),
        )
    )
    cases.append(
        base_case(
            "depth words negative",
            depth70=-1.0,
            depth78=-2.0,
            depthD8=-3.0,
            projected=(0x434FFFFF, 0x40000000, 0),
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
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print(f"Testing {FUNC_NAME} (0x{FUNC_ADDR:08X})...")
    orig_code = bytes(patch_original(get_orig_bytes()))
    cand_code, rodata = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B, "
        "relocations resolved."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, rodata, cases)

    print("\nNegative controls:")
    mutants = (
        ("threshold_lo", "constexpr s32 kProjectedThresholdBits = 0x43520000;",
         "constexpr s32 kProjectedThresholdBits = 0x43000000;"),
        ("scale_shift", "constexpr u32 kUnitFieldScaleShift = 10;",
         "constexpr u32 kUnitFieldScaleShift = 11;"),
        ("depth_if_offset",
         "value - *reinterpret_cast<const f32*>(record + 0x78);",
         "value - *reinterpret_cast<const f32*>(record + 0x74);"),
    )
    for name, old, new in mutants:
        mutant_code, mutant_rodata = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, rodata, case)
            bad = Runner().run(mutant_code, mutant_rodata, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
