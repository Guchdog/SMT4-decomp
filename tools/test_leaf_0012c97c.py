#!/usr/bin/env python3
"""Differential Unicorn test for ui_func_0012c97c (0x0012c97c, 1184 B)."""

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

FUNC_ADDR = 0x0012C97C
FUNC_SIZE = 1184
FUNC_NAME = "ui_func_0012c97c"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

PARENT_ADDR = 0x00600000
DESC_ADDR = 0x00601000
ALLOC_ADDR = 0x00602000
ALLOC_VTBL_ADDR = 0x00602100
VEC_ALLOC_ADDR = 0x00602200
VEC_BUF_OLD = 0x00603000
HEAP_BASE = 0x00610000
OBJ_VTBL_ADDR = 0x00420F90
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x002ACD38: "ui_func_002acd38",
    0x002B5498: "engine_func_002b5498",
    0x002AF604: "engine_func_002af604",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
STUB_ALLOC = STUB_BASE + 0x100
STUB_FREE = STUB_BASE + 0x104
STUB_OBJ_DTOR = STUB_BASE + 0x108
STUB_OBJ_INIT = STUB_BASE + 0x10C
STUB_BY_NAME["vtbl_alloc"] = STUB_ALLOC
STUB_BY_NAME["vtbl_free"] = STUB_FREE
STUB_BY_NAME["obj_dtor"] = STUB_OBJ_DTOR
STUB_BY_NAME["obj_init"] = STUB_OBJ_INIT
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
) -> tuple[int, list[tuple], bytes, bytes]:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STUB_BASE - 0x1000, 0x4000)
    uc.mem_map(RODATA_BASE, 0x20000)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(PARENT_ADDR, 0x20000)
    uc.mem_map(HALT_ADDR & ~0xFFF, 0x2000)

    uc.mem_write(CODE_BASE, code_bytes)
    for addr, blob in rodata_blobs:
        uc.mem_write(addr, blob)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

    obj_vtbl = bytearray(0x40)
    struct.pack_into("<I", obj_vtbl, 0x00, STUB_OBJ_DTOR)
    struct.pack_into("<I", obj_vtbl, 0x24, STUB_OBJ_INIT)
    uc.mem_write(OBJ_VTBL_ADDR, bytes(obj_vtbl))

    uc.mem_write(ALLOC_ADDR, struct.pack("<I", ALLOC_VTBL_ADDR))
    uc.mem_write(VEC_ALLOC_ADDR, struct.pack("<I", ALLOC_VTBL_ADDR))
    uc.mem_write(ALLOC_VTBL_ADDR, struct.pack("<IIII", 0, 0, STUB_ALLOC, STUB_FREE))

    desc = bytearray(0x140)
    struct.pack_into("<I", desc, 0x00, 0x40000006)
    if case.get("c0", False):
        desc[0xC0 : 0xE0] = bytes(0xA0 + i for i in range(0x20))
    if "ext_tag" in case:
        struct.pack_into("<I", desc, 0xBC, 0x40)  # ext at desc + 0xFC
        struct.pack_into("<I", desc, 0xFC, case["ext_tag"])
        desc[0x100] = 1
        for i in range(4, 0x28):
            desc[0xFC + i] = (i + 0x30) & 0xFF
    uc.mem_write(DESC_ADDR, bytes(desc))

    parent_addr = PARENT_ADDR if case.get("has_parent", False) else 0
    if parent_addr:
        pbuf = bytearray(0x40)
        struct.pack_into("<I", pbuf, 0x0C, case.get("p_link", 0))
        struct.pack_into("<I", pbuf, 0x10, 0x778899AA)
        struct.pack_into("<I", pbuf, 0x14, case.get("vec_alloc", VEC_ALLOC_ADDR))
        cnt = case.get("vec_cnt", 0)
        vbegin = VEC_BUF_OLD if cnt > 0 or case.get("has_vec_buf", True) else 0
        vend = vbegin + cnt * 4 if vbegin else 0
        struct.pack_into("<I", pbuf, 0x18, vbegin)
        struct.pack_into("<I", pbuf, 0x1C, vend)
        struct.pack_into("<I", pbuf, 0x20, case.get("cap_flags", 0x40000002))
        uc.mem_write(PARENT_ADDR, bytes(pbuf))
        if vbegin:
            uc.mem_write(vbegin, b"".join(struct.pack("<I", 0xD000 + i) for i in range(4)))

    trace: list[tuple] = []
    heap_ptr = [HEAP_BASE]
    alloc_idx = [0]

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

        if name == "vtbl_alloc":
            alloc_idx[0] += 1
            trace.append((name, r0, r1, r2))
            if case.get("fail_alloc_at", 0) == alloc_idx[0]:
                u.reg_write(UC_ARM_REG_R0, 0)
            else:
                ptr = heap_ptr[0]
                heap_ptr[0] += (r1 + 0x3F) & ~0x3F
                u.mem_write(ptr, b"\x00" * r1)
                u.reg_write(UC_ARM_REG_R0, ptr)
        elif name == "vtbl_free":
            trace.append((name, r0, r1))
        elif name == "ui_func_002acd38":
            src_b = bytes(u.mem_read(r1, r2))
            trace.append((name, r0, r2, src_b))
            u.mem_write(r0, src_b)
        elif name == "engine_func_002b5498":
            trace.append((name, r0, r1, r2, r3))
            u.mem_write(r0 + 4, struct.pack("<I", r1))
            if case.get("obj_has_link", False):
                u.mem_write(r0 + 0x0C, struct.pack("<I", 0xCAFE))
        elif name == "obj_init":
            trace.append((name, r0, r1))
            u.reg_write(UC_ARM_REG_R0, case.get("init_ret", 0) & 0xFFFFFFFF)
        elif name == "obj_dtor":
            trace.append((name, r0))
        elif name == "engine_func_002af604":
            trace.append((name, r0, r1))
            u.reg_write(UC_ARM_REG_R0, case.get("cmp_link_ret", 0))

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_R0, parent_addr)
    uc.reg_write(UC_ARM_REG_R1, DESC_ADDR)
    uc.reg_write(UC_ARM_REG_R2, 0x12345678)
    uc.reg_write(UC_ARM_REG_R3, ALLOC_ADDR)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(entry_addr, HALT_ADDR, timeout=5_000_000)

    ret = u_r0 = uc.reg_read(UC_ARM_REG_R0)
    return (
        u_r0,
        trace,
        bytes(uc.mem_read(PARENT_ADDR, 0x40)) if parent_addr else b"",
        bytes(uc.mem_read(HEAP_BASE, 0x1000)),
    )


