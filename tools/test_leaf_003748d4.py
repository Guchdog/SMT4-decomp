#!/usr/bin/env python3
"""Differential Unicorn test for func_003748d4 (0x003748d4, 1420 B)."""

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
    UC_ARM_REG_SP,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x003748D4
FUNC_SIZE = 1420
FUNC_NAME = "func_003748d4"

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
    0x002A1EF8: "func_002a1ef8",
    0x002A1D48: "func_002a1d48",
    0x002A1B98: "func_002a1b98",
    0x002A1A08: "func_002a1a08",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
STUB_BY_NAME["__aeabi_memclr8"] = STUB_BASE + 0x100
NAME_BY_STUB = {v: k for k, v in STUB_BY_NAME.items()}

G_CMD = 0x004652A0
CMD_BUF = DATA_BASE + 0x5000
SELF_ADDR = DATA_BASE + 0x1000
DATA_OBJ = DATA_BASE + 0x1200
SRC_ADDR = DATA_BASE + 0x2000


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


def run_side(
    code_bytes: bytes,
    rodata_blobs: list[tuple[int, bytes]],
    entry: int,
    params_spec: list[dict],
    ovs_spec: list[dict],
) -> tuple[list, int, int, int, bytes]:
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

    uc.mem_write(G_CMD, struct.pack("<I", CMD_BUF))
    uc.mem_write(SELF_ADDR + 0x08, struct.pack("<I", DATA_OBJ))
    uc.mem_write(SELF_ADDR + 0x14, struct.pack("<I", 0x000000F0))
    uc.mem_write(SELF_ADDR + 0x2C, struct.pack("<I", 0x00000F00))

    param_arr = DATA_BASE + 0x1400
    uc.mem_write(DATA_OBJ + 0x14, struct.pack("<i", len(params_spec)))
    uc.mem_write(DATA_OBJ + 0x18, struct.pack("<i", param_arr - (DATA_OBJ + 0x18)) if params_spec else struct.pack("<i", 0))
    for i, p in enumerate(params_spec):
        slot = param_arr + i * 4
        pdef = DATA_BASE + 0x3000 + i * 0x40
        uc.mem_write(slot, struct.pack("<i", pdef - slot))
        uc.mem_write(pdef + 0x04, bytes([p.get("en", 1), p.get("s2c", 0)]))
        uc.mem_write(pdef + 0x08, struct.pack("<i", p.get("reg", i)))
        uc.mem_write(pdef + 0x0C, struct.pack("<II", p.get("kind", 0), p.get("val", 1)))

    ov_arr = DATA_BASE + 0x2400
    uc.mem_write(SRC_ADDR + 0x290, struct.pack("<i", len(ovs_spec)))
    uc.mem_write(SRC_ADDR + 0x294, struct.pack("<i", ov_arr - (SRC_ADDR + 0x294)) if ovs_spec else struct.pack("<i", 0))
    for j, ov in enumerate(ovs_spec):
        slot = ov_arr + j * 4
        oitem = DATA_BASE + 0x4000 + j * 0x40
        uc.mem_write(slot, struct.pack("<i", oitem - slot))
        uc.mem_write(oitem + 0x04, struct.pack("<i", ov["idx"]))
        uc.mem_write(oitem + 0x08, struct.pack("<II", ov.get("kind", 0), ov.get("val", 1)))

    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_R1, SRC_ADDR)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)

    trace: list = []

    def u32(a: int) -> int:
        return struct.unpack("<I", uc.mem_read(a, 4))[0]

    def hook(uc_inst, address, size, user_data):
        name = NAME_BY_STUB.get(address)
        if name is None:
            return
        a0 = uc_inst.reg_read(UC_ARM_REG_R0)
        a1 = uc_inst.reg_read(UC_ARM_REG_R1)
        if name == "__aeabi_memclr8":
            uc_inst.mem_write(a0, b"\x00" * a1)
            return
        val = u32(a1)
        uc_inst.mem_write(a0, struct.pack("<I", val ^ 0x1234))
        trace.append((name, a0 - CMD_BUF, val))

    uc.hook_add(UC_HOOK_CODE, hook, begin=STUB_BASE, end=STUB_BASE + 0x1000)
    uc.emu_start(entry, HALT_ADDR, timeout=5_000_000, count=200_000)

    cmd_end = u32(G_CMD)
    return (
        trace,
        u32(SELF_ADDR + 0x14),
        u32(SELF_ADDR + 0x2C),
        cmd_end - CMD_BUF,
        bytes(uc.mem_read(CMD_BUF, cmd_end - CMD_BUF)),
    )


