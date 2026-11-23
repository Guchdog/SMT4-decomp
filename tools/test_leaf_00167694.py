#!/usr/bin/env python3
"""Differential test for func_00167694 (0x00167694) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the func_00167694 body and
runs the pinned original (extracted/exefs/code.bin) against the compiled
candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0 (the state pointer), continuation PC and final SP;
  * the complete 0x20000-byte plane-data page and the 0x1000-byte state page
    (every observable byte both read and written by the routine);
  * every emulated write, which must land inside the plane-data page (the
    routine keeps its 0x14-byte frame in an unobservable private stack area).

The original body clobbers r4-r11 without saving them (it is an ABI-violating
leaf).  Those register values are only leftovers of the scratch allocation, so
instead of demanding equal scratch values the test asserts that the compiled
candidate preserves r4-r11 and records the original values.

Coverage: both loop shapes (narrow widths <= 0x20 taking the 0x00167C7C path
and wider widths taking the four-group 0x20-byte chunk loop), the 8-byte tail
loop both entered and skipped, one to four row blocks, the signed counter
comparisons around 0x20, threshold bytes 0x00/0x01/0x7F/0x80/0xFF (signed lane
boundary) with zero and non-zero upper threshold bytes, and pseudo-random
plane data including saturated lane differences.
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
OUT_DIR = ROOT / "build/test_leaf_00167694"

FUNC_ADDR = 0x00167694
FUNC_SIZE = 1848

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00100000  # covers the function body
STATE_ADDR = 0x00700000
STATE_SIZE = 0x00001000
DATA_ADDR = 0x00500000
DATA_SIZE = 0x00020000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
DATA_OFFSET = 0x400

# The original body loads `ip` and `lr` from the literal pool that sits in the
# eight bytes immediately before its entry point (0x0016768C/0x00167690, the
# tail of the preceding routine):
#   0x001676B4  ldr ip, [pc, #-0x30]  -> 0x01010101
#   0x001676B8  ldr lr, [pc, #-0x30]  -> 0x20202020
# Those words are outside the 1848-byte body, so the fixture must plant them.
LITERAL_POOL_ADDR = 0x0016768C
LITERAL_POOL_SIZE = 8
LITERAL_POOL_WORDS = (0x01010101, 0x20202020)

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


def extract_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    for name, value in funcs.items():
        if "00167694" in name:
            code, relocs = value
            if relocs:
                raise RuntimeError(
                    "func_00167694 must be self-contained, found relocations: "
                    f"{relocs}"
                )
            return code
    raise RuntimeError(
        f"func_00167694 not found in {obj_file}: {sorted(funcs)}"
    )


def compile_candidate(source: Path = SOURCE, stem: str = "leaf_batch34_c") -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / f"{stem}.o"
    res = compile_tu_armv6k(source, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return extract_candidate(obj_file)


def compile_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant_src, f"mutant_{name}")


# ------------------------------------------------------------------- fixtures
def lcg_bytes(seed: int, size: int) -> bytes:
    state = seed & 0xFFFFFFFF
    out = bytearray(size)
    for index in range(size):
        state = (state * 1103515245 + 12345) & 0xFFFFFFFF
        out[index] = (state >> 16) & 0xFF
    return bytes(out)


def build_state(case: dict) -> bytes:
    page = bytearray(STATE_SIZE)
    struct.pack_into("<I", page, 0x04, DATA_ADDR + DATA_OFFSET)
    struct.pack_into("<I", page, 0x08, case["cols"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x0C, case["rows"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x10, case["threshold_a"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x14, case["threshold_b"] & 0xFFFFFFFF)
    # Sentinel words around the consumed fields: the routine must not touch
    # them, and the comparison below covers the whole page.
    struct.pack_into("<I", page, 0x00, 0xD00DFEED)
    struct.pack_into("<I", page, 0x18, 0x0BADF00D)
    return bytes(page)


class Runner:
    """One Unicorn machine; the routine is a leaf with no helper calls."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(STATE_ADDR, STATE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        with open(ORIG_BIN, "rb") as pool_source:
            pool_source.seek(LITERAL_POOL_ADDR - 0x00100000)
            pool = pool_source.read(LITERAL_POOL_SIZE)
        if struct.unpack("<II", pool) != LITERAL_POOL_WORDS:
            raise RuntimeError(f"unexpected literal pool contents {pool.hex()}")
        self.uc.mem_write(LITERAL_POOL_ADDR, pool)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.writes: list = []

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def run(self, code: bytes, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(STATE_ADDR, build_state(case))
        self.uc.mem_write(DATA_ADDR, case["data"])
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, STATE_ADDR)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=20_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        # Stack traffic is private scratch: the original keeps a 0x14-byte
        # frame below the entry SP and the compiled candidate uses its own
        # frame layout, so only writes outside DATA+STACK are stray.
        unexpected_writes = [
            (address, size)
            for address, size in self.writes
            if not (
                DATA_ADDR <= address < DATA_ADDR + DATA_SIZE
                or STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            )
        ]
        data_writes = [
            (address, size)
            for address, size in self.writes
            if DATA_ADDR <= address < DATA_ADDR + DATA_SIZE
        ]

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "state": bytes(self.uc.mem_read(STATE_ADDR, STATE_SIZE)),
            "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "unexpected_writes": unexpected_writes,
            "write_count": len(data_writes),
            "data_write_sizes": sorted({size for _address, size in data_writes}),
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp"):
        if orig[key] != cand[key]:
            problems.append(f"{key}: orig={orig[key]!r} cand={cand[key]!r}")
    if orig["state"] != cand["state"]:
        first = next(
            index
            for index, (a, b) in enumerate(zip(orig["state"], cand["state"]))
            if a != b
        )
        problems.append(f"state page differs at +0x{first:x}")
    if orig["data"] != cand["data"]:
        diffs = [
            index
            for index, (a, b) in enumerate(zip(orig["data"], cand["data"]))
            if a != b
        ]
        problems.append(
            f"data page differs in {len(diffs)} bytes, first at "
            f"+0x{diffs[0]:x}: orig=0x{orig['data'][diffs[0]]:02x} "
            f"cand=0x{cand['data'][diffs[0]]:02x}"
        )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "writes outside the plane data / stack: "
            f"orig={orig['unexpected_writes'][:8]} "
            f"cand={cand['unexpected_writes'][:8]}"
        )
    if orig["write_count"] != cand["write_count"]:
        problems.append(
            f"plane-data store count: orig={orig['write_count']} "
            f"cand={cand['write_count']}"
        )
    if cand["data_write_sizes"] != [1]:
        problems.append(
            f"candidate plane-data store widths {cand['data_write_sizes']} "
            "(the original issues byte stores)"
        )
    return problems


