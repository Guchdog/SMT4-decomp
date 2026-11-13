#!/usr/bin/env python3
"""Differential test for engine_func_0011b6a8 (0x0011b6a8) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the engine_func_0011b6a8
candidate body, resolves its five direct-call relocations to deterministic
stubs at the pinned addresses, and runs the pinned original
(extracted/exefs/code.bin, 400 B including its literal pool) against the
candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log (helper name plus every register argument), including
    the 500,000 ns sleep word and every svcGetSystemTick value;
  * the full 4 KiB object page and the canary page (final observable memory);
  * any emulated write outside the object page and the private stack.

Coverage: every entry-state class (6 versus every non-6 value), the immediate
state-3 / state-7 / state-1 poll results and the sleep loop with one to four
iterations, arbitrary poll states, tick values across the 32-bit, sign and
scale boundaries, 64-bit baselines below/equal/above the scaled tick
(borrowing delta), and counter carry/wrap in both words of both 64-bit
counters.  Negative controls mutate the tick magic, the microsecond magic,
the entry-state test, the abort states, the sleep constant and one counter
store offset; each mutant must be detected.
"""

from __future__ import annotations

import struct
import random
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
OUT_DIR = ROOT / "build/test_leaf_0011b6a8"

FUNC_ADDR = 0x0011B6A8
FUNC_SIZE = 400

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x300000
OBJ_ADDR = 0x00710000
OBJ_SIZE = 0x00001000
CANARY_ADDR = 0x00720000
CANARY_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets; stubs are placed at the same addresses so both
# the original bytes and the relocated candidate resolve to them.
STUB_2C3AA8 = 0x002C3AA8
STUB_2C3A24 = 0x002C3A24
STUB_2C4244 = 0x002C4244
STUB_2BB490 = 0x002BB490
STUB_TICK = 0x001240C0

STUB_NAMES = {
    STUB_2C3AA8: "engine_lock_enter_002c3aa8",
    STUB_2C3A24: "engine_lock_leave_002c3a24",
    STUB_2C4244: "nn_sdk_release_002c4244",
    STUB_2BB490: "camp_sleep_002bb490",
    STUB_TICK: "svcGetSystemTick",
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

STATE_OFFSET = 0x0C
COUNTER_A_OFFSET = 0x138
COUNTER_B_OFFSET = 0x140
BASELINE_OFFSET = 0x150


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0011b6a8" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_0011b6a8 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    call_targets = {
        "002c3aa8": STUB_2C3AA8,
        "002c3a24": STUB_2C3A24,
        "002c4244": STUB_2C4244,
        "002bb490": STUB_2BB490,
    }
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        if "GetSystemTick" in rel.symbol_name:
            target = STUB_TICK
        else:
            target = None
            for suffix, address in call_targets.items():
                if suffix in rel.symbol_name:
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
    obj_file = OUT_DIR / "leaf_batch34_c.o"
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


def build_object(case: dict) -> bytes:
    # 0xA5 fill makes any stray write inside the page visible in the page diff.
    page = bytearray([0xA5] * OBJ_SIZE)
    struct.pack_into("<I", page, STATE_OFFSET,
                     case.get("entry_state", 6) & 0xFFFFFFFF)
    struct.pack_into("<Q", page, COUNTER_A_OFFSET,
                     case.get("counter_a", 0) & 0xFFFFFFFFFFFFFFFF)
    struct.pack_into("<Q", page, COUNTER_B_OFFSET,
                     case.get("counter_b", 0) & 0xFFFFFFFFFFFFFFFF)
    struct.pack_into("<Q", page, BASELINE_OFFSET,
                     case.get("baseline", 0) & 0xFFFFFFFFFFFFFFFF)
    return bytes(page)


