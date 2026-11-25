#!/usr/bin/env python3
"""Differential Unicorn ARMv6K test for engine_func_002bc9d8 (0x002bc9d8)."""

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
    UC_ARM_REG_PC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_SP,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))
from build_check import compile_tu_armv6k  # noqa: E402

FUNC_NAME = "engine_func_002bc9d8"
ORIG_ADDR = 0x002BC9D8
ORIG_HALFWORDS = [
    0x2C02, 0xE240, 0x01B4, 0xE59F, 0x4010, 0xE92D, 0x000F, 0xE352,
    0x009C, 0xE590, 0xF102, 0x379F, 0x8010, 0xE8BD, 0xCA30, 0x002B,
    0xCA38, 0x002B, 0xCA60, 0x002B, 0xCA7C, 0x002B, 0xCA84, 0x002B,
    0xCA8C, 0x002B, 0xCA94, 0x002B, 0xCA9C, 0x002B, 0xCAA8, 0x002B,
    0xCAB4, 0x002B, 0xCABC, 0x002B, 0xCAC4, 0x002B, 0xCACC, 0x002B,
    0xCB34, 0x002B, 0xCB88, 0x002B, 0x002C, 0xE590, 0x003C, 0xEA00,
    0x2158, 0xE59F, 0x30A0, 0xE592, 0x0000, 0xE153, 0x0003, 0x1A00,
    0x0011, 0xE5D2, 0x0000, 0xE350, 0x0001, 0x13A0, 0x0034, 0x1A00,
    0x0000, 0xE3A0, 0x0032, 0xEA00, 0x3134, 0xE59F, 0x2004, 0xE590,
    0x3000, 0xE593, 0x2002, 0xE043, 0x200C, 0xE580, 0x2000, 0xE581,
    0x8010, 0xE8BD, 0x0020, 0xE590, 0x0029, 0xEA00, 0x0008, 0xE590,
    0x0027, 0xEA00, 0x001C, 0xE590, 0x0025, 0xEA00, 0x0004, 0xE590,
    0x0023, 0xEA00, 0x0000, 0xE350, 0x0000, 0x1590, 0x0020, 0xEA00,
    0x00EC, 0xE59F, 0x0000, 0xE590, 0x001D, 0xEA00, 0x0010, 0xE590,
    0x001B, 0xEA00, 0x0028, 0xE590, 0x0019, 0xEA00, 0x0018, 0xE590,
    0x0017, 0xEA00, 0x2028, 0xE590, 0x3020, 0xE590, 0x0002, 0xE153,
    0xFFC4, 0xDAFF, 0x0018, 0xE590, 0x2182, 0xE062, 0x0102, 0xE7D0,
    0x0005, 0xE350, 0xF100, 0x379F, 0x8010, 0xE8BD, 0xCB08, 0x002B,
    0xCB10, 0x002B, 0xCB18, 0x002B, 0xCB20, 0x002B, 0xCB28, 0x002B,
    0x0E31, 0xE3A0, 0x0006, 0xEA00, 0x0088, 0xE59F, 0x0004, 0xEA00,
    0x0084, 0xE59F, 0x0002, 0xEA00, 0x0080, 0xE59F, 0x0000, 0xEA00,
    0x0FC5, 0xE3A0, 0x0000, 0xE581, 0x8010, 0xE8BD, 0x2020, 0xE590,
    0x3028, 0xE590, 0x0003, 0xE152, 0xFFAA, 0xDAFF, 0x2018, 0xE590,
    0x3183, 0xE063, 0xC103, 0xE7D2, 0x0001, 0xE35C, 0xFFA5, 0x1AFF,
    0xE004, 0xE3A0, 0x3103, 0xE08E, 0xC008, 0xE3A0, 0x2003, 0xE792,
    0x2000, 0xE581, 0x2028, 0xE590, 0x0018, 0xE590, 0x2182, 0xE062,
    0x2102, 0xE08C, 0x0002, 0xE790, 0x0004, 0xE581, 0x8010, 0xE8BD,
    0x001C, 0xE59F, 0x4010, 0xE8BD, 0x2004, 0xE3A0, 0xF7B1, 0xEAF9,
    0x6290, 0x004C, 0x52A0, 0x0046, 0x0311, 0x0000, 0x0312, 0x0000,
    0x0313, 0x0000, 0x0058, 0x0040,
]
ORIG_BYTES = struct.pack("<" + "H" * len(ORIG_HALFWORDS), *ORIG_HALFWORDS)

