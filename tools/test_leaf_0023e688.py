#!/usr/bin/env python3
"""Differential Unicorn test for engine_func_0023e688 (0x0023e688, 1268 B)."""

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

FUNC_ADDR = 0x0023E688
FUNC_SIZE = 1268
FUNC_NAME = "engine_func_0023e688"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

MGR_ADDR = 0x00600000
BASE_ADDR = 0x00601000
A1_ADDR = 0x00603000
UNITS_ADDR = 0x00610000
HEAP_ADDR = 0x00620000
QSORT_ADDR = 0x002B7F0A
G_439ACC = 0x00439ACC
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x002934D4: "battle_func_002934d4",
    0x002C684C: "AsdMemory_func_002c684c",
    0x0023EC3C: "script_vm_func_0023ec3c",
    0x00250FB4: "ui_func_00250fb4",
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
            if top in (0xFA, 0xFB):
                h_bit = (insn >> 24) & 1
                target += h_bit * 2
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
) -> tuple[list[tuple], int, list[int]]:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STUB_BASE - 0x1000, 0x4000)
    uc.mem_map(RODATA_BASE, 0x20000)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(MGR_ADDR, 0x30000)
    uc.mem_map(HALT_ADDR & ~0xFFF, 0x2000)

    uc.mem_write(CODE_BASE, code_bytes)
    for addr, blob in rodata_blobs:
        uc.mem_write(addr, blob)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(QSORT_ADDR, struct.pack("<H", 0x4770))

    uc.mem_write(G_439ACC, struct.pack("<ff", 10.0, 20.0))
    uc.mem_write(MGR_ADDR, struct.pack("<I", BASE_ADDR))
    uc.mem_write(BASE_ADDR + 0x1E98, struct.pack("<I", UNITS_ADDR))
    uc.mem_write(A1_ADDR + 0x598, struct.pack("<I", 0xDEADBEEF))

    units_buf = bytearray(0x6D * 0x114)
    start = 4 if case.get("flag", 0) == 0 else 0x43
    n_active = case.get("n_active", 5)
    for i in range(0x6D):
        off = i * 0x114
        struct.pack_into("<I", units_buf, off + 0x5C, 0x9999)
        struct.pack_into("<h", units_buf, off + 0x62, 1000 + i)
        if start <= i < start + n_active:
            flags = 0x83
            if case.get("bit10", False) and i == start:
                flags |= 0x10
            struct.pack_into("<I", units_buf, off + 0x50, flags)
            struct.pack_into("<f", units_buf, off + 0x0C, 20.0 if i == start else 25.0)
            struct.pack_into("<h", units_buf, off + 0x62, 50 + (i - start))
        elif i == 0x6C:
            struct.pack_into("<I", units_buf, off + 0x50, 0x83)
            struct.pack_into("<h", units_buf, off + 0x62, 50)  # alias of start!
    uc.mem_write(UNITS_ADDR, bytes(units_buf))

    trace: list[tuple] = []
    rng_i = [0]

    def on_code(u: Uc, addr: int, _size: int, _user: object) -> None:
        if addr == HALT_ADDR:
            u.emu_stop()
            return
        if addr == QSORT_ADDR:
            r0 = u.reg_read(UC_ARM_REG_R0)
            r1 = u.reg_read(UC_ARM_REG_R1)
            r2 = u.reg_read(UC_ARM_REG_R2)
            r3 = u.reg_read(UC_ARM_REG_R3)
            elems = list(struct.unpack_from(f"<{r1}I", u.mem_read(r0, r1 * 4)))
            trace.append(("qsort", tuple(elems), r1, r2, r3))
            elems.reverse()
            u.mem_write(r0, struct.pack(f"<{r1}I", *elems))
            return
        name = NAME_BY_STUB.get(addr)
        if name is None:
            return
        r0 = u.reg_read(UC_ARM_REG_R0)
        if name == "battle_func_002934d4":
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, case.get("ret_2934d4", 0))
        elif name == "AsdMemory_func_002c684c":
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, HEAP_ADDR)
        elif name == "script_vm_func_0023ec3c":
            trace.append((name, r0 & 0xFFFF))
            v = rng_i[0] % max(1, (r0 & 0xFFFF))
            rng_i[0] += 1
            u.reg_write(UC_ARM_REG_R0, v)
        elif name == "ui_func_00250fb4":
            trace.append((name, r0))

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_R0, MGR_ADDR)
    uc.reg_write(UC_ARM_REG_R1, A1_ADDR)
    uc.reg_write(UC_ARM_REG_R2, case["mode"])
    uc.reg_write(UC_ARM_REG_R3, case.get("a3", 10))
    uc.mem_write(STACK_TOP - 4, struct.pack("<I", case.get("flag", 0)))
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP - 4)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(entry_addr, HALT_ADDR, timeout=5_000_000)

    a1_mode = struct.unpack_from("<I", uc.mem_read(A1_ADDR + 0x598, 4))[0]
    u_raw = uc.mem_read(UNITS_ADDR, 0x6D * 0x114)
    slots = [struct.unpack_from("<I", u_raw, i * 0x114 + 0x5C)[0] for i in range(0x6D)]
    return trace, a1_mode, slots


