#!/usr/bin/env python3
"""Differential Unicorn test for camp_func_001f1ad8 (0x001f1ad8, 1264 B)."""

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
    UC_ARM_REG_S1,
    UC_ARM_REG_S2,
    UC_ARM_REG_S3,
    UC_ARM_REG_S4,
    UC_ARM_REG_SP,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x001F1AD8
FUNC_SIZE = 1264
FUNC_NAME = "camp_func_001f1ad8"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

R5_ADDR = 0x00600000
G44EA00_OBJ = 0x00601000
LAYOUT_BASE = 0x00603000
SZ_BASE = 0x00604000
GLOBAL_44EA00 = 0x0044EA00
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x00262A44: "func_00262a44",
    0x0029F260: "camp_func_0029f260",
    0x0029F248: "camp_func_0029f248",
    0x002888DC: "camp_func_002888dc",
    0x002BF6D0: "camp_func_002bf6d0",
    0x002BF460: "ui_func_002bf460",
    0x0029F0F4: "camp_func_0029f0f4",
    0x001B0698: "camp_func_001b0698",
    0x002BE77C: "ui_func_002be77c",
    0x002BF710: "ui_func_002bf710",
    0x0029D8FC: "ui_func_0029d8fc",
    0x0029A418: "func_0029a418",
    0x002BEF70: "shop_func_002bef70",
    0x002BEF7C: "ui_func_002bef7c",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
STUB_CB = STUB_BASE + 0x100
STUB_BY_NAME["st30c_cb"] = STUB_CB
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
) -> tuple[list[tuple], bytes]:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STUB_BASE - 0x1000, 0x4000)
    uc.mem_map(RODATA_BASE, 0x20000)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(R5_ADDR, 0x10000)
    uc.mem_map(HALT_ADDR & ~0xFFF, 0x2000)

    uc.mem_write(CODE_BASE, code_bytes)
    for addr, blob in rodata_blobs:
        uc.mem_write(addr, blob)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

    r5_buf = bytearray(0x600)
    struct.pack_into("<f", r5_buf, 0x44, 1.25)
    struct.pack_into("<i", r5_buf, 0x3FC, case.get("t", 4))
    struct.pack_into("<hh", r5_buf, 0x44C, 0x100, 0x200)
    uc.mem_write(R5_ADDR, bytes(r5_buf))

    uc.mem_write(GLOBAL_44EA00, struct.pack("<I", G44EA00_OBJ))
    st30c = bytearray(0x20)
    struct.pack_into("<III", st30c, 0, 0, 0, case.get("init_30c", 3))
    st30c[0x18] = case.get("f_30c", 0)
    struct.pack_into("<I", st30c, 0x1C, STUB_CB)
    uc.mem_write(G44EA00_OBJ + 0x130C, bytes(st30c))

    trace: list[tuple] = []
    l_idx = [0]

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

        if name == "func_00262a44":
            trace.append((name,))
            u.reg_write(UC_ARM_REG_R0, 0 if case.get("r5_null", False) else R5_ADDR)
        elif name == "camp_func_0029f260":
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, 2 if r0 == R5_ADDR + 0x4E8 else 1)
        elif name == "camp_func_0029f248":
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, 1 if r0 == R5_ADDR + 0x4E8 else 0)
        elif name == "camp_func_002888dc":
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, 0x777)
        elif name == "camp_func_002bf6d0":
            trace.append((name, r0, r1))
            idx = l_idx[0]
            l_idx[0] += 1
            la = LAYOUT_BASE + idx * 0x20
            sa = SZ_BASE + idx * 0x10
            lbuf = bytearray(0x10)
            struct.pack_into("<hhI", lbuf, 8, 100 - idx * 17, 200 - idx * 23, sa)
            u.mem_write(la, bytes(lbuf))
            u.mem_write(sa, struct.pack("<hh", 80, 32))
            u.reg_write(UC_ARM_REG_R0, la)
        elif name == "ui_func_002bf460":
            s0, s1 = struct.unpack_from("<II", u.mem_read(sp, 8))
            trace.append((name, r0, r1, r2, r3, s0, s1))
        elif name == "camp_func_0029f0f4":
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, case.get("list2_len", 5))
        elif name == "camp_func_001b0698":
            trace.append((name, r0, r1, r3))
            u.mem_write(r2, f"Item{r3}\x00".encode("ascii"))
            u.reg_write(UC_ARM_REG_R0, case.get("nonzero", 0))
        elif name == "ui_func_002be77c":
            trace.append(
                (
                    name,
                    r0,
                    r1,
                    read_cstr(u, r2),
                    u.reg_read(UC_ARM_REG_S0),
                    u.reg_read(UC_ARM_REG_S1),
                    u.reg_read(UC_ARM_REG_S2),
                    u.reg_read(UC_ARM_REG_S3),
                    u.reg_read(UC_ARM_REG_S4),
                )
            )
        elif name == "ui_func_002bf710":
            trace.append((name, u.reg_read(UC_ARM_REG_S0)))
        elif name == "ui_func_0029d8fc":
            trace.append((name, r0 & 0xFFFF))
            u.reg_write(UC_ARM_REG_R0, case.get("kind", 0))
        elif name == "func_0029a418":
            s0 = struct.unpack_from("<I", u.mem_read(sp, 4))[0]
            trace.append((name, r0, r1, r2, r3, s0))
        elif name == "shop_func_002bef70":
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, 11)
        elif name == "ui_func_002bef7c":
            trace.append((name,))
            u.reg_write(UC_ARM_REG_R0, 22)
        elif name == "st30c_cb":
            trace.append((name,))

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_R0, 30)
    uc.reg_write(UC_ARM_REG_R1, 40)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(entry_addr, HALT_ADDR, timeout=5_000_000)

    return trace, bytes(uc.mem_read(G44EA00_OBJ + 0x130C, 0x20))