CAND_BASE = 0x01000000
STACK_BASE = 0x02000000
STACK_SIZE = 0x10000
RET_ADDR = 0x03000000
DATA_BASE = 0x00400000
DATA_SIZE = 0x00100000
CTX_ADDR = 0x00480000
ARR_ADDR = 0x00490000
OUT_ADDR = 0x004A0000
STUB_0013AA60 = 0x0013AA60


def load_elf_text_and_rodata(obj_path: pathlib.Path, func_name: str, base_addr: int):
    data = obj_path.read_bytes()
    e_shoff, = struct.unpack_from("<I", data, 0x20)
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 0x2E)
    sections = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        sh = struct.unpack_from("<10I", data, off)
        sections.append(sh)
    shstr_off = sections[e_shstrndx][4]

    def get_name(idx: int) -> str:
        end = data.index(b"\x00", shstr_off + idx)
        return data[shstr_off + idx : end].decode("ascii", errors="replace")

    sec_names = [get_name(sh[0]) for sh in sections]
    symtab_idx = next(i for i, sh in enumerate(sections) if sh[1] == 2)
    strtab_idx = sections[symtab_idx][6]
    strtab_off = sections[strtab_idx][4]
    sym_off = sections[symtab_idx][4]
    sym_size = sections[symtab_idx][5]
    sym_entsize = sections[symtab_idx][9]

    def get_sym_name(idx: int) -> str:
        end = data.index(b"\x00", strtab_off + idx)
        return data[strtab_off + idx : end].decode("ascii", errors="replace")

    symbols = []
    for off in range(sym_off, sym_off + sym_size, sym_entsize):
        st_name, st_value, st_size, st_info, st_other, st_shndx = struct.unpack_from(
            "<IIIBBH", data, off
        )
        symbols.append((get_sym_name(st_name), st_value, st_size, st_info, st_shndx))

    # Place allocatable sections sequentially from base_addr.
    sec_addrs = {}
    image = bytearray()
    for i, sh in enumerate(sections):
        sh_type, sh_flags, _, sh_offset, sh_size, _, _, sh_addralign = sh[1:9]
        if (sh_flags & 0x2) and sh_size > 0:
            align = max(4, sh_addralign)
            pad = (-len(image)) % align
            image.extend(b"\x00" * pad)
            sec_addrs[i] = base_addr + len(image)
            if sh_type == 8:  # SHT_NOBITS
                image.extend(b"\x00" * sh_size)
            else:
                image.extend(data[sh_offset : sh_offset + sh_size])

    target_sym = next(s for s in symbols if s[0] == func_name)
    target_addr = sec_addrs[target_sym[4]] + target_sym[1]
    target_size = target_sym[2]

    # Apply SHT_REL relocations.
    for i, sh in enumerate(sections):
        if sh[1] != 9:  # SHT_REL
            continue
        target_sec = sh[7]
        if target_sec not in sec_addrs:
            continue
        rel_off = sh[4]
        rel_size = sh[5]
        rel_entsize = sh[9]
        for off in range(rel_off, rel_off + rel_size, rel_entsize):
            r_offset, r_info = struct.unpack_from("<II", data, off)
            r_type = r_info & 0xFF
            r_sym = r_info >> 8
            sym = symbols[r_sym]
            if sym[4] in sec_addrs:
                S = sec_addrs[sym[4]] + sym[1]
            else:
                S = 0
            P = sec_addrs[target_sec] + r_offset
            img_off = P - base_addr
            if r_type in (2, 38):  # R_ARM_ABS32 / R_ARM_TARGET1
                A, = struct.unpack_from("<I", image, img_off)
                struct.pack_into("<I", image, img_off, (S + A) & 0xFFFFFFFF)
            elif r_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
                insn, = struct.unpack_from("<I", image, img_off)
                imm24 = insn & 0x00FFFFFF
                if imm24 & 0x00800000:
                    imm24 -= 0x01000000
                A = imm24 << 2
                val = ((S + A - P) >> 2) & 0x00FFFFFF
                struct.pack_into("<I", image, img_off, (insn & 0xFF000000) | val)

    return bytes(image), target_addr, target_size


