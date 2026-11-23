#!/usr/bin/env python3
"""Differential test for engine_func_0012fbf4 (0x0012FBF4) using Unicorn ARM.

The routine only touches its r0 object and makes two external calls:

  * camp_func_002b9cf8 (0x002B9CF8), the single-precision powf helper, is
    called twice with s0 = 10.0f and s1 = the computed exponent.  The log
    records both operand bit patterns and a deterministic stand-in result is
    returned in s0.
  * engine_func_002c3b48 (0x002C3B48), the requested-size zero-fill helper,
    is tail-called with r0 = self[+0x30] and r1 = self[+0x34].

Original and candidate are executed on identical fixtures.  The harness
compares return value, PC, SP, callee-saved core/VFP registers, the ordered
call log (arguments and operand bits) and the observable memory (the object,
the zero-fill window and the untouched stack above the entry SP).
"""

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
FUNC_ADDR = 0x0012FBF4
FUNC_SIZE = 464
SYMBOL = "engine_func_0012fbf4"
SOURCE = ROOT / "src/engine/leaf_batch45_b.cpp"

STUB_POW = 0x002B9CF8
STUB_MEMZERO = 0x002C3B48

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers 0x0012FBF4 and both helper addresses
OBJECT_ADDR = 0x00500000
OBJECT_SIZE = 0x00001000
FILL_ADDR = 0x00600000
FILL_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

SENTINEL = 0xAA
ZERO_FILL = b"\x00" * FILL_SIZE


def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        data = f.read(FUNC_SIZE)
    assert len(data) == FUNC_SIZE
    return data


def compile_candidate():
    out_dir = ROOT / "build/test_leaf_0012fbf4"
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_file = out_dir / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}")

    funcs = extract_elf_functions_detailed(obj_file)
    matches = [k for k in funcs if SYMBOL in k]
    if not matches:
        raise RuntimeError(f"{SYMBOL} missing from {obj_file}: {sorted(funcs)}")
    code_raw, relocs = funcs[matches[0]]
    code = bytearray(code_raw)
    if len(code) != FUNC_SIZE:
        raise RuntimeError(f"candidate size {len(code)} != {FUNC_SIZE}")

    for rel in relocs:
        off = rel.offset
        sym = rel.symbol_name
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            if "002b9cf8" in sym:
                target = STUB_POW
            elif "002c3b48" in sym:
                target = STUB_MEMZERO
            else:
                raise RuntimeError(f"unexpected call relocation to {sym}")
            pc = FUNC_ADDR + off + 8
            disp = (target - pc) >> 2
            orig_inst = struct.unpack_from("<I", code, off)[0]
            struct.pack_into("<I", code, off, (orig_inst & 0xFF000000) | (disp & 0x00FFFFFF))
        else:
            raise RuntimeError(f"unexpected relocation type {rel.relocation_type} ({sym})")
    return bytes(code)


def results_for_exponent(exp_bits):
    """Deterministic powf stand-in keyed on the exponent bit pattern.

    Exact +0.0f returns a value large enough that (s32)(result * 128) is out of
    range, exercising the VFP conversion's out-of-range result.  Infinities and
    NaNs propagate their class through the multiply.  Everything else maps into
    [1, 2) from the exponent mantissa.
    """
    magnitude = exp_bits & 0x7FFFFFFF
    if magnitude > 0x7F800000:
        return 0x7FC00000  # quiet NaN
    if magnitude == 0x7F800000:
        return 0x7F800000  # +/- infinity
    if exp_bits == 0x00000000:
        return 0x4E800000  # 2^29, result * 128 saturates s32
    return 0x3F800000 | (exp_bits & 0x007FFFFF)


