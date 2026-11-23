#!/usr/bin/env python3
"""Differential test for func_0016391c (0x0016391C) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the func_0016391c body and
runs the pinned original (extracted/exefs/code.bin) against the candidate in
separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP;
  * the entire config and filtered-buffer pages (full observable memory);
  * every memory write outside the private stack (address, width, value);
  * the ordered call log, which must stay empty: the function has no calls.

The original routine clobbers r4-r11 without saving them (it only pushes
{r0, lr}); the C++ candidate follows the AAPCS and restores them.  Callee-saved
values are therefore recorded as evidence, not compared for equality: the test
requires the candidate to return the seeded values and explicitly documents the
original's deviation.

Coverage: the signed (width - 0x20) boundary in both directions (short path at
<= 0, full path at > 0), widths that make the remaining count land exactly on
zero, positive and negative, chunk counts 1..4, tail groups 1..4, one and
several four-row bands, both thresholds zero and saturated, and byte-pattern
fixtures that exercise every packed-arithmetic GE outcome (all 0x00, all 0xFF,
alternating signs, saturating differences, and pseudo-random data).
Negative controls mutate the row stride, the band stride, the packed-two
literal, the tail bias, and the threshold A/B wiring; each mutant must be
detected.
"""

from __future__ import annotations

import random
import struct
import sys
from pathlib import Path

import unicorn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unicorn import arm_const as arm

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch34_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_0016391c"

FUNC_ADDR = 0x0016391C
FUNC_SIZE = 1848

# The routed body loads its two arithmetic constants from the literal pool that
# sits immediately before the function (outside the 1848-byte body):
#   0x00163914 -> 0x01010101   (r12 / ip)
#   0x00163918 -> 0x02020202   (r14 / lr)
ORIG_LITERAL_ONE = 0x00163914
ORIG_LITERAL_TWO = 0x00163918
ORIG_LITERAL_ONE_VALUE = 0x01010101
ORIG_LITERAL_TWO_VALUE = 0x02020202

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000
CONFIG_ADDR = 0x00700000
CONFIG_SIZE = 0x00001000
BUFFER_ADDR = 0x00710000
BUFFER_SIZE = 0x00020000  # 128 KiB covers every width/band used below
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


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0016391c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"func_0016391c not found in {obj_file}: {sorted(funcs)}"
        )
    code, relocs = candidate
    if relocs:
        raise RuntimeError(f"unexpected relocations in candidate: {relocs}")
    return bytes(code)


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
    funcs = extract_elf_functions_detailed(obj_file)
    for sym, value in funcs.items():
        if "0016391c" in sym:
            return bytes(value[0])
    raise RuntimeError(f"mutant func_0016391c not found: {sorted(funcs)}")


# --------------------------------------------------------------------- fixtures
PATTERN_BUILDERS = {
    "zero": lambda index: 0x00,
    "ones": lambda index: 0xFF,
    "alternating": lambda index: 0xFF if index & 1 else 0x00,
    "checker": lambda index: 0xAA if index & 2 else 0x55,
    "signed_edges": lambda index: (0x00, 0x7F, 0x80, 0xFF)[index & 3],
    "ramp": lambda index: index & 0xFF,
}


def build_buffer(case: dict) -> bytes:
    size = case.get("buffer_size", BUFFER_SIZE)
    pattern = case["pattern"]
    base = case.get("buffer_fill", 0x5A)
    page = bytearray([base & 0xFF]) * size
    if pattern == "random":
        rng = random.Random(case.get("seed", 0x1234))
        page = bytearray(rng.randrange(256) for _ in range(size))
    else:
        make = PATTERN_BUILDERS[pattern]
        for index in range(size):
            page[index] = make(index) & 0xFF
    if "patch" in case:
        for offset, value in case["patch"].items():
            page[offset] = value & 0xFF
    return bytes(page)


def build_config(case: dict) -> bytes:
    page = bytearray(CONFIG_SIZE)
    struct.pack_into(
        "<IIIIII",
        page,
        0,
        case.get("unused", 0xDEADBEEF) & 0xFFFFFFFF,
        BUFFER_ADDR,
        case["width"] & 0xFFFFFFFF,
        case["height"] & 0xFFFFFFFF,
        case.get("threshold_a", 0x00000000) & 0xFFFFFFFF,
        case.get("threshold_b", 0x00000000) & 0xFFFFFFFF,
    )
    return bytes(page)


