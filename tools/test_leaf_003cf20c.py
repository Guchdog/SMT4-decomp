#!/usr/bin/env python3
"""Differential test for engine_func_003cf20c (0x003cf20c) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the engine_func_003cf20c body,
resolves its direct calls to deterministic stubs, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every register argument and each helper's
    architected stack word (0x00246F90 receives one);
  * the scratch page (the 0x10-byte 0x002C684C allocation), the context object,
    the context-pointer slot, the actor table, the 0x1E98 flag table, the row
    page and the forwarded owner pointer (all must be identical);
  * any emulated write outside the private stack, scratch or row pages.

Coverage: the +0x44A0 master gate, every record filter bit (0x01, 0x40, 0x400,
0x04, 0x200), both probe reject masks, collected/blocked combinations for
counts 1-4 and every second-draw index, the +0x44A8 gate with first draws below,
at and above the 0xF threshold (including a negative draw), signed unit-id
boundaries, null allocation and null row results (both fault), and key/owner
forwarding. Negative controls mutate four constants and must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_003cf20c"

FUNC_ADDR = 0x003CF20C
FUNC_SIZE = 456

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x3F0000
SCRATCH_ADDR = 0x00700000
SCRATCH_SIZE = 0x00010000
BASE_ADDR = 0x00710000
BASE_SIZE = 0x00010000
ACTORS_ADDR = 0x00720000
ACTORS_SIZE = 0x00010000
FLAGTBL_ADDR = 0x00730000
FLAGTBL_SIZE = 0x00010000
ROW_ADDR = 0x00740000
ROW_SIZE = 0x00010000
OWNER_ADDR = 0x00750000
OWNER_SIZE = 0x00010000
CTXPTR_ADDR = 0x00760000
CTXPTR_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets; stubs are placed at the same addresses so both
# the original bytes and the relocated candidate resolve to them.
STUB_ALLOC = 0x002C684C
STUB_PROBE_A = 0x002462A0
STUB_PROBE_B = 0x0022AAAC
STUB_DRAW = 0x0023EC3C
STUB_BATTLE_RECORD = 0x00246F90
STUB_ROW = 0x00282B94
STUB_BATTLE_ACTION = 0x0022A76C
STUB_FREE = 0x00250FB4

STUB_NAMES = {
    STUB_ALLOC: "AsdMemory_func_002c684c",
    STUB_PROBE_A: "ui_func_002462a0",
    STUB_PROBE_B: "ui_func_0022aaac",
    STUB_DRAW: "script_vm_func_0023ec3c",
    STUB_BATTLE_RECORD: "battle_func_00246f90",
    STUB_ROW: "ui_func_00282b94",
    STUB_BATTLE_ACTION: "battle_func_0022a76c",
    STUB_FREE: "ui_func_00250fb4",
}

# Number of architected stack words each helper receives.
STACK_ARGS = {
    STUB_ALLOC: 0,
    STUB_PROBE_A: 0,
    STUB_PROBE_B: 0,
    STUB_DRAW: 0,
    STUB_BATTLE_RECORD: 1,   # mode 1
    STUB_ROW: 0,
    STUB_BATTLE_ACTION: 0,
    STUB_FREE: 0,
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

# Context-object offsets reproduced from the ARM.
MASTER_OFFSET = 0x44A0
MASTER2_OFFSET = 0x44A8
ACTOR_TABLE_POINTER_OFFSET = 0x1FC0
FLAG_TABLE_POINTER_OFFSET = 0x1E98
ACTOR_STRIDE = 0x288
ACTOR_FLAGS_OFFSET = 0x0
ACTOR_VALUE_OFFSET = 0x8
ACTOR_STAGE_OFFSET = 0x1C6
FLAG_STRIDE = 0x114
FLAG_UNIT_ID_OFFSET = 0x62
ROW_CLEAR_OFFSET = 0x1C8
ROW_FLAG_OFFSET = 0x1CA
ROW_FLAG_BIT = 0x10

ACTOR_COUNT = 4
FREE_RETURN = 0x5A5A0000
ROW_OFFSET_DEFAULT = 0x40


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "003cf20c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_003cf20c not found in {obj_file}: {sorted(funcs)}"
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
            displacement = (target - pc) >> 2
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
def build_base(case: dict) -> bytes:
    page = bytearray(BASE_SIZE)
    for index in range(0, BASE_SIZE, 4):
        struct.pack_into("<I", page, index, 0x5A5A0000 | (index & 0xFFFF))
    struct.pack_into("<I", page, MASTER_OFFSET, case.get("master", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, MASTER2_OFFSET, case.get("master2", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, ACTOR_TABLE_POINTER_OFFSET, ACTORS_ADDR)
    struct.pack_into("<I", page, FLAG_TABLE_POINTER_OFFSET, FLAGTBL_ADDR)
    return bytes(page)


def build_actors(case: dict) -> bytes:
    page = bytearray(ACTORS_SIZE)
    for index in range(0, ACTORS_SIZE, 1):
        page[index] = (index * 7 + 3) & 0xFF
    records = case.get(
        "records",
        [
            (0x1, 0x0000, 0x0000),
            (0x1, 0x0200, 0x0001),
            (0x0, 0x0000, 0x0002),
            (0x41, 0x0000, 0x0003),
        ],
    )
    for i, (flags, stage, value) in enumerate(records):
        base = i * ACTOR_STRIDE
        struct.pack_into("<I", page, base + ACTOR_FLAGS_OFFSET, flags & 0xFFFFFFFF)
        struct.pack_into("<h", page, base + ACTOR_VALUE_OFFSET, s16(value))
        struct.pack_into("<H", page, base + ACTOR_STAGE_OFFSET, stage & 0xFFFF)
    return bytes(page)


def build_flag_table(case: dict) -> bytes:
    page = bytearray(FLAGTBL_SIZE)
    for index in range(0, FLAGTBL_SIZE, 1):
        page[index] = (index * 11 + 5) & 0xFF
    ids = case.get("unit_ids", {})
    for value in range(8):
        struct.pack_into(
            "<h",
            page,
            value * FLAG_STRIDE + FLAG_UNIT_ID_OFFSET,
            s16(ids.get(value, 0x100 + value)),
        )
        # Distinct sentinel per record so a wrong stride/record is visible.
        struct.pack_into("<I", page, value * FLAG_STRIDE, 0xA5A50000 | value)
    return bytes(page)


def build_row(case: dict) -> bytes:
    page = bytearray(ROW_SIZE)
    for index in range(0, ROW_SIZE, 4):
        struct.pack_into("<I", page, index, 0x3C3C0000 | (index & 0xFFFF))
    row_base = case.get("row_offset", ROW_OFFSET_DEFAULT)
    struct.pack_into("<H", page, row_base + ROW_FLAG_OFFSET,
                     case.get("row_flag_initial", 0x00E0))
    struct.pack_into("<H", page, row_base + ROW_CLEAR_OFFSET, 0xFFFF)
    return bytes(page)


def s16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value & 0x80000000 else value


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (SCRATCH_ADDR, SCRATCH_SIZE),
            (BASE_ADDR, BASE_SIZE),
            (ACTORS_ADDR, ACTORS_SIZE),
            (FLAGTBL_ADDR, FLAGTBL_SIZE),
            (ROW_ADDR, ROW_SIZE),
            (OWNER_ADDR, OWNER_SIZE),
            (CTXPTR_ADDR, CTXPTR_SIZE),
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
        self.probe_a_index = 0
        self.probe_b_index = 0
        self.draw_index = 0
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value & ((1 << (size * 8)) - 1)))

    def _next_value(self, key: str, index: int, default: int = 0) -> int:
        values = self.case.get(key, [])
        if index >= len(values):
            return default
        return values[index] & 0xFFFFFFFF

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_ALLOC:
            self._log(address, r0)
            value = 0 if self.case.get("alloc_null", False) else SCRATCH_ADDR
            uc.reg_write(arm.UC_ARM_REG_R0, value)
        elif address == STUB_PROBE_A:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                self._next_value("probe_a", self.probe_a_index),
            )
            self.probe_a_index += 1
        elif address == STUB_PROBE_B:
            self._log(address, r0, r1)
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                self._next_value("probe_b", self.probe_b_index),
            )
            self.probe_b_index += 1
        elif address == STUB_DRAW:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self._next_value("draws", self.draw_index)
            )
            self.draw_index += 1
        elif address == STUB_BATTLE_RECORD:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2200_46F0)
        elif address == STUB_ROW:
            self._log(address, r0, r1)
            if self.case.get("row_null", False):
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                uc.reg_write(
                    arm.UC_ARM_REG_R0,
                    ROW_ADDR + self.case.get("row_offset", ROW_OFFSET_DEFAULT),
                )
        elif address == STUB_BATTLE_ACTION:
            self._log(address, r0, r1, r2)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2200_A76C)
        elif address == STUB_FREE:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("free_return", FREE_RETURN)
            )
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for name, args in log:
            out = []
            for arg in args:
                if isinstance(arg, int) and (
                    STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE
                    or SCRATCH_ADDR <= arg < SCRATCH_ADDR + SCRATCH_SIZE
                ):
                    out.append("<stack>" if arg >= STACK_ADDR else "<scratch>")
                else:
                    out.append(arg)
            normalised.append((name, tuple(out)))
        return normalised

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.probe_a_index = 0
        self.probe_b_index = 0
        self.draw_index = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(BASE_ADDR, build_base(case))
        self.uc.mem_write(ACTORS_ADDR, build_actors(case))
        self.uc.mem_write(FLAGTBL_ADDR, build_flag_table(case))
        self.uc.mem_write(ROW_ADDR, build_row(case))
        self.uc.mem_write(OWNER_ADDR, bytes(range(256)) * (OWNER_SIZE // 256))
        self.uc.mem_write(CTXPTR_ADDR, struct.pack("<I", BASE_ADDR))
        self.uc.mem_write(SCRATCH_ADDR, b"\x00" * SCRATCH_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, CTXPTR_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, OWNER_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("key", 0x1234ABCD) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0xDEADBEEF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        fault = None
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError as error:  # pragma: no cover - diagnostic path
            fault = self.uc.reg_read(arm.UC_ARM_REG_PC)

        read_only = {
            "base": bytes(self.uc.mem_read(BASE_ADDR, BASE_SIZE)),
            "actors": bytes(self.uc.mem_read(ACTORS_ADDR, ACTORS_SIZE)),
            "flagtable": bytes(self.uc.mem_read(FLAGTBL_ADDR, FLAGTBL_SIZE)),
            "owner": bytes(self.uc.mem_read(OWNER_ADDR, OWNER_SIZE)),
            "ctxptr": bytes(self.uc.mem_read(CTXPTR_ADDR, CTXPTR_SIZE)),
        }
        writable = {
            "scratch": bytes(self.uc.mem_read(SCRATCH_ADDR, SCRATCH_SIZE)),
            "row": bytes(self.uc.mem_read(ROW_ADDR, ROW_SIZE)),
        }

        unexpected_writes = []
        for address, size, _value in self.writes:
            allowed = (
                STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
                or SCRATCH_ADDR <= address < SCRATCH_ADDR + SCRATCH_SIZE
                or ROW_ADDR <= address < ROW_ADDR + ROW_SIZE
            )
            if not allowed:
                unexpected_writes.append((address, size))

        if fault is not None:
            return {
                "fault": True,
                "call_log": self._normalise(self.call_log),
                "read_only": read_only,
            }

        return {
            "fault": False,
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "read_only": read_only,
            "writable": writable,
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    if orig["fault"] != cand["fault"]:
        problems.append(f"fault: orig={orig['fault']} cand={cand['fault']}")
        return problems
    if orig["fault"]:
        if orig["call_log"] != cand["call_log"]:
            problems.append(
                "faulting call_log:\n    orig="
                + repr(orig["call_log"])
                + "\n    cand="
                + repr(cand["call_log"])
            )
        for key, value in orig["read_only"].items():
            if value != cand["read_only"][key]:
                problems.append(f"faulting fixture {key} differs")
        return problems

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
    for key, value in orig["read_only"].items():
        if value != cand["read_only"][key]:
            problems.append(f"fixture {key} was modified differently")
    for key, value in orig["writable"].items():
        if value != cand["writable"][key]:
            problems.append(f"writable fixture {key} differs")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def case(name: str, **overrides) -> dict:
    out = {"name": name}
    out.update(overrides)
    return out


def make_cases() -> list[dict]:
    collected = (0x1, 0x0000, 0x0000)
    blocked = (0x1, 0x0200, 0x0001)
    skipped_zero = (0x0, 0x0000, 0x0002)
    skipped_six = (0x41, 0x0000, 0x0003)
    baseline = [collected, blocked, skipped_zero, skipped_six]

    cases: list[dict] = []

    # --- master gate at +0x44A0
    cases.append(case("master bit 2 set", master=0x4))
    cases.append(case("master all ones", master=0xFFFFFFFF))
    cases.append(case("master bit 2 clear, other bits set", master=0xFFFFFFFB))
    cases.append(case("master high bit only", master=0x80000000))

    # --- baseline proceed / skip combinations
    cases.append(case("baseline collect + block", records=baseline))
    cases.append(case("collected but never blocked",
                      records=[collected, collected, skipped_zero, skipped_zero]))
    cases.append(case("blocked but nothing collected",
                      records=[blocked, blocked, skipped_zero, skipped_zero]))
    cases.append(case("all records filtered",
                      records=[skipped_zero, skipped_six,
                               (0x1, 0x0400, 0x0), (0x1, 0x0004, 0x0)]))
    cases.append(case("stage 0x400 skips collectible",
                      records=[(0x1, 0x0400, 0x0), blocked,
                               skipped_zero, skipped_zero]))
    cases.append(case("stage 0x004 skips collectible",
                      records=[(0x1, 0x0004, 0x0), blocked,
                               skipped_zero, skipped_zero]))
    cases.append(case("stage 0x404 skips collectible",
                      records=[(0x1, 0x0404, 0x0), blocked,
                               skipped_zero, skipped_zero]))
    cases.append(case("flags bit0 clear even with stage 0",
                      records=[(0x0, 0x0, 0x0), blocked,
                               skipped_zero, skipped_zero]))
    cases.append(case("flags bit6 set even with bit0",
                      records=[(0x41, 0x0, 0x0), blocked,
                               skipped_zero, skipped_zero]))
    cases.append(case("flags 0x40 only",
                      records=[(0x40, 0x0, 0x0), blocked,
                               skipped_zero, skipped_zero]))

    # --- probe reject masks (probe calls are unconditional per candidate)
    cases.append(case("probe A reject bit 16", records=baseline,
                      probe_a=[0x00010000]))
    cases.append(case("probe A reject bit 20", records=baseline,
                      probe_a=[0x00100000]))
    cases.append(case("probe B reject bit 17", records=baseline,
                      probe_b=[0x00020000]))
    cases.append(case("probe B reject bit 18", records=baseline,
                      probe_b=[0x00040000]))
    cases.append(case("probes nonzero without reject bits", records=baseline,
                      probe_a=[0x00E8FFFF], probe_b=[0x00008000]))
    cases.append(case("probe A rejects first candidate only",
                      records=[collected, (0x1, 0x0, 0x0002),
                               blocked, skipped_zero],
                      probe_a=[0x00010000, 0x0, 0x0], draws=[0, 0]))

    # --- count 1..4 and every second-draw index
    two = [collected, (0x1, 0x0, 0x0002), blocked, skipped_zero]
    three = [collected, (0x1, 0x0, 0x0002), (0x1, 0x0, 0x0003), blocked]
    four = [collected, (0x1, 0x0, 0x0002), (0x1, 0x0, 0x0003),
            (0x1, 0x0, 0x0004)]
    cases.append(case("count 1 pick 0", records=baseline, draws=[0, 0]))
    cases.append(case("count 2 pick 0", records=two, draws=[0, 0]))
    cases.append(case("count 2 pick 1", records=two, draws=[0, 1]))
    cases.append(case("count 3 pick 0", records=three, draws=[0, 0]))
    cases.append(case("count 3 pick 1", records=three, draws=[0, 1]))
    cases.append(case("count 3 pick 2", records=three, draws=[0, 2]))
    cases.append(case("blocker before the collectible",
                      records=[blocked, collected, skipped_zero, skipped_zero],
                      draws=[0, 0]))
    cases.append(case("two blockers around a collectible",
                      records=[blocked, collected, blocked, skipped_zero],
                      draws=[0, 0]))
    # Four collectible records leave the +0x200 blocker flag clear, so the
    # action is skipped even though the scratch list holds four values.
    for pick in range(4):
        cases.append(case(f"all four collected, no blocker (pick {pick})",
                          records=four, draws=[0, pick]))
    cases.append(case("count 1 out-of-range pick", records=baseline, draws=[0, 5]))

    # --- first draw threshold and the +0x44A8 gate (signed comparison)
    for draw in (-1, 0, 1, 14):
        cases.append(case(f"first draw {draw} bypasses gate2", records=baseline,
                          draws=[draw, 0], master2=0x8000000))
    cases.append(case("first draw 15, gate2 clear", records=baseline,
                      draws=[15, 0], master2=0))
    cases.append(case("first draw 15, gate2 bit 24", records=baseline,
                      draws=[15, 0], master2=0x1000000))
    cases.append(case("first draw 0x63, gate2 clear", records=baseline,
                      draws=[0x63, 0], master2=0xFFFFFFFF & ~0x1000000))
    cases.append(case("first draw 0x63, gate2 bit 24", records=baseline,
                      draws=[0x63, 0], master2=0x1000000))

    # --- signed unit ids and row offsets
    for ident, value in ((-1, 0), (-0x8000, 0), (0x7FFF, 0), (0, 0)):
        cases.append(case(f"unit id 0x{ident & 0xFFFF:04x}", records=baseline,
                          unit_ids={value: ident}, draws=[0, 0]))
    for offset in (0x0, 0x8, 0x100, 0x2000):
        cases.append(case(f"row offset 0x{offset:x}", records=baseline,
                          row_offset=offset, draws=[0, 0]))
    cases.append(case("row flag already has bit 0x10", records=baseline,
                      row_flag_initial=0x00F0))
    cases.append(case("row flag all ones", records=baseline,
                      row_flag_initial=0xFFFF))

    # --- forwarded key/owner and free return
    cases.append(case("negative key", records=baseline, key=0x80000000,
                      draws=[0, 0]))
    cases.append(case("key 0xFFFFFFFF", records=baseline, key=0xFFFFFFFF,
                      draws=[0, 0]))
    cases.append(case("custom free return", records=baseline, draws=[0, 0],
                      free_return=0xDEADBEEF))

    # --- signed collected values that are not selected
    cases.append(case("negative value not selected",
                      records=[(0x1, 0x0, 0xFFFF), (0x1, 0x0, 0x0002),
                               blocked, skipped_zero],
                      draws=[0, 1]))
    cases.append(case("0x8000 value not selected",
                      records=[(0x1, 0x0, 0x8000), (0x1, 0x0, 0x0002),
                               blocked, skipped_zero],
                      draws=[0, 1]))
    cases.append(case("0x7FFF value selected walks past the flag table",
                      records=[(0x1, 0x0, 0x7FFF), blocked,
                               skipped_zero, skipped_zero],
                      draws=[0, 0]))

    # --- null helper results
    cases.append(case("null allocation without collect",
                      records=[blocked, blocked, skipped_zero, skipped_zero],
                      alloc_null=True))
    cases.append(case("null allocation with collect", records=baseline,
                      alloc_null=True))
    cases.append(case("null row lookup", records=baseline, row_null=True,
                      draws=[0, 0]))

    return cases


def expected_baseline_log(key: int) -> list:
    """Ground-truth call log for the default record set and draws [0, 0]."""
    return [
        ("AsdMemory_func_002c684c", (0x10,)),
        ("ui_func_002462a0", (0x00000000, 0xF, 2, 0xFFFFFFFF)),
        ("ui_func_0022aaac", (0x00000000, 0xF)),
        ("script_vm_func_0023ec3c", (0x63,)),
        ("script_vm_func_0023ec3c", (0x00000000,)),
        ("battle_func_00246f90",
         (key, OWNER_ADDR, FLAGTBL_ADDR, 0x200, 1)),
        ("ui_func_00282b94", (BASE_ADDR, 0x00000100)),
        ("battle_func_0022a76c",
         (0x1C, ROW_ADDR + ROW_OFFSET_DEFAULT, 1)),
        ("ui_func_00250fb4", ("<scratch>",)),
    ]


def check_expected(scenario: dict, result: dict) -> None:
    """Pin a few fixture-derived expectations so the stubs cannot hide a
    scenario that is trivially identical on both sides."""
    name = scenario["name"]
    if name == "baseline collect + block":
        assert not result["fault"], "baseline must not fault"
        expected = expected_baseline_log(scenario.get("key", 0x1234ABCD))
        assert result["call_log"] == expected, (
            "baseline call log mismatch:\n  got="
            + repr(result["call_log"])
            + "\n  exp="
            + repr(expected)
        )
        assert result["ret"] == FREE_RETURN, result["ret"]
        assert result["sp"] == ENTRY_SP, hex(result["sp"])
        row = result["writable"]["row"]
        offset = ROW_OFFSET_DEFAULT
        assert struct.unpack_from("<H", row, offset + ROW_CLEAR_OFFSET)[0] == 0
        assert struct.unpack_from("<H", row, offset + ROW_FLAG_OFFSET)[0] == (
            0x00E0 | ROW_FLAG_BIT
        )
        scratch = result["writable"]["scratch"]
        assert struct.unpack_from("<i", scratch, 0)[0] == 0
        assert struct.unpack_from("<i", scratch, 4)[0] == 0
    elif name == "master bit 2 set":
        assert result["ret"] == 0x4, hex(result["ret"])
        assert result["call_log"] == [], result["call_log"]
    elif name == "first draw 15, gate2 clear":
        assert not result["fault"]
        assert [entry[0] for entry in result["call_log"]] == [
            "AsdMemory_func_002c684c",
            "ui_func_002462a0",
            "ui_func_0022aaac",
            "script_vm_func_0023ec3c",
            "ui_func_00250fb4",
        ], result["call_log"]
    elif name == "null allocation without collect":
        assert result["call_log"][-1] == ("ui_func_00250fb4", (0,)), (
            result["call_log"]
        )
    elif name == "count 3 pick 2":
        assert result["call_log"][8] == (
            "script_vm_func_0023ec3c", (0x00000002,)
        ), result["call_log"]
        assert result["call_log"][-2] == (
            "battle_func_0022a76c",
            (0x1C, ROW_ADDR + ROW_OFFSET_DEFAULT, 1),
        ), result["call_log"]


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for scenario in cases:
        orig = Runner().run(orig_code, scenario)
        check_expected(scenario, orig)
        cand = Runner().run(cand_code, scenario)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {scenario['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        suffix = " (fault)" if orig["fault"] else ""
        print(
            f"  [PASS] {scenario['name']}  "
            f"({len(orig['call_log'])} calls){suffix}"
        )
    return passed


def main() -> None:
    print("Testing engine_func_003cf20c (0x003cf20c)...")
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
        ("stage_skip_bits", "constexpr u32 kStageSkipBits = 0x400 | 0x4;",
         "constexpr u32 kStageSkipBits = 0x400;"),
        ("reject_mask", "constexpr u32 kRejectMask = 0x170000;",
         "constexpr u32 kRejectMask = 0x70000;"),
        ("draw_threshold", "constexpr s32 kFirstDrawThreshold = 0xF;",
         "constexpr s32 kFirstDrawThreshold = 0xE;"),
        ("flag_stride", "constexpr u32 kFlagStride = 0x114;",
         "constexpr u32 kFlagStride = 0x110;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for scenario in cases:
            orig = Runner().run(orig_code, scenario)
            bad = Runner().run(mutant_code, scenario)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
