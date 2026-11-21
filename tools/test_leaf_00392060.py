#!/usr/bin/env python3
"""Differential test for script_vm_func_00392060 (0x00392060) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_00392060"

FUNC_ADDR = 0x00392060
FUNC_SIZE = 656

G2FC8_PTR = 0x00432FC8
G3158_PTR = 0x00433158
G3130_PTR = 0x00433130

G2FC8_OBJ = 0x20000000
G3130_OBJ = 0x20001000
SELF_ADDR = 0x20006000
VOBJ_ADDR = 0x20007000
VTBL_ADDR = 0x20007100
VFUNC_ADDR = 0x00188000
RODATA_ADDR = 0x20008000

STUBS = {
    0x0026B7CC: "ui_func_0026b7cc",
    0x002B8584: "engine_func_002b8584",
    0x002A150C: "engine_func_002a150c",
    0x002339E8: "shop_func_002339e8",
    0x002339AC: "shop_func_002339ac",
    0x00291018: "script_vm_func_00291018",
    0x002971E4: "script_vm_func_002971e4",
    0x00233AC0: "camp_func_00233ac0",
    0x0019DFBC: "script_vm_func_0019dfbc",
    0x002F61A4: "func_002f61a4",
    0x002C1830: "camp_func_002c1830",
    0x002BC200: "camp_func_002bc200",
    0x00289984: "script_vm_func_00289984",
    0x0023554C: "script_vm_func_0023554c",
    0x002FEA30: "func_002fea30",
    0x002B9008: "camp_func_002b9008",
    0x00297674: "script_vm_func_00297674",
    0x00126EDC: "script_vm_func_00126edc",
    0x002BB09C: "engine_func_002bb09c",
    0x002BAD80: "engine_func_002bad80",
    0x00262BCC: "script_vm_func_00262bcc",
    VFUNC_ADDR: "vfunc1",
}

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


def compile_candidate() -> tuple[bytes, list[tuple[str, int]], bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_path = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj_path)
    if res.returncode != 0:
        raise RuntimeError(f"compile failed:\n{res.stderr}")

    data = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    shdrs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = shdrs[e_shstrndx][4]

    def sh_name(idx: int) -> str:
        off = shstr_off + shdrs[idx][0]
        return data[off : data.index(b"\x00", off)].decode("ascii", errors="replace")

    tidx = next(i for i in range(e_shnum) if sh_name(i) == ".text")
    text_data = bytearray(data[shdrs[tidx][4] : shdrs[tidx][4] + shdrs[tidx][5]])
    rodata_map: dict[int, int] = {}
    rodata_buf = bytearray()
    for i in range(e_shnum):
        if sh_name(i).startswith(".rodata"):
            while len(rodata_buf) % 4 != 0:
                rodata_buf.append(0)
            rodata_map[i] = RODATA_ADDR + len(rodata_buf)
            rodata_buf.extend(data[shdrs[i][4] : shdrs[i][4] + shdrs[i][5]])
    rodata = bytes(rodata_buf)
    symtab = next(s for s in shdrs if s[1] == 2)
    strtab_off = shdrs[symtab[6]][4]

    fn_off = fn_size = None
    for i in range(symtab[5] // 16):
        st_name, st_value, st_size, st_info, _, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + i * 16)
        if st_shndx == tidx:
            name = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
            if name == "script_vm_func_00392060":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("script_vm_func_00392060 not found in object")

    relocs: list[tuple[str, int]] = []
    for s in shdrs:
        if s[1] == 9 and s[7] == tidx:
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if fn_off <= r_off < fn_off + fn_size:
                    if r_type in (28, 29):
                        st_name = struct.unpack_from("<I", data, symtab[4] + sym_idx * 16)[0]
                        sname = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
                        relocs.append((sname, r_off - fn_off))
                    elif r_type == 2:
                        _, st_value, _, _, _, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + sym_idx * 16)
                        if st_shndx in rodata_map:
                            addend = struct.unpack_from("<I", text_data, r_off)[0]
                            struct.pack_into("<I", text_data, r_off, rodata_map[st_shndx] + st_value + addend)

    return bytes(text_data[fn_off : fn_off + fn_size]), relocs, rodata


def patch_bl(code: bytearray, at_off: int, src_pc: int, dst_pc: int) -> None:
    delta = (dst_pc - (src_pc + 8)) >> 2
    hi = code[at_off + 3]
    insn = (hi << 24) | (delta & 0x00FFFFFF)
    struct.pack_into("<I", code, at_off, insn)


def run_one(
    code_bytes: bytes,
    base_addr: int,
    relocs: list[tuple[str, int]] | None,
    rodata: bytes,
    state: int,
    vobj_ok: bool,
    ret_19dfbc: int,
    ret_2f61a4: int,
    ret_2c1830: int,
    ret_297674: int,
    ret_26b7cc: int,
) -> tuple[bytes, bytes, bytes, list[tuple], dict[str, int]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_map(0x20000000, 0x00010000)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_write(STACK_BASE, b"\x00" * STACK_SIZE)

    buf = bytearray(code_bytes)
    if relocs is not None:
        name_to_addr = {v: k for k, v in STUBS.items()}
        for sym_name, off in relocs:
            target = name_to_addr.get(sym_name)
            if target is None:
                raise RuntimeError(f"unexpected relocation: {sym_name}")
            patch_bl(buf, off, base_addr + off, target)

    uc.mem_write(base_addr, bytes(buf))
    if rodata:
        uc.mem_write(RODATA_ADDR, rodata)
    for addr in STUBS:
        uc.mem_write(addr, make_stub_bx_lr())

    uc.mem_write(G2FC8_PTR, struct.pack("<I", G2FC8_OBJ))
    uc.mem_write(G3158_PTR, struct.pack("<I", 0xCAFE3158))
    uc.mem_write(G3130_PTR, struct.pack("<I", G3130_OBJ))

    g2fc8 = bytearray(0xE00)
    struct.pack_into("<I", g2fc8, 0x754, 0xFFFFFFFF)
    uc.mem_write(G2FC8_OBJ, bytes(g2fc8))
    uc.mem_write(G3130_OBJ + 0x450C, b"\x01")

    uc.mem_write(VOBJ_ADDR, struct.pack("<I", VTBL_ADDR))
    uc.mem_write(VTBL_ADDR, struct.pack("<II", 0, VFUNC_ADDR))

    self_buf = bytearray(0x400)
    struct.pack_into("<I", self_buf, 0x00, 0xFFFFFFFF)
    struct.pack_into("<I", self_buf, 0x08, state)
    struct.pack_into("<I", self_buf, 0x208, VOBJ_ADDR if vobj_ok else 0)
    struct.pack_into("<I", self_buf, 0x350, 0xCAFE0350)
    struct.pack_into("<I", self_buf, 0x358, 0xCAFE0358)
    uc.mem_write(SELF_ADDR, bytes(self_buf))

    uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)

    calls: list[tuple] = []

    def hook_code(uc_inst, address, size, user_data):
        tag = STUBS.get(address)
        if tag is None:
            return
        r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
        if tag == "ui_func_0026b7cc":
            calls.append((tag,))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ret_26b7cc)
        elif tag in ("engine_func_002b8584", "shop_func_002339e8", "shop_func_002339ac", "camp_func_002bc200", "script_vm_func_00126edc", "vfunc1"):
            calls.append((tag, r0))
        elif tag in ("engine_func_002a150c", "script_vm_func_002971e4", "script_vm_func_00262bcc"):
            calls.append((tag, r0 if tag != "engine_func_002a150c" else "ptr", r1))
        elif tag == "script_vm_func_00291018":
            s = bytes(uc_inst.mem_read(r1, 20)).split(b"\x00", 1)[0]
            calls.append((tag, r0, s))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, 42)
        elif tag == "camp_func_00233ac0":
            calls.append((tag, r0, r1, r2))
        elif tag == "script_vm_func_0019dfbc":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ret_19dfbc)
        elif tag == "func_002f61a4":
            calls.append((tag,))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ret_2f61a4)
        elif tag == "camp_func_002c1830":
            calls.append((tag, r0, r1))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ret_2c1830)
        elif tag in ("script_vm_func_00289984", "script_vm_func_0023554c", "func_002fea30", "camp_func_002b9008"):
            calls.append((tag,))
        elif tag == "script_vm_func_00297674":
            calls.append((tag,))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ret_297674)
        elif tag == "engine_func_002bb09c":
            calls.append((tag,))
        elif tag == "engine_func_002bad80":
            calls.append((tag, r1))
            uc_inst.mem_write(r0, struct.pack("<Q", 0x1122334455667788))

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    out_self = bytes(uc.mem_read(SELF_ADDR, 0x400))
    out_g2fc8 = bytes(uc.mem_read(G2FC8_OBJ, 0xE00))
    out_g3130 = bytes(uc.mem_read(G3130_OBJ + 0x450C, 1))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return out_self, out_g2fc8, out_g3130, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs, cand_rodata = compile_candidate()

    cases = [
        ("state0_init", 0, True, 0, 0, 0, 0, 0),
        ("state1_not2_no_abort", 1, True, 0, 0, 0, 0, 0),
        ("state1_not2_abort", 1, True, 0, 1, 1, 0, 0),
        ("state1_2_r0_proceed", 1, True, 2, 0, 0, 0, 0),
        ("state1_2_r1_cancel_vobj", 1, True, 2, 0, 0, 1, 0),
        ("state1_2_r2_noop", 1, False, 2, 0, 0, 2, 0),
        ("state2_wait", 2, True, 0, 0, 0, 0, 0),
        ("state2_done_null_vobj", 2, False, 0, 0, 0, 0, 1),
        ("state2_done_with_vobj", 2, True, 0, 0, 0, 0, 1),
        ("state3_noop", 3, True, 0, 0, 0, 0, 0),
    ]

    for name, *args in cases:
        o_s, o_g, o_g2, o_c, o_r = run_one(orig_code, FUNC_ADDR, None, b"", *args)
        c_s, c_g, c_g2, c_c, c_r = run_one(cand_code, 0x00180000, cand_relocs, cand_rodata, *args)
        if (o_s, o_g, o_g2) != (c_s, c_g, c_g2):
            print(f"FAIL {name}: memory mismatch")
            return 1
        if o_c != c_c:
            print(f"FAIL {name}: calls mismatch\n  orig={o_c}\n  cand={c_c}")
            return 1
        if o_r != c_r:
            print(f"FAIL {name}: callee-saved mismatch")
            return 1

    # 5 mutation controls
    patched_cand = bytearray(cand_code)
    name_to_addr = {v: k for k, v in STUBS.items()}
    for sym_name, off in cand_relocs:
        patch_bl(patched_cand, off, 0x00180000 + off, name_to_addr[sym_name])

    def check_mutant(patch_fn, case_args):
        mc = bytearray(patched_cand)
        if not patch_fn(mc):
            return False
        o_s, o_g, o_g2, o_c, _ = run_one(orig_code, FUNC_ADDR, None, b"", *case_args)
        m_s, m_g, m_g2, m_c, _ = run_one(bytes(mc), 0x00180000, None, cand_rodata, *case_args)
        return (m_s, m_g, m_g2, m_c) != (o_s, o_g, o_g2, o_c)

    def mut_nop_reloc(reloc_idx: int):
        def _fn(mc: bytearray) -> bool:
            if reloc_idx >= len(cand_relocs):
                return False
            off = cand_relocs[reloc_idx][1]
            struct.pack_into("<I", mc, off, 0xE1A00000)
            return True
        return _fn

    reloc_map = {sym: idx for idx, (sym, _) in enumerate(cand_relocs)}
    mut_specs = [
        (mut_nop_reloc(reloc_map["ui_func_0026b7cc"]), cases[8][1:]),
        (mut_nop_reloc(reloc_map["engine_func_002b8584"]), cases[0][1:]),
        (mut_nop_reloc(reloc_map["camp_func_002bc200"]), cases[2][1:]),
        (mut_nop_reloc(reloc_map["script_vm_func_00126edc"]), cases[3][1:]),
        (mut_nop_reloc(reloc_map["script_vm_func_00262bcc"]), cases[3][1:]),
    ]
    mutants_ok = sum(1 for fn, cargs in mut_specs if check_mutant(fn, cargs))
    if mutants_ok != 5:
        print(f"FAIL: detected only {mutants_ok}/5 mutants")
        return 1

    print(
        f"PASS: script_vm_func_00392060 (0x{FUNC_ADDR:08x}) matched original across "
        f"{len(cases)} cases and detected {mutants_ok}/5 mutants "
        f"(candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