def build_canary() -> bytes:
    return bytes(((index * 7 + 0x31) & 0xFF) for index in range(CANARY_SIZE))


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(OBJ_ADDR, OBJ_SIZE)
        self.uc.mem_map(CANARY_ADDR, CANARY_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in (STUB_2C3AA8, STUB_2C3A24, STUB_2C4244, STUB_2BB490):
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )

        # The revision's only `svc #0x28; bx lr` wrapper.  The original executes
        # the SVC inline; the candidate calls the system function instead.
        self.uc.mem_write(
            STUB_TICK,
            struct.pack("<III", 0xE1A00000, 0xEF000028, 0xE12FFF1E),
        )

        self.uc.hook_add(unicorn.UC_HOOK_INTR, self._on_interrupt)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.tick_index = 0
        self.sleep_index = 0
        self.overrun = False

    # ----------------------------------------------------------------- helpers
    @staticmethod
    def _normalise(value: int):
        if OBJ_ADDR <= value < OBJ_ADDR + OBJ_SIZE:
            return "<object>"
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _set_state(self, value: int) -> None:
        self.uc.mem_write(
            OBJ_ADDR + STATE_OFFSET, struct.pack("<I", value & 0xFFFFFFFF)
        )

    def _next_tick(self) -> int:
        values = self.case.get("ticks", [0])
        value = values[min(self.tick_index, len(values) - 1)]
        self.tick_index += 1
        return value & 0xFFFFFFFFFFFFFFFF

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    # ------------------------------------------------------------------- stubs
    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        if address == STUB_2C3AA8:
            self._log(address, self._normalise(r0))
        elif address == STUB_2C3A24:
            self._log(address, self._normalise(r0))
        elif address == STUB_2C4244:
            self._log(address, self._normalise(r0))
            if self.case.get("post_release_state") is not None:
                self._set_state(self.case["post_release_state"])
        elif address == STUB_2BB490:
            self._log(address, r0, r1)
            self.sleep_index += 1
            states = self.case.get("sleep_states", ())
            if states:
                index = min(self.sleep_index - 1, len(states) - 1)
                self._set_state(states[index])
            if self.sleep_index > self.case.get("max_sleeps", len(states) + 2):
                # Safety valve: a case that never reaches a terminal state would
                # otherwise spin forever.  Such a run must not match anything.
                self.overrun = True
                self._set_state(3)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _on_interrupt(self, uc, intno, user_data) -> None:
        # `svc #0x28` is nn::os::GetSystemTick; PC already points at the
        # following instruction.  The original executes it inline, the
        # candidate reaches the identical SVC through the 0x001240C0 wrapper.
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
        self.tick_index = 0
        self.sleep_index = 0
        self.overrun = False

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(OBJ_ADDR, build_object(case))
        self.uc.mem_write(CANARY_ADDR, build_canary())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
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
            if not (OBJ_ADDR <= address < OBJ_ADDR + OBJ_SIZE)
            and not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        ]

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "object": bytes(self.uc.mem_read(OBJ_ADDR, OBJ_SIZE)),
            "canary": bytes(self.uc.mem_read(CANARY_ADDR, CANARY_SIZE)),
            "unexpected_writes": unexpected_writes,
            "overrun": self.overrun,
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
    if orig["object"] != cand["object"]:
        differing = [
            index
            for index, (left, right) in enumerate(
                zip(orig["object"], cand["object"])
            )
            if left != right
        ]
        problems.append(f"object page differs at offsets {differing[:16]}")
    if orig["canary"] != cand["canary"]:
        problems.append("canary page was modified")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    if orig["overrun"] or cand["overrun"]:
        problems.append(f"sleep-loop overrun orig={orig['overrun']} "
                        f"cand={cand['overrun']}")
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "entry_state": 6,
        "post_release_state": 3,
        "sleep_states": (),
        "ticks": [0],
        "baseline": 0,
        "counter_a": 0,
        "counter_b": 0,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- entry-state gate: any value other than 6 returns 0 with no effects
    for state in (0x00000000, 0x00000001, 0x00000002, 0x00000003,
                  0x00000004, 0x00000005, 0x00000007, 0x00000008,
                  0x7FFFFFFF, 0x80000000, 0xFFFFFFFE, 0xFFFFFFFF):
        cases.append(base_case(f"entry state 0x{state:08x}", entry_state=state))

    # --- immediate poll results after the state-5 transition
    cases.append(base_case("state 3 immediately", post_release_state=3))
    cases.append(base_case("state 7 aborts", post_release_state=7))
    cases.append(base_case("state 1 aborts", post_release_state=1))

    # --- sleep loop: 1..4 iterations before a terminal state (post_release_state
    # is cleared so the poll sees the state the sleep stub publishes)
    cases.append(base_case("one sleep then 3", post_release_state=None,
                           sleep_states=(3,)))
    cases.append(base_case("two sleeps then 3", post_release_state=None,
                           sleep_states=(5, 3)))
    cases.append(base_case("three sleeps then 3", post_release_state=None,
                           sleep_states=(0, 2, 3)))
    cases.append(base_case("four sleeps then 3", post_release_state=None,
                           sleep_states=(0xFFFFFFFF, 0x80000000, 6, 3),
                           max_sleeps=5))
    cases.append(base_case("one sleep then 7", post_release_state=None,
                           sleep_states=(7,)))
    cases.append(base_case("two sleeps then 1", post_release_state=None,
                           sleep_states=(5, 1)))
    cases.append(base_case("three sleeps then 7", post_release_state=None,
                           sleep_states=(2, 4, 7)))
    cases.append(base_case("sleep then 1", post_release_state=None,
                           sleep_states=(1,)))
    cases.append(base_case("state 0 then 3", post_release_state=None,
                           sleep_states=(0, 3)))
    cases.append(base_case("state 6 poll then 3", post_release_state=None,
                           sleep_states=(6, 3)))

    # --- tick values across the scale/sign boundaries (one tick path per run)
    for tick in (0x0000000000000000, 0x0000000000000001, 0x00000000000003E7,
                 0x00000000000003E8, 0x00000000000003E9, 0x000000000007A120,
                 0x00000000FFFFFFFF, 0x0000000100000000, 0x000000007FFFFFFF,
                 0x0000000080000000, 0x0000000123456789, 0x00000003BAD34AEE,
                 0x0000001000000000, 0x00123456789ABCDE, 0x7FFFFFFFFFFFFFFF,
                 0x8000000000000000, 0xFFFFFFFFFFFFFFFF, 0x123456789ABCDEF0,
                 0xEDCBA9876543210F, 0x0000000FFFFFFFFF):
        cases.append(base_case(f"tick 0x{tick:016x}", ticks=[tick]))

    # --- baseline versus scaled tick: below (positive delta), equal, above
    for tick, baseline in (
        (0x0000001000000000, 0x0000000000000000),
        (0x0000001000000000, 0x0000000000000001),
        (0x0000001000000000, 0x00000000000F4240),
        (0x0000001000000000, 0x0000000FFFFFFFF0),
        (0x0000000000000000, 0x0000000000000001),
        (0x0000000000000000, 0xFFFFFFFFFFFFFFFF),
        (0xFFFFFFFFFFFFFFFF, 0x0000000000000000),
        (0xFFFFFFFFFFFFFFFF, 0x7FFFFFFFFFFFFFFF),
        (0x7FFFFFFFFFFFFFFF, 0x8000000000000000),
        (0x8000000000000000, 0x7FFFFFFFFFFFFFFF),
        (0x123456789ABCDEF0, 0x0123456789ABCDEF),
        (0x000000000007A120, 0x000000000007A120),
    ):
        cases.append(
            base_case(f"tick 0x{tick:016x} baseline 0x{baseline:016x}",
                      ticks=[tick], baseline=baseline)
        )

    # --- counter carry/wrap in both 64-bit words of both counters
    for counter_a, counter_b in (
        (0x0000000000000000, 0x0000000000000000),
        (0x00000000FFFFFFFF, 0x00000000FFFFFFFF),
        (0x00000000FFFFFFFE, 0x00000000FFFFFFFE),
        (0x0000000100000000, 0x0000000100000000),
        (0xFFFFFFFFFFFFFFFF, 0xFFFFFFFFFFFFFFFF),
        (0xFFFFFFFF00000000, 0xFFFFFFFF00000000),
        (0x00000000FFFFFFFF, 0xFFFFFFFF00000000),
        (0xFFFFFFFF00000000, 0x00000000FFFFFFFF),
        (0x7FFFFFFFFFFFFFFF, 0x8000000000000000),
        (0x8000000000000000, 0x7FFFFFFFFFFFFFFF),
    ):
        cases.append(
            base_case(f"counters a=0x{counter_a:016x} b=0x{counter_b:016x}",
                      ticks=[0x0000001000000000],
                      baseline=0x0000000000000100,
                      counter_a=counter_a, counter_b=counter_b)
        )

    # --- the abort path must not touch the counters even when they are sentinels
    cases.append(
        base_case("abort leaves counters", post_release_state=7,
                  counter_a=0x0123456789ABCDEF, counter_b=0xFEDCBA9876543210)
    )
    cases.append(
        base_case("sleep-only path leaves counters", post_release_state=None,
                  sleep_states=(1,),
                  counter_a=0x0123456789ABCDEF, counter_b=0xFEDCBA9876543210)
    )

    # --- caller-clobbered registers are not part of the contract but are logged
    cases.append(base_case("arbitrary r1-r3", r1=0xDEADBEEF, r2=0x0BADF00D,
                           r3=0x13579BDF, ticks=[0x99999999]))

    # --- fixed-seed sweep over the independent inputs
    rng = random.Random(0x11B6A8)
    terminal = (1, 3, 7)
    for index in range(24):
        entry_state = 6 if index % 4 else rng.choice(
            (0, 1, 2, 3, 5, 7, 8, 0xFFFFFFFF))
        if entry_state != 6:
            cases.append(base_case(f"sweep {index:02d} entry 0x{entry_state:08x}",
                                   entry_state=entry_state))
            continue
        sleeps = index % 4
        sleep_states = tuple(
            rng.choice((0, 2, 4, 5, 6, 0x80000000, 0xFFFFFFFF))
            for _ in range(sleeps)
        ) + (rng.choice(terminal),)
        cases.append(
            base_case(
                f"sweep {index:02d} sleeps={sleeps}",
                post_release_state=None,
                sleep_states=sleep_states,
                ticks=[rng.getrandbits(64)],
                baseline=rng.getrandbits(64),
                counter_a=rng.getrandbits(64),
                counter_b=rng.getrandbits(64),
            )
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
    print("Testing engine_func_0011b6a8 (0x0011b6a8)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          f"(relocations resolved).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("tick_magic", "constexpr u64 kTickNanosecondsMagic = 0x3BAD34AEEu;",
         "constexpr u64 kTickNanosecondsMagic = 0x3BAD34AEFu;"),
        ("microsecond_magic",
         "constexpr u64 kMicrosecondsMagic = 0x20C49BA5E353F7CFu;",
         "constexpr u64 kMicrosecondsMagic = 0x20C49BA6E353F7CFu;"),
        ("entry_state_gate", "if (LoadU32(object, kStateOffset) != 6) {",
         "if (LoadU32(object, kStateOffset) != 5) {"),
        ("abort_states", "if (state == 7 || state == 1) {",
         "if (state == 7 || state == 2) {"),
        ("sleep_constant", "constexpr u64 kWaitNanoseconds = 0x0007A120u;",
         "constexpr u64 kWaitNanoseconds = 0x0007A121u;"),
        ("counter_store_offset",
         "StoreU32(object, kCounterAOffset + 4, counter_a_high_sum);",
         "StoreU32(object, kCounterAOffset + 8, counter_a_high_sum);"),
        ("delta_subtract", "const u64 elapsed = now - baseline;",
         "const u64 elapsed = now + baseline;"),
        ("sign_adjustment", "if (scaled < 0) {\n        ++microseconds;\n    }",
         "if (scaled < 1) {\n        ++microseconds;\n    }"),
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
