#!/usr/bin/env python3
"""Differential test for camp_func_002a043c (0x002a043c) using Unicorn ARM.

The pinned original (extracted/exefs/code.bin) and the compiled C++ candidate
(src/engine/leaf_batch41_c.cpp) run in separate Unicorn machines with identical
fixtures and deterministic stubs at the original direct-call addresses.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log, including every register argument and the contents
    digest of the u16 array each 0x0029D080 call searches;
  * the full camp work block (three arrays and three counts plus sentinels),
    the configuration block, both entry/info fixture pages, the selector table
    page and the manager slot page.

Coverage: both inclusive loop limits (0x4B0 / 0x1F4), the signed category
filter (0, equal, unequal, negative, 0x100), both 0x0029ED08/0x0029EC6C
acceptance arms, duplicate and overflowing category bytes, ascending and
descending id order through the sort stub, null and non-null 0x0029EC14
records, accepted/cleared info flag bit 0x20, every selector sign/table-match
combination and 0x001A14E4 both outcomes.

Negative controls mutate the candidate loop bound, the info flag mask, the
selector-table address and one zero-fill size; each mutant must be detected.
"""

from __future__ import annotations

import hashlib
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
OUT_DIR = ROOT / "build/test_leaf_002a043c"

FUNC_ADDR = 0x002A043C
FUNC_SIZE = 448

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the body (0x1A14E4..0x2C4B30 targets)
SELECTOR_ADDR = 0x00403000
SELECTOR_SIZE = 0x00001000  # holds the 0x0040333C table
MANAGER_ADDR = 0x0043D000
MANAGER_SIZE = 0x00001000  # holds the 0x0043DD68 manager slot
WORK_ADDR = 0x00500000
WORK_SIZE = 0x00004000
CONFIG_ADDR = 0x00510000
CONFIG_SIZE = 0x00001000
ENTRY_ADDR = 0x00700000
ENTRY_SIZE = 0x00004000
INFO_ADDR = 0x00710000
INFO_SIZE = 0x00004000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets (stubs are placed at the same addresses).
STUB_2A0FAC = 0x002A0FAC
STUB_2C4B30 = 0x002C4B30
STUB_29ED44 = 0x0029ED44
STUB_2B9364 = 0x002B9364
STUB_29ED08 = 0x0029ED08
STUB_29EC6C = 0x0029EC6C
STUB_29D080 = 0x0029D080
STUB_2B7F0A = 0x002B7F0A  # Thumb entry; the original reaches it with blx
STUB_29EC14 = 0x0029EC14
STUB_1A14E4 = 0x001A14E4

THUMB_STUBS = {STUB_2B7F0A}

STUB_NAMES = {
    STUB_2A0FAC: "camp_func_002a0fac",
    STUB_2C4B30: "engine_func_002c4b30",
    STUB_29ED44: "camp_func_0029ed44",
    STUB_2B9364: "camp_func_002b9364",
    STUB_29ED08: "camp_func_0029ed08",
    STUB_29EC6C: "ui_func_0029ec6c",
    STUB_29D080: "camp_func_0029d080",
    STUB_2B7F0A: "camp_func_002b7f08",
    STUB_29EC14: "func_0029ec14",
    STUB_1A14E4: "camp_func_001a14e4",
}

# Relocation symbol text -> stub address (0x2B7F08 is the ledger name of the
# Thumb routine whose entry is 0x2B7F0A).
SYMBOL_KEYS = {
    "002a0fac": STUB_2A0FAC,
    "002c4b30": STUB_2C4B30,
    "0029ed44": STUB_29ED44,
    "002b9364": STUB_2B9364,
    "0029ed08": STUB_29ED08,
    "0029ec6c": STUB_29EC6C,
    "0029d080": STUB_29D080,
    "002b7f08": STUB_2B7F0A,
    "0029ec14": STUB_29EC14,
    "001a14e4": STUB_1A14E4,
}

# Work-block layout (mirrors the constants in the replacement).
CANDIDATE_ARRAY = 0x5C0
CANDIDATE_BYTES = 0x962
UNIQUE_ARRAY = 0xF22
UNIQUE_BYTES = 0x70
SKILL_ARRAY = 0xF92
SKILL_BYTES = 0x3EA
CANDIDATE_COUNT = 0x137C
UNIQUE_COUNT = 0x1380
SKILL_COUNT = 0x1384
CANDIDATE_LIMIT = 0x4B0
SKILL_LIMIT = 0x1F4

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

