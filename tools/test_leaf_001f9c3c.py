#!/usr/bin/env python3
"""Differential test for func_001f9c3c (0x001f9c3c) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_001f9c3c"

FUNC_ADDR = 0x001F9C3C
FUNC_SIZE = 644

G_PTR_ADDR = 0x00447600
G2_ADDR = 0x0049F91C
OBJ_ADDR = 0x20000000

STUBS = {
    0x0020D788: "func_0020d788",
    0x002AA418: "func_002aa418",
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
            if name == "func_001f9c3c":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("func_001f9c3c not found in object")

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
    obj_null: bool,
    obj_state: int,
    g2_b20: int,
    entries: list[tuple[int, float, int, int, int]],
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
    for addr in STUBS:
        uc.mem_write(addr, make_stub_bx_lr())

    uc.mem_write(G_PTR_ADDR, struct.pack("<I", 0 if obj_null else OBJ_ADDR))
    g2 = bytearray(0x30)
    g2[0x20] = g2_b20
    uc.mem_write(G2_ADDR, bytes(g2))

    obj = bytearray(0x34 + 32 * 0x180)
    struct.pack_into("<I", obj, 4, obj_state)
    for idx, (b7e, f80, timer, val148, flags_mask) in enumerate(entries):
        off = 0x34 + idx * 0x180
        obj[off + 0x00] = 1
        obj[off + 0x7E] = b7e
        struct.pack_into("<f", obj, off + 0x80, f80)
        obj[off + 0x13E] = 1 if (flags_mask & 1) else 0
        struct.pack_into("<i", obj, off + 0x140, timer)
        obj[off + 0x144] = 1 if (flags_mask & 2) else 0
        struct.pack_into("<i", obj, off + 0x148, val148)
        obj[off + 0x17C] = 1 if (flags_mask & 4) else 0
    uc.mem_write(OBJ_ADDR, bytes(obj))

    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)
    uc.reg_write(arm.UC_ARM_REG_D8, 0x1122334455667788)
    uc.reg_write(arm.UC_ARM_REG_D9, 0x99AABBCCDDEEFF00)

    calls: list[tuple] = []

    def hook_code(uc_inst, address, size, user_data):
        tag = STUBS.get(address)
        if tag == "func_0020d788":
            calls.append((tag,))
        elif tag == "func_002aa418":
            r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc_inst.reg_read(arm.UC_ARM_REG_R3)
            s = [uc_inst.reg_read(getattr(arm, f"UC_ARM_REG_S{k}")) for k in range(9)]
            calls.append((tag, r0, r1, r2, r3, *s))

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=100000)

    out_obj = bytes(uc.mem_read(OBJ_ADDR, 0x34 + 32 * 0x180))
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
    cand_code, cand_relocs = compile_candidate()

    sample_entries = [
        (0, 45.0, 5, 0x43000000, 7),
        (0, 120.0, 15, 0x44000000, 7),
        (0, -45.0, 25, 0x44800000, 7),
        (0, -120.0, 35, 0x45000000, 7),
        (1, 0.0, 0, 0, 7),
        (0, 0.0, 0, 0, 3),
    ]

    cases = [
        ("obj_null", True, 8, 0, sample_entries),
        ("state_not_8", False, 7, 0, sample_entries),
        ("g2_b20_nz", False, 8, 1, sample_entries),
        ("active_all_quadrants", False, 8, 0, sample_entries),
    ]

    for name, *args in cases:
        o_o, o_c, o_r = run_one(orig_code, FUNC_ADDR, None, *args)
        c_o, c_c, c_r = run_one(cand_code, 0x00180000, cand_relocs, *args)
        if o_o != c_o:
            print(f"FAIL {name}: obj mismatch")
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
        o_o, o_c, _ = run_one(orig_code, FUNC_ADDR, None, *case_args)
        m_o, m_c, _ = run_one(bytes(mc), 0x00180000, None, *case_args)
        return (m_o, m_c) != (o_o, o_c)

    def mut_nop_reloc(reloc_idx: int):
        def _fn(mc: bytearray) -> bool:
            if reloc_idx >= len(cand_relocs):
                return False
            off = cand_relocs[reloc_idx][1]
            struct.pack_into("<I", mc, off, 0xE1A00000)
            return True
        return _fn

    def mut_const(old_val: int, new_val: int):
        def _fn(mc: bytearray) -> bool:
            for i in range(0, len(mc), 4):
                if struct.unpack_from("<I", mc, i)[0] == old_val:
                    struct.pack_into("<I", mc, i, new_val)
                    return True
            return False
        return _fn

    mut_specs = [
        (mut_nop_reloc(0), cases[3][1:]),
        (mut_nop_reloc(1), cases[3][1:]),
        (mut_nop_reloc(2), cases[3][1:]),
        (mut_const(0xEF6C3EFF, 0xEF6C3E00), cases[3][1:]),
        (mut_const(0x2DB5FFFF, 0x2DB5FF00), cases[3][1:]),
    ]
    mutants_ok = sum(1 for fn, cargs in mut_specs if check_mutant(fn, cargs))
    if mutants_ok != 5:
        print(f"FAIL: detected only {mutants_ok}/5 mutants")
        return 1

    print(
        f"PASS: func_001f9c3c (0x{FUNC_ADDR:08x}) matched original across "
        f"{len(cases)} cases and detected {mutants_ok}/5 mutants "
        f"(candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
