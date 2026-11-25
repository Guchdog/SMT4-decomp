#!/usr/bin/env python3
"""Differential Unicorn test for engine_func_00280054 (0x00280054, 1408 B)."""

from __future__ import annotations

import math
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
    UC_ARM_REG_S0,
    UC_ARM_REG_S1,
    UC_ARM_REG_S2,
    UC_ARM_REG_S3,
    UC_ARM_REG_S4,
    UC_ARM_REG_S5,
    UC_ARM_REG_SP,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x00280054
FUNC_SIZE = 1408
FUNC_NAME = "engine_func_00280054"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

DATA_BASE = 0x00600000
DATA_SIZE = 0x00040000
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x00280BF8: "script_vm_func_00280bf8",
    0x00287D54: "engine_func_00287d54",
    0x0028277C: "script_vm_func_0028277c",
    0x00282600: "script_vm_func_00282600",
    0x002526BC: "engine_func_002526bc",
    0x00287E4C: "script_vm_func_00287e4c",
    0x0027FE84: "script_vm_func_0027fe84",
    0x002B8B78: "script_vm_func_002b8b78",
    0x0024F248: "engine_func_0024f248",
    0x001FA6BC: "engine_func_001fa6bc",
    0x0027F10C: "script_vm_func_0027f10c",
    0x002BFFBC: "ui_func_002bffbc",
    0x00276550: "script_vm_func_00276550",
    0x002DFE6C: "engine_func_002dfe6c",
    0x00273A98: "script_vm_func_00273a98",
    0x00273A78: "script_vm_func_00273a78",
    0x002D3DAC: "engine_func_002d3dac",
    0x00276BA4: "script_vm_func_00276ba4",
    0x0027FD08: "script_vm_func_0027fd08",
    0x0027F6FC: "script_vm_func_0027f6fc",
    0x0028075C: "script_vm_func_0028075c",
    0x002805D4: "script_vm_func_002805d4",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
NAME_BY_STUB = {v: k for k, v in STUB_BY_NAME.items()}

G_CAM = 0x00447E88
G_4F4 = 0x004474F4
G_S = 0x0049F91C

