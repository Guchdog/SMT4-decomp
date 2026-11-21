#!/usr/bin/env python3
"""Differential Unicorn test for script_vm_func_0038de60 (0x0038de60, 1156 B)."""

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

FUNC_ADDR = 0x0038DE60
FUNC_SIZE = 1156
FUNC_NAME = "script_vm_func_0038de60"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x00510000
STACK_BASE = 0x02000000
STACK_SIZE = 0x00100000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

SELF_ADDR = 0x00600000
SHOP_ADDR = 0x00601000
SHOP_PTR_GLOBAL = 0x00432FC8
HALT_ADDR = 0x006FFFF0

CALLEES = {
    0x00234B30: "engine_func_00234b30",
    0x002A1578: "engine_func_002a1578",
    0x00354D28: "script_vm_func_00354d28",
    0x00354C30: "engine_func_00354c30",
    0x00234B08: "script_vm_func_00234b08",
    0x00354D4C: "script_vm_func_00354d4c",
    0x00353124: "script_vm_func_00353124",
    0x0035495C: "engine_func_0035495c",
    0x002345FC: "script_vm_func_002345fc",
    0x002345F0: "script_vm_func_002345f0",
    0x002344C4: "script_vm_func_002344c4",
    0x0023A330: "script_vm_func_0023a330",
    0x0038B510: "aocApplication_func_0038b510",
    0x003528D4: "engine_func_003528d4",
    0x003DF578: "script_vm_func_003df578",
    0x003DF588: "script_vm_func_003df588",
    0x003533EC: "engine_func_003533ec",
    0x0025461C: "script_vm_func_0025461c",
    0x002545C4: "script_vm_func_002545c4",
    0x0025456C: "script_vm_func_0025456c",
    0x002A8730: "script_vm_func_002a8730",
    0x0038D7B0: "script_vm_func_0038d7b0",
    0x00234368: "engine_func_00234368",
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
            if not (func_val <= r_offset < func_val + func_size):
                continue
            r_type = r_info & 0xFF
            r_sym = r_info >> 8
            sname, sval, sshndx = sym_info(r_sym)
            if r_type in (28, 29):
                target = STUB_BY_NAME[sname]
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


def read_cstr(uc: Uc, addr: int, limit: int = 128) -> str:
    if addr == 0:
        return "<NULL>"
    raw = bytes(uc.mem_read(addr, limit))
    nul = raw.find(0)
    if nul >= 0:
        raw = raw[:nul]
    return raw.decode("ascii", errors="replace")


def run_case(
    code_bytes: bytes,
    rodata_blobs: list[tuple[int, bytes]],
    entry_addr: int,
    case: dict,
) -> tuple[list[tuple], bytes, bytes]:
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

    uc.mem_write(SELF_ADDR, b"\x00" * 0x40)
    shop_init = bytearray(0x700)
    struct.pack_into("<I", shop_init, 0x80, 0x4444)
    struct.pack_into("<I", shop_init, 0x364, case["extra"])
    struct.pack_into("<I", shop_init, 0x5B0, 0x5555)
    struct.pack_into("<I", shop_init, 0x684, 0x80)
    uc.mem_write(SHOP_ADDR, bytes(shop_init))
    uc.mem_write(SHOP_PTR_GLOBAL, struct.pack("<I", SHOP_ADDR))

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
        r3 = u.reg_read(UC_ARM_REG_R3)

        if name == "engine_func_00234b30":
            trace.append((name, r1, r2))
            u.mem_write(r0, struct.pack("<Q", case["status_234b30"] & 0xFFFFFFFFFFFFFFFF))
        elif name == "engine_func_002a1578":
            st = struct.unpack_from("<q", u.mem_read(r0, 8))[0]
            trace.append((name, st))
            u.reg_write(UC_ARM_REG_R0, 0xFFFFFFFF if st < 0 else 0)
        elif name == "script_vm_func_00354d28":
            trace.append((name, r1, r3))
            u.mem_write(r0, struct.pack("<4I", 0x11, 0x22, 0x33, 0x44))
            u.mem_write(r2, b"\x00" * r3)
        elif name == "engine_func_00354c30":
            obj_w = struct.unpack_from("<4I", u.mem_read(r1, 16))
            trace.append((name, obj_w, r2))
            u.mem_write(r0, struct.pack("<Q", case["status_354c30"] & 0xFFFFFFFFFFFFFFFF))
        elif name == "script_vm_func_00354d4c":
            obj_w = struct.unpack_from("<4I", u.mem_read(r0, 16))
            trace.append((name, obj_w))
        elif name == "script_vm_func_00353124":
            u.mem_write(r0, b"\x00" * 0x38)
            u.mem_write(r1, b"\x00" * r2)
            trace.append((name, r2))
        elif name == "engine_func_0035495c":
            obj_w = struct.unpack_from("<4I", u.mem_read(r1, 16))
            trace.append((name, obj_w))
            u.mem_write(r0, b"".join(struct.pack("<I", 0x900 + i) for i in range(16)))
        elif name in ("script_vm_func_002345fc", "script_vm_func_002345f0"):
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, 0x111 if name.endswith("fc") else 0x222)
        elif name == "script_vm_func_002344c4":
            trace.append((name, r1, r2, r3))
            u.mem_write(r0, b"".join(struct.pack("<I", (r1 << 16) | i) for i in range(16)))
        elif name == "script_vm_func_0023a330":
            fmt_s = read_cstr(u, r1)
            str_s = read_cstr(u, r2)
            trace.append((name, r0, fmt_s, str_s))
            u.mem_write(r0, str_s.encode("ascii")[:63] + b"\x00")
        elif name == "aocApplication_func_0038b510":
            trace.append((name, r0))
        elif name == "engine_func_003528d4":
            sp = u.reg_read(UC_ARM_REG_SP)
            req = struct.unpack_from("<I", u.mem_read(sp, 4))[0]
            req_b = u.mem_read(req, 0x38)
            p0, p4, p8, pc = struct.unpack_from("<4I", req_b, 0)
            hdr_ptr = struct.unpack_from("<I", req_b, 0x1C)[0]
            hdr_w = struct.unpack_from("<16I", u.mem_read(hdr_ptr, 0x40)) if hdr_ptr else ()
            trace.append((name, r1, r2, r3, p0, p4, p8, pc, hdr_w))
            u.mem_write(r0, struct.pack("<Q", case["status_3528d4"] & 0xFFFFFFFFFFFFFFFF))
        elif name in ("script_vm_func_003df578", "script_vm_func_003df588"):
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, 0x777 if name.endswith("78") else 0x888)
        elif name == "engine_func_003533ec":
            trace.append((name, r1))
            u.mem_write(r2, struct.pack("<II", 0x101, 0x202))
            u.mem_write(r0, struct.pack("<Q", case["status_3533ec"] & 0xFFFFFFFFFFFFFFFF))
        elif name == "script_vm_func_00234b08":
            trace.append((name, r0))
        elif name in ("script_vm_func_0025461c", "script_vm_func_002545c4", "script_vm_func_0025456c"):
            p0, p1 = struct.unpack_from("<II", u.mem_read(r0, 8))
            trace.append((name, p0, p1))
            if name.endswith("1c"):
                u.reg_write(UC_ARM_REG_R0, p0 + 1)
            elif name.endswith("c4"):
                u.reg_write(UC_ARM_REG_R0, p1 + 2)
            else:
                u.reg_write(UC_ARM_REG_R0, p0 ^ p1)
        elif name == "script_vm_func_002a8730":
            trace.append((name, r0, r1, r2))
            u.reg_write(UC_ARM_REG_R0, 0xCAFEBABE)
        elif name == "script_vm_func_0038d7b0":
            trace.append((name, r0))
            u.reg_write(UC_ARM_REG_R0, case["res_38d7b0"] & 0xFFFFFFFF)
        elif name == "engine_func_00234368":
            trace.append((name, r1))
            u.mem_write(r0, struct.pack("<Q", case["status_234368"] & 0xFFFFFFFFFFFFFFFF))

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
    uc.emu_start(entry_addr, HALT_ADDR, timeout=5_000_000)

    return trace, bytes(uc.mem_read(SELF_ADDR, 0x40)), bytes(uc.mem_read(SHOP_ADDR, 0x700))


