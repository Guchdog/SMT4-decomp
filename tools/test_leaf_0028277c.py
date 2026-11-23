#!/usr/bin/env python3
"""Differential test for script_vm_func_0028277c (0x0028277c), a sinf clone.

The pinned original is a 456-byte libm-style ``sinf``:

  * |x| < pi/4 is evaluated directly with a minimax polynomial; a quadrant
    marker of -1 is produced when |x| < 2**-12 so the value is returned
    unchanged;
  * pi/4 <= |x| < 12867.5712890625 is reduced inline with the 2**23
    round-to-nearest trick and a four-part pi/2 constant;
  * anything larger (and every non-finite value) goes through the generic
    0x003EB4F4 reduction helper, which reports the quadrant through its
    out-pointer;
  * quadrant 0/1/2/3 returns sin(r)/cos(r)/-sin(r)/-cos(r);
  * zero and subnormals run the discarded 0x002A462C underflow probe,
    infinities store EDOM through the Thumb 0x002A464E helper and return the
    VFP default NaN (0/0), and NaN propagates through x + x.

The test compiles the candidate translation unit, relocates its four direct
calls to deterministic stubs placed at the pinned addresses, and runs the
pinned original against the candidate in separate Unicorn machines with
identical fixtures.

Compared outputs:
  * returned s0 bit pattern, continuation PC, final SP, callee-saved r4-r11
    and the callee-saved d8 (s16);
  * the ordered call log with the semantically live arguments of each helper
    (the reduction out-pointer is normalised to "<stack>");
  * every emulated write outside the private stack (must be none, and equal).

Coverage: each polynomial quadrant, the pi/4 and 2**-12 fast-path boundaries
from both sides, the 12867.5712890625 generic-reduction boundary, the four
inline quadrants for positive and negative x, every helper quadrant encoding
including the 0x10000000-n form, signed zeros, subnormals, tiny normals,
+/-infinity and quiet/signalling NaNs.  Negative controls mutate the
subnormal-probe condition, one sine coefficient, the cosine negation and the
generic-reduction threshold.
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
SOURCE = ROOT / "src/engine/leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_0028277c"

FUNC_ADDR = 0x0028277C
FUNC_SIZE = 456

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and all four helper stubs
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_CLASSIFY = 0x002A4600
STUB_UNDERFLOW = 0x002A462C
STUB_ERRNO = 0x002A464E
STUB_REDUCE = 0x003EB4F4

# 0x002A464E is Thumb code in the pinned image (reached with `blx`).
THUMB_STUBS = {STUB_ERRNO}

STUB_NAMES = {
    STUB_CLASSIFY: "ui_func_002a4600",
    STUB_UNDERFLOW: "ui_func_002a462c",
    STUB_ERRNO: "func_002a464e_errno_set",
    STUB_REDUCE: "ui_func_003eb4f4",
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
D8_START = 0x1122334455667788


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def bits_f32(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    functions = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in functions.items():
        if "0028277c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"script_vm_func_0028277c not found in {obj_file}: {sorted(functions)}"
        )

    code_raw, relocations = candidate
    code = bytearray(code_raw)
    seen: list[int] = []
    for rel in relocations:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if name == rel.symbol_name or f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        seen.append(target)

        pc = FUNC_ADDR + rel.offset + 8
        offset = target - pc
        if target in THUMB_STUBS:
            # BLX (immediate): cond=1111 101H, H = bit 1 of the offset.
            if offset & 1:
                raise RuntimeError(f"odd Thumb call target 0x{target:08x}")
            instruction = (
                0xFA000000
                | ((offset >> 2) & 0x00FFFFFF)
                | ((offset & 2) << 23)
            )
        else:
            displacement = offset >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            instruction = cond | (displacement & 0x00FFFFFF)
        struct.pack_into("<I", code, rel.offset, instruction)

    expected = set(STUB_NAMES)
    if set(seen) != expected:
        raise RuntimeError(
            f"candidate calls {sorted(seen)} but the pinned function calls "
            f"{sorted(expected)}"
        )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_b.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def classify_bits(bits: int) -> int:
    """Replicates the pinned 0x002A4600 classifier exactly."""
    shifted = (bits << 1) & 0xFFFFFFFF
    value = 0
    if ((shifted << 8) & 0xFFFFFFFF) != 0:
        value = 4
    if (shifted >> 24) != 0:
        value |= 1
    if (0xFF000000 & (~shifted & 0xFFFFFFFF)) == 0:
        value |= 2
    if value == 1:
        value = 5
    return value


def normalise(address: int):
    if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
        return "<stack>"
    return address


class SinRunner:
    """One Unicorn machine with deterministic stubs at the pinned addresses."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        # Enable the VFP coprocessor (CP10/CP11) and the floating-point unit.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        for address in STUB_NAMES:
            if address in THUMB_STUBS:
                self.uc.mem_write(address, struct.pack("<H", 0x4770))
            else:
                self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        s0 = uc.reg_read(arm.UC_ARM_REG_S0)
        if address == STUB_CLASSIFY:
            bits = uc.reg_read(arm.UC_ARM_REG_R0)
            self.call_log.append((STUB_NAMES[address], (bits,)))
            uc.reg_write(arm.UC_ARM_REG_R0, classify_bits(bits))
        elif address == STUB_UNDERFLOW:
            self.call_log.append((STUB_NAMES[address], (s0,)))
        elif address == STUB_ERRNO:
            value = uc.reg_read(arm.UC_ARM_REG_R0)
            self.call_log.append((STUB_NAMES[address], (value,)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_REDUCE:
            out_pointer = uc.reg_read(arm.UC_ARM_REG_R0)
            bits = uc.reg_read(arm.UC_ARM_REG_R1)
            self.call_log.append(
                (STUB_NAMES[address], (normalise(out_pointer), bits))
            )
            magnitude = (bits << 1) & 0xFFFFFFFF
            if magnitude >= 0xFF000000:
                # Non-finite: report -1 and leave s0 as the incoming value.
                out_value = 0xFFFFFFFF
                result = s0
            else:
                out_value = self.case.get("reduce_out", 0) & 0xFFFFFFFF
                result = self.case.get("reduce_bits", 0x3F000000) & 0xFFFFFFFF
            uc.mem_write(out_pointer, struct.pack("<I", out_value))
            uc.reg_write(arm.UC_ARM_REG_S0, result)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0)
        self.uc.reg_write(arm.UC_ARM_REG_S0, case["bits"] & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        self.uc.reg_write(arm.UC_ARM_REG_D8, D8_START)
        self.writes = []

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE):
                unexpected_writes.append((address, size))

        return {
            "ret_s0": self.uc.reg_read(arm.UC_ARM_REG_S0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "d8": self.uc.reg_read(arm.UC_ARM_REG_D8),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret_s0", "pc", "sp", "d8", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}: orig={orig[key]!r} cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"])
            + "\n    cand=" + repr(cand["call_log"])
        )
    if orig["unexpected_writes"] != cand["unexpected_writes"]:
        problems.append(
            "unexpected_writes: orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


# Handy bit patterns.
PI_4 = 0x3F490FDB            # 0.7853981634f
JUST_BELOW_PI_4 = 0x3F490FDA
TWO_M12 = 0x39800000        # 2**-12
JUST_BELOW_TWO_M12 = 0x397FFFFF
REDUCTION_LIMIT = 0x46490E49
JUST_BELOW_LIMIT = 0x46490E48
POS_INF = 0x7F800000
NEG_INF = 0xFF800000
QNAN = 0x7FC00000
NEG_QNAN = 0xFFC00000
SNAN = 0x7F800001


def make_cases() -> list[dict]:
    cases: list[dict] = []

    def add(name: str, bits: int, **overrides) -> None:
        case = {"name": name, "bits": bits}
        case.update(overrides)
        cases.append(case)

    # --- direct polynomial path, |x| in [2**-12, pi/4)
    for bits in (
        0x00000000, 0x80000000,          # +/- zero (tiny path)
        TWO_M12, TWO_M12 + 1,
        JUST_BELOW_TWO_M12,
        0x3A83126F, 0xBA83126F,          # +/- 0.001
        0x3DCCCCCD, 0xBDCCCCCD,          # +/- 0.1
        0x3E800000, 0xBE800000,          # +/- 0.25
        0x3F000000, 0xBF000000,          # +/- 0.5
        0x3F400000, 0xBF400000,          # +/- 0.75
        JUST_BELOW_PI_4, 0xBF490FDA,
        0x3F490FD9,
    ):
        add(f"fast x=0x{bits:08x}", bits)

    # --- tiny inputs (quadrant marker -1, probe only for zero/subnormal)
    for bits in (
        0x00000001, 0x80000001,          # smallest subnormals
        0x0000FFFF, 0x007FFFFF,          # subnormals -> probe
        0x00800000, 0x80800000,          # min normal -> no probe
        0x397FFFFE, 0xB97FFFFE,
        0x397FFFFF, 0xB97FFFFF,
    ):
        add(f"tiny x=0x{bits:08x}", bits)

    # --- inline range reduction, pi/4 <= |x| < 12867.5712890625
    inline = (
        0x3F490FDB, 0x3F800000, 0x40000000, 0x40400000, 0x40800000,
        0x40A00000, 0x40C00000, 0x40E00000, 0x41200000, 0x42C80000,
        0x447A0000, 0x461C4000, JUST_BELOW_LIMIT,
    )
    for bits in inline:
        add(f"inline x=0x{bits:08x}", bits)
        add(f"inline x=-0x{bits & 0x7FFFFFFF:08x}", bits | 0x80000000)

    # --- generic reduction helper, every quadrant encoding
    reduce_encodings = (0, 1, 2, 3, 0x10000000, 0x10000000 - 1,
                        0x10000000 - 2, 0x10000000 - 3, 0x0FFFFFFD)
    reduce_inputs = (REDUCTION_LIMIT, 0x46500000, 0x4B000000, 0x7F7FFFFF,
                     0xFF7FFFFF)
    for index, out_value in enumerate(reduce_encodings):
        bits = reduce_inputs[index % len(reduce_inputs)]
        result_bits = 0x3F000000 if index % 2 == 0 else 0xBF000000
        add(
            f"reduce x=0x{bits:08x} out=0x{out_value:08x}",
            bits,
            reduce_out=out_value,
            reduce_bits=result_bits,
        )

    # --- non-finite values, all forced through 0x003EB4F4
    add("+infinity", POS_INF)
    add("-infinity", NEG_INF)
    add("quiet NaN", QNAN)
    add("negative quiet NaN", NEG_QNAN)
    add("signalling NaN", SNAN)
    add("max NaN payload", 0x7FFFFFFF)
    add("negative max NaN payload", 0xFFFFFFFF)

    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases) -> int:
    passed = 0
    for case in cases:
        orig = SinRunner().run(orig_code, case)
        cand = SinRunner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(
            f"  [PASS] {case['name']}  ret=0x{orig['ret_s0']:08x} "
            f"calls={len(orig['call_log'])}"
        )
    return passed