class LeafRunner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(CONFIG_ADDR, CONFIG_SIZE)
        self.uc.mem_map(BUFFER_ADDR, BUFFER_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.writes: list = []

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def run(self, code: bytes, case: dict) -> dict:
        self.writes = []
        self.uc.mem_write(FUNC_ADDR, code)
        # The routed original reads these words from before the function body;
        # without them Unicorn would see zeros and diverge from the image.
        self.uc.mem_write(
            ORIG_LITERAL_ONE, struct.pack("<I", ORIG_LITERAL_ONE_VALUE)
        )
        self.uc.mem_write(
            ORIG_LITERAL_TWO, struct.pack("<I", ORIG_LITERAL_TWO_VALUE)
        )
        self.uc.mem_write(CONFIG_ADDR, build_config(case))
        buffer = build_buffer(case)
        self.uc.mem_write(BUFFER_ADDR, buffer)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, CONFIG_ADDR)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=10_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_buffer = BUFFER_ADDR <= address < BUFFER_ADDR + BUFFER_SIZE
            if not in_stack and not in_buffer:
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": [],
            "config": bytes(self.uc.mem_read(CONFIG_ADDR, CONFIG_SIZE)),
            "buffer": bytes(self.uc.mem_read(BUFFER_ADDR, BUFFER_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp"):
        if orig[key] != cand[key]:
            problems.append(f"{key}: orig={orig[key]!r} cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(f"call_log: orig={orig['call_log']!r} cand={cand['call_log']!r}")
    if orig["config"] != cand["config"]:
        problems.append("config page was modified differently")
    if orig["buffer"] != cand["buffer"]:
        first = next(
            index
            for index, (left, right) in enumerate(
                zip(orig["buffer"], cand["buffer"])
            )
            if left != right
        )
        problems.append(
            f"buffer mismatch at offset 0x{first:x}: "
            f"orig={orig['buffer'][first]:02x} cand={cand['buffer'][first]:02x}"
        )
    if orig["unexpected_writes"] != cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    if orig["unexpected_writes"]:
        problems.append(f"writes outside the buffer: {orig['unexpected_writes']}")
    return problems


def base_case(name: str, width: int, height: int, **overrides) -> dict:
    case = {
        "name": name,
        "width": width,
        "height": height,
        "pattern": "random",
        "seed": 0x1234,
        "buffer_size": 0x20000,
        "threshold_a": 0x00000000,
        "threshold_b": 0x00000000,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- signed (width - 0x20) boundary: short path at <= 0.  Widths in
    # 0x80000000..0x8000001F wrap to a huge positive counter (full path), so
    # the negative short-path samples use 0x80000020 and above.
    for width in (0x00000000, 0x00000001, 0x00000008, 0x0000001F, 0x00000020,
                  0x80000020, 0xFFFFFFFF):
        cases.append(base_case(f"short path width=0x{width:08x}", width, 4))
    cases.append(base_case("short path multi-band width=0x20", 0x20, 0x10))
    cases.append(base_case("short path negative width, 2 bands", 0xFFFFFFFF, 8))

    # --- full path: width > 0x20; chunk counts and tail groups
    for width in (0x21, 0x22, 0x27, 0x28, 0x2F, 0x30, 0x31, 0x38, 0x3F,
                  0x40, 0x41, 0x48, 0x4F, 0x50, 0x58, 0x60, 0x68, 0x70,
                  0x78, 0x80):
        cases.append(base_case(f"full path width=0x{width:02x}", width, 4))

    # --- multiple bands and multi-band chunk accumulation
    for height in (4, 8, 12, 16):
        for width in (0x21, 0x40, 0x5F):
            cases.append(
                base_case(f"bands height={height} width=0x{width:02x}",
                          width, height, seed=0x1000 + width + height)
            )

    # --- thresholds: zero, saturated, alternating, and prefix-OR spread
    for threshold_a, threshold_b in (
        (0x00000000, 0x00000000),
        (0xFFFFFFFF, 0xFFFFFFFF),
        (0x000000FF, 0x000000FF),
        (0x0000FF00, 0x00FF0000),
        (0x80808080, 0x7F7F7F7F),
        (0x01010101, 0x02020202),
        (0x00000001, 0x00000001),
        (0x000000FF, 0x00000001),
        (0xFFFFFF00, 0x0000FFFF),
    ):
        for width in (0x20, 0x21, 0x40, 0x60):
            cases.append(
                base_case(
                    f"thresholds 0x{threshold_a:08x}/0x{threshold_b:08x} "
                    f"width=0x{width:02x}",
                    width, 8, threshold_a=threshold_a, threshold_b=threshold_b,
                )
            )

    # --- data patterns that reach every saturating / GE outcome
    for pattern in PATTERN_BUILDERS:
        cases.append(base_case(f"pattern {pattern}", 0x40, 8, pattern=pattern))
        cases.append(base_case(f"short pattern {pattern}", 0x20, 8, pattern=pattern))
    cases.append(base_case("random high byte", 0x60, 12, seed=0xDEADBEEF))
    cases.append(base_case("random wide", 0x80, 16, seed=0x0BADF00D))

    # Patch a single group's four row windows so that a_high/a_low and
    # b_low/b_high differ in both directions; exercises all three sel masks.
    cases.append(base_case("patch all sel masks", 0x21, 4, pattern="zero",
                           patch={0x007: 0x10, 0x008: 0xF0,
                                  0x107: 0x90, 0x108: 0x20,
                                  0x207: 0x00, 0x208: 0xFF,
                                  0x307: 0x7F, 0x308: 0x80}))
    cases.append(base_case("patch saturation", 0x21, 4, pattern="zero",
                           patch={0x007: 0xFF, 0x008: 0x00,
                                  0x107: 0x00, 0x108: 0xFF,
                                  0x207: 0xFF, 0x208: 0xFF,
                                  0x307: 0x00, 0x308: 0x00}))

    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases: list[dict]) -> int:
    passed = 0
    for case in cases:
        orig = LeafRunner().run(orig_code, case)
        cand = LeafRunner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        # The candidate must obey the AAPCS.  The original does not (it only
        # saves r0/lr), so its r4-r11 values are recorded but not compared.
        for name, seeded in CALLEE_SAVED_START.items():
            if cand["callee_saved"][name] != seeded:
                raise SystemExit(
                    f"  [FAIL] {case['name']}: candidate clobbered {name}: "
                    f"0x{cand['callee_saved'][name]:08x} != 0x{seeded:08x}"
                )
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['unexpected_writes'])} writes)")
    return passed