class Runner:
    def __init__(self):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(OBJECT_ADDR, OBJECT_SIZE)
        self.uc.mem_map(FILL_ADDR, FILL_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.call_log = []

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for addr, hook in ((STUB_POW, self._on_pow), (STUB_MEMZERO, self._on_memzero)):
            self.uc.mem_write(addr, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, hook, begin=addr, end=addr)

        # Enable the VFP coprocessor (CP10/CP11) and the floating-point unit.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.reg_write(arm.UC_ARM_REG_FPSCR, 0)

    def _on_pow(self, uc, address, size, user_data):
        base = uc.reg_read(arm.UC_ARM_REG_S0)
        exponent = uc.reg_read(arm.UC_ARM_REG_S1)
        self.call_log.append(("powf", base, exponent))
        uc.reg_write(arm.UC_ARM_REG_S0, results_for_exponent(exponent))

    def _on_memzero(self, uc, address, size, user_data):
        dst = uc.reg_read(arm.UC_ARM_REG_R0)
        length = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("memzero", dst, length))
        if dst == 0 or length == 0:
            return
        try:
            uc.mem_write(dst, b"\x00" * length)
        except Exception:
            pass  # out-of-range fixtures are logged but not stored

    def run(self, code, object_image):
        self.call_log = []
        self.uc.mem_write(FUNC_ADDR, code)
        # The same runner executes the original and then the candidate at the
        # same address; drop translated blocks so the new bytes are decoded.
        self.uc.ctl_flush_tb()
        self.uc.mem_write(OBJECT_ADDR, object_image + bytes([SENTINEL]) * (0x400 - len(object_image)))
        self.uc.mem_write(FILL_ADDR, bytes([SENTINEL]) * FILL_SIZE)
        self.uc.mem_write(STACK_ADDR, bytes([SENTINEL]) * STACK_SIZE)

        sp = STACK_ADDR + STACK_SIZE - 0x100
        self.uc.reg_write(arm.UC_ARM_REG_SP, sp)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJECT_ADDR)
        for reg, value in (
            (arm.UC_ARM_REG_R4, 0x44444444),
            (arm.UC_ARM_REG_R5, 0x55555555),
            (arm.UC_ARM_REG_R6, 0x66666666),
            (arm.UC_ARM_REG_R7, 0x77777777),
            (arm.UC_ARM_REG_R8, 0x88888888),
            (arm.UC_ARM_REG_R9, 0x99999999),
            (arm.UC_ARM_REG_R10, 0xAAAAAAAA),
            (arm.UC_ARM_REG_R11, 0xBBBBBBBB),
        ):
            self.uc.reg_write(reg, value)
        for d in range(8, 16):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_D{d}"), 0xD000000000000000 | d)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
        except Exception as exc:  # pragma: no cover - crash diagnostics
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {exc}") from exc

        snapshot = {
            "call_log": list(self.call_log),
            "object": bytes(self.uc.mem_read(OBJECT_ADDR, 0x400)),
            "fill": bytes(self.uc.mem_read(FILL_ADDR, FILL_SIZE)),
            "stack_above_sp": bytes(self.uc.mem_read(sp, STACK_ADDR + STACK_SIZE - sp)),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "r0": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "r4_r11": [self.uc.reg_read(getattr(arm, f"UC_ARM_REG_R{n}")) for n in range(4, 12)],
            "d8_d15": [self.uc.reg_read(getattr(arm, f"UC_ARM_REG_D{n}")) for n in range(8, 16)],
        }
        return snapshot


def f32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]


def make_object(
    *,
    count_a=1000,
    count_scale=256,
    count_b=2000,
    f18=1.5,
    f1c=0.5,
    f24=2.25,
    f28=-3.5,
    mirror=0,
    fill_ptr=FILL_ADDR + 0x100,
    fill_len=0x40,
    pair_lo=5,
    pair_hi=(-7) & 0xFFFFFFFF,
    word40=0xDEADBEEF,
):
    obj = bytearray(0x400)
    struct.pack_into("<I", obj, 0x0C, count_a & 0xFFFFFFFF)
    struct.pack_into("<I", obj, 0x10, count_scale & 0xFFFFFFFF)
    struct.pack_into("<I", obj, 0x14, count_b & 0xFFFFFFFF)
    struct.pack_into("<f", obj, 0x18, f18)
    struct.pack_into("<f", obj, 0x1C, f1c)
    struct.pack_into("<f", obj, 0x24, f24)
    struct.pack_into("<f", obj, 0x28, f28)
    obj[0x2D] = mirror & 0xFF
    struct.pack_into("<I", obj, 0x30, fill_ptr & 0xFFFFFFFF)
    struct.pack_into("<I", obj, 0x34, fill_len & 0xFFFFFFFF)
    struct.pack_into("<I", obj, 0x38, pair_lo & 0xFFFFFFFF)
    struct.pack_into("<I", obj, 0x3C, pair_hi & 0xFFFFFFFF)
    struct.pack_into("<I", obj, 0x40, word40 & 0xFFFFFFFF)
    return bytes(obj)


def ratio_from_bits(bits):
    return make_object(f1c=struct.unpack("<f", struct.pack("<I", bits))[0])


