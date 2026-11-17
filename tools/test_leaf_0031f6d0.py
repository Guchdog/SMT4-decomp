#!/usr/bin/env python3
"""Differential test for ui_func_0031f6d0 (0x0031F6D0) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts ui_func_0031f6d0,
resolves ui_func_002c615c (signed divmod), maps global buffer 0x004EA81C,
and compares the pinned original against the compiled candidate across
period<=0, period>0 interpolation, negative/positive indices, and mutants.
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
FUNC_ADDR = 0x0031F6D0
FUNC_SIZE = 768
FUNC_NAME = "ui_func_0031f6d0"

STUB_BASE = 0x00110000
STUB_2C615C = STUB_BASE
GLOBAL_PAGE = 0x004EA000
GLOBAL_BASE = 0x004EA81C

MEM_BASE = 0x20000000
MEM_SIZE = 0x00010000
SELF_ADDR = 0x20000000
STATE_ADDR = 0x20001000
STACK_TOP = 0x2000F000
TRAP_ADDR = 0x001F0000


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
        if cond == 0xE and op in (0xA, 0xB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = FUNC_ADDR + off
            target = pc + 8 + (imm24 << 2)
            if target == 0x002C615C:
                struct.pack_into("<I", code, off, encode_arm_branch(pc, STUB_2C615C, link=(op == 0xB)))
    return code


def patch_cand_code(raw: bytes, relocs: list) -> bytearray:
    code = bytearray(raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29) and rel.symbol_name == "ui_func_002c615c":
            insn = struct.unpack_from("<I", code, rel.offset)[0]
            cond = (insn >> 28) & 0xF
            op = (insn >> 24) & 0xF
            link = op == 0xB
            pc = FUNC_ADDR + rel.offset
            imm24 = ((STUB_2C615C - (pc + 8)) >> 2) & 0x00FFFFFF
            struct.pack_into("<I", code, rel.offset, (cond << 28) | ((0xB if link else 0xA) << 24) | imm24)
        else:
            raise RuntimeError(f"Unsupported relocation type {rel.relocation_type} for {rel.symbol_name}")
    return code


def build_candidate(src_text: str | None = None) -> bytearray:
    out_dir = ROOT / "build" / "test_leaf_0031f6d0"
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
        self.uc.mem_map(GLOBAL_PAGE, 0x1000)
        self.uc.mem_map(MEM_BASE, MEM_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))
        self.uc.mem_write(STUB_2C615C, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)
        self.uc.mem_write(GLOBAL_PAGE, b"\x00" * 0x1000)

        # Populate g_100 initial color
        self.uc.mem_write(GLOBAL_BASE + 0x100, struct.pack("<4f", *case["g100_init"]))

        # Populate self
        self_buf = bytearray(0x80)
        struct.pack_into("<i", self_buf, 0x38, case["total"])
        for idx, col in enumerate(case["palette"]):
            struct.pack_into("<I", self_buf, 0x3C + idx * 4, col)
        self.uc.mem_write(SELF_ADDR, bytes(self_buf))

        # Populate state
        state_buf = bytearray(0x20)
        struct.pack_into("<b", state_buf, 0x18, case["base_idx"])
        self.uc.mem_write(STATE_ADDR, bytes(state_buf))

        def on_div(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            num = struct.unpack("<i", struct.pack("<I", uc.reg_read(arm.UC_ARM_REG_R0)))[0]
            den = struct.unpack("<i", struct.pack("<I", uc.reg_read(arm.UC_ARM_REG_R1)))[0]
            q = int(num / den)  # C trunc-toward-zero
            r = num - q * den
            uc.reg_write(arm.UC_ARM_REG_R0, q & 0xFFFFFFFF)
            uc.reg_write(arm.UC_ARM_REG_R1, r & 0xFFFFFFFF)

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_div, begin=STUB_2C615C, end=STUB_2C615C + 4)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, STATE_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case["step"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)
        finally:
            self.uc.hook_del(hook)

        return {
            "g100": tuple(round(x, 6) for x in struct.unpack("<4f", self.uc.mem_read(GLOBAL_BASE + 0x100, 16))),
            "g110": tuple(round(x, 6) for x in struct.unpack("<4f", self.uc.mem_read(GLOBAL_BASE + 0x110, 16))),
            "g120": tuple(round(x, 6) for x in struct.unpack("<4f", self.uc.mem_read(GLOBAL_BASE + 0x120, 16))),
        }


PAL = [0xFF000080, 0x00FF00FF, 0x0000FFFF, 0x808080FF, 0xFFFFFFFF, 0x11223344]


def make_cases() -> list[dict]:
    return [
        {"name": "period_zero_uses_base_idx", "total": 5, "base_idx": 2, "step": 3, "g100_init": (0.5, 0.5, 1.0, 1.0), "palette": PAL},
        {"name": "period_neg_uses_base_idx", "total": -12, "base_idx": 4, "step": 1, "g100_init": (1.0, 0.5, 0.25, 0.5), "palette": PAL},
        {"name": "interp_mid_step", "total": 60, "base_idx": 1, "step": 25, "g100_init": (0.8, 0.6, 0.4, 1.0), "palette": PAL},
        {"name": "interp_wraps_mod_6", "total": 60, "base_idx": 5, "step": 10, "g100_init": (1.0, 1.0, 1.0, 1.0), "palette": PAL},
        {"name": "interp_negative_step", "total": 60, "base_idx": 3, "step": -15, "g100_init": (0.5, 0.75, 0.25, 0.5), "palette": PAL},
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
        ("period_div6", "/ 6;", "/ 5;"),
        ("mod_6", "% 6;", "% 5;"),
        ("inv_255", "0x3B808081u", "0x3B818081u"),
        ("pal_off", "+ 0x3Cu", "+ 0x40u"),
        ("g120_copy", "g_110[i] = g_120[i];", "g_110[i] = 0.0f;"),
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