def run_case(code_bytes, entry_addr, is_orig, case_cfg):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00300000, UC_PROT_ALL)
    uc.mem_map(DATA_BASE, DATA_SIZE, UC_PROT_ALL)
    uc.mem_map(CAND_BASE, 0x00100000, UC_PROT_ALL)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_ALL)
    uc.mem_map(RET_ADDR, 0x1000, UC_PROT_ALL)

    if is_orig:
        uc.mem_write(ORIG_ADDR, code_bytes)
    else:
        uc.mem_write(CAND_BASE, code_bytes)

    uc.mem_write(STUB_0013AA60, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(RET_ADDR, struct.pack("<I", 0xE12FFF1E))

    # Populate globals and ctx.
    uc.mem_write(0x004C6290 + 0x9C, struct.pack("<I", case_cfg["ctx_ptr"]))
    uc.mem_write(0x004C6290 + 0xA0, struct.pack("<I", case_cfg["cmp_ctx"]))
    uc.mem_write(0x004C6290 + 0x11, struct.pack("<B", case_cfg["flag_11"]))
    uc.mem_write(0x004652A0, struct.pack("<I", case_cfg["cursor"]))

    if case_cfg["ctx_ptr"] != 0:
        c = case_cfg["ctx_ptr"]
        uc.mem_write(c + 0x00, struct.pack("<I", case_cfg["f00"]))
        uc.mem_write(c + 0x04, struct.pack("<I", case_cfg["f04"]))
        uc.mem_write(c + 0x08, struct.pack("<I", case_cfg["f08"]))
        uc.mem_write(c + 0x0C, struct.pack("<I", case_cfg["f0c"]))
        uc.mem_write(c + 0x10, struct.pack("<I", case_cfg["f10"]))
        uc.mem_write(c + 0x18, struct.pack("<I", ARR_ADDR))
        uc.mem_write(c + 0x1C, struct.pack("<I", case_cfg["f1c"]))
        uc.mem_write(c + 0x20, struct.pack("<i", case_cfg["count"]))
        uc.mem_write(c + 0x28, struct.pack("<i", case_cfg["idx"]))
        uc.mem_write(c + 0x2C, struct.pack("<I", case_cfg["f2c"]))

    for idx, entry in enumerate(case_cfg["entries"]):
        base = ARR_ADDR + idx * 28
        uc.mem_write(base + 0, struct.pack("<B", entry[0]))
        uc.mem_write(base + 4, struct.pack("<I", entry[1]))
        uc.mem_write(base + 8, struct.pack("<I", entry[2]))

    uc.mem_write(OUT_ADDR, struct.pack("<II", 0xDEADBEEF, 0xCAFEBABE))

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_C1_C0_2, uc.reg_read(UC_ARM_REG_C1_C0_2) | 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 0x100)
    uc.reg_write(UC_ARM_REG_LR, RET_ADDR)
    uc.reg_write(UC_ARM_REG_R0, case_cfg["op"])
    uc.reg_write(UC_ARM_REG_R1, OUT_ADDR)

    calls = []

    def hook_code(uc_inst, address, size, user_data):
        if address == STUB_0013AA60:
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(UC_ARM_REG_R2)
            calls.append((r0, r1, r2))
            uc_inst.mem_write(r1, struct.pack("<I", 0x12345678))

    uc.hook_add(1 << 2, hook_code)  # UC_HOOK_CODE = 4
    uc.emu_start(entry_addr, RET_ADDR, timeout=5_000_000, count=10_000)

    out0, out1 = struct.unpack("<II", uc.mem_read(OUT_ADDR, 8))
    f0c = (
        struct.unpack("<I", uc.mem_read(case_cfg["ctx_ptr"] + 0x0C, 4))[0]
        if case_cfg["ctx_ptr"] != 0
        else None
    )
    return (out0, out1, f0c, calls)


