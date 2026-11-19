#!/usr/bin/env python3
"""Differential test for func_0015eb60 (0x0015eb60) with Unicorn ARM."""

from __future__ import annotations

import math
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
OUT_DIR = ROOT / "build" / "test_leaf_0015eb60"

FUNC_ADDR = 0x0015EB60
FUNC_SIZE = 500

STUB_POWF = 0x002B9CF8
STUB_FLUSH = 0x002C3B48

OBJ_ADDR = 0x20000000
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
            if name == "func_0015eb60":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol func_0015eb60 not found")

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


def u32_to_f32(u: int) -> float:
    return struct.unpack("<f", struct.pack("<I", u))[0]


def f32_to_u32(f: float) -> int:
    return struct.unpack("<I", struct.pack("<f", f))[0]


def run_one(
    code_bytes: bytes,
    base_addr: int,
    relocs: list[tuple[str, int]] | None,
    u4: int,
    u8: int,
    u0c: int,
    f14: float,
    flag24: int,
    s30: int,
    s34: int,
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
            if "camp_func_002b9cf8" in sym_name:
                patch_bl(buf, off, base_addr + off, STUB_POWF)
            elif "engine_func_002c3b48" in sym_name:
                patch_bl(buf, off, base_addr + off, STUB_FLUSH)
            else:
                raise RuntimeError(f"unexpected relocation: {sym_name}")

    uc.mem_write(base_addr, bytes(buf))
    uc.mem_write(STUB_POWF, make_stub_bx_lr())
    uc.mem_write(STUB_FLUSH, make_stub_bx_lr())

    obj = bytearray(0x100)
    for off in range(0, 0x100, 4):
        struct.pack_into("<I", obj, off, 0x5A5A5A5A)
    struct.pack_into("<I", obj, 0x04, u4)
    struct.pack_into("<I", obj, 0x08, u8)
    struct.pack_into("<I", obj, 0x0C, u0c)
    struct.pack_into("<f", obj, 0x10, 1.5)
    struct.pack_into("<f", obj, 0x14, f14)
    struct.pack_into("<f", obj, 0x1C, 2.25)
    struct.pack_into("<f", obj, 0x20, -0.75)
    obj[0x24] = flag24
    struct.pack_into("<I", obj, 0x28, 0x20004000)
    struct.pack_into("<I", obj, 0x2C, 0x200)
    struct.pack_into("<i", obj, 0x30, s30)
    struct.pack_into("<i", obj, 0x34, s34)
    struct.pack_into("<I", obj, 0x38, 0xCAFEBABE)
    uc.mem_write(OBJ_ADDR, bytes(obj))

    uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)
    uc.reg_write(arm.UC_ARM_REG_D8, 0x1122334455667788)
    uc.reg_write(arm.UC_ARM_REG_D9, 0x99AABBCCDDEEFF00)

    calls: list[tuple] = []

    def hook_code(uc_inst, address, size, user_data):
        if address == STUB_POWF:
            b = u32_to_f32(uc_inst.reg_read(arm.UC_ARM_REG_S0))
            e = u32_to_f32(uc_inst.reg_read(arm.UC_ARM_REG_S1))
            calls.append(("powf", round(b, 4), round(e, 4)))
            res = math.pow(b, e) if b > 0 else 0.0
            uc_inst.reg_write(arm.UC_ARM_REG_S0, f32_to_u32(res))
        elif address == STUB_FLUSH:
            calls.append(("flush", uc_inst.reg_read(arm.UC_ARM_REG_R0), uc_inst.reg_read(arm.UC_ARM_REG_R1)))

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=STUB_POWF, end=STUB_POWF)
    uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=STUB_FLUSH, end=STUB_FLUSH)
    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    out_obj = bytes(uc.mem_read(OBJ_ADDR, 0x100))
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

    cases = [
        ("small_u4_flag0_p05", 2, 100, 3, 0.5, 0, 10, 20),
        ("large_u4_flag1_p12", 20, 200, 30, 1.2, 1, -5, 15),
        ("boundary_5_flag1_p095", 5, 50, 5, 0.95, 1, 0, 100),
        ("boundary_4_flag0_p096", 4, 1000, 4, 0.96, 0, 30, -30),
    ]

    for name, u4, u8, u0c, f14, flg, s30, s34 in cases:
        o_obj, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, u4, u8, u0c, f14, flg, s30, s34)
        c_obj, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_relocs, u4, u8, u0c, f14, flg, s30, s34)
        if o_obj != c_obj:
            for off in range(0, 0x100, 4):
                ow = struct.unpack_from("<I", o_obj, off)[0]
                cw = struct.unpack_from("<I", c_obj, off)[0]
                if ow != cw:
                    print(f"FAIL {name}: obj+0x{off:02x} orig=0x{ow:08x} cand=0x{cw:08x}")
            return 1
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch orig={o_calls} cand={c_calls}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch")
            return 1

    # 5 negative / mutation controls
    ref_obj, ref_calls, _ = run_one(orig_code, FUNC_ADDR, None, 20, 200, 30, 1.2, 1, -5, 15)
    mutants = [
        ("mut_u4", 10, 200, 30, 1.2, 1, -5, 15),
        ("mut_u8", 20, 100, 30, 1.2, 1, -5, 15),
        ("mut_u0c", 20, 200, 10, 1.2, 1, -5, 15),
        ("mut_f14", 20, 200, 30, 0.4, 1, -5, 15),
        ("mut_flag24", 20, 200, 30, 1.2, 0, -5, 15),
    ]
    detected = 0
    for mname, u4, u8, u0c, f14, flg, s30, s34 in mutants:
        m_obj, m_calls, _ = run_one(cand_code, 0x00180000, cand_relocs, u4, u8, u0c, f14, flg, s30, s34)
        if (m_obj, m_calls) != (ref_obj, ref_calls):
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: func_0015eb60 (0x0015eb60) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
