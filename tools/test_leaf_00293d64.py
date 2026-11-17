#!/usr/bin/env python3
"""Differential test for Status_HandleLRPrompt (0x00293d64) with Unicorn ARM.

Compiles src/ui/status.cpp, extracts Status_HandleLRPrompt, resolves
g_StatusManager, and compares the pinned original (extracted/exefs/code.bin)
against the compiled candidate across all state/mode/flag combinations.
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
OUT_DIR = ROOT / "build" / "test_leaf_00293d64"

FUNC_ADDR = 0x00293D64
FUNC_SIZE = 204
G_STATUS_MANAGER_ADDR = 0x0044E140

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
        if "Status_HandleLRPrompt" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"Status_HandleLRPrompt not found in {obj_file}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type == 2:  # R_ARM_ABS32
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
        self, code: bytes, sub_state: int, main_id: int, prompt_flag: int
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(G_STATUS_MANAGER_ADDR, struct.pack("<II", 1, PTR_WORK))
        uc.mem_write(PTR_WORK, b"\x00" * WORK_SIZE)
        uc.mem_write(PTR_WORK + 0x1E67, bytes([sub_state & 0xFF]))
        uc.mem_write(PTR_WORK + 0x1E66, bytes([main_id & 0xFF]))
        uc.mem_write(PTR_WORK + 0x12F1, bytes([prompt_flag & 0xFF]))
        uc.mem_write(STACK_BASE, b"\x00" * STACK_SIZE)
        uc.mem_write(LR_SENTINEL, struct.pack("<I", 0xE12FFF1E))

        bad_writes: list[tuple[int, int, int]] = []

        def on_write(
            _emu: unicorn.Uc, _access: int, addr: int, size: int, value: int, _user: object
        ) -> None:
            if STACK_BASE <= addr < STACK_BASE + STACK_SIZE:
                return
            bad_writes.append((addr, size, value))

        hook = uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=1000)
        uc.hook_del(hook)

        return {
            "r0": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {
                name: uc.reg_read(getattr(arm, f"UC_ARM_REG_{name.upper()}"))
                for name in CALLEE_SAVED
            },
            "bad_writes": bad_writes,
        }


def compare(orig: dict[str, object], cand: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    if orig["r0"] != cand["r0"]:
        diffs.append(f"r0: orig={orig['r0']} cand={cand['r0']}")
    if orig["pc"] != cand["pc"]:
        diffs.append(f"pc: orig={orig['pc']:#x} cand={cand['pc']:#x}")
    if orig["sp"] != cand["sp"]:
        diffs.append(f"sp: orig={orig['sp']:#x} cand={cand['sp']:#x}")
    if orig["callee"] != cand["callee"]:
        diffs.append("callee-saved register mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()
    cases = [
        (s, m, f)
        for s in (0, 3, 5, 6, 8, 9)
        for m in (0, 6, 7, 8, 9, 10, 11, 13, 14, 15)
        for f in (0, 1)
    ]
    for s, m, f in cases:
        orig_res = Runner().run(orig_bytes, s, m, f)
        cand_res = Runner().run(cand_bytes, s, m, f)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [s={s}, m={m}, f={f}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_state9", "state == 8 || state == 9", "state == 8"),
        ("drop_mode7", "mode == 11 || mode == 7) {\n        return 3;", "mode == 11) {\n        return 3;"),
        ("wrong_mode14", "if (mode == 14) {\n        return 1;\n    }", "if (mode == 14) {\n        return 2;\n    }"),
        ("wrong_mode0", "return prompt_flag == 0 ? 3 : 2;", "return prompt_flag == 0 ? 4 : 2;"),
        ("invert_prompt", "return prompt_flag == 0 ? 4 : 2;", "return prompt_flag == 0 ? 2 : 4;"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for s, m, f in cases:
            if compare(Runner().run(orig_bytes, s, m, f), Runner().run(mut_bytes, s, m, f)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: Status_HandleLRPrompt (0x00293d64) matched original across "
        f"{len(cases)} cases and detected {detected}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
