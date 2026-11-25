#!/usr/bin/env python3
"""Differential test for camp_func_00194a08 (0x00194a08, 948 B) using Unicorn."""

from __future__ import annotations

import pathlib
import struct
import sys

from unicorn import UC_ARCH_ARM, UC_MODE_ARM, Uc, UcError
from unicorn.arm_const import (
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_LR,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_S0,
    UC_ARM_REG_S1,
    UC_ARM_REG_S2,
    UC_ARM_REG_S3,
    UC_ARM_REG_S4,
    UC_ARM_REG_SP,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = REPO_ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = REPO_ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
BUILD_DIR = REPO_ROOT / "build" / "test_leaf_00194a08"
OBJ_PATH = BUILD_DIR / "leaf_batch45_b.o"

ORIG_BASE = 0x00194A08
ORIG_SIZE = 948
CAND_BASE = 0x00800000
RODATA_BASE = 0x00900000
STUB_BASE = 0x00A00000

G43DD08_SLOT = 0x0043DD08
G5_BASE = 0x20000000
TBL_PTR = 0x20010000
TBB_PAYLOAD = 0x20020000
LAY_BASE = 0x20030000
SUB_P_ADDR = 0x20040000
STACK_TOP = 0x30010000
SENTINEL_LR = 0x7FFFF000

TARGET_FN = "camp_func_00194a08"
ORIG_CALLEES = {
    0x0029D8E4: "camp_func_0029d8e4",
    0x002BEF7C: "ui_func_002bef7c",
    0x002BF558: "func_002bf558",
    0x00290C38: "camp_func_00290c38",
    0x002BF6D0: "camp_func_002bf6d0",
    0x0029F260: "camp_func_0029f260",
    0x002C0EC4: "Tbb_GetGlobalSubTable",
    0x002C0E9C: "Tbb_GetPayloadData",
    0x002C0E4C: "Tbb_GetRowCount",
    0x002BE7FC: "ui_func_002be7fc",
    0x002BE77C: "ui_func_002be77c",
    0x00290A68: "ui_func_00290a68",
    0x002B7118: "engine_func_002b7118",
}


def compile_candidate():
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(SRC_CPP, OBJ_PATH)
    if res.returncode != 0:
        raise RuntimeError(f"compile failed:\n{res.stderr}")

    data = OBJ_PATH.read_bytes()
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
            if name == TARGET_FN:
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError(f"{TARGET_FN} not found in object")

    ro_blob = bytearray()
    sec_to_ro_off: dict[int, int] = {}
    for idx, s in enumerate(shdrs):
        nm = sh_name(idx)
        if nm.startswith(".rodata"):
            sec_to_ro_off[idx] = len(ro_blob)
            ro_blob.extend(data[s[4] : s[4] + s[5]])
            while len(ro_blob) % 4:
                ro_blob.append(0)

    relocs = []
    abs_relocs = []
    for s in shdrs:
        if s[1] == 9 and s[7] == tidx:
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if fn_off <= r_off < fn_off + fn_size:
                    st_name, st_value, _, _, _, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + sym_idx * 16)
                    sname = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
                    if r_type in (28, 29):
                        relocs.append((sname, r_off - fn_off))
                    elif r_type == 2 and st_shndx in sec_to_ro_off:
                        addend = struct.unpack_from("<I", text_data, r_off)[0]
                        abs_relocs.append((r_off - fn_off, sec_to_ro_off[st_shndx] + st_value + addend))
                    elif r_type == 2 and st_shndx == tidx:
                        addend = struct.unpack_from("<I", text_data, r_off)[0]
                        abs_relocs.append((r_off - fn_off, (CAND_BASE - RODATA_BASE) + (addend + st_value - fn_off)))

    return bytes(text_data[fn_off : fn_off + fn_size]), relocs, bytes(ro_blob), abs_relocs


def make_arm_uc():
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.mem_map(0x00100000, 0x00700000)
    uc.mem_map(CAND_BASE, 0x00100000)
    uc.mem_map(RODATA_BASE, 0x00100000)
    uc.mem_map(STUB_BASE, 0x00100000)
    uc.mem_map(0x20000000, 0x00100000)
    uc.mem_map(0x30000000, 0x00100000)
    uc.mem_map(0x7FFF0000, 0x00010000)
    return uc


