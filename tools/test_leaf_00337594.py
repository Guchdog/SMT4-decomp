#!/usr/bin/env python3
"""Differential test for battle_func_00337594 (0x00337594) using Unicorn ARM."""

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

FUNC_ADDR = 0x00337594
FUNC_SIZE = 1004
FUNC_NAME = "battle_func_00337594"
TRAP_ADDR = 0x000F0000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000

G_4342C8 = 0x004342C8
G_435D18 = 0x00435D18
G_435D90 = 0x00435D90
G_439CF8 = 0x00439CF8
G_439A20 = 0x00439A20
G_43427C = 0x0043427C

G_C8_ADDR = 0x004A0000
D18_ADDR = 0x004A1000
D90_ADDR = 0x004A5000
SELF_ADDR = 0x004B0000
ARR1_ADDR = 0x004C0000
ARR2_ADDR = 0x004D0000
R8_ADDR = 0x004E0000
ENTRY_ADDR = 0x004E0200
CREATED_ADDR = 0x004E0300
OBJ_ADDR = 0x004E0400
STACK_TOP = 0x08020000

CALLEES = {
    0x002B087C: ("battle_func_002b087c", 1),
    0x00294334: ("engine_func_00294334", 2),
    0x00240744: ("battle_func_00240744", 0),
    0x0027DC58: ("ui_func_0027dc58", 2),
    0x00295300: ("ui_func_00295300", 1),
    0x0029423C: ("ui_func_0029423c", 2),
    0x00295284: ("ui_func_00295284", 1),
    0x0023FCE0: ("engine_func_0023fce0", 1),
    0x003C1B8C: ("func_003c1b8c", 1),
    0x002406AC: ("func_002406ac", 4),
    0x0027EB98: ("script_vm_func_0027eb98", 1),
    0x00245330: ("battle_func_00245330", 6),
    0x00240660: ("battle_func_00240660", 5),
}
STUB_BY_NAME = {name: STUB_BASE + idx * 4 for idx, (_, (name, _)) in enumerate(CALLEES.items())}
ADDR_BY_STUB = {STUB_BASE + idx * 4: addr for idx, addr in enumerate(CALLEES.keys())}


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
        if (insn & 0x0E000000) == 0x0A000000:
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = FUNC_ADDR + off
            target = (pc + 8 + imm24 * 4) & 0xFFFFFFFF
            if target in CALLEES:
                stub = STUB_BY_NAME[CALLEES[target][0]]
                rel = (stub - (pc + 8)) // 4
                struct.pack_into("<I", buf, off, (insn & 0xFF000000) | (rel & 0x00FFFFFF))
    return bytes(buf)


