#!/usr/bin/env python3
"""Differential test for engine_func_002c25f0 (0x002c25f0) using Unicorn ARM.

The pinned original at 0x002c25f0 is a four-byte tail veneer::

    0x002c25f0: b 0x00147830

It has no stack frame, saves no registers, forwards r0/r1 unchanged and returns
whatever 0x00147830 leaves in r0.  The ledger records the function as four
bytes; the candidate is compiled from readable C++ in
src/engine/leaf_batch36_c.cpp and relocated to the same address.

This runner compiles that translation unit, extracts engine_func_002c25f0,
resolves its single R_ARM_JUMP24 to a deterministic stub placed at the original
target 0x00147830, and executes the pinned original and the candidate in
separate Unicorn machines with identical fixtures.

Compared outputs per case:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log of the stub (r0-r3 and SP), so a lost, swapped or
    truncated argument is visible;
  * the full ARG, CANARY and STACK pages (the stub writes an argument-dependent
    pattern into ARG, so forwarded values must agree byte for byte);
  * every emulated memory write outside the stub's own mem_write calls.

Coverage: null/zero, page boundaries, exact page-size lengths, non-null and
non-aligned pointers, 32-bit boundary sizes, negative and zero helper returns.
Negative controls mutate forwarded arguments and the returned r0; a not-detected
mutant fails the run.  A comment-only mutant must stay undetected.

The deeper chain 0x00147830 -> 0x002AD4F0 -> 0x00147C0C -> SVC 0x32 is not
executed; 0x00147830 is modeled as a boundary stub.
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
SOURCE = ROOT / "src/engine/leaf_batch36_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_002c25f0"

FUNC_ADDR = 0x002C25F0
FUNC_SIZE = 4

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers 0x002C25F0 and the stub at 0x00147830
ARG_ADDR = 0x00700000
ARG_SIZE = 0x00010000
CANARY_ADDR = 0x00710000
CANARY_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_ADDR = 0x00147830
STUB_NAME = "func_00147830"

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


def extract_candidate(obj_file: Path):
    funcs = extract_elf_functions_detailed(obj_file)
    for name, value in funcs.items():
        if "002c25f0" in name:
            return name, value
    raise RuntimeError(
        f"engine_func_002c25f0 not found in {obj_file}: {sorted(funcs)}"
    )


def relocate_candidate(obj_file: Path) -> tuple[str, bytes]:
    name, (code_raw, relocs) = extract_candidate(obj_file)
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            if "147830" not in rel.symbol_name:
                raise RuntimeError(f"unexpected call target: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (STUB_ADDR - pc) >> 2
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
    return name, bytes(code)


def compile_candidate() -> tuple[str, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch36_c.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_variant(tag: str, old: str, new: str) -> tuple[str, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    variant_src = OUT_DIR / f"variant_{tag}.cpp"
    variant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"variant_{tag}.o"
    res = compile_tu_armv6k(variant_src, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Variant {tag} compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def fill_pattern(length: int, seed: int) -> bytes:
    out = bytearray(length)
    for index in range(length):
        out[index] = (index * 37 + seed) & 0xFF
    return bytes(out)


class VeneerRunner:
    """One Unicorn machine with a deterministic stub at 0x00147830."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(ARG_ADDR, ARG_SIZE)
        self.uc.mem_map(CANARY_ADDR, CANARY_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        # Original Thumb? No: 0x00147830 is ARM code; `bx lr` is enough.
        self.uc.mem_write(STUB_ADDR, struct.pack("<I", 0xE12FFF1E))
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_stub, begin=STUB_ADDR, end=STUB_ADDR
        )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.helper_ret = 0
        self.arg_before = b""

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        sp = uc.reg_read(arm.UC_ARM_REG_SP)
        self.call_log.append((STUB_NAME, r0, r1, r2, r3, sp))

        # Only touch the supplied buffer when the whole range is inside ARG.
        if ARG_ADDR <= r0 and r1 <= ARG_ADDR + ARG_SIZE - r0:
            pattern = bytes(
                ((index * 7 + r1) ^ (r0 >> 8) ^ 0x5A) & 0xFF
                for index in range(r1)
            )
            uc.mem_write(r0, pattern)

        uc.reg_write(arm.UC_ARM_REG_R0, self.helper_ret & 0xFFFFFFFF)

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.helper_ret = case["helper_ret"] & 0xFFFFFFFF

        self.uc.mem_write(FUNC_ADDR, code)
        self.arg_before = fill_pattern(ARG_SIZE, 0x11)
        self.uc.mem_write(ARG_ADDR, self.arg_before)
        self.uc.mem_write(CANARY_ADDR, fill_pattern(CANARY_SIZE, 0x22))
        self.uc.mem_write(STACK_ADDR, fill_pattern(STACK_SIZE, 0x33))
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case["r0"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["r1"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case["r2"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case["r3"] & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "arg": bytes(self.uc.mem_read(ARG_ADDR, ARG_SIZE)),
            "canary": bytes(self.uc.mem_read(CANARY_ADDR, CANARY_SIZE)),
            "stack": bytes(self.uc.mem_read(STACK_ADDR, STACK_SIZE)),
            "writes": list(self.writes),
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "call_log", "writes"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for key in ("arg", "canary", "stack"):
        if orig[key] != cand[key]:
            # Report the first differing byte to keep failures readable.
            first = next(
                (
                    index
                    for index, (left, right) in enumerate(zip(orig[key], cand[key]))
                    if left != right
                ),
                -1,
            )
            problems.append(f"{key} differs (first byte index {first})")
    # The veneer must not write memory itself; ARG changes come from the stub.
    if orig["writes"] or cand["writes"]:
        problems.append(f"emulated writes orig={orig['writes']} cand={cand['writes']}")
    return problems


def base_case(name: str, r0: int, r1: int, helper_ret: int = 0, **overrides) -> dict:
    case = {
        "name": name,
        "r0": r0,
        "r1": r1,
        "r2": 0xC0DE0001,
        "r3": 0xFEED0002,
        "helper_ret": helper_ret,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- null / zero and ordinary forwarding
    cases.append(base_case("null pointer, zero size", 0, 0))
    cases.append(base_case("null pointer, zero size, non-zero return", 0, 0, 0x12345678))
    cases.append(base_case("null pointer, size 1", 0, 1))
    cases.append(base_case("valid pointer, zero size", ARG_ADDR, 0, 0x7FFFFFFF))
    cases.append(base_case("valid pointer, size 1", ARG_ADDR, 1, 0x80000000))
    cases.append(base_case("valid pointer, size 4", ARG_ADDR, 4, 0xFFFFFFFF))
    cases.append(base_case("valid pointer, size 16", ARG_ADDR, 0x10, 0))
    cases.append(base_case("mid-page pointer, size 0x100", ARG_ADDR + 0x800, 0x100, 1))
    cases.append(base_case("unaligned pointer", ARG_ADDR + 3, 5, 0x40000000))
    cases.append(base_case("unaligned pointer, byte size", ARG_ADDR + 0x123, 1, 0xDEADBEEF))

    # --- page boundaries (all lengths fit, including the exact page)
    cases.append(base_case("page end minus 4, size 4", ARG_ADDR + ARG_SIZE - 4, 4))
    cases.append(base_case("page end minus 1, size 1", ARG_ADDR + ARG_SIZE - 1, 1))
    cases.append(base_case("page end minus 8, size 8", ARG_ADDR + ARG_SIZE - 8, 8))
    cases.append(base_case("page end, zero size", ARG_ADDR + ARG_SIZE, 0))
    cases.append(base_case("whole page", ARG_ADDR, ARG_SIZE, 0x55555555))

    # --- sizes that leave ARG (stub must not write; arguments still forwarded)
    cases.append(base_case("size one past page", ARG_ADDR, ARG_SIZE + 1))
    cases.append(base_case("size one past page end", ARG_ADDR + ARG_SIZE - 1, 2))
    cases.append(base_case("huge size", ARG_ADDR, 0xFFFFFFFF))
    cases.append(base_case("huge size, high bit", ARG_ADDR, 0x80000000))
    cases.append(base_case("max positive size", ARG_ADDR, 0x7FFFFFFF))

    # --- 32-bit boundary pointers (not dereferenced by the stub)
    cases.append(base_case("pointer 1", 1, 1))
    cases.append(base_case("pointer high bit", 0x80000000, 0x80000000))
    cases.append(base_case("pointer all ones", 0xFFFFFFFF, 0))
    cases.append(base_case("pointer below ARG", ARG_ADDR - 0x10000, 0x100))
    cases.append(base_case("pointer in canary", CANARY_ADDR, 0x20))
    cases.append(base_case("pointer in stack", STACK_ADDR, 0x20))

    # --- every kind of helper return value
    for value in (0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF, 0x0BADF00D):
        cases.append(
            base_case(f"helper return 0x{value:08x}", ARG_ADDR, 0x20, value)
        )

    # --- deterministic sweep of lengths and return values
    rng = random.Random(0x2C25F0)
    lengths = [0, 1, 2, 3, 4, 7, 8, 15, 16, 31, 32, 63, 64, 0x7F, 0x100, 0x3FF]
    for index in range(24):
        offset = rng.randrange(0, ARG_SIZE - 0x400)
        length = rng.choice(lengths)
        ret = rng.getrandbits(32)
        cases.append(
            base_case(
                f"sweep {index}: offset 0x{offset:x} length {length}",
                ARG_ADDR + offset,
                length,
                ret,
                r2=rng.getrandbits(32),
                r3=rng.getrandbits(32),
            )
        )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = VeneerRunner().run(orig_code, case)
        cand = VeneerRunner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}")
    return passed


def main() -> None:
    print("Testing engine_func_002c25f0 (0x002c25f0)...")
    orig_code = get_orig_bytes()
    name, cand_code = compile_candidate()
    print(
        f"symbol {name}: original {len(orig_code)} B "
        f"[{orig_code.hex(' ')}], candidate {len(cand_code)} B "
        f"[{cand_code.hex(' ')}] after relocation"
    )
    if len(cand_code) != FUNC_SIZE:
        raise SystemExit(f"candidate body is {len(cand_code)} bytes, expected 4")
    if cand_code == orig_code:
        print("Candidate is byte-identical to the pinned veneer.")
    else:
        print("Note: candidate bytes differ from the original (semantic mode).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = [
        (
            "zero_size",
            "return func_00147830(address, size);",
            "return func_00147830(address, 0);",
        ),
        (
            "constant_return",
            "    return func_00147830(address, size);",
            "    func_00147830(address, size);\n    return 0;",
        ),
        (
            "swapped_arguments",
            "return func_00147830(address, size);",
            "return func_00147830(reinterpret_cast<void*>(size), "
            "static_cast<u32>(reinterpret_cast<unsigned long>(address)));",
        ),
    ]
    for tag, old, new in mutants:
        mutant_code = compile_candidate_variant(tag, old, new)[1]
        detected = False
        for case in cases:
            orig = VeneerRunner().run(orig_code, case)
            bad = VeneerRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {tag} was not detected"
        print(f"  [PASS] {tag} mutant is detected")

    benign_code = compile_candidate_variant(
        "benign_comment", "Tail veneer at 0x00147830", "Tail thunk at 0x00147830"
    )[1]
    benign_detected = False
    for case in cases:
        orig = VeneerRunner().run(orig_code, case)
        benign = VeneerRunner().run(benign_code, case)
        if compare(orig, benign):
            benign_detected = True
            break
    assert not benign_detected, "comment-only control was incorrectly detected"
    print("  [PASS] comment-only control stays undetected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
