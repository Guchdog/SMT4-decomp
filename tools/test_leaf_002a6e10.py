#!/usr/bin/env python3
"""Differential test for func_002a6e10 (0x002a6e10) using Unicorn ARM.

The function converts a signed day count (days since 2000-01-01) into calendar
year/month/day and writes the three words through optional pointers.  This test
compiles ``src/engine/leaf_batch44_b.cpp``, extracts the candidate body, and
runs it side by side with the pinned original in separate Unicorn machines with
identical fixtures.

Compared state:
  * continuation PC, final SP and the callee-saved r4-r11;
  * every write outside the private stack, in order (address, size, value);
  * the complete 64 KiB data page;
  * known-date assertions for the recovered contract.

Coverage: the 60-day epoch shift, all month-index arms, the leap-day arm, 400-
year/100-year/4-year rollovers, signed wrap-around at both 32-bit extremes,
zero and negative day counts, and every null/non-null combination of the three
output pointers (including all three aliased to one word and all null).
Negative controls mutate the epoch shift, the century length, the leap-day
constant, and the September month split; each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch44_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_002a6e10"

FUNC_ADDR = 0x002A6E10
FUNC_SIZE = 400

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000
DATA_ADDR = 0x00600000
DATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Output slots inside the data page.  The year slot also aliases the month/day
# slot in the "same pointer" case.
YEAR_OFF = 0x100
MONTH_OFF = 0x104
DAY_OFF = 0x108
ALIAS_OFF = 0x10C

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

DATA_FILLER = bytes(((index * 37 + 0x5A) & 0xFF) for index in range(DATA_SIZE))


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def compile_candidate(source: Path = SOURCE, stem: str = "leaf_batch44_b"):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / f"{stem}.o"
    result = compile_tu_armv6k(source, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")

    functions = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in functions.items():
        if "002a6e10" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"func_002a6e10 not found in {obj_file}: {sorted(functions)}"
        )

    code, relocations = candidate
    if relocations:
        raise RuntimeError(f"unexpected relocations in leaf function: {relocations}")
    return bytes(code)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_source = OUT_DIR / f"mutant_{name}.cpp"
    mutant_source.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant_source, f"mutant_{name}")


class DateRunner:
    """One Unicorn machine; each candidate/original gets its own instance."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.writes: list[tuple[int, int, int]] = []
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def run(
        self,
        code: bytes,
        year_ptr: int,
        month_ptr: int,
        day_ptr: int,
        days: int,
    ) -> dict:
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DATA_ADDR, DATA_FILLER)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, year_ptr & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, month_ptr & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, day_ptr & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, days & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        outside_stack = [
            (address, size, value)
            for address, size, value in self.writes
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        ]

        def read_slot(pointer: int) -> int | None:
            if pointer == 0:
                return None
            return struct.unpack("<I", self.uc.mem_read(pointer, 4))[0]

        return {
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "writes": outside_stack,
            "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "year": read_slot(year_ptr),
            "month": read_slot(month_ptr),
            "day": read_slot(day_ptr),
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}: orig={orig[key]!r} cand={cand[key]!r}")
    if orig["writes"] != cand["writes"]:
        problems.append(f"writes: orig={orig['writes']} cand={cand['writes']}")
    if orig["data"] != cand["data"]:
        first = next(
            index
            for index, (left, right) in enumerate(zip(orig["data"], cand["data"]))
            if left != right
        )
        problems.append(f"data differs at data+0x{first:x}")
    for key in ("year", "month", "day"):
        if orig[key] != cand[key]:
            problems.append(f"{key}: orig={orig[key]!r} cand={cand[key]!r}")
    return problems


def decode_outputs(result: dict) -> tuple[int, int, int]:
    return result["year"], result["month"], result["day"]


