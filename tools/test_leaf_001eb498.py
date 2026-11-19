#!/usr/bin/env python3
"""Differential test for engine_func_001eb498 (0x001eb498) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_001eb498"

FUNC_ADDR = 0x001EB498
FUNC_SIZE = 628

TABLE_ADDR = 0x00464DA8
SRC_ADDR = 0x20000000
DST_ADDR = 0x20001000
STR_BASE = 0x20002000

STUBS = {
    0x0017F928: "engine_func_0017f928",
    0x002C3290: "engine_func_002c3290",
    0x002B45F8: "engine_func_002b45f8",
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


def compile_candidate() -> tuple[bytes, list[tuple[str, int]]]:
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
    text_data = data[shdrs[tidx][4] : shdrs[tidx][4] + shdrs[tidx][5]]
    symtab = next(s for s in shdrs if s[1] == 2)
    strtab_off = shdrs[symtab[6]][4]

    fn_off = fn_size = None
    for i in range(symtab[5] // 16):
        st_name, st_value, st_size, st_info, _, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + i * 16)
        if st_shndx == tidx:
            name = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
            if name == "engine_func_001eb498":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("engine_func_001eb498 not found in object")

    relocs: list[tuple[str, int]] = []
    for s in shdrs:
        if s[1] == 9 and s[7] == tidx:
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if fn_off <= r_off < fn_off + fn_size and r_type in (28, 29):
                    st_name = struct.unpack_from("<I", data, symtab[4] + sym_idx * 16)[0]
                    sname = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
                    relocs.append((sname, r_off - fn_off))

    return bytes(text_data[fn_off : fn_off + fn_size]), relocs


def patch_bl(code: bytearray, at_off: int, src_pc: int, dst_pc: int) -> None:
    delta = (dst_pc - (src_pc + 8)) >> 2
    hi = code[at_off + 3]
    insn = (hi << 24) | (delta & 0x00FFFFFF)
    struct.pack_into("<I", code, at_off, insn)


def run_one(
    code_bytes: bytes,
    base_addr: int,
    relocs: list[tuple[str, int]] | None,
    src_bytes: bytes,
    count_only: int,
) -> tuple[int, bytes, dict[str, int]]:
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
    for addr in STUBS:
        uc.mem_write(addr, make_stub_bx_lr())

    # Build a synthetic tag table at 0x00464DA8 terminated by 0xF890
    uc.mem_write(STR_BASE + 0x00, b"<col:\x00")
    uc.mem_write(STR_BASE + 0x20, b"<wait>\x00")
    uc.mem_write(STR_BASE + 0x40, b"<skip>\x00")
    entries = [
        (0xF802, 1, STR_BASE + 0x00),   # <col:1a> -> 0x02F8 + arg+1
        (0xF803, 0, STR_BASE + 0x20),   # <wait> -> 0x03F8
        (0xFFFF, 0, STR_BASE + 0x40),   # <skip> -> code==0xFFFF falls back to char
        (0xF810, 2, 0),                 # raw 0xF810 with 2 extra u16s
        (0xF890, 0, 0),                 # sentinel
    ]
    tbl = bytearray(len(entries) * 16)
    for i, (code, arg_cnt, sptr) in enumerate(entries):
        struct.pack_into("<HHII", tbl, i * 16, code, 0, arg_cnt, 0)
        struct.pack_into("<I", tbl, i * 16 + 12, sptr)
    uc.mem_write(TABLE_ADDR, bytes(tbl))

    uc.mem_write(SRC_ADDR, src_bytes)
    uc.mem_write(DST_ADDR, b"\xAA" * 0x80)

    uc.reg_write(arm.UC_ARM_REG_R0, SRC_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, DST_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R2, count_only)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)

    def hook_code(uc_inst, address, size, user_data):
        tag = STUBS.get(address)
        if tag == "engine_func_0017f928":
            r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0) & 0xFF
            r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1) & 0xFF
            # Note: cur[1] passed as r0, cur[0] passed as r1 -> (r1 << 8) | r0
            val = (r1 << 8) | r0
            uc_inst.reg_write(arm.UC_ARM_REG_R0, val)
        elif tag == "engine_func_002c3290":
            r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            s = bytes(uc_inst.mem_read(r0, 32)).split(b"\x00", 1)[0]
            uc_inst.reg_write(arm.UC_ARM_REG_R0, len(s))
        elif tag == "engine_func_002b45f8":
            r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
            s0 = bytes(uc_inst.mem_read(r0, r2))
            s1 = bytes(uc_inst.mem_read(r1, r2))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, 0 if s0 == s1 else 1)

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    ret = uc.reg_read(arm.UC_ARM_REG_R0)
    out_dst = bytes(uc.mem_read(DST_ADDR, 0x80))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return ret, out_dst, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs = compile_candidate()

    cases = [
        ("empty_ff_ff", b"\xFF\xFF", 0),
        ("plain_chars", b"AB\xFF\xFF", 0),
        ("count_only", b"<col:1a>AB<wait>\xFF\xFF", 1),
        ("col_hex_lower_upper_ff", b"<col:1a><col:FF><col:0B>\xFF\xFF", 0),
        ("wait_and_skip_tag", b"<wait><skip>\xFF\xFF", 0),
        ("raw_f810_2extra", b"\x10\xF8\x12\x34\x56\x78\xFF\xFF", 0),
    ]

    for name, *args in cases:
        o_ret, o_dst, o_regs = run_one(orig_code, FUNC_ADDR, None, *args)
        c_ret, c_dst, c_regs = run_one(cand_code, 0x00180000, cand_relocs, *args)
        if o_ret != c_ret or o_dst != c_dst:
            print(f"FAIL {name}: mismatch orig_ret={o_ret} cand_ret={c_ret}")
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
        o_r, o_d, _ = run_one(orig_code, FUNC_ADDR, None, *case_args)
        m_r, m_d, _ = run_one(bytes(mc), 0x00180000, None, *case_args)
        return (m_r, m_d) != (o_r, o_d)

    def mut_nop_reloc(reloc_idx: int):
        def _fn(mc: bytearray) -> bool:
            if reloc_idx >= len(cand_relocs):
                return False
            off = cand_relocs[reloc_idx][1]
            struct.pack_into("<I", mc, off, 0xE1A00000)
            return True
        return _fn

    def mut_flip_cond(target_idx: int):
        def _fn(mc: bytearray) -> bool:
            seen = 0
            for i in range(0, len(mc), 4):
                w = struct.unpack_from("<I", mc, i)[0]
                if (w & 0x0E000000) == 0x0A000000 and (w >> 28) in (0x0, 0x1):
                    if seen == target_idx:
                        struct.pack_into("<I", mc, i, (w & 0x0FFFFFFF) | (((w >> 28) ^ 1) << 28))
                        return True
                    seen += 1
            return False
        return _fn

    mut_specs = [
        (mut_nop_reloc(0), cases[1][1:]),
        (mut_nop_reloc(1), cases[1][1:]),
        (mut_nop_reloc(3), cases[3][1:]),
        (mut_nop_reloc(5), cases[5][1:]),
        (mut_flip_cond(1), cases[2][1:]),
    ]
    mutants_ok = sum(1 for fn, cargs in mut_specs if check_mutant(fn, cargs))
    if mutants_ok != 5:
        print(f"FAIL: detected only {mutants_ok}/5 mutants")
        return 1

    print(
        f"PASS: engine_func_001eb498 (0x{FUNC_ADDR:08x}) matched original across "
        f"{len(cases)} cases and detected {mutants_ok}/5 mutants "
        f"(candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