class Runner:
    def __init__(self, code_bytes: bytes, rodata_blobs: list[tuple[int, bytes]] | None = None) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x000F0000, 0x00010000)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(0x08000000, 0x00100000)
        cpacr = self.uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, cpacr | (0xF << 20))
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_write(FUNC_ADDR, code_bytes)
        if rodata_blobs:
            for addr, data in rodata_blobs:
                self.uc.mem_write(addr, data)
        for stub_addr in ADDR_BY_STUB:
            self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE1A00000))

    def run(
        self,
        *,
        fp_val: int = -1,
        state: int = 0,
        target_id: int = 42,
        existing_match: bool = False,
        d18_flag: int = 0,
        r4_flags: int = 0,
        ret_5300: int = 1,
        ret_5284: int = 1,
        busy1_last: int = 1,
        busy2_last: int = 1,
    ) -> dict:
        self.uc.mem_write(G_4342C8, struct.pack("<I", G_C8_ADDR))
        self.uc.mem_write(G_435D18, struct.pack("<I", D18_ADDR))
        self.uc.mem_write(G_435D90, struct.pack("<I", D90_ADDR))
        self.uc.mem_write(G_439CF8, struct.pack("<I", 0x11223344))
        self.uc.mem_write(G_43427C, struct.pack("<I", 0x5566))

        g9a20 = bytearray(0x20)
        struct.pack_into("<I", g9a20, 4, 10)
        struct.pack_into("<I", g9a20, 8, 20)
        struct.pack_into("<I", g9a20, 0x18, 30)
        self.uc.mem_write(G_439A20, bytes(g9a20))

        self.uc.mem_write(G_C8_ADDR, b"\x00" * 0x700)
        d18_buf = bytearray(0x3100)
        struct.pack_into("<I", d18_buf, 0x3028, d18_flag)
        self.uc.mem_write(D18_ADDR, bytes(d18_buf))
        d90_buf = bytearray(0x2000)
        struct.pack_into("<I", d90_buf, 0x1E98, ARR2_ADDR)
        self.uc.mem_write(D90_ADDR, bytes(d90_buf))

        r8_buf = bytearray(0x100)
        struct.pack_into("<h", r8_buf, 0x88, target_id)
        self.uc.mem_write(R8_ADDR, bytes(r8_buf))

        ent_buf = bytearray(0x20)
        struct.pack_into("<i", ent_buf, 4, target_id if existing_match else 999)
        self.uc.mem_write(ENTRY_ADDR, bytes(ent_buf))

        arr1_buf = bytearray(0x36 * 0x288)
        if busy1_last:
            struct.pack_into("<I", arr1_buf, 0x35 * 0x288, 1)
        self.uc.mem_write(ARR1_ADDR, bytes(arr1_buf))

        arr2_buf = bytearray(0x36 * 0x114)
        for k in range(0x36):
            struct.pack_into("<H", arr2_buf, k * 0x114 + 0x58, 0x100)
            struct.pack_into("<H", arr2_buf, k * 0x114 + 0x62, 0x70 + k)
        if busy2_last:
            struct.pack_into("<I", arr2_buf, 0x35 * 0x114 + 0x50, 1)
        self.uc.mem_write(ARR2_ADDR, bytes(arr2_buf))

        self_buf = bytearray(0x4500)
        struct.pack_into("<I", self_buf, 0x1E98, ARR2_ADDR)
        struct.pack_into("<I", self_buf, 0x1FC0, ARR1_ADDR)
        struct.pack_into("<I", self_buf, 0x1FE4, r4_flags)
        struct.pack_into("<I", self_buf, 0x1FE8, target_id)
        if existing_match:
            struct.pack_into("<I", self_buf, 0x2134, ENTRY_ADDR)
        self_buf[0x4450] = state & 0xFF
        struct.pack_into("<i", self_buf, 0x4454, fp_val)
        self.uc.mem_write(SELF_ADDR, bytes(self_buf))

        trace: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr == TRAP_ADDR:
                uc.emu_stop()
                return
            if addr not in ADDR_BY_STUB:
                return
            target = ADDR_BY_STUB[addr]
            name, nargs = CALLEES[target]
            regs = (arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1, arm.UC_ARM_REG_R2, arm.UC_ARM_REG_R3)
            args = tuple(uc.reg_read(regs[i]) for i in range(min(nargs, 4)))
            sp = uc.reg_read(arm.UC_ARM_REG_SP)
            if nargs == 6:
                s0, s1 = struct.unpack("<II", uc.mem_read(sp, 8))
                trace.append((name, args + (s0, s1)))
            elif nargs == 5:
                s0 = struct.unpack("<I", uc.mem_read(sp, 4))[0]
                trace.append((name, args + (s0,)))
            else:
                trace.append((name, args))

            if name == "battle_func_002b087c":
                uc.reg_write(arm.UC_ARM_REG_R0, R8_ADDR)
            elif name == "engine_func_00294334":
                uc.reg_write(arm.UC_ARM_REG_R0, CREATED_ADDR)
            elif name == "ui_func_0027dc58":
                uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
            elif name == "ui_func_00295300":
                uc.reg_write(arm.UC_ARM_REG_R0, ret_5300)
            elif name == "ui_func_00295284":
                uc.reg_write(arm.UC_ARM_REG_R0, ret_5284)
            elif name == "script_vm_func_0027eb98":
                uc.reg_write(arm.UC_ARM_REG_R0, 0x888)
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        try:
            self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_R1, 0x12)
            self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
            self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=100000)
        finally:
            self.uc.hook_del(hook)

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "fp": struct.unpack("<i", self.uc.mem_read(SELF_ADDR + 0x4454, 4))[0],
            "sl": self.uc.mem_read(SELF_ADDR + 0x4450, 1)[0],
            "r4_r5": struct.unpack("<II", self.uc.mem_read(SELF_ADDR + 0x1FE4, 8)),
            "g_634": struct.unpack("<I", self.uc.mem_read(G_C8_ADDR + 0x634, 4))[0],
            "arr1_34": bytes(self.uc.mem_read(ARR1_ADDR + 0x34 * 0x288, 0xE0)),
            "arr2_34": bytes(self.uc.mem_read(ARR2_ADDR + 0x34 * 0x114, 0x70)),
            "trace": trace,
        }


def build_cases() -> list[tuple[str, dict]]:
    return [
        ("already_active", {"fp_val": 5}),
        ("st0_match_d18", {"state": 0, "existing_match": True, "d18_flag": 0x400}),
        ("st0_miss_create", {"state": 0, "existing_match": False, "d18_flag": 0}),
        ("st2_noop", {"state": 2}),
        ("st1_5300_fail", {"state": 1, "ret_5300": 0}),
        ("st1_5284_fail", {"state": 1, "ret_5284": 0}),
        ("st1_full_r4_0", {"state": 1, "r4_flags": 0, "busy1_last": 1, "busy2_last": 1}),
        ("st1_full_r4_3", {"state": 1, "r4_flags": 3, "busy1_last": 0, "busy2_last": 0}),
    ]


def run_suite(orig_code: bytes, cand_code: bytes, rodata_blobs: list[tuple[int, bytes]]) -> list[str]:
    failures: list[str] = []
    for name, kwargs in build_cases():
        orig = Runner(orig_code).run(**kwargs)
        cand = Runner(cand_code, rodata_blobs).run(**kwargs)
        if orig != cand:
            failures.append(f"{name}: orig={orig} cand={cand}")
    return failures


def run_negative_controls(orig_code: bytes, cpp_text: str, work_dir: Path) -> None:
    mutations = [
        ("wrong_fp_check", "if (*fp != -1)", "if (*fp == -1)"),
        ("wrong_d18_mask", "(d18 + 0x3028u) & 0x400u", "(d18 + 0x3028u) & 0x200u"),
        ("wrong_idx1_init", "s32 idx1 = 0x35;", "s32 idx1 = 0x34;"),
        ("wrong_r5_val", "*reinterpret_cast<u32*>(r5_p + 0x50u) = 0x00020483u;", "*reinterpret_cast<u32*>(r5_p + 0x50u) = 0x00020484u;"),
        ("wrong_mode_flag", "((*reinterpret_cast<const u32*>(r5_p + 0x50u) & 0x10u) != 0u) ? 7u : 6u;", "((*reinterpret_cast<const u32*>(r5_p + 0x50u) & 0x10u) != 0u) ? 7u : 9u;"),
    ]
    for mut_name, old, new in mutations:
        assert old in cpp_text, f"mutation anchor missing: {mut_name}"
        mut_src = cpp_text.replace(old, new, 1)
        cand_code, rodata_blobs, _ = compile_candidate(work_dir, mut_src)
        failures = run_suite(orig_code, cand_code, rodata_blobs)
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_00337594"
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
