#!/usr/bin/env python3
"""Differential test for func_003dff3c (0x003dff3c) using Unicorn ARM.

The routine packs a fixed rendering record from a source structure and, when
``submit`` is non-zero, forwards it to the shared continuation at 0x0022673C.
The recovered contract is documented next to the C++ in
``src/engine/leaf_batch41_c.cpp``.

The runner compiles ``src/engine/leaf_batch41_c.cpp``, extracts the
``func_003dff3c`` body, resolves its single R_ARM_JUMP24/R_ARM_CALL relocation
to a deterministic stub at 0x0022673C, and runs the pinned original
(``extracted/exefs/code.bin``) against the candidate in separate Unicorn
machines with identical fixtures (CP10/CP11 enabled through C1_C0_2/FPEXC).

Compared per case:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered tail-call log with the exact pointer, cursor and mode;
  * the full 64 KiB output page (seeded with a deterministic pattern so
    unwritten words and any stray byte store are visible), the full source
    page;
  * every emulated write outside the output page and the private stack.

FPSCR is captured for diagnostics but deliberately not compared.  The
original performs exactly one VFP comparison (the gate on the +0x04 value),
while Clang also lowers the integer zero test inside the binary16 helper to
`vcmp.f32` and speculates the out-of-range `vcvt` onto the saturating path.
Those instructions overwrite FPSCR[31:28] and can set FPSCR.IOC even though
the original skips them, so FPSCR is not reproducible from equivalent C++
without encoding the compiler's instruction selection.  FPSCR is neither an
input nor an output of the recovered contract and no caller consumes it.

Coverage:
  * the byte-0 gate: zero and non-zero, on both submit paths;
  * ``submit`` = 0, 1, 2 and 0xFFFFFFFF; ``extra`` = 0, 1, 0x80, 0x80000000
    and 0xFFFFFFFF, including the gate=0 case where extra is ignored;
  * ``object[1]`` = 0, 1, 0x7F, 0x80 and 0xFF (bit-0 substitution);
  * the 24-bit conversion: +0, -0, denormals, 2^-24/2^-25, 0.5, the largest
    float below 1.0, 1.0, 2.0, 2^24-1, 2^24, 1e30, 3.4e38, negatives,
    +inf, -inf, qNaN, sNaN and negative NaN;
  * the binary16 pair: +-0, 2^-15 and neighbours, 2^-14, 1.0, +-inf, NaN
    with distinct payloads, 2^17, -2^17, 2^31, 3.4e38, and sums that cancel
    or overflow to infinity;
  * the pointer word 0, ordinary page values, and two addresses whose +0x7C
    bias wraps around 32 bits.

Negative controls recompile mutated source (all fixed words, the scale, the
saturation constant, the bit-0 mask, the half mantissa mask/bias, every
source offset and the tail bias); each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_003dff3c"

FUNC_NAME = "func_003dff3c"
FUNC_ADDR = 0x003DFF3C
FUNC_SIZE = 400
CONTINUATION = 0x0022673C

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00300000  # function plus the continuation stub
DATA_ADDR = 0x00700000
DATA_SIZE = 0x00010000
OUT_ADDR = 0x00710000
OUT_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

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

PATTERN_FIXED_VALUE = 291.3125  # 0x123.5
PATTERN_UNUSED_VALUE = -777.25
PATTERN_SECOND_VALUE = 1.5
PATTERN_THIRD_VALUE = 2.25
PATTERN_POINTER = 0x00731000


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def bits_f32(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    entry = funcs.get(FUNC_NAME)
    if entry is None:
        raise RuntimeError(
            f"{FUNC_NAME} not found in {obj_file}: {sorted(funcs)}"
        )

    raw, relocs = entry
    code = bytearray(raw)
    if len(relocs) != 1:
        raise RuntimeError(f"expected exactly one relocation, got {relocs!r}")
    rel = relocs[0]
    if rel.relocation_type not in (28, 29):
        raise RuntimeError(f"unexpected relocation type {rel.relocation_type}")
    if "0022673c" not in rel.symbol_name:
        raise RuntimeError(f"unexpected call target {rel.symbol_name!r}")

    pc = FUNC_ADDR + rel.offset + 8
    displacement = (CONTINUATION - pc) >> 2
    original = struct.unpack_from("<I", code, rel.offset)[0]
    cond = original & 0xFF000000
    struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
    return bytes(code)


def compile_variant(src_file: Path, out_obj: Path) -> bytes:
    res = compile_tu_armv6k(src_file, out_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(out_obj)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return compile_variant(SOURCE, OUT_DIR / "leaf_batch41_c.o")


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_variant(mutant_src, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def build_source(case: dict) -> bytes:
    page = bytearray(((i * 7 + 3) & 0xFF) for i in range(DATA_SIZE))
    page[0] = case.get("gate", 1) & 0xFF
    page[1] = case.get("half_flag", 0) & 0xFF
    struct.pack_into("<I", page, 4, case.get("fixed", f32_bits(PATTERN_FIXED_VALUE)))
    struct.pack_into("<I", page, 8, case.get("unused", f32_bits(PATTERN_UNUSED_VALUE)))
    struct.pack_into(
        "<I", page, 0xC, case.get("second", f32_bits(PATTERN_SECOND_VALUE))
    )
    struct.pack_into(
        "<I", page, 0x10, case.get("third", f32_bits(PATTERN_THIRD_VALUE))
    )
    struct.pack_into("<I", page, 0x14, case.get("pointer", PATTERN_POINTER))
    return bytes(page)


def build_output() -> bytes:
    return bytes(((i * 11 + 5) & 0xFF) for i in range(OUT_SIZE))


class Runner:
    """One Unicorn machine with a deterministic continuation stub."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # The original uses VFP for every float field; enable CP10/CP11.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (DATA_ADDR, DATA_SIZE),
            (OUT_ADDR, OUT_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)

        self.uc.mem_write(CONTINUATION, struct.pack("<I", 0xE12FFF1E))  # bx lr
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE,
            self._on_continuation,
            begin=CONTINUATION,
            end=CONTINUATION,
        )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []

    # -- stub -------------------------------------------------------------
    def _on_continuation(self, uc, address, size, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        self.call_log.append(("func_0022673c", r0, r1, r2))
        # Observable side effect keyed on the two pointer arguments so a wrong
        # cursor or continuation address cannot compare equal.
        marker = (r0 * 33 ^ (r2 << 16) ^ 0xDEADBEEF) & 0xFFFFFFFF
        uc.mem_write(r1, struct.pack("<I", marker))
        uc.reg_write(
            arm.UC_ARM_REG_R0, (r0 * 33 ^ (r2 << 16) ^ 0x5A5A5A5A) & 0xFFFFFFFF
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value & ((1 << (8 * size)) - 1)))

    # -- execution --------------------------------------------------------
    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for name, r0, r1, r2 in log:
            out = [r0, r2]
            out.append("<stack>" if STACK_ADDR <= r1 < STACK_ADDR + STACK_SIZE else r1)
            normalised.append((name, tuple(out)))
        return normalised

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DATA_ADDR, build_source(case))
        self.uc.mem_write(OUT_ADDR, build_output())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.reg_write(arm.UC_ARM_REG_FPSCR, 0)
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, DATA_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, OUT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("submit", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("extra", 0) & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_out = OUT_ADDR <= address < OUT_ADDR + OUT_SIZE
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not (in_out or in_stack):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "fpscr": self.uc.reg_read(arm.UC_ARM_REG_FPSCR),
            "float_scratch": [
                self.uc.reg_read(arm.UC_ARM_REG_S0 + index) for index in range(4)
            ],
            "output": bytes(self.uc.mem_read(OUT_ADDR, OUT_SIZE)),
            "source": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    # FPSCR/float_scratch are recorded in the result but not compared; see the
    # module docstring for why the compiler cannot preserve them.
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
    if orig["output"] != cand["output"]:
        problems.append("output page differs")
    if orig["source"] != cand["source"]:
        problems.append("source page was modified")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "gate": 1,
        "half_flag": 0,
        "submit": 0,
        "extra": 0,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- gate / submit / extra combinations
    for gate in (0, 1, 0xFF):
        for submit in (0, 1, 2, 0xFFFFFFFF):
            for extra in (0, 1, 0x80, 0x80000000, 0xFFFFFFFF):
                cases.append(
                    base_case(
                        f"gate {gate} submit 0x{submit:08x} extra 0x{extra:08x}",
                        gate=gate,
                        submit=submit,
                        extra=extra,
                    )
                )

    # --- bit-0 substitution from object[1]
    for half_flag in (0x00, 0x01, 0x02, 0x7F, 0x80, 0xFF):
        cases.append(
            base_case(
                f"half flag byte 0x{half_flag:02x}",
                half_flag=half_flag,
                fixed=f32_bits(0.5),
            )
        )
        cases.append(
            base_case(
                f"half flag byte 0x{half_flag:02x} submit",
                half_flag=half_flag,
                submit=1,
                extra=1,
            )
        )

    # --- 24-bit fixed-point conversion boundaries
    fixed_values = {
        "plus zero": 0x00000000,
        "minus zero": 0x80000000,
        "min denormal": 0x00000001,
        "max denormal": 0x007FFFFF,
        "2^-30": f32_bits(2.0**-30),
        "2^-25": f32_bits(2.0**-25),
        "2^-24": f32_bits(2.0**-24),
        "3*2^-24": f32_bits(3.0 * 2.0**-24),
        "5*2^-24": f32_bits(5.0 * 2.0**-24),
        "2^-24 - 2^-48": f32_bits(2.0**-24 - 2.0**-48),
        "0.5": f32_bits(0.5),
        "0.75": f32_bits(0.75),
        "largest below 1": 0x3F7FFFFF,
        "one": f32_bits(1.0),
        "one plus ulp": 0x3F800001,
        "2.0": f32_bits(2.0),
        "2^24 - 1": f32_bits(16777215.0),
        "2^24": f32_bits(16777216.0),
        "1e30": f32_bits(1e30),
        "max finite": 0x7F7FFFFF,
        "minus one": f32_bits(-1.0),
        "minus tiny": 0x80000001,
        "plus inf": 0x7F800000,
        "minus inf": 0xFF800000,
        "qNaN": 0x7FC00000,
        "sNaN": 0x7F800001,
        "negative NaN": 0xFFC00000,
    }
    for name, bits in fixed_values.items():
        cases.append(
            base_case(
                f"fixed {name} (0x{bits:08x})",
                fixed=bits,
                second=f32_bits(1.0),
                third=f32_bits(1.0),
            )
        )

    # --- binary16 pair boundaries (fixed value kept simple)
    half_values = {
        "both zero": (0x00000000, 0x00000000),
        "negative zero pair": (0x80000000, 0x80000000),
        "zero plus negative zero": (0x00000000, 0x80000000),
        "negative zero plus zero": (0x80000000, 0x00000000),
        "2^-15": (f32_bits(2.0**-15), 0x00000000),
        "2^-15 * 1.5": (0x38400000, 0x00000000),
        "just below 2^-15": (0x37FFFFFF, 0x00000000),
        "2^-14": (f32_bits(2.0**-14), 0x00000000),
        "min denormal": (0x00000001, 0x00000000),
        "1.0 and 1.0": (f32_bits(1.0), f32_bits(1.0)),
        "1.0 and -1.0": (f32_bits(1.0), f32_bits(-1.0)),
        "2^17": (f32_bits(2.0**17), 0x00000000),
        "minus 2^17": (f32_bits(-(2.0**17)), 0x00000000),
        "2^31": (f32_bits(2.0**31), 0x00000000),
        "minus 2^31": (f32_bits(-(2.0**31)), 0x00000000),
        "max finite": (0x7F7FFFFF, 0x00000000),
        "plus inf": (0x7F800000, 0x00000000),
        "minus inf": (0xFF800000, 0x00000000),
        "inf plus inf": (0x7F800000, 0x7F800000),
        "inf minus inf": (0x7F800000, 0xFF800000),
        "qNaN first": (0x7FC00000, 0x00000000),
        "qNaN second": (0x00000000, 0x7FC02345),
        "distinct NaNs": (0x7FC00001, 0x7FC00002),
        "distinct NaNs reversed": (0x7FC00002, 0x7FC00001),
        "sNaN first": (0x7F800001, 0x00000000),
        "cancel to zero": (f32_bits(1e38), f32_bits(-1e38)),
        "overflow to inf": (f32_bits(1e38), f32_bits(1e38)),
    }
    for name, (second, third) in half_values.items():
        cases.append(
            base_case(
                f"halves {name}",
                fixed=f32_bits(0.5),
                second=second,
                third=third,
            )
        )
        cases.append(
            base_case(
                f"halves {name} submit",
                fixed=f32_bits(0.25),
                second=second,
                third=third,
                submit=1,
                extra=1,
                half_flag=0x80,
            )
        )

    # --- pointer word and +0x7C bias wrap-around
    for pointer in (
        0x00000000,
        0x00000001,
        PATTERN_POINTER,
        0xFFFFF000,
        0xFFFFFF84,
        0xFFFFFF90,
        0xFFFFFFFF,
    ):
        cases.append(
            base_case(
                f"pointer 0x{pointer:08x}",
                pointer=pointer,
                submit=1,
            )
        )
        cases.append(
            base_case(
                f"pointer 0x{pointer:08x} gated off",
                pointer=pointer,
                submit=1,
                gate=0,
            )
        )

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
    return passed


def main() -> None:
    print("Testing func_003dff3c (0x003dff3c)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocation resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)
    print(f"  [PASS] {passed} differential cases")

    print("\nNegative controls:")
    mutants = (
        ("header_word0", "constexpr u32 kHeaderWord0 = 0x00E40103;",
         "constexpr u32 kHeaderWord0 = 0x00E40102;"),
        ("header_word1", "constexpr u32 kHeaderWord1 = 0x00010100;",
         "constexpr u32 kHeaderWord1 = 0x00010101;"),
        ("extra_word", "constexpr u32 kExtraWord = 0x00200080;",
         "constexpr u32 kExtraWord = 0x00200081;"),
        ("fixed_word0", "constexpr u32 kFixedWord0 = 0x000F008B;",
         "constexpr u32 kFixedWord0 = 0x000F008A;"),
        ("fixed_word1", "constexpr u32 kFixedWord1 = 0x000F0130;",
         "constexpr u32 kFixedWord1 = 0x000F0131;"),
        ("fixed_scale", "constexpr f32 kFixedScale = 16777216.0f;",
         "constexpr f32 kFixedScale = 8388608.0f;"),
        ("fixed_saturated", "constexpr u32 kFixedSaturated = 0x00FFFFFFu;",
         "constexpr u32 kFixedSaturated = 0x00FFFFF7u;"),
        ("fixed_mask", "constexpr u32 kFixedMask = ~1u;",
         "constexpr u32 kFixedMask = ~3u;"),
        ("half_mantissa_mask",
         "constexpr u32 kHalfMantissaMask = 0x3FFu;",
         "constexpr u32 kHalfMantissaMask = 0x1FFu;"),
        ("half_bias", "constexpr u32 kHalfBias = 0x70;",
         "constexpr u32 kHalfBias = 0x71;"),
        ("gate_byte", "constexpr u32 kGateByte = 0x00;",
         "constexpr u32 kGateByte = 0x02;"),
        ("half_flag_byte", "constexpr u32 kHalfFlagByte = 0x01;",
         "constexpr u32 kHalfFlagByte = 0x02;"),
        ("fixed_value_offset", "constexpr u32 kFixedValue = 0x04;",
         "constexpr u32 kFixedValue = 0x08;"),
        ("second_value_offset", "constexpr u32 kSecondValue = 0x0C;",
         "constexpr u32 kSecondValue = 0x08;"),
        ("third_value_offset", "constexpr u32 kThirdValue = 0x10;",
         "constexpr u32 kThirdValue = 0x14;"),
        ("object_pointer_offset", "constexpr u32 kObjectPointer = 0x14;",
         "constexpr u32 kObjectPointer = 0x18;"),
        ("tail_bias", "constexpr u32 kTailBias = 0x7C;",
         "constexpr u32 kTailBias = 0x78;"),
    )
    for name, old, new in mutants:
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
