#!/usr/bin/env python3
"""Differential Unicorn test for engine_func_001f4480 (0x001f4480, 1140 B)."""

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

FUNC_ADDR = 0x001F4480
FUNC_SIZE = 1140
FUNC_NAME = "engine_func_001f4480"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

OUT_ADDR = 0x004A0000
REC_ADDR = 0x004A1000
HALT_ADDR = 0x004FFFF0

CALLEES = {
    0x00258074: "script_vm_func_00258074",
    0x00258040: "script_vm_func_00258040",
    0x00269E34: "script_vm_func_00269e34",
    0x00258020: "script_vm_func_00258020",
    0x002B087C: "battle_func_002b087c",
    0x002B67E0: "engine_func_002b67e0",
    0x002BE7FC: "ui_func_002be7fc",
    0x002C3290: "engine_func_002c3290",
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


def read_cstr(uc: Uc, addr: int) -> bytes:
    buf = bytes(uc.mem_read(addr, 256))
    return buf.split(b"\x00", 1)[0]


def run_one(code_bytes: bytes, rodata_blobs: list[tuple[int, bytes]], code_bin: bytes, case: dict) -> dict:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x000F0000, 0x00010000)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    # Copy pinned .rodata strings/tables from code.bin
    uc.mem_write(0x00402540, code_bin[0x00402540 - CODE_BASE : 0x004026A0 - CODE_BASE])
    uc.mem_write(FUNC_ADDR, code_bytes)
    for base, blob in rodata_blobs:
        uc.mem_write(base, blob)
    for stub_addr in NAME_BY_STUB:
        uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(HALT_ADDR, struct.pack("<I", 0xE12FFF1E))

    uc.mem_write(OUT_ADDR, b"\xAA" * 0x80)
    uc.mem_write(REC_ADDR, b"\x00" * 0x60)
    for e, raw in case.get("rec_map", {}).items():
        uc.mem_write(REC_ADDR + 0x24 + e * 2, struct.pack("<H", raw))

    kinds = case.get("kinds", {})
    vals = case.get("vals", {})

    def hook_code(uc_inst, address, size, user_data):
        name = NAME_BY_STUB.get(address)
        if name is None:
            return
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        if name == "script_vm_func_00258074":
            uc_inst.reg_write(UC_ARM_REG_R0, kinds.get(r0, 0))
        elif name == "script_vm_func_00258040":
            uc_inst.reg_write(UC_ARM_REG_R0, vals.get(r0, 100))
        elif name == "script_vm_func_00269e34":
            uc_inst.reg_write(UC_ARM_REG_R0, kinds.get(r1, 0))
        elif name == "script_vm_func_00258020":
            uc_inst.reg_write(UC_ARM_REG_R0, vals.get(r1, 100))
        elif name == "battle_func_002b087c":
            uc_inst.reg_write(UC_ARM_REG_R0, REC_ADDR)
        elif name == "ui_func_002be7fc":
            s = read_cstr(uc_inst, r1)
            uc_inst.mem_write(r0, s + b"\x00")
        elif name == "engine_func_002b67e0":
            cur = read_cstr(uc_inst, r0)
            add = read_cstr(uc_inst, r1)
            uc_inst.mem_write(r0, cur + add + b"\x00")
        elif name == "engine_func_002c3290":
            uc_inst.reg_write(UC_ARM_REG_R0, len(read_cstr(uc_inst, r0)))

    uc.hook_add(UC_HOOK_CODE, hook_code)
    uc.reg_write(UC_ARM_REG_R0, case.get("a0", 0))
    uc.reg_write(UC_ARM_REG_R1, case.get("a1", 0))
    uc.reg_write(UC_ARM_REG_R2, case.get("a2", 0))
    uc.reg_write(UC_ARM_REG_R3, OUT_ADDR)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(FUNC_ADDR, HALT_ADDR, timeout=5_000_000, count=30_000)

    return {"out": bytes(uc.mem_read(OUT_ADDR, 0x64))}


def build_cases() -> list[dict]:
    return [
        {"name": "a0_mixed", "a0": 1, "kinds": {11: 1, 12: 2, 13: 0, 14: 0, 15: 1}, "vals": {13: 50, 14: 100}},
        {"name": "a1_all_none", "a0": 0, "a1": 10, "kinds": {}, "vals": {}},
        {"name": "a1_mixed", "a0": 0, "a1": 10, "kinds": {11: 2, 12: 0, 13: 1, 14: 0, 15: 2}, "vals": {12: 99, 14: 100}},
        {"name": "a2_rec_all_five_trunc", "a0": 0, "a1": 0, "a2": 7, "rec_map": {11: 1 << 10, 12: 2 << 10, 13: 50, 14: 99, 15: 2 << 10}},
    ]


def verify(cpp_text: str) -> tuple[bool, int, str]:
    cand_code, rodata_blobs, cand_size = compile_candidate(cpp_text)
    code_bin = CODE_BIN.read_bytes()
    orig_code = patch_orig_bl(code_bin[FUNC_ADDR - CODE_BASE : FUNC_ADDR - CODE_BASE + FUNC_SIZE])

    for case in build_cases():
        orig_res = run_one(orig_code, [], code_bin, case)
        cand_res = run_one(cand_code, rodata_blobs, code_bin, case)
        if orig_res != cand_res:
            return False, cand_size, f"FAIL {case['name']}:\n  orig={orig_res}\n  cand={cand_res}"
    return True, cand_size, "OK"


def run_negative_controls(cpp_text: str) -> None:
    mutations = [
        ("wrong_res_thresh", "(raw & 0x3FFu) < 0x64u", "(raw & 0x3FFu) < 0x63u"),
        ("wrong_kind_shift", "raw >> 10u;", "raw >> 11u;"),
        ("wrong_sep", '"\\x81\\x5E"', '"\\x81\\x5F"'),
        ("wrong_trunc_limit", ">= 0x5Du)", ">= 0x90u)"),
        ("wrong_no_ailment", '"\\x82\\x6D\\x82\\x8F\\x81\\x40', '"\\x82\\x6E\\x82\\x8F\\x81\\x40'),
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
