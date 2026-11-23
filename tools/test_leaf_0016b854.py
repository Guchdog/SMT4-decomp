#!/usr/bin/env python3
"""Differential test for func_0016b854 (0x0016b854) using Unicorn ARM.

The pinned original is a hand-written leaf that the four call sites inside
func_0016ba30 enter with a private register contract (r3 destination cursor,
r4 source-index cursor, r6 fill value, r7 table base, r8 leading count,
sl/r10 byte stride).  The candidate keeps that entry contract in a small shim
and implements the row-write loop as readable C++.

Each case runs the original bytes and the candidate shim/body in separate
Unicorn machines with identical fixtures and compares:

  * return PC, SP, the preserved registers r0/r5/r6/r7/r8/r10/r11 and the two
    in/out cursors r3/r4;
  * the complete destination, source-index and lookup-table pages (the original
    reads source/table and writes only the destination);
  * any write outside the destination page and the private stack.

r9 (sb) is a scratch register in the original and r12 (ip) is caller-saved;
the contract does not preserve them, so they are recorded but not compared.
There are no direct, indirect or helper calls in this function, so the call
log is empty by construction.

Coverage: lead 0..3 (both counted loops at every boundary), byte strides that
are zero, odd, large and negative, fill values at signed 16-bit boundaries,
table words whose low halfword truncates sign/high bits, source index 0 and the
last valid table entry, and destination offsets.  Negative controls mutate the
value count, trailing count, leading count, stride units and the final value
store; every mutant must be detected.
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

SOURCE = ROOT / "src/engine/leaf_batch45_b.cpp"
ORIG_BIN = ROOT / "extracted/exefs/code.bin"
OUT_DIR = ROOT / "build/test_leaf_0016b854"

FUNC_ADDR = 0x0016B854
FUNC_SIZE = 476
BODY_ADDR = 0x00170000  # candidate C++ body; relocation target of the shim's BL

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00100000  # covers FUNC_ADDR and BODY_ADDR
DST_ADDR = 0x00600000
DST_SIZE = 0x00020000
SRC_ADDR = 0x00620000
SRC_SIZE = 0x00010000
TABLE_ADDR = 0x00630000
TABLE_SIZE = 0x00020000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x200
TABLE_ENTRIES = 0x2000

SHIM_SYMBOL = "func_0016b854"
BODY_SYMBOL = "engine_stride_row_writer"

# Registers the private contract keeps intact (in/out cursors r3/r4 compared
# separately).  r9/r12 are deliberately absent.
PRESERVED_REGS = {
    "r0": arm.UC_ARM_REG_R0,
    "r5": arm.UC_ARM_REG_R5,
    "r6": arm.UC_ARM_REG_R6,
    "r7": arm.UC_ARM_REG_R7,
    "r8": arm.UC_ARM_REG_R8,
    "r10": arm.UC_ARM_REG_R10,
    "r11": arm.UC_ARM_REG_R11,
}
CURSOR_REGS = {
    "r3": arm.UC_ARM_REG_R3,
    "r4": arm.UC_ARM_REG_R4,
}
SCRATCH_REGS = {
    "r9": arm.UC_ARM_REG_R9,
    "r12": arm.UC_ARM_REG_R12,
}
REG_START = {
    "r0": 0x00C0FFEE,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
    "r12": 0xCCCCCCCC,
}

DEFAULT_SRC = list(range(20)) + [0x1FFF]
TABLE_SPECIAL = {
    0: 0x00000000,
    1: 0xFFFFFFFF,
    2: 0x12345678,
    3: 0x00007FFF,
    4: 0xFFFF8000,
    5: 0x00010000,
    0x1FFF: 0xABCD1234,
}


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def compile_candidate(name: str | None = None,
                      mutant: tuple[str, str] | None = None) -> tuple[bytes, bytes]:
    """Compile, extract the shim/body and resolve the shim's BL to BODY_ADDR."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    src_file = SOURCE
    obj_file = OUT_DIR / "leaf_batch45_b.o"
    if mutant is not None:
        old, new = mutant
        text = SOURCE.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
        src_file = OUT_DIR / f"mutant_{name}.cpp"
        src_file.write_text(text.replace(old, new), encoding="utf-8")
        obj_file = OUT_DIR / f"mutant_{name}.o"

    result = compile_tu_armv6k(src_file, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"compilation failed: {result.stderr}")

    funcs = extract_elf_functions_detailed(obj_file)
    if SHIM_SYMBOL not in funcs or BODY_SYMBOL not in funcs:
        raise RuntimeError(f"missing symbols in {obj_file}: {sorted(funcs)}")
    shim_raw, shim_relocs = funcs[SHIM_SYMBOL]
    body, body_relocs = funcs[BODY_SYMBOL]
    if body_relocs:
        raise RuntimeError(f"body unexpectedly has relocations: {body_relocs}")

    shim = bytearray(shim_raw)
    for rel in shim_relocs:
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unexpected shim relocation {rel.relocation_type} ({rel.symbol_name})"
            )
        if BODY_SYMBOL not in rel.symbol_name:
            raise RuntimeError(f"unexpected shim call target {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (BODY_ADDR - pc) >> 2
        original = struct.unpack_from("<I", shim, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into("<I", shim, rel.offset, cond | (displacement & 0x00FFFFFF))
    return bytes(shim), body


def build_table() -> bytes:
    words = [((index * 0x9E3779B1) ^ (index << 16)) & 0xFFFFFFFF
             for index in range(TABLE_ENTRIES)]
    for index, value in TABLE_SPECIAL.items():
        words[index] = value
    return struct.pack(f"<{TABLE_ENTRIES}I", *words)


def build_dst(case: dict) -> bytes:
    # Non-zero, non-repeating halfword pattern so every store is observable.
    base = case.get("dst_pattern", 0xC3C3)
    return struct.pack("<H", base & 0xFFFF) * (DST_SIZE // 2)


def src_page(case: dict) -> bytes:
    indices = list(case.get("src", DEFAULT_SRC))
    if len(indices) < 21:
        raise RuntimeError("source index fixture needs at least 21 entries")
    padded = indices + [0] * (SRC_SIZE // 4 - len(indices))
    return struct.pack(f"<{SRC_SIZE // 4}I", *padded)


class RowRunner:
    """One fresh Unicorn machine; the original has no helper calls to stub."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DST_ADDR, DST_SIZE)
        self.uc.mem_map(SRC_ADDR, SRC_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.writes: list[tuple[int, int, int]] = []
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.call_log: list = []

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def run(self, code: bytes, body: bytes, case: dict) -> dict:
        table = build_table()
        src = src_page(case)
        dst = build_dst(case)

        self.uc.mem_write(FUNC_ADDR, code)
        if body:
            self.uc.mem_write(BODY_ADDR, body)
        self.uc.mem_write(DST_ADDR, dst)
        self.uc.mem_write(SRC_ADDR, src)
        self.uc.mem_write(TABLE_ADDR, table)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        stride = case.get("stride", 2) & 0xFFFFFFFF
        dst_start = DST_ADDR + case.get("dst_offset", 0)
        self.writes = []

        for name, value in REG_START.items():
            self.uc.reg_write(PRESERVED_REGS.get(name, CURSOR_REGS.get(
                name, SCRATCH_REGS.get(name))), value)
        self.uc.reg_write(arm.UC_ARM_REG_R3, dst_start)
        self.uc.reg_write(arm.UC_ARM_REG_R4, SRC_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R6, case.get("zero", 0) & 0xFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R7, TABLE_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R8, case.get("lead", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R10, stride)  # sl
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"crash at PC=0x{pc:08x}: {error}") from error

        outside = []
        for address, size, _value in self.writes:
            in_dst = DST_ADDR <= address and address + size <= DST_ADDR + DST_SIZE
            in_stack = STACK_ADDR <= address and address + size <= STACK_ADDR + STACK_SIZE
            if not (in_dst or in_stack):
                outside.append((address, size))

        return {
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "regs": {
                name: self.uc.reg_read(reg) for name, reg in PRESERVED_REGS.items()
            },
            "cursors": {
                name: self.uc.reg_read(reg) for name, reg in CURSOR_REGS.items()
            },
            "scratch": {
                name: self.uc.reg_read(reg) for name, reg in SCRATCH_REGS.items()
            },
            "call_log": list(self.call_log),
            "memory": {
                "dst": bytes(self.uc.mem_read(DST_ADDR, DST_SIZE)),
                "src": bytes(self.uc.mem_read(SRC_ADDR, SRC_SIZE)),
                "table": bytes(self.uc.mem_read(TABLE_ADDR, TABLE_SIZE)),
            },
            "outside_writes": outside,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("pc", "sp", "regs", "cursors", "call_log", "outside_writes"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for page, value in orig["memory"].items():
        if value != cand["memory"][page]:
            first = next(
                (i for i, (a, b) in enumerate(zip(value, cand["memory"][page])) if a != b),
                None,
            )
            problems.append(f"{page} page differs (first byte {first})")
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {"name": name, "lead": 0, "stride": 2, "zero": 0}
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- leading loop and trailing loop: lead 0..3 covers 0/3, 1/2, 2/1, 3/0
    for lead in (0, 1, 2, 3):
        cases.append(base_case(f"lead {lead}", lead=lead))

    # --- fill value (r6) boundaries, including signed 16-bit values
    for zero in (0x0000, 0x0001, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF):
        cases.append(base_case(f"fill 0x{zero:04x}", zero=zero, lead=2))

    # --- byte strides: zero, odd, small, large, negative (two's complement)
    for stride in (0x00000000, 0x00000001, 0x00000004, 0x00000006,
                   0x00000020, 0x00000100, 0x00000400):
        cases.append(base_case(f"stride 0x{stride:08x}", stride=stride, lead=2))
    for stride in (0xFFFFFFF0, 0xFFFFFFFC):
        cases.append(base_case(f"stride 0x{stride:08x}", stride=stride, lead=2,
                               dst_offset=0x8000))

    # --- destination start offsets, including an odd/unaligned start
    for offset in (0x0000, 0x0002, 0x0001, 0x0100, 0x4000, 0x8000):
        cases.append(base_case(f"dst offset 0x{offset:04x}",
                               dst_offset=offset, lead=3, stride=4))

    # --- source indices: table truncation, first and last valid entry
    cases.append(base_case("truncating table words",
                           src=[2] * 21, lead=0))
    cases.append(base_case("signed table words",
                           src=[3, 4, 5, 1] + [1] * 17, lead=1))
    cases.append(base_case("last table index",
                           src=[0x1FFF] * 21, lead=2))
    cases.append(base_case("mixed indices",
                           src=[0, 0x1FFF, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                                12, 13, 14, 15, 16, 17, 18, 19, 20],
                           lead=3, stride=6, zero=0x8000))

    # --- combined edge: lead 3 removes the trailing loop, negative stride
    cases.append(base_case("lead 3 negative stride", lead=3,
                           stride=0xFFFFFFF8, dst_offset=0x1000,
                           zero=0xFFFF))

    return cases


def run_case_set(orig_code, cand_code, cand_body, cases) -> int:
    passed = 0
    for case in cases:
        orig = RowRunner().run(orig_code, b"", case)
        cand = RowRunner().run(cand_code, cand_body, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}")
    return passed


def main() -> None:
    print("Testing func_0016b854 (0x0016b854) row writer...")
    orig_code = get_orig_bytes()
    cand_code, cand_body = compile_candidate()
    print(
        f"Original {len(orig_code)} B (460 B code + 16 B caller literal pool); "
        f"candidate shim {len(cand_code)} B, C++ body {len(cand_body)} B."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cand_body, cases)

    print("\nNegative controls:")
    mutants = (
        ("value_count",
         "for (u32 i = 0; i < 20; ++i) {",
         "for (u32 i = 0; i < 19; ++i) {"),
        ("trailing_count", "u32 tail = 3u - lead;", "u32 tail = 4u - lead;"),
        ("leading_count",
         "for (u32 i = 0; i < lead; ++i) {",
         "for (u32 i = 0; i < lead + 1u; ++i) {"),
        ("stride_units", "cursor += stride;", "cursor += stride * 2u;"),
        ("final_value",
         "\n    store(static_cast<u16>(table[*src++]));",
         "\n    store(zero);"),
    )
    for name, old, new in mutants:
        mutant_code, mutant_body = compile_candidate(name, (old, new))
        detected = False
        for case in cases:
            orig = RowRunner().run(orig_code, b"", case)
            bad = RowRunner().run(mutant_code, mutant_body, case)
            if compare(orig, bad):
                detected = True
                break
        if not detected:
            raise SystemExit(f"negative control failed: {name} was not detected")
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
