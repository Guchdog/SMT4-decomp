#!/usr/bin/env python3
"""Differential test for camp_func_0033138c (0x0033138c) using Unicorn ARM.

Compiles src/engine/leaf_batch45_b.cpp, extracts the camp_func_0033138c body,
resolves its direct calls to deterministic stubs at the pinned original targets,
and runs the pinned original (extracted/exefs/code.bin) against the candidate in
separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log with every register argument and the five architected
    stack words of the 0x0029F878 page poll (stack pointers normalised);
  * the s8 out flag the 0x0029F878 stub writes through its 7th argument;
  * the full work page, the 0x0043DA90 pointer page, and every write outside the
    private stack (address and width).

Coverage: state 0, 1, 2 and 0xFFFFFFFF; commands 0xB, 0xC, 0xD, 0, 0x11 and
0xFFFFFFFF; both poll helpers zero and non-zero; gate 0 zero/non-zero including
0x80000000; the s8 out flag at 0x00/0x01/0x7F/0x80/0xFF (sign boundary); gate 1
and gate 9 zero and non-zero; the identifier predicate zero and non-zero; cursor
sums that select entries 0..2 including a -1/+1 wrap; and the 6 / 0xB step
values. Negative controls mutate the node id, state offset, table base, queued
select dispatch id and published menu value; each mutant must be detected.
"""

from __future__ import annotations

import csv
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
SOURCE = ROOT / "src/engine/leaf_batch45_b.cpp"
FUNCTIONS_CSV = ROOT / "config/functions.csv"
OUT_DIR = ROOT / "build/test_leaf_0033138c"

FUNC_ADDR = 0x0033138C
FUNC_SIZE = 836

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x3F0000
WORK_ADDR = 0x00500000
WORK_SIZE = 0x00008000
DATA_ADDR = 0x00430000
DATA_SIZE = 0x00020000
NODE_ADDR = 0x00760000
NODE_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
WORK_POINTER_SLOT = 0x0043DA90

STUB_002BF6D0 = 0x002BF6D0
STUB_0029F878 = 0x0029F878
STUB_0029F278 = 0x0029F278
STUB_002C1830 = 0x002C1830
STUB_0029F260 = 0x0029F260
STUB_0029F248 = 0x0029F248
STUB_0029EBA8 = 0x0029EBA8
STUB_002994B4 = 0x002994B4
STUB_00299B9C = 0x00299B9C
STUB_00299E60 = 0x00299E60
STUB_002BDAC0 = 0x002BDAC0
STUB_00299410 = 0x00299410
STUB_0028FF04 = 0x0028FF04
STUB_0026A7C4 = 0x0026A7C4
STUB_0029CEE4 = 0x0029CEE4
STUB_002BC200 = 0x002BC200
STUB_0029E63C = 0x0029E63C
STUB_0029E5C8 = 0x0029E5C8
STUB_0029F10C = 0x0029F10C
STUB_002B8CCC = 0x002B8CCC

STUB_NAMES = {
    STUB_002BF6D0: "camp_func_002bf6d0",
    STUB_0029F878: "camp_func_0029f878",
    STUB_0029F278: "camp_func_0029f278",
    STUB_002C1830: "camp_func_002c1830",
    STUB_0029F260: "camp_func_0029f260",
    STUB_0029F248: "camp_func_0029f248",
    STUB_0029EBA8: "engine_func_0029eba8",
    STUB_002994B4: "engine_func_002994b4",
    STUB_00299B9C: "engine_func_00299b9c",
    STUB_00299E60: "engine_func_00299e60",
    STUB_002BDAC0: "camp_func_002bdac0",
    STUB_00299410: "engine_func_00299410",
    STUB_0028FF04: "camp_func_0028ff04",
    STUB_0026A7C4: "camp_func_0026a7c4",
    STUB_0029CEE4: "camp_func_0029cee4",
    STUB_002BC200: "camp_func_002bc200",
    STUB_0029E63C: "SortMenu_Init",
    STUB_0029E5C8: "engine_func_0029e5c8",
    STUB_0029F10C: "camp_func_0029f10c",
    STUB_002B8CCC: "camp_func_002b8ccc",
}

