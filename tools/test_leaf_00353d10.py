#!/usr/bin/env python3
"""Differential Unicorn test for engine_func_00353d10 (0x00353d10, 1240 B)."""

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

FUNC_ADDR = 0x00353D10
FUNC_SIZE = 1240
FUNC_NAME = "engine_func_00353d10"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

OUT_STATUS_ADDR = 0x00600000
OUT_VAL_ADDR = 0x00600100
HDR_PAIR_ADDR = 0x00600200
NUM_STR_ADDR = 0x00600300
ITEMS_ADDR = 0x00601000
G_4C7000 = 0x004C7000
STRTOULL_ADDR = 0x00100BF6
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x002BAD80: "engine_func_002bad80",
    0x0023A15C: "func_0023a15c",
    0x00361350: "engine_func_00361350",
    0x003613C8: "func_003613c8",
    0x0023A11C: "func_0023a11c",
    0x002C57B4: "func_002c57b4",
    0x002C57A4: "func_002c57a4",
    0x0023A068: "func_0023a068",
    0x002A1578: "engine_func_002a1578",
    0x002B5F84: "script_vm_func_002b5f84",
    0x002BAC28: "engine_func_002bac28",
    0x00353A50: "ui_func_00353a50",
    0x003522E8: "func_003522e8",
    0x00353ACC: "func_00353acc",
    0x00353B58: "func_00353b58",
    0x00353800: "func_00353800",
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


def read_cstr(uc: Uc, addr: int, limit: int = 32) -> str:
    raw = bytes(uc.mem_read(addr, limit))
    nul = raw.find(0)
    return (raw[:nul] if nul >= 0 else raw).decode("ascii", errors="replace")