CAM_ADDR = DATA_BASE + 0x1000
P4F4_ADDR = DATA_BASE + 0x1400


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

    for idx in range(symtab[5] // 16):
        name, val, shndx = sym_info(idx)
        if name in STUB_BY_NAME and shndx == func_shndx:
            stub = STUB_BY_NAME[name]
            rel = ((stub - (CODE_BASE + val + 8)) >> 2) & 0x00FFFFFF
            struct.pack_into("<I", text_bytes, val, 0xEA000000 | rel)

    rodata_blobs: list[tuple[int, bytes]] = []
    rodata_map: dict[int, int] = {}
    next_ro = RODATA_BASE
    for idx, sh in enumerate(sections):
        sname = sec_name(idx)
        if sname.startswith(".rodata"):
            blob = elf[sh[4] : sh[4] + sh[5]]
            rodata_map[idx] = next_ro
            rodata_blobs.append((next_ro, blob))
            next_ro += (len(blob) + 0x1F) & ~0x1F

    for idx, sh in enumerate(sections):
        if sh[1] != 9:
            continue
        if sec_name(sh[7]) != text_name:
            continue
        for pos in range(0, sh[5], 8):
            r_off, r_info = struct.unpack_from("<II", elf, sh[4] + pos)
            r_type = r_info & 0xFF
            sym_idx = r_info >> 8
            sname, sval, sshndx = sym_info(sym_idx)

            is_in_func = func_val <= r_off < func_val + func_size
            if not is_in_func and not (r_type in (28, 29) and sname in STUB_BY_NAME):
                continue

            if sname in STUB_BY_NAME:
                target = STUB_BY_NAME[sname]
            elif sshndx in rodata_map:
                target = rodata_map[sshndx] + sval
            elif sshndx == func_shndx:
                target = CODE_BASE + sval
            else:
                raise RuntimeError(f"Unhandled reloc {sname!r} type={r_type} at 0x{r_off:x}")

            if r_type in (28, 29):
                insn = struct.unpack_from("<I", text_bytes, r_off)[0]
                rel = ((target - (CODE_BASE + r_off + 8)) >> 2) & 0x00FFFFFF
                struct.pack_into("<I", text_bytes, r_off, (insn & 0xFF000000) | rel)
            elif r_type == 2:
                addend = struct.unpack_from("<i", text_bytes, r_off)[0]
                struct.pack_into("<I", text_bytes, r_off, target + addend)
            elif r_type == 43:
                insn = struct.unpack_from("<I", text_bytes, r_off)[0]
                imm16 = target & 0xFFFF
                struct.pack_into("<I", text_bytes, r_off, (insn & 0xFFF0F000) | ((imm16 >> 12) << 16) | (imm16 & 0xFFF))
            elif r_type == 44:
                insn = struct.unpack_from("<I", text_bytes, r_off)[0]
                imm16 = (target >> 16) & 0xFFFF
                struct.pack_into("<I", text_bytes, r_off, (insn & 0xFFF0F000) | ((imm16 >> 12) << 16) | (imm16 & 0xFFF))
            else:
                raise RuntimeError(f"Unsupported r_type={r_type} for {sname!r}")

    return bytes(text_bytes), rodata_blobs, CODE_BASE + func_val


def patch_orig_bl(code: bytearray) -> None:
    for off in range(FUNC_ADDR - CODE_BASE, FUNC_ADDR - CODE_BASE + FUNC_SIZE, 4):
        insn = struct.unpack_from("<I", code, off)[0]
        top = (insn >> 24) & 0xFF
        if ((top & 0x0E) == 0x0A and top < 0xF0) or top in (0xFA, 0xFB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = CODE_BASE + off + 8
            target = pc + (imm24 << 2)
            if target in CALLEES:
                stub = STUB_BY_NAME[CALLEES[target]]
                rel = ((stub - pc) >> 2) & 0x00FFFFFF
                op = 0xEB000000 if top in (0xFA, 0xFB) else (insn & 0xFF000000)
                struct.pack_into("<I", code, off, op | rel)
    # 0x002805D0 is `mov r0, r0` falling through into script_vm_func_002805d4
    tail_off = 0x002805D0 - CODE_BASE
    stub = STUB_BY_NAME["script_vm_func_002805d4"]
    rel = ((stub - (0x002805D0 + 8)) >> 2) & 0x00FFFFFF
    struct.pack_into("<I", code, tail_off, 0xEA000000 | rel)


def run_side(
    code_bytes: bytes,
    rodata_blobs: list[tuple[int, bytes]],
    entry: int,
    cfg: dict,
) -> tuple[list, bytes, bytes]:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, code_bytes)

    uc.mem_map(STUB_BASE, 0x2000)
    for addr in NAME_BY_STUB:
        uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))

    uc.mem_map(RODATA_BASE, 0x20000)
    for addr, blob in rodata_blobs:
        uc.mem_write(addr, blob)

    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(0x006F0000, 0x10000)
    uc.mem_write(HALT_ADDR, struct.pack("<I", 0xE320F000))

    uc.mem_write(G_CAM, struct.pack("<I", CAM_ADDR))
    uc.mem_write(G_4F4, struct.pack("<I", P4F4_ADDR))
    uc.mem_write(G_S, b"\x00" * 0x240)

    uc.mem_write(CAM_ADDR, b"\x00" * 0x140)
    uc.mem_write(CAM_ADDR + 0x04, struct.pack("<ii", cfg["state"], cfg.get("timer", 0)))
    uc.mem_write(CAM_ADDR + 0x1C, struct.pack("<fff", 10.0, 20.0, 30.0))
    uc.mem_write(CAM_ADDR + 0x28, struct.pack("<fff", *cfg.get("cam_pos", (40.0, 50.0, 60.0))))
    uc.mem_write(CAM_ADDR + 0x4C, struct.pack("<ff", 15.0, 45.0))
    uc.mem_write(CAM_ADDR + 0x115, bytes([cfg.get("f115", 0)]))
    uc.mem_write(CAM_ADDR + 0x118, struct.pack("<fff", *cfg.get("tgt_pos", (100.0, 50.0, 120.0))))
    uc.mem_write(CAM_ADDR + 0x124, struct.pack("<fff", 0.6, 0.0, 0.8))
    uc.mem_write(CAM_ADDR + 0x130, struct.pack("<f", cfg.get("step", 30.0)))

    uc.mem_write(G_S + 0x80, struct.pack("<I", 0x777))
    uc.mem_write(G_S + 0x84, struct.pack("<fff", *cfg.get("s_pos", (50.0, 50.0, 70.0))))
    uc.mem_write(G_S + 0x22A, bytes([1]))

    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)

    trace: list = []

    def f_from_reg(reg) -> float:
        bits = uc.reg_read(reg)
        return round(struct.unpack("<f", struct.pack("<I", bits))[0], 4)

    def f_to_reg(reg, val: float) -> None:
        uc.reg_write(reg, struct.unpack("<I", struct.pack("<f", val))[0])

    def hook(uc_inst, address, size, user_data):
        name = NAME_BY_STUB.get(address)
        if name is None:
            return
        a0 = uc_inst.reg_read(UC_ARM_REG_R0)
        a1 = uc_inst.reg_read(UC_ARM_REG_R1)

        if name == "script_vm_func_00280bf8":
            trace.append((name,))
        elif name == "engine_func_00287d54":
            dx = f_from_reg(UC_ARM_REG_S0) - f_from_reg(UC_ARM_REG_S3)
            dy = f_from_reg(UC_ARM_REG_S1) - f_from_reg(UC_ARM_REG_S4)
            dz = f_from_reg(UC_ARM_REG_S2) - f_from_reg(UC_ARM_REG_S5)
            d = math.sqrt(dx * dx + dy * dy + dz * dz)
            f_to_reg(UC_ARM_REG_S0, d)
            trace.append((name, round(d, 3)))
        elif name == "script_vm_func_0028277c":
            ang = f_from_reg(UC_ARM_REG_S0)
            f_to_reg(UC_ARM_REG_S0, math.sin(ang))
            trace.append((name, ang))
        elif name == "script_vm_func_00282600":
            ang = f_from_reg(UC_ARM_REG_S0)
            f_to_reg(UC_ARM_REG_S0, math.cos(ang))
            trace.append((name, ang))
        elif name == "engine_func_002526bc":
            vals = (f_from_reg(UC_ARM_REG_S0), f_from_reg(UC_ARM_REG_S1), f_from_reg(UC_ARM_REG_S2),
                    f_from_reg(UC_ARM_REG_S3), f_from_reg(UC_ARM_REG_S4))
            uc_inst.mem_write(a0, struct.pack("<fff", 0.6, 0.0, 0.8))
            trace.append((name, vals))
        elif name == "script_vm_func_00287e4c":
            f_to_reg(UC_ARM_REG_S0, 77.5)
            trace.append((name, f_from_reg(UC_ARM_REG_S0), f_from_reg(UC_ARM_REG_S3)))
        elif name in ("script_vm_func_0027fe84", "script_vm_func_002b8b78", "script_vm_func_0027fd08"):
            trace.append((name, a0))
        elif name == "engine_func_0024f248":
            trace.append((name, a0, a1))
        elif name == "engine_func_001fa6bc":
            trace.append((name, f_from_reg(UC_ARM_REG_S0), f_from_reg(UC_ARM_REG_S1),
                          f_from_reg(UC_ARM_REG_S2), f_from_reg(UC_ARM_REG_S3)))
        elif name == "script_vm_func_0027f10c":
            ret = cfg.get("ret_27f10c", 0)
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, ret))
        elif name == "ui_func_002bffbc":
            ret = cfg.get("ret_2bffbc", 0)
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, a0, ret))
        elif name == "script_vm_func_00276550":
            ret = cfg.get("ret_276550", 0)
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, ret))
        elif name == "script_vm_func_00273a78":
            ret = cfg.get("ret_273a78", 0)
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, ret))
        elif name == "script_vm_func_0027f6fc":
            ret = cfg.get("ret_27f6fc", 0)
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, a0 - CAM_ADDR, a1 - CAM_ADDR, ret))
        elif name == "script_vm_func_0028075c":
            trace.append((name, a0 - CAM_ADDR))
        elif name == "script_vm_func_002805d4":
            trace.append((name, f_from_reg(UC_ARM_REG_S0), f_from_reg(UC_ARM_REG_S1)))
        else:
            trace.append((name,))

    uc.hook_add(UC_HOOK_CODE, hook, begin=STUB_BASE, end=STUB_BASE + 0x1000)
    uc.emu_start(entry, HALT_ADDR, timeout=5_000_000, count=200_000)

    return trace, bytes(uc.mem_read(CAM_ADDR, 0x134)), bytes(uc.mem_read(P4F4_ADDR, 0xB0))


