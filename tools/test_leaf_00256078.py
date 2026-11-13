#!/usr/bin/env python3
"""Differential test for script_vm_func_00256078 (0x00256078) using Unicorn ARM.

Compiles ``src/engine/leaf_batch45_a.cpp``, extracts the
``script_vm_func_00256078`` body, relocates its direct calls to deterministic
stubs at the pinned original addresses, and runs the pinned original
(``extracted/exefs/code.bin``) against the candidate in separate Unicorn
machines with identical fixtures.

Compared outputs:
  * return ``r0`` (the tail call's result), continuation PC, final SP and the
    restored callee-saved ``r4-r11``;
  * the ordered call log with every meaningful register argument, including the
    ``ldr``/``strd``/memcpy/zero-fill sizes and the ``0x00255318`` tail call;
  * the owner work page, the request page, the unit-slot page, the actor table
    page (normal and high-alias), the camp list page, the helper value page,
    the zero page used for null slot results, and the stack above the entry SP,
    byte for byte;
  * every emulated write outside those fixtures and the private stack.

Coverage:
  * modes 0, 1, 2 and everything else (3, 4, 0xFF, 0x80000000, 0xFFFFFFFF);
  * mode 0 request byte 0 bit 0 set/clear with the remaining bits varied;
  * mode 0 signed ``s16`` request payload index 0, 1, 0x7FFF, 0x8000, 0xFFFF,
    0x8001;
  * mode 1 free-slot selection (slot 4 free, 4/5 occupied, all occupied, slot
    0x34) and the optional flag byte 0/1/2/0xFF; ``u16`` id boundaries;
  * mode 2 list status bit 1 set/clear and unrelated bits;
  * slot-claim failures: out-of-range index 0x6D/0x6E/-1/0x80000000, occupied
    unit, and mode 1 with every candidate slot occupied;
  * marker boundaries index -1, 0, 1, 3, 4, 5, 0x35, 0x36, 0x37,
    0x80000000 and two wrapped-offset indices resolved through a high alias;
  * the stack ``flag`` argument 0, 1, 2 and 0xFFFFFFFF;
  * 16-bit wrap-around of both mode counters.

The test does not model fault timing: a null slot result is exercised with
address 0 mapped as a zero page, exactly like the original's subsequent
low-address accesses.  Modes outside {0,1,2} leave the slot pointer at zero and
therefore write to that zero page as well.
"""

from __future__ import annotations

import random
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
OUT_DIR = ROOT / "build/test_leaf_00256078"

FUNC_ADDR = 0x00256078
FUNC_SIZE = 620

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000      # covers the function and every stub below 0x3F0000
ZERO_ADDR = 0x00000000
ZERO_SIZE = 0x00010000
OWNER_ADDR = 0x00700000
OWNER_SIZE = 0x00008000
REQUEST_ADDR = 0x00710000
REQUEST_SIZE = 0x00001000
UNIT_ADDR = 0x00720000
UNIT_SIZE = 0x00020000
ACTOR_ADDR = 0x00750000
ACTOR_SIZE = 0x00010000
ACTOR_HIGH_ADDR = 0xFF000000
ACTOR_HIGH_SIZE = 0x00010000
LIST_ADDR = 0x00790000
LIST_SIZE = 0x00010000
VALUE_ADDR = 0x007A0000
VALUE_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets; stubs are placed at the same addresses so both
# the original bytes and the relocated candidate resolve to them.
STUB_256418 = 0x00256418
STUB_33A7D4 = 0x0033A7D4
STUB_2BCF58 = 0x002BCF58
STUB_2B66EC = 0x002B66EC
STUB_2A89E4 = 0x002A89E4
STUB_2B087C = 0x002B087C
STUB_2A8A08 = 0x002A8A08
STUB_2C3B48 = 0x002C3B48
STUB_3BE980 = 0x003BE980
STUB_255318 = 0x00255318

