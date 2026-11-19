#!/usr/bin/env python3
"""Differential test for func_0028640c (0x0028640c) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_0028640c"

FUNC_ADDR = 0x0028640C
FUNC_SIZE = 504

STUB_EULER = 0x002B22FC
STUB_MUL = 0x002B71F8

MAT_ADDR = 0x20000000
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
        raise RuntimeError(f"compile failed:\n{res.stderr}\n{res.stdout}")

    data = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    secs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = secs[e_shstrndx][4]
    sec_names = [data[shstr_off + s[0] : data.index(b"\x00", shstr_off + s[0])].decode("ascii", errors="replace") for s in secs]
    tidx = sec_names.index(".text")
    text_data = data[secs[tidx][4] : secs[tidx][4] + secs[tidx][5]]

    symtab = next(s for s in secs if s[1] == 2)
    strtab_off = secs[symtab[6]][4]
    fn_off = fn_size = None
    for idx in range(symtab[5] // 16):
        st_name, st_value, st_size, _st_info, _st_other, st_shndx = struct.unpack_from("<IIIbbH", data, symtab[4] + idx * 16)
        if st_shndx == tidx:
            name = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
            if name == "func_0028640c":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol func_0028640c not found")

    relocs: list[tuple[str, int]] = []
    for s in secs:
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
    dx: int,
    dy: int,
    dz: int,
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
        for sym_name, off in relocs:
            if "func_002b22fc" in sym_name:
                patch_bl(buf, off, base_addr + off, STUB_EULER)
            elif "func_002b71f8" in sym_name:
                patch_bl(buf, off, base_addr + off, STUB_MUL)
            else:
                raise RuntimeError(f"unexpected relocation: {sym_name}")

    uc.mem_write(base_addr, bytes(buf))
    uc.mem_write(STUB_EULER, make_stub_bx_lr())
    uc.mem_write(STUB_MUL, make_stub_bx_lr())

    mat = bytearray(0x40)
    for i in range(16):
        struct.pack_into("<f", mat, i * 4, float(i + 1))
    uc.mem_write(MAT_ADDR, bytes(mat))

    uc.reg_write(arm.UC_ARM_REG_R0, MAT_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, dx & 0xFFFFFFFF)
    uc.reg_write(arm.UC_ARM_REG_R2, dy & 0xFFFFFFFF)
    uc.reg_write(arm.UC_ARM_REG_R3, dz & 0xFFFFFFFF)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)
    uc.reg_write(arm.UC_ARM_REG_D8, 0x1122334455667788)

    calls: list[tuple] = []

    def hook_code(uc_inst, address, size, user_data):
        if address == STUB_EULER:
            dst_ptr = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            s0 = uc_inst.reg_read(arm.UC_ARM_REG_S0)
            s1 = uc_inst.reg_read(arm.UC_ARM_REG_S1)
            s2 = uc_inst.reg_read(arm.UC_ARM_REG_S2)
            calls.append(("euler", s0, s1, s2))
            uc_inst.mem_write(dst_ptr, struct.pack("<IIII", s0, s1, s2, 0x3F800000))
        elif address == STUB_MUL:
            r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
            tmp_words = struct.unpack_from("<4I", uc_inst.mem_read(r2, 16))
            calls.append(("mul", r0, r1, tmp_words))
            uc_inst.mem_write(r0, struct.pack("<4I", *tmp_words))

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=STUB_EULER, end=STUB_EULER)
    uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=STUB_MUL, end=STUB_MUL)
    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    out_mat = bytes(uc.mem_read(MAT_ADDR, 0x40))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "d8": uc.reg_read(arm.UC_ARM_REG_D8),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return out_mat, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs = compile_candidate()

    cases = [
        ("all_zero", 0, 0, 0),
        ("simple_pos", 45, 90, 180),
        ("simple_neg", -45, -90, -180),
        ("wrap_pos_large", 360, 725, 1081),
        ("wrap_neg_large", -360, -725, -1081),
        ("partial_xz", 123, 0, -270),
    ]

    for name, dx, dy, dz in cases:
        o_mat, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, dx, dy, dz)
        c_mat, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_relocs, dx, dy, dz)
        if o_mat != c_mat or o_calls != c_calls:
            print(f"FAIL {name}: mismatch\n  orig={o_calls}\n  cand={c_calls}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch")
            return 1

    # 5 negative / mutation controls
    ref_mat, ref_calls, _ = run_one(orig_code, FUNC_ADDR, None, 45, 90, 180)
    mutants = [
        ("mut_dx", 46, 90, 180),
        ("mut_dy", 45, 91, 180),
        ("mut_dz", 45, 90, 181),
        ("mut_zero_y", 45, 0, 180),
        ("mut_neg_x", -45, 90, 180),
    ]
    detected = 0
    for mname, dx, dy, dz in mutants:
        m_mat, m_calls, _ = run_one(cand_code, 0x00180000, cand_relocs, dx, dy, dz)
        if (m_mat, m_calls) != (ref_mat, ref_calls):
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: func_0028640c (0x0028640c) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
