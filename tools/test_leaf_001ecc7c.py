#!/usr/bin/env python3
"""Differential Unicorn test for ui_func_001ecc7c (0x001ecc7c, 972 B entry in 1256 B chunk)."""

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

FUNC_ADDR = 0x001ECC7C
FUNC_SIZE = 972
FUNC_NAME = "ui_func_001ecc7c"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

R5_ADDR = 0x00600000
G44EA00_OBJ = 0x00601000
GLOBAL_43DC20 = 0x0043DC20
GLOBAL_44EA00 = 0x0044EA00
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x002C3BA8: "ui_func_002c3ba8",
    0x002C5F7C: "ui_func_002c5f7c",
    0x002B217C: "ui_func_002b217c",
    0x002BF460: "ui_func_002bf460",
    0x002C5FA4: "battle_func_002c5fa4",
    0x002BF710: "ui_func_002bf710",
    0x002C1B64: "ui_func_002c1b64",
    0x002C1ABC: "ui_func_002c1abc",
    0x002BF558: "func_002bf558",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
STUB_CB24C = STUB_BASE + 0x100
STUB_CB2AC = STUB_BASE + 0x104
STUB_BY_NAME["cb_24c"] = STUB_CB24C
STUB_BY_NAME["cb_2ac"] = STUB_CB2AC
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
) -> tuple[int, list[tuple], bytes]:
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

    r5_ptr = 0 if case.get("r5_null", False) else R5_ADDR
    uc.mem_write(GLOBAL_43DC20 + 4, struct.pack("<I", r5_ptr))
    if r5_ptr:
        r5_buf = bytearray(0x100)
        struct.pack_into("<II", r5_buf, 8, case.get("r5_8", 1), case.get("r5_c", 0))
        for i in range(5):
            off = i * 20
            struct.pack_into("<ff", r5_buf, off + 0x18, float(10 + i * 5), float(20 + i * 7))
            struct.pack_into("<f", r5_buf, off + 0x7C, float(50 + i * 11))
            struct.pack_into("<f", r5_buf, off + 0x88, float(128 + i * 20))
        uc.mem_write(R5_ADDR, bytes(r5_buf))

    uc.mem_write(GLOBAL_44EA00, struct.pack("<I", G44EA00_OBJ))
    g_buf = bytearray(0x1400)
    struct.pack_into("<III", g_buf, 0x124C, 0, 0, case.get("init_24c", 0x999))
    g_buf[0x124C + 0x18] = case.get("f_24c", 0)
    struct.pack_into("<I", g_buf, 0x124C + 0x1C, STUB_CB24C)
    struct.pack_into("<III", g_buf, 0x12AC, 0, 0, case.get("init_2ac", 0x888))
    g_buf[0x12AC + 0x18] = case.get("f_2ac", 0)
    struct.pack_into("<I", g_buf, 0x12AC + 0x1C, STUB_CB2AC)
    uc.mem_write(G44EA00_OBJ, bytes(g_buf))

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

        if name in ("ui_func_002c3ba8", "ui_func_002c1b64", "ui_func_002c1abc"):
            trace.append((name, r0))
        elif name == "ui_func_002c5f7c":
            trace.append((name, r0, r1))
            u.reg_write(UC_ARM_REG_R0, 0x5000 + r0 * 16 + r1)
        elif name == "battle_func_002c5fa4":
            trace.append((name, r0, r1, r2))
            u.reg_write(UC_ARM_REG_R0, 0x6000 + r1)
        elif name == "ui_func_002b217c":
            s0, s1 = struct.unpack_from("<II", u.mem_read(sp, 8))
            vecs = tuple(struct.unpack_from("<4f", u.mem_read(p, 16)) for p in (r0, r1, r2, r3))
            trace.append((name, vecs, s0, s1))
        elif name in ("ui_func_002bf460", "func_002bf558"):
            s0, s1 = struct.unpack_from("<II", u.mem_read(sp, 8))
            trace.append((name, r0, r1, r2, r3, s0, s1))
        elif name == "ui_func_002bf710":
            trace.append((name, u.reg_read(UC_ARM_REG_S0)))
        elif name in ("cb_24c", "cb_2ac"):
            trace.append((name,))

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(entry_addr, HALT_ADDR, timeout=5_000_000)

    return uc.reg_read(UC_ARM_REG_R0), trace, bytes(uc.mem_read(G44EA00_OBJ + 0x1240, 0xA0))


CASES = [
    {"name": "r5_null", "r5_null": True},
    {"name": "r5_8_zero", "r5_8": 0},
    {"name": "r5_c_is_1", "r5_c": 1, "f_24c": 1},
    {"name": "r5_c_is_0_full_cb", "r5_c": 0, "f_24c": 1, "f_2ac": 1},
    {"name": "r5_c_is_0_nocb", "r5_c": 0, "init_24c": 0x5010, "init_2ac": 0x6001},
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
            for i in range(max(len(ores[1]), len(cres[1]))):
                a = ores[1][i] if i < len(ores[1]) else None
                b = cres[1][i] if i < len(cres[1]) else None
                if a != b:
                    print(f"  diff[{i}]: {a} != {b}")
                    break
            return 1
        print(f"PASS {case['name']} ({len(ores[1])} calls)")

    muts = [
        ("neg_r5_8_check", "    if (r5 == nullptr || *reinterpret_cast<const u32*>(r5 + 8u) == 0u) {", "    if (r5 == nullptr) {"),
        ("neg_r5_c_check", "    if (*reinterpret_cast<const u32*>(r5 + 0x0Cu) == 1u) {", "    if (*reinterpret_cast<const u32*>(r5 + 0x0Cu) == 2u) {"),
        ("neg_loop1_bound", "        const f32 inv255 = static_cast<f32>(0x3B808081u ? 1.0f / 255.0f : 0.0f);\n        for (s32 i = 0; i < 5; ++i) {", "        const f32 inv255 = static_cast<f32>(0x3B808081u ? 1.0f / 255.0f : 0.0f);\n        for (s32 i = 0; i < 4; ++i) {"),
        ("neg_loop2_bound", "        set_state_1ecc7c(*reinterpret_cast<u8* const*>(0x0044EA00u) + 0x12ACu,\n                         battle_func_002c5fa4(6u, 1u, 0u));\n\n        for (s32 i = 0; i < 5; ++i) {", "        set_state_1ecc7c(*reinterpret_cast<u8* const*>(0x0044EA00u) + 0x12ACu,\n                         battle_func_002c5fa4(6u, 1u, 0u));\n\n        for (s32 i = 0; i < 4; ++i) {"),
        ("neg_final_2c5fa4", "        set_state_1ecc7c(*reinterpret_cast<u8* const*>(0x0044EA00u) + 0x12ACu,\n                         battle_func_002c5fa4(6u, 7u, 0u));", "        set_state_1ecc7c(*reinterpret_cast<u8* const*>(0x0044EA00u) + 0x12ACu,\n                         battle_func_002c5fa4(6u, 8u, 0u));"),
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
