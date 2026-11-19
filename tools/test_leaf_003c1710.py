#!/usr/bin/env python3
"""Differential test for ui_func_003c1710 (0x003c1710) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_003c1710"

FUNC_ADDR = 0x003C1710
FUNC_SIZE = 612

G_ADDR = 0x00439CE0
OBJ_ADDR = 0x20000000
UNIT_ADDR = 0x20001000
RODATA_ADDR = 0x20008000

STUBS = {
    0x00282B94: "ui_func_00282b94",
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
    ridx = next((i for i in range(e_shnum) if sh_name(i) == ".rodata"), None)
    text_data = bytearray(data[shdrs[tidx][4] : shdrs[tidx][4] + shdrs[tidx][5]])
    rodata = data[shdrs[ridx][4] : shdrs[ridx][4] + shdrs[ridx][5]] if ridx is not None else b""
    symtab = next(s for s in shdrs if s[1] == 2)
    strtab_off = shdrs[symtab[6]][4]

    fn_off = fn_size = None
    for i in range(symtab[5] // 16):
        st_name, st_value, st_size, st_info, _, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + i * 16)
        if st_shndx == tidx:
            name = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
            if name == "ui_func_003c1710":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("ui_func_003c1710 not found in object")

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
                    elif r_type == 2 and ridx is not None:
                        st_value, st_shndx = struct.unpack_from("<IH", data, symtab[4] + sym_idx * 16)[0:2]
                        # read st_value (4), skip st_size (4), st_info (1), st_other (1), read st_shndx (2)
                        _, st_value, _, _, _, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + sym_idx * 16)
                        if st_shndx == ridx:
                            addend = struct.unpack_from("<I", text_data, r_off)[0]
                            struct.pack_into("<I", text_data, r_off, RODATA_ADDR + st_value + addend)

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
    flags_50: int,
    unit_ok: bool,
    unit_w0: int,
    unit_mask: int,
    obj_64: int,
    obj_6c: int,
    obj_80: int,
    obj_8c: int,
    obj_90: int,
    obj_94: int,
    fade_frames: int,
) -> tuple[bytes, list[tuple], dict[str, int]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_map(0x20000000, 0x00010000)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    cpacr = uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, cpacr | (0xF << 20))
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

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

    g = bytearray(0x20)
    struct.pack_into("<i", g, 0xC, fade_frames)
    struct.pack_into("<I", g, 0x18, 0x11223344)
    uc.mem_write(G_ADDR, bytes(g))

    obj = bytearray(0xA0)
    struct.pack_into("<I", obj, 0x50, flags_50)
    struct.pack_into("<h", obj, 0x62, -7)
    struct.pack_into("<I", obj, 0x64, obj_64)
    struct.pack_into("<I", obj, 0x6C, obj_6c)
    struct.pack_into("<i", obj, 0x80, obj_80)
    struct.pack_into("<I", obj, 0x8C, obj_8c)
    struct.pack_into("<I", obj, 0x90, obj_90)
    struct.pack_into("<I", obj, 0x94, obj_94)
    uc.mem_write(OBJ_ADDR, bytes(obj))

    unit = bytearray(0x200)
    struct.pack_into("<I", unit, 0x00, unit_w0)
    struct.pack_into("<H", unit, 0x1C6, unit_mask)
    uc.mem_write(UNIT_ADDR, bytes(unit))

    uc.reg_write(arm.UC_ARM_REG_R0, 0x12345678)
    uc.reg_write(arm.UC_ARM_REG_R1, OBJ_ADDR)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)
    uc.reg_write(arm.UC_ARM_REG_D8, 0x1122334455667788)
    uc.reg_write(arm.UC_ARM_REG_D9, 0x99AABBCCDDEEFF00)

    calls: list[tuple] = []

    def hook_code(uc_inst, address, size, user_data):
        tag = STUBS.get(address)
        if tag == "ui_func_00282b94":
            r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
            calls.append((tag, r0, r1))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, UNIT_ADDR if unit_ok else 0)

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    out_obj = bytes(uc.mem_read(OBJ_ADDR, 0xA0))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "d8": uc.reg_read(arm.UC_ARM_REG_D8),
        "d9": uc.reg_read(arm.UC_ARM_REG_D9),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return out_obj, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs, cand_rodata = compile_candidate()

    cases = [
        ("flag_off", 0, True, 0x80000, 0x3FF, 1, 0xAA0000FF, 0, 0, 0, 0, 10),
        ("unit_null", 2, False, 0x80000, 0x3FF, 1, 0xAA0000FF, 0, 0, 0, 0, 10),
        ("no_flag_80000", 2, True, 0x0, 0x3FF, 1, 0xAA0000FF, 0, 0, 0, 0, 10),
        ("obj64_ffff", 2, True, 0x80000, 0x3FF, 0xFFFF, 0xAA0000FF, 0, 0, 0, 0, 10),
        ("slot0_pick_7_interp", 2, True, 0x80000, 1 << 7, 1, 0x10203040, 2, 0x10203040, 0x52DEE7FF, 0, 10),
        ("slot5_color_change", 2, True, 0x80000, 1 << 5, 1, 0x10203040, 5, 0x00000000, 0x11111111, 5, 10),
        ("slot6_interp", 2, True, 0x80000, 1 << 6, 1, 0x80402010, 4, 0x80402010, 0xF721F9FF, 6, 10),
        ("slot8_hold_before_advance", 2, True, 0x80000, (1 << 8) | (1 << 3), 1, 0x0, 34, 0x0, 0xEFD629FF, 8, 10),
        ("slot8_advance_to_3", 2, True, 0x80000, (1 << 8) | (1 << 3), 1, 0x0, 35, 0x0, 0xEFD629FF, 8, 10),
        ("slot9_advance_wrap_to_2", 2, True, 0x80000, (1 << 9) | (1 << 2), 1, 0x0, 35, 0x0, 0x7E620CFF, 9, 10),
        ("default_color_no_next", 2, True, 0x80000, (1 << 4), 1, 0x0, 35, 0x0, 0x11223344, 4, 10),
    ]

    for name, *args in cases:
        o_obj, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, b"", *args)
        c_obj, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_relocs, cand_rodata, *args)
        if o_obj != c_obj:
            print(f"FAIL {name}: obj mismatch")
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
        o_o, o_c, _ = run_one(orig_code, FUNC_ADDR, None, b"", *case_args)
        m_o, m_c, _ = run_one(bytes(mc), 0x00180000, None, cand_rodata, *case_args)
        return (m_o, m_c) != (o_o, o_c)

    def mut_nop_bl(mc: bytearray) -> bool:
        off = cand_relocs[0][1]
        struct.pack_into("<I", mc, off, 0xE1A00000)
        return True

    def mut_flip_cond(target_cond: int):
        def _fn(mc: bytearray) -> bool:
            seen = 0
            for i in range(0, len(mc), 4):
                w = struct.unpack_from("<I", mc, i)[0]
                if (w & 0x0E000000) == 0x0A000000 and (w >> 28) in (0x0, 0x1):
                    if seen == target_cond:
                        new_cc = (w >> 28) ^ 1
                        struct.pack_into("<I", mc, i, (w & 0x0FFFFFFF) | (new_cc << 28))
                        return True
                    seen += 1
            return False
        return _fn

    mut_specs = [
        (mut_flip_cond(0), cases[0][1:]),
        (mut_flip_cond(2), cases[2][1:]),
        (mut_flip_cond(3), cases[3][1:]),
        (mut_flip_cond(4), cases[4][1:]),
        (mut_flip_cond(7), cases[5][1:]),
    ]
    mutants_ok = sum(1 for fn, cargs in mut_specs if check_mutant(fn, cargs))
    if mutants_ok != 5:
        print(f"FAIL: detected only {mutants_ok}/5 mutants")
        return 1

    print(
        f"PASS: ui_func_003c1710 (0x{FUNC_ADDR:08x}) matched original across "
        f"{len(cases)} cases and detected {mutants_ok}/5 mutants "
        f"(candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
