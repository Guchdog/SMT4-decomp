#!/usr/bin/env python3
"""Differential test for script_vm_func_00297c9c (0x00297C9C) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the script_vm_func_00297c9c
body and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn ARM machines with identical fixtures.

The routine has no calls and no indirect branches, so there is no call log to
compare.  The observable contract is:

  * return r0, continuation PC, final SP and callee-saved r4-r11 (in
    particular r11/fp, which the candidate uses as a scratch register);
  * the complete 0x20000-byte fixture page that contains the record block
    starting at the pointer published through 0x00447A78.  The page is
    pre-filled with a per-case byte pattern, so a wrong store width, a missing
    store, an over-long loop or a write outside +0x3C..+0xCBD0 all show up;
  * a second, equal-sized "argument" page addressed through the incoming r0.
    The original never reads r0, so this page must stay untouched;
  * the full 0x10000-byte data page holding the 0x00447A78 pointer word;
  * any write outside the fixture page, the argument page and the private
    stack (the original pushes 4 bytes, the candidate 36; stack scratch below
    SP is not part of the contract).

Coverage:
  * 128-iteration sweep bound (+0x1D0..+0xCBD0) and the +0x3C preset element;
  * zero / 0xFF / 0x55 / 0xAA / 0x7F / 0x80 / 0xF0 / pseudo-random fixture
    fills, so every written and every preserved byte is exercised;
  * record-block bases at offsets 0, 4, 0x1000, 0x8000 and 0x10000 of the
    fixture page, including bases whose last 0x194-byte record ends a few
    bytes below the page end;
  * junk r0/r1/r2/r3 to prove the incoming argument is dead;
  * preset-vs-sweep divergence (50 at +0x78/+0x7C, 0 at +0x5C..+0x74, and the
    fields the preset leaves untouched);
  * negative controls: a changed sweep constant, a shortened loop bound, a
    changed preset value, a changed sweep word and a widened byte store; each
    mutant must be detected.

Domain limit: the global pointer must address a mapped object.  A null
0x00447A78 makes both bodies fault; the fault addresses differ because the
original and the candidate order their first accesses differently, so the null
case is reported as a documented boundary (both fault) rather than compared
byte-for-byte.
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
OUT_DIR = ROOT / "build/test_leaf_00297c9c"

FUNC_ADDR = 0x00297C9C
FUNC_SIZE = 404

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000
DATA_ADDR = 0x00440000
DATA_SIZE = 0x00010000          # holds the 0x00447A78 pointer word
GLOBAL_ADDR = 0x00447A78
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
FIXTURE_ADDR = 0x10000000
FIXTURE_SIZE = 0x00020000       # > 0x10000 + 0xCBD0 for the largest base
ARG_ADDR = 0x10200000
ARG_SIZE = 0x00020000
TRAP_ADDR = 0x90000000

BLOCK_SIZE = 0xCBD0             # 0x3C preset + 0x80 * 0x194 records
RECORD_COUNT = 0x80
RECORD_SIZE = 0x194
PRESET_OFFSET = 0x3C
RECORD_BASE = 0x1D0

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

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
    with open(ORIG_BIN, "rb") as stream:
        stream.seek(FUNC_ADDR - 0x00100000)
        return stream.read(FUNC_SIZE)


def compile_candidate(source: Path, obj_name: str) -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / obj_name
    result = compile_tu_armv6k(source, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    functions = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in functions.items():
        if "00297c9c" in name.lower():
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"script_vm_func_00297c9c not found in {obj_file}: {sorted(functions)}"
        )
    body, relocations = candidate
    if relocations:
        raise RuntimeError(
            "unexpected relocations in script_vm_func_00297c9c: "
            + repr(relocations)
        )
    return bytes(body)


def compile_candidate_baseline() -> bytes:
    return compile_candidate(SOURCE, "leaf_batch41_c.o")


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant_src, f"mutant_{name}.o")


def fill_pattern(kind: str, size: int) -> bytes:
    if kind == "zero":
        return b"\x00" * size
    if kind == "ones":
        return b"\xff" * size
    if kind == "alternating":
        return b"\x55" * size
    if kind == "inverse":
        return b"\xaa" * size
    if kind == "low":
        return b"\x7f" * size
    if kind == "high":
        return b"\x80" * size
    if kind == "nibble":
        return b"\xf0" * size
    if kind == "stream":
        # Deterministic xorshift stream: every byte differs from its neighbours
        # and from the values the routine stores.
        out = bytearray(size)
        state = 0x12345678
        for index in range(size):
            state ^= (state << 13) & 0xFFFFFFFF
            state ^= state >> 17
            state ^= (state << 5) & 0xFFFFFFFF
            out[index] = state & 0xFF
        return bytes(out)
    if kind == "words":
        out = bytearray(size)
        for offset in range(0, size, 4):
            struct.pack_into("<I", out, offset, 0xA5A50000 | (offset & 0xFFFF))
        return bytes(out)
    raise AssertionError(f"unknown fill pattern {kind}")


def base_case(name: str, base_offset: int = 0, fill: str = "stream",
              jitter: bool = False) -> dict:
    return {
        "name": name,
        "base_offset": base_offset,
        "fill": fill,
        "jitter": jitter,
    }


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # Every fill pattern at the canonical base.  Zero fills exercise the value
    # stores; non-zero fills prove that unwritten bytes are preserved and that
    # store widths match (a widened byte store would clobber the +0x01..+0x03
    # or +0x4D..+0x4F padding bytes).
    for fill in ("zero", "ones", "alternating", "inverse", "low", "high",
                 "nibble", "stream", "words"):
        cases.append(base_case(f"fill {fill} at base+0", fill=fill))

    # Record-block bases across the fixture page, including 4-aligned but
    # otherwise unaligned-looking addresses and a base whose last record ends
    # 0x430 bytes below the page end.
    for offset in (4, 0x100, 0x1000, 0x8000, 0x10000):
        cases.append(
            base_case(f"base+0x{offset:x} stream", base_offset=offset,
                      fill="stream")
        )
    cases.append(base_case("base+4 ones", base_offset=4, fill="ones"))
    cases.append(base_case("base+0x10000 inverse", base_offset=0x10000,
                           fill="inverse"))

    # Junk incoming arguments: r0 in particular must be ignored.
    cases.append(base_case("argument r0 is dead", fill="words", jitter=True))

    return cases


class S297C9CRunner:
    """One Unicorn machine with the original or candidate body installed."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # The body uses VFP (vldr/vstr/vstmia): enable CP10/CP11.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(FIXTURE_ADDR, FIXTURE_SIZE)
        self.uc.mem_map(ARG_ADDR, ARG_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.writes: list[tuple[int, int]] = []

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def run(self, code: bytes, case: dict) -> dict:
        pattern = fill_pattern(case["fill"], FIXTURE_SIZE)
        self.uc.mem_write(FIXTURE_ADDR, pattern)
        self.uc.mem_write(ARG_ADDR, fill_pattern("words", ARG_SIZE))
        data_page = bytearray(fill_pattern("stream", DATA_SIZE))
        global_value = FIXTURE_ADDR + case["base_offset"]
        struct.pack_into("<I", data_page, GLOBAL_ADDR - DATA_ADDR, global_value)
        self.uc.mem_write(DATA_ADDR, bytes(data_page))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.uc.mem_write(FUNC_ADDR, code)
        self.writes = []

        # Junk arguments; the routine ignores all of them.
        if case.get("jitter", False):
            r0 = ARG_ADDR + 0x40
            r1 = 0x11111111
            r2 = 0x22222222
            r3 = 0x33333333
        else:
            r0 = 0
            r1 = 0
            r2 = 0
            r3 = 0

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, r0)
        self.uc.reg_write(arm.UC_ARM_REG_R1, r1)
        self.uc.reg_write(arm.UC_ARM_REG_R2, r2)
        self.uc.reg_write(arm.UC_ARM_REG_R3, r3)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError as error:  # pragma: no cover - boundary path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            return {"faulted": True, "fault_pc": pc, "fault": str(error)}

        unexpected_writes = []
        for address, size in self.writes:
            in_fixture = FIXTURE_ADDR <= address < FIXTURE_ADDR + FIXTURE_SIZE
            in_arg = ARG_ADDR <= address < ARG_ADDR + ARG_SIZE
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not (in_fixture or in_arg or in_stack):
                unexpected_writes.append((address, size))

        return {
            "faulted": False,
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "fixture": bytes(self.uc.mem_read(FIXTURE_ADDR, FIXTURE_SIZE)),
            "arg": bytes(self.uc.mem_read(ARG_ADDR, ARG_SIZE)),
            "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def describe_memory_difference(case: dict, left: bytes, right: bytes,
                               base: int) -> str:
    diffs = [index for index in range(len(left)) if left[index] != right[index]]
    if not diffs:
        return ""
    shown = ", ".join(f"+0x{index:x}" for index in diffs[:12])
    if len(diffs) > 12:
        shown += f", ... ({len(diffs)} bytes total)"
    return (
        f"  [{case['name']}] memory at 0x{base:x} differs at {shown}\n"
        f"    orig={left[diffs[0]:diffs[0] + 8].hex()}\n"
        f"    cand={right[diffs[0]:diffs[0] + 8].hex()}"
    )


