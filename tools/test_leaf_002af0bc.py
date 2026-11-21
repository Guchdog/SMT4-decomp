#!/usr/bin/env python3
"""Differential Unicorn test for battle_func_002af0bc (0x002af0bc, 1132 B)."""

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

FUNC_ADDR = 0x002AF0BC
FUNC_SIZE = 1132
FUNC_NAME = "battle_func_002af0bc"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

SELF_ADDR = 0x004A0000
TARGET_ADDR = 0x004A1000
TARGET_VT = 0x004A1100
H1_ADDR = 0x004A2000
H1_VT = 0x004A2100
H2_ADDR = 0x004A3000
H2_VT = 0x004A3100
TARGET_MAT_ADDR = 0x004A4000
ID12_ADDR = 0x004A4100
ID16_ADDR = 0x004A4200
HALT_ADDR = 0x004FFFF0

CALLEES = {
    0x002ACBD8: "engine_func_002acbd8",
    0x002A84EC: "func_002a84ec",
    0x002A7F04: "battle_func_002a7f04",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
STUB_BY_NAME["target_get"] = STUB_BASE + 0x20
STUB_BY_NAME["h1_build"] = STUB_BASE + 0x24
STUB_BY_NAME["h2_build"] = STUB_BASE + 0x28
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
        if top in (0xEA, 0xEB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = FUNC_ADDR + off
            target = pc + 8 + imm24 * 4
            if target in CALLEES:
                stub = STUB_BY_NAME[CALLEES[target]]
                rel = ((stub - (pc + 8)) // 4) & 0x00FFFFFF
                struct.pack_into("<I", buf, off, (top << 24) | rel)
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

    uc.mem_write(SELF_ADDR, b"\x00" * 0x300)
    uc.mem_write(SELF_ADDR + 0x0C, struct.pack("<I", TARGET_ADDR if case.get("has_target") else 0))
    uc.mem_write(SELF_ADDR + 0x98, struct.pack("<I", 0x11111111))
    uc.mem_write(SELF_ADDR + 0xA8, struct.pack("<I", 0x22222222))
    uc.mem_write(SELF_ADDR + 0xB8, struct.pack("<I", 0x33333333))
    uc.mem_write(SELF_ADDR + 0x258, struct.pack("<I", H1_ADDR))
    uc.mem_write(SELF_ADDR + 0x260, struct.pack("<I", H2_ADDR))

    uc.mem_write(TARGET_ADDR, struct.pack("<I", TARGET_VT))
    uc.mem_write(TARGET_VT + 0x14, struct.pack("<I", STUB_BY_NAME["target_get"]))
    uc.mem_write(H1_ADDR, struct.pack("<I", H1_VT))
    uc.mem_write(H1_VT + 0x0C, struct.pack("<I", STUB_BY_NAME["h1_build"]))
    uc.mem_write(H2_ADDR, struct.pack("<I", H2_VT))
    uc.mem_write(H2_VT + 0x0C, struct.pack("<I", STUB_BY_NAME["h2_build"]))

    uc.mem_write(ID12_ADDR, struct.pack("<12I", *range(100, 112)))
    uc.mem_write(ID16_ADDR, struct.pack("<16f", *[float(i + 1) for i in range(16)]))

    trace: list[tuple] = []

    def hook_code(uc_inst, address, size, user_data):
        name = NAME_BY_STUB.get(address)
        if name is None:
            return
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(UC_ARM_REG_R2)
        r3 = uc_inst.reg_read(UC_ARM_REG_R3)
        if name == "target_get":
            trace.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, TARGET_MAT_ADDR)
        elif name == "engine_func_002acbd8":
            trace.append((name,))
            uc_inst.reg_write(UC_ARM_REG_R0, ID12_ADDR)
        elif name == "h1_build":
            vec3 = struct.unpack("<III", uc_inst.mem_read(r3, 12))
            trace.append((name, r0, r1, r2, vec3))
        elif name == "func_002a84ec":
            trace.append((name, r0, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("a84ec_ret", 1))
        elif name == "h2_build":
            trace.append((name, r0, r1, r2))
            uc_inst.mem_write(r1, struct.pack("<16f", *case["mat"]))
        elif name == "battle_func_002a7f04":
            trace.append((name,))
            uc_inst.reg_write(UC_ARM_REG_R0, ID16_ADDR)

    uc.hook_add(UC_HOOK_CODE, hook_code)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(FUNC_ADDR, HALT_ADDR, timeout=5_000_000, count=20_000)

    out_mat = struct.unpack("<16f", uc.mem_read(SELF_ADDR + 0x1E8, 64))
    mid12 = struct.unpack("<12I", uc.mem_read(SELF_ADDR + 0x178, 48))
    return {"out_mat": out_mat, "mid12": mid12, "trace": trace}


def build_cases() -> list[dict]:
    diag_mat = [
        2.0, 0.0, 0.0, 0.0,
        0.0, 4.0, 0.0, 0.0,
        0.0, 0.0, 8.0, 0.0,
        0.0, 0.0, 0.0, 2.0,
    ]
    singular_mat = [
        1.0, 2.0, 3.0, 4.0,
        2.0, 4.0, 6.0, 8.0,
        0.0, 1.0, 0.0, 1.0,
        1.0, 0.0, 1.0, 0.0,
    ]
    general_mat = [
        1.0, 0.0, 1.0, 2.0,
        1.0, 2.0, 0.0, 4.0,
        1.0, 1.0, 2.0, 0.0,
        0.0, 1.0, 1.0, 1.0,
    ]
    return [
        {"name": "target_nonnull_diag", "has_target": True, "a84ec_ret": 1, "mat": diag_mat},
        {"name": "target_null_singular", "has_target": False, "a84ec_ret": 0, "mat": singular_mat},
        {"name": "invert_general_4x4", "has_target": True, "a84ec_ret": 1, "mat": general_mat},
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
        ("wrong_tmp_off2", "tmp[2] = *reinterpret_cast<const u32*>(self + 0xB8u);", "tmp[2] = *reinterpret_cast<const u32*>(self + 0xB4u);"),
        ("wrong_det_sign", "+ a5 * b0;", "- a5 * b0;"),
        ("wrong_inv_m4", "(-m[4] * b5 + m[6] * b2 - m[7] * b1)", "(m[4] * b5 + m[6] * b2 - m[7] * b1)"),
        ("wrong_inv_m11", "(-m[8] * a4 + m[9] * a2 - m[11] * a0)", "(-m[8] * a4 - m[9] * a2 - m[11] * a0)"),
        ("wrong_id_copy_cnt", "i < 12u; ++i) {\n            dst[i]", "i < 11u; ++i) {\n            dst[i]"),
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
