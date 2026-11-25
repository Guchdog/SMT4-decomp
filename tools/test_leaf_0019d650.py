#!/usr/bin/env python3
"""Differential Unicorn ARMv6K test for battle_func_0019d650 (0x0019d650)."""

from __future__ import annotations

import pathlib
import struct
import sys
import tempfile
import unittest

from unicorn import UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_ALL, Uc
from unicorn.arm_const import (
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_CPSR,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_LR,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_SP,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))
from build_check import compile_tu_armv6k  # noqa: E402

FUNC_NAME = "battle_func_0019d650"
ORIG_ADDR = 0x0019D650
ORIG_HALFWORDS = [
    0x41F0, 0xE92D, 0x5000, 0xE1A0, 0x6001, 0xE1A0, 0x0000, 0xE590,
    0xD6D9, 0xEB03, 0x7000, 0xE1A0, 0x0000, 0xE596, 0x4000, 0xE3A0,
    0xD6D5, 0xEB03, 0x1000, 0xE1D7, 0x4000, 0x13E0, 0x0007, 0xE1D0,
    0x4001, 0x13A0, 0x0000, 0x0354, 0x0007, 0x1A00, 0x0000, 0xE595,
    0x4460, 0xEB04, 0x4000, 0xE1A0, 0x0000, 0xE596, 0x445D, 0xEB04,
    0x22B4, 0xE1D4, 0x02B4, 0xE1D0, 0x4000, 0xE042, 0x0004, 0xE1A0,
    0x81F0, 0xE8BD,
]
ORIG_BYTES = struct.pack("<" + "H" * len(ORIG_HALFWORDS), *ORIG_HALFWORDS)

STUB_002931CC = 0x002931CC
STUB_002AE818 = 0x002AE818
CAND_BASE = 0x01000000
STACK_BASE = 0x02000000
STACK_SIZE = 0x10000
RET_ADDR = 0x03000000
DATA_BASE = 0x04000000
ARG_A_ADDR = DATA_BASE + 0x100
ARG_B_ADDR = DATA_BASE + 0x110
OBJ_A_ADDR = DATA_BASE + 0x200
OBJ_B_ADDR = DATA_BASE + 0x300


