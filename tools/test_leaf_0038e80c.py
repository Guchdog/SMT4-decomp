#!/usr/bin/env python3
"""Differential Unicorn test for engine_func_0038e80c (0x0038e80c, 1172 B)."""

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
    UC_ARM_REG_SP,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x0038E80C
FUNC_SIZE = 1172
FUNC_NAME = "engine_func_0038e80c"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

SELF_ADDR = 0x00600000
OBJ_ADDR = 0x00601000
VTBL_ADDR = 0x00602000
NEW_TASK_ADDR = 0x00603000
SHOP_ADDR = 0x00604000
SUB_ADDR = 0x00605000
SHOP_PTR_GLOBAL = 0x00432FC8
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x00234278: "engine_func_00234278",
    0x0027EC84: "camp_func_0027ec84",
    0x00233F4C: "engine_func_00233f4c",
    0x00234160: "engine_func_00234160",
    0x00234004: "engine_func_00234004",
    0x0026B7CC: "ui_func_0026b7cc",
    0x002A17C0: "engine_func_002a17c0",
    0x00233F0C: "battle_func_00233f0c",
    0x002342B8: "func_002342b8",
    0x002C4B30: "engine_func_002c4b30",
    0x00233AC0: "camp_func_00233ac0",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
STUB_VTBL_DTOR = STUB_BASE + 0x100
STUB_VTBL_GET_RESULT = STUB_BASE + 0x104
STUB_BY_NAME["vtbl_dtor"] = STUB_VTBL_DTOR
STUB_BY_NAME["vtbl_get_result"] = STUB_VTBL_GET_RESULT
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
) -> tuple[list[tuple], bytes, bytes, bytes]:
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

    self_init = bytearray(0x300)
    struct.pack_into("<IIII", self_init, 0, case["flags"], case.get("f4", 0), case["state"], case.get("cnt", 0))
    struct.pack_into("<I", self_init, 0x208, OBJ_ADDR if case.get("has_obj", True) else 0)
    uc.mem_write(SELF_ADDR, bytes(self_init))

    uc.mem_write(OBJ_ADDR, struct.pack("<I", VTBL_ADDR))
    uc.mem_write(VTBL_ADDR, struct.pack("<IIII", 0, STUB_VTBL_DTOR, 0, STUB_VTBL_GET_RESULT))
    uc.mem_write(NEW_TASK_ADDR, b"\x00" * 0x100)

    shop_init = bytearray(0x800)
    for i in range(0x694, 0x6D4, 4):
        struct.pack_into("<I", shop_init, i, 0xAAAAAAAA)
    struct.pack_into("<I", shop_init, 0x688, SUB_ADDR)
    uc.mem_write(SHOP_ADDR, bytes(shop_init))
    uc.mem_write(SHOP_PTR_GLOBAL, struct.pack("<I", SHOP_ADDR))

    sub_init = bytearray(0xA00)
    struct.pack_into("<H", sub_init, 0x9AA, 0xBEEF)
    uc.mem_write(SUB_ADDR, bytes(sub_init))

    trace: list[tuple] = []

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

        if name == "engine_func_00234278":
            trace.append((name,))
            u.mem_write(r0, b"\x00" * 20)
        elif name == "vtbl_get_result":
            trace.append((name, r1))
            st_b = struct.pack("<5I", case.get("st0", 0), 0x11, 0x22, 0x33, 0x44)
            u.mem_write(r0, st_b)
        elif name == "vtbl_dtor":
            trace.append((name, r0))
        elif name == "camp_func_0027ec84":
            st = struct.unpack_from("<5I", u.mem_read(r0, 20))
            trace.append((name, st))
            u.reg_write(UC_ARM_REG_R0, case.get("done", 0))
        elif name == "engine_func_002a17c0":
            st = struct.unpack_from("<5I", u.mem_read(r0, 20))
            trace.append((name, st))
            u.reg_write(UC_ARM_REG_R0, case.get("err", 0))
        elif name == "ui_func_0026b7cc":
            trace.append((name,))
            u.reg_write(UC_ARM_REG_R0, case.get("ui", 0))
        elif name == "engine_func_00234160":
            trace.append((name, r0, r1))
            u.reg_write(UC_ARM_REG_R0, NEW_TASK_ADDR)
        elif name == "engine_func_00233f4c":
            trace.append((name, r0, r1))
        elif name == "battle_func_00233f0c":
            trace.append((name, r0))
        elif name == "func_002342b8":
            arg = struct.unpack_from("<5I", u.mem_read(r1, 20))
            trace.append((name, r0, arg))
        elif name == "engine_func_002c4b30":
            trace.append((name, r0, r1))
        elif name == "camp_func_00233ac0":
            trace.append((name, r0, r1, r2))
        elif name == "engine_func_00234004":
            trace.append((name, r0, r1, r2))

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(entry_addr, HALT_ADDR, timeout=5_000_000)

    return (
        trace,
        bytes(uc.mem_read(SELF_ADDR, 0x300)),
        bytes(uc.mem_read(SHOP_ADDR, 0x800)),
        bytes(uc.mem_read(NEW_TASK_ADDR, 0x100)),
    )


