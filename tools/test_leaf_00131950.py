#!/usr/bin/env python3
"""Differential test for engine_func_00131950 (0x00131950) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the engine_func_00131950 body,
resolves its direct calls to deterministic stubs placed at the original call
targets (0x00123C24 introsort stage, 0x002B3B6C ordering predicate), and runs
the pinned original (extracted/exefs/code.bin) against the candidate in separate
Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log: every 0x00123C24 (first, last, depth) triple, every
    0x002B3B6C (left, right) pair, and the vtable-selected sink call with its
    target address and (sink, state) arguments;
  * the full owner / state / vector / element / key / sink / vtable pages;
  * any emulated write outside the private stack and the sorted vector.

Coverage: empty, single-element, threshold sizes 16 and 17 and 33, the fast
memmove path at every shift distance, the unguarded downward walk at every
distance, null elements on either side of the comparison, equal keys, signed and
unsigned key boundaries, both signed threshold sides, three different indirect
call targets with distinct return values, and four introsort-stage mutations.
"""

from __future__ import annotations

import functools
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
OUT_DIR = ROOT / "build/test_leaf_00131950"

FUNC_ADDR = 0x00131950
FUNC_SIZE = 620

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the function and both direct-call stubs
OWNER_ADDR = 0x00700000
OWNER_SIZE = 0x00001000
STATE_ADDR = 0x00710000
STATE_SIZE = 0x00001000
VECTOR_ADDR = 0x00720000
VECTOR_SIZE = 0x00010000
ELEMENT_ADDR = 0x00730000
ELEMENT_SIZE = 0x00010000
KEY_ADDR = 0x00740000
KEY_SIZE = 0x00010000
SINK_ADDR = 0x00750000
SINK_SIZE = 0x00001000
VTABLE_ADDR = 0x00751000
VTABLE_SIZE = 0x00001000
SINKFN_ADDR = 0x00800000
SINKFN_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_123C24 = 0x00123C24
STUB_2B3B6C = 0x002B3B6C

STUB_NAMES = {
    STUB_123C24: "func_00123c24",
    STUB_2B3B6C: "battle_func_002b3b6c",
}

# Indirect targets: one 16-byte slot per sink implementation.
SINK_FN = [SINKFN_ADDR + 0x10 * index for index in range(3)]

# `self` layout read by the function.
OWNER_STATE_OFFSET = 0x04
OWNER_SINK_OFFSET = 0x0C

# Shared-state vector header.
STATE_BEGIN_OFFSET = 0xBC
STATE_END_OFFSET = 0xC0

# Sink vtable entry used by the tail call.
NOTIFY_SLOT_OFFSET = 0x14

# Element / key record layout seen by 0x002B3B6C.
ELEMENT_STRIDE = 0x10
ELEMENT_KEY_OFFSET = 0x08
KEY_STRIDE = 0x40
KEY_FLAGS_OFFSET = 0x00
KEY_VALUE_OFFSET = 0x4C
KEY_FLAGS_ACCEPTED = 0x40000001  # bits outside this mask invalidate the key object

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


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00131950" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_00131950 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unexpected relocation type {rel.relocation_type} "
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
        struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
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
def build_owner() -> bytes:
    page = bytearray(OWNER_SIZE)
    # Unrelated filler everywhere, so a stray store is visible.
    for offset in range(0, OWNER_SIZE, 4):
        struct.pack_into("<I", page, offset, 0xC0DE0000 | offset)
    struct.pack_into("<I", page, OWNER_STATE_OFFSET, STATE_ADDR)
    struct.pack_into("<I", page, OWNER_SINK_OFFSET, SINK_ADDR)
    return bytes(page)


def build_state(count: int) -> bytes:
    page = bytearray(STATE_SIZE)
    for offset in range(0, STATE_SIZE, 4):
        struct.pack_into("<I", page, offset, 0x5A5A0000 | offset)
    struct.pack_into("<I", page, STATE_BEGIN_OFFSET, VECTOR_ADDR)
    struct.pack_into("<I", page, STATE_END_OFFSET, VECTOR_ADDR + 4 * count)
    return bytes(page)