CASES = [
    {"name": "basic_no_c0_no_ext"},
    {"name": "with_c0_and_ext_80000000", "c0": True, "ext_tag": 0x80000000},
    {"name": "ext_40000000", "ext_tag": 0x40000000},
    {"name": "ext_20000000", "ext_tag": 0x20000000},
    {"name": "ext_10000000", "ext_tag": 0x10000000},
    {"name": "ext_08000000", "ext_tag": 0x08000000},
    {"name": "ext_04000000", "ext_tag": 0x04000000},
    {"name": "ext_unknown_tag_frees_c0", "c0": True, "ext_tag": 0x00000001},
    {"name": "alloc_c0_fail", "c0": True, "fail_alloc_at": 1},
    {"name": "alloc_ext_fail_frees_c0", "c0": True, "ext_tag": 0x10000000, "fail_alloc_at": 2},
    {"name": "alloc_obj_fail_frees_both", "c0": True, "ext_tag": 0x10000000, "fail_alloc_at": 3},
    {"name": "init_fail_dtor_and_free", "init_ret": -1},
    {"name": "attach_parent_has_room", "has_parent": True, "vec_cnt": 1, "cap_flags": 0x40000002},
    {"name": "attach_parent_grow_vec", "has_parent": True, "vec_cnt": 1, "cap_flags": 0x40000001},
    {"name": "attach_parent_grow_from_zero", "has_parent": True, "vec_cnt": 0, "has_vec_buf": False, "cap_flags": 0x40000000},
    {"name": "attach_parent_bad_flags", "has_parent": True, "vec_cnt": 1, "cap_flags": 0x80000001},
    {"name": "attach_parent_link_match", "has_parent": True, "p_link": 0x9999, "cmp_link_ret": 1},
    {"name": "attach_obj_already_linked", "has_parent": True, "obj_has_link": True},
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
            print(f"  orig ret={hex(ores[0])} trace={ores[1]}")
            print(f"  cand ret={hex(cres[0])} trace={cres[1]}")
            return 1
    print(f"PASS {len(CASES)} cases")

    muts = [
        (
            "neg_c0_size",
            "        block_c0 = vtbl_alloc_12c97c(alloc, 0x20u, 4u);",
            "        block_c0 = vtbl_alloc_12c97c(alloc, 0x1Cu, 4u);",
        ),
        (
            "neg_ext_unknown_skip",
            "        default:\n            return 0u;\n    }\n}\n\ninline void attach_child_12c97c",
            "        default:\n            return 0x10u;\n    }\n}\n\ninline void attach_child_12c97c",
        ),
        (
            "neg_init_sign",
            "    if (reinterpret_cast<InitFn>(obj_vtbl[9])(obj, alloc) < 0) {",
            "    if (reinterpret_cast<InitFn>(obj_vtbl[9])(obj, alloc) <= 0) {",
        ),
        (
            "neg_vec_align",
            "                    vtbl_alloc_12c97c(vec_alloc, static_cast<u32>(new_cap) * 4u, 0x20u));",
            "                    vtbl_alloc_12c97c(vec_alloc, static_cast<u32>(new_cap) * 4u, 4u));",
        ),
        (
            "neg_obj_parent_off",
            "        *reinterpret_cast<u32*>(obj + 0x0Cu) = *reinterpret_cast<const u32*>(parent + 0x10u);",
            "        *reinterpret_cast<u32*>(obj + 0x0Cu) = *reinterpret_cast<const u32*>(parent + 0x14u);",
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
