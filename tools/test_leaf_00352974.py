#!/usr/bin/env python3
"""Differential test for ui_func_00352974 (0x00352974) using Unicorn ARM.

Compiles src/engine/leaf_batch45_b.cpp, extracts the ui_func_00352974 body and
resolves its direct calls to deterministic stubs that live at the original
target addresses. The pinned original (extracted/exefs/code.bin) and the
relocated candidate then run in separate Unicorn machines with identical
fixtures.

Observed and compared:
  * continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log, including the 5th/6th stack arguments of the second
    lookup and the UTF-8 / UTF-16 payloads handed between helpers;
  * the full 8-byte destination value and the entire out page, so narrower or
    wider stores are detected;
  * the key page and holder page (must remain unmodified);
  * all writes outside the private emulated stack (must stay in the out page).

Coverage:
  * zero key pair, low-word-only, high-word-only and both-word keys;
  * lookup status: special icon tag 0x11 with indices 99/100/179/180 plus tag
    0x10/0x12 controls, negative statuses (including a negative special tag),
    and non-negative statuses that take the second lookup;
  * holder present/absent on every path;
  * second lookup negative, zero and positive with argument/stack-word checks;
  * caller id (r3) values 0, 0xFFFF, 0x1234ABCD, 0xFFFFFFFF and several a2
    values, proving no unintended 16-bit truncation in the candidate.

Negative controls mutate the zero-key constant, the special-icon lower index
bound, the second lookup stack word and the descriptor byte-length formula; each
mutant must be detected. The helpers are stubs: this test does not establish the
behavior of 0x2BAD80, 0x23A2EC, 0x2ACB3C, 0x2B5C2C, 0x355F78, 0x2A4DF0 or
0x2B93F0, nor any real resource-table lookup.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_00352974"

FUNC_ADDR = 0x00352974
FUNC_SIZE = 444

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000
OUT_ADDR = 0x00710000
OUT_SIZE = 0x00001000
KEY_ADDR = 0x00720000
KEY_SIZE = 0x00001000
HOLDER_ADDR = 0x00730000
HOLDER_SIZE = 0x00001000
RODATA_ADDR = 0x00750000
RODATA_SIZE = 0x00002000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets. Stubs sit at the same addresses so the pinned
# original and the relocated candidate both reach them.
STUB_2BAD80 = 0x002BAD80
STUB_23A2EC = 0x0023A2EC
STUB_2ACB3C = 0x002ACB3C
STUB_2B5C2C = 0x002B5C2C
STUB_355F78 = 0x00355F78
STUB_2A4DF0 = 0x002A4DF0
STUB_2B93F0 = 0x002B93F0

# 0x2ACB3C and 0x2B5C2C are Thumb callable in the pinned image (the original
# reaches them with BLX); 0x23A2EC forwards to an ARM formatter.
THUMB_STUBS = {STUB_2ACB3C, STUB_2B5C2C}

STUB_NAMES = {
    STUB_2BAD80: "engine_func_002bad80",
    STUB_23A2EC: "ui_func_0023a2ec",
    STUB_2ACB3C: "ui_func_002acb3c",
    STUB_2B5C2C: "ui_func_002b5c2c",
    STUB_355F78: "ui_func_00355f78",
    STUB_2A4DF0: "ui_func_002a4df0",
    STUB_2B93F0: "engine_func_002b93f0",
}

# Architected stack words each helper receives.
STACK_ARGS = {
    STUB_2BAD80: 0,
    STUB_23A2EC: 0,
    STUB_2ACB3C: 0,
    STUB_2B5C2C: 0,
    STUB_355F78: 1,   # lookup flag
    STUB_2A4DF0: 2,   # caller a2, 0x1200
    STUB_2B93F0: 0,
}

RODATA_SECTIONS = {
    ".rodata.str1.1": RODATA_ADDR + 0x0000,
    ".rodata": RODATA_ADDR + 0x0800,
    ".rodata.cst16": RODATA_ADDR + 0x0C00,
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


# --------------------------------------------------------------------- ELF I/O
def parse_elf(path: Path) -> dict:
    data = path.read_bytes()
    if data[:4] != b"\x7fELF":
        raise RuntimeError(f"{path} is not an ELF file")
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    e_shstrndx = struct.unpack_from("<H", data, 50)[0]
    raw = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr = raw[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]

    def section_name(offset: int) -> str:
        end = shstrtab.find(b"\x00", offset)
        return shstrtab[offset:end].decode("ascii", errors="replace")

    sections = []
    for index, sec in enumerate(raw):
        sections.append(
            {
                "name": section_name(sec[0]),
                "type": sec[1],
                "offset": sec[4],
                "size": sec[5],
                "link": sec[6],
                "info": sec[7],
                "entsize": sec[9],
            }
        )

    symtab_index = next(
        (i for i, sec in enumerate(sections) if sec["type"] == 2), None
    )
    if symtab_index is None:
        raise RuntimeError(f"{path} has no symbol table")
    symtab = sections[symtab_index]
    strtab_sec = sections[symtab["link"]]
    strtab = data[strtab_sec["offset"] : strtab_sec["offset"] + strtab_sec["size"]]

    def symbol_name(offset: int) -> str:
        end = strtab.find(b"\x00", offset)
        return strtab[offset:end].decode("ascii", errors="replace")

    symbols = []
    entsize = symtab["entsize"] or 16
    for i in range(symtab["size"] // entsize):
        pos = symtab["offset"] + i * entsize
        st_name, st_value, st_size, st_info, _other, st_shndx = struct.unpack_from(
            "<IIIBBH", data, pos
        )
        symbols.append(
            {
                "name": symbol_name(st_name),
                "value": st_value & ~1,
                "size": st_size,
                "type": st_info & 0x0F,
                "shndx": st_shndx,
            }
        )

    relocations: dict[int, list] = {}
    for sec in sections:
        if sec["type"] != 9:  # SHT_REL
            continue
        entries = []
        entsize = sec["entsize"] or 8
        for i in range(sec["size"] // entsize):
            pos = sec["offset"] + i * entsize
            r_offset, r_info = struct.unpack_from("<II", data, pos)
            entries.append((r_offset, r_info & 0xFF, r_info >> 8))
        relocations[sec["info"]] = entries

    return {
        "data": data,
        "sections": sections,
        "symbols": symbols,
        "relocations": relocations,
    }


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def _stub_for_symbol(symbol_name: str) -> int | None:
    if not symbol_name:
        return None
    for address in STUB_NAMES:
        if f"{address:08x}" in symbol_name:
            return address
    return None


def relocate_candidate(obj_file: Path) -> tuple[bytes, dict[str, bytes]]:
    elf = parse_elf(obj_file)
    symbols = elf["symbols"]
    sections = elf["sections"]

    target_index = None
    target_symbol = None
    for index, sym in enumerate(symbols):
        if (
            sym["type"] == 2
            and "00352974" in sym["name"]
            and 0 < sym["shndx"] < len(sections)
        ):
            target_index = index
            target_symbol = sym
            break
    if target_symbol is None:
        available = [s["name"] for s in symbols if "352974" in s["name"]]
        raise RuntimeError(
            f"ui_func_00352974 not found in {obj_file}: {available}"
        )

    section = sections[target_symbol["shndx"]]
    start = section["offset"] + target_symbol["value"]
    code = bytearray(elf["data"][start : start + target_symbol["size"]])

    resolved_calls = 0
    for offset, rtype, sym_index in elf["relocations"].get(
        target_symbol["shndx"], []
    ):
        if not (
            target_symbol["value"]
            <= offset
            < target_symbol["value"] + target_symbol["size"]
        ):
            continue
        rel_off = offset - target_symbol["value"]
        symbol = symbols[sym_index]
        if rtype in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = _stub_for_symbol(symbol["name"])
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {symbol['name']}")
            resolved_calls += 1
            pc = FUNC_ADDR + rel_off + 8
            displacement = target - pc
            if target in THUMB_STUBS:
                if displacement & 3:
                    raise RuntimeError(
                        f"unaligned Thumb call target 0x{target:08x}"
                    )
                instruction = (
                    0xFA000000
                    | ((displacement >> 2) & 0x00FFFFFF)
                    | ((displacement & 2) << 23)
                )
            else:
                world = struct.unpack_from("<I", code, rel_off)[0]
                cond = world & 0xFF000000
                instruction = cond | ((displacement >> 2) & 0x00FFFFFF)
            struct.pack_into("<I", code, rel_off, instruction)
        elif rtype == 2:  # R_ARM_ABS32 into a read-only constant
            base = RODATA_SECTIONS.get(symbol["name"])
            if base is None and 0 < symbol["shndx"] < len(sections):
                base = RODATA_SECTIONS.get(sections[symbol["shndx"]]["name"])
            if base is None:
                raise RuntimeError(
                    f"unresolved absolute relocation: {symbol['name']!r}"
                )
            addend = struct.unpack_from("<I", code, rel_off)[0]
            struct.pack_into("<I", code, rel_off, base + symbol["value"] + addend)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rtype} for {symbol['name']!r}"
            )

    if resolved_calls != 8:
        raise RuntimeError(f"expected 8 direct calls, resolved {resolved_calls}")

    rodata: dict[str, bytes] = {}
    for name, _base in RODATA_SECTIONS.items():
        section = next((s for s in sections if s["name"] == name), None)
        if section is not None:
            rodata[name] = elf["data"][
                section["offset"] : section["offset"] + section["size"]
            ]
    if b"/icons/%u.icn\x00" not in rodata.get(".rodata", b""):
        raise RuntimeError("icon format string missing from .rodata")
    return bytes(code), rodata


def compile_candidate_baseline() -> tuple[bytes, dict[str, bytes]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_b.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(
    name: str, old: str, new: str
) -> tuple[bytes, dict[str, bytes]]:
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
def build_key(case: dict) -> bytes:
    page = bytearray(KEY_SIZE)
    for index in range(0, KEY_SIZE, 4):
        struct.pack_into("<I", page, index, 0x5A5A0000 | (index & 0xFFFF))
    struct.pack_into("<I", page, 0, case.get("key_low", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 4, case.get("key_high", 0) & 0xFFFFFFFF)
    return bytes(page)


def build_out(case: dict) -> bytes:
    page = bytearray(OUT_SIZE)
    for index in range(0, OUT_SIZE, 4):
        struct.pack_into("<I", page, index, 0xCDCD0000 | (index & 0xFFFF))
    return bytes(page)


def build_holder_page() -> bytes:
    page = bytearray(HOLDER_SIZE)
    for index in range(0, HOLDER_SIZE, 4):
        struct.pack_into("<I", page, index, 0xABAB0000 | (index & 0xFFFF))
    return bytes(page)


def read_c_string(uc, address: int, limit: int = 64) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


def read_utf16(uc, address: int, limit: int = 64) -> bytes:
    out = bytearray()
    for index in range(limit):
        unit = struct.unpack("<H", uc.mem_read(address + 2 * index, 2))[0]
        if unit == 0:
            break
        out.append(unit & 0xFF)
    return bytes(out)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(OUT_ADDR, OUT_SIZE)
        self.uc.mem_map(KEY_ADDR, KEY_SIZE)
        self.uc.mem_map(HOLDER_ADDR, HOLDER_SIZE)
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

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _normalise_pointer(self, value: int) -> int | str:
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args + self._stack_words(
            STACK_ARGS[address])))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2BAD80:
            self._log(address, self._normalise_pointer(r0), r1)
            high = 0x5A5A0000 | ((r1 * 2654435761) & 0xFFFF)
            uc.mem_write(r0, struct.pack("<II", r1 & 0xFFFFFFFF, high))
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_23A2EC:
            fmt = read_c_string(uc, r2)
            self._log(address, r1, fmt, r3)
            payload = b"/icons/" + str(r3).encode("ascii") + b".icn"
            payload = payload[: max(0, r1 - 1)]
            uc.mem_write(r0, payload + b"\x00")
            uc.reg_write(arm.UC_ARM_REG_R0, len(payload))
        elif address == STUB_2ACB3C:
            src = read_c_string(uc, r1)
            self._log(address, self._normalise_pointer(r0), src, r2)
            count = 0
            text = bytearray()
            for index in range(r2):
                byte = 0
                if index < len(src):
                    byte = src[index]
                uc.mem_write(r0 + 2 * index, struct.pack("<H", byte))
                if byte == 0:
                    break
                text.append(byte)
                count += 1
            uc.reg_write(arm.UC_ARM_REG_R0, count)
        elif address == STUB_2B5C2C:
            text = read_utf16(uc, r0)
            self._log(address, text)
            uc.reg_write(arm.UC_ARM_REG_R0, len(text))
        elif address == STUB_355F78:
            desc_type, desc_text, desc_len = struct.unpack("<III",
                                                           uc.mem_read(r3, 12))
            text = read_utf16(uc, desc_text, max(1, min(desc_len // 2, 64)))
            self._log(address, self._normalise_pointer(r0), r1, r2, desc_type,
                      text, desc_len)
            if self.case.get("holder_write", True):
                uc.mem_write(r0, struct.pack("<I", HOLDER_ADDR))
            uc.reg_write(arm.UC_ARM_REG_R0,
                         self.case["status"] & 0xFFFFFFFF)
        elif address == STUB_2A4DF0:
            self._log(address, self._normalise_pointer(r0), r1, r2, r3)
            second = self.case["second_status"] & 0xFFFFFFFF
            uc.mem_write(r0, struct.pack("<II", 0x51000000 | (second & 0xFFFF),
                                         second))
            uc.reg_write(arm.UC_ARM_REG_R0, second)
        elif address == STUB_2B93F0:
            self._log(address, r0)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for name, args in log:
            normalised.append((name, args))
        return normalised

    def run(self, code: bytes, rodata: dict[str, bytes], case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(OUT_ADDR, build_out(case))
        self.uc.mem_write(KEY_ADDR, build_key(case))
        self.uc.mem_write(HOLDER_ADDR, build_holder_page())
        self.uc.mem_write(RODATA_ADDR, b"\x00" * RODATA_SIZE)
        for name, base in RODATA_SECTIONS.items():
            payload = rodata.get(name)
            if payload:
                self.uc.mem_write(base, payload)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OUT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, KEY_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("a2", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("a3", 0) & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        external_writes = sorted(
            {
                address
                for address, _size in self.writes
                if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
            }
        )

        out_page = bytes(self.uc.mem_read(OUT_ADDR, OUT_SIZE))
        return {
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "out_page": out_page,
            "out_value": struct.unpack_from("<Q", out_page, 0)[0],
            "key_page": bytes(self.uc.mem_read(KEY_ADDR, KEY_SIZE)),
            "holder_page": bytes(self.uc.mem_read(HOLDER_ADDR, HOLDER_SIZE)),
            "external_writes": external_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"])
            + "\n    cand=" + repr(cand["call_log"])
        )
    if orig["out_page"] != cand["out_page"]:
        differing = [
            index
            for index, (left, right) in enumerate(
                zip(orig["out_page"], cand["out_page"])
            )
            if left != right
        ]
        problems.append(f"out page differs at offsets {differing[:16]}")
    if orig["key_page"] != cand["key_page"]:
        problems.append("key page was modified differently")
    if orig["holder_page"] != cand["holder_page"]:
        problems.append("holder page was modified differently")
    if orig["external_writes"] != cand["external_writes"]:
        problems.append(
            "external writes:\n    orig="
            + repr(orig["external_writes"])
            + "\n    cand="
            + repr(cand["external_writes"])
        )
    for value in orig["external_writes"]:
        if not (OUT_ADDR <= value < OUT_ADDR + OUT_SIZE):
            problems.append(f"write outside the out page at 0x{value:08x}")
    return problems


# ------------------------------------------------------------------- test cases
def make_cases() -> list[dict]:
    cases: list[dict] = []

    def add(name: str, **fields) -> None:
        case = {
            "name": name,
            "key_low": 0x12345678,
            "key_high": 0x9ABCDEF0,
            "a2": 0x11112222,
            "a3": 0x0000ABCD,
            "status": 0,
            "second_status": 0,
            "holder_write": True,
        }
        case.update(fields)
        cases.append(case)

    # Zero key short circuit: helpers other than 0x2BAD80 must not run.
    add("zero key", key_low=0, key_high=0, status=0xFFFFFFFF, a2=0xDEADBEEF)
    add("zero key with id", key_low=0, key_high=0, a3=0)

    # Key halves: only one word must be nonzero to take the slow path.
    add("low key only", key_low=1, key_high=0, status=0xFFFFFFFF)
    add("high key only", key_low=0, key_high=1, status=0xFFFFFFFF)
    add("both key words", key_low=0xFFFFFFFF, key_high=0xFFFFFFFF,
        status=0xFFFFFFFF)

    # Special icon tag: index boundaries 99/100/179/180 plus tag controls.
    for index in (0, 99, 100, 140, 179, 180, 1023):
        status = (0x11 << 10) | index
        for holder_write in (True, False):
            add(f"special tag index {index} holder={holder_write}",
                status=status, holder_write=holder_write,
                second_status=0x7FFFFFFF)
    add("special tag index 140 negative status",
        status=0xFFFF0000 | (0x11 << 10) | 140, second_status=0xFFFFFFFF)
    for tag in (0x10, 0x12, 0x00, 0xFF):
        add(f"tag 0x{tag:02x} index 140", status=(tag << 10) | 140,
            second_status=0)

    # Negative status (not the special tag) decodes the status directly.
    for status in (0x80000000, 0x800003FF, 0xFFFFFFFF, 0xA5A5A5A5):
        for holder_write in (True, False):
            add(f"negative status 0x{status:08x} holder={holder_write}",
                status=status, holder_write=holder_write)

    # Non-negative statuses that take the second lookup.
    for status in (0, 1, 0x7FFFFFFF, (0x11 << 10) | 99, (0x11 << 10) | 180):
        for second in (-1, 0, 0x7FFFFFFF, 0x80000000):
            add(f"second lookup status 0x{status:08x} -> 0x{second & 0xFFFFFFFF:08x}",
                status=status, second_status=second)
        add(f"second lookup status 0x{status:08x} no holder",
            status=status, second_status=1, holder_write=False)

    # Caller-supplied id and stack argument widths.
    for a3 in (0, 0xFFFF, 0x1234ABCD, 0xFFFFFFFF):
        add(f"id 0x{a3:08x}", a3=a3, status=0xFFFFFFFF)
    for a2 in (0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        add(f"arg2 0x{a2:08x}", a2=a2, status=0, second_status=-1)

    return cases


def run_case_set(orig_code, cand_code, rodata, cases) -> int:
    passed = 0
    for case in cases:
        original = Runner().run(orig_code, rodata, case)
        candidate = Runner().run(cand_code, rodata, case)
        problems = compare(original, candidate)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(original['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing ui_func_00352974 (0x00352974)...")
    orig_code = get_orig_bytes()
    cand_code, rodata = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B, "
        f"rodata {sum(len(v) for v in rodata.values())} B (relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, rodata, cases)

    print("\nNegative controls:")
    controls = (
        ("zero_key_constant", "kZeroKeyDefault = 0xE0A13882u",
         "kZeroKeyDefault = 0xE0A13883u"),
        ("special_index_min", "kIconIndexMin = 100u",
         "kIconIndexMin = 99u"),
        ("second_stack_word", "kSecondLookupStack1 = 0x1200u",
         "kSecondLookupStack1 = 0x1201u"),
        ("descriptor_length", "descriptor[2] = (units + 1) * 2;",
         "descriptor[2] = (units + 2) * 2;"),
    )
    for name, old, new in controls:
        mutant_code, mutant_rodata = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            original = Runner().run(orig_code, mutant_rodata, case)
            bad = Runner().run(mutant_code, mutant_rodata, case)
            if compare(original, bad):
                detected = True
                print(f"  [PASS] {name} detected by {case['name']}")
                break
        if not detected:
            print(f"  [FAIL] negative control not detected: {name}")
            raise SystemExit(1)

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