def build_vector(case: dict) -> bytes:
    page = bytearray(VECTOR_SIZE)
    for offset in range(0, VECTOR_SIZE, 4):
        struct.pack_into("<I", page, offset, 0xEEEE0000 | offset)
    for index, element in enumerate(case["vector"]):
        value = 0 if element is None else ELEMENT_ADDR + element * ELEMENT_STRIDE
        struct.pack_into("<I", page, 4 * index, value)
    return bytes(page)


def build_records(case: dict) -> tuple[bytes, bytes]:
    elements = bytearray(ELEMENT_SIZE)
    keys = bytearray(KEY_SIZE)
    for offset in range(0, ELEMENT_SIZE, 4):
        struct.pack_into("<I", elements, offset, 0xE1E10000 | offset)
    for offset in range(0, KEY_SIZE, 4):
        struct.pack_into("<I", keys, offset, 0x4C4C0000 | offset)
    for index, (key_value, flags) in enumerate(zip(case["keys"], case["key_flags"])):
        base = index * ELEMENT_STRIDE
        struct.pack_into("<I", elements, base + ELEMENT_KEY_OFFSET,
                         KEY_ADDR + index * KEY_STRIDE)
        kbase = index * KEY_STRIDE
        struct.pack_into("<I", keys, kbase + KEY_FLAGS_OFFSET, flags & 0xFFFFFFFF)
        struct.pack_into("<I", keys, kbase + KEY_VALUE_OFFSET,
                         key_value & 0xFFFFFFFF)
    return bytes(elements), bytes(keys)


def build_sink(case: dict) -> tuple[bytes, bytes]:
    sink = bytearray(SINK_SIZE)
    for offset in range(0, SINK_SIZE, 4):
        struct.pack_into("<I", sink, offset, 0x51A10000 | offset)
    struct.pack_into("<I", sink, 0, VTABLE_ADDR)

    vtable = bytearray(VTABLE_SIZE)
    for offset in range(0, VTABLE_SIZE, 4):
        struct.pack_into("<I", vtable, offset, 0x7AB10000 | offset)
    struct.pack_into("<I", vtable, NOTIFY_SLOT_OFFSET,
                     SINK_FN[case.get("sink_target", 0)])
    return bytes(sink), bytes(vtable)


