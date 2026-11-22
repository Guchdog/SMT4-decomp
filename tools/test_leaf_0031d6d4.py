#!/usr/bin/env python3
"""Differential Unicorn test for script_vm_func_0031d6d4 (0x0031d6d4, 1400 B)."""

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

FUNC_ADDR = 0x0031D6D4
FUNC_SIZE = 1400
FUNC_NAME = "script_vm_func_0031d6d4"

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
    0x00297674: "script_vm_func_00297674",
    0x0027FD08: "script_vm_func_0027fd08",
    0x0028550C: "script_vm_func_0028550c",
    0x002766CC: "script_vm_func_002766cc",
    0x002735C8: "script_vm_func_002735c8",
    0x0026FBC0: "script_vm_func_0026fbc0",
    0x002760BC: "script_vm_func_002760bc",
    0x002706E4: "script_vm_func_002706e4",
    0x002BF9E8: "script_vm_func_002bf9e8",
    0x002857E4: "script_vm_func_002857e4",
    0x0027DA20: "script_vm_func_0027da20",
    0x0027D9B8: "script_vm_func_0027d9b8",
    0x0027D6E4: "script_vm_func_0027d6e4",
    0x002766F0: "script_vm_func_002766f0",
    0x00276BC0: "script_vm_func_00276bc0",
    0x00276C24: "script_vm_func_00276c24",
    0x00276088: "script_vm_func_00276088",
    0x0027FE84: "script_vm_func_0027fe84",
    0x00273AB0: "script_vm_func_00273ab0",
    0x00273DE8: "script_vm_func_00273de8",
    0x0027D35C: "script_vm_func_0027d35c",
    0x002C2BD0: "script_vm_func_002c2bd0",
    0x002C2BA4: "script_vm_func_002c2ba4",
    0x00271280: "script_vm_func_00271280",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
NAME_BY_STUB = {v: k for k, v in STUB_BY_NAME.items()}

G_S = 0x0049F91C
G_FD14 = 0x0049FD14
G_E28 = 0x00447E28
G_4F4 = 0x004474F4
G_E88 = 0x00447E88
G_FC8 = 0x00432FC8

R4_ADDR = DATA_BASE + 0x1000
S4F4_ADDR = DATA_BASE + 0x1200
SE88_ADDR = DATA_BASE + 0x1400
SFC8_ADDR = DATA_BASE + 0x1600
REC_ADDR = DATA_BASE + 0x1800


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
    cfg: dict,
) -> tuple[list, list[bytes]]:
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

    # Initialize globals
    uc.mem_write(G_S, b"\x00" * 0x260)
    uc.mem_write(G_E28, struct.pack("<I", R4_ADDR))
    uc.mem_write(G_4F4, struct.pack("<I", S4F4_ADDR))
    uc.mem_write(G_E88, struct.pack("<I", SE88_ADDR))
    uc.mem_write(G_FC8, struct.pack("<I", SFC8_ADDR))

    for off, val in cfg.get("s_bytes", {}).items():
        uc.mem_write(G_S + off, bytes([val]))
    for off, val in cfg.get("s_u32", {}).items():
        uc.mem_write(G_S + off, struct.pack("<i", val))
    fd14 = cfg.get("fd14", [-1, 0, 0])
    uc.mem_write(G_FD14, struct.pack("<iii", *fd14))
    for off, val in cfg.get("r4_u32", {}).items():
        uc.mem_write(R4_ADDR + off, struct.pack("<I", val))
    uc.mem_write(SFC8_ADDR + 0xC0, bytes([cfg.get("fc8_c0", 0)]))
    uc.mem_write(SE88_ADDR + 0x4C, struct.pack("<f", 5.5))
    uc.mem_write(REC_ADDR + 4, struct.pack("<hhhh", 10, 20, 30, 40))

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
        a1 = uc_inst.reg_read(UC_ARM_REG_R1)
        a2 = uc_inst.reg_read(UC_ARM_REG_R2)
        a3 = uc_inst.reg_read(UC_ARM_REG_R3)

        if name == "script_vm_func_00297674":
            ret = cfg.get("ret_297674", 0)
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, ret))
        elif name == "script_vm_func_0028550c":
            s0 = u32(cur_sp)
            s1 = u32(cur_sp + 4)
            trace.append((name, a0, a1, a2, a3, s0, s1))
        elif name == "script_vm_func_0026fbc0":
            ret = cfg.get("ret_26fbc0", 0)
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, ret))
        elif name == "script_vm_func_002857e4":
            ret = cfg.get("ret_2857e4", 0)
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, ret))
        elif name == "script_vm_func_0027da20":
            ret = cfg.get("ret_27da20", -1)
            uc_inst.reg_write(UC_ARM_REG_R0, ret & 0xFFFFFFFF)
            trace.append((name, a0, a1, a2, ret))
        elif name == "script_vm_func_0027d9b8":
            uc_inst.reg_write(UC_ARM_REG_R0, REC_ADDR)
            trace.append((name, a0))
        elif name == "script_vm_func_0027d6e4":
            s0 = uc_inst.reg_read(UC_ARM_REG_S0)
            fv = round(struct.unpack("<f", struct.pack("<I", s0))[0], 3)
            trace.append((name, a0, a1, a2, fv))
        elif name == "script_vm_func_002c2bd0":
            ret = cfg.get("ret_2c2bd0", {}).get(a0, 0)
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, a0, ret))
        elif name in (
            "script_vm_func_0027fd08",
            "script_vm_func_002766cc",
            "script_vm_func_002735c8",
            "script_vm_func_002bf9e8",
            "script_vm_func_00276bc0",
            "script_vm_func_0027fe84",
            "script_vm_func_00273ab0",
            "script_vm_func_00271280",
        ):
            trace.append((name, a0))
        elif name in ("script_vm_func_002766f0", "script_vm_func_00276c24", "script_vm_func_002c2ba4"):
            trace.append((name, a0, a1, a2))
        else:
            trace.append((name,))

    uc.hook_add(UC_HOOK_CODE, hook, begin=STUB_BASE, end=STUB_BASE + 0x1000)
    uc.emu_start(entry, HALT_ADDR, timeout=5_000_000, count=200_000)

    snaps = [
        bytes(uc.mem_read(G_S, 0x260)),
        bytes(uc.mem_read(G_FD14, 12)),
        bytes(uc.mem_read(R4_ADDR, 0x60)),
        bytes(uc.mem_read(S4F4_ADDR, 0xB0)),
        bytes(uc.mem_read(SE88_ADDR, 0x60)),
        bytes(uc.mem_read(SFC8_ADDR + 0xC0, 4)),
    ]
    return trace, snaps