CASES = [
    {"name": "r5_null", "r5_null": True},
    {"name": "t_4_kind1_cb", "t": 4, "list2_len": 5, "kind": 1, "nonzero": 1, "f_30c": 1},
    {"name": "t_2_kind0_nocb", "t": 2, "list2_len": 10, "kind": 0, "nonzero": 0, "init_30c": 3},
    {"name": "t_0_kind2", "t": 0, "list2_len": 2, "kind": 2, "nonzero": 0},
    {"name": "t_3_kind6", "t": 3, "list2_len": 8, "kind": 6, "nonzero": 1},
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
            for i in range(max(len(ores[0]), len(cres[0]))):
                a = ores[0][i] if i < len(ores[0]) else None
                b = cres[0][i] if i < len(cres[0]) else None
                if a != b:
                    print(f"  diff[{i}]: {a} != {b}")
                    break
            return 1
        print(f"PASS {case['name']} ({len(ores[0])} calls)")

    muts = [
        ("neg_t_ge_3", "inline s32 lerp_pos_1f1ad8(s32 src, s32 dst, s32 t) {\n    if (t >= 4) {", "inline s32 lerp_pos_1f1ad8(s32 src, s32 dst, s32 t) {\n    if (t >= 3) {"),
        ("neg_b5_skip", "    if (*reinterpret_cast<const s32*>(r5 + 0x3FCu) >= 4) {\n        ui_func_002bf460(2u, 0x24u, 0xB5u, bx, by, 0x97u);", "    if (*reinterpret_cast<const s32*>(r5 + 0x3FCu) > 4) {\n        ui_func_002bf460(2u, 0x24u, 0xB5u, bx, by, 0x97u);"),
        ("neg_loop8_bound", "    for (s32 i = 0; i < 8; ++i) {", "    for (s32 i = 0; i < 7; ++i) {"),
        ("neg_kind6_check", "    const u32 spr = (kind == 1 || kind == 2 || kind == 6) ? 0xC3u : 0xC2u;", "    const u32 spr = (kind == 1 || kind == 2) ? 0xC3u : 0xC2u;"),
        ("neg_final_color", "    const u32 color2 = (nz2 != 0) ? 0x008400FFu : 0xFFFFFFFFu;", "    const u32 color2 = (nz2 != 0) ? 0x008400FFu : 0xFFu;"),
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
