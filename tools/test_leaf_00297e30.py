#!/usr/bin/env python3
"""Differential test for camp_func_00297e30 (0x00297e30, 272 B) using Unicorn."""

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
    UC_ARM_REG_SP,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = REPO_ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = REPO_ROOT / "src" / "engine" / "leaf_batch46_a.cpp"
BUILD_DIR = REPO_ROOT / "build" / "test_leaf_00297e30"
OBJ_PATH = BUILD_DIR / "leaf_batch46_a.o"

ORIG_BASE = 0x00297E30
ORIG_SIZE = 272
CAND_BASE = 0x00800000
RODATA_BASE = 0x00900000
STUB_BASE = 0x00A00000

SELF_BASE = 0x20000000
FMT_ADDR = 0x20010000
STACK_TOP = 0x30010000
SENTINEL_LR = 0x7FFFF000

TARGET_FN = "camp_func_00297e30"
ORIG_CALLEES = {
    0x002E384C: "camp_func_002e384c",
    0x0029F10C: "camp_func_0029f10c",
    0x002BE7FC: "ui_func_002be7fc",
    0x00254228: "camp_func_00254228",
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
    return raw.split(b"\x00", 1)[0].decode("ascii", errors="replace")


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

        if name == "camp_func_002e384c":
            calls.append((name, r0, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, FMT_ADDR)
        elif name == "ui_func_002be7fc":
            fmt = read_cstr(uc_inst, r1)
            out = fmt.replace("%d", str(r2))
            uc_inst.mem_write(r0, out.encode("ascii") + b"\x00")
            calls.append((name, fmt, r2))
        elif name == "camp_func_0029f10c":
            calls.append((name, read_cstr(uc_inst, r0), r1))
        elif name == "camp_func_00254228":
            calls.append((name, r0, r1, r2, r3))

    if is_orig:
        for addr in ORIG_CALLEES:
            uc.hook_add(1 << 2, hook_code, begin=addr, end=addr)
    else:
        for addr in stub_map.values():
            uc.hook_add(1 << 2, hook_code, begin=addr, end=addr)

    uc.mem_write(FMT_ADDR, b"MSG_%d\x00")
    uc.mem_write(SELF_BASE + 0x306C, struct.pack("<i", cfg["val"]))

    uc.reg_write(UC_ARM_REG_R0, SELF_BASE)
    uc.reg_write(UC_ARM_REG_R1, cfg["kind"])
    uc.reg_write(UC_ARM_REG_R2, cfg["flag"])
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL_LR)

    entry = ORIG_BASE if is_orig else CAND_BASE
    uc.emu_start(entry, SENTINEL_LR, count=20000)

    return {"calls": calls}


def make_cases():
    cases = [{"kind": k, "flag": k & 1, "val": 0} for k in range(13)]
    cases.append({"kind": 9, "flag": 0, "val": 9})
    cases.append({"kind": 9, "flag": 1, "val": 10})
    cases.append({"kind": 9, "flag": 0, "val": 99})
    cases.append({"kind": 9, "flag": 0, "val": 100})
    return cases


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
        ("corrupt_flag_cmp", 0x00297EB8, b"\x01\x00\x52\xe3"),
        ("flip_kind9_branch", 0x00297ED0, b"\x00\x00\x00\xea"),
        ("corrupt_val_100", 0x00297F08, b"\x63\x00\x50\xe3"),
        ("corrupt_val_10", 0x00297F14, b"\x09\x00\x50\xe3"),
        ("corrupt_254228_r2", 0x00297F24, b"\x13\x20\xa0\xe3"),
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
