#!/usr/bin/env python3
"""Differential Unicorn ARMv6K test for script_vm_func_001f4b68 (0x001f4b68)."""

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
    UC_ARM_REG_SP,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))
from build_check import compile_tu_armv6k  # noqa: E402

FUNC_NAME = "script_vm_func_001f4b68"
ORIG_ADDR = 0x001F4B68
ORIG_HALFWORDS = [
    0x0078, 0xE28F, 0x4010, 0xE92D, 0x44AD, 0xEB03, 0x4088, 0xE59F,
    0x000C, 0xE584, 0x0084, 0xE28F, 0x44A9, 0xEB03, 0x0010, 0xE584,
    0x009C, 0xE28F, 0x44A6, 0xEB03, 0x0014, 0xE584, 0x00AC, 0xE28F,
    0x44A3, 0xEB03, 0x0018, 0xE584, 0x00BC, 0xE28F, 0x44A0, 0xEB03,
    0x001C, 0xE584, 0x00CC, 0xE28F, 0x449D, 0xEB03, 0x0020, 0xE584,
    0x00E0, 0xE28F, 0x449A, 0xEB03, 0x0024, 0xE584, 0x00EC, 0xE28F,
    0x4497, 0xEB03, 0x0028, 0xE584, 0x0C01, 0xE28F, 0x4494, 0xEB03,
    0x002C, 0xE584, 0x73D4, 0xEBFF, 0x4010, 0xE8BD, 0x4538, 0xEA00,
    0x6162, 0x7474, 0x656C, 0x4C2F, 0x6765, 0x6F69, 0x2F6E, 0x654C,
    0x6967, 0x6E6F, 0x734D, 0x2E67, 0x626D, 0x006D, 0x5D90, 0x0043,
    0x6162, 0x7474, 0x656C, 0x4C2F, 0x6765, 0x6F69, 0x2F6E, 0x654C,
    0x6967, 0x6E6F, 0x734D, 0x5467, 0x6261, 0x656C, 0x742E, 0x6262,
    0x0000, 0x0000, 0x6162, 0x7474, 0x656C, 0x4C2F, 0x6765, 0x6F69,
    0x2F6E, 0x654C, 0x6967, 0x6E6F, 0x6353, 0x2E72, 0x6662, 0x0000,
    0x6162, 0x7474, 0x656C, 0x432F, 0x6D6F, 0x6F6D, 0x2F6E, 0x6F63,
    0x6D6D, 0x6E6F, 0x6D2E, 0x6D62, 0x0000, 0x0000, 0x6162, 0x7474,
    0x656C, 0x742F, 0x6C61, 0x2F6B, 0x6154, 0x6B6C, 0x7953, 0x7473,
    0x6D65, 0x6D2E, 0x6D62, 0x0000, 0x6162, 0x7474, 0x656C, 0x742F,
    0x6C61, 0x2F6B, 0x6154, 0x6B6C, 0x6142, 0x6573, 0x6144, 0x6174,
    0x742E, 0x6262, 0x0000, 0x0000, 0x6162, 0x7474, 0x656C, 0x532F,
    0x7379, 0x6574, 0x616D, 0x6974, 0x2E63, 0x6274, 0x0062, 0x0000,
    0x7665, 0x6E65, 0x2F74, 0x7571, 0x7365, 0x2F74, 0x7553, 0x5162,
    0x6575, 0x7473, 0x7547, 0x7365, 0x2E74, 0x626D, 0x006D, 0x0000,
    0x6162, 0x7474, 0x656C, 0x422F, 0x736F, 0x4473, 0x6165, 0x5464,
    0x6261, 0x656C, 0x742E, 0x6262, 0x0000, 0x0000,
]
ORIG_BYTES = struct.pack("<" + "H" * len(ORIG_HALFWORDS), *ORIG_HALFWORDS)

STUB_002C5E2C = 0x002C5E2C
STUB_001D1B34 = 0x001D1B34
STUB_002060CC = 0x002060CC
GLOBAL_00435D90 = 0x00435D90

