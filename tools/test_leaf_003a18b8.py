#!/usr/bin/env python3
"""Differential test for shop_func_003a18b8 (0x003a18b8) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the shop_func_003a18b8 body,
resolves its ten direct calls to deterministic stubs, and runs the pinned
original (extracted/exefs/code.bin) against the candidate in separate Unicorn
machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log: the four argument-less helpers, every named-resource
    load (pointer, NUL-terminated name read from memory, status destination and
    flags), the texture group pair, both sprite factories (id arguments) and the
    tail continuation (handle, 0, 0);
  * the 32-bit status words the load stub writes through its out pointer and
    the sprite handles the factories return;
  * the complete shop-object page (writes at +0x160/+0x164/+0x15D40/+0x15D44)
    and the read-only name page;
  * every emulated write outside the private stack.

Coverage: state 0 and state 1 with every selector type plus both shared
defaults, unmatched state bytes (2, 0x7F, 0x80, 0xFF) where the type word must
not influence the result, zero and non-zero factory results, and three object
base alignments. Negative controls mutate the primary name, the state-0
type-6/7 first id, the state-1 type-10 second id, the secondary status offset
and the primary sprite slot; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_003a18b8"

FUNC_ADDR = 0x003A18B8
FUNC_SIZE = 436

CODE_ADDR = 0x00200000     # covers 0x00247D64..0x003A18B8 and every stub
CODE_SIZE = 0x00200000
NAMES_ADDR = 0x00406000    # 0x004076B0..0x00407720 live in this page
NAMES_SIZE = 0x00002000
OBJECT_ADDR = 0x00710000
OBJECT_SIZE = 0x00020000   # +0x15D48 is the highest field used
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_289B4C = 0x00289B4C
STUB_289AE8 = 0x00289AE8
STUB_28DC54 = 0x0028DC54
STUB_28D974 = 0x0028D974
STUB_297704 = 0x00297704
STUB_2C4E28 = 0x002C4E28
STUB_2C5AB8 = 0x002C5AB8
STUB_2FDFB8 = 0x002FDFB8
STUB_2860B4 = 0x002860B4
STUB_247D64 = 0x00247D64

STUB_NAMES = {
    STUB_289B4C: "CommonBg_func_00289b4c",
    STUB_289AE8: "script_vm_func_00289ae8",
    STUB_28DC54: "camp_func_0028dc54",
    STUB_28D974: "ButtonHelp_Init",
    STUB_297704: "script_vm_func_00297704",
    STUB_2C4E28: "AsdTMTexTable_func_002c4e28",
    STUB_2C5AB8: "engine_func_002c5ab8",
    STUB_2FDFB8: "Npc2d_func_002fdfb8",
    STUB_2860B4: "Npc2d_func_002860b4",
    STUB_247D64: "engine_func_00247d64",
}

# Name pointers copied from the function's literal pool (0x003A1A50..).
NAME_STRINGS = {
    0x004076B0: b"shop_primary.tgd",
    0x004076C0: b"shop_s0_type8.tgd",
    0x004076D8: b"shop_s0_type67.tgd",
    0x004076F0: b"shop_s0_other.tgd",
    0x00407708: b"shop_s1_type9.tgd",
    0x00407720: b"shop_s1_other.tgd",
}

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


def build_names_page() -> bytes:
    page = bytearray(NAMES_SIZE)
    for index in range(NAMES_SIZE):
        page[index] = (index * 29 + 0x5C) & 0xFF
    for offset, text in NAME_STRINGS.items():
        start = offset - NAMES_ADDR
        page[start : start + len(text) + 1] = text + b"\x00"
    return bytes(page)


NAMES_PAGE = build_names_page()

OBJECT_FILL = bytes((index * 37 + 0x11) & 0xFF for index in range(OBJECT_SIZE))


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "003a18b8" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"shop_func_003a18b8 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 10, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            # 0x0028D974's uncompiled symbol keeps its recovered domain name.
            target = {"ButtonHelp_Init": STUB_28D974}.get(rel.symbol_name)
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond_or_bl = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, cond_or_bl | (displacement & 0x00FFFFFF)
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


def read_c_string(uc, address: int, limit: int = 32) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


def build_object(case: dict) -> bytes:
    page = bytearray(OBJECT_FILL)
    base = case.get("object_offset", 0)
    page[base + 0x14] = case["state"] & 0xFF
    struct.pack_into("<I", page, base + 0x18, case["type"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, base + 0x160, 0xDEAD1600)
    struct.pack_into("<I", page, base + 0x164, 0xDEAD1640)
    struct.pack_into("<I", page, base + 0x15D40, 0xDEAD0000)
    struct.pack_into("<I", page, base + 0x15D44, 0xDEAD0004)
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(NAMES_ADDR, NAMES_SIZE)
        self.uc.mem_map(OBJECT_ADDR, OBJECT_SIZE)
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
        self.load_index = 0
        self.primary_index = 0
        self.secondary_index = 0
        self.tail_index = 0
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)

        if address in (STUB_289B4C, STUB_289AE8, STUB_28DC54, STUB_28D974):
            # These helpers overwrite r0 before reading it; r0-r3 are dead.
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, 0xA0000000 | (address & 0xFFFF))
        elif address == STUB_297704:
            name = read_c_string(uc, r0)
            self._log(address, r0, name, r1, r2)
            self.load_index += 1
            if r1:
                uc.mem_write(
                    r1, struct.pack("<I", 0x5A5A0000 | self.load_index)
                )
            uc.reg_write(arm.UC_ARM_REG_R0, 0x29770000 | self.load_index)
        elif address == STUB_2C4E28:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2C4E0000 | (r0 & 0xFFFF))
        elif address == STUB_2C5AB8:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2C5A0000 | (r0 & 0xFFFF))
        elif address == STUB_2FDFB8:
            self._log(address, r0)
            self.primary_index += 1
            if self.case.get("null_primary"):
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                uc.reg_write(
                    arm.UC_ARM_REG_R0,
                    (0x2FDF0000 | ((r0 & 0xFF) << 8) | self.primary_index)
                    & 0xFFFFFFFF,
                )
        elif address == STUB_2860B4:
            self._log(address, r0, r1, r2)
            self.secondary_index += 1
            if self.case.get("null_secondary"):
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                uc.reg_write(
                    arm.UC_ARM_REG_R0,
                    (0x28600000 | ((r0 & 0xFF) << 8) | self.secondary_index)
                    & 0xFFFFFFFF,
                )
        elif address == STUB_247D64:
            self._log(address, r0, r1, r2)
            self.tail_index += 1
            uc.reg_write(arm.UC_ARM_REG_R0, 0x247D0000 | self.tail_index)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.load_index = 0
        self.primary_index = 0
        self.secondary_index = 0
        self.tail_index = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(NAMES_ADDR, NAMES_PAGE)
        self.uc.mem_write(OBJECT_ADDR, build_object(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        object_base = OBJECT_ADDR + case.get("object_offset", 0)
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, object_base)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        nonstack_writes = []
        for address, size, value in self.writes:
            if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
                continue
            nonstack_writes.append((address, size, value))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self.call_log,
            "object": bytes(self.uc.mem_read(OBJECT_ADDR, OBJECT_SIZE)),
            "names": bytes(self.uc.mem_read(NAMES_ADDR, NAMES_SIZE)),
            "nonstack_writes": nonstack_writes,
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
    if orig["object"] != cand["object"]:
        differing = [
            index
            for index, (left, right) in enumerate(
                zip(orig["object"], cand["object"])
            )
            if left != right
        ]
        problems.append(
            f"object page differs at {differing[:8]}"
            f"{'...' if len(differing) > 8 else ''}"
        )
    if orig["names"] != cand["names"]:
        problems.append("name page was modified differently")
    if orig["nonstack_writes"] != cand["nonstack_writes"]:
        problems.append(
            "non-stack writes:\n    orig="
            + repr(orig["nonstack_writes"])
            + "\n    cand="
            + repr(cand["nonstack_writes"])
        )
    return problems


def base_case(name: str, state: int, type_word: int, **overrides) -> dict:
    case = {
        "name": name,
        "state": state,
        "type": type_word,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []
    types = (0, 1, 2, 5, 6, 7, 8, 9, 10, 11, 0x7FFFFFFF, 0x80000000,
             0xFFFFFFFF)

    # --- every selector of both state branches plus the shared defaults
    for type_word in types:
        cases.append(
            base_case(f"state 0 type 0x{type_word:08x}", 0, type_word)
        )
    for type_word in types:
        cases.append(
            base_case(f"state 1 type 0x{type_word:08x}", 1, type_word)
        )

    # --- state bytes that skip the second load entirely
    for state in (2, 0x7F, 0x80, 0xFF):
        for type_word in (0, 5, 8, 9):
            cases.append(
                base_case(f"state 0x{state:02x} type {type_word}",
                          state, type_word)
            )

    # --- zero and non-zero factory results
    cases.append(
        base_case("state 0 type 8 null primary", 0, 8, null_primary=True)
    )
    cases.append(
        base_case("state 1 type 9 null primary", 1, 9, null_primary=True)
    )
    cases.append(
        base_case("state 0 type 8 null secondary", 0, 8, null_secondary=True)
    )
    cases.append(
        base_case("state 1 type 10 null secondary", 1, 10,
                  null_secondary=True)
    )
    cases.append(
        base_case("state 0 type 8 both null", 0, 8, null_primary=True,
                  null_secondary=True)
    )
    cases.append(
        base_case("state 3 null primary", 3, 9, null_primary=True)
    )

    # --- object base alignment / placement
    for offset in (0x10, 0x100, 0x1F0):
        cases.append(
            base_case(f"state 1 type 5 object+0x{offset:x}", 1, 5,
                      object_offset=offset)
        )

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
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing shop_func_003a18b8 (0x003a18b8)...")
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
        ("primary_name", "constexpr u32 kPrimaryName = 0x004076B0u;",
         "constexpr u32 kPrimaryName = 0x004076B4u;"),
        ("state0_type67_first_id",
         "            name = NameAt(shop_3a18b8::kState0Type67Name);\n"
         "            first_id = 0x8B;",
         "            name = NameAt(shop_3a18b8::kState0Type67Name);\n"
         "            first_id = 0x8A;"),
        ("state1_type10_second_id",
         "            name = NameAt(shop_3a18b8::kState1DefaultName);\n"
         "            first_id = 0x89;\n"
         "            second_id = 0xA3;",
         "            name = NameAt(shop_3a18b8::kState1DefaultName);\n"
         "            first_id = 0x89;\n"
         "            second_id = 0xA2;"),
        ("secondary_status_offset",
         "constexpr u32 kSecondaryStatusOffset = 0x164;",
         "constexpr u32 kSecondaryStatusOffset = 0x168;"),
        ("primary_sprite_offset",
         "constexpr u32 kPrimarySpriteOffset = 0x15D40; // literal 0x00015D40"
         " (0x003A1A60)",
         "constexpr u32 kPrimarySpriteOffset = 0x15D3C; // literal 0x00015D40"
         " (0x003A1A60)"),
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
