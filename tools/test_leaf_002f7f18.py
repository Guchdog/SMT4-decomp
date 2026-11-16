#!/usr/bin/env python3
"""Differential test for engine_func_002f7f18 (0x002f7f18) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the engine_func_002f7f18 body,
resolves its eight direct calls to deterministic stubs, and runs the pinned
original (extracted/exefs/code.bin) against the candidate in separate Unicorn
machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log with every register argument and the architected stack
    arguments of each helper (nine words for 0x0027E1A0, three for 0x00250800);
  * every fixture page (actor tables, both UI state pages, both record tables,
    the script-context slot page) must be byte-identical and unmodified;
  * any emulated write outside the private stack.

Coverage: the four actor visit slots with each skip condition (bit0 clear,
bit6 set, negative s16 id), the id/index boundaries, signed s16 value
boundaries, bit3 of the u16 clamp word set and clear, wrapping 32-bit scale
products, the 0x51EB851F signed division by 100 (including negatives), the
signed `limit_selector > 0` test, null and non-null 0x0027EB98 results, and a
case where 0x00293C98 alternates between two UI state pages so that a wrong
call order (actor table vs record table read) is observable.  Negative
controls mutate constants and comparison directions; each mutant must be
detected.
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
OUT_DIR = ROOT / "build/test_leaf_002f7f18"

FUNC_ADDR = 0x002F7F18
FUNC_SIZE = 432

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers 0x002F7F18 and every stub below 0x002F0000

SLOT_ADDR = 0x00434000
SLOT_SIZE = 0x00001000  # holds the script-context slot at 0x0043427C

ACTORS_ADDR = 0x00700000
ACTORS_SIZE = 0x00010000  # two 4-entry actor tables (A at +0, B at +0x8000)
UI_A_ADDR = 0x00710000
UI_B_ADDR = 0x00720000
UI_SIZE = 0x00004000  # actor/record base pointers live at +0x1FC0 / +0x1E98

RECORDS_ADDR = 0x00730000
RECORDS_SIZE = 0x00040000  # 949 record slots of 276 bytes
TRAP_ADDR = 0x90000000

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

SCRIPT_CONTEXT_SLOT = 0x0043427C
UI_GLOBAL_ADDR = 0x00435D90  # only documented; ui_func_00293c98 is stubbed

# Original direct-call targets; stubs are written at the same addresses so both
# the pinned original and the relocated candidate resolve to them.
STUB_296F60 = 0x00296F60
STUB_27EB98 = 0x0027EB98
STUB_293C98 = 0x00293C98
STUB_27E1A0 = 0x0027E1A0
STUB_250800 = 0x00250800

STUB_NAMES = {
    STUB_296F60: "engine_func_00296f60",
    STUB_27EB98: "script_vm_func_0027eb98",
    STUB_293C98: "ui_func_00293c98",
    STUB_27E1A0: "battle_func_0027e1a0",
    STUB_250800: "battle_func_00250800",
}

# Number of architected stack words each helper receives.
STACK_ARGS = {
    STUB_296F60: 0,
    STUB_27EB98: 0,
    STUB_293C98: 0,
    STUB_27E1A0: 9,  # value_a, value_b, -1, limit, slot, slot, 9, 0.0f, 0
    STUB_250800: 3,  # 0, 0.0f, 0
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

# AAPCS callee-saved VFP registers d8-d15.  The pinned original never touches
# them; the candidate spills d8 as its 8-byte stack alignment slot, so the
# differential also proves the VFP save/restore round-trips.
CALLEE_SAVED_VFP = {
    "d8": arm.UC_ARM_REG_D8,
    "d9": arm.UC_ARM_REG_D9,
    "d10": arm.UC_ARM_REG_D10,
    "d11": arm.UC_ARM_REG_D11,
    "d12": arm.UC_ARM_REG_D12,
    "d13": arm.UC_ARM_REG_D13,
    "d14": arm.UC_ARM_REG_D14,
    "d15": arm.UC_ARM_REG_D15,
}
CALLEE_SAVED_VFP_START = {
    "d8": 0x0807060504030201,
    "d9": 0x100F0E0D0C0B0A09,
    "d10": 0x1817161514131211,
    "d11": 0x201F1E1D1C1B1A19,
    "d12": 0x2827262524232221,
    "d13": 0x302F2E2D2C2B2A29,
    "d14": 0x3837363534333231,
    "d15": 0x403F3E3D3C3B3A39,
}

ACTOR_STRIDE = 648
ACTOR_COUNT = 4
ACTORS_B_OFFSET = 0x8000

# Actor header layout recovered from the ARM (only these offsets are touched).
ACTOR_FLAGS = 0x000
ACTOR_ID = 0x008
ACTOR_VALUE_A = 0x1B6
ACTOR_VALUE_B = 0x1BA
ACTOR_CLAMP = 0x1C6

RECORD_STRIDE = 276
RECORDS_B_OFFSET = 0x10000
MAX_TEST_ID = 949  # (RECORDS_SIZE - RECORD_STRIDE) // RECORD_STRIDE

DEFAULT_ACTORS = [
    # flags, s16 id, s16 value_a, s16 value_b, u16 clamp word
    dict(flags=0x00000001, id=0x0000, value_a=100, value_b=200, clamp=0x0000),
    dict(flags=0x00000001, id=0x0001, value_a=-50, value_b=32767, clamp=0x0008),
    dict(flags=0x00000041, id=0x0002, value_a=7, value_b=7, clamp=0x0008),
    dict(flags=0x00000000, id=0x0003, value_a=7, value_b=7, clamp=0x0000),
]

DEFAULT_ACTORS_B = [
    dict(flags=0x00000001, id=0x0004, value_a=101, value_b=-101, clamp=0x0008),
    dict(flags=0x00000000, id=0x0005, value_a=1, value_b=1, clamp=0x0000),
    dict(flags=0x00000001, id=0x0006, value_a=99, value_b=100, clamp=0x0000),
    dict(flags=0x00000001, id=0x0007, value_a=32767, value_b=-32768, clamp=0x0008),
]


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "002f7f18" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_002f7f18 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = None
            for address, name in STUB_NAMES.items():
                if f"{address:08x}" in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            displacement = (target - (FUNC_ADDR + rel.offset + 8)) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
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
def build_actor_page(case: dict) -> bytes:
    page = bytearray(ACTORS_SIZE)
    tables = (
        ("a", 0, DEFAULT_ACTORS),
        ("b", ACTORS_B_OFFSET, DEFAULT_ACTORS_B),
    )
    for tag, base, defaults in tables:
        actors = case.get(f"actors_{tag}", defaults)
        if len(actors) != ACTOR_COUNT:
            raise ValueError("every actor table needs exactly four entries")
        for index, spec in enumerate(actors):
            offset = base + index * ACTOR_STRIDE
            struct.pack_into("<I", page, offset + ACTOR_FLAGS,
                             spec["flags"] & 0xFFFFFFFF)
            struct.pack_into("<h", page, offset + ACTOR_ID, spec["id"])
            struct.pack_into("<h", page, offset + ACTOR_VALUE_A, spec["value_a"])
            struct.pack_into("<h", page, offset + ACTOR_VALUE_B, spec["value_b"])
            struct.pack_into("<H", page, offset + ACTOR_CLAMP, spec["clamp"])
            # Filler that must stay untouched.
            struct.pack_into("<I", page, offset + 0x004,
                             0xA5A50000 | (base >> 8) | index)
            page[offset + 0x200] = (base >> 8) ^ index ^ 0x5A
    return bytes(page)


def build_ui_page(actors_base: int, records_base: int, tag: int) -> bytes:
    page = bytearray(UI_SIZE)
    struct.pack_into("<I", page, 0x1FC0, actors_base)
    struct.pack_into("<I", page, 0x1E98, records_base)
    # Unrelated sentinels so a wrong offset is visible.
    struct.pack_into("<I", page, 0x0000, 0x10000000 | tag)
    struct.pack_into("<I", page, 0x1FC4, 0xDEAD0000 | tag)
    struct.pack_into("<I", page, 0x1E9C, 0xBEEF0000 | tag)
    return bytes(page)


def build_record_page(tag: int) -> bytes:
    # The function never reads record contents, only the computed pointer, so a
    # deterministic filler plus a few markers is enough to prove non-modification.
    seed = bytes(((i * 37 + tag) & 0xFF) for i in range(256))
    page = bytearray(seed * (RECORDS_SIZE // 256))
    for ident in (0, 1, 2, 3, 4, 5, 6, 7, MAX_TEST_ID):
        base = ident * RECORD_STRIDE
        if base + 4 <= RECORDS_SIZE:
            struct.pack_into("<I", page, base, 0x50C00000 | (tag << 8) | ident)
    return bytes(page)


def build_slot_page(case: dict) -> bytes:
    page = bytearray(SLOT_SIZE)
    struct.pack_into("<I", page, SCRIPT_CONTEXT_SLOT - SLOT_ADDR,
                     case.get("context", 0x00600000) & 0xFFFFFFFF)
    page[0x10] = 0x5A
    page[SLOT_SIZE - 1] = 0xA5
    return bytes(page)


def read_u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


class F7F18Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(SLOT_ADDR, SLOT_SIZE)
        self.uc.mem_map(ACTORS_ADDR, ACTORS_SIZE)
        self.uc.mem_map(UI_A_ADDR, UI_SIZE)
        self.uc.mem_map(UI_B_ADDR, UI_SIZE)
        self.uc.mem_map(RECORDS_ADDR, RECORDS_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        # Enable CP10/CP11 access and the VFP unit: the candidate spills d8 for
        # its 8-byte stack alignment, and this Unicorn build traps VFP until
        # CPACR/FPEXC are programmed.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.ui_calls = 0
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

    def _ui_page(self) -> int:
        self.ui_calls += 1
        if self.case.get("alternate_ui") and self.ui_calls % 2 == 0:
            return UI_B_ADDR
        return UI_A_ADDR

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_296F60:
            self._log(address, r0)
            selectors = self.case.get("selectors", (0, 1, 2))
            value = selectors[r0] if r0 < len(selectors) else 0
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        elif address == STUB_27EB98:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0,
                         self.case.get("handle", 0x00610000) & 0xFFFFFFFF)
        elif address == STUB_293C98:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, self._ui_page())
        elif address == STUB_27E1A0:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, 0xDEAD0001)
        elif address == STUB_250800:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, 0xDEAD0002)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.ui_calls = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(SLOT_ADDR, build_slot_page(case))
        self.uc.mem_write(ACTORS_ADDR, build_actor_page(case))
        self.uc.mem_write(
            UI_A_ADDR, build_ui_page(ACTORS_ADDR, RECORDS_ADDR, 0xA1)
        )
        self.uc.mem_write(
            UI_B_ADDR,
            build_ui_page(ACTORS_ADDR + ACTORS_B_OFFSET,
                          RECORDS_ADDR + RECORDS_B_OFFSET, 0xB2),
        )
        self.uc.mem_write(RECORDS_ADDR, build_record_page(0x11))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for reg, value in ((arm.UC_ARM_REG_R0, 0x11111111),
                           (arm.UC_ARM_REG_R1, 0x22222222),
                           (arm.UC_ARM_REG_R2, 0x33333333),
                           (arm.UC_ARM_REG_R3, 0x44444444)):
            self.uc.reg_write(reg, value)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        for name, value in CALLEE_SAVED_VFP_START.items():
            self.uc.reg_write(CALLEE_SAVED_VFP[name], value)

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
            "callee_saved_vfp": {
                name: self.uc.reg_read(reg)
                for name, reg in CALLEE_SAVED_VFP.items()
            },
            "call_log": list(self.call_log),
            "fixtures": {
                "slot": bytes(self.uc.mem_read(SLOT_ADDR, SLOT_SIZE)),
                "actors": bytes(self.uc.mem_read(ACTORS_ADDR, ACTORS_SIZE)),
                "ui_a": bytes(self.uc.mem_read(UI_A_ADDR, UI_SIZE)),
                "ui_b": bytes(self.uc.mem_read(UI_B_ADDR, UI_SIZE)),
                "records": bytes(self.uc.mem_read(RECORDS_ADDR, RECORDS_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "callee_saved_vfp"):
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
        "selectors": (100, 100, 1),
        "handle": 0x00610000,
        "context": 0x00600000,
    }
    case.update(overrides)
    return case


def actors(**specs) -> list[dict]:
    table = [dict(spec) for spec in DEFAULT_ACTORS]
    for key, value in specs.items():
        index = int(key[1:])
        table[index].update(value)
    return table


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- baseline: two of four actors are emitted (slots 0 and 5)
    cases.append(base_case("baseline: two of four actors emitted"))

    # --- skip conditions, one at a time
    cases.append(base_case("bit0 clear on actor 0",
                           actors_a=actors(a0={"flags": 0x00000000})))
    cases.append(base_case("bit6 set on actor 0",
                           actors_a=actors(a0={"flags": 0x00000041})))
    cases.append(base_case("negative id -1 on actor 0",
                           actors_a=actors(a0={"id": -1})))
    cases.append(base_case("negative id -32768 on actor 0",
                           actors_a=actors(a0={"id": -32768})))
    cases.append(base_case("bit0 clear but bit6 also clear on actor 1",
                           actors_a=actors(a1={"flags": 0x00000000})))
    cases.append(base_case("actor 0 flags 0xFFFFFFFF (both bits set)",
                           actors_a=actors(a0={"flags": 0xFFFFFFFF})))
    cases.append(base_case("all four actors emitted",
                           actors_a=actors(a0={"flags": 1}, a2={"flags": 1},
                                           a3={"flags": 1})))
    cases.append(base_case("no actor emitted",
                           actors_a=actors(a0={"flags": 0}, a1={"flags": 0})))
    cases.append(base_case("only actor 3 emitted",
                           actors_a=actors(a0={"flags": 0}, a1={"flags": 0},
                                           a3={"flags": 1})))

    # --- id boundaries (record pointer = base + id*276)
    for ident in (0, 1, 2, 255, MAX_TEST_ID):
        cases.append(base_case(f"id {ident}",
                               actors_a=actors(a0={"id": ident})))
    cases.append(base_case("ids 2/3/4/5",
                           actors_a=actors(a0={"id": 2, "flags": 1},
                                           a1={"id": 3, "flags": 1},
                                           a2={"id": 4, "flags": 1},
                                           a3={"id": 5, "flags": 1})))

    # --- s16 value boundaries with bit3 clear and set
    for value in (0, 1, 99, 100, 101, 32767, -1, -100, -32768):
        for clamp in (0x0000, 0x0008):
            cases.append(
                base_case(
                    f"value_a={value} value_b={value} clamp=0x{clamp:04x}",
                    actors_a=actors(
                        a0={"value_a": value, "value_b": value, "clamp": clamp,
                            "flags": 1},
                        a1={"flags": 0},
                    ),
                )
            )

    # --- bit3 is isolated: other clamp bits must not trigger the clamp
    for clamp in (0x0004, 0x0010, 0x8000, 0xFFFF):
        cases.append(
            base_case(f"clamp word 0x{clamp:04x}",
                      actors_a=actors(a0={"clamp": clamp, "flags": 1},
                                      a1={"flags": 0}))
        )

    # --- scale values, including wrapping 32-bit products
    for scale_a, scale_b in (
        (0, 0),
        (1, 1),
        (100, 100),
        (0xFFFFFFFF, 0xFFFFFFFF),
        (0x80000000, 0x80000000),
        (0x7FFFFFFF, 0x80000000),
        (0x01000000, 0x00010000),
    ):
        cases.append(
            base_case(
                f"scales 0x{scale_a:08x}/0x{scale_b:08x}",
                selectors=(scale_a, scale_b, 1),
                actors_a=actors(
                    a0={"flags": 1, "value_a": 32767, "value_b": -32768,
                        "clamp": 0},
                    a1={"flags": 1, "value_a": -1, "value_b": 2, "clamp": 0},
                    a2={"flags": 0}, a3={"flags": 0},
                ),
            )
        )

    # --- limit_selector signed comparison (cmp r4,#0 / movgt #0x3E0)
    for selector in (0, 1, 2, -1, -2147483648, 2147483647):
        cases.append(
            base_case(f"limit selector 0x{selector & 0xFFFFFFFF:08x}",
                      selectors=(100, 100, selector))
        )

    # --- 0x0027EB98 handle: null and non-null
    cases.append(base_case("handle null", handle=0))
    cases.append(base_case("handle non-null", handle=0x0061ABCD))

    # --- script context slot value
    cases.append(base_case("context slot null", context=0))
    cases.append(base_case("context slot arbitrary", context=0xFFFFFFF0))

    # --- 0x00293C98 alternating between two UI state pages
    cases.append(base_case("alternating UI state pages", alternate_ui=True))
    cases.append(base_case("alternating UI, all actors emitted",
                           alternate_ui=True,
                           actors_a=actors(a0={"flags": 1}, a1={"flags": 1},
                                           a2={"flags": 1}, a3={"flags": 1})))
    cases.append(base_case("alternating UI, no actor emitted",
                           alternate_ui=True,
                           actors_a=actors(a0={"flags": 0}, a1={"flags": 0},
                                           a2={"flags": 0}, a3={"flags": 0})))

    # --- combined: four emitted actors, clamping, alternate page, zero limit
    cases.append(base_case(
        "combined: four emitted, clamp, alternate UI, limit 0",
        selectors=(37, 1000, 0),
        handle=0,
        alternate_ui=True,
        actors_a=actors(a0={"flags": 1, "id": 3, "value_a": 200,
                            "value_b": -200, "clamp": 0x0008},
                        a1={"flags": 1, "id": 6, "value_a": 99,
                            "value_b": 101, "clamp": 0x0000},
                        a2={"flags": 1, "id": 8, "value_a": -32768,
                            "value_b": 32767, "clamp": 0x0008},
                        a3={"flags": 1, "id": 9, "value_a": 1,
                            "value_b": 1, "clamp": 0x0008}),
    ))
    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = F7F18Runner().run(orig_code, case)
        cand = F7F18Runner().run(cand_code, case)
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
    print("Testing engine_func_002f7f18 (0x002f7f18)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(all eight call relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("hidden_bit", "kActorHiddenBit = 0x40;", "kActorHiddenBit = 0x20;"),
        ("enabled_bit", "kActorEnabledBit = 0x01;", "kActorEnabledBit = 0x02;"),
        ("actor_stride", "kActorStride = 648;", "kActorStride = 644;"),
        ("record_stride", "kRecordStride = 276;", "kRecordStride = 272;"),
        ("clamp_bit", "kClampBit = 0x0008;", "kClampBit = 0x0004;"),
        ("limit_constant", "kLimitEnabled = 0x3E0;", "kLimitEnabled = 0x3E1;"),
        ("slot_stride", "kSlotStride = 5;", "kSlotStride = 4;"),
        ("row_start", "kRowStart = 9;", "kRowStart = 8;"),
        ("sub_call_flags", "kSubCallFlags = 0x010001C1;",
         "kSubCallFlags = 0x010001C0;"),
        ("scale_divisor", "kScaleDivisor = 100;", "kScaleDivisor = 99;"),
        ("unused_argument", "kUnusedArgument = -1;", "kUnusedArgument = -2;"),
        ("limit_comparison", "limit_selector > 0 ? kLimitEnabled",
         "limit_selector >= 0 ? kLimitEnabled"),
        ("id_comparison", "if (id < 0) {", "if (id <= 0) {"),
        ("zero_fixup", "if (value_a == 0) {", "if (value_a == 1) {"),
        ("actor_array_offset", "kActorArrayOffset = 0x1FC0;",
         "kActorArrayOffset = 0x1FC4;"),
        ("record_array_offset", "kRecordArrayOffset = 0x1E98;",
         "kRecordArrayOffset = 0x1E9C;"),
        ("return_value", "    return 1;\n}", "    return 0;\n}"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = F7F18Runner().run(orig_code, case)
            try:
                bad = F7F18Runner().run(mutant_code, case)
            except RuntimeError:
                # A mutant that faults (e.g. a shifted table pointer) is just
                # as detectable as one with a differing call log.
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
