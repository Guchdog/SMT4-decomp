#!/usr/bin/env python3
"""Differential test for func_002ed03c (0x002ed03c, 932 B) using Unicorn."""

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
    UC_ARM_REG_SP,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = REPO_ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = REPO_ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
BUILD_DIR = REPO_ROOT / "build" / "test_leaf_002ed03c"
OBJ_PATH = BUILD_DIR / "leaf_batch45_b.o"

ORIG_BASE = 0x002ED03C
ORIG_SIZE = 932
CAND_BASE = 0x00800000
RODATA_BASE = 0x00900000
STUB_BASE = 0x00A00000

G446FE8 = 0x00446FE8
G49F91C = 0x0049F91C
A_E45C = 0x0049E45C
A_E65C = 0x0049E65C
A_E7DC = 0x0049E7DC
A_E87C = 0x0049E87C

P0_ADDR = 0x20000000
P1_ADDR = 0x20000100
TRI2_ADDR = 0x20010000
TRI3_ADDR = 0x20020000
STACK_TOP = 0x30010000
SENTINEL_LR = 0x7FFFF000

TARGET_FN = "func_002ed03c"
ORIG_CALLEES = {
    0x0026EE9C: "script_vm_func_0026ee9c",
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

        if name == "script_vm_func_0026ee9c":
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            r1 = struct.unpack("<i", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_R1)))[0]
            r2 = struct.unpack("<i", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_R2)))[0]
            r3 = uc_inst.reg_read(UC_ARM_REG_R3)
            s0 = uc_inst.reg_read(UC_ARM_REG_S0)
            s1 = uc_inst.reg_read(UC_ARM_REG_S1)
            s2 = uc_inst.reg_read(UC_ARM_REG_S2)
            s3 = uc_inst.reg_read(UC_ARM_REG_S3)
            calls.append((name, r1, r2, r3, s0, s1, s2, s3))
            uc_inst.mem_write(r0, struct.pack("<f", cfg["t_out"]))

    if is_orig:
        for addr in ORIG_CALLEES:
            uc.hook_add(1 << 2, hook_code, begin=addr, end=addr)
    else:
        for addr in stub_map.values():
            uc.hook_add(1 << 2, hook_code, begin=addr, end=addr)

    uc.mem_write(A_E45C, b"\xFF" * 16)
    uc.mem_write(A_E65C, b"\xFF" * 16)
    uc.mem_write(A_E7DC, b"\xFF" * 16)
    uc.mem_write(A_E87C, b"\xFF" * 16)

    g446 = bytearray(0x28)
    struct.pack_into("<IIIII", g446, 0x00, 0, 5, 6, len(cfg["tri2"]), len(cfg["tri3"]))
    struct.pack_into("<II", g446, 0x20, TRI2_ADDR, TRI3_ADDR)
    uc.mem_write(G446FE8, bytes(g446))

    for base_addr, tris in ((TRI2_ADDR, cfg["tri2"]), (TRI3_ADDR, cfg["tri3"])):
        buf = bytearray(max(1, len(tris)) * 0xA8)
        for i, (b4, b5, b8, nx, ny, nz, dist) in enumerate(tris):
            off = i * 0xA8
            buf[off + 4] = b4 & 0xFF
            buf[off + 5] = b5 & 0xFF
            buf[off + 8] = b8 & 0xFF
            struct.pack_into("<ffff", buf, off + 0x0C, nx, ny, nz, dist)
        uc.mem_write(base_addr, bytes(buf))

    uc.mem_write(P0_ADDR, struct.pack("<fff", *cfg["p0"]))
    uc.mem_write(P1_ADDR, struct.pack("<fff", *cfg["p1"]))

    uc.reg_write(UC_ARM_REG_R0, P0_ADDR)
    uc.reg_write(UC_ARM_REG_R1, P1_ADDR)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL_LR)

    entry = ORIG_BASE if is_orig else CAND_BASE
    uc.emu_start(entry, SENTINEL_LR, count=20000)

    return {
        "ret": uc.reg_read(UC_ARM_REG_R0),
        "p0": struct.unpack("<fff", uc.mem_read(P0_ADDR, 12)),
        "p1": struct.unpack("<fff", uc.mem_read(P1_ADDR, 12)),
        "g49_3d0": struct.unpack("<ii", uc.mem_read(G49F91C + 0x3D0, 8)),
        "arrays": (
            bytes(uc.mem_read(A_E45C, 8)),
            bytes(uc.mem_read(A_E65C, 8)),
            bytes(uc.mem_read(A_E7DC, 8)),
            bytes(uc.mem_read(A_E87C, 8)),
        ),
        "calls": calls,
    }