def make_cases() -> list[tuple[str, dict]]:
    return [
        ("state0_near", {"state": 0, "cam_pos": (40.0, 50.0, 60.0), "s_pos": (50.0, 50.0, 70.0)}),
        ("state0_far", {"state": 0, "cam_pos": (0.0, 0.0, 0.0), "s_pos": (200.0, 0.0, 0.0)}),
        ("state1_wait", {"state": 1, "timer": 1}),
        ("state1_advance", {"state": 1, "timer": 2}),
        ("state2_f10c", {"state": 2, "ret_27f10c": 1}),
        ("state2_bffbc", {"state": 2, "ret_2bffbc": 1}),
        ("state2_6550", {"state": 2, "ret_276550": 1}),
        ("state2_idle", {"state": 2}),
        ("state10", {"state": 10}),
        ("state11_wait", {"state": 11, "timer": 5}),
        ("state11_fire", {"state": 11, "timer": 19}),
        ("state12_wait", {"state": 12, "ret_273a78": 1}),
        ("state12_fire", {"state": 12, "ret_273a78": 0}),
        ("state13_wait", {"state": 13, "timer": 10}),
        ("state13_fire", {"state": 13, "timer": 19}),
        ("state5a", {"state": 0x5A}),
        ("state5b", {"state": 0x5B}),
        ("state5c_wait", {"state": 0x5C, "timer": 2}),
        ("state5c_fire", {"state": 0x5C, "timer": 3}),
        ("default_snap_f115", {"state": 99, "f115": 1, "cam_pos": (95.0, 50.0, 120.0), "tgt_pos": (100.0, 50.0, 120.0), "step": 30.0}),
        ("default_step_f115_hit", {"state": 99, "f115": 1, "cam_pos": (0.0, 50.0, 0.0), "tgt_pos": (100.0, 50.0, 100.0), "step": 10.0, "ret_27f6fc": 1}),
    ]