def load_elf_text_and_rodata(
    obj_path: pathlib.Path, func_name: str, base_addr: int, ext_addrs: dict[str, int]
):
    data = obj_path.read_bytes()
    e_shoff, = struct.unpack_from("<I", data, 0x20)
    e_shentsize, e_shnum, _ = struct.unpack_from("<HHH", data, 0x2E)
    sections = [
        struct.unpack_from("<10I", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]

    symtab_idx = next(i for i, sh in enumerate(sections) if sh[1] == 2)
    strtab_off = sections[sections[symtab_idx][6]][4]
    sym_off, sym_size, sym_entsize = (
        sections[symtab_idx][4],
        sections[symtab_idx][5],
        sections[symtab_idx][9],
    )

    def get_sym_name(idx: int) -> str:
        end = data.index(b"\x00", strtab_off + idx)
        return data[strtab_off + idx : end].decode("ascii", errors="replace")

    symbols = []
    for off in range(sym_off, sym_off + sym_size, sym_entsize):
        st_name, st_value, st_size, st_info, _, st_shndx = struct.unpack_from(
            "<IIIBBH", data, off
        )
        symbols.append((get_sym_name(st_name), st_value, st_size, st_info, st_shndx))

    sec_addrs = {}
    image = bytearray()
    for i, sh in enumerate(sections):
        sh_type, sh_flags, _, sh_offset, sh_size, _, _, sh_addralign = sh[1:9]
        if (sh_flags & 0x2) and sh_size > 0:
            align = max(4, sh_addralign)
            image.extend(b"\x00" * ((-len(image)) % align))
            sec_addrs[i] = base_addr + len(image)
            if sh_type == 8:
                image.extend(b"\x00" * sh_size)
            else:
                image.extend(data[sh_offset : sh_offset + sh_size])

    target_sym = next(s for s in symbols if s[0] == func_name)
    target_addr = sec_addrs[target_sym[4]] + target_sym[1]
    target_size = target_sym[2]

    for sh in sections:
        if sh[1] != 9:
            continue
        target_sec = sh[7]
        if target_sec not in sec_addrs:
            continue
        rel_off, rel_size, rel_entsize = sh[4], sh[5], sh[9]
        for off in range(rel_off, rel_off + rel_size, rel_entsize):
            r_offset, r_info = struct.unpack_from("<II", data, off)
            r_type = r_info & 0xFF
            sym = symbols[r_info >> 8]
            if sym[4] in sec_addrs:
                S = sec_addrs[sym[4]] + sym[1]
            elif sym[0] in ext_addrs:
                S = ext_addrs[sym[0]]
            else:
                S = 0
            P = sec_addrs[target_sec] + r_offset
            img_off = P - base_addr
            if r_type in (2, 38):
                A, = struct.unpack_from("<I", image, img_off)
                struct.pack_into("<I", image, img_off, (S + A) & 0xFFFFFFFF)
            elif r_type in (28, 29):
                insn, = struct.unpack_from("<I", image, img_off)
                imm24 = insn & 0x00FFFFFF
                if imm24 & 0x00800000:
                    imm24 -= 0x01000000
                A = imm24 << 2
                val = ((S + A - P) >> 2) & 0x00FFFFFF
                struct.pack_into("<I", image, img_off, (insn & 0xFF000000) | val)

    return bytes(image), target_addr, target_size


def to_s32(v: int) -> int:
    return v - 0x100000000 if (v & 0x80000000) else v


def run_case(code_bytes, entry_addr, is_orig, id_a, id_b, fa, fb, va, vb):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00200000, UC_PROT_ALL)
    uc.mem_map(CAND_BASE, 0x00100000, UC_PROT_ALL)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_ALL)
    uc.mem_map(RET_ADDR, 0x1000, UC_PROT_ALL)
    uc.mem_map(DATA_BASE, 0x10000, UC_PROT_ALL)

    if is_orig:
        uc.mem_write(ORIG_ADDR, code_bytes)
    else:
        uc.mem_write(CAND_BASE, code_bytes)

    uc.mem_write(STUB_002931CC, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(STUB_002AE818, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(RET_ADDR, struct.pack("<I", 0xE12FFF1E))

    uc.mem_write(ARG_A_ADDR, struct.pack("<I", id_a))
    uc.mem_write(ARG_B_ADDR, struct.pack("<I", id_b))
    uc.mem_write(OBJ_A_ADDR + 0x24, struct.pack("<H", va))
    uc.mem_write(OBJ_B_ADDR + 0x24, struct.pack("<H", vb))

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_C1_C0_2, uc.reg_read(UC_ARM_REG_C1_C0_2) | 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 0x100)
    uc.reg_write(UC_ARM_REG_LR, RET_ADDR)
    uc.reg_write(UC_ARM_REG_R0, ARG_A_ADDR)
    uc.reg_write(UC_ARM_REG_R1, ARG_B_ADDR)

    calls = []

    def hook_code(uc_inst, address, size, user_data):
        if address == STUB_002931CC:
            arg = uc_inst.reg_read(UC_ARM_REG_R0)
            calls.append(("2931cc", arg))
            uc_inst.reg_write(UC_ARM_REG_R0, fa if arg == id_a else fb)
        elif address == STUB_002AE818:
            arg = uc_inst.reg_read(UC_ARM_REG_R0)
            calls.append(("2ae818", arg))
            uc_inst.reg_write(UC_ARM_REG_R0, OBJ_A_ADDR if arg == id_a else OBJ_B_ADDR)

    uc.hook_add(1 << 2, hook_code)
    uc.emu_start(entry_addr, RET_ADDR, timeout=5_000_000, count=10_000)
    return to_s32(uc.reg_read(UC_ARM_REG_R0)), calls


CASES = [
    (10, 20, 0, 0, 100, 100),
    (10, 20, 0, 0, 50, 120),
    (10, 20, 0, 0, 300, 25),
    (10, 20, 0, 0, 0, 0xFFFF),
    (10, 20, 1, 0, 50, 120),
    (10, 20, 0, 1, 50, 120),
    (10, 20, 1, 1, 50, 120),
    (10, 20, 3, 1, 50, 120),
    (10, 20, 1, 2, 50, 120),
    (10, 20, 3, 3, 200, 150),
]


class TestBattleFunc0019d650(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory()
        obj_path = pathlib.Path(cls.tmpdir.name) / "leaf_batch46_a.o"
        res = compile_tu_armv6k(
            REPO_ROOT / "src/engine/leaf_batch46_a.cpp", obj_path, REPO_ROOT
        )
        if res.returncode != 0:
            raise RuntimeError(f"Compile failed:\n{res.stderr}")
        cls.cand_img, cls.cand_addr, cls.cand_size = load_elf_text_and_rodata(
            obj_path,
            FUNC_NAME,
            CAND_BASE,
            {
                "battle_func_002931cc": STUB_002931CC,
                "camp_func_002ae818": STUB_002AE818,
            },
        )

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def test_differential(self):
        for idx, cfg in enumerate(CASES):
            with self.subTest(case=idx):
                orig = run_case(ORIG_BYTES, ORIG_ADDR, True, *cfg)
                cand = run_case(self.cand_img, self.cand_addr, False, *cfg)
                self.assertEqual(cand, orig)

    def test_negative_controls(self):
        mutants = [
            ("invert_fa_only", CASES[4], lambda r: (-r[0], r[1])),
            ("invert_fb_only", CASES[5], lambda r: (-r[0], r[1])),
            ("wrong_multi_bit", CASES[8], lambda r: (-1, r[1])),
            ("wrong_tiebreak_sign", CASES[1], lambda r: (-r[0], r[1])),
            ("skip_helper_calls", CASES[1], lambda r: (r[0], [])),
        ]
        for mname, cfg, mutate in mutants:
            with self.subTest(mutant=mname):
                orig = run_case(ORIG_BYTES, ORIG_ADDR, True, *cfg)
                cand = run_case(self.cand_img, self.cand_addr, False, *cfg)
                self.assertEqual(cand, orig)
                self.assertNotEqual(mutate(cand), orig)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestBattleFunc0019d650)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print(
        f"PASS: {len(CASES)} cases + 5/5 mutants "
        f"(candidate {TestBattleFunc0019d650.cand_size} B)"
    )