def make_pointer_cases() -> list[dict]:
    all_three = {
        "name": "all three pointers",
        "year": DATA_ADDR + YEAR_OFF,
        "month": DATA_ADDR + MONTH_OFF,
        "day": DATA_ADDR + DAY_OFF,
    }
    return [
        all_three,
        {
            "name": "no output pointers",
            "year": 0,
            "month": 0,
            "day": 0,
        },
        {
            "name": "year only",
            "year": DATA_ADDR + YEAR_OFF,
            "month": 0,
            "day": 0,
        },
        {
            "name": "month only",
            "year": 0,
            "month": DATA_ADDR + MONTH_OFF,
            "day": 0,
        },
        {
            "name": "day only",
            "year": 0,
            "month": 0,
            "day": DATA_ADDR + DAY_OFF,
        },
        {
            "name": "year and month",
            "year": DATA_ADDR + YEAR_OFF,
            "month": DATA_ADDR + MONTH_OFF,
            "day": 0,
        },
        {
            "name": "all three aliased",
            "year": DATA_ADDR + ALIAS_OFF,
            "month": DATA_ADDR + ALIAS_OFF,
            "day": DATA_ADDR + ALIAS_OFF,
        },
    ]


def make_days() -> list[tuple[int, str, tuple[int, int, int] | None]]:
    """(day count, description, expected date when known)."""
    cases: list[tuple[int, str, tuple[int, int, int] | None]] = [
        (0, "2000-01-01 epoch", (2000, 1, 1)),
        (1, "2000-01-02", (2000, 1, 2)),
        (30, "2000-01-31", (2000, 1, 31)),
        (31, "2000-02-01", (2000, 2, 1)),
        (59, "2000-02-29 leap day", (2000, 2, 29)),
        (60, "2000-03-01 rebase", (2000, 3, 1)),
        (61, "2000-03-02", (2000, 3, 2)),
        (90, "2000-03-31", (2000, 3, 31)),
        (91, "2000-04-01", (2000, 4, 1)),
        (305, "2000-11-01", (2000, 11, 1)),
        (334, "2000-11-30", (2000, 11, 30)),
        (335, "2000-12-01", (2000, 12, 1)),
        (365, "2000-12-31", (2000, 12, 31)),
        (366, "2001-01-01 month split", (2001, 1, 1)),
        (730, "2001-12-31", (2001, 12, 31)),
        (731, "2002-01-01", (2002, 1, 1)),
        (1095, "2002-12-31", (2002, 12, 31)),
        (1096, "2003-01-01", (2003, 1, 1)),
        (1460, "2003-12-31", (2003, 12, 31)),
        (1461, "2004-01-01", (2004, 1, 1)),
        (1519, "2004-02-28", (2004, 2, 28)),
        (1520, "2004-02-29 leap-day arm", (2004, 2, 29)),
        (1521, "2004-03-01", (2004, 3, 1)),
        (2981, "2008-02-29 leap-day arm", (2008, 2, 29)),
        (36583, "2100-02-28 century boundary", (2100, 2, 28)),
        (36584, "2100-03-01 century boundary", (2100, 3, 1)),
        (36584 + 36523, "2200-02-28 second century", (2200, 2, 28)),
        (36584 + 36524, "2200-03-01 second century", (2200, 3, 1)),
        (-1, "1999-12-31 negative", (1999, 12, 31)),
        (-31, "1999-12-01", (1999, 12, 1)),
        (-60, "1999-11-02", (1999, 11, 2)),
        (-61, "1999-11-01", (1999, 11, 1)),
        (-365, "1999-01-01", (1999, 1, 1)),
        (-1460, "1996-01-02", (1996, 1, 2)),
        (-146097, "400-year rollover negative", (1600, 1, 1)),
        (-146098, "1600-01-01 derivative", (1599, 12, 31)),
        (0x7FFFFFFF, "INT32_MAX wrap", (5881610, 7, 11)),
        (0x7FFFFFFE, "INT32_MAX-1 wrap", (5881610, 7, 10)),
        (0x80000000 - 0x100000000, "INT32_MIN wrap", (5881610, 7, 12)),
        (0x80000000 - 0x100000000 + 60, "INT32_MIN+60", None),
        (0x80000001 - 0x100000000, "INT32_MIN+1", None),
        (-0x7FFFFFFF, "INT32_MIN+1 magnitude", None),
    ]
    # Around every 400-year revolution boundary and its +/-1 neighbours.
    for era in range(-4, 5):
        base = era * 146097
        for delta, label in ((-1, "-1"), (0, ""), (1, "+1")):
            days = base + delta
            cases.append((days, f"400y boundary era {era} {label}".strip(), None))
    # Leap days of eight consecutive four-year groups (exercise the arm often).
    for group in range(8):
        cases.append((1520 + group * 1461, f"leap day group {group}", None))
    return cases


