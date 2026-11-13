#!/usr/bin/env python3
"""Differential test for engine_func_00155fd0 (0x00155FD0) using Unicorn ARM.

Compiles src/engine/leaf_batch28_a.cpp, extracts the engine_func_00155fd0 body,
resolves its direct calls to deterministic stubs, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

The 412-byte symbol contains a 24-byte entry stub (0x00155FD0..0x00155FE7)
that resolves the owning object through 0x002AD630 and falls through into the
frame loop at 0x00155FE8.  Execution therefore starts at 0x00155FD0.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with the register arguments of every helper, the
    output values written by the tick/measure helpers and the getter indices;
  * the full object page (including the frame-duration words at +0x00/+0x04
    and the loop flag at +0x0D), the profiler table page at 0x004E6F14 and any
    emulated write outside the private stack/object pages.

Coverage: the tick/no-tick branch, the getter arm for every signed selector
boundary, zero and non-zero getter results, the null/non-null work callback,
the callback gate, the second callback, one to three loop iterations, selector
and gate changes between iterations, and 64-bit tick/measure wrap-around.
Negative controls mutate the loop flag, the tick subtraction, the selector
mask, the callback gate and the duration store offset.
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
SOURCE = ROOT / "src/engine/leaf_batch28_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_00155fd0"

FUNC_ADDR = 0x00155FD0
FUNC_SIZE = 412

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x300000
DATA_ADDR = 0x00400000
DATA_SIZE = 0x001F0000  # covers the profiler table at 0x004E6F14
CTX_ADDR = 0x00600000
CTX_SIZE = 0x00010000
CB_ADDR = 0x00700000
CB_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

PROFILER_TABLE = 0x004E6F14

# Original direct-call targets; stubs are placed at the same addresses so both
# the original bytes and the relocated candidate resolve to them.
STUB_2AD630 = 0x002AD630
STUB_159DC4 = 0x00159DC4
STUB_2A232C = 0x002A232C
STUB_153268 = 0x00153268
STUB_2C4244 = 0x002C4244
STUB_2C3AA8 = 0x002C3AA8
STUB_2C3A24 = 0x002C3A24
STUB_2C3628 = 0x002C3628
STUB_159EE4 = 0x00159EE4

# The revision's only `svc #0x28; bx lr` wrapper (0x001240C0).  The original
# executes the SVC directly; the candidate calls the system function instead.
STUB_TICK = 0x001240C0

CB_WORK = CB_ADDR + 0x00
CB_SECOND = CB_ADDR + 0x04

STUB_NAMES = {
    STUB_2AD630: "func_002ad630",
    STUB_159DC4: "func_00159dc4",
    STUB_2A232C: "func_002a232c",
    STUB_153268: "func_00153268",
    STUB_2C4244: "func_002c4244",
    STUB_2C3AA8: "func_002c3aa8",
    STUB_2C3A24: "func_002c3a24",
    STUB_2C3628: "func_002c3628",
    STUB_159EE4: "func_00159ee4",
    STUB_TICK: "svcGetSystemTick",
    CB_WORK: "callback_work",
    CB_SECOND: "callback_second",
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
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00155fd0" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"engine_func_00155fd0 not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        if "GetSystemTick" in rel.symbol_name:
            target = STUB_TICK
        else:
            for address, name in STUB_NAMES.items():
                if name in rel.symbol_name:
                    target = address
                    break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        condition = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, condition | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch28_a.o"
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


def pack_u64(value: int) -> bytes:
    return struct.pack("<Q", value & 0xFFFFFFFFFFFFFFFF)


def build_ctx(case: dict) -> bytes:
    page = bytearray(CTX_SIZE)
    page[0x08] = case.get("use_svc", 0) & 0xFF
    page[0x0D] = case.get("running", 1) & 0xFF
    page[0x0E] = case.get("selector", 0) & 0xFF
    page[0x30] = case.get("gate", 0) & 0xFF
    struct.pack_into("<I", page, 0x00, case.get("initial_low", 0xDEADBEEF))
    struct.pack_into("<I", page, 0x04, case.get("initial_high", 0x0BADF00D))
    struct.pack_into("<I", page, 0x28, case.get("work_cb", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x2C, case.get("work_arg", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x20, case.get("second_cb", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x24, case.get("second_arg", 0) & 0xFFFFFFFF)
    return bytes(page)


def build_data() -> bytes:
    page = bytearray(DATA_SIZE)
    # Non-zero sentinel around the profiler table so stray accesses are visible.
    for offset in range(0x200):
        page[PROFILER_TABLE - DATA_ADDR + offset] = (offset * 3 + 0x11) & 0xFF
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(CTX_ADDR, CTX_SIZE)
        self.uc.mem_map(CB_ADDR, CB_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in (STUB_2AD630, STUB_159DC4, STUB_2A232C, STUB_153268,
                        STUB_2C4244, STUB_2C3AA8, STUB_2C3A24, STUB_2C3628,
                        STUB_159EE4, STUB_TICK, CB_WORK, CB_SECOND):
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )

        self.uc.hook_add(unicorn.UC_HOOK_INTR, self._on_interrupt)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.measured_index = 0
        self.tick_index = 0
        self.iteration_count = 0

    # ----------------------------------------------------------------- helpers
    def _normalise(self, value: int) -> object:
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        if CTX_ADDR <= value < CTX_ADDR + CTX_SIZE:
            return "<ctx>"
        if CB_ADDR <= value < CB_ADDR + CB_SIZE:
            return "<callback>"
        return value

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _next_measured(self) -> int:
        values = self.case.get("measured", [0])
        value = values[min(self.measured_index, len(values) - 1)]
        self.measured_index += 1
        return value & 0xFFFFFFFFFFFFFFFF

    def _next_tick(self) -> int:
        values = self.case.get("ticks", [0])
        value = values[min(self.tick_index, len(values) - 1)]
        self.tick_index += 1
        return value & 0xFFFFFFFFFFFFFFFF

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _write_u8(self, offset: int, value: int) -> None:
        self.uc.mem_write(CTX_ADDR + offset, bytes([value & 0xFF]))

    def _after_iteration(self) -> None:
        self.iteration_count += 1
        count = self.iteration_count
        mutation = self.case.get("toggle_use_svc_after")
        if mutation == count:
            current = self.uc.mem_read(CTX_ADDR + 0x08, 1)[0]
            self._write_u8(0x08, current ^ 1)
        mutation = self.case.get("set_selector_after")
        if mutation is not None and mutation[0] == count:
            self._write_u8(0x0E, mutation[1])
        mutation = self.case.get("set_gate_after")
        if mutation is not None and mutation[0] == count:
            self._write_u8(0x30, mutation[1])

    # ------------------------------------------------------------------- stubs
    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2AD630:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR)
        elif address == STUB_159DC4:
            value = self._next_measured()
            self._log(address, self._normalise(r0), value)
            uc.mem_write(r0, pack_u64(value))
        elif address == STUB_2A232C:
            self._log(address)
        elif address == STUB_153268:
            self._log(address, r0, r1, self._normalise(r2), self._normalise(r3))
            outputs = self.case.get("counters", {}).get(r1, (0, 0))
            uc.mem_write(r2, struct.pack("<I", outputs[0] & 0xFFFFFFFF))
            uc.mem_write(r3, struct.pack("<I", outputs[1] & 0xFFFFFFFF))
        elif address in (STUB_2C4244, STUB_2C3AA8, STUB_2C3A24, STUB_2C3628):
            self._log(address, self._normalise(r0))
        elif address == STUB_159EE4:
            self._log(address)
            self._after_iteration()
            if self.iteration_count >= self.case.get("iterations", 1):
                self._write_u8(0x0D, 0)
        elif address in (CB_WORK, CB_SECOND):
            self._log(address, r0)
        elif address == STUB_TICK:
            value = self._next_tick()
            self._log(address, value)
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
            uc.reg_write(arm.UC_ARM_REG_R1, (value >> 32) & 0xFFFFFFFF)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _on_interrupt(self, uc, intno, user_data) -> None:
        # `svc #0x28` is the nn::os::GetSystemTick import; PC already points at
        # the following instruction.
        if intno != 2:
            raise RuntimeError(f"unexpected ARM interrupt {intno}")
        value = self._next_tick()
        self.call_log.append((STUB_NAMES[STUB_TICK], (value,)))
        uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R1, (value >> 32) & 0xFFFFFFFF)

    # --------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.measured_index = 0
        self.tick_index = 0
        self.iteration_count = 0

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DATA_ADDR, build_data())
        self.uc.mem_write(CTX_ADDR, build_ctx(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case.get("argument", CTX_ADDR))
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("r1", 0x11111111))
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("r2", 0x22222222))
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("r3", 0x33333333))
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = [
            (address, size)
            for address, size, _value in self.writes
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
            and not (CTX_ADDR <= address < CTX_ADDR + CTX_SIZE)
        ]

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "ctx": bytes(self.uc.mem_read(CTX_ADDR, CTX_SIZE)),
            "profiler": bytes(self.uc.mem_read(PROFILER_TABLE, 0x200)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"])
            + "\n    cand=" + repr(cand["call_log"])
        )
    if orig["ctx"] != cand["ctx"]:
        differing = [
            index for index, (a, b) in enumerate(zip(orig["ctx"], cand["ctx"])) if a != b
        ]
        problems.append(f"object page differs at offsets {differing[:16]}")
    if orig["profiler"] != cand["profiler"]:
        problems.append("profiler table page was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "use_svc": 0,
        "running": 1,
        "selector": 0,
        "gate": 0,
        "work_cb": 0,
        "work_arg": 0x12345678,
        "second_cb": 0,
        "second_arg": 0x9ABCDEF0,
        "iterations": 1,
        "counters": {0: (0, 0), 1: (0, 0)},
        "measured": [0],
        "ticks": [0],
        "argument": CTX_ADDR,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- synchronisation branch
    cases.append(base_case("no tick path"))
    cases.append(base_case("tick path", use_svc=1, measured=[0x1234],
                           ticks=[0x1000, 0x1100]))
    cases.append(base_case("tick path with non-zero initial running",
                           use_svc=1, running=0xFF, measured=[0x10],
                           ticks=[0x20, 0x30]))

    # --- signed selector boundaries; getter arm only when the byte is non-zero
    for selector in (0x00, 0x01, 0x02, 0x7F, 0x80, 0xFF, 0xFE, 0x81):
        cases.append(base_case(f"selector 0x{selector:02x}", selector=selector,
                               counters={0: (0, 0), 1: (0, 0)}))
        cases.append(base_case(f"selector 0x{selector:02x} counters non-zero",
                               selector=selector,
                               counters={0: (0, 0xFFFFFFFF), 1: (0x80000000, 0)}))

    # --- zero / non-zero getter results and the second output's irrelevance
    for first, second, label in (
        ((0x00000000, 0xFFFFFFFF), (0x00000000, 0xFFFFFFFF), "zero result"),
        ((0x00000001, 0x00000000), (0x00000000, 0x00000000), "first non-zero"),
        ((0x00000000, 0x00000000), (0x00000001, 0x00000000), "second non-zero"),
        ((0x80000000, 0x00000000), (0x00000000, 0x00000000), "sign-bit result"),
    ):
        cases.append(base_case(f"getter {label}", selector=1,
                               counters={0: first, 1: second}))

    # --- work callback: null/non-null, gate, signed selector and sb interaction
    cases.append(base_case("work callback", work_cb=CB_WORK, gate=0,
                           work_arg=0xCAFEBABE))
    cases.append(base_case("work callback gated", work_cb=CB_WORK, gate=1))
    cases.append(base_case("work callback with zero argument",
                           work_cb=CB_WORK, gate=0, work_arg=0))
    cases.append(base_case("work callback drives cleanup", work_cb=CB_WORK,
                           selector=1, counters={0: (0, 0), 1: (0, 0)}))
    cases.append(base_case("work callback without bit 0", work_cb=CB_WORK,
                           selector=2, counters={0: (1, 0), 1: (0, 0)}))
    cases.append(base_case("work callback and getter cleanup", work_cb=CB_WORK,
                           selector=1, counters={0: (0, 0), 1: (2, 0)}))

    # --- second callback: lock/unlock around it, with and without the first
    cases.append(base_case("second callback", second_cb=CB_SECOND,
                           second_arg=0x0BADCAFE))
    cases.append(base_case("second callback with work callback",
                           work_cb=CB_WORK, second_cb=CB_SECOND))
    cases.append(base_case("second callback zero argument", second_cb=CB_SECOND,
                           second_arg=0))

    # --- full cleanup combination
    cases.append(base_case("full cleanup", selector=1,
                           counters={0: (1, 0), 1: (0, 0)},
                           work_cb=CB_WORK, second_cb=CB_SECOND))

    # --- loop bounds and between-iteration re-reads
    for iterations in (1, 2, 3):
        cases.append(base_case(f"{iterations} iteration(s)", iterations=iterations))
        cases.append(base_case(f"{iterations} tick iteration(s)", use_svc=1,
                               iterations=iterations,
                               measured=[0x100, 0x200, 0x300],
                               ticks=[0x1000, 0x1100, 0x1200, 0x1300]))
    cases.append(base_case("tick flag set between iterations", use_svc=0,
                           iterations=2, toggle_use_svc_after=1,
                           measured=[0x55], ticks=[0x700, 0x701]))
    cases.append(base_case("tick flag cleared between iterations", use_svc=1,
                           iterations=2, toggle_use_svc_after=1,
                           measured=[0x66], ticks=[0x800, 0x801]))
    cases.append(base_case("selector enabled between iterations", selector=0,
                           iterations=2, set_selector_after=(1, 1),
                           counters={0: (1, 0), 1: (0, 0)}))
    cases.append(base_case("selector disabled between iterations", selector=1,
                           iterations=2, set_selector_after=(1, 0),
                           counters={0: (1, 0), 1: (0, 0)}))
    cases.append(base_case("gate set between iterations", gate=0,
                           work_cb=CB_WORK, iterations=2, set_gate_after=(1, 1)))
    cases.append(base_case("gate cleared between iterations", gate=1,
                           work_cb=CB_WORK, iterations=2, set_gate_after=(1, 0)))

    # --- 64-bit frame-duration arithmetic: carry, wrap and word boundaries
    for measured, ticks, label in (
        ([0x0000000000000001], [0xFFFFFFFFFFFFFFFF, 0x0000000000000001], "diff wrap"),
        ([0xFFFFFFFFFFFFFFFF], [0x0000000000000000, 0x0000000000000001], "sum wrap"),
        ([0xFFFFFFFF00000000], [0x00000000FFFFFFF0, 0x0000000100000000], "high word carry"),
        ([0x00000000FFFFFFFF], [0x0000000000000001, 0x0000000000000002], "low word overflow"),
        ([0x7FFFFFFFFFFFFFFF], [0x8000000000000000, 0x8000000000000001], "signed boundary"),
        ([0x8000000000000000], [0x7FFFFFFFFFFFFFFF, 0x8000000000000000], "sign-bit boundary"),
    ):
        cases.append(base_case(f"tick math {label}", use_svc=1, selector=0,
                               measured=measured, ticks=ticks))

    # --- initial loop flag and argument forwarding
    for running in (0, 1, 0x7F, 0xFF):
        cases.append(base_case(f"initial loop flag 0x{running:02x}", running=running))
    for argument in (0, CTX_ADDR, 0xFFFFFFFF):
        cases.append(base_case(f"argument 0x{argument:08x}", argument=argument))

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
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing engine_func_00155fd0 (0x00155FD0)...")
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
        ("loop_flag_initial_value",
         "*reinterpret_cast<u8*>(base + 0xd) = 1;",
         "*reinterpret_cast<u8*>(base + 0xd) = 0;"),
        ("tick_subtraction_order",
         "measured_ticks + (end_tick - start_tick)",
         "measured_ticks + (start_tick - end_tick)"),
        ("selector_bit_mask",
         "(cleanup_selector & 1) != 0",
         "cleanup_selector != 0"),
        ("callback_gate",
         "if (LoadU8(base, 0x30) == 0)",
         "if (LoadU8(base, 0x30) != 0)"),
        ("duration_store_offset",
         "StoreU32(base, 0, static_cast<u32>(frame_ticks));",
         "StoreU32(base, 4, static_cast<u32>(frame_ticks));"),
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