def build_cases():
    base = {
        "op": 0x200,
        "ctx_ptr": CTX_ADDR,
        "cmp_ctx": CTX_ADDR,
        "flag_11": 1,
        "cursor": 0x00466000,
        "f00": 0x11110000,
        "f04": 0x00465300,
        "f08": 0x22220008,
        "f0c": 0x3333000C,
        "f10": 0x44440010,
        "f1c": 0x5555001C,
        "f2c": 0x6666002C,
        "count": 4,
        "idx": 1,
        "entries": [
            (0, 0xAAAAAAAA, 0xBBBBBBBB),
            (1, 0x12340001, 0x56780002),
            (2, 0x99990001, 0x88880002),
            (4, 0x77770001, 0x66660002),
        ],
    }
    cases = []
    for op in range(0x1FE, 0x211):
        c = dict(base)
        c["op"] = op
        cases.append((f"op_{op:#x}", c))

    # 0x201 variants
    for cmp_ctx, flag_11 in [(CTX_ADDR, 0), (CTX_ADDR + 4, 1), (CTX_ADDR + 4, 0)]:
        c = dict(base)
        c["op"] = 0x201
        c["cmp_ctx"] = cmp_ctx
        c["flag_11"] = flag_11
        cases.append((f"op_0x201_cmp_{cmp_ctx:#x}_f_{flag_11}", c))

    # 0x207 with null ctx
    c = dict(base)
    c["op"] = 0x207
    c["ctx_ptr"] = 0
    cases.append(("op_0x207_null", c))

    # 0x20c variants: count <= idx, kinds 0..5
    for idx, count, kind in [
        (1, 1, 0),
        (2, 1, 0),
        (-1, 0, 0),
        (0, 4, 0),
        (1, 4, 1),
        (2, 4, 2),
        (3, 4, 3),
        (3, 4, 4),
        (3, 4, 5),
    ]:
        c = dict(base)
        c["op"] = 0x20C
        c["idx"] = idx
        c["count"] = count
        c["entries"] = list(base["entries"])
        if 0 <= idx < len(c["entries"]):
            c["entries"][idx] = (kind, 0x1111, 0x2222)
        cases.append((f"op_0x20c_idx_{idx}_cnt_{count}_k_{kind}", c))

    # 0x20d variants: count <= idx, kind != 1, kind == 1
    for idx, count, kind in [(1, 1, 1), (2, 1, 1), (0, 4, 0), (1, 4, 1), (2, 4, 2)]:
        c = dict(base)
        c["op"] = 0x20D
        c["idx"] = idx
        c["count"] = count
        cases.append((f"op_0x20d_idx_{idx}_cnt_{count}_k_{kind}", c))

    return cases


class TestEngineFunc002bc9d8(unittest.TestCase):
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
            obj_path, FUNC_NAME, CAND_BASE
        )
        cls.cases = build_cases()

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def test_differential(self):
        for name, cfg in self.cases:
            with self.subTest(name=name):
                got_orig = run_case(ORIG_BYTES, ORIG_ADDR, True, cfg)
                got_cand = run_case(self.cand_img, self.cand_addr, False, cfg)
                self.assertEqual(got_cand, got_orig, f"Mismatch on {name}")

    def test_negative_controls(self):
        mutants = [
            ("wrong_op_0x201_flag", 0x201, {"flag_11": 0}, lambda r: (1, r[1], r[2], r[3])),
            ("wrong_op_0x202_sub", 0x202, {}, lambda r: (r[0] + 1, r[1], r[2], r[3])),
            ("wrong_op_0x20c_kind", 0x20C, {}, lambda r: (0x999, r[1], r[2], r[3])),
            ("wrong_op_0x20d_second_word", 0x20D, {}, lambda r: (r[0], r[1] ^ 1, r[2], r[3])),
            ("wrong_op_0x20e_no_call", 0x20E, {}, lambda r: (r[0], r[1], r[2], [])),
        ]
        base_cfg = dict(self.cases[0][1])
        for mname, op, overrides, mutate in mutants:
            with self.subTest(mutant=mname):
                cfg = dict(base_cfg)
                cfg["op"] = op
                cfg.update(overrides)
                orig = run_case(ORIG_BYTES, ORIG_ADDR, True, cfg)
                cand = run_case(self.cand_img, self.cand_addr, False, cfg)
                self.assertEqual(cand, orig)
                self.assertNotEqual(mutate(cand), orig)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestEngineFunc002bc9d8)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print(
        f"PASS: {len(TestEngineFunc002bc9d8.cases)} cases + 5/5 mutants "
        f"(candidate {TestEngineFunc002bc9d8.cand_size} B)"
    )
