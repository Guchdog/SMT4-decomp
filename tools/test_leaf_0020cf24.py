#!/usr/bin/env python3
"""Differential test for engine_func_0020cf24 (0x0020cf24) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the engine_func_0020cf24 body,
resolves its three direct callees to deterministic stubs at their original
addresses, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.

The body has no branches and no loops: it is a straight-line build of 35 widget
slots.  Coverage therefore targets the observable sequence and the data it
publishes:

  * the full ordered call log (71 calls) including the group key 0x0A, every
    row sub-index and the 0x00/0x01/0x0E priming of one entry;
  * every published table offset 0x00..0x88, 0x5C and 0x64;
  * enabled slots (write 1 to widget +0x3C/+0x40) versus publish-only slots;
  * non-null and null widget results for the publish-only slots;
  * a helper that retargets the node-table pointer mid-way (the original
    re-reads it for every slot), including at the last two entries;
  * ignored return values from the texture-table load and the row loads;
  * incoming r0-r3 sentinels (zero, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF).

Compared outputs: return r0, continuation PC, final SP, callee-saved r4-r11,
the ordered call log, every non-stack memory write (address, width, value), and
the final contents of the global, both table pages and the widget page.

No indirect calls exist.  Enabled slots whose widget lookup returns null fault
in both bodies at widget +0x3C; that invalid-input domain is documented rather
than exercised (the faulting address is not exposed by Unicorn).
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
OUT_DIR = ROOT / "build/test_leaf_0020cf24"

FUNC_ADDR = 0x0020CF24
FUNC_SIZE = 1496

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and the stubs below 0x2C5B04
GLOBAL_ADDR = 0x00447000
GLOBAL_SIZE = 0x00001000
TABLE_ADDR = 0x00700000
TABLE2_ADDR = 0x00701000
TABLE_SIZE = 0x00001000
NODE_ADDR = 0x00710000
NODE_SIZE = 0x00040000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# `ldr r5,[pc,#0x574]` -> 0x00447A78; the node table base is the word at +0x04.
GLOBAL_TABLE_SLOT = 0x00447A7C

STUB_TEX_TABLE = 0x002C5B04
STUB_ROW_LOAD = 0x002C5AB8
STUB_GET_WIDGET = 0x002C1DE4

STUB_NAMES = {
    STUB_TEX_TABLE: "AsdTMTexTable_func_002c5b04",
    STUB_ROW_LOAD: "engine_func_002c5ab8",
    STUB_GET_WIDGET: "script_vm_func_002c1de4",
}

# Every stub receives two register arguments and no stack arguments.
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

# Table offsets written by the original, in write order (used for reporting).
PUBLISHED_OFFSETS = (
    0x88, 0x78, 0x80, 0x7C, 0x84, 0x58, 0x6C, 0x70, 0x74, 0x00, 0x04, 0x08,
    0x0C, 0x10, 0x14, 0x34, 0x38, 0x30, 0x3C, 0x40, 0x44, 0x48, 0x18, 0x24,
    0x28, 0x2C, 0x1C, 0x20, 0x60, 0x4C, 0x68, 0x50, 0x54, 0x64, 0x5C,
)
ENABLED_OFFSETS = (
    0x88, 0x78, 0x80, 0x7C, 0x84, 0x58, 0x00, 0x04, 0x08, 0x0C, 0x10, 0x14,
    0x34, 0x38, 0x30, 0x3C, 0x40, 0x44, 0x48, 0x68, 0x50, 0x54, 0x64, 0x5C,
)


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("engine_func_0020cf24")
    if candidate is None:
        raise RuntimeError(
            f"engine_func_0020cf24 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type != 28:  # R_ARM_CALL
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if name == rel.symbol_name:
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


def widget_address(salt: int, sub: int) -> int:
    """Deterministic widget pointer: distinct per (salt low nibble, sub)."""
    return NODE_ADDR + ((((salt & 0x0F) * 64) + (sub & 0x3F)) << 8)


class CF24Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
        self.uc.mem_map(TABLE2_ADDR, TABLE_SIZE)
        self.uc.mem_map(NODE_ADDR, NODE_SIZE)
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
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        self._log(address, r0, r1)

        if address == STUB_TEX_TABLE:
            value = 0 if self.case.get("tex_table_null") else (0x0BAD0000 | r0)
            uc.reg_write(arm.UC_ARM_REG_R0, value)
        elif address == STUB_ROW_LOAD:
            value = 0 if self.case.get("row_load_null") else (0x0C0DE000 | r1)
            uc.reg_write(arm.UC_ARM_REG_R0, value)
        else:  # STUB_GET_WIDGET
            if self.case.get("retarget_sub") == r1:
                # Retarget the node-table pointer observed by the next slot.
                uc.mem_write(
                    GLOBAL_TABLE_SLOT,
                    struct.pack("<I", self.case.get("retarget_to", TABLE2_ADDR)),
                )
            if self.case.get("null_sub") == r1:
                value = 0
            else:
                value = widget_address(self.case.get("salt", 1), r1)
            uc.reg_write(arm.UC_ARM_REG_R0, value)

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)

        global_page = bytearray(GLOBAL_SIZE)
        struct.pack_into("<I", global_page, GLOBAL_TABLE_SLOT - GLOBAL_ADDR, TABLE_ADDR)
        # Filler that must survive untouched.
        for offset in range(0, GLOBAL_SIZE, 4):
            if offset != GLOBAL_TABLE_SLOT - GLOBAL_ADDR:
                struct.pack_into("<I", global_page, offset, 0xA5A50000 | offset)
        self.uc.mem_write(GLOBAL_ADDR, bytes(global_page))

        table = bytearray(TABLE_SIZE)
        for offset in range(0, TABLE_SIZE, 4):
            struct.pack_into("<I", table, offset, 0x7AB00000 | offset)
        self.uc.mem_write(TABLE_ADDR, bytes(table))
        table2 = bytearray(TABLE_SIZE)
        for offset in range(0, TABLE_SIZE, 4):
            struct.pack_into("<I", table2, offset, 0x7AC00000 | offset)
        self.uc.mem_write(TABLE2_ADDR, bytes(table2))
        self.uc.mem_write(NODE_ADDR, b"\x00" * NODE_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for index, register in enumerate(
            (arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1, arm.UC_ARM_REG_R2, arm.UC_ARM_REG_R3)
        ):
            self.uc.reg_write(register, case.get("arg", (0, 0, 0, 0))[index] & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        outside_stack = [
            (address, size, value)
            for address, size, value in self.writes
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        ]
        unexpected = [
            (address, size)
            for address, size, _value in outside_stack
            if not (GLOBAL_ADDR <= address < GLOBAL_ADDR + GLOBAL_SIZE
                    or TABLE_ADDR <= address < TABLE_ADDR + TABLE_SIZE
                    or TABLE2_ADDR <= address < TABLE2_ADDR + TABLE_SIZE
                    or NODE_ADDR <= address < NODE_ADDR + NODE_SIZE)
        ]

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "writes": sorted(outside_stack),
            "unexpected_writes": unexpected,
            "fixtures": {
                "global": bytes(self.uc.mem_read(GLOBAL_ADDR, GLOBAL_SIZE)),
                "table": bytes(self.uc.mem_read(TABLE_ADDR, TABLE_SIZE)),
                "table2": bytes(self.uc.mem_read(TABLE2_ADDR, TABLE_SIZE)),
                "node": bytes(self.uc.mem_read(NODE_ADDR, NODE_SIZE)),
            },
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append("call_log differs")
        for index, (left, right) in enumerate(
            zip(orig["call_log"], cand["call_log"])
        ):
            if left != right:
                problems.append(f"  call {index}: orig={left!r} cand={right!r}")
        if len(orig["call_log"]) != len(cand["call_log"]):
            problems.append(
                f"  call count orig={len(orig['call_log'])} "
                f"cand={len(cand['call_log'])}"
            )
    if orig["writes"] != cand["writes"]:
        problems.append("memory writes differ")
        left = set(orig["writes"])
        right = set(cand["writes"])
        for entry in sorted(left - right)[:8]:
            problems.append(f"  only orig: {entry!r}")
        for entry in sorted(right - left)[:8]:
            problems.append(f"  only cand: {entry!r}")
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            differences = [
                offset
                for offset in range(len(value))
                if value[offset] != cand["fixtures"][key][offset]
            ]
            problems.append(
                f"fixture {key} differs at {len(differences)} bytes, "
                f"first 0x{differences[0]:x}" if differences else f"fixture {key} differs"
            )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "salt": 1,
        "null_sub": None,
        "retarget_sub": None,
        "arg": (0, 0, 0, 0),
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- baseline and per-salt widget identities (distinct pointers per slot)
    cases.append(base_case("baseline"))
    for salt in (0, 2, 3, 0x7F, 0xFF):
        cases.append(base_case(f"salt {salt}", salt=salt))

    # --- incoming r0-r3 are never read: zero, positive, negative, all ones
    for args in (
        (0x00000000, 0x00000000, 0x00000000, 0x00000000),
        (0x7FFFFFFF, 0x55555555, 0x2AAAAAAA, 0x12345678),
        (0x80000000, 0xFFFFFFFF, 0x80000000, 0xFFFFFFFF),
        (0xFFFFFFFF, 0x80000000, 0xFFFFFFFF, 0x80000000),
    ):
        cases.append(base_case(f"incoming args {args[0]:#010x}", arg=args))

    # --- ignored return values of the texture-table and row-load helpers
    cases.append(base_case("texture table returns null", tex_table_null=True))
    cases.append(base_case("row load returns null", row_load_null=True))
    cases.append(base_case("both return null", tex_table_null=True,
                           row_load_null=True))

    # --- null widget pointer for every publish-only slot (no +0x3C/+0x40 write)
    for sub, offset in (
        (0x1C, 0x6C), (0x1E, 0x70), (0x1D, 0x74), (0x08, 0x18), (0x09, 0x24),
        (0x0B, 0x28), (0x06, 0x2C), (0x07, 0x1C), (0x0A, 0x20), (0x02, 0x60),
        (0x17, 0x4C),
    ):
        cases.append(base_case(f"null widget for sub 0x{sub:02x} -> 0x{offset:02x}",
                               null_sub=sub))

    # --- node-table retargeting mid-way: the original re-reads [0x00447A7C]
    # Retargeting during sub 0x01 would leave table2[0x64] unwritten when the
    # 0x64 slot is enabled, which faults in the original; that invalid-input
    # domain is not exercised.
    for sub in (0x1F, 0x22, 0x1C, 0x0E, 0x17, 0x05, 0x1A, 0x00):
        cases.append(base_case(f"table retarget during sub 0x{sub:02x}",
                               retarget_sub=sub))
    cases.append(base_case("retarget to the first table again", retarget_sub=0x22,
                           retarget_to=TABLE_ADDR))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = CF24Runner().run(orig_code, case)
        cand = CF24Runner().run(cand_code, case)
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
    print("Testing engine_func_0020cf24 (0x0020cf24)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(3 call relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("enable_flag_0x58", "RegisterNode(0x19, 0x58, true);",
         "RegisterNode(0x19, 0x58, false);"),
        ("field_offset_0x08", "RegisterNode(0x0F, 0x08, true);",
         "RegisterNode(0x0F, 0x0C, true);"),
        ("prime_sub", "AsdRow_LoadNow(kGroup, 0x01);\n    RegisterNode(0x0E",
         "AsdRow_LoadNow(kGroup, 0x02);\n    RegisterNode(0x0E"),
        ("group_key", "constexpr u32 kGroup = 0x0A;",
         "constexpr u32 kGroup = 0x0B;"),
        ("return_slot", "return EnableWidget(kLastSlot);",
         "return EnableWidget(0x64);"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = CF24Runner().run(orig_code, case)
            bad = CF24Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
