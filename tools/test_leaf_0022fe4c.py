#!/usr/bin/env python3
"""Differential Unicorn test for shop_func_0022fe4c (0x0022fe4c, 1404 B)."""

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
    UC_ARM_REG_SP,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x0022FE4C
FUNC_SIZE = 1404
FUNC_NAME = "shop_func_0022fe4c"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

DATA_BASE = 0x00600000
DATA_SIZE = 0x00040000
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x0028EC74: "shop_func_0028ec74",
    0x00230680: "shop_func_00230680",
    0x002338C4: "unite_func_002338c4",
    0x002305C8: "camp_func_002305c8",
    0x0023046C: "shop_func_0023046c",
    0x002337A0: "shop_func_002337a0",
    0x002923D0: "shop_func_002923d0",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
NAME_BY_STUB = {v: k for k, v in STUB_BY_NAME.items()}

ACTIVE_IDS = {
    0x001, 0x03C, 0x03D, 0x0B4, 0x0B5, 0x12C, 0x12D, 0x1A4,
    0x1A5, 0x21C, 0x21D, 0x294, 0x295, 0x30C, 0x30D, 0x33E,
}


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
    next_ro = RODATA_BASE
    for idx, sh in enumerate(sections):
        sname = sec_name(idx)
        if sname.startswith(".rodata"):
            blob = elf[sh[4] : sh[4] + sh[5]]
            rodata_map[idx] = next_ro
            rodata_blobs.append((next_ro, blob))
            next_ro += (len(blob) + 0x1F) & ~0x1F

    for idx, sh in enumerate(sections):
        if sh[1] != 9:
            continue
        if sec_name(sh[7]) != text_name:
            continue
        for pos in range(0, sh[5], 8):
            r_off, r_info = struct.unpack_from("<II", elf, sh[4] + pos)
            r_type = r_info & 0xFF
            sym_idx = r_info >> 8
            sname, sval, sshndx = sym_info(sym_idx)

            is_in_func = func_val <= r_off < func_val + func_size
            if not is_in_func and not (r_type in (28, 29) and sname in STUB_BY_NAME):
                continue

            if sname in STUB_BY_NAME:
                target = STUB_BY_NAME[sname]
            elif sshndx in rodata_map:
                target = rodata_map[sshndx] + sval
            elif sshndx == func_shndx:
                target = CODE_BASE + sval
            else:
                raise RuntimeError(f"Unhandled reloc {sname!r} type={r_type} at 0x{r_off:x}")

            if r_type in (28, 29):
                insn = struct.unpack_from("<I", text_bytes, r_off)[0]
                rel = ((target - (CODE_BASE + r_off + 8)) >> 2) & 0x00FFFFFF
                struct.pack_into("<I", text_bytes, r_off, (insn & 0xFF000000) | rel)
            elif r_type == 2:
                addend = struct.unpack_from("<i", text_bytes, r_off)[0]
                struct.pack_into("<I", text_bytes, r_off, target + addend)
            elif r_type == 43:
                insn = struct.unpack_from("<I", text_bytes, r_off)[0]
                imm16 = target & 0xFFFF
                struct.pack_into("<I", text_bytes, r_off, (insn & 0xFFF0F000) | ((imm16 >> 12) << 16) | (imm16 & 0xFFF))
            elif r_type == 44:
                insn = struct.unpack_from("<I", text_bytes, r_off)[0]
                imm16 = (target >> 16) & 0xFFFF
                struct.pack_into("<I", text_bytes, r_off, (insn & 0xFFF0F000) | ((imm16 >> 12) << 16) | (imm16 & 0xFFF))
            else:
                raise RuntimeError(f"Unsupported r_type={r_type} for {sname!r}")

    return bytes(text_bytes), rodata_blobs, CODE_BASE + func_val