def make_cases() -> list[tuple[str, list[dict], list[dict]]]:
    return [
        ("empty_all", [], []),
        ("ov_only_filters_and_bits", [
            {"en": 1, "s2c": 0, "reg": 0, "kind": 0, "val": 0},
            {"en": 1, "s2c": 1, "reg": 1, "kind": 0, "val": 1},
            {"en": 0, "s2c": 0, "reg": 2, "kind": 0, "val": 1},
            {"en": 1, "s2c": 0, "reg": -1, "kind": 0, "val": 1},
        ], [
            {"idx": -1, "kind": 0, "val": 1},
            {"idx": 4, "kind": 0, "val": 1},
            {"idx": 2, "kind": 0, "val": 1},
            {"idx": 3, "kind": 0, "val": 1},
            {"idx": 0, "kind": 0, "val": 1},
            {"idx": 1, "kind": 0, "val": 0},
        ]),
        ("ov_kinds_1_to_5_both_slots", [
            {"s2c": 1, "reg": 10},
            {"s2c": 1, "reg": 11},
            {"s2c": 1, "reg": 12},
            {"s2c": 1, "reg": 13},
            {"s2c": 0, "reg": 20},
            {"s2c": 0, "reg": 21},
            {"s2c": 0, "reg": 22},
            {"s2c": 0, "reg": 23},
            {"s2c": 1, "reg": 24},
        ], [
            {"idx": 0, "kind": 1, "val": 0x101},
            {"idx": 1, "kind": 2, "val": 0x102},
            {"idx": 2, "kind": 3, "val": 0x103},
            {"idx": 3, "kind": 4, "val": 0x104},
            {"idx": 4, "kind": 1, "val": 0x201},
            {"idx": 5, "kind": 2, "val": 0x202},
            {"idx": 6, "kind": 3, "val": 0x203},
            {"idx": 7, "kind": 4, "val": 0x204},
            {"idx": 8, "kind": 5, "val": 0x205},
        ]),
        ("fallback_all_kinds_both_slots", [
            {"s2c": 1, "reg": 0, "kind": 0, "val": 0},
            {"s2c": 0, "reg": 4, "kind": 0, "val": 0},
            {"s2c": 1, "reg": 1, "kind": 1, "val": 0x301},
            {"s2c": 1, "reg": 2, "kind": 2, "val": 0x302},
            {"s2c": 1, "reg": 3, "kind": 3, "val": 0x303},
            {"s2c": 1, "reg": 4, "kind": 4, "val": 0x304},
            {"s2c": 0, "reg": 5, "kind": 1, "val": 0x401},
            {"s2c": 0, "reg": 6, "kind": 2, "val": 0x402},
            {"s2c": 0, "reg": 7, "kind": 3, "val": 0x403},
            {"s2c": 0, "reg": 8, "kind": 4, "val": 0x404},
            {"s2c": 0, "reg": 9, "kind": 5, "val": 0x405},
        ], []),
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
    for name, p_spec, o_spec in cases:
        o_res = run_side(orig_code, [], FUNC_ADDR, p_spec, o_spec)
        c_res = run_side(cand_code, rodata_blobs, cand_entry, p_spec, o_spec)
        if o_res != c_res:
            print(f"FAIL {name}:\n  orig={o_res}\n  cand={c_res}")
            return 1
        print(f"PASS {name}")

    # 5 negative controls
    src_text = SRC_CPP.read_text(encoding="utf-8")
    mutations = [
        ("neg_slot_2c", "bool is_slot_2c = (pdef[5u] != 0u);", "bool is_slot_2c = false;"),
        ("neg_cmd_tag", "is_slot_2c ? 0x804F0290u : 0x804F02C0u", "0x804F0290u"),
        ("neg_idx_bounds", "if (idx < 0 || idx >= param_count)", "if (idx < 0 || idx >= param_count - 1)"),
        ("neg_applied_flag", "applied[idx] = 1u;", "applied[idx] = 0u;"),
        ("neg_cmd_advance", "*g_cmd = cmd + 6;", "*g_cmd = cmd + 4;"),
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
        for _, p_spec, o_spec in cases:
            o_res = run_side(orig_code, [], FUNC_ADDR, p_spec, o_spec)
            m_res = run_side(m_code, m_ro, m_entry, p_spec, o_spec)
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
