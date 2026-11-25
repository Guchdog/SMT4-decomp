#!/usr/bin/env python3
"""Differential Unicorn ARMv6K test for script_vm_func_002be548 (0x002be548)."""

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
    UC_ARM_REG_R3,
    UC_ARM_REG_SP,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))
from build_check import compile_tu_armv6k  # noqa: E402

FUNC_NAME = "script_vm_func_002be548"
ORIG_ADDR = 0x002BE548
ORIG_HALFWORDS = [
    0x47F0, 0xE92D, 0xD008, 0xE24D, 0x4000, 0xE3A0, 0x7000, 0xE1A0,
    0x6028, 0xE59D, 0xA001, 0xE1A0, 0x8002, 0xE1A0, 0x9003, 0xE1A0,
    0x5004, 0xE1A0, 0xC037, 0xEBFF, 0x000B, 0xE350, 0xF100, 0x379F,
    0x0056, 0xEA00, 0xE5C8, 0x002B, 0xE5A8, 0x002B, 0xE5F0, 0x002B,
    0xE610, 0x002B, 0xE630, 0x002B, 0xE650, 0x002B, 0xE670, 0x002B,
    0xE690, 0x002B, 0xE6B0, 0x002B, 0xE6D4, 0x002B, 0xE6D4, 0x002B,
    0x0007, 0xE1A0, 0xD8A8, 0xEBFF, 0x006C, 0xE5D0, 0xF000, 0xE320,
    0xBFE3, 0xEBFF, 0x4000, 0xE1A0, 0xF000, 0xE320, 0x0043, 0xEA00,
    0x0007, 0xE1A0, 0xBFBC, 0xEBFF, 0x0053, 0xE5D0, 0x0000, 0xE350,
    0x4144, 0x059F, 0x003D, 0x0A00, 0xBFD9, 0xEBFF, 0x4000, 0xE1A0,
    0xF000, 0xE320, 0x0039, 0xEA00, 0x4130, 0xE59F, 0x0000, 0xE356,
    0x0036, 0x0A00, 0xE03A, 0xEBFF, 0x00B0, 0xE1D0, 0x0007, 0xE150,
    0x002F, 0x0A00, 0x0031, 0xEA00, 0x0000, 0xE356, 0x4FFE, 0xE3A0,
    0x002E, 0x0A00, 0xE032, 0xEBFF, 0x00B2, 0xE1D0, 0x0007, 0xE150,
    0x0027, 0x0A00, 0x0029, 0xEA00, 0x40F4, 0xE59F, 0x0000, 0xE356,
    0x0026, 0x0A00, 0xE02A, 0xEBFF, 0x00B6, 0xE1D0, 0x0007, 0xE150,
    0x001F, 0x0A00, 0x0021, 0xEA00, 0x40D8, 0xE59F, 0x0000, 0xE356,
    0x001E, 0x0A00, 0xE022, 0xEBFF, 0x00B8, 0xE1D0, 0x0007, 0xE150,
    0x0017, 0x0A00, 0x0019, 0xEA00, 0x0000, 0xE356, 0x4FFF, 0xE3A0,
    0x0016, 0x0A00, 0xE01A, 0xEBFF, 0x00BA, 0xE1D0, 0x0007, 0xE150,
    0x000F, 0x0A00, 0x0011, 0xEA00, 0x409C, 0xE59F, 0x0000, 0xE356,
    0x000E, 0x0A00, 0xE012, 0xEBFF, 0x00BC, 0xE1D0, 0x0007, 0xE150,
    0x0007, 0x0A00, 0x0009, 0xEA00, 0x4080, 0xE59F, 0x0000, 0xE356,
    0x0006, 0x0A00, 0xE00A, 0xEBFF, 0x00B4, 0xE1D0, 0x0007, 0xE150,
    0x0002, 0x1A00, 0x5001, 0xE3A0, 0x0000, 0xEA00, 0x4060, 0xE59F,
    0x300A, 0xE1A0, 0x1013, 0xE3A0, 0x2004, 0xE1A0, 0x0002, 0xE3A0,
    0x80F0, 0xE1CD, 0xC163, 0xEBFF, 0x0000, 0xE355, 0xF000, 0xE320,
    0x0007, 0x0A00, 0x0001, 0xE289, 0x0004, 0xE58D, 0x2034, 0xE59F,
    0x300A, 0xE1A0, 0x1013, 0xE3A0, 0x0002, 0xE3A0, 0x8000, 0xE58D,
    0x0350, 0xEB00, 0xD008, 0xE28D, 0x87F0, 0xE8BD, 0x03FF, 0x0000,
    0x03F7, 0x0000, 0x03FA, 0x0000, 0x03FB, 0x0000, 0x03FD, 0x0000,
    0x03F9, 0x0000, 0x03FE, 0x0000, 0x0417, 0x0000,
]
ORIG_BYTES = struct.pack("<" + "H" * len(ORIG_HALFWORDS), *ORIG_HALFWORDS)

