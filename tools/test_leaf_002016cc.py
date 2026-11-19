#!/usr/bin/env python3
"""Differential test for ui_func_002016cc (0x002016cc) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_002016cc"

FUNC_ADDR = 0x002016CC
FUNC_SIZE = 640

G_PTR_ADDR = 0x0044EA00
G_OBJ_ADDR = 0x20000000
STATE_ADDR = 0x20002000
ITEMS_ADDR = 0x20003000
APPLY_FN_ADDR = 0x00188000
RODATA_ADDR = 0x20008000

STUBS = {
    0x002C0AC8: "ui_func_002c0ac8",
    0x002C1B64: "ui_func_002c1b64",
    0x002C3BA8: "ui_func_002c3ba8",
    0x0032AF00: "func_0032af00",
    0x002C5F7C: "ui_func_002c5f7c",
    0x002C1D3C: "ui_func_002c1d3c",
    0x002B7A10: "func_002b7a10",
    0x002C1ABC: "ui_func_002c1abc",
    0x002BE77C: "ui_func_002be77c",
    0x00262A54: "script_vm_func_00262a54",
    APPLY_FN_ADDR: "apply_fn",
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
            if name == "ui_func_002016cc":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("ui_func_002016cc not found in object")

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
    mode_10: int,
    total_60: int,
    sel_68: int,
    alpha_6c: float,
    stack_dirty: int,
    blend_ret: int,
) -> tuple[int, bytes, list[tuple], dict[str, int]]:
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
        if base_addr == FUNC_ADDR and addr == 0x00262A54:
            uc.mem_write(addr, struct.pack("<H", 0x4770))
        else:
            uc.mem_write(addr, make_stub_bx_lr())

    uc.mem_write(G_PTR_ADDR, struct.pack("<I", G_OBJ_ADDR))
    stack_obj = bytearray(0x40)
    struct.pack_into("<I", stack_obj, 0x00, 0)
    struct.pack_into("<I", stack_obj, 0x08, 0x11111111)
    stack_obj[0x18] = stack_dirty
    struct.pack_into("<I", stack_obj, 0x1C, APPLY_FN_ADDR)
    uc.mem_write(G_OBJ_ADDR + 0x124C, bytes(stack_obj))

    state_buf = bytearray(0x80)
    struct.pack_into("<I", state_buf, 0x10, mode_10)
    struct.pack_into("<i", state_buf, 0x60, total_60)
    struct.pack_into("<I", state_buf, 0x64, ITEMS_ADDR)
    struct.pack_into("<i", state_buf, 0x68, sel_68)
    struct.pack_into("<f", state_buf, 0x6C, alpha_6c)
    uc.mem_write(STATE_ADDR, bytes(state_buf))

    items_buf = bytearray(16 * 0x228)
    for i in range(16):
        s = f"item_{i:02d}".encode("ascii") + b"\x00"
        items_buf[i * 0x228 : i * 0x228 + len(s)] = s
    uc.mem_write(ITEMS_ADDR, bytes(items_buf))

    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)
    uc.reg_write(arm.UC_ARM_REG_D8, 0x1122334455667788)
    uc.reg_write(arm.UC_ARM_REG_D9, 0x99AABBCCDDEEFF00)

    calls: list[tuple] = []

    def hook_code(uc_inst, address, size, user_data):
        tag = STUBS.get(address)
        if tag is None:
            return
        r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc_inst.reg_read(arm.UC_ARM_REG_R3)
        if tag == "ui_func_002c0ac8":
            calls.append((tag,))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, STATE_ADDR)
        elif tag in ("ui_func_002c1b64", "ui_func_002c3ba8", "ui_func_002c1abc"):
            calls.append((tag, r0))
        elif tag == "func_0032af00":
            calls.append((tag,))
        elif tag == "ui_func_002c5f7c":
            calls.append((tag, r0, r1))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, blend_ret)
        elif tag == "apply_fn":
            calls.append((tag, r0))
        elif tag == "ui_func_002c1d3c":
            calls.append((tag, r0, r1))
        elif tag == "func_002b7a10":
            q0 = struct.unpack("<4f", uc_inst.mem_read(r0, 16))
            s0 = uc_inst.reg_read(arm.UC_ARM_REG_S0)
            s1 = uc_inst.reg_read(arm.UC_ARM_REG_S1)
            s2 = uc_inst.reg_read(arm.UC_ARM_REG_S2)
            s3 = uc_inst.reg_read(arm.UC_ARM_REG_S3)
            s4 = uc_inst.reg_read(arm.UC_ARM_REG_S4)
            calls.append((tag, q0, s0, s1, s2, s3, s4))
        elif tag == "script_vm_func_00262a54":
            src_s = bytes(uc_inst.mem_read(r1, r2)).split(b"\x00", 1)[0]
            uc_inst.mem_write(r0, src_s + b"\x00")
            calls.append((tag, src_s, r2))
        elif tag == "ui_func_002be77c":
            txt = bytes(uc_inst.mem_read(r2, 32)).split(b"\x00", 1)[0]
            s0 = uc_inst.reg_read(arm.UC_ARM_REG_S0)
            s1 = uc_inst.reg_read(arm.UC_ARM_REG_S1)
            s2 = uc_inst.reg_read(arm.UC_ARM_REG_S2)
            s3 = uc_inst.reg_read(arm.UC_ARM_REG_S3)
            s4 = uc_inst.reg_read(arm.UC_ARM_REG_S4)
            calls.append((tag, r0, r1, txt, s0, s1, s2, s3, s4))

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    ret = uc.reg_read(arm.UC_ARM_REG_R0)
    out_stack = bytes(uc.mem_read(G_OBJ_ADDR + 0x124C, 0x20))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "d8": uc.reg_read(arm.UC_ARM_REG_D8),
        "d9": uc.reg_read(arm.UC_ARM_REG_D9),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return ret, out_stack, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs, cand_rodata = compile_candidate()

    cases = [
        ("mode0_alpha0", 0, 0, 0, 0.0, 0, 0x11111111),
        ("mode0_alpha_nz_blend_diff", 0, 0, 0, 0.5, 0, 0x22222222),
        ("mode0_alpha_nz_dirty_stack", 0, 0, 0, 0.75, 1, 0x11111111),
        ("mode1_total0", 1, 0, 0, 0.0, 0, 0),
        ("mode1_total3_sel1", 1, 3, 1, 0.0, 0, 0),
        ("mode1_total15_sel12_scroll", 1, 15, 12, 0.0, 0, 0),
    ]

    for name, *args in cases:
        o_ret, o_st, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, b"", *args)
        c_ret, c_st, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_relocs, cand_rodata, *args)
        if o_ret != c_ret or o_st != c_st:
            print(f"FAIL {name}: ret/stack mismatch")
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
        (mut_nop_reloc(1), cases[1][1:]),
        (mut_nop_reloc(2), cases[1][1:]),
        (mut_nop_reloc(3), cases[1][1:]),
        (mut_nop_reloc(len(cand_relocs) - 1), cases[4][1:]),
        (mut_nop_reloc(len(cand_relocs) - 2), cases[4][1:]),
    ]
    mutants_ok = sum(1 for fn, cargs in mut_specs if check_mutant(fn, cargs))
    if mutants_ok != 5:
        print(f"FAIL: detected only {mutants_ok}/5 mutants")
        return 1

    print(
        f"PASS: ui_func_002016cc (0x{FUNC_ADDR:08x}) matched original across "
        f"{len(cases)} cases and detected {mutants_ok}/5 mutants "
        f"(candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
