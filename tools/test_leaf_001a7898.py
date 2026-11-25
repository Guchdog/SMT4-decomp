#!/usr/bin/env python3
"""Differential test for ui_func_001a7898 (0x001a7898, 928 B) using Unicorn."""

from __future__ import annotations

import math
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
    UC_ARM_REG_SP,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = REPO_ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = REPO_ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
BUILD_DIR = REPO_ROOT / "build" / "test_leaf_001a7898"
OBJ_PATH = BUILD_DIR / "leaf_batch45_b.o"

ORIG_BASE = 0x001A7898
ORIG_SIZE = 928
CAND_BASE = 0x00800000
RODATA_BASE = 0x00900000
STUB_BASE = 0x00A00000

SELF_BASE = 0x20000000
CAM_BASE = 0x20010000
TBL_BASE = 0x00407FC0
STACK_TOP = 0x30010000
SENTINEL_LR = 0x7FFFF000

TARGET_FN = "ui_func_001a7898"
ORIG_CALLEES = {
    0x002C5218: "ui_func_002c5218",
    0x002885D4: "ui_func_002885d4",
    0x00288424: "engine_func_00288424",
    0x001D1B74: "func_001d1b74",
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
    tan_off = None
    for i in range(symtab[5] // 16):
        st_name, st_value, st_size, st_info, _, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + i * 16)
        if st_shndx == tidx:
            name = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
            if name == TARGET_FN:
                fn_off, fn_size = st_value, st_size
            elif name == "engine_func_00288424":
                tan_off = st_value
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

    return bytes(text_data[fn_off : fn_off + fn_size]), relocs, bytes(ro_blob), abs_relocs, tan_off, fn_off


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


def patch_candidate_relocs(uc, cand_bytes, relocs, abs_relocs, stub_map, tan_off, fn_off):
    buf = bytearray(cand_bytes)
    for sym_name, rel_off in relocs:
        if sym_name not in stub_map:
            raise RuntimeError(f"missing stub for {sym_name}")
        pc = CAND_BASE + rel_off + 8
        diff = (stub_map[sym_name] - pc) >> 2
        insn = struct.unpack_from("<I", buf, rel_off)[0]
        insn = (insn & 0xFF000000) | (diff & 0x00FFFFFF)
        struct.pack_into("<I", buf, rel_off, insn)
    # Also redirect direct PC-relative bl to engine_func_00288424 if not in relocs
    if tan_off is not None:
        for off in range(0, len(buf), 4):
            insn = struct.unpack_from("<I", buf, off)[0]
            if (insn & 0x0F000000) == 0x0B000000:
                imm24 = insn & 0x00FFFFFF
                if imm24 & 0x00800000:
                    imm24 -= 0x01000000
                target_in_text = fn_off + off + 8 + (imm24 << 2)
                if target_in_text == tan_off:
                    pc = CAND_BASE + off + 8
                    diff = (stub_map["engine_func_00288424"] - pc) >> 2
                    struct.pack_into("<I", buf, off, (insn & 0xFF000000) | (diff & 0x00FFFFFF))
    for rel_off, ro_off in abs_relocs:
        struct.pack_into("<I", buf, rel_off, RODATA_BASE + ro_off)
    uc.mem_write(CAND_BASE, bytes(buf))


def run_instance(code_bytes, is_orig, cand_relocs, ro_blob, abs_relocs, tan_off, fn_off, cfg):
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
        patch_candidate_relocs(uc, code_bytes, cand_relocs, abs_relocs, stub_map, tan_off, fn_off)

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

        if name == "ui_func_002c5218":
            calls.append((name,))
            uc_inst.reg_write(UC_ARM_REG_R0, CAM_BASE)
        elif name == "ui_func_002885d4":
            s0_u = uc_inst.reg_read(UC_ARM_REG_S0)
            s0_f = struct.unpack("<f", struct.pack("<I", s0_u))[0]
            s0_f = max(-1.0, min(1.0, s0_f))
            res = math.acos(s0_f)
            calls.append((name, round(s0_f, 5)))
            uc_inst.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", res))[0])
        elif name == "engine_func_00288424":
            s0_u = uc_inst.reg_read(UC_ARM_REG_S0)
            s0_f = struct.unpack("<f", struct.pack("<I", s0_u))[0]
            res = math.tan(s0_f)
            calls.append((name, round(s0_f, 5)))
            uc_inst.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", res))[0])
        elif name == "func_001d1b74":
            calls.append((name,))
            uc_inst.reg_write(UC_ARM_REG_R0, cfg["ret_1d1b74"])

    if is_orig:
        for addr in ORIG_CALLEES:
            uc.hook_add(1 << 2, hook_code, begin=addr, end=addr)
    else:
        for addr in stub_map.values():
            uc.hook_add(1 << 2, hook_code, begin=addr, end=addr)

    # Set up tables at 0x00407FC0 and 0x004083C0
    uc.mem_write(TBL_BASE, struct.pack("<ffff", 0.8, 0.6, 0.1, 0.2))
    uc.mem_write(TBL_BASE + 0x400, struct.pack("<ffff", 0.9, 0.4358899, 0.1, 0.2))

    cam_buf = bytearray(0x40)
    struct.pack_into("<fff", cam_buf, 0x04, cfg["eye_x"], 0.0, cfg["eye_z"])
    struct.pack_into("<fff", cam_buf, 0x10, cfg["tgt_x"], cfg["tgt_y"], cfg["tgt_z"])
    struct.pack_into("<f", cam_buf, 0x28, 60.0)
    uc.mem_write(CAM_BASE, bytes(cam_buf))

    self_buf = bytearray(0x40)
    self_buf[0x17] = cfg["flag17"]
    struct.pack_into("<fff", self_buf, 0x18, cfg["sx"], 0.0, cfg["sz"])
    struct.pack_into("<ff", self_buf, 0x2C, 100.0, 20.0)
    uc.mem_write(SELF_BASE, bytes(self_buf))

    uc.reg_write(UC_ARM_REG_R0, SELF_BASE)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL_LR)

    entry = ORIG_BASE if is_orig else CAND_BASE
    uc.emu_start(entry, SENTINEL_LR, count=20000)

    out_self = struct.unpack("<6f", uc.mem_read(SELF_BASE + 0x18, 24))
    return {"out": out_self, "calls": calls}