def main() -> int:
    raw = bytearray(CODE_BIN.read_bytes())
    patch_orig_bl(raw)
    orig_code = bytes(raw)

    with tempfile.TemporaryDirectory() as tmpdir:
        obj_path = Path(tmpdir) / "leaf_batch45_c.o"
        res = compile_tu_armv6k(SRC_CPP, obj_path)
        if res.returncode != 0:
            print(f"COMPILE ERROR:\n{res.stderr}")
            return 1
        cand_code, rodata_blobs, cand_entry = patch_cand_elf(obj_path)

    cases = make_cases()
    for name, cfg in cases:
        o_res = run_side(orig_code, [], FUNC_ADDR, cfg)
        c_res = run_side(cand_code, rodata_blobs, cand_entry, cfg)
        if o_res != c_res:
            print(f"FAIL {name}:\n  orig_tr={o_res[0]}\n  cand_tr={c_res[0]}")
            return 1
        print(f"PASS {name}")

    # 5 negative controls
    src_text = SRC_CPP.read_text(encoding="utf-8")
    mutations = [
        ("neg_state0_cmp", "static_cast<s32>(dist_bits) < 0x42700000", "static_cast<s32>(dist_bits) < 0x41F00000"),
        ("neg_state1_timer", "if (*reinterpret_cast<s32*>(cam + 8u) > 2)", "if (*reinterpret_cast<s32*>(cam + 8u) > 3)"),
        ("neg_state2_f10c", "if (script_vm_func_0027f10c() != 0)", "if (script_vm_func_0027f10c() == 0)"),
        ("neg_state13_timer", "if (t == 0x14) {\n                engine_func_002d3dac();", "if (t == 0x15) {\n                engine_func_002d3dac();"),
        ("neg_f115_guard", "if (cam[0x115u] != 0u)", "if (cam[0x115u] == 0u)"),
    ]
    for mname, old, new in mutations:
        assert old in src_text, f"Mutation target not found: {old}"
        mut_src = src_text.replace(old, new, 1)
        with tempfile.TemporaryDirectory() as tmpdir:
            mut_cpp = Path(tmpdir) / "mut.cpp"
            mut_obj = Path(tmpdir) / "mut.o"
            mut_cpp.write_text(mut_src, encoding="utf-8")
            res = compile_tu_armv6k(mut_cpp, mut_obj)
            if res.returncode != 0:
                print(f"MUT COMPILE ERR {mname}: {res.stderr}")
                return 1
            m_code, m_ro, m_entry = patch_cand_elf(mut_obj)
        detected = False
        for _, cfg in cases:
            o_res = run_side(orig_code, [], FUNC_ADDR, cfg)
            m_res = run_side(m_code, m_ro, m_entry, cfg)
            if o_res != m_res:
                detected = True
                break
        if not detected:
            print(f"FAIL negative control {mname} was not detected!")
            return 1
        print(f"PASS {mname} (detected)")

    print(f"ALL PASS: {len(cases)} cases + {len(mutations)} negative controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
