#!/usr/bin/env python3
"""Differential test for shop_func_003a3e98 (0x003A3E98) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the shop_func_003a3e98 body,
resolves every direct call to a deterministic stub at the original target
address, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log with every meaningful register argument (pointer
    arguments from the private work page are normalised to "<work>");
  * the full 0x20000-byte work page and the pinned 0x0044E000 data page that
    holds the two-column selection cycle table;
  * any emulated write outside the private work page or stack.

Coverage:
  * state +0x08: 0, 1 and every other 32-bit form, including 0x80000000;
  * state 1 script result 2 versus 0/1/3/-1/0x7FFFFFFF/0x80000000;
  * signed list count -1/0/1/0x7FFFFFFF/0x80000000 and both 0x0027F10C
    results;
  * changed flag from 0x0022FD54: 0/1/2/-1/0x80000000;
  * list index 0..9 with the list == 8 equip gate, including 0x00230D24
    zero/non-zero and 0x0028FDE0 results -1/0/1/2/0x7FFFFFFF/0x80000000;
  * selection index 0..7, 0xFFFFFFFF and 0x20000000 (32-bit stride wrap);
  * all four selection outcomes in each direction plus both no-selection
    paths (0x00256750 zero/non-zero);
  * s16 touch handles 6 versus 0/5/-1/0x7FFF/-0x8000;
  * mode byte 0/1/2/0x80/0xFF and row counts with a stub that mutates the
    re-read s16 counter between loop iterations.
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
OUT_DIR = ROOT / "build/test_leaf_003a3e98"

FUNC_ADDR = 0x003A3E98
FUNC_SIZE = 684

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # 0x0019DFBC .. 0x003A3E98 and every helper target
WORK_ADDR = 0x00600000
WORK_SIZE = 0x00020000
TABLE_ADDR = 0x0044E000
TABLE_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_19DFBC = 0x0019DFBC
STUB_2972E8 = 0x002972E8
STUB_29E8C0 = 0x0029E8C0
STUB_29F10C = 0x0029F10C
STUB_22FD54 = 0x0022FD54
STUB_22FCF8 = 0x0022FCF8
STUB_27F10C = 0x0027F10C
STUB_2337A0 = 0x002337A0
STUB_230D24 = 0x00230D24
STUB_28FDE0 = 0x0028FDE0
STUB_22FCC8 = 0x0022FCC8
STUB_29D8FC = 0x0029D8FC
STUB_22FC98 = 0x0022FC98
STUB_276550 = 0x00276550
STUB_256750 = 0x00256750
STUB_232A48 = 0x00232A48
STUB_22FBC0 = 0x0022FBC0
STUB_22E7DC = 0x0022E7DC
STUB_22FE4C = 0x0022FE4C
STUB_22FC8C = 0x0022FC8C
STUB_230F84 = 0x00230F84
STUB_2329DC = 0x002329DC
STUB_2333D4 = 0x002333D4
STUB_297128 = 0x00297128
STUB_2339E8 = 0x002339E8
STUB_2339AC = 0x002339AC
STUB_2B9008 = 0x002B9008

# Declaration name emitted by the candidate -> original call target.
RELOC_TARGETS = {
    "script_vm_func_0019dfbc": STUB_19DFBC,
    "ui_func_002972e8": STUB_2972E8,
    "camp_func_0029e8c0": STUB_29E8C0,
    "camp_func_0029f10c": STUB_29F10C,
    "shop_func_0022fd54": STUB_22FD54,
    "shop_func_0022fcf8": STUB_22FCF8,
    "script_vm_func_0027f10c": STUB_27F10C,
    "shop_func_002337a0": STUB_2337A0,
    "shop_func_00230d24": STUB_230D24,
    "shop_func_0028fde0": STUB_28FDE0,
    "shop_func_0022fcc8": STUB_22FCC8,
    "ui_func_0029d8fc": STUB_29D8FC,
    "shop_func_0022fc98": STUB_22FC98,
    "script_vm_func_00276550": STUB_276550,
    "shop_func_00256750": STUB_256750,
    "shop_func_00232a48": STUB_232A48,
    "camp_func_0022fbc0": STUB_22FBC0,
    "shop_func_0022e7dc": STUB_22E7DC,
    "shop_func_0022fe4c": STUB_22FE4C,
    "shop_func_0022fc8c": STUB_22FC8C,
    "shop_func_00230f84": STUB_230F84,
    "shop_func_002329dc": STUB_2329DC,
    "shop_func_002333d4": STUB_2333D4,
    "shop_func_00297128": STUB_297128,
    "shop_func_002339e8": STUB_2339E8,
    "shop_func_002339ac": STUB_2339AC,
    "camp_func_002b9008": STUB_2B9008,
}

STUB_NAMES = {address: name for name, address in RELOC_TARGETS.items()}

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

# Work-page offsets recovered from the ARM body.
OFF_NEXT_MODE = 0x004
OFF_STATE = 0x008
OFF_MODE_BYTE = 0x014
OFF_SCRIPT = 0x168
OFF_SPRITE_GROUP = 0x3A8
OFF_ITEM_PANEL = 0x828
OFF_MENU_OBJECT = 0x85C
OFF_LIST = 0x860
OFF_SELECTION = 0x864
OFF_LIST_BASE = 0x880
OFF_LIST_COUNT = 0x888
LIST_STRIDE = 116
OFF_ITEM_BASE = 0xC94
ITEM_LIST_STRIDE = 4098
OFF_TOUCH_FORWARD = 0x15D4C
OFF_TOUCH_BACKWARD = 0x15D4E
OFF_ROW_COUNT = 0x15D50
OFF_SUB_STATE = 0x15D60
SCRIPT_POINTER = WORK_ADDR + 0x1F000
MENU_OBJECT = WORK_ADDR + 0x1000

TABLE_COLUMN_STRIDE = 8


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def get_table_page() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(TABLE_ADDR - 0x00100000)
        return f.read(TABLE_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "003a3e98" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"shop_func_003a3e98 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        target = RELOC_TARGETS.get(rel.symbol_name)
        if target is None:
            raise RuntimeError(f"unresolved relocation: {rel.symbol_name}")
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        if target & 3:
            raise RuntimeError(f"unaligned call target 0x{target:08x}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
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


def s16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def u32_offset(value: int) -> int:
    return value & 0xFFFFFFFF


# --------------------------------------------------------------------- fixtures
def build_work(case: dict) -> bytes:
    page = bytearray(WORK_SIZE)
    # Deterministic filler so a missing explicit field cannot silently read 0.
    for offset in range(0, WORK_SIZE, 4):
        struct.pack_into("<I", page, offset, 0xA5A50000 | ((offset * 7) & 0xFFFF))

    struct.pack_into("<I", page, OFF_STATE, case.get("state", 0) & 0xFFFFFFFF)
    struct.pack_into(
        "<I", page, OFF_NEXT_MODE, case.get("next_mode", 0x87654321) & 0xFFFFFFFF
    )
    struct.pack_into("<I", page, OFF_SCRIPT, case.get("script", SCRIPT_POINTER))
    page[OFF_MODE_BYTE] = case.get("mode_byte", 0) & 0xFF
    struct.pack_into("<I", page, OFF_MENU_OBJECT, MENU_OBJECT)
    struct.pack_into(
        "<I", page, OFF_LIST, case.get("list", 0) & 0xFFFFFFFF
    )
    struct.pack_into(
        "<I", page, OFF_SELECTION, case.get("selection", 0) & 0xFFFFFFFF
    )
    struct.pack_into(
        "<I", page, OFF_SUB_STATE, case.get("sub_state", 0x12345678) & 0xFFFFFFFF
    )
    struct.pack_into(
        "<h", page, OFF_TOUCH_FORWARD, case.get("touch_forward", 0)
    )
    struct.pack_into(
        "<h", page, OFF_TOUCH_BACKWARD, case.get("touch_backward", 0)
    )
    struct.pack_into("<h", page, OFF_ROW_COUNT, case.get("row_count", 0))
    struct.pack_into("<I", page, OFF_SPRITE_GROUP, 0xDEADBEEF)
    struct.pack_into("<I", page, OFF_ITEM_PANEL, 0xFEEDFACE)

    list_index = case.get("list", 0) & 0xFFFFFFFF
    count_offset = u32_offset(OFF_LIST_COUNT + list_index * LIST_STRIDE)
    struct.pack_into("<i", page, count_offset, s32(case.get("list_count", 0)))

    entry_index = case.get("entry_index", 0) & 0xFFFFFFFF
    item_offset = u32_offset(
        OFF_ITEM_BASE + list_index * ITEM_LIST_STRIDE + entry_index * 4
    )
    struct.pack_into("<H", page, item_offset, case.get("item_id", 0x1234) & 0xFFFF)

    for offset, data in case.get("raw", {}).items():
        page[offset:offset + len(data)] = data
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
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
        self.touch_index = 0
        self.row_mutation_index = 0

    # ------------------------------------------------------------------ stubs
    @staticmethod
    def _next(sequence, index: int, default: int = 0) -> int:
        if not sequence:
            return default
        if index < len(sequence):
            return sequence[index]
        return sequence[-1]

    def _normalise(self, value: int):
        if WORK_ADDR <= value < WORK_ADDR + WORK_SIZE:
            return "<work>"
        return value

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], tuple(args)))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        case = self.case

        if address == STUB_19DFBC:
            self._log(address, self._normalise(r0))
            uc.reg_write(
                arm.UC_ARM_REG_R0, case.get("script_state", 2) & 0xFFFFFFFF
            )
        elif address == STUB_2972E8:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, r0)  # real body leaves r0 unchanged
        elif address == STUB_29E8C0:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, 1)
        elif address == STUB_29F10C:
            self._log(address, r0, r1)
        elif address == STUB_22FD54:
            self._log(address, self._normalise(r0))
            uc.reg_write(
                arm.UC_ARM_REG_R0, case.get("changed", 0) & 0xFFFFFFFF
            )
        elif address == STUB_22FCF8:
            self._log(address, self._normalise(r0))
        elif address == STUB_27F10C:
            self._log(address, s32(r0))
            uc.reg_write(
                arm.UC_ARM_REG_R0, case.get("list_change", 0) & 0xFFFFFFFF
            )
        elif address == STUB_2337A0:
            self._log(address, self._normalise(r0))
            uc.reg_write(
                arm.UC_ARM_REG_R0, case.get("entry_index", 0) & 0xFFFFFFFF
            )
        elif address == STUB_230D24:
            self._log(address, self._normalise(r0), r1)
            uc.reg_write(
                arm.UC_ARM_REG_R0, case.get("equip_match", 0) & 0xFFFFFFFF
            )
        elif address == STUB_28FDE0:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, case.get("equip_count", 0) & 0xFFFFFFFF
            )
        elif address == STUB_22FCC8:
            self._log(address)
            uc.reg_write(
                arm.UC_ARM_REG_R0, case.get("forward_result", 0) & 0xFFFFFFFF
            )
        elif address == STUB_29D8FC:
            self._log(address, s16(r0))
            index = self.touch_index
            self.touch_index += 1
            value = self._next(case.get("touch_returns", [0]), index, 0)
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        elif address == STUB_22FC98:
            self._log(address)
            uc.reg_write(
                arm.UC_ARM_REG_R0, case.get("cancel_check", 0) & 0xFFFFFFFF
            )
        elif address == STUB_276550:
            self._log(address)
            uc.reg_write(
                arm.UC_ARM_REG_R0, case.get("confirm_ready", 0) & 0xFFFFFFFF
            )
        elif address == STUB_256750:
            self._log(address)
            uc.reg_write(
                arm.UC_ARM_REG_R0, case.get("second_check", 0) & 0xFFFFFFFF
            )
        elif address == STUB_232A48:
            self._log(address)
        elif address == STUB_22FBC0:
            self._log(address, self._normalise(r0))
            uc.reg_write(arm.UC_ARM_REG_R0, case.get("tail_b", 0xB0000000))
        elif address == STUB_22E7DC:
            self._log(address, self._normalise(r0), r1)
            uc.reg_write(arm.UC_ARM_REG_R0, case.get("tail_a", 0xA0000000))
        elif address == STUB_22FE4C:
            self._log(address, self._normalise(r0), r1)
        elif address == STUB_22FC8C:
            # The real callee overwrites r0 with its own constant and ignores
            # every register argument; only its result is observable.
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, case.get("selection_tail", 0xC0000000))
        elif address == STUB_230F84:
            self._log(address, r0)
        elif address == STUB_2329DC:
            self._log(address)
        elif address == STUB_2333D4:
            self._log(address, self._normalise(r0), r1)
        elif address == STUB_297128:
            self._log(address)
        elif address == STUB_2339E8:
            self._log(address, self._normalise(r0))
        elif address == STUB_2339AC:
            self._log(address, self._normalise(r0))
        elif address == STUB_2B9008:
            self._log(address)
            sequence = case.get("row_count_after", [])
            if sequence:
                index = self.row_mutation_index
                self.row_mutation_index += 1
                value = self._next(sequence, index, sequence[-1])
                uc.mem_write(
                    WORK_ADDR + OFF_ROW_COUNT, struct.pack("<h", s16(value))
                )
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, table_page: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = dict(case)
        self.touch_index = 0
        self.row_mutation_index = 0
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(WORK_ADDR, build_work(case))
        self.uc.mem_write(TABLE_ADDR, table_page)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, WORK_ADDR)
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
        for address, size in self.writes:
            in_work = WORK_ADDR <= address < WORK_ADDR + WORK_SIZE
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not (in_work or in_stack):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "work": bytes(self.uc.mem_read(WORK_ADDR, WORK_SIZE)),
            "table": bytes(self.uc.mem_read(TABLE_ADDR, TABLE_SIZE)),
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
    for key in ("work", "table"):
        if orig[key] != cand[key]:
            first = next(
                (
                    index
                    for index, (left, right) in enumerate(zip(orig[key], cand[key]))
                    if left != right
                ),
                None,
            )
            problems.append(f"{key} differs first at +0x{first:x}")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "state": 0,
        "list": 0,
        "list_count": 0,
        "entry_index": 0,
        "item_id": 0x1234,
        "selection": 0,
        "changed": 0,
        "script_state": 2,
        "forward_result": 0,
        "cancel_check": 0,
        "confirm_ready": 0,
        "second_check": 0,
        "equip_match": 0,
        "equip_count": 0,
        "list_change": 0,
        "touch_forward": 0,
        "touch_backward": 0,
        "mode_byte": 0,
        "row_count": 0,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- phase selector: state 0, state 1 and every other form
    for state in (2, 3, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF):
        cases.append(base_case(f"state 0x{state & 0xFFFFFFFF:08x}", state=state))
    for script in (0, 1, 2, 3, -1, 0x7FFFFFFF, 0x80000000):
        cases.append(base_case(f"state 1 script {s32(script)}", state=1,
                               script_state=script))

    # --- changed flag and signed list count
    for changed in (0, 1, 2, -1, 0x80000000):
        cases.append(base_case(f"changed {s32(changed)} count 0", changed=changed))
        cases.append(base_case(f"changed {s32(changed)} count 3 list change 1",
                               changed=changed, list_count=3, list_change=1))
    for count in (-1, 0, 1, 0x7FFFFFFF, 0x80000000):
        cases.append(base_case(f"signed count {s32(count)}", list_count=count,
                               list_change=1))
        cases.append(base_case(f"signed count {s32(count)} no change",
                               list_count=count, list_change=0))

    # --- list index and the list == 8 equip gate
    for list_index in (0, 1, 7, 8, 9):
        cases.append(base_case(f"list {list_index}", list_index=list_index,
                               list_count=2, list_change=1))
    cases.append(base_case("list 8 equip no match", list=8,
                           equip_match=0, changed=1))
    for equip_count in (-1, 0, 1, 2, 0x7FFFFFFF, 0x80000000):
        cases.append(
            base_case(
                f"list 8 equip match {s32(equip_count)}",
                list=8,
                equip_match=1,
                equip_count=equip_count,
                changed=1,
            )
        )

    # --- selection index and both cycle-table columns
    for selection in (0, 1, 2, 3, 4, 7, 0xFFFFFFFF, 0x20000000):
        cases.append(base_case(f"selection {selection & 0xFFFFFFFF:08x} forward",
                               selection=selection, forward_result=1))
        cases.append(base_case(f"selection {selection & 0xFFFFFFFF:08x} backward",
                               selection=selection, cancel_check=1))

    # --- selection outcomes
    cases.append(base_case("forward by helper", forward_result=1))
    cases.append(base_case("forward by first touch", touch_forward=6,
                           touch_returns=[6]))
    cases.append(base_case("backward by helper", cancel_check=1))
    cases.append(base_case("backward by second touch", touch_backward=6,
                           touch_returns=[0, 6]))
    cases.append(base_case("activate", confirm_ready=1))
    cases.append(base_case("second check false", confirm_ready=0, second_check=0))
    cases.append(base_case("second check true", confirm_ready=0, second_check=1))
    for handle in (0, 5, 6, -1, 0x7FFF, -0x8000):
        cases.append(base_case(f"forward touch handle {handle}",
                               touch_forward=handle, touch_returns=[handle]))
        cases.append(base_case(f"backward touch handle {handle}",
                               touch_backward=handle, touch_returns=[0, handle]))

    # --- activate details: mode byte, row counter, re-read bound
    for mode in (0, 1, 2, 0x80, 0xFF):
        cases.append(base_case(f"activate mode byte 0x{mode:02x}", mode_byte=mode,
                               confirm_ready=1))
    for row_count in (-1, 0, 1, 3, 5):
        cases.append(base_case(f"activate row count {row_count}",
                               row_count=row_count, confirm_ready=1))
    cases.append(base_case("activate mutating row count 0->1->0",
                           row_count=0, row_count_after=[1, 0], confirm_ready=1))
    cases.append(base_case("activate mutating row count 2->1->0",
                           row_count=2, row_count_after=[1, 0], confirm_ready=1))
    cases.append(base_case("activate mutating row count 1->3",
                           row_count=1, row_count_after=[3, 3], confirm_ready=1))

    # --- item id and entry-index address arithmetic boundaries
    for entry_index in (0, 1, 0x20, 0xFFFFFFFF, 0x40000000):
        cases.append(
            base_case(
                f"entry index 0x{entry_index & 0xFFFFFFFF:08x}",
                entry_index=entry_index,
                item_id=0xBEEF,
                list=0,
            )
        )

    return cases


def run_case_set(orig_code, cand_code, table_page, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, table_page, case)
        cand = Runner().run(cand_code, table_page, case)
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
    print("Testing shop_func_003a3e98 (0x003a3e98)...")
    orig_code = get_orig_bytes()
    table_page = get_table_page()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(all call relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, table_page, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("opening_next_mode", "constexpr u32 kOpeningNextMode = 3;",
         "constexpr u32 kOpeningNextMode = 4;"),
        ("text_color", "constexpr u32 kTextColor = 0x323232FF;",
         "constexpr u32 kTextColor = 0x323232FE;"),
        ("selected_list", "constexpr u32 kSelectedList = 8;",
         "constexpr u32 kSelectedList = 7;"),
        ("next_list_mode", "constexpr u32 kNextListMode = 11;",
         "constexpr u32 kNextListMode = 10;"),
        ("item_table_stride", "constexpr u32 kItemTableStride = 4098;",
         "constexpr u32 kItemTableStride = 4099;"),
        ("sub_state_offset", "constexpr u32 kSubState = 0x15D60;",
         "constexpr u32 kSubState = 0x15D64;"),
        ("touch_confirm_state", "constexpr s32 kTouchConfirmState = 6;",
         "constexpr s32 kTouchConfirmState = 5;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, table_page, case)
            bad = Runner().run(mutant_code, table_page, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
