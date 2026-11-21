#!/usr/bin/env python3
"""Differential test for camp_func_0022d33c (0x0022d33c) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_0022d33c"

FUNC_ADDR = 0x0022D33C
FUNC_SIZE = 652

G_LAST_ADDR = 0x0043D9C8
G_ARR_ADDR = 0x0049357C
G_OUT_ADDR = 0x004935CC
G_PCOL_ADDR = 0x0049375C

SELF_ADDR = 0x20000000
ITEM_INFO_ADDR = 0x20002000
POS0_ADDR = 0x20003000
POS1_ADDR = 0x20003100
RODATA_ADDR = 0x20008000

STUBS = {
    0x0029EBC4: "shop_func_0029ebc4",
    0x002338AC: "unite_func_002338ac",
    0x002B9364: "camp_func_002b9364",
    0x002BF6C8: "camp_func_002bf6c8",
    0x0029D100: "camp_func_0029d100",
    0x002BE7FC: "ui_func_002be7fc",
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
            if name == "camp_func_0022d33c":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("camp_func_0022d33c not found in object")

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
    w28: int,
    start_idx: int,
    last_idx: int,
    count: int,
    b94: int,
    ba4: int,
    ba5: int,
    c_val: int,
    d_val: int,
    price_mode0: int,
    price_mode1: int,
) -> tuple[bytes, bytes, list[tuple], dict[str, int]]:
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
        if base_addr == FUNC_ADDR and addr == 0x002BE7FC:
            uc.mem_write(addr, struct.pack("<H", 0x4770))
        else:
            uc.mem_write(addr, make_stub_bx_lr())

    uc.mem_write(G_LAST_ADDR, struct.pack("<II", 0, last_idx))
    uc.mem_write(G_ARR_ADDR, b"\x00" * 0x240)

    self_buf = bytearray(0x800)
    struct.pack_into("<I", self_buf, 0x28, w28)
    self_buf[0x94] = b94 & 0xFF
    self_buf[0x5A4] = ba4 & 0xFF
    self_buf[0x5A5] = ba5 & 0xFF
    for i in range(4):
        off = 0x5AC + (start_idx + i) * 32
        struct.pack_into("<H", self_buf, off + 0x00, 100 + i)
        self_buf[off + 0x0C] = c_val
        self_buf[off + 0x0D] = d_val
    uc.mem_write(SELF_ADDR, bytes(self_buf))

    uc.mem_write(ITEM_INFO_ADDR, bytes([0, 0, 0, 55]))
    uc.mem_write(POS0_ADDR, b"\x00" * 8 + struct.pack("<hh", 10, 20))
    uc.mem_write(POS1_ADDR, b"\x00" * 8 + struct.pack("<hh", 3, -5))

    uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
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
        if tag == "shop_func_0029ebc4":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, start_idx)
        elif tag == "unite_func_002338ac":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, count)
        elif tag == "camp_func_002b9364":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ITEM_INFO_ADDR)
        elif tag == "camp_func_002bf6c8":
            calls.append((tag, r0, r1))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, POS1_ADDR if r1 == 0x4C6 else POS0_ADDR)
        elif tag == "camp_func_0029d100":
            sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
            s0 = struct.unpack_from("<I", uc_inst.mem_read(sp, 4))[0]
            calls.append((tag, r0, r1, r2, r3, s0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, price_mode0 if r1 == 0 else price_mode1)
        elif tag == "ui_func_002be7fc":
            fmt = bytes(uc_inst.mem_read(r1, 8)).split(b"\x00", 1)[0]
            out = f"{r2:8d}".encode("ascii") + b"\x00"
            uc_inst.mem_write(r0, out)
            calls.append((tag, fmt, r2))

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    out_last = bytes(uc.mem_read(G_LAST_ADDR, 8))
    out_arr = bytes(uc.mem_read(G_ARR_ADDR, 0x240))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return out_last, out_arr, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs, cand_rodata = compile_candidate()

    cases = [
        ("w28_0", 0, 1, 0, 2, 100, 0, 0, 10, 20, 500, 500),
        ("same_idx", 1, 2, 2, 2, 100, 0, 0, 10, 20, 500, 500),
        ("count_0", 1, 1, 2, 0, 100, 0, 0, 10, 20, 500, 500),
        ("ba4_0_mode0", 1, 1, 2, 2, 99, 0, 0, 10, 20, 500, 500),
        ("ba4_0_mode2", 1, 1, 2, 2, 100, 0, 2, 10, 20, 500, 500),
        ("ba4_1_mode1_gt_cheaper", 1, 1, 2, 2, 100, 1, 1, 30, 10, 500, 400),
        ("ba4_1_mode1_lt_pricier", 1, 1, 2, 2, 100, 1, 1, 10, 30, 500, 600),
    ]

    for name, *args in cases:
        o_l, o_a, o_c, o_r = run_one(orig_code, FUNC_ADDR, None, b"", *args)
        c_l, c_a, c_c, c_r = run_one(cand_code, 0x00180000, cand_relocs, cand_rodata, *args)
        if (o_l, o_a) != (c_l, c_a):
            print(f"FAIL {name}: memory mismatch")
            return 1
        if o_c != c_c:
            print(f"FAIL {name}: calls mismatch\n  orig={o_c}\n  cand={c_c}")
            return 1
        if o_r != c_r:
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
        o_l, o_a, o_c, _ = run_one(orig_code, FUNC_ADDR, None, b"", *case_args)
        m_l, m_a, m_c, _ = run_one(bytes(mc), 0x00180000, None, cand_rodata, *case_args)
        return (m_l, m_a, m_c) != (o_l, o_a, o_c)

    def mut_nop_reloc(reloc_idx: int):
        def _fn(mc: bytearray) -> bool:
            if reloc_idx >= len(cand_relocs):
                return False
            off = cand_relocs[reloc_idx][1]
            struct.pack_into("<I", mc, off, 0xE1A00000)
            return True
        return _fn

    mut_specs = [
        (mut_nop_reloc(0), cases[3][1:]),
        (mut_nop_reloc(1), cases[3][1:]),
        (mut_nop_reloc(2), cases[3][1:]),
        (mut_nop_reloc(3), cases[3][1:]),
        (mut_nop_reloc(9), cases[3][1:]),
    ]
    mutants_ok = sum(1 for fn, cargs in mut_specs if check_mutant(fn, cargs))
    if mutants_ok != 5:
        print(f"FAIL: detected only {mutants_ok}/5 mutants")
        return 1

    print(
        f"PASS: camp_func_0022d33c (0x{FUNC_ADDR:08x}) matched original across "
        f"{len(cases)} cases and detected {mutants_ok}/5 mutants "
        f"(candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