def main() -> None:
    print("Testing script_vm_func_0028277c (0x0028277c)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        (
            "subnormal_probe_condition",
            "        if (magnitude == kInfinityShift) {\n"
            "            (void)func_002a464e_errno_set(1);  // *__errno_location() = EDOM\n"
            "            volatile f32 zero = 0.0f;\n"
            "            return zero / zero;  // VFP default NaN\n"
            "        }\n"
            "        if (ui_func_002a4600(F32ToBits(reduced)) == 4u) {",
            "        if (magnitude == kInfinityShift) {\n"
            "            (void)func_002a464e_errno_set(1);  // *__errno_location() = EDOM\n"
            "            volatile f32 zero = 0.0f;\n"
            "            return zero / zero;  // VFP default NaN\n"
            "        }\n"
            "        if (ui_func_002a4600(F32ToBits(reduced)) <= 4u) {",
        ),
        (
            "sine_accumulation",
            "    poly = kSinC2 + square * poly;",
            "    poly = kSinC2 - square * poly;",
        ),
        (
            "cosine_negation",
            "            cosine = -cosine;",
            "            cosine = cosine;",
        ),
        (
            "generic_reduction_threshold",
            "constexpr u32 kReductionLimit = 0x46490E49u;   // bits of 12867.5712890625f",
            "constexpr u32 kReductionLimit = 0x46490E4Au;   // bits of 12867.5712890625f",
        ),
    )
    for name, old, new in mutants:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = SinRunner().run(orig_code, case)
            bad = SinRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        if not detected:
            raise AssertionError(f"negative control failed: {name} was not detected")
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
