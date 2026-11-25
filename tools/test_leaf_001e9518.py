#!/usr/bin/env python3
"""Differential Unicorn ARMv6K test for ui_func_001e9518 (0x001e9518)."""

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

FUNC_NAME = "ui_func_001e9518"
ORIG_ADDR = 0x001E9518
ORIG_HALFWORDS = [
    0x4070, 0xE92D, 0x51EC, 0xE59F, 0x4000, 0xE595, 0x0008, 0xE594,
    0x0063, 0xE350, 0x0004, 0x0A00, 0x0002, 0xE3A0, 0x5AA0, 0xEB03,
    0x0000, 0xE350, 0x0063, 0x13A0, 0x0008, 0x1584, 0x0008, 0xE594,
    0x0000, 0xE350, 0x0004, 0x0A00, 0x0001, 0xE350, 0x0006, 0x0A00,
    0x0063, 0xE350, 0x0063, 0x1A00, 0x0064, 0xEA00, 0x0001, 0xE3A0,
    0x1000, 0xE3A0, 0x00F8, 0xE1C4, 0x005E, 0xEA00, 0x0004, 0xE3A0,
    0x3EAB, 0xEB03, 0x0000, 0xE350, 0xF000, 0xE320, 0x0008, 0x0A00,
    0x0010, 0xE594, 0x1001, 0xE240, 0x0009, 0xE351, 0x0000, 0xC3A0,
    0x0002, 0xCA00, 0x0000, 0xE351, 0x0009, 0xB3A0, 0x0001, 0xA240,
    0x0010, 0xE584, 0x0003, 0xE3A0, 0x3E9D, 0xEB03, 0x0000, 0xE350,
    0xF000, 0xE320, 0x0008, 0x0A00, 0x0010, 0xE594, 0x1001, 0xE280,
    0x0009, 0xE351, 0x0000, 0xC3A0, 0x0002, 0xCA00, 0x0000, 0xE351,
    0x0009, 0xB3A0, 0x0001, 0xA280, 0x0010, 0xE584, 0x0000, 0xE3A0,
    0x5A73, 0xEB03, 0x0000, 0xE350, 0xF000, 0xE320, 0x003B, 0x0A00,
    0x0010, 0xE594, 0x000A, 0xE350, 0xF100, 0x379F, 0x0039, 0xEA00,
    0x9630, 0x001E, 0x9644, 0x001E, 0x9658, 0x001E, 0x9668, 0x001E,
    0x967C, 0x001E, 0x9690, 0x001E, 0x96A0, 0x001E, 0x96B4, 0x001E,
    0x96C0, 0x001E, 0x96D0, 0x001E, 0x00DC, 0xE59F, 0x77D5, 0xEB02,
    0xF000, 0xE320, 0xF000, 0xE320, 0x002A, 0xEA00, 0x001E, 0xE3A0,
    0x9ECB, 0xEB02, 0xF000, 0xE320, 0xF000, 0xE320, 0x0025, 0xEA00,
    0x00B8, 0xE59F, 0x203C, 0xE3A0, 0x1000, 0xE3A0, 0x0002, 0xEA00,
    0x00AC, 0xE59F, 0x203C, 0xE3A0, 0x1000, 0xE3A0, 0xDBF1, 0xEB02,
    0x001C, 0xEA00, 0x000F, 0xE3A0, 0xCBF2, 0xEB02, 0xF000, 0xE320,
    0xF000, 0xE320, 0x0017, 0xEA00, 0x0088, 0xE59F, 0x203C, 0xE3A0,
    0x1000, 0xE3A0, 0x0002, 0xEA00, 0x007C, 0xE59F, 0x203C, 0xE3A0,
    0x1000, 0xE3A0, 0x85EB, 0xEBFE, 0x000E, 0xEA00, 0x0058, 0xE59F,
    0x100F, 0xE3A0, 0x0001, 0xEA00, 0x0050, 0xE59F, 0x100F, 0xE3A0,
    0xE53F, 0xEB01, 0x0007, 0xEA00, 0x0048, 0xE59F, 0x100F, 0xE3A0,
    0xE53B, 0xEB01, 0xF000, 0xE320, 0xF000, 0xE320, 0x0001, 0xEA00,
    0x0001, 0xE3A0, 0x5A32, 0xEB03, 0x0000, 0xE3A0, 0x8070, 0xE8BD,
    0x0000, 0xE595, 0x1000, 0xE3A0, 0x0000, 0xE590, 0x6BAB, 0xEB03,
    0x0000, 0xE3E0, 0x8070, 0xE8BD, 0xE110, 0x0044, 0x0010, 0x0100,
    0x0004, 0x0100, 0x0007, 0x0100, 0x0009, 0x0100, 0x0006, 0x0100,
]
ORIG_BYTES = struct.pack("<" + "H" * len(ORIG_HALFWORDS), *ORIG_HALFWORDS)

STUBS = {
    "ui_func_002bffbc": 0x002BFFBC,
    "ui_func_002b902c": 0x002B902C,
    "engine_func_00287590": 0x00287590,
    "script_vm_func_0029117c": 0x0029117C,
    "camp_func_002a0640": 0x002A0640,
    "script_vm_func_0029c650": 0x0029C650,
    "engine_func_0018ae60": 0x0018AE60,
    "script_vm_func_00262bcc": 0x00262BCC,
    "battle_func_002c45b8": 0x002C45B8,
}

