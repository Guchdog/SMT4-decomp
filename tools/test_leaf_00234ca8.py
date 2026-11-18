#!/usr/bin/env python3
"""Differential test for aocTexCtrl_func_00234ca8 (0x00234ca8) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_00234ca8"

FUNC_ADDR = 0x00234CA8
FUNC_SIZE = 164

STUB_ALLOC = 0x002C4B84
STUB_INIT = 0x003936E8

STUB_NAMES = {
    STUB_ALLOC: "AsdMem_Alloc",
    STUB_INIT: "aocTexCtrl_func_003936e8",
}

PTR_CTRL = 0x20000000
PTR_STATE = 0x20010000
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


def _stub_address(symbol_name: str) -> int | None:
    for addr, name in STUB_NAMES.items():
        if name in symbol_name:
            return addr
    return None


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next((val for name, val in funcs.items() if "aocTexCtrl_func_00234ca8" in name), None)
    if candidate is None:
        raise RuntimeError(f"aocTexCtrl_func_00234ca8 not found in {obj_file}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        off = rel.offset
        sym_name = rel.symbol_name
        rtype = rel.relocation_type
        if rtype in (28, 29):
            dst = _stub_address(sym_name)
            if dst is None:
                raise RuntimeError(f"Unhandled call relocation: {sym_name}")
            pc = FUNC_ADDR + off + 8
            disp = ((dst - pc) >> 2) & 0x00FFFFFF
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

    def run(self, code: bytes, existing_state: int) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x400)
        uc.mem_write(FUNC_ADDR, code)

        uc.mem_write(PTR_CTRL, struct.pack("<II", 0x11223344, existing_state))
        uc.mem_write(PTR_STATE, b"\xAA" * 0x18)

        for stub_addr in STUB_NAMES:
            uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

        calls: list[tuple[object, ...]] = []
        bad_writes: list[int] = []

        def on_mem_invalid(uc_cb: unicorn.Uc, access: int, addr: int, size: int, val: int, _ud: object) -> bool:
            bad_writes.append(addr)
            return False

        def on_code(uc_cb: unicorn.Uc, addr: int, size: int, _ud: object) -> None:
            if addr == STUB_ALLOC:
                r0 = uc_cb.reg_read(arm.UC_ARM_REG_R0)
                r1 = uc_cb.reg_read(arm.UC_ARM_REG_R1)
                r2 = uc_cb.reg_read(arm.UC_ARM_REG_R2)
                r3 = uc_cb.reg_read(arm.UC_ARM_REG_R3)
                sp = uc_cb.reg_read(arm.UC_ARM_REG_SP)
                s0 = struct.unpack("<I", uc_cb.mem_read(sp, 4))[0]
                calls.append(("alloc", r0, r1, r2, r3, s0))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_STATE)
            elif addr == STUB_INIT:
                r0 = uc_cb.reg_read(arm.UC_ARM_REG_R0)
                calls.append(("3936e8", r0))

        h_code = uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        h_mem = uc.hook_add(unicorn.UC_HOOK_MEM_WRITE_UNMAPPED | unicorn.UC_HOOK_MEM_READ_UNMAPPED, on_mem_invalid)

        uc.reg_write(arm.UC_ARM_REG_R0, PTR_CTRL)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=500)
        finally:
            uc.hook_del(h_code)
            uc.hook_del(h_mem)

        callee = {
            reg_name: uc.reg_read(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"))
            for reg_name in CALLEE_SAVED
        }
        return {
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": callee,
            "calls": calls,
            "ctrl": bytes(uc.mem_read(PTR_CTRL, 8)),
            "state": bytes(uc.mem_read(PTR_STATE, 0x18)),
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
        diffs.append(f"calls mismatch (orig {orig['calls']} vs cand {cand['calls']})")
    if orig["ctrl"] != cand["ctrl"]:
        diffs.append("ctrl mismatch")
    if orig["state"] != cand["state"]:
        diffs.append("state mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()
    cases = [
        ("existing", PTR_STATE),
        ("null_state", 0),
    ]
    for label, st in cases:
        orig_res = Runner().run(orig_bytes, st)
        cand_res = Runner().run(cand_bytes, st)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_guard", "if (ctrl->state != nullptr)", "if (false)"),
        ("wrong_alloc_sz", "AsdMem_Alloc(0x100, 0x100, 0, 0x18, 1)", "AsdMem_Alloc(0x100, 0x100, 0, 0x1C, 1)"),
        ("short_clear", "for (s32 i = 0; i < 6; ++i)", "for (s32 i = 0; i < 5; ++i)"),
        ("drop_store", "ctrl->state = reinterpret_cast<AocTexCtrlState*>(raw);", "// dropped"),
        ("drop_tail_call", "aocTexCtrl_func_003936e8(ctrl);", "// dropped"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, st in cases:
            if compare(Runner().run(orig_bytes, st), Runner().run(mut_bytes, st)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: aocTexCtrl_func_00234ca8 (0x00234ca8) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
