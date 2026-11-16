#!/usr/bin/env python3
"""Differential test for btlUnit_CheckPartyActive (0x001d29c8) with Unicorn ARM.

Compiles src/battle/btl_ui.cpp, extracts btlUnit_CheckPartyActive, resolves its
direct calls to deterministic stubs placed at the pinned target addresses
(0x002ae3f0 and 0x002b9364), and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * return r0, continuation PC (0x90000000), final SP, callee-saved r4-r11;
  * ordered call log (stub address, r0 argument);
  * unexpected writes outside the stack.

Coverage:
  * all three slot groups null -> 0, zero calls;
  * party_slots active at first, middle, and last slot (indices 0, 3, 7) -> 1
    with early return (no further slots, reserve_slots, or guest_unit checked);
  * party_slots with null unit pointers and non-3 statuses (0, 1, 2, 4, 0xFF)
    falling through to reserve_slots;
  * reserve_slots active at indices 0, 5, 7 -> 1 with early return;
  * guest_unit non-null with sub_party_id boundary values (0, 0x1234, 0xFFFF),
    active at indices 0, 4, 7 -> 1, and all inactive -> 0;
  * negative/mutation controls on kActiveStatus, kSlotCount,
    kPartySlotArrayOffset, kSubPartySlotArrayOffset, and kUnitStatusOffset.
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
SOURCE = ROOT / "src/battle/btl_ui.cpp"
OUT_DIR = ROOT / "build/test_leaf_001d29c8"

FUNC_ADDR = 0x001D29C8
FUNC_SIZE = 240

CODE_ADDR = 0x001C0000
CODE_SIZE = 0x00200000  # covers 0x001D29C8 and stubs up to 0x003C0000
WORK_ADDR = 0x00500000
WORK_SIZE = 0x00001000
PARTY_ADDR = 0x00510000
RESERVE_ADDR = 0x00520000
SUBPARTY_ADDR = 0x00530000
UNITS_ADDR = 0x00540000
PAGE_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2AE3F0 = 0x002AE3F0
STUB_2B9364 = 0x002B9364

STUB_NAMES = {
    STUB_2AE3F0: "battle_func_002ae3f0",
    STUB_2B9364: "camp_func_002b9364",
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
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def _stub_address(symbol_name: str) -> int | None:
    for address in STUB_NAMES:
        if f"{address:08x}" in symbol_name:
            return address
    return None


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "btlUnit_CheckPartyActive" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"btlUnit_CheckPartyActive not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = _stub_address(rel.symbol_name)
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
                f"for {rel.symbol_name!r}"
            )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "btl_ui.o"
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


class Runner:
    """One Unicorn machine with deterministic stubs at 0x002ae3f0 and 0x002b9364."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(PARTY_ADDR, PAGE_SIZE)
        self.uc.mem_map(RESERVE_ADDR, PAGE_SIZE)
        self.uc.mem_map(SUBPARTY_ADDR, PAGE_SIZE)
        self.uc.mem_map(UNITS_ADDR, PAGE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        # BX LR at each stub address
        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for addr in STUB_NAMES:
            self.uc.mem_write(addr, bx_lr)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE320F000))

        self.unit_map: dict[int, int] = {}
        self.subparty_map: dict[int, int] = {}
        self.call_log: list[tuple[int, int]] = []
        self.bad_writes: list[tuple[int, int, int]] = []

        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_stub, None, STUB_2AE3F0, STUB_2AE3F0)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_stub, None, STUB_2B9364, STUB_2B9364)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    def _on_stub(self, uc: unicorn.Uc, address: int, size: int, user_data: object) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append((address, r0))
        if address == STUB_2AE3F0:
            uc.reg_write(arm.UC_ARM_REG_R0, self.unit_map.get(r0, 0))
        elif address == STUB_2B9364:
            uc.reg_write(arm.UC_ARM_REG_R0, self.subparty_map.get(r0, SUBPARTY_ADDR))

    def _on_write(
        self,
        uc: unicorn.Uc,
        access: int,
        address: int,
        size: int,
        value: int,
        user_data: object,
    ) -> None:
        if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE):
            self.bad_writes.append((address, size, value))

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.bad_writes = []
        self.unit_map = {}
        self.subparty_map = {}

        self.uc.mem_write(FUNC_ADDR, b"\x00" * max(FUNC_SIZE, len(code) + 16))
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(STACK_ADDR, b"\xCD" * STACK_SIZE)

        work = bytearray(b"\x00" * 0x288)
        party_ptr = PARTY_ADDR if case.get("party") is not None else 0
        reserve_ptr = RESERVE_ADDR if case.get("reserve") is not None else 0
        guest_ptr = 0x00600000 if case.get("guest") else 0
        sub_party_id = case.get("sub_party_id", 0)

        struct.pack_into("<H", work, 0xCE, sub_party_id)
        struct.pack_into("<I", work, 0x278, party_ptr)
        struct.pack_into("<I", work, 0x27C, reserve_ptr)
        struct.pack_into("<I", work, 0x284, guest_ptr)
        self.uc.mem_write(WORK_ADDR, bytes(work))

        # Populate party_slots (+0x34), reserve_slots (+0x34), sub_party (+0x3C)
        party_buf = bytearray(b"\xAA" * 0x100)
        if case.get("party") is not None:
            for i, uid in enumerate(case["party"]):
                struct.pack_into("<H", party_buf, 0x34 + i * 2, uid)
        self.uc.mem_write(PARTY_ADDR, bytes(party_buf))

        reserve_buf = bytearray(b"\xBB" * 0x100)
        if case.get("reserve") is not None:
            for i, uid in enumerate(case["reserve"]):
                struct.pack_into("<H", reserve_buf, 0x34 + i * 2, uid)
        self.uc.mem_write(RESERVE_ADDR, bytes(reserve_buf))

        subparty_buf = bytearray(b"\xCC" * 0x100)
        if case.get("subparty") is not None:
            for i, uid in enumerate(case["subparty"]):
                struct.pack_into("<H", subparty_buf, 0x3C + i * 2, uid)
        self.uc.mem_write(SUBPARTY_ADDR, bytes(subparty_buf))
        self.subparty_map[sub_party_id] = SUBPARTY_ADDR

        # Populate unit structs at UNITS_ADDR + idx * 0x40
        units_buf = bytearray(b"\x00" * PAGE_SIZE)
        for idx, (uid, status) in enumerate(case.get("units", {}).items()):
            if status is None:
                self.unit_map[uid] = 0
            else:
                unit_addr = UNITS_ADDR + idx * 0x40
                units_buf[idx * 0x40 + 0x23] = status & 0xFF
                self.unit_map[uid] = unit_addr
        self.uc.mem_write(UNITS_ADDR, bytes(units_buf))

        self.uc.reg_write(arm.UC_ARM_REG_R0, WORK_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for name, reg in CALLEE_SAVED.items():
            self.uc.reg_write(reg, CALLEE_SAVED_START[name])

        self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000, count=200_000)

        return {
            "r0": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()},
            "calls": list(self.call_log),
            "bad_writes": list(self.bad_writes),
        }