WORK_CONTEXT = 0x00C0DEF0


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "002a043c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"camp_func_002a043c not found in {obj_file}: "
                           f"{sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        target = None
        for key, address in SYMBOL_KEYS.items():
            if key in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved relocation: {rel.symbol_name} "
                               f"(type {rel.relocation_type})")
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(f"unexpected relocation type "
                               f"{rel.relocation_type} for {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        offset = target - pc
        if target in THUMB_STUBS:
            # BLX (immediate): the candidate emits an ARM BL to the Thumb
            # routine's ledger symbol; turn it into BLX.
            # BLX immediate is halfword-aligned; bit 1 of the displacement
            # becomes the H field of the encoding.
            if offset & 1:
                raise RuntimeError(f"unaligned Thumb call 0x{target:08x}")
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
            struct.pack_into("<I", code, rel.offset,
                             cond | (displacement & 0x00FFFFFF))
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {count} times")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    res = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures
def build_work(case: dict) -> bytes:
    page = bytearray(b"\xA5" * WORK_SIZE)
    struct.pack_into("<I", page, 0, WORK_CONTEXT)
    return bytes(page)


def build_config(case: dict) -> bytes:
    page = bytearray(CONFIG_SIZE)
    page[0x24] = case.get("selected_lo", 0) & 0xFF
    page[0x25] = case.get("selected_hi", 0) & 0xFF
    page[0x31] = case.get("selector", 0) & 0xFF
    # Unrelated filler bytes must stay untouched.
    for offset in (0x20, 0x22, 0x26, 0x30, 0x32, 0x40):
        page[offset] = (offset ^ 0x5A) & 0xFF
    return bytes(page)


def default_entry(index: int) -> tuple[int, int]:
    return index & 0xFFFF, (index * 7 + 3) & 0xFF


def build_entries(case: dict) -> bytes:
    page = bytearray(ENTRY_SIZE)
    overrides = case.get("entries", {})
    for index in range(CANDIDATE_LIMIT + 1):
        ident, category = default_entry(index)
        if index in overrides:
            ident, category = overrides[index]
        base = index * 4
        struct.pack_into("<H", page, base, ident & 0xFFFF)
        page[base + 2] = category & 0xFF
        page[base + 3] = (index * 13 + 5) & 0xFF
    return bytes(page)


def default_info(index: int) -> tuple[int, int]:
    return (index * 5 + 1) & 0xFF, 0x20


def build_infos(case: dict) -> bytes:
    page = bytearray(INFO_SIZE)
    overrides = case.get("infos", {})
    for index in range(SKILL_LIMIT + 1):
        category, flags = default_info(index)
        if index in overrides:
            category, flags = overrides[index]
        base = index * 8
        page[base + 2] = category & 0xFF
        page[base + 3] = flags & 0xFF
        page[base + 0] = (index * 3 + 1) & 0xFF
        page[base + 1] = (index * 3 + 2) & 0xFF
    return bytes(page)


def build_selector(case: dict) -> bytes:
    page = bytearray(SELECTOR_SIZE)
    base = 0x40333C - SELECTOR_ADDR
    table = {index: 0x1000 + index for index in range(128)}
    table.update(case.get("table", {}))
    for index, value in table.items():
        struct.pack_into("<I", page, base + index * 4, value & 0xFFFFFFFF)
    return bytes(page)


def build_manager(case: dict) -> bytes:
    page = bytearray(MANAGER_SIZE)
    struct.pack_into("<I", page, 0x43DD68 - MANAGER_ADDR, WORK_ADDR)
    return bytes(page)


def read_c_array(uc, address: int, count: int) -> bytes:
    if count <= 0:
        return b""
    return bytes(uc.mem_read(address, count * 2))


class A043CRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(SELECTOR_ADDR, SELECTOR_SIZE)
        self.uc.mem_map(MANAGER_ADDR, MANAGER_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(CONFIG_ADDR, CONFIG_SIZE)
        self.uc.mem_map(ENTRY_ADDR, ENTRY_SIZE)
        self.uc.mem_map(INFO_ADDR, INFO_SIZE)
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

        self.call_log: list = []
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _log(self, name: str, *args) -> None:
        self.call_log.append((name, args))

    def _ed44(self, ident: int) -> int:
        if self.case.get("ed44_all", False):
            return 1
        return 1 if ident in self.case.get("ed44_true", set()) else 0

    def _e4(self, index: int) -> int:
        if self.case.get("e4_all", False):
            return 1
        return 1 if index in self.case.get("e4_true", set()) else 0

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2A0FAC:
            self._log("camp_func_002a0fac")
            uc.reg_write(arm.UC_ARM_REG_R0, CONFIG_ADDR)
        elif address == STUB_2C4B30:
            self._log("engine_func_002c4b30", r0, r1)
            if r1:
                uc.mem_write(r0, b"\x00" * r1)
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_29ED44:
            self._log("camp_func_0029ed44", r0, r1 & 0xFFFF)
            uc.reg_write(arm.UC_ARM_REG_R0, self._ed44(r1 & 0xFFFF))
        elif address == STUB_2B9364:
            self._log("camp_func_002b9364", r0)
            uc.reg_write(arm.UC_ARM_REG_R0, ENTRY_ADDR + (r0 & 0xFFFF) * 4)
        elif address == STUB_29ED08:
            self._log("camp_func_0029ed08", r0 & 0xFFFF)
            value = 0 if (r0 & 0xFFFF) in self.case.get("ed08_false", set()) else 1
            uc.reg_write(arm.UC_ARM_REG_R0, value)
        elif address == STUB_29EC6C:
            self._log("ui_func_0029ec6c", r0 & 0xFFFF)
            value = 1 if (r0 & 0xFFFF) in self.case.get("ec6c_true", set()) else 0
            uc.reg_write(arm.UC_ARM_REG_R0, value)
        elif address == STUB_29D080:
            count = r1 - (1 << 32) if r1 & 0x80000000 else r1
            raw = read_c_array(uc, r0, count)
            digest = hashlib.sha1(raw).digest()[:8]
            self._log("camp_func_0029d080", r0, count, r2 & 0xFFFF, digest)
            found = 0
            for index in range(max(count, 0)):
                if struct.unpack_from("<H", raw, index * 2)[0] == (r2 & 0xFFFF):
                    found = 1
                    break
            uc.reg_write(arm.UC_ARM_REG_R0, found)
        elif address == STUB_2B7F0A:
            count = r1 - (1 << 32) if r1 & 0x80000000 else r1
            self._log("camp_func_002b7f08", r0, r1, r2, r3)
            if r2 == 2 and 1 < count < 0x2000:
                raw = bytearray(uc.mem_read(r0, count * 2))
                values = sorted(
                    struct.unpack_from(f"<{count}H", raw, 0)
                )
                struct.pack_into(f"<{count}H", raw, 0, *values)
                uc.mem_write(r0, bytes(raw))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_29EC14:
            self._log("func_0029ec14", r0)
            if r0 in self.case.get("info_null", set()):
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, INFO_ADDR + (r0 & 0x1FF) * 8)
        elif address == STUB_1A14E4:
            self._log("camp_func_001a14e4", r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self._e4(r0))
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(WORK_ADDR, build_work(case))
        self.uc.mem_write(CONFIG_ADDR, build_config(case))
        self.uc.mem_write(ENTRY_ADDR, build_entries(case))
        self.uc.mem_write(INFO_ADDR, build_infos(case))
        self.uc.mem_write(SELECTOR_ADDR, build_selector(case))
        self.uc.mem_write(MANAGER_ADDR, build_manager(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x44444444)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=20_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "fixtures": {
                "work": bytes(self.uc.mem_read(WORK_ADDR, WORK_SIZE)),
                "config": bytes(self.uc.mem_read(CONFIG_ADDR, CONFIG_SIZE)),
                "entries": bytes(self.uc.mem_read(ENTRY_ADDR, ENTRY_SIZE)),
                "infos": bytes(self.uc.mem_read(INFO_ADDR, INFO_SIZE)),
                "selector": bytes(self.uc.mem_read(SELECTOR_ADDR,
                                                   SELECTOR_SIZE)),
                "manager": bytes(self.uc.mem_read(MANAGER_ADDR,
                                                  MANAGER_SIZE)),
            },
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n"
                            f"    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        left = orig["call_log"]
        right = cand["call_log"]
        first = None
        for index in range(min(len(left), len(right))):
            if left[index] != right[index]:
                first = index
                break
        detail = (f"lengths {len(left)}/{len(right)}")
        if first is not None:
            detail += f", first diff at {first}:\n    orig={left[first]!r}" \
                      f"\n    cand={right[first]!r}"
        problems.append(f"call_log: {detail}")
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            left = value
            right = cand["fixtures"][key]
            first = next((i for i in range(len(left)) if left[i] != right[i]),
                         None)
            problems.append(
                f"fixture {key} differs (first byte 0x{first:x}, "
                f"orig=0x{left[first]:02x}, cand=0x{right[first]:02x})"
            )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "selected_lo": 0,
        "selected_hi": 0,
        "selector": 0,
        "ed44_all": False,
        "ed44_true": set(),
        "ed08_false": set(),
        "ec6c_true": set(),
        "e4_all": False,
        "e4_true": set(),
        "entries": {},
        "infos": {},
        "info_null": set(),
        "table": {},
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- nothing accepted: only the zero fills, the ed44 scan and qsort(0)
    cases.append(base_case("all candidates rejected by 0x29ED44"))

    # --- full ranges: both loop limits are inclusive (0x4B0 and 0x1F4)
    cases.append(base_case("full range, all accepted", ed44_all=True,
                           e4_all=True, selector=-1))

    # --- category filter: signed 16-bit versus zero-extended byte
    cases.append(base_case(
        "category filter positive equal",
        selected_lo=5,
        ed44_true={1, 2, 3},
        entries={1: (0x0011, 5), 2: (0x0012, 6), 3: (0x0013, 5)},
    ))
    cases.append(base_case(
        "category filter positive unequal",
        selected_lo=5,
        ed44_true={1, 2, 3},
        entries={1: (0x0011, 6), 2: (0x0012, 7), 3: (0x0013, 8)},
    ))
    cases.append(base_case(
        "category filter 0x0100 cannot match a byte",
        selected_lo=0x00, selected_hi=0x01,
        ed44_true={1, 2},
        entries={1: (0x0011, 0x00), 2: (0x0012, 0xFF)},
    ))
    cases.append(base_case(
        "category filter -1 cannot match a byte",
        selected_lo=0xFF, selected_hi=0xFF,
        ed44_true={1, 2},
        entries={1: (0x0011, 0xFF), 2: (0x0012, 0x00)},
    ))
    cases.append(base_case(
        "category filter -32768",
        selected_lo=0x00, selected_hi=0x80,
        ed44_true={1},
        entries={1: (0x0011, 0x00)},
    ))
    cases.append(base_case(
        "category filter 32767",
        selected_lo=0xFF, selected_hi=0x7F,
        ed44_true={1},
        entries={1: (0x0011, 0xFF)},
    ))

    # --- 0x29ED08 / 0x29EC6C acceptance arms (AND of zero results)
    # The stubs receive the 16-bit entry ids (0x0107/0x0108), not the slot
    # indexes, so the overrides are keyed by id.
    for ed08_zero, ec6c_one in ((False, False), (False, True),
                                (True, False), (True, True)):
        cases.append(base_case(
            f"acceptance ed08zero={ed08_zero} ec6c={ec6c_one}",
            ed44_true={7, 8},
            entries={7: (0x0107, 0x31), 8: (0x0108, 0x32)},
            ed08_false={0x0108} if ed08_zero else {0xFFFF},
            ec6c_true={0x0107, 0x0108} if ec6c_one else set(),
        ))

    # --- duplicate bytes and array capacity overflow past 56 slots
    cases.append(base_case(
        "duplicate category bytes",
        ed44_all=True,
        entries={index: (index, 0x42) for index in range(40)},
        # Only the first 40 ids processed? No: entry overrides only apply to
        # those indices, the rest keep default categories.
    ))
    cases.append(base_case(
        "sixty distinct category bytes overflow the u16 array",
        selected_lo=0xFF, selected_hi=0xFF,  # none stored as candidates
        ed44_true=set(range(60)),
        entries={index: (0x0600 + index, index) for index in range(60)},
    ))

    # --- sort stub: descending ids must be reordered; 0/1/2 candidates
    cases.append(base_case("single candidate", ed44_true={9},
                           entries={9: (0x7777, 1)}))
    cases.append(base_case("two candidates", ed44_true={9, 10},
                           entries={9: (0x8888, 1), 10: (0x1111, 1)}))
    cases.append(base_case(
        "six descending candidates",
        ed44_true={10, 11, 12, 13, 14, 15},
        entries={index: (0x9000 - index, 1)
                 for index in range(10, 16)},
    ))
    cases.append(base_case(
        "descending candidates with duplicate ids",
        ed44_true={20, 21, 22},
        entries={20: (0x3333, 2), 21: (0x3333, 2), 22: (0x1111, 2)},
    ))

    # --- 0x29EC14 null and info flag bit
    cases.append(base_case(
        "skill info null for some slots",
        selector=-1, ed44_true={1}, e4_all=True,
        info_null={3, 4, 0x1F4},
    ))
    cases.append(base_case(
        "skill flag 0x20 clear and set",
        selector=-1, ed44_true={1}, e4_all=True,
        infos={0: (0x10, 0x00), 1: (0x11, 0x20), 2: (0x12, 0xFF),
               3: (0x13, 0xDF), 4: (0x14, 0x21), 5: (0x15, 0x00)},
    ))

    # --- selector >= 0 table match/mismatch, and negative selectors
    cases.append(base_case(
        "selector 3 table match",
        selector=3, ed44_true={1}, e4_all=True,
        infos={index: (0x20, 0x20)
               for index in range(0, 8)},
        table={3: 0x20},
    ))
    cases.append(base_case(
        "selector 3 table mismatch",
        selector=3, ed44_true={1}, e4_all=True,
        infos={index: (0x21, 0x20) for index in range(0, 8)},
        table={3: 0x20},
    ))
    cases.append(base_case(
        "selector 127 table match",
        selector=127, ed44_true={1}, e4_all=True,
        infos={index: (0x30, 0x20) for index in range(0, 4)},
        table={127: 0x30},
    ))
    cases.append(base_case(
        "selector -1 skips the table",
        selector=-1, ed44_true={1}, e4_all=True,
        infos={index: (0x30, 0x20) for index in range(0, 4)},
        table={127: 0x30},
    ))
    cases.append(base_case(
        "selector -128 skips the table",
        selector=-128, ed44_true={1}, e4_all=True,
    ))

    # --- 0x1A14E4 outcomes and the skill-limit boundary
    cases.append(base_case(
        "1a14e4 accepts even slots",
        selector=-1, ed44_true={1},
        e4_true=set(range(0, SKILL_LIMIT + 1, 2)),
    ))
    cases.append(base_case(
        "1a14e4 rejects all",
        selector=-1, ed44_true={1}, e4_true=set(),
    ))
    cases.append(base_case(
        "skill limit slot 0x1F4 accepted",
        selector=-1, ed44_true={1}, e4_true={SKILL_LIMIT},
    ))
    cases.append(base_case(
        "skill limit slot 0x1F4 rejected",
        selector=-1, ed44_true={1}, e4_true={SKILL_LIMIT - 1},
    ))

    # --- candidate-limit boundary and slot 0x4B0 handling
    cases.append(base_case(
        "candidate limit slot 0x4B0 accepted",
        ed44_true={CANDIDATE_LIMIT},
        entries={CANDIDATE_LIMIT: (0x4B0A, 0x0A)},
    ))
    cases.append(base_case(
        "candidate limit slot 0x4B0 rejected",
        ed44_true={CANDIDATE_LIMIT - 1},
    ))

    # --- 16-bit entry id truncation and odd ids
    cases.append(base_case(
        "entry ids wrap at 16 bits",
        ed44_true={5, 6, 7},
        entries={5: (0xFFFF, 0x10), 6: (0x0000, 0x00),
                 7: (0x8000, 0x80)},
    ))
    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = A043CRunner().run(orig_code, case)
        cand = A043CRunner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        work = orig["fixtures"]["work"]
        counts = struct.unpack_from("<III", work, CANDIDATE_COUNT)
        print(f"  [PASS] {case['name']}  "
              f"(calls {len(orig['call_log'])}, counts {counts})")
    return passed


def main() -> None:
    print("Testing camp_func_002a043c (0x002a043c)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          f"(relocations resolved).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("candidate_limit", "constexpr u32 kCandidateLimit = 0x4B0;",
         "constexpr u32 kCandidateLimit = 0x4AF;"),
        ("info_flag_mask", "constexpr u8 kInfoAccepted = 0x20;",
         "constexpr u8 kInfoAccepted = 0x10;"),
        ("selector_table", "constexpr u32 kSelectorTable = 0x0040333C;",
         "constexpr u32 kSelectorTable = 0x00403338;"),
        ("unique_fill_size",
         "engine_func_002c4b30(work + kUniqueByteArray, kUniqueSlotBytes);",
         "engine_func_002c4b30(work + kUniqueByteArray, kSkillSlotBytes);"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = A043CRunner().run(orig_code, case)
            bad = A043CRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
