#!/usr/bin/env python3
"""Differential Unicorn test for ui_func_00373094 (0x00373094, 1376 B)."""

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

FUNC_ADDR = 0x00373094
FUNC_SIZE = 1376
FUNC_NAME = "ui_func_00373094"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

DATA_BASE = 0x00600000
DATA_SIZE = 0x00080000
HEAP_BASE = 0x00620000
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x002BCF58: "ui_func_002bcf58",
    0x00101208: "crt_func_00101208",
    0x0036F2D8: "func_0036f2d8",
    0x00373B40: "func_00373b40",
}
STUB_BY_NAME = {name: STUB_BASE + i * 4 for i, name in enumerate(CALLEES.values())}
STUB_ALLOC = STUB_BASE + 0x100
STUB_36FD98 = STUB_BASE + 0x104
STUB_BY_NAME["alloc_fn"] = STUB_ALLOC
STUB_BY_NAME["battle_func_0036fd98"] = STUB_36FD98
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
    is_orig: bool,
    code_bytes: bytes,
    rodata_blobs: list[tuple[int, bytes]],
    entry: int,
    setup_fn,
) -> tuple[tuple[int, int], list, bytes]:
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

    out_addr, src_wrap, alloc_addr, flags, cfg = setup_fn(uc)

    uc.reg_write(UC_ARM_REG_R0, out_addr)
    uc.reg_write(UC_ARM_REG_R1, src_wrap)
    uc.reg_write(UC_ARM_REG_R2, alloc_addr)
    uc.reg_write(UC_ARM_REG_R3, flags)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)

    heap_cur = [HEAP_BASE]
    alloc_cnt = [0]
    f2d8_cnt = [0]
    trace: list = []

    def u32(a: int) -> int:
        return struct.unpack("<I", uc.mem_read(a, 4))[0]

    def hook(uc_inst, address, size, user_data):
        name = NAME_BY_STUB.get(address)
        if name is None:
            return
        cur_sp = uc_inst.reg_read(UC_ARM_REG_SP)
        a0 = uc_inst.reg_read(UC_ARM_REG_R0)
        a1 = uc_inst.reg_read(UC_ARM_REG_R1)
        a2 = uc_inst.reg_read(UC_ARM_REG_R2)
        a3 = uc_inst.reg_read(UC_ARM_REG_R3)

        if name == "alloc_fn":
            alloc_cnt[0] += 1
            if cfg.get("fail_alloc_at") == alloc_cnt[0]:
                ret = 0
            else:
                ret = heap_cur[0]
                heap_cur[0] += (a1 + 0xF) & ~0xF
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append(("alloc", a1, a2, ret))
        elif name == "ui_func_002bcf58":
            uc_inst.mem_write(a0, bytes(uc_inst.mem_read(a1, a2)))
            trace.append(("memcpy", a0, a1, a2))
        elif name == "crt_func_00101208":
            ctor = u32(cur_sp)
            ctor_tag = "36fd98" if ctor in (0x0036FD98, STUB_36FD98) else f"0x{ctor:x}"
            uc_inst.mem_write(a0, bytes(uc_inst.mem_read(a1, a2 * a3)))
            uc_inst.reg_write(UC_ARM_REG_R0, a0)
            trace.append(("vec_ctor", a0, a1, a2, a3, ctor_tag))
        elif name == "func_0036f2d8":
            f2d8_cnt[0] += 1
            ptr = u32(a0)
            if cfg.get("fail_f2d8_at") == f2d8_cnt[0]:
                ret = 0
            else:
                ret = heap_cur[0]
                heap_cur[0] += 0x20
                uc_inst.mem_write(ret, bytes(uc_inst.mem_read(ptr, 16)))
            uc_inst.reg_write(UC_ARM_REG_R0, ret)
            trace.append(("36f2d8", ptr, a1, ret))
        elif name == "func_00373b40":
            err = 0x80000000 if cfg.get("fail_373b40") else 0
            ret_ptr = 0 if cfg.get("null_373b40") else heap_cur[0]
            if ret_ptr:
                heap_cur[0] += 0x20
                uc_inst.mem_write(ret_ptr, bytes(uc_inst.mem_read(a3, 16)))
            uc_inst.mem_write(a0, struct.pack("<II", ret_ptr, err))
            trace.append(("373b40", a1, a2, a3, ret_ptr, err))

    uc.hook_add(UC_HOOK_CODE, hook, begin=STUB_BASE, end=STUB_BASE + 0x1000)
    uc.emu_start(entry, HALT_ADDR, timeout=5_000_000, count=200_000)

    out_pair = (u32(out_addr), u32(out_addr + 4))
    heap_snap = bytes(uc.mem_read(HEAP_BASE, heap_cur[0] - HEAP_BASE))
    return out_pair, trace, heap_snap


