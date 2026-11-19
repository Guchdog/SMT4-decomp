#!/usr/bin/env python3
"""Differential Unicorn test for camp_func_00233ac0 (0x00233ac0, 1100 B)."""

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

FUNC_ADDR = 0x00233AC0
FUNC_SIZE = 1100
FUNC_NAME = "camp_func_00233ac0"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

SELF_ADDR = 0x004A0000
G_SHOP_PTR = 0x00432FC8
SHOP_ADDR = 0x004A2000
TABLE_ADDR = 0x004A4000
HALT_ADDR = 0x004FFFF0

CALLEES = {
    0x00291000: "script_vm_func_00291000",
    0x00289F00: "script_vm_func_00289f00",
    0x002A8A8C: "ui_func_002a8a8c",
    0x002B8B78: "script_vm_func_002b8b78",
    0x002AE874: "camp_func_002ae874",
    0x002B8794: "camp_func_002b8794",
    0x002337A0: "shop_func_002337a0",
    0x0023378C: "engine_func_0023378c",
    0x00394338: "engine_func_00394338",
    0x002638FC: "PlaceWin_SetVisible",
    0x0029F10C: "camp_func_0029f10c",
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
                    else:
                        raise RuntimeError(f"Unexpected R_ARM_ABS32 section {s_shndx} ({s_name})")
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
    uc.mem_map(0x000F0000, 0x00010000)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(FUNC_ADDR, code_bytes)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(HALT_ADDR, struct.pack("<I", 0xE12FFF1E))

    uc.mem_write(SELF_ADDR, struct.pack("<I", case.get("self0", 0)))
    uc.mem_write(G_SHOP_PTR, struct.pack("<I", SHOP_ADDR))
    uc.mem_write(SHOP_ADDR + 0x678, struct.pack("<I", TABLE_ADDR))
    rec_idx = case.get("rec_idx", 2)
    rec_addr = TABLE_ADDR + rec_idx * 2504
    uc.mem_write(rec_addr + 0x9B3, bytes([case.get("rec_flag", 0)]))

    trace: list[tuple] = []

    def hook_code(uc_inst, address, size, user_data):
        name = NAME_BY_STUB.get(address)
        if name is None:
            return
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(UC_ARM_REG_R2)
        r3 = uc_inst.reg_read(UC_ARM_REG_R3)
        if name == "camp_func_002b8794":
            trace.append((name, r0, r1, r2, r3))
        elif name == "shop_func_002337a0":
            trace.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, rec_idx)
        elif name == "engine_func_0023378c":
            trace.append((name, r0, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("valid", 1))
        elif name == "engine_func_00394338":
            trace.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("kind", 0))
        elif name == "camp_func_0029f10c":
            trace.append((name, r0, r1))
        elif name in ("script_vm_func_00291000", "script_vm_func_00289f00", "script_vm_func_002b8b78", "PlaceWin_SetVisible"):
            trace.append((name, r0))
        else:
            trace.append((name,))

    uc.hook_add(UC_HOOK_CODE, hook_code)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_R1, case["state"] & 0xFFFFFFFF)
    uc.reg_write(UC_ARM_REG_R2, case.get("flag", 0))
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(FUNC_ADDR, HALT_ADDR, timeout=5_000_000, count=20_000)

    self0_after = struct.unpack("<I", uc.mem_read(SELF_ADDR, 4))[0]
    return {"self0": self0_after, "trace": trace}


def build_cases() -> list[dict]:
    return [
        {"name": "st_m1_clear", "state": -1, "self0": 0x00100001},
        {"name": "st_m1_nop", "state": -1, "self0": 0x00000001},
        {"name": "st0", "state": 0, "self0": 0},
        {"name": "st1_flag0", "state": 1, "flag": 0},
        {"name": "st1_flag1", "state": 1, "flag": 1},
        {"name": "st2_invalid", "state": 2, "flag": 1, "valid": 0},
        {"name": "st2_rec_flag1", "state": 2, "flag": 0, "valid": 1, "rec_flag": 1},
        {"name": "st2_kind0", "state": 2, "flag": 0, "valid": 1, "rec_flag": 0, "kind": 0},
        {"name": "st2_kind1", "state": 2, "flag": 0, "valid": 1, "rec_flag": 0, "kind": 1},
        {"name": "st2_kind2", "state": 2, "flag": 0, "valid": 1, "rec_flag": 0, "kind": 2},
        {"name": "st2_kind3", "state": 2, "flag": 0, "valid": 1, "rec_flag": 0, "kind": 3},
        {"name": "st2_kind4", "state": 2, "flag": 0, "valid": 1, "rec_flag": 0, "kind": 4},
        {"name": "st3_flag1", "state": 3, "flag": 1},
        {"name": "st3_flag0", "state": 3, "flag": 0},
        {"name": "st4_flag1", "state": 4, "flag": 1},
        {"name": "st4_flag0", "state": 4, "flag": 0},
        {"name": "st5_default", "state": 5, "self0": 0x123},
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
        ("wrong_m1_bit", "bits & ~0x100000u;", "bits & ~0x200000u;"),
        ("wrong_rec_stride", "table + idx2 * 2504;", "table + idx2 * 2500;"),
        ("wrong_rec_flag_off", "rec[0x9B3u]", "rec[0x9B2u]"),
        ("wrong_kind2_arg", "camp_func_002b8794(4u, 0x0Eu, 0x4Eu, 0u);", "camp_func_002b8794(4u, 0x0Eu, 0x4Fu, 0u);"),
        ("wrong_st4_se", "script_vm_func_002b8b78(0xCEu);", "script_vm_func_002b8b78(0xCFu);"),
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
