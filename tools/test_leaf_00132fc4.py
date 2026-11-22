#!/usr/bin/env python3
"""Differential Unicorn test for func_00132fc4 (0x00132fc4, 1224 B)."""

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

FUNC_ADDR = 0x00132FC4
FUNC_SIZE = 1224
FUNC_NAME = "func_00132fc4"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

CTX_ADDR = 0x00600000
RT_ADDR = 0x00600100
GPU_ADDR = 0x00601000
COLOR_ADDR = 0x00602000
DEPTH_ADDR = 0x00602100
CMDBUF_ADDR = 0x00603000

G_CMDPTR = 0x004652A0
G_CMDEND = 0x004652A4
G_CTX = 0x004652A8
G_GPU = 0x004655C0
TAIL_SUB_ADDR = 0x001425E8
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x00147994: "func_00147994",
    TAIL_SUB_ADDR: "sub_001425e8",
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


def run_case(
    code_bytes: bytes,
    rodata_blobs: list[tuple[int, bytes]],
    entry_addr: int,
    case: dict,
) -> tuple[list[tuple], bytes, bytes, int]:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STUB_BASE - 0x1000, 0x4000)
    uc.mem_map(RODATA_BASE, 0x20000)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(CTX_ADDR, 0x10000)
    uc.mem_map(HALT_ADDR & ~0xFFF, 0x2000)

    uc.mem_write(CODE_BASE, code_bytes)
    for addr, blob in rodata_blobs:
        uc.mem_write(addr, blob)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(TAIL_SUB_ADDR, struct.pack("<I", 0xE12FFF1E))

    uc.mem_write(G_CTX, struct.pack("<I", CTX_ADDR))
    uc.mem_write(G_GPU, struct.pack("<I", GPU_ADDR))
    cmd_end = CMDBUF_ADDR + case.get("cmd_cap", 0x200)
    uc.mem_write(G_CMDPTR, struct.pack("<II", CMDBUF_ADDR, cmd_end))
    uc.mem_write(CMDBUF_ADDR, b"\x00" * 0x200)

    uc.mem_write(CTX_ADDR + 8, struct.pack("<I", RT_ADDR))

    c_ptr = COLOR_ADDR if case.get("has_color", True) else 0
    d_ptr = (COLOR_ADDR if case.get("same_ptr", False) else DEPTH_ADDR) if case.get("has_depth", True) else 0
    rt_buf = bytearray(0x24)
    struct.pack_into("<II", rt_buf, 0x0C, c_ptr, 0)
    struct.pack_into("<I", rt_buf, 0x1C, d_ptr)
    uc.mem_write(RT_ADDR, bytes(rt_buf))

    if c_ptr:
        cbuf = bytearray(0x40)
        struct.pack_into("<IIIIII", cbuf, 0, case.get("cp", 0x12000000), 0, 0, case.get("cw", 400), case.get("ch", 240), 0)
        struct.pack_into("<II", cbuf, 0x1C, case.get("cfmt", 0), 0x111)
        uc.mem_write(c_ptr, bytes(cbuf))
    if d_ptr and d_ptr != c_ptr:
        dbuf = bytearray(0x40)
        struct.pack_into("<IIIIII", dbuf, 0, case.get("dp", 0x13000000), 0, 0, case.get("dw", 400), case.get("dh", 240), 0)
        struct.pack_into("<I", dbuf, 0x20, 0x222)
        struct.pack_into("<I", dbuf, 0x38, case.get("dfmt", 0x18))
        uc.mem_write(d_ptr, bytes(dbuf))

    gpu = bytearray(0x900)
    struct.pack_into("<III", gpu, 0, 0, case.get("gpu4", 0), case.get("gpu8", 0))
    gpu[0x30] = case.get("gpu30", 0)
    gpu[0x54] = case.get("gpu54", 1)
    gpu[0x648] = case.get("gpu648", 1)
    struct.pack_into("<I", gpu, 0x68C, case.get("old_68c", 0))
    struct.pack_into("<II", gpu, 0x698, case.get("old_w", 0), case.get("old_h", 0))
    struct.pack_into("<II", gpu, 0x80C, case.get("old_dptr", 0), case.get("old_cptr", 0))
    uc.mem_write(GPU_ADDR, bytes(gpu))

    trace: list[tuple] = []

    def on_code(u: Uc, addr: int, _size: int, _user: object) -> None:
        if addr == HALT_ADDR:
            u.emu_stop()
            return
        if addr == TAIL_SUB_ADDR:
            trace.append(("sub_001425e8", u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
            return
        name = NAME_BY_STUB.get(addr)
        if name is None:
            return
        r0 = u.reg_read(UC_ARM_REG_R0)
        r1 = u.reg_read(UC_ARM_REG_R1)
        if name == "func_00147994":
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, (r0 ^ 0x10000) & 0xFFFFFFFF)
        elif name == "sub_001425e8":
            trace.append((name, r0, r1))

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(entry_addr, HALT_ADDR, timeout=5_000_000)

    cmd_ptr = struct.unpack_from("<I", uc.mem_read(G_CMDPTR, 4))[0]
    return trace, bytes(uc.mem_read(GPU_ADDR, 0x900)), bytes(uc.mem_read(CMDBUF_ADDR, 0x200)), cmd_ptr


CASES = [
    {"name": "both_null", "has_color": False, "has_depth": False},
    {"name": "color_zero_ptr", "cp": 0},
    {"name": "color_zero_dim", "cw": 0},
    {"name": "depth_zero_dim", "dh": 0},
    {"name": "dim_mismatch", "dw": 320},
    {"name": "same_color_depth_ptr", "same_ptr": True},
    {"name": "gpu8_bit100_skip", "gpu8": 0x100},
    {"name": "color_only_fmt0", "has_depth": False, "cfmt": 0},
    {"name": "color_only_fmt2", "has_depth": False, "cfmt": 2},
    {"name": "color_only_fmt3", "has_depth": False, "cfmt": 3},
    {"name": "color_only_fmt4", "has_depth": False, "cfmt": 4},
    {"name": "depth_only_16", "has_color": False, "dfmt": 0x10, "old_68c": 3},
    {"name": "depth_only_18", "has_color": False, "dfmt": 0x18, "old_68c": 0},
    {"name": "depth_only_20", "has_color": False, "dfmt": 0x20, "old_68c": 0},
    {"name": "both_same_size_gpu4_bit100", "gpu4": 0x100, "old_w": 400, "old_h": 240, "old_cptr": 0x12000000, "old_dptr": 0x13000000},
    {"name": "cmd_buf_full", "cmd_cap": 0},
    {"name": "gpu30_nonzero_skips_tail", "gpu30": 1},
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
            print(f"  orig cmd={hex(ores[3])} trace={ores[0]}")
            print(f"  cand cmd={hex(cres[3])} trace={cres[0]}")
            return 1
    print(f"PASS {len(CASES)} cases")

    muts = [
        ("neg_status_check", "    if (status != 0x8CD5u) {", "    if (status == 0x8CD5u) {"),
        ("neg_color_fmt4", "            case 4u:\n                *reinterpret_cast<u32*>(st4 + 4u) = 4u;", "            case 4u:\n                *reinterpret_cast<u32*>(st4 + 4u) = 5u;"),
        ("neg_depth_bit4", "            if ((new_68c == 0u) != (old_68c == 0u)) {\n                *reinterpret_cast<u32*>(gpu) |= 4u;", "            if ((new_68c == 0u) != (old_68c == 0u)) {\n                *reinterpret_cast<u32*>(gpu) |= 8u;"),
        ("neg_packed_h_minus_1", "        const u32 packed = (w & 0xFFFu) | (((h - 1u) & 0xFFFu) << 12u) | 0x01000000u;", "        const u32 packed = (w & 0xFFFu) | ((h & 0xFFFu) << 12u) | 0x01000000u;"),
        ("neg_tail_flag30", "    if (gpu[0x30u] == 0u) {\n        gpu[0x30u] = 1u;", "    if (gpu[0x30u] == 0u) {\n        gpu[0x30u] = 2u;"),
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
