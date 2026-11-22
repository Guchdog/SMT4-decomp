#!/usr/bin/env python3
"""Differential Unicorn test for battle_func_003f821c (0x003f821c, 1372 B)."""

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

FUNC_ADDR = 0x003F821C
FUNC_SIZE = 1372
FUNC_NAME = "battle_func_003f821c"

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
    0x003FD56C: "battle_func_003fd56c",
    0x003FE018: "battle_func_003fe018",
    0x00225BA4: "battle_func_00225ba4",
    0x00286604: "func_00286604",
    0x002A5078: "battle_func_002a5078",
    0x002C00B4: "battle_func_002c00b4",
    0x002A84EC: "func_002a84ec",
    0x002B7B34: "engine_func_002b7b34",
    0x00225B20: "func_00225b20",
    0x00225750: "func_00225750",
    0x00225824: "func_00225824",
    0x00225A74: "battle_func_00225a74",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
VTBL_GET_TYPE_STUB = STUB_BASE + 0x100
STUB_BY_NAME["vtbl_get_type"] = VTBL_GET_TYPE_STUB
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

    # Redirect same-TU naked functions in CALLEES to their Unicorn stubs
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
            if not is_in_func:
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
            elif r_type == 43:  # R_ARM_MOVW_ABS_NC
                insn = struct.unpack_from("<I", text_bytes, r_off)[0]
                imm16 = target & 0xFFFF
                imm4 = (imm16 >> 12) & 0xF
                imm12 = imm16 & 0xFFF
                struct.pack_into("<I", text_bytes, r_off, (insn & 0xFFF0F000) | (imm4 << 16) | imm12)
            elif r_type == 44:  # R_ARM_MOVT_ABS
                insn = struct.unpack_from("<I", text_bytes, r_off)[0]
                imm16 = (target >> 16) & 0xFFFF
                imm4 = (imm16 >> 12) & 0xF
                imm12 = imm16 & 0xFFF
                struct.pack_into("<I", text_bytes, r_off, (insn & 0xFFF0F000) | (imm4 << 16) | imm12)
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
    is_orig: bool,
    code_bytes: bytes,
    rodata_blobs: list[tuple[int, bytes]],
    entry: int,
    setup_fn,
) -> tuple[list, list[bytes]]:
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

    sp = STACK_TOP
    r0, r1, r2, r3, stack_args, check_addrs = setup_fn(uc, sp)
    for i, val in enumerate(stack_args):
        uc.mem_write(sp + i * 4, struct.pack("<I", val & 0xFFFFFFFF))

    uc.reg_write(UC_ARM_REG_R0, r0)
    uc.reg_write(UC_ARM_REG_R1, r1)
    uc.reg_write(UC_ARM_REG_R2, r2)
    uc.reg_write(UC_ARM_REG_R3, r3)
    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)

    trace: list = []

    def u32(a: int) -> int:
        return struct.unpack("<I", uc.mem_read(a, 4))[0]

    def u8(a: int) -> int:
        return uc.mem_read(a, 1)[0]

    def hook(uc_inst, address, size, user_data):
        name = NAME_BY_STUB.get(address)
        if name is None:
            return
        cur_sp = uc_inst.reg_read(UC_ARM_REG_SP)
        a0 = uc_inst.reg_read(UC_ARM_REG_R0)
        a1 = uc_inst.reg_read(UC_ARM_REG_R1)
        a2 = uc_inst.reg_read(UC_ARM_REG_R2)
        a3 = uc_inst.reg_read(UC_ARM_REG_R3)

        if name == "vtbl_get_type":
            tid = u32(a0 + 0x10)
            uc_inst.reg_write(UC_ARM_REG_R0, tid)
            trace.append(("vtbl", a0, tid))
        elif name in ("battle_func_003fd56c", "battle_func_003fe018"):
            s0 = u32(cur_sp)
            s1 = u32(cur_sp + 4)
            s2 = u32(cur_sp + 8)
            s3 = u32(cur_sp + 12)
            s4 = u32(cur_sp + 16)
            trace.append((name, a1, a2, a3, s0, s1, s2, s3, s4))
        elif name == "battle_func_00225ba4":
            trace.append((name, a0, a1, a2, a3))
        elif name == "func_00286604":
            v = u32(a1)
            for k in range(4):
                uc_inst.mem_write(a0 + k * 4, struct.pack("<I", (v + 0x100 + k) & 0xFFFFFFFF))
            trace.append((name, v))
        elif name == "battle_func_002c00b4":
            v = u32(a1)
            for k in range(4):
                uc_inst.mem_write(a0 + k * 4, struct.pack("<I", (v ^ (0xC00B4 + k)) & 0xFFFFFFFF))
            trace.append((name, a0, v))
        elif name == "func_002a84ec":
            v = u32(a1)
            for k in range(4):
                uc_inst.mem_write(a0 + k * 4, struct.pack("<I", (v + 0x2A84 + k) & 0xFFFFFFFF))
            trace.append((name, v))
        elif name == "engine_func_002b7b34":
            v = u32(a1)
            for k in range(4):
                uc_inst.mem_write(a0 + k * 4, struct.pack("<I", (v ^ (0x2B7B + k)) & 0xFFFFFFFF))
            trace.append((name, v))
        elif name == "battle_func_002a5078":
            va = u32(a1)
            vb = u32(a2)
            for k in range(4):
                uc_inst.mem_write(a0 + k * 4, struct.pack("<I", (va + vb + k) & 0xFFFFFFFF))
            trace.append((name, va, vb))
        elif name == "func_00225b20":
            ret = u32(a1)
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append((name, a0, a1, ret))
        elif name == "func_00225750":
            ctx = (u32(a0), u32(a0 + 4), u32(a0 + 8), u32(a0 + 12), u8(a0 + 16))
            trace.append((name, ctx, a1, a2))
        elif name == "battle_func_00225a74":
            trace.append((name, a0, a1, u32(a1), a2))
        elif name == "func_00225824":
            abuf = (u32(a1), u32(a1 + 4), u32(a1 + 8), u32(a1 + 12))
            trace.append((name, a0, abuf, a2, a3))

    uc.hook_add(UC_HOOK_CODE, hook, begin=STUB_BASE, end=STUB_BASE + 0x1000)
    uc.emu_start(entry, HALT_ADDR, timeout=5_000_000, count=200_000)

    mem_snaps = [bytes(uc.mem_read(addr, sz)) for addr, sz in check_addrs]
    return trace, mem_snaps


