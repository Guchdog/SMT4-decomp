#!/usr/bin/env python3
"""Differential test for camp_func_00198fcc (0x00198FCC) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts camp_func_00198fcc,
resolves Thumb func_002b7f0a (qsort), and compares the pinned original against
the compiled candidate across empty, single-group odd/even, two-group odd/even,
pre-set b575e, and mutant negative controls.
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
SRC_CPP = ROOT / "src/engine/leaf_batch45_a.cpp"
FUNC_ADDR = 0x00198FCC
FUNC_SIZE = 848
FUNC_NAME = "camp_func_00198fcc"

STUB_BASE = 0x00110000
STUB_2B7F0A = STUB_BASE

MEM_BASE = 0x20000000
MEM_SIZE = 0x00010000
SELF_ADDR = 0x20000000
STACK_TOP = 0x2000F000
TRAP_ADDR = 0x001F0000


def encode_arm_blx_thumb(pc: int, target: int) -> int:
    diff = target - (pc + 8)
    h_bit = (diff >> 1) & 1
    imm24 = (diff >> 2) & 0x00FFFFFF
    return 0xFA000000 | (h_bit << 24) | imm24


def patch_orig_code(raw: bytes) -> bytearray:
    code = bytearray(raw)
    for off in range(0, len(code), 4):
        insn = struct.unpack_from("<I", code, off)[0]
        cond = (insn >> 28) & 0xF
        op = (insn >> 24) & 0xF
        pc = FUNC_ADDR + off
        if cond == 0xF and (op & 0xE) == 0xA:
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            h_bit = (insn >> 24) & 1
            target = pc + 8 + (imm24 << 2) + (h_bit << 1)
            if target == 0x002B7F0A:
                struct.pack_into("<I", code, off, encode_arm_blx_thumb(pc, STUB_2B7F0A))
    return code


def patch_cand_code(raw: bytes, relocs: list) -> bytearray:
    code = bytearray(raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29) and rel.symbol_name == "func_002b7f0a":
            pc = FUNC_ADDR + rel.offset
            struct.pack_into("<I", code, rel.offset, encode_arm_blx_thumb(pc, STUB_2B7F0A))
        else:
            raise RuntimeError(f"Unsupported relocation type {rel.relocation_type} for {rel.symbol_name}")
    return code


def build_candidate(src_text: str | None = None) -> bytearray:
    out_dir = ROOT / "build" / "test_leaf_00198fcc"
    out_dir.mkdir(parents=True, exist_ok=True)
    if src_text is None:
        src_path = SRC_CPP
        obj_path = out_dir / "baseline.o"
    else:
        src_path = out_dir / "mutant.cpp"
        obj_path = out_dir / "mutant.o"
        src_path.write_text(src_text, encoding="utf-8")

    res = compile_tu_armv6k(src_path, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compile failed:\n{res.stderr}")
    funcs = extract_elf_functions_detailed(obj_path)
    if FUNC_NAME not in funcs:
        raise RuntimeError(f"{FUNC_NAME} not found in compiled ELF")
    raw, relocs = funcs[FUNC_NAME]
    return patch_cand_code(raw, relocs)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        self.uc.mem_map(STUB_BASE, 0x1000)
        self.uc.mem_map(FUNC_ADDR & ~0xFFF, 0x2000)
        self.uc.mem_map(MEM_BASE, MEM_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))
        self.uc.mem_write(STUB_2B7F0A, struct.pack("<HH", 0x4770, 0))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)

        vals = case["vals"]
        buf = bytearray(0x6000)
        struct.pack_into("<i", buf, 0x5758, len(vals))
        buf[0x575E] = case.get("b575e", 0)
        buf[0x575F] = case.get("b575f", 0)
        for idx, v in enumerate(vals):
            struct.pack_into("<f", buf, 0x5760 + idx * 0x2C + 0x10, v)
        self.uc.mem_write(SELF_ADDR, bytes(buf))

        call_log: list[tuple] = []

        def on_qsort(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc.reg_read(arm.UC_ARM_REG_R3)
            call_log.append(("qsort", r0 - SELF_ADDR, r1, r2, r3))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_qsort, begin=STUB_2B7F0A, end=STUB_2B7F0A + 4)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)
        finally:
            self.uc.hook_del(hook)

        pairs = [
            struct.unpack("<ii", self.uc.mem_read(SELF_ADDR + 0x5780 + i * 44, 8))
            for i in range(len(vals))
        ]
        flags = tuple(self.uc.mem_read(SELF_ADDR + 0x575E, 2))
        return {"call_log": call_log, "flags": flags, "pairs": pairs}


def make_cases() -> list[dict]:
    return [
        {"name": "empty", "vals": []},
        {"name": "single_group_odd_3", "vals": [1.0, 1.0, 1.0]},
        {"name": "single_group_even_4", "vals": [2.0, 2.0, 2.0, 2.0]},
        {"name": "two_groups_odd_even_3_2", "vals": [1.0, 1.0, 1.0, 2.0, 2.0]},
        {"name": "two_groups_even_odd_2_3", "vals": [1.0, 1.0, 2.0, 2.0, 2.0]},
        {"name": "preset_b575e_1_b575f_0", "vals": [1.0, 2.0], "b575e": 1, "b575f": 0},
    ]


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = patch_orig_code(raw_bin[off : off + FUNC_SIZE])
    src_text = SRC_CPP.read_text(encoding="utf-8")
    cand_code = build_candidate()
    print(f"{FUNC_NAME}: orig {len(orig_code)} B, cand {len(cand_code)} B")

    cases = make_cases()
    for case in cases:
        orig_res = Runner().run(orig_code, case)
        cand_res = Runner().run(cand_code, case)
        if orig_res != cand_res:
            print(f"FAIL [{case['name']}]:")
            print("  orig:", orig_res)
            print("  cand:", cand_res)
            return 1
        print(f"PASS [{case['name']}]")

    mutants = [
        ("cmp_dir", "prev < cur", "prev <= cur"),
        ("odd_1a1", "0x1A1", "0x1A2"),
        ("even_1a6", "0x1A6", "0x1A7"),
        ("g0_14a", "0x14A", "0x14B"),
        ("g1_159", "0x159", "0x15A"),
    ]
    for name, old, new in mutants:
        assert old in src_text, f"Mutant target not found: {old}"
        m_code = build_candidate(src_text.replace(old, new, 1))
        detected = False
        for case in cases:
            orig_res = Runner().run(orig_code, case)
            try:
                bad_res = Runner().run(m_code, case)
            except unicorn.UcError:
                detected = True
                break
            if orig_res != bad_res:
                detected = True
                break
        if not detected:
            print(f"FAIL [mutant {name}]: not detected!")
            return 1
        print(f"PASS [mutant {name} detected]")

    print(f"ALL PASS: {len(cases)} cases + {len(mutants)} negative controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
