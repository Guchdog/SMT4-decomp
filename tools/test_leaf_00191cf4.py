#!/usr/bin/env python3
"""Differential test for camp_func_00191cf4 (0x00191cf4) with Unicorn ARM."""

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
SOURCE = ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_00191cf4"

FUNC_ADDR = 0x00191CF4
FUNC_SIZE = 440

STUB_2A0FAC = 0x002A0FAC
STUB_2B7F0A = 0x002B7F0A

STUB_NAMES = {
    STUB_2A0FAC: "camp_func_002a0fac",
    STUB_2B7F0A: "func_002b7f0a",
}

ADDR_CAMP_GLOBAL = 0x0043DD68
PTR_CAMP = 0x20000000
PTR_CFG = 0x20010000
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
    candidate = next((val for name, val in funcs.items() if "camp_func_00191cf4" in name), None)
    if candidate is None:
        raise RuntimeError(f"camp_func_00191cf4 not found in {obj_file}")

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
    obj = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    fs = text.index("extern \"C\" void camp_func_00191cf4(")
    fe = text.index("\n}\n", fs) + 3
    body = text[fs:fe]
    if body.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"leaf_batch45_b_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"leaf_batch45_b_mutant_{name}.o"
    mutant_src.write_text(text[:fs] + body.replace(old, new, 1) + text[fe:], encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_CAMP, 0x00020000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        *,
        mode_420: int,
        b11: int,
        b12: int,
        count: int,
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(0x00100000, ORIG_BIN.read_bytes())
        uc.mem_write(FUNC_ADDR, code)

        uc.mem_write(ADDR_CAMP_GLOBAL, struct.pack("<I", PTR_CAMP))
        uc.mem_write(PTR_CAMP, b"\x00" * 0x7000)
        uc.mem_write(PTR_CAMP + 0x420, bytes([mode_420]))
        uc.mem_write(PTR_CAMP + 0x6670, struct.pack("<i", count))
        uc.mem_write(PTR_CFG, b"\x00" * 0x20)
        uc.mem_write(PTR_CFG + 0x11, bytes([b11, b12]))

        calls: list[tuple[str, tuple[int, ...]]] = []

        def ret_arm(val: int | None = None) -> None:
            if val is not None:
                uc.reg_write(arm.UC_ARM_REG_R0, val & 0xFFFFFFFF)
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            cpsr = uc.reg_read(arm.UC_ARM_REG_CPSR)
            uc.reg_write(arm.UC_ARM_REG_CPSR, cpsr & ~0x20)
            uc.reg_write(arm.UC_ARM_REG_PC, lr & ~1)

        def on_code(uc_inst: unicorn.Uc, address: int, _size: int, _user: object) -> None:
            r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc_inst.reg_read(arm.UC_ARM_REG_R3)
            if address == STUB_2A0FAC:
                calls.append(("2a0fac", ()))
                ret_arm(PTR_CFG)
            elif address in (STUB_2B7F0A, STUB_2B7F0A & ~3):
                calls.append(("qsort", (r0, r1, r2, r3)))
                ret_arm(None)

        hooks = [
            uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_2A0FAC, end=STUB_2A0FAC),
            uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=0x002B7F08, end=0x002B7F0C),
        ]
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=5_000_000)
        finally:
            for h in hooks:
                uc.hook_del(h)

        return {
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "calls": calls,
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("sp", "callee", "calls"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()

    cases = [
        ("m0_k1_asc", {"mode_420": 0, "b11": 0x01, "b12": 0x02, "count": 10}),
        ("m0_k1_desc", {"mode_420": 0, "b11": 0x81, "b12": 0x02, "count": 11}),
        ("m1_k2_asc", {"mode_420": 1, "b11": 0x01, "b12": 0x02, "count": 12}),
        ("m1_k2_desc", {"mode_420": 1, "b11": 0x01, "b12": 0x82, "count": 13}),
        ("m0_k31_asc", {"mode_420": 0, "b11": 0x31, "b12": 0x00, "count": 14}),
        ("m0_k31_desc", {"mode_420": 0, "b11": 0xB1, "b12": 0x00, "count": 15}),
        ("m1_k3_asc", {"mode_420": 1, "b11": 0x00, "b12": 0x03, "count": 16}),
        ("m1_k3_desc", {"mode_420": 1, "b11": 0x00, "b12": 0x83, "count": 17}),
        ("none", {"mode_420": 0, "b11": 0x05, "b12": 0x05, "count": 18}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, **kw)
        cand_res = Runner().run(cand_bytes, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("flip_slot_sel", "(camp[0x420] == 1)", "(camp[0x420] == 0)"),
        ("flip_asc", "((*slot & 0x80u) == 0)", "((*slot & 0x80u) != 0)"),
        ("wrong_k1_cb", "0x00207280u", "0x002E4ABCu"),
        ("wrong_k31_val", "== 0x31u)", "== 0x30u)"),
        ("wrong_k3_cb", "0x001F643Cu", "0x002DCEACu"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, kw in cases:
            if compare(Runner().run(orig_bytes, **kw), Runner().run(mut_bytes, **kw)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: camp_func_00191cf4 (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
