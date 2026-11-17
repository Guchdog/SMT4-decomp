#!/usr/bin/env python3
"""Differential test for StatusBustUp_Init (0x00223a90) with Unicorn ARM.

Compiles src/ui/status.cpp, extracts StatusBustUp_Init, resolves
g_StatusBustUpManager and direct calls, and compares the pinned original
(extracted/exefs/code.bin) against the candidate in Unicorn.
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
OUT_DIR = ROOT / "build" / "test_leaf_00223a90"

FUNC_ADDR = 0x00223A90
FUNC_SIZE = 248

G_MGR_ADDR = 0x0044E158

STUB_2C4E28 = 0x002C4E28
STUB_2C5B04 = 0x002C5B04
STUB_ALLOC = 0x002C4B84
STUB_2C3B48 = 0x002C3B48

STUB_NAMES = {
    STUB_2C4E28: "AsdTMTexTable_func_002c4e28",
    STUB_2C5B04: "AsdTMTexTable_func_002c5b04",
    STUB_ALLOC: "AsdMem_Alloc",
    STUB_2C3B48: "engine_func_002c3b48",
}

PTR_BUF1 = 0x20010000
PTR_BUF2 = 0x20020000
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
    candidate = None
    for name, value in funcs.items():
        if "StatusBustUp_Init" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"StatusBustUp_Init not found in {obj_file}")

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
            struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if "g_StatusBustUpManager" in rel.symbol_name:
                target = G_MGR_ADDR + addend
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
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(self, code: bytes, ref_count: int, buf1: int, buf2: int) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(G_MGR_ADDR, struct.pack("<b3BII", ref_count, 0, 0, 0, buf1, buf2))
        uc.mem_write(STACK_BASE, b"\x00" * STACK_SIZE)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for addr in STUB_NAMES:
            uc.mem_write(addr, bx_lr)
        uc.mem_write(LR_SENTINEL, bx_lr)

        calls: list[tuple[object, ...]] = []
        bad_writes: list[tuple[int, int, int]] = []
        alloc_idx = 0

        def on_stub(emu: unicorn.Uc, addr: int, _size: int, _user: object) -> None:
            nonlocal alloc_idx
            r0 = emu.reg_read(arm.UC_ARM_REG_R0)
            r1 = emu.reg_read(arm.UC_ARM_REG_R1)
            r2 = emu.reg_read(arm.UC_ARM_REG_R2)
            r3 = emu.reg_read(arm.UC_ARM_REG_R3)
            sp = emu.reg_read(arm.UC_ARM_REG_SP)
            if addr == STUB_2C4E28:
                calls.append((addr, r0))
            elif addr == STUB_2C5B04:
                calls.append((addr, r0, r1))
            elif addr == STUB_ALLOC:
                sp0 = struct.unpack("<I", emu.mem_read(sp, 4))[0]
                calls.append((addr, r0, r1, r2, r3, sp0))
                ret = PTR_BUF1 if r3 == 0x266 and alloc_idx == 0 else PTR_BUF2
                alloc_idx += 1
                emu.reg_write(arm.UC_ARM_REG_R0, ret)
            elif addr == STUB_2C3B48:
                calls.append((addr, r0, r1))

        def on_write(
            _emu: unicorn.Uc, _access: int, addr: int, size: int, value: int, _user: object
        ) -> None:
            if G_MGR_ADDR <= addr < G_MGR_ADDR + 12:
                return
            if STACK_BASE <= addr < STACK_BASE + STACK_SIZE:
                return
            bad_writes.append((addr, size, value))

        hooks = [
            uc.hook_add(unicorn.UC_HOOK_CODE, on_stub, None, addr, addr)
            for addr in STUB_NAMES
        ]
        hooks.append(uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write))

        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=1000)
        for hook in hooks:
            uc.hook_del(hook)

        return {
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {
                name: uc.reg_read(getattr(arm, f"UC_ARM_REG_{name.upper()}"))
                for name in CALLEE_SAVED
            },
            "calls": calls,
            "mgr": bytes(uc.mem_read(G_MGR_ADDR, 12)),
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
    if orig["mgr"] != cand["mgr"]:
        diffs.append(f"mgr: orig={orig['mgr'].hex()} cand={cand['mgr'].hex()}")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()
    cases = [
        ("init_both", 0, 0, 0),
        ("neg_buf1_set", -1, PTR_BUF1, 0),
        ("zero_buf2_set", 0, 0, PTR_BUF2),
        ("ref_pos", 1, 0, 0),
    ]
    for label, rc, b1, b2 in cases:
        orig_res = Runner().run(orig_bytes, rc, b1, b2)
        cand_res = Runner().run(cand_bytes, rc, b1, b2)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_buf1_size", "kBuffer1Size = 0x266;", "kBuffer1Size = 0x268;"),
        ("wrong_buf2_size", "kBuffer2Size = 0x81;", "kBuffer2Size = 0x82;"),
        ("wrong_ref_cmp", "if (mgr->ref_count <= 0)", "if (mgr->ref_count == 0)"),
        ("drop_buf1_null_chk", "if (mgr->buffer1 == nullptr)", "if (true)"),
        ("wrong_ref_inc", "++mgr->ref_count;", "--mgr->ref_count;"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, rc, b1, b2 in cases:
            if compare(Runner().run(orig_bytes, rc, b1, b2), Runner().run(mut_bytes, rc, b1, b2)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: StatusBustUp_Init (0x00223a90) matched original across "
        f"{len(cases)} cases and detected {detected}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
