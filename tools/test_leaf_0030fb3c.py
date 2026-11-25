#!/usr/bin/env python3
"""Differential Unicorn test for battle_func_0030fb3c (0x0030fb3c, 1420 B)."""

from __future__ import annotations

import math
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
    UC_ARM_REG_S0,
    UC_ARM_REG_S1,
    UC_ARM_REG_SP,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x0030FB3C
FUNC_SIZE = 1360
FUNC_NAME = "battle_func_0030fb3c"

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
    0x002AD6D8: "battle_func_002ad6d8",
    0x002820A4: "ui_func_002820a4",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
NAME_BY_STUB = {v: k for k, v in STUB_BY_NAME.items()}

G_4F4 = 0x004474F4
SELF_ADDR = DATA_BASE + 0x1000
P4F4_ADDR = DATA_BASE + 0x2000


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
    is_orig: bool,
    code_bytes: bytes,
    rodata_blobs: list[tuple[int, bytes]],
    entry: int,
    lut_bytes: bytes,
    kind: int,
    mode: int,
    ang_deg: float,
    hw: float,
    hh: float,
) -> tuple[list, list[float]]:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, code_bytes)
    if not is_orig:
        uc.mem_write(0x00407FC0, lut_bytes)

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

    uc.mem_write(G_4F4, struct.pack("<I", P4F4_ADDR))
    uc.mem_write(P4F4_ADDR + 0x4C, struct.pack("<f", 35.0))
    uc.mem_write(P4F4_ADDR + 0x54, struct.pack("<f", 85.0))

    uc.mem_write(SELF_ADDR, b"\x00" * 0x160)
    uc.mem_write(SELF_ADDR + 0x10, struct.pack("<I", kind))
    uc.mem_write(SELF_ADDR + 0x68, struct.pack("<fff", 10.0, 20.0, 30.0))
    uc.mem_write(SELF_ADDR + 0x74, struct.pack("<f", ang_deg))

    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_R1, mode)
    uc.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", hw))[0])
    uc.reg_write(UC_ARM_REG_S1, struct.unpack("<I", struct.pack("<f", hh))[0])
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)

    trace: list = []

    def hook(uc_inst, address, size, user_data):
        name = NAME_BY_STUB.get(address)
        if name is None:
            return
        if name == "ui_func_002820a4":
            dx = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S0)))[0]
            dz = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S1)))[0]
            ret = math.atan2(dx, dz)
            uc_inst.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", ret))[0])
            trace.append((name, round(dx, 4), round(dz, 4)))
        elif name == "battle_func_002ad6d8":
            a0 = uc_inst.reg_read(UC_ARM_REG_R0)
            a1 = uc_inst.reg_read(UC_ARM_REG_R1)
            a2 = uc_inst.reg_read(UC_ARM_REG_R2)
            m = struct.unpack("<12f", uc_inst.mem_read(a1, 48))
            v = struct.unpack("<3f", uc_inst.mem_read(a2, 12))
            out = (
                m[0] * v[0] + m[1] * v[1] + m[2] * v[2],
                m[4] * v[0] + m[5] * v[1] + m[6] * v[2],
                m[8] * v[0] + m[9] * v[1] + m[10] * v[2],
            )
            uc_inst.mem_write(a0, struct.pack("<3f", *out))
            trace.append((name, tuple(round(x, 4) for x in v)))

    uc.hook_add(UC_HOOK_CODE, hook, begin=STUB_BASE, end=STUB_BASE + 0x1000)
    uc.emu_start(entry, HALT_ADDR, timeout=5_000_000, count=200_000)

    out_floats = [round(x, 4) for x in struct.unpack("<24f", uc.mem_read(SELF_ADDR + 0xF0, 96))]
    return trace, out_floats


def make_cases() -> list[tuple[str, tuple[int, int, float, float, float]]]:
    return [
        ("kind0_mode0", (0, 0, 0.0, 4.0, 2.5)),
        ("kind0_mode1", (0, 1, 0.0, 4.0, 2.5)),
        ("kind1_pos_mode0", (1, 0, 45.0, 3.0, 5.0)),
        ("kind1_neg_mode1", (1, 1, -135.0, 3.0, 5.0)),
        ("kind1_wrap_large", (1, 0, 100000.0, 2.0, 1.0)),
        ("kind2_noop", (2, 0, 45.0, 3.0, 5.0)),
    ]


def main() -> int:
    raw = bytearray(CODE_BIN.read_bytes())
    lut_bytes = bytes(raw[0x00407FC0 - CODE_BASE : 0x00407FC0 - CODE_BASE + 256 * 16])
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
        o_res = run_side(True, orig_code, [], FUNC_ADDR, lut_bytes, *params)
        c_res = run_side(False, cand_code, rodata_blobs, cand_entry, lut_bytes, *params)
        if o_res != c_res:
            print(f"FAIL {name}:\n  orig={o_res}\n  cand={c_res}")
            return 1
        print(f"PASS {name}")

    # 5 negative controls
    src_text = SRC_CPP.read_text(encoding="utf-8")
    mutations = [
        ("neg_kind_guard", "if (kind != 0u && kind != 1u)", "if (kind != 0u)"),
        ("neg_kind1_branch", "if (kind == 1u) {\n        ang_y =", "if (kind == 2u) {\n        ang_y ="),
        ("neg_neg_sin", "out_s = neg_sin ? -s : s;", "out_s = s;"),
        ("neg_mode_1", "u32 dst_off = (mode == 1u) ? 0xF0u : 0x120u;", "u32 dst_off = 0x120u;"),
        ("neg_offset_ox", "corners[i][0] += ox;", "corners[i][0] += 0.0f;"),
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
            o_res = run_side(True, orig_code, [], FUNC_ADDR, lut_bytes, *params)
            m_res = run_side(False, m_code, m_ro, m_entry, lut_bytes, *params)
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