CAND_BASE = 0x01000000
STACK_BASE = 0x02000000
STACK_SIZE = 0x10000
RET_ADDR = 0x03000000
GLOBAL_PTR = 0x0044E110
STATE_ADDR = 0x00450000


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


def run_case(code_bytes, entry_addr, is_orig, st2, st3, st4, btn2, btn0, up4, dn3):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000, UC_PROT_ALL)
    uc.mem_map(CAND_BASE, 0x00100000, UC_PROT_ALL)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_ALL)
    uc.mem_map(RET_ADDR, 0x1000, UC_PROT_ALL)

    if is_orig:
        uc.mem_write(ORIG_ADDR, code_bytes)
    else:
        uc.mem_write(CAND_BASE, code_bytes)

    for stub in list(STUBS.values()) + [RET_ADDR]:
        uc.mem_write(stub, struct.pack("<I", 0xE12FFF1E))

    uc.mem_write(GLOBAL_PTR, struct.pack("<I", STATE_ADDR))
    uc.mem_write(STATE_ADDR, struct.pack("<IIIII", 0xABCD0000, 0, st2, st3, st4))

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_C1_C0_2, uc.reg_read(UC_ARM_REG_C1_C0_2) | 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 0x100)
    uc.reg_write(UC_ARM_REG_LR, RET_ADDR)

    calls = []

    def hook_code(uc_inst, address, size, user_data):
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(UC_ARM_REG_R2)
        if address == STUBS["ui_func_002bffbc"]:
            calls.append(("2bffbc", r0))
            uc_inst.reg_write(UC_ARM_REG_R0, btn2 if r0 == 2 else (btn0 if r0 == 0 else 0))
        elif address == STUBS["ui_func_002b902c"]:
            calls.append(("2b902c", r0))
            uc_inst.reg_write(UC_ARM_REG_R0, up4 if r0 == 4 else (dn3 if r0 == 3 else 0))
        elif address == STUBS["engine_func_00287590"]:
            calls.append(("287590", r0))
        elif address == STUBS["script_vm_func_0029117c"]:
            calls.append(("29117c", r0))
        elif address == STUBS["camp_func_002a0640"]:
            calls.append(("2a0640", r0, r1, r2))
        elif address == STUBS["script_vm_func_0029c650"]:
            calls.append(("29c650", r0))
        elif address == STUBS["engine_func_0018ae60"]:
            calls.append(("18ae60", r0, r1, r2))
        elif address == STUBS["script_vm_func_00262bcc"]:
            calls.append(("262bcc", r0, r1))
        elif address == STUBS["battle_func_002c45b8"]:
            calls.append(("2c45b8", r0, r1))

    uc.hook_add(1 << 2, hook_code)
    uc.emu_start(entry_addr, RET_ADDR, timeout=5_000_000, count=10_000)
    ret = uc.reg_read(UC_ARM_REG_R0)
    out_state = struct.unpack("<III", uc.mem_read(STATE_ADDR + 8, 12))
    return ret, out_state, calls


CASES = [
    ("st2_0", (0, 99, 3, 0, 0, 0, 0)),
    ("st2_2_other", (2, 99, 3, 0, 0, 0, 0)),
    ("st2_0_btn2", (0, 99, 3, 1, 0, 0, 0)),
    ("st2_0x63", (0x63, 99, 3, 0, 0, 0, 0)),
    ("st2_1_up_wrap", (1, 0, 0, 0, 0, 1, 0)),
    ("st2_1_up_norm", (1, 0, 5, 0, 0, 1, 0)),
    ("st2_1_dn_wrap", (1, 0, 9, 0, 0, 0, 1)),
    ("st2_1_dn_norm", (1, 0, 4, 0, 0, 0, 1)),
    ("st2_1_no_btn0", (1, 0, 2, 0, 0, 0, 0)),
    ("st2_1_oob_idx10", (1, 0, 10, 0, 1, 0, 0)),
] + [(f"st2_1_exec_{i}", (1, 0, i, 0, 1, 0, 0)) for i in range(10)]


class TestUiFunc001e9518(unittest.TestCase):
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
            ("wrong_st2_0_ret", CASES[0][1], lambda r: (1, r[1], r[2])),
            ("wrong_st2_0x63_ret", CASES[3][1], lambda r: (0, r[1], r[2])),
            ("wrong_up_wrap", CASES[4][1], lambda r: (r[0], (r[1][0], r[1][1], 0), r[2])),
            ("wrong_case9_arg", CASES[19][1], lambda r: (r[0], r[1], r[2][:-1] + [("262bcc", 0x01000007, 0xF)])),
            ("skip_btn1_on_no_btn0", CASES[8][1], lambda r: (r[0], r[1], r[2][:-1])),
        ]
        for mname, cfg, mutate in mutants:
            with self.subTest(mutant=mname):
                orig = run_case(ORIG_BYTES, ORIG_ADDR, True, *cfg)
                cand = run_case(self.cand_img, self.cand_addr, False, *cfg)
                self.assertEqual(cand, orig)
                self.assertNotEqual(mutate(cand), orig)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestUiFunc001e9518)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print(
        f"PASS: {len(CASES)} cases + 5/5 mutants "
        f"(candidate {TestUiFunc001e9518.cand_size} B)"
    )
