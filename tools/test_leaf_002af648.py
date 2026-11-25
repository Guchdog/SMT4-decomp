#!/usr/bin/env python3
"""Differential Unicorn ARMv6K test for engine_func_002af648 (0x002af648)."""

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

FUNC_NAME = "engine_func_002af648"
ORIG_ADDR = 0x002AF648
ORIG_HALFWORDS = [
    0x4FF0, 0xE92D, 0xD00C, 0xE24D, 0x5000, 0xE1A0, 0x7001, 0xE1A0,
    0x8002, 0xE1A0, 0x0004, 0xE590, 0x4030, 0xE59D, 0xB003, 0xE1A0,
    0x0000, 0xE350, 0x000D, 0x0A00, 0x4079, 0xEB00, 0x0000, 0xE350,
    0x0001, 0x1377, 0x0000, 0x1358, 0x0008, 0x0A00, 0x6C02, 0xE285,
    0x120A, 0xE5D5, 0x00B8, 0xE1D6, 0x9000, 0xE3A0, 0x0000, 0xE351,
    0x0001, 0xE280, 0x00B8, 0xE1C6, 0x0003, 0x0A00, 0x0016, 0xEA00,
    0xD00C, 0xE28D, 0x0000, 0xE3A0, 0x8FF0, 0xE8BD, 0x0C27, 0xE1A0,
    0x0007, 0xE350, 0xA001, 0xE3A0, 0xF100, 0x379F, 0x000E, 0xEA00,
    0xF704, 0x002A, 0xF6E4, 0x002A, 0xF830, 0x002A, 0xF778, 0x002A,
    0xF704, 0x002A, 0xF79C, 0x002A, 0xF7DC, 0x002A, 0x0004, 0xE595,
    0x1007, 0xE1A0, 0x4893, 0xEBFA, 0x0001, 0xE350, 0xF000, 0xE320,
    0x000A, 0x0A00, 0x0003, 0xE350, 0x0011, 0x0A00, 0x0000, 0xE3A0,
    0x10B8, 0xE1D6, 0x1001, 0xE241, 0x1801, 0xE1A0, 0x1821, 0xE1B0,
    0x10B8, 0xE1C6, 0x920A, 0x05C5, 0xD00C, 0xE28D, 0x8FF0, 0xE8BD,
    0x300B, 0xE1A0, 0x2008, 0xE1A0, 0x1007, 0xE1A0, 0x0005, 0xE1A0,
    0x4000, 0xE58D, 0x03F6, 0xEBFA, 0xF000, 0xE320, 0xF000, 0xE320,
    0xFFEE, 0xEAFF, 0x0000, 0xE3E0, 0x0004, 0xE58D, 0x300B, 0xE1A0,
    0x2008, 0xE1A0, 0x1007, 0xE1A0, 0x0005, 0xE1A0, 0x4000, 0xE58D,
    0x42EA, 0xEBFA, 0xF000, 0xE320, 0xF000, 0xE320, 0xFFE3, 0xEAFF,
    0x300B, 0xE1A0, 0x2008, 0xE1A0, 0x1007, 0xE1A0, 0x0005, 0xE1A0,
    0x4000, 0xE58D, 0x4376, 0xEBFA, 0xF000, 0xE320, 0xF000, 0xE320,
    0xFFDA, 0xEAFF, 0x0008, 0xE31B, 0x1007, 0xE1A0, 0x000A, 0x0A00,
    0x0004, 0xE595, 0xF496, 0xEBFF, 0x1000, 0xE1A0, 0x3004, 0xE1A0,
    0x2008, 0xE1A0, 0x0005, 0xE1A0, 0xA000, 0xE58D, 0xF446, 0xEBFF,
    0x0000, 0xE350, 0xF000, 0xE320, 0x0014, 0x0A00, 0x0001, 0xE3A0,
    0xFFCA, 0xEAFF, 0x0004, 0xE595, 0x1007, 0xE1A0, 0xF488, 0xEBFF,
    0x1000, 0xE1A0, 0x3004, 0xE1A0, 0x2008, 0xE1A0, 0x0005, 0xE1A0,
    0xA000, 0xE58D, 0xF438, 0xEBFF, 0x1000, 0xE1B0, 0xF000, 0xE320,
    0x0006, 0x0A00, 0x3004, 0xE1A0, 0x2008, 0xE1A0, 0x0005, 0xE1A0,
    0x03F8, 0xEBFA, 0xF000, 0xE320, 0xF000, 0xE320, 0xFFB7, 0xEAFF,
    0x0009, 0xE1A0, 0xFFB5, 0xEAFF, 0x300B, 0xE1A0, 0x2008, 0xE1A0,
    0x1007, 0xE1A0, 0x0005, 0xE1A0, 0x4000, 0xE58D, 0x0348, 0xEBFA,
    0xF000, 0xE320, 0xF000, 0xE320, 0xFFAC, 0xEAFF,
]
ORIG_BYTES = struct.pack("<" + "H" * len(ORIG_HALFWORDS), *ORIG_HALFWORDS)

