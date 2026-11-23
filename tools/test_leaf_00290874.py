#!/usr/bin/env python3
"""Differential test for script_vm_func_00290874 (0x00290874) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the script_vm_func_00290874
body, resolves its direct calls to deterministic stubs placed at the original
target addresses, and runs the pinned original (extracted/exefs/code.bin)
against the candidate in the same Unicorn machine layout with identical
fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log with every register argument (none of the six helpers
    takes a stack argument, so the architected stack-argument list is empty);
  * the manager block (0x500 bytes of fields plus the selection table), the
    pointer slot page and the auxiliary data page, byte for byte;
  * any emulated write outside the private stack (the routine itself is
    read-only: it only reads the manager and calls helpers).

Coverage:
  * mode != 0 and mode == 0, index 0/1/2/3/other/0xFFFFFFFF, column 0/1/2/other;
  * every 0x002B8B78 request id (0x6C..0x74) and the tail-branch id 0x6E;
  * page flag 0/1/0x80, both 0x002B8794 page-flag rows;
  * selection probe equal and not equal, signed/wrapped getter sums and the
    resulting 16-bit table address, predicate 0/1/2;
  * helper stubs that mutate the manager so the post-call reloads are
    observable (index/column changes made inside 0x002B8B78).

Negative controls recompile three candidate mutants (wrong request id, wrong
selection-table offset, missing post-call reload); each must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_00290874"

FUNC_ADDR = 0x00290874
FUNC_SIZE = 452

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x3F0000
DATA_ADDR = 0x00430000
DATA_SIZE = 0x00010000  # holds the 0x0043DD50 manager-pointer slot
MANAGER_ADDR = 0x00500000
MANAGER_SIZE = 0x00002000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Offsets inside the manager block (from the ARM body).
MODE_OFFSET = 0x5C4
COLUMN_OFFSET = 0x5C8
INDEX_OFFSET = 0x5D0
PAGE_FLAG_OFFSET = 0x5F1
SLOT_OFFSET = 0x660
SELECTION_BASE = 0x700
SELECTION_WORD = 0x8A

# Original direct-call targets; stubs sit at the same addresses so both the
# original bytes and the relocated candidate resolve to them.
STUB_2B8B78 = 0x002B8B78
STUB_2B8794 = 0x002B8794
STUB_29F260 = 0x0029F260
STUB_29F248 = 0x0029F248
STUB_290694 = 0x00290694
STUB_2904D0 = 0x002904D0

STUB_NAMES = {
    STUB_2B8B78: "script_vm_func_002b8b78",
    STUB_2B8794: "camp_func_002b8794",
    STUB_29F260: "camp_func_0029f260",
    STUB_29F248: "camp_func_0029f248",
    STUB_290694: "script_vm_func_00290694",
    STUB_2904D0: "script_vm_func_002904d0",
}

# None of these helpers receives a stack argument.
STACK_ARGS = {address: 0 for address in STUB_NAMES}

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


def find_candidate(obj_file: Path):
    funcs = extract_elf_functions_detailed(obj_file)
    for name, value in funcs.items():
        if "00290874" in name:
            return value
    raise RuntimeError(f"script_vm_func_00290874 not found in {obj_file}")


def relocate_candidate(obj_file: Path) -> bytes:
    code_raw, relocs = find_candidate(obj_file)
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address in STUB_NAMES:
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
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
SELECTION_OFFSET_NOTE = (
    "selection table address = manager + 0x700 + ((u32)span << 1) + 0x8A"
)


def selection_offset(first: int, second: int) -> int:
    span = (first + second) & 0xFFFFFFFF
    return (SELECTION_BASE + ((span << 1) & 0xFFFFFFFF) + SELECTION_WORD) & 0xFFFFFFFF


def build_manager(case: dict) -> bytes:
    page = bytearray(MANAGER_SIZE)
    for offset in range(0, MANAGER_SIZE, 4):
        struct.pack_into("<I", page, offset, (0xC0DE0000 | offset) & 0xFFFFFFFF)

    page[MODE_OFFSET] = case.get("mode", 0) & 0xFF
    struct.pack_into("<I", page, COLUMN_OFFSET, case.get("column", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, INDEX_OFFSET, case.get("index", 0) & 0xFFFFFFFF)
    page[PAGE_FLAG_OFFSET] = case.get("page_flag", 0) & 0xFF

    first = case.get("first", 0)
    second = case.get("second", 0)
    offset = selection_offset(first, second)
    table = case.get("table", 0) & 0xFFFF
    if offset + 2 <= MANAGER_SIZE:
        struct.pack_into("<H", page, offset, table)
        # Neighbouring halfword holds a different value so a wrong table offset
        # is observable.
        neighbour = (offset - 2) & 0xFFFFFFFF
        if neighbour + 2 <= MANAGER_SIZE:
            struct.pack_into("<H", page, neighbour, (~table) & 0xFFFF)
    else:  # pragma: no cover - case construction keeps this in range
        raise RuntimeError(f"selection offset 0x{offset:x} outside manager page")
    return bytes(page)


def build_data(case: dict) -> bytes:
    page = bytearray(DATA_SIZE)
    struct.pack_into("<I", page, 0x0043DD50 - DATA_ADDR, MANAGER_ADDR)
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(MANAGER_ADDR, MANAGER_SIZE)
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
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _apply_mutation(self) -> None:
        mutation = self.case.get("sound_mutation")
        if not mutation:
            return
        index = mutation.get("index")
        column = mutation.get("column")
        if index is not None:
            self.uc.mem_write(
                MANAGER_ADDR + INDEX_OFFSET, struct.pack("<I", index & 0xFFFFFFFF)
            )
        if column is not None:
            self.uc.mem_write(
                MANAGER_ADDR + COLUMN_OFFSET, struct.pack("<I", column & 0xFFFFFFFF)
            )

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2B8B78:
            self._log(address, r0)
            self._apply_mutation()
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                (self.case.get("sound_return", 0x01000000) + r0) & 0xFFFFFFFF,
            )
        elif address == STUB_2B8794:
            self._log(address, r0, r1, r2, r3)
            # Distinct per-argument value so forwarded r0 is argument-sensitive.
            command_return = (
                ((r0 & 0xFF) << 24)
                | ((r1 & 0xFF) << 16)
                | ((r2 & 0xFF) << 8)
                | (r3 & 0xFF)
            )
            uc.reg_write(arm.UC_ARM_REG_R0, command_return)
        elif address == STUB_29F260:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("first", 0) & 0xFFFFFFFF
            )
        elif address == STUB_29F248:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("second", 0) & 0xFFFFFFFF
            )
        elif address == STUB_290694:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("probe", 0) & 0xFFFF)
        elif address == STUB_2904D0:
            self._log(address)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("predicate", 0) & 0xFFFFFFFF
            )
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DATA_ADDR, build_data(case))
        self.uc.mem_write(MANAGER_ADDR, build_manager(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x44444444)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not in_stack:
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "fixtures": {
                "manager": bytes(self.uc.mem_read(MANAGER_ADDR, MANAGER_SIZE)),
                "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
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
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "mode": 0,
        "index": 0,
        "column": 0,
        "page_flag": 0,
        "first": 0,
        "second": 0,
        "table": 0x1234,
        "probe": 0x9999,  # mismatch by default
        "predicate": 0,
        "sound_return": 0x01000000,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- mode != 0: every early return / tail branch
    cases.append(base_case("mode=1 index=0 early return 0", mode=1, index=0))
    cases.append(base_case("mode=1 index=1 request 0x6C then return 1",
                           mode=1, index=1))
    cases.append(base_case("mode=1 index=2 column=0 request 0x6D then return 0",
                           mode=1, index=2, column=0))
    cases.append(base_case("mode=1 index=2 column=1 tail 0x6E",
                           mode=1, index=2, column=1))
    cases.append(base_case("mode=1 index=2 column=2 return 2",
                           mode=1, index=2, column=2))
    cases.append(base_case("mode=1 index=0xFFFFFFFF returns word",
                           mode=1, index=0xFFFFFFFF))
    cases.append(base_case("mode=2 acts as non-zero", mode=2, index=2,
                           column=1))
    cases.append(base_case("mode=0x80 acts as non-zero", mode=0x80, index=1))

    # --- post-call reloads: the 0x2B8B78 stub mutates the manager
    cases.append(base_case(
        "mode=1 reload index 1->2 and column->1 then tail 0x6E",
        mode=1, index=1, column=0,
        sound_mutation={"index": 2, "column": 1},
    ))
    cases.append(base_case(
        "mode=1 reload column 0->1 then tail 0x6E",
        mode=1, index=2, column=0,
        sound_mutation={"column": 1},
    ))
    cases.append(base_case(
        "mode=1 reload index 1->0 then early return 0",
        mode=1, index=1,
        sound_mutation={"index": 0},
    ))
    cases.append(base_case(
        "mode=0 reload index 1->3 and column->2 then request 0x74",
        mode=0, index=1,
        sound_mutation={"index": 3, "column": 2},
    ))

    # --- mode == 0: every request id
    cases.append(base_case("mode=0 index=0 mismatch, predicate 0"))
    cases.append(base_case("mode=0 index=1 request 0x6F", index=1))
    cases.append(base_case("mode=0 index=2 column=0 request 0x70",
                           index=2, column=0))
    cases.append(base_case("mode=0 index=2 column=1 request 0x71",
                           index=2, column=1))
    cases.append(base_case("mode=0 index=2 column=2 no request",
                           index=2, column=2))
    cases.append(base_case("mode=0 index=3 column=0 request 0x72",
                           index=3, column=0))
    cases.append(base_case("mode=0 index=3 column=1 request 0x73",
                           index=3, column=1))
    cases.append(base_case("mode=0 index=3 column=2 request 0x74",
                           index=3, column=2))
    cases.append(base_case("mode=0 index=4 no request", index=4))

    # --- page flag rows
    cases.append(base_case("page flag 1 advance rows and match",
                           page_flag=1, probe=0x1234, predicate=1))
    cases.append(base_case("page flag 0x80 advance rows and mismatch",
                           page_flag=0x80))
    cases.append(base_case("page flag 1 suppresses mismatch row",
                           page_flag=1))
    cases.append(base_case("page flag clear plays mismatch row"))

    # --- selection compare and final predicate
    cases.append(base_case("probe equals table, predicate 1",
                           probe=0x1234, predicate=1))
    cases.append(base_case("probe equals table, predicate 2 treated as true",
                           probe=0x1234, predicate=2))
    cases.append(base_case("probe mismatch, predicate 1", predicate=1))
    cases.append(base_case("probe 0 vs table 0xFFFF", table=0xFFFF, probe=0))
    cases.append(base_case("probe 0xFFFF vs table 0xFFFF",
                           table=0xFFFF, probe=0xFFFF))

    # --- signed / wrapped getter sums (16-bit table address)
    cases.append(base_case("span -1 + 0 wraps to offset 0x788",
                           first=-1, second=0, table=0xBEEF,
                           probe=0xBEEF, predicate=1))
    cases.append(base_case("span 0x7FFFFFFF + 0x7FFFFFFF wraps to 0x786",
                           first=0x7FFFFFFF, second=0x7FFFFFFF,
                           table=0xCAFE, probe=0xCAFE, predicate=1))
    cases.append(base_case("span -0x80000000 + -0x80000000 wraps",
                           first=-0x80000000, second=-0x80000000,
                           table=0x0F0F, probe=0x0F0F, predicate=1))
    cases.append(base_case("span 0x100 + 0x100 selects offset 0xB8A",
                           first=0x100, second=0x100, table=0x7777,
                           probe=0x7777, predicate=1))
    cases.append(base_case("span order 5 + 7 vs 7 + 5", first=5, second=7,
                           table=0x0101, probe=0x0101, predicate=0))
    return cases


def run_once(code: bytes, case: dict) -> dict:
    # A fresh Unicorn instance per run: the emulated code page is rewritten for
    # each input, and a new machine also guarantees no translation-cache or
    # register/memory leakage between the original, candidate and mutants.
    return Runner().run(code, case)


def main() -> int:
    print("Testing script_vm_func_00290874 (0x00290874)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"  original {len(orig_code)} B, candidate {len(cand_code)} B")

    cases = make_cases()

    failures = 0
    for case in cases:
        res_orig = run_once(orig_code, case)
        res_cand = run_once(cand_code, case)
        problems = compare(res_orig, res_cand)
        if problems:
            failures += 1
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print("    " + problem.replace("\n", "\n    "))
        else:
            print(f"  [PASS] {case['name']}")

    print(f"\n{len(cases) - failures}/{len(cases)} differential cases passed")
    if failures:
        return 1

    # ------------------------------------------------------- negative controls
    mutants = [
        (
            "request_id",
            "constexpr u32 kRequestModeIndex1 = 0x6C;",
            "constexpr u32 kRequestModeIndex1 = 0x6D;",
        ),
        (
            "table_offset",
            "constexpr u32 kSelectionWordOffset = 0x8A;",
            "constexpr u32 kSelectionWordOffset = 0x88;",
        ),
        (
            "missing_reload",
            "            script_vm_func_002b8b78(kRequestMode2Column0);\n"
            "        }\n"
            "        column = *reinterpret_cast<const volatile u32*>(\n"
            "            manager + kColumnOffset);\n"
            "        if (column != 1) {",
            "            script_vm_func_002b8b78(kRequestMode2Column0);\n"
            "        }\n"
            "        if (column != 1) {",
        ),
    ]

    detected = 0
    for name, old, new in mutants:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected_on = None
        for case in cases:
            res_orig = run_once(orig_code, case)
            res_cand = run_once(mutant_code, case)
            if compare(res_orig, res_cand):
                detected_on = case["name"]
                break
        if detected_on is None:
            print(f"  [FAIL] negative control '{name}' was NOT detected")
            failures += 1
        else:
            detected += 1
            print(f"  [PASS] negative control '{name}' detected on "
                  f"'{detected_on}'")

    if failures:
        return 1
    print(f"\nAll {len(cases)} cases and {detected} negative controls passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