def compare(case: dict, orig: dict, cand: dict) -> list[str]:
    problems: list[str] = []
    if orig["faulted"] != cand["faulted"]:
        problems.append(
            f"  [{case['name']}] fault mismatch: orig={orig['faulted']} "
            f"cand={cand['faulted']}"
        )
        return problems
    if orig["faulted"]:
        if orig["fault_pc"] != cand["fault_pc"]:
            problems.append(
                f"  [{case['name']}] fault pc: orig=0x{orig['fault_pc']:08x} "
                f"cand=0x{cand['fault_pc']:08x}"
            )
        return problems

    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(
                f"  [{case['name']}] {key}: orig={orig[key]!r} "
                f"cand={cand[key]!r}"
            )
    for key, base in (("fixture", FIXTURE_ADDR), ("arg", ARG_ADDR),
                      ("data", DATA_ADDR)):
        difference = describe_memory_difference(case, orig[key], cand[key], base)
        if difference:
            problems.append(difference)
    if orig["unexpected_writes"] != cand["unexpected_writes"]:
        problems.append(
            f"  [{case['name']}] unexpected writes: "
            f"orig={orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def run_case_set(orig_code: bytes, cand_code: bytes, cases: list[dict]) -> int:
    passed = 0
    for case in cases:
        orig = S297C9CRunner().run(orig_code, case)
        cand = S297C9CRunner().run(cand_code, case)
        problems = compare(case, orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(problem)
            raise SystemExit(1)
        base = FIXTURE_ADDR + case["base_offset"]
        print(
            f"  [PASS] {case['name']}  (block 0x{base:08x}..0x{base + BLOCK_SIZE:08x})"
        )
        passed += 1
    return passed


def check_null_global_boundary(orig_code: bytes, cand_code: bytes) -> None:
    """Both bodies must fault when 0x00447A78 does not address a mapped object.

    The original writes +0x1D0 first, the candidate +0x1F8/+0x1FC, so only the
    fact of the fault is comparable; the record documents that limit.
    """
    case = base_case("null global")

    def faulted(code: bytes) -> bool:
        runner = S297C9CRunner()
        runner.uc.mem_write(FIXTURE_ADDR, fill_pattern("zero", FIXTURE_SIZE))
        runner.uc.mem_write(ARG_ADDR, fill_pattern("zero", ARG_SIZE))
        data_page = bytearray(DATA_SIZE)
        struct.pack_into("<I", data_page, GLOBAL_ADDR - DATA_ADDR, 0)
        runner.uc.mem_write(DATA_ADDR, bytes(data_page))
        runner.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        runner.uc.mem_write(FUNC_ADDR, code)
        runner.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        runner.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        try:
            runner.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=1_000_000)
        except unicorn.UcError:
            return True
        return False

    orig_faulted = faulted(orig_code)
    cand_faulted = faulted(cand_code)
    if not (orig_faulted and cand_faulted):
        raise SystemExit(
            f"  [FAIL] null global: orig faulted={orig_faulted} "
            f"cand faulted={cand_faulted}"
        )
    print("  [PASS] null global faults in both bodies (addresses not comparable)")


def main() -> None:
    print("Testing script_vm_func_00297c9c (0x00297C9C)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(no relocations)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)
    check_null_global_boundary(orig_code, cand_code)

    print("\nNegative controls:")
    controls = (
        # Changed sweep constant (1150 -> 1152 at record +0x5C/+0x68).
        ("sweep_value", "constexpr f32 kValue1150 = 1150.0f;",
         "constexpr f32 kValue1150 = 1152.0f;"),
        # Shortened sweep: the last record (index 0x7F) is never written.
        ("sweep_underrun",
         "for (s32 index = 0; index < static_cast<s32>(kRecordCount); ++index) {",
         "for (s32 index = 0; index < static_cast<s32>(kRecordCount) - 1; ++index) {"),
        # Over-long sweep: a 129th record is written at +0xCBD0.
        ("sweep_overrun",
         "for (s32 index = 0; index < static_cast<s32>(kRecordCount); ++index) {",
         "for (s32 index = 0; index <= static_cast<s32>(kRecordCount); ++index) {"),
        # Changed preset value (50 -> 25 at preset +0x78).
        ("preset_value", "preset.field_078 = kValue50;",
         "preset.field_078 = kValue25;"),
        # Changed sweep word (+0x190).
        ("sweep_word", "record.field_190 = 0;", "record.field_190 = 1;"),
        # Widened byte store (+0x4C byte -> 0x4C..0x4F word).
        ("store_width", "record.field_04c = 0;",
         "*reinterpret_cast<u32*>(&record.field_04c) = 0;"),
    )
    for name, old, new in controls:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = S297C9CRunner().run(orig_code, case)
            bad = S297C9CRunner().run(mutant_code, case)
            if compare(case, orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