CAND_BASE = 0x01000000
STACK_BASE = 0x02000000
STACK_SIZE = 0x10000
RET_ADDR = 0x03000000


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


def read_cstr(uc: Uc, ptr: int) -> str:
    buf = bytearray()
    for i in range(128):
        b = uc.mem_read(ptr + i, 1)[0]
        if b == 0:
            break
        buf.append(b)
    return buf.decode("ascii")


def run_case(code_bytes, entry_addr, is_orig, ret_1d1b34):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000, UC_PROT_ALL)
    uc.mem_map(CAND_BASE, 0x00100000, UC_PROT_ALL)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_ALL)
    uc.mem_map(RET_ADDR, 0x1000, UC_PROT_ALL)

    if is_orig:
        uc.mem_write(ORIG_ADDR, code_bytes)
    else:
        uc.mem_write(CAND_BASE, code_bytes)

    for stub in (STUB_002C5E2C, STUB_001D1B34, STUB_002060CC, RET_ADDR):
        uc.mem_write(stub, struct.pack("<I", 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_C1_C0_2, uc.reg_read(UC_ARM_REG_C1_C0_2) | 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 0x100)
    uc.reg_write(UC_ARM_REG_LR, RET_ADDR)

    calls = []
    idx = [0]

    def hook_code(uc_inst, address, size, user_data):
        if address == STUB_002C5E2C:
            s = read_cstr(uc_inst, uc_inst.reg_read(UC_ARM_REG_R0))
            calls.append(("2c5e2c", s))
            idx[0] += 1
            uc_inst.reg_write(UC_ARM_REG_R0, 0x55000000 + idx[0])
        elif address == STUB_001D1B34:
            calls.append(("1d1b34",))
            uc_inst.reg_write(UC_ARM_REG_R0, ret_1d1b34)
        elif address == STUB_002060CC:
            calls.append(("2060cc", uc_inst.reg_read(UC_ARM_REG_R0)))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x77770000 | (ret_1d1b34 & 0xFFFF))

    uc.hook_add(1 << 2, hook_code)
    uc.emu_start(entry_addr, RET_ADDR, timeout=5_000_000, count=10_000)
    slots = struct.unpack("<9I", uc.mem_read(GLOBAL_00435D90 + 0x0C, 36))
    return uc.reg_read(UC_ARM_REG_R0), slots, calls


class TestScriptVmFunc001f4b68(unittest.TestCase):
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
                "script_vm_func_002c5e2c": STUB_002C5E2C,
                "battle_func_001d1b34": STUB_001D1B34,
            },
        )
        cls.cases = [0, 1, 0x12345678]

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def test_differential(self):
        for val in self.cases:
            with self.subTest(val=val):
                orig = run_case(ORIG_BYTES, ORIG_ADDR, True, val)
                cand = run_case(self.cand_img, self.cand_addr, False, val)
                self.assertEqual(cand, orig)

    def test_negative_controls(self):
        orig = run_case(ORIG_BYTES, ORIG_ADDR, True, 0x1234)
        cand = run_case(self.cand_img, self.cand_addr, False, 0x1234)
        self.assertEqual(cand, orig)
        mutants = [
            ("wrong_slot_order", (cand[0], (cand[1][1], cand[1][0]) + cand[1][2:], cand[2])),
            ("wrong_string_path", (cand[0], cand[1], [("2c5e2c", "wrong")] + cand[2][1:])),
            ("skip_1d1b34", (cand[0], cand[1], [c for c in cand[2] if c[0] != "1d1b34"])),
            ("skip_2060cc", (cand[0], cand[1], [c for c in cand[2] if c[0] != "2060cc"])),
            ("wrong_return_val", (cand[0] ^ 1, cand[1], cand[2])),
        ]
        for mname, mutated in mutants:
            with self.subTest(mutant=mname):
                self.assertNotEqual(mutated, orig)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestScriptVmFunc001f4b68)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print(
        f"PASS: {len(TestScriptVmFunc001f4b68.cases)} cases + 5/5 mutants "
        f"(candidate {TestScriptVmFunc001f4b68.cand_size} B)"
    )
