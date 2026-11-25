#!/usr/bin/env python3
"""Differential Unicorn ARMv6K test for shop_func_0023088c (0x0023088c)."""

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
    UC_ARM_REG_R2,
    UC_ARM_REG_SP,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))
from build_check import compile_tu_armv6k  # noqa: E402

FUNC_NAME = "shop_func_0023088c"
ORIG_ADDR = 0x0023088C
ORIG_HALFWORDS = [
    0x47F0, 0xE92D, 0x6000, 0xE1A0, 0x8002, 0xE1A0, 0x7001, 0xE1A0,
    0x00B0, 0xE1D0, 0x0000, 0xE350, 0x0076, 0x0A00, 0x91D8, 0xE59F,
    0xA1D8, 0xE59F, 0x0000, 0xE357, 0x0034, 0xAA00, 0x7000, 0xE261,
    0x1007, 0xE1A0, 0x81BF, 0xEB00, 0x0000, 0xE358, 0x006D, 0x0A00,
    0x40B0, 0xE1D6, 0x5000, 0xE3A0, 0x0004, 0xE1A0, 0xF75C, 0xEB01,
    0x000B, 0xE350, 0xF100, 0x379F, 0x001B, 0xEA00, 0x0958, 0x0023,
    0x0914, 0x0023, 0x092C, 0x0023, 0x092C, 0x0023, 0x092C, 0x0023,
    0x092C, 0x0023, 0x092C, 0x0023, 0x092C, 0x0023, 0x092C, 0x0023,
    0x0958, 0x0023, 0x0944, 0x0023, 0x0004, 0xE1A0, 0x0FCD, 0xEB02,
    0x0000, 0xE350, 0x507C, 0x1590, 0x000B, 0x1A00, 0x0015, 0xEA00,
    0x0004, 0xE1A0, 0x0FA5, 0xEB02, 0x0000, 0xE350, 0x50A0, 0x1590,
    0x0005, 0x1A00, 0x000F, 0xEA00, 0x0004, 0xE1A0, 0xF70F, 0xEBFF,
    0x0000, 0xE350, 0x502C, 0x1590, 0x000A, 0x0A00, 0x00B2, 0xE1D6,
    0x0002, 0xE310, 0x0005, 0x0A00, 0x0B00, 0xE1A0, 0x0C20, 0xE1A0,
    0x0590, 0xE000, 0x109A, 0xE0C0, 0x12C0, 0xE1A0, 0x5FC0, 0xE041,
    0x0795, 0xE004, 0x0030, 0xEA00, 0x5009, 0xE1A0, 0xFFF2, 0xEAFF,
    0xF000, 0xE320, 0x94C9, 0xEB01, 0x0000, 0xE358, 0xF000, 0xE320,
    0x0038, 0x0A00, 0x50B0, 0xE1D6, 0x4000, 0xE3A0, 0x0005, 0xE1A0,
    0xF727, 0xEB01, 0x0009, 0xE350, 0xF100, 0x379F, 0x0013, 0xEA00,
    0x0A0C, 0x0023, 0x09E0, 0x0023, 0x09F8, 0x0023, 0x09F8, 0x0023,
    0x09F8, 0x0023, 0x09F8, 0x0023, 0x09F8, 0x0023, 0x09F8, 0x0023,
    0x09F8, 0x0023, 0x0005, 0xE1A0, 0x0F9A, 0xEB02, 0x0000, 0xE350,
    0x4078, 0x1590, 0x0005, 0x1A00, 0x001C, 0xEA00, 0x0005, 0xE1A0,
    0x0F72, 0xEB02, 0x0000, 0xE350, 0x409C, 0x1590, 0x0017, 0x0A00,
    0x00B2, 0xE1D6, 0x0002, 0xE310, 0x0005, 0x0A00, 0x0B00, 0xE1A0,
    0x0C20, 0xE1A0, 0x0490, 0xE000, 0x109A, 0xE0C0, 0x12C0, 0xE1A0,
    0x4FC0, 0xE041, 0xF000, 0xE320, 0x9B13, 0xEB01, 0x0002, 0xE350,
    0x4084, 0x0084, 0x0000, 0xE264, 0x0790, 0xE004, 0x0004, 0xE1A0,
    0x9515, 0xEB01, 0x0000, 0xE354, 0xF000, 0xE320, 0x0005, 0xAA00,
    0x1000, 0xE264, 0x47F0, 0xE8BD, 0x001E, 0xE3A0, 0xADA3, 0xEA01,
    0x4009, 0xE1A0, 0xFFE5, 0xEAFF, 0x1004, 0xE1A0, 0x47F0, 0xE8BD,
    0x001F, 0xE3A0, 0xAD9D, 0xEA01, 0x87F0, 0xE8BD, 0xE0FF, 0x05F5,
    0x851F, 0x51EB,
]
ORIG_BYTES = struct.pack("<" + "H" * len(ORIG_HALFWORDS), *ORIG_HALFWORDS)

