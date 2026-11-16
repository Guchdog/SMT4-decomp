#!/usr/bin/env python3
"""Differential test for engine_func_00140318 (0x00140318) using Unicorn ARM.

Compiles src/engine/leaf_batch28_a.cpp, extracts the engine_func_00140318 body,
resolves its seven direct helpers to deterministic stubs placed at the pinned
call-target addresses, and runs the pinned original (extracted/exefs/code.bin)
against the candidate in separate Unicorn machines with identical fixtures.

Compared per case:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log, including every register argument, the architected
    stack argument of 0x002AC8E4 and both stack words of 0x001404AC;
  * the indirect vtable slot reached from [self->vtable + 0x10], with receiver
    and key;
  * the five record name bytes observed at the 0x002AC614 call (the original
    clears them at 0x001403D0..0x001403E4), the record index word and the
    record words forwarded to 0x001404AC;
  * the full DATA fixture page and any write outside the private stack.

Coverage: every flag form (0, bit 1 and bit 3 alone, both, all ones, and each
bit cleared), pre-pass failure and success with zero/non-zero helpers, null and
non-null vtable lookups, empty/one/three/four element lists, a filter failure on
each loop iteration, the 0xFFFFFFFF alternate-selector sentinel and explicit
overrides, signed selector boundaries, null and non-null keys, record lookup /
fill / forward failures, and 32-bit boundary values forwarded to 0x001404AC.
Negative controls mutate the pre-pass flag, the vtable slot offset, the
alternate-selector sentinel, the pre-pass mode argument, and the forwarded
record argument order; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_00140318"

FUNC_ADDR = 0x00140318
FUNC_SIZE = 404

# ---------------------------------------------------------------------------
# Emulated address space
# ---------------------------------------------------------------------------
CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers 0x140318 .. 0x2AC8E4 and the vtable stubs
DATA_ADDR = 0x00400000
DATA_SIZE = 0x00040000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Fixture placement inside DATA.
OBJECT = 0x00400000       # +0x00 vtable, +0x04 context
VTABLE = 0x00400100
CONTEXT = 0x00400200
STREAM = 0x00400300
KEY = 0x00400400
LIST = 0x00420000         # +0x00 count, +0x04 elements
LIST_ELEMENTS = LIST + 4

# Direct-call stubs at the original targets (both images resolve to them).
STUB_KEY = 0x002ACA0C        # engine_func_002aca0c(void* context)
STUB_FILTER = 0x002AC8E4     # engine_func_002ac8e4(self,key,stream,extra,mode)
STUB_RECORD = 0x0014D390     # engine_func_0014d390(context,selector,record)
STUB_CURSOR = 0x002AC6D0     # engine_func_002ac6d0(cursor,key)
STUB_FILL = 0x002AC614       # engine_func_002ac614(cursor,record,index,mode)
STUB_FORWARD = 0x001404AC    # engine_func_001404ac(self,first,second,stream,flags,extra)
STUB_LIST = 0x001522DC       # func_001522dc(context,selector)

# Indirect vtable targets.
STUB_VTABLE_10 = 0x002F0000
STUB_VTABLE_14 = 0x002F0010

STUB_NAMES = {
    STUB_KEY: "engine_func_002aca0c",
    STUB_FILTER: "engine_func_002ac8e4",
    STUB_RECORD: "engine_func_0014d390",
    STUB_CURSOR: "engine_func_002ac6d0",
    STUB_FILL: "engine_func_002ac614",
    STUB_FORWARD: "engine_func_001404ac",
    STUB_LIST: "func_001522dc",
    STUB_VTABLE_10: "vtable_10",
    STUB_VTABLE_14: "vtable_14",
}

# Call relocation symbol -> stub address.
CALL_STUBS = {
    "engine_func_002aca0c": STUB_KEY,
    "engine_func_002ac8e4": STUB_FILTER,
    "engine_func_0014d390": STUB_RECORD,
    "engine_func_002ac6d0": STUB_CURSOR,
    "engine_func_002ac614": STUB_FILL,
    "engine_func_001404ac": STUB_FORWARD,
    "func_001522dc": STUB_LIST,
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


def compile_candidate(src: Path, obj: Path) -> bytes:
    obj.parent.mkdir(parents=True, exist_ok=True)
    result = compile_tu_armv6k(src, obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"compilation failed for {src}:\n{result.stderr}")

    funcs = extract_elf_functions_detailed(obj)
    if "engine_func_00140318" not in funcs:
        raise RuntimeError(
            f"engine_func_00140318 not found in {obj}: {sorted(funcs)}"
        )
    raw, relocs = funcs["engine_func_00140318"]
    code = bytearray(raw)
    seen = set()
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(f"unsupported relocation: {rel}")
        target = CALL_STUBS.get(rel.symbol_name)
        if target is None:
            raise RuntimeError(f"unexpected call relocation: {rel.symbol_name}")
        seen.add(rel.symbol_name)
        instruction = struct.unpack_from("<I", code, rel.offset)[0]
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        struct.pack_into(
            "<I",
            code,
            rel.offset,
            (instruction & 0xFF000000) | (displacement & 0x00FFFFFF),
        )
    missing = set(CALL_STUBS) - seen
    if missing:
        raise RuntimeError(f"missing call relocations: {sorted(missing)}")
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    return compile_candidate(SOURCE, OUT_DIR / "leaf_batch28_a.o")


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant = OUT_DIR / f"mutant_{name}.cpp"
    mutant.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant, OUT_DIR / f"mutant_{name}.o")


def normalise(value: int):
    if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
        return "<stack>"
    return value


def read_u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


def write_u32(uc, address: int, value: int) -> None:
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


class Machine:
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
            unicorn.UC_HOOK_CODE, self._on_stub,
            begin=min(STUB_NAMES), end=max(STUB_NAMES),
        )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.outside_stack_writes: list = []
        self.case: dict = {}
        self.filter_index = 0
        self.key_index = 0

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], tuple(args) + self._stack_words(self.STACK_ARGS[address]))
        )

    STACK_ARGS = {
        STUB_KEY: 0,
        STUB_FILTER: 1,     # mode: 0 pre-pass / 1 loop
        STUB_RECORD: 0,
        STUB_CURSOR: 0,
        STUB_FILL: 0,
        STUB_FORWARD: 2,    # flags, extra
        STUB_LIST: 0,
        STUB_VTABLE_10: 0,
        STUB_VTABLE_14: 0,
    }

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE):
            self.outside_stack_writes.append((address, size))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        case = self.case

        if address == STUB_KEY:
            self._log(address, r0)
            updates = case.get("key_count_updates", {})
            if self.key_index in updates:
                write_u32(uc, LIST, updates[self.key_index])
            self.key_index += 1
            uc.reg_write(arm.UC_ARM_REG_R0, case["key"])

        elif address == STUB_FILTER:
            value = filter_result(case, self.filter_index)
            self.filter_index += 1
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, value)

        elif address == STUB_RECORD:
            self._log(address, r0, r1, normalise(r2))
            record = r2
            if case["record_ok"]:
                name = case["lookup_name"]
                uc.mem_write(
                    record,
                    struct.pack("<II", case["lookup_id"], case["lookup_value"]),
                )
                uc.mem_write(record + 8, bytes(name))
            uc.reg_write(arm.UC_ARM_REG_R0, 1 if case["record_ok"] else 0)

        elif address == STUB_CURSOR:
            self._log(address, normalise(r0), normalise(r1))
            cursor = r0
            uc.mem_write(
                cursor,
                struct.pack("<II", case["cursor_words"][0], case["cursor_words"][1]),
            )

        elif address == STUB_FILL:
            record = r1
            before = bytes(uc.mem_read(record, 0x18))
            self.call_log.append(
                (
                    STUB_NAMES[address],
                    (normalise(r0), normalise(record), r2, r3)
                    + struct.unpack("<II", before[0:8])
                    + tuple(before[8:13]),
                )
            )
            if case["fill_ok"]:
                uc.mem_write(
                    record,
                    struct.pack(
                        "<II",
                        case["filled_id"],
                        case["filled_value"],
                    ),
                )
                uc.mem_write(record + 8, bytes(case["filled_name"]))
            uc.reg_write(arm.UC_ARM_REG_R0, 1 if case["fill_ok"] else 0)

        elif address == STUB_FORWARD:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, 1 if case["forward_ok"] else 0)

        elif address == STUB_LIST:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, LIST)

        elif address == STUB_VTABLE_10:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, case["vtable_result"])

        elif address == STUB_VTABLE_14:
            # Only reached by the vtable-slot negative control.
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, 0)

        else:  # pragma: no cover - guarded by hook range
            raise AssertionError(f"unexpected stub 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        uc = self.uc
        self.call_log = []
        self.outside_stack_writes = []
        self.filter_index = 0
        self.key_index = 0
        self.case = case

        uc.mem_write(DATA_ADDR, b"\x00" * DATA_SIZE)
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        uc.mem_write(FUNC_ADDR, code)
        uc.ctl_flush_tb()

        write_u32(uc, OBJECT + 0x00, VTABLE)
        write_u32(uc, OBJECT + 0x04, CONTEXT)
        write_u32(uc, VTABLE + 0x10, STUB_VTABLE_10)
        write_u32(uc, VTABLE + 0x14, STUB_VTABLE_14)

        write_u32(uc, LIST, case["list_count"])
        elements = case["list_elements"]
        for index in range(case["list_count"]):
            value = elements[index % len(elements)] if elements else 0
            write_u32(uc, LIST_ELEMENTS + index * 4, value)

        # Incoming stack arguments: [sp] = extra, [sp+4] = alt selector.
        uc.mem_write(ENTRY_SP, struct.pack("<II", case["extra"], case["alt"]))

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, OBJECT)
        uc.reg_write(arm.UC_ARM_REG_R1, case["selector"])
        uc.reg_write(arm.UC_ARM_REG_R2, STREAM)
        uc.reg_write(arm.UC_ARM_REG_R3, case["flags"])
        for name, value in CALLEE_SAVED_START.items():
            uc.reg_write(CALLEE_SAVED[name], value)

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "data": bytes(uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "outside_stack_writes": list(self.outside_stack_writes),
        }


def filter_result(case: dict, index: int) -> int:
    results = case["filter_results"]
    if not results:
        return 1
    return results[min(index, len(results) - 1)] & 0xFFFFFFFF


# ---------------------------------------------------------------------------
# Independent model
# ---------------------------------------------------------------------------
def model(case: dict) -> tuple[int, list[str], list]:
    """Expected return and ordered call names, plus notable argument records."""
    name = case["name"]
    events = ["engine_func_002aca0c"]
    filter_index = 1 if (case["flags"] & 0x02) else 0

    if case["flags"] & 0x02:
        events.append("engine_func_002ac8e4")
        if filter_result(case, 0) == 0:
            return 0, events, []

    if not (case["flags"] & 0x08):
        return 1, events, []

    events.append("vtable_10")
    if case["vtable_result"] != 0:
        events.append("engine_func_0014d390")
        if not case["record_ok"]:
            return 0, events, []
        events.append("engine_func_002ac6d0")
        events.append("engine_func_002ac614")
        if not case["fill_ok"]:
            return 0, events, []
        events.append("engine_func_001404ac")
        return (1 if case["forward_ok"] else 0), events, []

    events.append("func_001522dc")
    count = case["list_count"]
    if count == 0:
        return 1, events, []

    updates = case["key_count_updates"]
    key_index = 1          # the initial 0x002ACA0C call was call index 0
    iteration = 0
    while count > iteration:
        events.append("engine_func_002aca0c")
        if key_index in updates:
            count = updates[key_index]
        key_index += 1
        events.append("engine_func_002ac8e4")
        if filter_result(case, filter_index) == 0:
            return 0, events, []
        filter_index += 1
        iteration += 1

    return 1, events, []


def check_expectations(case: dict, result: dict) -> None:
    name = case["name"]
    expected_ret, expected_events, _ = model(case)

    assert result["pc"] == TRAP_ADDR, f"did not return to LR on {name}"
    assert result["sp"] == ENTRY_SP, f"SP not restored on {name}"
    assert result["callee_saved"] == CALLEE_SAVED_START, (
        f"callee-saved registers clobbered on {name}"
    )
    assert not result["outside_stack_writes"], (
        f"writes outside the private stack on {name}: "
        f"{result['outside_stack_writes']}"
    )
    assert result["ret"] == expected_ret, (
        f"return {result['ret']} != model {expected_ret} on {name}"
    )

    names = [entry[0] for entry in result["call_log"]]
    assert names == expected_events, (
        f"call sequence on {name}:\n  got={names}\n  want={expected_events}"
    )

    # Every helper sees the fixture context, stream and self as expected.
    for callee, args in result["call_log"]:
        if callee == "engine_func_002aca0c":
            assert args == (CONTEXT,), f"key context on {name}: {args}"
        elif callee == "engine_func_002ac8e4":
            self_ptr, key, stream, extra, mode = args
            assert self_ptr == OBJECT, f"filter self on {name}: {args}"
            assert stream == STREAM, f"filter stream on {name}: {args}"
            assert extra == case["extra"], f"filter extra on {name}: {args}"
            assert mode in (0, 1), f"filter mode on {name}: {args}"
        elif callee == "engine_func_0014d390":
            assert args == (CONTEXT, case["selector"], "<stack>"), (
                f"record lookup args on {name}: {args}"
            )
        elif callee == "engine_func_002ac6d0":
            assert args[1] == case["vtable_result"], (
                f"cursor key on {name}: {args}"
            )
        elif callee == "engine_func_002ac614":
            cursor, record, index, mode, rec_id, rec_value, *nm = args
            assert cursor == "<stack>" and record == "<stack>", (
                f"fill pointers on {name}: {args}"
            )
            assert index == case["lookup_id"], f"fill index on {name}: {args}"
            assert mode == 0, f"fill mode on {name}: {args}"
            assert (rec_id, rec_value) == (
                case["lookup_id"], case["lookup_value"]
            ), f"fill record words on {name}: {args}"
            assert tuple(nm) == (0, 0, 0, 0, 0), (
                f"record name was not cleared before fill on {name}: {args}"
            )
        elif callee == "engine_func_001404ac":
            self_ptr, first, second, stream, flags, extra = args
            assert self_ptr == OBJECT, f"forward self on {name}: {args}"
            assert (first, second) == (
                case["filled_id"], case["filled_value"]
            ), f"forward record args on {name}: {args}"
            assert stream == STREAM, f"forward stream on {name}: {args}"
            assert flags == case["flags"], f"forward flags on {name}: {args}"
            assert extra == case["extra"], f"forward extra on {name}: {args}"
        elif callee == "func_001522dc":
            assert args == (CONTEXT, selection(case)), (
                f"list selector on {name}: {args}"
            )
        elif callee == "vtable_10":
            assert args == (OBJECT, case["key"]), f"vtable args on {name}: {args}"
        else:  # vtable_14 only appears in negative controls
            raise AssertionError(f"unexpected call on {name}: {callee} {args}")


def selection(case: dict) -> int:
    if case["alt"] == 0xFFFFFFFF:
        return case["selector"]
    return case["alt"]


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "call_log"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["data"] != cand["data"]:
        index = next(
            i for i in range(0, len(orig["data"]), 4)
            if orig["data"][i : i + 4] != cand["data"][i : i + 4]
        )
        problems.append(
            "data differs first at 0x"
            f"{DATA_ADDR + index:08x}: "
            f"orig={orig['data'][index:index + 4].hex()} "
            f"cand={cand['data'][index:index + 4].hex()}"
        )
    if orig["outside_stack_writes"] != cand["outside_stack_writes"]:
        problems.append(
            "outside-stack writes orig="
            f"{orig['outside_stack_writes']} cand={cand['outside_stack_writes']}"
        )
    return problems


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "flags": 0x00000008,
        "selector": 0x00000001,
        "alt": 0xFFFFFFFF,
        "extra": 0x11111111,
        "key": KEY,
        "vtable_result": 0,
        "filter_results": [1],
        "record_ok": True,
        "lookup_id": 0x00000002,
        "lookup_value": 0x0000CAFE,
        "lookup_name": (0x41, 0x42),
        "fill_ok": True,
        "filled_id": 0x00000ABC,
        "filled_value": 0x00000DEF,
        "filled_name": (0x57, 0x58, 0x59, 0x5A, 0x21),
        "forward_ok": True,
        "cursor_words": (0xAAAA0001, 0xBBBB0002),
        "list_count": 0,
        "list_elements": (0xE0000000, 0xE0000001, 0xE0000002, 0xE0000003),
        "key_count_updates": {},
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- flag forms and the pre-pass ------------------------------------------
    cases.append(base_case("flags 0", flags=0x00000000))
    cases.append(base_case("flags bit 0 only", flags=0x00000001))
    cases.append(base_case("flags bit 1 only", flags=0x00000002))
    cases.append(base_case("flags bit 1 clear, all others set", flags=0xFFFFFFFD))
    cases.append(base_case("flags bit 3 clear, all others set", flags=0xFFFFFFF7))
    cases.append(base_case("flags bit 3 only, empty list", flags=0x00000008))
    cases.append(
        base_case("flags bit 1 set, all others clear", flags=0x00000002,
                  filter_results=[1])
    )
    cases.append(
        base_case("pre-pass returns zero", flags=0x00000002,
                  filter_results=[0])
    )
    cases.append(
        base_case("pre-pass returns 0xFFFFFFFF", flags=0x00000002,
                  filter_results=[0xFFFFFFFF])
    )
    cases.append(
        base_case("pre-pass returns 0x80000000", flags=0x00000002,
                  filter_results=[0x80000000])
    )
    cases.append(
        base_case("pre-pass failure with lookup bit set", flags=0x0000000A,
                  filter_results=[0])
    )

    # --- null vtable result: the list path ------------------------------------
    cases.append(base_case("null lookup, empty list", flags=0x00000008,
                           list_count=0))
    cases.append(base_case("null lookup, one element", flags=0x00000008,
                           list_count=1, filter_results=[1, 1]))
    cases.append(base_case("null lookup, three elements", flags=0x00000008,
                           list_count=3, filter_results=[1, 1, 1, 1]))
    cases.append(base_case("null lookup, four elements", flags=0x00000008,
                           list_count=4, filter_results=[1, 1, 1, 1, 1]))
    cases.append(base_case("null lookup, first iteration fails",
                           flags=0x00000008, list_count=3,
                           filter_results=[0]))
    cases.append(base_case("null lookup, second iteration fails",
                           flags=0x00000008, list_count=3,
                           filter_results=[1, 0]))
    cases.append(base_case("null lookup, third iteration fails",
                           flags=0x00000008, list_count=3,
                           filter_results=[1, 1, 0]))
    cases.append(base_case("loop count shrinks during iteration",
                           flags=0x00000008, list_count=4,
                           filter_results=[1, 1, 1, 1, 1],
                           key_count_updates={1: 1}))
    cases.append(base_case("loop count grows during iteration",
                           flags=0x00000008, list_count=1,
                           filter_results=[1, 1, 1, 1],
                           key_count_updates={1: 3}))
    cases.append(base_case("loop count shrinks on second iteration",
                           flags=0x00000008, list_count=4,
                           filter_results=[1, 1, 1, 1],
                           key_count_updates={2: 2}))
    cases.append(base_case("pre-pass plus two-element loop", flags=0x0000000A,
                           list_count=2, filter_results=[1, 1, 1]))
    cases.append(base_case("pre-pass failure plus lookup bit",
                           flags=0x0000000A, list_count=2,
                           filter_results=[0, 1]))
    cases.append(base_case("null key in loop path", flags=0x00000008,
                           key=0x00000000, list_count=2,
                           filter_results=[1, 1, 1]))
    cases.append(base_case("all flags set, three-element loop",
                           flags=0xFFFFFFFF, list_count=3,
                           filter_results=[1, 1, 1, 1]))

    # --- alternate selector ---------------------------------------------------
    cases.append(base_case("alt sentinel uses selector", flags=0x00000008,
                           alt=0xFFFFFFFF, selector=0x12345678, list_count=1,
                           filter_results=[1, 1]))
    cases.append(base_case("alt override", flags=0x00000008,
                           alt=0xDEADBEEF, selector=0x12345678, list_count=1,
                           filter_results=[1, 1]))
    cases.append(base_case("alt zero", flags=0x00000008, alt=0x00000000,
                           selector=0x12345678, list_count=1,
                           filter_results=[1, 1]))
    cases.append(base_case("alt high bit", flags=0x00000008, alt=0x80000000,
                           list_count=1, filter_results=[1, 1]))
    cases.append(base_case("selector 0xFFFFFFFF with sentinel",
                           flags=0x00000008, alt=0xFFFFFFFF,
                           selector=0xFFFFFFFF, list_count=1,
                           filter_results=[1, 1]))
    cases.append(base_case("selector 0x80000000 with override",
                           flags=0x00000008, alt=0xFFFFFFFF,
                           selector=0x80000000, list_count=1,
                           filter_results=[1, 1]))

    # --- non-null vtable result: the record path ------------------------------
    cases.append(base_case("record path success", flags=0x00000008,
                           vtable_result=KEY))
    cases.append(base_case("record path with pre-pass", flags=0x0000000A,
                           vtable_result=KEY, filter_results=[1]))
    cases.append(base_case("record path, all flags set",
                           flags=0xFFFFFFFF, vtable_result=KEY,
                           filter_results=[1]))
    cases.append(base_case("record path, bit 1 clear",
                           flags=0xFFFFFFF9, vtable_result=KEY))
    cases.append(base_case("record path, lookup fails", flags=0x00000008,
                           vtable_result=KEY, record_ok=False))
    cases.append(base_case("record path, fill fails", flags=0x00000008,
                           vtable_result=KEY, fill_ok=False))
    cases.append(base_case("record path, forward fails", flags=0x00000008,
                           vtable_result=KEY, forward_ok=False))
    cases.append(base_case("record path, pre-pass fails", flags=0x0000000A,
                           vtable_result=KEY, filter_results=[0]))
    cases.append(base_case("record path, override selector ignored",
                           flags=0x00000008, vtable_result=KEY,
                           alt=0xDEADBEEF, selector=0x22222222))
    cases.append(base_case("record path boundaries", flags=0x00000008,
                           vtable_result=KEY,
                           selector=0xFFFFFFFF, lookup_id=0x80000000,
                           lookup_value=0xFFFFFFFF,
                           filled_id=0x7FFFFFFF,
                           filled_value=0x80000000,
                           extra=0x80000000))
    cases.append(base_case("record path zero words", flags=0x00000008,
                           vtable_result=KEY, lookup_id=0, lookup_value=0,
                           filled_id=0, filled_value=0))
    cases.append(base_case("record path extra all bits",
                           flags=0x00000008, vtable_result=KEY,
                           extra=0xFFFFFFFF))
    cases.append(base_case("record path key not from first call",
                           flags=0x00000008, vtable_result=KEY,
                           key=0x00000000))
    cases.append(base_case("record path three high words",
                           flags=0x00000008, vtable_result=KEY,
                           lookup_id=0xFFFFFFFE, lookup_value=0x7FFFFFFF,
                           filled_id=0xFFFFFFFF, filled_value=0x00000001))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = Machine().run(orig_code, case)
        cand = Machine().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        check_expectations(case, orig)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing engine_func_00140318 (0x00140318)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"  original: {len(orig_code)} B, candidate: {len(cand_code)} B")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        (
            "pre_pass_flag",
            "constexpr u32 kPrePassFlag   = 0x02;",
            "constexpr u32 kPrePassFlag   = 0x04;",
        ),
        (
            "vtable_slot",
            "constexpr u32 kVtableSlot    = 0x10;",
            "constexpr u32 kVtableSlot    = 0x14;",
        ),
        (
            "alternate_sentinel",
            "constexpr u32 kNoAlternate   = 0xffffffffu;",
            "constexpr u32 kNoAlternate   = 0xfffffffeu;",
        ),
        (
            "pre_pass_mode",
            "if (engine_func_002ac8e4(self, key, stream, extra, 0) == 0) {",
            "if (engine_func_002ac8e4(self, key, stream, extra, 1) == 0) {",
        ),
        (
            "forward_argument_order",
            "if (engine_func_001404ac(self, record.id, record.value, stream, flags,",
            "if (engine_func_001404ac(self, record.value, record.id, stream, flags,",
        ),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Machine().run(orig_code, case)
            bad = Machine().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