def make_cases():
    return [
        {  # dist < 0.01 -> early return 1
            "p0": (1.0, 2.0, 3.0), "p1": (1.0, 2.0, 3.0), "t_out": 10.0,
            "tri2": [], "tri3": [],
        },
        {  # tri2[0] active b4=1 (sets sb=1, g49_3d0), tri3[0] active b4=2 (sets A_E87C[0]=1)
            "p0": (10.0, 20.0, 30.0), "p1": (0.0, 0.0, 0.0), "t_out": 250.0,
            "tri2": [(1, 2, 1, 0.0, 1.0, 0.0, 30.0), (2, 1, 1, 1.0, 0.0, 0.0, 5.0)],
            "tri3": [(2, 3, 1, 1.0, 0.0, 0.0, 5.0)],
        },
        {  # tri2[0] b4=2 with negative d (skips push), tri3[0] b4=1 with t_out=100
            "p0": (10.0, 20.0, 30.0), "p1": (0.0, 0.0, 0.0), "t_out": 100.0,
            "tri2": [(2, 1, 1, 0.0, 1.0, 0.0, 50.0)],
            "tri3": [(1, 1, 1, 0.0, 1.0, 0.0, 30.0)],
        },
        {  # t_out < 0 -> rejected
            "p0": (10.0, 20.0, 30.0), "p1": (0.0, 0.0, 0.0), "t_out": -1.0,
            "tri2": [(1, 1, 1, 0.0, 1.0, 0.0, 30.0)],
            "tri3": [(2, 1, 1, 0.0, 1.0, 0.0, 5.0)],
        },
    ]


def main():
    orig_all = CODE_BIN.read_bytes()
    orig_bytes = orig_all[ORIG_BASE - 0x00100000 : ORIG_BASE - 0x00100000 + ORIG_SIZE]
    cand_bytes, cand_relocs, ro_blob, abs_relocs = compile_candidate()

    cases = make_cases()
    for idx, cfg in enumerate(cases):
        o = run_instance(orig_bytes, True, [], b"", [], cfg)
        c = run_instance(cand_bytes, False, cand_relocs, ro_blob, abs_relocs, cfg)
        if o["ret"] != c["ret"] or o["g49_3d0"] != c["g49_3d0"] or o["arrays"] != c["arrays"] or o["calls"] != c["calls"]:
            raise AssertionError(f"case {idx} mismatch:\norig={o}\ncand={c}")
        for a, b in zip(o["p0"] + o["p1"], c["p0"] + c["p1"]):
            if abs(a - b) > 1e-4:
                raise AssertionError(f"case {idx} vec mismatch:\norig={o['p0']} {o['p1']}\ncand={c['p0']} {c['p1']}")

    mutants = [
        ("corrupt_early_ret", 0x002ED18C, b"\x00\x00\xa0\xc3"),
        ("skip_3d0_init", 0x002ED07C, b"\x00\x00\xa0\xe1"),
        ("corrupt_sb_set", 0x002ED380, b"\x00\xb0\xa0\xe3"),
        ("corrupt_tri_step", 0x002ED2EC, b"\xa4\x40\x84\xe2"),
        ("corrupt_out_sub25", 0x002ED308, b"\x00\x0a\x39\xee"),
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
                if (o["ret"] != m["ret"] or o["p0"] != m["p0"] or o["p1"] != m["p1"] or
                        o["g49_3d0"] != m["g49_3d0"] or o["arrays"] != m["arrays"] or o["calls"] != m["calls"]):
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