def patch_candidate_relocs(uc, cand_bytes, relocs, abs_relocs, stub_map):
    buf = bytearray(cand_bytes)
    for sym_name, rel_off in relocs:
        if sym_name not in stub_map:
            raise RuntimeError(f"missing stub for {sym_name}")
        pc = CAND_BASE + rel_off + 8
        diff = (stub_map[sym_name] - pc) >> 2
        insn = struct.unpack_from("<I", buf, rel_off)[0]
        insn = (insn & 0xFF000000) | (diff & 0x00FFFFFF)
        struct.pack_into("<I", buf, rel_off, insn)
    for rel_off, ro_off in abs_relocs:
        struct.pack_into("<I", buf, rel_off, RODATA_BASE + ro_off)
    uc.mem_write(CAND_BASE, bytes(buf))


def read_cstr(uc, addr):
    raw = bytes(uc.mem_read(addr, 64))
    return raw.split(b"\x00", 1)[0]


def run_instance(code_bytes, is_orig, cand_relocs, ro_blob, abs_relocs, cfg):
    uc = make_arm_uc()
    stub_map = {}
    if is_orig:
        uc.mem_write(ORIG_BASE, code_bytes)
    else:
        if ro_blob:
            uc.mem_write(RODATA_BASE, ro_blob)
        next_stub = STUB_BASE
        for addr, name in ORIG_CALLEES.items():
            stub_map[name] = next_stub
            uc.mem_write(next_stub, struct.pack("<I", 0xE12FFF1E))
            next_stub += 4
        patch_candidate_relocs(uc, code_bytes, cand_relocs, abs_relocs, stub_map)

    for addr in ORIG_CALLEES:
        if addr == 0x002BE7FC:
            uc.mem_write(addr, b"\x70\x47\x70\x47")
        else:
            uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))

    calls = []

    def hook_code(uc_inst, address, size, user_data):
        name = None
        if is_orig and address in ORIG_CALLEES:
            name = ORIG_CALLEES[address]
        elif not is_orig:
            for k, v in stub_map.items():
                if address == v:
                    name = k
                    break

        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(UC_ARM_REG_R2)
        r3 = uc_inst.reg_read(UC_ARM_REG_R3)
        sp = uc_inst.reg_read(UC_ARM_REG_SP)

        if name == "camp_func_0029d8e4":
            calls.append((name, r0 - G5_BASE))
            uc_inst.reg_write(UC_ARM_REG_R0, cfg["count"])
        elif name == "ui_func_002bef7c":
            calls.append((name, r0 - G5_BASE))
            uc_inst.reg_write(UC_ARM_REG_R0, 12)
        elif name == "func_002bf558":
            s0, s1 = struct.unpack("<II", uc_inst.mem_read(sp, 8))
            calls.append((name, r0, r1, r2, r3, s0, s1))
        elif name == "camp_func_00290c38":
            s = struct.unpack("<12I", uc_inst.mem_read(sp, 48))
            calls.append((name, r0 - G5_BASE, r1, r2, r3, s))
        elif name == "camp_func_002bf6d0":
            calls.append((name, r0, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, LAY_BASE + r1 * 0x20)
        elif name == "camp_func_0029f260":
            calls.append((name, r0 - G5_BASE))
            uc_inst.reg_write(UC_ARM_REG_R0, 0)
        elif name == "Tbb_GetGlobalSubTable":
            calls.append((name, r0, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, TBL_PTR)
        elif name == "Tbb_GetPayloadData":
            calls.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, TBB_PAYLOAD)
        elif name == "Tbb_GetRowCount":
            calls.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, cfg["row_count"])
        elif name == "ui_func_00290a68":
            uc_inst.mem_write(r0, f"{r1}".encode("ascii") + b"\x00")
            calls.append((name, r1))
        elif name == "ui_func_002be7fc":
            fmt = read_cstr(uc_inst, r1)
            a2 = read_cstr(uc_inst, r2)
            if fmt == b"%s":
                out = a2
            elif b"\x82g" in fmt:
                a3 = read_cstr(uc_inst, r3)
                out = a2 + b"H_" + a3 + b"M"
            else:
                a3 = read_cstr(uc_inst, r3)
                out = a2 + b"_" + a3
            uc_inst.mem_write(r0, out + b"\x00")
            calls.append((name, fmt, out))
        elif name == "ui_func_002b7118" or name == "engine_func_002b7118":
            s = read_cstr(uc_inst, r0)
            calls.append((name, s, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, len(s) * 8)
        elif name == "ui_func_002be77c":
            s = read_cstr(uc_inst, r2)
            f0 = uc_inst.reg_read(UC_ARM_REG_S0)
            f1 = uc_inst.reg_read(UC_ARM_REG_S1)
            f2 = uc_inst.reg_read(UC_ARM_REG_S2)
            f3 = uc_inst.reg_read(UC_ARM_REG_S3)
            f4 = uc_inst.reg_read(UC_ARM_REG_S4)
            calls.append((name, r0, r1, s, f0, f1, f2, f3, f4))

    if is_orig:
        for addr in ORIG_CALLEES:
            uc.hook_add(1 << 2, hook_code, begin=addr, end=addr)
    else:
        for addr in stub_map.values():
            uc.hook_add(1 << 2, hook_code, begin=addr, end=addr)

    uc.mem_write(G43DD08_SLOT, struct.pack("<I", G5_BASE))
    g5 = bytearray(0x600)
    struct.pack_into("<hhh", g5, 0x348, 10, 20, 30)
    struct.pack_into("<hh", g5, 0x424, cfg["row_idx"], 0)
    struct.pack_into("<I", g5, 0x35C, cfg["val35c"])
    uc.mem_write(G5_BASE, bytes(g5))

    uc.mem_write(SUB_P_ADDR, struct.pack("<h", 180))
    for gid in (0x13, 0x14, 0x15, 0x16):
        buf = bytearray(0x20)
        struct.pack_into("<hhI", buf, 8, 20 + gid * 3, 40 + gid, SUB_P_ADDR)
        uc.mem_write(LAY_BASE + gid * 0x20, bytes(buf))

    tbb = bytearray(0x80)
    row_off = 0x40
    tbb[row_off + 2 : row_off + 7] = b"NAME\x00"
    tbb[row_off + 0x37 : row_off + 0x3D] = cfg["unit"]
    tbb[row_off + 0x3F] = cfg["is_time"]
    uc.mem_write(TBB_PAYLOAD, bytes(tbb))

    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL_LR)

    entry = ORIG_BASE if is_orig else CAND_BASE
    uc.emu_start(entry, SENTINEL_LR, count=20000)

    return {"calls": calls}


