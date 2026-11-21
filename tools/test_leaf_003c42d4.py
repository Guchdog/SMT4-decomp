#!/usr/bin/env python3
"""Differential Unicorn test for battle_func_003c42d4 (0x003c42d4, 1144 B)."""

from __future__ import annotations

import struct
import sys
import tempfile
from pathlib import Path

from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_ARM, Uc
from unicorn.arm_const import (
    UC_ARM_REG_LR,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_SP,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x003C42D4
FUNC_SIZE = 1144
FUNC_NAME = "battle_func_003c42d4"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

CTX_ADDR = 0x00600000
SUB_ADDR = 0x00600100
VAL_PTR_ADDR = 0x00600200
CAMP_PTR_ADDR = 0x00600300
TARGET_ADDR = 0x00610000
GLOBAL_27_ADDR = 0x00439AD4
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x002564CC: "battle_func_002564cc",
    0x0022A5D8: "battle_func_0022a5d8",
    0x0022A5F8: "battle_func_0022a5f8",
    0x002A8A08: "camp_func_002a8a08",
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
            if not (func_val <= r_offset < func_val + func_size):
                continue
            r_type = r_info & 0xFF
            r_sym = r_info >> 8
            sname, sval, sshndx = sym_info(r_sym)
            if r_type in (28, 29):
                target = STUB_BY_NAME[sname]
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


def run_case(
    code_bytes: bytes,
    rodata_blobs: list[tuple[int, bytes]],
    entry_addr: int,
    cmd: int,
    flag_val: int,
    val_u32: int,
    init_bits: int,
) -> tuple[list[tuple], bytes, int, int]:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STUB_BASE - 0x1000, 0x4000)
    uc.mem_map(RODATA_BASE, 0x20000)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(CTX_ADDR, 0x20000)
    uc.mem_map(HALT_ADDR & ~0xFFF, 0x2000)

    uc.mem_write(CODE_BASE, code_bytes)
    for addr, blob in rodata_blobs:
        uc.mem_write(addr, blob)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

    uc.mem_write(CTX_ADDR + 0x10, struct.pack("<I", SUB_ADDR))
    uc.mem_write(VAL_PTR_ADDR, struct.pack("<I", val_u32))
    uc.mem_write(CAMP_PTR_ADDR, struct.pack("<I", 0x11112222))
    uc.mem_write(GLOBAL_27_ADDR, struct.pack("<I", 0x33334444))

    target_init = bytearray(0x5000)
    struct.pack_into("<II", target_init, 0x44A8, init_bits, init_bits)
    uc.mem_write(TARGET_ADDR, bytes(target_init))

    trace: list[tuple] = []

    def on_code(u: Uc, addr: int, _size: int, _user: object) -> None:
        if addr == HALT_ADDR:
            u.emu_stop()
            return
        name = NAME_BY_STUB.get(addr)
        if name is None:
            return
        r0 = u.reg_read(UC_ARM_REG_R0)
        if name == "battle_func_002564cc":
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, cmd & 0xFFFFFFFF)
        elif name == "battle_func_0022a5d8":
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, flag_val & 0xFFFFFFFF)
        elif name == "battle_func_0022a5f8":
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, VAL_PTR_ADDR)
        elif name == "camp_func_002a8a08":
            trace.append((name,))
            u.reg_write(UC_ARM_REG_R0, CAMP_PTR_ADDR)

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.reg_write(UC_ARM_REG_R0, CTX_ADDR)
    uc.reg_write(UC_ARM_REG_R1, TARGET_ADDR)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(entry_addr, HALT_ADDR, timeout=5_000_000)

    camp_val = struct.unpack_from("<I", uc.mem_read(CAMP_PTR_ADDR, 4))[0]
    g27_val = struct.unpack_from("<I", uc.mem_read(GLOBAL_27_ADDR, 4))[0]
    return trace, bytes(uc.mem_read(TARGET_ADDR, 0x5000)), camp_val, g27_val


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


def build_cases() -> list[tuple[str, int, int, int, int]]:
    cases: list[tuple[str, int, int, int, int]] = []
    value_cmds = {4, 11, 12, 24, 26, 27}
    for cmd in range(29):
        if cmd in value_cmds:
            cases.append((f"cmd_{cmd}_val", cmd, 0, 0xA5A50000 + cmd, 0xFFFFFFFF))
        else:
            cases.append((f"cmd_{cmd}_set", cmd, 1, 0, 0x00000000))
            cases.append((f"cmd_{cmd}_clr", cmd, 0, 0, 0xFFFFFFFF))
    cases.append(("cmd_29_oob", 29, 1, 0xDEAD, 0x12345678))
    cases.append(("cmd_max_oob", 0xFFFFFFFF, 1, 0xDEAD, 0x12345678))
    return cases


def main() -> int:
    orig_mem = bytearray(CODE_SIZE)
    raw_code = CODE_BIN.read_bytes()
    orig_mem[0 : len(raw_code)] = raw_code
    patch_orig_bl(orig_mem)
    orig_bytes = bytes(orig_mem)

    cpp_text = SRC_CPP.read_text(encoding="utf-8")
    cand_bytes, cand_ro, cand_entry = compile_cand(cpp_text)
    cases = build_cases()

    for cname, cmd, fval, uval, init_bits in cases:
        ot, otgt, oc, og = run_case(orig_bytes, [], FUNC_ADDR, cmd, fval, uval, init_bits)
        ct, ctgt, cc, cg = run_case(cand_bytes, cand_ro, cand_entry, cmd, fval, uval, init_bits)
        if (ot, otgt, oc, og) != (ct, ctgt, cc, cg):
            print(f"FAIL {cname}")
            return 1
    print(f"PASS {len(cases)} cases (all 29 commands set/clear/value + 2 OOB)")

    muts = [
        ("neg_oob_28", "    if (cmd >= 29u) {", "    if (cmd >= 28u) {"),
        ("neg_bit_clear_skip", "                *flags &= ~bc.mask;", "                *flags |= bc.mask;"),
        ("neg_wrong_offset_44ac", "{0x44ACu, 0x00000040u},", "{0x44A8u, 0x00000040u},"),
        (
            "neg_wrong_value_offset",
            "*reinterpret_cast<u32*>(target + 0x4A50u) = *battle_func_0022a5f8(sub, cmd);",
            "*reinterpret_cast<u32*>(target + 0x4A54u) = *battle_func_0022a5f8(sub, cmd);",
        ),
        (
            "neg_case27_global",
            "*reinterpret_cast<u32*>(0x00439AD4u) = *battle_func_0022a5f8(sub, cmd);",
            "*reinterpret_cast<u32*>(0x00439AD8u) = *battle_func_0022a5f8(sub, cmd);",
        ),
    ]

    for mname, old, new in muts:
        assert old in cpp_text, f"Anchor missing for {mname}"
        mut_cpp = cpp_text.replace(old, new, 1)
        m_bytes, m_ro, m_entry = compile_cand(mut_cpp)
        caught = False
        for _, cmd, fval, uval, init_bits in cases:
            ot, otgt, oc, og = run_case(orig_bytes, [], FUNC_ADDR, cmd, fval, uval, init_bits)
            mt, mtgt, mc, mg = run_case(m_bytes, m_ro, m_entry, cmd, fval, uval, init_bits)
            if (ot, otgt, oc, og) != (mt, mtgt, mc, mg):
                caught = True
                break
        if not caught:
            print(f"FAIL negative control {mname} was not caught!")
            return 1
        print(f"PASS {mname} (caught)")

    print(f"ALL PASS: {len(cases)} cases + {len(muts)} negative controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
