#!/usr/bin/env python3
"""Differential test for func_001393e0 (0x001393e0) using Unicorn ARM.

Compiles ``src/engine/leaf_batch34_c.cpp``, extracts the func_001393e0 body,
resolves its seven direct calls to deterministic stubs, and runs the pinned
original (``extracted/exefs/code.bin``) against the candidate in separate
Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log with every register argument and the four architected
    stack arguments of 0x002AD714 (hour/minute/second/millisecond);
  * the calendar record observed by the 0x00139F20 stub (year word, signed
    month/day/unknown/hour/minute/second and signed millisecond), which proves
    the caller zeroed the time-of-day fields;
  * the full 64 KiB state page (all state writes, untouched filler included);
  * any emulated write outside the private stack and the state page.

Coverage: both entry branches (rebuild vs. advance), the early-return window at
100 frame units, the equality branch and its skip path, the 300/10 counter
saturation boundaries (below, at and above each cap), the accumulator divisor
boundaries 99/100/1000, multi-day loops, signed 64-bit timestamp boundaries,
and sign-extended month/day/year values.

Negative controls mutate the day step, both saturation caps and the early-return
threshold; each mutant must be detected by the same case set.
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
OUT_DIR = ROOT / "build/test_leaf_001393e0"

FUNC_ADDR = 0x001393E0
FUNC_SIZE = 976

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # function plus every stub below 0x400000
STATE_ADDR = 0x00710000
STATE_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

STATE_OFFSET = 0x0100
ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
MS_PER_DAY = 86400000

STUB_2C586C = 0x002C586C
STUB_2AD8F8 = 0x002AD8F8
STUB_139F20 = 0x00139F20
STUB_2AD714 = 0x002AD714
STUB_13924C = 0x0013924C
STUB_139230 = 0x00139230

STUB_NAMES = {
    STUB_2C586C: "engine_func_002c586c",
    STUB_2AD8F8: "engine_func_002ad8f8",
    STUB_139F20: "func_00139f20",
    STUB_2AD714: "func_002ad714",
    STUB_13924C: "func_0013924c",
    STUB_139230: "func_00139230",
}

# Number of architected stack words each helper receives beyond r0-r3.
STACK_ARGS = {
    STUB_2C586C: 0,
    STUB_2AD8F8: 0,
    STUB_139F20: 0,
    STUB_2AD714: 4,  # hour, minute, second, millisecond
    STUB_13924C: 0,
    STUB_139230: 0,
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


def find_candidate(obj_file: Path):
    funcs = extract_elf_functions_detailed(obj_file)
    for name, value in funcs.items():
        if "001393e0" in name:
            return value
    raise RuntimeError(f"func_001393e0 not found in {obj_file}: {sorted(funcs)}")


def relocate_candidate(obj_file: Path) -> bytes:
    code_raw, relocs = find_candidate(obj_file)
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if f"{address:08x}" in rel.symbol_name or name in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
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
def state_sentinel() -> bytearray:
    """Deterministic filler so stray state-page writes are visible."""
    return bytearray(((i * 37 + 11) & 0xFF) for i in range(STATE_SIZE))


def build_state_page(case: dict) -> bytes:
    page = state_sentinel()
    base = STATE_OFFSET
    page[base + 0x00 : base + 0x04] = bytes((case.get("reserved", 0xA5) & 0xFF,) * 4)
    struct.pack_into("<H", page, base + 0x04, case.get("counterA", 0) & 0xFFFF)
    struct.pack_into("<H", page, base + 0x06, case.get("counterB", 0) & 0xFFFF)
    struct.pack_into("<I", page, base + 0x08, case.get("lastStamp", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, base + 0x0C, case.get("accum", 0) & 0xFFFFFFFF)
    struct.pack_into("<h", page, base + 0x10, case.get("state_year", 2020) & 0xFFFF)
    page[base + 0x12] = case.get("state_month", 3) & 0xFF
    page[base + 0x13] = case.get("state_day", 14) & 0xFF
    return bytes(page)


def build_date_bytes(case: dict) -> bytes:
    raw = bytearray(12)
    struct.pack_into("<I", raw, 0x00, case.get("date_year", 2026) & 0xFFFFFFFF)
    raw[0x04] = case.get("date_month", 5) & 0xFF
    raw[0x05] = case.get("date_day", 20) & 0xFF
    raw[0x06] = case.get("date_unknown06", 0x42) & 0xFF
    raw[0x07] = case.get("date_hour", 13) & 0xFF
    raw[0x08] = case.get("date_minute", 37) & 0xFF
    raw[0x09] = case.get("date_second", 59) & 0xFF
    struct.pack_into("<H", raw, 0x0A, case.get("date_ms", 321) & 0xFFFF)
    return bytes(raw)


def distribute_sum(total: int) -> list[int]:
    """Split an exact 24-word sum into 16-bit words."""
    total = max(0, min(total, 24 * 0xFFFF))
    words = []
    remaining = total
    for _ in range(24):
        word = min(remaining, 0xFFFF)
        words.append(word)
        remaining -= word
    return words


def derived_sum(timestamp: int) -> int:
    """Timestamp-dependent total used when a case does not pin the sum."""
    value = timestamp & 0xFFFFFFFFFFFFFFFF
    total = 0
    for index in range(24):
        total += (value ^ (index * 0x1357 + 0x2468)) & 0xFFFF
    return total


def signed64(low: int, high: int) -> int:
    value = (low & 0xFFFFFFFF) | ((high & 0xFFFFFFFF) << 32)
    return value - (1 << 64) if value & (1 << 63) else value


def pack64(value: int) -> bytes:
    return struct.pack("<Q", value & 0xFFFFFFFFFFFFFFFF)


class RegenRunner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(STATE_ADDR, STATE_SIZE)
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
        self.calendar_index = 0
        self.case: dict = {}

    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2C586C:
            self._log(address, r0)
            uc.mem_write(r0, pack64(self.case.get("raw", 0x0011223344556677)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_2AD8F8:
            timestamp = struct.unpack("<Q", uc.mem_read(r1, 8))[0]
            self._log(address, r0, timestamp)
            uc.mem_write(r0, build_date_bytes(self.case))
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_139F20:
            raw = bytes(uc.mem_read(r1, 12))
            self._log(
                address,
                r0,
                struct.unpack_from("<I", raw, 0x00)[0],
                struct.unpack_from("<b", raw, 0x04)[0],
                struct.unpack_from("<b", raw, 0x05)[0],
                struct.unpack_from("<b", raw, 0x06)[0],
                struct.unpack_from("<b", raw, 0x07)[0],
                struct.unpack_from("<b", raw, 0x08)[0],
                struct.unpack_from("<b", raw, 0x09)[0],
                struct.unpack_from("<h", raw, 0x0A)[0],
            )
            uc.mem_write(r0, pack64(self.case.get("first", 0)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_2AD714:
            self._log(address, r0, r1, r2, r3)
            uc.mem_write(r0, pack64(self.case.get("second", 0)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_13924C:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("cur", 0) & 0xFFFFFFFF)
        elif address == STUB_139230:
            timestamp = signed64(r2, r3)
            self._log(address, r0, r1, timestamp)
            sums = self.case.get("calendar_sums")
            if sums is not None and self.calendar_index < len(sums):
                total = sums[self.calendar_index]
            else:
                total = derived_sum(timestamp)
            self.calendar_index += 1
            uc.mem_write(
                r0,
                b"".join(struct.pack("<H", word) for word in distribute_sum(total)),
            )
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

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
        self.calendar_index = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(STATE_ADDR, build_state_page(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, STATE_ADDR + STATE_OFFSET)
        for register in (
            arm.UC_ARM_REG_R1,
            arm.UC_ARM_REG_R2,
            arm.UC_ARM_REG_R3,
        ):
            self.uc.reg_write(register, 0)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_state = STATE_ADDR <= address < STATE_ADDR + STATE_SIZE
            if not in_stack and not in_state:
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "state": bytes(self.uc.mem_read(STATE_ADDR, STATE_SIZE)),
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
    if orig["state"] != cand["state"]:
        first = next(
            index
            for index, (left, right) in enumerate(zip(orig["state"], cand["state"]))
            if left != right
        )
        problems.append(
            f"state page differs first at 0x{first:04x}: "
            f"orig=0x{orig['state'][first]:02x} cand=0x{cand['state'][first]:02x}"
        )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def case(name: str, **overrides) -> dict:
    value = {
        "name": name,
        "raw": 0x0011223344556677,
        "first": 0,
        "second": 0,
        "cur": 0x1000,
    }
    value.update(overrides)
    return value


def make_cases() -> list[dict]:
    cases: list[dict] = []
    day = MS_PER_DAY

    # --- entry branch: rebuild (first < second)
    cases.append(
        case(
            "first below second -> rebuild",
            first=100,
            second=day + 500,
            cur=0x2000,
            counterA=5,
            counterB=3,
            lastStamp=0x0100,
            accum=0x1234,
        )
    )
    cases.append(
        case(
            "first far below second (negative second) -> rebuild",
            first=-(1 << 63),
            second=0,
            cur=1,
            counterA=7,
            counterB=7,
            lastStamp=0,
            accum=9,
        )
    )

    # --- entry branch: rebuild through counterA saturation
    cases.append(
        case(
            "counterA == 300 with equal stamps -> rebuild",
            first=day * 3,
            second=day * 3,
            cur=0x4000,
            counterA=300,
            counterB=2,
            lastStamp=0x4000 - 50,
            accum=0x77,
        )
    )
    cases.append(
        case(
            "counterA == 301 clamps on rebuild",
            first=0,
            second=0,
            cur=0x4001,
            counterA=301,
            counterB=0,
            lastStamp=0x4001 - 200,
            accum=0,
        )
    )
    cases.append(
        case(
            "counterA == 300 keeps 300 and returns day",
            first=0,
            second=0,
            cur=0x4001,
            counterA=300,
            counterB=5,
            lastStamp=0x4001 - 200,
            accum=0,
        )
    )

    # --- entry branch: rebuild through lastStamp > cur
    cases.append(
        case(
            "lastStamp above cur -> rebuild",
            first=10,
            second=day * 2,
            cur=0x100,
            counterA=1,
            counterB=1,
            lastStamp=0x101,
            accum=5,
        )
    )

    # --- entry branch: equal stamps with counterB saturated -> rebuild
    for counter_b in (10, 11, 0xFFFF):
        cases.append(
            case(
                f"equal stamps, counterB={counter_b} -> rebuild",
                first=day,
                second=day,
                cur=0x3000,
                counterA=12,
                counterB=counter_b,
                lastStamp=0x3000 - 500,
                accum=0x900,
            )
        )

    # --- early return window: (cur - lastStamp) < 100
    for delta in (0, 1, 99):
        cases.append(
            case(
                f"advance path early return delta={delta}",
                first=day + 10,
                second=day,
                cur=0x5000,
                counterA=4,
                counterB=4,
                lastStamp=0x5000 - delta,
                accum=0x2222,
            )
        )
    cases.append(
        case(
            "advance path delta=100 proceeds",
            first=day + 10,
            second=day,
            cur=0x5000,
            counterA=4,
            counterB=4,
            lastStamp=0x5000 - 100,
            accum=0,
            calendar_sums=[1000, 1000],
        )
    )

    # --- single equal iteration, counterB / accumulator boundaries
    for counter_b, total in (
        (0, 0),
        (0, 99),
        (0, 100),
        (0, 999),
        (0, 1000),
        (5, 1000),
        (9, 999),
        (10, 999),
        (20, 150),
    ):
        cases.append(
            case(
                f"equal one step counterB={counter_b} sum={total}",
                first=day * 4,
                second=day * 4,
                cur=0x6000,
                counterA=10,
                counterB=counter_b,
                lastStamp=0x6000 - 300,
                accum=0,
                calendar_sums=[total],
            )
        )

    # --- counterA saturation inside the equal iteration
    for counter_a, total, base in (
        (299, 999, 0),
        (295, 999, 0),
        (290, 999, 0),
        (250, 100, 0),
        (299, 100, 0),
    ):
        cases.append(
            case(
                f"equal step counterA={counter_a} sum={total}",
                first=day * 5,
                second=day * 5,
                cur=0x6100,
                counterA=counter_a,
                counterB=0,
                lastStamp=0x6100 - 300,
                accum=base,
                calendar_sums=[total],
            )
        )

    # --- accumulator base larger than the sum (elapsed clamps to zero)
    cases.append(
        case(
            "sum below accumulator -> zero elapsed",
            first=day,
            second=day,
            cur=0x6200,
            counterA=20,
            counterB=3,
            lastStamp=0x6200 - 400,
            accum=5000,
            calendar_sums=[4999],
        )
    )
    cases.append(
        case(
            "sum equal to accumulator -> zero elapsed",
            first=day,
            second=day,
            cur=0x6201,
            counterA=20,
            counterB=3,
            lastStamp=0x6201 - 400,
            accum=5000,
            calendar_sums=[5000],
        )
    )
    cases.append(
        case(
            "accumulator low16 only",
            first=day,
            second=day,
            cur=0x6202,
            counterA=20,
            counterB=3,
            lastStamp=0x6202 - 400,
            accum=0xFFFF0000 | 100,
            calendar_sums=[350],
        )
    )

    # --- multi-day loops (non-equal iterations only advance counterA)
    cases.append(
        case(
            "two day gap, equal only on final step",
            first=day * 2,
            second=0,
            cur=0x7000,
            counterA=290,
            counterB=9,
            lastStamp=0x7000 - 500,
            accum=0,
            calendar_sums=[999, 1000, 500],
        )
    )
    cases.append(
        case(
            "three day gap with mixed sums",
            first=day * 3,
            second=0,
            cur=0x7100,
            counterA=100,
            counterB=2,
            lastStamp=0x7100 - 500,
            accum=0x100,
            calendar_sums=[250, 1250, 999, 4321],
        )
    )
    cases.append(
        case(
            "negative timestamps two steps",
            first=-day,
            second=-day * 2,
            cur=0x7200,
            counterA=11,
            counterB=9,
            lastStamp=0x7200 - 500,
            accum=0,
            calendar_sums=[350],
        )
    )
    cases.append(
        case(
            "negative to zero single step",
            first=-1,
            second=-day,
            cur=0x7300,
            counterA=0,
            counterB=0,
            lastStamp=0x7300 - 500,
            accum=0,
            calendar_sums=[0],
        )
    )
    cases.append(
        case(
            "second wraps toward INT64 boundaries",
            first=(1 << 63) - 1 - day * 2,
            second=(1 << 63) - 1 - day * 3,
            cur=0x7400,
            counterA=5,
            counterB=5,
            lastStamp=0x7400 - 500,
            accum=0,
            calendar_sums=[1200, 1200, 1200, 1200],
        )
    )

    cases.append(
        case(
            "four day gap, accumulator only used on first iteration",
            first=day * 4,
            second=0,
            cur=0x7700,
            counterA=250,
            counterB=15,
            lastStamp=0x7700 - 500,
            accum=0xFFFF0000 | 1000,
            calendar_sums=[1050, 2000, 999, 1000, 5000],
        )
    )

    # --- signed date fields and the time-of-day zeroing
    for month, day_byte, year in (
        (0x85, 0xF0, 0xFFFF8001),
        (0x7F, 0x7F, 0x00007FFF),
        (0x80, 0x01, 0x8000),
    ):
        cases.append(
            case(
                f"signed date month=0x{month:02x} day=0x{day_byte:02x} "
                f"year=0x{year:08x}",
                first=day,
                second=day,
                cur=0x7500,
                counterA=42,
                counterB=6,
                lastStamp=0x7500 - 250,
                accum=0x33,
                date_year=year,
                date_month=month,
                date_day=day_byte,
                date_unknown06=0x80,
                date_hour=23,
                date_minute=58,
                date_second=57,
                date_ms=-2,
                calendar_sums=[777],
            )
        )

    # --- raw timestamp forwarding
    for raw in (0, 0xFFFFFFFFFFFFFFFF, 0x0123456789ABCDEF):
        cases.append(
            case(
                f"raw timestamp 0x{raw:016x}",
                raw=raw,
                first=day,
                second=0,
                cur=0x7600,
                counterA=1,
                counterB=1,
                lastStamp=0x7600 - 500,
                accum=0,
                calendar_sums=[123],
            )
        )

    return cases


def run_case_set(orig_code, cand_code, cases, verbose: bool = True) -> int:
    passed = 0
    for entry in cases:
        orig = RegenRunner().run(orig_code, entry)
        cand = RegenRunner().run(cand_code, entry)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {entry['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        if verbose:
            print(f"  [PASS] {entry['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing func_001393e0 (0x001393e0)...")
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
        (
            "day_step",
            "constexpr u64 kRegenMsPerDay = 86400000;   // 0x05265c00",
            "constexpr u64 kRegenMsPerDay = 86400001;   // 0x05265c00",
        ),
        (
            "counter_a_cap",
            "constexpr u32 kRegenCounterACap = 300;     // 0x12c",
            "constexpr u32 kRegenCounterACap = 299;     // 0x12c",
        ),
        (
            "counter_b_cap",
            "constexpr u32 kRegenCounterBCap = 10;      // 0x0a",
            "constexpr u32 kRegenCounterBCap = 9;       // 0x0a",
        ),
        (
            "early_return_threshold",
            "constexpr u32 kRegenStampDelta = 100;      // 0x64",
            "constexpr u32 kRegenStampDelta = 101;      // 0x64",
        ),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for entry in cases:
            orig = RegenRunner().run(orig_code, entry)
            bad = RegenRunner().run(mutant_code, entry)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