STUBS = {
    "engine_func_002bf85c": 0x002BF85C,
    "engine_func_00141940": 0x00141940,
    "engine_func_0013071c": 0x0013071C,
    "engine_func_00140318": 0x00140318,
    "engine_func_0014056c": 0x0014056C,
    "engine_func_002aca0c": 0x002ACA0C,
    "engine_func_002ac8e4": 0x002AC8E4,
    "engine_func_00130800": 0x00130800,
    "engine_func_0013056c": 0x0013056C,
}

CAND_BASE = 0x01000000
STACK_BASE = 0x02000000
STACK_SIZE = 0x10000
RET_ADDR = 0x03000000
DATA_BASE = 0x04000000
OBJ_ADDR = DATA_BASE + 0x100


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
    handle,
    key,
    arg2,
    arg3,
    arg4,
    cnt_init=0,
    flag_20a=0,
    valid_handle=1,
    kind_141940=1,
    ok_2ac8e4=0x777,
):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00300000, UC_PROT_ALL)
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

    uc.mem_write(OBJ_ADDR + 4, struct.pack("<I", handle))
    uc.mem_write(OBJ_ADDR + 0x208, struct.pack("<H", cnt_init))
    uc.mem_write(OBJ_ADDR + 0x20A, struct.pack("<B", flag_20a))

    sp = STACK_BASE + STACK_SIZE - 0x100
    uc.mem_write(sp, struct.pack("<I", arg4))

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_C1_C0_2, uc.reg_read(UC_ARM_REG_C1_C0_2) | 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, RET_ADDR)
    uc.reg_write(UC_ARM_REG_R0, OBJ_ADDR)
    uc.reg_write(UC_ARM_REG_R1, key)
    uc.reg_write(UC_ARM_REG_R2, arg2)
    uc.reg_write(UC_ARM_REG_R3, arg3)

    calls = []

    def hook_code(uc_inst, address, size, user_data):
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(UC_ARM_REG_R2)
        r3 = uc_inst.reg_read(UC_ARM_REG_R3)
        cur_sp = uc_inst.reg_read(UC_ARM_REG_SP)
        s0, s1 = struct.unpack("<II", uc_inst.mem_read(cur_sp, 8))
        if address == STUBS["engine_func_002bf85c"]:
            calls.append(("2bf85c", r0))
            uc_inst.reg_write(UC_ARM_REG_R0, valid_handle)
        elif address == STUBS["engine_func_00141940"]:
            calls.append(("141940", r0, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, kind_141940)
        elif address == STUBS["engine_func_0013071c"]:
            calls.append(("13071c", r0, r1, r2, r3, s0))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x1071)
        elif address == STUBS["engine_func_00140318"]:
            calls.append(("140318", r0, r1, r2, r3, s0, s1))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x1403)
        elif address == STUBS["engine_func_0014056c"]:
            calls.append(("14056c", r0, r1, r2, r3, s0))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x1405)
        elif address == STUBS["engine_func_0013056c"]:
            calls.append(("13056c", r0, r1, r2, r3, s0))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x1305)
        elif address == STUBS["engine_func_002aca0c"]:
            calls.append(("2aca0c", r0, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x555)
        elif address == STUBS["engine_func_002ac8e4"]:
            calls.append(("2ac8e4", r0, r1, r2, r3, s0))
            uc_inst.reg_write(UC_ARM_REG_R0, ok_2ac8e4)
        elif address == STUBS["engine_func_00130800"]:
            calls.append(("130800", r0, r1, r2, r3))
            uc_inst.reg_write(UC_ARM_REG_R0, 0x1308)

    uc.hook_add(1 << 2, hook_code)
    uc.emu_start(entry_addr, RET_ADDR, timeout=5_000_000, count=10_000)
    ret = uc.reg_read(UC_ARM_REG_R0)
    cnt_out = struct.unpack("<H", uc.mem_read(OBJ_ADDR + 0x208, 2))[0]
    flag_out = uc.mem_read(OBJ_ADDR + 0x20A, 1)[0]
    return ret, cnt_out, flag_out, calls


CASES = [
    ("null_handle", (0, 0x01000001, 0x10, 0, 0x20, 0, 0, 1, 1, 1)),
    ("invalid_handle", (0x1234, 0x01000001, 0x10, 0, 0x20, 0, 0, 0, 1, 1)),
    ("key_neg1", (0x1234, 0xFFFFFFFF, 0x10, 0, 0x20, 0, 0, 1, 1, 1)),
    ("arg2_zero", (0x1234, 0x01000001, 0, 0, 0x20, 0, 0, 1, 1, 1)),
    ("flag_20a_nonzero_cnt0", (0x1234, 0x01000001, 0x10, 0, 0x20, 0, 9, 1, 1, 1)),
    ("flag_20a_nonzero_cnt1", (0x1234, 0x01000001, 0x10, 0, 0x20, 1, 9, 1, 1, 1)),
    ("tag0_default", (0x1234, 0x00000001, 0x10, 0, 0x20, 0, 0, 1, 1, 1)),
    ("tag1_kind1", (0x1234, 0x01000005, 0x10, 0x22, 0x33, 0, 0, 1, 1, 1)),
    ("tag1_kind3", (0x1234, 0x01000005, 0x10, 0x22, 0x33, 0, 0, 1, 3, 1)),
    ("tag1_kind2_other", (0x1234, 0x01000005, 0x10, 0x22, 0x33, 0, 0, 1, 2, 1)),
    ("tag2", (0x1234, 0x02000005, 0x10, 0x22, 0x33, 0, 0, 1, 1, 1)),
    ("tag3", (0x1234, 0x03000005, 0x10, 0x22, 0x33, 0, 0, 1, 1, 1)),
    ("tag4_default", (0x1234, 0x04000005, 0x10, 0x22, 0x33, 0, 0, 1, 1, 1)),
    ("tag5_no_bit8", (0x1234, 0x05000005, 0x10, 0x00, 0x33, 0, 0, 1, 1, 1)),
    ("tag5_bit8_ok", (0x1234, 0x05000005, 0x10, 0x08, 0x33, 0, 0, 1, 1, 0x777)),
    ("tag5_bit8_fail", (0x1234, 0x05000005, 0x10, 0x08, 0x33, 0, 0, 1, 1, 0)),
    ("tag6_ok", (0x1234, 0x06000005, 0x10, 0x00, 0x33, 0, 0, 1, 1, 0x777)),
    ("tag6_fail", (0x1234, 0x06000005, 0x10, 0x00, 0x33, 0, 0, 1, 1, 0)),
    ("tag7_default", (0x1234, 0x07000005, 0x10, 0x00, 0x33, 0, 0, 1, 1, 1)),
]


class TestEngineFunc002af648(unittest.TestCase):
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
            ("wrong_flag_clear_when_cnt_nonzero", CASES[5][1], lambda r: (r[0], r[1], 0, r[3])),
            ("wrong_tag1_kind3_arg5", CASES[8][1], lambda r: (r[0], r[1], r[2], r[3][:-1] + [r[3][-1][:-1] + (0,)])),
            ("wrong_tag5_bit8_fail_ret", CASES[15][1], lambda r: (1, r[1], r[2], r[3])),
            ("wrong_tag6_fail_calls_130800", CASES[17][1], lambda r: (0x1308, r[1], r[2], r[3])),
            ("wrong_tag2_ret", CASES[10][1], lambda r: (0, r[1], r[2], r[3])),
        ]
        for mname, cfg, mutate in mutants:
            with self.subTest(mutant=mname):
                orig = run_case(ORIG_BYTES, ORIG_ADDR, True, *cfg)
                cand = run_case(self.cand_img, self.cand_addr, False, *cfg)
                self.assertEqual(cand, orig)
                self.assertNotEqual(mutate(cand), orig)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestEngineFunc002af648)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print(
        f"PASS: {len(CASES)} cases + 5/5 mutants "
        f"(candidate {TestEngineFunc002af648.cand_size} B)"
    )