def case(name: str, cols: int, rows: int = 4, threshold_a: int = 0x20,
         threshold_b: int = 0x30, seed: int = 1) -> dict:
    return {
        "name": name,
        "cols": cols,
        "rows": rows,
        "threshold_a": threshold_a,
        "threshold_b": threshold_b,
        "data": lcg_bytes(seed, DATA_SIZE),
    }


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- wide path, full plane width: 0x20-byte chunks plus the 8-byte tail
    cases.append(case("cols 0x200 rows 4", 0x200, seed=0x1111))
    cases.append(case("cols 0x200 rows 8", 0x200, rows=8, seed=0x2222))
    cases.append(case("cols 0x200 rows 0x10", 0x200, rows=0x10, seed=0x3333))
    cases.append(case("cols 0x1F0 rows 4", 0x1F0, seed=0x4444))
    cases.append(case("cols 0x1E0 rows 8", 0x1E0, rows=8, seed=0x5555))
    cases.append(case("cols 0x220 crosses plane stride", 0x220, seed=0x6666))

    # --- tail loop skipped exactly (cols % 0x20 == 8)
    cases.append(case("cols 0x28 tail skipped", 0x28, seed=0x7777))
    cases.append(case("cols 0x48 tail skipped", 0x48, seed=0x8888))
    cases.append(case("cols 0x68 tail skipped", 0x68, rows=8, seed=0x9999))

    # --- tail loop entered with a negative remainder
    cases.append(case("cols 0x21", 0x21, seed=0xAAAA))
    cases.append(case("cols 0x27", 0x27, seed=0xBBBB))
    cases.append(case("cols 0x3F", 0x3F, seed=0xCCCC))
    cases.append(case("cols 0x40", 0x40, seed=0xDDDD))
    cases.append(case("cols 0x41", 0x41, seed=0xEEEE))

    # --- narrow path below/at the 0x20 boundary
    cases.append(case("cols 0x20 narrow boundary", 0x20, seed=0x1234))
    cases.append(case("cols 0x1F narrow", 0x1F, seed=0x2345))
    cases.append(case("cols 0x18 narrow", 0x18, seed=0x3456))
    cases.append(case("cols 0x10 narrow", 0x10, seed=0x4567))
    cases.append(case("cols 0x08 narrow", 0x08, seed=0x5678))
    cases.append(case("cols 0x04 narrow", 0x04, seed=0x6789))
    cases.append(case("cols 0x00 narrow", 0x00, rows=8, seed=0x789A))

    # --- signed-counter boundary around 0x20 on the 32-bit wrap side
    cases.append(case("cols 0x80000020 signed negative", 0x80000020, seed=0x89AB))
    cases.append(case("cols 0xFFFFFFFF signed negative", 0xFFFFFFFF, seed=0x9ABC))

    # --- thresholds: zero disables the keep-source select, 0xFF enables it
    for a in (0x00, 0x01, 0x7F, 0x80, 0xFF):
        for b in (0x00, 0x01, 0x7F, 0x80, 0xFF):
            cases.append(
                case(f"thresholds a=0x{a:02X} b=0x{b:02X}", 0x200,
                     threshold_a=a, threshold_b=b, seed=0xA000 + a * 16 + b)
            )

    # --- upper threshold bytes are folded into every lane by the orr chain
    cases.append(case("threshold words with high bytes", 0x40,
                      threshold_a=0x12345678, threshold_b=0x9ABCDEF0,
                      seed=0xBEEF))
    cases.append(case("threshold words 0xFFFFFFFF", 0x48,
                      threshold_a=0xFFFFFFFF, threshold_b=0xFFFFFFFF,
                      seed=0xCAFE))

    # --- pseudo-random combinations of width, rows and thresholds
    widths = (0x200, 0x1F8, 0x48, 0x28, 0x21, 0x20, 0x18, 0x0C)
    for index in range(10):
        cases.append(
            case(
                f"random {index}",
                widths[index % len(widths)],
                rows=4 * (1 + index % 3),
                threshold_a=(index * 37 + 11) & 0xFF,
                threshold_b=(index * 53 + 7) & 0xFF,
                seed=0xF000 + index,
            )
        )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for item in cases:
        orig = Runner().run(orig_code, item)
        cand = Runner().run(cand_code, item)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {item['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        # The compiled candidate must obey the callee-saved register contract.
        for name, value in CALLEE_SAVED_START.items():
            if cand["callee_saved"][name] != value:
                print(f"  [FAIL] {item['name']}: candidate clobbers {name}")
                raise SystemExit(1)
        passed += 1
        print(
            f"  [PASS] {item['name']}  ({orig['write_count']} byte stores, "
            f"{len(orig['unexpected_writes'])} stray)"
        )
    return passed


def main() -> None:
    print("Testing func_00167694 (0x00167694)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(self-contained, no relocations)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("store_offset", "base[plane * 0x200 + 7]", "base[plane * 0x200 + 6]"),
        ("rounding_bias", "constexpr u32 kHalf = 0x20202020u;",
         "constexpr u32 kHalf = 0x20202021u;"),
        ("row_advance", "base += 0x7E8;  // 0x800 - 0x18",
         "base += 0x7E0;  // 0x800 - 0x18"),
        ("narrow_boundary", "if (static_cast<s32>(counter) <= 0) {",
         "if (static_cast<s32>(counter) < 0) {"),
        ("threshold_swap", "Ssub8GeMask(blend3, threshold_a)",
         "Ssub8GeMask(blend3, threshold_b)"),
    ):
        mutant_code = compile_mutant(name, old, new)
        detected = False
        for item in cases:
            orig = Runner().run(orig_code, item)
            bad = Runner().run(mutant_code, item)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
