#!/usr/bin/env python3
"""Differential test for ui_func_00235ac4 (0x00235ac4, 760 B) using Unicorn."""

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
    UC_ARM_REG_S0,
    UC_ARM_REG_SP,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = REPO_ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = REPO_ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
BUILD_DIR = REPO_ROOT / "build" / "test_leaf_00235ac4"
OBJ_PATH = BUILD_DIR / "leaf_batch45_b.o"

ORIG_BASE = 0x00235AC4
ORIG_SIZE = 760
CAND_BASE = 0x00800000
RODATA_BASE = 0x00900000
STUB_BASE = 0x00A00000
SELF_BASE = 0x20000000
C0_BASE = 0x20010000
NODE1_BASE = 0x20020000
NODE2_BASE = 0x20030000
STACK_TOP = 0x30010000
SENTINEL_LR = 0x7FFFF000

TARGET_FN = "ui_func_00235ac4"
ORIG_CALLEES = {
    0x002C615C: "ui_func_002c615c",
    0x003E7430: "func_003e7430",
    0x0037FD88: "func_0037fd88",
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
                        abs_relocs.append((r_off - fn_off, sec_to_ro_off[st_shndx] + st_value))

    return bytes(text_data[fn_off : fn_off + fn_size]), relocs, bytes(ro_blob), abs_relocs


def make_arm_uc():
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.mem_map(0x00100000, 0x00700000)
    uc.mem_map(CAND_BASE, 0x00100000)
    uc.mem_map(RODATA_BASE, 0x00100000)
    uc.mem_map(STUB_BASE, 0x00100000)
    uc.mem_map(SELF_BASE, 0x00100000)
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


def run_instance(code_bytes, is_orig, cand_relocs, ro_blob, abs_relocs, case_cfg):
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
        if name == "ui_func_002c615c":
            num = struct.unpack("<i", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_R0)))[0]
            den = struct.unpack("<i", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_R1)))[0]
            q = int(num / den) if den != 0 else 0
            calls.append(("idiv", num, den, q))
            uc_inst.reg_write(UC_ARM_REG_R0, q & 0xFFFFFFFF)
        elif name == "func_003e7430":
            p = uc_inst.reg_read(UC_ARM_REG_R0)
            idx = uc_inst.reg_read(UC_ARM_REG_R1)
            val_u32 = struct.unpack("<I", uc_inst.mem_read(p + 0x38 + idx * 4, 4))[0]
            calls.append(("3e7430", p, idx, val_u32))
            uc_inst.reg_write(UC_ARM_REG_S0, val_u32)
        elif name == "func_0037fd88":
            p = uc_inst.reg_read(UC_ARM_REG_R0)
            b = uc_inst.reg_read(UC_ARM_REG_R1) & 0xFF
            f_u32 = uc_inst.reg_read(UC_ARM_REG_S0)
            calls.append(("37fd88", p, b, f_u32))
            uc_inst.mem_write(p + 0xE0, struct.pack("<I", f_u32))
            uc_inst.mem_write(p + 0xCB, bytes([b]))

    if is_orig:
        for addr in ORIG_CALLEES:
            uc.hook_add(1 << 2, hook_code, begin=addr, end=addr)
    else:
        for addr in stub_map.values():
            uc.hook_add(1 << 2, hook_code, begin=addr, end=addr)

    self_buf = bytearray(0x100)
    c0_buf = bytearray(0x100)
    node1_buf = bytearray(0x150)
    node2_buf = bytearray(0x150)

    self_buf[5] = case_cfg["flag5"]
    struct.pack_into("<I", self_buf, 0xC0, C0_BASE)
    struct.pack_into("<I", self_buf, 0xC4, case_cfg["node_head"])
    struct.pack_into("<ff", self_buf, 0x08, case_cfg["f08"], case_cfg["f0c"])
    struct.pack_into("<fff", self_buf, 0x10, case_cfg["f10"], case_cfg["f14"], case_cfg["f18"])
    struct.pack_into("<IIII", self_buf, 0x54, 0x11111111, 0x22222222, 0x33333333, 0x44444444)
    self_buf[0x64] = case_cfg["b64"]
    self_buf[0x6C] = case_cfg["b6c"]
    self_buf[0x6D] = case_cfg["b6d"]
    struct.pack_into("<hh", self_buf, 0x6E, case_cfg["s6e"], case_cfg["s70"])
    struct.pack_into("<bb", self_buf, 0x72, case_cfg["s72"], case_cfg["s73"])
    struct.pack_into("<hh", self_buf, 0x74, case_cfg["s74"], case_cfg["s76"])
    struct.pack_into("<bb", self_buf, 0x78, case_cfg["s78"], case_cfg["s79"])
    struct.pack_into("<hh", self_buf, 0x7A, case_cfg["s7a"], case_cfg["s7c"])
    struct.pack_into("<bb", self_buf, 0x7E, case_cfg["s7e"], case_cfg["s7f"])
    struct.pack_into("<hh", self_buf, 0x80, case_cfg["s80"], case_cfg["s82"])
    self_buf[0x84] = case_cfg["b84"]
    self_buf[0x86] = case_cfg["b86"]
    self_buf[0x92] = case_cfg["b92"]
    self_buf[0x93] = case_cfg["b93"]
    self_buf[0x94] = case_cfg["b94"]
    self_buf[0x95] = case_cfg["b95"]
    struct.pack_into("<ff", self_buf, 0x98, case_cfg["f98"], case_cfg["f9c"])

    struct.pack_into("<fffff", c0_buf, 0x14, case_cfg["c14"], case_cfg["c18"], case_cfg["c1c"], case_cfg["c20"], case_cfg["c24"])
    struct.pack_into("<f", c0_buf, 0x28, case_cfg["c28"])
    c0_buf[0x2C] = case_cfg["c2c"]
    struct.pack_into("<fff", c0_buf, 0x30, case_cfg["c30"], case_cfg["c38"], case_cfg["c3c"])
    struct.pack_into("<f", c0_buf, 0x60, case_cfg["c60"])
    c0_buf[0x74] = case_cfg["c74"]

    struct.pack_into("<I", node1_buf, 0x138, case_cfg["node2"])
    struct.pack_into("<I", node2_buf, 0x138, 0)

    uc.mem_write(SELF_BASE, bytes(self_buf))
    uc.mem_write(C0_BASE, bytes(c0_buf))
    uc.mem_write(NODE1_BASE, bytes(node1_buf))
    uc.mem_write(NODE2_BASE, bytes(node2_buf))

    uc.reg_write(UC_ARM_REG_R0, SELF_BASE)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL_LR)

    entry = ORIG_BASE if is_orig else CAND_BASE
    uc.emu_start(entry, SENTINEL_LR, count=20000)

    return {
        "node1": bytes(uc.mem_read(NODE1_BASE, 0x140)),
        "node2": bytes(uc.mem_read(NODE2_BASE, 0x140)),
        "calls": calls,
    }


