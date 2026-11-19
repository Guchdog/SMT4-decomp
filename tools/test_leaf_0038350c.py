#!/usr/bin/env python3
"""Differential test for script_vm_func_0038350c (0x0038350c) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_0038350c"

FUNC_ADDR = 0x0038350C
FUNC_SIZE = 628

SELF_ADDR = 0x20000000
ENTRIES_ADDR = 0x20002000
SLOT_PTR_BASE = 0x20004000
RODATA_ADDR = 0x20008000

STUBS = {
    0x0023EBC0: "func_0023ebc0",
    0x00385D0C: "func_00385d0c",
    0x00385D2C: "func_00385d2c",
    0x00235510: "script_vm_func_00235510",
    0x00385D14: "camp_func_00385d14",
    0x002C0BA8: "script_vm_func_002c0ba8",
    0x002B7F0A: "camp_func_002b7f08",
    0x002B7F08: "camp_func_002b7f08",
    0x00297004: "ui_func_00297004",
    0x002BE7FC: "ui_func_002be7fc",
    0x0031E438: "engine_func_0031e438",
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
            if name == "script_vm_func_0038350c":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("script_vm_func_0038350c not found in object")

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
    g0: int,
    g1: int,
    g2: int,
    b10: int,
    b18: int,
    entries: list[tuple[int, int, int, int, int]],
    flag_set: set[int],
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
    if rodata:
        uc.mem_write(RODATA_ADDR, rodata)
    for addr in STUBS:
        if base_addr == FUNC_ADDR:
            if addr in (0x002B7F0A, 0x002BE7FC):
                uc.mem_write(addr, struct.pack("<H", 0x4770))
            elif addr != 0x002B7F08:
                uc.mem_write(addr, make_stub_bx_lr())
        elif addr != 0x002B7F0A:
            uc.mem_write(addr, make_stub_bx_lr())

    self_buf = bytearray(0xE00)
    self_buf[0x10] = b10 & 0xFF
    self_buf[0x18] = b18 & 0xFF
    for i in range(6):
        p0 = SLOT_PTR_BASE + i * 0x20
        p1 = SLOT_PTR_BASE + (i + 6) * 0x20
        struct.pack_into("<I", self_buf, 0xD10 + i * 4, p0)
        struct.pack_into("<I", self_buf, 0xD28 + i * 4, p1)
        uc.mem_write(p0 + 8, struct.pack("<I", 0xA000 + i))
        uc.mem_write(p1 + 8, struct.pack("<I", 0xB000 + i))
    uc.mem_write(SELF_ADDR, bytes(self_buf))

    ebuf = bytearray(len(entries) * 0x88)
    for i, (h60, h62, h64, h66, h68) in enumerate(entries):
        struct.pack_into("<HHHHH", ebuf, i * 0x88 + 0x60, h60, h62, h64, h66, h68)
    uc.mem_write(ENTRIES_ADDR, bytes(ebuf))

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
        if tag == "func_0023ebc0":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, g0)
        elif tag == "func_00385d0c":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, g1)
        elif tag == "func_00385d2c":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, g2)
        elif tag == "script_vm_func_00235510":
            calls.append((tag, r0, r1))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ENTRIES_ADDR + r1 * 0x88)
        elif tag == "camp_func_00385d14":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, len(entries))
        elif tag == "script_vm_func_002c0ba8":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, 1 if r0 in flag_set else 0)
        elif tag == "camp_func_002b7f08":
            calls.append((tag, r0, r1, r2, r3))
        elif tag == "ui_func_00297004":
            calls.append((tag, r0, r1))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, 2)
        elif tag == "ui_func_002be7fc":
            fmt = bytes(uc_inst.mem_read(r1, 32)).split(b"\x00", 1)[0]
            out = fmt.decode("ascii") % (r2, r3)
            uc_inst.mem_write(r0, out.encode("ascii") + b"\x00")
            calls.append((tag, out))
        elif tag == "engine_func_0031e438":
            s = bytes(uc_inst.mem_read(r1, 32)).split(b"\x00", 1)[0]
            calls.append((tag, r0, s, r2))

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    out_self = bytes(uc.mem_read(SELF_ADDR, 0xE00))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return out_self, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs, cand_rodata = compile_candidate()

    sample_entries = [
        (3, 1, 2, 0, 0),    # match slot 1, h64=2 -> val 1
        (3, 2, 1, 10, 0),   # match slot 2, h66=10(set), h64=1 -> val 2
        (3, 2, 3, 0, 0),    # dup slot 2 -> skipped
        (3, 3, 0, 11, 0),   # h66=11(unset) -> skipped
        (3, 4, 0, 0, 10),   # h68=10(set) -> skipped
        (9, 5, 0, 0, 0),    # wrong b10 -> skipped
        (3, 6, 2, 0, 0),    # match slot 6
    ]

    cases = [
        ("g0_fail", 0, 1, 1, 3, 1, sample_entries, {10}),
        ("g1_fail", 1, 0, 1, 3, 1, sample_entries, {10}),
        ("g2_fail", 1, 1, 0, 3, 1, sample_entries, {10}),
        ("b18_0_no_spawn", 1, 1, 1, 3, 0, sample_entries, {10}),
        ("b18_1_full", 1, 1, 1, 3, 1, sample_entries, {10}),
        ("cap_at_6", 1, 1, 1, 3, 1, [(3, i + 1, 2, 0, 0) for i in range(8)], set()),
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
        (mut_nop_reloc(0), cases[4][1:]),
        (mut_nop_reloc(1), cases[4][1:]),
        (mut_nop_reloc(2), cases[4][1:]),
        (mut_nop_reloc(8), cases[4][1:]),
        (mut_nop_reloc(11), cases[4][1:]),
    ]
    mutants_ok = sum(1 for fn, cargs in mut_specs if check_mutant(fn, cargs))
    if mutants_ok != 5:
        print(f"FAIL: detected only {mutants_ok}/5 mutants")
        return 1

    print(
        f"PASS: script_vm_func_0038350c (0x{FUNC_ADDR:08x}) matched original across "
        f"{len(cases)} cases and detected {mutants_ok}/5 mutants "
        f"(candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
