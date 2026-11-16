#!/usr/bin/env python3
"""Differential test for script_vm_func_0033bdc8 (0x0033bdc8) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the script_vm_func_0033bdc8
body, resolves its direct calls (and the Thumb qsort call) to deterministic
stubs placed at the original addresses, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

The reconstructed body is the NkmGrowEvent record merge:

  * copy the 0x604-byte source record to a private stack buffer;
  * find the source's +0x4A index among the three s8 bytes at manager+0x9108;
  * 0x29BE68(source[+0x4A]) releases the live entry, 0x29C468(index, table_id,
    0) rebuilds it from the camp table (the stubs model both observable
    effects: +0x46 clearing, 0x18-entry list compaction, free-slot claim and
    the full 0x604-byte rebuild);
  * OR the 0x40 flag bytes at +0x4C and saturating-add the 0x500 stat bytes at
    +0x8C into the rebuilt live record;
  * 0x29C084 marks the live skill bitmap;
  * collect source skills (+0x34, eight u16) that 0x26B9EC reports as missing
    from the live record into the caller's eight-entry array;
  * qsort (0x2B7F0A, Thumb) the whole eight-entry array with the 0x2013E8
    comparator address;
  * capacity = 0x29CB94(live); terminate the collected run at out[new_count]
    when it fits; subtract the number of empty live slots among the first
    `capacity` entries; if the result is positive return 1 without installing
    anything, else install the sorted nonzero ids into the first free live
    slots starting at the "already known" count and return 0; both paths call
    0x29C950(live) last.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with all architected arguments of every helper (all
    helpers take register arguments only, so the stack-word list is empty);
  * every write outside the private stack, as an ordered list of
    (address, size, value) - the loops and stores must happen in the same
    order;
  * the complete 0x80000-byte manager page (live record, three special bytes,
    0x18-entry list), the source page and the caller's out page.

Coverage: zero/all-zero/new/known skill mixes; new counts 0..8; the
out[new_count] sentinel at both ends (8 skips it); garbage entries after the
sentinel (the original sorts and may install them); capacity -1, 0, 1..10;
balance > 0, == 0 and < 0; all four live-index match positions plus no match;
source index 0, 1, 2, 3, 23, 24, 25, 0x7F, 0x80, 0xFF and signed s8 no-match
cases for 0x80/0xFF; table ids 0, 1, 0x1F4, 0xFFFF; flag OR 0x00/0x55/0xAA/0xFF
patterns; stat sums 0x000, 0x0FF, 0x100, 0x1FF, 0x1FE and the 0x7F/0x80
boundary; and the +0x46 id word read as the ninth capacity entry.

Domain limits: every helper is stubbed, so their bodies are not compared.  The
0x29C468 rebuild is a deterministic stand-in for 0x001A7CAC's camp-table copy;
the qsort stub sorts the eight u16 entries ascending instead of using the
0x2013E8 rank ordering.  Both machines run the same stubs, so these choices do
not weaken the differential.  No caller-composition or whole-game claim is
made.
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
OUT_DIR = ROOT / "build/test_leaf_0033bdc8"

FUNC_ADDR = 0x0033BDC8
FUNC_SIZE = 684

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers 0x33BDC8 and every stub below 0x2B8000

MANAGER_BASE = 0x00500000
MANAGER_SIZE = 0x00080000  # 0x11C + 255 * 0x604 + 0x604 fits comfortably
SOURCE_ADDR = 0x00600000
PAGE_SIZE = 0x00001000
OUT_ADDR = 0x00610000

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

RECORD_SIZE = 0x604
RECORD_STRIDE = 0x604
MANAGER_MGR_OFFSET = 0x8C      # camp_func_002a8a08 return
MANAGER_LIVE_OFFSET = 0x11C    # first live record (camp_func_002a89e4)
MANAGER_LIST_OFFSET = 0x90F0   # +0x18 s8 list, relative to the manager pointer
MANAGER_SPECIAL_OFFSET = 0x9108  # three s8 live indices
MANAGER_LIST_COUNT = 0x18
SKILL_OFFSET = 0x34
SKILL_COUNT = 8
INDEX_OFFSET = 0x4A
ID_WORD_OFFSET = 0x46
FLAG_OFFSET = 0x4C
FLAG_SIZE = 0x40
STAT_OFFSET = 0x8C
STAT_SIZE = 0x500

STUB_2BCF58 = 0x002BCF58
STUB_2A8A08 = 0x002A8A08
STUB_29BE68 = 0x0029BE68
STUB_29C468 = 0x0029C468
STUB_2A89E4 = 0x002A89E4
STUB_29C084 = 0x0029C084
STUB_26B9EC = 0x0026B9EC
STUB_2B7F0A = 0x002B7F0A
STUB_29CB94 = 0x0029CB94
STUB_29C950 = 0x0029C950

STUB_NAMES = {
    STUB_2BCF58: "ui_func_002bcf58",
    STUB_2A8A08: "camp_func_002a8a08",
    STUB_29BE68: "camp_func_0029be68",
    STUB_29C468: "camp_func_0029c468",
    STUB_2A89E4: "camp_func_002a89e4",
    STUB_29C084: "camp_func_0029c084",
    STUB_26B9EC: "ui_func_0026b9ec",
    STUB_2B7F0A: "func_002b7f0a",
    STUB_29CB94: "script_vm_func_0029cb94",
    STUB_29C950: "script_vm_func_0029c950",
}

# 0x2B7F0A is Thumb code in the pinned image (the original reaches it with
# `blx`); the candidate's R_ARM_CALL is turned into BLX for the same target.
THUMB_STUBS = {STUB_2B7F0A}

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


def relocate_candidate(obj_file: Path) -> bytes:
    functions = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in functions.items():
        if "0033bdc8" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"script_vm_func_0033bdc8 not found in {obj_file}: {sorted(functions)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        offset = target - pc
        if target in THUMB_STUBS:
            # BLX (immediate) carries bit 1 of the offset in H; only an odd
            # offset (halfword bit 0) is unrepresentable.
            if offset & 1:
                raise RuntimeError(f"unaligned Thumb call target 0x{target:08x}")
            instruction = (
                0xFA000000
                | ((offset >> 2) & 0x00FFFFFF)
                | ((offset & 2) << 23)
            )
            struct.pack_into("<I", code, rel.offset, instruction)
        else:
            displacement = offset >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


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
    return relocate_candidate(obj_file)


def filler(size: int, seed: int) -> bytes:
    return bytes(((index * 37) + seed) & 0xFF for index in range(size))


def repeat(byte: int, size: int) -> bytes:
    return bytes([byte & 0xFF]) * size


def live_address(index: int) -> int:
    return MANAGER_BASE + MANAGER_LIVE_OFFSET + index * RECORD_STRIDE


def manager_address() -> int:
    return MANAGER_BASE + MANAGER_MGR_OFFSET


def s8(value: int) -> int:
    value &= 0xFF
    return value - 0x100 if value & 0x80 else value


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "index": 0,
        "table_id": 0,
        "skills": [0] * SKILL_COUNT,
        "flags": repeat(0x00, FLAG_SIZE),
        "stats": repeat(0x00, STAT_SIZE),
        "pre_skills": [0] * SKILL_COUNT,
        "pre_flags": repeat(0x00, FLAG_SIZE),
        "pre_stats": repeat(0x00, STAT_SIZE),
        "pre_id_word": 0x1111,
        "pre_flag_byte": 0x22,
        "rebuild_skills": [0] * SKILL_COUNT,
        "rebuild_flags": repeat(0x0F, FLAG_SIZE),
        "rebuild_stats": repeat(0x40, STAT_SIZE),
        "rebuild_id_word": None,
        "rebuild_flag_byte": 0x00,
        "special": [0xFF, 0xFF, 0xFF],
        "list": [0xFF] * MANAGER_LIST_COUNT,
        "capacity": 4,
        "out_init": [0] * SKILL_COUNT,
    }
    case.update(overrides)
    return case


class LeafRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # ARMv6K: the pinned original uses ldrd/strd-style pool loads and the
        # candidate lowers the saturating add loop to UQADD8.
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)  # CP10/CP11 on
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)    # FPEXC.EN
        for base, size in (
            (CODE_ADDR, CODE_SIZE),
            (MANAGER_BASE, MANAGER_SIZE),
            (SOURCE_ADDR, PAGE_SIZE),
            (OUT_ADDR, PAGE_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(base, size)

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
        self.pages: dict = {}

    # ------------------------------------------------------------------ stubs
    def _norm(self, value: int) -> object:
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _log(self, address: int, args) -> None:
        self.call_log.append((STUB_NAMES[address], tuple(args)))

    def _read8(self, address: int) -> int:
        return self.uc.mem_read(address, 1)[0]

    def _write8(self, address: int, value: int) -> None:
        self.uc.mem_write(address, struct.pack("<B", value & 0xFF))

    def _manager_list(self, index: int) -> int:
        return manager_address() + MANAGER_LIST_OFFSET + index

    def _release_live_entry(self, index: int) -> None:
        """Model 0x0029BE68's observable manager updates."""
        mgr = manager_address()
        if index >= MANAGER_LIST_COUNT:
            return
        for offset in range(3):
            if s8(self._read8(mgr + MANAGER_SPECIAL_OFFSET + offset)) == index:
                self._write8(mgr + MANAGER_SPECIAL_OFFSET + offset, 0xFF)
        for offset in range(MANAGER_LIST_COUNT):
            if s8(self._read8(self._manager_list(offset))) == index:
                self._write8(self._manager_list(offset), 0xFF)
        for slot in range(MANAGER_LIST_COUNT):
            if s8(self._read8(self._manager_list(slot))) >= 0:
                continue
            for later in range(slot + 1, MANAGER_LIST_COUNT):
                if s8(self._read8(self._manager_list(later))) < 0:
                    continue
                self._write8(self._manager_list(slot),
                             self._read8(self._manager_list(later)))
                self._write8(self._manager_list(later), 0xFF)
                break

    def _rebuild_live_entry(self, index: int, table_id: int) -> None:
        """Deterministic stand-in for 0x0029C468 -> 0x001A7CAC mode 0."""
        case = self.case
        rebuilt = bytearray(RECORD_SIZE)
        rebuilt[0x00:0x34] = filler(0x34, table_id & 0xFF)
        for slot in range(SKILL_COUNT):
            struct.pack_into(
                "<H", rebuilt, SKILL_OFFSET + slot * 2,
                case["rebuild_skills"][slot] & 0xFFFF,
            )
        id_word = case["rebuild_id_word"]
        if id_word is None:
            id_word = table_id & 0xFFFF
        struct.pack_into("<H", rebuilt, ID_WORD_OFFSET, id_word & 0xFFFF)
        rebuilt[0x48] = case["rebuild_flag_byte"] & 0xFF
        rebuilt[INDEX_OFFSET] = index & 0xFF
        rebuilt[FLAG_OFFSET:FLAG_OFFSET + FLAG_SIZE] = case["rebuild_flags"]
        rebuilt[STAT_OFFSET:STAT_OFFSET + STAT_SIZE] = case["rebuild_stats"]
        rebuilt[0x58C:RECORD_SIZE] = filler(RECORD_SIZE - 0x58C, 0x60)
        self.uc.mem_write(live_address(index), bytes(rebuilt))

        # 0x001A7CAC claims the first free entry of the 0x18-entry list.
        for offset in range(MANAGER_LIST_COUNT):
            if s8(self._read8(self._manager_list(offset))) < 0:
                self._write8(self._manager_list(offset), index)
                break

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2BCF58:
            self._log(address, (self._norm(r0), r1, r2))
            payload = bytes(uc.mem_read(r1, r2))
            uc.mem_write(r0, payload)
            uc.reg_write(arm.UC_ARM_REG_R0, (r0 + r2) & 0xFFFFFFFF)
        elif address == STUB_2A8A08:
            self._log(address, (self._norm(r0),))
            uc.reg_write(arm.UC_ARM_REG_R0, manager_address())
        elif address == STUB_29BE68:
            self._log(address, (r0,))
            self._release_live_entry(r0 & 0xFF)
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                1 if (r0 & 0xFF) < MANAGER_LIST_COUNT else 0,
            )
        elif address == STUB_29C468:
            self._log(address, (r0, r1, r2))
            self._rebuild_live_entry(r0 & 0xFF, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_2A89E4:
            self._log(address, (r0,))
            uc.reg_write(arm.UC_ARM_REG_R0, live_address(r0 & 0xFF))
        elif address == STUB_29C084:
            self._log(address, (r0,))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_26B9EC:
            self._log(address, (r0, r1))
            found = 0
            for slot in range(SKILL_COUNT):
                value = struct.unpack(
                    "<H", uc.mem_read(r0 + SKILL_OFFSET + slot * 2, 2)
                )[0]
                if value == (r1 & 0xFFFF):
                    found = 1
                    break
            uc.reg_write(arm.UC_ARM_REG_R0, found)
        elif address == STUB_2B7F0A:
            self._log(address, (r0, r1, r2, r3))
            count = r1 & 0xFFFF
            width = r2 & 0xFFFF
            raw = bytearray(uc.mem_read(r0, count * width))
            if width == 2:
                values = sorted(struct.unpack(f"<{count}H", raw))
                struct.pack_into(f"<{count}H", raw, 0, *values)
                uc.mem_write(r0, bytes(raw))
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_29CB94:
            self._log(address, (self._norm(r0),))
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case["capacity"] & 0xFFFFFFFF
            )
        elif address == STUB_29C950:
            self._log(address, (r0,))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    # -------------------------------------------------------------- fixtures
    def _build_pages(self, case: dict) -> None:
        uc = self.uc
        index = case["index"] & 0xFF

        manager = bytearray(filler(MANAGER_SIZE, 0x41))
        mgr = MANAGER_MGR_OFFSET
        for offset in range(MANAGER_LIST_COUNT):
            manager[mgr + MANAGER_LIST_OFFSET + offset] = (
                case["list"][offset] & 0xFF
            )
        for offset in range(3):
            manager[mgr + MANAGER_SPECIAL_OFFSET + offset] = (
                case["special"][offset] & 0xFF
            )
        live = bytearray(filler(RECORD_SIZE, 0x51))
        for slot in range(SKILL_COUNT):
            struct.pack_into(
                "<H", live, SKILL_OFFSET + slot * 2,
                case["pre_skills"][slot] & 0xFFFF,
            )
        struct.pack_into("<H", live, ID_WORD_OFFSET,
                         case["pre_id_word"] & 0xFFFF)
        live[0x48] = case["pre_flag_byte"] & 0xFF
        live[INDEX_OFFSET] = index
        live[FLAG_OFFSET:FLAG_OFFSET + FLAG_SIZE] = case["pre_flags"]
        live[STAT_OFFSET:STAT_OFFSET + STAT_SIZE] = case["pre_stats"]
        base = MANAGER_LIVE_OFFSET + index * RECORD_STRIDE
        manager[base:base + RECORD_SIZE] = live

        source = bytearray(filler(PAGE_SIZE, 0x21))
        source[0:RECORD_SIZE] = filler(RECORD_SIZE, 0x31)
        for slot in range(SKILL_COUNT):
            struct.pack_into(
                "<H", source, SKILL_OFFSET + slot * 2,
                case["skills"][slot] & 0xFFFF,
            )
        source[INDEX_OFFSET] = index
        source[FLAG_OFFSET:FLAG_OFFSET + FLAG_SIZE] = case["flags"]
        source[STAT_OFFSET:STAT_OFFSET + STAT_SIZE] = case["stats"]

        out = bytearray(filler(PAGE_SIZE, 0x61))
        for slot in range(SKILL_COUNT):
            struct.pack_into(
                "<H", out, slot * 2, case["out_init"][slot] & 0xFFFF
            )

        self.pages = {
            "manager": (MANAGER_BASE, bytes(manager)),
            "source": (SOURCE_ADDR, bytes(source)),
            "out": (OUT_ADDR, bytes(out)),
        }
        for _name, (address, data) in self.pages.items():
            uc.mem_write(address, data)

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        uc = self.uc
        self.call_log = []
        self.writes = []
        self.case = case

        uc.mem_write(FUNC_ADDR, code)
        self._build_pages(case)
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, SOURCE_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R1, case["table_id"] & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R2, OUT_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            uc.reg_write(CALLEE_SAVED[name], value)

        faulted = False
        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError:
            faulted = True

        leaks = []
        external_writes = []
        for address, size, value in self.writes:
            if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
                continue
            external_writes.append((address, size, value))
            inside = (
                MANAGER_BASE <= address < MANAGER_BASE + MANAGER_SIZE
                or SOURCE_ADDR <= address < SOURCE_ADDR + PAGE_SIZE
                or OUT_ADDR <= address < OUT_ADDR + PAGE_SIZE
            )
            if not inside:
                leaks.append((address, size))

        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "external_writes": external_writes,
            "leaks": leaks,
            "faulted": faulted,
            "pages": {
                name: bytes(uc.mem_read(address, len(data)))
                for name, (address, data) in self.pages.items()
            },
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    if orig["faulted"] or cand["faulted"]:
        if orig["faulted"] != cand["faulted"]:
            problems.append(
                f"fault mismatch: orig={orig['faulted']} cand={cand['faulted']}"
            )
        if orig["call_log"] != cand["call_log"]:
            problems.append(
                "call_log before fault:\n    orig="
                + repr(orig["call_log"])
                + "\n    cand="
                + repr(cand["call_log"])
            )
        return problems

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
    if orig["external_writes"] != cand["external_writes"]:
        problems.append(
            "external writes:\n    orig="
            + repr(orig["external_writes"])
            + "\n    cand="
            + repr(cand["external_writes"])
        )
    for name in orig["pages"]:
        if orig["pages"][name] != cand["pages"][name]:
            problems.append(f"page {name} was modified differently")
    if orig["leaks"] or cand["leaks"]:
        problems.append(
            f"writes outside fixtures: orig={orig['leaks']} cand={cand['leaks']}"
        )
    return problems


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- baseline: no skills at all
    cases.append(base_case("empty source, capacity 4"))
    cases.append(base_case("empty source, live slots filled", capacity=0))
    cases.append(
        base_case(
            "empty source, out array garbage",
            out_init=[0xDEAD, 0xBEEF, 0x1111, 0x2222, 0xFFFF, 0x0001, 0, 0],
        )
    )

    # --- single new skill installed into the first free live slot
    cases.append(
        base_case(
            "one new skill, empty live slots",
            skills=[0x0101, 0, 0, 0, 0, 0, 0, 0],
            capacity=8,
        )
    )
    cases.append(
        base_case(
            "one new skill at the last source slot",
            skills=[0, 0, 0, 0, 0, 0, 0, 0x0202],
            capacity=8,
        )
    )

    # --- known/new split and the insertion start index
    cases.append(
        base_case(
            "all eight source skills already known",
            skills=[0x1000 + i for i in range(8)],
            rebuild_skills=[0x1000 + i for i in range(8)],
            capacity=8,
            out_init=[0xAAAA, 0xBBBB, 0xCCCC, 0xDDDD, 0xEEEE, 0xFFFF,
                      0x1234, 0x5678],
        )
    )
    cases.append(
        base_case(
            "known then new, insertion starts at known count",
            skills=[0x0A0A, 0x0B0B, 0, 0, 0, 0, 0, 0],
            rebuild_skills=[0, 0x0A0A, 0, 0, 0, 0, 0, 0],
            capacity=4,
        )
    )
    cases.append(
        base_case(
            "two known two new",
            skills=[0x0A0A, 0x0B0B, 0x0C0C, 0x0D0D, 0, 0, 0, 0],
            rebuild_skills=[0x0A0A, 0x0B0B, 0, 0, 0, 0, 0, 0],
            capacity=4,
        )
    )
    cases.append(
        base_case(
            "duplicate source skills",
            skills=[0x0007, 0x0007, 0x0007, 0, 0, 0, 0, 0],
            capacity=8,
        )
    )

    # --- new counts 1..8 with no free slots and with exactly enough
    for count in range(1, SKILL_COUNT + 1):
        cases.append(
            base_case(
                f"{count} new skills, capacity 8, all live slots free",
                skills=[0x0500 + i for i in range(count)]
                + [0] * (SKILL_COUNT - count),
                capacity=8,
            )
        )
    for free in (0, 1, 2, 3, 4):
        cases.append(
            base_case(
                "four new skills, "
                f"{free} free live slots in the first capacity entries",
                skills=[0x0600 + i for i in range(4)] + [0] * 4,
                rebuild_skills=[0] * free
                + [0x0700 + i for i in range(SKILL_COUNT - free)],
                capacity=4,
            )
        )

    # --- capacity boundaries
    for capacity in (-1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10):
        cases.append(
            base_case(
                f"capacity {capacity}",
                skills=[0x0801, 0x0802, 0, 0, 0, 0, 0, 0],
                rebuild_skills=[0, 0, 0, 0, 0, 0, 0, 0],
                capacity=capacity,
                rebuild_id_word=0x7777,
            )
        )

    # --- new_count == 8 skips the out[new_count] sentinel
    cases.append(
        base_case(
            "eight new skills, sentinel not written",
            skills=[0x0900 + i for i in range(8)],
            capacity=8,
            out_init=[0xAAAA] * SKILL_COUNT,
        )
    )
    cases.append(
        base_case(
            "eight new skills, capacity 4 rejects",
            skills=[0x0900 + i for i in range(8)],
            rebuild_skills=[0x0A00 + i for i in range(4)] + [0] * 4,
            capacity=4,
        )
    )

    # --- balance == 0 (exactly enough room, must install)
    cases.append(
        base_case(
            "balance exactly zero installs",
            skills=[0x0C01, 0x0C02, 0, 0, 0, 0, 0, 0],
            rebuild_skills=[0x0D01, 0, 0, 0, 0, 0, 0, 0],
            capacity=4,
        )
    )
    cases.append(
        base_case(
            "balance one rejects",
            skills=[0x0C01, 0x0C02, 0, 0, 0, 0, 0, 0],
            rebuild_skills=[0x0D01, 0x0D02, 0, 0, 0, 0, 0, 0],
            capacity=3,
        )
    )

    # --- live-index match positions and signed s8 comparison
    for special_index, special in (
        (0, [0, 0xFF, 0xFF]),
        (0, [0, 0x01, 0x02]),
        (1, [0xFF, 1, 0xFF]),
        (2, [0xFF, 0xFF, 2]),
        (3, [0xFF, 0xFF, 0xFF]),
        (0x7F, [0x7F, 0xFF, 0xFF]),
        (0x80, [0x80, 0xFF, 0xFF]),
        (0xFF, [0xFF, 0xFF, 0xFF]),
        (0x42, [0x42, 0x42, 0x42]),
    ):
        cases.append(
            base_case(
                f"index 0x{special_index:02x} special {special}",
                index=special_index,
                special=special,
                capacity=4,
            )
        )

    # --- index byte boundaries and the 0x18 list cutoff in 0x29BE68
    for index in (0, 1, 2, 0x17, 0x18, 0x19, 0x7F, 0xFE, 0xFF):
        cases.append(
            base_case(
                f"index 0x{index:02x} list containment",
                index=index,
                list=[index, 0x05, 0xFF] + [0xFF] * (MANAGER_LIST_COUNT - 3),
                capacity=4,
            )
        )
    cases.append(
        base_case(
            "list compaction with two matches",
            index=0x05,
            list=[0x05, 0xFF, 0x09, 0x05, 0xFF, 0x02]
            + [0xFF] * (MANAGER_LIST_COUNT - 6),
            capacity=4,
        )
    )
    cases.append(
        base_case(
            "list full of free entries",
            index=0x03,
            list=[0xFF] * MANAGER_LIST_COUNT,
            capacity=4,
        )
    )

    # --- table id forwarding
    for table_id in (0, 1, 0x01F4, 0x1234, 0xFFFF, 0xFFFFFFFF):
        cases.append(
            base_case(
                f"table id 0x{table_id:08x}",
                table_id=table_id,
                skills=[0x0E01, 0, 0, 0, 0, 0, 0, 0],
                capacity=8,
            )
        )

    # --- flag OR boundaries
    for live_flags, source_flags in (
        (0x00, 0x00),
        (0x00, 0xFF),
        (0xFF, 0x00),
        (0xFF, 0xFF),
        (0x55, 0xAA),
        (0xAA, 0x55),
        (0x0F, 0xF0),
    ):
        cases.append(
            base_case(
                f"flag OR live 0x{live_flags:02x} source 0x{source_flags:02x}",
                rebuild_flags=repeat(live_flags, FLAG_SIZE),
                flags=repeat(source_flags, FLAG_SIZE),
                capacity=4,
            )
        )
    cases.append(
        base_case(
            "flag OR per-byte pattern",
            rebuild_flags=filler(FLAG_SIZE, 0x11),
            flags=filler(FLAG_SIZE, 0x77),
            capacity=4,
        )
    )

    # --- saturating stat add boundaries
    for live_stat, source_stat in (
        (0x00, 0x00),
        (0x00, 0xFF),
        (0xFF, 0x00),
        (0xFF, 0xFF),
        (0x80, 0x80),
        (0x7F, 0x80),
        (0x7F, 0x01),
        (0xFE, 0x01),
        (0xFE, 0x00),
        (0x01, 0xFE),
    ):
        cases.append(
            base_case(
                f"stat add 0x{live_stat:02x}+0x{source_stat:02x}",
                rebuild_stats=repeat(live_stat, STAT_SIZE),
                stats=repeat(source_stat, STAT_SIZE),
                capacity=4,
            )
        )
    cases.append(
        base_case(
            "stat add per-byte patterns",
            rebuild_stats=filler(STAT_SIZE, 0x13),
            stats=filler(STAT_SIZE, 0x57),
            capacity=4,
        )
    )
    cases.append(
        base_case(
            "stat add alternating wrap values",
            rebuild_stats=bytes([0x80 if i & 1 else 0x7F
                                 for i in range(STAT_SIZE)]),
            stats=bytes([0x80 if i % 3 else 0x01 for i in range(STAT_SIZE)]),
            capacity=4,
        )
    )

    # --- +0x46 id word is capacity entry 9
    cases.append(
        base_case(
            "capacity 9 id word non-zero",
            skills=[0x0F01, 0x0F02, 0, 0, 0, 0, 0, 0],
            rebuild_skills=[0] * 8,
            rebuild_id_word=0x1234,
            capacity=9,
        )
    )
    cases.append(
        base_case(
            "capacity 9 id word zero",
            skills=[0x0F01, 0x0F02, 0, 0, 0, 0, 0, 0],
            rebuild_skills=[0] * 8,
            rebuild_id_word=0,
            capacity=9,
        )
    )
    cases.append(
        base_case(
            "capacity 10 reads flag byte neighbours",
            skills=[0x0F01, 0, 0, 0, 0, 0, 0, 0],
            rebuild_skills=[0] * 8,
            rebuild_id_word=0x0000,
            rebuild_flag_byte=0x00,
            capacity=10,
        )
    )

    # --- out array garbage after the sentinel
    cases.append(
        base_case(
            "one new skill with garbage tail",
            skills=[0x0B01, 0, 0, 0, 0, 0, 0, 0],
            out_init=[0x1111, 0x2222, 0x3333, 0x4444, 0x5555, 0x6666,
                      0x7777, 0x8888],
            capacity=8,
        )
    )
    cases.append(
        base_case(
            "garbage tail with capacity 4 rejects",
            skills=[0x0B01, 0x0B02, 0x0B03, 0, 0, 0, 0, 0],
            rebuild_skills=[0x0E01, 0x0E02, 0, 0, 0, 0, 0, 0],
            out_init=[0x1111, 0x2222, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF,
                      0xFFFF, 0xFFFF],
            capacity=4,
        )
    )

    # --- larger mixed scenario
    cases.append(
        base_case(
            "mixed known/new with list and specials",
            index=0x0B,
            table_id=0x01F4,
            skills=[0x0A0A, 0, 0x0C0C, 0, 0x0E0E, 0, 0x1010, 0],
            rebuild_skills=[0x0A0A, 0x0C0C, 0, 0, 0, 0, 0, 0],
            special=[0xFF, 0x0B, 0xFF],
            list=[0x01, 0xFF, 0x0B, 0xFF, 0x07]
            + [0xFF] * (MANAGER_LIST_COUNT - 5),
            rebuild_flags=filler(FLAG_SIZE, 0x0D),
            flags=filler(FLAG_SIZE, 0x2B),
            rebuild_stats=filler(STAT_SIZE, 0x1F),
            stats=filler(STAT_SIZE, 0x33),
            capacity=6,
        )
    )

    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases) -> int:
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
        print(
            f"  [PASS] {case['name']}  "
            f"({len(orig['call_log'])} calls, ret {orig['ret']})"
        )
    return passed


