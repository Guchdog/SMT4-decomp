#!/usr/bin/env python3
"""Differential test for func_002c45c0 (0x002c45c0, 288 B) using Unicorn."""

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
    UC_ARM_REG_SP,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = REPO_ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = REPO_ROOT / "src" / "engine" / "leaf_batch46_a.cpp"
BUILD_DIR = REPO_ROOT / "build" / "test_leaf_002c45c0"
OBJ_PATH = BUILD_DIR / "leaf_batch46_a.o"

ORIG_BASE = 0x002C45C0
ORIG_SIZE = 288
CAND_BASE = 0x00800000
RODATA_BASE = 0x00900000
STUB_BASE = 0x00A00000

SLOT_4E3CF4 = 0x004E3CF4
BUCKETS_ADDR = 0x20000000
NODE0_ADDR = 0x20001000
NODE1_ADDR = 0x20002000
CHILD0_ADDR = 0x20003000
CHILD1_ADDR = 0x20004000
STACK_TOP = 0x30010000
SENTINEL_LR = 0x7FFFF000

TARGET_FN = "func_002c45c0"
ORIG_CALLEES = {
    0x002C43F4: "func_002c43f4",
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
        if name == "func_002c43f4":
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            v36 = struct.unpack("<h", uc_inst.mem_read(r0 + 0x36, 2))[0]
            calls.append((name, r0, v36))

    if is_orig:
        for addr in ORIG_CALLEES:
            uc.hook_add(1 << 2, hook_code, begin=addr, end=addr)
    else:
        for addr in stub_map.values():
            uc.hook_add(1 << 2, hook_code, begin=addr, end=addr)

    uc.mem_write(SLOT_4E3CF4, struct.pack("<I", BUCKETS_ADDR))
    buckets = bytearray(0x40)
    struct.pack_into("<I", buckets, 2 * 8, NODE0_ADDR)
    uc.mem_write(BUCKETS_ADDR, bytes(buckets))

    n0 = bytearray(0xA0)
    struct.pack_into("<I", n0, 0x24, 0x111)
    struct.pack_into("<I", n0, 0x4C, NODE1_ADDR)
    uc.mem_write(NODE0_ADDR, bytes(n0))

    n1 = bytearray(0xA0)
    struct.pack_into("<I", n1, 0x24, 0x222)
    struct.pack_into("<I", n1, 0x58, CHILD0_ADDR if cfg["has_children"] else 0)
    n1[0x98] = cfg["st"]
    uc.mem_write(NODE1_ADDR, bytes(n1))

    c0 = bytearray(0x70)
    struct.pack_into("<I", c0, 0x5C, CHILD1_ADDR)
    uc.mem_write(CHILD0_ADDR, bytes(c0))
    c1 = bytearray(0x70)
    uc.mem_write(CHILD1_ADDR, bytes(c1))

    uc.reg_write(UC_ARM_REG_R0, (2 << 20) | 0x222)
    uc.reg_write(UC_ARM_REG_R1, cfg["val"] & 0xFFFFFFFF)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL_LR)

    entry = ORIG_BASE if is_orig else CAND_BASE
    uc.emu_start(entry, SENTINEL_LR, count=20000)

    return {
        "ret": uc.reg_read(UC_ARM_REG_R0),
        "n1_36": struct.unpack("<h", uc.mem_read(NODE1_ADDR + 0x36, 2))[0],
        "n1_98": uc.mem_read(NODE1_ADDR + 0x98, 1)[0],
        "c0_36": struct.unpack("<h", uc.mem_read(CHILD0_ADDR + 0x36, 2))[0],
        "c1_36": struct.unpack("<h", uc.mem_read(CHILD1_ADDR + 0x36, 2))[0],
        "calls": calls,
    }


def make_cases():
    return [
        {"st": 0, "has_children": True, "val": -5},
        {"st": 1, "has_children": True, "val": 123},
        {"st": 2, "has_children": False, "val": -100},
        {"st": 3, "has_children": True, "val": 42},
        {"st": 4, "has_children": True, "val": 77},
        {"st": 5, "has_children": False, "val": 88},
        {"st": 6, "has_children": True, "val": 99},
    ]


def main():
    orig_all = CODE_BIN.read_bytes()
    orig_bytes = orig_all[ORIG_BASE - 0x00100000 : ORIG_BASE - 0x00100000 + ORIG_SIZE]
    cand_bytes, cand_relocs, ro_blob, abs_relocs = compile_candidate()

    cases = make_cases()
    for idx, cfg in enumerate(cases):
        o = run_instance(orig_bytes, True, [], b"", [], cfg)
        c = run_instance(cand_bytes, False, cand_relocs, ro_blob, abs_relocs, cfg)
        if o != c:
            raise AssertionError(f"case {idx} mismatch:\norig={o}\ncand={c}")

    mutants = [
        ("corrupt_ret0", 0x002C46D4, b"\x01\x00\xa0\xe3"),
        ("corrupt_ret1", 0x002C46CC, b"\x00\x00\xa0\xe3"),
        ("skip_set_st4", 0x002C46C8, b"\x00\x00\xa0\xe1"),
        ("corrupt_child_36", 0x002C4648, b"\xb8\x13\xc0\xe1"),
        ("skip_next_node", 0x002C45F8, b"\x00\x00\xa0\xe1"),
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
                if o != m:
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
