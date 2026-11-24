#!/usr/bin/env python3
"""Differential test for the 0x0013A29C span (484 bytes) using Unicorn ARM.

The ledger row covers two entry points:

  * 0x0013A29C  engine_func_0013a29c(void* state)       (channel reset)
  * 0x0013A458  engine_func_0013a458(void* state, f32)  (channel setter)

The runner compiles src/engine/leaf_batch41_c.cpp, extracts both candidate
symbols, resolves their direct calls to deterministic stubs placed at the
original target addresses, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in two Unicorn machines with
identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log with every register/float argument (floats logged as
    raw IEEE-754 bits) and the architected stack words of each helper;
  * the full observable object page, engine-base page (selector table plus slot
    pointer cell) and slot/descriptor page;
  * every emulated write outside the private stack is reported.

Coverage: gate byte zero/non-zero, all signed gain bytes for +0x30/+0x31,
readiness-gate returns 0/1/-1/INT_MAX, distinct table indices, slot pointers,
pre-filled object word/float/halfword fields, mode-0/mode-1 helper ordering,
the second entry point on both the skip and the update path, and negative
controls for constants, modes, stores and the skip-path return value.

The helper stubs reproduce the *post-readiness-gate* effect of each real helper
(the helpers themselves re-check 0x002BB5B4).  The readiness gate is exercised
directly through the one call made by the body at 0x0013A3FC.
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
OUT_DIR = ROOT / "build/test_leaf_0013a29c"

FUNC_ADDR = 0x0013A29C
FUNC_SIZE = 484
SUB_ADDR = 0x0013A458
SUB_SIZE = 0x28  # instructions plus the trailing 0x004E6F64 literal

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the body and every stub below 0x2C3AA8
OBJ_ADDR = 0x00700000
OBJ_SIZE = 0x00010000
BASE_ADDR = 0x004E0000
BASE_SIZE = 0x00010000
SLOT_ADDR = 0x00500000
SLOT_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Fixed engine channel-table base carried by the 0x0013A454 literal.
ENGINE_BASE = 0x004E6F64
# offsetof(ENGINE_BASE) inside the mapped base page.
BASE_PAGE_OFFSET = ENGINE_BASE - BASE_ADDR
# u16 selector at base + 0x131E.
SELECTOR_OFFSET = BASE_PAGE_OFFSET + 0x131E

# A distinctive sentinel pattern for every fixture byte.
SENTINEL = bytes(((i * 7 + 0x33) & 0xFF) for i in range(0x10000))


def sentinel(size: int, seed: int = 0) -> bytes:
    return bytes(((i * 7 + 0x33 + seed) & 0xFF) for i in range(size))


STUB_2A86E4 = 0x002A86E4
STUB_2A8674 = 0x002A8674
STUB_2A8608 = 0x002A8608
STUB_147074 = 0x00147074
STUB_146F88 = 0x00146F88
STUB_147020 = 0x00147020
STUB_146FD8 = 0x00146FD8
STUB_147128 = 0x00147128
STUB_146F44 = 0x00146F44
STUB_2BB5B4 = 0x002BB5B4
STUB_2C3AA8 = 0x002C3AA8
STUB_2C3A24 = 0x002C3A24

STUB_NAMES = {
    STUB_2A86E4: "func_002a86e4",
    STUB_2A8674: "func_002a8674",
    STUB_2A8608: "func_002a8608",
    STUB_147074: "func_00147074",
    STUB_146F88: "func_00146f88",
    STUB_147020: "func_00147020",
    STUB_146FD8: "func_00146fd8",
    STUB_147128: "func_00147128",
    STUB_146F44: "func_00146f44",
    STUB_2BB5B4: "func_002bb5b4",
    STUB_2C3AA8: "engine_func_002c3aa8",
    STUB_2C3A24: "engine_func_002c3a24",
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


# ------------------------------------------------------------------ utilities


def get_orig_bytes(address: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(address - 0x00100000)
        return f.read(size)


def float_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def compile_candidate():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")

    functions = extract_elf_functions_detailed(obj_file)
    found: dict[str, bytes] = {}
    for symbol, (raw, relocs) in functions.items():
        for wanted, base in (
            ("engine_func_0013a29c", FUNC_ADDR),
            ("engine_func_0013a458", SUB_ADDR),
        ):
            if wanted not in symbol:
                continue
            code = bytearray(raw)
            for rel in relocs:
                if rel.relocation_type in (1, 28, 29):
                    target = None
                    for address, name in ((a, n) for a, n in STUB_NAMES.items()):
                        if f"{address:08x}" in rel.symbol_name:
                            target = address
                            break
                    if target is None:
                        raise RuntimeError(
                            f"unresolved call relocation {rel.symbol_name} "
                            f"in {symbol}"
                        )
                    if target & 3:
                        raise RuntimeError(f"unaligned call target 0x{target:08x}")
                    pc = base + rel.offset + 8
                    displacement = (target - pc) >> 2
                    original = struct.unpack_from("<I", code, rel.offset)[0]
                    cond = original & 0xFF000000
                    struct.pack_into(
                        "<I", code, rel.offset,
                        cond | (displacement & 0x00FFFFFF),
                    )
                elif rel.relocation_type == 2:  # R_ARM_ABS32
                    addend = struct.unpack_from("<I", code, rel.offset)[0]
                    raise RuntimeError(
                        f"unexpected ABS32 relocation {rel.symbol_name} "
                        f"addend 0x{addend:08x} in {symbol}"
                    )
                else:
                    raise RuntimeError(
                        f"unhandled relocation type {rel.relocation_type} "
                        f"for {rel.symbol_name} in {symbol}"
                    )
            found[wanted] = bytes(code)
    if "engine_func_0013a29c" not in found:
        raise RuntimeError(
            f"engine_func_0013a29c not found: {sorted(functions)}"
        )
    if "engine_func_0013a458" not in found:
        raise RuntimeError(
            f"engine_func_0013a458 not found: {sorted(functions)}"
        )
    return found["engine_func_0013a29c"], found["engine_func_0013a458"]


def compile_mutant(name: str, old: str, new: str):
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant = OUT_DIR / f"mutant_{name}.cpp"
    mutant.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    functions = extract_elf_functions_detailed(obj_file)
    out: dict[str, bytes] = {}
    for symbol, (raw, relocs) in functions.items():
        for wanted, base in (
            ("engine_func_0013a29c", FUNC_ADDR),
            ("engine_func_0013a458", SUB_ADDR),
        ):
            if wanted not in symbol:
                continue
            code = bytearray(raw)
            for rel in relocs:
                if rel.relocation_type in (1, 28, 29):
                    target = None
                    for address in STUB_NAMES:
                        if f"{address:08x}" in rel.symbol_name:
                            target = address
                            break
                    if target is None:
                        raise RuntimeError(
                            f"unresolved mutant relocation {rel.symbol_name}"
                        )
                    pc = base + rel.offset + 8
                    displacement = (target - pc) >> 2
                    original = struct.unpack_from("<I", code, rel.offset)[0]
                    cond = original & 0xFF000000
                    struct.pack_into(
                        "<I", code, rel.offset,
                        cond | (displacement & 0x00FFFFFF),
                    )
                else:
                    raise RuntimeError(
                        f"unhandled mutant relocation {rel.relocation_type}"
                    )
            out[wanted] = bytes(code)
    return out["engine_func_0013a29c"], out["engine_func_0013a458"]


# -------------------------------------------------------------------- fixtures


def build_obj(case: dict) -> bytes:
    page = bytearray(sentinel(OBJ_SIZE))
    page[0x00] = case.get("gate", 1) & 0xFF
    page[0x01] = case.get("flag_01", 0xA5) & 0xFF
    page[0x03] = case.get("flag_03", 0xA5) & 0xFF
    struct.pack_into("<I", page, 0x04, case.get("value_04", 0x40B00000))
    struct.pack_into("<I", page, 0x08, case.get("value_08", 0x40400000))
    struct.pack_into("<I", page, 0x0C, case.get("value_0c", 0x3F000000))
    struct.pack_into("<I", page, 0x10, case.get("value_10", 0x3E800000))
    for offset, key in ((0x14, "word_14"), (0x18, "word_18"),
                        (0x1C, "word_1c"), (0x20, "word_20")):
        struct.pack_into("<I", page, offset, case.get(key, 0xDEADBEEF))
    page[0x24] = case.get("byte_24", 0x5A) & 0xFF
    page[0x25] = case.get("byte_25", 0x5A) & 0xFF
    struct.pack_into("<H", page, 0x28, case.get("half_28", 0x1234) & 0xFFFF)
    struct.pack_into("<H", page, 0x2A, case.get("half_2a", 0x1234) & 0xFFFF)
    page[0x30] = case.get("byte_30", 0x7F) & 0xFF
    page[0x31] = case.get("byte_31", 0x80) & 0xFF
    struct.pack_into("<H", page, 0x32, case.get("half_32", 0x1234) & 0xFFFF)
    return bytes(page)


def build_base(case: dict) -> bytes:
    page = bytearray(sentinel(BASE_SIZE, seed=0x11))
    index = case.get("index", 0)
    slot = case.get("slot", SLOT_ADDR + case.get("slot_offset", 0x40))
    struct.pack_into("<H", page, SELECTOR_OFFSET, index & 0xFFFF)
    cell = BASE_PAGE_OFFSET + 0x1000 + index * 4 + 0xA0
    if not (0 <= cell <= BASE_SIZE - 4):
        raise RuntimeError(f"slot pointer cell 0x{cell:x} outside base page")
    struct.pack_into("<I", page, cell, slot)
    return bytes(page)


def build_slot(case: dict) -> bytes:
    page = bytearray(sentinel(SLOT_SIZE, seed=0x77))
    offset = case.get("slot_offset", 0x40)
    # Field values the helpers overwrite are pre-filled with distinct values.
    struct.pack_into("<I", page, offset + 0x00, case.get("slot_flags", 0x80000001))
    struct.pack_into("<I", page, offset + 0x04, case.get("slot_04", 0x7FC00000))
    struct.pack_into("<I", page, offset + 0x08, case.get("slot_08", 0x11223344))
    struct.pack_into("<H", page, offset + 0x10, 0xAAAA)
    struct.pack_into("<H", page, offset + 0x18, 0xBBBB)
    struct.pack_into("<H", page, offset + 0x1C, 0xCCCC)
    struct.pack_into("<H", page, offset + 0x22, 0xDDDD)
    struct.pack_into("<H", page, offset + 0x28, 0xEEEE)
    struct.pack_into("<H", page, offset + 0x2A, 0xFFFF)
    struct.pack_into("<H", page, offset + 0xBC, 0x1234)
    struct.pack_into("<I", page, offset + 0xC0, case.get("slot_c0", 0x22222222))
    return bytes(page)


# ---------------------------------------------------------------------- runner


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # Enable the VFP coprocessor used by the float helpers.
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(BASE_ADDR, BASE_SIZE)
        self.uc.mem_map(SLOT_ADDR, SLOT_SIZE)
        self.uc.mem_map(OBJ_ADDR, OBJ_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for address in STUB_NAMES:
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    # ---------------------------------------------------------------- helpers
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", bytes(self.uc.mem_read(sp, 4 * count)))

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], tuple(args)))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _slot(self) -> int:
        index = struct.unpack(
            "<H", bytes(self.uc.mem_read(ENGINE_BASE + 0x131E, 2))
        )[0]
        cell = ENGINE_BASE + index * 4 + 0x1000 + 0xA0
        return struct.unpack("<I", bytes(self.uc.mem_read(cell, 4)))[0]

    def _read_u16(self, address: int) -> int:
        return struct.unpack("<H", bytes(self.uc.mem_read(address, 2)))[0]

    def _read_u32(self, address: int) -> int:
        return struct.unpack("<I", bytes(self.uc.mem_read(address, 4)))[0]

    def _write_u16(self, address: int, value: int) -> None:
        self.uc.mem_write(address, struct.pack("<H", value & 0xFFFF))

    def _write_u32(self, address: int, value: int) -> None:
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    # ------------------------------------------------------------------ stubs
    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)

        if address == STUB_2A86E4:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            self._log(address, r0, s0)
            slot = self._slot()
            self._write_u32(slot + 4, s0)
            self._write_u32(slot, self._read_u32(slot) | 0x00010000)
            uc.reg_write(arm.UC_ARM_REG_R0, 0xA86E4000)
        elif address == STUB_2A8674:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            self._log(address, r0, r1, s0)
            slot = self._slot()
            self._write_u32(slot + 8 + r1 * 4, s0)
            flags = self._read_u32(slot)
            if r1 == 0:
                flags |= 0x01000000
            elif r1 == 1:
                flags |= 0x02000000
            self._write_u32(slot, flags)
            uc.reg_write(arm.UC_ARM_REG_R0, 0xA8674000)
        elif address == STUB_2A8608:
            self._log(address, r0, r1, r2)
            slot = self._slot()
            self._write_u16(slot + 0x28 + r1 * 2, r2)
            flags = self._read_u32(slot)
            if r1 == 0:
                flags |= 0x00000100
            elif r1 == 1:
                flags |= 0x00000200
            self._write_u32(slot, flags)
            uc.reg_write(arm.UC_ARM_REG_R0, 1)
        elif address == STUB_147074:
            self._log(address, r0, r1, r2)
            slot = self._slot()
            self._write_u16(slot + 0x24 + r1 * 2, r2)
            flags = self._read_u32(slot)
            if r1 == 0:
                flags |= 0x00000040
            elif r1 == 1:
                flags |= 0x00000080
            self._write_u32(slot, flags)
            uc.reg_write(arm.UC_ARM_REG_R0, 1)
        elif address == STUB_146F88:
            self._log(address, r0, r1)
            slot = self._slot()
            value = 0x8000 if r1 > 0x8000 else r1
            self._write_u16(slot + 0x22, value)
            self._write_u32(slot, self._read_u32(slot) | 0x80000000)
            uc.reg_write(arm.UC_ARM_REG_R0, 1)
        elif address == STUB_147020:
            self._log(address, r0, r1)
            slot = self._slot()
            value = 0x7FFF if r1 >= 0x8000 else r1
            self._write_u16(slot + 0x1C, value)
            self._write_u32(slot, self._read_u32(slot) | 0x20000000)
            uc.reg_write(arm.UC_ARM_REG_R0, 1)
        elif address == STUB_146FD8:
            self._log(address, r0, r1)
            slot = self._slot()
            self._write_u16(slot + 0x18, r1)
            self._write_u32(slot, self._read_u32(slot) | 0x08000000)
            uc.reg_write(arm.UC_ARM_REG_R0, 1)
        elif address == STUB_147128:
            self._log(address, r0, r1)
            slot = self._slot()
            self._write_u16(slot + 0x10, r1)
            self._write_u32(slot, self._read_u32(slot) | 0x00008000)
            uc.reg_write(arm.UC_ARM_REG_R0, 1)
        elif address == STUB_146F44:
            self._log(address, r0, r1)
            slot = self._slot()
            self._write_u16(slot + 0xBC, r1)
            self._write_u32(slot + 0xC0, self._read_u32(slot + 0xC0) | 0x00010000)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x146F4400)
        elif address == STUB_2BB5B4:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("gate_result", 1))
        elif address in (STUB_2C3AA8, STUB_2C3A24):
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        else:  # pragma: no cover - guarded by registration
            raise AssertionError(f"unexpected stub 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, address: int, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(address, code)
        self.uc.mem_write(OBJ_ADDR, build_obj(case))
        self.uc.mem_write(BASE_ADDR, build_base(case))
        self.uc.mem_write(SLOT_ADDR, build_slot(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_S0, case.get("arg_s0", float_bits(0.5)))
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(address, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for write_address, size, _value in self.writes:
            in_region = (
                STACK_ADDR <= write_address < STACK_ADDR + STACK_SIZE
                or OBJ_ADDR <= write_address < OBJ_ADDR + OBJ_SIZE
                or BASE_ADDR <= write_address < BASE_ADDR + BASE_SIZE
                or SLOT_ADDR <= write_address < SLOT_ADDR + SLOT_SIZE
            )
            if not in_region:
                unexpected_writes.append((write_address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "obj": bytes(self.uc.mem_read(OBJ_ADDR, OBJ_SIZE)),
            "base": bytes(self.uc.mem_read(BASE_ADDR, BASE_SIZE)),
            "slot": bytes(self.uc.mem_read(SLOT_ADDR, SLOT_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved",
                "call_log", "obj", "base", "slot", "unexpected_writes"):
        if orig[key] != cand[key]:
            if key in ("obj", "base", "slot"):
                first = next(
                    (i for i, (a, b) in enumerate(zip(orig[key], cand[key])) if a != b),
                    None,
                )
                problems.append(
                    f"{key}: differs at offset 0x{first:x}  "
                    f"orig={orig[key][first]:02x} cand={cand[key][first]:02x}"
                    if first is not None
                    else f"{key}: length differs"
                )
            else:
                problems.append(f"{key}: orig={orig[key]!r} cand={cand[key]!r}")
    return problems


# ------------------------------------------------------------------- case sets


def base_case(name: str, entry: str = "main", **overrides) -> dict:
    case = {
        "name": name,
        "entry": entry,
        "gate": 1,
        "gate_result": 1,
        "index": 0,
        "slot_offset": 0x40,
        "arg_s0": float_bits(0.5),
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # Gate byte 0 skips all four float resets and the two float helpers.
    cases.append(base_case("gate byte 0 skips float block", gate=0))
    cases.append(base_case("gate byte 0, readiness gate 0",
                           gate=0, gate_result=0))

    # Gate byte non-zero, readiness gate values (only zero/non-zero matters).
    for result in (0, 1, -1, 0x7FFFFFFF, -0x80000000):
        cases.append(
            base_case(f"gate byte 1 readiness 0x{result & 0xFFFFFFFF:08x}",
                      gate=1, gate_result=result)
        )
    cases.append(base_case("gate byte 0xFF readiness 1", gate=0xFF))

    # Every signed gain byte value forwarded through mode 0/1.
    for value in (0x00, 0x01, 0x7F, 0x80, 0x81, 0xFE, 0xFF):
        cases.append(
            base_case(f"gain bytes +0x30=0x{value:02x} +0x31=0x{value:02x}",
                      byte_30=value, byte_31=value)
        )
    cases.append(base_case("gain bytes +0x30=0x80 +0x31=0x7F",
                           byte_30=0x80, byte_31=0x7F))
    cases.append(base_case("gain bytes +0x30=0x7F +0x31=0x80",
                           byte_30=0x7F, byte_31=0x80))

    # Distinct table selectors and slot locations to catch hard-coded slots.
    for index, slot_offset in ((0, 0), (1, 0x100), (2, 0x200), (0x77, 0x300)):
        cases.append(
            base_case(f"selector {index} slot offset 0x{slot_offset:x}",
                      index=index, slot_offset=slot_offset)
        )

    # Pre-existing values that the initializer overwrites, including flags.
    for flags in (0, 0xFFFFFFFF, 0x0000FFFF):
        cases.append(base_case(f"slot flags 0x{flags:08x}", slot_flags=flags))
    cases.append(base_case("object fields pre-filled",
                           word_14=0, word_18=0xFFFFFFFF, word_1c=1,
                           word_20=0x80000000, byte_24=0, byte_25=0xFF,
                           half_28=0x7FFF, half_2a=0x8000, half_32=2,
                           flag_01=0, flag_03=1))
    cases.append(base_case("object float fields NaN/inf",
                           value_04=0x7FC00000, value_08=0x7F800000,
                           value_0c=0xFF800000, value_10=0x80000000))

    # Second entry point: skip path returns the incoming object pointer.
    cases.append(base_case("setter skip path", entry="sub", gate=0,
                           arg_s0=float_bits(1.25)))
    cases.append(base_case("setter skip path negative", entry="sub", gate=0,
                           arg_s0=float_bits(-3.5)))
    # Second entry point: update path stores the argument and forwards the
    # product with the current +0x08 value.
    for value in (0.0, -0.0, 1.0, -1.0, 0.5, -3.5, 123.25):
        cases.append(
            base_case(f"setter update value {value}", entry="sub", gate=1,
                      arg_s0=float_bits(value))
        )
    cases.append(base_case("setter update with NaN multiplier", entry="sub",
                           gate=1, value_08=0x7FC00000))
    return cases


def run_entry(orig_code, cand_code, case) -> int:
    entry = case["entry"]
    if entry == "main":
        address = FUNC_ADDR
        orig = orig_code["main"]
        cand = cand_code["main"]
    else:
        address = SUB_ADDR
        orig = orig_code["sub"]
        cand = cand_code["sub"]

    orig_result = Runner().run(orig, address, case)
    cand_result = Runner().run(cand, address, case)
    problems = compare(orig_result, cand_result)
    if problems:
        print(f"  [FAIL] {case['name']}")
        for problem in problems:
            print(f"    {problem}")
        raise SystemExit(1)
    print(
        f"  [PASS] {case['name']}  "
        f"({len(orig_result['call_log'])} calls)"
    )
    return 1


def code_set(main: bytes, sub: bytes) -> dict[str, bytes]:
    return {"main": main, "sub": sub}


def main() -> None:
    print("Testing engine_func_0013a29c / engine_func_0013a458 (0x0013a29c)...")
    orig_main = get_orig_bytes(FUNC_ADDR, FUNC_SIZE)
    orig_sub = get_orig_bytes(SUB_ADDR, SUB_SIZE)
    cand_main, cand_sub = compile_candidate()
    print(
        f"Original main {len(orig_main)} B / sub {len(orig_sub)} B; "
        f"candidate main {len(cand_main)} B / sub {len(cand_sub)} B."
    )

    orig_code = code_set(orig_main, orig_sub)
    cand_code = code_set(cand_main, cand_sub)
    cases = make_cases()
    passed = 0
    for case in cases:
        passed += run_entry(orig_code, cand_code, case)
    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")

    print("\nNegative controls:")
    mutants = (
        ("unity_constant", "constexpr f32 kUnity = 1.0f;",
         "constexpr f32 kUnity = 2.0f;"),
        ("half_2a", "state->half_2a = 0x8000u;", "state->half_2a = 0x8001u;"),
        ("half_28", "state->half_28 = 0x7FFFu;", "state->half_28 = 0x7FFEu;"),
        ("tail_value", "return func_00146f44(kEngineBase, 0u);",
         "return func_00146f44(kEngineBase, 1u);"),
        ("mode_zero_first",
         "(void)func_002a8608(kEngineBase, 0u, "
         "static_cast<s32>(state->byte_30));",
         "(void)func_002a8608(kEngineBase, 1u, "
         "static_cast<s32>(state->byte_30));"),
        ("value_0c_reset", "state->value_0c = kUnity;",
         "state->value_0c = kUnity * 2.0f;"),
        ("flag_01", "state->flag_01 = 1;", "state->flag_01 = 2;"),
        ("byte_25", "state->byte_25 = 0;", "state->byte_25 = 1;"),
        ("setter_skip_return",
         "return static_cast<u32>(reinterpret_cast<std::uintptr_t>(state_ptr));",
         "return 0u;"),
        ("setter_store",
         "    state->value_04 = value;\n"
         "    return func_002a86e4(kEngineBase, value * state->value_08);",
         "    state->value_04 = value * 2.0f;\n"
         "    return func_002a86e4(kEngineBase, value * state->value_08);"),
    )
    for name, old, new in mutants:
        mutant_main, mutant_sub = compile_mutant(name, old, new)
        mutant_code = code_set(mutant_main, mutant_sub)
        detected = False
        for case in cases:
            if case["entry"] == "main":
                address, orig, mutant = FUNC_ADDR, orig_code["main"], mutant_code["main"]
            else:
                address, orig, mutant = SUB_ADDR, orig_code["sub"], mutant_code["sub"]
            orig_result = Runner().run(orig, address, case)
            mutant_result = Runner().run(mutant, address, case)
            if compare(orig_result, mutant_result):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print("\nAll differential cases and negative controls passed.")


if __name__ == "__main__":
    main()
