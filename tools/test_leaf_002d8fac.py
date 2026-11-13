#!/usr/bin/env python3
"""Differential test for ui_func_002d8fac (0x002d8fac) using Unicorn ARM.

The pinned original (extracted/exefs/code.bin) and the C++ candidate compiled
from src/engine/leaf_batch41_c.cpp are run in separate Unicorn ARM machines
with identical fixtures.  Every direct helper is replaced by a deterministic
stub at its original address, so the original's BL/B tail branches and the
candidate's relocated calls resolve to the same code.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log with every architected argument (and the string read
    by the two 0x002BF86C calls);
  * the full work, profile, second-profile, game-work and manager regions;
  * any write outside the private stack and the writable fixture regions.

Coverage includes the three early exits, the deactivate path, both status-mode
values, selected indices 0/1/2/0xFFFFFFFF, helper-driven manager->selected
re-reads, the null refreshed page, helper-driven work->profile re-reads, long
and empty page text, halfword extraction boundaries, and an unaligned profile
pointer.  Negative controls mutate the copy length, active-byte offset, profile
pointer offset, status polarity and the profile halfword selector.
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
OUT_DIR = ROOT / "build/test_leaf_002d8fac"

FUNC_ADDR = 0x002D8FAC
FUNC_SIZE = 420

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000
DATA_ADDR = 0x00430000
DATA_SIZE = 0x00030000
WORK_ADDR = 0x00500034          # +0x24C is 0x80-aligned, so a helper can
WORK_SIZE = 0x00010000          # make the refreshed page address exactly zero
PROFILE_ADDR = 0x00600000
PROFILE2_ADDR = 0x00610000
PROFILE_SIZE = 0x00010000
GAMEWORK_ADDR = 0x00700000
GAMEWORK_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

WORK_BASE = WORK_ADDR & ~0xFFF
WORK_BIAS = WORK_ADDR - WORK_BASE

MANAGER_ADDR = 0x0044DE28
GAMEWORK_GLOBAL = 0x0043E2A8

# 0x0029A384 can change manager->selected to this value; the refreshed page
# address then becomes (WORK_ADDR + 0x24C + (selected << 7)) mod 2^32 == 0.
NULL_PAGE_SELECTED = ((1 << 32) - (WORK_ADDR + 0x24C)) // 0x80
assert (WORK_ADDR + 0x24C + ((NULL_PAGE_SELECTED << 7) & 0xFFFFFFFF)) & 0xFFFFFFFF == 0

# Original direct-call targets; stubs are placed at the same addresses so both
# the original bytes and the relocated candidate resolve to them.
STUB_2BCF58 = 0x002BCF58
STUB_2BF86C = 0x002BF86C
STUB_2C0B94 = 0x002C0B94
STUB_2B66EC = 0x002B66EC
STUB_29E260 = 0x0029E260
STUB_29EB14 = 0x0029EB14
STUB_299974 = 0x00299974
STUB_29C768 = 0x0029C768
STUB_2998D8 = 0x002998D8
STUB_29A384 = 0x0029A384
STUB_26B810 = 0x0026B810

STUB_NAMES = {
    STUB_2BCF58: "ui_func_002bcf58",
    STUB_2BF86C: "engine_func_002bf86c",
    STUB_2C0B94: "ui_func_002c0b94",
    STUB_2B66EC: "script_vm_func_002b66ec",
    STUB_29E260: "camp_func_0029e260",
    STUB_29EB14: "ui_func_0029eb14",
    STUB_299974: "ui_func_00299974",
    STUB_29C768: "script_vm_func_0029c768",
    STUB_2998D8: "ui_func_002998d8",
    STUB_29A384: "engine_func_0029a384",
    STUB_26B810: "Status_SetMode1EB9",
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


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    functions = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in functions.items():
        if "002d8fac" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"ui_func_002d8fac not found in {obj_file}: {sorted(functions)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name} at {rel.offset}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if name in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        condition = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, condition | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
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


def read_c_string(uc, address: int, limit: int = 0x100) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


def build_work(case: dict) -> bytes:
    work = bytearray(WORK_SIZE)
    for index in range(WORK_SIZE):
        work[index] = (index * 37 + 11) & 0xFF

    selected = case.get("selected", 0) & 0xFFFFFFFF
    struct.pack_into("<I", work, WORK_BIAS + 0x18,
                     case.get("applied", 0x11111111) & 0xFFFFFFFF)
    work[WORK_BIAS + 0x28] = case.get("busy", 0) & 0xFF
    work[WORK_BIAS + 0x355] = case.get("transition", 0) & 0xFF
    struct.pack_into("<I", work, WORK_BIAS + 0x350,
                     case.get("profile", PROFILE_ADDR) & 0xFFFFFFFF)

    page_bases = {WORK_BIAS + 0x24C + index * 0x80 for index in (0, 1)}
    if selected not in (0, 1):
        page_bases.add(
            WORK_BIAS + ((0x24C + ((selected << 7) & 0xFFFFFFFF)) & 0xFFFFFFFF)
        )
    for page_index, base in enumerate(sorted(page_bases)):
        if base + 0x80 <= WORK_SIZE:
            fill_page(work, base, case, page_index)

    # These two fields win over any overlapping page bytes so the routine has a
    # valid profile pointer and a deterministic active-page byte.  Out-of-range
    # pages/indices only occur on early-exit cases, which never read them.
    struct.pack_into("<I", work, WORK_BIAS + 0x350,
                     case.get("profile", PROFILE_ADDR) & 0xFFFFFFFF)
    active_offset = WORK_BIAS + ((0x34C + selected) & 0xFFFFFFFF)
    if active_offset < WORK_SIZE:
        work[active_offset] = case.get("active", 0) & 0xFF
    return bytes(work)


def fill_page(work: bytearray, base: int, case: dict, page_index: int) -> None:
    tag = page_index
    struct.pack_into("<I", work, base + 0x12, case.get("word_12", 0x80000000 | tag))
    struct.pack_into("<I", work, base + 0x16, case.get("word_16", 0xFFFF8000 | tag))
    struct.pack_into("<I", work, base + 0x1A, case.get("word_1a", 0x12348000 | tag))
    struct.pack_into("<H", work, base + 0x1E, case.get("half_1e", 0xFFFF) & 0xFFFF)
    struct.pack_into("<I", work, base + 0x20, case.get("word_20", 0xDEADBEEF))
    struct.pack_into("<H", work, base + 0x24, case.get("half_24", 0x8001) & 0xFFFF)
    struct.pack_into("<H", work, base + 0x26, case.get("half_26", 0xFFFE) & 0xFFFF)
    for index in range(0x0E):
        work[base + 0x30 + index] = (0x30 + index + tag * 0x11) & 0xFF
    struct.pack_into("<I", work, base + 0x3E, case.get("word_3e", 0xCAFEBABE))
    struct.pack_into("<I", work, base + 0x42, case.get("word_42", 0x13579BDF))
    struct.pack_into("<I", work, base + 0x46, case.get("word_46", 0x2468ACE0))
    struct.pack_into("<H", work, base + 0x4A, case.get("half_4a", 0xABCD) & 0xFFFF)
    work[base + 0x4C] = case.get("byte_4c", 0x5A) & 0xFF
    work[base + 0x64] = case.get("page_byte64", 0) & 0xFF

    text = case.get("page_text", b"Page%d" % tag)
    if case.get("long_text"):
        # Overwrite the fields deliberately; both implementations read the same
        # bytes back as page fields after the text.
        work[base : base + len(text)] = text
    else:
        work[base : base + len(text) + 1] = text + b"\x00"


def build_profile(fill: int = 0xCC) -> bytes:
    return bytes([fill]) * PROFILE_SIZE


def build_gamework() -> bytes:
    page = bytearray(GAMEWORK_SIZE)
    for index in range(GAMEWORK_SIZE):
        page[index] = (index * 13 + 7) & 0xFF
    return bytes(page)


def build_data(case: dict) -> bytes:
    page = bytearray(DATA_SIZE)
    for index in range(DATA_SIZE):
        page[index] = (index * 3 + 1) & 0xFF
    manager_offset = MANAGER_ADDR - DATA_ADDR
    gamework_offset = GAMEWORK_GLOBAL - DATA_ADDR
    struct.pack_into("<I", page, manager_offset + 0x04, WORK_ADDR)
    struct.pack_into("<I", page, manager_offset + 0x08, case.get("selected", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, gamework_offset + 0x04, GAMEWORK_ADDR)
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(WORK_ADDR & ~0xFFF, WORK_SIZE)
        self.uc.mem_map(PROFILE_ADDR, PROFILE_SIZE)
        self.uc.mem_map(PROFILE2_ADDR, PROFILE_SIZE)
        self.uc.mem_map(GAMEWORK_ADDR, GAMEWORK_SIZE)
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
        self.case: dict = {}

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _log(self, name: str, *args) -> None:
        self.call_log.append((name, args))

    def _write_u32(self, address: int, value: int) -> None:
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)

        if address == STUB_2BCF58:
            self._log("ui_func_002bcf58", r0, r1, r2)
            payload = bytes(uc.mem_read(r1, r2))
            uc.mem_write(r0, payload)
        elif address == STUB_2BF86C:
            text = read_c_string(uc, r1)
            self._log("engine_func_002bf86c", r0, r1, text)
            uc.mem_write(r0, text + b"\x00")
        elif address == STUB_2C0B94:
            result = GAMEWORK_ADDR + 0x88
            self._log("ui_func_002c0b94", result)
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_2B66EC:
            result = GAMEWORK_ADDR + 0x90
            self._log("script_vm_func_002b66ec", result)
            if "after_2b66ec_profile" in self.case:
                self._write_u32(WORK_ADDR + 0x350, self.case["after_2b66ec_profile"])
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_29E260:
            self._log("camp_func_0029e260", r0)
            if "after_29e260_selected" in self.case:
                self._write_u32(MANAGER_ADDR + 0x08, self.case["after_29e260_selected"])
        elif address == STUB_29EB14:
            self._log("ui_func_0029eb14", r0)
            if "after_29eb14_selected" in self.case:
                self._write_u32(MANAGER_ADDR + 0x08, self.case["after_29eb14_selected"])
        elif address == STUB_299974:
            result = 0x29990000 | (r0 & 0xFFFF)
            self._log("ui_func_00299974", r0, result)
            if "after_299974_selected" in self.case:
                self._write_u32(MANAGER_ADDR + 0x08, self.case["after_299974_selected"])
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_29C768:
            self._log("script_vm_func_0029c768", r0)
            if "after_29c768_selected" in self.case:
                self._write_u32(MANAGER_ADDR + 0x08, self.case["after_29c768_selected"])
        elif address == STUB_2998D8:
            result = 0x29980000 | ((r0 & 0xFF) << 16) | (r1 & 0xFFFF)
            self._log("ui_func_002998d8", r0, r1, result)
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_29A384:
            self._log("engine_func_0029a384", r0)
            if "after_29a384_selected" in self.case:
                self._write_u32(MANAGER_ADDR + 0x08, self.case["after_29a384_selected"])
            if "after_29a384_profile" in self.case:
                self._write_u32(WORK_ADDR + 0x350, self.case["after_29a384_profile"])
        elif address == STUB_26B810:
            self._log("Status_SetMode1EB9", r0)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DATA_ADDR, build_data(case))
        work_base = WORK_ADDR & ~0xFFF
        self.uc.mem_write(work_base, build_work(case))
        self.uc.mem_write(PROFILE_ADDR, build_profile())
        self.uc.mem_write(PROFILE2_ADDR, build_profile(0xDD))
        self.uc.mem_write(GAMEWORK_ADDR, build_gamework())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x44444444)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        allowed = (
            (work_base, work_base + WORK_SIZE),
            (PROFILE_ADDR, PROFILE_ADDR + PROFILE_SIZE),
            (PROFILE2_ADDR, PROFILE2_ADDR + PROFILE_SIZE),
            (GAMEWORK_ADDR, GAMEWORK_ADDR + GAMEWORK_SIZE),
            (DATA_ADDR, DATA_ADDR + DATA_SIZE),
            (STACK_ADDR, STACK_ADDR + STACK_SIZE),
        )
        unexpected_writes = []
        for write_address, write_size in self.writes:
            if not any(start <= write_address < end for start, end in allowed):
                unexpected_writes.append((write_address, write_size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "work": bytes(self.uc.mem_read(work_base, WORK_SIZE)),
            "profile": bytes(self.uc.mem_read(PROFILE_ADDR, PROFILE_SIZE)),
            "profile2": bytes(self.uc.mem_read(PROFILE2_ADDR, PROFILE_SIZE)),
            "gamework": bytes(self.uc.mem_read(GAMEWORK_ADDR, GAMEWORK_SIZE)),
            "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
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
    for key in ("work", "profile", "profile2", "gamework", "data"):
        if orig[key] != cand[key]:
            first = next(
                (index for index, (a, b) in enumerate(zip(orig[key], cand[key])) if a != b),
                None,
            )
            problems.append(
                f"{key} region differs first at 0x{first:x}"
                if first is not None
                else f"{key} region length differs"
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
        "selected": 0,
        "applied": 0x11111111,
        "busy": 0,
        "transition": 0,
        "active": 0,
        "page_byte64": 0,
        "profile": PROFILE_ADDR,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- the three early exits ------------------------------------------------
    cases.append(base_case("equal selection 0", selected=0, applied=0))
    cases.append(base_case("equal selection 0xFFFFFFFF", selected=0xFFFFFFFF,
                           applied=0xFFFFFFFF))
    cases.append(base_case("equal selection 0x12345678", selected=0x12345678,
                           applied=0x12345678))
    cases.append(base_case("busy 1", applied=0x11111111, busy=1))
    cases.append(base_case("busy 0xFF", applied=0x11111111, busy=0xFF))
    cases.append(base_case("transition 1", applied=0x11111111, transition=1))
    cases.append(base_case("transition 0xFF", applied=0x11111111,
                           transition=0xFF))

    # --- deactivate path ------------------------------------------------------
    cases.append(base_case("inactive page 0", selected=0, active=0))
    cases.append(base_case("inactive page 1", selected=1, active=0))
    cases.append(base_case("inactive page 0xFFFFFFFF", selected=0xFFFFFFFF,
                           active=0))

    # --- activate path and status-mode polarity -------------------------------
    cases.append(base_case("active page 0 mode 0", selected=0, active=1,
                           page_byte64=0))
    cases.append(base_case("active page 0 mode 1", selected=0, active=1,
                           page_byte64=1))
    cases.append(base_case("active page 0 mode 0xFF", selected=0, active=0x80,
                           page_byte64=0xFF))
    cases.append(base_case("active page 1 mode 0x80", selected=1, active=0xFF,
                           page_byte64=0x80))
    cases.append(base_case("active page 0xFFFFFFFF mode 0x7F",
                           selected=0xFFFFFFFF, active=1, page_byte64=0x7F))
    cases.append(base_case("active page 2 (past the two-page array)", selected=2,
                           active=1, page_byte64=0))
    cases.append(base_case("active page 2 mode 1", selected=2, active=1,
                           page_byte64=1))

    # --- helper-driven manager->selected re-reads -----------------------------
    cases.append(base_case("0x0029E260 changes selection before copy",
                           selected=0, active=1, after_29e260_selected=1))
    cases.append(base_case("0x0029EB14 changes selection before copy",
                           selected=0, active=1, after_29eb14_selected=1))
    cases.append(base_case("0x00299974 changes selection before copy",
                           selected=0, active=1, after_299974_selected=1))
    cases.append(base_case("0x0029A384 makes the refreshed page null",
                           selected=0, active=1,
                           after_29a384_selected=NULL_PAGE_SELECTED))

    # --- helper-driven work->profile re-reads ---------------------------------
    cases.append(base_case("0x002B66EC changes the profile pointer",
                           selected=0, active=1,
                           after_2b66ec_profile=PROFILE2_ADDR))
    cases.append(base_case("0x0029A384 changes the profile pointer",
                           selected=0, active=1,
                           after_29a384_profile=PROFILE2_ADDR))

    # --- string and halfword boundaries ---------------------------------------
    cases.append(base_case("empty page text", selected=0, active=1,
                           page_text=b""))
    cases.append(base_case("page text 0x11 bytes", selected=0, active=1,
                           page_text=b"A" * 0x11))
    cases.append(base_case("page text 0x20 bytes over the fields", selected=0,
                           active=1, page_text=b"B" * 0x20, long_text=True))
    cases.append(base_case("halfword extraction 0x0000/0xFFFF", selected=0,
                           active=1, word_16=0x00008000, word_1a=0xFFFF0000))
    cases.append(base_case("halfword extraction 0x7FFF/0x8000", selected=0,
                           active=1, word_16=0x7FFF8000, word_1a=0x80007FFF))

    # --- unaligned profile pointer --------------------------------------------
    cases.append(base_case("unaligned profile pointer", selected=0, active=1,
                           profile=PROFILE_ADDR + 2))

    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases: list[dict]) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, case)
        cand = Runner().run(cand_code, case)
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
    print("Testing ui_func_002d8fac (0x002d8fac)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("copy_length", "constexpr u32 kCopyLength = 0x0E;",
         "constexpr u32 kCopyLength = 0x0D;"),
        ("active_offset", "constexpr u32 kActiveByteOffset = 0x34C;",
         "constexpr u32 kActiveByteOffset = 0x34D;"),
        ("slot_page_stride", "constexpr u32 kSlotPageStride = 0x80;",
         "constexpr u32 kSlotPageStride = 0x40;"),
        ("status_polarity",
         "refresh_page->byte_64 != 0 ? 1 : 0",
         "refresh_page->byte_64 != 0 ? 0 : 1"),
        ("profile_halfword",
         "static_cast<u16>(profile_view(work)->word_04 >> 16)",
         "static_cast<u16>(profile_view(work)->word_08 >> 16)"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