STUB_002AE650 = 0x002AE650
STUB_002B4854 = 0x002B4854
STUB_002AE54C = 0x002AE54C
STUB_002AE4C4 = 0x002AE4C4
STUB_002B66EC = 0x002B66EC
STUB_002AEC80 = 0x002AEC80
STUB_002BF460 = 0x002BF460

CAND_BASE = 0x01000000
STACK_BASE = 0x02000000
STACK_SIZE = 0x10000
RET_ADDR = 0x03000000
DATA_BASE = 0x04000000
OBJ_002AE4C4 = DATA_BASE + 0x100
OBJ_002B4854 = DATA_BASE + 0x200
OBJ_002B66EC = DATA_BASE + 0x300


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
    code_bytes, entry_addr, is_orig, arg0, arg1, arg2, arg3, arg4, kind, flag53
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

    for stub in (
        STUB_002AE650,
        STUB_002B4854,
        STUB_002AE54C,
        STUB_002AE4C4,
        STUB_002B66EC,
        STUB_002AEC80,
        STUB_002BF460,
    ):
        uc.mem_write(stub, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(RET_ADDR, struct.pack("<I", 0xE12FFF1E))

    uc.mem_write(OBJ_002AE4C4 + 0x53, struct.pack("<B", flag53))
    uc.mem_write(OBJ_002B4854 + 0x6C, struct.pack("<B", 0x42))
    # Populate u16 slots at +0x0, +0x2, +0x4, +0x6, +0x8, +0xa, +0xc
    uc.mem_write(
        OBJ_002B66EC,
        struct.pack("<HHHHHHH", 101, 102, 103, 104, 105, 106, 107),
    )

    sp = STACK_BASE + STACK_SIZE - 0x100
    uc.mem_write(sp, struct.pack("<I", arg4))

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_C1_C0_2, uc.reg_read(UC_ARM_REG_C1_C0_2) | 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, RET_ADDR)
    uc.reg_write(UC_ARM_REG_R0, arg0)
    uc.reg_write(UC_ARM_REG_R1, arg1)
    uc.reg_write(UC_ARM_REG_R2, arg2)
    uc.reg_write(UC_ARM_REG_R3, arg3)

    calls = []

    def hook_code(uc_inst, address, size, user_data):
        if address == STUB_002AE650:
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            calls.append(("2ae650", r0))
            uc_inst.reg_write(UC_ARM_REG_R0, kind)
        elif address == STUB_002B4854:
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            calls.append(("2b4854", r0))
            uc_inst.reg_write(UC_ARM_REG_R0, OBJ_002B4854)
        elif address == STUB_002AE54C:
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            calls.append(("2ae54c", r0))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x700 + r0)
        elif address == STUB_002AE4C4:
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            calls.append(("2ae4c4", r0))
            uc_inst.reg_write(UC_ARM_REG_R0, OBJ_002AE4C4)
        elif address == STUB_002B66EC:
            calls.append(("2b66ec",))
            uc_inst.reg_write(UC_ARM_REG_R0, OBJ_002B66EC)
        elif address in (STUB_002AEC80, STUB_002BF460):
            cur_sp = uc_inst.reg_read(UC_ARM_REG_SP)
            s0, s1 = struct.unpack("<II", uc_inst.mem_read(cur_sp, 8))
            tag = "2aec80" if address == STUB_002AEC80 else "2bf460"
            calls.append((
                tag,
                uc_inst.reg_read(UC_ARM_REG_R0),
                uc_inst.reg_read(UC_ARM_REG_R1),
                uc_inst.reg_read(UC_ARM_REG_R2),
                uc_inst.reg_read(UC_ARM_REG_R3),
                s0,
                s1,
            ))

    uc.hook_add(1 << 2, hook_code)
    uc.emu_start(entry_addr, RET_ADDR, timeout=5_000_000, count=10_000)
    return calls