def build_cases() -> list[dict]:
    return [
        {"name": "all_null", "party": None, "reserve": None, "guest": False},
        {
            "name": "party_slot0_active",
            "party": [10, 11, 12, 13, 14, 15, 16, 17],
            "reserve": [20, 21, 22, 23, 24, 25, 26, 27],
            "guest": True,
            "sub_party_id": 1,
            "subparty": [30, 31, 32, 33, 34, 35, 36, 37],
            "units": {10: 3, 20: 3, 30: 3},
        },
        {
            "name": "party_slot3_active",
            "party": [10, 11, 12, 13, 14, 15, 16, 17],
            "reserve": [20, 21, 22, 23, 24, 25, 26, 27],
            "guest": True,
            "sub_party_id": 2,
            "subparty": [30, 31, 32, 33, 34, 35, 36, 37],
            "units": {10: None, 11: 0, 12: 2, 13: 3},
        },
        {
            "name": "party_slot7_active",
            "party": [10, 11, 12, 13, 14, 15, 16, 17],
            "reserve": None,
            "guest": False,
            "units": {10: 0, 11: 1, 12: 2, 13: 4, 14: 0xFF, 15: None, 16: 1, 17: 3},
        },
        {
            "name": "party_inactive_reserve_slot0_active",
            "party": [10, 11, 12, 13, 14, 15, 16, 17],
            "reserve": [20, 21, 22, 23, 24, 25, 26, 27],
            "guest": True,
            "sub_party_id": 5,
            "subparty": [30, 31, 32, 33, 34, 35, 36, 37],
            "units": {10: 1, 11: 2, 12: 4, 20: 3},
        },
        {
            "name": "party_null_reserve_slot7_active",
            "party": None,
            "reserve": [20, 21, 22, 23, 24, 25, 26, 27],
            "guest": True,
            "sub_party_id": 9,
            "subparty": [30, 31, 32, 33, 34, 35, 36, 37],
            "units": {20: 0, 21: 2, 22: 4, 23: None, 24: 1, 25: 2, 26: 0xFF, 27: 3},
        },
        {
            "name": "guest_slot0_active",
            "party": [10, 11, 12, 13, 14, 15, 16, 17],
            "reserve": [20, 21, 22, 23, 24, 25, 26, 27],
            "guest": True,
            "sub_party_id": 0x1234,
            "subparty": [30, 31, 32, 33, 34, 35, 36, 37],
            "units": {30: 3},
        },
        {
            "name": "guest_slot7_active_max_id",
            "party": None,
            "reserve": None,
            "guest": True,
            "sub_party_id": 0xFFFF,
            "subparty": [30, 31, 32, 33, 34, 35, 36, 37],
            "units": {30: None, 31: 0, 32: 2, 33: 4, 34: 1, 35: 5, 36: 0xFE, 37: 3},
        },
        {
            "name": "all_inactive_with_guest",
            "party": [10, 11, 12, 13, 14, 15, 16, 17],
            "reserve": [20, 21, 22, 23, 24, 25, 26, 27],
            "guest": True,
            "sub_party_id": 0,
            "subparty": [30, 31, 32, 33, 34, 35, 36, 37],
            "units": {10: 2, 20: 4, 30: 1, 37: 2},
        },
    ]