def build_cases():
    cases = []

    cases.append(("baseline direct", make_object()))

    cases.append((
        "low counts clamp to 4.888",
        make_object(count_a=0, count_b=0, count_scale=1),
    ))

    cases.append((
        "max u32 counts and scale",
        make_object(count_a=0xFFFFFFFF, count_scale=0xFFFFFFFF, count_b=0xFFFFFFFF),
    ))

    cases.append((
        "mirror selector == 1",
        make_object(mirror=1, f1c=0.25),
    ))

    cases.append((
        "mirror selector other than 1 (2)",
        make_object(mirror=2, f1c=0.75),
    ))

    # +0x1C clamp boundary: signed bit-pattern compare against 0x3F733333.
    cases.append(("ratio exactly 0.95", ratio_from_bits(0x3F733333)))
    cases.append(("ratio one ulp above 0.95", ratio_from_bits(0x3F733334)))
    cases.append(("ratio negative (-2.0)", make_object(f1c=-2.0)))
    cases.append(("ratio +100.0 clamps to 0.95", make_object(f1c=100.0)))
    cases.append(("ratio negative zero", ratio_from_bits(0x80000000)))

    # Scale denominator: ((u32)+0x10 * 0.001f) * 32728.0f.
    cases.append((
        "zero scale, +0x38 pair zero -> powf(10, 0) saturation",
        make_object(count_scale=0, pair_lo=0, pair_hi=0),
    ))
    cases.append((
        "zero scale, nonzero pair -> signed infinities",
        make_object(count_scale=0, pair_lo=0x80000000, pair_hi=0x7FFFFFFF),
    ))

    # Signed interpretation of the +0xB4 pair (VCVT.F32.S32).
    cases.append(("negative pair entries", make_object(pair_lo=0x80000000, pair_hi=0xFFFFFFFF)))
    cases.append(("large positive pair entries", make_object(pair_lo=0x7FFFFFFF, pair_hi=0x00000001)))

    # Float overflow / NaN in the *128 conversions.
    cases.append((
        "inf/nan float fields",
        make_object(f18=float("inf"), f24=float("-inf"), f28=float("nan")),
    ))

    # Zero-fill argument boundaries.
    cases.append(("zero fill length", make_object(fill_len=0)))
    cases.append(("null fill pointer", make_object(fill_ptr=0, fill_len=0x40)))
    cases.append(("fill pointer outside mapped fill window", make_object(fill_ptr=0xDEAD0000, fill_len=8)))

    return cases


def compare(label, orig, cand):
    problems = []
    for key in ("pc", "sp", "r0", "r4_r11", "d8_d15", "call_log", "object", "fill", "stack_above_sp"):
        if orig[key] != cand[key]:
            problems.append(key)
    if problems:
        detail = []
        for key in problems:
            if key in ("object", "fill", "stack_above_sp"):
                o, c = orig[key], cand[key]
                first = next((i for i in range(min(len(o), len(c))) if o[i] != c[i]), None)
                detail.append(f"{key}: differs at byte {first}")
            elif key == "call_log":
                detail.append(f"call_log:\n  orig={orig[key]}\n  cand={cand[key]}")
            else:
                detail.append(f"{key}: orig={orig[key]} cand={cand[key]}")
        raise AssertionError(f"{label}: " + "; ".join(detail))


def main():
    print(f"Testing {SYMBOL} (0x{FUNC_ADDR:08x})...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    runner = Runner()
    cases = build_cases()

    for label, object_image in cases:
        orig = runner.run(orig_code, object_image)
        cand = runner.run(cand_code, object_image)
        compare(label, orig, cand)
        print(f"  [PASS] {label}")

    # Every branch/loop path is represented at least once.
    # Negative control: perturbing the 0.95f ratio clamp must be detected.
    mutated = bytearray(cand_code)
    needle = struct.pack("<I", 0x3F733333)
    hits = 0
    start = 0
    while True:
        pos = mutated.find(needle, start)
        if pos < 0:
            break
        mutated[pos:pos + 4] = struct.pack("<I", 0x3F700000)
        hits += 1
        start = pos + 4
    if hits == 0:
        raise AssertionError("negative control: ratio literal not found in candidate")

    detected = 0
    for label, object_image in cases:
        orig = runner.run(orig_code, object_image)
        bad = runner.run(bytes(mutated), object_image)
        try:
            compare(label, orig, bad)
        except AssertionError:
            detected += 1
    if detected == 0:
        raise AssertionError("negative control: mutated clamp was not detected")
    print(f"  [PASS] negative control (mutated 0.95f clamp detected in {detected} case(s))")

    print(f"\nAll {len(cases)} differential test cases PASSED!")


if __name__ == "__main__":
    main()
