#!/usr/bin/env python3
"""Differential test for script_vm_func_0038ff58 (0x0038ff58, 760 B) using Unicorn."""

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
    UC_ARM_REG_SP,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = REPO_ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = REPO_ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
BUILD_DIR = REPO_ROOT / "build" / "test_leaf_0038ff58"
OBJ_PATH = BUILD_DIR / "leaf_batch45_b.o"

ORIG_BASE = 0x0038FF58
ORIG_SIZE = 760
CAND_BASE = 0x00800000
RODATA_BASE = 0x00900000
STUB_BASE = 0x00A00000

GLOBAL_SLOT = 0x00432FC8
GLOBAL_OBJ = 0x20020000
TBL_ADDR = 0x20030000
SELF_BASE = 0x20000000
OBJ208_ADDR = 0x20010000
VTBL_ADDR = 0x20011000
VTBL_FN4 = 0x00B00000
VTBL_FN12 = 0x00B00010
STACK_TOP = 0x30010000
SENTINEL_LR = 0x7FFFF000

TARGET_FN = "script_vm_func_0038ff58"
ORIG_CALLEES = {
    0x00234278: "engine_func_00234278",
    0x0019DFBC: "script_vm_func_0019dfbc",
    0x0027EC84: "camp_func_0027ec84",
    0x00233F0C: "battle_func_00233f0c",
    0x00297128: "shop_func_00297128",
    0x00234004: "engine_func_00234004",
    0x00233F4C: "engine_func_00233f4c",
    0x00291018: "script_vm_func_00291018",
    0x002971E4: "script_vm_func_002971e4",
    0x00233AC0: "camp_func_00233ac0",
    0x0026B7CC: "ui_func_0026b7cc",
    0x00234160: "engine_func_00234160",
    0x002337A0: "shop_func_002337a0",
    0x002A17C0: "engine_func_002a17c0",
    0x002A0F88: "script_vm_func_002a0f88",
    0x002B8584: "engine_func_002b8584",
    0x0026F0D8: "ui_func_0026f0d8",
    0x002BC200: "camp_func_002bc200",
    0x0029111C: "shop_func_0029111c",
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
    uc.mem_map(VTBL_FN4, 0x00100000)
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


def read_cstr(uc, addr):
    if addr == 0:
        return None
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
        uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(VTBL_FN4, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(VTBL_FN12, struct.pack("<I", 0xE12FFF1E))

    calls = []

    def hook_code(uc_inst, address, size, user_data):
        if address == VTBL_FN4:
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            calls.append(("vtbl_dtor", r0))
            return
        if address == VTBL_FN12:
            sret = uc_inst.reg_read(UC_ARM_REG_R0)
            obj = uc_inst.reg_read(UC_ARM_REG_R1)
            calls.append(("vtbl_get", obj))
            uc_inst.mem_write(sret, struct.pack("<5I", 0xA1, 0xA2, 0xA3, 0xA4, 0xA5))
            return

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

        if name == "engine_func_00234278":
            uc_inst.mem_write(r0, struct.pack("<5I", 1, 2, 3, 4, 5))
            calls.append((name,))
        elif name == "script_vm_func_0019dfbc":
            calls.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, 0)
        elif name == "camp_func_0027ec84":
            w = struct.unpack("<5I", uc_inst.mem_read(r0, 20))
            calls.append((name, w))
            uc_inst.reg_write(UC_ARM_REG_R0, cfg["ret_27ec84"])
        elif name == "engine_func_002a17c0":
            w = struct.unpack("<5I", uc_inst.mem_read(r0, 20))
            calls.append((name, w))
            uc_inst.reg_write(UC_ARM_REG_R0, cfg["ret_2a17c0"])
        elif name == "script_vm_func_00291018":
            s = read_cstr(uc_inst, r1)
            calls.append((name, r0, s))
            uc_inst.reg_write(UC_ARM_REG_R0, 77)
        elif name == "script_vm_func_002971e4":
            calls.append((name, r0, r1))
        elif name == "camp_func_00233ac0":
            calls.append((name, r0, r1, r2))
        elif name == "engine_func_00233f4c":
            calls.append((name, r0, r1))
        elif name == "engine_func_00234004":
            calls.append((name, r0, r1, r2))
        elif name == "ui_func_0026b7cc":
            calls.append((name,))
            uc_inst.reg_write(UC_ARM_REG_R0, cfg["ret_26b7cc"])
        elif name == "engine_func_00234160":
            calls.append((name, r0 - SELF_BASE, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, OBJ208_ADDR)
        elif name == "shop_func_002337a0":
            calls.append((name, r0 - SELF_BASE))
            uc_inst.reg_write(UC_ARM_REG_R0, 2)
        elif name == "script_vm_func_002a0f88":
            calls.append((name,))
            uc_inst.reg_write(UC_ARM_REG_R0, cfg["ret_2a0f88"])
        elif name == "ui_func_0026f0d8":
            calls.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, cfg["ret_26f0d8"])
        elif name == "shop_func_0029111c":
            calls.append((name,))
            uc_inst.reg_write(UC_ARM_REG_R0, cfg["ret_29111c"])
        elif name in ("battle_func_00233f0c", "engine_func_002b8584", "camp_func_002bc200"):
            calls.append((name, r0))
        elif name == "shop_func_00297128":
            calls.append((name,))

    if is_orig:
        for addr in ORIG_CALLEES:
            uc.hook_add(1 << 2, hook_code, begin=addr, end=addr)
    else:
        for addr in stub_map.values():
            uc.hook_add(1 << 2, hook_code, begin=addr, end=addr)
    uc.hook_add(1 << 2, hook_code, begin=VTBL_FN4, end=VTBL_FN4)
    uc.hook_add(1 << 2, hook_code, begin=VTBL_FN12, end=VTBL_FN12)

    uc.mem_write(GLOBAL_SLOT, struct.pack("<I", GLOBAL_OBJ))
    uc.mem_write(GLOBAL_OBJ + 0x678, struct.pack("<I", TBL_ADDR))
    uc.mem_write(TBL_ADDR + 0x9AA + 2 * 0x139 * 8, struct.pack("<H", 0xBEEF))

    uc.mem_write(VTBL_ADDR + 4, struct.pack("<I", VTBL_FN4))
    uc.mem_write(VTBL_ADDR + 12, struct.pack("<I", VTBL_FN12))
    uc.mem_write(OBJ208_ADDR, struct.pack("<I", VTBL_ADDR))

    self_buf = bytearray(0x400)
    struct.pack_into("<I", self_buf, 0x00, cfg["flags"])
    struct.pack_into("<I", self_buf, 0x08, cfg["state"])
    struct.pack_into("<I", self_buf, 0x208, cfg["obj208"])
    struct.pack_into("<I", self_buf, 0x350, 0x12345678)
    struct.pack_into("<I", self_buf, 0x358, 0x87654321)
    uc.mem_write(SELF_BASE, bytes(self_buf))

    uc.reg_write(UC_ARM_REG_R0, SELF_BASE)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL_LR)

    entry = ORIG_BASE if is_orig else CAND_BASE
    uc.emu_start(entry, SENTINEL_LR, count=20000)

    return {
        "self": bytes(uc.mem_read(SELF_BASE, 0x230)),
        "obj208": bytes(uc.mem_read(OBJ208_ADDR, 0x20)),
        "calls": calls,
    }