# Number of architected stack words each helper receives.
STACK_ARGS = {
    STUB_002BF6D0: 0,
    STUB_0029F878: 5,   # rect x/y/z, out-flag pointer, 0, 1
    STUB_0029F278: 0,
    STUB_002C1830: 0,
    STUB_0029F260: 0,
    STUB_0029F248: 0,
    STUB_0029EBA8: 0,
    STUB_002994B4: 0,
    STUB_00299B9C: 0,
    STUB_00299E60: 0,
    STUB_002BDAC0: 0,
    STUB_00299410: 0,
    STUB_0028FF04: 0,
    STUB_0026A7C4: 0,
    STUB_0029CEE4: 0,
    STUB_002BC200: 0,
    STUB_0029E63C: 0,
    STUB_0029E5C8: 0,
    STUB_0029F10C: 0,
    STUB_002B8CCC: 0,
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

# --------------------------------------------------------------------- work map
STATE_OFFSET = 0x1C
STEP_OFFSET = 0x20
SELECTED_OFFSET = 0x2C
FLAG_OFFSET = 0x31
MODE_OFFSET = 0x98
LIST_OFFSET = 0x34
OBJECT_OFFSET = 0x6D4
RECT_X_OFFSET = 0xE02
RECT_Y_OFFSET = 0xE04
RECT_Z_OFFSET = 0xE06
RECT_EXTRA_OFFSET = 0xE0C
TABLE_B_OFFSET = 0x147C
PAGE_OFFSETS = {0x0B: 0x00B0, 0x0C: 0x0114, 0x0D: 0x0178}

TABLE_ENTRY_COUNT = 8


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def elf_sections(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    e_shstrndx = struct.unpack_from("<H", data, 50)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    result: dict[str, bytes] = {}
    for section in sections:
        end = shstrtab.find(b"\x00", section[0])
        name = shstrtab[section[0] : end].decode("ascii", errors="replace")
        result[name] = data[section[4] : section[4] + section[5]]
    return result


def resolve_calls(code: bytearray, relocs, names: dict[str, int]) -> None:
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in names.items():
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


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0033138c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"camp_func_0033138c not found in {obj_file}: {sorted(funcs)}"
        )
    code_raw, relocs = candidate
    code = bytearray(code_raw)
    resolve_calls(code, relocs, STUB_NAMES)
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_b.o"
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
def build_work(case: dict) -> bytes:
    page = bytearray(WORK_SIZE)
    for offset in range(0, WORK_SIZE, 4):
        struct.pack_into("<I", page, offset, (0xA5A50000 ^ offset) & 0xFFFFFFFF)

    struct.pack_into("<I", page, STATE_OFFSET, case["state"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, STEP_OFFSET, case["step"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, SELECTED_OFFSET, case["selected"] & 0xFFFFFFFF)
    page[FLAG_OFFSET] = case["flag_byte_initial"] & 0xFF
    page[MODE_OFFSET] = case["mode_byte"] & 0xFF
    struct.pack_into("<I", page, LIST_OFFSET, 0x11112222)
    struct.pack_into("<I", page, OBJECT_OFFSET, 0x33334444)

    struct.pack_into("<h", page, RECT_X_OFFSET, case["rect_x"])
    struct.pack_into("<h", page, RECT_Y_OFFSET, case["rect_y"])
    struct.pack_into("<h", page, RECT_Z_OFFSET, case["rect_z"])
    struct.pack_into("<I", page, RECT_EXTRA_OFFSET, 0x55556666)

    for index in range(TABLE_ENTRY_COUNT):
        struct.pack_into("<H", page, TABLE_B_OFFSET + index * 2,
                         case["table_ids"][index] & 0xFFFF)

    for command, offset in PAGE_OFFSETS.items():
        struct.pack_into("<I", page, offset, 0x70000000 | command)
    return bytes(page)


def build_data(case: dict) -> bytes:
    page = bytearray(DATA_SIZE)
    for offset in range(0, DATA_SIZE, 4):
        struct.pack_into("<I", page, offset, (0xC3C30000 ^ offset) & 0xFFFFFFFF)
    struct.pack_into("<I", page, WORK_POINTER_SLOT - DATA_ADDR, WORK_ADDR)
    return bytes(page)


def sign8(value: int) -> int:
    return value - 0x100 if value & 0x80 else value


class LeafRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(NODE_ADDR, NODE_SIZE)
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
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        case = self.case

        if address == STUB_002BF6D0:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, NODE_ADDR)
        elif address == STUB_0029F878:
            self._log(address, r0, r1, r2, r3)
            sp = uc.reg_read(arm.UC_ARM_REG_SP)
            out_pointer = struct.unpack("<I", uc.mem_read(sp + 8, 4))[0]
            uc.mem_write(out_pointer, struct.pack("<B", case["out_flag"] & 0xFF))
            uc.reg_write(arm.UC_ARM_REG_R0, case["f878_result"])
        elif address == STUB_0029F278:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, case["f278_result"])
        elif address == STUB_002C1830:
            self._log(address, r0, r1)
            if r0 == 0:
                result = case["gate0"]
            elif r0 == 1:
                result = case["gate1"]
            elif r0 == 9:
                result = case["gate9"]
            else:
                raise AssertionError(f"unexpected 0x2C1830 select id {r0}")
            uc.reg_write(arm.UC_ARM_REG_R0, result & 0xFFFFFFFF)
        elif address == STUB_0029F260:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, case["cursor_a"] & 0xFFFFFFFF)
        elif address == STUB_0029F248:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, case["cursor_b"] & 0xFFFFFFFF)
        elif address == STUB_0029EBA8:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, case["list_index"] & 0xFFFFFFFF)
        elif address == STUB_002994B4:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, case["select_result"] & 0xFFFFFFFF)
        elif address == STUB_00299B9C:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, case["dispatch_result"] & 0xFFFFFFFF)
        elif address == STUB_00299E60:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x60000000)
        elif address == STUB_002BDAC0:
            self._log(address, r0, r1, r2)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x60000001)
        elif address == STUB_00299410:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x60000002)
        elif address == STUB_0028FF04:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, case["predicate"] & 0xFFFFFFFF)
        elif address == STUB_0026A7C4:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x60000003)
        elif address == STUB_0029CEE4:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x60000004)
        elif address == STUB_002BC200:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, 0xBC200000 | (r0 & 0xFFFF))
        elif address == STUB_0029E63C:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x60000005)
        elif address == STUB_0029E5C8:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x60000006)
        elif address == STUB_0029F10C:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x60000007)
        elif address == STUB_002B8CCC:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, case["flag_byte"] & 0xFF)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for name, args in log:
            out = []
            for arg in args:
                if isinstance(arg, int) and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE:
                    out.append("<stack>")
                else:
                    out.append(arg)
            normalised.append((name, tuple(out)))
        return normalised

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(WORK_ADDR, build_work(case))
        self.uc.mem_write(DATA_ADDR, build_data(case))
        self.uc.mem_write(NODE_ADDR, b"\x00" * NODE_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case["command"] & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        outside = [
            (address, size)
            for address, size, _value in self.writes
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        ]
        outside.sort()

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "outside_writes": outside,
            "work": bytes(self.uc.mem_read(WORK_ADDR, WORK_SIZE)),
            "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "call_log"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for key in ("work", "data"):
        if orig[key] != cand[key]:
            first = next(
                (i for i, (a, b) in enumerate(zip(orig[key], cand[key])) if a != b),
                None,
            )
            problems.append(f"{key} differs at byte {first}")
    if orig["outside_writes"] != cand["outside_writes"]:
        problems.append(
            "outside writes:\n    orig="
            + repr(orig["outside_writes"])
            + "\n    cand="
            + repr(cand["outside_writes"])
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "command": 0x0B,
        "state": 1,
        "step": 0x00,
        "selected": 0xDEADBEEF,
        "flag_byte_initial": 0x5A,
        "mode_byte": 0x02,
        "rect_x": 0x0123,
        "rect_y": -0x0456,
        "rect_z": 0x0789,
        "f878_result": 0,
        "f278_result": 0,
        "gate0": 0,
        "gate1": 1,
        "gate9": 1,
        "predicate": 1,
        "cursor_a": 0,
        "cursor_b": 0,
        "list_index": 0x11223344,
        "select_result": 0x55667788,
        "dispatch_result": 0x99AABBCC,
        "out_flag": 0,
        "flag_byte": 0xA7,
        "table_ids": [0x2000 + i * 3 for i in range(TABLE_ENTRY_COUNT)],
    }
    case.update(overrides)
    return case


def make_cases() -> list:
    cases: list = []

    # --- state dispatch: 0, 1, and early returns
    for state, command in (
        (2, 0x0B),
        (2, 0x0C),
        (3, 0x0D),
        (0xFFFFFFFF, 0x00),
        (0x80000000, 0x11),
    ):
        cases.append(base_case(f"state 0x{state:08x} cmd 0x{command:02x}",
                               state=state, command=command))
    for command in (0x0B, 0x0C, 0x0D, 0x00, 0x11, 0xFFFFFFFF):
        cases.append(base_case(f"state 0 cmd 0x{command:02x}",
                               state=0, command=command))

    # --- poll results: 0x0029F878 / 0x0029F278
    for result in (1, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"f878 result 0x{result:08x}", f878_result=result))
    for result in (1, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"f278 result 0x{result:08x}", f278_result=result))

    # --- gate 0 and the s8 out flag (0x3314A0..0x3314C4)
    for gate0 in (1, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"gate0 0x{gate0:08x} cmd B", gate0=gate0))
    for flag in (0x00, 0x01, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"out flag 0x{flag:02x} gate0 0 cmd B",
                               gate0=0, out_flag=flag))
        cases.append(base_case(f"out flag 0x{flag:02x} gate0 0 cmd C",
                               command=0x0C, gate0=0, out_flag=flag))

    # --- gate 1 / gate 9 branches
    for gate1 in (1, 0x80000000):
        for command in (0x0B, 0x0C, 0x0D, 0x11):
            cases.append(base_case(
                f"gate1 0x{gate1:08x} cmd 0x{command:02x}",
                gate1=gate1, command=command))
    for gate9 in (0, 1, 0x7FFFFFFF, 0x80000000):
        for command in (0x0B, 0x0C, 0x0D, 0x00):
            cases.append(base_case(
                f"gate9 0x{gate9:08x} cmd 0x{command:02x}",
                gate1=0, gate9=gate9, command=command))

    # --- identifier-list branch (command 0xB, non-zero combined gate)
    for predicate in (0, 1, 0x80000000):
        for index in (0, 1, 2, 7):
            cases.append(base_case(
                f"table index {index} predicate 0x{predicate:08x}",
                command=0x0B, gate0=1, predicate=predicate,
                cursor_a=index, cursor_b=0))
    # -1 + 1 wraps to entry 0 in 32-bit arithmetic.
    cases.append(base_case("cursor wrap -1 + 1", command=0x0B, gate0=1,
                           cursor_a=-1, cursor_b=1))
    cases.append(base_case("cursor wrap 0x7FFFFFFF + 1", command=0x0B,
                           gate0=1, cursor_a=0x7FFFFFFF, cursor_b=1,
                           table_ids=[0x3333] * TABLE_ENTRY_COUNT))
    # Out flag alone (gate 0) still reaches the identifier branch for 0xB.
    cases.append(base_case("out flag only cmd B", command=0x0B, gate0=0,
                           out_flag=0x01, predicate=1))
    # Command 0xC never takes the identifier branch even with a non-zero gate.
    cases.append(base_case("combined gate non-zero cmd C", command=0x0C,
                           gate0=1, out_flag=0x01, gate1=0, gate9=1))

    # --- reset path (0x3314C8..0x331534) for every command shape
    for command in (0x0B, 0x0C, 0x0D, 0x00, 0x11, 0xFFFFFFFF):
        cases.append(base_case(f"reset path cmd 0x{command:02x}",
                               command=command, gate0=0, out_flag=0,
                               gate1=1))

    # --- mode byte sign extension on the 0x002994B4 path
    for mode in (0x00, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"mode byte 0x{mode:02x}", mode_byte=mode,
                               f878_result=1))

    # --- rect / list values only need to be forwarded verbatim
    cases.append(base_case("rect boundaries", f878_result=1,
                           rect_x=-0x8000, rect_y=0x7FFF, rect_z=-1,
                           list_index=-1, select_result=0xFFFFFFFF,
                           dispatch_result=0x80000000))
    cases.append(base_case("sorted flag byte", gate1=0, gate9=1,
                           flag_byte=0x80))
    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = LeafRunner().run(orig_code, case)
        cand = LeafRunner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def check_ledger_row() -> None:
    with open(FUNCTIONS_CSV, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    matches = [row for row in rows if row["address"].lower() == "0x0033138c"]
    if len(matches) != 1:
        raise RuntimeError(f"expected one ledger row, found {len(matches)}")
    row = matches[0]
    if row["name"] != "camp_func_0033138c":
        raise RuntimeError(f"ledger name changed: {row['name']}")
    if row["src_file"] != "src/engine/leaf_batch45_b.cpp":
        raise RuntimeError(f"ledger src_file changed: {row['src_file']}")
    print(f"Ledger row: status={row['status']} size={row['size']}")


def main() -> None:
    print("Testing camp_func_0033138c (0x0033138c)...")
    check_ledger_row()
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
        ("node_id", "constexpr u32 kNode = 0x56D;",
         "constexpr u32 kNode = 0x56C;"),
        ("state_offset", "constexpr u32 kState = 0x1C;",
         "constexpr u32 kState = 0x18;"),
        ("table_base", "constexpr u32 kTableB = 0x147C;",
         "constexpr u32 kTableB = 0x147E;"),
        ("select_dispatch", "constexpr u32 kDispatchSelect = 0x0100016Eu;",
         "constexpr u32 kDispatchSelect = 0x0100016Fu;"),
        ("publish_menu", "constexpr u32 kPublishMenu = 0x28;",
         "constexpr u32 kPublishMenu = 0x29;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = LeafRunner().run(orig_code, case)
            bad = LeafRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
