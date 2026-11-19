#!/usr/bin/env python3
"""Differential Unicorn test for engine_func_0038f1d0 (0x0038f1d0, 400 B entry in a 1112 B span)."""

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

FUNC_ADDR = 0x0038F1D0
FUNC_SIZE = 400
FUNC_NAME = "engine_func_0038f1d0"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

SELF_ADDR = 0x004A0000
G_SHOP_PTR = 0x00432FC8
SHOP_ADDR = 0x004A2000
OBJ_ADDR = 0x004A4000
VTABLE_ADDR = 0x004A5000
HALT_ADDR = 0x004FFFF0

CALLEES = {
    0x0038B75C: "engine_func_0038b75c",
    0x002ACB3C: "ui_func_002acb3c",
    0x00233F4C: "engine_func_00233f4c",
    0x00233AC0: "camp_func_00233ac0",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
STUB_BY_NAME["release"] = STUB_BASE + 0x40
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
            func_val = val
            func_size = struct.unpack_from("<I", elf, symtab[4] + idx * 16 + 8)[0]
            func_shndx = shndx
            break
    assert func_val is not None and func_size is not None and func_shndx is not None

    text_sh = sections[func_shndx]
    code = bytearray(elf[text_sh[4] + func_val : text_sh[4] + func_val + func_size])

    rodata_blob = bytearray()
    rodata_map: dict[int, int] = {}
    for idx, sh in enumerate(sections):
        if sec_name(idx).startswith(".rodata"):
            rodata_map[idx] = RODATA_BASE + len(rodata_blob)
            rodata_blob.extend(elf[sh[4] : sh[4] + sh[5]])
            while len(rodata_blob) % 4 != 0:
                rodata_blob.append(0)

    for sh in sections:
        if sh[1] == 9 and sh[7] == func_shndx:
            for pos in range(sh[4], sh[4] + sh[5], 8):
                r_off, r_info = struct.unpack_from("<II", elf, pos)
                if not (func_val <= r_off < func_val + func_size):
                    continue
                c_off = r_off - func_val
                r_type = r_info & 0xFF
                s_name, _, s_shndx = sym_info(r_info >> 8)
                if r_type in (28, 29):
                    insn = struct.unpack_from("<I", code, c_off)[0]
                    cond = (insn >> 28) & 0xF
                    op = (insn >> 24) & 0xF
                    link = op == 0xB
                    target = STUB_BY_NAME[s_name]
                    pc = FUNC_ADDR + c_off
                    imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
                    struct.pack_into("<I", code, c_off, (cond << 28) | ((0xB if link else 0xA) << 24) | imm24)
                elif r_type == 2:
                    addend = struct.unpack_from("<I", code, c_off)[0]
                    if s_shndx == func_shndx:
                        struct.pack_into("<I", code, c_off, (FUNC_ADDR - func_val) + addend)
                    elif s_shndx in rodata_map:
                        struct.pack_into("<I", code, c_off, rodata_map[s_shndx] + addend)
                    else:
                        raise RuntimeError(f"Unexpected R_ARM_ABS32 section {s_shndx} ({s_name})")
                else:
                    raise RuntimeError(f"Unsupported reloc {r_type} for {s_name}")
    rodata_blobs = [(RODATA_BASE, bytes(rodata_blob))] if rodata_blob else []
    return bytes(code), rodata_blobs, func_size


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


def compile_candidate(cpp_text: str) -> tuple[bytes, list[tuple[int, bytes]], int]:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        src = td_path / "cand.cpp"
        obj = td_path / "cand.o"
        src.write_text(cpp_text, encoding="utf-8")
        res = compile_tu_armv6k(src, obj)
        if res.returncode != 0:
            raise RuntimeError(f"compile failed:\n{res.stderr}")
        return patch_cand_elf(obj)


def read_utf16(uc: Uc, addr: int) -> str:
    out = bytearray()
    while len(out) < 256:
        ch = bytes(uc.mem_read(addr + len(out), 2))
        if ch == b"\x00\x00":
            break
        out.extend(ch)
    return out.decode("utf-16le")


def run_one(code_bytes: bytes, rodata_blobs: list[tuple[int, bytes]], case: dict) -> dict:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x000F0000, 0x00010000)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(FUNC_ADDR, code_bytes)
    for base, blob in rodata_blobs:
        uc.mem_write(base, blob)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(HALT_ADDR, struct.pack("<I", 0xE12FFF1E))

    uc.mem_write(SELF_ADDR, b"\xCC" * 0x300)
    uc.mem_write(SELF_ADDR + 8, struct.pack("<I", case["state"] & 0xFFFFFFFF))
    uc.mem_write(SELF_ADDR + 0xC, struct.pack("<I", case.get("timer", 7) & 0xFFFFFFFF))
    uc.mem_write(SELF_ADDR + 0x208, struct.pack("<I", 0 if case.get("noobj") else OBJ_ADDR))
    uc.mem_write(OBJ_ADDR, struct.pack("<I", VTABLE_ADDR))
    uc.mem_write(VTABLE_ADDR, struct.pack("<II", 0xDEAD0000, STUB_BY_NAME["release"]))
    uc.mem_write(G_SHOP_PTR, struct.pack("<I", SHOP_ADDR))
    uc.mem_write(SHOP_ADDR, b"\xAA" * 0x800)

    trace: list[tuple] = []

    def hook_code(uc_inst, address, size, user_data):
        name = NAME_BY_STUB.get(address)
        if name is None:
            return
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(UC_ARM_REG_R2)
        r3 = uc_inst.reg_read(UC_ARM_REG_R3)
        sp = uc_inst.reg_read(UC_ARM_REG_SP)
        if name == "engine_func_0038b75c":
            a4, a5, a6 = struct.unpack("<III", uc_inst.mem_read(sp, 12))
            pre = bytes(uc_inst.mem_read(r1, 0x44))
            trace.append((name, r0, r1, read_utf16(uc_inst, r2), r3, a4, a5, a6, pre))
            uc_inst.mem_write(r1, bytes(range(0x40)))
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("b75c_ret", 1))
        elif name == "ui_func_002acb3c":
            trace.append((name, r0, r1, r2))
            uc_inst.mem_write(r0, bytes(uc_inst.mem_read(r1, r2)))
        elif name == "camp_func_00233ac0":
            trace.append((name, r0, r1, r2))
        elif name == "release":
            trace.append((name, r0))
        else:
            trace.append((name, r0, r1))

    uc.hook_add(UC_HOOK_CODE, hook_code)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(FUNC_ADDR, HALT_ADDR, timeout=5_000_000, count=20_000)

    self_after = bytes(uc.mem_read(SELF_ADDR, 0x300))
    shop_after = bytes(uc.mem_read(SHOP_ADDR + 0x680, 0x80))
    return {"self": self_after, "shop": shop_after, "trace": trace}


