#!/usr/bin/env python3
"""Differential test for script_vm_func_00264368 (0x00264368, 776 B) using Unicorn."""

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
    UC_ARM_REG_S0,
    UC_ARM_REG_S1,
    UC_ARM_REG_SP,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = REPO_ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = REPO_ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
BUILD_DIR = REPO_ROOT / "build" / "test_leaf_00264368"
OBJ_PATH = BUILD_DIR / "leaf_batch45_b.o"

ORIG_BASE = 0x00264368
ORIG_SIZE = 776
CAND_BASE = 0x00800000
RODATA_BASE = 0x00900000
STUB_BASE = 0x00A00000

SLOT_4474F4 = 0x004474F4
SLOT_447060 = 0x00447060
GLOB_49F91C = 0x0049F91C
OBJ_4474F4 = 0x20000000
OBJ_447060 = 0x20010000
STACK_TOP = 0x30010000
SENTINEL_LR = 0x7FFFF000

TARGET_FN = "script_vm_func_00264368"
ORIG_CALLEES = {
    0x002C17D4: "ui_func_002c17d4",
    0x00276550: "script_vm_func_00276550",
    0x002BFFBC: "ui_func_002bffbc",
    0x00287D74: "script_vm_func_00287d74",
    0x0027F150: "script_vm_func_0027f150",
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

        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        if name == "ui_func_002c17d4":
            calls.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, cfg["mask8"] if r0 == 8 else cfg["mask7"])
        elif name == "ui_func_002bffbc":
            calls.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, cfg["cnt8"] if r0 == 8 else cfg["cnt7"])
        elif name == "script_vm_func_00276550":
            calls.append((name,))
            uc_inst.reg_write(UC_ARM_REG_R0, cfg["ret_276550"])
        elif name == "script_vm_func_00287d74":
            f0, f1 = struct.unpack("<ff", uc_inst.mem_read(r0, 8))
            calls.append((name, f0, f1))
            uc_inst.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", cfg["ret_287d74"]))[0])
        elif name == "script_vm_func_0027f150":
            s0 = uc_inst.reg_read(UC_ARM_REG_S0)
            s1 = uc_inst.reg_read(UC_ARM_REG_S1)
            calls.append((name, s0, s1))
            uc_inst.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", cfg["ret_27f150"]))[0])

    if is_orig:
        for addr in ORIG_CALLEES:
            uc.hook_add(1 << 2, hook_code, begin=addr, end=addr)
    else:
        for addr in stub_map.values():
            uc.hook_add(1 << 2, hook_code, begin=addr, end=addr)

    uc.mem_write(SLOT_4474F4, struct.pack("<I", OBJ_4474F4))
    uc.mem_write(SLOT_447060, struct.pack("<I", OBJ_447060))

    g49 = bytearray(0x40)
    g49[0x18] = cfg["g49_18"]
    struct.pack_into("<I", g49, 0x1C, cfg["g49_1c"])
    uc.mem_write(GLOB_49F91C, bytes(g49))

    o7060 = bytearray(0x100)
    struct.pack_into("<f", o7060, 0x50, cfg["angle"])
    o7060[0x94] = cfg["reset"]
    uc.mem_write(OBJ_447060, bytes(o7060))

    o74f4 = bytearray(0x240)
    o74f4[0xB0] = cfg["b0"]
    o74f4[0xB1] = cfg["b1"]
    struct.pack_into("<hh", o74f4, 0xB2, cfg["b2"], cfg["b4"])
    struct.pack_into("<fff", o74f4, 0xB8, 0.0, cfg["bc"], cfg["c0"])
    uc.mem_write(OBJ_4474F4, bytes(o74f4))

    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL_LR)

    entry = ORIG_BASE if is_orig else CAND_BASE
    uc.emu_start(entry, SENTINEL_LR, count=20000)

    return {
        "o74f4": bytes(uc.mem_read(OBJ_4474F4, 0x220)),
        "o7060": bytes(uc.mem_read(OBJ_447060, 0xA0)),
        "calls": calls,
    }


def make_cases():
    base = {
        "angle": 45.0,
        "reset": 0,
        "g49_18": 0,
        "g49_1c": 0,
        "b0": 0,
        "b1": 0,
        "b2": 0,
        "b4": 0,
        "bc": 180.0,
        "c0": 1.0,
        "mask8": 1,
        "mask7": 1,
        "cnt8": 0,
        "cnt7": 0,
        "ret_276550": 0,
        "ret_287d74": 0.5,
        "ret_27f150": 20.0,
    }
    cases = [dict(base)]  # triggers b0=1 via mask8&mask7&!cnt8&!cnt7&!b1

    c2 = dict(base)
    c2["reset"] = 1
    c2["angle"] = -1.0  # wrap +360
    c2["ret_287d74"] = -0.5  # < 0 -> c0 = -1.0
    cases.append(c2)

    c3 = dict(base)
    c3["b0"] = 1
    c3["ret_27f150"] = 10.0  # < 15.5 -> snap to bc
    cases.append(c3)

    c4 = dict(base)
    c4["b0"] = 1
    c4["c0"] = -1.0
    c4["angle"] = 350.0  # 350 + 15 = 365 -> wrap -360
    cases.append(c4)

    c5 = dict(base)
    c5["g49_18"] = 1
    c5["b1"] = 1
    c5["b2"] = 5
    cases.append(c5)

    c6 = dict(base)
    c6["b1"] = 1
    c6["mask8"] = 0
    c6["mask7"] = 0
    c6["ret_276550"] = 0
    cases.append(c6)
    return cases


def main():
    orig_all = CODE_BIN.read_bytes()
    orig_bytes = orig_all[ORIG_BASE - 0x00100000 : ORIG_BASE - 0x00100000 + ORIG_SIZE]
    cand_bytes, cand_relocs, ro_blob, abs_relocs = compile_candidate()

    cases = make_cases()
    for idx, cfg in enumerate(cases):
        o = run_instance(orig_bytes, True, [], b"", [], cfg)
        c = run_instance(cand_bytes, False, cand_relocs, ro_blob, abs_relocs, cfg)
        if o["o74f4"] != c["o74f4"] or o["o7060"] != c["o7060"] or o["calls"] != c["calls"]:
            raise AssertionError(f"case {idx} mismatch:\norig calls={o['calls']}\ncand calls={c['calls']}")

    mutants = [
        ("corrupt_reset_b2", 0x002643C0, b"\xb0\xa0\xc0\xe1"),
        ("flip_c0_branch", 0x00264548, b"\xc0\x00\x80\x2d"),
        ("corrupt_step15", 0x002645AC, b"\x00\x0a\x20\xce"),
        ("skip_wrap360_lo", 0x00264614, b"\x00\x0a\x30\x0e"),
        ("skip_out_store", 0x00264634, b"\x00\x00\xa0\xe1"),
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
                if o["o74f4"] != m["o74f4"] or o["o7060"] != m["o7060"] or o["calls"] != m["calls"]:
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