def run_case(
    code_bytes: bytes,
    rodata_blobs: list[tuple[int, bytes]],
    entry_addr: int,
    case: dict,
) -> tuple[list[tuple], int, int, bytes]:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STUB_BASE - 0x1000, 0x4000)
    uc.mem_map(RODATA_BASE, 0x20000)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(OUT_STATUS_ADDR, 0x10000)
    uc.mem_map(HALT_ADDR & ~0xFFF, 0x2000)

    uc.mem_write(CODE_BASE, code_bytes)
    for addr, blob in rodata_blobs:
        uc.mem_write(addr, blob)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(STRTOULL_ADDR, struct.pack("<H", 0x4770))  # Thumb bx lr

    uc.mem_write(OUT_STATUS_ADDR, struct.pack("<Q", 0))
    uc.mem_write(OUT_VAL_ADDR, struct.pack("<I", 0))
    uc.mem_write(HDR_PAIR_ADDR, struct.pack("<II", 0x123456, 0xAB03))
    uc.mem_write(NUM_STR_ADDR, b"123456789012\x00")
    uc.mem_write(G_4C7000, b"\x00" * 0x1100)

    items = case.get("items", [])
    ibuf = bytearray(len(items) * 8 + 8)
    for idx, (w0, w1) in enumerate(items):
        struct.pack_into("<II", ibuf, idx * 8, w0, w1)
    uc.mem_write(ITEMS_ADDR, bytes(ibuf))

    trace: list[tuple] = []
    idx_3522e8 = [0]

    def on_code(u: Uc, addr: int, _size: int, _user: object) -> None:
        if addr == HALT_ADDR:
            u.emu_stop()
            return
        if addr == STRTOULL_ADDR:
            r0 = u.reg_read(UC_ARM_REG_R0)
            r1 = u.reg_read(UC_ARM_REG_R1)
            r2 = u.reg_read(UC_ARM_REG_R2)
            trace.append(("strtoull", read_cstr(u, r0), r1, r2))
            u.reg_write(UC_ARM_REG_R0, 0x11223344)
            u.reg_write(UC_ARM_REG_R1, 0x55667788)
            return
        name = NAME_BY_STUB.get(addr)
        if name is None:
            return
        r0 = u.reg_read(UC_ARM_REG_R0)
        r1 = u.reg_read(UC_ARM_REG_R1)
        r2 = u.reg_read(UC_ARM_REG_R2)
        r3 = u.reg_read(UC_ARM_REG_R3)
        sp = u.reg_read(UC_ARM_REG_SP)

        if name == "engine_func_002bad80":
            trace.append((name, r0, r1))
            u.mem_write(r0, struct.pack("<Q", r1))
        elif name == "func_0023a15c":
            trace.append((name, r0, r1))
            u.reg_write(UC_ARM_REG_R0, case.get("rc_23a15c", 0) & 0xFFFFFFFF)
        elif name == "engine_func_00361350":
            trace.append((name, r0))
        elif name == "func_003613c8":
            trace.append((name, r0))
        elif name == "func_0023a11c":
            trace.append((name, r1, r2))
            u.reg_write(UC_ARM_REG_R0, case.get("rc_23a11c", 0) & 0xFFFFFFFF)
        elif name in ("func_002c57b4", "func_002c57a4"):
            trace.append((name,))
            key = "ret_2c57b4" if name.endswith("b4") else "ret_2c57a4"
            u.reg_write(UC_ARM_REG_R0, case.get(key, 0))
        elif name == "func_0023a068":
            trace.append((name, r1))
            u.mem_write(r0, struct.pack("<Q", case.get("st64", 0) & 0xFFFFFFFFFFFFFFFF))
        elif name == "engine_func_002a1578":
            st = struct.unpack_from("<q", u.mem_read(r0, 8))[0]
            trace.append((name, st))
            u.reg_write(UC_ARM_REG_R0, 0xFFFFFFFF if st < 0 else 0)
        elif name == "script_vm_func_002b5f84":
            trace.append((name,))
            u.reg_write(UC_ARM_REG_R0, 0xAAAABBBB)
        elif name == "engine_func_002bac28":
            trace.append((name,))
            u.mem_write(r0, struct.pack("<I", 0x99887766))
        elif name == "ui_func_00353a50":
            s0, s1 = struct.unpack_from("<II", u.mem_read(sp, 8))
            trace.append((name, r0, r2, r3, read_cstr(u, s0), s1))
            entries = case.get("entries", [])
            u.mem_write(G_4C7000 + 0x438, struct.pack("<I", len(entries)))
            for idx, (elo, ehi) in enumerate(entries):
                u.mem_write(G_4C7000 + 0x238 + idx * 8, struct.pack("<II", elo, ehi))
            u.reg_write(UC_ARM_REG_R0, case.get("rc_353a50", 0) & 0xFFFFFFFF)
        elif name == "func_003522e8":
            entry_val = struct.unpack_from("<Q", u.mem_read(r2, 8))[0]
            trace.append((name, r1, r3, entry_val))
            u.mem_write(r0, b"\x00" * 0x18)
            u.mem_write(r0 + 0x10, struct.pack("<H", 0x4567 + idx_3522e8[0]))
            idx_3522e8[0] += 1
            u.reg_write(UC_ARM_REG_R0, case.get("rc_3522e8", 0) & 0xFFFFFFFF)
        elif name == "func_00353acc":
            trace.append((name, r0, r1, r2, r3))
        elif name == "func_00353b58":
            v = struct.unpack_from("<I", u.mem_read(r0, 4))[0]
            trace.append((name, v))
            u.reg_write(UC_ARM_REG_R0, case.get("rc_353b58", 0) & 0xFFFFFFFF)
        elif name == "func_00353800":
            trace.append((name, r0, r1))
            u.reg_write(UC_ARM_REG_R0, case.get("rc_353800", 0) & 0xFFFFFFFF)

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.reg_write(UC_ARM_REG_R0, OUT_STATUS_ADDR)
    uc.reg_write(UC_ARM_REG_R1, 0x5555)
    uc.reg_write(UC_ARM_REG_R2, OUT_VAL_ADDR)
    uc.reg_write(UC_ARM_REG_R3, HDR_PAIR_ADDR)
    uc.mem_write(STACK_TOP - 12, struct.pack("<III", NUM_STR_ADDR, ITEMS_ADDR, case["count"]))
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP - 12)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(entry_addr, HALT_ADDR, timeout=5_000_000)

    out_st = struct.unpack_from("<Q", uc.mem_read(OUT_STATUS_ADDR, 8))[0]
    out_val = struct.unpack_from("<I", uc.mem_read(OUT_VAL_ADDR, 4))[0]
    return trace, out_st, out_val, bytes(uc.mem_read(G_4C7000, 0x250))


