#!/usr/bin/env python3
"""Differential test for func_003635f0 (0x003635f0) using Unicorn ARM.

The pinned original body is executed from extracted/exefs/code.bin and the
compiled candidate body from src/engine/leaf_batch41_c.cpp.  Direct calls are
relocated to deterministic stubs at their original addresses; the virtual calls
and the member-function-pointer dispatch use fixture vtables that point at
further deterministic stubs.

Compared per case:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log with the architected arguments of every helper
    (all helpers here take zero stack words);
  * every byte of the 1 MiB fixture/data region, the two-word dispatch
    descriptor at 0x004105AC, and all writes outside the private stack;
  * the helper side effects are also stamped into a scratch page so call order
    is visible in memory.

Coverage: empty and non-empty instances of all three manager vectors, single
element loop bounds, owner child-vector sizes 0..3, every skip-flag value class,
state flags cleared by the first entry pass, context field and registered-link
boundary values, both dispatch descriptor branches (direct and virtual), several
direct/virtual targets, zero/non-zero helper results, and the empty-final-vector
return path.  Negative controls mutate the recovered field offsets and vtable
slot indices; every mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_003635f0"

FUNC_ADDR = 0x003635F0
FUNC_SIZE = 444

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00320000       # covers 0x00100000..0x00420000
DISPATCH_ADDR = 0x004105AC   # two-word {target, adjustment} descriptor
DATA_ADDR = 0x00700000
DATA_SIZE = 0x00100000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Fixture layout inside DATA_ADDR.
CTX = 0x00000
MANAGER = 0x10000
EC_PTRS = 0x20000
REG_OBJECTS = 0x30000
OC_PTRS = 0x40000
OWNER_OBJECTS = 0x50000
CHILD_LISTS = 0x60000
CHILD_PTRS = 0x70000
CHILD_OBJECTS = 0x80000
ENTRY_PTRS = 0x90000
ENTRY_OBJECTS = 0xA0000
SUBSTATES = 0xB0000
VTABLES = 0xC0000
SCRATCH = 0xD0000
SCRATCH_ADDR = DATA_ADDR + SCRATCH

# Direct-call targets keep their original addresses.
STUB_361C64 = 0x00361C64
STUB_3E138C = 0x003E138C
STUB_DISPATCH = 0x00375CC8     # shipped descriptor target (adjustment 0)

# Virtual/dispatch thunk targets.
STUB_SLOT_FIRST = (0x00380000, 0x00380004)
STUB_SLOT_BARE = (0x00380008, 0x0038000C)
STUB_SLOT_WITH_ARG = (0x00380010, 0x00380014)
STUB_DISPATCH_ODD = (0x00380018, 0x0038001C)
STUB_DISPATCH_ALT = 0x00380020

STUB_NAMES = {
    STUB_361C64: "func_00361c64",
    STUB_3E138C: "func_003e138c",
    STUB_DISPATCH: "func_00375cc8",
    STUB_DISPATCH_ALT: "dispatch_alt",
    STUB_SLOT_FIRST[0]: "slot_first_0",
    STUB_SLOT_FIRST[1]: "slot_first_1",
    STUB_SLOT_BARE[0]: "slot_bare_0",
    STUB_SLOT_BARE[1]: "slot_bare_1",
    STUB_SLOT_WITH_ARG[0]: "slot_arg_0",
    STUB_SLOT_WITH_ARG[1]: "slot_arg_1",
    STUB_DISPATCH_ODD[0]: "dispatch_odd_0",
    STUB_DISPATCH_ODD[1]: "dispatch_odd_1",
}

# Number of architected register arguments logged per stub.
STUB_ARG_COUNT = {
    STUB_361C64: 2,
    STUB_3E138C: 3,
    STUB_DISPATCH: 1,
    STUB_DISPATCH_ALT: 1,
    STUB_SLOT_FIRST[0]: 3,
    STUB_SLOT_FIRST[1]: 3,
    STUB_SLOT_BARE[0]: 1,
    STUB_SLOT_BARE[1]: 1,
    STUB_SLOT_WITH_ARG[0]: 3,
    STUB_SLOT_WITH_ARG[1]: 3,
    STUB_DISPATCH_ODD[0]: 1,
    STUB_DISPATCH_ODD[1]: 1,
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


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as stream:
        stream.seek(FUNC_ADDR - 0x00100000)
        return stream.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "003635f0" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"func_003635f0 not found in {obj_file}: {sorted(funcs)}")

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
            if name in rel.symbol_name:
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


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures
DEFAULT_REGISTERED = (SCRATCH_ADDR + 0x200, SCRATCH_ADDR + 0x204)
DEFAULT_OWNERS = (2, 1)
DEFAULT_ENTRIES = (
    {"skip": 0x00, "state_flag": 0x00},
    {"skip": 0x00, "state_flag": 0xFF},
    {"skip": 0x01, "state_flag": 0x00},
)


def build_data(case: dict) -> bytes:
    page = bytearray(b"\xA5" * DATA_SIZE)

    def write_u32(offset: int, value: int) -> None:
        struct.pack_into("<I", page, offset, value & 0xFFFFFFFF)

    def write_byte(offset: int, value: int) -> None:
        page[offset] = value & 0xFF

    write_u32(CTX + 0x08, case.get("ctx_first", 0x11110000))
    write_u32(CTX + 0x10, case.get("ctx_second", 0x22220000))

    registered = tuple(case.get("registered", DEFAULT_REGISTERED))
    registered_base = DATA_ADDR + EC_PTRS
    for index, link in enumerate(registered):
        object_address = DATA_ADDR + REG_OBJECTS + index * 0x40
        write_u32(REG_OBJECTS + index * 0x40 + 0x00,
                  DATA_ADDR + VTABLES + 0x100 + index * 0x40)  # dispatch vtable
        write_u32(REG_OBJECTS + index * 0x40 + 0x04,
                  DATA_ADDR + VTABLES + 0x100 + index * 0x40)  # +2 adjust
        write_u32(REG_OBJECTS + index * 0x40 - 0x04,
                  DATA_ADDR + VTABLES + 0x100 + index * 0x40)  # -2 adjust
        write_u32(REG_OBJECTS + index * 0x40 + 0x28, link)
        write_u32(EC_PTRS + index * 4, object_address)
    write_u32(MANAGER + 0xEC, registered_base)
    write_u32(MANAGER + 0xF0, registered_base + 4 * len(registered))

    owners = tuple(case.get("owners", DEFAULT_OWNERS))
    child_index = 0
    for owner_index, child_count in enumerate(owners):
        owner_address = DATA_ADDR + OWNER_OBJECTS + owner_index * 0x100
        child_list_address = DATA_ADDR + CHILD_LISTS + owner_index * 0x20
        write_u32(OWNER_OBJECTS + owner_index * 0x100 + 0x00,
                  DATA_ADDR + VTABLES + (owner_index & 1) * 0x40)
        write_u32(OWNER_OBJECTS + owner_index * 0x100 + 0x34,
                  child_list_address)
        write_u32(CHILD_LISTS + owner_index * 0x20 + 0x08,
                  DATA_ADDR + CHILD_PTRS + child_index * 4)
        write_u32(CHILD_LISTS + owner_index * 0x20 + 0x0C,
                  DATA_ADDR + CHILD_PTRS + (child_index + child_count) * 4)
        for _ in range(child_count):
            child_address = DATA_ADDR + CHILD_OBJECTS + child_index * 0x40
            write_u32(CHILD_OBJECTS + child_index * 0x40 + 0x00,
                      DATA_ADDR + VTABLES + (child_index & 1) * 0x40)
            write_u32(CHILD_PTRS + child_index * 4, child_address)
            child_index += 1
        write_u32(OC_PTRS + owner_index * 4, owner_address)
    write_u32(MANAGER + 0x0C, DATA_ADDR + OC_PTRS)
    write_u32(MANAGER + 0x10, DATA_ADDR + OC_PTRS + 4 * len(owners))

    entries = tuple(case.get("entries", DEFAULT_ENTRIES))
    for index, spec in enumerate(entries):
        entry_address = DATA_ADDR + ENTRY_OBJECTS + index * 0x300
        state_address = DATA_ADDR + SUBSTATES + index * 0x40
        write_u32(ENTRY_OBJECTS + index * 0x300 + 0x220, state_address)
        write_byte(ENTRY_OBJECTS + index * 0x300 + 0x231, spec.get("skip", 0))
        write_byte(SUBSTATES + index * 0x40 + 0x18, spec.get("state_flag", 0))
        write_u32(ENTRY_PTRS + index * 4, entry_address)
    write_u32(MANAGER + 0x3C, DATA_ADDR + ENTRY_PTRS)
    write_u32(MANAGER + 0x40, DATA_ADDR + ENTRY_PTRS + 4 * len(entries))

    for variant in range(2):
        vtable = VTABLES + variant * 0x40
        write_u32(vtable + 0x00, STUB_SLOT_FIRST[variant])
        write_u32(vtable + 0x0C, STUB_SLOT_WITH_ARG[variant])
        write_u32(vtable + 0x20, STUB_SLOT_BARE[variant])
    for index in range(len(registered)):
        vtable = VTABLES + 0x100 + index * 0x40
        write_u32(vtable + 0x08, STUB_DISPATCH_ODD[index & 1])
        write_u32(vtable + 0x10, STUB_DISPATCH_ODD[index & 1])

    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
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
        self.scratch_index = 0
        self.case: dict = {}

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value & ((1 << (size * 8)) - 1)))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        count = STUB_ARG_COUNT[address]
        registers = (
            uc.reg_read(arm.UC_ARM_REG_R0),
            uc.reg_read(arm.UC_ARM_REG_R1),
            uc.reg_read(arm.UC_ARM_REG_R2),
        )
        self.call_log.append((STUB_NAMES[address], registers[:count]))

        # Record call order in memory as well as in the Python log.
        self.uc.mem_write(
            SCRATCH_ADDR + self.scratch_index, bytes(((address >> 4) & 0xFF,))
        )
        self.scratch_index += 1

        if address == STUB_DISPATCH:
            returns = self.case.get("dispatch_returns", (0xD15A0000,))
            value = returns[min(len(returns) - 1, self.scratch_index - 1)]
        elif address == STUB_DISPATCH_ALT:
            value = self.case.get("dispatch_alt_return", 0xA17E0000)
        elif address in STUB_DISPATCH_ODD:
            value = self.case.get("dispatch_odd_return", 0x0DD00000)
        elif address == STUB_361C64:
            value = self.case.get("direct_return", 0x361C0000)
        elif address == STUB_3E138C:
            value = self.case.get("e138c_return", 0x3E130000)
        else:
            value = 0x51070000
        uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.scratch_index = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DATA_ADDR, build_data(case))
        target, adjustment = case.get("dispatch", (STUB_DISPATCH, 0))
        self.uc.mem_write(
            DISPATCH_ADDR, struct.pack("<II", target & 0xFFFFFFFF,
                                       adjustment & 0xFFFFFFFF)
        )
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, DATA_ADDR + CTX)
        self.uc.reg_write(arm.UC_ARM_REG_R1, DATA_ADDR + MANAGER)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x12345678)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x9ABCDEF0)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        external_writes = [
            write
            for write in self.writes
            if not (STACK_ADDR <= write[0] < STACK_ADDR + STACK_SIZE)
        ]
        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "writes": external_writes,
            "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "descriptor": bytes(self.uc.mem_read(DISPATCH_ADDR, 8)),
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "call_log", "writes",
                "data", "descriptor"):
        if orig[key] != cand[key]:
            problems.append(f"{key} differs")
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "registered": DEFAULT_REGISTERED,
        "owners": DEFAULT_OWNERS,
        "entries": DEFAULT_ENTRIES,
        "dispatch": (STUB_DISPATCH, 0),
        "dispatch_returns": (0xD15A0000,),
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    cases.append(base_case("baseline"))
    cases.append(base_case("all vectors empty", registered=(), owners=(),
                           entries=()))
    cases.append(base_case("registered empty", registered=()))
    cases.append(base_case("owners empty", owners=()))
    cases.append(base_case("entries empty", entries=()))
    cases.append(base_case("single registered", registered=(SCRATCH_ADDR + 0x210,)))
    cases.append(base_case("three registered",
                           registered=(0x00000000, 0xFFFFFFFF,
                                       SCRATCH_ADDR + 0x218)))
    cases.append(base_case("three registered, empty owners and entries",
                           registered=(SCRATCH_ADDR + 0x210, SCRATCH_ADDR + 0x214,
                                       SCRATCH_ADDR + 0x218),
                           owners=(), entries=()))

    for owners in ((), (0,), (1,), (3,), (0, 0), (0, 2, 0), (2, 0, 3)):
        cases.append(base_case(f"owner child counts {owners}", owners=owners))

    for skip in (0x00, 0x01, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"skip flag 0x{skip:02x}",
                               entries=({"skip": skip, "state_flag": 0x00},)))
    for state_flag in (0x00, 0x01, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"initial state flag 0x{state_flag:02x}",
                               entries=({"skip": 0, "state_flag": state_flag},)))

    for ctx_first, ctx_second in (
        (0x00000000, 0x00000000),
        (0xFFFFFFFF, 0xFFFFFFFF),
        (0x7FFFFFFF, 0x80000000),
        (0x80000000, 0x7FFFFFFF),
        (SCRATCH_ADDR + 0x300, SCRATCH_ADDR + 0x310),
    ):
        cases.append(base_case(
            f"context fields 0x{ctx_first:08x}/0x{ctx_second:08x}",
            ctx_first=ctx_first, ctx_second=ctx_second))

    cases.append(base_case("direct helper returns zero", direct_return=0,
                           e138c_return=0))
    cases.append(base_case("direct helper returns non-zero",
                           direct_return=0xFFFFFFFF, e138c_return=0x80000000))
    cases.append(base_case("dispatch returns zero", dispatch_returns=(0,)))
    cases.append(base_case("dispatch returns boundary values",
                           dispatch_returns=(0xFFFFFFFF, 0x80000000,
                                             0x7FFFFFFF)))
    cases.append(base_case("empty final vector leaves descriptor address",
                           registered=()))

    # Descriptor branches: direct target selection, even adjustment, and the
    # virtual form (object offset 0, vtable byte offset 8 and 16).
    cases.append(base_case("dispatch alternate direct target",
                           dispatch=(STUB_DISPATCH_ALT, 0)))
    cases.append(base_case("dispatch even adjustment 2 (object +1)",
                           dispatch=(STUB_DISPATCH, 2)))
    cases.append(base_case("dispatch even adjustment 0x100 (object +0x80)",
                           dispatch=(STUB_DISPATCH, 0x100)))
    cases.append(base_case("dispatch even negative adjustment -8 (object -4)",
                           dispatch=(STUB_DISPATCH, 0xFFFFFFF8)))
    cases.append(base_case("dispatch virtual offset 0",
                           dispatch=(0x00000010, 1)))
    cases.append(base_case("dispatch virtual offset 8",
                           dispatch=(0x00000008, 1)))
    cases.append(base_case("dispatch virtual object +4",
                           dispatch=(0x00000010, 9)))
    cases.append(base_case("dispatch virtual negative object -4",
                           dispatch=(0x00000010, 0xFFFFFFF9)))
    cases.append(base_case("dispatch virtual with one registered",
                           registered=(SCRATCH_ADDR + 0x220,),
                           dispatch=(0x00000010, 1)))
    cases.append(base_case("dispatch virtual with three registered",
                           registered=(SCRATCH_ADDR + 0x220, SCRATCH_ADDR + 0x224,
                                       SCRATCH_ADDR + 0x228),
                           dispatch=(0x00000010, 1)))

    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases: list[dict]) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, case)
        cand = Runner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                if problem in ("data", "writes", "descriptor"):
                    print(f"    {problem}")
                else:
                    key = problem.split()[0]
                    print(f"    {problem}:")
                    print(f"      orig={orig[key]!r}")
                    print(f"      cand={cand[key]!r}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing func_003635f0 (0x003635f0)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(direct call relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("registered_link_offset",
         "constexpr u32 kRegisteredLinkOffset = 0x28;",
         "constexpr u32 kRegisteredLinkOffset = 0x2C;"),
        ("bare_vtable_slot",
         "constexpr u32 kSlotBare = 8;",
         "constexpr u32 kSlotBare = 7;"),
        ("context_second_offset",
         "constexpr u32 kContextSecondOffset = 0x10;",
         "constexpr u32 kContextSecondOffset = 0x14;"),
        ("skip_flag_offset",
         "constexpr u32 kSkipFlagOffset = 0x231;",
         "constexpr u32 kSkipFlagOffset = 0x230;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            try:
                bad = Runner().run(mutant_code, case)
            except Exception:
                detected = True
                break
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