CASES = [
    {
        "name": "init_status_err",
        "extra": 0,
        "status_234b30": 0x8000000000000001,
        "status_354c30": 0,
        "status_3528d4": 0,
        "status_3533ec": 0,
        "res_38d7b0": 0,
        "status_234368": 0,
    },
    {
        "name": "obj_354c30_err",
        "extra": 0,
        "status_234b30": 0,
        "status_354c30": 0x8000000000000002,
        "status_3528d4": 0,
        "status_3533ec": 0,
        "res_38d7b0": 0,
        "status_234368": 0,
    },
    {
        "name": "exec_3528d4_err",
        "extra": 3,
        "status_234b30": 0,
        "status_354c30": 0,
        "status_3528d4": 0x8000000000000003,
        "status_3533ec": 0,
        "res_38d7b0": 0,
        "status_234368": 0,
    },
    {
        "name": "exec_3533ec_err",
        "extra": 0,
        "status_234b30": 0,
        "status_354c30": 0,
        "status_3528d4": 0,
        "status_3533ec": 0x8000000000000004,
        "res_38d7b0": 0,
        "status_234368": 0,
    },
    {
        "name": "full_success_extra0_res_ok",
        "extra": 0,
        "status_234b30": 0,
        "status_354c30": 0,
        "status_3528d4": 0,
        "status_3533ec": 0,
        "res_38d7b0": 0,
        "status_234368": 0x1234,
    },
    {
        "name": "full_success_extra_nonzero_res_neg",
        "extra": 5,
        "status_234b30": 0,
        "status_354c30": 0,
        "status_3528d4": 0,
        "status_3533ec": 0,
        "res_38d7b0": -1,
        "status_234368": 0x1234,
    },
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
        ot, oself, oshop = run_case(orig_bytes, [], FUNC_ADDR, case)
        ct, cself, cshop = run_case(cand_bytes, cand_ro, cand_entry, case)
        if (ot, oself, oshop) != (ct, cself, cshop):
            print(f"FAIL {case['name']}")
            return 1
        print(f"PASS {case['name']} ({len(ot)} calls)")

    muts = [
        (
            "neg_init_status_skip",
            "    engine_func_00234b30(&status, shop + 0x28u, shop + 0x18u);\n"
            "    if (check_status_38cdf4(self, status)) {\n"
            "        return;\n"
            "    }\n"
            "\n"
            "    u8 buf_400_a[0x400];",
            "    engine_func_00234b30(&status, shop + 0x28u, shop + 0x18u);\n"
            "    if (!check_status_38cdf4(self, status)) {\n"
            "        return;\n"
            "    }\n"
            "\n"
            "    u8 buf_400_a[0x400];",
        ),
        (
            "neg_354c30_skip_dtor",
            "    engine_func_00354c30(&status, obj, shop + 0x694u);\n"
            "    if (check_status_38cdf4(self, status)) {\n"
            "        script_vm_func_00234b08(shop + 0x28u);\n"
            "        script_vm_func_00354d4c(obj);\n"
            "        return;\n"
            "    }",
            "    engine_func_00354c30(&status, obj, shop + 0x694u);\n"
            "    if (check_status_38cdf4(self, status)) {\n"
            "        script_vm_func_00234b08(shop + 0x28u);\n"
            "        return;\n"
            "    }",
        ),
        (
            "neg_extra_zero_skip",
            "    const u32 extra = *reinterpret_cast<const u32*>(shop + 0x364u);\n"
            "    if (extra != 0u) {\n"
            "        *reinterpret_cast<u8**>(req + 8u) = shop + 0xE3u;\n"
            "        *reinterpret_cast<u32*>(req + 0x0Cu) = extra;\n"
            "    }\n"
            "\n"
            "    aocApplication_func_0038b510(shop);",
            "    const u32 extra = *reinterpret_cast<const u32*>(shop + 0x364u);\n"
            "    if (extra == 0u) {\n"
            "        *reinterpret_cast<u8**>(req + 8u) = shop + 0xE3u;\n"
            "        *reinterpret_cast<u32*>(req + 0x0Cu) = extra;\n"
            "    }\n"
            "\n"
            "    aocApplication_func_0038b510(shop);",
        ),
        (
            "neg_res_sign_flip",
            "    const s32 res = script_vm_func_0038d7b0(self);\n"
            "    script_vm_func_00234b08(shop + 0x28u);\n"
            "    if (res >= 0) {",
            "    const s32 res = script_vm_func_0038d7b0(self);\n"
            "    script_vm_func_00234b08(shop + 0x28u);\n"
            "    if (res < 0) {",
        ),
        (
            "neg_wrong_obj_offset",
            "    engine_func_00354c30(&status, obj, shop + 0x694u);",
            "    engine_func_00354c30(&status, obj, shop + 0x698u);",
        ),
    ]

    for mname, old, new in muts:
        assert old in cpp_text, f"Anchor missing for {mname}"
        mut_cpp = cpp_text.replace(old, new, 1)
        m_bytes, m_ro, m_entry = compile_cand(mut_cpp)
        caught = False
        for case in CASES:
            ot, oself, oshop = run_case(orig_bytes, [], FUNC_ADDR, case)
            mt, mself, mshop = run_case(m_bytes, m_ro, m_entry, case)
            if (ot, oself, oshop) != (mt, mself, mshop):
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