def patch_orig_bl(code: bytearray) -> None:
    for off in range(FUNC_ADDR - CODE_BASE, FUNC_ADDR - CODE_BASE + FUNC_SIZE, 4):
        insn = struct.unpack_from("<I", code, off)[0]
        top = (insn >> 24) & 0xFF
        if ((top & 0x0E) == 0x0A and top < 0xF0) or top in (0xFA, 0xFB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = CODE_BASE + off + 8
            target = pc + (imm24 << 2)
            if target in CALLEES:
                stub = STUB_BY_NAME[CALLEES[target]]
                rel = ((stub - pc) >> 2) & 0x00FFFFFF
                op = 0xEB000000 if top in (0xFA, 0xFB) else (insn & 0xFF000000)
                struct.pack_into("<I", code, off, op | rel)


def run_side(
    code_bytes: bytes,
    rodata_blobs: list[tuple[int, bytes]],
    entry: int,
    mode: int,
    idx_860: int,
    item_idx: int,
    a1: int,
) -> tuple[int, list, int]:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, code_bytes)

    uc.mem_map(STUB_BASE, 0x2000)
    for addr in NAME_BY_STUB:
        uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))

    uc.mem_map(RODATA_BASE, 0x20000)
    for addr, blob in rodata_blobs:
        uc.mem_write(addr, blob)

    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(0x006F0000, 0x10000)
    uc.mem_write(HALT_ADDR, struct.pack("<I", 0xE320F000))

    self_addr = DATA_BASE
    uc.mem_write(self_addr + 0x860, struct.pack("<I", idx_860))
    uc.mem_write(self_addr + 0x864, struct.pack("<I", mode))
    uc.mem_write(self_addr + 0x9CA4, struct.pack("<H", 0xBEEF))
    uc.mem_write(self_addr + 0xC94 + idx_860 * 0x1002 + item_idx * 4, struct.pack("<H", 0x4321))

    uc.reg_write(UC_ARM_REG_R0, self_addr)
    uc.reg_write(UC_ARM_REG_R1, a1)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)

    trace: list = []

    def u32(a: int) -> int:
        return struct.unpack("<I", uc.mem_read(a, 4))[0]

    def hook(uc_inst, address, size, user_data):
        name = NAME_BY_STUB.get(address)
        if name is None:
            return
        cur_sp = uc_inst.reg_read(UC_ARM_REG_SP)
        a0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(UC_ARM_REG_R2)
        r3 = uc_inst.reg_read(UC_ARM_REG_R3)

        if name == "shop_func_0028ec74":
            ret = 1 if a0 in ACTIVE_IDS else 0
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
        elif name == "shop_func_00230680":
            s0 = u32(cur_sp)
            cnt = struct.unpack("<H", uc_inst.mem_read(a0 + 0x1000, 2))[0] + 1
            uc_inst.mem_write(a0 + 0x1000, struct.pack("<H", cnt))
            trace.append((name, a0 - self_addr, r1, r2, r3, s0))
        elif name == "unite_func_002338c4":
            s0 = u32(cur_sp)
            s1 = u32(cur_sp + 4)
            trace.append((name, a0 - self_addr, r1, r2, r3, s0, s1))
        elif name == "camp_func_002305c8":
            trace.append((name, a0 - self_addr, r1))
        elif name == "shop_func_0023046c":
            trace.append((name, a0 - self_addr, r1))
        elif name == "shop_func_002337a0":
            uc_inst.reg_write(UC_ARM_REG_R0, item_idx)
            trace.append((name, a0 - self_addr))
        elif name == "shop_func_002923d0":
            uc_inst.reg_write(UC_ARM_REG_R0, 0x77)
            trace.append((name, a0))

    uc.hook_add(UC_HOOK_CODE, hook, begin=STUB_BASE, end=STUB_BASE + 0x1000)
    uc.emu_start(entry, HALT_ADDR, timeout=5_000_000, count=500_000)

    c2d = uc.mem_read(self_addr + 0xC2D, 1)[0]
    return uc.reg_read(UC_ARM_REG_R0), trace, c2d


def make_cases() -> list[tuple[str, tuple[int, int, int, int]]]:
    return [
        ("mode_0", (0, 0, 2, 0xAA)),
        ("mode_1", (1, 1, 3, 0xBB)),
        ("mode_2", (2, 2, 1, 0xCC)),
        ("mode_3", (3, 1, 0, 0xDD)),
        ("mode_4_default", (4, 0, 4, 0xEE)),
    ]


def main() -> int:
    raw = bytearray(CODE_BIN.read_bytes())
    patch_orig_bl(raw)
    orig_code = bytes(raw)

    with tempfile.TemporaryDirectory() as tmpdir:
        obj_path = Path(tmpdir) / "leaf_batch45_c.o"
        res = compile_tu_armv6k(SRC_CPP, obj_path)
        if res.returncode != 0:
            print(f"COMPILE ERROR:\n{res.stderr}")
            return 1
        cand_code, rodata_blobs, cand_entry = patch_cand_elf(obj_path)

    cases = make_cases()
    for name, params in cases:
        o_res = run_side(orig_code, [], FUNC_ADDR, *params)
        c_res = run_side(cand_code, rodata_blobs, cand_entry, *params)
        if o_res != c_res:
            print(f"FAIL {name}:\n  orig={o_res}\n  cand={c_res}")
            return 1
        print(f"PASS {name}")

    # 5 negative controls
    src_text = SRC_CPP.read_text(encoding="utf-8")
    mutations = [
        ("neg_mode_0", "if (mode == 0u) {\n        for (const auto& r : kMode0)", "if (mode == 9u) {\n        for (const auto& r : kMode0)"),
        ("neg_mode_1", "else if (mode == 1u) {\n        for (const auto& r : kMode1)", "else if (mode == 9u) {\n        for (const auto& r : kMode1)"),
        ("neg_mode_2", "else if (mode == 2u) {\n        for (const auto& r : kMode2)", "else if (mode == 9u) {\n        for (const auto& r : kMode2)"),
        ("neg_mode_3", "else if (mode == 3u) {\n        for (const auto& r : kMode3)", "else if (mode == 9u) {\n        for (const auto& r : kMode3)"),
        ("neg_c2d", "self[0xC2Du] = 1u;", "self[0xC2Du] = 0u;"),
    ]
    for mname, old, new in mutations:
        assert old in src_text, f"Mutation target not found: {old}"
        mut_src = src_text.replace(old, new, 1)
        with tempfile.TemporaryDirectory() as tmpdir:
            mut_cpp = Path(tmpdir) / "mut.cpp"
            mut_obj = Path(tmpdir) / "mut.o"
            mut_cpp.write_text(mut_src, encoding="utf-8")
            res = compile_tu_armv6k(mut_cpp, mut_obj)
            if res.returncode != 0:
                print(f"MUT COMPILE ERR {mname}: {res.stderr}")
                return 1
            m_code, m_ro, m_entry = patch_cand_elf(mut_obj)
        detected = False
        for _, params in cases:
            o_res = run_side(orig_code, [], FUNC_ADDR, *params)
            m_res = run_side(m_code, m_ro, m_entry, *params)
            if o_res != m_res:
                detected = True
                break
        if not detected:
            print(f"FAIL negative control {mname} was not detected!")
            return 1
        print(f"PASS {mname} (detected)")

    print(f"ALL PASS: {len(cases)} cases + {len(mutations)} negative controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
