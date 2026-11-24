#!/usr/bin/env python3
"""Differential test for func_00169840 (0x00169840) using Unicorn ARM.

Compiles ``src/engine/leaf_batch34_c.cpp``, extracts the candidate body, and runs
the pinned original (``extracted/exefs/code.bin``) against the candidate in two
separate Unicorn machines with identical fixtures.

The function has no calls, no relocations and no indirect branches, so there is
no helper or indirect target to stub.  Its only external dependency is the
PC-relative literal pool it reads from the pinned image (0x01010101 and
0x20202020 at 0x00169838/0x0016983C, immediately before the entry point), which
the fixture supplies verbatim.

Compared outputs:
  * return r0 (the state pointer), continuation PC and final SP;
  * the complete destination page, the source page (must stay untouched) and
    the config page;
  * the set of destination byte addresses written (the original uses ldrd/strd
    for the copies, so sizes are compared as covered bytes rather than as
    store instructions);
  * any write outside the destination page and the private stack.

Callee-saved registers: the original saves only r0/lr and therefore clobbers
r4-r11 (the same ABI violation as 0x001602DC/0x00167DCC).  The candidate is a
normal AAPCS function and must preserve them; the test checks the candidate
against the entry sentinels and documents that the original clobbers them
instead of comparing two undefined register values.

Coverage:
  * horizontal counter (width - 0x10): widths 0x00, 0x04, 0x08, 0x10, 0x18,
    0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80, 0x100, 0x110, 0x210 so the
    signed > 0 repeat path, both exact-zero trailing-lane paths, the negative
    early exit and a non-positive start are all exercised;
  * vertical band counter (height - 8): one through eight bands;
  * threshold bytes 0x00, 0x01, 0x20, 0x7F, 0x80, 0xFF and prefix-OR expanded
    words with non-zero high bytes;
  * explicit first-lane boundary values for every comparison:
    |A-C| / |F-D| / |B-C| / |D-E| against threshold B (equal and one below),
    |C-D| against threshold A (equal and one below), the 0x20 sharpen clamp at
    0x00/0x7F/0xFF inputs, zero lanes and saturated lanes;
  * signed/unsigned boundary differences (distance 0x80 against threshold 0x7F
    and threshold 0x80, which unsigned ``usub8`` treats as never exceeded);
  * a later lane inside the chunk and a lane in the 0x10-byte tail;
  * the two four-row copy preludes: the top and bottom rows of the destination
    must equal the source bytes, and a non-positive width still copies one
    0x20-byte chunk.
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
SOURCE = ROOT / "src/engine/leaf_batch34_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_00169840"

FUNC_ADDR = 0x00169840
FUNC_SIZE = 3668

CODE_ADDR = 0x00150000
CODE_SIZE = 0x00030000
CONFIG_ADDR = 0x00400000
CONFIG_SIZE = 0x00001000
SRC_ADDR = 0x00500000
SRC_SIZE = 0x00080000
DST_ADDR = 0x00580000
DST_SIZE = 0x00080000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# 0x00169938/0x0016993C load two packed constants PC-relative from the literal
# pool at 0x00169838/0x0016983C (inside the preceding block).
LITERAL_POOL_ADDR = 0x00169838
LITERAL_POOL_SIZE = 8

ROW_STRIDE = 0x200
BAND_BYTES = 0x1000
FIRST_BAND = 0x1000

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
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def get_literal_pool() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(LITERAL_POOL_ADDR - 0x00100000)
        pool = handle.read(LITERAL_POOL_SIZE)
    if struct.unpack("<II", pool) != (0x01010101, 0x20202020):
        raise RuntimeError(f"unexpected literal pool bytes: {pool!r}")
    return pool


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")

    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next(
        (value for name, value in funcs.items() if "00169840" in name), None
    )
    if candidate is None:
        raise RuntimeError(f"func_00169840 not found in {obj_file}: {sorted(funcs)}")
    code, relocs = candidate
    if relocs:
        raise RuntimeError(f"unexpected relocations in func_00169840: {relocs}")
    return code


def lcg_bytes(seed: int, size: int) -> bytearray:
    state = seed & 0xFFFFFFFF
    out = bytearray(size)
    for index in range(size):
        state = (state * 1103515245 + 12345) & 0xFFFFFFFF
        out[index] = (state >> 16) & 0xFF
    return out


def build_src(case: dict) -> bytes:
    page = lcg_bytes(case.get("src_seed", 0x12345678), SRC_SIZE)
    for offset, byte in case.get("bytes", {}).items():
        page[offset] = byte & 0xFF
    for offset, word in case.get("words", {}).items():
        struct.pack_into("<I", page, offset, word & 0xFFFFFFFF)
    return bytes(page)


def build_dst(case: dict) -> bytes:
    return bytes(lcg_bytes(case.get("dst_seed", 0x89ABCDEF), DST_SIZE))


def build_config(case: dict) -> bytes:
    return struct.pack(
        "<IIIIII",
        SRC_ADDR,
        DST_ADDR,
        case["width_bytes"],
        case["height_bytes"],
        case.get("threshold_a", 0x20),
        case.get("threshold_b", 0x20),
    )


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(CONFIG_ADDR, CONFIG_SIZE)
        self.uc.mem_map(SRC_ADDR, SRC_SIZE)
        self.uc.mem_map(DST_ADDR, DST_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.literal_pool = get_literal_pool()
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.writes: list = []

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def run(self, code: bytes, case: dict) -> dict:
        src = build_src(case)
        dst = build_dst(case)
        config = build_config(case)
        self.uc.mem_write(CODE_ADDR, b"\x00" * CODE_SIZE)
        self.uc.mem_write(LITERAL_POOL_ADDR, self.literal_pool)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(CONFIG_ADDR, config)
        self.uc.mem_write(SRC_ADDR, src)
        self.uc.mem_write(DST_ADDR, dst)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, CONFIG_ADDR)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=40_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        covered: set[int] = set()
        out_of_bounds = []
        for address, size in self.writes:
            in_dst = DST_ADDR <= address and address + size <= DST_ADDR + DST_SIZE
            in_stack = STACK_ADDR <= address and address + size <= STACK_ADDR + STACK_SIZE
            if in_dst:
                covered.update(range(address, address + size))
            elif in_stack:
                pass
            else:
                out_of_bounds.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "dst": bytes(self.uc.mem_read(DST_ADDR, DST_SIZE)),
            "src": bytes(self.uc.mem_read(SRC_ADDR, SRC_SIZE)),
            "config": bytes(self.uc.mem_read(CONFIG_ADDR, CONFIG_SIZE)),
            "input_dst": dst,
            "dst_bytes_written": frozenset(covered),
            "out_of_bounds_writes": out_of_bounds,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["dst"] != cand["dst"]:
        first = next(
            index
            for index, (left, right) in enumerate(zip(orig["dst"], cand["dst"]))
            if left != right
        )
        problems.append(
            f"dst mismatch at DST+0x{first:x}: "
            f"orig={orig['dst'][first:first + 16]!r} "
            f"cand={cand['dst'][first:first + 16]!r}"
        )
    if orig["src"] != cand["src"]:
        problems.append("source page differs (it must not be written)")
    if orig["config"] != cand["config"]:
        problems.append("config page differs")
    if orig["dst_bytes_written"] != cand["dst_bytes_written"]:
        only_orig = orig["dst_bytes_written"] - cand["dst_bytes_written"]
        only_cand = cand["dst_bytes_written"] - orig["dst_bytes_written"]
        problems.append(
            "written-byte coverage mismatch: "
            f"only orig={sorted(only_orig)[:8]} only cand={sorted(only_cand)[:8]}"
        )
    if orig["out_of_bounds_writes"] or cand["out_of_bounds_writes"]:
        problems.append(
            "out-of-bounds writes orig="
            f"{orig['out_of_bounds_writes']} cand={cand['out_of_bounds_writes']}"
        )
    return problems


def check_callee_saved(cand: dict) -> list[str]:
    return [
        f"candidate did not preserve {name}: "
        f"{cand['callee_saved'][name]:#010x}"
        for name in CALLEE_SAVED
        if cand["callee_saved"][name] != CALLEE_SAVED_START[name]
    ]


def check_copies(orig: dict, case: dict, src: bytes) -> list[str]:
    """The top/bottom preludes must copy source bytes; assert they are visible."""
    problems = []
    width = case["width_bytes"]
    chunks = 1 if width == 0 else (width + 0x1F) // 0x20
    copied = min(chunks * 0x20, SRC_SIZE)
    for row_base in (0, (case["height_bytes"] - 4) * ROW_STRIDE):
        if not (0 <= row_base < SRC_SIZE):
            continue
        left = src[row_base:row_base + copied]
        right = orig["dst"][row_base:row_base + copied]
        if left != right:
            problems.append(
                f"copy prelude did not reproduce row at DST+0x{row_base:x}"
            )
    return problems


def effect_stats(orig: dict) -> tuple[int, int]:
    changed = 0
    for index in range(0, DST_SIZE, 4):
        if orig["input_dst"][index:index + 4] != orig["dst"][index:index + 4]:
            changed += 1
    return changed, len(orig["dst_bytes_written"])


def lane_offsets(index: int) -> dict:
    centre = FIRST_BAND + index * 4
    return {
        "a": centre - 3 * ROW_STRIDE,
        "b": centre - 2 * ROW_STRIDE,
        "c": centre - 1 * ROW_STRIDE,
        "d": centre,
        "e": centre + 1 * ROW_STRIDE,
        "f": centre + 2 * ROW_STRIDE,
    }


def lane_words(a: int, b: int, c: int, d: int, e: int, f: int,
               index: int = 0) -> dict:
    offsets = lane_offsets(index)
    return {
        offsets["a"]: a * 0x01010101,
        offsets["b"]: b * 0x01010101,
        offsets["c"]: c * 0x01010101,
        offsets["d"]: d * 0x01010101,
        offsets["e"]: e * 0x01010101,
        offsets["f"]: f * 0x01010101,
    }


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "width_bytes": 0x30,
        "height_bytes": 0x18,
        "threshold_a": 0x20,
        "threshold_b": 0x20,
        "src_seed": 0x12345678,
        "dst_seed": 0x89ABCDEF,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases = []

    # --- horizontal counter: >0 repeat, ==0 tail, <0 skip tail ------------
    for width in (0x08, 0x10, 0x18, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80):
        cases.append(base_case(f"width 0x{width:02x}"))
        cases.append(base_case(f"width 0x{width:02x} thresholds 0",
                               threshold_a=0x00, threshold_b=0x00))
        cases.append(base_case(f"width 0x{width:02x} thresholds 0xFF",
                               threshold_a=0xFF, threshold_b=0xFF))
    cases.append(base_case("width 0x00 copies one chunk", width_bytes=0x00))
    cases.append(base_case("width 0x04 wraps negative", width_bytes=0x04))
    for width in (0x100, 0x110, 0x210, 0x0C):
        cases.append(base_case(f"width 0x{width:03x}", width_bytes=width,
                               height_bytes=0x38))
        cases.append(base_case(f"width 0x{width:03x} thresholds 0x7F",
                               width_bytes=width, height_bytes=0x38,
                               threshold_a=0x7F, threshold_b=0x7F,
                               src_seed=0x5EED1234, dst_seed=0x0FEDCBA9))

    # --- vertical band counter: 1..8 bands --------------------------------
    for height in (0x10, 0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0x48):
        cases.append(base_case(f"height 0x{height:02x} bands",
                               height_bytes=height, width_bytes=0x30))
        cases.append(base_case(f"height 0x{height:02x} negative tail",
                               height_bytes=height, width_bytes=0x20))

    # --- threshold bytes and prefix-OR expansion --------------------------
    for threshold in (0x00, 0x01, 0x20, 0x7F, 0x80, 0xFF):
        cases.append(
            base_case(
                f"thresholds 0x{threshold:02x}",
                threshold_a=threshold,
                threshold_b=threshold,
                src_seed=0x0F1E2D3C,
            )
        )
    for threshold_a, threshold_b in (
        (0x00001234, 0x00000056),
        (0x0000FF00, 0x000000FF),
        (0x80504020, 0x00000010),
        (0x7F7F7F7F, 0x80808080),
    ):
        cases.append(
            base_case(
                f"prefix-or 0x{threshold_a:08x}/0x{threshold_b:08x}",
                threshold_a=threshold_a,
                threshold_b=threshold_b,
                src_seed=0x27182818,
            )
        )

    # --- explicit first-lane values for every comparison ------------------
    boundary = [
        ("all distances below", 0x40, 0x11, 0x40, 0x50, 0x66, 0x50,
         0x40, 0x40),
        ("all distances above", 0x00, 0x77, 0x40, 0x50, 0x88, 0x90,
         0x40, 0x40),
        ("above boundary equal", 0x20, 0x50, 0x40, 0x50, 0x66, 0x50,
         0x40, 0x20),
        ("above boundary one below", 0x21, 0x50, 0x40, 0x50, 0x66, 0x50,
         0x40, 0x20),
        ("below boundary equal", 0x40, 0x40, 0x40, 0x50, 0x40, 0x70,
         0x40, 0x20),
        ("below boundary one below", 0x40, 0x40, 0x40, 0x50, 0x40, 0x6F,
         0x40, 0x20),
        ("inner-above boundary equal", 0x40, 0x60, 0x40, 0x50, 0x66, 0x50,
         0x40, 0x20),
        ("inner-above boundary one below", 0x40, 0x5F, 0x40, 0x50, 0x66,
         0x50, 0x40, 0x20),
        ("inner-below boundary equal", 0x40, 0x40, 0x40, 0x50, 0x70, 0x50,
         0x40, 0x20),
        ("inner-below boundary one below", 0x40, 0x40, 0x40, 0x50, 0x6F,
         0x50, 0x40, 0x20),
        ("centre boundary equal", 0x40, 0x11, 0x40, 0x50, 0x66, 0x50,
         0x10, 0x40),
        ("centre boundary one below", 0x40, 0x11, 0x40, 0x50, 0x66, 0x50,
         0x11, 0x40),
        ("sharpen raise zero", 0x40, 0x00, 0x40, 0x50, 0x00, 0x50,
         0xC0, 0xC0),
        ("sharpen raise sixteen", 0x40, 0x7F, 0x40, 0x50, 0x00, 0x50,
         0xC0, 0xC0),
        ("sharpen raise thirtytwo", 0x40, 0xFF, 0x40, 0x50, 0x00, 0x50,
         0xC0, 0xC0),
        ("sharpen fall thirtytwo", 0x40, 0x00, 0x40, 0x50, 0xFF, 0x50,
         0xC0, 0xC0),
        ("sharpen fall sixteen", 0x40, 0x80, 0x40, 0x50, 0xFF, 0x50,
         0xC0, 0xC0),
        ("sharpen high saturation", 0xFF, 0xFF, 0xFF, 0xFF, 0x10, 0xFF,
         0x40, 0xF0),
        ("saturated extremes", 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00,
         0x20, 0x20),
        ("zero lane", 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x20, 0x20),
        ("all maximum", 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x20, 0x20),
    ]
    for (label, a, b, c, d, e, f, ta, tb) in boundary:
        cases.append(
            base_case(
                f"first lane {label}",
                threshold_a=ta,
                threshold_b=tb,
                words=lane_words(a, b, c, d, e, f),
            )
        )

    # --- unsigned vs signed boundary (usub8, not ssub8) -------------------
    signed_cases = [
        ("above distance 0x80 vs 0x7F", 0x00, 0x40, 0x80, 0x00, 0x00, 0x00,
         0x00, 0x7F),
        ("below distance 0x80 vs 0x7F", 0x00, 0x00, 0x00, 0x00, 0x40, 0x80,
         0x00, 0x7F),
        ("inner-above distance 0x80 vs 0x7F", 0x00, 0x80, 0x00, 0x00, 0x00,
         0x00, 0x00, 0x7F),
        ("centre distance 0x80 vs 0x7F", 0x00, 0x00, 0x00, 0x80, 0x00, 0x00,
         0x7F, 0x00),
        ("threshold 0x80 never exceeded", 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF,
         0x80, 0x80),
    ]
    for (label, a, b, c, d, e, f, ta, tb) in signed_cases:
        cases.append(
            base_case(
                f"unsigned {label}",
                threshold_a=ta,
                threshold_b=tb,
                words=lane_words(a, b, c, d, e, f),
            )
        )

    # --- later lanes: inside the first chunk and in the 0x10-byte tail ----
    for index in (1, 7, 8, 11):
        cases.append(
            base_case(
                f"lane {index} boundary",
                threshold_a=0x20,
                threshold_b=0x20,
                words=lane_words(0x00, 0x00, 0x00, 0x20, 0x00, 0xFF,
                                 index=index),
            )
        )

    # --- determinism / seeds ----------------------------------------------
    for seed in (0x00000000, 0xFFFFFFFF, 0xDEADBEEF):
        cases.append(
            base_case(f"seed 0x{seed:08x}", src_seed=seed, dst_seed=seed ^ 0x55AA55AA)
        )

    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases: list[dict]) -> int:
    passed = 0
    total_changed = 0
    unchanged_cases = 0
    for case in cases:
        orig = Runner().run(orig_code, case)
        cand = Runner().run(cand_code, case)
        problems = compare(orig, cand)
        problems.extend(check_callee_saved(cand))
        problems.extend(check_copies(orig, case, build_src(case)))
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        if orig["ret"] != CONFIG_ADDR:
            print(f"  [FAIL] {case['name']}: return {orig['ret']:#x}")
            raise SystemExit(1)
        if orig["sp"] != ENTRY_SP:
            print(f"  [FAIL] {case['name']}: final SP {orig['sp']:#x}")
            raise SystemExit(1)
        changed, _ = effect_stats(orig)
        if changed:
            total_changed += changed
        else:
            unchanged_cases += 1
        passed += 1
        print(
            f"  [PASS] {case['name']}  "
            f"({changed} words changed, {len(orig['dst_bytes_written'])} bytes written)"
        )

    assert total_changed > 0, "no case exercised a filtered/copied write"
    print(
        f"  ({total_changed} destination words changed across the suite; "
        f"{unchanged_cases} cases left every word unchanged)"
    )
    return passed


def compile_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next(
        (value for name_, value in funcs.items() if "00169840" in name_), None
    )
    if candidate is None or candidate[1]:
        raise RuntimeError("mutant function missing or unexpectedly relocated")
    return candidate[0]


def main() -> None:
    print("Testing func_00169840 (0x00169840)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B, no relocations.")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    controls = (
        (
            "row_stride",
            "constexpr u32 kCopyFilterRowStride = 0x200u;",
            "constexpr u32 kCopyFilterRowStride = 0x204u;",
        ),
        (
            "band_bytes",
            "constexpr u32 kCopyFilterBandBytes = 0x1000u;",
            "constexpr u32 kCopyFilterBandBytes = 0x1004u;",
        ),
        (
            "chunk_bytes",
            "constexpr u32 kCopyFilterChunkBytes = 0x20u;",
            "constexpr u32 kCopyFilterChunkBytes = 0x1Fu;",
        ),
        (
            "tail_bytes",
            "constexpr u32 kCopyFilterTailBytes = 0x10u;",
            "constexpr u32 kCopyFilterTailBytes = 0x0Cu;",
        ),
        (
            "width_bias",
            "constexpr u32 kCopyFilterWidthBias = 0x10u;",
            "constexpr u32 kCopyFilterWidthBias = 0x0Cu;",
        ),
        (
            "height_step",
            "constexpr u32 kCopyFilterHeightStep = 8u;",
            "constexpr u32 kCopyFilterHeightStep = 4u;",
        ),
        (
            "copied_rows",
            "constexpr u32 kCopyFilterCopiedRows = 4u;",
            "constexpr u32 kCopyFilterCopiedRows = 2u;",
        ),
        (
            "copy_store_offset",
            "    store_word(dst - 0x400 + lane, output.inner_above);",
            "    store_word(dst - 0x404 + lane, output.inner_above);",
        ),
        (
            "last_row_shift",
            "        (config->height_bytes - kCopyFilterCopiedRows) << 9;  // * 0x200",
            "        (config->height_bytes - kCopyFilterCopiedRows) << 8;  // * 0x200",
        ),
        (
            "centre_threshold",
            "    mask = byte_uge8_mask(distance, threshold_a);",
            "    mask = byte_uge8_mask(distance, threshold_b);",
        ),
    )
    for name, old, new in controls:
        mutant = compile_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")
    print("Original clobbers r4-r11 (it saves only r0/lr);")
    print("the candidate preserves them and the test checks that ABI property.")


if __name__ == "__main__":
    main()