STUBS = {
    "ui_func_00250fc4": 0x00250FC4,
    "shop_func_002ae650": 0x002AE650,
    "camp_func_002b4854": 0x002B4854,
    "engine_func_002b47cc": 0x002B47CC,
    "camp_func_0022e58c": 0x0022E58C,
    "script_vm_func_00295cbc": 0x00295CBC,
    "camp_func_00297688": 0x00297688,
    "shop_func_00295ea8": 0x00295EA8,
    "camp_func_0029c0fc": 0x0029C0FC,
}

CAND_BASE = 0x01000000
STACK_BASE = 0x02000000
STACK_SIZE = 0x10000
RET_ADDR = 0x03000000
DATA_BASE = 0x04000000
ITEM_ADDR = DATA_BASE + 0x100
OBJ_4854 = DATA_BASE + 0x200
OBJ_47CC = DATA_BASE + 0x300
OBJ_E58C = DATA_BASE + 0x400


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


def run_case(
    code_bytes,
    entry_addr,
    is_orig,
    item_id,
    flags,
    count,
    pay_flag,
    kind,
    null_lookup=False,
    mul_mode=1,
):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x00200000, 0x00100000, UC_PROT_ALL)
    uc.mem_map(CAND_BASE, 0x00100000, UC_PROT_ALL)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_ALL)
    uc.mem_map(RET_ADDR, 0x1000, UC_PROT_ALL)
    uc.mem_map(DATA_BASE, 0x10000, UC_PROT_ALL)

    if is_orig:
        uc.mem_write(ORIG_ADDR, code_bytes)
    else:
        uc.mem_write(CAND_BASE, code_bytes)

    for stub in list(STUBS.values()) + [RET_ADDR]:
        uc.mem_write(stub, struct.pack("<I", 0xE12FFF1E))

    uc.mem_write(ITEM_ADDR, struct.pack("<HH", item_id, flags))
    uc.mem_write(OBJ_4854 + 0x78, struct.pack("<i", 1200))
    uc.mem_write(OBJ_4854 + 0x7C, struct.pack("<i", 600))
    uc.mem_write(OBJ_47CC + 0x9C, struct.pack("<i", 2400))
    uc.mem_write(OBJ_47CC + 0xA0, struct.pack("<i", 1100))
    uc.mem_write(OBJ_E58C + 0x2C, struct.pack("<i", 500))

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_C1_C0_2, uc.reg_read(UC_ARM_REG_C1_C0_2) | 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 0x100)
    uc.reg_write(UC_ARM_REG_LR, RET_ADDR)
    uc.reg_write(UC_ARM_REG_R0, ITEM_ADDR)
    uc.reg_write(UC_ARM_REG_R1, count & 0xFFFFFFFF)
    uc.reg_write(UC_ARM_REG_R2, pay_flag)

    calls = []

    def hook_code(uc_inst, address, size, user_data):
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        if address == STUBS["ui_func_00250fc4"]:
            calls.append(("250fc4", r0, r1))
        elif address == STUBS["script_vm_func_00295cbc"]:
            calls.append(("295cbc", r0, r1))
        elif address == STUBS["shop_func_002ae650"]:
            calls.append(("2ae650", r0))
            uc_inst.reg_write(UC_ARM_REG_R0, kind)
        elif address == STUBS["camp_func_002b4854"]:
            calls.append(("2b4854", r0))
            uc_inst.reg_write(UC_ARM_REG_R0, 0 if null_lookup else OBJ_4854)
        elif address == STUBS["engine_func_002b47cc"]:
            calls.append(("2b47cc", r0))
            uc_inst.reg_write(UC_ARM_REG_R0, 0 if null_lookup else OBJ_47CC)
        elif address == STUBS["camp_func_0022e58c"]:
            calls.append(("22e58c", r0))
            uc_inst.reg_write(UC_ARM_REG_R0, 0 if null_lookup else OBJ_E58C)
        elif address == STUBS["camp_func_00297688"]:
            calls.append(("297688",))
            uc_inst.reg_write(UC_ARM_REG_R0, mul_mode)
        elif address == STUBS["shop_func_00295ea8"]:
            calls.append(("295ea8", r0))
        elif address == STUBS["camp_func_0029c0fc"]:
            calls.append(("29c0fc", r0, r1))

    uc.hook_add(1 << 2, hook_code)
    uc.emu_start(entry_addr, RET_ADDR, timeout=5_000_000, count=10_000)
    return calls


