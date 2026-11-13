#!/usr/bin/env python3
"""Differential test for engine_func_0014cae4 (0x0014CAE4) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the engine_func_0014cae4
body, resolves its direct calls to deterministic stubs at the original
addresses, and runs the pinned 608-byte original (extracted/exefs/code.bin)
against the candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log with every register argument, the architected stack
    arguments of 0x002A4828 (mode, 0x80, user), and the string bytes each
    string/memory helper actually received;
  * the full slot page (including the 0x604-based sibling table), the source
    and descriptor records, the string page, the raw/decoded asset pages, the
    AsdTexture page, and the 0x00430000 manager page;
  * every write is confined to the private stack, the slot page or the
    texture page.

Coverage: plain and "-<byte>" names, positive/negative/zero sibling codes
(0, 2, 3, 4, -1, 127, -128), variant 0/1/0xFF, flags 0/0x10000 and every
rejected flag form, empty/one-byte/long names, null and non-null loads, STEX
match and mismatch before and after the AOC upload, the early-complete
(data+0x24) path, data+4 == 1, and the asset-size wrap boundaries.
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
OUT_DIR = ROOT / "build/test_leaf_0014cae4"

FUNC_ADDR = 0x0014CAE4
FUNC_SIZE = 608

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers 0x0014CAE4 and every stub below 0x00300000
DATA_ADDR = 0x00430000
DATA_SIZE = 0x00010000
SLOT_ADDR = 0x00710000
SLOT_SIZE = 0x00010000
SOURCE_ADDR = 0x00720000
SOURCE_SIZE = 0x00001000
DESC_ADDR = 0x00721000
DESC_SIZE = 0x00001000
STRING_ADDR = 0x00722000
STRING_SIZE = 0x00002000
ASSET_ADDR = 0x00740000
ASSET_SIZE = 0x00010000
TEXTURE_ADDR = 0x00750000
TEXTURE_SIZE = 0x00004000
RODATA_ADDR = 0x00760000
RODATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

MANAGER_SLOT = 0x00433130
MANAGER_ADDR = DATA_ADDR + 0x1000

SLOT_BASE = SLOT_ADDR + 0x8000
SIBLING_TABLE_END = 0x604
SIBLING_STRIDE = 0x20

RAW_ASSET_ADDR = ASSET_ADDR + 0x1000
DECODED_ASSET_ADDR = ASSET_ADDR + 0x2000

# Original direct-call targets; stubs live at the same addresses so both the
# pinned bytes and the relocated candidate reach them.
STUB_2BF86C = 0x002BF86C  # strcpy
STUB_2B67E0 = 0x002B67E0  # strcat
STUB_2C3290 = 0x002C3290  # strlen
STUB_2C1A48 = 0x002C1A48  # memcmp
STUB_2A4828 = 0x002A4828  # buffered asset request
STUB_2A465C = 0x002A465C  # AOC texture upload
STUB_2C4360 = 0x002C4360  # free
STUB_2BD940 = 0x002BD940  # AsdTexture create

# 0x2B67E0 and 0x2C1A48 are Thumb in the pinned binary (the original reaches
# them with blx); a real link turns the candidate's R_ARM_CALL into BLX too.
THUMB_STUBS = {STUB_2B67E0, STUB_2C1A48}

STUB_NAMES = {
    STUB_2BF86C: "engine_func_002bf86c",
    STUB_2B67E0: "engine_func_002b67e0",
    STUB_2C3290: "engine_func_002c3290",
    STUB_2C1A48: "engine_func_002c1a48",
    STUB_2A4828: "engine_func_002a4828",
    STUB_2A465C: "smt4::engine::aocTexCtrl_func_002a465c",
    STUB_2C4360: "engine_func_002c4360",
    STUB_2BD940: "smt4::engine::AsdTexture_func_002bd940",
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

# String page layout.
STR_BASE_NAME = STRING_ADDR + 0x000
STR_SOURCE_PATH = STRING_ADDR + 0x100
STR_DESC_NAME = STRING_ADDR + 0x200
STR_SIBLING_NAMES = STRING_ADDR + 0x400
STRING_NODE_BASE = STRING_ADDR + 0x1000
STRING_NODE_STRIDE = 0x20


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
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + index * e_shentsize)
        for index in range(e_shnum)
    ]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    result: dict[str, bytes] = {}
    for section in sections:
        end = shstrtab.find(b"\x00", section[0])
        name = shstrtab[section[0] : end].decode("ascii", errors="replace")
        result[name] = data[section[4] : section[4] + section[5]]
    return result


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0014cae4" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_0014cae4 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = None
            for address, _symbol in STUB_NAMES.items():
                if f"{address:08x}" in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            offset = target - pc
            if target in THUMB_STUBS:
                if offset & 3:
                    raise RuntimeError(f"unaligned Thumb call target 0x{target:08x}")
                instruction = (
                    0xFA000000
                    | ((offset >> 2) & 0x00FFFFFF)
                    | ((offset & 2) << 23)
                )
            else:
                original = struct.unpack_from("<I", code, rel.offset)[0]
                condition = original & 0xFF000000
                instruction = condition | ((offset >> 2) & 0x00FFFFFF)
            struct.pack_into("<I", code, rel.offset, instruction)
        elif rel.relocation_type == 2:  # R_ARM_ABS32 into .rodata.str1.1
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into("<I", code, rel.offset, RODATA_ADDR + addend)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name!r}"
            )

    rodata = elf_sections(obj_file).get(".rodata.str1.1", b"")
    return bytes(code), rodata


def compile_candidate_baseline() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures
def read_string(uc, address: int, limit: int = 0xC0) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


def write_fixture(uc, address: int, size: int, fill: int) -> None:
    uc.mem_write(address, bytes([fill]) * size)


def build_asset(magic: bytes, fields: dict[int, int]) -> bytes:
    buffer = bytearray(0x80)
    buffer[0:4] = magic
    for offset, value in fields.items():
        struct.pack_into("<I", buffer, offset, value & 0xFFFFFFFF)
    return bytes(buffer)


DEFAULT_FIELDS = {
    0x04: 0x00000002,
    0x08: 0x11111111,
    0x0C: 0x22222222,
    0x10: 0x33333333,
    0x14: 0x44444444,
    0x18: 0x55555555,
    0x20: 0x00000100,
    0x24: 0x00000000,
}

DECODED_FIELDS = {
    0x04: 0x00000002,
    0x08: 0xA1A1A1A1,
    0x0C: 0xB2B2B2B2,
    0x10: 0xC3C3C3C3,
    0x14: 0xD4D4D4D4,
    0x18: 0xE5E5E5E5,
    0x20: 0x00000040,
    0x24: 0x00000000,
}


def sibling_entry_address(code: int) -> int:
    """Address of the 0x20-byte sibling entry selected by one name byte."""
    signed = code - 0x100 if code >= 0x80 else code
    return (SLOT_BASE + SIBLING_TABLE_END - signed * SIBLING_STRIDE) & 0xFFFFFFFF


def build_case_pages(case: dict) -> dict[str, bytes]:
    """Build every fixture page for one differential case."""
    sibling_codes = tuple(case.get("sibling_codes", ()))

    slot_page = bytearray([0xCC]) * SLOT_SIZE
    base = SLOT_BASE - SLOT_ADDR

    # Sibling entries addressed through slot + 0x604 - code * 0x20.  Each
    # entry's first word points at a node whose +8 word is the name string.
    for index, code in enumerate(sibling_codes):
        entry = sibling_entry_address(code) - SLOT_ADDR
        node = STRING_NODE_BASE + index * STRING_NODE_STRIDE
        struct.pack_into("<I", slot_page, entry, node)
        struct.pack_into("<I", slot_page, entry + 4, 0x5A5A0000 | index)

    struct.pack_into(
        "<IIIII",
        slot_page,
        base,
        SOURCE_ADDR,
        DESC_ADDR,
        case.get("texture_sentinel", 0xDEAD0008),
        case.get("loaded_sentinel", 0xDEAD000C),
        case.get("flags", 0) & 0xFFFFFFFF,
    )

    source_page = bytearray([0xDD]) * SOURCE_SIZE
    # The path is an inline NUL-terminated string at source+0x0C.
    inline_path = case["source_path"] + b"\x00"
    source_page[0x0C : 0x0C + len(inline_path)] = inline_path

    desc_page = bytearray([0xEE]) * DESC_SIZE
    struct.pack_into("<I", desc_page, 0x08, STR_DESC_NAME)
    desc_page[0x0D] = case.get("variant", 0) & 0xFF

    string_page = bytearray([0x00]) * STRING_SIZE

    def put_string(address: int, data: bytes) -> None:
        offset = address - STRING_ADDR
        encoded = data + b"\x00"
        string_page[offset : offset + len(encoded)] = encoded

    put_string(STR_BASE_NAME, case["base_name"])
    put_string(STR_SOURCE_PATH, case["source_path"])
    put_string(STR_DESC_NAME, case["desc_name"])
    for index, _code in enumerate(sibling_codes):
        put_string(STR_SIBLING_NAMES + index * 0x40,
                   case.get("sibling_name", b"ref"))
        node_offset = (STRING_NODE_BASE + index * STRING_NODE_STRIDE) - STRING_ADDR
        struct.pack_into(
            "<I", string_page, node_offset + 8,
            STR_SIBLING_NAMES + index * 0x40,
        )

    asset_page = bytearray([0x00]) * ASSET_SIZE
    raw = build_asset(case.get("asset_magic", b"STEX"),
                      case.get("asset_fields", DEFAULT_FIELDS))
    asset_page[0x1000 : 0x1000 + len(raw)] = raw
    decoded = build_asset(case.get("decoded_magic", b"STEX"),
                          case.get("decoded_fields", DECODED_FIELDS))
    asset_page[0x2000 : 0x2000 + len(decoded)] = decoded

    texture_page = bytearray([0xA5]) * TEXTURE_SIZE

    data_page = bytearray([0x00]) * DATA_SIZE
    struct.pack_into("<I", data_page, MANAGER_SLOT - DATA_ADDR, MANAGER_ADDR)

    return {
        "slot": bytes(slot_page),
        "source": bytes(source_page),
        "desc": bytes(desc_page),
        "strings": bytes(string_page),
        "asset": bytes(asset_page),
        "texture": bytes(texture_page),
        "data": bytes(data_page),
    }


class LeafRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(SLOT_ADDR, SLOT_SIZE)
        self.uc.mem_map(SOURCE_ADDR, SOURCE_SIZE)
        self.uc.mem_map(DESC_ADDR, DESC_SIZE)
        self.uc.mem_map(STRING_ADDR, STRING_SIZE)
        self.uc.mem_map(ASSET_ADDR, ASSET_SIZE)
        self.uc.mem_map(TEXTURE_ADDR, TEXTURE_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            if address in THUMB_STUBS:
                self.uc.mem_write(address, struct.pack("<H", 0x4770))
            else:
                self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.texture_index = 0
        self.loaded_pointer = 0

    # ------------------------------------------------------------------ stubs
    def _read_cstr(self, address: int, limit: int = 0xC0) -> bytes:
        try:
            return read_string(self.uc, address, limit)
        except unicorn.UcError:
            return b"<unreadable>"

    def _memcmp(self, address: int, size: int) -> bytes:
        try:
            return bytes(self.uc.mem_read(address, size))
        except unicorn.UcError:
            return b"<unreadable>"

    def _stack_word(self, index: int) -> int:
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack("<I", self.uc.mem_read(sp + index * 4, 4))[0]

    @staticmethod
    def _normalise(value: int) -> object:
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2BF86C:
            source = self._read_cstr(r1)
            self.call_log.append(
                (STUB_NAMES[address], (self._normalise(r0), source))
            )
            uc.mem_write(r0, source + b"\x00")
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_2B67E0:
            source = self._read_cstr(r1)
            existing = self._read_cstr(r0)
            self.call_log.append(
                (STUB_NAMES[address], (self._normalise(r0), source, existing))
            )
            uc.mem_write(r0, existing + source + b"\x00")
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_2C3290:
            text = self._read_cstr(r0)
            self.call_log.append((STUB_NAMES[address], (text,)))
            uc.reg_write(arm.UC_ARM_REG_R0, len(text))
        elif address == STUB_2C1A48:
            left = self._memcmp(r0, r2)
            right = self._memcmp(r1, r2)
            self.call_log.append(
                (STUB_NAMES[address], (left, right, r2))
            )
            result = 0
            for lhs, rhs in zip(left, right):
                lhs_s = lhs - 0x100 if lhs >= 0x80 else lhs
                rhs_s = rhs - 0x100 if rhs >= 0x80 else rhs
                if lhs_s != rhs_s:
                    result = lhs_s - rhs_s
                    break
            uc.reg_write(arm.UC_ARM_REG_R0, result & 0xFFFFFFFF)
        elif address == STUB_2A4828:
            manager = r0
            primary = self._read_cstr(r1)
            secondary = self._read_cstr(r2)
            out_pointer = r3
            mode = self._stack_word(0)
            size_arg = self._stack_word(1)
            user = self._stack_word(2)
            if self.case.get("load_result") == "null":
                self.call_log.append(
                    (
                        STUB_NAMES[address],
                        (
                            manager,
                            primary,
                            secondary,
                            self._normalise(out_pointer),
                            mode,
                            size_arg,
                            user,
                            "<null>",
                        ),
                    )
                )
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                out_size = self.case.get("asset_size", 0x200) & 0xFFFFFFFF
                uc.mem_write(out_pointer, struct.pack("<I", out_size))
                self.loaded_pointer = RAW_ASSET_ADDR
                self.call_log.append(
                    (
                        STUB_NAMES[address],
                        (
                            manager,
                            primary,
                            secondary,
                            self._normalise(out_pointer),
                            mode,
                            size_arg,
                            user,
                            out_size,
                        ),
                    )
                )
                uc.reg_write(arm.UC_ARM_REG_R0, RAW_ASSET_ADDR)
        elif address == STUB_2A465C:
            self.call_log.append(
                (STUB_NAMES[address], (r0, r1, r2))
            )
            if self.case.get("decode_result") == "same":
                uc.reg_write(arm.UC_ARM_REG_R0, r0)
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, DECODED_ASSET_ADDR)
        elif address == STUB_2C4360:
            self.call_log.append((STUB_NAMES[address], (r0,)))
        elif address == STUB_2BD940:
            self.call_log.append((STUB_NAMES[address], (r0,)))
            texture = TEXTURE_ADDR + self.texture_index * 0x100
            self.texture_index += 1
            uc.reg_write(arm.UC_ARM_REG_R0, texture)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, rodata: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = dict(case)
        self.case.pop("_sibling_nodes", None)
        self.texture_index = 0
        self.loaded_pointer = 0

        pages = build_case_pages(self.case)

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(RODATA_ADDR, rodata)
        self.uc.mem_write(DATA_ADDR, pages["data"])
        self.uc.mem_write(SLOT_ADDR, pages["slot"])
        self.uc.mem_write(SOURCE_ADDR, pages["source"])
        self.uc.mem_write(DESC_ADDR, pages["desc"])
        self.uc.mem_write(STRING_ADDR, pages["strings"])
        self.uc.mem_write(ASSET_ADDR, pages["asset"])
        self.uc.mem_write(TEXTURE_ADDR, pages["texture"])
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, STR_BASE_NAME)
        self.uc.reg_write(arm.UC_ARM_REG_R1, SLOT_BASE)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("user", 0x12345678))
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        expected_write_pages = (STACK_ADDR, SLOT_ADDR, TEXTURE_ADDR)
        unexpected_writes = []
        for address, size, _value in self.writes:
            if not any(
                base <= address < base + length
                for base, length in (
                    (STACK_ADDR, STACK_SIZE),
                    (SLOT_ADDR, SLOT_SIZE),
                    (TEXTURE_ADDR, TEXTURE_SIZE),
                )
            ):
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
                "slot": bytes(self.uc.mem_read(SLOT_ADDR, SLOT_SIZE)),
                "source": bytes(self.uc.mem_read(SOURCE_ADDR, SOURCE_SIZE)),
                "desc": bytes(self.uc.mem_read(DESC_ADDR, DESC_SIZE)),
                "strings": bytes(self.uc.mem_read(STRING_ADDR, STRING_SIZE)),
                "asset": bytes(self.uc.mem_read(ASSET_ADDR, ASSET_SIZE)),
                "texture": bytes(self.uc.mem_read(TEXTURE_ADDR, TEXTURE_SIZE)),
                "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
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
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            differing = [
                index for index, (left, right) in enumerate(zip(value, cand["fixtures"][key]))
                if left != right
            ]
            problems.append(
                f"fixture {key} differs at {differing[:8]} "
                f"({len(differing)} bytes)"
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
        "base_name": b"data/tex/base",
        "source_path": b"tex/spr/path",
        "desc_name": b"normal",
        "variant": 0,
        "flags": 0,
        "asset_magic": b"STEX",
        "asset_fields": dict(DEFAULT_FIELDS),
        "decoded_magic": b"STEX",
        "decoded_fields": dict(DECODED_FIELDS),
        "asset_size": 0x200,
        "load_result": "ok",
        "decode_result": "new",
        "user": 0x12345678,
    }
    case.update(overrides)
    return case


def dash_name(code: int) -> bytes:
    return b"-" + bytes([code & 0xFF])


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- plain names / base path branch
    cases.append(base_case("plain name, full parse"))
    cases.append(base_case("plain name, data+4 != 1",
                           asset_fields={**DEFAULT_FIELDS, 0x04: 2}))
    cases.append(base_case("plain name, data+4 == 1 (copy 0x3c/0x40)",
                           asset_fields={**DEFAULT_FIELDS, 0x04: 1}))
    cases.append(base_case("plain long name",
                           desc_name=b"n" * 100))
    cases.append(base_case("plain long base name",
                           base_name=b"b" * 100))

    # --- "-<byte>" sibling reference: every signed-boundary code
    for code, label in (
        (0x00, "code 0 -> slot+0x604"),
        (0x02, "code 2 -> slot+0x5c4"),
        (0x03, "code 3 -> slot+0x5a4"),
        (0x04, "code 4 -> slot+0x584"),
        (0xFF, "code -1 -> slot+0x624"),
        (0x7F, "code +127 -> slot-0x9dc"),
        (0x80, "code -128 -> slot+0x1604"),
    ):
        cases.append(
            base_case(f"dash name {label}", desc_name=dash_name(code),
                      sibling_codes=(code,), sibling_name=b"ref_spr")
        )
    cases.append(
        base_case("dash name, variant 1, flag 0x10000",
                  desc_name=dash_name(0x03), sibling_codes=(0x03,),
                  sibling_name=b"ref_spr", variant=1, flags=0x10000)
    )
    cases.append(base_case("dash name, empty sibling string",
                           desc_name=dash_name(0x02), sibling_codes=(0x02,),
                           sibling_name=b""))

    # --- variant / mode selection
    cases.append(base_case("variant 1, plain", variant=1))
    cases.append(base_case("variant 1, flag 0x10000", variant=1, flags=0x10000))
    cases.append(base_case("variant 0xFF, flag 0", variant=0xFF))
    cases.append(base_case("variant 1, flag 0x10000, data+4 == 1",
                           variant=1, flags=0x10000,
                           decoded_fields={**DECODED_FIELDS, 0x04: 1}))
    cases.append(base_case("variant 1, decode returns input",
                           variant=1, decode_result="same"))
    cases.append(base_case("flag 0x10000, variant 0",
                           flags=0x10000, asset_fields={**DEFAULT_FIELDS, 0x04: 1}))

    # --- flag rejection
    for flags in (0x1, 0x2, 0x20000, 0x10001, 0x10002, 0xFFFFFFFF, 0x0000FFFE):
        cases.append(base_case(f"rejected flags 0x{flags:08x}", flags=flags))

    # --- empty name -> strlen == 0
    cases.append(base_case("empty descriptor name", desc_name=b""))
    cases.append(base_case("empty descriptor name, variant 1",
                           desc_name=b"", variant=1))
    cases.append(base_case("dash-only name (code byte NUL)",
                           desc_name=b"-", sibling_codes=(0x00,)))

    # --- load failures
    cases.append(base_case("load returns null", load_result="null"))
    cases.append(base_case("load returns null, variant 1",
                           load_result="null", variant=1))

    # --- STEX checks
    cases.append(base_case("raw magic mismatch", asset_magic=b"XTEX"))
    cases.append(base_case("decoded magic mismatch",
                           variant=1, decoded_magic=b"XTEX"))
    cases.append(base_case("raw magic partial mismatch",
                           asset_magic=b"STEZ"))

    # --- early-complete path
    cases.append(base_case("data+0x24 non-zero",
                           asset_fields={**DEFAULT_FIELDS, 0x24: 0x1}))
    cases.append(base_case("data+0x24 non-zero with -1",
                           asset_fields={**DEFAULT_FIELDS, 0x24: 0xFFFFFFFF},
                           variant=1, flags=0x10000))

    # --- asset size arithmetic boundaries
    for size, offset in ((1, 0x100), (0x100, 0x100), (0, 0),
                         (0xFFFFFFFF, 0xFFFFFFFF), (0x80000000, 0x80000000),
                         (0x00000001, 0xFFFFFFFF)):
        cases.append(
            base_case(
                f"size 0x{size:08x} minus offset 0x{offset:08x}",
                asset_size=size,
                asset_fields={**DEFAULT_FIELDS, 0x20: offset},
            )
        )

    # --- texture object initial content drives the |= 0x10 store
    cases.append(base_case("texture sentinel in 0x2c slot",
                           texture_sentinel=0xFFFFFFFC))
    cases.append(base_case("loaded sentinel value",
                           loaded_sentinel=0x7FFFFFFF))

    # --- user argument pass-through
    for user in (0, 1, 0xFFFFFFFF, 0x80000000):
        cases.append(base_case(f"user 0x{user:08x}", user=user))

    return cases


def run_case_set(orig_code, cand_code, rodata, cases) -> int:
    passed = 0
    for case in cases:
        orig = LeafRunner().run(orig_code, rodata, case)
        cand = LeafRunner().run(cand_code, rodata, case)
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
    print("Testing engine_func_0014cae4 (0x0014CAE4)...")
    orig_code = get_orig_bytes()
    cand_code, cand_rodata = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B, "
        f"rodata {len(cand_rodata)} B (relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cand_rodata, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("cmp_suffix", 'engine_func_002b67e0(variant_name, ".cmp");',
         'engine_func_002b67e0(variant_name, ".cmq");'),
        ("mode_toggle", "const u32 load_mode = desc->variant != 0 ? (base_mode ^ 2u) : base_mode;",
         "const u32 load_mode = base_mode;"),
        ("sibling_stride", "constexpr u32 kSiblingStride = 0x20;",
         "constexpr u32 kSiblingStride = 0x10;"),
        ("size_store_offset", "*reinterpret_cast<u32*>(object + 0x28) =",
         "*reinterpret_cast<u32*>(object + 0x2C) ="),
    ):
        mutant_code, mutant_rodata = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = LeafRunner().run(orig_code, cand_rodata, case)
            try:
                bad = LeafRunner().run(mutant_code, mutant_rodata, case)
            except RuntimeError:
                # A mutant that faults where the original completes is itself a
                # detected behavioral difference.
                detected = True
                break
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
