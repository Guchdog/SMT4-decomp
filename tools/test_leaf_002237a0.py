#!/usr/bin/env python3
"""Differential test for SaveLoad_Thread_func_002237a0 (0x002237a0) with Unicorn ARM."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_002237a0"

FUNC_ADDR = 0x002237A0
FUNC_SIZE = 632

SELF_ADDR = 0x20000000
ALLOC_RET = 0x20004000
RODATA_ADDR = 0x20008000

STUBS = {
    0x002C54D8: "engine_func_002c54d8",
    0x002C5468: "engine_func_002c5468",
    0x002C5450: "engine_func_002c5450",
    0x002C34A4: "engine_func_002c34a4",
    0x002BCF34: "nn_sdk_func_002bcf34",
    0x002BCE50: "nn_sdk_func_002bce50",
    0x002CBDAC: "func_002cbdac",
}

STACK_BASE = 0x7F000000
STACK_SIZE = 0x10000
STACK_INIT = STACK_BASE + STACK_SIZE - 0x200
LR_SENTINEL = 0x90000000

CALLEE_SAVED = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}


def make_stub_bx_lr() -> bytes:
    return struct.pack("<I", 0xE12FFF1E)


def compile_candidate() -> tuple[bytes, list[tuple[str, int]], bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_path = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj_path)
    if res.returncode != 0:
        raise RuntimeError(f"compile failed:\n{res.stderr}")

    data = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    shdrs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = shdrs[e_shstrndx][4]

    def sh_name(idx: int) -> str:
        off = shstr_off + shdrs[idx][0]
        return data[off : data.index(b"\x00", off)].decode("ascii", errors="replace")

    tidx = next(i for i in range(e_shnum) if sh_name(i) == ".text")
    text_data = bytearray(data[shdrs[tidx][4] : shdrs[tidx][4] + shdrs[tidx][5]])
    rodata_map: dict[int, int] = {}
    rodata_buf = bytearray()
    for i in range(e_shnum):
        if sh_name(i).startswith(".rodata"):
            while len(rodata_buf) % 4 != 0:
                rodata_buf.append(0)
            rodata_map[i] = RODATA_ADDR + len(rodata_buf)
            rodata_buf.extend(data[shdrs[i][4] : shdrs[i][4] + shdrs[i][5]])
    rodata = bytes(rodata_buf)
    symtab = next(s for s in shdrs if s[1] == 2)
    strtab_off = shdrs[symtab[6]][4]

    fn_off = fn_size = None
    for i in range(symtab[5] // 16):
        st_name, st_value, st_size, st_info, _, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + i * 16)
        if st_shndx == tidx:
            name = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
            if name == "SaveLoad_Thread_func_002237a0":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("SaveLoad_Thread_func_002237a0 not found in object")

    relocs: list[tuple[str, int]] = []
    for s in shdrs:
        if s[1] == 9 and s[7] == tidx:
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if fn_off <= r_off < fn_off + fn_size:
                    if r_type in (28, 29):
                        st_name = struct.unpack_from("<I", data, symtab[4] + sym_idx * 16)[0]
                        sname = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
                        relocs.append((sname, r_off - fn_off))
                    elif r_type == 2:
                        _, st_value, _, _, _, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + sym_idx * 16)
                        if st_shndx in rodata_map:
                            addend = struct.unpack_from("<I", text_data, r_off)[0]
                            struct.pack_into("<I", text_data, r_off, rodata_map[st_shndx] + st_value + addend)

    return bytes(text_data[fn_off : fn_off + fn_size]), relocs, rodata


def patch_bl(code: bytearray, at_off: int, src_pc: int, dst_pc: int) -> None:
    delta = (dst_pc - (src_pc + 8)) >> 2
    hi = code[at_off + 3]
    insn = (hi << 24) | (delta & 0x00FFFFFF)
    struct.pack_into("<I", code, at_off, insn)


def run_one(
    code_bytes: bytes,
    base_addr: int,
    relocs: list[tuple[str, int]] | None,
    rodata: bytes,
    mode: int,
    r_54d8: int,
    r_5450: int,
    r_ce50: int,
    r_bdac: int,
) -> tuple[int, bytes, list[tuple], dict[str, int]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_map(0x20000000, 0x00010000)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    buf = bytearray(code_bytes)
    if relocs is not None:
        name_to_addr = {v: k for k, v in STUBS.items()}
        for sym_name, off in relocs:
            target = name_to_addr.get(sym_name)
            if target is None:
                raise RuntimeError(f"unexpected relocation: {sym_name}")
            patch_bl(buf, off, base_addr + off, target)

    uc.mem_write(base_addr, bytes(buf))
    if rodata:
        uc.mem_write(RODATA_ADDR, rodata)
    for addr in STUBS:
        uc.mem_write(addr, make_stub_bx_lr())

    self_buf = bytearray(0x60)
    struct.pack_into("<II", self_buf, 0x34, 0x20008000, 0x2000)
    struct.pack_into("<I", self_buf, 0x4C, 0x99999999)
    uc.mem_write(SELF_ADDR, bytes(self_buf))

    uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, mode)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)

    calls: list[tuple] = []

    def hook_code(uc_inst, address, size, user_data):
        tag = STUBS.get(address)
        if tag is None:
            return
        r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc_inst.reg_read(arm.UC_ARM_REG_R3)
        if tag == "engine_func_002c54d8":
            calls.append((tag, r1, r2))
            uc_inst.mem_write(r0, struct.pack("<I", 0x12345678))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, r_54d8)
        elif tag == "engine_func_002c5468":
            calls.append((tag, r0))
        elif tag == "engine_func_002c5450":
            calls.append((tag, r1, r2))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, r_5450)
        elif tag == "engine_func_002c34a4":
            sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
            s = struct.unpack_from("<2I", uc_inst.mem_read(sp, 8))
            calls.append((tag, r0, r1, r2, r3, *s))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ALLOC_RET)
        elif tag == "nn_sdk_func_002bcf34":
            calls.append((tag, r0, r1, r2))
        elif tag == "nn_sdk_func_002bce50":
            desc = struct.unpack_from("<4I", uc_inst.mem_read(r1, 16))
            s3 = struct.unpack_from("<I", uc_inst.mem_read(r3, 4))[0]
            sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
            s = struct.unpack_from("<4I", uc_inst.mem_read(sp, 16))
            calls.append((tag, r0, desc, r2, s3, *s))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, r_ce50)
        elif tag == "func_002cbdac":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, r_bdac)

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    ret = uc.reg_read(arm.UC_ARM_REG_R0)
    out_self = bytes(uc.mem_read(SELF_ADDR, 0x60))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return ret, out_self, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs, cand_rodata = compile_candidate()

    cases = [
        ("mode0_ok", 0, 0, 0, 0, 1),
        ("mode1_neg_err_reported", 1, 0x80000001, 0x80000002, 0x80000003, 0),
        ("mode2_00600000_masked", 2, 0, 0, 0x80600001, 1),
        ("mode3_pos_fail", 3, 0, 0, 1, 0),
        ("mode9_default_e7e3ffff", 9, 0, 0, 0, 0),
    ]

    for name, *args in cases:
        o_ret, o_self, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, b"", *args)
        c_ret, c_self, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_relocs, cand_rodata, *args)
        if o_ret != c_ret or o_self != c_self:
            print(f"FAIL {name}: ret/self mismatch orig={o_ret} cand={c_ret}")
            return 1
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch\n  orig={o_calls}\n  cand={c_calls}")
            return 1
        if o_regs != c_regs:
            print(f"FAIL {name}: callee-saved mismatch")
            return 1

    # 5 mutation controls
    patched_cand = bytearray(cand_code)
    name_to_addr = {v: k for k, v in STUBS.items()}
    for sym_name, off in cand_relocs:
        patch_bl(patched_cand, off, 0x00180000 + off, name_to_addr[sym_name])

    def check_mutant(patch_fn, case_args):
        mc = bytearray(patched_cand)
        if not patch_fn(mc):
            return False
        o_r, o_s, o_c, _ = run_one(orig_code, FUNC_ADDR, None, b"", *case_args)
        m_r, m_s, m_c, _ = run_one(bytes(mc), 0x00180000, None, cand_rodata, *case_args)
        return (m_r, m_s, m_c) != (o_r, o_s, o_c)

    def mut_nop_reloc(reloc_idx: int):
        def _fn(mc: bytearray) -> bool:
            if reloc_idx >= len(cand_relocs):
                return False
            off = cand_relocs[reloc_idx][1]
            struct.pack_into("<I", mc, off, 0xE1A00000)
            return True
        return _fn

    mut_specs = [
        (mut_nop_reloc(0), cases[0][1:]),
        (mut_nop_reloc(1), cases[1][1:]),
        (mut_nop_reloc(2), cases[0][1:]),
        (mut_nop_reloc(4), cases[0][1:]),
        (mut_nop_reloc(len(cand_relocs) - 1), cases[0][1:]),
    ]
    mutants_ok = sum(1 for fn, cargs in mut_specs if check_mutant(fn, cargs))
    if mutants_ok != 5:
        print(f"FAIL: detected only {mutants_ok}/5 mutants")
        return 1

    print(
        f"PASS: SaveLoad_Thread_func_002237a0 (0x{FUNC_ADDR:08x}) matched original across "
        f"{len(cases)} cases and detected {mutants_ok}/5 mutants "
        f"(candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
