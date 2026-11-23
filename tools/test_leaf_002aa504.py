#!/usr/bin/env python3
"""Differential test for script_vm_func_002aa504 (0x002aa504) using Unicorn ARM.

The pinned function is an unsigned 64-bit divide with the ARM EABI
``__aeabi_uldivmod`` register contract: numerator in r0:r1, divisor in r2:r3,
quotient returned in r0:r1 and remainder published in r2:r3.  A zero divisor
calls 0x001524E8 (a no-op in the pinned image) and returns quotient 0 with the
numerator as remainder.

The test compiles ``src/engine/leaf_batch45_b.cpp`` with
``tools.build_check.compile_tu_armv6k``, extracts the candidate body, resolves
its single direct call to a deterministic stub at 0x001524E8, and runs it and
the pinned original in separate Unicorn machines with identical fixtures.

Compared outputs:
  * quotient (r0:r1) and remainder (r2:r3), checked against Python's exact
    integer division as an independent oracle;
  * continuation PC, final SP and callee-saved r4-r11;
  * the ordered log of 0x001524E8 calls (r0, r1) plus its residual r2/r3
    register state, which the C-level two-argument declaration does not carry;
  * the untouched data page and any write outside the private stack.

Coverage: zero divisor, zero numerator, numerator < divisor, every exponent
difference 0..6, both low and high divisors, the reciprocal-table branch and
the main shift/subtract branch, boundary and randomized 64-bit pairs, and
constructed ``q * d + r`` triples.  A code-coverage hook asserts that every
instruction in the original body [0x002AA504, 0x002AA7B4) is executed at least
once, so every original branch and loop bound is exercised.

Negative controls recompile mutated copies of the source and require detection.
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
SOURCE = ROOT / "src/engine/leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_002aa504"

FUNC_ADDR = 0x002AA504
FUNC_SIZE = 752
FUNC_CODE_END = 0x002AA7B4          # first literal-pool word

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000              # covers the function and 0x001524E8
DATA_ADDR = 0x00800000
DATA_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
ENTRY_DATA = bytes((0x40 + i) & 0xFF for i in range(DATA_SIZE))

DIV0_ADDR = 0x001524E8
DIV0_NAME = "script_vm_func_001524e8"
DIV0_BODY = struct.pack("<II", 0xE1A00000, 0xE12FFF1E)  # mov r0,r0; bx lr

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
        if "002aa504" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"script_vm_func_002aa504 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        if "001524e8" not in rel.symbol_name:
            raise RuntimeError(f"unexpected call target: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (DIV0_ADDR - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_b.o"
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


def u64(lo: int, hi: int) -> int:
    return (lo & 0xFFFFFFFF) | ((hi & 0xFFFFFFFF) << 32)


class DivRunner:
    """One Unicorn machine; reuse it for every case of one implementation."""

    def __init__(self, track_coverage: bool = False) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        self.uc.mem_write(DIV0_ADDR, DIV0_BODY)
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_div0, begin=DIV0_ADDR, end=DIV0_ADDR
        )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.track_coverage = track_coverage
        self.coverage: set[int] = set()
        if track_coverage:
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE,
                self._on_code,
                begin=FUNC_ADDR,
                end=FUNC_CODE_END - 1,
            )

        self.call_log: list[tuple[int, int, int, int]] = []
        self.writes: list[tuple[int, int, int]] = []

    def _on_code(self, uc, address: int, size: int, user_data) -> None:
        self.coverage.add(address)

    def _on_div0(self, uc, address: int, size: int, user_data) -> None:
        self.call_log.append(
            (
                uc.reg_read(arm.UC_ARM_REG_R0),
                uc.reg_read(arm.UC_ARM_REG_R1),
                uc.reg_read(arm.UC_ARM_REG_R2),
                uc.reg_read(arm.UC_ARM_REG_R3),
            )
        )

    def _on_write(self, uc, access, address: int, size: int, value: int,
                  user_data) -> None:
        self.writes.append((address, size, value))

    def run(self, code: bytes, numerator: int, divisor: int) -> dict:
        self.call_log = []
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, code)
        # Unicorn 2.1.4 can keep a translated block when the replacement code
        # has the same length (the mutants are the same size as the candidate).
        # Drop the cached blocks explicitly so every run executes its own bytes.
        self.uc.ctl_remove_cache(FUNC_ADDR, FUNC_ADDR + FUNC_SIZE)
        self.uc.mem_write(DATA_ADDR, ENTRY_DATA)
        self.uc.mem_write(STACK_ADDR, b"\xA5" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, numerator & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, (numerator >> 32) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, divisor & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, (divisor >> 32) & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        quotient = u64(
            self.uc.reg_read(arm.UC_ARM_REG_R0),
            self.uc.reg_read(arm.UC_ARM_REG_R1),
        )
        remainder = u64(
            self.uc.reg_read(arm.UC_ARM_REG_R2),
            self.uc.reg_read(arm.UC_ARM_REG_R3),
        )

        outside = [
            (address, size)
            for address, size, _value in self.writes
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        ]

        return {
            "quotient": quotient,
            "remainder": remainder,
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            # The callee ignores r2/r3, but keep the residual register state in
            # the log so the documentation is explicit about the difference.
            "call_log": list(self.call_log),
            "call_args": [(r0, r1) for r0, r1, _r2, _r3 in self.call_log],
            "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "outside_writes": outside,
            "stack": bytes(self.uc.mem_read(STACK_ADDR, STACK_SIZE)),
        }


def expected(numerator: int, divisor: int) -> tuple[int, int]:
    if divisor == 0:
        return 0, numerator
    return divmod(numerator, divisor)


def compare(orig: dict, cand: dict, numerator: int, divisor: int) -> list[str]:
    problems = []
    exp_q, exp_r = expected(numerator, divisor)
    if (orig["quotient"], orig["remainder"]) != (exp_q, exp_r):
        problems.append(
            f"original differs from oracle: q={orig['quotient']:#x} "
            f"r={orig['remainder']:#x}, expected q={exp_q:#x} r={exp_r:#x}"
        )
    if (cand["quotient"], cand["remainder"]) != (exp_q, exp_r):
        problems.append(
            f"candidate differs from oracle: q={cand['quotient']:#x} "
            f"r={cand['remainder']:#x}, expected q={exp_q:#x} r={exp_r:#x}"
        )
    for key in ("quotient", "remainder", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_args"] != cand["call_args"]:
        problems.append(
            "0x001524E8 call arguments (r0, r1):\n    orig="
            + repr(orig["call_args"])
            + "\n    cand="
            + repr(cand["call_args"])
        )
    if bool(orig["call_args"]) != (divisor == 0):
        problems.append(
            f"unexpected divide-by-zero call count: {orig['call_args']}"
        )
    if orig["data"] != cand["data"]:
        problems.append("data page was modified differently")
    if orig["data"] != ENTRY_DATA:
        problems.append("original wrote the data page")
    if orig["outside_writes"] or cand["outside_writes"]:
        problems.append(
            "writes outside the private stack: "
            f"orig={orig['outside_writes']} cand={cand['outside_writes']}"
        )
    return problems


def make_cases() -> list[tuple[int, int]]:
    M = 1 << 64
    cases: list[tuple[int, int]] = []

    boundary_values = [
        0,
        1,
        2,
        3,
        4,
        5,
        7,
        0x7FFFFFFF,
        0x80000000,
        0xFFFFFFFF,
        0x100000000,
        0x100000001,
        0x7FFFFFFFFFFFFFFF,
        0x8000000000000000,
        0xFFFFFFFFFFFFFFFF,
    ]

    # Zero/nonzero and tiny-limb combinations (exercise div-by-zero, the
    # numerator < divisor shortcut, and the small-exponent path).
    for a in boundary_values:
        for b in boundary_values:
            cases.append((a, b))

    # Every exponent difference 0..6 with low and high divisors, including
    # exact powers of two where quotient bit alignment is easiest to get wrong.
    for diff in range(0, 7):
        d = 3
        n = d << diff
        cases.append((n, d))
        cases.append((n + 1, d))
        cases.append((n - 1, d))
        for d2 in (1, 2, 5, 0x8001, 0xFFFFFFFF, 0x80000000,
                   0x8000000000000000, 0xFFFFFFFFFFFFFFFF):
            n2 = (d2 << diff) & (M - 1)
            cases.append((n2, d2))
            cases.append(((n2 + 1) & (M - 1), d2))
            cases.append(((n2 - 1) & (M - 1), d2))

    # High divisors (> 2^63) and quotient 0/1 boundaries.
    for d in (0x8000000000000000, 0x8000000000000001, 0xFFFFFFFFFFFFFFFF,
              0xFFFFFFFFFFFFFFFE, 0xC000000000000000):
        for n in (0, 1, d - 1, d, d + 1, M - 1):
            if 0 <= n < M:
                cases.append((n, d))

    # Constructed exact and inexact q * d + r triples.
    random.seed(0x2AA504)
    for _ in range(400):
        d = random.randrange(1, M)
        q = random.randrange(0, M)
        r = random.randrange(0, d)
        n = (q * d + r) % M
        cases.append((n, d))

    # Randomized full-width pairs, including many zero-divisor draws replaced
    # by an explicit zero case above.
    for _ in range(1200):
        cases.append((random.getrandbits(64), random.getrandbits(64)))
        cases.append((random.getrandbits(64), random.getrandbits(64) & 0xFFFF))

    # Larger-quotient shapes: numerator much wider than the divisor.
    for _ in range(200):
        d = random.getrandbits(random.randrange(1, 33)) | 1
        n = random.getrandbits(64)
        cases.append((n, d))

    # Deduplicate while preserving order.
    seen = set()
    unique = []
    for case in cases:
        if case not in seen:
            seen.add(case)
            unique.append(case)
    return unique


def main() -> None:
    print("Testing script_vm_func_002aa504 (0x002aa504)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B, "
        "1 direct call relocated."
    )

    cases = make_cases()
    orig_runner = DivRunner(track_coverage=True)
    cand_runner = DivRunner()

    passed = 0
    for index, (numerator, divisor) in enumerate(cases):
        orig = orig_runner.run(orig_code, numerator, divisor)
        cand = cand_runner.run(cand_code, numerator, divisor)
        problems = compare(orig, cand, numerator, divisor)
        if problems:
            print(
                f"  [FAIL] case {index}: n=0x{numerator:016x} "
                f"d=0x{divisor:016x}"
            )
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1

    expected_pcs = set(range(FUNC_ADDR, FUNC_CODE_END, 4))
    uncovered = sorted(expected_pcs - orig_runner.coverage)
    if uncovered:
        print("  [FAIL] original instruction coverage incomplete:")
        for pc in uncovered:
            print(f"    0x{pc:08x}")
        raise SystemExit(1)

    print(
        f"  [PASS] {passed} differential cases; all {len(expected_pcs)} "
        "original instructions executed."
    )

    print("Negative controls:")
    controls = [
        ("shift_align", "u64 shifted = divisor << shift;",
         "u64 shifted = divisor >> shift;"),
        ("remainder_subtract", "remainder -= shifted;",
         "remainder += shifted;"),
        ("equal_exponent", "if (num_bits >= den_bits) {",
         "if (num_bits > den_bits) {"),
        ("divide_by_zero_args", "script_vm_func_001524e8(0, 0);",
         "script_vm_func_001524e8(0, 1);"),
        ("remainder_high_word",
         'register u32 rem_hi __asm__("r3") = '
         "static_cast<u32>(remainder >> 32);",
         'register u32 rem_hi __asm__("r3") = '
         "static_cast<u32>(remainder);"),
    ]
    control_cases = [
        (0x8000000000000000, 0x8000000000000000),   # equal exponent
        (0x0000000000000600, 3),                    # aligned divisor shift
        (0xFFFFFFFFFFFFFFFF, 2),                    # ordinary division
        (0x0000000500000003, 0x0000000300000000),   # high remainder word
        (0xDEADBEEF, 0),                            # divide-by-zero path
        (0x0123456789ABCDEF, 0x10),
    ]
    for name, old, new in controls:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for numerator, divisor in control_cases:
            orig = orig_runner.run(orig_code, numerator, divisor)
            bad = cand_runner.run(mutant_code, numerator, divisor)
            if compare(orig, bad, numerator, divisor):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