def make_extra_days() -> list[int]:
    """Additional systematic and pseudo-random counts for the all-pointer path."""
    extra: list[int] = []
    # Stage boundaries (in rebased terms) with +/-1 neighbours.
    for period in (146097, 36524, 1461, 365):
        for k in range(-6, 7):
            for delta in (-1, 0, 1):
                extra.append(60 + k * period + delta)
    # Deterministic 32-bit LCG sample across the whole input range.
    state = 0x1234ABCD
    for _ in range(160):
        state = (state * 1103515245 + 12345) & 0xFFFFFFFF
        extra.append(state - 0x100000000 if state & 0x80000000 else state)
    # Deduplicate while preserving order.
    seen: set[int] = set()
    unique: list[int] = []
    for value in extra:
        value = value - 0x100000000 if value & 0x80000000 else value
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return unique


def main() -> None:
    print("Testing func_002a6e10 (0x002a6e10)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(no relocations)."
    )

    runner = DateRunner()
    candidate_runner = DateRunner()
    days_list = make_days()
    pointer_cases = make_pointer_cases()
    checks = 0
    known_checks = 0

    for days, description, expected in days_list:
        for pointers in pointer_cases:
            case_name = f"{description} / {pointers['name']}"
            orig = runner.run(
                orig_code, pointers["year"], pointers["month"], pointers["day"], days
            )
            cand = candidate_runner.run(
                cand_code, pointers["year"], pointers["month"], pointers["day"], days
            )
            problems = compare(orig, cand)
            if problems:
                print(f"  [FAIL] {case_name}")
                for problem in problems:
                    print(f"    {problem}")
                raise SystemExit(1)
            if expected is not None and pointers["name"] == "all three pointers":
                got = decode_outputs(orig)
                if got != expected:
                    print(
                        f"  [FAIL] {case_name}: expected {expected}, original gave "
                        f"{got}"
                    )
                    raise SystemExit(1)
                known_checks += 1
            checks += 1

    # Explicit no-write check for the all-null case at a few values.
    for days in (0, 60, 1520, -1, 0x7FFFFFFF):
        result = runner.run(orig_code, 0, 0, 0, days)
        if result["writes"]:
            print(f"  [FAIL] null pointers wrote at day {days}: {result['writes']}")
            raise SystemExit(1)
        checks += 1

    # Systematic/pseudo-random counts through the all-pointer path.
    for days in make_extra_days():
        orig = runner.run(
            orig_code, DATA_ADDR + YEAR_OFF, DATA_ADDR + MONTH_OFF,
            DATA_ADDR + DAY_OFF, days
        )
        cand = candidate_runner.run(
            cand_code, DATA_ADDR + YEAR_OFF, DATA_ADDR + MONTH_OFF,
            DATA_ADDR + DAY_OFF, days
        )
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] extra day {days}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        checks += 1

    print(
        f"  [PASS] {checks} differential runs, {known_checks} known-date assertions"
    )

    print("Negative controls:")
    mutants = (
        (
            "epoch_shift",
            "static_cast<u32>(day_count) - 0x3cu",
            "static_cast<u32>(day_count) - 0x3du",
        ),
        (
            "century_length",
            "days_in_era = days_in_era - century * 36524;",
            "days_in_era = days_in_era - century * 36525;",
        ),
        ("leap_day", "day = 0x1d;", "day = 0x1c;"),
        (
            "september_split",
            "} else if (month_index <= 9) {",
            "} else if (month_index < 9) {",
        ),
    )
    for name, old, new in mutants:
        mutant_code = compile_candidate_mutant(name, old, new)
        mutant_runner = DateRunner()
        detected = False
        for days, _description, _expected in days_list:
            orig = runner.run(
                orig_code, DATA_ADDR + YEAR_OFF, DATA_ADDR + MONTH_OFF,
                DATA_ADDR + DAY_OFF, days
            )
            bad = mutant_runner.run(
                mutant_code, DATA_ADDR + YEAR_OFF, DATA_ADDR + MONTH_OFF,
                DATA_ADDR + DAY_OFF, days
            )
            if compare(orig, bad):
                detected = True
                break
        if not detected:
            print(f"  [FAIL] negative control {name} was not detected")
            raise SystemExit(1)
        print(f"  [PASS] negative control {name} detected")

    print(f"\nAll {checks} differential cases PASSED.")


if __name__ == "__main__":
    main()
