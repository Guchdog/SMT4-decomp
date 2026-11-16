#!/usr/bin/env python3
"""Differential test for func_001c8874 (0x001c8874) with Unicorn ARM.

Compiles src/ui/result.cpp, extracts func_001c8874, resolves its direct calls
and g_ResultManager relocation against the pinned target addresses, and runs
the pinned original (extracted/exefs/code.bin) against the candidate in
separate Unicorn machines with identical fixtures.

Compared outputs:
  * continuation PC (0x90000000), final SP, callee-saved r4-r11;
  * ordered call log (stub address, register arguments);
  * unexpected writes outside the stack (and optional state mutation inside
    ui_func_003b6150).

Coverage:
  * g_ResultManager.work == nullptr -> immediate return;
  * script_vm_func_00296cbc(work) == 0 -> immediate return;
  * signed state <= 7 (-0x80000000, -1, 0, 7) calling ui_func_003b6150(work, 0, 0),
    including mutation of work+0x352C inside ui_func_003b6150 to 0x0A before
    the switch re-read;
  * state == 8 (above 7, no pre-step call, no switch match);
  * state == 0x0A, 0x11, 0x12 dispatching to their respective slot offsets
    (+0x50C, +0xAC, +0x598) and renderers;
  * negative/mutation controls on kPreStepMaxState, kModeA, kModeB, kModeC,
    kSlotAOffset, kSlotBOffset, and kSlotCOffset.
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
SOURCE = ROOT / "src/ui/result.cpp"
OUT_DIR = ROOT / "build/test_leaf_001c8874"

FUNC_ADDR = 0x001C8874
FUNC_SIZE = 264

CODE_ADDR = 0x001C0000
CODE_SIZE = 0x00210000  # covers 0x001C8874..0x003D0000
GLOBALS_PAGE = 0x0044D000
PTR_MANAGER = 0x0044DC20
WORK_ADDR = 0x00500000
WORK_SIZE = 0x00004000
PAGE_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_296CBC = 0x00296CBC
STUB_3B6150 = 0x003B6150
STUB_2BEF7C = 0x002BEF7C
STUB_2BEF70 = 0x002BEF70
STUB_3B72A4 = 0x003B72A4
STUB_3B6C7C = 0x003B6C7C
STUB_3B4BC0 = 0x003B4BC0

STUB_NAMES = {
    STUB_296CBC: "script_vm_func_00296cbc",
    STUB_3B6150: "ui_func_003b6150",
    STUB_2BEF7C: "ui_func_002bef7c",
    STUB_2BEF70: "shop_func_002bef70",
    STUB_3B72A4: "ui_func_003b72a4",
    STUB_3B6C7C: "ui_func_003b6c7c",
    STUB_3B4BC0: "Ui_DemonCompendiumSearch",
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
    if "Ui_DemonCompendiumSearch" in symbol_name:
        return STUB_3B4BC0
    for address in STUB_NAMES:
        if f"{address:08x}" in symbol_name:
            return address
    return None


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "func_001c8874" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"func_001c8874 not found in {obj_file}: {sorted(funcs)}"
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
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if "g_ResultManager" in rel.symbol_name:
                target = PTR_MANAGER + addend
            else:
                raise RuntimeError(f"unresolved ABS32 relocation: {rel.symbol_name!r}")
            struct.pack_into("<I", code, rel.offset, target)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name!r}"
            )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "result.o"
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
    """One Unicorn machine with deterministic stubs for func_001c8874."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBALS_PAGE, PAGE_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
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

        if address == STUB_296CBC:
            self.call_log.append((address, r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["ready"])
        elif address == STUB_3B6150:
            self.call_log.append((address, r0, r1, r2))
            if "post_prestep_state" in self.case:
                self.uc.mem_write(
                    WORK_ADDR + 0x352C,
                    struct.pack("<i", self.case["post_prestep_state"]),
                )
        elif address == STUB_2BEF7C:
            self.call_log.append((address, r0))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x12345678)
        elif address == STUB_2BEF70:
            self.call_log.append((address, r0))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x9ABCDEF0)
        elif address in (STUB_3B72A4, STUB_3B6C7C, STUB_3B4BC0):
            self.call_log.append((address, r0, r1, r2))

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
        self.case = case
        self.call_log = []
        self.bad_writes = []

        self.uc.mem_write(FUNC_ADDR, b"\x00" * max(FUNC_SIZE, len(code) + 16))
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(STACK_ADDR, b"\xCD" * STACK_SIZE)
        self.uc.mem_write(GLOBALS_PAGE, b"\x00" * PAGE_SIZE)
        self.uc.mem_write(
            PTR_MANAGER, struct.pack("<I", WORK_ADDR if case["work"] else 0)
        )

        work = bytearray(b"\x00" * WORK_SIZE)
        struct.pack_into("<i", work, 0x352C, case.get("state", 0))
        self.uc.mem_write(WORK_ADDR, bytes(work))

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
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()},
            "calls": list(self.call_log),
            "bad_writes": list(self.bad_writes),
        }


def build_cases() -> list[dict]:
    return [
        {"name": "work_null", "work": False, "ready": 1},
        {"name": "not_ready", "work": True, "ready": 0, "state": 0},
        {"name": "state_min_s32", "work": True, "ready": 1, "state": -0x80000000},
        {"name": "state_neg1", "work": True, "ready": 1, "state": -1},
        {"name": "state_7_boundary", "work": True, "ready": 1, "state": 7},
        {
            "name": "state_0_mutated_to_mode_a",
            "work": True,
            "ready": 1,
            "state": 0,
            "post_prestep_state": 0x0A,
        },
        {"name": "state_8_no_prestep", "work": True, "ready": 1, "state": 8},
        {"name": "mode_a_0x0a", "work": True, "ready": 1, "state": 0x0A},
        {"name": "mode_b_0x11", "work": True, "ready": 1, "state": 0x11},
        {"name": "mode_c_0x12", "work": True, "ready": 1, "state": 0x12},
    ]


def compare_outputs(name: str, orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee", "calls", "bad_writes"):
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
        ("prestep_max", "kPreStepMaxState = 7;", "kPreStepMaxState = 6;"),
        ("mode_a", "kModeA = 0x0A;", "kModeA = 0x0B;"),
        ("mode_b", "kModeB = 0x11;", "kModeB = 0x10;"),
        ("mode_c", "kModeC = 0x12;", "kModeC = 0x13;"),
        ("slot_a", "kSlotAOffset = 0x50C;", "kSlotAOffset = 0x510;"),
        ("slot_b", "kSlotBOffset = 0xAC;", "kSlotBOffset = 0xB0;"),
        ("slot_c", "kSlotCOffset = 0x598;", "kSlotCOffset = 0x59C;"),
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
        f"PASS: func_001c8874 (0x001c8874) matched original across "
        f"{len(cases)} cases and detected {len(mutants)}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