def build_case(flags: int, cfg: dict | None = None):
    cfg = cfg or {}

    def setup(uc: Uc):
        out_addr = DATA_BASE + 0x100
        src_wrap = DATA_BASE + 0x200
        alloc_addr = DATA_BASE + 0x300
        vtbl_addr = DATA_BASE + 0x400
        src = DATA_BASE + 0x1000

        uc.mem_write(vtbl_addr + 8, struct.pack("<I", STUB_ALLOC))
        uc.mem_write(alloc_addr, struct.pack("<I", vtbl_addr))
        uc.mem_write(src_wrap + 8, struct.pack("<I", src))

        # Fill src (0x2D8 bytes) with deterministic pattern
        pat = bytes((i * 7 + 3) & 0xFF for i in range(0x2D8))
        uc.mem_write(src, pat)

        # Elements for flag 1 (0x290 count, 0x294 rel array)
        tags = cfg.get("tags", [0, 1, 2, 3, 4, 5])
        uc.mem_write(src + 0x290, struct.pack("<i", len(tags)))
        arr = DATA_BASE + 0x2000
        uc.mem_write(src + 0x294, struct.pack("<i", arr - (src + 0x294)) if tags else struct.pack("<i", 0))
        for i, tag in enumerate(tags):
            elem = DATA_BASE + 0x3000 + i * 0x40
            slot = arr + i * 4
            uc.mem_write(slot, struct.pack("<i", elem - slot))
            rel0 = 0x100 if (i % 2 == 0) else 0
            uc.mem_write(elem + 0x00, struct.pack("<i", rel0))
            uc.mem_write(elem + 0x04, struct.pack("<I", 0xAAAA0000 + i))
            uc.mem_write(elem + 0x08, struct.pack("<I", 0xBB000000 | tag))
            for k in range(6):
                uc.mem_write(elem + 0x0C + k * 4, struct.pack("<I", 0x1000 + i * 0x10 + k))

        # Flag 0x20: 3 slots at 0x274..0x27C
        for i in range(3):
            slot = src + 0x274 + i * 4
            if cfg.get("f20_present", True) and i != 1:
                tgt = DATA_BASE + 0x4000 + i * 0x20
                uc.mem_write(slot, struct.pack("<i", tgt - slot))
                uc.mem_write(tgt, struct.pack("<IIII", 0x50 + i, 0x60 + i, 0x70 + i, 0x80 + i))
            else:
                uc.mem_write(slot, struct.pack("<i", 0))

        # Flag 0x40: slot at 0x280
        if cfg.get("f40_present", True):
            tgt40 = DATA_BASE + 0x4100
            uc.mem_write(src + 0x280, struct.pack("<i", tgt40 - (src + 0x280)))
            uc.mem_write(tgt40, struct.pack("<IIII", 0x91, 0x92, 0x93, 0x94))
        else:
            uc.mem_write(src + 0x280, struct.pack("<i", 0))

        # Flag 0x780 / 0x100: slot at 0x288
        if cfg.get("f288_present", True):
            sub = DATA_BASE + 0x5000
            uc.mem_write(src + 0x288, struct.pack("<i", sub - (src + 0x288)))
            uc.mem_write(sub, bytes((j * 11 + 5) & 0xFF for j in range(0xF4)))
            if cfg.get("sub28_present", True):
                sub2 = DATA_BASE + 0x5400
                uc.mem_write(sub + 0x28, struct.pack("<i", sub2 - (sub + 0x28)))
                uc.mem_write(sub2, struct.pack("<IIII", 0xE1, 0xE2, 0xE3, 0xE4))
            else:
                uc.mem_write(sub + 0x28, struct.pack("<i", 0))
        else:
            uc.mem_write(src + 0x288, struct.pack("<i", 0))

        return out_addr, src_wrap, alloc_addr, flags, cfg

    return setup


def make_cases() -> list[tuple[str, object]]:
    return [
        ("alloc_fail_initial", build_case(0x7FF, {"fail_alloc_at": 1})),
        ("flags_0_basic_clone", build_case(0)),
        ("flag_1_tags_0_to_5", build_case(1, {"tags": [0, 1, 2, 3, 4, 5]})),
        ("flag_1_alloc_arr_fail", build_case(1, {"fail_alloc_at": 2})),
        ("flag_1_alloc_node_fail", build_case(1, {"fail_alloc_at": 4})),
        ("flag_20_clone_3", build_case(0x20)),
        ("flag_20_f2d8_fail", build_case(0x20, {"fail_f2d8_at": 2})),
        ("flag_40_clone", build_case(0x40)),
        ("flag_40_f2d8_fail", build_case(0x40, {"fail_f2d8_at": 1})),
        ("flag_80_sub_no_100", build_case(0x80)),
        ("flag_100_sub_with_sub28", build_case(0x100)),
        ("flag_100_sub_null_sub28", build_case(0x100, {"null_373b40": True})),
        ("flag_100_sub_err_373b40", build_case(0x100, {"fail_373b40": True})),
        ("all_flags_combined", build_case(0x161)),
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
        o_out, o_tr, o_hp = run_side(True, orig_code, [], FUNC_ADDR, setup_fn)
        c_out, c_tr, c_hp = run_side(False, cand_code, rodata_blobs, cand_entry, setup_fn)
        if o_out != c_out or o_tr != c_tr or o_hp != c_hp:
            print(f"FAIL {name}:\n  orig_out={o_out}\n  cand_out={c_out}\n  orig_tr={o_tr}\n  cand_tr={c_tr}")
            return 1
        print(f"PASS {name}")

    # 5 negative controls
    src_text = SRC_CPP.read_text(encoding="utf-8")
    mutations = [
        ("neg_flag_1", "if ((flags & 1u) != 0u) {\n        s32 count = *reinterpret_cast<s32*>(src + 0x290u);", "if ((flags & 2u) != 0u) {\n        s32 count = *reinterpret_cast<s32*>(src + 0x290u);"),
        ("neg_tag_0", "if (tag == 0u || tag == 1u)", "if (tag == 1u)"),
        ("neg_flag_20", "if ((flags & 0x20u) != 0u)", "if ((flags & 0x200u) != 0u)"),
        ("neg_flag_40", "if ((flags & 0x40u) != 0u)", "if ((flags & 0x80u) != 0u)"),
        ("neg_flag_100", "if ((flags & 0x100u) != 0u)", "if ((flags & 0x200u) != 0u)"),
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
            o_out, o_tr, o_hp = run_side(True, orig_code, [], FUNC_ADDR, setup_fn)
            m_out, m_tr, m_hp = run_side(False, m_code, m_ro, m_entry, setup_fn)
            if o_out != m_out or o_tr != m_tr or o_hp != m_hp:
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