def make_cases():
    return [
        # flag17=1, general angle
        {"flag17": 1, "eye_x": 10.0, "eye_z": 20.0, "tgt_x": 30.0, "tgt_y": 200.0, "tgt_z": 50.0, "sx": 40.0, "sz": 70.0, "ret_1d1b74": 0},
        # flag17=1, exact dot == +1.0 (dz < 0, dx == 0)
        {"flag17": 1, "eye_x": 10.0, "eye_z": 50.0, "tgt_x": 10.0, "tgt_y": 200.0, "tgt_z": 20.0, "sx": 10.0, "sz": 10.0, "ret_1d1b74": 0},
        # flag17=1, exact dot == -1.0 (dz > 0, dx == 0)
        {"flag17": 1, "eye_x": 10.0, "eye_z": 20.0, "tgt_x": 10.0, "tgt_y": 200.0, "tgt_z": 50.0, "sx": 10.0, "sz": 80.0, "ret_1d1b74": 0},
        # flag17=0, ret_1d1b74=0
        {"flag17": 0, "eye_x": 10.0, "eye_z": 20.0, "tgt_x": 30.0, "tgt_y": 250.0, "tgt_z": 50.0, "sx": 0.0, "sz": 0.0, "ret_1d1b74": 0},
        # flag17=0, ret_1d1b74=1, dot == +1.0
        {"flag17": 0, "eye_x": 10.0, "eye_z": 50.0, "tgt_x": 10.0, "tgt_y": 250.0, "tgt_z": 20.0, "sx": 0.0, "sz": 0.0, "ret_1d1b74": 1},
    ]


def main():
    orig_all = CODE_BIN.read_bytes()
    orig_bytes = orig_all[ORIG_BASE - 0x00100000 : ORIG_BASE - 0x00100000 + ORIG_SIZE]
    cand_bytes, cand_relocs, ro_blob, abs_relocs, tan_off, fn_off = compile_candidate()

    cases = make_cases()
    for idx, cfg in enumerate(cases):
        o = run_instance(orig_bytes, True, [], b"", [], None, None, cfg)
        c = run_instance(cand_bytes, False, cand_relocs, ro_blob, abs_relocs, tan_off, fn_off, cfg)
        for a, b in zip(o["out"], c["out"]):
            if abs(a - b) > 1e-4:
                raise AssertionError(f"case {idx} float mismatch:\norig={o['out']}\ncand={c['out']}")
        if o["calls"] != c["calls"]:
            raise AssertionError(f"case {idx} calls mismatch:\norig={o['calls']}\ncand={c['calls']}")

    mutants = [
        ("flip_flag17", 0x001A78C8, b"\x01\x00\x50\xe3"),
        ("corrupt_dot_1", 0x001A791C, b"\x0a\x0a\x84\x0d"),
        ("skip_negate", 0x001A795C, b"\x00\x00\xa0\xe1"),
        ("corrupt_24_off", 0x001A79F8, b"\x0a\x0a\x84\xed"),
        ("skip_scale_01", 0x001A7A10, b"\x00\x00\xa0\xe1"),
    ]
    detected = 0
    for name, m_addr, repl in mutants:
        m_off = m_addr - ORIG_BASE
        mut_bytes = bytearray(orig_bytes)
        mut_bytes[m_off : m_off + 4] = repl
        caught = False
        for cfg in cases:
            try:
                o = run_instance(orig_bytes, True, [], b"", [], None, None, cfg)
                m = run_instance(bytes(mut_bytes), True, [], b"", [], None, None, cfg)
                if o["out"] != m["out"] or o["calls"] != m["calls"]:
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
