#!/usr/bin/env python3
"""Differential Unicorn test for ui_func_0033aa2c (0x0033aa2c, 1120 B)."""

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

FUNC_ADDR = 0x0033AA2C
FUNC_SIZE = 1120
FUNC_NAME = "ui_func_0033aa2c"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

SELF_ADDR = 0x004A0000
CURSOR_ADDR = 0x004A4000
CACHE_ADDR = 0x004A5000
ITEMS_BASE = 0x004A6000
META_BASE = 0x004AE000
OBJ_BASE = 0x004AF000
TEX_BASE = 0x004AF400
WRAP_ADDR = 0x004AF800
G_WRAP_ARG = 0x0043427C
HALT_ADDR = 0x004FFFF0

CALLEES = {
    0x0027DCA0: "ui_func_0027dca0",
    0x0027DC58: "ui_func_0027dc58",
    0x002C4B30: "engine_func_002c4b30",
    0x002B7F08: "camp_func_002b7f08",
    0x0027EB98: "script_vm_func_0027eb98",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
NAME_BY_STUB = {v: k for k, v in STUB_BY_NAME.items()}


def patch_cand_elf(obj_path: Path) -> tuple[bytes, int]:
    elf = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", elf, 0x20)[0]
    e_shentsize, e_shnum, _ = struct.unpack_from("<HHH", elf, 0x2E)
    sections = [struct.unpack_from("<10I", elf, e_shoff + i * e_shentsize) for i in range(e_shnum)]

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
            func_val = val
            func_size = struct.unpack_from("<I", elf, symtab[4] + idx * 16 + 8)[0]
            func_shndx = shndx
            break
    assert func_val is not None and func_size is not None and func_shndx is not None

    text_sh = sections[func_shndx]
    code = bytearray(elf[text_sh[4] + func_val : text_sh[4] + func_val + func_size])

    for sh in sections:
        if sh[1] == 9 and sh[7] == func_shndx:
            for pos in range(sh[4], sh[4] + sh[5], 8):
                r_off, r_info = struct.unpack_from("<II", elf, pos)
                if not (func_val <= r_off < func_val + func_size):
                    continue
                c_off = r_off - func_val
                r_type = r_info & 0xFF
                s_name, _, _ = sym_info(r_info >> 8)
                if r_type in (28, 29):
                    insn = struct.unpack_from("<I", code, c_off)[0]
                    cond = (insn >> 28) & 0xF
                    op = (insn >> 24) & 0xF
                    link = op == 0xB
                    target = STUB_BY_NAME[s_name]
                    pc = FUNC_ADDR + c_off
                    imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
                    struct.pack_into("<I", code, c_off, (cond << 28) | ((0xB if link else 0xA) << 24) | imm24)
                else:
                    raise RuntimeError(f"Unsupported reloc {r_type} for {s_name}")
    return bytes(code), func_size


def patch_orig_bl(orig_code: bytes) -> bytes:
    buf = bytearray(orig_code)
    for off in range(0, len(buf), 4):
        insn = struct.unpack_from("<I", buf, off)[0]
        top = (insn >> 24) & 0xFF
        if top in (0xEA, 0xEB, 0xFA, 0xFB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            h_bit = (top & 1) if top >= 0xFA else 0
            pc = FUNC_ADDR + off
            target = (pc + 8 + imm24 * 4 + h_bit * 2) & ~3
            if target in CALLEES:
                stub = STUB_BY_NAME[CALLEES[target]]
                rel = ((stub - (pc + 8)) // 4) & 0x00FFFFFF
                op = 0xEA000000 if top == 0xEA else 0xEB000000
                struct.pack_into("<I", buf, off, op | rel)
    return bytes(buf)


def compile_candidate(cpp_text: str) -> tuple[bytes, int]:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        src = td_path / "cand.cpp"
        obj = td_path / "cand.o"
        src.write_text(cpp_text, encoding="utf-8")
        res = compile_tu_armv6k(src, obj)
        if res.returncode != 0:
            raise RuntimeError(f"compile failed:\n{res.stderr}")
        return patch_cand_elf(obj)


def setup_tex_obj(uc: Uc, slot: int, obj_id: int, x0: int, w: int) -> int:
    obj = OBJ_BASE + slot * 0x20
    tex = TEX_BASE + slot * 0x40
    uc.mem_write(obj + 0x04, struct.pack("<I", obj_id))
    uc.mem_write(obj + 0x10, struct.pack("<I", tex))
    uc.mem_write(tex + 0x20, struct.pack("<h", x0))
    uc.mem_write(tex + 0x24, struct.pack("<H", w))
    return obj


def run_one(code_bytes: bytes, case: dict) -> dict:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x000F0000, 0x00010000)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(FUNC_ADDR, code_bytes)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(HALT_ADDR, struct.pack("<I", 0xE12FFF1E))

    uc.mem_write(SELF_ADDR, b"\x00" * 0x2300)
    uc.mem_write(SELF_ADDR + 0x1FBC, struct.pack("<I", CACHE_ADDR if case.get("has_cache") else 0))
    uc.mem_write(SELF_ADDR + 0x1E98, struct.pack("<I", ITEMS_BASE))
    uc.mem_write(CACHE_ADDR, b"\xFF" * (50 * 24))

    if case.get("has_cache"):
        for k, (slot, cid, cx, cy, cz) in enumerate(case.get("cache_entries", [])):
            off = slot * 24
            uc.mem_write(CACHE_ADDR + off + 2, struct.pack("<h", cid))
            uc.mem_write(CACHE_ADDR + off + 0x0C, struct.pack("<fff", cx, cy, cz))

    uc.mem_write(CURSOR_ADDR, b"\x00" * 0x80)
    uc.mem_write(CURSOR_ADDR + 0x00, struct.pack("<f", case.get("cur_key", 1.0)))
    uc.mem_write(CURSOR_ADDR + 0x40, struct.pack("<f", 1.0))
    uc.mem_write(CURSOR_ADDR + 0x62, struct.pack("<h", 10))

    # Meta & Obj for id=10 (cursor), id=11 (item0), id=12 (item1)
    for mid, oid, x0, w in [(10, 100, 1, 6), (11, 101, 2, 8), (12, 102, 2, 8)]:
        uc.mem_write(META_BASE + mid * 0x20 + 0x0C, struct.pack("<I", oid))
        obj = setup_tex_obj(uc, mid - 10, oid, x0, w)
        uc.mem_write(SELF_ADDR + 0x2134 + (mid - 10) * 4, struct.pack("<I", obj))

    uc.mem_write(ITEMS_BASE, b"\x00" * (0x450 + 50 * 0x114))
    for idx, (slot, x_val, mid) in enumerate(case.get("items", [])):
        addr = ITEMS_BASE + 0x450 + slot * 0x114
        uc.mem_write(addr + 0x0C, struct.pack("<f", x_val))
        uc.mem_write(addr + 0x40, struct.pack("<f", 1.0))
        uc.mem_write(addr + 0x50, struct.pack("<I", 0x83))
        uc.mem_write(addr + 0x62, struct.pack("<h", mid))

    uc.mem_write(G_WRAP_ARG, struct.pack("<I", 77))
    wrap_item = ITEMS_BASE + 0x450 + 5 * 0x114
    uc.mem_write(wrap_item + 0x0C, struct.pack("<f", 12.0))
    uc.mem_write(wrap_item + 0x40, struct.pack("<f", 1.0))
    uc.mem_write(wrap_item + 0x62, struct.pack("<h", 11))
    uc.mem_write(WRAP_ADDR + 0x24, struct.pack("<I", 0 if case.get("wrap_null") else wrap_item))

    def hook_code(uc_inst, address, size, user_data):
        name = NAME_BY_STUB.get(address)
        if name is None:
            return
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(UC_ARM_REG_R2)
        if name == "ui_func_0027dca0":
            uc_inst.reg_write(UC_ARM_REG_R0, META_BASE + r1 * 0x20)
        elif name == "ui_func_0027dc58":
            if (r1 == 100 and case.get("obj_null")) or (r1 == 101 and case.get("obj2_null")):
                uc_inst.reg_write(UC_ARM_REG_R0, 0)
            else:
                uc_inst.reg_write(UC_ARM_REG_R0, OBJ_BASE + (r1 - 100) * 0x20)
        elif name == "engine_func_002c4b30":
            uc_inst.mem_write(r0, b"\x00" * r1)
        elif name == "camp_func_002b7f08":
            # Keep items in ascending |x| or as provided; sort by |x| descending if needed
            ptrs = list(struct.unpack(f"<{r1}I", uc_inst.mem_read(r0, r1 * 4)))
            ptrs.sort(key=lambda p: abs(struct.unpack("<f", uc_inst.mem_read(p + 0x0C, 4))[0]), reverse=True)
            if r1:
                uc_inst.mem_write(r0, struct.pack(f"<{r1}I", *ptrs))
        elif name == "script_vm_func_0027eb98":
            uc_inst.reg_write(UC_ARM_REG_R0, WRAP_ADDR)

    uc.hook_add(UC_HOOK_CODE, hook_code)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_R1, CURSOR_ADDR)
    uc.reg_write(UC_ARM_REG_R2, case.get("flags", 0))
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(FUNC_ADDR, HALT_ADDR, timeout=5_000_000, count=50_000)

    ret = uc.reg_read(UC_ARM_REG_R0)
    xyz = struct.unpack("<fff", uc.mem_read(CURSOR_ADDR + 0x0C, 12))
    return {"ret": ret, "xyz": xyz}


def build_cases() -> list[dict]:
    return [
        {"name": "cached_slot0_hit", "has_cache": True, "cur_key": 2.0, "cache_entries": [(0, 0, 2.0, 3.0, 4.0)]},
        {"name": "cached_slot1_hit", "has_cache": True, "cur_key": 5.0, "cache_entries": [(1, 1, 5.0, 6.0, 7.0)]},
        {"name": "cached_slot2_hit", "has_cache": True, "cur_key": 8.0, "cache_entries": [(2, 2, 8.0, 9.0, 10.0)]},
        {"name": "cached_miss_obj_null", "has_cache": True, "cur_key": 9.0, "cache_entries": [(0, 0, 2.0, 3.0, 4.0)], "obj_null": True},
        {"name": "flags_10000_insert_idx0", "flags": 0x10000, "items": [(0, 5.0, 11)]},
        {"name": "flags_10000_gap_8_75", "flags": 0x10000, "items": [(0, 11.25, 11)]},
        {"name": "flags_10000_insert_mid", "flags": 0x10000, "items": [(0, -19.0, 11), (1, 5.0, 12)]},
        {"name": "flags_10000_insert_end", "flags": 0x10000, "items": [(0, 30.0, 11)]},
        {"name": "flags_20000_left", "flags": 0x20000},
        {"name": "flags_40000_right", "flags": 0x40000},
        {"name": "flags_0_wrap_null", "flags": 0, "wrap_null": True},
        {"name": "flags_0_obj2_null", "flags": 0, "obj2_null": True},
    ]


def verify(cpp_text: str) -> tuple[bool, int, str]:
    cand_code, cand_size = compile_candidate(cpp_text)
    with open(CODE_BIN, "rb") as f:
        f.seek(FUNC_ADDR - CODE_BASE)
        orig_code = patch_orig_bl(f.read(FUNC_SIZE))

    for case in build_cases():
        orig_res = run_one(orig_code, case)
        cand_res = run_one(cand_code, case)
        if orig_res != cand_res:
            return False, cand_size, f"FAIL {case['name']}:\n  orig={orig_res}\n  cand={cand_res}"
    return True, cand_size, "OK"


def run_negative_controls(cpp_text: str) -> None:
    mutations = [
        ("wrong_cache_stride", "base + r0 * 24 + 2", "base + r0 * 28 + 2"),
        ("wrong_item_stride", "base_items + i * 0x114;", "base_items + i * 0x104;"),
        ("wrong_scale_const", "cur_scale * 2.5f;", "cur_scale * 3.0f;"),
        ("wrong_margin_const", "- 20.0f >=", "- 25.0f >="),
        ("wrong_flags_40000", "0x40000u", "0x80000u"),
    ]
    for name, old, new in mutations:
        assert old in cpp_text, f"Mutation anchor missing: {name}"
        mutated = cpp_text.replace(old, new, 1)
        ok, _, _ = verify(mutated)
        if ok:
            raise AssertionError(f"Negative control {name} unexpectedly passed!")


def main() -> int:
    cpp_text = SRC_CPP.read_text(encoding="utf-8")
    ok, cand_size, msg = verify(cpp_text)
    if not ok:
        print(msg)
        return 1
    run_negative_controls(cpp_text)
    print(f"ALL PASS: {len(build_cases())} cases + 5 negative controls (cand_size={cand_size}B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