STUB_NAMES = {
    STUB_256418: "battle_func_00256418",
    STUB_33A7D4: "script_vm_func_0033a7d4",
    STUB_2BCF58: "ui_func_002bcf58",
    STUB_2B66EC: "script_vm_func_002b66ec",
    STUB_2A89E4: "camp_func_002a89e4",
    STUB_2B087C: "battle_func_002b087c",
    STUB_2A8A08: "camp_func_002a8a08",
    STUB_2C3B48: "engine_func_002c3b48",
    STUB_3BE980: "camp_func_003be980",
    STUB_255318: "script_vm_func_00255318",
}

STUB_ADDRESSES = {name: address for address, name in STUB_NAMES.items()}

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

# ARM-visible layout constants (the test knows no wider structure).
UNIT_STRIDE = 0x288
UNIT_LIMIT = 0x6D
UNIT_ID_OFFSET = 0x6E
ACTOR_STRIDE = 0x114
OWNER_ACTOR_BASE = 0x1E98
OWNER_COUNTER0 = 0x1FC4
OWNER_COUNTER1 = 0x1FC6
OWNER_MODE2_FLAG = 0x49C4
CAMP_RECORD_OFFSET = 0x910C
CAMP_STATUS_OFFSET = 0x910C + 0x44
VALUE_A = VALUE_ADDR + 0x100
VALUE_B = VALUE_ADDR + 0x200
VALUE_C = VALUE_ADDR + 0x300


def s16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def pattern(size: int, seed: int, step: int = 7) -> bytes:
    return bytes((index * step + seed) & 0xFF for index in range(size))


# --------------------------------------------------------------------- candidate
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    functions = extract_elf_functions_detailed(obj_file)
    candidate = functions.get("script_vm_func_00256078")
    if candidate is None:
        raise RuntimeError(
            "script_vm_func_00256078 not found in object: "
            + ", ".join(sorted(functions))
        )

    code_raw, relocations = candidate
    code = bytearray(code_raw)
    if not relocations:
        raise RuntimeError("candidate has no relocations")
    for rel in relocations:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = STUB_ADDRESSES.get(rel.symbol_name)
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


