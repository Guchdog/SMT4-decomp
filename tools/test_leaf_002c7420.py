#!/usr/bin/env python3
"""Differential Unicorn test for ui_func_002c7420 (0x002c7420, 1304 B)."""

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
    UC_ARM_REG_S0,
    UC_ARM_REG_SP,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x002C7420
FUNC_SIZE = 1304
FUNC_NAME = "ui_func_002c7420"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

SELF_ADDR = 0x00600000
R6_ADDR = 0x00601000
OBJS_ADDR = 0x00602000
ITEMS_ADDR = 0x00603000
G_4EA81C = 0x004EA81C
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x0024FAA4: "func_0024faa4",
    0x0024FA94: "func_0024fa94",
    0x002A2F1C: "ui_func_002a2f1c",
    0x002B2CEC: "ui_func_002b2cec",
    0x002A399C: "engine_func_002a399c",
    0x002A3D50: "engine_func_002a3d50",
    0x00281E20: "ui_func_00281e20",
    0x001A839C: "func_001a839c",
    0x0024C5B0: "engine_func_0024c5b0",
    0x0024C584: "engine_func_0024c584",
    0x00250420: "engine_func_00250420",
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
        if ((top & 0x0E) == 0x0A and top < 0xF0) or top in (0xFA, 0xFB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x800000:
                imm24 -= 0x1000000
            pc = FUNC_ADDR + off + 8
            target = pc + (imm24 << 2)
            if target in CALLEES:
                stub = STUB_BY_NAME[CALLEES[target]]
                new_imm = ((stub - pc) >> 2) & 0x00FFFFFF
                op = 0xEB000000 if top in (0xFA, 0xFB) else (insn & 0xFF000000)
                struct.pack_into("<I", code_bytes, base + off, op | new_imm)


def run_case(
    code_bytes: bytes,
    rodata_blobs: list[tuple[int, bytes]],
    entry_addr: int,
    case: dict,
) -> list[tuple]:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STUB_BASE - 0x1000, 0x4000)
    uc.mem_map(RODATA_BASE, 0x20000)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(SELF_ADDR, 0x10000)
    uc.mem_map(HALT_ADDR & ~0xFFF, 0x2000)

    uc.mem_write(CODE_BASE, code_bytes)
    for addr, blob in rodata_blobs:
        uc.mem_write(addr, blob)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

    self_buf = bytearray(0x60)
    struct.pack_into("<H", self_buf, 0x0C, case["kind"])
    struct.pack_into("<III", self_buf, 0x34, OBJS_ADDR, 0, OBJS_ADDR)
    struct.pack_into("<I", self_buf, 0x4C, R6_ADDR)
    uc.mem_write(SELF_ADDR, bytes(self_buf))

    count = case.get("count", 3)
    r6_buf = bytearray(0x20)
    struct.pack_into("<iII", r6_buf, 8, count, 1 if case.get("has_xform", False) else 0, 0)
    struct.pack_into("<I", r6_buf, 0x18, ITEMS_ADDR)
    uc.mem_write(R6_ADDR, bytes(r6_buf))

    uc.mem_write(OBJS_ADDR, struct.pack("<3I", 0x10001, 0x10002, 0x10003))

    items_buf = bytearray(0x28 * 3)
    states = [0, 1, -1]
    for i in range(3):
        off = i * 0x28
        struct.pack_into("<ffffif", items_buf, off, 1.0 + i, 2.0 + i, 3.0 + i, 1.0, states[i], 0.5 * (i + 1))
    uc.mem_write(ITEMS_ADDR, bytes(items_buf))

    mat = [
        2.0, 0.0, 0.0, 0.0,
        0.0, 3.0, 0.0, 0.0,
        0.0, 0.0, 4.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]
    uc.mem_write(G_4EA81C + 0x140, struct.pack("<16f", *mat))

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
        if name == "func_0024faa4":
            trace.append((name, r0))
            u.mem_write(r1, struct.pack("<4f", 1.0, 2.0, 3.0, 4.0))
        elif name == "func_0024fa94":
            trace.append((name, r0))
            u.mem_write(r1, struct.pack("<4f", 10.0, 20.0, 30.0, 1.0))
        elif name == "ui_func_002a2f1c":
            v = struct.unpack_from("<4f", u.mem_read(r0, 16))
            trace.append((name, v))
        elif name in ("ui_func_002b2cec", "func_001a839c", "ui_func_00281e20", "engine_func_00250420"):
            trace.append((name, r0))
        elif name in ("engine_func_002a399c", "engine_func_0024c5b0"):
            trace.append((name, r0, u.reg_read(UC_ARM_REG_S0)))
        elif name in ("engine_func_002a3d50", "engine_func_0024c584"):
            pos = struct.unpack_from("<4f", u.mem_read(r1, 16))
            trace.append((name, r0, pos))

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", 2.5))[0])
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(entry_addr, HALT_ADDR, timeout=5_000_000)
    return trace


CASES = [
    {"name": "kind_other", "kind": 4},
    {"name": "kind6_xform_count3", "kind": 6, "has_xform": True, "count": 3},
    {"name": "kind6_noxform_count3", "kind": 6, "has_xform": False, "count": 3},
    {"name": "kind5_xform_count3", "kind": 5, "has_xform": True, "count": 3},
    {"name": "kind5_noxform_count3", "kind": 5, "has_xform": False, "count": 3},
    {"name": "kind6_count0", "kind": 6, "has_xform": True, "count": 0},
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
        ot = run_case(orig_bytes, [], FUNC_ADDR, case)
        ct = run_case(cand_bytes, cand_ro, cand_entry, case)
        if ot != ct:
            print(f"FAIL {case['name']}")
            for i in range(max(len(ot), len(ct))):
                a = ot[i] if i < len(ot) else None
                b = ct[i] if i < len(ct) else None
                if a != b:
                    print(f"  diff[{i}]: {a} != {b}")
                    break
            return 1
        print(f"PASS {case['name']} ({len(ot)} calls)")

    muts = [
        ("neg_kind_check", "    if (kind != 5u && kind != 6u) {", "    if (kind != 6u) {"),
        ("neg_objs_off", "        *reinterpret_cast<u8* const* const*>(self + ((kind == 5u) ? 0x34u : 0x3Cu));", "        *reinterpret_cast<u8* const* const*>(self + ((kind == 5u) ? 0x34u : 0x38u));"),
        ("neg_xform_bit", "    const bool has_xform = (*reinterpret_cast<const u32*>(r6 + 0x0Cu) & 1u) != 0u;", "    const bool has_xform = (*reinterpret_cast<const u32*>(r6 + 0x0Cu) & 2u) != 0u;"),
        ("neg_st_neg", "        if (*reinterpret_cast<const s32*>(items + 0x10u) < 0) {", "        if (*reinterpret_cast<const s32*>(items + 0x10u) <= 0) {"),
        ("neg_scale_mul", "        const f32 s = *reinterpret_cast<const f32*>(items + 0x18u) * scale;", "        const f32 s = *reinterpret_cast<const f32*>(items + 0x18u) + scale;"),
    ]

    for mname, old, new in muts:
        assert old in cpp_text, f"Anchor missing for {mname}"
        mut_cpp = cpp_text.replace(old, new, 1)
        m_bytes, m_ro, m_entry = compile_cand(mut_cpp)
        caught = False
        for case in CASES:
            ores = run_case(orig_bytes, [], FUNC_ADDR, case)
            try:
                mres = run_case(m_bytes, m_ro, m_entry, case)
            except Exception:
                caught = True
                break
            if ores != mres:
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
