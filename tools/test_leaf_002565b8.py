#!/usr/bin/env python3
"""Differential test for script_vm_func_002565b8 (0x002565b8) using Unicorn ARM.

Compiles src/engine/leaf_batch33_c.cpp, extracts the script_vm_func_002565b8
body, resolves its direct calls to deterministic stubs at the pinned original
addresses, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * continuation PC, final SP and the restored callee-saved r4-r11;
  * the ordered call log: every 0x002B66EC fetch (six per accepted record) and
    every 0x002A89E4 indexed fetch with its signed argument;
  * the six shared-record pages, the 256 indexed record pages, the list table,
    the zero page (used for null helper results) and the stack outside the dead
    push frame, byte for byte;
  * every emulated write outside the private stack and those fixture pages.

The original has no defined return value; its final r0 is an incidental
register and no recovered caller consumes it.  The test therefore records r0
for diagnostics but does not use it as an equality gate.

Coverage:
  * modes 0, 1, 2, 3 and everything else (4, 0xFF, 0x80000000, 0xFFFFFFFF);
  * every first-pass gate: mask bit 1, bit 0x400, the `1 << (bit & 0xFF)` bit,
    each fetched record distinct, and mask-bit indices 0, 1, 31, 32, 255, 256;
  * signed product/divide boundaries: top/limit 0, +/-1, 0x7FFF, 0x8000,
    scales 0, +/-1, 99, 100, 101, 0x7FFFFFFF, 0x80000000, and products that
    wrap modulo 2^32;
  * every saturation edge: amount <= 0, value <= 0, value == limit,
    value > limit (including negative limits below the floor of 1);
  * every second-pass gate: flags bits 2, 0x400, 4, the shift bit, unrelated
    high flags, negative list bytes (-1, -2, -128), category 127, counted
    lengths -1/0/1/2/3/24/100, the three fixed entries, two list bases
    (including null) and null 0x002B66EC / 0x002A89E4 results;
  * negative controls mutate the wide reject bit, the second reject bit, the
    divisor, the fixed count, both list offsets, the shift-count boundary and
    the negative amount clamp; each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch33_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_002565b8"

FUNC_ADDR = 0x002565B8
FUNC_SIZE = 408

IMAGE_ADDR = 0x001F0000
IMAGE_SIZE = 0x00200000      # covers the function and the four stub addresses
ZERO_SIZE = 0x00010000       # address 0, for null helper results
RECORD_ADDR = 0x00700000
RECORD_SIZE = 0x00001000     # six 0x100-byte shared records
CAT_ADDR = 0x00710000
CAT_SIZE = 0x00020000        # 256 records, 0x200 bytes apart
TABLE_ADDR = 0x00730000
TABLE_SIZE = 0x00010000      # list base + 0x90F0 / +0x9108
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Direct-call stubs at the pinned original addresses.
STUB_2B66EC = 0x002B66EC
STUB_2A89E4 = 0x002A89E4
STUB_2A8A08 = 0x002A8A08
STUB_2A8A1C = 0x002A8A1C

STUB_NAMES = {
    STUB_2B66EC: "script_vm_func_002b66ec",
    STUB_2A89E4: "camp_func_002a89e4",
    STUB_2A8A08: "camp_func_002a8a08",
    STUB_2A8A1C: "camp_func_002a8a1c",
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

# ARM-visible field offsets (the test deliberately knows no wider structure).
SHARED_MASK_OFFSET = 0x72
RECORD_FLAGS_OFFSET = 0x44
RECORD_LIMIT_OFFSET = 0x0E
RECORD_TOP_OFFSET = 0x1C
RECORD_VALUE_OFFSET = 0x2A
COUNTED_LIST_OFFSET = 0x90F0
FIXED_LIST_OFFSET = 0x9108
SHARED_RECORD_STRIDE = 0x100
CATEGORY_STRIDE = 0x200
SHARED_CALL_COUNT = 6
DEAD_FRAME_SIZE = 0x40


def _pattern(size: int, seed: int) -> bytes:
    block = bytes((index * 7 + seed) & 0xFF for index in range(256))
    return (block * ((size + 255) // 256))[:size]


def s16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def u16(value: int) -> int:
    return value & 0xFFFF


# --------------------------------------------------------------------- candidate
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    functions = extract_elf_functions_detailed(obj_file)
    candidate = functions.get("script_vm_func_002565b8")
    if candidate is None:
        raise RuntimeError(
            "script_vm_func_002565b8 not found in object: "
            + ", ".join(sorted(functions))
        )

    code_raw, relocations = candidate
    code = bytearray(code_raw)
    for rel in relocations:
        if rel.relocation_type in (1, 28, 29):
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
            condition = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset,
                condition | (displacement & 0x00FFFFFF),
            )
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code)


def compile_variant(src_file: Path, obj_file: Path) -> bytes:
    result = compile_tu_armv6k(src_file, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed for {src_file}: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return compile_variant(SOURCE, OUT_DIR / "leaf_batch33_c.o")


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_source = OUT_DIR / f"mutant_{name}.cpp"
    mutant_source.write_text(text.replace(old, new), encoding="utf-8")
    return compile_variant(mutant_source, OUT_DIR / f"mutant_{name}.o")


# --------------------------------------------------------------------- fixtures
def build_shared_records(case: dict) -> bytes:
    page = bytearray(_pattern(RECORD_SIZE, 0x51))
    masks = case["shared_masks"]
    tops = case["shared_tops"]
    values = case["shared_values"]
    for index in range(SHARED_CALL_COUNT):
        base = index * SHARED_RECORD_STRIDE
        struct.pack_into("<H", page, base + SHARED_MASK_OFFSET, u16(masks[index]))
        struct.pack_into("<h", page, base + RECORD_TOP_OFFSET, s16(tops[index]))
        struct.pack_into("<h", page, base + RECORD_VALUE_OFFSET, s16(values[index]))
        # Filler words that must stay untouched by the routine.
        struct.pack_into("<I", page, base + 0x40, 0xA5A50000 | index)
        struct.pack_into("<I", page, base + 0x90, 0x5A5A0000 | index)
    return bytes(page)


def build_categories(case: dict) -> bytes:
    page = bytearray(_pattern(CAT_SIZE, 0x33))
    table = case["categories"]
    for index in range(256):
        base = index * CATEGORY_STRIDE
        fields = table.get(index)
        if fields is None:
            flags, limit, value = 0, 0x7FFF, 0x7FFF
        else:
            flags = fields.get("flags", 0)
            limit = fields.get("limit", 0x7FFF)
            value = fields.get("value", 0x7FFF)
        struct.pack_into("<H", page, base + RECORD_FLAGS_OFFSET, u16(flags))
        struct.pack_into("<h", page, base + RECORD_LIMIT_OFFSET, s16(limit))
        struct.pack_into("<h", page, base + RECORD_VALUE_OFFSET, s16(value))
        struct.pack_into("<I", page, base + 0x40, 0x3C3C0000 | index)
    return bytes(page)


def build_table(case: dict) -> bytes:
    page = bytearray(_pattern(TABLE_SIZE, 0x77))
    counted = case["list_bytes"]
    fixed = case["fixed_bytes"]
    if len(counted) > TABLE_SIZE - COUNTED_LIST_OFFSET:
        raise ValueError("counted list fixture is too long")
    page[COUNTED_LIST_OFFSET:COUNTED_LIST_OFFSET + len(counted)] = counted
    if len(fixed) > 3:
        raise ValueError("fixed list fixture must hold at most three bytes")
    page[FIXED_LIST_OFFSET:FIXED_LIST_OFFSET + len(fixed)] = fixed
    return bytes(page)


def build_zero_page(case: dict) -> bytes:
    page = bytearray(ZERO_SIZE)
    for offset, value in case["zero_halfwords"].items():
        struct.pack_into("<H", page, offset, u16(value))
    for offset, value in case["zero_words"].items():
        struct.pack_into("<I", page, offset, value & 0xFFFFFFFF)
    return bytes(page)


# ----------------------------------------------------------------------- runner
class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0, ZERO_SIZE)
        self.uc.mem_map(IMAGE_ADDR, IMAGE_SIZE)
        self.uc.mem_map(RECORD_ADDR, RECORD_SIZE)
        self.uc.mem_map(CAT_ADDR, CAT_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
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
        self.shared_calls = 0
        self.case: dict = {}

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        if address == STUB_2B66EC:
            self.call_log.append(("script_vm_func_002b66ec",))
            index = self.shared_calls
            self.shared_calls += 1
            if index >= SHARED_CALL_COUNT:
                raise AssertionError("more than six shared-record fetches")
            if index in self.case["shared_null"]:
                pointer = 0
            else:
                pointer = RECORD_ADDR + index * SHARED_RECORD_STRIDE
            uc.reg_write(arm.UC_ARM_REG_R0, pointer & 0xFFFFFFFF)
        elif address == STUB_2A89E4:
            index = uc.reg_read(arm.UC_ARM_REG_R0)
            self.call_log.append(("camp_func_002a89e4", index))
            if index in self.case["category_null"]:
                pointer = 0
            else:
                pointer = CAT_ADDR + (index & 0xFF) * CATEGORY_STRIDE
            uc.reg_write(arm.UC_ARM_REG_R0, pointer & 0xFFFFFFFF)
        elif address == STUB_2A8A08:
            self.call_log.append(("camp_func_002a8a08",))
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case["list_base"] & 0xFFFFFFFF
            )
        elif address == STUB_2A8A1C:
            self.call_log.append(("camp_func_002a8a1c",))
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case["list_count"] & 0xFFFFFFFF
            )
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        uc = self.uc
        self.case = case
        self.call_log = []
        self.writes = []
        self.shared_calls = 0

        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(0, build_zero_page(case))
        uc.mem_write(RECORD_ADDR, build_shared_records(case))
        uc.mem_write(CAT_ADDR, build_categories(case))
        uc.mem_write(TABLE_ADDR, build_table(case))
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []
        uc.ctl_flush_tb()

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, case["mode"] & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R1, case["bit"] & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R2, case["scale"] & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            uc.reg_write(CALLEE_SAVED[name], value)

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error
        finally:
            uc.ctl_flush_tb()

        sp = uc.reg_read(arm.UC_ARM_REG_SP)
        frame_low = ENTRY_SP - DEAD_FRAME_SIZE
        stack_below = bytes(uc.mem_read(STACK_ADDR, frame_low - STACK_ADDR))
        stack_above = bytes(
            uc.mem_read(ENTRY_SP, STACK_ADDR + STACK_SIZE - ENTRY_SP)
        )

        fixtures = (
            (ZERO_SIZE, 0),
            (RECORD_SIZE, RECORD_ADDR),
            (CAT_SIZE, CAT_ADDR),
            (TABLE_SIZE, TABLE_ADDR),
        )
        unexpected_writes = []
        for address, write_size in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_fixture = any(
                base <= address < base + size for size, base in fixtures
            )
            if not (in_stack or in_fixture):
                unexpected_writes.append((address, write_size))

        return {
            "r0": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": sp,
            "callee_saved": {
                name: uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "zero": bytes(uc.mem_read(0, ZERO_SIZE)),
            "records": bytes(uc.mem_read(RECORD_ADDR, RECORD_SIZE)),
            "categories": bytes(uc.mem_read(CAT_ADDR, CAT_SIZE)),
            "table": bytes(uc.mem_read(TABLE_ADDR, TABLE_SIZE)),
            "stack_below": stack_below,
            "stack_above": stack_above,
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list:
    problems = []
    for key in (
        "pc",
        "sp",
        "callee_saved",
        "call_log",
        "zero",
        "records",
        "categories",
        "table",
        "stack_below",
        "stack_above",
        "unexpected_writes",
    ):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    return problems


# ------------------------------------------------------------------------ cases
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "mode": 0,
        "bit": 1,
        "scale": 100,
        "shared_masks": [0, 0, 0, 0, 0, 0],
        "shared_tops": [1000, 1000, 1000, 1000, 1000, 1000],
        "shared_values": [1000, 1000, 1000, 1000, 1000, 1000],
        "shared_null": set(),
        "category_null": set(),
        "categories": {},
        "list_bytes": bytes(0x80),
        "fixed_bytes": b"\x00\x00\x00",
        "list_base": TABLE_ADDR,
        "list_count": 0,
        "zero_halfwords": {},
        "zero_words": {},
    }
    case.update(overrides)
    return case


def accepted_shared_case(name: str, **overrides) -> dict:
    """A case whose first pass passes all gates and stores into call 6."""
    defaults = {
        "shared_masks": [0, 0, 2, 0, 0, 0],
        "shared_tops": [500, 500, 500, 500, 500, 1000],
        "shared_values": [900, 900, 900, 900, 900, 1000],
        "list_bytes": bytes(0x18),
        "list_count": 0,
    }
    defaults.update(overrides)
    return base_case(name, **defaults)


def make_cases() -> list:
    cases: list = []

    # --- mode dispatch ------------------------------------------------------
    cases.append(base_case("mode 4: no pass runs", mode=4, bit=1))
    cases.append(base_case("mode 0xffffffff: no pass runs", mode=0xFFFFFFFF))
    cases.append(base_case("mode 0x80000000: no pass runs", mode=0x80000000))
    cases.append(base_case("mode 0x100: no pass runs", mode=0x100))
    cases.append(base_case("mode 1: only the counted list", mode=1, list_count=0))
    cases.append(
        base_case(
            "mode 2: first pass plus fixed list", mode=2,
            shared_masks=[0, 0, 2, 0, 0, 0], shared_tops=[100] * 6,
            shared_values=[100] * 6, fixed_bytes=b"\x00\x00\x00",
        )
    )
    cases.append(
        base_case(
            "mode 3: first pass plus fixed list", mode=3,
            shared_masks=[0, 0, 2, 0, 0, 0], shared_tops=[100] * 6,
            shared_values=[100] * 6, fixed_bytes=b"\x00\x00\x00",
        )
    )

    # --- first-pass gates: one, two, three and six fetches ------------------
    cases.append(
        base_case(
            "first mask bit 1 rejects after one fetch", mode=0,
            shared_masks=[2, 0, 2, 0, 0, 0], list_count=0,
        )
    )
    cases.append(
        base_case(
            "second mask bit 0x400 rejects after two fetches", mode=0,
            shared_masks=[0, 0x400, 2, 0, 0, 0], list_count=0,
        )
    )
    cases.append(
        base_case(
            "third mask lacks the bit after three fetches", mode=0,
            shared_masks=[0, 0, 0, 0, 0, 0], bit=1, scale=100,
            list_count=0,
        )
    )
    cases.append(
        base_case(
            "mask bits 1 and 0x400 together still reject", mode=0,
            shared_masks=[3, 0x402, 2, 0, 0, 0], list_count=0,
        )
    )
    cases.append(
        base_case(
            "unrelated mask bits pass the gates", mode=0,
            shared_masks=[0x8000, 0x0080, 0x0002, 0, 0, 0], bit=1,
            list_count=0,
        )
    )

    # --- first-pass clamping ------------------------------------------------
    cases.append(accepted_shared_case("first pass plain decrement"))
    cases.append(
        accepted_shared_case(
            "first pass amount clamps from zero",
            shared_tops=[0] * 6, shared_values=[50] * 6,
        )
    )
    cases.append(
        accepted_shared_case(
            "first pass negative top clamps amount",
            shared_tops=[-500] * 6, shared_values=[50] * 6,
        )
    )
    cases.append(
        accepted_shared_case(
            "first pass current reaches zero -> 1",
            shared_tops=[1000] * 6, shared_values=[1] * 6,
        )
    )
    cases.append(
        accepted_shared_case(
            "first pass current negative -> 1",
            shared_tops=[1000] * 6, shared_values=[-32000] * 6,
        )
    )
    cases.append(
        accepted_shared_case(
            "first pass value equals upper bound",
            shared_tops=[500] * 6, shared_values=[600] * 6,
        )
    )
    cases.append(
        accepted_shared_case(
            "first pass value above positive bound",
            shared_tops=[100] * 6, shared_values=[600] * 6,
        )
    )
    cases.append(
        accepted_shared_case(
            "first pass negative upper bound stores it",
            shared_tops=[-5] * 6, shared_values=[100] * 6,
        )
    )
    cases.append(
        accepted_shared_case(
            "first pass zero upper bound stores it",
            shared_tops=[0] * 6, shared_values=[100] * 6,
        )
    )
    cases.append(
        accepted_shared_case(
            "first pass upper bound one",
            shared_tops=[1] * 6, shared_values=[100] * 6,
        )
    )
    for scale, label in (
        (0, "zero"),
        (-1, "-1"),
        (-100, "-100"),
        (1, "1"),
        (99, "99"),
        (101, "101"),
        (0x7FFFFFFF, "0x7fffffff"),
        (0x80000000, "0x80000000"),
    ):
        cases.append(
            accepted_shared_case(
                f"first pass scale {label} distinct records",
                shared_tops=[0, 0, 0, 32767, 0, 32767],
                shared_values=[0, 0, 0, 0, 32767, 0],
                scale=scale,
            )
        )
    cases.append(
        accepted_shared_case(
            "first pass negative top and current",
            shared_tops=[0, 0, 0, -32768, 0, 32767],
            shared_values=[0, 0, 0, 0, -32768, 0],
        )
    )
    cases.append(
        accepted_shared_case(
            "first pass wrapped product and negative bound",
            shared_tops=[0, 0, 0, 32767, 0, -32768],
            shared_values=[0, 0, 0, 0, -32768, 0],
            scale=0x7FFFFFFF,
        )
    )
    cases.append(
        accepted_shared_case(
            "first pass wrapped product and zero bound",
            shared_tops=[0, 0, 0, -32768, 0, 0],
            shared_values=[0, 0, 0, 0, 32767, 0],
            scale=0x80000000,
        )
    )
    cases.append(
        accepted_shared_case(
            "first pass product wraps to a positive quotient",
            shared_tops=[0, 0, 0, 32767, 0, 100],
            shared_values=[0, 0, 0, 0, 32767, 0],
            scale=0x7FFFFFFF,
        )
    )

    # --- second-pass flags --------------------------------------------------
    # The reject gates are bits 1 (2), 10 (0x400) and 2 (4).  Bit index 3
    # selects mask 8, which is disjoint from all three, so an accepted record
    # can be produced and each reject gate tested on its own.
    cases.append(
        base_case(
            "counted list flags bit 2 rejects", mode=1, bit=3, list_count=1,
            list_bytes=b"\x00",
            categories={0: {"flags": 0x000A, "limit": 10, "value": 10}},
        )
    )
    cases.append(
        base_case(
            "counted list flags bit 0x400 rejects", mode=1, bit=3,
            list_count=1, list_bytes=b"\x00",
            categories={0: {"flags": 0x0408, "limit": 10, "value": 10}},
        )
    )
    cases.append(
        base_case(
            "counted list flags bit 4 rejects", mode=1, bit=3, list_count=1,
            list_bytes=b"\x00",
            categories={0: {"flags": 0x000C, "limit": 10, "value": 10}},
        )
    )
    cases.append(
        base_case(
            "counted list flags lack the shift bit", mode=1, bit=3,
            list_count=1, list_bytes=b"\x00",
            categories={0: {"flags": 0, "limit": 10, "value": 10}},
        )
    )
    cases.append(
        base_case(
            "counted list unrelated high flags still store", mode=1, bit=3,
            list_count=1, list_bytes=b"\x00",
            categories={0: {"flags": 0x8008, "limit": 10, "value": 10}},
        )
    )

    # --- second-pass list index handling ------------------------------------
    cases.append(
        base_case(
            "negative list bytes are skipped", mode=1, bit=3, list_count=4,
            list_bytes=b"\xff\xfe\x80\x00",
            categories={0: {"flags": 8, "limit": 10, "value": 10}},
        )
    )
    cases.append(
        base_case(
            "category 127 is in range", mode=1, bit=3, list_count=1,
            list_bytes=b"\x7f",
            categories={127: {"flags": 8, "limit": 10, "value": 10}},
        )
    )
    for count in (-1, 0, 1, 2, 3, 24, 100):
        payload = bytes(index & 0x7F for index in range(max(count, 0)))
        cases.append(
            base_case(
                f"counted length {count}", mode=1, bit=3,
                list_count=count, list_bytes=payload,
                categories={
                    index: {"flags": 8, "limit": 0x7FFF, "value": 0x7FFF}
                    for index in range(100)
                },
            )
        )

    # --- second-pass clamping ----------------------------------------------
    def category_case(name: str, **category_fields) -> dict:
        return base_case(
            name, mode=1, bit=3, list_count=1, list_bytes=b"\x00",
            categories={0: category_fields},
        )

    cases.append(category_case("second pass plain decrement", flags=8,
                               limit=1000, value=1000))
    cases.append(category_case("second pass amount zero clamps", flags=8,
                               limit=0, value=50))
    cases.append(category_case("second pass negative limit clamps amount",
                               flags=8, limit=-500, value=50))
    cases.append(category_case("second pass current reaches zero", flags=8,
                               limit=1000, value=1))
    cases.append(category_case("second pass current negative", flags=8,
                               limit=1000, value=-32000))
    cases.append(category_case("second pass value equals limit", flags=8,
                               limit=500, value=600))
    cases.append(category_case("second pass value above limit", flags=8,
                               limit=100, value=600))
    cases.append(category_case("second pass negative limit stores it", flags=8,
                               limit=-5, value=100))
    cases.append(category_case("second pass zero limit stores it", flags=8,
                               limit=0, value=100))
    cases.append(category_case("second pass limit one", flags=8,
                               limit=1, value=100))
    for scale, label in (
        (0, "zero"), (-1, "-1"), (-100, "-100"), (1, "1"),
        (99, "99"), (101, "101"), (0x7FFFFFFF, "0x7fffffff"),
        (0x80000000, "0x80000000"),
    ):
        cases.append(
            base_case(
                f"second pass scale {label}", mode=1, bit=3, list_count=3,
                list_bytes=b"\x00\x01\x02", scale=scale,
                categories={
                    0: {"flags": 8, "limit": 32767, "value": 32767},
                    1: {"flags": 8, "limit": -32768, "value": -1},
                    2: {"flags": 8, "limit": 1000, "value": 500},
                },
            )
        )

    # --- fixed list (modes 2 and 3) ----------------------------------------
    cases.append(
        base_case(
            "fixed list processes three entries", mode=2, bit=3,
            fixed_bytes=b"\x01\x02\x03",
            categories={
                1: {"flags": 8, "limit": 100, "value": 100},
                2: {"flags": 8, "limit": 200, "value": 300},
                3: {"flags": 8, "limit": -7, "value": 50},
            },
        )
    )
    cases.append(
        base_case(
            "fixed list skips negative and rejected entries", mode=3, bit=3,
            fixed_bytes=b"\xff\x00\x02",
            categories={
                0: {"flags": 0x0408, "limit": 10, "value": 10},
                2: {"flags": 8, "limit": 10, "value": 10},
            },
        )
    )

    # --- mask-bit index boundaries -----------------------------------------
    for bit, label in (
        (0, "0"), (1, "1"), (15, "15"), (16, "16"), (30, "30"),
        (31, "31"), (32, "32"), (33, "33"), (255, "255"), (256, "256"),
        (0xFFFFFFFF, "0xffffffff"),
    ):
        mask = 1 << (bit & 0xFF) if (bit & 0xFF) < 32 else 0
        cases.append(
            base_case(
                f"mask bit index {label}", mode=0, bit=bit, scale=100,
                shared_masks=[0, 0, mask, 0, 0, 0],
                shared_tops=[1000] * 6, shared_values=[1000] * 6,
                list_count=0,
            )
        )

    # --- null helper results ------------------------------------------------
    cases.append(
        base_case(
            "null shared record with a mapped zero page", mode=0, bit=1,
            shared_null=set(range(SHARED_CALL_COUNT)),
            zero_halfwords={
                SHARED_MASK_OFFSET: 2,
                RECORD_TOP_OFFSET: 100,
                RECORD_VALUE_OFFSET: 100,
            },
            list_count=0,
        )
    )
    cases.append(
        base_case(
            "null shared record rejected by its zero-page mask", mode=0, bit=1,
            shared_null=set(range(SHARED_CALL_COUNT)),
            zero_halfwords={SHARED_MASK_OFFSET: 0x400},
            list_count=0,
        )
    )
    cases.append(
        base_case(
            "null indexed record skips the store", mode=1, bit=1,
            list_count=1, list_bytes=b"\x00", category_null={0},
        )
    )
    cases.append(
        base_case(
            "null list base reads the zero-page list", mode=1, bit=3,
            list_base=0, list_count=1,
            categories={0: {"flags": 8, "limit": 10, "value": 10}},
        )
    )

    return cases


# ------------------------------------------------------------------------- main
def run_case_set(orig_code: bytes, cand_code: bytes, cases: list) -> int:
    passed = 0
    r0_mismatches = 0
    for case in cases:
        orig = Runner().run(orig_code, case)
        cand = Runner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        if orig["r0"] != cand["r0"]:
            r0_mismatches += 1
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    print(
        f"  (incidental r0 differs in {r0_mismatches}/{passed} cases; "
        "not an ABI result)"
    )
    return passed


def main() -> None:
    print("Testing script_vm_func_002565b8 (0x002565b8)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("wide_reject_bit", "constexpr u32 kRejectFlagWide = 0x400u;",
         "constexpr u32 kRejectFlagWide = 0x200u;"),
        ("second_reject_bit", "constexpr u32 kRejectFlagTwo = 4u;",
         "constexpr u32 kRejectFlagTwo = 8u;"),
        ("percent_divisor", "constexpr s32 kPercentDivisor = 100;",
         "constexpr s32 kPercentDivisor = 101;"),
        ("fixed_list_count", "constexpr s32 kFixedListCount = 3;",
         "constexpr s32 kFixedListCount = 2;"),
        ("fixed_list_offset", "constexpr u32 kFixedListOffset = 0x9108u;",
         "constexpr u32 kFixedListOffset = 0x9109u;"),
        ("counted_list_offset", "constexpr u32 kCountedListOffset = 0x90F0u;",
         "constexpr u32 kCountedListOffset = 0x90F1u;"),
        ("mask_shift_value", "return shift < 32u ? (1u << shift) : 0u;",
         "return shift < 32u ? (1u << (shift & 0xFEu)) : 0u;"),
        ("amount_zero_clamp", "if (amount <= 0) {\n                        amount = 1;\n                    }\n                    s32 value = current - amount;",
         "if (amount < 0) {\n                        amount = 1;\n                    }\n                    s32 value = current - amount;"),
        ("null_record_gate", "if (record == nullptr) {\n            continue;\n        }",
         "if (record != nullptr) {\n            continue;\n        }"),
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