def compile_variant(src_file: Path, obj_file: Path) -> bytes:
    result = compile_tu_armv6k(src_file, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed for {src_file}: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return compile_variant(SOURCE, OUT_DIR / "leaf_batch45_a.o")


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_source = OUT_DIR / f"mutant_{name}.cpp"
    mutant_source.write_text(text.replace(old, new), encoding="utf-8")
    return compile_variant(mutant_source, OUT_DIR / f"mutant_{name}.o")


# --------------------------------------------------------------------- fixtures
def build_owner(case: dict) -> bytes:
    page = bytearray(pattern(OWNER_SIZE, 0x11))
    struct.pack_into("<I", page, OWNER_ACTOR_BASE, case["actor_base"] & 0xFFFFFFFF)
    struct.pack_into("<H", page, OWNER_COUNTER0, case["counter0"] & 0xFFFF)
    struct.pack_into("<H", page, OWNER_COUNTER1, case["counter1"] & 0xFFFF)
    page[OWNER_MODE2_FLAG] = case["owner_flag"] & 0xFF
    return bytes(page)


def build_request(case: dict) -> bytes:
    page = bytearray(pattern(REQUEST_SIZE, 0x22, step=5))
    page[0] = case["req0"] & 0xFF
    struct.pack_into("<H", page, 2, case["req2"] & 0xFFFF)
    struct.pack_into("<H", page, 8, case["req8"] & 0xFFFF)
    page[0xD4] = case["req_d4"] & 0xFF
    return bytes(page)


def build_units(case: dict) -> bytes:
    page = bytearray(pattern(UNIT_SIZE, 0x33, step=3))
    for index in range(UNIT_LIMIT + 1):
        base = index * UNIT_STRIDE
        occupied = 1 if index in case["occupied"] else 0
        struct.pack_into("<I", page, base, 0xA5A50000 | (index << 1) | occupied)
        struct.pack_into(
            "<H", page, base + UNIT_ID_OFFSET,
            case["unit_ids"].get(index, 0x8000 | index),
        )
        # Non-zero junk in every area the routine must clear or overwrite.
        for offset in (0x72, 0xAE, 0x258, 0x274):
            struct.pack_into("<I", page, base + offset, 0xC0DE0000 | index)
        struct.pack_into("<H", page, base + 0xBE, 0xBEEF)
        page[base + 0xCC] = 0x7F
    return bytes(page)


def build_zero(case: dict) -> bytes:
    page = bytearray(ZERO_SIZE)
    struct.pack_into("<H", page, UNIT_ID_OFFSET, 0x0BAD)
    for offset in range(0x72, 0xAE, 4):
        struct.pack_into("<I", page, offset, 0x5A5A0000 | offset)
    for offset in range(0x258, 0x278, 4):
        struct.pack_into("<I", page, offset, 0x3C3C0000 | offset)
    struct.pack_into("<H", page, 0xBE, 0x1234)
    return bytes(page)


def build_list(case: dict) -> bytes:
    page = bytearray(pattern(LIST_SIZE, 0x55, step=11))
    struct.pack_into("<H", page, CAMP_STATUS_OFFSET, case["list_status"] & 0xFFFF)
    return bytes(page)


def read_actor(slot: int) -> int:
    return ACTOR_ADDR + slot * ACTOR_STRIDE


# ----------------------------------------------------------------------- runner
class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        for base, size in (
            (ZERO_ADDR, ZERO_SIZE),
            (CODE_ADDR, CODE_SIZE),
            (OWNER_ADDR, OWNER_SIZE),
            (REQUEST_ADDR, REQUEST_SIZE),
            (UNIT_ADDR, UNIT_SIZE),
            (ACTOR_ADDR, ACTOR_SIZE),
            (ACTOR_HIGH_ADDR, ACTOR_HIGH_SIZE),
            (LIST_ADDR, LIST_SIZE),
            (VALUE_ADDR, VALUE_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(base, size)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    # ------------------------------------------------------------------ stubs
    def _unit_available(self, index: int, want_occupied: int) -> int:
        if not 0 <= index < UNIT_LIMIT:
            return 0
        base = UNIT_ADDR + index * UNIT_STRIDE
        flag = struct.unpack("<I", self.uc.mem_read(base, 4))[0] & 1
        return base if flag == want_occupied else 0

    def _first_free_unit(self) -> int:
        for index in range(4, 0x36):
            base = UNIT_ADDR + index * UNIT_STRIDE
            flag = struct.unpack("<I", self.uc.mem_read(base, 4))[0] & 1
            if flag == 0:
                return base
        return 0

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_256418:
            self.call_log.append(("battle_func_00256418", r0, r1, r2))
            index = r1 - (1 << 32) if r1 & 0x80000000 else r1
            uc.reg_write(arm.UC_ARM_REG_R0, self._unit_available(index, r2))
        elif address == STUB_33A7D4:
            self.call_log.append(("script_vm_func_0033a7d4", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self._first_free_unit())
        elif address == STUB_2BCF58:
            self.call_log.append(("ui_func_002bcf58", r0, r1, r2))
            if r2:
                uc.mem_write(r0, bytes(uc.mem_read(r1, r2)))
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_2B66EC:
            self.call_log.append(("script_vm_func_002b66ec",))
            uc.reg_write(arm.UC_ARM_REG_R0, VALUE_A)
        elif address == STUB_2A89E4:
            index = r0 - (1 << 32) if r0 & 0x80000000 else r0
            self.call_log.append(("camp_func_002a89e4", index))
            uc.reg_write(arm.UC_ARM_REG_R0, VALUE_B + (index & 0x7F) * 0x10)
        elif address == STUB_2B087C:
            self.call_log.append(("battle_func_002b087c", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, VALUE_C + (r0 & 0xFF) * 4)
        elif address == STUB_2A8A08:
            self.call_log.append(("camp_func_002a8a08", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, LIST_ADDR)
        elif address == STUB_2C3B48:
            self.call_log.append(("engine_func_002c3b48", r0, r1))
            if r1:
                uc.mem_write(r0, bytes(r1))
        elif address == STUB_3BE980:
            self.call_log.append(("camp_func_003be980", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x30000000 | (r0 & 0xFFF))
        elif address == STUB_255318:
            self.call_log.append(("script_vm_func_00255318", r0, r1, r2, r3))
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                0x40000000
                ^ ((r0 & 0xFF) << 8)
                ^ ((r2 & 0xFFF) << 12)
                ^ (r1 & 0xF)
                ^ (r3 & 0xFFFF),
            )
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        uc = self.uc
        self.call_log = []
        self.writes = []

        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(ZERO_ADDR, build_zero(case))
        uc.mem_write(OWNER_ADDR, build_owner(case))
        uc.mem_write(REQUEST_ADDR, build_request(case))
        uc.mem_write(UNIT_ADDR, build_units(case))
        uc.mem_write(ACTOR_ADDR, pattern(ACTOR_SIZE, 0x44, step=9))
        uc.mem_write(ACTOR_HIGH_ADDR, pattern(ACTOR_HIGH_SIZE, 0x66, step=13))
        uc.mem_write(LIST_ADDR, build_list(case))
        uc.mem_write(VALUE_ADDR, pattern(VALUE_SIZE, 0x77, step=17))
        uc.mem_write(STACK_ADDR, b"\xCC" * STACK_SIZE)
        uc.mem_write(ENTRY_SP, struct.pack("<I", case["flag"] & 0xFFFFFFFF))
        self.writes = []
        uc.ctl_flush_tb()

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, OWNER_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R1, REQUEST_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R2, case["mode"] & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R3, case["index"] & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            uc.reg_write(CALLEE_SAVED[name], value)

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error
        finally:
            uc.ctl_flush_tb()

        fixtures = (
            ("zero", ZERO_ADDR, ZERO_SIZE),
            ("owner", OWNER_ADDR, OWNER_SIZE),
            ("request", REQUEST_ADDR, REQUEST_SIZE),
            ("units", UNIT_ADDR, UNIT_SIZE),
            ("actors", ACTOR_ADDR, ACTOR_SIZE),
            ("actors_high", ACTOR_HIGH_ADDR, ACTOR_HIGH_SIZE),
            ("list", LIST_ADDR, LIST_SIZE),
            ("values", VALUE_ADDR, VALUE_SIZE),
        )
        unexpected_writes = []
        for address, write_size in self.writes:
            inside = any(
                base <= address < base + size for _, base, size in fixtures
            ) or STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not inside:
                unexpected_writes.append((address, write_size))

        return {
            "r0": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "pages": {
                name: bytes(uc.mem_read(base, size))
                for name, base, size in fixtures
            },
            "stack_above": bytes(
                uc.mem_read(ENTRY_SP, STACK_ADDR + STACK_SIZE - ENTRY_SP)
            ),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list:
    problems = []
    for key in ("r0", "pc", "sp", "callee_saved", "call_log", "stack_above"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for name in orig["pages"]:
        if orig["pages"][name] != cand["pages"][name]:
            problems.append(f"page {name} differs")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


# ------------------------------------------------------------------------ cases
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "mode": 0,
        "index": 0,
        "flag": 0,
        "req0": 0x00,
        "req2": 0x0000,
        "req8": 0x0000,
        "req_d4": 0x00,
        "counter0": 0x1234,
        "counter1": 0x5678,
        "owner_flag": 0xA5,
        "occupied": set(),
        "unit_ids": {},
        "actor_base": ACTOR_ADDR,
        "list_status": 0x0000,
    }
    case.update(overrides)
    return case


def high_alias_case(name: str, index: int, **overrides) -> dict:
    """Place the wrapped actor-table offset inside the high alias page."""
    offset = (index * ACTOR_STRIDE) & 0xFFFFFFFF
    base = (ACTOR_HIGH_ADDR - offset) & 0xFFFFFFFF
    return base_case(name, index=index, actor_base=base, **overrides)


def make_cases() -> list:
    cases: list = []

    # --- mode dispatch ------------------------------------------------------
    cases.append(base_case("mode 0 baseline, request bit 0 clear"))
    cases.append(base_case("mode 0 request bit 0 set", req0=0x01))
    cases.append(base_case("mode 0 request bits 0 and 1 set", req0=0x03))
    cases.append(base_case("mode 0 request high bit only", req0=0x80))
    cases.append(base_case("mode 0 request all bits set", req0=0xFF))
    cases.append(base_case("mode 1 baseline", mode=1))
    cases.append(base_case("mode 2 baseline", mode=2))
    cases.append(base_case("mode 3 leaves a null slot", mode=3))
    cases.append(base_case("mode 4 leaves a null slot", mode=4))
    cases.append(base_case("mode 0xFF leaves a null slot", mode=0xFF))
    cases.append(base_case("mode 0x80000000 leaves a null slot", mode=0x80000000))
    cases.append(base_case("mode 0xFFFFFFFF leaves a null slot", mode=0xFFFFFFFF))

    # --- mode 0 payload selection and signed s16 index ----------------------
    for value, label in (
        (0x0000, "0"),
        (0x0001, "1"),
        (0x7FFF, "0x7fff"),
        (0x8000, "-0x8000"),
        (0xFFFF, "-1"),
        (0x8001, "-0x7fff"),
    ):
        cases.append(
            base_case(f"mode 0 flagged s16 payload {label}", req0=0x01, req8=value)
        )
        cases.append(
            base_case(f"mode 0 plain s16 payload {label}", req0=0x00, req8=value)
        )

    # --- mode 1 id and optional-flag byte ----------------------------------
    for value, label in (
        (0x0000, "0"),
        (0x0001, "1"),
        (0x7FFF, "0x7fff"),
        (0x8000, "0x8000"),
        (0xABCD, "0xabcd"),
        (0xFFFF, "0xffff"),
    ):
        cases.append(base_case(f"mode 1 id {label}", mode=1, req2=value))
    for byte, label in ((0x00, "0"), (0x01, "1"), (0x02, "2"), (0xFF, "0xff")):
        cases.append(
            base_case(f"mode 1 flag byte {label}", mode=1, req_d4=byte)
        )

    # --- mode 1 free-slot selection ----------------------------------------
    cases.append(base_case("mode 1 slots 4 and 5 occupied", mode=1,
                           occupied={4, 5}))
    cases.append(
        base_case("mode 1 all candidate slots occupied", mode=1,
                  occupied=set(range(4, 0x36)))
    )
    cases.append(
        base_case("mode 1 only slot 0x35 free", mode=1,
                  occupied=set(range(4, 0x35)))
    )
    cases.append(
        base_case("mode 1 slot 0x36 occupied is not scanned", mode=1,
                  occupied={0x36})
    )

    # --- mode 2 list status ------------------------------------------------
    for status, label in (
        (0x0000, "0x0000"),
        (0x0002, "bit 1"),
        (0x0003, "bits 0 and 1"),
        (0x0004, "bit 2"),
        (0xFFFF, "all bits"),
    ):
        cases.append(
            base_case(f"mode 2 status {label}", mode=2, list_status=status)
        )

    # --- slot-claim failures ----------------------------------------------
    cases.append(base_case("mode 0 index at the unit limit", index=0x6D))
    cases.append(base_case("mode 0 index past the unit limit", index=0x6E))
    cases.append(base_case("mode 0 occupied unit at index 0", occupied={0}))
    cases.append(base_case("mode 0 occupied unit at index 4", index=4,
                           occupied={4}))
    cases.append(high_alias_case("mode 0 index -1", -1))
    cases.append(base_case("mode 0 index 0x80000000", index=0x80000000))
    cases.append(base_case("mode 2 occupied unit at index 7", mode=2, index=7,
                           occupied={7}))
    cases.append(base_case("mode 2 index at the unit limit", mode=2, index=0x6D))

    # --- index boundaries for the join ------------------------------------
    for index in (0, 1, 2, 3, 4, 5, 0x35, 0x36, 0x37):
        cases.append(base_case(f"join index {index}", index=index))
        cases.append(base_case(f"join index {index} mode 1", mode=1, index=index))
    cases.append(base_case("join index 0x36 with flag", index=0x36, flag=1))
    cases.append(base_case("join index 0x37 with flag", index=0x37, flag=1))

    # --- wrapped actor-table offsets ---------------------------------------
    cases.append(high_alias_case("join index -1 wrapped offset", -1))
    cases.append(high_alias_case("join index 0x7fffffff wrapped offset",
                                 0x7FFFFFFF))
    cases.append(high_alias_case("join index 0x10004 truncates to 4", 0x10004))

    # --- stack flag ---------------------------------------------------------
    for flag, label in ((0, "0"), (1, "1"), (2, "2"), (0xFFFFFFFF, "-1")):
        cases.append(base_case(f"flag {label}", flag=flag))
    cases.append(base_case("flag 1 with mode 1", mode=1, flag=1))
    cases.append(base_case("flag 1 with mode 2", mode=2, flag=1))
    cases.append(base_case("flag 1 with mode 3", mode=3, flag=1))

    # --- 16-bit counter wrap -------------------------------------------------
    cases.append(base_case("mode 0 counter wraps", counter0=0xFFFF))
    cases.append(base_case("mode 1 counter wraps", mode=1, counter1=0xFFFF))
    cases.append(base_case("mode 0 counter zero", counter0=0x0000))
    cases.append(base_case("mode 2 keeps both counters", mode=2,
                           counter0=0xFFFF, counter1=0xFFFF))

    return cases


# ------------------------------------------------------------------------- main
def make_sweep_cases() -> list:
    """Deterministic combination sweep over every recovered field."""
    rng = random.Random(0x256078)
    cases: list = []
    for trial in range(40):
        mode = rng.choice([0, 1, 2, 3, 4, 0xFF, 0x80000000, 0xFFFFFFFF])
        fields = {
            "mode": mode,
            "flag": rng.getrandbits(32),
            "req0": rng.getrandbits(8),
            "req2": rng.getrandbits(16),
            "req8": rng.getrandbits(16),
            "req_d4": rng.getrandbits(8),
            "counter0": rng.getrandbits(16),
            "counter1": rng.getrandbits(16),
            "list_status": rng.getrandbits(16),
            "owner_flag": rng.getrandbits(8),
        }
        if rng.random() < 0.15:
            cases.append(high_alias_case(f"sweep {trial} wrapped", -1, **fields))
        else:
            cases.append(
                base_case(
                    f"sweep {trial}",
                    index=rng.randrange(0, 0x6E),
                    occupied={i for i in range(0x6E) if rng.random() < 0.3},
                    unit_ids={i: rng.getrandbits(16) for i in range(0x10)},
                    **fields,
                )
            )
    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases: list) -> int:
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
    print("Testing script_vm_func_00256078 (0x00256078)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nDeterministic combination sweep:")
    sweep_cases = make_sweep_cases()
    run_case_set(orig_code, cand_code, sweep_cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("mode0_flagged_kind", "constexpr u32 kKindMode0Flagged = 7u;",
         "constexpr u32 kKindMode0Flagged = 8u;"),
        ("actor_stride", "constexpr u32 kSlotTableStride = 0x114u;",
         "constexpr u32 kSlotTableStride = 0x110u;"),
        ("marker_boundary", "constexpr s32 kMarkerHighBoundary = 0x36;",
         "constexpr s32 kMarkerHighBoundary = 0x35;"),
        ("flag_argument_bit",
         "constexpr u32 kSlotBitFlagArgument = 0x20000000u;",
         "constexpr u32 kSlotBitFlagArgument = 0x10000000u;"),
        ("camp_status_offset",
         "constexpr u32 kCampRecordStatusOffset = 0x44u;",
         "constexpr u32 kCampRecordStatusOffset = 0x45u;"),
        ("request_tail_begin", "constexpr u32 kRequestTailBegin = 0x14Cu;",
         "constexpr u32 kRequestTailBegin = 0x148u;"),
        ("mode1_flag_byte", "constexpr u32 kSlotMode1ByteOffset = 0x1A0u;",
         "constexpr u32 kSlotMode1ByteOffset = 0x1A1u;"),
        ("mode0_payload_index", "constexpr u32 kSlotMode0IndexOffset = 0xD4u;",
         "constexpr u32 kSlotMode0IndexOffset = 0xD2u;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                print(f"  [PASS] {name} mutant detected by '{case['name']}'")
                break
        assert detected, f"negative control failed: {name} was not detected"

    print(
        f"\nAll {passed}/{len(cases)} differential cases and "
        f"{len(sweep_cases)}/{len(sweep_cases)} sweep cases PASSED."
    )


if __name__ == "__main__":
    main()
