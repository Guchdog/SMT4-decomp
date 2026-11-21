#!/usr/bin/env python3
"""Differential Unicorn test for battle_func_003c4cec (0x003c4cec, 1140 B)."""

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

FUNC_ADDR = 0x003C4CEC
FUNC_SIZE = 1140
FUNC_NAME = "battle_func_003c4cec"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

SELF_ADDR = 0x004A0000
SUB_ADDR = 0x004A0100
MGR_ADDR = 0x004A0200
UNIT_ADDR = 0x004A1000
LINK0_ADDR = 0x004A2000
LINK1_ADDR = 0x004A2100
LINK2_ADDR = 0x004A2200
VAL_PTR_ADDR = 0x004A3000
HALT_ADDR = 0x004FFFF0

CALLEES = {
    0x002564CC: "battle_func_002564cc",
    0x00256418: "battle_func_00256418",
    0x0022A5F8: "battle_func_0022a5f8",
    0x00293C98: "ui_func_00293c98",
    0x0022A53C: "battle_func_0022a53c",
    0x0022A594: "battle_func_0022a594",
    0x002458D4: "script_vm_func_002458d4",
    0x0022A5D8: "battle_func_0022a5d8",
    0x00245888: "func_00245888",
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

    uc.mem_write(SELF_ADDR, b"\x00" * 0x40)
    uc.mem_write(SELF_ADDR + 0x10, struct.pack("<I", SUB_ADDR))
    uc.mem_write(SELF_ADDR + 0x1C, struct.pack("<I", 2))

    uc.mem_write(UNIT_ADDR, b"\x00" * 0x300)
    uc.mem_write(UNIT_ADDR + 0x00, struct.pack("<I", case.get("flags", 0x04001010)))
    uc.mem_write(UNIT_ADDR + 0xCE, struct.pack("<H", 0x0042))
    uc.mem_write(UNIT_ADDR + 0x1B4, struct.pack("<9h", 10, 20, 30, 40, 50, 60, 70, 80, 90))
    uc.mem_write(UNIT_ADDR + 0x278, struct.pack("<III", LINK0_ADDR, 0, LINK2_ADDR))
    uc.mem_write(LINK0_ADDR, b"\x00" * 0x40)
    uc.mem_write(LINK2_ADDR, b"\x00" * 0x40)
    uc.mem_write(VAL_PTR_ADDR, struct.pack("<I", case.get("ret_val", 123)))

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
        if name == "battle_func_002564cc":
            uc_inst.reg_write(UC_ARM_REG_R0, case["cmd"])
        elif name == "battle_func_00256418":
            trace.append((name, r0, r1, r2))
            uc_inst.reg_write(UC_ARM_REG_R0, 0 if case.get("unit_null") else UNIT_ADDR)
        elif name == "battle_func_0022a5f8":
            trace.append((name, r0, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, VAL_PTR_ADDR)
        elif name == "ui_func_00293c98":
            uc_inst.reg_write(UC_ARM_REG_R0, MGR_ADDR + 0x100)
        elif name == "battle_func_0022a53c":
            a4, a5 = struct.unpack("<II", uc_inst.mem_read(sp, 8))
            trace.append((name, r0, r1, r2, r3, a4, a5))
        elif name == "battle_func_0022a594":
            trace.append((name, r0, r1, r2))
        elif name == "script_vm_func_002458d4":
            trace.append((name, r0))
            uc_inst.reg_write(UC_ARM_REG_R0, 555)
        elif name == "battle_func_0022a5d8":
            trace.append((name, r0, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, case.get("chk_val", 1))
        elif name == "func_00245888":
            trace.append((name, r0, r1))

    uc.hook_add(UC_HOOK_CODE, hook_code)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_R1, MGR_ADDR)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(FUNC_ADDR, HALT_ADDR, timeout=5_000_000, count=20_000)

    return {
        "sel": struct.unpack("<I", uc.mem_read(SELF_ADDR + 0x1C, 4))[0],
        "unit_flags": struct.unpack("<I", uc.mem_read(UNIT_ADDR, 4))[0],
        "stats": struct.unpack("<9h", uc.mem_read(UNIT_ADDR + 0x1B4, 18)),
        "l0": struct.unpack("<hh", uc.mem_read(LINK0_ADDR + 0x2A, 4)),
        "l2": struct.unpack("<hh", uc.mem_read(LINK2_ADDR + 0x2A, 4)),
        "trace": trace,
    }


def build_cases() -> list[dict]:
    cases = [
        {"name": "cmd0_with_10", "cmd": 0, "flags": 0x04001010},
        {"name": "cmd0_no_10", "cmd": 0, "flags": 0x00000000},
        {"name": "cmd0_unit_null", "cmd": 0, "unit_null": True},
    ]
    for c in range(1, 10):
        cases.append({"name": f"cmd_{c}", "cmd": c, "ret_val": 100 + c})
    cases.extend([
        {"name": "cmd10_set", "cmd": 10, "chk_val": 1, "flags": 0},
        {"name": "cmd10_clr", "cmd": 10, "chk_val": 0, "flags": 0xFFFFFFFF},
        {"name": "cmd11_set", "cmd": 11, "chk_val": 1, "flags": 0},
        {"name": "cmd11_clr", "cmd": 11, "chk_val": 0, "flags": 0xFFFFFFFF},
        {"name": "cmd12_on", "cmd": 12, "flags": 0x10, "ret_val": 888},
        {"name": "cmd12_off", "cmd": 12, "flags": 0x00},
        {"name": "cmd1_unit_null", "cmd": 1, "unit_null": True},
        {"name": "cmd13_default", "cmd": 13},
    ])
    return cases


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
        ("wrong_kmax_5", "9999, 9999, 9999, 9999, 999,", "9999, 9999, 9999, 9999, 998,"),
        ("wrong_sync_off1", "sync_linked_stat_3c4cec(unit, 0x2Au, v);", "sync_linked_stat_3c4cec(unit, 0x2Cu, v);"),
        ("wrong_flag10_bit", "if (battle_func_0022a5d8(sub, 10u) != 0) {\n                    *reinterpret_cast<u32*>(unit) |= 0x1000u;", "if (battle_func_0022a5d8(sub, 10u) != 0) {\n                    *reinterpret_cast<u32*>(unit) |= 0x2000u;"),
        ("wrong_flag11_shift", ">> 26u);", ">> 25u);"),
        ("wrong_cmd12_mask", "& 0x10u) != 0u) {\n                func_00245888", "& 0x20u) != 0u) {\n                func_00245888"),
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
