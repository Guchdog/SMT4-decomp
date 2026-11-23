#!/usr/bin/env python3
"""Differential test for ui_func_0022d994 (0x0022d994, 456 B).

Compiles src/engine/leaf_batch41_c.cpp, extracts the ui_func_0022d994 body,
resolves its eight direct call relocations to deterministic stubs, and runs the
pinned original (extracted/exefs/code.bin) against the candidate in separate
Unicorn ARM machines with identical fixtures.

Compared on every case:
  * return r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log with every register argument and the architected stack
    words of the draw calls (1 for 0x230F18, 2 for 0x231D60);
  * every emulated write outside the private stack frame, in order;
  * the self object, the 0x0044EA00 global and its overlay object, and every
    layout/size buffer (final bytes).

Coverage: flag == 0 and non-zero forms (including high-bit and all-ones), all
four 0x2BF6C8 lookups, signed 16-bit layout offsets at -0x8000/0x7FFF, width
words with and without bit 15 set, base-id and forwarded-argument boundaries,
dirty-byte and non-null callback combinations, and callback depth 0/1. Negative
controls mutate the base-id bias, the width mask, the scale literal, the
flag-selected draw id and the dirty-byte clear; each mutant must be detected.
"""

from __future__ import annotations

import struct
import sys
import tempfile
from pathlib import Path

