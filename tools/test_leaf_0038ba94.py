#!/usr/bin/env python3
"""Differential test for script_vm_func_0038ba94 (0x0038BA94) with Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the candidate body, resolves
its direct calls and constant references to deterministic stubs/fixtures, and
runs the pinned original (extracted/exefs/code.bin) against it in separate
Unicorn machines with identical inputs.

Compared outputs:
  * continuation PC, final SP and callee-saved r4-r11 (r0 is recorded as a
    diagnostic only: the function is `void`, so its early/late r0 leftovers are
    not architected);
  * the ordered call log with every register argument and the architected stack
    words of engine_func_0038a364 (including the repeated entry pointer);
  * the "%s/%s" arguments read by the Thumb format stub (destination, format,
    prefix string, row name string) and the text bytes it produces;
  * self, entry arrays, payload rows, the 0x00433130 global cell, the candidate
    .rodata tables/strings and the low (null-payload) page;
  * every emulated write outside the private stack, in order.

Coverage: both mode gate branches, container/entries null gates, row count 0,
all 48 jump-table categories, out-of-range/negative signed bytes, null sub-table
and null payload results, a mutated container/mode byte between lookups, an
entry-array pointer replaced by the format stub, and multi-row mixtures.

Negative controls mutate a category-table slot, the prefix offset and the
entry "listed" byte offset; each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_0038ba94"

FUNC_ADDR = 0x0038BA94
FUNC_SIZE = 452

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x3F0000
SELF_ADDR = 0x00700000
ENTRIES_ADDR = 0x00710000
ENTRIES2_ADDR = 0x00720000
PAYLOAD_ADDR = 0x00730000
PAGE_SIZE = 0x00010000
GLOBAL_ADDR = 0x00430000
GLOBAL_SIZE = 0x00010000
RODATA_ADDR = 0x00750000
RODATA_STR_ADDR = 0x00760000
LOW_ADDR = 0x00000000
LOW_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

TABLE_ADDR = 0x00780000
CONTAINER_ADDR = 0x00781000
MANAGER_ADDR = 0x00782000
GLOBAL_CELL = 0x00433130

# Original direct-call targets. The stubs live at the same addresses so the
# original bytes and the relocated candidate reach the same code.
STUB_TBB_SUBTABLE = 0x002AC2F4
STUB_TBB_PAYLOAD = 0x002C0E9C
STUB_TBB_ROWCOUNT = 0x002C0E4C
STUB_MEM_ZERO = 0x002C4B30
STUB_FORMAT = 0x002BE7FC  # Thumb in the pinned binary; reached with BLX
STUB_RENDER = 0x0038A364

THUMB_STUBS = {STUB_FORMAT}

STUB_NAMES = {
    STUB_TBB_SUBTABLE: "Tbb_GetSubTable",
    STUB_TBB_PAYLOAD: "Tbb_GetPayloadData",
    STUB_TBB_ROWCOUNT: "Tbb_GetRowCount",
    STUB_MEM_ZERO: "engine_func_002c4b30",
    STUB_FORMAT: "ui_func_002be7fc",
    STUB_RENDER: "engine_func_0038a364",
}

# Architected stack words each helper receives.
STACK_ARGS = {
    STUB_TBB_SUBTABLE: 0,
    STUB_TBB_PAYLOAD: 0,
    STUB_TBB_ROWCOUNT: 0,
    STUB_MEM_ZERO: 0,
    STUB_FORMAT: 0,
    STUB_RENDER: 2,
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

SELF_PREFIX_OFFSET = 0x24
SELF_MODE_OFFSET = 0x45
SELF_CONTAINER_OFFSET = 0x48
SELF_ENTRIES_OFFSET = 0x4C
RECORD_STRIDE = 0x40
ENTRY_STRIDE = 0x10
ENTRY_LISTED_OFFSET = 0x0C


# --------------------------------------------------------------------- ELF I/O
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def _parse_elf(path: Path):
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
    names = []
    for section in sections:
        end = shstrtab.find(b"\x00", section[0])
        names.append(shstrtab[section[0] : end].decode("ascii", errors="replace"))

    symtab_index = names.index(".symtab")
    symtab = sections[symtab_index]
    strtab = sections[symtab[6]]
    strtab_data = data[strtab[4] : strtab[4] + strtab[5]]
    symbols = []
    for i in range(symtab[5] // 16):
        st_name, st_val, st_size, st_info, _other, st_shndx = struct.unpack_from(
            "<IIIBBH", data, symtab[4] + i * 16
        )
        end = strtab_data.find(b"\x00", st_name)
        name = strtab_data[st_name:end].decode("ascii", errors="replace")
        symbols.append((name, st_val, st_size, st_shndx))

    reloc_section = names.index(".rel.text")
    reloc = sections[reloc_section]
    relocs = []
    for i in range(reloc[5] // 8):
        r_offset, r_info = struct.unpack_from("<II", data, reloc[4] + i * 8)
        relocs.append((r_offset, r_info & 0xFF, r_info >> 8))

    return data, sections, names, symbols, relocs


def _section_bytes(data, sections, names, wanted):
    for index, name in enumerate(names):
        if name == wanted:
            section = sections[index]
            return index, data[section[4] : section[4] + section[5]]
    raise RuntimeError(f"section {wanted} not found")


def relocate_candidate(obj_file: Path):
    data, sections, names, symbols, relocs = _parse_elf(obj_file)

    text_index, text_bytes = _section_bytes(data, sections, names, ".text")
    del text_index
    func = next(
        (
            s
            for s in symbols
            if "0038ba94" in s[0] and s[2] > 0
        ),
        None,
    )
    if func is None:
        raise RuntimeError("script_vm_func_0038ba94 symbol not found")
    func_value, func_size = func[1], func[2]
    code = bytearray(text_bytes[func_value : func_value + func_size])

    rodata_index, rodata_bytes = _section_bytes(data, sections, names, ".rodata")
    str_index, str_bytes = _section_bytes(
        data, sections, names, ".rodata.str1.1"
    )

    for r_offset, r_type, sym_index in relocs:
        if not (func_value <= r_offset < func_value + func_size):
            continue
        offset = r_offset - func_value
        sym_name, _sym_value, _sym_size, sym_shndx = symbols[sym_index]
        if r_type in (28, 29):
            target = None
            for address, name in STUB_NAMES.items():
                if name in sym_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {sym_name!r}")
            pc = FUNC_ADDR + offset + 8
            delta = target - pc
            if target in THUMB_STUBS:
                if delta & 3:
                    raise RuntimeError(f"unaligned Thumb target 0x{target:08x}")
                instruction = (
                    0xFA000000
                    | ((delta >> 2) & 0x00FFFFFF)
                    | ((delta & 2) << 23)
                )
                struct.pack_into("<I", code, offset, instruction)
            else:
                original = struct.unpack_from("<I", code, offset)[0]
                cond = original & 0xFF000000
                struct.pack_into(
                    "<I", code, offset, cond | ((delta >> 2) & 0x00FFFFFF)
                )
        elif r_type == 2:  # R_ARM_ABS32
            addend = struct.unpack_from("<I", code, offset)[0]
            if sym_shndx == rodata_index:
                target = RODATA_ADDR + addend
            elif sym_shndx == str_index:
                target = RODATA_STR_ADDR + addend
            elif names[sym_shndx] == ".text":
                target = FUNC_ADDR + (addend - func_value)
            else:
                raise RuntimeError(
                    f"unhandled ABS32 section {names[sym_shndx]!r} "
                    f"(symbol {sym_name!r})"
                )
            struct.pack_into("<I", code, offset, target)
        else:
            raise RuntimeError(
                f"unhandled relocation type {r_type} for {sym_name!r}"
            )

    if b"%s/%s\x00" not in str_bytes:
        raise RuntimeError("could not locate the '%s/%s' format string")
    return bytes(code), rodata_bytes, str_bytes


def compile_candidate():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str):
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed:\n{result.stderr}")
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures
def build_self(case: dict) -> bytes:
    page = bytearray(PAGE_SIZE)
    for offset in range(0, 0x60, 4):
        struct.pack_into("<I", page, offset, 0xC0DE0000 | offset)
    prefix = case.get("prefix", b"PREFIX")
    page[SELF_PREFIX_OFFSET : SELF_PREFIX_OFFSET + len(prefix)] = prefix
    page[SELF_MODE_OFFSET] = case.get("mode", 1) & 0xFF
    container = 0 if case.get("container_null") else CONTAINER_ADDR
    entries = 0 if case.get("entries_null") else ENTRIES_ADDR
    struct.pack_into("<I", page, SELF_CONTAINER_OFFSET, container)
    struct.pack_into("<I", page, SELF_ENTRIES_OFFSET, entries)
    return bytes(page)


def build_entries(case: dict, base_marker: int) -> bytes:
    page = bytearray(PAGE_SIZE)
    for index in range(PAGE_SIZE // ENTRY_STRIDE):
        entry = index * ENTRY_STRIDE
        struct.pack_into("<I", page, entry, 0xE0000000 | (base_marker << 16) | index)
        page[entry + 0x0C] = 0xE0 | (index & 0x0F)
        page[entry + 0x0D] = 0xDD
        page[entry + 0x0E] = 0xEE
        page[entry + 0x0F] = 0xFF
    return bytes(page)


def build_payload(case: dict) -> bytes:
    page = bytearray(PAGE_SIZE)
    fill = case.get("payload_fill", 0xA5)
    for index in range(PAGE_SIZE):
        page[index] = fill & 0xFF
    categories = case.get("categories", [])
    for index, category in enumerate(categories):
        row = index * RECORD_STRIDE
        page[row] = category & 0xFF
        name = f"Row{index:02d}".encode("ascii")
        page[row + 1 : row + 1 + len(name)] = name
        page[row + 1 + len(name)] = 0
    return bytes(page)


def build_stub_region(case: dict) -> bytes:
    page = bytearray(LOW_SIZE)
    # Zero category/name bytes are what an included row sees with payload==0.
    page[0] = 0
    return bytes(page)


def read_c_string(uc, address: int, limit: int = 64) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class LeafRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(SELF_ADDR, PAGE_SIZE)
        self.uc.mem_map(ENTRIES_ADDR, PAGE_SIZE)
        self.uc.mem_map(ENTRIES2_ADDR, PAGE_SIZE)
        self.uc.mem_map(PAYLOAD_ADDR, PAGE_SIZE)
        self.uc.mem_map(RODATA_ADDR, PAGE_SIZE)
        self.uc.mem_map(RODATA_STR_ADDR, PAGE_SIZE)
        self.uc.mem_map(LOW_ADDR, LOW_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            if address in THUMB_STUBS:
                self.uc.mem_write(address, struct.pack("<H", 0x4770))  # bx lr
            else:
                self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.table_index = 0
        self.render_index = 0

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _normalise(self, value: int) -> object:
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_TBB_SUBTABLE:
            self._log(address, r0, r1)
            tables = self.case.get("tables", [TABLE_ADDR, TABLE_ADDR])
            value = tables[min(self.table_index, len(tables) - 1)]
            self.table_index += 1
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        elif address == STUB_TBB_PAYLOAD:
            self._log(address, r0)
            if self.case.get("mutate_container_on_payload"):
                uc.mem_write(
                    SELF_ADDR + SELF_CONTAINER_OFFSET, struct.pack("<I", 0)
                )
            if self.case.get("mutate_mode_on_payload"):
                uc.mem_write(SELF_ADDR + SELF_MODE_OFFSET, b"\x00")
            value = 0 if self.case.get("payload_null") else PAYLOAD_ADDR
            uc.reg_write(arm.UC_ARM_REG_R0, value)
        elif address == STUB_TBB_ROWCOUNT:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("row_count", 0) & 0xFFFFFFFF
            )
        elif address == STUB_MEM_ZERO:
            self._log(address, self._normalise(r0), r1)
            uc.mem_write(r0, b"\x00" * min(r1, STACK_SIZE))
        elif address == STUB_FORMAT:
            fmt = read_c_string(uc, r1)
            prefix = read_c_string(uc, r2)
            name = read_c_string(uc, r3)
            self._log(
                address,
                self._normalise(r0),
                fmt,
                self._normalise(r2),
                self._normalise(r3),
                prefix,
                name,
            )
            payload = (prefix + b"/" + name)[:0x7F] + b"\x00"
            uc.mem_write(r0, payload)
            if self.case.get("mutate_entries_on_format"):
                uc.mem_write(
                    SELF_ADDR + SELF_ENTRIES_OFFSET,
                    struct.pack("<I", ENTRIES2_ADDR),
                )
            uc.reg_write(arm.UC_ARM_REG_R0, len(payload) - 1)
        elif address == STUB_RENDER:
            text = read_c_string(uc, r1)
            self._log(
                address,
                r0,
                self._normalise(r1),
                self._normalise(r2),
                r3,
                text,
            )
            self.render_index += 1
            uc.reg_write(arm.UC_ARM_REG_R0, 0x0038A364)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, rodata: bytes, rodata_str: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.table_index = 0
        self.render_index = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(
            GLOBAL_ADDR,
            bytes(GLOBAL_SIZE),
        )
        self.uc.mem_write(
            GLOBAL_CELL, struct.pack("<I", MANAGER_ADDR)
        )
        self.uc.mem_write(SELF_ADDR, build_self(case))
        self.uc.mem_write(ENTRIES_ADDR, build_entries(case, 1))
        self.uc.mem_write(ENTRIES2_ADDR, build_entries(case, 2))
        self.uc.mem_write(PAYLOAD_ADDR, build_payload(case))
        self.uc.mem_write(RODATA_ADDR, rodata + bytes(PAGE_SIZE - len(rodata)))
        self.uc.mem_write(
            RODATA_STR_ADDR, rodata_str + bytes(PAGE_SIZE - len(rodata_str))
        )
        self.uc.mem_write(LOW_ADDR, build_stub_region(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=10_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected = [
            entry
            for entry in self.writes
            if not (STACK_ADDR <= entry[0] < STACK_ADDR + STACK_SIZE)
        ]

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self.call_log,
            "writes": unexpected,
            "fixtures": {
                "self": bytes(self.uc.mem_read(SELF_ADDR, PAGE_SIZE)),
                "entries": bytes(self.uc.mem_read(ENTRIES_ADDR, PAGE_SIZE)),
                "entries2": bytes(self.uc.mem_read(ENTRIES2_ADDR, PAGE_SIZE)),
                "payload": bytes(self.uc.mem_read(PAYLOAD_ADDR, PAGE_SIZE)),
                "global": bytes(self.uc.mem_read(GLOBAL_ADDR, GLOBAL_SIZE)),
                "rodata": bytes(self.uc.mem_read(RODATA_ADDR, PAGE_SIZE)),
                "rodata_str": bytes(
                    self.uc.mem_read(RODATA_STR_ADDR, PAGE_SIZE)
                ),
                "low": bytes(self.uc.mem_read(LOW_ADDR, LOW_SIZE)),
            },
        }


def compare(orig: dict, cand: dict) -> list:
    problems = []
    for key in ("pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    # The function is `void`: no return value is architected. The original
    # leaves incidental leftovers in r0 (1 after a rendered row, a table or
    # container pointer on early exits, 0 on a zero row count); the candidate's
    # register allocation produces different leftovers. r0 is recorded in the
    # result for diagnostics but is deliberately not part of equivalence.
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    if orig["writes"] != cand["writes"]:
        problems.append(
            "writes:\n    orig=" + repr(orig["writes"]) + "\n    cand="
            + repr(cand["writes"])
        )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            first = next(
                (i for i, (a, b) in enumerate(zip(value, cand["fixtures"][key])) if a != b),
                None,
            )
            problems.append(
                f"fixture {key} differs (first byte {first})"
            )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "mode": 1,
        "prefix": b"PREFIX",
        "tables": [TABLE_ADDR, TABLE_ADDR],
        "row_count": 2,
        "categories": [0x00, 0x2F],
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- early gates
    cases.append(base_case("mode 0 returns before any helper", mode=0))
    cases.append(base_case("mode 0 with null container", mode=0, container_null=True))
    cases.append(base_case("container null", container_null=True))
    cases.append(base_case("entries null", entries_null=True))
    cases.append(base_case("mode 2 is non-zero", mode=2, row_count=1))
    cases.append(base_case("mode 0xFF is non-zero", mode=0xFF, row_count=1))

    # --- row count boundary
    cases.append(base_case("row count 0", row_count=0, categories=[]))
    cases.append(base_case("row count 1 category 0", row_count=1, categories=[0x00]))
    cases.append(base_case("row count 1 category 0x2F", row_count=1, categories=[0x2F]))
    cases.append(base_case("row count 1 category 0x30", row_count=1, categories=[0x30]))
    cases.append(base_case("row count 1 category 0x31", row_count=1, categories=[0x31]))
    cases.append(base_case("row count 1 category 0x80", row_count=1, categories=[0x80]))
    cases.append(base_case("row count 1 category 0xFF", row_count=1, categories=[0xFF]))

    # --- every jump-table slot exactly once
    cases.append(
        base_case(
            "all 48 categories",
            row_count=48,
            categories=list(range(48)),
        )
    )

    # --- signed / out-of-range mixture around the table edge
    cases.append(
        base_case(
            "signed and out-of-range mixture",
            row_count=6,
            categories=[0x80, 0xFF, 0x30, 0x31, 0x2F, 0x00],
        )
    )
    cases.append(
        base_case(
            "excluded list holes",
            row_count=7,
            categories=[0x07, 0x0C, 0x10, 0x14, 0x16, 0x1D, 0x20],
        )
    )

    # --- null helper results
    cases.append(
        base_case(
            "first sub-table null",
            tables=[0, TABLE_ADDR],
            row_count=2,
            categories=[0x00, 0x01],
        )
    )
    cases.append(
        base_case(
            "second sub-table null",
            tables=[TABLE_ADDR, 0],
            row_count=2,
            categories=[0x00, 0x01],
        )
    )
    cases.append(
        base_case(
            "payload null reads address zero",
            payload_null=True,
            row_count=3,
            categories=[],
        )
    )

    # --- state mutated by a helper between reads
    cases.append(
        base_case(
            "container cleared during payload lookup",
            mutate_container_on_payload=True,
            row_count=4,
            categories=[0x00, 0x01, 0x02, 0x03],
        )
    )
    cases.append(
        base_case(
            "mode cleared during payload lookup",
            mutate_mode_on_payload=True,
            row_count=4,
            categories=[0x00, 0x01, 0x02, 0x03],
        )
    )
    cases.append(
        base_case(
            "entry array replaced by format stub",
            mutate_entries_on_format=True,
            row_count=3,
            categories=[0x00, 0x15, 0x2F],
        )
    )

    # --- multi-row mixtures with distinct names
    cases.append(
        base_case(
            "mixed rows 0x00 0x0D 0x21 0x2F",
            row_count=4,
            categories=[0x00, 0x0D, 0x21, 0x2F],
        )
    )
    cases.append(
        base_case(
            "prefix and fill variation",
            prefix=b"SECONDARY/PATH",
            payload_fill=0x5A,
            row_count=3,
            categories=[0x17, 0x0B, 0x06],
        )
    )
    return cases


def run_case_set(orig_code, cand_code, rodata, rodata_str, cases) -> int:
    passed = 0
    for case in cases:
        orig = LeafRunner().run(orig_code, rodata, rodata_str, case)
        cand = LeafRunner().run(cand_code, rodata, rodata_str, case)
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
    print("Testing script_vm_func_0038ba94 (0x0038BA94)...")
    orig_code = get_orig_bytes()
    cand_code, rodata, rodata_str = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B, "
        f"rodata {len(rodata)} B, rodata.str1.1 {len(rodata_str)} B."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, rodata, rodata_str, cases)

    print("\nNegative controls:")
    controls = (
        (
            "category_table_slot",
            "1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0,",
            "1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0,",
        ),
        ("prefix_offset", "kPrefixOffset = 0x24;", "kPrefixOffset = 0x25;"),
        (
            "entry_listed_offset",
            "kEntryListedOffset = 0x0c;",
            "kEntryListedOffset = 0x0d;",
        ),
    )
    for name, old, new in controls:
        mutant_code, mutant_rodata, mutant_str = compile_candidate_mutant(
            name, old, new
        )
        detected = False
        for case in cases:
            orig = LeafRunner().run(orig_code, rodata, rodata_str, case)
            bad = LeafRunner().run(mutant_code, mutant_rodata, mutant_str, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
