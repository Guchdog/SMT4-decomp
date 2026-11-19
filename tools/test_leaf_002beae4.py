#!/usr/bin/env python3
"""Differential Unicorn test for battle_func_002beae4 (0x002beae4, 1072 B)."""

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

FUNC_ADDR = 0x002BEAE4
FUNC_SIZE = 1072
FUNC_NAME = "battle_func_002beae4"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

INFO_ADDR = 0x004A0000
DIMS_ADDR = 0x004A0100
G_UI_PTR_ADDR = 0x0044EA00
G_UI_OBJ_ADDR = 0x004A1000
TEX_CB_STUB = STUB_BASE + 0x40
HALT_ADDR = 0x004FFFF0

CALLEES = {
    0x002BF6D0: "camp_func_002bf6d0",
    0x002B0908: "func_002b0908",
    0x002C5FA4: "battle_func_002c5fa4",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
STUB_BY_NAME["tex_cb"] = TEX_CB_STUB
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

    # Info + dims
    uc.mem_write(INFO_ADDR + 0x0C, struct.pack("<I", DIMS_ADDR))
    uc.mem_write(DIMS_ADDR, struct.pack("<hh", case.get("full_w", 120), case.get("h", 12)))

    # Global UI object at 0x0044EA00
    uc.mem_write(G_UI_PTR_ADDR, struct.pack("<I", G_UI_OBJ_ADDR))
    p_addr = G_UI_OBJ_ADDR + 0x12AC
    uc.mem_write(p_addr, b"\x00" * 0x24)
    uc.mem_write(p_addr + 0x00, struct.pack("<I", 1))  # idx = 1
    uc.mem_write(p_addr + 0x08 + 4, struct.pack("<I", case.get("old_tex", 0)))
    uc.mem_write(p_addr + 0x18, bytes([case.get("dirty", 0)]))
    uc.mem_write(p_addr + 0x1C, struct.pack("<I", TEX_CB_STUB))

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
        if name == "camp_func_002bf6d0":
            trace.append(("info", r0, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, INFO_ADDR)
        elif name == "func_002b0908":
            y_bits, w, h, z_bits = struct.unpack("<IIiI", uc_inst.mem_read(sp, 16))
            trace.append(("draw", r0, r1, r2, r3, y_bits, w, h, z_bits))
        elif name == "battle_func_002c5fa4":
            val = 1000 + r1
            trace.append(("get_tex", r0, r1, r2))
            uc_inst.reg_write(UC_ARM_REG_R0, val)
        elif name == "tex_cb":
            trace.append(("tex_cb", r0))

    uc.hook_add(UC_HOOK_CODE, hook_code)

    uc.reg_write(UC_ARM_REG_R0, case["cur"] & 0xFFFFFFFF)
    uc.reg_write(UC_ARM_REG_R1, case["max"] & 0xFFFFFFFF)
    uc.reg_write(UC_ARM_REG_R2, case["delta"] & 0xFFFFFFFF)
    uc.reg_write(UC_ARM_REG_R3, case["step"] & 0xFFFFFFFF)

    stack_args = struct.pack(
        "<IIIIIIIII",
        case.get("a4", 5),
        case.get("color", 0x11111111),
        case.get("heal_color", 0x22222222),
        case.get("dmg_color", 0x33333333),
        case.get("low_color", 0x44444444),
        case.get("x", 100) & 0xFFFFFFFF,
        0x42480000,  # 50.0f
        0x3F800000,  # 1.0f
        case.get("skip_main", 0),
    )
    uc.mem_write(STACK_TOP, stack_args)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)

    uc.emu_start(FUNC_ADDR, HALT_ADDR, timeout=5_000_000, count=20_000)

    dirty_after = uc.mem_read(p_addr + 0x18, 1)[0]
    slot_after = struct.unpack("<I", uc.mem_read(p_addr + 0x0C, 4))[0]
    return {"dirty": dirty_after, "slot": slot_after, "trace": trace}


def build_cases() -> list[dict]:
    return [
        {"name": "delta0_normal", "cur": 80, "max": 100, "delta": 0, "step": 0},
        {"name": "delta0_above_low_25", "cur": 25, "max": 100, "delta": 0, "step": 0},
        {"name": "delta0_low_hp", "cur": 20, "max": 100, "delta": 0, "step": 0},
        {"name": "delta0_zero_cur", "cur": 0, "max": 100, "delta": 0, "step": 0},
        {"name": "heal_step0_skip0", "cur": 30, "max": 100, "delta": 40, "step": 0},
        {"name": "heal_step18_anim_skip1", "cur": 30, "max": 100, "delta": 40, "step": 18, "skip_main": 1, "dirty": 1},
        {"name": "heal_step21_done", "cur": 30, "max": 100, "delta": 40, "step": 21},
        {"name": "heal_clamp_max", "cur": 90, "max": 100, "delta": 50, "step": 5},
        {"name": "dmg_step0_skip0", "cur": 80, "max": 100, "delta": -30, "step": 0},
        {"name": "dmg_step14_anim_skip1", "cur": 80, "max": 100, "delta": -50, "step": 14, "skip_main": 1, "old_tex": 99},
        {"name": "dmg_step25_done", "cur": 80, "max": 100, "delta": -30, "step": 25},
        {"name": "dmg_clamp_zero", "cur": 10, "max": 100, "delta": -50, "step": 5},
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
        ("wrong_low_pct", "s32 thresh = (q12_max / 100) * 20;", "s32 thresh = (q12_max / 100) * 30;"),
        ("wrong_anim_scale", "static_cast<f32>(diff) * 0.1f *", "static_cast<f32>(diff) * 0.2f *"),
        ("wrong_step_bound", "if (static_cast<u32>(step - 11) <= 9u) {\n            const u32 anim = static_cast<u32>(static_cast<f32>(diff)", "if (static_cast<u32>(step - 11) <= 5u) {\n            const u32 anim = static_cast<u32>(static_cast<f32>(diff)"),
        ("wrong_tex_after_delta", "set_tex_002beae4(7u);", "set_tex_002beae4(8u);"),
        ("wrong_dmg_x", "draw_delta_002beae4(a4, dmg_color, x + static_cast<s32>(w_next)", "draw_delta_002beae4(a4, dmg_color, x + static_cast<s32>(w_cur)"),
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
