#!/usr/bin/env python3
"""Differential test for func_001c0610 (0x001c0610) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the func_001c0610 body,
resolves its direct calls to deterministic stubs, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log of the single 0x0035EFBC call: object pointer, mode,
    stack count, the 16-word input table and the 16-word pre-call buffer;
  * the 64-byte buffer produced by the stub (read back after the call);
  * the exact control/work bytes at 0x004E0E88..0x004E1F64 (sentinels make
    every untouched word visible) and the caller word page;
  * any emulated write outside the private stack and that control/work range.

The candidate zeroes its 0x40-byte stack buffer through the compiler runtime
helper `__aeabi_memclr8` (the pinned original inlines the stores); the runner
links a real zero-fill implementation at a private address, so the helper is
part of the environment rather than of the compared call log.

Coverage: gate bit set/clear, zero/odd/even/clamped/negative counts, the signed
16-word clamp boundary (0x10 / 0x11), every helper sign-bit form, zero and
non-zero buffer words (including bit 31), every result slot, and source arrays
that alias the global input/result tables.
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
OUT_DIR = ROOT / "build/test_leaf_001c0610"

FUNC_ADDR = 0x001C0610
FUNC_SIZE = 476

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the function and the 0x0035EFBC stub
GLOBAL_PAGE = 0x004E0000
GLOBAL_SIZE = 0x00010000
CONTROL_ADDR = 0x004E0E88   # control block (literal 0x001C07DC)
WORK_ADDR = 0x004E1E88      # scratch block (control + 0x1000)
TABLE_ADDR = 0x004E1ED4     # copied input table (literal 0x001C07E4)
RESULT_ADDR = 0x004E1F14    # result table (literal 0x001C07E8)
OBJECT_ADDR = 0x004E0E90    # control + 8, first argument of 0x0035EFBC
SNAPSHOT_START = CONTROL_ADDR
SNAPSHOT_END = 0x004E1F64

SOURCE_PAGE = 0x00700000
SOURCE_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_HELPER = 0x0035EFBC
STUB_MEMCLR = 0x00380000   # private address for the compiler runtime helper
STUB_NAMES = {STUB_HELPER: "engine_func_0035efbc"}

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

SNAPSHOT_SIZE = SNAPSHOT_END - SNAPSHOT_START
WORD_COUNT = 16


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("func_001c0610")
    if candidate is None:
        raise RuntimeError(
            f"func_001c0610 not found in {obj_file}: {sorted(funcs)}"
        )
    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type != 28:  # only R_ARM_CALL is expected
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        if "0035efbc" in rel.symbol_name:
            target = STUB_HELPER
        elif "aeabi_memclr8" in rel.symbol_name:
            target = STUB_MEMCLR
        else:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        delta = target - pc
        if delta % 4:
            raise RuntimeError(f"unaligned call target 0x{target:08x}")
        original = struct.unpack_from("<I", code, rel.offset)[0]
        if (original & 0x0F000000) != 0x0B000000:
            raise RuntimeError(
                f"relocation at 0x{rel.offset:x} is not a BL: 0x{original:08x}"
            )
        cond = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, cond | ((delta >> 2) & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
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
DEFAULT_SOURCE = [
    0x11111111, 0x22222222, 0x33333333, 0x00000000,
    0x44444444, 0x55555555, 0x66666666, 0x77777777,
    0x88888888, 0x99999999, 0xAAAAAAAA, 0xBBBBBBBB,
    0xCCCCCCCC, 0xDDDDDDDD, 0xEEEEEEEE, 0xFFFFFFFF,
]

ZERO_FILL = [0] * WORD_COUNT


def pattern_word(address: int) -> int:
    return 0xC0DE0000 | ((address - CONTROL_ADDR) & 0xFFFF)


def build_globals(case: dict) -> bytes:
    """Sentinels everywhere, then the case-controlled control words."""
    page = bytearray(GLOBAL_SIZE)
    base_offset = CONTROL_ADDR - GLOBAL_PAGE
    for index in range(SNAPSHOT_SIZE // 4):
        struct.pack_into(
            "<I", page, base_offset + index * 4,
            pattern_word(CONTROL_ADDR + index * 4),
        )
    struct.pack_into("<I", page, base_offset + 0x00, case.get("state", 1))
    struct.pack_into("<I", page, base_offset + 0x04, case.get("status", 0))
    return bytes(page)


def build_source_page(case: dict) -> bytes:
    page = bytearray(SOURCE_SIZE)
    for index in range(SOURCE_SIZE // 4):
        struct.pack_into("<I", page, index * 4, pattern_word(SOURCE_PAGE + index * 4))
    words = list(case.get("source", DEFAULT_SOURCE))[:WORD_COUNT]
    if len(words) != WORD_COUNT:
        raise RuntimeError("source fixtures need exactly 16 words")
    for index, word in enumerate(words):
        struct.pack_into("<I", page, index * 4, word & 0xFFFFFFFF)
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at fixed addresses."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBAL_PAGE, GLOBAL_SIZE)
        self.uc.mem_map(SOURCE_PAGE, SOURCE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        self.uc.mem_write(STUB_HELPER, struct.pack("<I", 0xE12FFF1E))  # bx lr
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_helper, begin=STUB_HELPER,
            end=STUB_HELPER,
        )
        self.uc.mem_write(STUB_MEMCLR, struct.pack("<I", 0xE12FFF1E))  # bx lr
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_memclr, begin=STUB_MEMCLR,
            end=STUB_MEMCLR,
        )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.buffer_ptr = 0
        self.memclr_calls = 0
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _words(self, address: int, count: int) -> tuple:
        raw = self.uc.mem_read(address, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_memclr(self, uc, address: int, size: int, user_data) -> None:
        # __aeabi_memclr8(dest, bytes): zero the range, return dest in r0.
        dest = uc.reg_read(arm.UC_ARM_REG_R0)
        count = uc.reg_read(arm.UC_ARM_REG_R1)
        uc.mem_write(dest, b"\x00" * count)
        uc.reg_write(arm.UC_ARM_REG_R0, dest)
        self.memclr_calls += 1

    def _on_helper(self, uc, address: int, size: int, user_data) -> None:
        obj = uc.reg_read(arm.UC_ARM_REG_R0)
        out = uc.reg_read(arm.UC_ARM_REG_R1)
        mode = uc.reg_read(arm.UC_ARM_REG_R2)
        table = uc.reg_read(arm.UC_ARM_REG_R3)
        sp = uc.reg_read(arm.UC_ARM_REG_SP)
        count = struct.unpack("<I", uc.mem_read(sp, 4))[0]
        table_words = self._words(table, WORD_COUNT)
        before = self._words(out, WORD_COUNT)

        self.call_log.append(
            (
                STUB_NAMES[address],
                obj,
                mode,
                count,
                table_words,
                before,
            )
        )
        self.buffer_ptr = out
        self.case["observed_table"] = table_words

        result = self.case.get("helper_ret", 0) & 0xFFFFFFFF
        if not (result & 0x80000000):
            fill = list(self.case.get("fill", ZERO_FILL))[:WORD_COUNT]
            if len(fill) != WORD_COUNT:
                raise RuntimeError("buffer fixtures need exactly 16 words")
            payload = b"".join(struct.pack("<I", word & 0xFFFFFFFF) for word in fill)
            uc.mem_write(out, payload)
        uc.reg_write(arm.UC_ARM_REG_R0, result)

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.buffer_ptr = 0
        self.memclr_calls = 0
        self.case = dict(case)

        self.uc.mem_write(FUNC_ADDR, b"\x00" * 0x400)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(GLOBAL_PAGE, build_globals(case))
        self.uc.mem_write(SOURCE_PAGE, build_source_page(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        values_addr = case.get("values_addr", SOURCE_PAGE)
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, values_addr)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("count", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        buffer = b""
        if self.buffer_ptr:
            buffer = bytes(self.uc.mem_read(self.buffer_ptr, 4 * WORD_COUNT))

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_globals = SNAPSHOT_START <= address < SNAPSHOT_END
            if not in_stack and not in_globals:
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "buffer": buffer,
            "globals": bytes(
                self.uc.mem_read(SNAPSHOT_START, SNAPSHOT_SIZE)
            ),
            "source_page": bytes(self.uc.mem_read(SOURCE_PAGE, SOURCE_SIZE)),
            "memclr_calls": self.memclr_calls,
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
    if orig["buffer"] != cand["buffer"]:
        problems.append(
            f"buffer:\n    orig={orig['buffer'].hex()}\n    cand={cand['buffer'].hex()}"
        )
    if orig["globals"] != cand["globals"]:
        diffs = [
            (index, left, right)
            for index, (left, right) in enumerate(
                zip(orig["globals"], cand["globals"])
            )
            if left != right
        ]
        problems.append(
            "globals differ at "
            + ", ".join(
                f"+0x{index:04x}: orig=0x{left:02x} cand=0x{right:02x}"
                for index, left, right in diffs[:12]
            )
        )
    if orig["source_page"] != cand["source_page"]:
        problems.append("source page was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "state": 1,
        "status": 0,
        "count": WORD_COUNT,
        "source": list(DEFAULT_SOURCE),
        "fill": list(ZERO_FILL),
        "helper_ret": 0,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- gate bit at 0x004E0E88
    cases.append(base_case("gate clear, count 4", state=0xFFFFFFFE, count=4))
    cases.append(base_case("gate clear with other bits", state=2, count=0))
    cases.append(base_case("gate clear all bits but 0", state=0xAAAAAAAA, count=7))
    cases.append(base_case("gate set with all bits", state=0xFFFFFFFF, count=4))

    # --- count boundaries: 0, odd/even, clamp at 16
    cases.append(base_case("count 0 early exit", count=0, status=0x12340000))
    cases.append(base_case("count 0 with nonzero buffer", count=0,
                           fill=[0xDEADBEEF] * WORD_COUNT))
    cases.append(base_case("count 1 odd", count=1, fill=[0xDEADBEEF] + [0] * 15))
    cases.append(base_case("count 1, buffer zero", count=1))
    cases.append(base_case("count 2 even", count=2, fill=[0, 0xCAFEBABE] + [0] * 14))
    cases.append(base_case("count 3 odd", count=3,
                           fill=[0x10101010, 0, 0x30303030] + [0] * 13))
    cases.append(base_case("count 8", count=8,
                           fill=[0x11110000, 0, 0x33330000, 0,
                                 0x55550000, 0, 0x77770000, 0] + [0] * 8))
    cases.append(base_case("count 15 odd", count=15,
                           fill=[0x01020304] * 15 + [0]))
    cases.append(base_case("count 16 maximum", count=16,
                           fill=[0x01020304 + index for index in range(16)]))
    cases.append(base_case("count 16 all zero", count=16))
    cases.append(base_case("count 17 clamps to 16", count=17,
                           fill=[0x51515151 + index for index in range(16)]))
    cases.append(base_case("count 0x7FFFFFFF clamps", count=0x7FFFFFFF,
                           fill=[0x61616161] * 16))
    cases.append(base_case("count 0x7FFFFFF8 clamps", count=0x7FFFFFF8,
                           fill=[0x71717171] * 16))
    cases.append(base_case("count 0x10 boundary", count=0x10,
                           fill=[0] * 15 + [0x0F0F0F0F]))
    cases.append(base_case("count 0x0F boundary", count=0x0F,
                           fill=[0] * 15 + [0x0F0F0F0F]))
    cases.append(base_case("count 0x11 boundary", count=0x11,
                           source=[0x12121212] * 16, fill=[0] * 16))

    # --- negative requests: signed clamp keeps them, helper sign decides
    for count in (-1, -2, 0x80000000, 0xFFFF0000):
        cases.append(base_case(
            f"count 0x{count & 0xFFFFFFFF:08x} helper negative", count=count,
            helper_ret=0x80000000, fill=[0xDEADBEEF] * 16))
        cases.append(base_case(
            f"count 0x{count & 0xFFFFFFFF:08x} helper zero", count=count,
            helper_ret=0, fill=[0xDEADBEEF] * 16))

    # --- helper result sign bit
    for result in (0, 1, 0x7FFFFFFF, 0x80000000, 0x80000001, 0xFFFFFFFF,
                   0xD820EBF8):
        cases.append(base_case(
            f"helper result 0x{result:08x}", count=16, helper_ret=result,
            fill=[0x31313131 + index for index in range(16)]))

    # --- buffer words: zero/non-zero mix, bit-31 values, out-of-limit words
    cases.append(base_case(
        "buffer mixed zero and non-zero", count=16,
        fill=[0, 1, 0, 0x80000000, 0xFFFFFFFF, 0, 0, 2,
              0, 0, 0x7FFFFFFF, 0, 3, 0, 0, 4]))
    cases.append(base_case(
        "buffer nonzero beyond limit 3", count=3,
        fill=[0x11111111, 0, 0, 0x44444444, 0x55555555] + [0x66666666] * 11))
    cases.append(base_case(
        "buffer nonzero at index 8 with limit 9", count=9,
        fill=[0] * 8 + [0x88888888] + [0x99999999] * 7))
    cases.append(base_case(
        "buffer nonzero at index 15 with limit 15", count=15,
        fill=[0] * 15 + [0xFFFFFFFF]))
    cases.append(base_case(
        "buffer bit 31 only", count=4,
        fill=[0x80000000, 0x80000000, 0x80000000, 0x80000000] + [0] * 12))

    # --- pre-existing status word bits are preserved by the ORs
    for status in (0x00000001, 0xFFFF0000, 0xFFFFFFFF, 0x00010000,
                   0x00040000):
        cases.append(base_case(
            f"status 0x{status:08x} success", count=4, status=status,
            fill=[0xAAAA0001, 0, 0xBBBB0002, 0] + [0] * 12))
        cases.append(base_case(
            f"status 0x{status:08x} error", count=4, status=status,
            helper_ret=0x80000000))

    # --- source arrays: zeros, aliases of the global tables, other page words
    cases.append(base_case(
        "source zeros and max", count=16,
        source=[0, 0xFFFFFFFF] * 8))
    cases.append(base_case(
        "source aliases result table", count=4,
        values_addr=RESULT_ADDR, fill=[0x11110000, 0x22220000, 0, 0x44440000]
        + [0] * 12))
    cases.append(base_case(
        "source aliases input table", count=4,
        values_addr=TABLE_ADDR, fill=[0x11110000, 0x22220000, 0, 0x44440000]
        + [0] * 12))
    cases.append(base_case(
        "source aliases input table odd", count=5,
        values_addr=TABLE_ADDR, fill=[0x11110000] * 5 + [0] * 11))
    cases.append(base_case(
        "source inside page", count=16,
        values_addr=SOURCE_PAGE + 0x100,
        source=[0x01010101 * (index + 1) for index in range(16)]))
    cases.append(base_case(
        "errors latch over existing bits", count=16, status=0x00020000,
        helper_ret=0x80000000, fill=[0xDEADBEEF] * 16))

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
        print(
            f"  [PASS] {case['name']}  (ret=0x{orig['ret']:08x}, "
            f"{len(orig['call_log'])} call(s))"
        )
    return passed


def main() -> None:
    print("Testing func_001c0610 (0x001c0610)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("gate_bit", "constexpr u32 kInitializedBit = 1;",
         "constexpr u32 kInitializedBit = 2;"),
        ("max_words", "constexpr s32 kMaxWords = 0x10;",
         "constexpr s32 kMaxWords = 0x0F;"),
        ("error_flag", "constexpr u32 kErrorFlag = 0x00040000;",
         "constexpr u32 kErrorFlag = 0x00010000;"),
        ("result_flag", "constexpr u32 kResultFlag = 0x00020000;",
         "constexpr u32 kResultFlag = 0x00010000;"),
        ("done_flag", "constexpr u32 kDoneFlag = 0x00010000;",
         "constexpr u32 kDoneFlag = 0x00020000;"),
        ("helper_mode", "constexpr u32 kHelperMode = 1;",
         "constexpr u32 kHelperMode = 2;"),
        ("result_address", "return kResultTableAddress;",
         "return kResultTableAddress + 4;"),
        ("odd_copy", "area->input_4C[0] = values[0];",
         "area->input_4C[0] = values[1];"),
    ):
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
