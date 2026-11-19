#!/usr/bin/env python3
"""Differential test for engine_func_0015b5b8 (0x0015b5b8) with Unicorn ARM."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_0015b5b8"

FUNC_ADDR = 0x0015B5B8
FUNC_SIZE = 484

STUB_ASDGPU_ADDR = 0x002BC300

DST_ADDR = 0x20000000
SRC_ADDR = 0x20001000
META_ADDR = 0x20002000
SUB_BASE = 0x20003000
DATA_BASE = 0x20004000
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


def compile_candidate() -> tuple[bytes, dict[str, int]]:
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
            if name == "engine_func_0015b5b8":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol engine_func_0015b5b8 not found")

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
    insn = 0xEB000000 | (delta & 0x00FFFFFF)
    struct.pack_into("<I", code, at_off, insn)


def run_one(
    code_bytes: bytes,
    base_addr: int,
    relocs: dict[str, int] | None,
    dst_init: bytearray,
    src_init: bytearray,
    meta_byte: int,
    sub_specs: list[tuple[int, int]],
    mutate_fn=None,
) -> tuple[bytes, list[int], dict[str, int]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_map(0x20000000, 0x00010000)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    buf = bytearray(code_bytes)
    if relocs is not None:
        for sym_name, off in relocs:
            if "AsdGpu_Address" in sym_name:
                patch_bl(buf, off, base_addr + off, STUB_ASDGPU_ADDR)
            else:
                raise RuntimeError(f"unexpected relocation: {sym_name}")

    uc.mem_write(base_addr, bytes(buf))
    uc.mem_write(STUB_ASDGPU_ADDR, make_stub_bx_lr())

    dst = bytearray(dst_init)
    src = bytearray(src_init)
    struct.pack_into("<i", dst, 0x0C, META_ADDR - (DST_ADDR + 0x0C))
    meta = bytearray(0x20)
    struct.pack_into("<I", meta, 0x08, meta_byte)
    uc.mem_write(META_ADDR, bytes(meta))

    for i, (direct_ptr, rel_off) in enumerate(sub_specs):
        sub_addr = SUB_BASE + i * 0x40
        struct.pack_into("<i", src, 0x38 + i * 4, sub_addr - (SRC_ADDR + 0x38 + i * 4))
        sub = bytearray(0x40)
        struct.pack_into("<I", sub, 0x18, direct_ptr)
        struct.pack_into("<i", sub, 0x0C, rel_off)
        uc.mem_write(sub_addr, bytes(sub))

    uc.mem_write(DST_ADDR, bytes(dst))
    uc.mem_write(SRC_ADDR, bytes(src))

    if mutate_fn is not None:
        mutate_fn(uc)

    uc.reg_write(arm.UC_ARM_REG_R0, DST_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, SRC_ADDR)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)

    calls: list[int] = []

    def hook_code(uc_inst, address, size, user_data):
        if address == STUB_ASDGPU_ADDR:
            arg0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            calls.append(arg0)
            # Deterministic non-trivial 32-bit physical address transform
            ret = ((arg0 * 0x45D9F3B) ^ 0xA5A55A5A) & 0xFFFFFFFF
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ret)

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=STUB_ASDGPU_ADDR, end=STUB_ASDGPU_ADDR)
    uc.emu_start(base_addr, LR_SENTINEL, count=20000)

    out_dst = bytes(uc.mem_read(DST_ADDR, 0x60))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return out_dst, calls, regs


def build_case(seed: int, fmt_val: int, w: int, h: int, mips: int, meta_byte: int, use_rel: bool):
    dst = bytearray(0x60)
    for off in range(0, 0x60, 4):
        struct.pack_into("<I", dst, off, (0xF1E2D3C4 ^ (seed * 0x01010101 + off * 0x111111)) & 0xFFFFFFFF)

    src = bytearray(0x60)
    struct.pack_into("<I", src, 0x18, w)
    struct.pack_into("<I", src, 0x1C, h)
    struct.pack_into("<I", src, 0x28, mips)
    struct.pack_into("<I", src, 0x34, fmt_val)

    subs: list[tuple[int, int]] = []
    for i in range(6):
        if use_rel and (i % 2 == 1):
            subs.append((0, 0x100 + i * 0x20))
        else:
            subs.append((DATA_BASE + i * 0x80 + (seed & 0xF), 0))
    return dst, src, meta_byte, subs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs = compile_candidate()

    cases = [
        ("fmt_c_meta0_direct", *build_case(1, 0x0C, 0x123, 0x456, 5, 0x00, False)),
        ("fmt_c_meta1_rel", *build_case(2, 0x0C, 0x7FF, 0x7FF, 8, 0x01, True)),
        ("fmt_5_meta2_direct", *build_case(3, 0x05, 0x001, 0x002, 4, 0x02, False)),
        ("fmt_1c_meta255_rel", *build_case(4, 0x1C, 0xFFF, 0xF800 | 0x321, 1, 0xFF, True)),
        ("fmt_0_meta0x100_rel", *build_case(5, 0x00, 0x800, 0x800, 16, 0x100, True)),
        ("fmt_c_mips0_direct", *build_case(6, 0x0C, 0x040, 0x080, 0, 0x03, False)),
    ]

    for name, dst, src, meta_byte, subs in cases:
        o_dst, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, dst, src, meta_byte, subs)
        c_dst, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_relocs, dst, src, meta_byte, subs)
        if o_dst != c_dst:
            for off in range(0, 0x60, 4):
                ow = struct.unpack_from("<I", o_dst, off)[0]
                cw = struct.unpack_from("<I", c_dst, off)[0]
                if ow != cw:
                    print(f"FAIL {name}: dst+0x{off:02x} orig=0x{ow:08x} cand=0x{cw:08x}")
            return 1
        if o_calls != c_calls:
            print(f"FAIL {name}: calls orig={o_calls} cand={c_calls}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch orig={o_regs} cand={c_regs}")
            return 1

    # 5 negative / mutation controls
    mutants = [
        ("mut_wrong_preserved_hi", lambda uc: uc.mem_write(DST_ADDR + 0x10, struct.pack("<I", 0xDEADBEEF))),
        ("mut_wrong_fmt_0x0c_bit", lambda uc: uc.mem_write(SRC_ADDR + 0x34, struct.pack("<I", 0x0B))),
        ("mut_wrong_meta_byte", lambda uc: uc.mem_write(META_ADDR + 0x08, struct.pack("<I", 0x02))),
        ("mut_wrong_sub_ptr", lambda uc: uc.mem_write(SUB_BASE + 0x18, struct.pack("<I", DATA_BASE + 0x1234))),
        ("mut_wrong_width", lambda uc: uc.mem_write(SRC_ADDR + 0x18, struct.pack("<I", 0x124))),
    ]
    base_name, dst0, src0, meta0, subs0 = cases[0]
    ref_dst, ref_calls, _ = run_one(orig_code, FUNC_ADDR, None, dst0, src0, meta0, subs0)
    detected = 0
    for mname, mfn in mutants:
        m_dst, m_calls, _ = run_one(cand_code, 0x00180000, cand_relocs, dst0, src0, meta0, subs0, mutate_fn=mfn)
        if m_dst != ref_dst or m_calls != ref_calls:
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: engine_func_0015b5b8 (0x0015b5b8) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
