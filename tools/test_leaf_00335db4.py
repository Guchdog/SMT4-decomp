#!/usr/bin/env python3
"""Differential Unicorn test for ui_func_00335db4 (0x00335db4, 1384 B)."""

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
    UC_ARM_REG_S0,
    UC_ARM_REG_SP,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x00335DB4
FUNC_SIZE = 1384
FUNC_NAME = "ui_func_00335db4"

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
    0x002C5F7C: "ui_func_002c5f7c",
    0x002BF710: "ui_func_002bf710",
    0x002BEF14: "script_vm_func_002bef14",
    0x002BF6D0: "camp_func_002bf6d0",
    0x002BA46C: "ui_func_002ba46c",
    0x002BF460: "ui_func_002bf460",
    0x002C5FA4: "battle_func_002c5fa4",
    0x002A37A4: "func_002a37a4",
    0x002A3788: "func_002a3788",
    0x0026E9C4: "func_0026e9c4",
    0x002C1B64: "ui_func_002c1b64",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
STUB_CB1 = STUB_BASE + 0x100
STUB_CB2 = STUB_BASE + 0x104
STUB_BY_NAME["cb1"] = STUB_CB1
STUB_BY_NAME["cb2"] = STUB_CB2
STUB_BY_NAME["__aeabi_memclr4"] = STUB_BASE + 0x108
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

            if not (func_val <= r_off < func_val + func_size):
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


def run_side(
    code_bytes: bytes,
    rodata_blobs: list[tuple[int, bytes]],
    entry: int,
    setup_fn,
) -> tuple[int, list]:
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

    self_addr = setup_fn(uc)

    uc.reg_write(UC_ARM_REG_R0, self_addr)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)

    trace: list = []

    def u32(a: int) -> int:
        return struct.unpack("<I", uc.mem_read(a, 4))[0]

    def f32_bits(bits: int) -> float:
        return round(struct.unpack("<f", struct.pack("<I", bits))[0], 5)

    def hook(uc_inst, address, size, user_data):
        name = NAME_BY_STUB.get(address)
        if name is None:
            return
        cur_sp = uc_inst.reg_read(UC_ARM_REG_SP)
        a0 = uc_inst.reg_read(UC_ARM_REG_R0)
        a1 = uc_inst.reg_read(UC_ARM_REG_R1)
        a2 = uc_inst.reg_read(UC_ARM_REG_R2)
        a3 = uc_inst.reg_read(UC_ARM_REG_R3)

        if name == "ui_func_002c5f7c":
            ret = 0x100 + a0 * 10 + a1
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, a0, a1, ret))
        elif name == "battle_func_002c5fa4":
            ret = 0x200 + a0 * 10 + a1
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, a0, a1, a2, ret))
        elif name in ("cb1", "cb2"):
            trace.append((name, a0))
        elif name == "ui_func_002bf710":
            s0 = uc_inst.reg_read(UC_ARM_REG_S0)
            trace.append((name, f32_bits(s0)))
        elif name == "script_vm_func_002bef14":
            trace.append((name,))
        elif name == "camp_func_002bf6d0":
            layout = DATA_BASE + 0x5000 + a1 * 0x20
            uc_inst.mem_write(layout + 8, struct.pack("<hh", 40 + (a1 & 7), 20 + (a1 & 3)))
            uc_inst.reg_write(UC_ARM_REG_R0, layout)
            trace.append((name, a0, a1))
        elif name == "ui_func_002ba46c":
            s0 = uc_inst.reg_read(UC_ARM_REG_S0)
            fv = struct.unpack("<f", struct.pack("<I", s0))[0]
            ret_f = fv * 100.0 + 12.25
            uc_inst.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", ret_f))[0])
            trace.append((name, a0, f32_bits(s0)))
        elif name == "ui_func_002bf460":
            s0 = u32(cur_sp)
            s1 = u32(cur_sp + 4)
            trace.append((name, a0, a1, a2, a3, s0, s1))
        elif name == "func_002a37a4":
            pmin = tuple(f32_bits(u32(a2 + i * 4)) for i in range(3))
            q_init = tuple(u32(a1 + i * 4) for i in range(16))
            trace.append((name, q_init, pmin))
        elif name == "func_002a3788":
            pmax = tuple(f32_bits(u32(a1 + i * 4)) for i in range(3))
            trace.append((name, pmax))
        elif name == "func_0026e9c4":
            trace.append((name,))
        elif name == "ui_func_002c1b64":
            trace.append((name, a0))
        elif name == "__aeabi_memclr4":
            uc_inst.mem_write(a0, b"\x00" * a1)

    uc.hook_add(UC_HOOK_CODE, hook, begin=STUB_BASE, end=STUB_BASE + 0x1000)
    uc.emu_start(entry, HALT_ADDR, timeout=5_000_000, count=200_000)

    return uc.reg_read(UC_ARM_REG_R0), trace


