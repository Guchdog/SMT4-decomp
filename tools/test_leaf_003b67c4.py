#!/usr/bin/env python3
"""Differential Unicorn test for ui_func_003b67c4 (0x003b67c4, 1208 B)."""

from __future__ import annotations

import struct
import sys
import tempfile
from pathlib import Path

from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_ARM, Uc
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x003B67C4
FUNC_SIZE = 1208
FUNC_NAME = "ui_func_003b67c4"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

A0_ADDR = 0x00600000
DEMON_ADDR = 0x00610000
MC_ADDR = 0x00611000
LAYOUT_ADDR = 0x00612000
G0_ADDR = 0x00613000
G0_C_ADDR = 0x00614000
GLOBAL_44DC38 = 0x0044DC38
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x002A89E4: "camp_func_002a89e4",
    0x002BF6D0: "camp_func_002bf6d0",
    0x002BF460: "ui_func_002bf460",
    0x002B66EC: "script_vm_func_002b66ec",
    0x002B0788: "ui_func_002b0788",
    0x002BE4DC: "func_002be4dc",
    0x002B6A98: "ui_func_002b6a98",
    0x002BE16C: "engine_func_002be16c",
    0x003B6FC4: "ui_func_003b6fc4",
    0x002B0908: "func_002b0908",
    0x002BF710: "ui_func_002bf710",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
NAME_BY_STUB = {v: k for k, v in STUB_BY_NAME.items()}


