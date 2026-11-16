#!/usr/bin/env python3
"""Differential test for script_vm_func_0037ea70 (0x0037EA70) using Unicorn ARM.

`src/engine/leaf_batch45_a.cpp` is compiled with
`tools.build_check.compile_tu_armv6k`, the `script_vm_func_0037ea70` body is
extracted, its five direct-call relocations are resolved to deterministic stubs
placed at the original targets, and the pinned original
(`extracted/exefs/code.bin`) and the candidate are run in separate Unicorn
machines with identical fixtures.

Compared outputs:

  * return r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log, including the 64-bit arguments and quotient of the
    two 0x002AA504 divides, the stack flag and gathered buffer passed to
    0x0015C310, the entry pointer passed to 0x002BD448, and the object/value
    pair passed to 0x00235DBC;
  * the complete 128 KiB script-VM object page and the 4 KiB controller page;
  * every emulated write outside those pages and the private stack.

Coverage: every gate (state byte, large-offset gate byte, null link, helper
rejection); the normal dispatch early exits (ready byte, controller flag,
controller value); the 0x18-byte entry scan at its first/middle/last index and
with every state class; the slot pass with null and non-null links, every
bound 0..8, the active-byte short circuit, and a stub that shrinks the bound
mid-loop; the special pass in modes 0/1/2/3/0xFF, with positive and negative
64-bit products, the exact 0xFFFFFFFF and 2**32 quotient boundaries, slot
counts 0..8, wrapping/non-wrapping indices including a count of 0, repeated
special passes, a reset stub that clears the gate byte, and a consumer stub
that rewrites the index/count fields.  Negative controls mutate the dispatch
state, the wrap comparison, the helper gate, the saturation value, the slot
value source, the scan condition and the stack flag; every mutant must be
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
SOURCE = ROOT / "src/engine/leaf_batch45_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_0037ea70"

FUNC_ADDR = 0x0037EA70
FUNC_SIZE = 628

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers 0x15C310..0x3E73FC and the target function
OBJ_ADDR = 0x00600000
OBJ_SIZE = 0x00020000  # covers the +0x1B5C time table
CTRL_ADDR = 0x00620000
CTRL_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# The caller passes the sub-object at +0x44; the thunk subtracts it.
THIS_OFFSET = 0x44

# Original direct-call targets.  Both the pinned original and the relocated
# candidate resolve to stubs placed at these addresses.
STUB_3E73FC = 0x003E73FC
STUB_2BD448 = 0x002BD448
STUB_235DBC = 0x00235DBC
STUB_15C310 = 0x0015C310
STUB_2AA504 = 0x002AA504

STUB_NAMES = {
    STUB_3E73FC: "func_003e73fc",
    STUB_2BD448: "engine_func_002bd448",
    STUB_235DBC: "func_00235dbc",
    STUB_15C310: "engine_func_0015c310",
    STUB_2AA504: "script_vm_func_002aa504",
}

# Number of architected stack words each helper receives.
STACK_ARGS = {
    STUB_3E73FC: 0,
    STUB_2BD448: 0,
    STUB_235DBC: 0,
    STUB_15C310: 1,  # the 2/1 dispatch flag
    STUB_2AA504: 0,
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

# Object layout (relative to the adjusted base).
HDR_GATE = 0x0D
HDR_ACTIVE = 0x53
HDR_READY = 0x54
HDR_RUNNING = 0x56
HDR_ACCUMULATOR = 0x58
HDR_CONTROLLER = 0x60
HDR_ENTRY_COUNT = 0x68
HDR_ENTRY_INDEX = 0x6C
HDR_DISPATCH_INDEX = 0x70
HDR_MODE = 0x74
HDR_MODE_VALUE = 0x78
HDR_MODE_SCALE = 0x80
HDR_TIME_FACTOR = 0x94
HDR_SLOT_COUNT = 0xD0
SECONDARY_GATE = 0x1AD8

SLOT_BASE = 0xD8
SLOT_STRIDE = 0x340
SLOT_LINK = 0x30
ENTRY_BASE = 0x10C
ENTRY_STRIDE = 0x18
ENTRY_STATE = 0x11
TIME_BASE = 0x1B5C
TIME_STRIDE = 0x8

DEFAULT_LINK = CTRL_ADDR + 0x300
CTRL_FLAG = 0x4D
CTRL_VALUE = 0x80


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0037ea70" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"script_vm_func_0037ea70 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
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
def build_object(case: dict) -> bytes:
    page = bytearray(OBJ_SIZE)
    for index in range(OBJ_SIZE):
        page[index] = (index * 37 + 0x5B) & 0xFF

    def put32(offset: int, value: int) -> None:
        struct.pack_into("<I", page, offset, value & 0xFFFFFFFF)

    page[HDR_GATE] = case.get("gate_0D", 1) & 0xFF
    page[SECONDARY_GATE] = case.get("gate_1AD8", 1) & 0xFF
    page[HDR_ACTIVE] = case.get("active_53", 0) & 0xFF
    page[HDR_READY] = case.get("ready_54", 0) & 0xFF
    page[HDR_RUNNING] = case.get("running_56", 0) & 0xFF
    put32(HDR_ACCUMULATOR, case.get("accumulator", 0))
    put32(HDR_CONTROLLER, CTRL_ADDR)
    put32(HDR_ENTRY_COUNT, case.get("entry_count", 4))
    put32(HDR_ENTRY_INDEX, case.get("entry_index", 0))
    put32(HDR_DISPATCH_INDEX, case.get("dispatch_index", 0))
    page[HDR_MODE] = case.get("mode", 0) & 0xFF
    put32(HDR_MODE_VALUE, case.get("mode_value", 0))
    put32(HDR_MODE_SCALE, case.get("mode_scale", 1000))
    put32(HDR_TIME_FACTOR, case.get("time_factor", 1))
    put32(HDR_SLOT_COUNT, case.get("slot_count", 0))

    links = dict(case.get("slot_links", {}))
    links[0] = case.get("link", DEFAULT_LINK)
    values = dict(case.get("slot_values", {}))
    for slot in range(8):
        put32(SLOT_BASE + slot * SLOT_STRIDE, values.get(slot, 0))
        put32(SLOT_BASE + slot * SLOT_STRIDE + SLOT_LINK, links.get(slot, 0))

    states = dict(case.get("entry_states", {}))
    default_state = case.get("default_state", 0)
    for entry in range(16):
        page[ENTRY_BASE + entry * ENTRY_STRIDE + ENTRY_STATE] = states.get(
            entry, default_state
        ) & 0xFF

    times = dict(case.get("time_entries", {}))
    for entry in range(16):
        put32(TIME_BASE + entry * TIME_STRIDE, times.get(entry, 0x1000 + entry))
    return bytes(page)


def build_controller(case: dict) -> bytes:
    page = bytearray(CTRL_SIZE)
    for index in range(CTRL_SIZE):
        page[index] = (index * 17 + 0xA5) & 0xFF
    page[CTRL_FLAG] = case.get("ctrl_flag", 0) & 0xFF
    struct.pack_into("<I", page, CTRL_VALUE, case.get("ctrl_value", 1) & 0xFFFFFFFF)
    page[0x17] = case.get("ctrl_selector", 0) & 0xFF
    struct.pack_into("<H", page, 0x20, case.get("ctrl_flags", 0x1234) & 0xFFFF)
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(OBJ_ADDR, OBJ_SIZE)
        self.uc.mem_map(CTRL_ADDR, CTRL_SIZE)
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
        self.slot_calls = 0
        self.mutation_applied = False

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

    def _put32(self, address: int, value: int) -> None:
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_3E73FC:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("helper_return", 1))
        elif address == STUB_2BD448:
            self._log(address, r0)
            uc.mem_write(r0, b"\x00" * 0x18)
            if self.case.get("reset_clears_gate", False):
                self.uc.mem_write(OBJ_ADDR + HDR_GATE, b"\x00")
            if self.case.get("reset_mutation"):
                for offset, value in self.case["reset_mutation"].items():
                    self._put32(OBJ_ADDR + offset, value)
        elif address == STUB_235DBC:
            self._log(address, r0, r1)
            self.slot_calls += 1
            selector = uc.mem_read(r0 + 0x17, 1)[0]
            signed = selector - 0x100 if selector & 0x80 else selector
            if signed != (r1 - (1 << 32) if r1 & 0x80000000 else r1):
                uc.mem_write(r0 + 0x17, struct.pack("<B", r1 & 0xFF))
                flags = struct.unpack("<H", uc.mem_read(r0 + 0x20, 2))[0]
                uc.mem_write(r0 + 0x20, struct.pack("<H", (flags | 2) & 0xFFFF))
            if self.case.get("slot_pass_mutation") and self.slot_calls == 1:
                for offset, value in self.case["slot_pass_mutation"].items():
                    self._put32(OBJ_ADDR + offset, value)
        elif address == STUB_15C310:
            slot_count = min(int(self.case.get("slot_count", 0)), 8)
            buffer_words = (
                tuple(struct.unpack(f"<{slot_count}I", uc.mem_read(r1, 4 * slot_count)))
                if slot_count
                else ()
            )
            flag = self._stack_words(1)[0]
            self._log(address, r0, r1, r2, r3, flag, buffer_words)
            if self.case.get("consume_mutation") and not self.mutation_applied:
                self.mutation_applied = True
                for offset, value in self.case["consume_mutation"].items():
                    self._put32(OBJ_ADDR + offset, value)
        elif address == STUB_2AA504:
            numerator = r0 | (r1 << 32)
            divisor = r2 | (r3 << 32)
            self._log(address, numerator, divisor)
            if divisor == 0:
                raise RuntimeError("0x002AA504 stub received a zero divisor")
            quotient, remainder = divmod(numerator, divisor)
            uc.reg_write(arm.UC_ARM_REG_R0, quotient & 0xFFFFFFFF)
            uc.reg_write(arm.UC_ARM_REG_R1, (quotient >> 32) & 0xFFFFFFFF)
            uc.reg_write(arm.UC_ARM_REG_R2, remainder & 0xFFFFFFFF)
            uc.reg_write(arm.UC_ARM_REG_R3, (remainder >> 32) & 0xFFFFFFFF)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for name, args in log:
            out = []
            for arg in args:
                if isinstance(arg, tuple):
                    out.append(
                        tuple(
                            "<stack>"
                            if isinstance(item, int)
                            and STACK_ADDR <= item < STACK_ADDR + STACK_SIZE
                            else item
                            for item in arg
                        )
                    )
                elif isinstance(arg, int) and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE:
                    out.append("<stack>")
                else:
                    out.append(arg)
            normalised.append((name, tuple(out)))
        return normalised

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.slot_calls = 0
        self.mutation_applied = False

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(OBJ_ADDR, build_object(case))
        self.uc.mem_write(CTRL_ADDR, build_controller(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR + THIS_OFFSET)
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

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_object = OBJ_ADDR <= address < OBJ_ADDR + OBJ_SIZE
            in_controller = CTRL_ADDR <= address < CTRL_ADDR + CTRL_SIZE
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not (in_object or in_controller or in_stack):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "object": bytes(self.uc.mem_read(OBJ_ADDR, OBJ_SIZE)),
            "controller": bytes(self.uc.mem_read(CTRL_ADDR, CTRL_SIZE)),
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
    for key in ("object", "controller"):
        if orig[key] != cand[key]:
            diff = [
                index
                for index, (left, right) in enumerate(zip(orig[key], cand[key]))
                if left != right
            ]
            problems.append(
                f"fixture {key} differs at {len(diff)} byte(s), first {diff[:16]}"
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
        "gate_0D": 1,
        "gate_1AD8": 1,
        "link": DEFAULT_LINK,
        "helper_return": 1,
        "ready_54": 0,
        "ctrl_flag": 0,
        "ctrl_value": 1,
        "entry_count": 4,
        "entry_index": 0,
        "dispatch_index": 0,
        "default_state": 0,
        "entry_states": {},
        "slot_count": 0,
        "time_factor": 1,
        "slot_values": {},
        "slot_links": {},
        "time_entries": {},
        "mode": 0,
        "mode_value": 0,
        "mode_scale": 1000,
        "active_53": 0,
        "accumulator": 0,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- gate chain ---------------------------------------------------------
    cases.append(base_case("gate 0x0D zero", gate_0D=0))
    cases.append(base_case("gate 0x0D 0xFF", gate_0D=0xFF))
    cases.append(base_case("secondary gate zero", gate_1AD8=0))
    cases.append(base_case("secondary gate 0xFF", gate_1AD8=0xFF))
    cases.append(base_case("null link", link=0))
    cases.append(base_case("helper rejects link", helper_return=0))
    cases.append(base_case("helper accepts link", helper_return=1))
    cases.append(base_case("helper returns 0xFFFFFFFF", helper_return=0xFFFFFFFF))

    # --- normal dispatch early exits ---------------------------------------
    for ready in (1, 2, 0x7F, 0xFF):
        cases.append(base_case(f"ready 0x{ready:02x}", ready_54=ready))
    for flag in (1, 0x40, 0xFF):
        cases.append(base_case(f"controller flag 0x{flag:02x}", ctrl_flag=flag))
    cases.append(base_case("controller value zero", ctrl_value=0))
    cases.append(base_case("controller value maximum", ctrl_value=0xFFFFFFFF))

    # --- entry scan ---------------------------------------------------------
    cases.append(base_case("scan empty count 0", entry_count=0))
    cases.append(base_case("scan count 1 state 0", entry_count=1))
    cases.append(base_case("scan first entry state 1", entry_states={0: 1}))
    cases.append(base_case("scan first entry state 2", entry_states={0: 2}))
    cases.append(base_case("scan middle entry state 1", entry_states={2: 1}))
    cases.append(base_case("scan last entry state 2", entry_states={3: 2}))
    cases.append(base_case("scan last entry state 1", entry_count=8,
                           entry_states={7: 1}))
    cases.append(base_case("scan ignores state 3", entry_states={0: 3}))
    cases.append(base_case("scan ignores state 4", entry_states={0: 4}))
    cases.append(base_case("scan ignores state 0xFF", entry_states={0: 0xFF}))
    cases.append(base_case("scan state 1 after state 3", entry_states={0: 3, 1: 1}))
    cases.append(base_case("scan dispatch entry state 3 is special",
                           entry_count=4, dispatch_index=2,
                           entry_states={2: 3}))

    # --- slot pass ----------------------------------------------------------
    links = {
        0: DEFAULT_LINK,
        1: 0,
        2: CTRL_ADDR + 0x400,
        3: 0,
        4: CTRL_ADDR + 0x500,
        5: 0,
        6: CTRL_ADDR + 0x600,
        7: CTRL_ADDR + 0x700,
    }
    for count in range(0, 9):
        cases.append(
            base_case(f"slot pass count {count}", slot_count=count,
                      slot_links=links)
        )
    cases.append(base_case("slot pass active 1 short circuit", slot_count=5,
                           active_53=1, slot_links=links))
    cases.append(base_case("slot pass active 2 is not 1", slot_count=5,
                           active_53=2, slot_links=links))
    cases.append(base_case("slot pass selector already 1", slot_count=3,
                           slot_links=links, ctrl_selector=1,
                           ctrl_flags=0x0002))
    cases.append(base_case("slot pass selector 0x80", slot_count=3,
                           slot_links=links, ctrl_selector=0x80,
                           ctrl_flags=0x0000))
    cases.append(base_case("slot pass shrinks bound after first call",
                           slot_count=4, slot_links=links,
                           slot_pass_mutation={HDR_SLOT_COUNT: 1}))
    cases.append(base_case("slot pass grows bound after first call",
                           slot_count=2, slot_links=links,
                           slot_pass_mutation={HDR_SLOT_COUNT: 5}))
    cases.append(base_case("slot pass count ignored when zero links",
                           slot_count=3,
                           slot_links={0: DEFAULT_LINK, 1: 0, 2: 0}))

    # --- special pass: mode 0 ----------------------------------------------
    cases.append(base_case("special mode 0", dispatch_index=0,
                           entry_states={0: 3}, entry_count=4,
                           mode=0, mode_value=0x12345678,
                           accumulator=0x01020304, time_entries={0: 0x11223344}))
    cases.append(base_case("special mode 0 index 3", dispatch_index=3,
                           entry_states={3: 3}, entry_count=4,
                           mode=0, mode_value=0xFFFFFFFF,
                           accumulator=0xFFFFFFFF, time_entries={3: 2}))
    cases.append(base_case("special mode 3", dispatch_index=1,
                           entry_states={1: 3}, entry_count=4,
                           mode=3, mode_value=0x12345678))
    cases.append(base_case("special mode 0xFF", dispatch_index=1,
                           entry_states={1: 3}, entry_count=4,
                           mode=0xFF, mode_value=0x12345678))

    # --- special pass: mode 1 division -------------------------------------
    division_cases = (
        ("zero product", 0, 1000),
        ("unit", 1, 1000),
        ("small product", 3, 7),
        ("signed negative", -1, 1000),
        ("signed minimum", -0x80000000, 1),
        ("unsigned maximum factor", 1000, 0xFFFFFFFF),
        ("quotient exactly 0xFFFFFFFF", 1000, 0xFFFFFFFF),
        ("quotient 2**32", 0x40000000, 4000),
        ("quotient just below 2**32", 0x40000000, 3999),
        ("factor high bit", 1, 0x80000000),
        ("factor high bit negative value", -2, 0x80000000),
        ("both large positive", 0x7FFFFFFF, 0xFFFFFFFF),
        ("scale zero", 0x7FFFFFFF, 0),
    )
    for name, value, scale in division_cases:
        cases.append(
            base_case(f"special mode 1 {name}", dispatch_index=2,
                      entry_states={2: 3}, entry_count=4,
                      mode=1, mode_value=value, mode_scale=scale)
        )

    # --- special pass: gathers every slot count ----------------------------
    slot_values = {slot: 0x10000000 + slot * 0x01010101 for slot in range(8)}
    for count in range(0, 9):
        cases.append(
            base_case(f"special slot gather {count}", dispatch_index=1,
                      entry_states={1: 3}, entry_count=4, slot_count=count,
                      time_factor=3, entry_index=7,
                      slot_values=slot_values,
                      slot_links=links)
        )

    # --- special pass: counter wrap and re-entry ---------------------------
    cases.append(base_case("special first index count 1 wrap", dispatch_index=0,
                           entry_count=1, entry_states={0: 3}))
    cases.append(base_case("special count 0 wrap", dispatch_index=5,
                           entry_count=0, entry_states={5: 3}))
    cases.append(base_case("special index wrap at count 2", dispatch_index=1,
                           entry_count=2, entry_states={1: 3}))
    cases.append(base_case("special repeated passes", dispatch_index=0,
                           entry_count=4, entry_states={0: 3, 1: 3, 2: 0},
                           slot_count=2, slot_values=slot_values,
                           slot_links=links))
    cases.append(base_case("special all entries special", entry_count=3,
                           dispatch_index=0,
                           entry_states={0: 3, 1: 3, 2: 3}))
    cases.append(base_case("special entry index 0xFFFFFFFF wrap",
                           dispatch_index=0, entry_count=4,
                           entry_states={0: 3}, entry_index=0xFFFFFFFF))
    cases.append(base_case("special entry index maximum", dispatch_index=0,
                           entry_count=4, entry_states={0: 3},
                           entry_index=0xFFFFFFFE))
    cases.append(base_case("special resets gate byte", dispatch_index=0,
                           entry_count=4, entry_states={0: 3},
                           reset_clears_gate=True))
    cases.append(base_case("special reset clears next entry", dispatch_index=0,
                           entry_count=4, entry_states={0: 3, 1: 3},
                           reset_mutation={HDR_DISPATCH_INDEX: 1}))
    cases.append(base_case("special consumer rewrites counters",
                           dispatch_index=1, entry_count=4,
                           entry_states={1: 3},
                           consume_mutation={
                               HDR_ENTRY_COUNT: 2,
                               HDR_ENTRY_INDEX: 0xFFFFFFFF,
                               HDR_DISPATCH_INDEX: 1,
                           }))
    cases.append(base_case("special mode 1 and slot gather", dispatch_index=1,
                           entry_count=4, entry_states={1: 3},
                           mode=1, mode_value=1234567, mode_scale=999,
                           slot_count=3, time_factor=5, entry_index=11,
                           slot_values=slot_values, slot_links=links))

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
    print("Testing script_vm_func_0037ea70 (0x0037EA70)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("dispatch_state", "if (entry->state_11 == 3) {",
         "if (entry->state_11 == 2) {"),
        ("wrap_comparison", "if (next_entry_index >= entry_count) {",
         "if (next_entry_index > entry_count) {"),
        ("helper_gate", "if (func_003e73fc(link) == 0) {",
         "if (func_003e73fc(link) != 0) {"),
        ("saturation", "constexpr u32 kSaturated = 0xFFFFFFFFu;",
         "constexpr u32 kSaturated = 0xFFFFFFFEu;"),
        ("slot_value_source",
         "factor * entry_index + slot_at(base, slot)->value_00;",
         "factor * entry_index + slot_at(base, slot)->link_30;"),
        ("scan_state_test", "if (state == 2 || state == 1) {",
         "if (state == 2) {"),
        ("stack_flag",
         "const u32 call_flag = (header->gate_0D != 0) ? 2u : 1u;",
         "const u32 call_flag = (header->gate_0D != 0) ? 1u : 2u;"),
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