def make_cases() -> list[tuple[str, dict]]:
    f8_bytes = {0xF8: 1, 0xF9: 2, 0xFA: 3, 0xFB: 4, 0xFC: 5, 0xFD: 6}
    return [
        ("flag_250_ok", {"s_bytes": {**f8_bytes, 0x250: 1}, "ret_297674": 0}),
        ("flag_24d_ok", {"s_bytes": {**f8_bytes, 0x24D: 1}, "ret_297674": 0}),
        ("flag_24e_ok", {"s_bytes": {**f8_bytes, 0x24E: 1}, "ret_297674": 0}),
        ("flag_24e_fail_then_fbc0", {"s_bytes": {**f8_bytes, 0x24E: 1}, "ret_297674": 1, "ret_26fbc0": 1}),
        ("flag_24f_then_s54", {"s_bytes": {0x24F: 1}, "s_u32": {0x54: 1}}),
        ("s50_special_1f_lt63", {"s_bytes": f8_bytes, "s_u32": {0x50: 1, 0x00: 0x23, 0xB4: 5, 0x74: 0xAA}}),
        ("s50_special_19_ge63", {"s_bytes": f8_bytes, "s_u32": {0x50: 1, 0x00: 0x1A, 0xB4: 0x63, 0x74: 0xBB}}),
        ("s50_5_6_lt63", {"s_bytes": f8_bytes, "s_u32": {0x50: 1, 0x00: 5, 0x04: 6, 0xB4: 10, 0x74: 0xCC}}),
        ("s50_other", {"s_bytes": f8_bytes, "s_u32": {0x50: 1, 0x00: 5, 0x04: 7, 0x74: 0xDD}}),
        ("fd14_mismatch", {"fd14": [10, 20, 30], "r4_u32": {0x2C: 11, 0x30: 20}}),
        ("fd14_match_idx_neg1", {
            "fd14": [10, 20, 30],
            "r4_u32": {0x2C: 10, 0x30: 99},
            "ret_2857e4": 20,
            "s_u32": {0x08: 1, 0x0C: 2, 0x10: 3},
            "ret_27da20": -1,
            "ret_2c2bd0": {0: 3, 1: 3},
        }),
        ("fd14_match_idx_0", {
            "fd14": [10, 20, 30],
            "r4_u32": {0x2C: 10, 0x30: 20},
            "s_bytes": {0x228: 1},
            "s_u32": {0x48: 1, 0x08: 4, 0x0C: 5, 0x10: 6},
            "ret_27da20": 0,
            "ret_2c2bd0": {0: 1, 1: 3},
        }),
        ("fd14_neg1_fc8_set", {"fd14": [-1, 0, 0], "fc8_c0": 1}),
        ("fd14_neg1_fc8_clear", {"fd14": [-1, 0, 0], "fc8_c0": 0, "ret_2c2bd0": {0: 3, 1: 3}}),
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
    for name, cfg in cases:
        o_tr, o_sn = run_side(orig_code, [], FUNC_ADDR, cfg)
        c_tr, c_sn = run_side(cand_code, rodata_blobs, cand_entry, cfg)
        if o_tr != c_tr or o_sn != c_sn:
            print(f"FAIL {name}:\n  orig_tr={o_tr}\n  cand_tr={c_tr}")
            return 1
        print(f"PASS {name}")

    # 5 negative controls
    src_text = SRC_CPP.read_text(encoding="utf-8")
    mutations = [
        ("neg_250_guard", "if (s[0x250u] != 0u)", "if (s[0x251u] != 0u)"),
        ("neg_s50_special", "((t - 0x1Fu) <= 4u)", "((t - 0x1Fu) <= 3u)"),
        ("neg_fd14_guard", "if (g_fd14[0] != -1)", "if (g_fd14[0] == -1)"),
        ("neg_idx_check", "if (idx != -1)", "if (idx == -1)"),
        ("neg_fc8_c0", "if (g_fc8[0xC0u] != 0u)", "if (g_fc8[0xC0u] == 0u)"),
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
        for _, cfg in cases:
            o_tr, o_sn = run_side(orig_code, [], FUNC_ADDR, cfg)
            m_tr, m_sn = run_side(m_code, m_ro, m_entry, cfg)
            if o_tr != m_tr or o_sn != m_sn:
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