CASES = [
    {"name": "state0_ok", "state": 0, "flags": 0x200, "ui": 1},
    {"name": "state0_no_flag", "state": 0, "flags": 0, "ui": 1},
    {"name": "state0_ui_zero", "state": 0, "flags": 0x200, "ui": 0},
    {"name": "state1_no_flag", "state": 1, "flags": 0},
    {"name": "state1_done", "state": 1, "flags": 0x200, "done": 1},
    {"name": "state1_err_66", "state": 1, "flags": 0x200, "done": 0, "err": 1, "st0": 0x66},
    {"name": "state1_err_67", "state": 1, "flags": 0x200, "done": 0, "err": 1, "st0": 0x67},
    {"name": "state1_err_other", "state": 1, "flags": 0x200, "done": 0, "err": 1, "st0": 0x99},
    {"name": "state1_pending", "state": 1, "flags": 0x200, "done": 0, "err": 0},
    {"name": "state2_with_obj", "state": 2, "flags": 0, "has_obj": True},
    {"name": "state2_null_obj", "state": 2, "flags": 0, "has_obj": False},
    {"name": "state3_done", "state": 3, "flags": 0, "done": 1},
    {"name": "state3_err_66_ignored", "state": 3, "flags": 0, "done": 0, "err": 1, "st0": 0x66},
    {"name": "state4_done", "state": 4, "flags": 0x200, "done": 1},
    {"name": "state4_err_67", "state": 4, "flags": 0x200, "done": 0, "err": 1, "st0": 0x67},
    {"name": "state5_ok", "state": 5, "flags": 0},
    {"name": "state6_done", "state": 6, "flags": 0, "done": 1},
    {"name": "state6_err_other", "state": 6, "flags": 0, "done": 0, "err": 1, "st0": 0x12},
    {"name": "state7_wait", "state": 7, "flags": 0, "cnt": 2},
    {"name": "state7_done", "state": 7, "flags": 0, "cnt": 1},
    {"name": "state_270f_match", "state": 0x270F, "flags": 0, "f4": 6},
    {"name": "state_270f_nomatch", "state": 0x270F, "flags": 0, "f4": 5},
    {"name": "state_oob", "state": 8, "flags": 0},
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
            return 1
    print(f"PASS {len(CASES)} cases (all 9 states + branches + OOB)")

    muts = [
        (
            "neg_state0_flag_bit",
            "        case 0:\n"
            "            if (ui_func_0026b7cc() != 0 && (*reinterpret_cast<const u32*>(self) & 0x200u) != 0u) {",
            "        case 0:\n"
            "            if (ui_func_0026b7cc() != 0 && (*reinterpret_cast<const u32*>(self) & 0x100u) != 0u) {",
        ),
        (
            "neg_state3_check_fg",
            "            } else if (engine_func_002a17c0(st) != 0) {\n"
            "                handle_task_error_38e80c(self, st, false);",
            "            } else if (engine_func_002a17c0(st) != 0) {\n"
            "                handle_task_error_38e80c(self, st, true);",
        ),
        (
            "neg_state5_u16_offset",
            "            *reinterpret_cast<u32*>(task + 0x14u) = *reinterpret_cast<const u16*>(sub + 0x9AAu);",
            "            *reinterpret_cast<u32*>(task + 0x14u) = *reinterpret_cast<const u16*>(sub + 0x9ACu);",
        ),
        (
            "neg_state6_clear_len",
            "                u32* const cleared = reinterpret_cast<u32*>(shop + 0x694u);\n"
            "                for (u32 i = 0u; i < 16u; ++i) {",
            "                u32* const cleared = reinterpret_cast<u32*>(shop + 0x694u);\n"
            "                for (u32 i = 0u; i < 15u; ++i) {",
        ),
        (
            "neg_state7_cnt_cmp",
            "        case 7: {\n"
            "            const s32 cnt = *reinterpret_cast<const s32*>(self + 0x0Cu) - 1;\n"
            "            *reinterpret_cast<s32*>(self + 0x0Cu) = cnt;\n"
            "            if (cnt > 0) {",
            "        case 7: {\n"
            "            const s32 cnt = *reinterpret_cast<const s32*>(self + 0x0Cu) - 1;\n"
            "            *reinterpret_cast<s32*>(self + 0x0Cu) = cnt;\n"
            "            if (cnt >= 0) {",
        ),
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
