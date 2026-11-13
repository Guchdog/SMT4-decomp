#!/usr/bin/env python3
"""Differential test for ui_func_0033b3e0 (0x0033b3e0) using Unicorn ARM.

Compiles ``src/engine/leaf_batch41_c.cpp``, extracts the ``ui_func_0033b3e0``
body, resolves its two direct calls to deterministic stubs placed at the
original target addresses, and runs the pinned original
(``extracted/exefs/code.bin``) against the candidate on two Unicorn machines
with identical fixtures.

Compared outputs per case:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log with every register argument of both helpers;
  * every emulated write outside the private stack, in order;
  * the full UI context page, the 0x114-stride flag table, the 0x288-stride
    actor table, the 0x00439CA8 global page and the low page used for the
    unchecked helper-result dereference.

Coverage: both required flag bits (0x01/0x80) in every combination, the
cursor domain (-5, -1, 0, 10, 11, 0x7FFF), the free-slot scan with an occupied
prefix, an exhausted slot list (including one reached from a negative start),
an insertion before the slot array, positive/negative/zero/boundary inserted
values, primary-key swaps and non-swaps, tie-break swaps and non-swaps, s16
truncation of the key sum (wrap-around and post-truncation equality), signed
key ordering, negative slots skipped in both loops, a full exchange pass, the
flag-table index boundaries (negative, 0, 0x6C, 0x100) and a null helper
result.

Negative controls recompile mutated source (flag mask, key offsets, key
truncation, comparison directions, the start-versus-free sort origin and the
free-slot test); each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_0033b3e0"

FUNC_NAME = "ui_func_0033b3e0"
FUNC_ADDR = 0x0033B3E0
FUNC_SIZE = 400

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers 0x0033B3E0 and both stub addresses
ZERO_ADDR = 0x00000000
ZERO_SIZE = 0x00001000
GLOBAL_ADDR = 0x00439000
GLOBAL_SIZE = 0x00001000  # 0x00439CA8 lies at +0xCA8
CTX_ADDR = 0x00800000
CTX_SIZE = 0x00004000
FLAG_MAP = 0x00810000
FLAG_MAP_SIZE = 0x00020000
ACTOR_MAP = 0x00840000
ACTOR_MAP_SIZE = 0x00020000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# fixture layout inside the mapped pages
FLAG_TABLE = FLAG_MAP + 0x4000     # base stored at ui+0x1E98
ACTOR_TABLE = ACTOR_MAP            # base stored at ui+0x1FC0
GLOBAL_CELL = GLOBAL_ADDR + 0xCA8  # 0x00439CA8
FLAG_RECORD_STRIDE = 0x114
FLAG_WORD_OFFSET = 0x50
ACTOR_STRIDE = 0x288
ACTOR_COUNT = 0x6D

SLOT_ARRAY = 0x2F06
SLOT_CURSOR = 0x2F1E

DEFAULT_BUFFER = 0x00900000
DEFAULT_ZERO_VALUE = 0x1234

# Original direct-call targets; the stubs live at the same addresses so the
# original bytes and the relocated candidate resolve to them.
STUB_282B94 = 0x00282B94
STUB_25508C = 0x0025508C

STUB_NAMES = {
    STUB_282B94: "ui_func_00282b94",
    STUB_25508C: "script_vm_func_0025508c",
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
        if "0033b3e0" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"{FUNC_NAME} not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        target = None
        for address, name in STUB_NAMES.items():
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(
                f"unhandled relocation {rel.relocation_type} -> {rel.symbol_name}"
            )
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unexpected relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        condition = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, condition | (displacement & 0x00FFFFFF)
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
def all_slots(value: int = -1) -> dict:
    return {index: value for index in range(12)}


def build_ctx(case: dict) -> bytes:
    page = bytearray(b"\xCC" * CTX_SIZE)
    struct.pack_into("<I", page, 0x1E98, FLAG_TABLE)
    struct.pack_into("<I", page, 0x1FC0, ACTOR_TABLE)
    for index, value in case["slots"].items():
        struct.pack_into("<h", page, SLOT_ARRAY + 2 * index, value)
    struct.pack_into("<h", page, SLOT_CURSOR, case["cursor"])
    return bytes(page)


def build_flags(case: dict) -> bytes:
    # Every record outside the tested one keeps 0x11111111 (bit 0 set, bit 7
    # clear) so a wrong index or stride reads a different value.
    page = bytearray(b"\x11" * FLAG_MAP_SIZE)
    offset = FLAG_TABLE - FLAG_MAP + FLAG_WORD_OFFSET + (
        case["id"] * FLAG_RECORD_STRIDE
    )
    if not 0 <= offset <= FLAG_MAP_SIZE - 4:
        raise RuntimeError(f"flag fixture offset 0x{offset:x} outside the page")
    struct.pack_into("<I", page, offset, case["flags"] & 0xFFFFFFFF)
    return bytes(page)


def default_actor_fields(index: int) -> dict:
    return {
        "key0": (0x0100 + index) & 0xFFFF,
        "key1": (0x0010 + (index & 0x0F)) & 0xFFFF,
        "tie": (0x40 + index) & 0xFFFF,
        "value": (0x50 + index) & 0xFFFF,
    }


def build_actors(case: dict) -> bytes:
    page = bytearray(ACTOR_MAP_SIZE)
    for index in range(ACTOR_COUNT):
        fields = default_actor_fields(index)
        base = index * ACTOR_STRIDE
        struct.pack_into("<h", page, base + 0x08, fields["tie"])
        # Neighbour word of the secondary key: distinct per record so a wrong
        # secondary-key offset cannot read the same values.
        struct.pack_into("<h", page, base + 0x0A, (0x60 + index) & 0xFFFF)
        struct.pack_into("<H", page, base + 0x1C2, fields["key0"])
        struct.pack_into("<H", page, base + 0x254, fields["key1"])
        struct.pack_into("<h", page, base + 0x6E, fields["value"])
    for index, override in case.get("actors", {}).items():
        base = index * ACTOR_STRIDE
        fields = default_actor_fields(index)
        fields.update(override)
        struct.pack_into("<h", page, base + 0x08, fields["tie"])
        struct.pack_into("<H", page, base + 0x1C2, fields["key0"] & 0xFFFF)
        struct.pack_into("<H", page, base + 0x254, fields["key1"] & 0xFFFF)
        struct.pack_into("<h", page, base + 0x6E, fields["value"])
    if case.get("value") is not None:
        # The helper-selected record carries the s16 copied into the slot.
        base = case["helper_record"] * ACTOR_STRIDE
        struct.pack_into("<h", page, base + 0x6E, case["value"])
    # Sentinel tail beyond the last catalogued record.
    tail = ACTOR_COUNT * ACTOR_STRIDE
    page[tail:] = b"\x5A" * (ACTOR_MAP_SIZE - tail)
    return bytes(page)


def build_global(case: dict) -> bytes:
    page = bytearray(b"\x7E" * GLOBAL_SIZE)
    struct.pack_into("<I", page, GLOBAL_CELL - GLOBAL_ADDR,
                     case["buffer"] & 0xFFFFFFFF)
    return bytes(page)


def build_zero(case: dict) -> bytes:
    page = bytearray(ZERO_SIZE)
    struct.pack_into("<h", page, 0x6E, case["zero_value"])
    return bytes(page)


# ---------------------------------------------------------------------- runner
class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        for address, size in (
            (ZERO_ADDR, ZERO_SIZE),
            (CODE_ADDR, CODE_SIZE),
            (GLOBAL_ADDR, GLOBAL_SIZE),
            (CTX_ADDR, CTX_SIZE),
            (FLAG_MAP, FLAG_MAP_SIZE),
            (ACTOR_MAP, ACTOR_MAP_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)

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
    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value & ((1 << (8 * size)) - 1)))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        if address == STUB_282B94:
            self.call_log.append(("ui_func_00282b94", r0, r1))
            if self.case["helper_null"]:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                uc.reg_write(
                    arm.UC_ARM_REG_R0,
                    ACTOR_TABLE + self.case["helper_record"] * ACTOR_STRIDE,
                )
        elif address == STUB_25508C:
            self.call_log.append(("script_vm_func_0025508c", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, (r0 ^ 0x5A5A5A5A) & 0xFFFFFFFF)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.case = case
        uc = self.uc

        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(ZERO_ADDR, build_zero(case))
        uc.mem_write(GLOBAL_ADDR, build_global(case))
        uc.mem_write(CTX_ADDR, build_ctx(case))
        uc.mem_write(FLAG_MAP, build_flags(case))
        uc.mem_write(ACTOR_MAP, build_actors(case))
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R1, case["id"] & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            uc.reg_write(CALLEE_SAVED[name], value)

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = [
            (address, size, value)
            for address, size, value in self.writes
            if not STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
        ]

        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "writes": unexpected_writes,
            "ctx": bytes(uc.mem_read(CTX_ADDR, CTX_SIZE)),
            "flags": bytes(uc.mem_read(FLAG_MAP, FLAG_MAP_SIZE)),
            "actors": bytes(uc.mem_read(ACTOR_MAP, ACTOR_MAP_SIZE)),
            "global": bytes(uc.mem_read(GLOBAL_ADDR, GLOBAL_SIZE)),
            "zero": bytes(uc.mem_read(ZERO_ADDR, ZERO_SIZE)),
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
    if orig["writes"] != cand["writes"]:
        problems.append(
            "writes:\n    orig="
            + repr(orig["writes"])
            + "\n    cand="
            + repr(cand["writes"])
        )
    for key in ("ctx", "flags", "actors", "global", "zero"):
        if orig[key] != cand[key]:
            for offset in range(len(orig[key])):
                if orig[key][offset] != cand[key][offset]:
                    problems.append(
                        f"fixture {key} differs from offset 0x{offset:x}"
                    )
                    break
    return problems


# ----------------------------------------------------------------------- cases
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "id": 1,
        "flags": 0x81,
        "cursor": 0,
        "slots": all_slots(),
        "helper_record": 3,
        "helper_null": False,
        "value": None,
        "buffer": DEFAULT_BUFFER,
        "zero_value": DEFAULT_ZERO_VALUE,
        "actors": {},
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- flag gate: both required bits in every combination
    for flags in (0x00, 0x01, 0x80, 0x81, 0xFF, 0xFFFFFFFF, 0x5B, 0x5A,
                  0x7FFFFFFF, 0xFFFFFF7F):
        cases.append(base_case(f"flags 0x{flags:08x}", flags=flags))

    # --- flag-table index boundaries (record 0x114, field +0x50)
    for ident in (0, 1, 0x6C, 0x6D, 0x100, -1, -0x20):
        cases.append(base_case(f"id {ident}", id=ident))

    # --- cursor domain and the free-slot scan
    cases.append(base_case("cursor 0, empty list", value=1))               # at 1
    cases.append(base_case("cursor 1, empty list", cursor=1, value=1))     # at 2
    cases.append(base_case("cursor 10, empty list", cursor=10, value=1))   # at 11
    cases.append(base_case("cursor 11 saturates", cursor=11, value=1))     # none
    cases.append(base_case("cursor 0x7FFF saturates", cursor=0x7FFF, value=1))
    cases.append(base_case("cursor -1 inserts at 0", cursor=-1, value=1))
    cases.append(base_case(
        "cursor -5 inserts before the array",
        cursor=-5,
        slots={-4: -1, -3: 2, -2: -1, -1: -1, **{i: -1 for i in range(12)}},
        helper_record=4,
        value=4,
        actors={2: {"key0": 0x0001, "key1": 0x0000, "tie": 0x30},
                4: {"key0": 0x0009, "key1": 0x0000, "tie": 0x31}},
    ))
    cases.append(base_case(
        "cursor -5 exhausts a full list",
        cursor=-5,
        slots={(-4 + k): 0 for k in range(16)},
        value=1,
    ))
    cases.append(base_case(
        "occupied prefix before the free slot",
        slots={**{i: -1 for i in range(12)}, 1: 0, 2: 5},
        helper_record=9,
        value=9,
        actors={0: {"key0": 0x0002, "key1": 0x0000, "tie": 0x20},
                5: {"key0": 0x0004, "key1": 0x0000, "tie": 0x21},
                9: {"key0": 0x0008, "key1": 0x0000, "tie": 0x22}},
    ))
    cases.append(base_case(
        "first slot occupied",
        slots={**{i: -1 for i in range(12)}, 1: 7},
        helper_record=2,
        value=2,
    ))
    cases.append(base_case(
        "all slots from 1 occupied",
        slots={i: (i - 1) for i in range(1, 12)},
        value=1,
    ))

    # --- inserted value boundaries
    for value in (0x7FFF, -0x8000, -1, 0, 1, 0x6C):
        cases.append(base_case(f"value {value}", value=value))
    cases.append(base_case("value 0x7FFF from actor record 0x6C",
                           helper_record=0x6C, value=0x7FFF))

    # --- primary key comparisons
    cases.append(base_case(
        "swap when key_j < key_i",
        value=2,
        slots={**{i: -1 for i in range(12)}, 2: 5, 3: 1},
        actors={2: {"key0": 0x0002, "key1": 0x0000, "tie": 0x50},
                5: {"key0": 0x0008, "key1": 0x0000, "tie": 0x51},
                1: {"key0": 0x0001, "key1": 0x0000, "tie": 0x52}},
    ))
    cases.append(base_case(
        "no swap when key_j > key_i",
        value=5,
        slots={**{i: -1 for i in range(12)}, 2: 1, 3: 2},
        actors={5: {"key0": 0x0008, "key1": 0x0000, "tie": 0x50},
                1: {"key0": 0x0001, "key1": 0x0000, "tie": 0x51},
                2: {"key0": 0x0002, "key1": 0x0000, "tie": 0x52}},
    ))
    cases.append(base_case(
        "signed key order",
        value=2,
        slots={**{i: -1 for i in range(12)}, 2: 1},
        actors={2: {"key0": 0xFFFE, "key1": 0x0000, "tie": 0x60},
                1: {"key0": 0x0001, "key1": 0x0000, "tie": 0x61}},
    ))
    cases.append(base_case(
        "s16 key wrap-around",
        value=1,
        slots={**{i: -1 for i in range(12)}, 2: 2},
        actors={1: {"key0": 0xFFFF, "key1": 0xFFFF, "tie": 0x70},
                2: {"key0": 0x0001, "key1": 0x0000, "tie": 0x71}},
    ))
    cases.append(base_case(
        "post-truncation equality",
        value=1,
        slots={**{i: -1 for i in range(12)}, 2: 2},
        actors={1: {"key0": 0x8000, "key1": 0x8000, "tie": 0x72},
                2: {"key0": 0x0000, "key1": 0x0000, "tie": 0x73}},
    ))

    # --- tie-break (equal primary keys)
    cases.append(base_case(
        "tie-break swaps when larger",
        value=1,
        slots={**{i: -1 for i in range(12)}, 2: 2},
        actors={1: {"key0": 0x0003, "key1": 0x0004, "tie": 0x30},
                2: {"key0": 0x0007, "key1": 0x0000, "tie": 0x20}},
    ))
    cases.append(base_case(
        "tie-break keeps order when smaller",
        value=1,
        slots={**{i: -1 for i in range(12)}, 2: 2},
        actors={1: {"key0": 0x0003, "key1": 0x0004, "tie": 0x20},
                2: {"key0": 0x0007, "key1": 0x0000, "tie": 0x30}},
    ))
    cases.append(base_case(
        "tie-break equal keeps order",
        value=1,
        slots={**{i: -1 for i in range(12)}, 2: 2},
        actors={1: {"key0": 0x0003, "key1": 0x0004, "tie": 0x30},
                2: {"key0": 0x0007, "key1": 0x0000, "tie": 0x30}},
    ))

    # --- negative slots skipped in the inner and outer loops
    cases.append(base_case(
        "inner loop skips a negative slot",
        value=1,
        slots={**{i: -1 for i in range(12)}, 2: 5, 3: -1, 4: 3},
    ))
    cases.append(base_case(
        "outer loop skips a negative slot",
        value=-1,
        slots={**{i: -1 for i in range(12)}, 2: 5, 4: 3},
    ))
    cases.append(base_case(
        "two free holes in the window",
        value=1,
        slots={**{i: -1 for i in range(12)}, 2: -9, 3: 5, 4: -9, 5: 2},
    ))

    # --- full exchange pass over a scrambled window
    cases.append(base_case(
        "exchange pass over ten values",
        value=6,
        slots={**{i: -1 for i in range(12)},
               2: 5, 3: 4, 4: 3, 5: 2, 6: 1, 7: 0,
               8: 11, 9: 10, 10: 9, 11: 8},
        actors={i: {"key0": 0x0100 + i, "key1": (0x10 + (i & 0xF)) & 0xFFFF,
                    "tie": 0x40 + i} for i in range(12)},
    ))

    # --- helper result: null and non-null
    cases.append(base_case("helper returns null", helper_null=True))
    cases.append(base_case("helper returns null, cursor saturates",
                           helper_null=True, cursor=11))
    cases.append(base_case("helper returns null, flags reject",
                           helper_null=True, flags=0x01))
    cases.append(base_case("helper record 0", helper_record=0))
    cases.append(base_case("helper record 0x6C", helper_record=0x6C))

    # --- global buffer cell contents
    for buffer in (0x00000000, 0xFFFFFFFF, 0x00900000, 0x12345678):
        cases.append(base_case(f"buffer cell 0x{buffer:08x}", buffer=buffer))

    return cases


# ------------------------------------------------------------------------ main
def run_cases(orig_code: bytes, cand_code: bytes, cases: list[dict]) -> int:
    orig_runner = Runner()
    cand_runner = Runner()
    passed = 0
    for case in cases:
        orig = orig_runner.run(orig_code, case)
        cand = cand_runner.run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls, "
              f"{len(orig['writes'])} memory writes)")
    return passed


def main() -> None:
    print(f"Testing {FUNC_NAME} (0x{FUNC_ADDR:08x})...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          f"(relocations resolved).")

    cases = make_cases()
    passed = run_cases(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        ("flag_mask",
         "constexpr u32 kFlagBit7 = 0x00000080;",
         "constexpr u32 kFlagBit7 = 0x00000040;"),
        ("primary_key_low_offset",
         "constexpr u32 kPrimaryKeyLowOffset = 0x1C2;",
         "constexpr u32 kPrimaryKeyLowOffset = 0x1C6;"),
        ("secondary_key_offset",
         "constexpr u32 kSecondaryKeyOffset = 0x008;",
         "constexpr u32 kSecondaryKeyOffset = 0x00A;"),
        ("key_truncation",
         "return static_cast<s16>(static_cast<u16>(low + high));",
         "return static_cast<s32>(low + high);"),
        ("key_direction",
         "? key_j < key_i",
         "? key_j > key_i"),
        ("tie_direction",
         ": SecondaryKey(actors, slot_j) >",
         ": SecondaryKey(actors, slot_j) <"),
        ("sort_origin",
         "for (s32 j = start;",
         "for (s32 j = free_index;"),
        ("free_slot_test",
         "*SlotAt(ui, free_index) >= 0",
         "*SlotAt(ui, free_index) > 0"),
        ("insert_cursor_bias",
         "ui + ui_b3e0::kCursorOffset)) + 1;",
         "ui + ui_b3e0::kCursorOffset)) + 2;"),
    )
    for name, old, new in mutants:
        mutant_code = compile_candidate_mutant(name, old, new)
        orig_runner = Runner()
        mutant_runner = Runner()
        detected = False
        for case in cases:
            orig = orig_runner.run(orig_code, case)
            bad = mutant_runner.run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED; "
          f"all {len(mutants)} mutants detected.")


if __name__ == "__main__":
    main()
