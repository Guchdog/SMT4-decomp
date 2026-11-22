#!/usr/bin/env python3
"""Differential Unicorn test for script_vm_func_002a0790 (0x002a0790, 1220 B)."""

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
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_SP,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x002A0790
FUNC_SIZE = 1220
FUNC_NAME = "script_vm_func_002a0790"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

V2_ADDR = 0x00600000
V2_P4_ADDR = 0x00600100
V2_P4C_ADDR = 0x00600200
PARENT5_ADDR = 0x00601000
PARENT6_ADDR = 0x00602000
VEC5_BUF = 0x00610000
VEC6_BUF = 0x00611000
CHILDREN_BASE = 0x00620000
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x00152790: "script_vm_func_00152790",
    0x002A44F8: "script_vm_func_002a44f8",
    0x002A4518: "script_vm_func_002a4518",
    0x002AF604: "engine_func_002af604",
    0x002AF528: "engine_func_002af528",
    0x002A4508: "script_vm_func_002a4508",
    0x002C2B34: "engine_func_002c2b34",
    0x001DB538: "script_vm_func_001db538",
    0x003948D0: "func_003948d0",
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
) -> tuple[int, list[tuple], bytes, bytes, bytes]:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STUB_BASE - 0x1000, 0x4000)
    uc.mem_map(RODATA_BASE, 0x20000)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(V2_ADDR, 0x30000)
    uc.mem_map(HALT_ADDR & ~0xFFF, 0x2000)

    uc.mem_write(CODE_BASE, code_bytes)
    for addr, blob in rodata_blobs:
        uc.mem_write(addr, blob)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

    idx = case["idx"]
    uc.mem_write(V2_ADDR + 4, struct.pack("<I", V2_P4_ADDR))
    uc.mem_write(V2_P4_ADDR + 0x4C, struct.pack("<I", V2_P4C_ADDR))
    uc.mem_write(V2_P4C_ADDR, struct.pack("<I", 0xCAFE1234))

    p5 = bytearray(0x40)
    struct.pack_into("<IIIII", p5, 0x0C, case.get("p5_link", 0), 0x11110005, 0, VEC5_BUF, VEC5_BUF)
    struct.pack_into("<I", p5, 0x20, 0x40000000)
    uc.mem_write(PARENT5_ADDR, bytes(p5))

    p6 = bytearray(0x40)
    struct.pack_into("<IIIII", p6, 0x0C, 0, 0x11110006, 0, VEC6_BUF, VEC6_BUF)
    struct.pack_into("<I", p6, 0x20, 0x40000000)
    uc.mem_write(PARENT6_ADDR, bytes(p6))

    uc.mem_write(0x00464B84 + idx * 4, struct.pack("<I", 0xABCD0000 + idx))
    uc.mem_write(0x004D9880, b"\x00" * 0x2000)

    if case.get("populate", False):
        stride = idx * 0x284
        bases = [
            0x004D9880 + 0x264 + stride,
            0x004D9D88 + 0x264 + stride,
            0x004D9880 + 0xA10 + 0x264 + stride,
            0x004D9D88 + 0xA10 + 0x264 + stride,
        ]
        cid = 0
        for b in bases:
            for i in range(8):
                caddr = CHILDREN_BASE + cid * 0x20
                uc.mem_write(b + i * 4, struct.pack("<I", caddr))
                if case.get("prelinked_id", -1) == cid:
                    uc.mem_write(caddr + 0x0C, struct.pack("<I", 0x9999))
                cid += 1
        qbase = 0x004DACA0 + 4 + idx * 0x14
        for i in range(4):
            caddr = CHILDREN_BASE + cid * 0x20
            uc.mem_write(qbase + i * 4, struct.pack("<I", caddr))
            cid += 1

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

        if name == "script_vm_func_00152790":
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, 0x22220000 + r0)
        elif name == "script_vm_func_002a44f8":
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, V2_ADDR)
        elif name == "script_vm_func_002a4518":
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, PARENT5_ADDR)
        elif name == "script_vm_func_002a4508":
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, PARENT6_ADDR)
        elif name == "engine_func_002af604":
            trace.append((name, r0, r1))
            u.reg_write(UC_ARM_REG_R0, 1 if r1 == CHILDREN_BASE else 0)
        elif name == "engine_func_002af528":
            trace.append((name, r0, r1))
            if case.get("grow_fail", False):
                u.reg_write(UC_ARM_REG_R0, 0)
            else:
                cap_flags = struct.unpack_from("<I", u.mem_read(r0 + 0x0C, 4))[0]
                u.mem_write(r0 + 0x0C, struct.pack("<I", (cap_flags & 0xC0000000) | r1))
                u.reg_write(UC_ARM_REG_R0, 1)
        elif name == "engine_func_002c2b34":
            trace.append((name, r0, r1))
        elif name == "script_vm_func_001db538":
            trace.append((name, r0))
        elif name == "func_003948d0":
            trace.append((name, r0, r1, r2, r3))
            u.reg_write(UC_ARM_REG_R0, 0x77778888)

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.reg_write(UC_ARM_REG_R0, idx)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(entry_addr, HALT_ADDR, timeout=5_000_000)

    return (
        uc.reg_read(UC_ARM_REG_R0),
        trace,
        bytes(uc.mem_read(VEC5_BUF, 0x100)),
        bytes(uc.mem_read(VEC6_BUF, 0x40)),
        bytes(uc.mem_read(CHILDREN_BASE, 36 * 0x20)),
    )


CASES = [
    {"name": "idx0_all_null", "idx": 0, "populate": False},
    {"name": "idx1_attach_all_with_grow", "idx": 1, "populate": True},
    {"name": "idx0_grow_fail", "idx": 0, "populate": True, "grow_fail": True},
    {"name": "idx0_link_and_prelinked", "idx": 0, "populate": True, "p5_link": 0x8888, "prelinked_id": 2},
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
            print(f"  orig ret={hex(ores[0])} len={len(ores[1])}")
            print(f"  cand ret={hex(cres[0])} len={len(cres[1])}")
            return 1
        print(f"PASS {case['name']} ({len(ores[1])} calls)")

    muts = [
        ("neg_stride_a0", "    const u32 stride = static_cast<u32>(idx) * 0x284u;", "    const u32 stride = static_cast<u32>(idx) * 0x280u;"),
        ("neg_loop8_bound", "    for (s16 i = 0; i < 8; ++i) {", "    for (s16 i = 0; i < 7; ++i) {"),
        ("neg_loop4_bound", "    for (s16 i = 0; i < 4; ++i) {", "    for (s16 i = 0; i < 3; ++i) {"),
        ("neg_cap_double", "        const u32 new_cap = (cap != 0u) ? (cap << 1) : 1u;", "        const u32 new_cap = (cap != 0u) ? (cap + 1u) : 1u;"),
        ("neg_tail_off", "    return func_003948d0(v1, v2, 0x004DACE0u + static_cast<u32>(idx) * 0x40u, v3);", "    return func_003948d0(v1, v2, 0x004DACE4u + static_cast<u32>(idx) * 0x40u, v3);"),
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
