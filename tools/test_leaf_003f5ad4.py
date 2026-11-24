#!/usr/bin/env python3
"""Differential test for ui_func_003f5ad4 (0x003f5ad4) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the ui_func_003f5ad4 body,
resolves its four direct calls to deterministic stubs at the pinned target
addresses, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in identical Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC (trap), final SP, and the r4-r11 sentinels;
  * the ordered call log: divmod quotient/remainder, width helper inputs, the
    6-byte descriptor copy, the filter call (source, output, row record,
    descriptor words, stack count) and both allocator slots;
  * the full row page, object page, scratch page, output page, allocator pool
    and 0x0044E918 function-pointer page;
  * every emulated write outside the private stack.

Coverage: zero width (early success), widths below/at/above 0x20, even widths
that select the transposed-tail loop, single-row and multi-row paths, zero-row
divmod-by-zero path, quotient remainders, allocation sizes and boundaries
(capacity exactly equal/lower), scratch and output growth with zero and nonzero
old pointers, allocator failure at each slot, re-reads of +0x00/+0x0C after the
filter call, and both descriptor/state writes.

Negative controls mutate the width bias/mode, output field offsets, the narrow
limit, the single-row dispatch, the transposed size store, the release guard,
the allocation-failure returns, the output requirement and the transposed
destination stride; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_003f5ad4"

FUNC_ADDR = 0x003F5AD4
FUNC_SIZE = 472

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00250000  # to 0x00440000: covers the function and all stubs
SLOT_ADDR = 0x0044E000
SLOT_SIZE = 0x00002000  # covers 0x0044E918 / 0x0044E91C
ROW_ADDR = 0x00700000
ROW_SIZE = 0x00010000
OBJECT_ADDR = 0x00720000
OBJECT_SIZE = 0x00010000
SCRATCH_ADDR = 0x00740000
SCRATCH_SIZE = 0x00010000
OUTPUT_ADDR = 0x00760000
OUTPUT_SIZE = 0x00010000
POOL_ADDR = 0x00780000
POOL_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

SCRATCH_ALT = SCRATCH_ADDR + 0x8000
OUTPUT_ALT = OUTPUT_ADDR + 0x8000

# The helpers live at their pinned addresses so the original's own BL targets
# land on the stubs; the candidate's relocations are rewritten to match.
STUB_2C6C10 = 0x002C6C10
STUB_360270 = 0x00360270
STUB_2BD9EC = 0x002BD9EC
STUB_36014C = 0x0036014C
STUB_ALLOC = 0x002B0000
STUB_FREE = 0x002B0010

STUB_NAMES = {
    STUB_2C6C10: "ui_func_002c6c10",
    STUB_360270: "func_00360270",
    STUB_2BD9EC: "script_vm_func_002bd9ec",
    STUB_36014C: "func_0036014c",
    STUB_ALLOC: "allocator_slot0",
    STUB_FREE: "allocator_slot1",
}

CALL_RELOCATIONS = {
    "002c6c10": STUB_2C6C10,
    "00360270": STUB_360270,
    "002bd9ec": STUB_2BD9EC,
    "0036014c": STUB_36014C,
}

ALLOCATOR_TABLE = 0x0044E918
ALLOC_STRIDE = 0x800

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
        if "003f5ad4" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"ui_func_003f5ad4 not found in {obj_file}: {sorted(funcs)}"
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
        for address_text, address in CALL_RELOCATIONS.items():
            if address_text in rel.symbol_name:
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
def page_pattern(multiplier: int, addend: int) -> bytes:
    return bytes((index * multiplier + addend) & 0xFF
                 for index in range(0x10000))


def build_fixtures(case: dict) -> dict:
    row = bytearray(page_pattern(13, 5))
    scratch = bytearray(page_pattern(29, 7))
    output = bytearray(page_pattern(31, 9))
    obj = bytearray(OBJECT_SIZE)
    pool = bytearray(POOL_SIZE)

    row_count = case["row_count"]
    total = case["total"]
    if row_count:
        stride = total // row_count
        descriptor = case.get("descriptor", (0x0001, 0xFFFE, 0x0002))
        for index in range(row_count):
            base = index * stride
            if base + 0x60 > ROW_SIZE:
                raise AssertionError(f"row fixture overflow at row {index}")
            struct.pack_into("<HHH", row, base + 0x20, *descriptor)

    struct.pack_into("<I", obj, 0x00, case.get("out_ptr", OUTPUT_ADDR) & 0xFFFFFFFF)
    struct.pack_into("<I", obj, 0x04, case.get("out_cap", 0x10000) & 0xFFFFFFFF)
    struct.pack_into("<I", obj, 0x08, 0xDEADBEEF)  # cleared by the routine
    struct.pack_into("<I", obj, 0x0C,
                     case.get("scratch_ptr", SCRATCH_ADDR) & 0xFFFFFFFF)
    struct.pack_into("<I", obj, 0x10,
                     case.get("scratch_cap", 0x10000) & 0xFFFFFFFF)
    struct.pack_into("<I", obj, 0x18, row_count & 0xFFFFFFFF)

    return {
        "row": bytes(row),
        "object": bytes(obj),
        "scratch": bytes(scratch),
        "output": bytes(output),
        "pool": bytes(pool),
    }


# ---------------------------------------------------------------------- helpers
def to_s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def width_helper(value: int, mode: int, rate: int) -> int:
    if mode == 0:
        divisor = to_s32(rate)
        if divisor == 0:
            return 0
        return (int(to_s32(value) / divisor)) & 0xFFFFFFFF
    if mode == 1:
        divisor = to_s32((rate << 1) & 0xFFFFFFFF)
        if divisor == 0:
            return 0
        return (int(to_s32(value) / divisor)) & 0xFFFFFFFF
    if mode == 2:
        shifted = (value << 1) & 0xFFFFFFFF
        remainder = shifted & 0xF
        upper = shifted >> 4
        extra = remainder - 2 if remainder >= 2 else 0
        return (upper * 14 + extra) & 0xFFFFFFFF
    return 0


class Runner:
    """One Unicorn machine with deterministic stubs at the pinned targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(SLOT_ADDR, SLOT_SIZE)
        self.uc.mem_map(ROW_ADDR, ROW_SIZE)
        self.uc.mem_map(OBJECT_ADDR, OBJECT_SIZE)
        self.uc.mem_map(SCRATCH_ADDR, SCRATCH_SIZE)
        self.uc.mem_map(OUTPUT_ADDR, OUTPUT_SIZE)
        self.uc.mem_map(POOL_ADDR, POOL_SIZE)
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
        self.alloc_index = 0

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value & 0xFFFFFFFF))

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2C6C10:
            if r1 == 0:
                quotient, remainder = 0xFFFFFFFF, r0
            else:
                quotient, remainder = divmod(r0, r1)
            self._log(address, r0, r1, quotient, remainder)
            uc.reg_write(arm.UC_ARM_REG_R0, quotient)
            uc.reg_write(arm.UC_ARM_REG_R1, remainder)

        elif address == STUB_360270:
            result = width_helper(r0, r1, r2)
            self._log(address, r0, r1, r2, result)
            uc.reg_write(arm.UC_ARM_REG_R0, result)

        elif address == STUB_2BD9EC:
            word0 = struct.unpack("<I", uc.mem_read(r1, 4))[0]
            word1 = struct.unpack("<H", uc.mem_read(r1 + 4, 2))[0]
            self._log(address, r1, word0, word1)
            uc.mem_write(r0, struct.pack("<IH", word0, word1))

        elif address == STUB_36014C:
            sp = uc.reg_read(arm.UC_ARM_REG_SP)
            count = struct.unpack("<I", uc.mem_read(sp, 4))[0]
            state = struct.unpack("<HHH", uc.mem_read(r3, 6))
            self._log(address, r0, r1, r2, state[0], state[1], state[2], count)

            payload = bytes(uc.mem_read(r0, count * 2)) if count else b""
            values = bytearray()
            for index in range(count):
                low = payload[2 * index]
                high = payload[2 * index + 1]
                value = ((low | (high << 8)) ^ ((index * 0x37) & 0xFFFF))
                values += struct.pack("<H", value)
            if count:
                uc.mem_write(r1, bytes(values))

            new_state = (
                payload[0] if count >= 1 else 0,
                payload[1] if count >= 2 else 0,
                payload[2] if count >= 3 else 0,
            )
            uc.mem_write(r3, struct.pack("<HHH", *new_state))

            if self.case.get("reassign_scratch", False):
                uc.mem_write(OBJECT_ADDR + 0x0C,
                             struct.pack("<I", SCRATCH_ALT))
            if self.case.get("reassign_output", False):
                uc.mem_write(OBJECT_ADDR + 0x00,
                             struct.pack("<I", OUTPUT_ALT))

        elif address == STUB_ALLOC:
            self._log(address, r0)
            self.alloc_index += 1
            if self.alloc_index == self.case.get("alloc_fail_index", 0):
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                uc.reg_write(
                    arm.UC_ARM_REG_R0,
                    POOL_ADDR + ALLOC_STRIDE * (self.alloc_index - 1),
                )

        elif address == STUB_FREE:
            self._log(address, r0)

        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.alloc_index = 0

        fixtures = build_fixtures(case)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(ROW_ADDR, fixtures["row"])
        self.uc.mem_write(OBJECT_ADDR, fixtures["object"])
        self.uc.mem_write(SCRATCH_ADDR, fixtures["scratch"])
        self.uc.mem_write(OUTPUT_ADDR, fixtures["output"])
        self.uc.mem_write(POOL_ADDR, fixtures["pool"])
        self.uc.mem_write(SLOT_ADDR, b"\x00" * SLOT_SIZE)
        self.uc.mem_write(
            ALLOCATOR_TABLE,
            struct.pack("<II", STUB_ALLOC, STUB_FREE),
        )
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJECT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, ROW_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case["total"] & 0xFFFFFFFF)
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
            if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
                continue
            unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "pages": {
                "row": bytes(self.uc.mem_read(ROW_ADDR, ROW_SIZE)),
                "object": bytes(self.uc.mem_read(OBJECT_ADDR, OBJECT_SIZE)),
                "scratch": bytes(self.uc.mem_read(SCRATCH_ADDR, SCRATCH_SIZE)),
                "output": bytes(self.uc.mem_read(OUTPUT_ADDR, OUTPUT_SIZE)),
                "pool": bytes(self.uc.mem_read(POOL_ADDR, POOL_SIZE)),
                "slot": bytes(self.uc.mem_read(SLOT_ADDR, SLOT_SIZE)),
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
    for key, value in orig["pages"].items():
        if value != cand["pages"][key]:
            first = next(
                index
                for index, (left, right) in enumerate(zip(value, cand["pages"][key]))
                if left != right
            )
            problems.append(
                f"page {key} differs first at +0x{first:x}:\n"
                f"    orig={value[first:first + 16]!r}\n"
                f"    cand={cand['pages'][key][first:first + 16]!r}"
            )
    if orig["unexpected_writes"] != cand["unexpected_writes"]:
        problems.append(
            "unexpected writes:\n    orig="
            + repr(orig["unexpected_writes"])
            + "\n    cand="
            + repr(cand["unexpected_writes"])
        )
    return problems


# ------------------------------------------------------------------- case table
def make_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "row_count": 2,
        "q": 0x3E,          # width 42
        "remainder": 0,
        "out_ptr": OUTPUT_ADDR,
        "out_cap": 0x10000,
        "scratch_ptr": SCRATCH_ADDR,
        "scratch_cap": 0x10000,
        "descriptor": (0x0001, 0xFFFE, 0x0002),
        "alloc_fail_index": 0,
    }
    case.update(overrides)
    case["total"] = (case["q"] * case["row_count"] + case["remainder"])
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- width zero exits before touching either buffer
    cases.append(make_case("width zero, one row", row_count=1, q=0x26))
    cases.append(make_case("width zero, three rows", row_count=3, q=0x26,
                           scratch_ptr=0, scratch_cap=0, out_cap=0))

    # --- width boundaries around 0x20 (all real widths are even)
    cases.append(make_case("width 30 below narrow, two rows", row_count=2,
                           q=0x38, scratch_cap=0x100, out_cap=0,
                           out_ptr=0))
    cases.append(make_case("width 32 exactly, two rows", row_count=2, q=0x39,
                           scratch_cap=0x100, out_cap=0, out_ptr=0))
    cases.append(make_case("width 34, two rows, allocates scratch and output",
                           row_count=2, q=0x3A, scratch_ptr=0, scratch_cap=0,
                           out_ptr=0, out_cap=0))
    cases.append(make_case("width 34, one row, allocates output only",
                           row_count=1, q=0x3A, out_ptr=0, out_cap=0,
                           scratch_ptr=0, scratch_cap=0))
    cases.append(make_case("width 30, one row, no transposition", row_count=1,
                           q=0x38, out_ptr=0, out_cap=0))

    # --- transpose tail, several row counts
    cases.append(make_case("width 42, three rows, preallocated",
                           row_count=3, q=0x3E))
    cases.append(make_case("width 70, five rows, allocated",
                           row_count=5, q=0x4E, scratch_ptr=0, scratch_cap=0,
                           out_ptr=0, out_cap=0))
    cases.append(make_case("width 64, one row, preallocated", row_count=1,
                           q=0x4B))
    cases.append(make_case("width 34, two rows, capacity exactly equal",
                           row_count=2, q=0x3A, out_cap=8, scratch_cap=0))

    # --- quotient remainder is dead but logged
    cases.append(make_case("width 42, two rows, division remainder 1",
                           row_count=2, q=0x3E, remainder=1))
    cases.append(make_case("width 42, three rows, division remainder 2",
                           row_count=3, q=0x3E, remainder=2))

    # --- release/reallocate paths
    cases.append(make_case("width 42, three rows, zero old pointers",
                           row_count=3, q=0x3E, scratch_ptr=0, scratch_cap=0,
                           out_ptr=0, out_cap=0))
    cases.append(make_case("width 42, three rows, nonzero undersized pointers",
                           row_count=3, q=0x3E, scratch_cap=0, out_cap=0))
    cases.append(make_case("width 64, two rows, free scratch, keep output",
                           row_count=2, q=0x4B, scratch_ptr=SCRATCH_ADDR + 0x40,
                           scratch_cap=0, out_cap=0x10000))
    cases.append(make_case("width 42, two rows, free output, keep scratch",
                           row_count=2, q=0x3E, out_ptr=OUTPUT_ADDR + 0x40,
                           out_cap=0, scratch_cap=0x10000))

    # --- allocation failures
    cases.append(make_case("scratch allocation fails", row_count=2, q=0x3A,
                           scratch_ptr=0, scratch_cap=0, out_ptr=0, out_cap=0,
                           alloc_fail_index=1))
    cases.append(make_case("scratch allocation fails with old pointer",
                           row_count=3, q=0x3E, scratch_cap=0, out_ptr=0,
                           out_cap=0, alloc_fail_index=1))
    cases.append(make_case("output allocation fails first", row_count=2,
                           q=0x3E, scratch_cap=0x10000, out_ptr=0, out_cap=0,
                           alloc_fail_index=1))
    cases.append(make_case("output allocation fails second", row_count=2,
                           q=0x3A, scratch_ptr=0, scratch_cap=0, out_ptr=0,
                           out_cap=0, alloc_fail_index=2))
    cases.append(make_case("output allocation fails with old pointer",
                           row_count=2, q=0x3E, scratch_cap=0x10000,
                           out_cap=0, alloc_fail_index=1))

    # --- zero rows: divmod by zero, no buffers touched
    cases.append(make_case("zero rows", row_count=0, q=0x3E, scratch_ptr=0,
                           scratch_cap=0, out_ptr=0, out_cap=0))

    # --- helpers re-read the buffer fields after decoding
    cases.append(make_case("filter call reassigns scratch", row_count=3,
                           q=0x3E, reassign_scratch=True))
    cases.append(make_case("filter call reassigns output", row_count=2,
                           q=0x3E, reassign_output=True))
    cases.append(make_case("filter call reassigns both", row_count=3, q=0x3E,
                           reassign_scratch=True, reassign_output=True))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
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
    print("Testing ui_func_003f5ad4 (0x003f5ad4)...")
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
        ("width_bias", "constexpr u32 kWidthBias26 = 0x26u;",
         "constexpr u32 kWidthBias26 = 0x27u;"),
        ("width_mode", "constexpr u32 kWidthMode = 2u;",
         "constexpr u32 kWidthMode = 1u;"),
        ("output_capacity_offset", "constexpr u32 kOutputCapacity4 = 0x04;",
         "constexpr u32 kOutputCapacity4 = 0x08;"),
        ("narrow_limit", "constexpr u32 kNarrowLimit20 = 0x20u;",
         "constexpr u32 kNarrowLimit20 = 0x1Eu;"),
        ("valid_size_store",
         "store_u32(object + kOutputValid8, transposed_bytes);",
         "store_u32(object + kOutputValid8, required);"),
        ("release_guard", "if (old_scratch != 0) {",
         "if (old_scratch == 0) {"),
        ("scratch_failure_return",
         "if (scratch == 0) {\n            return 0;",
         "if (scratch == 0) {\n            return 1;"),
        ("output_failure_return",
         "if (output == 0) {\n            return 0;",
         "if (output == 0) {\n            return 1;"),
        ("single_row_dispatch", "if (row_count == 1) {\n        const u32 row_record",
         "if (row_count >= 1) {\n        const u32 row_record"),
        ("row_requirement",
         "const u32 required = row_count == 1 ? (width << 1) : transposed_bytes;",
         "const u32 required = row_count == 1 ? width : transposed_bytes;"),
        ("transpose_stride", "destination += output_stride;",
         "destination += 2;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            try:
                bad = Runner().run(mutant_code, case)
            except RuntimeError:
                # A mutant that faults where the original succeeds is a
                # behaviour difference, not a harness failure.
                detected = True
                break
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