def make_cases():
    base = {
        "flags": 0x200,
        "state": 0,
        "obj208": OBJ208_ADDR,
        "ret_27ec84": 1,
        "ret_2a17c0": 1,
        "ret_26b7cc": 1,
        "ret_2a0f88": 1,
        "ret_26f0d8": 1,
        "ret_29111c": 1,
    }
    cases = [dict(base)]  # state 0

    c1 = dict(base)
    c1["state"] = 1
    cases.append(c1)

    c2 = dict(base)
    c2["state"] = 2
    cases.append(c2)

    c2b = dict(base)
    c2b["state"] = 2
    c2b["ret_27ec84"] = 0
    cases.append(c2b)

    c3 = dict(base)
    c3["state"] = 3
    cases.append(c3)

    c4 = dict(base)
    c4["state"] = 4
    cases.append(c4)

    c5 = dict(base)
    c5["state"] = 5
    cases.append(c5)

    c9999 = dict(base)
    c9999["state"] = 9999
    cases.append(c9999)
    return cases


def main():
    orig_all = CODE_BIN.read_bytes()
    orig_bytes = orig_all[ORIG_BASE - 0x00100000 : ORIG_BASE - 0x00100000 + ORIG_SIZE]
    cand_bytes, cand_relocs, ro_blob, abs_relocs = compile_candidate()

    cases = make_cases()
    for idx, cfg in enumerate(cases):
        o = run_instance(orig_bytes, True, [], b"", [], cfg)
        c = run_instance(cand_bytes, False, cand_relocs, ro_blob, abs_relocs, cfg)
        if o["self"] != c["self"] or o["obj208"] != c["obj208"] or o["calls"] != c["calls"]:
            raise AssertionError(f"case {idx} (state={cfg['state']}) mismatch:\norig calls={o['calls']}\ncand calls={c['calls']}")

    mutants = [
        ("flip_state0_orr", 0x0039002C, b"\x02\x08\x80\xe3"),
        ("flip_state1_tst", 0x00390090, b"\x01\x0b\x10\xe3"),
        ("corrupt_state2_out", 0x0038FFE0, b"\x04\x00\xa0\xe3"),
        ("corrupt_state3_next", 0x00390178, b"\x05\x00\xa0\xe3"),
        ("skip_state5_clear", 0x00390214, b"\x00\x00\xa0\xe1"),
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
                if o["self"] != m["self"] or o["obj208"] != m["obj208"] or o["calls"] != m["calls"]:
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