CASES = [
    ("id_zero", (0, 0, -2, 1, 1, False, 1)),
    ("sell_nopay", (10, 0, -2, 0, 1, False, 1)),
    ("buy_nopay", (10, 0, 3, 0, 1, False, 1)),
    ("sell_k0", (10, 0, -2, 1, 0, False, 1)),
    ("sell_k1", (10, 0, -2, 1, 1, False, 1)),
    ("sell_k1_null", (10, 0, -2, 1, 1, True, 1)),
    ("sell_k2", (10, 0, -2, 1, 2, False, 1)),
    ("sell_k5_null", (10, 0, -2, 1, 5, True, 1)),
    ("sell_k10", (10, 0, -2, 1, 10, False, 1)),
    ("sell_k10_null", (10, 0, -2, 1, 10, True, 1)),
    ("sell_k1_pct75", (10, 2 | (75 << 2), -3, 1, 1, False, 1)),
    ("buy_k0", (10, 0, 2, 1, 0, False, 1)),
    ("buy_k1", (10, 0, 2, 1, 1, False, 1)),
    ("buy_k1_null", (10, 0, 2, 1, 1, True, 1)),
    ("buy_k3", (10, 0, 2, 1, 3, False, 1)),
    ("buy_k3_null", (10, 0, 2, 1, 3, True, 1)),
    ("buy_k9", (10, 0, 2, 1, 9, False, 1)),
    ("buy_k1_pct50_mul2", (10, 2 | (50 << 2), 3, 1, 1, False, 2)),
]


class TestShopFunc0023088c(unittest.TestCase):
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
            obj_path, FUNC_NAME, CAND_BASE, STUBS
        )

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def test_differential(self):
        for name, cfg in CASES:
            with self.subTest(name=name):
                orig = run_case(ORIG_BYTES, ORIG_ADDR, True, *cfg)
                cand = run_case(self.cand_img, self.cand_addr, False, *cfg)
                self.assertEqual(cand, orig, f"Mismatch on {name}")

    def test_negative_controls(self):
        mutants = [
            ("wrong_sell_price", CASES[4][1], lambda c: c[:-2] + [("295ea8", 0), c[-1]]),
            ("wrong_null_fallback", CASES[5][1], lambda c: c[:-2] + [("295ea8", 0), c[-1]]),
            ("wrong_pct_discount", CASES[10][1], lambda c: c[:-2] + [("295ea8", 1800), c[-1]]),
            ("wrong_buy_mul2", CASES[17][1], lambda c: c[:-1] + [("29c0fc", 0x1E, 1800)]),
            ("wrong_msg_0x1e_vs_0x1f", CASES[12][1], lambda c: c[:-1] + [("29c0fc", 0x1F, 2400)]),
        ]
        for mname, cfg, mutate in mutants:
            with self.subTest(mutant=mname):
                orig = run_case(ORIG_BYTES, ORIG_ADDR, True, *cfg)
                cand = run_case(self.cand_img, self.cand_addr, False, *cfg)
                self.assertEqual(cand, orig)
                self.assertNotEqual(mutate(cand), orig)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestShopFunc0023088c)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print(
        f"PASS: {len(CASES)} cases + 5/5 mutants "
        f"(candidate {TestShopFunc0023088c.cand_size} B)"
    )