def build_cases():
    cases = [
        ("kind0_flag0", (101, 0x10, 0x20, 0x30, 1, 0, 0)),
        ("kind0_flag5", (101, 0x10, 0x20, 0x30, 1, 0, 5)),
        ("kind1", (101, 0x10, 0x20, 0x30, 1, 1, 0)),
        ("kind9", (101, 0x10, 0x20, 0x30, 1, 9, 0)),
        ("kind10", (101, 0x10, 0x20, 0x30, 1, 10, 0)),
        ("kind11_default", (101, 0x10, 0x20, 0x30, 1, 11, 0)),
    ]
    # Cases 2..8: arg4=0 vs arg4=1, match vs mismatch
    match_vals = {2: 101, 3: 102, 4: 104, 5: 105, 6: 106, 7: 107, 8: 103}
    for k, mv in match_vals.items():
        cases.append((f"kind{k}_arg4_0_match", (mv, 0x11, 0x22, 0x33, 0, k, 0)))
        cases.append((f"kind{k}_arg4_1_match", (mv, 0x11, 0x22, 0x33, 1, k, 0)))
        cases.append((f"kind{k}_arg4_1_miss", (999, 0x11, 0x22, 0x33, 1, k, 0)))
    return cases


class TestScriptVmFunc002be548(unittest.TestCase):
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
            obj_path, FUNC_NAME, CAND_BASE, {"shop_func_002ae650": STUB_002AE650}
        )
        cls.cases = build_cases()

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def test_differential(self):
        for name, cfg in self.cases:
            with self.subTest(name=name):
                orig = run_case(ORIG_BYTES, ORIG_ADDR, True, *cfg)
                cand = run_case(self.cand_img, self.cand_addr, False, *cfg)
                self.assertEqual(cand, orig, f"Mismatch on {name}")

    def test_negative_controls(self):
        mutants = [
            ("wrong_kind0_flag0_const", self.cases[0][1], lambda c: c[:-1] + [("2aec80", 2, 0x13, 0x3FE, 0x10, 0x20, 0x30)]),
            ("wrong_kind3_msg_id", self.cases[8][1], lambda c: c[:-2] + [("2aec80", 2, 0x13, 0, 0x11, 0x22, 0x33), c[-1]]),
            ("drop_2bf460_on_match", self.cases[7][1], lambda c: c[:-1]),
            ("wrong_arg3_plus1", self.cases[7][1], lambda c: c[:-1] + [c[-1][:-1] + (0x33,)]),
            ("wrong_default_msg", self.cases[5][1], lambda c: c[:-1] + [("2aec80", 2, 0x13, 0x3FE, 0x10, 0x20, 0x30)]),
        ]
        for mname, cfg, mutate in mutants:
            with self.subTest(mutant=mname):
                orig = run_case(ORIG_BYTES, ORIG_ADDR, True, *cfg)
                cand = run_case(self.cand_img, self.cand_addr, False, *cfg)
                self.assertEqual(cand, orig)
                self.assertNotEqual(mutate(cand), orig)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestScriptVmFunc002be548)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print(
        f"PASS: {len(TestScriptVmFunc002be548.cases)} cases + 5/5 mutants "
        f"(candidate {TestScriptVmFunc002be548.cand_size} B)"
    )