def read_u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (OWNER_ADDR, OWNER_SIZE),
            (STATE_ADDR, STATE_SIZE),
            (VECTOR_ADDR, VECTOR_SIZE),
            (ELEMENT_ADDR, ELEMENT_SIZE),
            (KEY_ADDR, KEY_SIZE),
            (SINK_ADDR, SINK_SIZE),
            (VTABLE_ADDR, VTABLE_SIZE),
            (SINKFN_ADDR, SINKFN_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for address in STUB_NAMES:
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_direct_stub,
                             begin=address, end=address)
        for address in SINK_FN:
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_sink,
                             begin=address, end=address)

        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _log(self, name: str, *args) -> None:
        st = STACK_ADDR
        normalised = tuple(
            "<stack>" if isinstance(arg, int) and st <= arg < st + STACK_SIZE
            else arg
            for arg in args
        )
        self.call_log.append((name, normalised))

    def _on_direct_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)

        if address == STUB_123C24:
            self._log("func_00123c24", r0, r1, r2)
            self._mutate_vector(r0, r1)
        elif address == STUB_2B3B6C:
            # First argument is the stateless comparator object.
            self._log("battle_func_002b3b6c", r0, r1, r2)
            uc.reg_write(arm.UC_ARM_REG_R0, self._compare(r1, r2))
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _on_sink(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("sink", address, r0, r1))
        uc.reg_write(arm.UC_ARM_REG_R0,
                     self.case.get("sink_return", 0) & 0xFFFFFFFF)

    def _mutate_vector(self, first: int, last: int) -> None:
        """Deterministic stand-in for the introsort stage (0x00123C24).

        0x00123C24 leaves the range partitioned, which guarantees that the
        element left at the front is not ordered after any later element.  The
        unguarded insertion stage that follows depends on that invariant (it
        walks down without a lower bound), so the stand-in re-establishes it for
        ranges above the 16-element threshold.
        """
        mode = self.case.get("introsort", "keep")
        count = (last - first) // 4
        if count == 0:
            return
        words = [read_u32(self.uc, first + 4 * i) for i in range(count)]
        if mode == "reverse":
            words.reverse()
        elif mode == "rotate":
            words = words[1:] + words[:1]
        elif mode == "swap_ends":
            words[0], words[-1] = words[-1], words[0]
        elif mode == "merge_halves":
            half = count // 2
            words = words[half:] + words[:half]
        elif mode == "sorted":
            words.sort(key=functools.cmp_to_key(self._order))
        elif mode != "keep":  # pragma: no cover - guarded by case construction
            raise AssertionError(f"unknown introsort mode {mode!r}")
        if count > 16:
            lowest = 0
            for index in range(1, count):
                if self._order(words[index], words[lowest]) < 0:
                    lowest = index
            words[0], words[lowest] = words[lowest], words[0]
        self.uc.mem_write(first, b"".join(struct.pack("<I", w) for w in words))

    def _order(self, left: int, right: int) -> int:
        if self._compare(left, right):
            return -1
        if self._compare(right, left):
            return 1
        return 0

    def _compare(self, left: int, right: int) -> int:
        """Recovered ordering predicate of 0x002B3B6C.

        `right == null` reports "ordered"; a null `left` never is.  Both key
        objects must pass the 0x40000001 mask test, otherwise the original
        would dereference address 0x4C (no fixture exercises that).
        """
        if right == 0:
            return 1
        if left == 0:
            return 0
        left_key = read_u32(self.uc, left + ELEMENT_KEY_OFFSET)
        right_key = read_u32(self.uc, right + ELEMENT_KEY_OFFSET)
        if left_key != 0 and read_u32(self.uc, left_key) & ~KEY_FLAGS_ACCEPTED:
            left_key = 0
        if right_key != 0 and read_u32(self.uc, right_key) & ~KEY_FLAGS_ACCEPTED:
            right_key = 0
        if left_key == 0 or right_key == 0:
            raise AssertionError(
                "fixture triggered the comparator's null key-object dereference"
            )
        left_value = read_u32(self.uc, left_key + KEY_VALUE_OFFSET)
        right_value = read_u32(self.uc, right_key + KEY_VALUE_OFFSET)
        return 1 if left_value < right_value else 0

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        count = len(case["vector"])
        elements, keys = build_records(case)
        sink, vtable = build_sink(case)

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(OWNER_ADDR, build_owner())
        self.uc.mem_write(STATE_ADDR, build_state(count))
        self.uc.mem_write(VECTOR_ADDR, build_vector(case))
        self.uc.mem_write(ELEMENT_ADDR, elements)
        self.uc.mem_write(KEY_ADDR, keys)
        self.uc.mem_write(SINK_ADDR, sink)
        self.uc.mem_write(VTABLE_ADDR, vtable)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OWNER_ADDR)
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
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_vector = VECTOR_ADDR <= address < VECTOR_ADDR + VECTOR_SIZE
            if not (in_stack or in_vector):
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
                "owner": bytes(self.uc.mem_read(OWNER_ADDR, OWNER_SIZE)),
                "state": bytes(self.uc.mem_read(STATE_ADDR, STATE_SIZE)),
                "vector": bytes(self.uc.mem_read(VECTOR_ADDR, VECTOR_SIZE)),
                "elements": bytes(self.uc.mem_read(ELEMENT_ADDR, ELEMENT_SIZE)),
                "keys": bytes(self.uc.mem_read(KEY_ADDR, KEY_SIZE)),
                "sink": bytes(self.uc.mem_read(SINK_ADDR, SINK_SIZE)),
                "vtable": bytes(self.uc.mem_read(VTABLE_ADDR, VTABLE_SIZE)),
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
            "call_log:\n    orig=" + repr(orig["call_log"]) +
            "\n    cand=" + repr(cand["call_log"])
        )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig=" + repr(orig["unexpected_writes"]) +
            " cand=" + repr(cand["unexpected_writes"])
        )
    return problems


