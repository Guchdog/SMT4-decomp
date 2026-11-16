#!/usr/bin/env python3
"""Differential test for btlTalkCommand_func_00318770 (0x00318770) with Unicorn ARM.

Compiles src/battle/battle_extras.cpp, extracts btlTalkCommand_func_00318770,
resolves its direct calls against the pinned target addresses, and runs the
pinned original (extracted/exefs/code.bin) against the candidate in separate
Unicorn machines with identical fixtures.

Compared outputs:
  * return r0 (1), continuation PC (0x90000000), final SP, callee-saved r4-r11;
  * ordered call log (stub address, register/stack arguments);
  * unexpected writes outside the candidate buffer and stack.

Coverage:
  * fast-path direct target selection (target_id != 0, flag 0x400 set,
    target_lv <= talk_state[0x76], check_unit == 0) -> commits target_id;
  * script_vm_func_00297004(min_lv) <= 0 -> commits -1 and frees buffer;
  * full scan over 1..0x4B0 with 0 matching candidates -> commits -1;
  * full scan with multiple matching candidates -> selects via Random_Range
    and commits chosen signed halfword;
  * min_lv clamping (max_lv < 20 -> half=10, min_lv <= 0 -> clamped to 1);
  * negative/mutation controls on kUnitFlagMask, kMaxEntryId, kCandidateBufSize,
    half-level clamping, and `target_unit[2] <= talk_state[0x76]`.
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
SOURCE = ROOT / "src/battle/battle_extras.cpp"
OUT_DIR = ROOT / "build/test_leaf_00318770"

FUNC_ADDR = 0x00318770
FUNC_SIZE = 516

CODE_ADDR = 0x00240000
CODE_SIZE = 0x00100000  # covers 0x0024EC64..0x00318974
BASE_UNIT_ADDR = 0x00500000
TARGET_UNIT_ADDR = 0x00501000
TALK_STATE_ADDR = 0x00502000
CAND_BUF_ADDR = 0x00510000
ENTRIES_ADDR = 0x00520000
UNITS_ADDR = 0x00540000
PAGE_SIZE = 0x00001000
ENTRIES_SIZE = 0x00010000
UNITS_SIZE = 0x00020000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_296F60 = 0x00296F60
STUB_2B087C = 0x002B087C
STUB_2B9364 = 0x002B9364
STUB_2B66EC = 0x002B66EC
STUB_24EC64 = 0x0024EC64
STUB_28DF54 = 0x0028DF54
STUB_2C4B84 = 0x002C4B84
STUB_297004 = 0x00297004
STUB_2BD25C = 0x002BD25C
STUB_2C0BCC = 0x002C0BCC
STUB_2C4360 = 0x002C4360

STUB_NAMES = {
    STUB_296F60: "script_vm_func_00296f60",
    STUB_2B087C: "battle_func_002b087c",
    STUB_2B9364: "camp_func_002b9364",
    STUB_2B66EC: "script_vm_func_002b66ec",
    STUB_24EC64: "battle_func_0024ec64",
    STUB_28DF54: "camp_func_0028df54",
    STUB_2C4B84: "engine_func_002c4b84",
    STUB_297004: "script_vm_func_00297004",
    STUB_2BD25C: "camp_func_002bd25c",
    STUB_2C0BCC: "engine_func_002c0bcc",
    STUB_2C4360: "engine_func_002c4360",
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
        if "btlTalkCommand_func_00318770" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"btlTalkCommand_func_00318770 not found in {obj_file}: {sorted(funcs)}"
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
    obj_file = OUT_DIR / "battle_extras.o"
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
    """One Unicorn machine with deterministic stubs for btlTalkCommand_func_00318770."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(BASE_UNIT_ADDR, PAGE_SIZE)
        self.uc.mem_map(TARGET_UNIT_ADDR, PAGE_SIZE)
        self.uc.mem_map(TALK_STATE_ADDR, PAGE_SIZE)
        self.uc.mem_map(CAND_BUF_ADDR, PAGE_SIZE)
        self.uc.mem_map(ENTRIES_ADDR, ENTRIES_SIZE)
        self.uc.mem_map(UNITS_ADDR, UNITS_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for addr in STUB_NAMES:
            self.uc.mem_write(addr, bx_lr)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE320F000))

        self.case: dict = {}
        self.call_log: list[tuple] = []
        self.bad_writes: list[tuple[int, int, int]] = []

        for addr in STUB_NAMES:
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_stub, None, addr, addr)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    def _on_stub(
        self, uc: unicorn.Uc, address: int, size: int, user_data: object
    ) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        sp = uc.reg_read(arm.UC_ARM_REG_SP)

        if address == STUB_296F60:
            self.call_log.append((address, r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["base_id"])
        elif address == STUB_2B087C:
            if r0 == self.case["base_id"]:
                uc.reg_write(arm.UC_ARM_REG_R0, BASE_UNIT_ADDR)
            elif r0 == self.case["target_id"] and not self.case.get("in_loop"):
                uc.reg_write(arm.UC_ARM_REG_R0, TARGET_UNIT_ADDR if self.case["target_nonnull"] else 0)
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, UNITS_ADDR + r0 * 0x20)
        elif address == STUB_2B9364:
            if r0 == 1:
                self.case["in_loop"] = True
            uc.reg_write(arm.UC_ARM_REG_R0, ENTRIES_ADDR + r0 * 0x10)
        elif address == STUB_2B66EC:
            self.call_log.append((address,))
            uc.reg_write(arm.UC_ARM_REG_R0, TALK_STATE_ADDR)
        elif address == STUB_24EC64:
            self.call_log.append((address, r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("check_ret", {}).get(r0, 1))
        elif address == STUB_28DF54:
            self.call_log.append((address, struct.unpack("<i", struct.pack("<I", r0))[0]))
        elif address == STUB_2C4B84:
            stack_args = struct.unpack("<1I", self.uc.mem_read(sp, 4))
            self.call_log.append((address, r0, r1, r2, r3, stack_args))
            uc.reg_write(arm.UC_ARM_REG_R0, CAND_BUF_ADDR)
        elif address == STUB_297004:
            self.call_log.append((address, struct.unpack("<i", struct.pack("<I", r0))[0]))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["visible_ret"])
        elif address == STUB_2BD25C:
            self.call_log.append((address, r0))
        elif address == STUB_2C0BCC:
            self.call_log.append((address, r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("rand_idx", 0))
        elif address == STUB_2C4360:
            self.call_log.append((address, r0))

    def _on_write(
        self,
        uc: unicorn.Uc,
        access: int,
        address: int,
        size: int,
        value: int,
        user_data: object,
    ) -> None:
        allowed = (
            (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
            or (CAND_BUF_ADDR <= address < CAND_BUF_ADDR + 0x962)
        )
        if not allowed:
            self.bad_writes.append((address, size, value))

    def run(self, code: bytes, case: dict) -> dict:
        self.case = dict(case)
        self.case["in_loop"] = False
        self.call_log = []
        self.bad_writes = []

        self.uc.mem_write(FUNC_ADDR, b"\x00" * max(FUNC_SIZE, len(code) + 16))
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(STACK_ADDR, b"\xCD" * STACK_SIZE)
        self.uc.mem_write(CAND_BUF_ADDR, b"\xEE" * PAGE_SIZE)

        base = bytearray(b"\x00" * 0x100)
        base[2] = case["base_lv"] & 0xFF
        struct.pack_into("<H", base, 0x82, case["target_id"])
        self.uc.mem_write(BASE_UNIT_ADDR, bytes(base))

        target = bytearray(b"\x00" * 0x40)
        target[2] = case["target_lv"] & 0xFF
        struct.pack_into("<H", target, 0x16, case["target_flags"])
        self.uc.mem_write(TARGET_UNIT_ADDR, bytes(target))

        ts = bytearray(b"\x00" * 0x100)
        ts[0x76] = case["talk_lv"] & 0xFF
        self.uc.mem_write(TALK_STATE_ADDR, bytes(ts))

        entries = bytearray(b"\x00" * ENTRIES_SIZE)
        units = bytearray(b"\x00" * UNITS_SIZE)
        for id_val, (cand_id, lv, flags) in case.get("entries", {}).items():
            struct.pack_into("<H", entries, id_val * 0x10 + 0, cand_id)
            entries[id_val * 0x10 + 3] = lv & 0xFF
            struct.pack_into("<H", units, id_val * 0x20 + 0x16, flags)
        self.uc.mem_write(ENTRIES_ADDR, bytes(entries))
        self.uc.mem_write(UNITS_ADDR, bytes(units))

        self.uc.reg_write(arm.UC_ARM_REG_R0, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x44444444)
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
        {
            "name": "fast_path_target_match",
            "base_id": 5,
            "base_lv": 30,
            "target_id": 42,
            "target_nonnull": True,
            "target_lv": 25,
            "target_flags": 0x400,
            "talk_lv": 25,
            "check_ret": {42: 0},
            "visible_ret": 1,
        },
        {
            "name": "visible_nonpositive_early_exit",
            "base_id": 5,
            "base_lv": 30,
            "target_id": 42,
            "target_nonnull": True,
            "target_lv": 26,
            "target_flags": 0x400,
            "talk_lv": 25,
            "check_ret": {42: 0},
            "visible_ret": 0,
        },
        {
            "name": "scan_no_candidates",
            "base_id": 5,
            "base_lv": 12,
            "target_id": 0,
            "target_nonnull": False,
            "target_lv": 0,
            "target_flags": 0,
            "talk_lv": 25,
            "visible_ret": 1,
        },
        {
            "name": "scan_multiple_candidates_pick_second",
            "base_id": 5,
            "base_lv": 40,
            "target_id": 99,
            "target_nonnull": True,
            "target_lv": 20,
            "target_flags": 0x000,
            "talk_lv": 30,
            "visible_ret": 1,
            "entries": {
                1: (101, 15, 0x400),
                10: (102, 25, 0x400),
                0x4B0: (103, 30, 0x400),
            },
            "check_ret": {101: 0, 102: 1, 103: 0},
            "rand_idx": 1,
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
        ("unit_flag_mask", "kUnitFlagMask = 0x400;", "kUnitFlagMask = 0x200;"),
        ("max_entry_id", "kMaxEntryId = 0x4B0;", "kMaxEntryId = 0x4AF;"),
        ("buf_size", "kCandidateBufSize = 0x962;", "kCandidateBufSize = 0x964;"),
        ("half_clamp", "if (half < 10) {\n        half = 10;\n    }", "if (half < 11) {\n        half = 11;\n    }"),
        ("target_lv_cmp", "target_unit[2] <= talk_state[0x76]", "target_unit[2] < talk_state[0x76]"),
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
        f"PASS: btlTalkCommand_func_00318770 (0x00318770) matched original across "
        f"{len(cases)} cases and detected {len(mutants)}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