def build_case(
    s1: int,
    s2: int,
    s3: int,
    s4: int,
    f1_bits: int,
    objs_spec: list[dict],
):
    def setup(uc: Uc, sp: int):
        r0_arg = DATA_BASE + 0x100
        a1 = 0x12345678
        a2 = 0x87654321
        r3_mgr = DATA_BASE + 0x200
        f0_ptr = DATA_BASE + 0x400
        uc.mem_write(f0_ptr + 0x148, struct.pack("<I", 0xCAFEBABE))

        vtbl_addr = DATA_BASE + 0x800
        uc.mem_write(vtbl_addr + 8, struct.pack("<I", VTBL_GET_TYPE_STUB))

        arr_addr = DATA_BASE + 0x900
        check_addrs: list[tuple[int, int]] = []

        for idx, spec in enumerate(objs_spec):
            if spec is None:
                uc.mem_write(arr_addr + idx * 4, struct.pack("<I", 0))
                continue
            obj = DATA_BASE + 0x1000 + idx * 0x1000
            uc.mem_write(arr_addr + idx * 4, struct.pack("<I", obj))
            uc.mem_write(obj, struct.pack("<I", vtbl_addr))
            uc.mem_write(obj + 0x10, struct.pack("<I", spec["type_id"]))
            uc.mem_write(obj + 0x38, struct.pack("<I", spec.get("f38", 1)))
            uc.mem_write(obj + 0x8C, struct.pack("<I", spec.get("mat", 0x11110000 + idx)))
            uc.mem_write(obj + 0xF8, struct.pack("<I", spec.get("fF8", 0)))
            uc.mem_write(obj + 0x1F4, bytes([spec.get("f1F4", 0)]))
            uc.mem_write(obj + 0x1F6, bytes([spec.get("f1F6", 1)]))
            uc.mem_write(obj + 0x230, bytes([spec.get("f230", 0)]))

            m220 = obj + 0x400
            m220_8 = obj + 0x480
            uc.mem_write(obj + 0x220, struct.pack("<I", m220))
            uc.mem_write(m220 + 0x18, b"\x77")
            uc.mem_write(m220 + 8, struct.pack("<I", m220_8))
            uc.mem_write(m220_8 + 0x28, struct.pack("<I", spec.get("m220_28", 0)))
            check_addrs.append((m220 + 0x18, 1))
            check_addrs.append((obj + 0x1BC, 16))

            data = obj + 0x600
            uc.mem_write(obj + 8, struct.pack("<I", data))

            items_meta = spec.get("items", [])
            item_arr_p = obj + 0x800
            uc.mem_write(obj + 0x164, struct.pack("<I", item_arr_p))

            list_base = obj + 0x900
            if spec.get("use_fallback", False):
                uc.mem_write(obj + 0x170, struct.pack("<II", list_base, list_base))
                uc.mem_write(data + 0xB4, struct.pack("<I", len(items_meta)))
                rel_b8 = (list_base - (data + 0xB8)) if items_meta else 0
                uc.mem_write(data + 0xB8, struct.pack("<i", rel_b8))
            else:
                uc.mem_write(obj + 0x170, struct.pack("<II", list_base, list_base + len(items_meta) * 4))

            c8_table = obj + 0xA00
            uc.mem_write(data + 0xC8, struct.pack("<i", c8_table - (data + 0xC8)))

            for j, it in enumerate(items_meta):
                item_addr = obj + 0xB00 + j * 0x40
                slot_addr = list_base + j * 4
                uc.mem_write(slot_addr, struct.pack("<i", item_addr - slot_addr))
                uc.mem_write(item_addr + 0x00, struct.pack("<I", it["ret"]))
                uc.mem_write(item_addr + 0x18, struct.pack("<I", j))
                uc.mem_write(item_addr + 0x1C, struct.pack("<I", j))

                q_outer = obj + 0xC00 + j * 0x40
                q_inner = obj + 0xC20 + j * 0x40
                uc.mem_write(item_arr_p + j * 4, struct.pack("<I", q_outer))
                uc.mem_write(q_outer + 0x2C, struct.pack("<I", q_inner))
                uc.mem_write(q_inner + 0x20, struct.pack("<I", it["byte_arg"]))

                c8_slot = c8_table + j * 4
                obj2 = obj + 0xD00 + j * 0x40
                node = obj + 0xD80 + j * 0x40
                uc.mem_write(c8_slot, struct.pack("<i", obj2 - c8_slot))
                uc.mem_write(obj2 + 0x1C, struct.pack("<i", node - (obj2 + 0x1C)))

        uc.mem_write(r3_mgr + 0x2C, struct.pack("<II", arr_addr, arr_addr + len(objs_spec) * 4))
        return r0_arg, a1, a2, r3_mgr, [f0_ptr, s1, s2, s3, s4, f1_bits], check_addrs

    return setup


