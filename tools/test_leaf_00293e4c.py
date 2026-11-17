#!/usr/bin/env python3
"""Differential test for Status_UpdateAffinityTable (0x00293e4c) with Unicorn ARM.

Compiles src/ui/status.cpp, extracts Status_UpdateAffinityTable, resolves
g_StatusManager and StatusDown_SetDisplayMode, and compares the pinned original
(extracted/exefs/code.bin) against the candidate across 200 state/mode cases.
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

ORIG_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "ui" / "status.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_00293e4c"

FUNC_ADDR = 0x00293E4C
FUNC_SIZE = 520

G_STATUS_MANAGER_ADDR = 0x0044E140
STUB_SET_DISPLAY_MODE = 0x00292F44

PTR_WORK = 0x20000000
WORK_SIZE = 0x1EBC
STACK_BASE = 0x7F000000
STACK_SIZE = 0x10000
STACK_INIT = STACK_BASE + STACK_SIZE - 0x200
LR_SENTINEL = 0x90000000

CALLEE_SAVED = {
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
        if "Status_UpdateAffinityTable" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"Status_UpdateAffinityTable not found in {obj_file}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            if "StatusDown_SetDisplayMode" not in rel.symbol_name:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (STUB_SET_DISPLAY_MODE - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if "g_StatusManager" in rel.symbol_name:
                target = G_STATUS_MANAGER_ADDR + addend
            else:
                raise RuntimeError(f"unresolved ABS32 relocation: {rel.symbol_name!r}")
            struct.pack_into("<I", code, rel.offset, target)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} for {rel.symbol_name!r}"
            )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "status.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"status_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"status_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    result = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed: {result.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_WORK, 0x10000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self, code: bytes, main_id: int, sub_state: int, disp_state: int, lock: int
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(G_STATUS_MANAGER_ADDR, struct.pack("<II", 1, PTR_WORK))

        uc.mem_write(PTR_WORK, b"\x00" * WORK_SIZE)
        uc.mem_write(PTR_WORK + 0x14, struct.pack("<I", 0xDEADBEEF))
        uc.mem_write(PTR_WORK + 0x1E63, bytes([0]))
        uc.mem_write(PTR_WORK + 0x1E66, bytes([main_id & 0xFF]))
        uc.mem_write(PTR_WORK + 0x1E67, bytes([sub_state & 0xFF]))
        uc.mem_write(PTR_WORK + 0x12E4, struct.pack("<I", disp_state))
        uc.mem_write(PTR_WORK + 0x12F1, bytes([lock & 0xFF]))
        uc.mem_write(STACK_BASE, b"\x00" * STACK_SIZE)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        uc.mem_write(STUB_SET_DISPLAY_MODE, bx_lr)
        uc.mem_write(LR_SENTINEL, bx_lr)

        calls: list[int] = []
        bad_writes: list[tuple[int, int, int]] = []

        def on_stub(emu: unicorn.Uc, _addr: int, _size: int, _user: object) -> None:
            calls.append(emu.reg_read(arm.UC_ARM_REG_R0))

        def on_write(
            _emu: unicorn.Uc, _access: int, addr: int, size: int, value: int, _user: object
        ) -> None:
            if PTR_WORK <= addr < PTR_WORK + WORK_SIZE:
                return
            if STACK_BASE <= addr < STACK_BASE + STACK_SIZE:
                return
            bad_writes.append((addr, size, value))

        h1 = uc.hook_add(
            unicorn.UC_HOOK_CODE, on_stub, None, STUB_SET_DISPLAY_MODE, STUB_SET_DISPLAY_MODE
        )
        h2 = uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)

        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=2000)
        uc.hook_del(h1)
        uc.hook_del(h2)

        return {
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {
                name: uc.reg_read(getattr(arm, f"UC_ARM_REG_{name.upper()}"))
                for name in CALLEE_SAVED
            },
            "calls": calls,
            "work": bytes(uc.mem_read(PTR_WORK, WORK_SIZE)),
            "bad_writes": bad_writes,
        }


def compare(orig: dict[str, object], cand: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    if orig["pc"] != cand["pc"]:
        diffs.append(f"pc: orig={orig['pc']:#x} cand={cand['pc']:#x}")
    if orig["sp"] != cand["sp"]:
        diffs.append(f"sp: orig={orig['sp']:#x} cand={cand['sp']:#x}")
    if orig["callee"] != cand["callee"]:
        diffs.append("callee-saved register mismatch")
    if orig["calls"] != cand["calls"]:
        diffs.append(f"calls: orig={orig['calls']} cand={cand['calls']}")
    if orig["work"] != cand["work"]:
        diffs.append("work memory mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()
    cases = [
        (m, s, d, l)
        for m in (0, 6, 7, 8, 9, 10, 11, 13, 14, 15)
        for s in (0, 6)
        for d in (0, 1, 2, 3, 4)
        for l in (0, 1)
    ]
    for m, s, d, l in cases:
        orig_res = Runner().run(orig_bytes, m, s, d, l)
        cand_res = Runner().run(cand_bytes, m, s, d, l)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [m={m}, s={s}, d={d}, l={l}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_field14", "work->field_14 = 0;", "work->field_14 = 1;"),
        ("wrong_flag1e63", "work->flag_1e63 = 1;", "work->flag_1e63 = 0;"),
        ("drop_mode0_lock", "if (*affinity_lock == 0 && *display_state == 2)", "if (*display_state == 2)"),
        ("drop_mode7", "if (mode == 8 || mode == 9 || mode == 10 || mode == 11 || mode == 7)", "if (mode == 8 || mode == 9 || mode == 10 || mode == 11)"),
        ("drop_mode13_lock", "    if (mode == 13) {\n        if (*display_state == 0) {\n            StatusDown_SetDisplayMode(0);\n        }\n        if (*display_state == 1) {\n            StatusDown_SetDisplayMode(1);\n        }\n        if (*affinity_lock != 0) {\n            return;\n        }", "    if (mode == 13) {\n        if (*display_state == 0) {\n            StatusDown_SetDisplayMode(0);\n        }\n        if (*display_state == 1) {\n            StatusDown_SetDisplayMode(1);\n        }\n        if (false) {\n            return;\n        }"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for m, s, d, l in cases:
            if compare(Runner().run(orig_bytes, m, s, d, l), Runner().run(mut_bytes, m, s, d, l)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: Status_UpdateAffinityTable (0x00293e4c) matched original across "
        f"{len(cases)} cases and detected {detected}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
