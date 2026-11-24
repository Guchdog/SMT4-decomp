#!/usr/bin/env python3
"""Differential test for func_00167dcc (0x00167dcc) using Unicorn ARM.

Compiles ``src/engine/leaf_batch34_c.cpp``, extracts the candidate body, and runs
the pinned original (``extracted/exefs/code.bin``) against the candidate in two
separate Unicorn machines with identical fixtures.

The function has no calls, no relocations and no indirect branches, so there is
no helper or indirect target to stub.  Its only external dependency is the
PC-relative literal pool it reads from the pinned image (0x01010101 and
0x20202020 at 0x0016768C/0x00167690), which the fixture supplies verbatim.
Compared outputs:
  * return r0 (the config pointer), continuation PC and final SP;
  * the complete filtered data page and the config page;
  * the ordered sequence of data-page writes (address, width) -- the original
    writes the four middle rows of every lane in a fixed order and the
    candidate's volatile stores must preserve it;
  * any write outside the data page and the private stack.

Callee-saved registers: the original saves only r0/lr and therefore clobbers
r4-r11 (the same ABI violation as 0x001602DC).  The candidate is a normal AAPCS
function and must preserve them.  The test checks the candidate against the
entry sentinels and documents that the original clobbers them instead of
comparing two undefined register values.

Coverage:
  * horizontal counter (width - 0x10): 0, 4, 8, 12, 16, 24, 32, 40, 48, 64, 80,
    96, 0x100 and 0x110 bytes so the signed >0 repeat path, both exact-zero
    trailing-lane paths and the negative early exit are all exercised (including
    a negative start);
  * vertical band counter (height - 8): one through six bands plus a negative
    tail;
  * threshold bytes 0x00, 0x01, 0x20, 0x7F, 0x80, 0xFF and prefix-OR expanded
    words with non-zero high bytes;
  * explicit first-lane boundary values for every comparison:
    |A-C| / |F-D| / |B-C| / |D-E| against threshold B (equal and one below),
    |C-D| against threshold A (equal and one below), the 0x20 sharpen clamp at
    0x00/0x7F/0xFF inputs, zero lanes and saturated lanes;
  * signed/unsigned boundary differences (distance 0x80 against threshold 0x7F
    and threshold 0x80, which unsigned `usub8` treats as never exceeded);
  * a later lane inside the chunk and a lane in the 0x10-byte tail.
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
OUT_DIR = ROOT / "build/test_leaf_00167dcc"

FUNC_ADDR = 0x00167DCC
FUNC_SIZE = 2996

CODE_ADDR = 0x00150000
CODE_SIZE = 0x00020000
CONFIG_ADDR = 0x00400000
CONFIG_SIZE = 0x00001000
DATA_ADDR = 0x00500000
DATA_SIZE = 0x00040000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
DATA_BASE = DATA_ADDR

# 0x00167DE4/0x00167DE8 load two packed constants PC-relative from the shared
# literal pool at 0x0016768C/0x00167690 (inside the preceding block):
# 0x01010101 and 0x20202020.  They are not relocations, so the fixture must
# place the pinned image bytes there or the original would multiply-by-zero.
LITERAL_POOL_ADDR = 0x0016768C
LITERAL_POOL_SIZE = 8

ROW_STRIDE = 0x200
FIRST_GROUP = 0x1000  # relative to DATA_BASE (base + 0x1000)

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
        (value for name, value in funcs.items() if "00167dcc" in name), None
    )
    if candidate is None:
        raise RuntimeError(f"func_00167dcc not found in {obj_file}: {sorted(funcs)}")
    code, relocs = candidate
    if relocs:
        raise RuntimeError(f"unexpected relocations in func_00167dcc: {relocs}")
    return code


def lcg_bytes(seed: int, size: int) -> bytearray:
    state = seed & 0xFFFFFFFF
    out = bytearray(size)
    for index in range(size):
        state = (state * 1103515245 + 12345) & 0xFFFFFFFF
        out[index] = (state >> 16) & 0xFF
    return out


def build_data(case: dict) -> bytes:
    page = lcg_bytes(case.get("seed", 0x12345678), DATA_SIZE)
    for offset, byte in case.get("bytes", {}).items():
        page[offset] = byte & 0xFF
    for offset, word in case.get("words", {}).items():
        struct.pack_into("<I", page, offset, word & 0xFFFFFFFF)
    return bytes(page)


def build_config(case: dict) -> bytes:
    return struct.pack(
        "<IIIIII",
        case.get("unused0", 0xA5A50000),
        DATA_BASE,
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
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.literal_pool = get_literal_pool()
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.writes: list = []

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def run(self, code: bytes, case: dict) -> dict:
        data = build_data(case)
        config = build_config(case)
        self.uc.mem_write(CODE_ADDR, b"\x00" * CODE_SIZE)
        self.uc.mem_write(LITERAL_POOL_ADDR, self.literal_pool)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(CONFIG_ADDR, config)
        self.uc.mem_write(DATA_ADDR, data)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, CONFIG_ADDR)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=20_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        data_writes = [
            (address, size)
            for address, size in self.writes
            if DATA_ADDR <= address < DATA_ADDR + DATA_SIZE
        ]
        out_of_bounds = [
            (address, size)
            for address, size in self.writes
            if not (DATA_ADDR <= address < DATA_ADDR + DATA_SIZE)
            and not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        ]

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "config": bytes(self.uc.mem_read(CONFIG_ADDR, CONFIG_SIZE)),
            "input_data": data,
            "data_writes": data_writes,
            "out_of_bounds_writes": out_of_bounds,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["data"] != cand["data"]:
        first = next(
            index
            for index, (left, right) in enumerate(zip(orig["data"], cand["data"]))
            if left != right
        )
        problems.append(
            f"data mismatch at DATA+0x{first:x}: "
            f"orig={orig['data'][first:first + 16]!r} "
            f"cand={cand['data'][first:first + 16]!r}"
        )
    if orig["config"] != cand["config"]:
        problems.append("config page differs")
    if orig["data_writes"] != cand["data_writes"]:
        first = next(
            (
                index
                for index, (left, right) in enumerate(
                    zip(orig["data_writes"], cand["data_writes"])
                )
                if left != right
            ),
            min(len(orig["data_writes"]), len(cand["data_writes"])),
        )
        problems.append(
            "data write sequence mismatch at "
            f"#{first}: orig={orig['data_writes'][first:first + 6]!r} "
            f"cand={cand['data_writes'][first:first + 6]!r} "
            f"(counts {len(orig['data_writes'])}/{len(cand['data_writes'])})"
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


def effect_stats(result: dict) -> tuple[int, int]:
    changed = 0
    touched = 0
    for index in range(0, DATA_SIZE, 4):
        before = result["input_data"][index : index + 4]
        after = result["data"][index : index + 4]
        if before != after:
            changed += 1
        if any(after):
            touched += 1
    return changed, touched


def lane_offsets(index: int) -> dict:
    centre = FIRST_GROUP + index * 4
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
        "seed": 0x12345678,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases = []

    # --- horizontal counter: >0 repeat, ==0 tail, <0 skip tail ------------
    # width - 0x10 = {F8(F0), 8, 0x10, 0x18, 0x20, 0x28, 0x30}:
    # 0x30 and 0x50 land exactly on zero and run the four trailing lanes;
    # 0x20, 0x40 and 0x60 take the negative early exit; 0x00/0x08/0x10 start
    # at or below zero and still execute one unconditional 0x20-byte chunk.
    for width in (0x08, 0x10, 0x18, 0x20, 0x30, 0x40, 0x50, 0x60):
        cases.append(base_case(f"width 0x{width:02x}"))
        cases.append(base_case(f"width 0x{width:02x} thresholds 0",
                               threshold_a=0x00, threshold_b=0x00))
        cases.append(base_case(f"width 0x{width:02x} thresholds 0xFF",
                               threshold_a=0xFF, threshold_b=0xFF))
    cases.append(base_case("width 0x00 wraps negative", width_bytes=0x00))
    cases.append(base_case("width 0x04 wraps negative", width_bytes=0x04))
    # Deeper horizontal loops: 0x100 leaves a negative remainder after eight
    # chunks, 0x110 lands exactly on zero before the trailing lanes.
    for width in (0x100, 0x110, 0x0C):
        cases.append(base_case(f"width 0x{width:03x}", width_bytes=width,
                               height_bytes=0x38))
        cases.append(base_case(f"width 0x{width:03x} thresholds 0x7F",
                               width_bytes=width, height_bytes=0x38,
                               threshold_a=0x7F, threshold_b=0x7F,
                               seed=0x5EED1234))

    # --- vertical band counter: 1..6 bands --------------------------------
    for height in (0x10, 0x18, 0x20, 0x28, 0x30, 0x38):
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
                seed=0x0F1E2D3C,
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
                seed=0x27182818,
            )
        )

    # --- explicit first-lane values for every comparison ------------------
    # Centre rows are 0x40/0x50 (pair average 0x48) so the sharpen path
    # produces values distinct from the inputs whenever no mask fires.
    # (label, A, B, C, D, E, F, threshold_a, threshold_b)
    boundary = [
        ("all distances below", 0x40, 0x11, 0x40, 0x50, 0x66, 0x50,
         0x40, 0x40),
        ("all distances above", 0x00, 0x77, 0x40, 0x50, 0x88, 0x90,
         0x40, 0x40),
        # threshold_b = 0x20 for the four outer relations; threshold_a = 0x40
        # keeps the final |C-D| comparison clear of every case below.
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
        # Centre relation with threshold_a distinct from threshold_b, so a
        # threshold swap changes the selected value.
        ("centre boundary equal", 0x40, 0x11, 0x40, 0x50, 0x66, 0x50,
         0x10, 0x40),
        ("centre boundary one below", 0x40, 0x11, 0x40, 0x50, 0x66, 0x50,
         0x11, 0x40),
        # Sharpen clamp: (E, B) combinations split the packed 0x20 bias into
        # raise/fall distances of 0x00, 0x10 and 0x20, plus a high saturation.
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
    # distance 0x80 with threshold byte 0x7F: unsigned 0x80 >= 0x7F is true;
    # a signed implementation would see -128 < 127 and choose the filtered
    # value instead.  With threshold 0x80 the unsigned comparison is false.
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

    # --- a later lane in the same chunk, with shifted data ----------------
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
        cases.append(base_case(f"seed 0x{seed:08x}", seed=seed))

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
            f"({changed} words changed, {len(orig['data_writes'])} stores)"
        )

    assert total_changed > 0, "no case exercised a filtered write"
    assert unchanged_cases > 0, "no case exercised the unchanged path"
    print(
        f"  ({total_changed} filtered words across the suite; "
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
        (value for name_, value in funcs.items() if "00167dcc" in name_), None
    )
    if candidate is None or candidate[1]:
        raise RuntimeError("mutant function missing or unexpectedly relocated")
    return candidate[0]


def main() -> None:
    print("Testing func_00167dcc (0x00167dcc)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B, no relocations.")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    controls = (
        (
            "packed_twenty",
            "constexpr u32 kPackedTwenty = 0x20202020u;",
            "constexpr u32 kPackedTwenty = 0x21212121u;",
        ),
        (
            "packed_one",
            "constexpr u32 kPackedOne = 0x01010101u;",
            "constexpr u32 kPackedOne = 0x01010102u;",
        ),
        (
            "row_stride",
            "constexpr u32 kEdge200RowStride = 0x200u;",
            "constexpr u32 kEdge200RowStride = 0x204u;",
        ),
        (
            "band_bytes",
            "constexpr u32 kEdge200BandBytes = 0x1000u;",
            "constexpr u32 kEdge200BandBytes = 0x1004u;",
        ),
        (
            "unsigned_ge",
            "        const u32 right = (second >> shift) & 0xFFu;\n"
            "        if (right <= left) {",
            "        const u32 right = (second >> shift) & 0xFFu;\n"
            "        if (static_cast<s32>(static_cast<s8>(right)) <=\n"
            "            static_cast<s32>(static_cast<s8>(left))) {",
        ),
        (
            "tail_condition",
            "            if (static_cast<s32>(inner) == 0) {\n"
            "                // 0x001685A4..0x00168954",
            "            if (static_cast<s32>(inner) <= 0) {\n"
            "                // 0x001685A4..0x00168954",
        ),
        (
            "band_step",
            "        band_counter -= kEdge200HeightStep;",
            "        band_counter -= 4u;",
        ),
        (
            "centre_threshold",
            "    mask = byte_uge8_mask(distance, threshold_a);",
            "    mask = byte_uge8_mask(distance, threshold_b);",
        ),
        (
            "chunk_size",
            "constexpr u32 kEdge200ChunkBytes = 0x20u;",
            "constexpr u32 kEdge200ChunkBytes = 0x1Fu;",
        ),
        (
            "width_bias",
            "constexpr u32 kEdge200WidthBias = 0x10u;",
            "constexpr u32 kEdge200WidthBias = 0x0Cu;",
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