def patch_cand_elf(obj_path: Path) -> tuple[bytes, list[tuple[int, bytes]], int]:
    elf = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", elf, 0x20)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", elf, 0x2E)
    sections = [struct.unpack_from("<10I", elf, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = sections[e_shstrndx][4]

    def sec_name(idx: int) -> str:
        n_off = shstr_off + sections[idx][0]
        return elf[n_off : elf.find(b"\x00", n_off)].decode("ascii", errors="replace")

    symtab = next(sh for sh in sections if sh[1] == 2)
    strtab = sections[symtab[6]]
    str_off = strtab[4]

    def sym_info(sym_idx: int) -> tuple[str, int, int]:
        s_off = symtab[4] + sym_idx * 16
        st_name, st_value, _, _, _, st_shndx = struct.unpack_from("<IIIBBH", elf, s_off)
        end = elf.find(b"\x00", str_off + st_name)
        return elf[str_off + st_name : end].decode("ascii", errors="replace"), st_value, st_shndx

    func_val = func_size = func_shndx = None
    for idx in range(symtab[5] // 16):
        name, val, shndx = sym_info(idx)
        if name == FUNC_NAME:
            s_off = symtab[4] + idx * 16
            func_size = struct.unpack_from("<I", elf, s_off + 8)[0]
            func_val, func_shndx = val, shndx
            break
    if func_val is None or func_shndx is None:
        raise RuntimeError(f"Symbol {FUNC_NAME} not found")

    text_sh = sections[func_shndx]
    text_bytes = bytearray(elf[text_sh[4] : text_sh[4] + text_sh[5]])
    text_name = sec_name(func_shndx)

    rodata_blobs: list[tuple[int, bytes]] = []
    rodata_map: dict[int, int] = {}
    cur_ro = RODATA_BASE
    for idx, sh in enumerate(sections):
        sname = sec_name(idx)
        if sh[1] == 1 and sh[5] > 0 and sname.startswith(".rodata"):
            blob = elf[sh[4] : sh[4] + sh[5]]
            rodata_map[idx] = cur_ro
            rodata_blobs.append((cur_ro, blob))
            cur_ro = (cur_ro + len(blob) + 15) & ~15

    rel_sh = None
    for idx, sh in enumerate(sections):
        if sh[1] == 9 and sh[7] == func_shndx:
            rel_sh = sh
            break
    if rel_sh is None:
        for idx, sh in enumerate(sections):
            if sh[1] == 9 and sec_name(idx) == f".rel{text_name}":
                rel_sh = sh
                break

    if rel_sh is not None:
        for off in range(0, rel_sh[5], 8):
            r_offset, r_info = struct.unpack_from("<II", elf, rel_sh[4] + off)
            r_type = r_info & 0xFF
            r_sym = r_info >> 8
            sname, sval, sshndx = sym_info(r_sym)
            if not (func_val <= r_offset < func_val + func_size) and not (
                r_type in (28, 29) and sname in STUB_BY_NAME
            ):
                continue
            if r_type in (28, 29):
                if sname in STUB_BY_NAME:
                    target = STUB_BY_NAME[sname]
                elif sshndx == func_shndx:
                    target = CODE_BASE + sval
                else:
                    raise RuntimeError(f"Unknown call target {sname}")
                insn = struct.unpack_from("<I", text_bytes, r_offset)[0]
                imm24 = ((target - (CODE_BASE + r_offset + 8)) >> 2) & 0x00FFFFFF
                struct.pack_into("<I", text_bytes, r_offset, (insn & 0xFF000000) | imm24)
            elif r_type == 2:
                addend = struct.unpack_from("<i", text_bytes, r_offset)[0]
                if sshndx in rodata_map:
                    target = rodata_map[sshndx] + sval + addend
                    struct.pack_into("<I", text_bytes, r_offset, target)
                elif sshndx == func_shndx:
                    target = CODE_BASE + sval + addend
                    struct.pack_into("<I", text_bytes, r_offset, target)
            elif r_type in (43, 44):
                if sshndx in rodata_map:
                    target = rodata_map[sshndx] + sval
                    insn = struct.unpack_from("<I", text_bytes, r_offset)[0]
                    imm16 = (target & 0xFFFF) if r_type == 43 else ((target >> 16) & 0xFFFF)
                    enc = ((imm16 & 0xF000) << 4) | (imm16 & 0x0FFF)
                    struct.pack_into("<I", text_bytes, r_offset, (insn & 0xFFF0F000) | enc)
            elif r_type == 42:
                pass
            else:
                raise RuntimeError(f"Unhandled reloc type {r_type} for {sname}")

    return bytes(text_bytes), rodata_blobs, func_val


def patch_orig_bl(code_bytes: bytearray) -> None:
    base = FUNC_ADDR - CODE_BASE
    for off in range(0, FUNC_SIZE, 4):
        insn = struct.unpack_from("<I", code_bytes, base + off)[0]
        top = (insn >> 24) & 0xFF
        if top in (0xEA, 0xEB, 0xFA, 0xFB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x800000:
                imm24 -= 0x1000000
            pc = FUNC_ADDR + off + 8
            target = pc + (imm24 << 2)
            if target in CALLEES:
                stub = STUB_BY_NAME[CALLEES[target]]
                new_imm = ((stub - pc) >> 2) & 0x00FFFFFF
                op = 0xEA000000 if top == 0xEA else 0xEB000000
                struct.pack_into("<I", code_bytes, base + off, op | new_imm)


def read_cstr(uc: Uc, addr: int, limit: int = 32) -> str:
    raw = bytes(uc.mem_read(addr, limit))
    nul = raw.find(0)
    return (raw[:nul] if nul >= 0 else raw).decode("ascii", errors="replace")


def run_case(
    code_bytes: bytes,
    rodata_blobs: list[tuple[int, bytes]],
    entry_addr: int,
    case: dict,
) -> tuple[list[tuple], int]:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STUB_BASE - 0x1000, 0x4000)
    uc.mem_map(RODATA_BASE, 0x20000)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(A0_ADDR, 0x20000)
    uc.mem_map(HALT_ADDR & ~0xFFF, 0x2000)

    uc.mem_write(CODE_BASE, code_bytes)
    for addr, blob in rodata_blobs:
        uc.mem_write(addr, blob)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

    idx = case.get("idx", 0)
    a0_buf = bytearray(0xE000)
    struct.pack_into("<i", a0_buf, 0xD5E0 + idx * 4, case.get("slot_target", 0))
    uc.mem_write(A0_ADDR, bytes(a0_buf))

    demon_buf = bytearray(0x80)
    struct.pack_into("<H", demon_buf, 0x44, case.get("mask", 0))
    struct.pack_into("<h", demon_buf, 0x46, -123)
    demon_buf[0x48] = case.get("stat48", 10)
    uc.mem_write(DEMON_ADDR, bytes(demon_buf))

    mc_buf = bytearray(0x80)
    struct.pack_into("<H", mc_buf, 0x72, case.get("mask", 0))
    uc.mem_write(MC_ADDR, bytes(mc_buf))

    layout_buf = bytearray(0x10)
    struct.pack_into("<hh", layout_buf, 8, 100, 200)
    uc.mem_write(LAYOUT_ADDR, bytes(layout_buf))

    g0_buf = bytearray(0x10)
    struct.pack_into("<hhI", g0_buf, 8, -10, 20, G0_C_ADDR)
    uc.mem_write(G0_ADDR, bytes(g0_buf))
    uc.mem_write(G0_C_ADDR, struct.pack("<hh", 5, 42))

    uc.mem_write(GLOBAL_44DC38, struct.pack("<Ii", G0_ADDR, case.get("init_color", -99)))

    trace: list[tuple] = []

    def on_code(u: Uc, addr: int, _size: int, _user: object) -> None:
        if addr == HALT_ADDR:
            u.emu_stop()
            return
        name = NAME_BY_STUB.get(addr)
        if name is None:
            return
        r0 = u.reg_read(UC_ARM_REG_R0)
        r1 = u.reg_read(UC_ARM_REG_R1)
        r2 = u.reg_read(UC_ARM_REG_R2)
        r3 = u.reg_read(UC_ARM_REG_R3)
        sp = u.reg_read(UC_ARM_REG_SP)

        if name == "camp_func_002a89e4":
            trace.append((name, struct.unpack_from("<i", struct.pack("<I", r0))[0]))
            u.reg_write(UC_ARM_REG_R0, DEMON_ADDR)
        elif name == "camp_func_002bf6d0":
            trace.append((name, r0, r1))
            u.reg_write(UC_ARM_REG_R0, LAYOUT_ADDR)
        elif name == "ui_func_002bf460":
            s0, s1 = struct.unpack_from("<ii", u.mem_read(sp, 8))
            trace.append((name, r0, r1, r2, r3, s0, s1))
        elif name == "script_vm_func_002b66ec":
            trace.append((name,))
            u.reg_write(UC_ARM_REG_R0, MC_ADDR)
        elif name == "ui_func_002b0788":
            trace.append((name, r0 & 0xFFFF))
            u.reg_write(UC_ARM_REG_R0, (r0 + 100) & 0xFFFFFFFF)
        elif name == "func_002be4dc":
            trace.append((name, struct.unpack_from("<i", struct.pack("<I", r0))[0]))
        elif name == "ui_func_002b6a98":
            s0 = struct.unpack_from("<I", u.mem_read(sp, 4))[0]
            trace.append((name, struct.unpack_from("<i", struct.pack("<I", r0))[0], r1, r2, r3, s0))
        elif name == "engine_func_002be16c":
            s0, s1, s2, s3 = struct.unpack_from("<IIII", u.mem_read(sp, 16))
            trace.append((name, r0, r1, r2, r3, s0, s1, read_cstr(u, s2), s3))
        elif name == "ui_func_003b6fc4":
            trace.append((name, r0, struct.unpack_from("<i", struct.pack("<I", r1))[0], r2, r3))
        elif name == "func_002b0908":
            s0, s1, s2, s3 = struct.unpack_from("<IIII", u.mem_read(sp, 16))
            trace.append((name, r0, r1, r2, r3, s0, s1, s2, s3))
        elif name == "ui_func_002bf710":
            trace.append((name, u.reg_read(UC_ARM_REG_S0)))

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_R0, A0_ADDR)
    uc.reg_write(UC_ARM_REG_R1, case["mode"])
    uc.reg_write(UC_ARM_REG_R2, idx & 0xFFFFFFFF)
    uc.reg_write(UC_ARM_REG_R3, 5)
    sp_args = struct.pack(
        "<iiIIii",
        10,
        20,
        0x3F400000,
        case.get("flag", 0),
        case.get("val7", 0),
        case.get("val10", 10),
    )
    uc.mem_write(STACK_TOP - 24, sp_args)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP - 24)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(entry_addr, HALT_ADDR, timeout=5_000_000)

    final_color = struct.unpack_from("<i", uc.mem_read(GLOBAL_44DC38 + 4, 4))[0]
    return trace, final_color


CASES = [
    {"name": "mode0", "mode": 0},
    {"name": "mode1_gt_val7", "mode": 1, "val7": 1, "stat48": 10, "val10": 10},
    {"name": "mode1_gt_stat", "mode": 1, "val7": 0, "stat48": 11, "val10": 10},
    {"name": "mode1_le_eq", "mode": 1, "val7": 0, "stat48": 10, "val10": 10},
    {"name": "mode2_pos_found_bit10", "mode": 2, "idx": 1, "mask": 1 << 10, "slot_target": 0},
    {"name": "mode2_neg_not_found", "mode": 2, "idx": -1, "mask": 1 << 11, "slot_target": 0, "init_color": -1},
    {"name": "mode3", "mode": 3},
    {"name": "mode4_gt", "mode": 4, "val7": 0, "stat48": 15, "val10": 10},
    {"name": "mode4_le_same_color", "mode": 4, "val7": 0, "stat48": 10, "val10": 10, "init_color": -1},
    {"name": "mode5_tail", "mode": 5, "idx": 2},
    {"name": "mode6_flag1", "mode": 6, "flag": 1},
    {"name": "mode6_flag0", "mode": 6, "flag": 0},
    {"name": "mode7_flag0", "mode": 7, "flag": 0, "val7": 3},
    {"name": "mode7_flag1_lt8", "mode": 7, "flag": 1, "val7": 7},
    {"name": "mode7_flag1_ge8", "mode": 7, "flag": 1, "val7": 8},
    {"name": "mode8_oob", "mode": 8},
]


def compile_cand(cpp_text: str) -> tuple[bytes, list[tuple[int, bytes]], int]:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        src = td_path / "cand.cpp"
        obj = td_path / "cand.o"
        src.write_text(cpp_text, encoding="utf-8")
        compile_tu_armv6k(src, obj)
        text_bytes, rodata, func_val = patch_cand_elf(obj)
        cand_mem = bytearray(CODE_SIZE)
        cand_mem[0 : len(text_bytes)] = text_bytes
        return bytes(cand_mem), rodata, CODE_BASE + func_val


def main() -> int:
    orig_mem = bytearray(CODE_SIZE)
    raw_code = CODE_BIN.read_bytes()
    orig_mem[0 : len(raw_code)] = raw_code
    patch_orig_bl(orig_mem)
    orig_bytes = bytes(orig_mem)

    cpp_text = SRC_CPP.read_text(encoding="utf-8")
    cand_bytes, cand_ro, cand_entry = compile_cand(cpp_text)

    for case in CASES:
        ores = run_case(orig_bytes, [], FUNC_ADDR, case)
        cres = run_case(cand_bytes, cand_ro, cand_entry, case)
        if ores != cres:
            print(f"FAIL {case['name']}")
            print(f"  orig: {ores}")
            print(f"  cand: {cres}")
            return 1
    print(f"PASS {len(CASES)} cases (all 8 modes + branches + OOB)")

    muts = [
        (
            "neg_case1_cmp",
            "        case 1u:\n"
            "            if (val7 > 0 || static_cast<s32>(demon[0x48u]) > val10) {",
            "        case 1u:\n"
            "            if (val7 > 0 || static_cast<s32>(demon[0x48u]) >= val10) {",
        ),
        (
            "neg_case2_bit_limit",
            "            for (s32 bit = 1; bit < 0x0B; ++bit) {",
            "            for (s32 bit = 1; bit < 0x0A; ++bit) {",
        ),
        (
            "neg_case4_color",
            "            const s32 color = (val7 > 0 || static_cast<s32>(demon[0x48u]) > val10) ? 0xFF : -1;",
            "            const s32 color = (val7 > 0 || static_cast<s32>(demon[0x48u]) > val10) ? 0xFE : -1;",
        ),
        (
            "neg_case6_flag",
            "        case 6u:\n"
            "            if (flag != 0u) {",
            "        case 6u:\n"
            "            if (flag == 0u) {",
        ),
        (
            "neg_case7_scale",
            "            if (val7 < 8) {\n"
            "                ui_func_002bf710(static_cast<f32>(val7) * 0.125f);",
            "            if (val7 <= 8) {\n"
            "                ui_func_002bf710(static_cast<f32>(val7) * 0.125f);",
        ),
    ]

    for mname, old, new in muts:
        assert old in cpp_text, f"Anchor missing for {mname}"
        mut_cpp = cpp_text.replace(old, new, 1)
        m_bytes, m_ro, m_entry = compile_cand(mut_cpp)
        caught = False
        for case in CASES:
            if run_case(orig_bytes, [], FUNC_ADDR, case) != run_case(m_bytes, m_ro, m_entry, case):
                caught = True
                break
        if not caught:
            print(f"FAIL negative control {mname} was not caught!")
            return 1
        print(f"PASS {mname} (caught)")

    print(f"ALL PASS: {len(CASES)} cases + {len(muts)} negative controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
