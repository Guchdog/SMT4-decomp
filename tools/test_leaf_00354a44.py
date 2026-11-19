#!/usr/bin/env python3
"""Differential test for engine_func_00354a44 (0x00354a44) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_00354a44"

FUNC_ADDR = 0x00354A44
FUNC_SIZE = 492

STUB_STRNCMP = 0x002B45F8
STUB_LOG_ERR = 0x002C14F4

RODATA_BASE = 0x18000000
OBJ_ADDR = 0x20000000
TBL_ADDR = 0x20000100
ENTRIES_ADDR = 0x20000200
STR_BASE = 0x20001000
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


def _layout_rodata(obj_file: Path) -> tuple[bytes, dict[int, int]]:
    data = obj_file.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    raw_secs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = raw_secs[e_shstrndx][4]
    names = [data[shstr_off + s[0] : data.index(b"\x00", shstr_off + s[0])].decode("ascii", errors="replace") for s in raw_secs]

    image = bytearray()
    sec_addr: dict[int, int] = {}
    for i, s in enumerate(raw_secs):
        if s[1] == 1 and (s[2] & 2) and not names[i].startswith(".text"):
            align = max(s[8], 1)
            while len(image) % align:
                image.append(0)
            sec_addr[i] = RODATA_BASE + len(image)
            image.extend(data[s[4] : s[4] + s[5]])

    for i, s in enumerate(raw_secs):
        if s[1] == 9 and s[7] in sec_addr:
            target_off = sec_addr[s[7]] - RODATA_BASE
            symtab = raw_secs[s[6]]
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if r_type == 2:
                    st_shndx = struct.unpack_from("<H", data, symtab[4] + sym_idx * 16 + 14)[0]
                    if st_shndx in sec_addr:
                        val = struct.unpack_from("<I", image, target_off + r_off)[0]
                        struct.pack_into("<I", image, target_off + r_off, sec_addr[st_shndx] + val)

    return bytes(image), sec_addr


def compile_candidate() -> tuple[bytes, bytes, list[tuple[str, int]]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_path = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj_path)
    if res.returncode != 0:
        raise RuntimeError(f"compile failed:\n{res.stderr}\n{res.stdout}")

    rodata, sec_addr = _layout_rodata(obj_path)
    data = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    secs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = secs[e_shstrndx][4]
    sec_names = [data[shstr_off + s[0] : data.index(b"\x00", shstr_off + s[0])].decode("ascii", errors="replace") for s in secs]
    tidx = sec_names.index(".text")
    text_data = bytearray(data[secs[tidx][4] : secs[tidx][4] + secs[tidx][5]])

    symtab = next(s for s in secs if s[1] == 2)
    strtab_off = secs[symtab[6]][4]
    fn_off = fn_size = None
    for idx in range(symtab[5] // 16):
        st_name, st_value, st_size, _st_info, _st_other, st_shndx = struct.unpack_from("<IIIbbH", data, symtab[4] + idx * 16)
        if st_shndx == tidx:
            name = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
            if name == "engine_func_00354a44":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol engine_func_00354a44 not found")

    relocs: list[tuple[str, int]] = []
    for s in secs:
        if s[1] == 9 and s[7] == tidx:
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if not (fn_off <= r_off < fn_off + fn_size):
                    continue
                if r_type in (28, 29):
                    st_name = struct.unpack_from("<I", data, symtab[4] + sym_idx * 16)[0]
                    sname = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
                    relocs.append((sname, r_off - fn_off))
                elif r_type == 2:
                    st_value, _, _, _, st_shndx = struct.unpack_from("<IIbbH", data, symtab[4] + sym_idx * 16 + 4)
                    if st_shndx in sec_addr:
                        addend = struct.unpack_from("<I", text_data, r_off)[0]
                        struct.pack_into("<I", text_data, r_off, sec_addr[st_shndx] + st_value + addend)

    return bytes(text_data[fn_off : fn_off + fn_size]), rodata, relocs


def patch_bl(code: bytearray, at_off: int, src_pc: int, dst_pc: int) -> None:
    delta = (dst_pc - (src_pc + 8)) >> 2
    insn = 0xEB000000 | (delta & 0x00FFFFFF)
    struct.pack_into("<I", code, at_off, insn)


def read_cstr(uc: unicorn.Uc, ptr: int, max_len: int) -> bytes:
    if ptr == 0:
        return b""
    raw = bytes(uc.mem_read(ptr, max_len))
    nul = raw.find(b"\x00")
    return raw[:nul] if nul >= 0 else raw


def run_one(
    code_bytes: bytes,
    base_addr: int,
    orig_rodata: bytes | None,
    cand_rodata: bytes | None,
    relocs: list[tuple[str, int]] | None,
    pairs: list[tuple[str, str | None]],
) -> tuple[int, list[int], dict[str, int]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_map(RODATA_BASE, 0x00100000)
    uc.mem_map(0x20000000, 0x00010000)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    if orig_rodata is not None:
        uc.mem_write(0x00400000, orig_rodata)
    if cand_rodata is not None:
        uc.mem_write(RODATA_BASE, cand_rodata)

    buf = bytearray(code_bytes)
    if relocs is not None:
        for sym_name, off in relocs:
            if "engine_func_002b45f8" in sym_name:
                patch_bl(buf, off, base_addr + off, STUB_STRNCMP)
            elif "engine_func_002c14f4" in sym_name:
                patch_bl(buf, off, base_addr + off, STUB_LOG_ERR)
            else:
                raise RuntimeError(f"unexpected relocation: {sym_name}")

    uc.mem_write(base_addr, bytes(buf))
    uc.mem_write(STUB_STRNCMP, make_stub_bx_lr())
    uc.mem_write(STUB_LOG_ERR, make_stub_bx_lr())

    # Layout key/value pairs in memory
    cursor = STR_BASE
    entry_bytes = bytearray()
    for k, v in pairs:
        k_addr = cursor
        kb = k.encode("ascii") + b"\x00"
        uc.mem_write(k_addr, kb)
        cursor += (len(kb) + 3) & ~3
        if v is None:
            v_addr = 0
        else:
            v_addr = cursor
            vb = v.encode("ascii") + b"\x00"
            uc.mem_write(v_addr, vb)
            cursor += (len(vb) + 3) & ~3
        entry_bytes.extend(struct.pack("<II", k_addr, v_addr))

    uc.mem_write(ENTRIES_ADDR, bytes(entry_bytes))
    uc.mem_write(TBL_ADDR, struct.pack("<II", ENTRIES_ADDR, len(pairs)))
    uc.mem_write(OBJ_ADDR, struct.pack("<II", 0, TBL_ADDR))

    uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)

    err_logs: list[int] = []

    def hook_code(uc_inst, address, size, user_data):
        if address == STUB_STRNCMP:
            p0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            p1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
            n = uc_inst.reg_read(arm.UC_ARM_REG_R2)
            if p0 == 0 or p1 == 0 or n == 0:
                uc_inst.reg_write(arm.UC_ARM_REG_R0, 0 if p0 == p1 else 1)
            else:
                s0 = read_cstr(uc_inst, p0, n)
                s1 = read_cstr(uc_inst, p1, n)
                uc_inst.reg_write(arm.UC_ARM_REG_R0, 0 if s0 == s1 else (1 if s0 > s1 else 0xFFFFFFFF))
        elif address == STUB_LOG_ERR:
            err_logs.append(uc_inst.reg_read(arm.UC_ARM_REG_R0))

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=STUB_STRNCMP, end=STUB_STRNCMP)
    uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=STUB_LOG_ERR, end=STUB_LOG_ERR)
    uc.emu_start(base_addr, LR_SENTINEL, count=20000)

    ret = uc.reg_read(arm.UC_ARM_REG_R0)
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return ret, err_logs, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    orig_rodata = orig_all[0x00400000 - 0x00100000 : 0x00400000 - 0x00100000 + 0x20000]
    cand_code, cand_rodata, cand_relocs = compile_candidate()

    cases = [
        ("redeemable_gunit", [("other", "x"), ("sys.ECardStatus", "REDEEMABLE"), ("sys.ECardCurrency", "GUNIT")]),
        ("redeemable_points", [("sys.ECardStatus", "REDEEMABLE"), ("sys.ECardCurrency", "POINTS")]),
        ("redeemable_unknown_cur", [("sys.ECardStatus", "REDEEMABLE"), ("sys.ECardCurrency", "EUROS")]),
        ("redeemable_missing_cur", [("sys.ECardStatus", "REDEEMABLE")]),
        ("redeemable_null_cur", [("sys.ECardStatus", "REDEEMABLE"), ("sys.ECardCurrency", None)]),
        ("redeemed", [("sys.ECardStatus", "REDEEMED")]),
        ("revoked", [("sys.ECardStatus", "REVOKED")]),
        ("inactive", [("sys.ECardStatus", "INACTIVE")]),
        ("unknown_status", [("sys.ECardStatus", "EXPIRED")]),
        ("missing_status", [("foo", "bar")]),
        ("null_status", [("sys.ECardStatus", None)]),
    ]

    for name, pairs in cases:
        o_ret, o_errs, o_regs = run_one(orig_code, FUNC_ADDR, orig_rodata, None, None, pairs)
        c_ret, c_errs, c_regs = run_one(cand_code, 0x00180000, None, cand_rodata, cand_relocs, pairs)
        if o_ret != c_ret or o_errs != c_errs or o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: orig=(0x{o_ret:08x}, {o_errs}) cand=(0x{c_ret:08x}, {c_errs})")
            return 1

    # 5 negative / mutation controls
    ref_ret, ref_errs, _ = run_one(orig_code, FUNC_ADDR, orig_rodata, None, None, cases[0][1])
    mutants = [
        ("mut_points", [("sys.ECardStatus", "REDEEMABLE"), ("sys.ECardCurrency", "POINTS")]),
        ("mut_redeemed", [("sys.ECardStatus", "REDEEMED")]),
        ("mut_revoked", [("sys.ECardStatus", "REVOKED")]),
        ("mut_inactive", [("sys.ECardStatus", "INACTIVE")]),
        ("mut_missing", []),
    ]
    detected = 0
    for mname, mpairs in mutants:
        m_ret, m_errs, _ = run_one(cand_code, 0x00180000, None, cand_rodata, cand_relocs, mpairs)
        if (m_ret, m_errs) != (ref_ret, ref_errs):
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: engine_func_00354a44 (0x00354a44) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
