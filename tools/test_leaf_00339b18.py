#!/usr/bin/env python3
"""Differential test for engine_func_00339b18 (0x00339b18) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the engine_func_00339b18
body, relocates its direct calls and inline switch table, and runs the pinned
original (extracted/exefs/code.bin) against the candidate in separate Unicorn
machines with identical fixtures.

Observed and compared:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every register argument and the architected
    stack arguments of each helper (none of the five helpers uses stack args);
  * the full 0x10000-byte battle-main work page, the twelve party-slot pages,
    the 0x2B087C record pages, the 0x294334 creation pages, the registry
    records and the (empty) rodata page;
  * every emulated write outside those fixture pages.

Coverage:
  * the four preset ids and all four valid party counts (1..4);
  * the auto-scan path for party counts 0, 5 and 0xFFFFFFFF, including the
    twelve-slot boundary (only slot 11 non-zero), the four-id cap, and slots
    8..11 selected after zeros;
  * flag bit 0x40 set with otherwise irrelevant party counts and flag values
    0, 0x40, 0xBF, 0xFFFFFFFF;
  * signed s16 boundaries -0x8000, 0x7FFF, -1 and 0 read from record+0x88;
  * registry hits, misses, partial tables and a completely full table (the
    original appends without inserting when no free slot exists);
  * duplicate collected values, which match the record inserted by the first
    occurrence, and the collected != appended return value.

Negative controls mutate the first preset id, the slot count, the flag bit,
the scan bound, both record offsets, the scratch sizes and the return value;
each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_00339b18"

FUNC_ADDR = 0x00339B18
FUNC_SIZE = 640

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00400000  # covers the function and every stub below 0x3F0000
WORK_ADDR = 0x00600000
WORK_SIZE = 0x00010000
PARTY_ADDR = 0x00700000
PARTY_SIZE = 0x00010000
RECORD_ADDR = 0x00710000
RECORD_SIZE = 0x00010000
CREATE_ADDR = 0x00720000
CREATE_SIZE = 0x00010000
REGREC_ADDR = 0x00730000
REGREC_SIZE = 0x00010000
RODATA_ADDR = 0x00740000
RODATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2C4450 = 0x002C4450
STUB_2C4B30 = 0x002C4B30
STUB_2B087C = 0x002B087C
STUB_26F25C = 0x0026F25C
STUB_294334 = 0x00294334

STUB_NAMES = {
    STUB_2C4450: "camp_func_002c4450",
    STUB_2C4B30: "engine_func_002c4b30",
    STUB_2B087C: "battle_func_002b087c",
    STUB_26F25C: "camp_func_0026f25c",
    STUB_294334: "engine_func_00294334",
}

STACK_ARGS = {
    STUB_2C4450: 0,
    STUB_2C4B30: 0,
    STUB_2B087C: 0,
    STUB_26F25C: 0,
    STUB_294334: 0,
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

REGISTRY_OFFSET = 0x2134
REGISTRY_COUNT = 42
SLOT_OFFSET = 0x1FE4
PARTY_COUNT_OFFSET = 0x2F34
CLEAR_OFFSET = 0x357C
CLEAR_SIZE = 0xE10
ADDED_COUNT_OFFSET = 0x438C
COLLECTED_COUNT_OFFSET = 0x4390
SELECTED_OFFSET = 0x43A8
SELECTED_COUNT = 42
FLAGS_OFFSET = 0x44A8
PARTY_ID_OFFSET = 0x48
LOOKUP_VALUE_OFFSET = 0x88
REGISTRY_RECORD_STRIDE = 0x40
PAGE_STRIDE = 0x100

FIXTURE_PAGES = (
    (STACK_ADDR, STACK_SIZE),
    (WORK_ADDR, WORK_SIZE),
    (PARTY_ADDR, PARTY_SIZE),
    (RECORD_ADDR, RECORD_SIZE),
    (CREATE_ADDR, CREATE_SIZE),
    (REGREC_ADDR, REGREC_SIZE),
    (RODATA_ADDR, RODATA_SIZE),
)


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def elf_symbol_value(obj_file: Path, wanted: str) -> int:
    data = obj_file.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    symtab = next(s for s in sections if s[1] == 2)
    strtab = sections[symtab[6]]
    entsize = symtab[9] or 16
    for i in range(symtab[5] // entsize):
        st_name, st_val, _st_size, _st_info, _st_other, _st_shndx = (
            struct.unpack_from("<IIIBBH", data, symtab[4] + i * entsize)
        )
        name = data[strtab[4] + st_name :].split(b"\x00")[0].decode(
            "ascii", errors="replace"
        )
        if name == wanted:
            return st_val & ~1
    raise RuntimeError(f"symbol {wanted} not found in {obj_file}")


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    if "engine_func_00339b18" not in funcs:
        raise RuntimeError(
            f"engine_func_00339b18 not found in {obj_file}: {sorted(funcs)}"
        )
    code_raw, relocs = funcs["engine_func_00339b18"]
    code = bytearray(code_raw)
    func_sym = elf_symbol_value(obj_file, "engine_func_00339b18")

    for rel in relocs:
        symbol = rel.symbol_name
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = None
            for address, name in STUB_NAMES.items():
                if name in symbol:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {symbol!r}")
            displacement = (target - (FUNC_ADDR + rel.offset + 8)) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32 (inline switch table)
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if symbol in ("", ".text"):
                target = FUNC_ADDR + (addend - func_sym)
            else:
                raise RuntimeError(
                    f"unexpected ABS32 relocation against {symbol!r}"
                )
            struct.pack_into("<I", code, rel.offset, target)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {symbol!r}"
            )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
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
def sentinel_page(size: int, base: int) -> bytearray:
    page = bytearray(size)
    for offset in range(0, size, 4):
        struct.pack_into("<I", page, offset, base | (offset & 0xFFFF))
    return page


def build_work(case: dict) -> bytes:
    page = sentinel_page(WORK_SIZE, 0xA5A50000)

    present = case.get("registry_present", {})
    full = case.get("registry_full", False)
    for slot in range(REGISTRY_COUNT):
        if full or slot in present:
            pointer = REGREC_ADDR + slot * REGISTRY_RECORD_STRIDE
        else:
            pointer = 0
        struct.pack_into("<I", page, REGISTRY_OFFSET + slot * 4, pointer)

    for slot in range(REGISTRY_COUNT):
        struct.pack_into(
            "<II", page, SLOT_OFFSET + slot * 8,
            0x11110000 + slot, 0x22220000 + slot,
        )

    struct.pack_into(
        "<I", page, PARTY_COUNT_OFFSET, case.get("party_count", 1) & 0xFFFFFFFF
    )
    page[CLEAR_OFFSET : CLEAR_OFFSET + CLEAR_SIZE] = b"\x5A" * CLEAR_SIZE
    struct.pack_into("<i", page, ADDED_COUNT_OFFSET, -12345)
    struct.pack_into("<i", page, COLLECTED_COUNT_OFFSET, -54321)
    for slot in range(SELECTED_COUNT):
        struct.pack_into("<I", page, SELECTED_OFFSET + slot * 4, 0x77770000 + slot)
    struct.pack_into("<I", page, FLAGS_OFFSET, case.get("flags", 0) & 0xFFFFFFFF)
    return bytes(page)


def build_registry_records(case: dict) -> bytes:
    page = sentinel_page(REGREC_SIZE, 0xB0B00000)
    present = case.get("registry_present", {})
    ids = case.get("registry_ids", {})
    full = case.get("registry_full", False)
    for slot in range(REGISTRY_COUNT):
        if full or slot in present:
            value = ids.get(slot, 0x3000 + slot)
            struct.pack_into("<i", page, slot * REGISTRY_RECORD_STRIDE + 4, value)
    return bytes(page)


def build_party(case: dict) -> bytes:
    page = sentinel_page(PARTY_SIZE, 0xC0C00000)
    ids = case.get("party_ids", [0] * 12)
    for index in range(12):
        value = ids[index] if index < len(ids) else 0
        struct.pack_into(
            "<H", page, index * PAGE_STRIDE + PARTY_ID_OFFSET, value & 0xFFFF
        )
    return bytes(page)


def build_records(case: dict) -> bytes:
    page = sentinel_page(RECORD_SIZE, 0xD0D00000)
    values = case.get("lookup_values", [])
    for index in range(16):
        value = values[index] if index < len(values) else 0x0100 + index
        struct.pack_into("<h", page, index * PAGE_STRIDE + LOOKUP_VALUE_OFFSET, value)
    return bytes(page)


def build_rodata() -> bytes:
    return b"\x00" * RODATA_SIZE


def read_c_string(uc, address: int, limit: int = 32) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class SetupRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(PARTY_ADDR, PARTY_SIZE)
        self.uc.mem_map(RECORD_ADDR, RECORD_SIZE)
        self.uc.mem_map(CREATE_ADDR, CREATE_SIZE)
        self.uc.mem_map(REGREC_ADDR, REGREC_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
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
        self.lookup_index = 0
        self.create_index = 0
        self.case: dict = {}

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]))
        )

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2C4450:
            self._log(address, r0, r1, r2)
            uc.mem_write(r0, bytes([r2 & 0xFF]) * r1)
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_2C4B30:
            self._log(address, r0, r1)
            uc.mem_write(r0, b"\x00" * r1)
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_2B087C:
            self._log(address, r0)
            index = self.lookup_index
            self.lookup_index += 1
            uc.reg_write(arm.UC_ARM_REG_R0, RECORD_ADDR + index * PAGE_STRIDE)
        elif address == STUB_26F25C:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, PARTY_ADDR + (r0 & 0xFF) * PAGE_STRIDE)
        elif address == STUB_294334:
            self._log(address, r0, r1)
            index = self.create_index
            self.create_index += 1
            record = CREATE_ADDR + index * PAGE_STRIDE
            signed = r0 - (1 << 32) if r0 & 0x80000000 else r0
            uc.mem_write(record + 4, struct.pack("<i", signed))
            uc.reg_write(arm.UC_ARM_REG_R0, record)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for name, args in log:
            out = []
            for arg in args:
                if isinstance(arg, int) and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE:
                    out.append("<stack>")
                else:
                    out.append(arg)
            normalised.append((name, tuple(out)))
        return normalised

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.lookup_index = 0
        self.create_index = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(WORK_ADDR, build_work(case))
        self.uc.mem_write(PARTY_ADDR, build_party(case))
        self.uc.mem_write(RECORD_ADDR, build_records(case))
        self.uc.mem_write(CREATE_ADDR, bytes(sentinel_page(CREATE_SIZE, 0xE0E00000)))
        self.uc.mem_write(REGREC_ADDR, build_registry_records(case))
        self.uc.mem_write(RODATA_ADDR, build_rodata())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, WORK_ADDR)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        pages = {
            "work": bytes(self.uc.mem_read(WORK_ADDR, WORK_SIZE)),
            "party": bytes(self.uc.mem_read(PARTY_ADDR, PARTY_SIZE)),
            "records": bytes(self.uc.mem_read(RECORD_ADDR, RECORD_SIZE)),
            "create": bytes(self.uc.mem_read(CREATE_ADDR, CREATE_SIZE)),
            "regrec": bytes(self.uc.mem_read(REGREC_ADDR, REGREC_SIZE)),
            "rodata": bytes(self.uc.mem_read(RODATA_ADDR, RODATA_SIZE)),
        }

        unexpected_writes = []
        for address, size in self.writes:
            allowed = any(
                base <= address < base + length for base, length in FIXTURE_PAGES
            )
            if not allowed:
                unexpected_writes.append((address, size))

        work = pages["work"]
        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "pages": pages,
            "collected": struct.unpack_from("<i", work, COLLECTED_COUNT_OFFSET)[0],
            "added": struct.unpack_from("<i", work, ADDED_COUNT_OFFSET)[0],
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"])
            + "\n    cand=" + repr(cand["call_log"])
        )
    for key, value in orig["pages"].items():
        if value != cand["pages"][key]:
            differing = [
                i for i, (a, b) in enumerate(zip(value, cand["pages"][key]))
                if a != b
            ]
            problems.append(
                f"page {key} differs at {len(differing)} byte(s), first "
                f"offsets {[hex(i) for i in differing[:16]]}"
            )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {"name": name, "flags": 0, "party_count": 1}
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- preset path: flag bit 0x40, four fixed ids
    cases.append(base_case("flag 0x40 selects the four presets", flags=0x40,
                           party_count=0))
    cases.append(base_case("flag 0xFFFFFFFF still selects the presets",
                           flags=0xFFFFFFFF, party_count=1))
    cases.append(base_case("flag 0x40 with party count 0xFFFFFFFF",
                           flags=0x40, party_count=0xFFFFFFFF))
    cases.append(base_case("flag 0x40 with a distinct preset value set",
                           flags=0x40, lookup_values=[0x100, 0x200, 0x300, 0x400]))

    # --- preset path: party counts 1..4 use the first N presets
    for count in (1, 2, 3, 4):
        cases.append(base_case(f"party count {count} selects {count} preset(s)",
                               party_count=count))
    for flags in (0x00, 0xBF, 0x01, 0x80):
        cases.append(base_case(f"flag 0x{flags:02x} uses the party count",
                               flags=flags, party_count=3))

    # --- auto-scan path: invalid party counts
    for count in (0, 5, 6, 0xFFFFFFFF):
        cases.append(base_case(f"party count 0x{count:08x} auto-scans",
                               party_count=count))
    cases.append(base_case("auto-scan all twelve slots non-zero", party_count=0,
                           party_ids=[0x100 + i for i in range(12)]))
    cases.append(base_case("auto-scan only slot 11 non-zero", party_count=0,
                           party_ids=[0] * 11 + [0x2FF]))
    cases.append(base_case("auto-scan slots 8..11 non-zero", party_count=0,
                           party_ids=[0] * 8 + [0x108, 0x109, 0x10A, 0x10B]))
    cases.append(base_case("auto-scan first non-zero at slot 3", party_count=5,
                           party_ids=[0, 0, 0, 0x103, 0x104, 0x105, 0x106,
                                      0x107, 0x108, 0x109, 0x10A, 0x10B]))
    cases.append(base_case("auto-scan all zero", party_count=0,
                           party_ids=[0] * 12))
    cases.append(base_case("auto-scan 0xFFFF id", party_count=0,
                           party_ids=[0xFFFF] + [0] * 11))

    # --- signed s16 values read from record+0x88
    cases.append(base_case("signed values -0x8000 0x7FFF -1 0", flags=0x40,
                           lookup_values=[-0x8000, 0x7FFF, -1, 0]))
    cases.append(base_case("signed value -1 auto-scanned", party_count=0,
                           party_ids=[0x111], lookup_values=[-1]))
    cases.append(base_case("signed value 0x7FFF auto-scanned", party_count=0,
                           party_ids=[0x222], lookup_values=[0x7FFF]))

    # --- registry hits, misses and partial tables
    cases.append(base_case(
        "registry hits for two of four values", flags=0x40,
        lookup_values=[0x111, 0x222, 0x333, 0x444],
        registry_present={0: 0x111, 2: 0x333},
        registry_ids={0: 0x111, 2: 0x333}))
    cases.append(base_case(
        "registry miss on all four values", flags=0x40,
        lookup_values=[0x501, 0x502, 0x503, 0x504]))
    cases.append(base_case(
        "registry full, no matching value", flags=0x40,
        lookup_values=[0x601, 0x602, 0x603, 0x604], registry_full=True))
    cases.append(base_case(
        "registry full with one matching value", flags=0x40,
        lookup_values=[0x701, 0x702, 0x703, 0x704], registry_full=True,
        registry_ids={5: 0x703}))
    cases.append(base_case(
        "first free registry slot is 2", flags=0x40,
        lookup_values=[0x801, 0x802], registry_present={0: 0x900, 1: 0x901},
        registry_ids={0: 0x900, 1: 0x901}))
    cases.append(base_case(
        "last free registry slot is 41", flags=0x40,
        lookup_values=[0x811],
        registry_present={i: 0x900 + i for i in range(41)},
        registry_ids={i: 0x900 + i for i in range(41)}))

    # --- duplicate collected values match the first inserted record
    cases.append(base_case(
        "duplicate collected values", flags=0x40,
        lookup_values=[0x500, 0x500, 0x600, 0x600]))
    cases.append(base_case(
        "duplicate negative value", flags=0x40,
        lookup_values=[-2, -2, -2, -2]))
    cases.append(base_case(
        "duplicate values with pre-seeded registry", flags=0x40,
        lookup_values=[0x0A, 0x0A], registry_present={0: 0x0A},
        registry_ids={0: 0x0A}))

    # --- collected != appended return value
    cases.append(base_case(
        "return is collected count, not appended count", flags=0x40,
        lookup_values=[0x111, 0x222, 0x333, 0x444],
        registry_present={0: 0x111, 1: 0x222, 2: 0x333, 3: 0x444},
        registry_ids={0: 0x111, 1: 0x222, 2: 0x333, 3: 0x444}))
    cases.append(base_case(
        "return zero when auto-scan finds nothing", party_count=0,
        party_ids=[0] * 12))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = SetupRunner().run(orig_code, case)
        cand = SetupRunner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(
            f"  [PASS] {case['name']}  "
            f"(collected {orig['collected']}, added {orig['added']}, "
            f"{len(orig['call_log'])} calls)"
        )
    return passed


def main() -> None:
    print("Testing engine_func_00339b18 (0x00339b18)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("preset_first", "work->selected_ids[0] = 0x225;",
         "work->selected_ids[0] = 0x226;"),
        ("slot_count", "constexpr u32 kSlotCount = 42;",
         "constexpr u32 kSlotCount = 41;"),
        ("flags_bit", "constexpr u32 kFlagsPreset = 0x40;",
         "constexpr u32 kFlagsPreset = 0x20;"),
        ("scan_count", "constexpr u32 kScanCount = 12;",
         "constexpr u32 kScanCount = 11;"),
        ("party_id_offset", "constexpr u32 kPartyIdOffset = 0x48;",
         "constexpr u32 kPartyIdOffset = 0x4a;"),
        ("lookup_value_offset", "constexpr u32 kLookupValueOffset = 0x88;",
         "constexpr u32 kLookupValueOffset = 0x8a;"),
        ("clear_size", "constexpr u32 kClearSize = 0xe10;",
         "constexpr u32 kClearSize = 0xe0c;"),
        ("id_scratch_size", "constexpr u32 kIdScratchSize = 0xa8;",
         "constexpr u32 kIdScratchSize = 0xa4;"),
        ("return_value", "return static_cast<u32>(collected);",
         "return static_cast<u32>(added);"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = SetupRunner().run(orig_code, case)
            bad = SetupRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