def main() -> None:
    print("Testing script_vm_func_0033bdc8 (0x0033bdc8)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutations = (
        ("skill_offset", "kNkmSkillOffset = 0x34;", "kNkmSkillOffset = 0x36;"),
        ("flag_size", "kNkmFlagSize = 0x40;", "kNkmFlagSize = 0x3E;"),
        (
            "stat_saturation",
            "sum > 0xFFu ? 0xFFu : sum",
            "sum > 0xFFu ? 0xFEu : sum",
        ),
        ("balance_boundary", "if (balance > 0) {", "if (balance >= 0) {"),
        (
            "sentinel_boundary",
            "if (static_cast<s32>(kNkmSkillCount - new_count) > 0) {",
            "if (static_cast<s32>(kNkmSkillCount - new_count) >= 0) {",
        ),
        ("insert_start", "u32 slot = known_count;", "u32 slot = 0;"),
        (
            "special_signedness",
            "static_cast<s8>(manager[kNkmManagerListOffset + i])",
            "static_cast<u8>(manager[kNkmManagerListOffset + i])",
        ),
        (
            "flag_or",
            "live[offset] = static_cast<u8>(live[offset] | record[offset]);",
            "live[offset] = static_cast<u8>(live[offset] & record[offset]);",
        ),
        ("known_increment", "++known_count;", "++known_count; ++known_count;"),
        ("new_write_slot", "out[new_count] = id;", "out[0] = id;"),
    )
    for name, old, new in mutations:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = LeafRunner().run(orig_code, case)
            mutant = LeafRunner().run(mutant_code, case)
            if compare(orig, mutant):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
