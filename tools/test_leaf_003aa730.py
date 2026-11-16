#!/usr/bin/env python3
"""Differential test for shop_func_003aa730 (0x003AA730) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the shop_func_003aa730 body,
resolves every direct call to a deterministic stub at the original target
address, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log with every meaningful register argument;
  * the full work page, including the direct stores and the modelled helper
    effects (0x003AAD98 zeroes the flag bytes, 0x0022DF7C appends ids,
    0x003AADB0 sanitises the id array, 0x002313D4 stores two floats);
  * any emulated write outside the private work page or stack.

There are no stack-passed helper arguments in this function; every helper takes
at most four register arguments.

Coverage: both state paths (state == 4 and every other value), empty and
non-empty pick lists, both 0x002337A0 lookups sampled independently, zero and
non-zero entry flags, zero/high-bit ids, 0x0029E398 zero and non-zero returns,
equal and different active ids, signed row bounds 0x80000000/0xFFFFFFFF,
negative/zero/positive visible counts, wrap-around entry indices, the state-4
status gate (0x0026C8A8/0x00293D50/0x00293E30), 0x0029E2B0 transition direction,
row-change detection through both 0x0029EBC4 and 0x00240E8C, and s16 cursor
boundaries -0x8000/-1/0/8/0x7FFF including the post-helper re-read.
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
OUT_DIR = ROOT / "build/test_leaf_003aa730"

FUNC_ADDR = 0x003AA730
FUNC_SIZE = 620

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every target below 0x3F0000
WORK_ADDR = 0x00600000
WORK_SIZE = 0x00010000
WORK_BIAS = 0x800                  # r0 - WORK_ADDR
WORK_BASE = WORK_ADDR + WORK_BIAS  # r0 passed to the function
CHILD_ADDR = 0x00700000
CHILD_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_3A9AD8 = 0x003A9AD8
STUB_2337A0 = 0x002337A0
STUB_29E398 = 0x0029E398
STUB_29E19C = 0x0029E19C
STUB_29D924 = 0x0029D924
STUB_3AAD98 = 0x003AAD98
STUB_3AADB0 = 0x003AADB0
STUB_2338AC = 0x002338AC
STUB_29EBC4 = 0x0029EBC4
STUB_22DF7C = 0x0022DF7C
STUB_2334D8 = 0x002334D8
STUB_2BEF70 = 0x002BEF70
STUB_2BEF7C = 0x002BEF7C
STUB_2313D4 = 0x002313D4
STUB_2333D4 = 0x002333D4
STUB_29E2B0 = 0x0029E2B0
STUB_3C2D9C = 0x003C2D9C
STUB_3C2E94 = 0x003C2E94
STUB_233598 = 0x00233598
STUB_240E8C = 0x00240E8C
STUB_29E260 = 0x0029E260
STUB_26C8A8 = 0x0026C8A8
STUB_293D50 = 0x00293D50
STUB_293E30 = 0x00293E30

# Declaration name emitted by the candidate -> original call target.
RELOC_TARGETS = {
    "camp_func_003a9ad8": STUB_3A9AD8,
    "shop_func_002337a0": STUB_2337A0,
    "script_vm_func_0029e398": STUB_29E398,
    "camp_func_0029e19c": STUB_29E19C,
    "camp_func_0029d924": STUB_29D924,
    "func_003aad98": STUB_3AAD98,
    "func_003aadb0": STUB_3AADB0,
    "unite_func_002338ac": STUB_2338AC,
    "shop_func_0029ebc4": STUB_29EBC4,
    "unite_func_0022df7c": STUB_22DF7C,
    "shop_func_002334d8": STUB_2334D8,
    "shop_func_002bef70": STUB_2BEF70,
    "ui_func_002bef7c": STUB_2BEF7C,
    "shop_func_002313d4": STUB_2313D4,
    "shop_func_002333d4": STUB_2333D4,
    "camp_func_0029e2b0": STUB_29E2B0,
    "camp_func_003c2d9c": STUB_3C2D9C,
    "camp_func_003c2e94": STUB_3C2E94,
    "engine_func_00233598": STUB_233598,
    "shop_func_00240e8c": STUB_240E8C,
    "camp_func_0029e260": STUB_29E260,
    "Status_GetFlag1E63": STUB_26C8A8,
    "StatusDown_GetActiveMode": STUB_293D50,
    "StatusDown_GetStatusMode": STUB_293E30,
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

# Work-page offsets from the decoded function.
OFF_STATE = 0x14
OFF_STATE_AUX = 0x18
OFF_RESULT_COUNT = 0x28
OFF_SELECTED_IDS = 0x96
OFF_PICK_LIST = 0x5A8
OFF_ACTIVE_ID = 0xA5B0
OFF_CURSOR = 0xA5B2
OFF_A6BE = 0xA6BE
ENTRY_STRIDE = 0x20
SLOT_BASE = 0xFC
SLOT_STRIDE = 140


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "003aa730" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"shop_func_003aa730 not found in {obj_file}: {sorted(funcs)}"
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


# --------------------------------------------------------------------- fixtures
def build_work(case: dict) -> bytes:
    page = bytearray(WORK_SIZE)
    struct.pack_into("<I", page, WORK_BIAS + OFF_STATE, case.get("state", 0) & 0xFFFFFFFF)
    struct.pack_into(
        "<I", page, WORK_BIAS + OFF_STATE_AUX, case.get("state_aux", 0x99999999) & 0xFFFFFFFF
    )
    struct.pack_into(
        "<I", page, WORK_BIAS + OFF_RESULT_COUNT, case.get("result_count", 0) & 0xFFFFFFFF
    )
    page[WORK_BIAS + OFF_A6BE] = case.get("a6be_seed", 0x11) & 0xFF
    struct.pack_into(
        "<H", page, WORK_BIAS + OFF_PICK_LIST, case.get("list_count", 0) & 0xFFFF
    )
    struct.pack_into(
        "<H", page, WORK_BIAS + OFF_ACTIVE_ID, case.get("active_id", 0) & 0xFFFF
    )
    struct.pack_into("<H", page, WORK_BIAS + OFF_CURSOR, case.get("cursor", 0) & 0xFFFF)

    # Default list entries 0..31 are distinct and visible; the case overrides
    # individual (id, flag) pairs.
    entries = {index: (0x2000 + index, 1) for index in range(32)}
    entries.update(case.get("entries", {}))
    for index, (entry_id, flag) in entries.items():
        struct.pack_into(
            "<H", page, WORK_BIAS + OFF_PICK_LIST + index * ENTRY_STRIDE + 4,
            entry_id & 0xFFFF,
        )
        page[WORK_BIAS + OFF_PICK_LIST + index * ENTRY_STRIDE + 0x1C] = flag & 0xFF

    # Distinct selected-id / flag sentinels so the helper effects are visible.
    for index in range(16):
        struct.pack_into("<H", page, WORK_BIAS + OFF_SELECTED_IDS + index * 2,
                         0x5000 + index)
        page[WORK_BIAS + OFF_SELECTED_IDS + 0x20 + index] = 0x30 + index

    # 140-byte cursor sprite records; +0x10 feeds 0x2BEF70 and +0x0C points at
    # a child word that feeds 0x2BEF7C.
    for index, (pos_value, _unused) in build_slot_values().items():
        record = WORK_BIAS + SLOT_BASE + index * SLOT_STRIDE
        struct.pack_into("<i", page, record + 0x10, pos_value)
        struct.pack_into(
            "<I", page, record + 0x0C, CHILD_ADDR + (index + 8) * 0x40
        )

    if "raw" in case:
        for offset, data in case["raw"].items():
            page[offset:offset + len(data)] = data
    return bytes(page)


def build_children() -> bytes:
    page = bytearray(CHILD_SIZE)
    for index in range(-8, 17):
        base = (index + 8) * 0x40
        struct.pack_into("<i", page, base + 0x0C, -0x00234567 + index * 0x800)
    return bytes(page)


def build_slot_values() -> dict:
    values = {}
    for index in range(-8, 17):
        values[index] = (
            (0x00123456 + index * 0x1000) & 0xFFFFFFFF,
            0x0000C000,
        )
    return values


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(CHILD_ADDR, CHILD_SIZE)
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
        self.slot_values = build_slot_values()
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    @staticmethod
    def _next(sequence, index: int, default: int = 0) -> int:
        if not sequence:
            return default
        if index < len(sequence):
            return sequence[index]
        return sequence[-1]

    def _read_u8(self, address: int) -> int:
        raw = self.uc.mem_read(address, 1)
        return raw[0]

    def _read_s16(self, address: int) -> int:
        return struct.unpack("<h", self.uc.mem_read(address, 2))[0]

    def _read_u32(self, address: int) -> int:
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def _safe_u32(self, address: int) -> int:
        try:
            return self._read_u32(address)
        except unicorn.UcError:
            return ((address * 0x9E3779B1) ^ 0x5A5A5A5A) & 0xFFFFFFFF

    def _safe_s32(self, address: int) -> int:
        value = self._safe_u32(address)
        return value - (1 << 32) if value & 0x80000000 else value

    def _read_cursor(self) -> int:
        return self._read_s16(WORK_BASE + OFF_CURSOR)

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

        if address == STUB_3A9AD8:
            self._log(address, r0)
        elif address == STUB_2337A0:
            self._log(address, r0)
            index = case.setdefault("_accessor_index", 0)
            value = self._next(case.get("accessor_returns", [1]), index, 1)
            case["_accessor_index"] = index + 1
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        elif address == STUB_29E398:
            # 0x0029E398 ignores r0; only the boolean result is meaningful.
            self._log(address)
            uc.reg_write(
                arm.UC_ARM_REG_R0, case.get("script_vm_return", 1) & 0xFFFFFFFF
            )
        elif address == STUB_29E19C:
            self._log(address, r0, r1)
        elif address == STUB_29D924:
            self._log(address, r0)
        elif address == STUB_3AAD98:
            self._log(address, r0)
            # Real body: four word stores at +0x20, +0x24, +0x28, +0x2C.
            uc.mem_write(r0 + 0x20, struct.pack("<IIII", 0, 0, 0, 0))
        elif address == STUB_3AADB0:
            self._log(address, r0)
            # Real body: 16-slot sanitise of the ids/flags arrays.
            for index in range(16):
                value = self._read_s16(r0 + index * 2)
                if value == -1 or value == 0:
                    continue
                if self._read_u8(r0 + 0x20 + index) == 0:
                    uc.mem_write(r0 + index * 2, struct.pack("<h", -1))
            uc.reg_write(arm.UC_ARM_REG_R0, r0)  # r0 is preserved by the tail
        elif address == STUB_2338AC:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, case.get("visible_return", 0) & 0xFFFFFFFF
            )
        elif address == STUB_29EBC4:
            self._log(address, r0)
            index = case.setdefault("_row_index", 0)
            value = self._next(case.get("row_returns", [0]), index, 0)
            case["_row_index"] = index + 1
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        elif address == STUB_22DF7C:
            self._log(address, r0, r1)
            index = case.setdefault("_append_index", 0)
            case["_append_index"] = index + 1
            if r1 != 0 and index < 16:
                uc.mem_write(r0 + index * 2, struct.pack("<H", r1 & 0xFFFF))
                uc.mem_write(r0 + 0x20 + index, bytes([1]))
        elif address == STUB_2334D8:
            self._log(address, r0, r1)
            if case.get("advance_cursor", False):
                uc.mem_write(
                    WORK_BASE + OFF_CURSOR,
                    struct.pack("<H", (r1 + 1) & 0xFFFF),
                )
        elif address == STUB_2BEF70:
            self._log(address, r0)
            value = self._safe_s32(r0 + 0x10) >> 12
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        elif address == STUB_2BEF7C:
            self._log(address, r0)
            child = self._safe_u32(r0 + 0x0C)
            value = self._safe_s32(child + 0x0C) >> 12
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        elif address == STUB_2313D4:
            self._log(address, r0, r1, r2)
            uc.mem_write(r0, struct.pack("<ff", float(r1), float(r2)))
        elif address == STUB_2333D4:
            self._log(address, r0, r1)
        elif address == STUB_29E2B0:
            self._log(address)
            uc.reg_write(
                arm.UC_ARM_REG_R0, case.get("transition_dir", 0) & 0xFFFFFFFF
            )
        elif address == STUB_3C2D9C:
            self._log(address, r0)
        elif address == STUB_3C2E94:
            self._log(address, r0)
        elif address == STUB_233598:
            self._log(address)
        elif address == STUB_240E8C:
            self._log(address, r0)
            index = case.setdefault("_second_row_index", 0)
            value = self._next(case.get("second_row_returns", [0]), index, 0)
            case["_second_row_index"] = index + 1
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        elif address == STUB_29E260:
            self._log(address, r0)
        elif address == STUB_26C8A8:
            self._log(address)
            index = case.setdefault("_flag_index", 0)
            value = self._next(case.get("flag_returns", [0]), index, 0)
            case["_flag_index"] = index + 1
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        elif address == STUB_293D50:
            self._log(address)
            index = case.setdefault("_active_mode_index", 0)
            value = self._next(case.get("active_mode_returns", [0]), index, 0)
            case["_active_mode_index"] = index + 1
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        elif address == STUB_293E30:
            self._log(address)
            index = case.setdefault("_status_mode_index", 0)
            value = self._next(case.get("status_mode_returns", [0]), index, 0)
            case["_status_mode_index"] = index + 1
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = dict(case)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(WORK_ADDR, build_work(case))
        self.uc.mem_write(CHILD_ADDR, build_children())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, WORK_BASE)
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
    if orig["work"] != cand["work"]:
        first = next(
            (
                index
                for index, (left, right) in enumerate(
                    zip(orig["work"], cand["work"])
                )
                if left != right
            ),
            None,
        )
        problems.append(f"work page differs first at offset {first}")
    if orig["unexpected_writes"] != cand["unexpected_writes"]:
        problems.append(
            "unexpected writes:\n    orig="
            + repr(orig["unexpected_writes"])
            + "\n    cand="
            + repr(cand["unexpected_writes"])
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "state": 0,
        "state_aux": 0x99999999,
        "a6be_seed": 0x11,
        "list_count": 0,
        "active_id": 0,
        "cursor": 0,
        "result_count": 0,
        "script_vm_return": 1,
        "accessor_returns": [1],
        "visible_return": 0,
        "row_returns": [0],
        "second_row_returns": [0],
        "flag_returns": [0],
        "active_mode_returns": [0],
        "status_mode_returns": [0],
        "transition_dir": 0,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- selection pass (state != 4) --------------------------------------
    cases.append(base_case("empty list, state 0"))
    cases.append(base_case("empty list, state 5", state=5))
    cases.append(
        base_case(
            "empty list marks the 0xA6BE byte",
            a6be_seed=0x00,
            state=1,
        )
    )
    cases.append(
        base_case(
            "non-empty list, id changes",
            state=0,
            list_count=3,
            accessor_returns=[1, 1],
            entries={1: (0x1234, 1)},
            active_id=0,
            visible_return=2,
            row_returns=[0],
        )
    )
    cases.append(
        base_case(
            "non-empty list, id already active",
            list_count=3,
            accessor_returns=[1, 1],
            entries={1: (0x1234, 1)},
            active_id=0x1234,
            visible_return=2,
            row_returns=[0],
        )
    )
    cases.append(
        base_case(
            "entry flag zero selects id 0",
            list_count=3,
            accessor_returns=[1, 1],
            entries={1: (0x1234, 0)},
            active_id=0x4444,
            visible_return=1,
            row_returns=[0],
        )
    )
    cases.append(
        base_case(
            "zero id with zero active id still notifies",
            list_count=3,
            accessor_returns=[2, 2],
            entries={2: (0x7777, 0)},
            active_id=0,
            visible_return=0,
        )
    )
    cases.append(
        base_case(
            "0x29E398 zero skips the store",
            list_count=3,
            accessor_returns=[1, 1],
            entries={1: (0x1234, 1)},
            active_id=0x1111,
            script_vm_return=0,
        )
    )
    cases.append(
        base_case(
            "two accessor calls use independent indices",
            list_count=5,
            accessor_returns=[4, 0],
            entries={4: (0xABCD, 1), 0: (0x1111, 0)},
            active_id=0x2222,
            visible_return=0,
        )
    )
    cases.append(
        base_case(
            "high-bit id sign-extends into 0x29E19C",
            list_count=2,
            accessor_returns=[1, 1],
            entries={1: (0x8000, 1)},
            active_id=0,
            visible_return=0,
        )
    )
    cases.append(
        base_case(
            "id 0xFFFF sign-extends to -1",
            list_count=2,
            accessor_returns=[1, 1],
            entries={1: (0xFFFF, 1)},
            active_id=0,
            visible_return=0,
        )
    )
    cases.append(
        base_case(
            "active id 0xFFFF equals candidate id",
            list_count=2,
            accessor_returns=[1, 1],
            entries={1: (0xFFFF, 1)},
            active_id=0xFFFF,
            visible_return=0,
        )
    )

    # --- visible-count loop bounds ----------------------------------------
    for name, visible in (
        ("negative", -1),
        ("zero", 0),
        ("one", 1),
        ("three", 3),
        ("all-ones", 0xFFFFFFFF),
        ("signed-minimum", 0x80000000),
    ):
        cases.append(
            base_case(
                f"visible count {name}",
                list_count=8,
                accessor_returns=[1, 1],
                entries={1: (0x0101, 1)},
                active_id=0x0101,
                visible_return=visible,
                row_returns=[0],
            )
        )

    # --- per-iteration row values, including unsigned wrap ----------------
    for name, rows in (
        ("zero", [0]),
        ("one", [1]),
        ("two", [2]),
        ("negative", [-1]),
        ("wrap", [0xFFFFFFFF]),
        ("changing", [0, 1, 2]),
    ):
        cases.append(
            base_case(
                f"row value {name}",
                list_count=8,
                accessor_returns=[1, 1],
                entries={1: (0x0202, 1)},
                active_id=0x0202,
                visible_return=3 if name == "changing" else 2,
                row_returns=rows,
            )
        )

    # --- state-4 status gate ----------------------------------------------
    cases.append(
        base_case(
            "state 4, status flag zero, row values unchanged",
            state=4,
            list_count=0,
            flag_returns=[0],
            result_count=1,
            row_returns=[3, 3],
            second_row_returns=[4, 4],
            status_mode_returns=[1],
            cursor=0,
        )
    )
    cases.append(
        base_case(
            "state 4, status flag non-zero, active mode zero -> reset (dir 1)",
            state=4,
            list_count=0,
            flag_returns=[1],
            active_mode_returns=[0],
            transition_dir=1,
            cursor=5,
        )
    )
    cases.append(
        base_case(
            "state 4, status flag non-zero, active mode zero -> reset (dir 0)",
            state=4,
            list_count=0,
            flag_returns=[1],
            active_mode_returns=[0],
            transition_dir=0,
            cursor=5,
        )
    )
    cases.append(
        base_case(
            "state 4, second status flag non-zero -> loop head",
            state=4,
            list_count=0,
            flag_returns=[1, 1],
            active_mode_returns=[1],
            result_count=0,
        )
    )
    cases.append(
        base_case(
            "state 4, second status flag zero, result count zero",
            state=4,
            list_count=0,
            flag_returns=[1, 0],
            active_mode_returns=[1],
            result_count=0,
        )
    )
    cases.append(
        base_case(
            "state 4, result count negative",
            state=4,
            list_count=0,
            flag_returns=[0],
            result_count=0x80000000,
        )
    )
    cases.append(
        base_case(
            "state 4, result count positive",
            state=4,
            list_count=0,
            flag_returns=[0],
            result_count=0x7FFFFFFF,
            status_mode_returns=[1],
            row_returns=[5, 5],
            second_row_returns=[6, 6],
        )
    )
    cases.append(
        base_case(
            "state 4, status mode 1 calls 0x3C2D9C",
            state=4,
            flag_returns=[1, 0],
            active_mode_returns=[1],
            result_count=1,
            status_mode_returns=[1],
            row_returns=[7, 7],
            second_row_returns=[8, 8],
        )
    )
    cases.append(
        base_case(
            "state 4, status mode -1 calls 0x3C2E94",
            state=4,
            flag_returns=[1, 0],
            active_mode_returns=[1],
            result_count=1,
            status_mode_returns=[0, -1],
            row_returns=[9, 9],
            second_row_returns=[10, 10],
        )
    )
    cases.append(
        base_case(
            "state 4, no status helper call",
            state=4,
            flag_returns=[1, 0],
            active_mode_returns=[1],
            result_count=1,
            status_mode_returns=[0, 0],
            row_returns=[11, 11],
            second_row_returns=[12, 12],
        )
    )
    cases.append(
        base_case(
            "state 4, first row changes -> 0x233598",
            state=4,
            flag_returns=[0],
            result_count=1,
            status_mode_returns=[0, 0],
            row_returns=[13, 14],
            second_row_returns=[15, 15],
        )
    )
    cases.append(
        base_case(
            "state 4, only second row changes -> 0x233598",
            state=4,
            flag_returns=[0],
            result_count=1,
            status_mode_returns=[0, 0],
            row_returns=[16, 16],
            second_row_returns=[17, 18],
        )
    )
    cases.append(
        base_case(
            "state 4 output enters the selection pass",
            state=4,
            list_count=2,
            accessor_returns=[1, 1],
            entries={1: (0x3333, 1)},
            active_id=0,
            visible_return=1,
            row_returns=[19, 19, 0],
            second_row_returns=[20, 20],
            flag_returns=[0],
        )
    )

    # --- cursor / record-pointer coverage ---------------------------------
    for cursor in (0, 1, 8, 0x7FFF, 0x8000, 0xFFFF):
        cases.append(
            base_case(
                f"state 4 cursor 0x{cursor:04x}",
                state=4,
                flag_returns=[0],
                result_count=1,
                row_returns=[21, 21],
                second_row_returns=[22, 22],
                status_mode_returns=[0],
                cursor=cursor,
            )
        )
    cases.append(
        base_case(
            "state 4 cursor re-read after 0x2334D8",
            state=4,
            flag_returns=[0],
            result_count=1,
            row_returns=[23, 23],
            second_row_returns=[24, 24],
            status_mode_returns=[0],
            cursor=3,
            advance_cursor=True,
        )
    )

    # --- state reset boundary and byte/word widths ------------------------
    cases.append(
        base_case(
            "state 4 -> reset writes state 5 and cursor 0",
            state=4,
            list_count=0,
            flag_returns=[1],
            active_mode_returns=[0],
            transition_dir=1,
            state_aux=0xDEADBEEF,
        )
    )
    cases.append(
        base_case(
            "state 4 -> reset writes state 5 and cursor 4",
            state=4,
            list_count=0,
            flag_returns=[1],
            active_mode_returns=[0],
            transition_dir=-1,
            state_aux=0xDEADBEEF,
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
    print("Testing shop_func_003aa730 (0x003AA730)...")
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
        ("entry_byte", "kByteFlagA6BE = 0xA6BE;", "kByteFlagA6BE = 0xA6BF;"),
        ("active_id", "kActiveId = 0xA5B0;", "kActiveId = 0xA5B2;"),
        ("entry_stride", "kPickEntryStride = 0x20;", "kPickEntryStride = 0x10;"),
        ("state_compare", "kStateCursorMode = 4;", "kStateCursorMode = 5;"),
        ("entry_flag", "kPickEntryFlag = 0x1C;", "kPickEntryFlag = 0x18;"),
        ("slot_stride", "kSlotStride = 140;", "kSlotStride = 144;"),
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
