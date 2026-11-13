#!/usr/bin/env python3
"""Differential test for script_vm_func_00296390 (0x00296390) using Unicorn ARM.

Compiles src/engine/leaf_batch44_b.cpp, extracts the
script_vm_func_00296390 body, resolves its two direct calls to deterministic
stubs placed at the original targets, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate machines with
identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log with the pointer argument of every helper call;
  * the full 0x3800-byte work-block fixture (flags, gate bytes, per-index
    words/latches, pass-4 thresholds/counters and the untouched sentinels);
  * every emulated write outside the private stack and the fixture.

Coverage:
  * pass 1: the unconditional slot 0, every later slot's signed gate byte
    zero/non-zero, the ignored flag slot at +0x2D82 (which is read by no
    pass), and 0x80/0xFF signed-negative but non-zero bytes;
  * pass 2: gate byte zero, gate non-zero with a zero per-index word,
    gate non-zero with word/latch combinations, latch already set, and the
    0x01000174 id forwarded to the 0x002BF9E8 stub;
  * pass 3: result 1 only when both gate bytes are set on all six slots;
    each individual zero gate/gate2 slot produces 0;
  * pass 4: signed halfword boundaries 13/14/15, 0x7FFF, 0x8000 (-32768) and
    -1, and the signed counter reset at 0x10000 with counters 0, 0xFFFE,
    0xFFFF, 0x10000, 0x7FFFFFFF, 0x80000000 and 0xFFFFFFFF.
Negative controls mutate the 0x002BF9E8 id, the pass-4 threshold, the latch
value, the pass-1 slot-0 special case and the counter reset boundary; each
mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_00296390"

FUNC_ADDR = 0x00296390
FUNC_SIZE = 408

# 0x100000..0x300000 covers the function and both helper stubs.
CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000
FIXTURE_ADDR = 0x00710000
FIXTURE_SIZE = 0x00010000
FIXTURE_SNAPSHOT = 0x3800
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_RELEASE = 0x002BF9E8   # script_vm_func_002bf9e8(id)
STUB_UPDATE = 0x002BF9F0    # ui_func_002bf9f0(object)

STUB_NAMES = {
    STUB_RELEASE: "script_vm_func_002bf9e8",
    STUB_UPDATE: "ui_func_002bf9f0",
}

# Slot stride and every field offset observed in the instruction stream.
SLOT_STRIDE = 140           # (7*i) * 4, the original `rsb`/`lsl #2` chain
SLOT_COUNT = 6
PASS1_FLAG = 0x2D82         # s8 gate for slots 1..5 (slot 0 is unconditional)
PASS2_GATE = 0x2E0E         # s8 gate for pass 2; PASS1_FLAG + SLOT_STRIDE
PASS2_WORD = 0x3618         # u32[index]
PASS2_LATCH = 0x3648        # u8[index]
PASS2_OBJECT = 0x3158       # object handed to 0x002BF9F0 in pass 2
PASS3_GATE2 = 0x31E2        # s8 second gate; PASS2_OBJECT + 0x8a
PASS4_THRESHOLD = 0x31B6    # s16, compared with 14
PASS4_COUNTER = 0x3548      # u32[index]

RELEASE_ID = 0x01000174

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

MAX_STUB_CALLS = 64


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00296390" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"script_vm_func_00296390 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):  # PC24 / CALL / JUMP24
            target = None
            for address in STUB_NAMES:
                if f"{address:08x}" in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            displacement = (target - (FUNC_ADDR + rel.offset + 8)) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch44_b.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_source = OUT_DIR / f"mutant_{name}.cpp"
    mutant_source.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_source, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def build_fixture(case: dict) -> bytes:
    page = bytearray(b"\xCC" * FIXTURE_SIZE)

    # Seven signed gate bytes live on one stride-140 chain starting at
    # PASS1_FLAG: indices 0..5 are the pass-1 gates for slots 1..5 (index 0 is
    # never read) and indices 1..6 are the pass-2 gates for slots 0..5.
    flags = case.get("flags", [0] * 7)
    for index, value in enumerate(flags):
        page[PASS1_FLAG + SLOT_STRIDE * index] = value & 0xFF

    words = case.get("words", [0] * SLOT_COUNT)
    latches = case.get("latches", [0] * SLOT_COUNT)
    gates2 = case.get("gate2", [0] * SLOT_COUNT)
    thresholds = case.get("thresholds", [0] * SLOT_COUNT)
    counters = case.get("counters", [0] * SLOT_COUNT)

    for index in range(SLOT_COUNT):
        struct.pack_into("<I", page, PASS2_WORD + 4 * index,
                         words[index] & 0xFFFFFFFF)
        page[PASS2_LATCH + index] = latches[index] & 0xFF
        page[PASS3_GATE2 + SLOT_STRIDE * index] = gates2[index] & 0xFF
        struct.pack_into("<h", page, PASS4_THRESHOLD + SLOT_STRIDE * index,
                         thresholds[index])
        struct.pack_into("<I", page, PASS4_COUNTER + 4 * index,
                         counters[index] & 0xFFFFFFFF)
    return bytes(page)


class Leaf00296390Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(FIXTURE_ADDR, FIXTURE_SIZE)
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

    # ------------------------------------------------------------------ stubs
    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        if len(self.call_log) > MAX_STUB_CALLS:
            raise RuntimeError("stub call budget exceeded (possible loop)")

        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append((STUB_NAMES[address], r0))
        if address == STUB_RELEASE:
            # The original ignores the return value; keep it non-zero.
            uc.reg_write(arm.UC_ARM_REG_R0, 0xE8E8E8E8)
        else:
            uc.reg_write(arm.UC_ARM_REG_R0, 0xF0F0F0F0)

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(FIXTURE_ADDR, build_fixture(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, FIXTURE_ADDR)
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
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_fixture = (
                FIXTURE_ADDR <= address < FIXTURE_ADDR + FIXTURE_SIZE
            )
            if not (in_stack or in_fixture):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "fixture": bytes(self.uc.mem_read(FIXTURE_ADDR, FIXTURE_SNAPSHOT)),
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
    if orig["fixture"] != cand["fixture"]:
        for offset in range(0, FIXTURE_SNAPSHOT):
            if orig["fixture"][offset] != cand["fixture"][offset]:
                problems.append(
                    f"fixture differs from +0x{offset:04x}: "
                    f"orig=0x{orig['fixture'][offset]:02x} "
                    f"cand=0x{cand['fixture'][offset]:02x}"
                )
                break
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "flags": [0] * 7,
        "words": [0] * SLOT_COUNT,
        "latches": [0] * SLOT_COUNT,
        "gate2": [0] * SLOT_COUNT,
        "thresholds": [0] * SLOT_COUNT,
        "counters": [0] * SLOT_COUNT,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- pass 1: the unconditional slot 0 and every later gate
    cases.append(base_case("all pass-1/pass-2 gates zero"))
    cases.append(base_case("all gates 0x7F", flags=[0x7F] * 7))
    cases.append(base_case("all gates 0x80 (signed negative)",
                           flags=[0x80] * 7))
    cases.append(base_case("all gates 0xFF (signed negative)",
                           flags=[0xFF] * 7))
    cases.append(base_case("flag [0] is never read", flags=[1, 0, 0, 0, 0, 0, 0]))
    for index in range(1, 7):
        flags = [0] * 7
        flags[index] = 1
        cases.append(base_case(f"only gate [{index}] set", flags=flags))
    cases.append(base_case("alternating gates 1,0,1,0,1,0,1",
                           flags=[1, 0, 1, 0, 1, 0, 1]))
    cases.append(base_case("alternating gates 0,1,0,1,0,1,0",
                           flags=[0, 1, 0, 1, 0, 1, 0]))

    # --- pass 2: word/latch combinations on every slot
    cases.append(base_case(
        "pass 2 words non-zero, latches clear",
        flags=[1] * 7,
        words=[0x11110000 + index for index in range(SLOT_COUNT)],
    ))
    cases.append(base_case(
        "pass 2 words non-zero, latches already set",
        flags=[1] * 7,
        words=[0x22220000 + index for index in range(SLOT_COUNT)],
        latches=[1] * SLOT_COUNT,
    ))
    cases.append(base_case(
        "pass 2 mixed word/latch/gate combinations",
        flags=[0, 1, 0, 1, 1, 0, 1],
        words=[0, 0xAAAA0001, 0, 0xAAAA0003, 0xAAAA0004, 0],
        latches=[0, 1, 0, 0, 1, 0],
    ))
    cases.append(base_case(
        "pass 2 non-zero words behind zero gates stay untouched",
        flags=[0] * 7,
        words=[0xDEAD0000 + index for index in range(SLOT_COUNT)],
    ))
    cases.append(base_case(
        "pass 2 gate set but word zero",
        flags=[0, 1, 1, 1, 1, 1, 1],
        words=[0] * SLOT_COUNT,
    ))

    # --- pass 3: ready result
    cases.append(base_case(
        "ready = 1 when every gate pair is set",
        flags=[1] * 7,
        gate2=[1] * SLOT_COUNT,
    ))
    for index in range(SLOT_COUNT):
        gate2 = [1] * SLOT_COUNT
        gate2[index] = 0
        cases.append(base_case(f"gate2 [{index}] zero -> 0",
                               flags=[1] * 7, gate2=gate2))
    for index in range(1, 7):
        flags = [1] * 7
        flags[index] = 0
        cases.append(base_case(f"pass-1/pass-2 gate [{index}] zero -> 0",
                               flags=flags, gate2=[1] * SLOT_COUNT))
    cases.append(base_case(
        "gate2 0x80/0xFF signed-negative but non-zero",
        flags=[1] * 7,
        gate2=[0x80, 0xFF, 0x80, 0xFF, 0x80, 0xFF],
    ))
    cases.append(base_case(
        "later slot zero after earlier slots pass",
        flags=[1] * 7,
        gate2=[1, 1, 1, 1, 1, 0],
    ))

    # --- pass 4: signed threshold boundaries
    cases.append(base_case(
        "threshold boundaries 13/14/15/0/-1/0x7FFF",
        thresholds=[13, 14, 15, 0, -1, 0x7FFF],
        counters=[0x00000100, 0x00000200, 0x00000300,
                  0x00000400, 0x00000500, 0x00000600],
        gate2=[1] * SLOT_COUNT,
    ))
    cases.append(base_case(
        "all thresholds below 14 leave counters untouched",
        thresholds=[-32768, -1, 0, 13, 13, -32768],
        counters=[0xFFFFFFFF] * SLOT_COUNT,
    ))
    cases.append(base_case(
        "threshold -32768 (bit pattern 0x8000) is negative",
        thresholds=[-32768] * SLOT_COUNT,
        counters=[1] * SLOT_COUNT,
    ))

    # --- pass 4: signed counter reset boundary
    cases.append(base_case(
        "counter reset boundary sweep",
        thresholds=[14, 14, 14, 14, 14, 14],
        counters=[0, 0xFFFE, 0xFFFF, 0x10000, 0x7FFFFFFF, 0x80000000],
    ))
    cases.append(base_case(
        "counter 0xFFFFFFFF wraps to 0 without reset",
        thresholds=[14] * SLOT_COUNT,
        counters=[0xFFFFFFFF] * SLOT_COUNT,
    ))
    cases.append(base_case(
        "counter 0xFFFF resets only at threshold 14",
        thresholds=[13, 14, 15, 13, 14, 0x7FFF],
        counters=[0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF],
    ))
    cases.append(base_case(
        "counter 0xFFFE increments without reset",
        thresholds=[14] * SLOT_COUNT,
        counters=[0xFFFE] * SLOT_COUNT,
    ))
    cases.append(base_case(
        "counter 0x7FFFFFFF increments to signed negative",
        thresholds=[14] * SLOT_COUNT,
        counters=[0x7FFFFFFF] * SLOT_COUNT,
    ))

    # --- combined end-to-end case touching all four passes
    cases.append(base_case(
        "combined four-pass run",
        flags=[1, 1, 0, 1, 0, 1, 1],
        words=[0, 0x11111111, 0, 0x33333333, 0, 0x55555555],
        latches=[0, 0, 1, 0, 0, 1],
        gate2=[1, 1, 1, 1, 1, 1],
        thresholds=[13, 14, 0, 15, -1, 0x7FFF],
        counters=[0xFFFF, 0xFFFE, 0x7FFFFFFF, 0, 0xFFFFFFFF, 0x10000],
    ))
    cases.append(base_case(
        "combined four-pass run with zero gates",
        flags=[0, 1, 0, 0, 0, 0, 1],
        words=[0x99990000, 0x99990001, 0, 0, 0, 0x99990005],
        latches=[0, 0, 0, 0, 0, 0],
        gate2=[0, 1, 0, 1, 0, 1],
        thresholds=[14, 13, 15, 0, -1, -32768],
        counters=[0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF],
    ))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = Leaf00296390Runner().run(orig_code, case)
        cand = Leaf00296390Runner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(
            f"  [PASS] {case['name']}  "
            f"(ret={orig['ret']}, {len(orig['call_log'])} calls)"
        )
    return passed


def main() -> None:
    print("Testing script_vm_func_00296390 (0x00296390)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B (resolved).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("release_id", "script_vm_func_002bf9e8(0x01000174u);",
         "script_vm_func_002bf9e8(0x01000175u);"),
        ("threshold_boundary",
         "if (*reinterpret_cast<const s16*>(slot + 0x31B6) < 14) {",
         "if (*reinterpret_cast<const s16*>(slot + 0x31B6) < 13) {"),
        ("latch_value", "*latch = 1;", "*latch = 2;"),
        ("pass1_unconditional", "if (index != 0 &&",
         "if (index != 1 &&"),
        ("counter_reset_boundary", "if (static_cast<s32>(next) >= 0x10000) {",
         "if (static_cast<s32>(next) > 0x10000) {"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Leaf00296390Runner().run(orig_code, case)
            bad = Leaf00296390Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