def make_cases():
    return [
        {"count": 0, "row_count": 4, "row_idx": 1, "val35c": 100, "unit": b"PTS\x00\x00\x00", "is_time": 0},
        {"count": 1, "row_count": 4, "row_idx": 1, "val35c": 123, "unit": b"PTS\x00\x00\x00", "is_time": 0},
        {"count": 1, "row_count": 4, "row_idx": 1, "val35c": 3665, "unit": b"PTS\x00\x00\x00", "is_time": 1},
        {"count": 1, "row_count": 4, "row_idx": 1, "val35c": 77, "unit": b"0\x00\x00\x00\x00\x00", "is_time": 0},
        {"count": 1, "row_count": 1, "row_idx": 2, "val35c": 50, "unit": b"PTS\x00\x00\x00", "is_time": 0},
    ]


def main():
    orig_all = CODE_BIN.read_bytes()
    orig_bytes = orig_all[ORIG_BASE - 0x00100000 : ORIG_BASE - 0x00100000 + ORIG_SIZE]
    cand_bytes, cand_relocs, ro_blob, abs_relocs = compile_candidate()

    cases = make_cases()
    for idx, cfg in enumerate(cases):
        o = run_instance(orig_bytes, True, [], b"", [], cfg)
        c = run_instance(cand_bytes, False, cand_relocs, ro_blob, abs_relocs, cfg)
        if o["calls"] != c["calls"]:
            raise AssertionError(f"case {idx} mismatch:\norig={o['calls']}\ncand={c['calls']}")

    mutants = [
        ("flip_early_exit", 0x00194A2C, b"\x00\x00\x00\xea"),
        ("flip_last_row", 0x00194A8C, b"\x00\x00\x00\xea"),
        ("corrupt_tbb_slot", 0x00194B40, b"\x38\x00\xa0\xe3"),
        ("flip_is_time", 0x00194BF0, b"\x02\x00\x50\xe3"),
        ("corrupt_unit_30", 0x00194BFC, b"\x31\x00\x50\xe3"),
    ]
    detected = 0
    for name, m_addr, repl in mutants:
        m_off = m_addr - ORIG_BASE
        mut_bytes = bytearray(orig_bytes)
        mut_bytes[m_off : m_off + 4] = repl
        caught = False
        for cfg in cases:
            try:
                o = run_instance(orig_bytes, True, [], b"", [], cfg)
                m = run_instance(bytes(mut_bytes), True, [], b"", [], cfg)
                if o["calls"] != m["calls"]:
                    caught = True
                    break
            except UcError:
                caught = True
                break
        if not caught:
            raise AssertionError(f"mutant {name} was NOT detected")
        detected += 1

    print(
        f"PASS: {TARGET_FN} (0x{ORIG_BASE:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {ORIG_SIZE} B)"
    )


if __name__ == "__main__":
    raise SystemExit(main())