from unicorn import (
    UC_ARCH_ARM,
    UC_HOOK_CODE,
    UC_HOOK_MEM_WRITE,
    UC_MODE_ARM,
    Uc,
)
from unicorn.arm_const import (
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_R4,
    UC_ARM_REG_R5,
    UC_ARM_REG_R6,
    UC_ARM_REG_R7,
    UC_ARM_REG_R8,
    UC_ARM_REG_R9,
    UC_ARM_REG_R10,
    UC_ARM_REG_R11,
    UC_ARM_REG_S0,
    UC_ARM_REG_SP,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch41_c.cpp"

FUNC_ADDR = 0x0022D994
FUNC_SIZE = 456
FUNC_NAME = "ui_func_0022d994"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

SELF_ADDR = 0x00600000
SELF_SIZE = 0x10000
GLOBAL_44EA00 = 0x0044EA00
G44EA00_OBJ = 0x00610000
G44EA00_SIZE = 0x10000
LAYOUT_BASE = 0x00630000
LAYOUT_SIZE = 0x10000
SZ_BASE = 0x00640000
SZ_SIZE = 0x10000
STUB_CB = STUB_BASE + 0x100
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x002BF6C8: "camp_func_002bf6c8",
    0x002BF710: "ui_func_002bf710",
    0x00230F18: "ui_func_00230f18",
    0x00231D60: "camp_func_00231d60",
    0x002313EC: "func_002313ec",
    0x002BEF7C: "ui_func_002bef7c",
    0x002BEF70: "shop_func_002bef70",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
STUB_BY_NAME["sl_cb"] = STUB_CB
NAME_BY_STUB = {v: k for k, v in STUB_BY_NAME.items()}


def patch_cand_elf(obj_path: Path) -> tuple[bytes, int]:
    """Patch the candidate `.text` and return (code bytes, entry address)."""
    elf = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", elf, 0x20)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", elf, 0x2E)
    sections = [
        struct.unpack_from("<10I", elf, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr_off = sections[e_shstrndx][4]

    def sec_name(idx: int) -> str:
        n_off = shstr_off + sections[idx][0]
        return elf[n_off : elf.find(b"\x00", n_off)].decode("ascii", "replace")

    symtab = next(sh for sh in sections if sh[1] == 2)
    strtab = sections[symtab[6]]
    str_off = strtab[4]

    def sym_info(sym_idx: int) -> tuple[str, int, int]:
        s_off = symtab[4] + sym_idx * 16
        st_name, st_value, _, _, _, st_shndx = struct.unpack_from(
            "<IIIBBH", elf, s_off
        )
        end = elf.find(b"\x00", str_off + st_name)
        return elf[str_off + st_name : end].decode("ascii", "replace"), st_value, st_shndx

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
            if not (func_val <= r_offset < func_val + func_size):
                continue
            if r_type in (28, 29):
                if sname not in STUB_BY_NAME:
                    raise RuntimeError(f"Unknown call target {sname}")
                target = STUB_BY_NAME[sname]
                insn = struct.unpack_from("<I", text_bytes, r_offset)[0]
                imm24 = ((target - (CODE_BASE + r_offset + 8)) >> 2) & 0x00FFFFFF
                struct.pack_into("<I", text_bytes, r_offset, (insn & 0xFF000000) | imm24)
            elif r_type == 2:
                addend = struct.unpack_from("<i", text_bytes, r_offset)[0]
                if sshndx == func_shndx:
                    target = CODE_BASE + sval + addend
                    struct.pack_into("<I", text_bytes, r_offset, target)
                else:
                    raise RuntimeError(f"Unhandled ABS32 target {sname}")
            else:
                raise RuntimeError(f"Unhandled reloc type {r_type} for {sname}")

    cand_mem = bytearray(CODE_SIZE)
    cand_mem[0 : len(text_bytes)] = text_bytes
    return bytes(cand_mem), CODE_BASE + func_val


def patch_orig_bl(code_bytes: bytearray) -> None:
    base = FUNC_ADDR - CODE_BASE
    for off in range(0, FUNC_SIZE, 4):
        insn = struct.unpack_from("<I", code_bytes, base + off)[0]
        top = (insn >> 24) & 0xFF
        if top in (0xEA, 0xEB):
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


def run_case(code_bytes: bytes, entry_addr: int, case: dict) -> dict:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STUB_BASE - 0x1000, 0x4000)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(SELF_ADDR, SELF_SIZE)
    # 0x0044EA00 lies inside the mapped code range.
    uc.mem_map(G44EA00_OBJ, G44EA00_SIZE)
    uc.mem_map(LAYOUT_BASE, LAYOUT_SIZE)
    uc.mem_map(SZ_BASE, SZ_SIZE)
    uc.mem_map(HALT_ADDR & ~0xFFF, 0x2000)

    uc.mem_write(CODE_BASE, code_bytes)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

    # self: only the f32 field at +0x234 is read by the function itself.
    self_buf = bytearray(SELF_SIZE)
    struct.pack_into("<f", self_buf, 0x234, case.get("self_scale", 1.5))
    struct.pack_into("<i", self_buf, 0x2AC, case.get("record_x", 0x1234))
    struct.pack_into("<i", self_buf, 0x2B0, case.get("record_y", 0x5678))
    uc.mem_write(SELF_ADDR, bytes(self_buf))

    uc.mem_write(GLOBAL_44EA00, struct.pack("<I", G44EA00_OBJ))
    obj = bytearray(0x2000)
    sl_off = 0x130C
    depth = case.get("depth", 0)
    struct.pack_into("<I", obj, sl_off, depth)
    # Pending slot array at slot+8+depth*4.
    for i in range(4):
        struct.pack_into(
            "<I",
            obj,
            sl_off + 8 + i * 4,
            case.get("slot_values", [0, 0, 0, 0])[i],
        )
    obj[sl_off + 0x18] = case.get("slot_dirty", 0)
    struct.pack_into("<I", obj, sl_off + 0x1C, STUB_CB)
    uc.mem_write(G44EA00_OBJ, bytes(obj))

    trace: list[tuple] = []
    l_idx = [0]
    writes: list[tuple[int, int, int]] = []

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

        if name == "camp_func_002bf6c8":
            trace.append((name, r0, r1))
            idx = l_idx[0]
            l_idx[0] += 1
            la = LAYOUT_BASE + idx * 0x20
            sa = SZ_BASE + idx * 0x10
            bx = case.get("layout_x", [10, 11, 12, 13])[idx]
            by = case.get("layout_y", [20, 21, 22, 23])[idx]
            lbuf = bytearray(0x10)
            struct.pack_into("<I", lbuf, 0, sa)
            struct.pack_into("<HH", lbuf, 4, 0, 0)
            struct.pack_into("<hh", lbuf, 8, bx, by)
            struct.pack_into("<I", lbuf, 0xC, sa)
            # Width word lives at +4 and is significant for the 0x42C lookup.
            width_word = case.get("width_word", 0x8000 | (100 + idx))
            struct.pack_into("<H", lbuf, 4, width_word & 0xFFFF)
            u.mem_write(la, bytes(lbuf))
            u.mem_write(
                sa,
                struct.pack(
                    "<hh", case.get("clip_w", [40, 41, 42, 43])[idx],
                    case.get("clip_h", [16, 17, 18, 19])[idx],
                ),
            )
            u.reg_write(UC_ARM_REG_R0, la)
        elif name == "ui_func_002bf710":
            trace.append((name, u.reg_read(UC_ARM_REG_S0)))
        elif name == "ui_func_00230f18":
            s0 = struct.unpack_from("<I", u.mem_read(sp, 4))[0]
            trace.append((name, r0, r1, r2, r3, s0))
        elif name == "camp_func_00231d60":
            s0, s1 = struct.unpack_from("<II", u.mem_read(sp, 8))
            trace.append((name, r0, r1, r2, r3, s0, s1))
        elif name == "func_002313ec":
            trace.append((name, r0, r1, r2, r3))
        elif name == "ui_func_002bef7c":
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, case.get("cursor", 50))
        elif name == "shop_func_002bef70":
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, case.get("base_y_add", 60))
        elif name == "sl_cb":
            trace.append((name,))

    def on_write(u: Uc, _access: int, address: int, size: int, value: int, _user: object) -> None:
        if STACK_BASE <= address < STACK_BASE + STACK_SIZE:
            return
        writes.append((address, size, value))

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.hook_add(UC_HOOK_MEM_WRITE, on_write)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_R1, case.get("id_base", 3))
    uc.reg_write(UC_ARM_REG_R2, case.get("a4", 0))
    uc.reg_write(UC_ARM_REG_R3, case["flag"])
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(entry_addr, HALT_ADDR, timeout=5_000_000)

    regs = {
        "r0": uc.reg_read(UC_ARM_REG_R0),
        "pc": uc.reg_read(UC_ARM_REG_PC),
        "sp": uc.reg_read(UC_ARM_REG_SP),
    }
    for i, reg in enumerate(
        (
            UC_ARM_REG_R4,
            UC_ARM_REG_R5,
            UC_ARM_REG_R6,
            UC_ARM_REG_R7,
            UC_ARM_REG_R8,
            UC_ARM_REG_R9,
            UC_ARM_REG_R10,
            UC_ARM_REG_R11,
        )
    ):
        regs[f"r{i + 4}"] = uc.reg_read(reg)

    return {
        "trace": trace,
        "writes": writes,
        "regs": regs,
        "self": bytes(uc.mem_read(SELF_ADDR, SELF_SIZE)),
        "global": bytes(uc.mem_read(GLOBAL_44EA00, 4)),
        "obj": bytes(uc.mem_read(G44EA00_OBJ, G44EA00_SIZE)),
        "layout": bytes(uc.mem_read(LAYOUT_BASE, LAYOUT_SIZE)),
        "size": bytes(uc.mem_read(SZ_BASE, SZ_SIZE)),
    }