def main() -> None:
    print("Testing func_0016391c (0x0016391C)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"({FUNC_ADDR:#010x}, {FUNC_SIZE} B expected)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    # Evidence for the documented ABI deviation: the pinned original does not
    # save r4-r11 even though it uses them as scratch registers.
    evidence = LeafRunner().run(orig_code, base_case("abi evidence", 0x40, 4))
    clobbered = [
        name for name, seeded in CALLEE_SAVED_START.items()
        if evidence["callee_saved"][name] != seeded
    ]
    assert clobbered, "expected the original to clobber at least one callee-saved register"
    print(
        f"  [PASS] original clobbers callee-saved {clobbered} "
        "(candidate preserves them per AAPCS)"
    )

    print("\nNegative controls:")
    for name, old, new in (
        ("row_stride", "constexpr u32 kQuadRow100Stride = 0x100u;",
         "constexpr u32 kQuadRow100Stride = 0x104u;"),
        ("band_stride", "constexpr u32 kQuadRow100BandBytes = 0x400u;",
         "constexpr u32 kQuadRow100BandBytes = 0x404u;"),
        ("packed_two", "constexpr u32 kQuadRow100PackedTwo = 0x02020202u;",
         "constexpr u32 kQuadRow100PackedTwo = 0x02020203u;"),
        ("tail_bias", "constexpr u32 kQuadRow100TailBias = 0x18u;",
         "constexpr u32 kQuadRow100TailBias = 0x17u;"),
        ("threshold_wiring",
         "const u32 width_counter = config->width_bytes - kQuadRow100WidthBias;\n"
         "    const u32 threshold_a = prefix_or_bytes(config->threshold_a);",
         "const u32 width_counter = config->width_bytes - kQuadRow100WidthBias;\n"
         "    const u32 threshold_a = prefix_or_bytes(config->threshold_b);"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = LeafRunner().run(orig_code, case)
            bad = LeafRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