def compare_outputs(name: str, orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("r0", "pc", "sp", "callee", "calls", "bad_writes"):
        if orig[key] != cand[key]:
            diffs.append(f"{name}: {key} orig={orig[key]!r} cand={cand[key]!r}")
    if cand["sp"] != ENTRY_SP:
        diffs.append(f"{name}: sp not restored: {cand['sp']:#x}")
    if cand["callee"] != CALLEE_SAVED_START:
        diffs.append(f"{name}: callee-saved clobbered: {cand['callee']!r}")
    if cand["bad_writes"]:
        diffs.append(f"{name}: unexpected writes: {cand['bad_writes']!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()

    orig_runner = Runner()
    cand_runner = Runner()
    cases = build_cases()

    for case in cases:
        orig_res = orig_runner.run(orig_bytes, case)
        cand_res = cand_runner.run(cand_bytes, case)
        diffs = compare_outputs(case["name"], orig_res, cand_res)
        if diffs:
            for d in diffs:
                print("FAIL:", d)
            return 1

    mutants = [
        ("status_value", "kActiveStatus = 3;", "kActiveStatus = 4;"),
        ("slot_count", "kSlotCount = 8;", "kSlotCount = 7;"),
        ("party_offset", "kPartySlotArrayOffset = 0x34;", "kPartySlotArrayOffset = 0x36;"),
        ("subparty_offset", "kSubPartySlotArrayOffset = 0x3C;", "kSubPartySlotArrayOffset = 0x3E;"),
        ("unit_status_offset", "kUnitStatusOffset = 0x23;", "kUnitStatusOffset = 0x22;"),
    ]
    for m_name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(m_name, old, new)
        mut_runner = Runner()
        detected = False
        for case in cases:
            orig_res = orig_runner.run(orig_bytes, case)
            mut_res = mut_runner.run(mut_bytes, case)
            if compare_outputs(case["name"], orig_res, mut_res):
                detected = True
                break
        if not detected:
            print(f"FAIL: mutant {m_name} was not detected")
            return 1

    print(
        f"PASS: btlUnit_CheckPartyActive (0x001d29c8) matched original across "
        f"{len(cases)} cases and detected {len(mutants)}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
