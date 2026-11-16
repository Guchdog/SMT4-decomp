#!/usr/bin/env python3
"""Differential test for camp_func_001ee3f8 (0x001ee3f8) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the camp_func_001ee3f8 body,
resolves its nine direct calls to deterministic stubs at the pinned addresses,
and runs the pinned original (extracted/exefs/code.bin) against the candidate in
separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log including every register argument and the architected
    stack arguments of 0x00389FEC (four), 0x002BF558 and 0x002AEC80 (two each);
  * the camp-node page, battle-record page and the data page that holds the
    0x00433158 bundle slot plus the bundle payloads (must be identically
    modified);
  * any emulated write outside the private stack.

Coverage: the gate zero/non-zero split, negative/zero/positive ids, null camp
lookup, both record-flag branches, the 0x80/0x81 selected bound, the 0x264/0x265
fallback bound and the 16-bit truncation of the id, the second-lookup failures,
the zero/non-zero 0x002A63F8 result, both 0x002AEC20 results, short counts over
and under 0x80, negative s16 values scaled by 1000, stack-argument forwarding,
and the 0x00433158 bundle reload after the row setter. Negative controls mutate
one bound, the category, the record-flag offset, the two record field offsets,
the millisecond scale and the initial subindex seed; each mutant must be
detected.
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
SOURCE = ROOT / "src/engine/leaf_batch34_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_001ee3f8"

FUNC_ADDR = 0x001EE3F8
FUNC_SIZE = 428

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers 0x1EE3F8 through 0x00389FEC
DATA_ADDR = 0x00430000
DATA_SIZE = 0x00020000  # holds the 0x00433158 bundle slot
BUNDLE_ADDR = 0x00500000
BUNDLE_SIZE = 0x00010000
NODE_ADDR = 0x00600000
NODE_SIZE = 0x00010000
RECORD_ADDR = 0x00610000
RECORD_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

BUNDLE_SLOT = 0x00433158
BUNDLE_SLOT_OFFSET = BUNDLE_SLOT - DATA_ADDR

# Fixture placements inside their pages.
NODE_OFFSETS = (0x0100, 0x0200)
RECORD_OFFSETS = (0x0100, 0x0200)
BUNDLE0 = BUNDLE_ADDR + 0x0100
BUNDLE1 = BUNDLE_ADDR + 0x0200

STUB_2B9364 = 0x002B9364
STUB_2B087C = 0x002B087C
STUB_2A63F8 = 0x002A63F8
STUB_2AEC20 = 0x002AEC20
STUB_389FEC = 0x00389FEC
STUB_2BF558 = 0x002BF558
STUB_2AEC80 = 0x002AEC80

# Stub address -> (name, number of architected stack words).
STUB_INFO = {
    STUB_2B9364: ("camp_func_002b9364", 0),
    STUB_2B087C: ("battle_func_002b087c", 0),
    STUB_2A63F8: ("ui_func_002a63f8", 0),
    STUB_2AEC20: ("ui_func_002aec20", 0),
    STUB_389FEC: ("func_00389fec", 4),
    STUB_2BF558: ("func_002bf558", 2),
    STUB_2AEC80: ("script_vm_func_002aec80", 2),
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
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "001ee3f8" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"camp_func_001ee3f8 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        if rel.symbol_name.endswith("+0"):
            symbol = rel.symbol_name[:-2]
        else:
            symbol = rel.symbol_name
        target = None
        for address, (name, _stack_words) in STUB_INFO.items():
            if name == symbol:
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


def compile_candidate(out_name: str = "leaf_batch34_c.o") -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / out_name
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    result = compile_tu_armv6k(mutant_src, OUT_DIR / f"mutant_{name}.o", ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(OUT_DIR / f"mutant_{name}.o")


def patterned_page(size: int, seed: int) -> bytearray:
    return bytearray(((index * 7) + seed) & 0xFF for index in range(size))


def build_node_page(case: dict) -> bytes:
    page = patterned_page(NODE_SIZE, 0x5A)
    for offset, key in zip(NODE_OFFSETS, ("node0", "node1")):
        struct.pack_into("<H", page, offset + 0x90, case[key] & 0xFFFF)
    return bytes(page)


def build_record_page(case: dict) -> bytes:
    page = patterned_page(RECORD_SIZE, 0xC3)
    for offset, key in zip(RECORD_OFFSETS, ("record0", "record1")):
        record = case[key]
        page[offset + 0x03] = record["flag"] & 0xFF
        struct.pack_into("<h", page, offset + 0x88, record["selected"])
        page[offset + 0xA4] = record["short"] & 0xFF
    return bytes(page)


def build_data_page(case: dict) -> bytes:
    page = patterned_page(DATA_SIZE, 0x31)
    struct.pack_into("<I", page, BUNDLE_SLOT_OFFSET, BUNDLE0)
    return bytes(page)


def build_bundle_page() -> bytes:
    page = patterned_page(BUNDLE_SIZE, 0x77)
    return bytes(page)


def read_c_string(uc, address: int, limit: int = 16) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class EE3F8Runner:
    """One Unicorn machine with deterministic stubs at the pinned addresses."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(BUNDLE_ADDR, BUNDLE_SIZE)
        self.uc.mem_map(NODE_ADDR, NODE_SIZE)
        self.uc.mem_map(RECORD_ADDR, RECORD_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_INFO:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.a_index = 0
        self.b_index = 0

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_INFO[address][0], args + self._stack_words(STUB_INFO[address][1]))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _fixture(self, kind: str, name) -> int:
        if name is None:
            return 0
        page, offsets = (
            (NODE_ADDR, NODE_OFFSETS)
            if kind == "node"
            else (RECORD_ADDR, RECORD_OFFSETS)
        )
        return page + offsets[0 if name == 0 else 1]

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2B9364:
            self._log(address, self.a_index, r0)
            entry = self.case["a"][self.a_index]
            self.a_index += 1
            uc.reg_write(arm.UC_ARM_REG_R0, self._fixture("node", entry))
        elif address == STUB_2B087C:
            self._log(address, self.b_index, r0)
            entry = self.case["b"][self.b_index]
            self.b_index += 1
            uc.reg_write(arm.UC_ARM_REG_R0, self._fixture("record", entry))
        elif address == STUB_2A63F8:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["c"])
        elif address == STUB_2AEC20:
            self._log(address, r0, r1, r2, r3)
            if self.case.get("d_bundle") is not None:
                self.uc.mem_write(
                    BUNDLE_SLOT, struct.pack("<I", self.case["d_bundle"])
                )
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["d"])
        elif address == STUB_389FEC:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["e"])
        elif address == STUB_2BF558:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["f"])
        elif address == STUB_2AEC80:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["g"])
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for name, args in log:
            normalised.append((name, tuple(args)))
        return normalised

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.a_index = 0
        self.b_index = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(NODE_ADDR, build_node_page(case))
        self.uc.mem_write(RECORD_ADDR, build_record_page(case))
        self.uc.mem_write(DATA_ADDR, build_data_page(case))
        self.uc.mem_write(BUNDLE_ADDR, build_bundle_page())
        self.uc.mem_write(STACK_ADDR, b"\xA5" * STACK_SIZE)
        self.uc.mem_write(ENTRY_SP, struct.pack("<I", case["gate"] & 0xFFFFFFFF))
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case["id"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["arg1"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case["arg2"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case["arg3"] & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "fixtures": {
                "node": bytes(self.uc.mem_read(NODE_ADDR, NODE_SIZE)),
                "record": bytes(self.uc.mem_read(RECORD_ADDR, RECORD_SIZE)),
                "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
                "bundle": bytes(self.uc.mem_read(BUNDLE_ADDR, BUNDLE_SIZE)),
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
            problems.append(f"fixture {key} was modified differently")
    if orig["unexpected_writes"] != cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def make_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "id": 0x1234,
        "arg1": 0x11111111,
        "arg2": 0x22222222,
        "arg3": 0x33333333,
        "gate": 1,
        "a": [0, 1],
        "b": [0, 1],
        "node0": 0x0000,
        "node1": 0x0000,
        "record0": {"flag": 0x00, "selected": 0x0000, "short": 0x00},
        "record1": {"flag": 0x00, "selected": 0x0000, "short": 0x00},
        "c": 1,
        "d": 1,
        "e": 0xE0000001,
        "f": 0xF0000001,
        "g": 0x60000001,
        "d_bundle": None,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- gate zero: no lookups, raw id (including negative) becomes the value
    for ident in (0x00000000, 0x00000001, 0x00001234, 0x7FFFFFFF, -1, -0x80000000):
        cases.append(make_case(f"gate 0 id {ident}", gate=0, id=ident))
    cases.append(make_case("gate 0 id 0x1234 D returns 0 G", gate=0, id=0x1234,
                           d=0))
    cases.append(make_case("gate 0 id negative D returns 0 G", gate=0, id=-7,
                           d=0))
    cases.append(make_case("gate 0 id 0xABCD D returns 0 G", gate=0,
                           id=0x0000ABCD, d=0))
    cases.append(make_case("gate 0 D returns 0 short is zero", gate=0, d=0,
                           record0={"flag": 0xFF, "selected": 0x7FFF,
                                    "short": 0xFF}))
    cases.append(make_case("gate 0 C returns 0", gate=0, c=0))
    cases.append(make_case("gate 0 negative id C returns 0", gate=0, id=-3,
                           c=0))

    # --- gate non-zero, negative id: lookups skipped, subindex zero
    for ident in (-1, -0x80000000, 0xFFFFFFFF):
        cases.append(make_case(f"gate 1 id {ident}", id=ident))
        cases.append(make_case(f"gate 1 id {ident} D 0 G", id=ident, d=0))
    cases.append(make_case("gate 1 negative id C 0", id=-5, c=0))

    # --- gate non-zero with lookups
    cases.append(make_case("flag-clear fallback pass", id=0x0042, node0=0x0000,
                           d=1))
    cases.append(make_case("fallback value 0x264 passes", node0=0x0264, d=1))
    cases.append(make_case("fallback value 0x265 aborts", node0=0x0265, d=1))
    cases.append(make_case("fallback value 0xFFFF aborts", node0=0xFFFF, d=1))
    cases.append(make_case("fallback value 0x0100 D 0 G", node0=0x00FF, d=0))
    cases.append(make_case("fallback value 0x0100 short F", node0=0x00FF,
                           record0={"flag": 0x00, "selected": 0x0000,
                                    "short": 1}, d=0))

    cases.append(make_case("selected value 0x0000", record0={
        "flag": 0x01, "selected": 0x0000, "short": 0x00}))
    cases.append(make_case("selected value 0x0080 passes", record0={
        "flag": 0x01, "selected": 0x0080, "short": 0x00}))
    cases.append(make_case("selected value 0x0081 aborts", record0={
        "flag": 0x01, "selected": 0x0081, "short": 0x00}))
    cases.append(make_case("selected value 0x7FFF aborts", record0={
        "flag": 0x01, "selected": 0x7FFF, "short": 0x00}))
    cases.append(make_case("selected value -1 passes", record0={
        "flag": 0x01, "selected": -1, "short": 0x00}))
    cases.append(make_case("selected value -0x8000 passes", record0={
        "flag": 0x01, "selected": -0x8000, "short": 0x00}))
    cases.append(make_case("selected value -1 D 0 G scales", record0={
        "flag": 0x01, "selected": -1, "short": 0x00}, d=0))
    cases.append(make_case("selected value -3 D 0 G scales", record0={
        "flag": 0x01, "selected": -3, "short": 0x00}, d=0))
    cases.append(make_case("selected short 0xFF F", record0={
        "flag": 0x01, "selected": 0x0010, "short": 0xFF}, d=0))
    cases.append(make_case("selected short 0x01 F", record0={
        "flag": 0x01, "selected": 0x0010, "short": 0x01}, d=0))
    cases.append(make_case("selected short 0x00 G", record0={
        "flag": 0x01, "selected": 0x0010, "short": 0x00}, d=0))
    cases.append(make_case("selected D returns 0xFFFFFFFF", record0={
        "flag": 0x01, "selected": 0x0010, "short": 0x00}, d=0xFFFFFFFF))
    cases.append(make_case("record flag bit 0x80 is clear", record0={
        "flag": 0x80, "selected": 0x7777, "short": 0x11}, d=1))
    cases.append(make_case("record flag byte 0xFF is set", record0={
        "flag": 0xFF, "selected": 0x0011, "short": 0x22}, d=1))

    # --- A/B first call returns null.  The original dereferences the battle
    #     record without a second null test once the camp node is non-null, so
    #     a null battle record with a live camp node is a fault in both bodies
    #     and is not used as a differential case.
    cases.append(make_case("first camp lookup null", a=[None, 0]))
    cases.append(make_case("first camp lookup null battle non-null", a=[None, 0],
                           b=[0, 0]))
    cases.append(make_case("first camp lookup null battle null", a=[None, 0],
                           b=[None, 0]))
    cases.append(make_case("first lookup null with gate 0 ignored", gate=0,
                           a=[None, None], b=[None, None]))

    # --- second lookup failures with first lookup passing
    cases.append(make_case("second camp lookup null", a=[0, None]))
    cases.append(make_case("second camp lookup null gate 0 ignored", gate=0,
                           a=[None, None], b=[None, None]))
    cases.append(make_case("second selected value 0x0081 aborts", record1={
        "flag": 0x01, "selected": 0x0081, "short": 0x00}))
    cases.append(make_case("second selected value 0x0080 passes", record1={
        "flag": 0x01, "selected": 0x0080, "short": 0x00}))
    cases.append(make_case("second fallback 0x265 aborts", node1=0x0265))
    cases.append(make_case("second fallback 0x264 passes", node1=0x0264))

    # --- first and second lookups disagree: value from first, subindex from
    #     second, and the two categories can differ.
    cases.append(make_case(
        "first flag clear second flag set",
        node0=0x0010,
        record0={"flag": 0x00, "selected": 0x0000, "short": 0x00},
        record1={"flag": 0x01, "selected": 0x0042, "short": 0x00},
        d=1))
    cases.append(make_case(
        "first flag set second flag clear",
        record0={"flag": 0x01, "selected": 0x0020, "short": 0x03},
        node1=0x0010,
        record1={"flag": 0x00, "selected": 0x0000, "short": 0x00},
        d=1))
    cases.append(make_case(
        "first short count from first record only",
        node0=0x0005,
        record0={"flag": 0x00, "selected": 0x0000, "short": 0x44},
        record1={"flag": 0x00, "selected": 0x0000, "short": 0x00},
        d=0))

    # --- C/D results and tails
    cases.append(make_case("C returns 0 after both lookups", c=0))
    cases.append(make_case("D returns 0 with no short count", d=0,
                           node0=0x0000))
    cases.append(make_case("D returns 0 with short count", d=0,
                           record0={"flag": 0x01, "selected": 0x0000,
                                    "short": 0x80}))
    cases.append(make_case("D returns non-zero forwards E", d=1))
    cases.append(make_case("E return value forwarded", d=1, e=0xDEADBEEF))
    cases.append(make_case("F return value forwarded", d=0, f=0xF000BEEF,
                           record0={"flag": 0x01, "selected": 0x0000,
                                    "short": 0x02}))
    cases.append(make_case("G return value forwarded", d=0, g=0x6000BEEF,
                           node0=0x0000))

    # --- bundle reload after the row setter
    cases.append(make_case("D rewrites bundle slot before E", d=1,
                           d_bundle=BUNDLE1))

    # --- 16-bit id truncation for the lookups, full id for the E tail
    for ident in (0x0000ABCD, 0x1234ABCD, 0xFFFFABCD, 0x00010000, 0x7FFFFFFF):
        cases.append(make_case(f"id truncation {ident}", id=ident, d=1))
    cases.append(make_case("id truncation 0x1234ABCD D 0 G", id=0x1234ABCD,
                           d=0))

    # --- stack argument forwarding
    for arg1, arg2, arg3 in (
        (0x00000000, 0xFFFFFFFF, 0x80000000),
        (0xFEEDFACE, 0xCAFEBABE, 0xDEADBEEF),
    ):
        cases.append(make_case(
            f"stack args {arg1:08x}/{arg2:08x}/{arg3:08x}", arg1=arg1,
            arg2=arg2, arg3=arg3, d=1))
        cases.append(make_case(
            f"stack args {arg1:08x}/{arg2:08x}/{arg3:08x} G", arg1=arg1,
            arg2=arg2, arg3=arg3, d=0, node0=0x0000))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = EE3F8Runner().run(orig_code, case)
        cand = EE3F8Runner().run(cand_code, case)
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
    print("Testing camp_func_001ee3f8 (0x001ee3f8)...")
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
        ("selected_bound", "constexpr s32 kSelectedValueMax = 0x81;",
         "constexpr s32 kSelectedValueMax = 0x80;"),
        ("fallback_bound", "constexpr s32 kFallbackValueMax = 0x266;",
         "constexpr s32 kFallbackValueMax = 0x265;"),
        ("battle_category", "constexpr u32 kBattleCategory = 0x23;",
         "constexpr u32 kBattleCategory = 0x17;"),
        ("flag_offset", "constexpr u32 kBattleFlagByte = 0x03;",
         "constexpr u32 kBattleFlagByte = 0x04;"),
        ("selected_offset", "constexpr u32 kBattleSelectedValue = 0x88;",
         "constexpr u32 kBattleSelectedValue = 0x8A;"),
        ("camp_offset", "constexpr u32 kCampValueCount = 0x90;",
         "constexpr u32 kCampValueCount = 0x92;"),
        ("scale", "constexpr u32 kMillisecondScale = 1000;",
         "constexpr u32 kMillisecondScale = 999;"),
        ("subindex_seed", "u32 subindex = static_cast<u32>(id);",
         "u32 subindex = 0;"),
    ):
        mutant_code = compile_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = EE3F8Runner().run(orig_code, case)
            bad = EE3F8Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        if not detected:
            raise SystemExit(f"negative control failed: {name} was not detected")
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
