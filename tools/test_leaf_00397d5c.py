#!/usr/bin/env python3
"""Differential test for script_vm_func_00397d5c (0x00397d5c) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_00397d5c"

FUNC_ADDR = 0x00397D5C
FUNC_SIZE = 624

TABLE_ADDR = 0x00405160
TABLE_SIZE = 0x5A0

SELF_ADDR = 0x20000000
RES_PTR_ADDR = 0x20002000

STUBS = {
    0x0019DFBC: "script_vm_func_0019dfbc",
    0x00297674: "script_vm_func_00297674",
    0x00297178: "shop_func_00297178",
    0x002B8B78: "script_vm_func_002b8b78",
    0x002A0F88: "script_vm_func_002a0f88",
    0x00232974: "func_00232974",
    0x00295904: "script_vm_func_00295904",
    0x002971E4: "script_vm_func_002971e4",
    0x002AF854: "battle_func_002af854",
    0x0026A96C: "camp_func_0026a96c",
    0x00220EB4: "camp_func_00220eb4",
    0x00309F94: "camp_func_00309f94",
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
            if name == "script_vm_func_00397d5c":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("script_vm_func_00397d5c not found in object")

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
    table_bytes: bytes,
    b658: int,
    ret_2a0f88: int,
    ret_19dfbc: int,
    ret_297674: int,
    b29: int,
    b20: int,
    b649: int,
    res_val: int,
    len_val: int,
) -> tuple[bytes, list[tuple], dict[str, int]]:
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
    uc.mem_write(TABLE_ADDR, table_bytes)
    for addr in STUBS:
        uc.mem_write(addr, make_stub_bx_lr())

    self_buf = bytearray(0xA00)
    self_buf[0x20] = b20 & 0xFF
    self_buf[0x29] = b29 & 0xFF
    # Populate 9 big-endian SJIS-like entries at self + 0xB0 using entries from table1 & table2
    t1_first = struct.unpack_from(">H", table_bytes, 0)[0]
    t2_first = struct.unpack_from(">H", table_bytes, 0x410)[0]
    for i in range(9):
        val = t1_first if i % 2 == 0 else t2_first
        struct.pack_into(">H", self_buf, 0xB0 + i * 2, val)
    self_buf[0x649] = b649 & 0xFF
    struct.pack_into("<I", self_buf, 0x654, 0xCAFE0654)
    self_buf[0x658] = b658 & 0xFF
    uc.mem_write(SELF_ADDR, bytes(self_buf))
    uc.mem_write(RES_PTR_ADDR, struct.pack("<I", res_val))

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
        if tag == "script_vm_func_0019dfbc":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ret_19dfbc)
        elif tag == "script_vm_func_00297674":
            calls.append((tag,))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ret_297674)
        elif tag == "shop_func_00297178":
            calls.append((tag, r0, r1))
        elif tag == "script_vm_func_002b8b78":
            calls.append((tag, r0))
        elif tag == "script_vm_func_002a0f88":
            calls.append((tag,))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ret_2a0f88)
        elif tag == "func_00232974":
            calls.append((tag, r0))
            uc_inst.mem_write(r1, b"ABCDEFGH\x00" + b"\x00" * 11)
        elif tag == "script_vm_func_00295904":
            buf_bytes = bytes(uc_inst.mem_read(r1, 10))
            calls.append((tag, r0, buf_bytes))
        elif tag == "script_vm_func_002971e4":
            calls.append((tag, r0, r1))
        elif tag == "battle_func_002af854":
            calls.append((tag, r0, r1, r2))
        elif tag == "camp_func_0026a96c":
            calls.append((tag,))
        elif tag == "camp_func_00220eb4":
            buf_bytes = bytes(uc_inst.mem_read(r0, 18))
            calls.append((tag, buf_bytes, r1, r2))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, RES_PTR_ADDR)
        elif tag == "camp_func_00309f94":
            buf_bytes = bytes(uc_inst.mem_read(r0, 18))
            calls.append((tag, buf_bytes, r1))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, len_val)

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    out_self = bytes(uc.mem_read(SELF_ADDR, 0xA00))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return out_self, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    table_bytes = orig_all[TABLE_ADDR - 0x00100000 : TABLE_ADDR - 0x00100000 + TABLE_SIZE]
    cand_code, cand_relocs = compile_candidate()

    cases = [
        ("b658_0_gate_fail", 0, 0, 0, 0, 0, 0, 0, 0, 0),
        ("b658_0_init", 0, 1, 0, 0, 0, 0, 0, 0, 0),
        ("b658_1_not2", 1, 0, 1, 0, 0, 0, 0, 0, 0),
        ("b658_1_confirm_b29_1", 1, 0, 2, 1, 1, 0, 0, 0, 0),
        ("b658_1_confirm_b20_2", 1, 0, 2, 1, 0, 2, 0, 0, 0),
        ("b658_1_confirm_b20_6", 1, 0, 2, 1, 0, 6, 0, 0, 0),
        ("b658_1_confirm_b20_3", 1, 0, 2, 1, 0, 3, 0, 0, 0),
        ("b658_1_b649_2_cancel", 1, 0, 2, 0, 0, 0, 2, 0, 0),
        ("b658_1_b649_0_short_fail", 1, 0, 2, 0, 0, 0, 0, 0, 4),
        ("b658_1_b649_1_len6_ok", 1, 0, 2, 0, 0, 0, 1, 0, 6),
        ("b658_1_b649_0_res_nz_ok", 1, 0, 2, 0, 0, 0, 0, 1, 2),
    ]

    for name, *args in cases:
        o_self, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, table_bytes, *args)
        c_self, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_relocs, table_bytes, *args)
        if o_self != c_self:
            print(f"FAIL {name}: self mismatch")
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
        o_s, o_c, _ = run_one(orig_code, FUNC_ADDR, None, table_bytes, *case_args)
        m_s, m_c, _ = run_one(bytes(mc), 0x00180000, None, table_bytes, *case_args)
        return (m_s, m_c) != (o_s, o_c)

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
        (mut_nop_reloc(4), cases[1][1:]),
        (mut_nop_reloc(17), cases[9][1:]),
    ]
    mutants_ok = sum(1 for fn, cargs in mut_specs if check_mutant(fn, cargs))
    if mutants_ok != 5:
        print(f"FAIL: detected only {mutants_ok}/5 mutants")
        return 1

    print(
        f"PASS: script_vm_func_00397d5c (0x{FUNC_ADDR:08x}) matched original across "
        f"{len(cases)} cases and detected {mutants_ok}/5 mutants "
        f"(candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
