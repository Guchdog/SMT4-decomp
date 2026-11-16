#!/usr/bin/env python3
"""Differential test for engine_func_0037fd94 (0x0037fd94) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the engine_func_0037fd94 body,
resolves its direct calls to deterministic stubs placed at the pinned original
addresses, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every register argument (the layout buffer is
    normalised to <stack>);
  * the 0x20-byte layout buffer handed to 0x0015D14C whenever the original
    initialised it (descriptor mode byte 3);
  * the receiver, descriptor, slot-table, slot-element and pointed-to-byte
    pages (full observable memory);
  * writes outside the private stack and the expected receiver/slot ranges.

Coverage: signed loop-bound boundaries (-1, INT_MIN, 0, 1, 2, 3, 6) including
the logged-once snapshot; descriptor mode bytes 0/1/2/3/4/0xFF; the 14-byte
span rounding for span 0/1/13/14/15/27/28 and the 32-bit extremes; flag byte
0/1/0x80/0xFF (both the single- and double-record paths); header word and span
word signed boundaries (including 32-bit subtraction wrap); null and non-null
base pointers; scaler results of 0 (modes 2/4), value (mode 0) and 2*value
(mode 1). There are no indirect calls in this function: the only dynamic
targets are the slot-table element reads documented in the record.
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
SOURCE = ROOT / "src/engine/leaf_batch45_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_0037fd94"

FUNC_ADDR = 0x0037FD94
FUNC_SIZE = 600

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the function and every stub below 0x37C36C
SELF_ADDR = 0x00500000
SELF_SIZE = 0x00002000
DESC_ADDR = 0x00510000
DESC_SIZE = 0x00001000
SLOTS_ADDR = 0x00520000
SLOTS_SIZE = 0x00001000
ELEMS_ADDR = 0x00530000
ELEMS_SIZE = 0x00001000
POINT_ADDR = 0x00540000
POINT_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets; stubs are placed at the same addresses so both
# the original bytes and the relocated candidate resolve to them.
STUB_2A21B8 = 0x002A21B8
STUB_2C5FF4 = 0x002C5FF4
STUB_37C36C = 0x0037C36C
STUB_15D14C = 0x0015D14C
STUB_2BD448 = 0x002BD448
STUB_15D91C = 0x0015D91C

STUB_NAMES = {
    STUB_2A21B8: "func_002a21b8",
    STUB_2C5FF4: "engine_func_002c5ff4",
    STUB_37C36C: "func_0037c36c",
    STUB_15D14C: "func_0015d14c",
    STUB_2BD448: "engine_func_002bd448",
    STUB_15D91C: "func_0015d91c",
}

EXPECTED_CALLS = {
    STUB_2A21B8: 3,  # two header scaler calls, one per loop iteration
    STUB_2C5FF4: 1,  # descriptor mode 3 only
    STUB_37C36C: 1,  # descriptor mode 3 with a non-zero span
    STUB_15D14C: 1,  # every iteration
    STUB_2BD448: 2,  # first record, second record when flag != 0
    STUB_15D91C: 2,  # first record, second record when flag != 0
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

DESC_STRIDE = 0x30
MAX_RECORDS = 6


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def elf_sections(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    e_shstrndx = struct.unpack_from("<H", data, 50)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    result: dict[str, bytes] = {}
    for section in sections:
        end = shstrtab.find(b"\x00", section[0])
        name = shstrtab[section[0] : end].decode("ascii", errors="replace")
        if name:
            result[name] = data[section[4] : section[4] + section[5]]
    return result


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0037fd94" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_0037fd94 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    resolved: dict[int, int] = {}
    for rel in relocs:
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name!r}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if f"{address:08x}" in rel.symbol_name.lower():
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name!r}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
        )
        resolved[target] = resolved.get(target, 0) + 1

    if resolved != EXPECTED_CALLS:
        raise RuntimeError(
            f"direct call relocation set mismatch: got {resolved}, "
            f"expected {EXPECTED_CALLS}"
        )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
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


# --------------------------------------------------------------- helper model
def stub_scale(value: int, mode: int) -> int:
    """Exact model of func_002a21b8 (0x002A21B8)."""
    value &= 0xFFFFFFFF
    mode &= 0xFFFFFFFF
    if mode == 0:
        return value
    if mode == 1:
        return (value << 1) & 0xFFFFFFFF
    if mode != 3:
        return 0
    product = ((value + 1) & 0xFFFFFFFFFFFFFFFF) * 0x49249249
    high = (product >> 32) & 0xFFFFFFFF
    quotient = high >> 2
    remainder = (value - 14 * quotient) & 0xFFFFFFFF
    result = (quotient << 4) & 0xFFFFFFFF
    if remainder != 0:
        result = (result + remainder) & 0xFFFFFFFF
        result = (result + 2) & 0xFFFFFFFF
    return (result >> 1) & 0xFFFFFFFF


def round_span(span: int) -> int:
    """The in-function 14-byte span rounding (mode byte 3 only)."""
    span &= 0xFFFFFFFF
    product = ((span + 1) & 0xFFFFFFFFFFFFFFFF) * 0x49249249
    return (14 * ((product >> 34) & 0xFFFFFFFFFFFFFFFF)) & 0xFFFFFFFF


# --------------------------------------------------------------------- fixtures
def pattern(size: int, seed: int) -> bytes:
    return bytes(((index * 7) + seed) & 0xFF for index in range(size))


def build_desc(case: dict) -> bytes:
    page = bytearray(pattern(DESC_SIZE, 0x31))
    mode = case["mode"] & 0xFF
    flag = case["flag"] & 0xFF
    span = case["span"] & 0xFFFFFFFF
    page[0] = mode
    page[1] = flag
    struct.pack_into("<I", page, 0x0C, case["word0"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x10, case["word1"] & 0xFFFFFFFF)

    effective_span = round_span(span) if mode == 3 and span != 0 else span
    for index in range(MAX_RECORDS):
        base = index * DESC_STRIDE
        if case.get("null_base"):
            pointer = 0
        elif mode == 3 and span != 0:
            pointer = (
                POINT_ADDR + 0x100 + index * 0x40
                - stub_scale(effective_span, 3)
            ) & 0xFFFFFFFF
        else:
            pointer = POINT_ADDR + 0x100 + index * 0x40
        struct.pack_into("<I", page, base + 0x14, pointer)
        struct.pack_into("<H", page, base + 0x20, case["layout"][0])
        struct.pack_into("<H", page, base + 0x22, case["layout"][1])
        struct.pack_into("<H", page, base + 0x24, case["layout"][2])
        struct.pack_into("<H", page, base + 0x3E, case["tail"][0])
        struct.pack_into("<H", page, base + 0x40, case["tail"][1])
        struct.pack_into("<H", page, base + 0x42, case["tail"][2])
    return bytes(page)


def build_self(case: dict) -> bytes:
    page = bytearray(pattern(SELF_SIZE, 0xA1))
    struct.pack_into("<I", page, 0x134, SLOTS_ADDR)
    page[0x78:0x7C] = (case["self_word"] & 0xFFFFFFFF).to_bytes(4, "little")
    return bytes(page)


def build_slots(case: dict) -> bytes:
    page = bytearray(pattern(SLOTS_SIZE, 0x77))
    for index in range(16):
        struct.pack_into("<I", page, index * 4, ELEMS_ADDR + index * 0x40)
    # The count lives at +8, aliasing element slot 2; the recovered function
    # only reads slot 2 as a pointer for a count above the practical maximum.
    struct.pack_into("<i", page, 8, case["count"])
    return bytes(page)


def build_elems() -> bytes:
    return pattern(ELEMS_SIZE, 0x53)


def build_point() -> bytes:
    return pattern(POINT_SIZE, 0x9C)


class FD94Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(SELF_ADDR, SELF_SIZE)
        self.uc.mem_map(DESC_ADDR, DESC_SIZE)
        self.uc.mem_map(SLOTS_ADDR, SLOTS_SIZE)
        self.uc.mem_map(ELEMS_ADDR, ELEMS_SIZE)
        self.uc.mem_map(POINT_ADDR, POINT_SIZE)
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
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _read_u32(self, address: int) -> int:
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2A21B8:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, stub_scale(r0, r1))
        elif address == STUB_2C5FF4:
            self._log(address, r0, r1, r2)
            if r2:
                data = self.uc.mem_read(r1, r2)
                self.uc.mem_write(r0, bytes(data))
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_37C36C:
            self._log(address, r0, r1, r2, r3)
            anchor = (
                (r3 + 0x1111) & 0xFFFF,
                (r2 + 0x2222) & 0xFFFF,
                (((r3 ^ r2) & 0xFFFF) + 0x3333) & 0xFFFF,
            )
            self.uc.mem_write(r0, struct.pack("<HHH", *anchor))
        elif address == STUB_15D14C:
            entries = [r0, r1]
            if self.case.get("read_layout"):
                entries.append(bytes(self.uc.mem_read(r2, 0x20)))
            self._log(address, *entries)
        elif address == STUB_2BD448:
            self._log(address, r0)
            self.uc.mem_write(r0, b"\x00" * 0x18)
        elif address == STUB_15D91C:
            self._log(address, r0, r1, r2, r3)
            if r0:
                element = self._read_u32(r0 + 4 * r1)
                # Element slots beyond the two real records alias the count
                # word; only dereference a mapped element object.
                if ELEMS_ADDR <= element < ELEMS_ADDR + ELEMS_SIZE and r3 != 0:
                    self.uc.mem_write(
                        element + 0x1C, struct.pack("<I", r2 & 0xFFFFFFFF)
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
                if (
                    isinstance(arg, int)
                    and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE
                ):
                    out.append("<stack>")
                else:
                    out.append(arg)
            normalised.append((name, tuple(out)))
        return normalised

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(SELF_ADDR, build_self(case))
        self.uc.mem_write(DESC_ADDR, build_desc(case))
        self.uc.mem_write(SLOTS_ADDR, build_slots(case))
        self.uc.mem_write(ELEMS_ADDR, build_elems())
        self.uc.mem_write(POINT_ADDR, build_point())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, DESC_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case["span"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("r3", 0xDEADBEEF))
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
                STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
                or SELF_ADDR <= address < SELF_ADDR + SELF_SIZE
                or SLOTS_ADDR <= address < SLOTS_ADDR + SLOTS_SIZE
                or ELEMS_ADDR <= address < ELEMS_ADDR + ELEMS_SIZE
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
                "self": bytes(self.uc.mem_read(SELF_ADDR, SELF_SIZE)),
                "desc": bytes(self.uc.mem_read(DESC_ADDR, DESC_SIZE)),
                "slots": bytes(self.uc.mem_read(SLOTS_ADDR, SLOTS_SIZE)),
                "elems": bytes(self.uc.mem_read(ELEMS_ADDR, ELEMS_SIZE)),
                "point": bytes(self.uc.mem_read(POINT_ADDR, POINT_SIZE)),
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


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "mode": 0,
        "flag": 0,
        "span": 0,
        "count": 2,
        "word0": 0x11223344,
        "word1": 0x55667788,
        "self_word": 0x99AABBCC,
        "layout": (0x1234, 0x5678, 0x9ABC),
        "tail": (0x0102, 0x0304, 0x0506),
        "null_base": False,
    }
    case.update(overrides)
    case.setdefault("read_layout", case["mode"] == 3)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- signed loop bound, including the early-exit and snapshot forms
    for count in (-1, -0x80000000, 0, 1, 2, 3, 6):
        cases.append(base_case(f"count {count}", count=count))

    # --- descriptor mode byte: 3 is the only special-cased value
    for mode in (0, 1, 2, 3, 4, 0xFF):
        cases.append(base_case(f"mode {mode}", mode=mode, span=0))
        cases.append(base_case(f"mode {mode} span 14", mode=mode, span=14))

    # --- span rounding for mode 3 (0, 13->0, 14->14, ...) and 32-bit wrap
    for span in (0, 1, 13, 14, 15, 27, 28, 0x7FFFFFFF, 0xFFFFFFF0,
                 0xFFFFFFFE, 0xFFFFFFFF):
        cases.append(
            base_case(f"mode 3 span 0x{span:08x}", mode=3, span=span)
        )

    # --- non-special modes still forward the span into the scaler
    for mode in (0, 1, 2):
        for span in (0, 1, 14, 0xFFFFFFFF):
            cases.append(
                base_case(
                    f"mode {mode} span 0x{span:08x}", mode=mode, span=span
                )
            )

    # --- flag byte: single-record and paired-record paths
    for flag in (0, 1, 0x80, 0xFF):
        cases.append(base_case(f"flag 0x{flag:02x} mode 0", flag=flag))
        cases.append(base_case(f"flag 0x{flag:02x} mode 3", flag=flag, mode=3,
                               span=14))

    # --- header word/span word boundaries (subtraction wrap)
    for word0 in (0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(
            base_case(f"word0 0x{word0:08x}", word0=word0, mode=3, span=14,
                      flag=1)
        )
    for word1 in (0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(
            base_case(f"word1 0x{word1:08x}", word1=word1, mode=3, span=14,
                      flag=1)
        )

    # --- null base pointer (only dereferenced when mode 3 and span != 0)
    cases.append(base_case("null base mode 0", null_base=True, flag=1))
    cases.append(base_case("null base mode 2 span 14", null_base=True, mode=2,
                           span=14, flag=1))
    cases.append(base_case("null base mode 3 span 0", null_base=True, mode=3,
                           span=0))

    # --- scaler result zero/non-zero combinations per iteration
    for mode in (0, 1, 2, 3):
        for span in (14, 15):
            cases.append(
                base_case(
                    f"scaler mode {mode} span {span}", mode=mode, span=span,
                    count=3, flag=1,
                )
            )

    # --- record bytes beyond the first descriptor (tail reads the next one)
    for tail in ((0, 0, 0), (0x7FFF, 0x8000, 0xFFFF), (0xFFFF, 0, 0x8000)):
        cases.append(
            base_case(f"tail {tail}", tail=tail, mode=3, span=14, flag=0xFF)
        )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = FD94Runner().run(orig_code, case)
        cand = FD94Runner().run(cand_code, case)
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
    print("Testing engine_func_0037fd94 (0x0037fd94)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    controls = (
        ("span_granule", "constexpr u32 kSpanGranule = 14;",
         "constexpr u32 kSpanGranule = 13;"),
        ("span_magic", "constexpr u64 kSpanDivisorMagic = 0x49249249ull;",
         "constexpr u64 kSpanDivisorMagic = 0x49249248ull;"),
        ("desc_base_word", "constexpr u32 kDescBaseWord = 0x14;",
         "constexpr u32 kDescBaseWord = 0x10;"),
        ("self_tail_array", "constexpr u32 kSelfTailArray = 0x6C;",
         "constexpr u32 kSelfTailArray = 0x68;"),
        ("entry_anchor", "constexpr u32 kEntryAnchor = 0x08;",
         "constexpr u32 kEntryAnchor = 0x0C;"),
        ("bind_polarity", "desc[kDescFlagByte] == 0 ? 1u : 0u",
         "desc[kDescFlagByte] == 0 ? 0u : 1u"),
    )
    for name, old, new in controls:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = FD94Runner().run(orig_code, case)
            bad = FD94Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
