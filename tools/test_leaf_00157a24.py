#!/usr/bin/env python3
"""Differential Unicorn test for ui_func_00157a24 (0x00157a24, 1312 B)."""

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

FUNC_ADDR = 0x00157A24
FUNC_SIZE = 1312
FUNC_NAME = "ui_func_00157a24"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

SELF_ADDR = 0x00600000
VTBL_ADDR = 0x00603000
MGR64_ADDR = 0x00603100
SRC7C_ADDR = 0x00603200
ARR_FP_ADDR = 0x00603300
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x002BCF58: "ui_func_002bcf58",
    0x002C6C10: "ui_func_002c6c10",
    0x002AA504: "script_vm_func_002aa504",
    0x0015C310: "engine_func_0015c310",
    0x002BB270: "engine_func_002bb270",
    0x0015C5C8: "func_0015c5c8",
    0x002B4DDC: "func_002b4ddc",
    0x002A2268: "ui_func_002a2268",
    0x002A2224: "func_002a2224",
    0x0015D14C: "func_0015d14c",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
STUB_VTBL5 = STUB_BASE + 0x100
STUB_BY_NAME["vtbl5"] = STUB_VTBL5
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
) -> tuple[int, list[tuple], bytes]:
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

    uc.mem_write(VTBL_ADDR + 0x14, struct.pack("<I", STUB_VTBL5))
    uc.mem_write(MGR64_ADDR + 8, struct.pack("<I", 0xABCD))
    uc.mem_write(ARR_FP_ADDR, struct.pack("<3I", 1, 0, 1))

    src7c = bytearray(0x48)
    struct.pack_into("<I", src7c, 0x04, case.get("rate", 1000))
    struct.pack_into("<I", src7c, 0x18, case.get("sz", 0x200))
    # Channel 0 at self+0xA8 (src7c+0x2C): cnt=2, mode=0, tracks [0,1]
    src7c[0x2C : 0x33] = bytes([1, 2, 3, 0, 2, 0, 1])
    # Channel 1 at self+0xAF (src7c+0x33): cnt=1, mode=1 or 2, tracks [2]
    src7c[0x33 : 0x3A] = bytes([4, 5, 6, case.get("ch1_mode", 1), 1, 2, 0])
    uc.mem_write(SRC7C_ADDR, bytes(src7c))

    self_buf = bytearray(0x2000)
    struct.pack_into("<I", self_buf, 0, VTBL_ADDR)
    self_buf[0x0D] = case.get("d", 0)
    self_buf[0x50] = case.get("s50", 1)
    struct.pack_into("<II", self_buf, 0x60, 0x7777, MGR64_ADDR)
    self_buf[0x74] = case.get("dmode", 0)
    struct.pack_into("<III", self_buf, 0x78, case.get("delay", 50), 0, case.get("rate", 1000))
    struct.pack_into("<I", self_buf, 0x94, case.get("sz", 0x200))
    struct.pack_into("<II", self_buf, 0xD0, 3, 2)
    # Channel 0: cnt=3, mode=0, tracks [0,1,2]
    self_buf[0xA8 : 0xAF] = bytes([1, 2, 3, 0, 3, 0, 1])
    # Channel 1: cnt=2, mode=1 or 2, tracks [2,0]
    self_buf[0xAF : 0xB6] = bytes([4, 5, 6, case.get("ch1_mode", 1), 2, 2, 0])
    for t in range(3):
        struct.pack_into("<I", self_buf, 0xD8 + t * 0x340, 0x800000 + t * 0x10000)
    struct.pack_into("<H", self_buf, 0x1C58, 0x42)
    uc.mem_write(SELF_ADDR, bytes(self_buf))

    trace: list[tuple] = []
    v_idx = [0]

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

        if name == "vtbl5":
            trace.append((name, r0))
        elif name == "ui_func_002bcf58":
            data = bytes(u.mem_read(r1, r2))
            trace.append((name, r0, r2))
            u.mem_write(r0, data)
        elif name == "ui_func_002c6c10":
            trace.append((name, r0, r1))
            u.reg_write(UC_ARM_REG_R0, case.get("nbufs", 5))
        elif name == "script_vm_func_002aa504":
            num = struct.unpack_from("<q", struct.pack("<II", r0, r1))[0]
            den = struct.unpack_from("<q", struct.pack("<II", r2, r3))[0]
            trace.append((name, num, den))
            q = (num // den) if den else 0
            lo, hi = struct.unpack("<II", struct.pack("<q", q))
            u.reg_write(UC_ARM_REG_R0, lo)
            u.reg_write(UC_ARM_REG_R1, hi)
        elif name == "engine_func_0015c310":
            s0 = struct.unpack_from("<I", u.mem_read(sp, 4))[0]
            ptrs = struct.unpack_from("<3I", u.mem_read(r1, 12))
            trace.append((name, r0, ptrs, r2, r3, s0))
        elif name == "engine_func_002bb270":
            trace.append((name,))
            u.reg_write(UC_ARM_REG_R0, 0x3333)
        elif name == "func_0015c5c8":
            s0 = struct.unpack_from("<I", u.mem_read(sp, 4))[0]
            trace.append((name, r0, r1, r2, r3, s0))
            v_idx[0] += 1
            if case.get("fail_v_at", 0) == v_idx[0]:
                u.reg_write(UC_ARM_REG_R0, 0)
            else:
                u.reg_write(UC_ARM_REG_R0, 0x9000 + v_idx[0])
        elif name in ("func_002b4ddc", "ui_func_002a2268", "func_002a2224", "func_0015d14c"):
            trace.append((name, r0, r1))

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_R1, case.get("flag", 1))
    uc.reg_write(UC_ARM_REG_R2, SRC7C_ADDR)
    uc.reg_write(UC_ARM_REG_R3, ARR_FP_ADDR)
    uc.mem_write(STACK_TOP - 4, struct.pack("<I", case.get("id", 0x42)))
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP - 4)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(entry_addr, HALT_ADDR, timeout=5_000_000)

    return uc.reg_read(UC_ARM_REG_R0), trace, bytes(uc.mem_read(SELF_ADDR, 0x2000))


