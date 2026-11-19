#!/usr/bin/env python3
"""Differential test for engine_func_003b97c4 (0x003b97c4) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_003b97c4"

FUNC_ADDR = 0x003B97C4
FUNC_SIZE = 616

SELF_ADDR = 0x20000000
INFO_ADDR = 0x20002000
E5C_ADDR = 0x20003000
SB_ADDR = 0x20004000
ANIM_LIST_ADDR = 0x20005000
RODATA_ADDR = 0x20008000

STUBS = {
    0x002A63F8: "ui_func_002a63f8",
    0x003BA974: "script_vm_func_003ba974",
    0x002BE7FC: "ui_func_002be7fc",
    0x002C0BA8: "script_vm_func_002c0ba8",
    0x002350F4: "engine_func_002350f4",
    0x0022BA54: "engine_func_0022ba54",
    0x0022B158: "engine_func_0022b158",
    0x00234E70: "engine_func_00234e70",
    0x003BBD00: "engine_func_003bbd00",
    0x0022B144: "engine_func_0022b144",
    0x002C32F0: "engine_func_002c32f0",
    0x002A06A0: "engine_func_002a06a0",
    0x0022B3D8: "engine_func_0022b3d8",
    0x0023509C: "engine_func_0023509c",
    0x00263978: "PlaceWin_ShowMessage",
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
            if name == "engine_func_003b97c4":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("engine_func_003b97c4 not found in object")

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
    gate0: int,
    d6c: int,
    d70: int,
    info_b40: int,
    h64: int,
    h66: int,
    flag_h64_ret: int,
    flag_h66_ret: int,
    anim_idx: int,
    anim_list_ok: bool,
    anim_count: int,
    s3c: int,
    sb28: int,
    db0: int,
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
        if relocs is None and addr == 0x002BE7FC:
            uc.mem_write(addr, struct.pack("<H", 0x4770))
        else:
            uc.mem_write(addr, make_stub_bx_lr())

    self_buf = bytearray(0xF00)
    struct.pack_into("<h", self_buf, 0x3C, s3c)
    struct.pack_into("<I", self_buf, 0x90, 0x55)
    struct.pack_into("<I", self_buf, 0xD5C, INFO_ADDR)
    struct.pack_into("<I", self_buf, 0xD6C, d6c)
    struct.pack_into("<I", self_buf, 0xD70, d70)
    struct.pack_into("<I", self_buf, 0xDB0, db0)
    struct.pack_into("<I", self_buf, 0xE5C, E5C_ADDR)
    uc.mem_write(SELF_ADDR, bytes(self_buf))

    info_buf = bytearray(0x100)
    info_buf[0x40 : 0x45] = bytes([info_b40, ord("a"), ord("b"), ord("c"), 0])
    struct.pack_into("<i", info_buf, 0x60, anim_idx)
    struct.pack_into("<HH", info_buf, 0x64, h64, h66)
    info_buf[0x68 : 0x6C] = b"alt\x00"
    uc.mem_write(INFO_ADDR, bytes(info_buf))

    sb_buf = bytearray(0x40)
    struct.pack_into("<h", sb_buf, 0x28, sb28)
    sb_buf[0x2B] = 1  # s8 index
    uc.mem_write(SB_ADDR, bytes(sb_buf))

    anim_buf = bytearray(0x100)
    for i in range(4):
        s = f"anim{i}".encode("ascii") + b"\x00"
        anim_buf[i * 0x20 : i * 0x20 + len(s)] = s
    uc.mem_write(ANIM_LIST_ADDR, bytes(anim_buf))

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
        if tag == "ui_func_002a63f8":
            calls.append((tag, r0, r1))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, gate0)
        elif tag == "script_vm_func_003ba974":
            calls.append((tag, r0))
        elif tag == "ui_func_002be7fc":
            fmt = bytes(uc_inst.mem_read(r1, 16)).split(b"\x00", 1)[0]
            arg = bytes(uc_inst.mem_read(r2, 16)).split(b"\x00", 1)[0]
            out = (fmt.replace(b"%s", arg) + b"\x00")
            uc_inst.mem_write(r0, out)
            calls.append((tag, fmt, arg))
        elif tag == "script_vm_func_002c0ba8":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, flag_h64_ret if r0 == h64 else flag_h66_ret)
        elif tag == "engine_func_002350f4":
            s1 = bytes(uc_inst.mem_read(r1, 32)).split(b"\x00", 1)[0]
            s2 = bytes(uc_inst.mem_read(r2, 32)).split(b"\x00", 1)[0] if r2 != 0 else None
            calls.append((tag, r0, s1, s2))
        elif tag == "engine_func_0022ba54":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, SB_ADDR)
        elif tag == "engine_func_0022b158":
            calls.append((tag, r0, r1, r2))
        elif tag == "engine_func_00234e70":
            calls.append((tag, r0, r1, r2))
        elif tag == "engine_func_003bbd00":
            calls.append((tag,))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ANIM_LIST_ADDR if anim_list_ok else 0)
        elif tag == "engine_func_0022b144":
            calls.append((tag, r1))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, anim_count)
        elif tag == "engine_func_002c32f0":
            s0 = bytes(uc_inst.mem_read(r0, 32)).split(b"\x00", 1)[0]
            calls.append((tag, s0, r1, r2))
            uc_inst.mem_write(r1, struct.pack("<I", 0x9900 + r1))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, 0x8800 + (r1 & 0xFF))
        elif tag == "engine_func_002a06a0":
            calls.append((tag, r0, r1, r2))
        elif tag in ("engine_func_0022b3d8", "engine_func_0023509c"):
            calls.append((tag, r0, r1))
        elif tag == "PlaceWin_ShowMessage":
            calls.append((tag, r0))

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    out_self = bytes(uc.mem_read(SELF_ADDR, 0xF00))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return out_self, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs, cand_rodata = compile_candidate()

    cases = [
        ("gate0_fail", 0, 1, 1, ord("x"), 0, 0, 0, 0, 0, True, 2, 0, 0, 0),
        ("d6c_null", 1, 0, 1, ord("x"), 0, 0, 0, 0, 0, True, 2, 0, 0, 0),
        ("d70_null", 1, 1, 0, ord("x"), 0, 0, 0, 0, 0, True, 2, 0, 0, 0),
        ("b40_0x30_show_msg", 1, 1, 1, 0x30, 0, 0, 0, 0, 0, True, 2, 0, 0, 0),
        ("b40_0x30_skip_msg", 1, 1, 1, 0x30, 0, 0, 0, 0, 0, True, 2, 0, 0, 1),
        ("full_h64_anim2_s3c4_sb0", 1, 1, 1, ord("m"), 10, 20, 1, 0, 1, True, 2, 4, 0, 0),
        ("full_h66_anim0_s3c3_sb6", 1, 1, 1, ord("m"), 10, 20, 0, 1, 2, True, 0, 3, 6, 1),
        ("full_no_alt_neg_anim_s3c4_sb1", 1, 1, 1, ord("m"), 0, 0, 0, 0, -1, True, 2, 4, 1, 0),
        ("full_anim_null_s3c1_sb0", 1, 1, 1, ord("m"), 10, 0, 0, 0, 1, False, 2, 1, 0, 0),
    ]

    for name, *args in cases:
        o_self, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, b"", *args)
        c_self, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_relocs, cand_rodata, *args)
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
        o_s, o_c, _ = run_one(orig_code, FUNC_ADDR, None, b"", *case_args)
        m_s, m_c, _ = run_one(bytes(mc), 0x00180000, None, cand_rodata, *case_args)
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
        (mut_nop_reloc(0), cases[5][1:]),
        (mut_nop_reloc(1), cases[5][1:]),
        (mut_nop_reloc(2), cases[5][1:]),
        (mut_nop_reloc(4), cases[5][1:]),
        (mut_nop_reloc(len(cand_relocs) - 1), cases[5][1:]),
    ]
    mutants_ok = sum(1 for fn, cargs in mut_specs if check_mutant(fn, cargs))
    if mutants_ok != 5:
        print(f"FAIL: detected only {mutants_ok}/5 mutants")
        return 1

    print(
        f"PASS: engine_func_003b97c4 (0x{FUNC_ADDR:08x}) matched original across "
        f"{len(cases)} cases and detected {mutants_ok}/5 mutants "
        f"(candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