CASES = [
    {"name": "flag0_default", "flag": 0},
    {"name": "flag1_default", "flag": 1},
    {"name": "flag_high_bit", "flag": 0x80000000},
    {"name": "flag_all_ones", "flag": 0xFFFFFFFF},
    {"name": "flag0_id_base_0", "flag": 0, "id_base": 0},
    {"name": "flag0_id_base_max", "flag": 0, "id_base": 0xFFFFFFFF},
    {"name": "flag1_a4_max", "flag": 1, "a4": 0xFFFFFFFF},
    {"name": "signed_offsets", "flag": 0,
     "layout_x": [-0x8000, 0x7FFF, -1, 1],
     "layout_y": [0x7FFF, -0x8000, 0, -1]},
    {"name": "width_clear_bit15", "flag": 0, "width_word": 0x7FFF & ~0x8000},
    {"name": "width_bit15_only", "flag": 0, "width_word": 0x8000},
    {"name": "width_all_ones", "flag": 0, "width_word": 0xFFFF},
    {"name": "zero_width", "flag": 0, "width_word": 0},
    {"name": "dirty_no_cb", "flag": 0, "slot_dirty": 1, "depth": 0},
    {"name": "cb_nonnull_clean", "flag": 0, "slot_dirty": 0, "depth": 0,
     "slot_values": [0xDEADBEEF, 0, 0, 0]},
    {"name": "cb_nonnull_dirty", "flag": 1, "slot_dirty": 1, "depth": 1,
     "slot_values": [0, 0x12345678, 0, 0]},
    {"name": "depth3_slot_null", "flag": 1, "slot_dirty": 0, "depth": 3},
    {"name": "negative_cursor", "flag": 0, "cursor": -5, "base_y_add": -7},
    {"name": "scale_zero", "flag": 0, "self_scale": 0.0},
    {"name": "scale_negative", "flag": 1, "self_scale": -2.25},
]


