#!/usr/bin/env python3
"""Differential test for ui_func_002fca68 (0x002fca68) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_002fca68"

FUNC_ADDR = 0x002FCA68
FUNC_SIZE = 620

G_ADDR = 0x00446FE8
P0_ADDR = 0x20000000
P1_ADDR = 0x20000100
OUT_ADDR = 0x20000200
PLANES1_ADDR = 0x20001000
PLANES2_ADDR = 0x20002000

STUBS = {
    0x0024BD60: "func_0024bd60",
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
            if name == "ui_func_002fca68":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("ui_func_002fca68 not found in object")

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


def f32(v: float) -> int:
    return struct.unpack("<I", struct.pack("<f", v))[0]


def run_one(
    code_bytes: bytes,
    base_addr: int,
    relocs: list[tuple[str, int]] | None,
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    planes1: list[tuple[int, int, int, int, float, float, float, float]],
    planes2: list[tuple[int, int, int, int, float, float, float, float]],
    dist_ret: float,
) -> tuple[int, tuple[float, float, float], list[tuple], dict[str, int]]:
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

    g = bytearray(0x30)
    struct.pack_into("<i", g, 0x0C, len(planes1))
    struct.pack_into("<i", g, 0x10, len(planes2))
    struct.pack_into("<I", g, 0x20, PLANES1_ADDR)
    struct.pack_into("<I", g, 0x24, PLANES2_ADDR)
    uc.mem_write(G_ADDR, bytes(g))

    def pack_planes(plist):
        out = bytearray(len(plist) * 0xA8)
        for i, (w0, b8, s4, s5, nx, ny, nz, d) in enumerate(plist):
            off = i * 0xA8
            struct.pack_into("<I", out, off + 0x00, w0)
            struct.pack_into("<bb", out, off + 0x04, s4, s5)
            out[off + 0x08] = b8
            struct.pack_into("<4f", out, off + 0x0C, nx, ny, nz, d)
        return bytes(out)

    uc.mem_write(PLANES1_ADDR, pack_planes(planes1))
    uc.mem_write(PLANES2_ADDR, pack_planes(planes2))
    uc.mem_write(P0_ADDR, struct.pack("<3f", *p0))
    uc.mem_write(P1_ADDR, struct.pack("<3f", *p1))
    uc.mem_write(OUT_ADDR, b"\x00" * 12)

    uc.reg_write(arm.UC_ARM_REG_R0, P0_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, P1_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R2, OUT_ADDR)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)
    uc.reg_write(arm.UC_ARM_REG_D8, 0x1122334455667788)
    uc.reg_write(arm.UC_ARM_REG_D9, 0x99AABBCCDDEEFF00)

    calls: list[tuple] = []

    def hook_code(uc_inst, address, size, user_data):
        tag = STUBS.get(address)
        if tag == "func_0024bd60":
            r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
            s0 = uc_inst.reg_read(arm.UC_ARM_REG_S0)
            s1 = uc_inst.reg_read(arm.UC_ARM_REG_S1)
            s2 = uc_inst.reg_read(arm.UC_ARM_REG_S2)
            s3 = uc_inst.reg_read(arm.UC_ARM_REG_S3)
            calls.append((tag, r0, r1, r2, s0, s1, s2, s3))
            uc_inst.reg_write(arm.UC_ARM_REG_S0, f32(dist_ret))

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    ret = uc.reg_read(arm.UC_ARM_REG_R0)
    out_vec = struct.unpack("<3f", uc.mem_read(OUT_ADDR, 12))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "d8": uc.reg_read(arm.UC_ARM_REG_D8),
        "d9": uc.reg_read(arm.UC_ARM_REG_D9),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return ret, out_vec, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs = compile_candidate()

    p_hit_z = (1, 1, -2, 3, 0.0, 0.0, 1.0, 5.0)
    p_skip_b8 = (1, 0, -2, 3, 0.0, 0.0, 1.0, 5.0)
    p_skip_w0 = (2, 1, -2, 3, 0.0, 0.0, 1.0, 5.0)
    p_miss = (1, 1, -2, 3, 0.0, 0.0, 1.0, 100.0)

    cases = [
        ("no_planes", (0.0, 0.0, 0.0), (0.0, 0.0, 20.0), [], [], 0.5),
        ("pass1_hit_pos", (0.0, 0.0, 0.0), (0.0, 0.0, 20.0), [p_skip_b8, p_hit_z], [], 0.25),
        ("pass1_hit_neg_dist", (0.0, 0.0, 0.0), (0.0, 0.0, 20.0), [p_hit_z], [p_hit_z], -1.0),
        ("pass2_hit_only", (0.0, 0.0, 0.0), (0.0, 0.0, 20.0), [p_skip_w0, p_miss], [p_hit_z], 0.5),
        ("pass1_and_pass2_hit", (0.0, 0.0, 10.0), (0.0, 0.0, -10.0), [p_hit_z], [p_hit_z], 0.5),
    ]

    for name, *args in cases:
        o_ret, o_vec, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, *args)
        c_ret, c_vec, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_relocs, *args)
        if o_ret != c_ret or o_vec != c_vec:
            print(f"FAIL {name}: ret/vec mismatch orig=({o_ret},{o_vec}) cand=({c_ret},{c_vec})")
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
        o_r, o_v, o_c, _ = run_one(orig_code, FUNC_ADDR, None, *case_args)
        m_r, m_v, m_c, _ = run_one(bytes(mc), 0x00180000, None, *case_args)
        return (m_r, m_v, m_c) != (o_r, o_v, o_c)

    def mut_nop_bl(mc: bytearray) -> bool:
        off = cand_relocs[0][1]
        struct.pack_into("<I", mc, off, 0xE1A00000)
        return True

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

    def mut_const(old_val: int, new_val: int):
        def _fn(mc: bytearray) -> bool:
            for i in range(0, len(mc), 4):
                if struct.unpack_from("<I", mc, i)[0] == old_val:
                    struct.pack_into("<I", mc, i, new_val)
                    return True
            return False
        return _fn

    mut_specs = [
        (mut_nop_bl, cases[1][1:]),
        (mut_const(0x41000000, 0x41800000), cases[1][1:]),
        (mut_const(0x40A00000, 0x41200000), cases[3][1:]),
        (mut_flip_cond(4), cases[3][1:]),
        (mut_flip_cond(5), cases[1][1:]),
    ]
    mutants_ok = sum(1 for fn, cargs in mut_specs if check_mutant(fn, cargs))
    if mutants_ok != 5:
        print(f"FAIL: detected only {mutants_ok}/5 mutants")
        return 1

    print(
        f"PASS: ui_func_002fca68 (0x{FUNC_ADDR:08x}) matched original across "
        f"{len(cases)} cases and detected {mutants_ok}/5 mutants "
        f"(candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