def build_cases() -> list[dict]:
    return [
        {"name": "st0", "state": 0},
        {"name": "st1_ok_obj", "state": 1, "b75c_ret": 1},
        {"name": "st1_ok_noobj", "state": 1, "b75c_ret": 1, "noobj": True},
        {"name": "st1_fail", "state": 1, "b75c_ret": 0},
        {"name": "st2_timer5", "state": 2, "timer": 5},
        {"name": "st2_timer1_obj", "state": 2, "timer": 1},
        {"name": "st2_timer1_noobj", "state": 2, "timer": 1, "noobj": True},
        {"name": "st2_timer0", "state": 2, "timer": 0},
        {"name": "st2_timer_neg", "state": 2, "timer": -3},
        {"name": "st3_default", "state": 3},
        {"name": "st_big_default", "state": 0xFFFFFFFF},
    ]


def verify(cpp_text: str) -> tuple[bool, int, str]:
    cand_code, rodata_blobs, cand_size = compile_candidate(cpp_text)
    with open(CODE_BIN, "rb") as f:
        f.seek(FUNC_ADDR - CODE_BASE)
        orig_code = patch_orig_bl(f.read(FUNC_SIZE))

    for case in build_cases():
        orig_res = run_one(orig_code, [], case)
        cand_res = run_one(cand_code, rodata_blobs, case)
        if orig_res != cand_res:
            return False, cand_size, f"FAIL {case['name']}:\n  orig={orig_res}\n  cand={cand_res}"
    return True, cand_size, "OK"


def run_negative_controls(cpp_text: str) -> None:
    mutations = [
        ("wrong_state0_next", "case 0u:\n            *state = 1u;", "case 0u:\n            *state = 2u;"),
        ("wrong_zero_count", "i < 16u; ++i) {\n                buf[i] = 0u;", "i < 15u; ++i) {\n                buf[i] = 0u;"),
        ("wrong_title_text", 'u"16\\u30B1', 'u"17\\u30B1'),
        ("wrong_fail_timer", "*reinterpret_cast<u32*>(self + 0xCu) = 3u;", "*reinterpret_cast<u32*>(self + 0xCu) = 4u;"),
        ("wrong_timer_cmp", "if (*timer <= 0) {", "if (*timer < 0) {"),
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