def compile_cand(cpp_text: str) -> tuple[bytes, int]:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        src = td_path / "cand.cpp"
        obj = td_path / "cand.o"
        src.write_text(cpp_text, encoding="utf-8")
        res = compile_tu_armv6k(src, obj, ROOT)
        if res.returncode != 0:
            raise RuntimeError(f"Candidate compilation failed: {res.stderr}")
        return patch_cand_elf(obj)


def main() -> int:
    orig_mem = bytearray(CODE_SIZE)
    raw_code = CODE_BIN.read_bytes()
    orig_mem[0 : len(raw_code)] = raw_code
    patch_orig_bl(orig_mem)
    orig_bytes = bytes(orig_mem)

    cpp_text = SRC_CPP.read_text(encoding="utf-8")
    cand_bytes, cand_entry = compile_cand(cpp_text)

    for case in CASES:
        ores = run_case(orig_bytes, FUNC_ADDR, case)
        cres = run_case(cand_bytes, cand_entry, case)
        if ores != cres:
            print(f"FAIL {case['name']}")
            for key in ("trace", "writes", "regs"):
                if ores[key] != cres[key]:
                    print(f"  {key} differs:")
                    if isinstance(ores[key], list):
                        for i in range(max(len(ores[key]), len(cres[key]))):
                            a = ores[key][i] if i < len(ores[key]) else None
                            b = cres[key][i] if i < len(cres[key]) else None
                            if a != b:
                                print(f"    [{i}] {a} != {b}")
                                break
                    else:
                        print(f"    {ores[key]} != {cres[key]}")
            for key in ("self", "global", "obj", "layout", "size"):
                if ores[key] != cres[key]:
                    print(f"  {key} memory differs")
            return 1
        print(f"PASS {case['name']} ({len(ores['trace'])} calls)")

    mutants = [
        ("neg_id_bias", "id_base + 0x42Fu", "id_base + 0x430u"),
        ("neg_width_mask", "& 0x7FFFu", "& 0xFFFFu"),
        ("neg_scale_literal", "ui_func_002bf710(1.0f);", "ui_func_002bf710(0.5f);"),
        ("neg_flag_draw_id",
         "(flag != 0u) ? 0x42Bu : 0x42Au", "0x42Au"),
        ("neg_dirty_clear", "        slot[0x18u] = 0u;", "        slot[0x18u] = 1u;"),
        ("neg_base_x_offset", "base + 8u", "base + 0xAu"),
    ]

    for mname, old, new in mutants:
        assert old in cpp_text, f"Anchor missing for {mname}"
        mut_cpp = cpp_text.replace(old, new, 1)
        m_bytes, m_entry = compile_cand(mut_cpp)
        caught = False
        for case in CASES:
            if run_case(orig_bytes, FUNC_ADDR, case) != run_case(m_bytes, m_entry, case):
                caught = True
                break
        if not caught:
            print(f"FAIL negative control {mname} was not caught!")
            return 1
        print(f"PASS {mname} (caught)")

    print(f"ALL PASS: {len(CASES)} cases + {len(mutants)} negative controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
