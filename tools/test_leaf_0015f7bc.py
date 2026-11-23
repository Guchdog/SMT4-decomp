#!/usr/bin/env python3
"""Differential test for func_0015f7bc (0x0015f7bc) using Unicorn ARM.

Compiles ``src/engine/leaf_batch34_c.cpp``, extracts the candidate body, and runs
the pinned original (``extracted/exefs/code.bin``) against the candidate in two
separate Unicorn machines with identical fixtures.

The function has no calls and no relocations, so there is no helper to stub.
Compared outputs:
  * return r0 (the config pointer), continuation PC and final SP;
  * the complete filtered data page and the config page;
  * any write outside the data page and the private stack.

Callee-saved registers: the original saves only r0/lr and therefore clobbers
r4-r11 (an ABI violation).  The candidate is a normal AAPCS function and must
preserve them.  The test consequently checks the candidate against the entry
sentinels and documents that the original clobbers them instead of comparing
two undefined register values.

Coverage: inner counter values 0, 8, 16, 24, 32 and 40 bytes (both the exact
zero tail and the negative early exit); outer band counts 1-5; threshold bytes
0x00, 0x01, 0x20, 0x7F, 0x80 and 0xFF; prefix-OR thresholds with non-zero high
bytes; and explicit signed/unsigned boundary differences at the first lane.
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
OUT_DIR = ROOT / "build/test_leaf_0015f7bc"

FUNC_ADDR = 0x0015F7BC
FUNC_SIZE = 1000

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
DATA_BASE = DATA_ADDR + 0x2000

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


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")

    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next(
        (value for name, value in funcs.items() if "0015f7bc" in name), None
    )
    if candidate is None:
        raise RuntimeError(f"func_0015f7bc not found in {obj_file}: {sorted(funcs)}")
    code, relocs = candidate
    if relocs:
        raise RuntimeError(f"unexpected relocations in func_0015f7bc: {relocs}")
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
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.writes: list = []

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def run(self, code: bytes, case: dict) -> dict:
        data = build_data(case)
        config = build_config(case)
        self.uc.mem_write(CODE_ADDR, b"\x00" * CODE_SIZE)
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
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        expected_unused = case.get("unused0", 0xA5A50000)
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
            "expected_unused": expected_unused,
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


def first_lane_offsets() -> dict:
    centre = 0x2000  # relative to DATA_BASE
    return {
        "above": centre - 0x800,
        "lower": centre - 0x400,
        "upper": centre,
        "below": centre + 0x400,
    }


def lane_words(above: int, lower: int, upper: int, below: int) -> dict:
    offsets = first_lane_offsets()
    return {
        offsets["above"]: above * 0x01010101,
        offsets["lower"]: lower * 0x01010101,
        offsets["upper"]: upper * 0x01010101,
        offsets["below"]: below * 0x01010101,
    }


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "width_bytes": 24,
        "height_bytes": 16,
        "threshold_a": 0x20,
        "threshold_b": 0x20,
        "seed": 0x12345678,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases = []

    # --- inner counter / trailing-tail boundaries -------------------------
    # width_bytes - 8 = {0, 8, 16, 24, 32, 40}; 16 and 32 hit the exact-zero tail.
    for width in (8, 16, 24, 32, 40, 48):
        cases.append(base_case(f"inner {width - 8} bytes"))
        cases.append(base_case(f"inner {width - 8} bytes threshold 0", threshold_a=0))
        cases.append(
            base_case(f"inner {width - 8} bytes threshold 0xFF",
                      threshold_a=0xFF, threshold_b=0xFF)
        )

    # --- outer band count --------------------------------------------------
    for height in (16, 24, 32, 40, 48):
        cases.append(base_case(f"bands height {height}", height_bytes=height))

    # --- threshold bytes ---------------------------------------------------
    for threshold in (0x00, 0x01, 0x20, 0x7F, 0x80, 0xFF):
        cases.append(
            base_case(
                f"thresholds 0x{threshold:02x}",
                threshold_a=threshold,
                threshold_b=threshold,
                seed=0x0F1E2D3C,
            )
        )
        cases.append(
            base_case(
                f"thresholds a=0x{threshold:02x} b=0x{0x20 if threshold else 0xFF:02x}",
                threshold_a=threshold,
                threshold_b=0x20 if threshold else 0xFF,
                seed=0x31415926,
            )
        )

    # --- prefix-OR expansion of the threshold words ------------------------
    for threshold_a, threshold_b in (
        (0x00001234, 0x00000056),
        (0x0000FF00, 0x000000FF),
        (0x80504020, 0x00000010),
    ):
        cases.append(
            base_case(
                f"prefix-or 0x{threshold_a:08x}/0x{threshold_b:08x}",
                threshold_a=threshold_a,
                threshold_b=threshold_b,
                seed=0x27182818,
            )
        )

    # --- explicit first-lane boundary values ------------------------------
    # |above - lower| == threshold (GE true, unchanged) and threshold - 1
    # (GE false, filtered); the same for |upper - below| and |lower - upper|.
    boundary = [
        ("all differences below thresholds", 0x10, 0x11, 0x12, 0x13),
        ("all differences above thresholds", 0x00, 0x40, 0x00, 0x40),
        ("above boundary equal", 0x20, 0x00, 0x12, 0x13),
        ("above boundary one below", 0x1F, 0x00, 0x12, 0x13),
        ("below boundary equal", 0x00, 0x00, 0x20, 0x00),
        ("below boundary one below", 0x00, 0x00, 0x1F, 0x00),
        ("centre boundary equal", 0x00, 0x20, 0x00, 0x00),
        ("centre boundary one below", 0x00, 0x1F, 0x00, 0x00),
        ("saturated extremes", 0xFF, 0x00, 0xFF, 0x00),
        ("zero lane", 0x00, 0x00, 0x00, 0x00),
        ("all maximum", 0xFF, 0xFF, 0xFF, 0xFF),
    ]
    for label, above, lower, upper, below in boundary:
        cases.append(
            base_case(
                f"first lane {label}",
                threshold_a=0x20,
                threshold_b=0x20,
                words=lane_words(above, lower, upper, below),
            )
        )

    # --- signed threshold comparisons (> 0x7F differences) ----------------
    # threshold 0x7F: 0x80 interpreted signed is -128 < 127 -> GE false,
    # whereas an unsigned comparison would return true.
    cases.append(
        base_case(
            "signed above difference 0x80 vs 0x7F",
            threshold_a=0x7F,
            threshold_b=0x00,
            words=lane_words(0x00, 0x80, 0x00, 0x00),
        )
    )
    cases.append(
        base_case(
            "signed below difference 0x80 vs 0x7F",
            threshold_a=0x7F,
            threshold_b=0x00,
            words=lane_words(0x00, 0x00, 0x00, 0x80),
        )
    )
    cases.append(
        base_case(
            "signed centre difference 0x80 vs 0x7F",
            threshold_a=0x00,
            threshold_b=0x7F,
            words=lane_words(0x00, 0x80, 0x00, 0x00),
        )
    )
    cases.append(
        base_case(
            "signed centre difference 0xFF vs 0x7F",
            threshold_a=0x00,
            threshold_b=0x7F,
            words=lane_words(0x00, 0xFF, 0x00, 0x00),
        )
    )
    cases.append(
        base_case(
            "signed threshold 0x80 rejects nothing",
            threshold_a=0x80,
            threshold_b=0x80,
            seed=0xCAFEBABE,
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
        print(f"  [PASS] {case['name']}  ({changed} words changed)")

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
        (value for name_, value in funcs.items() if "0015f7bc" in name_), None
    )
    if candidate is None or candidate[1]:
        raise RuntimeError("mutant function missing or unexpectedly relocated")
    return candidate[0]


def main() -> None:
    print("Testing func_0015f7bc (0x0015f7bc)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B, no relocations.")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    controls = (
        ("packed_twenty", "constexpr u32 kPackedTwenty = 0x20202020u;",
         "constexpr u32 kPackedTwenty = 0x21212121u;"),
        ("packed_one", "constexpr u32 kPackedOne = 0x01010101u;",
         "constexpr u32 kPackedOne = 0x01010102u;"),
        ("row_stride", "constexpr u32 kRowStride = 0x400u;",
         "constexpr u32 kRowStride = 0x404u;"),
        ("signed_ge", "        if (left >= right) {",
         "        if (static_cast<u32>(left) >= static_cast<u32>(right)) {"),
        ("tail_condition", "            if (static_cast<s32>(inner) < 0) {",
         "            if (static_cast<s32>(inner) <= 0) {"),
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
