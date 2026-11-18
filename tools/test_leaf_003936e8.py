#!/usr/bin/env python3
"""Differential test for aocTexCtrl_func_003936e8 (0x003936e8) with Unicorn ARM."""

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
SOURCE = ROOT / "src" / "engine" / "aoc.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_003936e8"

FUNC_ADDR = 0x003936E8
FUNC_SIZE = 336

STUB_ALLOC = 0x002B76E8

PTR_CTRL = 0x20000000
PTR_STATE = 0x20001000
PTR_SRC = 0x20002000
PTR_BLOCK = 0x20010000
PTR_ITEMS = 0x20011000
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
    candidate = next((val for name, val in funcs.items() if "aocTexCtrl_func_003936e8" in name), None)
    if candidate is None:
        raise RuntimeError(f"aocTexCtrl_func_003936e8 not found in {obj_file}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        off = rel.offset
        sym_name = rel.symbol_name
        rtype = rel.relocation_type
        if rtype in (28, 29):
            if "AsdMem_AllocFlags" not in sym_name:
                raise RuntimeError(f"Unhandled call relocation: {sym_name}")
            pc = FUNC_ADDR + off + 8
            disp = ((STUB_ALLOC - pc) >> 2) & 0x00FFFFFF
            insn = struct.unpack_from("<I", code, off)[0]
            struct.pack_into("<I", code, off, (insn & 0xFF000000) | disp)
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "aoc.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"aoc_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"aoc_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_CTRL, 0x20000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(self, code: bytes, b_indices: list[int], c_pairs: list[tuple[int, int]]) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x400)
        uc.mem_write(FUNC_ADDR, code)

        uc.mem_write(PTR_CTRL, struct.pack("<II", PTR_SRC, PTR_STATE))
        uc.mem_write(PTR_STATE, b"\xAA" * 0x18)
        uc.mem_write(PTR_BLOCK, b"\xAA" * 0x30)
        uc.mem_write(PTR_ITEMS, b"\xAA" * 0x100)

        uc.mem_write(PTR_SRC, b"\x00" * 0x400)
        uc.mem_write(PTR_SRC + 0x14, struct.pack("<I", 0x40))
        uc.mem_write(PTR_SRC + 0x1C, struct.pack("<II", 0x140, len(b_indices)))
        uc.mem_write(PTR_SRC + 0x24, struct.pack("<III", 0x200, len(c_pairs), 0x300))

        for i, idx in enumerate(b_indices):
            uc.mem_write(PTR_SRC + 0x140 + i * 0x14 + 0x0C, struct.pack("<i", idx))
        for i, (b_idx, d_off) in enumerate(c_pairs):
            uc.mem_write(PTR_SRC + 0x200 + i * 0x10 + 0x00, struct.pack("<I", b_idx))
            uc.mem_write(PTR_SRC + 0x200 + i * 0x10 + 0x08, struct.pack("<I", d_off))

        uc.mem_write(STUB_ALLOC, struct.pack("<I", 0xE12FFF1E))

        alloc_idx = 0
        calls: list[tuple[int, int]] = []
        bad_writes: list[int] = []

        def on_mem_invalid(uc_cb: unicorn.Uc, access: int, addr: int, size: int, val: int, _ud: object) -> bool:
            bad_writes.append(addr)
            return False

        def on_code(uc_cb: unicorn.Uc, addr: int, size: int, _ud: object) -> None:
            nonlocal alloc_idx
            if addr == STUB_ALLOC:
                r0 = uc_cb.reg_read(arm.UC_ARM_REG_R0)
                r1 = uc_cb.reg_read(arm.UC_ARM_REG_R1)
                calls.append((r0, r1))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_BLOCK if alloc_idx == 0 else PTR_ITEMS)
                alloc_idx += 1

        h_code = uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        h_mem = uc.hook_add(unicorn.UC_HOOK_MEM_WRITE_UNMAPPED | unicorn.UC_HOOK_MEM_READ_UNMAPPED, on_mem_invalid)

        uc.reg_write(arm.UC_ARM_REG_R0, PTR_CTRL)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=2000)
        finally:
            uc.hook_del(h_code)
            uc.hook_del(h_mem)

        callee = {
            reg_name: uc.reg_read(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"))
            for reg_name in CALLEE_SAVED
        }
        return {
            "r0": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": callee,
            "calls": calls,
            "src": bytes(uc.mem_read(PTR_SRC, 0x300)),
            "state": bytes(uc.mem_read(PTR_STATE, 8)),
            "block": bytes(uc.mem_read(PTR_BLOCK, 0x10)),
            "items": bytes(uc.mem_read(PTR_ITEMS, 0x80)),
            "bad_writes": bad_writes,
        }


def compare(orig: dict[str, object], cand: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("r0", "pc", "sp", "callee", "calls", "src", "state", "block", "items"):
        if orig[k] != cand[k]:
            diffs.append(f"{k} mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()
    cases = [
        ("empty", [], []),
        ("b3_c2", [-1, 0, 2], [(1, 0x10), (2, 0x24)]),
        ("b1_c3", [1], [(0, 0), (0, 8), (0, 0x1C)]),
    ]
    for label, b_idx, c_pairs in cases:
        orig_res = Runner().run(orig_bytes, b_idx, c_pairs)
        cand_res = Runner().run(cand_bytes, b_idx, c_pairs)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_stride_a", "table_a + (idx * 0x50)", "table_a + (idx * 0x40)"),
        ("drop_neg1_b", "if (idx == -1) {", "if (false) {"),
        ("wrong_c_shift", "AsdMem_AllocFlags(static_cast<u32>(count_c) << 5, 0)", "AsdMem_AllocFlags(static_cast<u32>(count_c) << 4, 0)"),
        ("wrong_item_off", "items[(i * 8) + 1] =", "items[(i * 8) + 2] ="),
        ("wrong_ret", "return 1;\n}", "return 0;\n}"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, b_idx, c_pairs in cases:
            if compare(Runner().run(orig_bytes, b_idx, c_pairs), Runner().run(mut_bytes, b_idx, c_pairs)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: aocTexCtrl_func_003936e8 (0x003936e8) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