def build_case(f0: int, f1c: int, force_cb: int, init_val: int):
    def setup(uc: Uc) -> int:
        mgr = DATA_BASE + 0x1000
        uc.mem_write(0x0044EA00, struct.pack("<I", mgr))

        for off, cb in ((0x124C, STUB_CB1), (0x12AC, STUB_CB2)):
            stk = mgr + off
            uc.mem_write(stk + 0x00, struct.pack("<I", 0))
            uc.mem_write(stk + 0x08, struct.pack("<I", init_val))
            uc.mem_write(stk + 0x18, bytes([force_cb]))
            uc.mem_write(stk + 0x1C, struct.pack("<I", cb))

        self_addr = DATA_BASE + 0x200
        uc.mem_write(self_addr + 0x00, struct.pack("<I", f0))
        uc.mem_write(self_addr + 0x1C, struct.pack("<I", f1c))
        uc.mem_write(self_addr + 0x20, struct.pack("<f", 0.75))
        uc.mem_write(self_addr + 0x28, struct.pack("<f", 0.5))
        uc.mem_write(self_addr + 0x2C, struct.pack("<I", 0x11223344))
        uc.mem_write(self_addr + 0x30, struct.pack("<f", 0.25))
        uc.mem_write(self_addr + 0x34, struct.pack("<I", 0x55667788))
        return self_addr

    return setup


def make_cases() -> list[tuple[str, object]]:
    return [
        ("early_exit_f0_not_8", build_case(7, 1, 0, 0)),
        ("early_exit_f1c_zero", build_case(8, 0, 0, 0)),
        ("normal_no_force_cb", build_case(8, 1, 0, 0x10A)),
        ("normal_force_cb", build_case(8, 1, 1, 0x10A)),
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
    for name, setup_fn in cases:
        o_ret, o_tr = run_side(orig_code, [], FUNC_ADDR, setup_fn)
        c_ret, c_tr = run_side(cand_code, rodata_blobs, cand_entry, setup_fn)
        if o_ret != c_ret or o_tr != c_tr:
            print(f"FAIL {name}:\n  orig=({o_ret}, {o_tr})\n  cand=({c_ret}, {c_tr})")
            return 1
        print(f"PASS {name}")

    # 5 negative controls
    src_text = SRC_CPP.read_text(encoding="utf-8")
    mutations = [
        ("neg_f0_check", "if (*reinterpret_cast<u32*>(self) != 8u", "if (*reinterpret_cast<u32*>(self) != 9u"),
        ("neg_f1c_check", "*reinterpret_cast<u32*>(self + 0x1Cu) == 0u", "*reinterpret_cast<u32*>(self + 0x1Cu) != 0u"),
        ("neg_quad_flag", "quad[5] = quad_param;", "quad[5] = 0u;"),
        ("neg_tex_7d2", "camp_func_002bf6d0(0x2Du, 0x7D2u);", "camp_func_002bf6d0(0x2Du, 0x7D3u);"),
        ("neg_scale_28", "ui_func_002ba46c(*g_mgr, 0.28f)", "ui_func_002ba46c(*g_mgr, 0.29f)"),
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
        for _, setup_fn in cases:
            o_ret, o_tr = run_side(orig_code, [], FUNC_ADDR, setup_fn)
            m_ret, m_tr = run_side(m_code, m_ro, m_entry, setup_fn)
            if o_ret != m_ret or o_tr != m_tr:
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