CASES = [
    {"name": "count_gt_64", "count": 65},
    {"name": "count_64_ok", "count": 64, "items": [(0x1100 + i, 0x2200) for i in range(64)]},
    {"name": "bad_tag2", "count": 1, "items": [(0x1234, 0x02)]},
    {"name": "bad_tag3", "count": 1, "items": [(0x1234, 0x03)]},
    {"name": "err_23a15c", "count": 1, "items": [(0x1234, 0x00)], "rc_23a15c": -5},
    {"name": "err_23a11c", "count": 1, "items": [(0x1234, 0x00)], "rc_23a11c": -6},
    {"name": "err_2c57b4", "count": 1, "items": [(0x1234, 0x00)], "ret_2c57b4": 1},
    {"name": "err_2c57a4", "count": 1, "items": [(0x1234, 0x00)], "ret_2c57a4": 1},
    {"name": "err_2a1578", "count": 1, "items": [(0x1234, 0x00)], "st64": 0x8000000000000009},
    {"name": "err_353a50", "count": 1, "items": [(0x1234, 0x00)], "rc_353a50": -7},
    {"name": "err_3522e8", "count": 1, "items": [(0x1234, 0x00)], "entries": [(0x1111, 0x4008C)], "rc_3522e8": -8},
    {"name": "err_353b58", "count": 1, "items": [(0x1234, 0x00)], "rc_353b58": -9},
    {"name": "err_353800", "count": 1, "items": [(0x1234, 0x00)], "rc_353800": -10},
    {
        "name": "full_success_mixed",
        "count": 4,
        "items": [(0x11111, 0xAA00), (0x22222, 0xBB01), (0x33333, 0xCC00), (0x44444, 0xDD01)],
        "entries": [(0x555555, 0x4008C), (0x666666, 0x4000D)],
    },
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
            print(f"  orig st={hex(ores[1])} val={hex(ores[2])} calls={len(ores[0])}")
            print(f"  cand st={hex(cres[1])} val={hex(cres[2])} calls={len(cres[0])}")
            for i in range(max(len(ores[0]), len(cres[0]))):
                a = ores[0][i] if i < len(ores[0]) else None
                b = cres[0][i] if i < len(cres[0]) else None
                if a != b:
                    print(f"  diff[{i}]: {a} != {b}")
                    break
            return 1
        print(f"PASS {case['name']} ({len(ores[0])} calls)")

    muts = [
        ("neg_count_limit", "    if (count > 0x40u) {", "    if (count >= 0x40u) {"),
        ("neg_tag0_filter", "        if ((hi >> 14u) == 0x10u && static_cast<u16>(hi) == 0x8Cu) {", "        if ((hi >> 14u) == 0x10u && static_cast<u16>(hi) == 0x0Du) {"),
        ("neg_g_offset_43c", "    rc = ui_func_00353a50(h_ctx, &val8, hdr_pair[0], hdr_pair[1], num_str, g + 0x43Cu);", "    rc = ui_func_00353a50(h_ctx, &val8, hdr_pair[0], hdr_pair[1], num_str, g + 0x438u);"),
        ("neg_desc_u16_off", "                         (static_cast<u32>(*reinterpret_cast<const u16*>(desc + 0x10u)) << 16u);", "                         (static_cast<u32>(*reinterpret_cast<const u16*>(desc + 0x12u)) << 16u);"),
        ("neg_out_val_skip", "    *out_val = val8;\n    engine_func_002bad80(out_status, 0u);", "    engine_func_002bad80(out_status, 0u);"),
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
