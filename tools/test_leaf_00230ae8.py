#!/usr/bin/env python3
"""Differential test for shop_func_00230ae8 (0x00230ae8) using Unicorn ARM.

Compiles src/engine/leaf_batch44_b.cpp, extracts the shop_func_00230ae8 body,
resolves its ten direct call sites to deterministic stubs and runs the pinned
original (extracted/exefs/code.bin) against the candidate in separate Unicorn
machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every argument of every helper;
  * the full 0x400-byte touch-region list and 0x400-byte cursor host block
    (every store and every untouched sentinel);
  * any emulated write outside the private stack and those two blocks.

Coverage: all three -1 setup guards (including the first/second/third load
order), zero/negative/large-negative handle counts, every touch-state class
(0, 1, 2, 6, other) alone and in mixed sequences, signed 16-bit handle
boundaries, cursor kinds 0/1/none, visible-limit equal/less/greater and signed
32-bit wrap boundaries, both getter families with distinct per-call returns,
null/non-null and selected/other lookup values, and the debug registration call
with the +0x10 flag clear and set.  Positive expectations are recomputed from
the case description independently of the emulated original.

Negative controls mutate the state-1/2 selection, the count guard, the visible
limit comparison, the kind-1 first getter, the registration constant and the
kind-0 setter argument; each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch44_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_00230ae8"

FUNC_ADDR = 0x00230AE8
FUNC_SIZE = 408

IMAGE_ADDR = 0x00100000
IMAGE_SIZE = 0x00500000
SELF_ADDR = 0x00710000
SELF_SIZE = 0x00000400
HOST_ADDR = 0x00720000
HOST_SIZE = 0x00000400
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
CURSOR_ADDR = HOST_ADDR + 0x10

STUB_TOUCH = 0x0029D8FC
STUB_GET_PLAIN_FIRST = 0x0029F260
STUB_GET_KIND1_FIRST = 0x0029EBDC
STUB_LOOKUP_KIND1 = 0x00240EA4
STUB_LOOKUP_PLAIN = 0x0029E3BC
STUB_SET_PLAIN_POSITION = 0x00299000
STUB_SET_PLAIN_INDEX = 0x0029D8C0
STUB_SET_KIND1_POSITION = 0x0022A60C
STUB_SET_KIND1_INDEX = 0x00299558
STUB_REGISTER = 0x002B91C4

STUB_NAMES = {
    STUB_TOUCH: "ui_func_0029d8fc",
    STUB_GET_PLAIN_FIRST: "camp_func_0029f260",
    STUB_GET_KIND1_FIRST: "camp_func_0029ebdc",
    STUB_LOOKUP_KIND1: "shop_func_00240ea4",
    STUB_LOOKUP_PLAIN: "camp_func_0029e3bc",
    STUB_SET_PLAIN_POSITION: "script_vm_func_00299000",
    STUB_SET_PLAIN_INDEX: "camp_func_0029d8c0",
    STUB_SET_KIND1_POSITION: "shop_func_0022a60c",
    STUB_SET_KIND1_INDEX: "engine_func_00299558",
    STUB_REGISTER: "script_vm_func_002b91c4",
}

REGISTRATION_VALUE = 0x0100016C

# Offsets in the touch-region list.
OFF_REGION_04 = 0x04
OFF_REGION_08 = 0x08
OFF_REGION_COUNT = 0x0C
OFF_DEBUG_FLAGS = 0x10
OFF_ACTIVE = 0x11
OFF_RELEASE = 0x12
OFF_SELECTED = 0x14
OFF_HANDLES = 0x18

# Offsets in the cursor host block.
OFF_KIND = 0x00
OFF_VISIBLE_LIMIT = 0x08

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


# --------------------------------------------------------------------- helpers
def signed16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def signed32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value & 0x80000000 else value


def wrap32(value: int) -> int:
    return value & 0xFFFFFFFF


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00230ae8" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"shop_func_00230ae8 not found in {obj_file}: {sorted(funcs)}"
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
            pc = FUNC_ADDR + rel.offset + 8
            offset = target - pc
            if offset & 3:
                raise RuntimeError(f"unaligned call target 0x{target:08x}")
            displacement = offset >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            condition = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, condition | (displacement & 0x00FFFFFF)
            )
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch44_b.o"
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
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "region_04": 0x20,
        "region_08": 0x21,
        "count": 1,
        "debug_flags": 0,
        "handles": [0x40],
        "states": [1],
        "kind": 0,
        "visible_limit": 100,
        "f260_returns": [0x10],
        "ebdc_returns": [0x10],
        "lookup_plain": 0,
        "lookup_kind1": 0,
        "initial_active": 0xA5,
        "initial_selected": 0x1234,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- unregistered-region guards ----------------------------------------
    cases.append(base_case("guard region_04 = -1", region_04=-1, states=[1]))
    cases.append(base_case("guard region_08 = -1", region_08=-1, states=[1]))
    cases.append(base_case("guard count = -1 (also the count field)",
                           count=-1, states=[1]))
    cases.append(base_case("guard all three = -1", region_04=-1, region_08=-1,
                           count=-1))
    cases.append(base_case("guard region_04 = -1, count 3",
                           region_04=-1, count=3, handles=[1, 2, 3],
                           states=[1, 2, 6]))
    cases.append(base_case("guard bypass with stored active clear",
                           region_04=-1, count=3, handles=[1, 2, 3],
                           states=[1, 2, 6], initial_active=0))
    cases.append(base_case("guard bypass with stored index 0",
                           region_08=-1, count=2, handles=[1, 2],
                           states=[1, 2], initial_selected=0,
                           visible_limit=1000))
    cases.append(base_case("guard region_04 = -2 is registered",
                           region_04=-2, count=0))

    # --- count <= 0 after the setup stores ---------------------------------
    for count in (0, -2, -5, -0x80000000):
        cases.append(base_case(f"count {count} skips the loop", count=count,
                               handles=[0x11], states=[1]))
    cases.append(base_case("count 0 leaves the state sentinels cleared",
                           count=0, debug_flags=0xFF, kind=1))

    # --- touch states, single handle ---------------------------------------
    for state in (0, 1, 2, 3, 4, 5, 6, 7, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"single handle state {state:#04x}",
                               states=[state], kind=1,
                               f260_returns=[0x20],
                               ebdc_returns=[0x20]))
    cases.append(base_case("single handle state 2, kind 0", states=[2], kind=0))
    cases.append(base_case("single handle state 6, kind 0", states=[6], kind=0))

    # --- mixed handle sequences --------------------------------------------
    sequences = (
        [6, 0],
        [6, 1],
        [1, 6],
        [6, 1, 2],
        [2, 6, 2],
        [3, 1, 3],
        [1, 2, 6],
        [6, 6, 6],
        [0, 0, 1],
        [2, 0, 0],
        [0x40, 0x80, 0xC0],
    )
    for states in sequences:
        handles = [0x100 + index for index in range(len(states))]
        cases.append(base_case(
            "states " + "/".join(str(value) for value in states),
            count=len(states), handles=handles, states=states, kind=1,
            f260_returns=[0x30, 0x31, 0x32],
            ebdc_returns=[0x40, 0x41, 0x42],
        ))

    # --- signed 16-bit handle boundaries -----------------------------------
    cases.append(base_case(
        "signed handles -0x8000/0x7fff/-1/0",
        count=4, handles=[-0x8000, 0x7FFF, -1, 0], states=[0, 1, 2, 6],
        kind=0, f260_returns=[0x50, 0x51, 0x52]))
    cases.append(base_case(
        "signed handles 0x7fff/-0x8000", count=2,
        handles=[0x7FFF, -0x8000], states=[2, 1], kind=1,
        ebdc_returns=[0x60, 0x61, 0x62]))
    cases.append(base_case(
        "duplicate signed handles", count=3,
        handles=[-2, -2, 0x7FFF], states=[1, 6, 2], kind=0,
        f260_returns=[0x70, 0x71, 0x72]))

    # --- kind 0 cursor path: getters, limit, setters ----------------------
    cases.append(base_case("kind 0 active, limit above",
                           states=[1], kind=0, visible_limit=100,
                           f260_returns=[5, 6, 7], lookup_plain=0))
    cases.append(base_case("kind 0 limit equal", states=[1], kind=0,
                           visible_limit=10, f260_returns=[10, 6, 7]))
    cases.append(base_case("kind 0 limit below", states=[1], kind=0,
                           visible_limit=9, f260_returns=[10, 6, 7]))
    cases.append(base_case("kind 0 limit above by one", states=[1], kind=0,
                           visible_limit=11, f260_returns=[10, 6, 7]))
    cases.append(base_case("kind 0 negative scroll equal", states=[1], kind=0,
                           visible_limit=-5, f260_returns=[-5, 6, 7]))
    cases.append(base_case("kind 0 negative scroll above", states=[1], kind=0,
                           visible_limit=-4, f260_returns=[-5, 6, 7]))
    cases.append(base_case("kind 0 positive overflow proceeds", states=[1],
                           kind=0, visible_limit=0x10,
                           f260_returns=[0x7FFFFFFF, 6, 7]))
    cases.append(base_case("kind 0 positive overflow equal", states=[1],
                           kind=0, visible_limit=0x80000000,
                           f260_returns=[0x7FFFFFFF, 6, 7]))
    cases.append(base_case("kind 0 negative overflow proceeds", states=[1],
                           kind=0, visible_limit=0,
                           f260_returns=[-0x7FFFFFFF - 1, 6, 7]))
    cases.append(base_case("kind 0 debug set, lookup equals index",
                           states=[1], kind=0, debug_flags=1,
                           f260_returns=[5, 6, 7], lookup_plain=0))
    cases.append(base_case("kind 0 debug set, lookup differs",
                           states=[1], kind=0, debug_flags=1,
                           f260_returns=[5, 6, 7], lookup_plain=0x99))
    cases.append(base_case("kind 0 debug clear, lookup differs",
                           states=[1], kind=0, debug_flags=0,
                           f260_returns=[5, 6, 7], lookup_plain=0x99))
    cases.append(base_case("kind 0 debug flag 0x80, lookup differs",
                           states=[1], kind=0, debug_flags=0x80,
                           f260_returns=[5, 6, 7], lookup_plain=0xFFFFFFFF))
    cases.append(base_case("kind 0 lookup selected after index 2",
                           count=3, handles=[0x10, 0x11, 0x12],
                           states=[0, 0, 1], kind=0, debug_flags=1,
                           visible_limit=100, f260_returns=[3, 4, 5],
                           lookup_plain=2))
    cases.append(base_case("kind 0 lookup high word differs from index",
                           count=2, handles=[0x10, 0x11], states=[0, 1],
                           kind=0, debug_flags=1, visible_limit=100,
                           f260_returns=[3, 4, 5], lookup_plain=0x80000001))

    # --- kind 1 cursor path ------------------------------------------------
    cases.append(base_case("kind 1 active, limit above", states=[1], kind=1,
                           visible_limit=100, ebdc_returns=[5, 6, 7]))
    cases.append(base_case("kind 1 limit equal", states=[2], kind=1,
                           visible_limit=10, ebdc_returns=[10, 6, 7]))
    cases.append(base_case("kind 1 limit below", states=[2], kind=1,
                           visible_limit=9, ebdc_returns=[10, 6, 7]))
    cases.append(base_case("kind 1 negative wrap", states=[1], kind=1,
                           visible_limit=-3, ebdc_returns=[-3, 6, 7]))
    cases.append(base_case("kind 1 debug set, lookup differs", states=[1],
                           kind=1, debug_flags=1, ebdc_returns=[5, 6, 7],
                           lookup_kind1=0x80000000))
    cases.append(base_case("kind 1 debug set, lookup equals index", states=[1],
                           kind=1, debug_flags=1, ebdc_returns=[5, 6, 7],
                           lookup_kind1=0))
    cases.append(base_case("kind 1 debug clear, lookup differs", states=[1],
                           kind=1, debug_flags=0, ebdc_returns=[5, 6, 7],
                           lookup_kind1=0xEE))
    cases.append(base_case("kind 1 selected index 2, lookup equals",
                           count=3, handles=[0x10, 0x11, 0x12],
                           states=[0, 0, 2], kind=1, debug_flags=1,
                           visible_limit=100, ebdc_returns=[3, 4, 5],
                           lookup_kind1=2))

    # --- other kinds use the plain getters and return the kind byte -------
    for kind in (2, 3, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"kind {kind:#04x} plain getters", states=[1],
                               kind=kind, visible_limit=100,
                               f260_returns=[0x11, 0x12, 0x13],
                               lookup_plain=0))
        cases.append(base_case(f"kind {kind:#04x} limit equal", states=[1],
                               kind=kind, visible_limit=0x11,
                               f260_returns=[0x11, 0x12, 0x13]))
    cases.append(base_case("kind 0xFF debug set, lookup differs", states=[2],
                           kind=0xFF, debug_flags=1, visible_limit=100,
                           f260_returns=[5, 6, 7], lookup_plain=0x77))

    # --- longer scans and a guard-bypass full cursor path ------------------
    cases.append(base_case(
        "six handles mixed, selected index 5",
        count=6, handles=[0x20, 0x21, 0x22, 0x23, 0x24, 0x25],
        states=[6, 0, 1, 6, 3, 2], kind=0, debug_flags=1,
        visible_limit=1000, f260_returns=[0x80, 0x81, 0x82],
        lookup_plain=5))
    cases.append(base_case(
        "five handles all state 2, kind 1",
        count=5, handles=[0x30, 0x31, 0x32, 0x33, 0x34],
        states=[2, 2, 2, 2, 2], kind=1, debug_flags=1,
        visible_limit=1000, ebdc_returns=[0x90, 0x91, 0x92],
        lookup_kind1=4))
    cases.append(base_case(
        "guard bypass keeps stale selection through cursor path",
        region_08=-1, count=3, handles=[1, 2, 3], states=[1, 2, 6],
        kind=1, debug_flags=1, visible_limit=100000,
        ebdc_returns=[1, 2, 3], lookup_kind1=0x1234))

    return cases


# ------------------------------------------------------------------ emulation
class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(IMAGE_ADDR, IMAGE_SIZE)
        self.uc.mem_map(SELF_ADDR, SELF_SIZE)
        self.uc.mem_map(HOST_ADDR, HOST_SIZE)
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
        self.touch_index = 0
        self.plain_get_index = 0
        self.kind1_get_index = 0
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], tuple(args)))

    def _next(self, key: str, index: int) -> int:
        sequence = self.case[key]
        value = sequence[min(index, len(sequence) - 1)]
        return value & 0xFFFFFFFF

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)

        if address == STUB_TOUCH:
            handle = signed16(r0)
            self._log(address, handle)
            index = self.touch_index
            states = self.case["states"]
            state = states[min(index, len(states) - 1)]
            self.touch_index += 1
            uc.reg_write(arm.UC_ARM_REG_R0, state & 0xFF)
        elif address in (STUB_GET_PLAIN_FIRST, STUB_GET_KIND1_FIRST):
            self._log(address, r0)
            if address == STUB_GET_PLAIN_FIRST:
                index = self.plain_get_index
                self.plain_get_index += 1
                uc.reg_write(arm.UC_ARM_REG_R0, self._next("f260_returns", index))
            else:
                index = self.kind1_get_index
                self.kind1_get_index += 1
                uc.reg_write(arm.UC_ARM_REG_R0, self._next("ebdc_returns", index))
        elif address in (STUB_LOOKUP_KIND1, STUB_LOOKUP_PLAIN):
            self._log(address, r0)
            value = (self.case["lookup_kind1"]
                     if address == STUB_LOOKUP_KIND1
                     else self.case["lookup_plain"])
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        elif address in (
            STUB_SET_PLAIN_POSITION,
            STUB_SET_PLAIN_INDEX,
            STUB_SET_KIND1_POSITION,
            STUB_SET_KIND1_INDEX,
        ):
            self._log(address, r0, r1)
            # The real setters return with r0 unchanged; that value is the
            # cursor pointer for both 0x29D8C0 and 0x299558.
        elif address == STUB_REGISTER:
            self._log(address, r0)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.touch_index = 0
        self.plain_get_index = 0
        self.kind1_get_index = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)

        self_page = bytearray(SELF_SIZE)
        for index in range(SELF_SIZE):
            self_page[index] = (index * 29 + 0x6D) & 0xFF
        struct.pack_into("<I", self_page, 0x00, 0x00112233)
        struct.pack_into("<i", self_page, OFF_REGION_04, case["region_04"])
        struct.pack_into("<i", self_page, OFF_REGION_08, case["region_08"])
        struct.pack_into("<i", self_page, OFF_REGION_COUNT, case["count"])
        self_page[OFF_DEBUG_FLAGS] = case["debug_flags"] & 0xFF
        self_page[OFF_ACTIVE] = case["initial_active"] & 0xFF
        self_page[OFF_RELEASE] = 0x5A
        self_page[0x13] = 0xC3
        struct.pack_into("<h", self_page, OFF_SELECTED,
                         signed16(case["initial_selected"]))
        for index, handle in enumerate(case["handles"]):
            struct.pack_into("<h", self_page, OFF_HANDLES + index * 2, handle)
        self.uc.mem_write(SELF_ADDR, bytes(self_page))

        host_page = bytearray(HOST_SIZE)
        for index in range(HOST_SIZE):
            host_page[index] = (index * 43 + 0x17) & 0xFF
        host_page[OFF_KIND] = case["kind"] & 0xFF
        struct.pack_into("<i", host_page, OFF_VISIBLE_LIMIT,
                         signed32(case["visible_limit"]))
        struct.pack_into("<I", host_page, 0x0C, 0x13572468)
        host_page[CURSOR_ADDR - HOST_ADDR + 0x62] = 0x7E
        self.uc.mem_write(HOST_ADDR, bytes(host_page))

        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, HOST_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
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
            in_self = SELF_ADDR <= address < SELF_ADDR + SELF_SIZE
            in_host = HOST_ADDR <= address < HOST_ADDR + HOST_SIZE
            if not (in_stack or in_self or in_host):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "self_page": bytes(self.uc.mem_read(SELF_ADDR, SELF_SIZE)),
            "host_page": bytes(self.uc.mem_read(HOST_ADDR, HOST_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


# ----------------------------------------------------------------- comparison
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
    if orig["self_page"] != cand["self_page"]:
        words_orig = struct.unpack("<256I", orig["self_page"])
        words_cand = struct.unpack("<256I", cand["self_page"])
        diffs = [
            (index * 4, words_orig[index], words_cand[index])
            for index in range(len(words_orig))
            if words_orig[index] != words_cand[index]
        ]
        problems.append(f"touch-region list differs at {diffs[:8]}")
    if orig["host_page"] != cand["host_page"]:
        problems.append("cursor host block differs")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


# --------------------------------------------------- independent expectations
def expected_touch_fields(case: dict) -> dict:
    if (case["region_04"] == -1 or case["region_08"] == -1
            or case["count"] == -1):
        return {"guard": True, "active": case["initial_active"] & 0xFF,
                "release": 0x5A, "selected": case["initial_selected"] & 0xFFFF}
    count = case["count"]
    active = 0
    release = 0
    selected = -1
    if count > 0:
        for index in range(count):
            state = case["states"][min(index, len(case["states"]) - 1)]
            if state in (1, 2):
                active = 1
                selected = index
            elif state == 6:
                active = 0
                release = 1
                selected = index
    return {"guard": False, "active": active, "release": release,
            "selected": selected & 0xFFFF}


def expected_calls(case: dict, fields: dict) -> tuple[list, int]:
    """Return the expected call log and expected r0."""
    count = case["count"]
    calls = []
    if not fields["guard"] and count > 0:
        for index in range(count):
            handle = signed16(case["handles"][index])
            calls.append((STUB_NAMES[STUB_TOUCH], (handle,)))

    if fields["active"] == 0:
        return calls, 0

    kind = case["kind"] & 0xFF
    selected = signed16(fields["selected"])
    plain = kind != 1
    get_name = STUB_NAMES[STUB_GET_PLAIN_FIRST if plain
                         else STUB_GET_KIND1_FIRST]
    lookup_name = STUB_NAMES[STUB_LOOKUP_PLAIN if plain
                            else STUB_LOOKUP_KIND1]

    first_ret = case["f260_returns"][0] if plain else case["ebdc_returns"][0]
    calls.append((get_name, (CURSOR_ADDR,)))
    visible_end = wrap32(first_ret + selected)
    if signed32(case["visible_limit"]) <= signed32(visible_end):
        return calls, visible_end

    lookup = case["lookup_plain"] if plain else case["lookup_kind1"]
    calls.append((lookup_name, (CURSOR_ADDR,)))
    if case["debug_flags"] != 0 and wrap32(lookup) != wrap32(selected):
        calls.append((STUB_NAMES[STUB_REGISTER], (REGISTRATION_VALUE,)))

    sequence = case["f260_returns"] if plain else case["ebdc_returns"]
    third_ret = sequence[min(1, len(sequence) - 1)]
    calls.append((get_name, (CURSOR_ADDR,)))

    if kind == 0:
        calls.append((STUB_NAMES[STUB_SET_PLAIN_POSITION],
                      (CURSOR_ADDR, wrap32(third_ret))))
        calls.append((STUB_NAMES[STUB_SET_PLAIN_INDEX],
                      (CURSOR_ADDR, wrap32(selected))))
        return calls, kind
    if kind == 1:
        calls.append((STUB_NAMES[STUB_SET_KIND1_POSITION],
                      (CURSOR_ADDR, wrap32(third_ret))))
        calls.append((STUB_NAMES[STUB_SET_KIND1_INDEX],
                      (CURSOR_ADDR, wrap32(selected))))
        return calls, CURSOR_ADDR
    return calls, kind


def check_expectations(case: dict, result: dict) -> None:
    fields = expected_touch_fields(case)
    self_page = result["self_page"]
    assert self_page[OFF_ACTIVE] == fields["active"], (
        f"{case['name']}: active byte {self_page[OFF_ACTIVE]:#04x} != "
        f"{fields['active']:#04x}"
    )
    assert self_page[OFF_RELEASE] == fields["release"], (
        f"{case['name']}: release byte {self_page[OFF_RELEASE]:#04x} != "
        f"{fields['release']:#04x}"
    )
    assert struct.unpack_from("<h", self_page, OFF_SELECTED)[0] == \
        signed16(fields["selected"]), f"{case['name']}: selected index"

    calls, ret = expected_calls(case, fields)
    assert result["call_log"] == calls, (
        f"{case['name']}: calls\n  got  {result['call_log']}\n  want {calls}"
    )
    assert result["ret"] == ret, (
        f"{case['name']}: return {result['ret']:#010x} != {ret:#010x}"
    )


def _expectation_fails(case: dict, result: dict) -> bool:
    try:
        check_expectations(case, result)
    except AssertionError:
        return True
    return False


# ----------------------------------------------------------------------- main
def run_case_set(orig_code: bytes, cand_code: bytes, cases: list[dict]) -> int:
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
        check_expectations(case, cand)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing shop_func_00230ae8 (0x00230ae8)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"  original: {len(orig_code)} B, candidate: {len(cand_code)} B")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    controls = (
        ("state_2_dropped", "state == 1 || state == 2", "state == 1"),
        ("count_guard", "if (count > 0)", "if (count >= 0)"),
        ("visible_limit", "host->visible_limit_08 <= visible_end",
         "host->visible_limit_08 < visible_end"),
        ("kind1_first_getter", "cursor_position = camp_func_0029ebdc(cursor);",
         "cursor_position = camp_func_0029f260(cursor);"),
        ("registration_constant", "reinterpret_cast<void*>(0x0100016Cu)",
         "reinterpret_cast<void*>(0x0100016Du)"),
        ("plain_index_setter", "camp_func_0029d8c0(cursor, selected);",
         "camp_func_0029d8c0(cursor, cursor_value);"),
    )
    for name, old, new in controls:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant_code, case)
            if compare(orig, bad) or _expectation_fails(case, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