def make_cases():
    base = {
        "flag5": 1,
        "node_head": NODE1_BASE,
        "node2": NODE2_BASE,
        "f08": 2.0,
        "f0c": 1.5,
        "f10": 0.25,
        "f14": 0.5,
        "f18": 1.25,
        "b64": 7,
        "b6c": 20,
        "b6d": 120,
        "s6e": 100,
        "s70": 40,
        "s72": -30,
        "s73": 50,
        "s74": 80,
        "s76": 30,
        "s78": 10,
        "s79": 90,
        "s7a": 60,
        "s7c": 20,
        "s7e": -20,
        "s7f": 60,
        "s80": 50,
        "s82": 25,
        "b84": 100,
        "b86": 64,
        "b92": 90,
        "b93": 32,
        "b94": 64,
        "b95": 42,
        "f98": 0.75,
        "f9c": 3.25,
        "c14": 1.5,
        "c18": 2.0,
        "c1c": 0.125,
        "c20": 0.25,
        "c24": 0.5,
        "c28": 4.5,
        "c2c": 0,
        "c30": 0.75,
        "c38": 0.1,
        "c3c": 0.2,
        "c60": 0.8,
        "c74": 80,
    }
    cases = [dict(base)]

    c2 = dict(base)
    c2["s70"] = 120
    c2["s76"] = 80
    c2["s7c"] = 60
    c2["s7f"] = -120
    c2["s82"] = 50
    c2["c2c"] = 99
    c2["node2"] = 0
    cases.append(c2)

    c3 = dict(base)
    c3["s73"] = 120
    c3["s79"] = 127
    c3["s76"] = 80
    c3["s7c"] = 60
    cases.append(c3)

    c4 = dict(base)
    c4["flag5"] = 0
    cases.append(c4)

    c5 = dict(base)
    c5["node_head"] = 0
    cases.append(c5)
    return cases


def main():
    orig_all = CODE_BIN.read_bytes()
    orig_bytes = orig_all[ORIG_BASE - 0x00100000 : ORIG_BASE - 0x00100000 + ORIG_SIZE]
    cand_bytes, cand_relocs, ro_blob, abs_relocs = compile_candidate()

    cases = make_cases()
    for idx, cfg in enumerate(cases):
        o = run_instance(orig_bytes, True, [], b"", [], cfg)
        c = run_instance(cand_bytes, False, cand_relocs, ro_blob, abs_relocs, cfg)
        if o["node1"] != c["node1"] or o["node2"] != c["node2"] or o["calls"] != c["calls"]:
            raise AssertionError(f"case {idx} mismatch:\norig calls={o['calls']}\ncand calls={c['calls']}")

    mutants = [
        ("flip_flag5_cmp", 0x00235AD8, b"\x01\x00\x50\xe3"),
        ("flip_node2_branch", 0x00235D8C, b"\x00\x00\x00\xea"),
        ("corrupt_b64_off", 0x00235D7C, b"\x65\x00\xd5\xe5"),
        ("corrupt_s17_off", 0x00235D28, b"\xc8\x00\x84\xed"),
        ("skip_loop_step", 0x00235D04, b"\x01\x00\x54\xe3"),
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
                if o["node1"] != m["node1"] or o["node2"] != m["node2"] or o["calls"] != m["calls"]:
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
