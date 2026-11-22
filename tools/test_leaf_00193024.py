#!/usr/bin/env python3
"""Differential test for func_00193024 (0x00193024, 784 B) using Unicorn."""

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
    UC_ARM_REG_SP,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = REPO_ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = REPO_ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
BUILD_DIR = REPO_ROOT / "build" / "test_leaf_00193024"
OBJ_PATH = BUILD_DIR / "leaf_batch45_b.o"

ORIG_BASE = 0x00193024
ORIG_SIZE = 784
CAND_BASE = 0x00800000
RODATA_BASE = 0x00900000
STUB_BASE = 0x00A00000

SELF_BASE = 0x20000000
FLAG228_ADDR = 0x20010000
NODE_BASE = 0x20020000
STACK_TOP = 0x30010000
SENTINEL_LR = 0x7FFFF000

TARGET_FN = "func_00193024"
ORIG_CALLEES = {
    0x002916B8: "func_002916b8",
    0x00291950: "func_00291950",
    0x002915E4: "func_002915e4",
    0x002915B4: "func_002915b4",
    0x002918C4: "ui_func_002918c4",
    0x002914D8: "ui_func_002914d8",
    0x00291430: "func_00291430",
    0x00291304: "func_00291304",
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
    alloc_idx = [0]

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

        if name == "func_002916b8":
            calls.append((name, r0))
        elif name == "func_00291950":
            calls.append((name, r0))
        elif name == "func_002915e4":
            s0 = struct.unpack("<I", uc_inst.mem_read(sp, 4))[0]
            calls.append((name, r0 - SELF_BASE, r1 - SELF_BASE, r2 - SELF_BASE, r3 - SELF_BASE, s0 - SELF_BASE))
        elif name == "func_002915b4":
            s = struct.unpack("<6I", uc_inst.mem_read(sp, 24))
            calls.append((name, r0, r1 - SELF_BASE, r2 - SELF_BASE, r3, s[0], s[1] - SELF_BASE, s[2], s[3], s[4], s[5]))
            node = NODE_BASE + alloc_idx[0] * 0x400
            alloc_idx[0] += 1
            node_buf = bytearray(0x400)
            struct.pack_into("<ff", node_buf, 0x120, 1.0, 2.0)
            struct.pack_into("<f", node_buf, 0x1F4, 2.0)
            uc_inst.mem_write(node, bytes(node_buf))
            uc_inst.reg_write(UC_ARM_REG_R0, node)
        elif name == "ui_func_002918c4":
            calls.append((name, r0, r1, r2))
            uc_inst.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", 1.5))[0])
        elif name == "ui_func_002914d8":
            calls.append((name, r0, r1, r2, r3))
            uc_inst.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", 0.5))[0])
        elif name == "func_00291430":
            calls.append((name, r0, r1, r2))
            uc_inst.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", 3.25))[0])
        elif name == "func_00291304":
            s = struct.unpack("<4I", uc_inst.mem_read(sp, 16))
            calls.append((name, r0 - SELF_BASE, r1 - SELF_BASE, r2 - SELF_BASE, r3 - SELF_BASE, s[0] - SELF_BASE, s[1] - SELF_BASE, s[2] - SELF_BASE, s[3] - SELF_BASE))

    if is_orig:
        for addr in ORIG_CALLEES:
            uc.hook_add(1 << 2, hook_code, begin=addr, end=addr)
    else:
        for addr in stub_map.values():
            uc.hook_add(1 << 2, hook_code, begin=addr, end=addr)

    self_buf = bytearray(0x400)
    struct.pack_into("<f", self_buf, 0x00, cfg["f00"])
    struct.pack_into("<II", self_buf, 0x24, cfg["v24"], cfg["v34"])
    struct.pack_into("<III", self_buf, 0x16C, 50, 0x111, 0x222)
    struct.pack_into("<fII", self_buf, 0x17C, cfg["f17c"], 0x333, cfg["v184"])
    struct.pack_into("<i", self_buf, 0x188, -7)
    struct.pack_into("<IIII", self_buf, 0x21C, 0xAAA, 0xBBB, 0xCCC, FLAG228_ADDR)
    self_buf[0x22C] = 9
    struct.pack_into("<ii", self_buf, 0x230, cfg["cur_idx"], cfg["last_idx"])
    for idx, val in cfg["slots"].items():
        struct.pack_into("<I", self_buf, 0x238 + idx * 4, val)
    struct.pack_into("<h", self_buf, 0x300, cfg["v300"])

    uc.mem_write(FLAG228_ADDR, struct.pack("<I", 0x9999))
    uc.mem_write(SELF_BASE, bytes(self_buf))

    uc.reg_write(UC_ARM_REG_R0, SELF_BASE)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL_LR)

    entry = ORIG_BASE if is_orig else CAND_BASE
    uc.emu_start(entry, SENTINEL_LR, count=20000)

    return {
        "self": bytes(uc.mem_read(SELF_BASE, 0x320)),
        "flag228": bytes(uc.mem_read(FLAG228_ADDR, 4)),
        "nodes": [bytes(uc.mem_read(NODE_BASE + i * 0x400, 0x360)) for i in range(alloc_idx[0])],
        "calls": calls,
    }


def make_cases():
    return [
        {  # v24 == v184, v300 <= 0
            "f00": 2.0, "v24": 5, "v184": 5, "v34": 0, "f17c": 1.5,
            "cur_idx": 0, "last_idx": 0, "slots": {1: 0x1111}, "v300": 1,
        },
        {  # v24 == v184, v300 > 0
            "f00": 2.0, "v24": 5, "v184": 5, "v34": 0, "f17c": 1.5,
            "cur_idx": 0, "last_idx": 0, "slots": {}, "v300": 3,
        },
        {  # v24 != v184, spawn 2 nodes, cur_idx advances past empty slot
            "f00": 2.0, "v24": 1, "v184": 5, "v34": 0, "f17c": 2.5,
            "cur_idx": 0, "last_idx": 49, "slots": {0: 0, 1: 0, 2: 0x5555}, "v300": 2,
        },
        {  # v24 != v184, cur_idx < 0, spawn 1 node
            "f00": 3.0, "v24": 1, "v184": 5, "v34": 2, "f17c": 1.0,
            "cur_idx": -1, "last_idx": 48, "slots": {}, "v300": 2,
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
        if o["self"] != c["self"] or o["flag228"] != c["flag228"] or o["nodes"] != c["nodes"] or o["calls"] != c["calls"]:
            raise AssertionError(f"case {idx} mismatch:\norig calls={o['calls']}\ncand calls={c['calls']}")

    mutants = [
        ("flip_v300_dec", 0x0019305C, b"\x02\x00\x40\xe2"),
        ("skip_flag228_clr", 0x001930B0, b"\x00\x00\xa0\x11"),
        ("corrupt_v24_inc", 0x00193310, b"\x02\x00\x80\xe2"),
        ("corrupt_34c_off", 0x00193290, b"\xd4\x00\x85\xed"),
        ("skip_loop_step", 0x001932D0, b"\x02\x00\x80\xe2"),
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
                if o["self"] != m["self"] or o["flag228"] != m["flag228"] or o["nodes"] != m["nodes"] or o["calls"] != m["calls"]:
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