CASES = [
    {"name": "s50_zero", "s50": 0},
    {"name": "id_mismatch", "id": 0x43},
    {"name": "flag_zero", "flag": 0},
    {"name": "sz_gt_2000", "sz": 0x2001},
    {"name": "sz_eq_2000", "sz": 0x2000, "nbufs": 4},
    {"name": "nbufs_lt_4", "nbufs": 3},
    {"name": "nbufs_eq_4", "nbufs": 4},
    {"name": "voice_fail", "fail_v_at": 2},
    {"name": "success_dmode0", "nbufs": 5, "dmode": 0, "delay": 50, "ch1_mode": 1},
    {"name": "success_dmode1_clamp_cap32", "nbufs": 40, "dmode": 1, "delay": 0x40000000, "rate": 2000000, "d": 1, "ch1_mode": 2},
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
            print(f"  orig ret={ores[0]} calls={len(ores[1])}")
            print(f"  cand ret={cres[0]} calls={len(cres[1])}")
            for i in range(max(len(ores[1]), len(cres[1]))):
                a = ores[1][i] if i < len(ores[1]) else None
                b = cres[1][i] if i < len(cres[1]) else None
                if a != b:
                    print(f"  diff[{i}]: {a} != {b}")
                    break
            return 1
    print(f"PASS {len(CASES)} cases")

    muts = [
        ("neg_flag0_ret", "        reinterpret_cast<void (*)(u8*)>(vtbl[5])(self);\n        return 0u;", "        reinterpret_cast<void (*)(u8*)>(vtbl[5])(self);\n        return 1u;"),
        ("neg_sz_limit", "    if (sz > 0x2000u) {", "    if (sz >= 0x2000u) {"),
        ("neg_nbufs_min", "    if (n_bufs < 4u) {", "    if (n_bufs <= 4u) {"),
        ("neg_cap_32", "    const u32 capped = (n_bufs > 0x20u) ? 0x20u : n_bufs;", "    const u32 capped = (n_bufs > 0x10u) ? 0x10u : n_bufs;"),
        ("neg_ch_mode1", "            } else if (mode == 1u) {", "            } else if (mode == 2u) {"),
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