def make_cases() -> list[tuple[str, object]]:
    return [
        ("fast_s4_1_s3_0", build_case(0xAABB0011, 0x42, 0, 1, 0x3F800000, [])),
        ("fast_s4_1_s3_1", build_case(0xAABB0011, 0x42, 1, 1, 0x3F800000, [])),
        ("fast_s4_0_s3_1", build_case(0xAABB0011, 0x77, 1, 0, 0x40000000, [])),
        ("empty_list", build_case(0x00000055, 0x11, 0, 0, 0, [])),
        ("skipped_objs", build_case(0x55, 0x22, 0, 0, 0, [
            {"type_id": 0x00472288, "f1F6": 0, "f38": 1},
            {"type_id": 0x00472288, "f1F6": 1, "f38": 0},
        ])),
        ("branch_a_286604_m230_0", build_case(0x13, 0x24, 0, 0, 0, [{
            "type_id": 0x00472288,
            "f230": 0,
            "m220_28": 1,
            "f1F4": 0x40,
            "items": [{"ret": 1, "byte_arg": 0xA5}, {"ret": 0, "byte_arg": 0x11}],
        }])),
        ("branch_a_2c00b4_m230_1_fallback", build_case(0x05, 0x24, 0, 0, 0, [{
            "type_id": 0x00472288,
            "f230": 1,
            "m220_28": 0,
            "fF8": 0x200,
            "f1F4": 0x80,
            "use_fallback": True,
            "items": [{"ret": 1, "byte_arg": 0x33}],
        }])),
        ("branch_a_else_mat", build_case(0x09, 0x24, 0, 0, 0, [{
            "type_id": 0x00472288,
            "f230": 1,
            "m220_28": 0,
            "fF8": 0,
            "items": [{"ret": 1, "byte_arg": 0x7F}],
        }])),
        ("branch_b_4721e0_2c00b4", build_case(0x0A, 0xBC, 0, 0, 0, [{
            "type_id": 0x004721E0,
            "fF8": 0x200,
            "f1F4": 0x01,
            "items": [{"ret": 1, "byte_arg": 0x55}, {"ret": 0, "byte_arg": 0x66}],
        }])),
        ("branch_b_other_else_fallback", build_case(0x0A, 0xBC, 0, 0, 0, [{
            "type_id": DATA_BASE + 0x700,
            "fF8": 0,
            "f1F4": 0x20,
            "use_fallback": True,
            "items": [{"ret": 1, "byte_arg": 0x99}],
        }])),
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
        o_trace, o_mem = run_side(True, orig_code, [], FUNC_ADDR, setup_fn)
        c_trace, c_mem = run_side(False, cand_code, rodata_blobs, cand_entry, setup_fn)
        if o_trace != c_trace or o_mem != c_mem:
            print(f"FAIL {name}:\n  orig_trace={o_trace}\n  cand_trace={c_trace}\n  orig_mem={o_mem}\n  cand_mem={c_mem}")
            return 1
        print(f"PASS {name}")

    # 5 negative controls
    src_text = SRC_CPP.read_text(encoding="utf-8")
    mutations = [
        ("neg_s4_guard", "if (s4 == 1u || s3 == 1u)", "if (s4 == 2u || s3 == 1u)"),
        ("neg_type_472288", "if (type_id == 0x00472288u)", "if (type_id == 0x00472289u)"),
        ("neg_flag_200", "(*reinterpret_cast<u32*>(obj + 0xF8u) & 0x200u)", "(*reinterpret_cast<u32*>(obj + 0xF8u) & 0x400u)"),
        ("neg_type_4721e0", "(t2 == 0x004721E0u)", "(t2 == 0x004721E1u)"),
        ("neg_flag_1f4", "(flag_byte | obj[0x1F4u])", "(flag_byte | 0u)"),
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
            o_trace, o_mem = run_side(True, orig_code, [], FUNC_ADDR, setup_fn)
            m_trace, m_mem = run_side(False, m_code, m_ro, m_entry, setup_fn)
            if o_trace != m_trace or o_mem != m_mem:
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
