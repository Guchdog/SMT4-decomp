#!/usr/bin/env python3
"""Differential test for engine_func_0038edf0 (0x0038EDF0) using Unicorn ARM."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
import unicorn.arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x0038EDF0
FUNC_SIZE = 984
FUNC_NAME = "engine_func_0038edf0"
TRAP_ADDR = 0x000F0000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000
VT_BASE = 0x000F8000

G_PTR = 0x00432FC8
G_ADDR = 0x004A0000
SELF_ADDR = 0x004B0000
OBJ_ADDR = 0x004C0000
OBJ2_ADDR = 0x004C1000
VTABLE_ADDR = 0x004C2000
DESC_BASE = 0x004C3000
STACK_TOP = 0x08020000

CALLEES = {
    0x00234278: "engine_func_00234278",
    0x0027EC84: "camp_func_0027ec84",
    0x002A17C0: "engine_func_002a17c0",
    0x00233F0C: "battle_func_00233f0c",
    0x00234004: "engine_func_00234004",
    0x00233AC0: "camp_func_00233ac0",
    0x0026B7CC: "ui_func_0026b7cc",
    0x002339E8: "shop_func_002339e8",
    0x002339AC: "shop_func_002339ac",
    0x00233F4C: "engine_func_00233f4c",
    0x00234160: "engine_func_00234160",
    0x002342B8: "func_002342b8",
    0x002338C4: "unite_func_002338c4",
    0x00152434: "camp_func_00152434",
    0x002BF6D0: "camp_func_002bf6d0",
    0x002348E0: "camp_func_002348e0",
    0x002348A0: "camp_func_002348a0",
    0x00234840: "camp_func_00234840",
    0x002338AC: "unite_func_002338ac",
    0x00233804: "unite_func_00233804",
}
STUB_BY_NAME = {name: STUB_BASE + idx * 4 for idx, name in enumerate(CALLEES.values())}
ADDR_BY_STUB = {STUB_BASE + idx * 4: addr for idx, addr in enumerate(CALLEES.keys())}
VT1_STUB = VT_BASE + 4
VT3_STUB = VT_BASE + 12


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
                    if s_name in STUB_BY_NAME:
                        struct.pack_into("<I", code, c_off, STUB_BY_NAME[s_name] + addend)
                    elif s_shndx == func_shndx:
                        struct.pack_into("<I", code, c_off, (FUNC_ADDR - func_val) + addend)
                    elif s_shndx in rodata_map:
                        struct.pack_into("<I", code, c_off, rodata_map[s_shndx] + addend)
                    else:
                        raise RuntimeError(f"Unexpected R_ARM_ABS32 section {s_shndx} ({s_name})")
                else:
                    raise RuntimeError(f"Unsupported reloc {r_type} for {s_name}")
    rodata_blobs = [(RODATA_BASE, bytes(rodata_blob))] if rodata_blob else []
    return bytes(code), rodata_blobs, func_size


def compile_candidate(work_dir: Path, cpp_text: str | None = None) -> tuple[bytes, list[tuple[int, bytes]], int]:
    src = work_dir / "cand.cpp"
    if cpp_text is None:
        src.write_text(SRC_CPP.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        src.write_text(cpp_text, encoding="utf-8")
    obj = work_dir / "cand.o"
    res = compile_tu_armv6k(src, obj)
    if res.returncode != 0:
        raise RuntimeError(f"compile failed: {res.stderr}")
    return patch_cand_elf(obj)


def patch_orig_bl(orig_code: bytes) -> bytes:
    buf = bytearray(orig_code)
    for off in range(0, len(buf), 4):
        insn = struct.unpack_from("<I", buf, off)[0]
        if (insn & 0x0F000000) == 0x0B000000:
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = FUNC_ADDR + off
            target = (pc + 8 + imm24 * 4) & 0xFFFFFFFF
            if target in CALLEES:
                stub = STUB_BY_NAME[CALLEES[target]]
                rel = (stub - (pc + 8)) // 4
                struct.pack_into("<I", buf, off, (insn & 0xFF000000) | (rel & 0x00FFFFFF))
    return bytes(buf)


class Runner:
    def __init__(self, code_bytes: bytes, rodata_blobs: list[tuple[int, bytes]] | None = None) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x000F0000, 0x00010000)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(0x08000000, 0x00100000)
        self.uc.mem_write(FUNC_ADDR, code_bytes)
        if rodata_blobs:
            for addr, data in rodata_blobs:
                self.uc.mem_write(addr, data)
        for stub_addr in list(ADDR_BY_STUB) + [VT1_STUB, VT3_STUB]:
            self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE1A00000))

    def run(
        self,
        *,
        state: int,
        flags: int = 0x200,
        has_obj: bool = True,
        g_67c: int = 0x4444,
        ret_b7cc: int = 1,
        ret_ec84: int = 0,
        ret_17c0: int = 0,
        tag_byte: int = 0x11,
    ) -> dict:
        self.uc.mem_write(G_PTR, struct.pack("<I", G_ADDR))
        g_buf = bytearray(0x700)
        struct.pack_into("<I", g_buf, 0x67C, g_67c)
        self.uc.mem_write(G_ADDR, bytes(g_buf))

        self.uc.mem_write(VTABLE_ADDR, struct.pack("<IIII", 0, VT1_STUB, 0, VT3_STUB))
        self.uc.mem_write(OBJ_ADDR, struct.pack("<I", VTABLE_ADDR))
        self.uc.mem_write(OBJ2_ADDR, struct.pack("<I", VTABLE_ADDR))

        self_buf = bytearray(0x400)
        struct.pack_into("<Ii", self_buf, 0, flags, 0)
        struct.pack_into("<i", self_buf, 8, state)
        struct.pack_into("<I", self_buf, 0x208, OBJ_ADDR if has_obj else 0)
        self.uc.mem_write(SELF_ADDR, bytes(self_buf))

        descs: dict[int, int] = {}
        for idx, sub in enumerate((0x4E, 0x4F, 0x50)):
            d_addr = DESC_BASE + idx * 0x40
            arr_addr = d_addr + 0x20
            self.uc.mem_write(arr_addr, struct.pack("<hh", sub * 2, -sub))
            d_buf = bytearray(0x20)
            struct.pack_into("<hhI", d_buf, 8, sub + 1, sub + 2, arr_addr)
            self.uc.mem_write(d_addr, bytes(d_buf))
            descs[sub] = d_addr

        trace: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr == TRAP_ADDR:
                uc.emu_stop()
                return
            if addr == VT1_STUB:
                trace.append(("vt_release", uc.reg_read(arm.UC_ARM_REG_R0)))
                uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
                return
            if addr == VT3_STUB:
                r0 = uc.reg_read(arm.UC_ARM_REG_R0)
                r1 = uc.reg_read(arm.UC_ARM_REG_R1)
                trace.append(("vt_read_state", r1))
                w0 = (0x12345600 | (tag_byte & 0xFF))
                uc.mem_write(r0, struct.pack("<5I", w0, 0x22, 0x33, 0x44, 0x55))
                uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
                return
            if addr not in ADDR_BY_STUB:
                return
            target = ADDR_BY_STUB[addr]
            name = CALLEES[target]
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc.reg_read(arm.UC_ARM_REG_R3)
            sp = uc.reg_read(arm.UC_ARM_REG_SP)

            if name == "engine_func_00234278":
                uc.mem_write(r0, struct.pack("<5I", 1, 2, 3, 4, 5))
                trace.append((name,))
            elif name in ("camp_func_0027ec84", "engine_func_002a17c0", "func_002342b8"):
                buf = struct.unpack("<5I", uc.mem_read(r0 if name != "func_002342b8" else r1, 20))
                trace.append((name, buf))
                if name == "camp_func_0027ec84":
                    uc.reg_write(arm.UC_ARM_REG_R0, ret_ec84)
                elif name == "engine_func_002a17c0":
                    uc.reg_write(arm.UC_ARM_REG_R0, ret_17c0)
            elif name == "ui_func_0026b7cc":
                trace.append((name,))
                uc.reg_write(arm.UC_ARM_REG_R0, ret_b7cc)
            elif name == "engine_func_00234160":
                trace.append((name, r0, r1))
                uc.reg_write(arm.UC_ARM_REG_R0, OBJ2_ADDR)
            elif name == "unite_func_002338c4":
                s0, s1 = struct.unpack("<II", uc.mem_read(sp, 8))
                trace.append((name, r0, r1, r2, r3, s0, s1))
            elif name == "camp_func_002bf6d0":
                trace.append((name, r0, r1))
                uc.reg_write(arm.UC_ARM_REG_R0, descs[r1])
            elif name in ("camp_func_002348e0", "camp_func_002348a0", "camp_func_00234840"):
                s0 = struct.unpack("<i", uc.mem_read(sp, 4))[0]
                trace.append((name, r0, r1, r2, r3, s0))
            elif name == "unite_func_002338ac":
                trace.append((name, r0))
                uc.reg_write(arm.UC_ARM_REG_R0, 0x9876)
            elif name in ("camp_func_00233ac0", "engine_func_00234004"):
                trace.append((name, r0, r1, r2))
            elif name in ("engine_func_00233f4c", "shop_func_002339e8", "shop_func_002339ac", "battle_func_00233f0c", "camp_func_00152434"):
                trace.append((name, r0, r1 if name in ("engine_func_00233f4c", "camp_func_00152434") else 0))
            elif name == "unite_func_00233804":
                trace.append((name, r0, r1, r2, r3))
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        try:
            self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
            self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=100000)
        finally:
            self.uc.hook_del(hook)

        return {"self": bytes(self.uc.mem_read(SELF_ADDR, 0x360)), "trace": trace}


def build_cases() -> list[tuple[str, dict]]:
    return [
        ("st_0", {"state": 0}),
        ("st_1_wait", {"state": 1, "ret_b7cc": 0}),
        ("st_1_go", {"state": 1, "ret_b7cc": 1}),
        ("st_2_no_flag", {"state": 2, "flags": 0}),
        ("st_2_ec84", {"state": 2, "ret_ec84": 1}),
        ("st_2_idle", {"state": 2, "ret_17c0": 0}),
        ("st_2_tag66", {"state": 2, "ret_17c0": 1, "tag_byte": 0x66}),
        ("st_2_tag67", {"state": 2, "ret_17c0": 1, "tag_byte": 0x67}),
        ("st_2_tag_other", {"state": 2, "ret_17c0": 1, "tag_byte": 0x55}),
        ("st_3_obj", {"state": 3, "has_obj": True}),
        ("st_3_null", {"state": 3, "has_obj": False}),
        ("st_4_idle", {"state": 4, "ret_ec84": 0, "ret_17c0": 0}),
        ("st_4_done", {"state": 4, "ret_ec84": 0, "ret_17c0": 1}),
        ("st_4_g0", {"state": 4, "ret_ec84": 1, "g_67c": 0}),
        ("st_4_ok", {"state": 4, "ret_ec84": 1, "g_67c": 0x4444}),
        ("st_270f", {"state": 0x270F}),
        ("st_default", {"state": 99}),
    ]


def run_suite(orig_code: bytes, cand_code: bytes, rodata_blobs: list[tuple[int, bytes]]) -> list[str]:
    failures: list[str] = []
    for name, kwargs in build_cases():
        orig = Runner(orig_code).run(**kwargs)
        cand = Runner(cand_code, rodata_blobs).run(**kwargs)
        if orig != cand:
            failures.append(f"{name}: mismatch")
    return failures


def run_negative_controls(orig_code: bytes, cpp_text: str, work_dir: Path) -> None:
    mutations = [
        ("wrong_flag_200", "(*reinterpret_cast<const u32*>(self) & 0x200u)", "(*reinterpret_cast<const u32*>(self) & 0x100u)"),
        ("wrong_tag_66", "if (tag == 0x66u)", "if (tag == 0x65u)"),
        ("wrong_done_state", "case 0x270F:", "case 0x270E:"),
        ("wrong_orr_1000", "|= 0x1000u;", "|= 0x2000u;"),
        ("wrong_g_val_arg", "unite_func_002338c4(self + 0x240u, 3u, g_val, 0u, 1u, 1u);", "unite_func_002338c4(self + 0x240u, 3u, 0u, 0u, 1u, 1u);"),
    ]
    for mut_name, old, new in mutations:
        assert old in cpp_text, f"mutation anchor missing: {mut_name}"
        mut_src = cpp_text.replace(old, new, 1)
        cand_code, rodata_blobs, _ = compile_candidate(work_dir, mut_src)
        failures = run_suite(orig_code, cand_code, rodata_blobs)
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_0038edf0"
    work_dir.mkdir(parents=True, exist_ok=True)
    raw = CODE_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = patch_orig_bl(raw[off : off + FUNC_SIZE])
    cand_code, rodata_blobs, cand_size = compile_candidate(work_dir)
    failures = run_suite(orig_code, cand_code, rodata_blobs)
    if failures:
        for f in failures:
            print("FAIL:", f)
        return 1
    run_negative_controls(orig_code, SRC_CPP.read_text(encoding="utf-8"), work_dir)
    print(f"ALL PASS: {len(build_cases())} cases + 5 negative controls (cand_size={cand_size}B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
