#!/usr/bin/env python3
"""Differential test for func_0035f1b0 (0x0035f1b0) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_0035f1b0"

FUNC_ADDR = 0x0035F1B0
FUNC_SIZE = 504

STUBS = {
    0x0035F4A0: "func_0035f4a0",
    0x0035F454: "func_0035f454",
    0x0035EDD4: "func_0035edd4",
}
STREAM_GET_SIZE = 0x003F0300
STREAM_READ = 0x003F0320

OBJ_ADDR = 0x20000000
FLAGS_ADDR = 0x20000200
STREAM_ADDR = 0x20000400
VTBL_ADDR = 0x20000500
KEYS_ADDR = 0x20000600
STR_BASE = 0x20000800
SLOTS_BUF = 0x20001000
READ_BUF = 0x20002000
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
            if name == "func_0035f1b0":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol func_0035f1b0 not found")

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
    flag_1a: int,
    bit_1b: int,
    keys: list[str | None],
    match_mask: int,
    stream_size: int,
    read_ret: int,
    payload: bytes,
) -> tuple[int, bytes, list[tuple], dict[str, int]]:
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
    for addr in [*STUBS.keys(), STREAM_GET_SIZE, STREAM_READ]:
        uc.mem_write(addr, make_stub_bx_lr())

    obj = bytearray(0x40)
    obj[0x1A] = flag_1a
    obj[0x1B] = bit_1b
    struct.pack_into("<I", obj, 0x24, READ_BUF)
    struct.pack_into("<I", obj, 0x2C, SLOTS_BUF)
    uc.mem_write(OBJ_ADDR, bytes(obj))

    uc.mem_write(FLAGS_ADDR, b"\x00" * 0x40)

    vtbl = bytearray(0x40)
    struct.pack_into("<I", vtbl, 0x24, STREAM_GET_SIZE)
    struct.pack_into("<I", vtbl, 0x2C, STREAM_READ)
    uc.mem_write(VTBL_ADDR, bytes(vtbl))
    uc.mem_write(STREAM_ADDR, struct.pack("<I", VTBL_ADDR))

    cursor = STR_BASE
    kptrs = bytearray()
    for k in keys:
        if k is None:
            kptrs.extend(struct.pack("<I", 0))
        else:
            kb = k.encode("ascii") + b"\x00"
            uc.mem_write(cursor, kb)
            kptrs.extend(struct.pack("<I", cursor))
            cursor += (len(kb) + 3) & ~3
    uc.mem_write(KEYS_ADDR, bytes(kptrs))

    uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, FLAGS_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R2, STREAM_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R3, KEYS_ADDR)
    uc.mem_write(STACK_INIT, struct.pack("<I", len(keys)))
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)

    calls: list[tuple] = []
    f454_idx = 0

    def hook_code(uc_inst, address, size, user_data):
        nonlocal f454_idx
        if address == 0x0035F4A0:
            calls.append(("f4a0", uc_inst.reg_read(arm.UC_ARM_REG_R0), uc_inst.reg_read(arm.UC_ARM_REG_R1), uc_inst.reg_read(arm.UC_ARM_REG_R2)))
        elif address == 0x0035F454:
            calls.append(("f454", uc_inst.reg_read(arm.UC_ARM_REG_R0), uc_inst.reg_read(arm.UC_ARM_REG_R1), uc_inst.reg_read(arm.UC_ARM_REG_R2)))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, (match_mask >> f454_idx) & 1)
            f454_idx += 1
        elif address == STREAM_GET_SIZE:
            calls.append(("get_size", uc_inst.reg_read(arm.UC_ARM_REG_R0)))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, stream_size)
        elif address == STREAM_READ:
            dst = uc_inst.reg_read(arm.UC_ARM_REG_R1)
            sz = uc_inst.reg_read(arm.UC_ARM_REG_R2)
            calls.append(("read", uc_inst.reg_read(arm.UC_ARM_REG_R0), dst, sz))
            uc_inst.mem_write(dst, payload)
            uc_inst.reg_write(arm.UC_ARM_REG_R0, read_ret)
        elif address == 0x0035EDD4:
            r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc_inst.reg_read(arm.UC_ARM_REG_R3)
            sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
            s0, s1 = struct.unpack_from("<II", uc_inst.mem_read(sp, 8))
            line_bytes = bytes(uc_inst.mem_read(r2, max(0, r3 * 2)))
            slot0 = struct.unpack_from("<I", uc_inst.mem_read(s0, 4))[0]
            calls.append(("parse_line", r0, r1, line_bytes, r3, slot0, s1))

    for addr in [*STUBS.keys(), STREAM_GET_SIZE, STREAM_READ]:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    ret = uc.reg_read(arm.UC_ARM_REG_R0)
    out_flags = bytes(uc.mem_read(FLAGS_ADDR, 0x20))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return ret, out_flags, calls, regs


def u16_str(s: str) -> bytes:
    return b"\xff\xfe" + s.encode("utf-16-le")


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs = compile_candidate()

    p_lines = u16_str("aa=1\nbb=2\ncc=3")
    p_trailing_nl = u16_str("xx=1\nyy=2\n")
    p_nul = u16_str("aa=1\x00bb")
    p_bom_only = b"\xff\xfe"
    p_bad_bom = b"\x00\x00aa"

    cases = [
        ("null_key", 0, 2, ["k0", None], 0, 10, 10, p_lines),
        ("size_too_small", 0, 2, ["k0"], 1, 1, 1, p_lines),
        ("size_too_large", 0, 2, ["k0"], 1, 0x4001, 0x4001, p_lines),
        ("read_short", 0, 2, ["k0"], 1, len(p_lines), len(p_lines) - 2, p_lines),
        ("bad_bom", 1, 2, ["k0"], 0, len(p_bad_bom), len(p_bad_bom), p_bad_bom),
        ("bom_only", 1, 2, ["k0"], 0, len(p_bom_only), len(p_bom_only), p_bom_only),
        ("embedded_nul", 1, 2, ["k0"], 0, len(p_nul), len(p_nul), p_nul),
        ("normal_lines_flag0", 0, 3, ["k0", "k1", "k2"], 0b101, len(p_lines), len(p_lines), p_lines),
        ("trailing_nl_flag1", 1, 3, ["k0", "k1"], 0, len(p_trailing_nl), len(p_trailing_nl), p_trailing_nl),
    ]

    for name, *args in cases:
        o_ret, o_flg, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, *args)
        c_ret, c_flg, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_relocs, *args)
        if o_ret != c_ret or o_flg != c_flg:
            print(f"FAIL {name}: ret/flags orig=0x{o_ret:08x} cand=0x{c_ret:08x}")
            return 1
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch\n  orig={o_calls}\n  cand={c_calls}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch")
            return 1

    # 5 negative / mutation controls
    ref_ret, ref_flg, ref_calls, _ = run_one(orig_code, FUNC_ADDR, None, *cases[7][1:])
    mutants = [
        ("mut_flag_1a", (1, 3, ["k0", "k1", "k2"], 0b101, len(p_lines), len(p_lines), p_lines)),
        ("mut_bit_1b", (0, 4, ["k0", "k1", "k2"], 0b101, len(p_lines), len(p_lines), p_lines)),
        ("mut_mask", (0, 3, ["k0", "k1", "k2"], 0b010, len(p_lines), len(p_lines), p_lines)),
        ("mut_bad_bom", (0, 3, ["k0", "k1", "k2"], 0b101, len(p_bad_bom), len(p_bad_bom), p_bad_bom)),
        ("mut_nul", (0, 3, ["k0", "k1", "k2"], 0b101, len(p_nul), len(p_nul), p_nul)),
    ]
    detected = 0
    for mname, margs in mutants:
        m_ret, m_flg, m_calls, _ = run_one(cand_code, 0x00180000, cand_relocs, *margs)
        if (m_ret, m_flg, m_calls) != (ref_ret, ref_flg, ref_calls):
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: func_0035f1b0 (0x0035f1b0) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
