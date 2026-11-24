#!/usr/bin/env python3
"""Differential test for script_vm_func_003b87a0 (0x003B87A0) using Unicorn ARM.

The candidate C++ in src/engine/leaf_batch41_c.cpp is compiled with
`compile_tu_armv6k`, its body extracted from the object, and every direct-call
relocation is re-pointed at a deterministic helper.  The pinned original
(extracted/exefs/code.bin) and the relocated candidate then run in separate
Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every register argument (stack arguments included
    where the helper has any -- none do here);
  * the object page (self+0x20/+0x28/+0x2C/+0x58/+0x9C/+0xD60/+0xE58/+0xE5C and
    the 0x00433158 probe slot live inside it), the global status page at
    0x0049FA1C, the 0x0029C660 status table at 0x004D9758, the probe object and
    the helper scratch page byte-for-byte;
  * any emulated write outside those pages and the private stack.

Coverage: each global status word alone and together; the probe returning 0/1
with a null, valid and unrelated pointer; the 0x00400000 short circuit; every
bit of both `tst` masks with the 0x00000100 suppression bit clear and set; the
0x00002000 / 0x00000040 local-update paths; the second-mask call ordering; and
the epilogue byte 0xE58 zero/non-zero with null and valid tail objects.  Negative
controls mutate the 0x7A offset, codes 13/6, three flag bits, the 0x0029C660
arguments, the 0xD60 offset and the 0xE58 offset; each must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_003b87a0"

FUNC_ADDR = 0x003B87A0
FUNC_SIZE = 476

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the function and every helper below 0x400000
OBJECT_ADDR = 0x00430000
OBJECT_SIZE = 0x00020000  # self+0xE5C and the 0x00433158 probe slot
STATUS_ADDR = 0x0049F000
STATUS_SIZE = 0x00001000  # global status page (0x0049FA1C, +0x78/+0x7A)
TABLE_ADDR = 0x004D9000
TABLE_SIZE = 0x00001000  # 0x0029C660 status table at 0x004D9758
PROBE_ADDR = 0x00600000
PROBE_SIZE = 0x00001000  # object passed to 0x00276718
SCRATCH_ADDR = 0x00700000
SCRATCH_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Fixture offsets, all derived from the evidenced absolute addresses.
STATUS_WORD78 = 0x0049FA1C + 0x78 - STATUS_ADDR
STATUS_WORD7A = 0x0049FA1C + 0x7A - STATUS_ADDR
TABLE_RECORD_BASE = 0x004D9758 - TABLE_ADDR
PROBE_SLOT = 0x00433158 - OBJECT_ADDR

OFF_FLAGS20 = 0x20
OFF_CODE28 = 0x28
OFF_CODE2C = 0x2C
OFF_OUT58 = 0x58
OFF_UPDATE9C = 0x9C
OFF_RESULT_D60 = 0xD60
OFF_TAIL_FLAG_E58 = 0xE58
OFF_TAIL_OBJECT_E5C = 0xE5C
OFF_SUB_WRITE_E04 = 0xE04
OFF_FRAME_WRITE_E08 = 0xE08
OFF_TAIL_WRITE_E0C = 0xE0C

# Sentinels for fields the function must (or must not) rewrite.
SENTINEL_CODE28 = 0xA5A50028
SENTINEL_CODE2C = 0xA5A5002C
SENTINEL_D60 = 0xA5A50D60
SENTINEL_OUT0 = 0x11111111
SENTINEL_OUT4 = 0x22222222

# Original direct-call targets; stubs are placed at the same addresses so both
# the original bytes and the relocated candidate resolve to them.
STUB_276718 = 0x00276718
STUB_29C660 = 0x0029C660
STUB_297128 = 0x00297128
STUB_22BA54 = 0x0022BA54
STUB_3B897C = 0x003B897C
STUB_22B90C = 0x0022B90C
STUB_22B9D0 = 0x0022B9D0
STUB_341C74 = 0x00341C74

STUB_NAMES = {
    STUB_276718: "script_vm_func_00276718",
    STUB_29C660: "script_vm_func_0029c660",
    STUB_297128: "shop_func_00297128",
    STUB_22BA54: "engine_func_0022ba54",
    STUB_3B897C: "engine_func_003b897c",
    STUB_22B90C: "script_vm_func_0022b90c",
    STUB_22B9D0: "engine_func_0022b9d0",
    STUB_341C74: "engine_func_00341c74",
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
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "003b87a0" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"script_vm_func_003b87a0 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = None
            for address in STUB_NAMES:
                if f"{address:08x}" in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name!r}"
            )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
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


class ScriptVmRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(OBJECT_ADDR, OBJECT_SIZE)
        self.uc.mem_map(STATUS_ADDR, STATUS_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
        self.uc.mem_map(PROBE_ADDR, PROBE_SIZE)
        self.uc.mem_map(SCRATCH_ADDR, SCRATCH_SIZE)
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

    # ------------------------------------------------------------------ stubs
    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _in_page(self, address: int, base: int, size: int) -> bool:
        return base <= address < base + size

    def _write_u32(self, address: int, value: int) -> None:
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)

        if address == STUB_276718:
            self._log(address, r0)
            if r0 == PROBE_ADDR:
                self._write_u32(r0 + 0x388, 0xC0DE0000)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("probe_ret", 1) & 0xFFFFFFFF)
        elif address == STUB_29C660:
            self._log(address, r0, r1, r2)
            base = TABLE_ADDR + TABLE_RECORD_BASE + (r0 * 20)
            self._write_u32(base + 8, r1)
            self._write_u32(base + 4, 0)
            self.uc.mem_write(base + 0x10, bytes([1]))
            self._write_u32(base + 0xC, r2)
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_297128:
            self._log(address)
            count = self.uc.mem_read(SCRATCH_ADDR, 1)[0]
            self.uc.mem_write(SCRATCH_ADDR, bytes([(count + 1) & 0xFF]))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_22BA54:
            self._log(address, r0)
            self._write_u32(SCRATCH_ADDR + 0x40, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                (0x7A540000 | (r0 & 0xFFFF)) & 0xFFFFFFFF,
            )
        elif address == STUB_3B897C:
            self._log(address, r0)
            if self._in_page(r0, OBJECT_ADDR, OBJECT_SIZE):
                self._write_u32(r0 + OFF_SUB_WRITE_E04, 0x5B5B0001)
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_22B90C:
            self._log(address, r0)
            if self._in_page(r0, OBJECT_ADDR, OBJECT_SIZE):
                self._write_u32(r0 + OFF_FRAME_WRITE_E08, 0x5B5B0002)
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_22B9D0:
            self._log(address, r0, r1)
            if self._in_page(r1, OBJECT_ADDR, OBJECT_SIZE):
                self._write_u32(r1, 0x3F800000)
                self._write_u32(r1 + 4, 0x40000000)
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_341C74:
            self._log(address, r0)
            if self._in_page(r0, OBJECT_ADDR, OBJECT_SIZE):
                self._write_u32(r0 + OFF_TAIL_WRITE_E0C, 0x5B5B0003)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("tail_ret", 0x341C74) & 0xFFFFFFFF
            )
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
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
        self.case = case

        self.uc.mem_write(FUNC_ADDR, b"\x00" * FUNC_SIZE)
        self.uc.mem_write(FUNC_ADDR, code)

        object_page = bytearray(OBJECT_SIZE)
        struct.pack_into("<I", object_page, OFF_FLAGS20, case.get("flags", 0) & 0xFFFFFFFF)
        struct.pack_into("<I", object_page, OFF_CODE28, SENTINEL_CODE28)
        struct.pack_into("<I", object_page, OFF_CODE2C, SENTINEL_CODE2C)
        struct.pack_into("<I", object_page, OFF_RESULT_D60, SENTINEL_D60)
        struct.pack_into("<I", object_page, OFF_OUT58, SENTINEL_OUT0)
        struct.pack_into("<I", object_page, OFF_OUT58 + 4, SENTINEL_OUT4)
        struct.pack_into("<I", object_page, OFF_UPDATE9C, 0x9C9C009C)
        object_page[OFF_TAIL_FLAG_E58] = case.get("tail_flag", 0) & 0xFF
        struct.pack_into(
            "<I", object_page, OFF_TAIL_OBJECT_E5C, case.get("tail_ptr", 0) & 0xFFFFFFFF
        )
        struct.pack_into("<I", object_page, OFF_SUB_WRITE_E04, 0xE0E0E004)
        struct.pack_into("<I", object_page, OFF_FRAME_WRITE_E08, 0xE0E0E008)
        struct.pack_into("<I", object_page, OFF_TAIL_WRITE_E0C, 0xE0E0E00C)
        struct.pack_into(
            "<I", object_page, PROBE_SLOT, case.get("probe_ptr", 0) & 0xFFFFFFFF
        )
        self.uc.mem_write(OBJECT_ADDR, bytes(object_page))

        status_page = bytearray(STATUS_SIZE)
        struct.pack_into("<H", status_page, STATUS_WORD78, case.get("word78", 0) & 0xFFFF)
        struct.pack_into("<H", status_page, STATUS_WORD7A, case.get("word7a", 0) & 0xFFFF)
        status_page[0x10] = 0x5C
        self.uc.mem_write(STATUS_ADDR, bytes(status_page))

        self.uc.mem_write(TABLE_ADDR, b"\x00" * TABLE_SIZE)
        self.uc.mem_write(PROBE_ADDR, b"\x00" * PROBE_SIZE)
        self.uc.mem_write(SCRATCH_ADDR, b"\x00" * SCRATCH_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJECT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            allowed = (
                self._in_page(address, STACK_ADDR, STACK_SIZE)
                or self._in_page(address, OBJECT_ADDR, OBJECT_SIZE)
                or self._in_page(address, STATUS_ADDR, STATUS_SIZE)
                or self._in_page(address, TABLE_ADDR, TABLE_SIZE)
                or self._in_page(address, PROBE_ADDR, PROBE_SIZE)
                or self._in_page(address, SCRATCH_ADDR, SCRATCH_SIZE)
            )
            if not allowed:
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
                "object": bytes(self.uc.mem_read(OBJECT_ADDR, OBJECT_SIZE)),
                "status": bytes(self.uc.mem_read(STATUS_ADDR, STATUS_SIZE)),
                "table": bytes(self.uc.mem_read(TABLE_ADDR, TABLE_SIZE)),
                "probe": bytes(self.uc.mem_read(PROBE_ADDR, PROBE_SIZE)),
                "scratch": bytes(self.uc.mem_read(SCRATCH_ADDR, SCRATCH_SIZE)),
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
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "word78": 0,
        "word7a": 0,
        "probe_ptr": 0,
        "probe_ret": 0,
        "flags": 0,
        "tail_flag": 0,
        "tail_ptr": 0,
        "tail_ret": 0x341C74,
    }
    case.update(overrides)
    return case


FIRST_MASK_BITS = (
    0x00000010,
    0x00200000,
    0x00040000,
    0x00800000,
    0x04000000,
    0x01000000,
    0x02000000,
    0x08000000,
    0x20000000,
)

SECOND_MASK_BITS = (
    0x00800000,
    0x01000000,
    0x02000000,
    0x08000000,
    0x00100000,
    0x00080000,
    0x00200000,
    0x00040000,
    0x04000000,
    0x20000000,
)


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- global pending status words (0x7A checked before 0x78)
    cases.append(base_case("no pending words", probe_ptr=PROBE_ADDR, probe_ret=0,
                           flags=0))
    cases.append(base_case("word 0x7A pending", word7a=1))
    cases.append(base_case("word 0x7A maximum", word7a=0xFFFF))
    cases.append(base_case("word 0x78 pending", word78=1))
    cases.append(base_case("word 0x78 maximum", word78=0xFFFF))
    cases.append(base_case("both words pending", word7a=1, word78=1))
    cases.append(base_case("both words maximum", word7a=0xFFFF, word78=0xFFFF))

    # --- probe of *(u32*)0x00433158 through 0x00276718
    cases.append(base_case("probe null pointer, zero result", probe_ptr=0,
                           probe_ret=0, flags=0))
    cases.append(base_case("probe null pointer, non-zero result", probe_ptr=0,
                           probe_ret=1, flags=0))
    cases.append(base_case("probe valid pointer, zero result", probe_ptr=PROBE_ADDR,
                           probe_ret=0, flags=0))
    cases.append(base_case("probe valid pointer, non-zero result",
                           probe_ptr=PROBE_ADDR, probe_ret=1, flags=0))
    cases.append(base_case("probe unrelated pointer, non-zero result",
                           probe_ptr=0x12345678, probe_ret=1, flags=0))
    cases.append(base_case("probe non-zero result with pending 0x7A",
                           probe_ptr=PROBE_ADDR, probe_ret=1, word7a=1))

    # --- first flag priority: 0x00400000 short circuit
    cases.append(base_case("flag 0x00400000", probe_ptr=PROBE_ADDR, flags=0x00400000))
    cases.append(base_case("flag 0x00400000 with bit 0x10",
                           probe_ptr=PROBE_ADDR, flags=0x00400000 | 0x10))
    cases.append(base_case("flag 0x00400000 with bit 0x100",
                           probe_ptr=PROBE_ADDR, flags=0x00400000 | 0x100))
    cases.append(base_case("all flags set", probe_ptr=PROBE_ADDR,
                           flags=0xFFFFFFFF))

    # --- every first-mask bit, with and without the 0x00000100 suppressor
    for bit in FIRST_MASK_BITS:
        cases.append(base_case(f"first mask bit {bit:#010x}",
                               probe_ptr=PROBE_ADDR, flags=bit))
        cases.append(base_case(f"first mask bit {bit:#010x} + 0x100",
                               probe_ptr=PROBE_ADDR, flags=bit | 0x00000100))

    # --- local-update block: 0x00002000 / 0x00000040
    cases.append(base_case("local update, neither flag",
                           probe_ptr=PROBE_ADDR, flags=0))
    cases.append(base_case("local update, 0x2000 only",
                           probe_ptr=PROBE_ADDR, flags=0x00002000))
    cases.append(base_case("local update, 0x40 only",
                           probe_ptr=PROBE_ADDR, flags=0x00000040))
    cases.append(base_case("local update, 0x2000 and 0x40",
                           probe_ptr=PROBE_ADDR, flags=0x00002000 | 0x40))
    cases.append(base_case("local update, 0x100 only",
                           probe_ptr=PROBE_ADDR, flags=0x00000100))
    cases.append(base_case("local update, high bit only",
                           probe_ptr=PROBE_ADDR, flags=0x80000000))
    cases.append(base_case("local update, all but mask bits",
                           probe_ptr=PROBE_ADDR,
                           flags=0x00002000 | 0x40 | 0x100 | 0x80000000))

    # --- every second-mask bit, with and without the 0x00000100 suppressor
    for bit in SECOND_MASK_BITS:
        cases.append(base_case(f"second mask bit {bit:#010x}",
                               probe_ptr=PROBE_ADDR, flags=bit))
        cases.append(base_case(f"second mask bit {bit:#010x} + 0x100",
                               probe_ptr=PROBE_ADDR, flags=bit | 0x00000100))

    # --- complete second-mask union
    second_union = 0
    for bit in SECOND_MASK_BITS:
        second_union |= bit
    cases.append(base_case("second mask union", probe_ptr=PROBE_ADDR,
                           flags=second_union))
    cases.append(base_case("second mask union + 0x100", probe_ptr=PROBE_ADDR,
                           flags=second_union | 0x00000100))

    # --- epilogue tail: byte 0xE58 zero/non-zero, null and valid objects
    cases.append(base_case("tail flag zero", probe_ptr=PROBE_ADDR, flags=0,
                           tail_flag=0, tail_ptr=OBJECT_ADDR,
                           tail_ret=0xDEADBEEF))
    for tail_flag in (0x01, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"tail flag {tail_flag:#04x} valid object",
                               probe_ptr=PROBE_ADDR, flags=0,
                               tail_flag=tail_flag, tail_ptr=OBJECT_ADDR,
                               tail_ret=0xABCD0000 | tail_flag))
        cases.append(base_case(f"tail flag {tail_flag:#04x} null object",
                               probe_ptr=PROBE_ADDR, flags=0,
                               tail_flag=tail_flag, tail_ptr=0,
                               tail_ret=0xFFFFFFFF))
    cases.append(base_case("pending word and tail call", probe_ptr=PROBE_ADDR,
                           word7a=1, tail_flag=1, tail_ptr=OBJECT_ADDR,
                           tail_ret=0x01020304))
    cases.append(base_case("probe short circuit and tail call",
                           probe_ptr=PROBE_ADDR, probe_ret=1, tail_flag=1,
                           tail_ptr=OBJECT_ADDR, tail_ret=0x05060708))
    cases.append(base_case("0x400000 and tail call", probe_ptr=PROBE_ADDR,
                           flags=0x00400000, tail_flag=1, tail_ptr=OBJECT_ADDR,
                           tail_ret=0x090A0B0C))
    cases.append(base_case("0x2000 path and tail call", probe_ptr=PROBE_ADDR,
                           flags=0x00002000, tail_flag=1, tail_ptr=OBJECT_ADDR,
                           tail_ret=0x0D0E0F10))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = ScriptVmRunner().run(orig_code, case)
        cand = ScriptVmRunner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
    return passed


def main() -> None:
    print("Testing script_vm_func_003b87a0 (0x003B87A0)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)
    print(f"  [PASS] {passed}/{len(cases)} differential cases")

    print("Negative controls:")
    for name, old, new in (
        ("word7a_offset", "constexpr u32 kStatusWord7A = kStatusBase + 0x7Au;",
         "constexpr u32 kStatusWord7A = kStatusBase + 0x76u;"),
        ("code13", "constexpr u32 kCode13 = 13;",
         "constexpr u32 kCode13 = 11;"),
        ("code6", "constexpr u32 kCode6 = 6;",
         "constexpr u32 kCode6 = 7;"),
        ("first_bit", "constexpr u32 kBit00000010 = 0x00000010u;",
         "constexpr u32 kBit00000010 = 0x00000020u;"),
        ("second_bit", "constexpr u32 kBit00080000 = 0x00080000u;",
         "constexpr u32 kBit00080000 = 0x00080010u;"),
        ("local_bit", "constexpr u32 kBit00002000 = 0x00002000u;",
         "constexpr u32 kBit00002000 = 0x00001000u;"),
        ("callback_bit", "constexpr u32 kBit00000040 = 0x00000040u;",
         "constexpr u32 kBit00000040 = 0x00000080u;"),
        ("status_value30", "constexpr u32 kStatusValue30 = 30;",
         "constexpr u32 kStatusValue30 = 31;"),
        ("status_slot1", "constexpr u32 kStatusSlot1 = 1;",
         "constexpr u32 kStatusSlot1 = 2;"),
        ("result_offset", "constexpr u32 kUpdateResultD60 = 0xD60u;",
         "constexpr u32 kUpdateResultD60 = 0xD64u;"),
        ("tail_flag_offset", "constexpr u32 kTailFlagE58 = 0xE58u;",
         "constexpr u32 kTailFlagE58 = 0xE54u;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = ScriptVmRunner().run(orig_code, case)
            bad = ScriptVmRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
