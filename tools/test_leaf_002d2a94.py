#!/usr/bin/env python3
"""Differential test for script_vm_func_002d2a94 (0x002D2A94) using Unicorn ARM."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
SRC_CPP = ROOT / "src/engine/leaf_batch45_c.cpp"
FUNC_ADDR = 0x002D2A94
FUNC_SIZE = 956
FUNC_NAME = "script_vm_func_002d2a94"

STUB_BASE = 0x00110000
RODATA_BASE = 0x00120000
MEM_BASE = 0x20000000
MEM_SIZE = 0x00020000
R6_ADDR = 0x20000000
R7_ADDR = 0x20004000
PLAYER_ADDR = 0x20006000
STACK_TOP = 0x2001E000
TRAP_ADDR = 0x001F0000

G_R6_PTR = 0x00447600
G_SB = 0x0049F91C
G_PLAYER_PTR = 0x00447E88

CALLEES = {
    0x002C2B1C: ("engine_func_002c2b1c", 0),
    0x0029C0FC: ("camp_func_0029c0fc", 2),
    0x002BE7FC: ("ui_func_002be7fc", 4),
    0x00259544: ("script_vm_func_00259544", 2),
    0x0027DE00: ("script_vm_func_0027de00", 0),
    0x0027DB24: ("script_vm_func_0027db24", 1),
    0x00287D54: ("engine_func_00287d54", 0),
    0x0028277C: ("script_vm_func_0028277c", 0),
    0x00282600: ("script_vm_func_00282600", 0),
    0x00253AA0: ("engine_func_00253aa0", 2),
    0x00287E4C: ("script_vm_func_00287e4c", 0),
    0x0027F150: ("script_vm_func_0027f150", 0),
}

STUB_ADDRS = {addr: STUB_BASE + idx * 4 for idx, addr in enumerate(sorted(CALLEES))}
ADDR_BY_STUB = {v: k for k, v in STUB_ADDRS.items()}
NAME_TO_STUB = {CALLEES[k][0]: v for k, v in STUB_ADDRS.items()}


def patch_orig_code(raw: bytes) -> bytearray:
    code = bytearray(raw)
    for off in range(0, len(code), 4):
        insn = struct.unpack_from("<I", code, off)[0]
        cond = (insn >> 28) & 0xF
        op = (insn >> 24) & 0xF
        if cond != 0xF and op in (0xA, 0xB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = FUNC_ADDR + off
            target = pc + 8 + (imm24 << 2)
            if target in STUB_ADDRS:
                new_imm = ((STUB_ADDRS[target] - (pc + 8)) >> 2) & 0x00FFFFFF
                struct.pack_into("<I", code, off, (insn & 0xFF000000) | new_imm)
        elif (insn & 0xFE000000) == 0xFA000000:
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            h_bit = (insn >> 24) & 1
            pc = FUNC_ADDR + off
            target = (pc + 8 + (imm24 << 2) + (h_bit << 1)) & ~3
            if target in STUB_ADDRS:
                new_imm = ((STUB_ADDRS[target] - (pc + 8)) >> 2) & 0x00FFFFFF
                struct.pack_into("<I", code, off, 0xEB000000 | new_imm)
    return code


def patch_cand_elf(obj_path: Path) -> tuple[bytearray, list[tuple[int, bytes]]]:
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
                    target = NAME_TO_STUB[s_name]
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
    return code, rodata_blobs


class Runner:
    def __init__(self, code: bytes, rodata_blobs: list[tuple[int, bytes]] | None = None):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(MEM_BASE, MEM_SIZE)
        cpacr = self.uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, cpacr | (0xF << 20))
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        if rodata_blobs:
            for addr, blob in rodata_blobs:
                self.uc.mem_write(addr, blob)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))

    def run(
        self,
        sb_364: int,
        r6_4: int,
        val_194: int,
        idx_196: int,
        sb_36c: int,
        entry_idx: int,
        r4_50: int,
        r4_64: int,
        r4_68: int,
        r4_7c: int,
        dist1: float,
        dist2: float,
        diff_ang: float,
        r4_174: int = 6,
        r4_30: int = 4,
    ) -> dict:
        self.uc.mem_write(G_R6_PTR, struct.pack("<I", R6_ADDR))
        self.uc.mem_write(G_PLAYER_PTR, struct.pack("<I", PLAYER_ADDR))

        sb_buf = bytearray(0x400)
        struct.pack_into("<h", sb_buf, 0x194, val_194)
        struct.pack_into("<h", sb_buf, 0x196, idx_196)
        struct.pack_into("<I", sb_buf, 0x364, sb_364)
        struct.pack_into("<I", sb_buf, 0x36C, sb_36c)
        self.uc.mem_write(G_SB, bytes(sb_buf))

        r6_buf = bytearray(0x3100)
        struct.pack_into("<I", r6_buf, 4, r6_4)
        off = 0x34 + entry_idx * 0x180
        r6_buf[off] = 1
        struct.pack_into("<fff", r6_buf, off + 0x20, 10.0, 20.0, 30.0)
        struct.pack_into("<f", r6_buf, off + 0x2C, 45.0)
        struct.pack_into("<I", r6_buf, off + 0x30, r4_30)
        r6_buf[off + 0x50] = r4_50 & 0xFF
        struct.pack_into("<I", r6_buf, off + 0x54, 1)
        struct.pack_into("<I", r6_buf, off + 0x58, 0x2222)
        struct.pack_into("<i", r6_buf, off + 0x5C, 12)
        struct.pack_into("<I", r6_buf, off + 0x60, 0x3333)
        struct.pack_into("<I", r6_buf, off + 0x64, r4_64)
        struct.pack_into("<i", r6_buf, off + 0x68, r4_68)
        struct.pack_into("<I", r6_buf, off + 0x6C, 7)
        struct.pack_into("<I", r6_buf, off + 0x70, 0x777)
        r6_buf[off + 0x7C] = r4_7c & 0xFF
        struct.pack_into("<I", r6_buf, off + 0x84, 5)
        struct.pack_into("<i", r6_buf, off + 0x88, 30)
        struct.pack_into("<I", r6_buf, off + 0x174, r4_174)
        r6_buf[off + 0x17C] = 1
        self.uc.mem_write(R6_ADDR, bytes(r6_buf))

        r7_buf = bytearray(0x1000)
        r7_buf[0xF2A + 20] = 5
        r7_buf[0xF2B + 20] = -3 & 0xFF
        self.uc.mem_write(R7_ADDR, bytes(r7_buf))

        p_buf = bytearray(0x80)
        struct.pack_into("<fff", p_buf, 0x1C, 1.0, 2.0, 3.0)
        struct.pack_into("<f", p_buf, 0x4C, 90.0)
        self.uc.mem_write(PLAYER_ADDR, bytes(p_buf))

        trace: list[tuple] = []
        dist_calls = 0

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            nonlocal dist_calls
            if addr == TRAP_ADDR:
                uc.emu_stop()
                return
            if addr not in ADDR_BY_STUB:
                return
            target = ADDR_BY_STUB[addr]
            name, nargs = CALLEES[target]
            regs = (arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1, arm.UC_ARM_REG_R2, arm.UC_ARM_REG_R3)
            args = tuple(uc.reg_read(regs[i]) for i in range(nargs))
            if name == "ui_func_002be7fc":
                fmt = uc.mem_read(args[1], 10)
                trace.append((name, args[0], bytes(fmt), args[2], args[3]))
            else:
                trace.append((name, args))
            if name == "engine_func_002c2b1c":
                uc.reg_write(arm.UC_ARM_REG_R0, R7_ADDR)
            elif name == "engine_func_00287d54":
                dist_calls += 1
                val = dist1 if dist_calls == 1 else dist2
                uc.reg_write(arm.UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", val))[0])
            elif name == "script_vm_func_0028277c":
                uc.reg_write(arm.UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", 0.5))[0])
            elif name == "script_vm_func_00282600":
                uc.reg_write(arm.UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", 0.8))[0])
            elif name == "script_vm_func_00287e4c":
                uc.reg_write(arm.UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", 15.0))[0])
            elif name == "script_vm_func_0027f150":
                uc.reg_write(arm.UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", diff_ang))[0])
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        try:
            self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
            self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=100000)
        finally:
            self.uc.hook_del(hook)

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "sb": bytes(self.uc.mem_read(G_SB, 0x200)),
            "r7_22": struct.unpack("<H", bytes(self.uc.mem_read(R7_ADDR + 0x22, 2)))[0],
            "trace": trace,
        }


def build_cases() -> list[tuple[str, dict]]:
    base = {
        "sb_364": 0, "r6_4": 1, "val_194": 0, "idx_196": 0, "sb_36c": 1,
        "entry_idx": 0, "r4_50": 1, "r4_64": 1, "r4_68": 5, "r4_7c": 1,
        "dist1": 30.0, "dist2": 100.0, "diff_ang": 130.0,
    }
    return [
        ("gate_sb364", {**base, "sb_364": 1}),
        ("gate_r6_4", {**base, "r6_4": 0}),
        ("countdown_wait", {**base, "val_194": 3}),
        ("countdown_fire_fmt", {**base, "val_194": 2}),
        ("countdown_fire_vm", {**base, "val_194": 2, "r4_64": 0}),
        ("countdown_fire_zero", {**base, "val_194": 2, "r4_68": 0}),
        ("scan_direct_hit", {**base}),
        ("scan_alt_hit", {**base, "dist1": 70.0, "dist2": 55.0, "diff_ang": 60.0}),
        ("scan_miss_all", {**base, "dist1": 70.0, "dist2": 75.0}),
        ("scan_skip_30_eq_6", {**base, "r4_30": 6}),
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
        ("wrong_countdown_cmp", "if (val_194 != 1)", "if (val_194 != 0)"),
        ("wrong_dist1", "static_cast<s32>(0x42700000u) <= static_cast<s32>(float_to_bits_2d2a94(dist1))", "static_cast<s32>(0x41C80000u) <= static_cast<s32>(float_to_bits_2d2a94(dist1))"),
        ("wrong_dist2", "static_cast<s32>(float_to_bits_2d2a94(dist2)) >=\n                    static_cast<s32>(0x42700000u)", "static_cast<s32>(float_to_bits_2d2a94(dist2)) >=\n                    static_cast<s32>(0x42480000u)"),
        ("wrong_r4_30", "*reinterpret_cast<const u32*>(r4 + 0x30u) == 6u", "*reinterpret_cast<const u32*>(r4 + 0x30u) == 7u"),
        ("wrong_hit_mode", "engine_func_00253aa0(r4, 2u);", "engine_func_00253aa0(r4, 1u);"),
    ]
    for mut_name, old, new in mutations:
        assert old in cpp_text, f"mutation anchor missing: {mut_name}"
        mut_cpp = work_dir / f"mut_{mut_name}.cpp"
        mut_obj = work_dir / f"mut_{mut_name}.o"
        mut_cpp.write_text(cpp_text.replace(old, new, 1), encoding="utf-8")
        compile_tu_armv6k(mut_cpp, mut_obj, ROOT)
        cand_code, rodata_blobs = patch_cand_elf(mut_obj)
        failures = run_suite(orig_code, cand_code, rodata_blobs)
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_002d2a94"
    work_dir.mkdir(parents=True, exist_ok=True)

    raw = ORIG_BIN.read_bytes()[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    orig_code = patch_orig_code(raw)

    obj_path = work_dir / "leaf_batch45_c.o"
    compile_tu_armv6k(SRC_CPP, obj_path, ROOT)
    cand_code, rodata_blobs = patch_cand_elf(obj_path)

    failures = run_suite(orig_code, cand_code, rodata_blobs)
    if failures:
        for f in failures[:5]:
            print("FAIL:", f)
        return 1

    run_negative_controls(orig_code, SRC_CPP.read_text(encoding="utf-8"), work_dir)
    cases = build_cases()
    print(f"ALL PASS: {len(cases)} cases + 5 negative controls (cand_size={len(cand_code)}B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