def make_case(name: str, keys: list[int], vector: list[int | None],
              **overrides) -> dict:
    case = {
        "name": name,
        "keys": keys,
        "key_flags": [KEY_FLAGS_ACCEPTED] * len(keys),
        "vector": vector,
        "introsort": "keep",
        "sink_target": 0,
        "sink_return": 0,
    }
    case.update(overrides)
    return case


def ascending(count: int, start: int = 0) -> list[int]:
    return [start + index for index in range(count)]


def descending(count: int, start: int = 0) -> list[int]:
    return [start + count - 1 - index for index in range(count)]


def front_min_descending(count: int) -> list[int]:
    """Descending tail behind the global minimum, as introsort may leave it."""
    return [0] + [count - 1 - index for index in range(count - 1)]


def front_min_mixed(count: int) -> list[int]:
    values = [1 + (index * 7) % max(1, count - 1) for index in range(count)]
    return [0] + values[1:]


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- vector size boundaries and the empty / single-element exits
    cases.append(make_case("empty vector", [], []))
    cases.append(make_case("empty vector, sink returns -1", [], [],
                           sink_return=0xFFFFFFFF))
    cases.append(make_case("single element", [7], [0]))
    cases.append(make_case("single element, introsort reverse", [7], [0],
                           introsort="reverse"))

    # --- simple path (count <= 16): fast memmove branch and unguarded insert
    cases.append(make_case("two ascending", [1, 2], [0, 1]))
    cases.append(make_case("two descending", [2, 1], [0, 1]))
    cases.append(make_case("two equal", [5, 5], [0, 1]))
    cases.append(make_case("three descending", [3, 2, 1], [0, 1, 2]))
    cases.append(make_case("three ascending", [1, 2, 3], [0, 1, 2]))
    cases.append(make_case("five mixed", [3, 1, 5, 2, 4], [0, 1, 2, 3, 4]))
    cases.append(make_case("eight reversed", descending(8), list(range(8))))
    cases.append(make_case("eight ascending", ascending(8), list(range(8))))
    cases.append(make_case("sixteen ascending", ascending(16), list(range(16))))
    cases.append(make_case("sixteen descending", descending(16), list(range(16))))
    cases.append(make_case("sixteen mixed", [8, 3, 15, 1, 12, 6, 14, 2,
                                             10, 5, 13, 0, 11, 7, 9, 4],
                           list(range(16))))

    # --- threshold boundary: 17 elements take the two-phase path
    cases.append(make_case("seventeen ascending", ascending(17), list(range(17))))
    cases.append(make_case("seventeen front-min descending",
                           front_min_descending(17), list(range(17))))
    cases.append(make_case("seventeen front-min mixed",
                           front_min_mixed(17), list(range(17))))
    cases.append(make_case("seventeen descending via introsort stub",
                           descending(17), list(range(17)), introsort="keep"))

    # --- longer vectors, exercising the introsort-stage interaction
    for mode in ("keep", "reverse", "rotate", "swap_ends", "merge_halves",
                 "sorted"):
        cases.append(make_case(f"thirty-three {mode}", descending(33, start=100),
                               list(range(33)), introsort=mode))
    cases.append(make_case("sixty-four ascending", ascending(64),
                           list(range(64)), introsort="reverse"))
    cases.append(make_case("sixty-four front-min descending",
                           front_min_descending(64), list(range(64)),
                           introsort="keep"))

    # --- null elements exercise both comparator null arms
    cases.append(make_case("null leading element", [2, 1], [None, 0, 1]))
    cases.append(make_case("null trailing element", [1, 2], [0, 1, None]))
    cases.append(make_case("nulls interleaved", [4, 3, 2, 1],
                           [None, 0, None, 1, None, 2, None, 3]))
    cases.append(make_case("all null", [0], [None, None, None]))
    cases.append(make_case("null with reverse stage", [3, 2, 1],
                           [None, 0, 1, None, 2], introsort="reverse"))
    cases.append(make_case("null head, long vector", descending(20, start=1),
                           [None] + list(range(20)), introsort="reverse"))

    # --- key value boundaries: 0, 1, INT32_MIN, UINT32_MAX, equal keys
    for values in (
        [0, 1],
        [1, 0],
        [0x80000000, 0x7FFFFFFF],
        [0xFFFFFFFF, 0],
        [0x7FFFFFFF, 0x80000000],
        [0xFFFFFFFF, 0xFFFFFFFE],
    ):
        cases.append(make_case(
            f"keys {values[0]:#010x}/{values[1]:#010x}", values, [0, 1]))
    cases.append(make_case("four equal keys", [9, 9, 9, 9], [0, 1, 2, 3]))
    cases.append(make_case("duplicate heavy", [2, 2, 1, 1, 2, 1],
                           list(range(6))))
    cases.append(make_case("unsigned key order", [0xFFFFFFFF, 1, 0x80000000, 0],
                           [0, 1, 2, 3]))
    cases.append(make_case("unsigned key order, long vector",
                           [0xFFFFFFFF] + [0x80000000 + index
                                           for index in range(18)],
                           list(range(19))))

    # --- duplicate elements: the same object pointer may appear twice
    cases.append(make_case("duplicate element pointers", [3, 2, 1],
                           [0, 0, 1, 2]))
    cases.append(make_case("all same element", [5], [0, 0, 0, 0]))

    # --- key-object flag words that still pass the 0x40000001 mask
    cases.append(make_case("key flags zero", [2, 1], [0, 1],
                           key_flags=[0, 0]))
    cases.append(make_case("key flags bit 30", [2, 1], [0, 1],
                           key_flags=[0x40000000, 0x00000001]))
    cases.append(make_case("key flags mixed", descending(20), list(range(20)),
                           key_flags=[0x40000001 if i % 2 else 0
                                      for i in range(20)]))

    # --- indirect call: every sink target and return value
    for target in range(3):
        cases.append(make_case(f"sink target {target}", [2, 1], [0, 1],
                               sink_target=target,
                               sink_return=0x1000 + target))
    cases.append(make_case("sink returns 0xFFFFFFFF", [], [],
                           sink_target=2, sink_return=0xFFFFFFFF))
    cases.append(make_case("sink returns 0 with sorted vector", ascending(18),
                           list(range(18)), sink_target=1, sink_return=0))

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
    print("Testing engine_func_00131950 (0x00131950)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("threshold", "constexpr s32 kInsertionThreshold = 16;",
         "constexpr s32 kInsertionThreshold = 15;"),
        ("comparator_result",
         "return battle_func_002b3b6c(&comparator, left, right) != 0;",
         "return battle_func_002b3b6c(&comparator, left, right) == 0;"),
        ("shift_direction", "        dst[0] = dst[-1];",
         "        dst[0] = dst[0];"),
        ("introsort_depth", "        func_00123c24(begin, end, count);",
         "        func_00123c24(begin, end, count + 1);"),
        ("notify_argument_order", "    return notify(sink, current_state);",
         "    return notify(static_cast<void*>(current_state),\n"
         "                  static_cast<u8*>(sink));"),
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
