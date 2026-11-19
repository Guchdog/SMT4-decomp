#!/usr/bin/env python3
"""Differential test for engine_func_0027521c (0x0027521c) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_0027521c"

FUNC_ADDR = 0x0027521C
FUNC_SIZE = 640

G_PTR_ADDR = 0x00447A48
G8_ADDR = 0x0049F91C
OBJ_ADDR = 0x20000000
NODE_BASE = 0x20002000
SUB_BASE = 0x20003000
DEEP_BASE = 0x20004000

STUBS = {
    0x0027D010: "engine_func_0027d010",
    0x00152AF8: "script_vm_func_00152af8",
    0x002A7AA0: "script_vm_func_002a7aa0",
    0x00267420: "battle_func_00267420",
    0x0028C8A8: "engine_func_0028c8a8",
    0x0028C880: "engine_func_0028c880",
    0x002A5A54: "engine_func_002a5a54",
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


def compile_candidate() -> tuple[bytes, list[tuple[str, int]]]:
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
    text_data = data[shdrs[tidx][4] : shdrs[tidx][4] + shdrs[tidx][5]]
    symtab = next(s for s in shdrs if s[1] == 2)
    strtab_off = shdrs[symtab[6]][4]

    fn_off = fn_size = None
    for i in range(symtab[5] // 16):
        st_name, st_value, st_size, st_info, _, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + i * 16)
        if st_shndx == tidx:
            name = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
            if name == "engine_func_0027521c":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("engine_func_0027521c not found in object")

    relocs: list[tuple[str, int]] = []
    for s in shdrs:
        if s[1] == 9 and s[7] == tidx:
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if fn_off <= r_off < fn_off + fn_size and r_type in (28, 29):
                    st_name = struct.unpack_from("<I", data, symtab[4] + sym_idx * 16)[0]
                    sname = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
                    relocs.append((sname, r_off - fn_off))

    return bytes(text_data[fn_off : fn_off + fn_size]), relocs


def patch_bl(code: bytearray, at_off: int, src_pc: int, dst_pc: int) -> None:
    delta = (dst_pc - (src_pc + 8)) >> 2
    hi = code[at_off + 3]
    insn = (hi << 24) | (delta & 0x00FFFFFF)
    struct.pack_into("<I", code, at_off, insn)


def run_one(
    code_bytes: bytes,
    base_addr: int,
    relocs: list[tuple[str, int]] | None,
    obj_b4: int,
    obj_state: int,
    g8_b22: int,
    ret_27d010: int,
    node_flags: int,
    sub_38: int,
) -> tuple[bytes, bytes, bytes, list[tuple], dict[str, int]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_map(0x20000000, 0x00010000)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    cpacr = uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, cpacr | (0xF << 20))
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

    buf = bytearray(code_bytes)
    if relocs is not None:
        name_to_addr = {v: k for k, v in STUBS.items()}
        for sym_name, off in relocs:
            target = name_to_addr.get(sym_name)
            if target is None:
                raise RuntimeError(f"unexpected relocation: {sym_name}")
            patch_bl(buf, off, base_addr + off, target)

    uc.mem_write(base_addr, bytes(buf))
    for addr in STUBS:
        uc.mem_write(addr, make_stub_bx_lr())

    uc.mem_write(G_PTR_ADDR, struct.pack("<I", OBJ_ADDR))
    g8 = bytearray(0x30)
    g8[0x22] = g8_b22
    uc.mem_write(G8_ADDR, bytes(g8))

    obj = bytearray(0x400)
    struct.pack_into("<I", obj, 0x00, obj_state)
    obj[0x04] = obj_b4
    for i in (0, 2, 23):
        off = 0x1C + i * 0x28
        obj[off + 0] = 1
        obj[off + 1] = 1
        struct.pack_into("<4f", obj, off + 4, 1.0, 2.0, 3.0, 4.0)
        struct.pack_into("<hH", obj, off + 0x14, 7, 0xC if i != 2 else 0x5)
        node_addr = NODE_BASE + i * 0x20
        sub_addr = SUB_BASE + i * 0x40
        deep_addr = DEEP_BASE + i * 0x220
        struct.pack_into("<I", obj, off + 0x18, node_addr)
        struct.pack_into("<h", obj, off + 0x1C, -10 - i)
        uc.mem_write(node_addr, struct.pack("<III", node_flags, 0, sub_addr))
        sub_buf = bytearray(0x40)
        struct.pack_into("<I", sub_buf, 0x2C, deep_addr)
        struct.pack_into("<i", sub_buf, 0x38, sub_38)
        uc.mem_write(sub_addr, bytes(sub_buf))
        uc.mem_write(deep_addr + 0x1F6, b"\x77")
    uc.mem_write(OBJ_ADDR, bytes(obj))

    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)
    uc.reg_write(arm.UC_ARM_REG_D8, 0x1122334455667788)
    uc.reg_write(arm.UC_ARM_REG_D9, 0x99AABBCCDDEEFF00)

    calls: list[tuple] = []

    def hook_code(uc_inst, address, size, user_data):
        tag = STUBS.get(address)
        if tag is None:
            return
        r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
        if tag == "engine_func_0027d010":
            calls.append((tag,))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ret_27d010)
        elif tag in ("script_vm_func_00152af8", "script_vm_func_002a7aa0"):
            calls.append((tag, r0))
        elif tag == "battle_func_00267420":
            f = [uc_inst.reg_read(getattr(arm, f"UC_ARM_REG_S{k}")) for k in range(7)]
            calls.append((tag, r0, *f))
        elif tag == "engine_func_0028c8a8":
            vec = struct.unpack("<3f", uc_inst.mem_read(r2, 12))
            calls.append((tag, r0, r1, vec))
        elif tag == "engine_func_0028c880":
            f = [uc_inst.reg_read(getattr(arm, f"UC_ARM_REG_S{k}")) for k in range(3)]
            calls.append((tag, r0, r1, *f))
        elif tag == "engine_func_002a5a54":
            s0 = uc_inst.reg_read(arm.UC_ARM_REG_S0)
            calls.append((tag, r0, s0))

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    out_obj = bytes(uc.mem_read(OBJ_ADDR, 0x400))
    out_nodes = bytes(uc.mem_read(NODE_BASE, 0x400))
    out_deep = bytes(uc.mem_read(DEEP_BASE + 0x1F6, 1))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "d8": uc.reg_read(arm.UC_ARM_REG_D8),
        "d9": uc.reg_read(arm.UC_ARM_REG_D9),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return out_obj, out_nodes, out_deep, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs = compile_candidate()

    cases = [
        ("b4_0_g8_1_flag0", 0, 0, 1, 0, 0, 7),
        ("b4_0_g8_1_flag2", 0, 0, 1, 0, 2, 7),
        ("b4_0_g8_0_flag2_diff38", 0, 0, 0, 0, 2, 99),
        ("b4_0_g8_0_flag0_same38", 0, 0, 0, 0, 0, 7),
        ("b4_1_state0", 1, 0, 0, 0, 0, 0),
        ("b4_1_state1", 1, 1, 0, 0, 0, 0),
        ("b4_1_state2_gate0", 1, 2, 0, 0, 0, 0),
        ("b4_1_state2_gate1", 1, 2, 0, 1, 0, 0),
        ("b4_1_state3_noop", 1, 3, 0, 0, 0, 0),
    ]

    for name, *args in cases:
        o_o, o_n, o_d, o_c, o_r = run_one(orig_code, FUNC_ADDR, None, *args)
        c_o, c_n, c_d, c_c, c_r = run_one(cand_code, 0x00180000, cand_relocs, *args)
        if (o_o, o_n, o_d) != (c_o, c_n, c_d):
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
        o_o, o_n, o_d, o_c, _ = run_one(orig_code, FUNC_ADDR, None, *case_args)
        m_o, m_n, m_d, m_c, _ = run_one(bytes(mc), 0x00180000, None, *case_args)
        return (m_o, m_n, m_d, m_c) != (o_o, o_n, o_d, o_c)

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
        (mut_nop_reloc(reloc_map["engine_func_0028c8a8"]), cases[2][1:]),
        (mut_nop_reloc(reloc_map["engine_func_0028c880"]), cases[2][1:]),
        (mut_nop_reloc(reloc_map["engine_func_002a5a54"]), cases[2][1:]),
        (mut_nop_reloc(reloc_map["script_vm_func_00152af8"]), cases[4][1:]),
        (mut_nop_reloc(reloc_map["battle_func_00267420"]), cases[7][1:]),
    ]
    mutants_ok = sum(1 for fn, cargs in mut_specs if check_mutant(fn, cargs))
    if mutants_ok != 5:
        print(f"FAIL: detected only {mutants_ok}/5 mutants")
        return 1

    print(
        f"PASS: engine_func_0027521c (0x{FUNC_ADDR:08x}) matched original across "
        f"{len(cases)} cases and detected {mutants_ok}/5 mutants "
        f"(candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
