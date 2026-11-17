#!/usr/bin/env python3
"""Differential test for engine_func_00205628 (0x00205628) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts engine_func_00205628,
resolves its 4 callees and global pointer 0x0043DCF0, and compares the pinned
original against the compiled candidate across modes 4, 6, 8, default, and
sub-modes 0/1 plus mutant negative controls.
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
FUNC_ADDR = 0x00205628
FUNC_SIZE = 772
FUNC_NAME = "engine_func_00205628"

STUB_BASE = 0x00110000
GLOBAL_PAGE = 0x0043D000
G_PTR = 0x0043DCF0

MEM_BASE = 0x20000000
MEM_SIZE = 0x00010000
G_ADDR = 0x20000000
STACK_TOP = 0x2000F000
TRAP_ADDR = 0x001F0000

CALLEES = {
    0x00299558: ("engine_func_00299558", 2),
    0x0029D8C0: ("camp_func_0029d8c0", 2),
    0x0029EBF8: ("engine_func_0029ebf8", 1),
    0x0029F0F4: ("camp_func_0029f0f4", 1),
}

STUB_ADDRS = {addr: STUB_BASE + idx * 4 for idx, addr in enumerate(sorted(CALLEES))}
ADDR_BY_STUB = {v: k for k, v in STUB_ADDRS.items()}
NAME_TO_STUB = {CALLEES[k][0]: v for k, v in STUB_ADDRS.items()}


def encode_arm_branch(pc: int, target: int, link: bool) -> int:
    imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if link else 0xEA000000
    return opcode | imm24


def patch_orig_code(raw: bytes) -> bytearray:
    code = bytearray(raw)
    for off in range(0, len(code), 4):
        insn = struct.unpack_from("<I", code, off)[0]
        cond = (insn >> 28) & 0xF
        op = (insn >> 24) & 0xF
        if cond != 0xF and op in (0xA, 0xB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = FUNC_ADDR + off
            target = pc + 8 + (imm24 << 2)
            if target in STUB_ADDRS:
                struct.pack_into("<I", code, off, encode_arm_branch(pc, STUB_ADDRS[target], link=(op == 0xB)))
    return code


def patch_cand_code(raw: bytes, relocs: list) -> bytearray:
    code = bytearray(raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):
            insn = struct.unpack_from("<I", code, rel.offset)[0]
            cond = (insn >> 28) & 0xF
            op = (insn >> 24) & 0xF
            link = op == 0xB
            target = NAME_TO_STUB[rel.symbol_name]
            pc = FUNC_ADDR + rel.offset
            imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
            struct.pack_into("<I", code, rel.offset, (cond << 28) | ((0xB if link else 0xA) << 24) | imm24)
        else:
            raise RuntimeError(f"Unsupported relocation type {rel.relocation_type} for {rel.symbol_name}")
    return code


def build_candidate(src_text: str | None = None) -> bytearray:
    out_dir = ROOT / "build" / "test_leaf_00205628"
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
        self.uc.mem_map(STUB_BASE, 0x1000)
        self.uc.mem_map(FUNC_ADDR & ~0xFFF, 0x2000)
        self.uc.mem_map(GLOBAL_PAGE, 0x1000)
        self.uc.mem_map(MEM_BASE, MEM_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))

        for stub_addr in STUB_ADDRS.values():
            self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)
        self.uc.mem_write(G_PTR, struct.pack("<I", G_ADDR))

        g = bytearray(0xC00)
        struct.pack_into("<I", g, 0x20, case["mode"])
        struct.pack_into("<I", g, 0x2C, case.get("sub", 0))
        for col in case.get("b678", ()):
            g[0x678 + col] = 1
        for slot in case.get("u16_73c", ()):
            struct.pack_into("<H", g, 0x73C + slot * 8, 1)
        self.uc.mem_write(G_ADDR, bytes(g))

        call_log: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr not in ADDR_BY_STUB:
                return
            orig_target = ADDR_BY_STUB[addr]
            cname, arity = CALLEES[orig_target]
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            call_log.append((cname, *(r0, r1)[:arity]))

            ret = 0
            if orig_target == 0x0029EBF8:
                ret = case.get("cols", 4)
            elif orig_target == 0x0029F0F4:
                ret = case.get("rows", 5)
            uc.reg_write(arm.UC_ARM_REG_R0, ret)

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_BASE, end=STUB_BASE + 0x100)
        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)
        finally:
            self.uc.hook_del(hook)

        return {"call_log": call_log}


def make_cases() -> list[dict]:
    return [
        {"name": "mode_other_noop", "mode": 2},
        {"name": "mode4_hit_col2", "mode": 4, "cols": 4, "b678": (2,)},
        {"name": "mode4_empty", "mode": 4, "cols": 0},
        {"name": "mode6_sub0_slot5_lt12", "mode": 6, "sub": 0, "rows": 5, "cols": 4, "u16_73c": (5,)},
        {"name": "mode6_sub0_slot12_ge12", "mode": 6, "sub": 0, "rows": 5, "cols": 4, "u16_73c": (12,)},
        {"name": "mode6_sub1_slot17_ge12", "mode": 6, "sub": 1, "rows": 6, "cols": 4, "u16_73c": (17,)},
        {"name": "mode6_sub1_slot2_lt12", "mode": 6, "sub": 1, "rows": 5, "cols": 4, "u16_73c": (2,)},
        {"name": "mode8_b678_hit", "mode": 8, "cols": 4, "b678": (1,)},
        {"name": "mode8_sub0_slot5_lt12", "mode": 8, "sub": 0, "rows": 5, "cols": 4, "u16_73c": (5,)},
        {"name": "mode8_sub1_slot14_ge12", "mode": 8, "sub": 1, "rows": 6, "cols": 4, "u16_73c": (14,)},
        {"name": "mode8_sub2_breaks", "mode": 8, "sub": 2, "rows": 5, "cols": 4, "u16_73c": (5,)},
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
        ("mode4_list", "g + 0x8DCu", "g + 0x8E0u"),
        ("mode6_row_bias", "row - 4", "row - 3"),
        ("mode8_row_bias", "row - 3", "row - 4"),
        ("slot_thresh", ">= 0xC", ">= 0xD"),
        ("u16_off", "+ 0x73Cu", "+ 0x73Eu"),
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
