#!/usr/bin/env python3
"""Differential test for func_002c7090 (0x002c7090) using Unicorn ARM.

Compiles ``src/engine/leaf_batch42_b.cpp``, extracts the ``func_002c7090`` body,
resolves its four direct call relocations to deterministic stubs, and runs the
pinned original (``extracted/exefs/code.bin``) against the candidate in separate
Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log, including every register argument, the s0 float
    argument of ``ui_func_001e1bb0`` and the four raw words it observes in the
    shared colour block;
  * the owner page, the whole state page (including the 0x24-byte display
    record at +0xC0) and the 0x004EA81C colour-block page (must be identical);
  * the exact bytes each ``func_00257614`` stub writes to 0x004EA91C;
  * unexpected writes outside the private stack / fixture pages.

Coverage: ``count`` zero, positive, negative and both 32-bit signed extremes;
``frame`` below, equal to, and above ``count`` (the signed ``frame > count``
early exit, including the +/-0x80000000 boundaries); both ``flag_bc`` variants;
zero, positive and negative sampler results; zero/non-zero owner scale and
colour words; and colour bytes 0x00/0xFF/0x7F. Negative controls mutate the
default span, the signed comparison, the flag selector, the colour-byte order,
one source word, the scale argument and the value word.

The four helpers are stubs, so real-helper behaviour (sampling and colour
conversion) is not exercised; see the function record for that limit.
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
SOURCE = ROOT / "src/engine/leaf_batch42_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_002c7090"

FUNC_ADDR = 0x002C7090
FUNC_SIZE = 504

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers every stub (0x1E1BB0 .. 0x2C7090)
GLOBAL_ADDR = 0x004E0000
GLOBAL_SIZE = 0x00020000  # covers 0x004EA81C
OWNER_ADDR = 0x00700000
OWNER_SIZE = 0x00010000
STATE_ADDR = 0x00710000
STATE_SIZE = 0x00010000
STACK_ADDR = 0x00800000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

COLOR_BLOCK = 0x004EA81C
COLOR_CURRENT = COLOR_BLOCK + 0x100
COLOR_PREVIOUS = COLOR_BLOCK + 0x110
GLOBAL_SNAPSHOT_ADDR = 0x004EA800
GLOBAL_SNAPSHOT_SIZE = 0x00000200

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_269768 = 0x00269768
STUB_2698F4 = 0x002698F4
STUB_257614 = 0x00257614
STUB_1E1BB0 = 0x001E1BB0

STUB_NAMES = {
    STUB_269768: "func_00269768",
    STUB_2698F4: "func_002698f4",
    STUB_257614: "func_00257614",
    STUB_1E1BB0: "ui_func_001e1bb0",
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

F32_SCALE_RECIP = 0x3B808081  # 1.0f / 255.0f literal used by 0x00257614
MASK32 = 0xFFFFFFFF


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def bits_f32(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & MASK32))[0]


def sf(value: float) -> float:
    """Round a Python double to the nearest IEEE-754 single."""
    return bits_f32(f32_bits(value))


def s32(value: int) -> int:
    value &= MASK32
    return value - 0x100000000 if value & 0x80000000 else value


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "002c7090" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"func_002c7090 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if f"{address:08x}" in rel.symbol_name:
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


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch42_b.o"
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
DEFAULT_SOURCE_WORDS = (0x11223344, 0x55667788, 0x99AABBCC, 0xDDEEFF00)


def build_owner(case: dict) -> bytes:
    page = bytearray([0x5A]) * OWNER_SIZE
    source = case.get("source_words", DEFAULT_SOURCE_WORDS)
    struct.pack_into("<4I", page, 0x00, *[word & MASK32 for word in source])
    struct.pack_into("<I", page, 0x10, case.get("color_10", 0x1A2B3C4D) & MASK32)
    struct.pack_into("<f", page, 0x14, sf(case.get("scale", 1.5)))
    struct.pack_into("<i", page, 0x1C, s32(case.get("frame", 0)))
    struct.pack_into("<I", page, 0x24, STATE_ADDR)
    return bytes(page)


def build_state(case: dict) -> bytes:
    page = bytearray([0x3C]) * STATE_SIZE
    struct.pack_into("<4B", page, 0x24, 0x11, 0x22, 0x33, 0x44)
    struct.pack_into("<I", page, 0x28, case.get("value_28", 0xC0FFEE01) & MASK32)
    struct.pack_into("<I", page, 0x8C, 0x8C5EED00)
    struct.pack_into("<I", page, 0xB8, s32(case.get("count", 16)) & MASK32)
    page[0xBC] = case.get("flag_bc", 0) & 0xFF
    # Display record at +0xC0: sentinel every field so unwritten fields differ
    # from any value the routine could legitimately produce.
    struct.pack_into("<4I", page, 0xC0, 0xDEAD0000, 0xDEAD0004, 0xDEAD0008,
                     0xDEAD000C)
    struct.pack_into("<4I", page, 0xD0, 0xDEAD0010, 0xDEAD0014, 0xDEAD0018,
                     0xDEAD001C)
    struct.pack_into("<I", page, 0xE0, 0xDEAD0020)
    return bytes(page)


def build_global(case: dict) -> bytes:
    page = bytearray([0x00]) * GLOBAL_SIZE
    base = COLOR_BLOCK - GLOBAL_ADDR
    # Distinguish the current/previous blocks so a missed write is visible.
    for index in range(8):
        struct.pack_into("<I", page, base + 0x100 + index * 4,
                         0x0BAD0000 | (index & 0xFF))
    return bytes(page)


def read_c_string(uc, address: int, limit: int = 32) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class C7090Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # The 3DS CPU is an ARM11 MPCORE; enable VFP (CP10/CP11 + FPEXC.EN).
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(OWNER_ADDR, OWNER_SIZE)
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
        self.color_writes: list = []

    # ------------------------------------------------------------------ stubs
    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_269768:
            curve_head = struct.unpack("<I", uc.mem_read(r0, 4))[0]
            self.call_log.append(
                (STUB_NAMES[address], r0, s32(r1), s32(r2), curve_head)
            )
            sample = sf(1.5 + s32(r1) * 0.25 + s32(r2) * 0.125)
            uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(sample))
        elif address == STUB_2698F4:
            self.call_log.append(
                (STUB_NAMES[address], r0, r1, s32(r2), s32(r3))
            )
            color = (
                0xA5C30000
                ^ ((r3 * 0x9E3779B1) & MASK32)
                ^ ((r2 * 0x85EBCA77) & MASK32)
                ^ ((r1 * 0xC2B2AE3D) & MASK32)
            ) & MASK32
            uc.reg_write(arm.UC_ARM_REG_R0, color)
        elif address == STUB_257614:
            self.call_log.append((STUB_NAMES[address], r0))
            reciprocal = bits_f32(F32_SCALE_RECIP)
            components = (
                (r0 >> 24) & 0xFF,
                (r0 >> 16) & 0xFF,
                (r0 >> 8) & 0xFF,
                r0 & 0xFF,
            )
            values = [sf(component * reciprocal) for component in components]
            self.color_writes.append((r0, tuple(values)))
            uc.mem_write(COLOR_CURRENT, struct.pack("<4f", *values))
        elif address == STUB_1E1BB0:
            s_value = bits_f32(uc.reg_read(arm.UC_ARM_REG_S0))
            words = struct.unpack("<4I", uc.mem_read(r0, 16))
            self.call_log.append(
                (STUB_NAMES[address], r0, f32_bits(s_value), words)
            )
            new_values = [
                sf((words[0] & 0xFFFF) * 0.25 + s_value),
                sf((words[1] & 0xFFFF) * 0.25 - s_value),
                sf(((words[2] >> 16) & 0xFFFF) * 0.5 + s_value),
                sf(((words[3] >> 16) & 0xFFFF) * 0.5 - s_value),
            ]
            uc.mem_write(r0, struct.pack("<4f", *new_values))
            radius = sf(
                s_value * 3.0 + (words[0] & 0x7) * 0.125 + 2.0
            )
            uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(radius))
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.color_writes = []

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(GLOBAL_ADDR, build_global(case))
        self.uc.mem_write(OWNER_ADDR, build_owner(case))
        self.uc.mem_write(STATE_ADDR, build_state(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OWNER_ADDR)
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
        allowed = (
            (STACK_ADDR, STACK_ADDR + STACK_SIZE),
            (OWNER_ADDR, OWNER_ADDR + OWNER_SIZE),
            (STATE_ADDR, STATE_ADDR + STATE_SIZE),
            (GLOBAL_ADDR, GLOBAL_ADDR + GLOBAL_SIZE),
        )
        for address, size, _value in self.writes:
            if not any(low <= address < high for low, high in allowed):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "color_writes": list(self.color_writes),
            "fixtures": {
                "owner": bytes(self.uc.mem_read(OWNER_ADDR, OWNER_SIZE)),
                "state": bytes(self.uc.mem_read(STATE_ADDR, STATE_SIZE)),
                "global": bytes(
                    self.uc.mem_read(GLOBAL_SNAPSHOT_ADDR, GLOBAL_SNAPSHOT_SIZE)
                ),
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
    if orig["color_writes"] != cand["color_writes"]:
        problems.append(
            "color_writes:\n    orig="
            + repr(orig["color_writes"])
            + "\n    cand="
            + repr(cand["color_writes"])
        )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} differs")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "count": 16,
        "frame": 4,
        "flag_bc": 0,
        "scale": 1.5,
        "color_10": 0x1A2B3C4D,
        "value_28": 0xC0FFEE01,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- count zero: frame is never read, both geometry variants
    cases.append(base_case("count 0 flag 0", count=0, frame=0x12345678, flag_bc=0))
    cases.append(base_case("count 0 flag 1", count=0, frame=0x12345678, flag_bc=1))

    # --- frame vs count signed boundaries (frame > count early exit)
    for count, frame in (
        (16, 0),
        (16, 15),
        (16, 16),
        (16, 17),
        (-5, -6),
        (-5, -5),
        (-5, -4),
        (0x7FFFFFFF, 0x7FFFFFFF),
        (0x7FFFFFFF, 0x80000000),
        (0x80000000, 0x7FFFFFFF),
        (0x80000000, 0x80000000),
        (1, -1),
        (-1, 1),
    ):
        for flag in (0, 1):
            cases.append(
                base_case(
                    f"count {count} frame {frame} flag {flag}",
                    count=count,
                    frame=frame,
                    flag_bc=flag,
                )
            )

    # --- sampler result magnitudes and geometry (default path)
    for count, frame, flag in (
        (0, 0, 1),
        (-8, -8, 1),
        (40, 40, 1),
        (0xFFFFFFFF, 0xFFFFFFFF, 0),  # count -1
        (0x7FFFFFFF, 0x7FFFFFFF, 1),
    ):
        cases.append(
            base_case(
                f"sample sweep count {count} frame {frame} flag {flag}",
                count=count,
                frame=frame,
                flag_bc=flag,
            )
        )

    # --- owner-sourced geometry: scale and raw colour words
    for scale in (0.0, 1.0, -1.0, 2.5, 1e-8, 1e8):
        cases.append(
            base_case(f"owner scale {scale!r}", scale=scale, flag_bc=0,
                      count=20, frame=20)
        )
    for words in (
        (0x00000000, 0x00000000, 0x00000000, 0x00000000),
        (0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF),
        (0x0000FFFF, 0x7FFF8000, 0x80000000, 0xFFFF0000),
        (0x3F800000, 0x40000000, 0xBF800000, 0x00000001),
    ):
        cases.append(
            base_case(f"source words {words!r}", source_words=words,
                      flag_bc=0, count=3, frame=3)
        )

    # --- colour packing: each byte extreme through the 0x00257614 stub
    for color in (
        0x00000000,
        0xFFFFFFFF,
        0xFF000000,
        0x00FF0000,
        0x0000FF00,
        0x000000FF,
        0x7F7F7F7F,
        0x01020304,
    ):
        cases.append(base_case(f"color 0x{color:08x}", color_10=color))
        cases.append(base_case(f"color 0x{color:08x} flag 1", color_10=color,
                               flag_bc=1))

    # --- value word copied to display +0x10
    for value in (0x00000000, 0xFFFFFFFF, 0x80000000, 0x0000FFFF):
        cases.append(base_case(f"value 0x{value:08x}", value_28=value))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = C7090Runner().run(orig_code, case)
        cand = C7090Runner().run(cand_code, case)
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
    print("Testing func_002c7090 (0x002c7090)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          "(relocations resolved).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("default_span_x", "constexpr f32 kDefaultSpanX = 200.0f;",
         "constexpr f32 kDefaultSpanX = 201.0f;"),
        ("signed_comparison", "if (frame > count) {", "if (frame >= count) {"),
        ("flag_selector", "if (state->flag_bc != 0) {",
         "if (state->flag_bc == 0) {"),
        ("color_byte_order", "color_bytes[0] = static_cast<u8>(scaled3);",
         "color_bytes[0] = static_cast<u8>(scaled2);"),
        ("source_word_one", "block[1] = owner->color_source_00[1];",
         "block[1] = owner->color_source_00[0];"),
        ("scale_argument", "ui_func_001e1bb0(block, owner->scale_14 * sample)",
         "ui_func_001e1bb0(block, owner->scale_14 + sample)"),
        ("value_word", "display->value_10 = state->value_28;",
         "display->value_10 = state->value_28 + 1;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = C7090Runner().run(orig_code, case)
            bad = C7090Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