CASES = [
    {"name": "2934d4_nonzero", "mode": 1, "ret_2934d4": 1},
    {"name": "mode0_early", "mode": 0},
    {"name": "modeffff_early", "mode": 0xFFFF},
    {"name": "n_le_1", "mode": 2, "n_active": 1},
    {"name": "mode4_flag0_ok", "mode": 4, "flag": 0, "n_active": 4},
    {"name": "mode4_bit10_blocked", "mode": 4, "flag": 0, "n_active": 4, "bit10": True},
    {"name": "mode1_n2", "mode": 1, "flag": 0, "n_active": 2, "a3": 7},
    {"name": "mode1_n5_flag1", "mode": 1, "flag": 1, "n_active": 5, "a3": 7},
    {"name": "mode2_thirds", "mode": 2, "flag": 0, "n_active": 7, "a3": 10},
    {"name": "mode3_thirds", "mode": 3, "flag": 0, "n_active": 5, "a3": 10},
    {"name": "mode5_shuffle_lt40", "mode": 5, "flag": 0, "n_active": 6},
    {"name": "mode5_ge40", "mode": 5, "flag": 0, "n_active": 40},
    {"name": "mode6_default", "mode": 6, "flag": 0, "n_active": 4, "a3": 10},
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
            if ores[0] != cres[0]:
                print(f"  trace diff: {ores[0]} != {cres[0]}")
            if ores[1] != cres[1]:
                print(f"  mode diff: {ores[1]} != {cres[1]}")
            if ores[2] != cres[2]:
                for i in range(0x6D):
                    if ores[2][i] != cres[2][i]:
                        print(f"  slot[{i}]: {ores[2][i]} != {cres[2][i]}")
                        break
            return 1
    print(f"PASS {len(CASES)} cases")

    muts = [
        ("neg_init_clear", "    for (s32 i = 0; i < 0x6D; ++i) {", "    for (s32 i = 0; i < 0x6C; ++i) {"),
        ("neg_mode4_bit10", "            if (flag == 0u && !has_bit10) {", "            if (flag == 0u) {"),
        ("neg_mode1_n2_hi", "            *reinterpret_cast<u32*>(sel[i] + 0x5Cu) = (v >= lo && v <= hi) ? 0u : a3;", "            *reinterpret_cast<u32*>(sel[i] + 0x5Cu) = (v >= lo && v < hi) ? 0u : a3;"),
        ("neg_thirds_mul2", "        *reinterpret_cast<u32*>(sel[i] + 0x5Cu) = a3 * 2u;", "        *reinterpret_cast<u32*>(sel[i] + 0x5Cu) = a3 * 3u;"),
        ("neg_shuffle_40", "    const f32 step = 40.0f / static_cast<f32>(n);", "    const f32 step = 41.0f / static_cast<f32>(n);"),
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
