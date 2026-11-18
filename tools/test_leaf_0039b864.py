#!/usr/bin/env python3
"""Differential test for engine_func_0039b864 (0x0039B864) using Unicorn ARM."""

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

FUNC_ADDR = 0x0039B864
FUNC_SIZE = 996
FUNC_NAME = "engine_func_0039b864"
TRAP_ADDR = 0x000F0000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000

G_SB = 0x0049F91C
R9_ADDR = 0x004A1000
VEC_ADDR = 0x004A3000
SELF_ADDR = 0x004B0000
STACK_TOP = 0x08020000

CALLEES = {
    0x002C2B1C: "engine_func_002c2b1c",
    0x00231B54: "func_00231b54",
    0x002315C8: "camp_func_002315c8",
    0x002315B4: "func_002315b4",
    0x0039AE80: "func_0039ae80",
    0x00231F58: "func_00231f58",
    0x00231B38: "func_00231b38",
}
STUB_BY_NAME = {name: STUB_BASE + idx * 4 for idx, name in enumerate(CALLEES.values())}
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
        flags10: int = 0x02000000,
        sb_18: int = 0,
        r9_d5a: int = 6,
        ret_1b54: int = 1,
        hit_idx: int = -1,
        case3_second_ret: int = 1,
        slots: tuple[tuple[int, int, int, int], ...] = ((1, 3, 1, 1), (1, 5, 1, 1)),
        self_60: int = 5,
        ret_ae80: int = 9,
    ) -> dict:
        sb_buf = bytearray(0x40)
        sb_buf[0x18] = sb_18 & 0xFF
        self.uc.mem_write(G_SB, bytes(sb_buf))

        r9_buf = bytearray(0xE00)
        r9_buf[0xD5A] = r9_d5a & 0xFF
        self.uc.mem_write(R9_ADDR, bytes(r9_buf))

        self.uc.mem_write(VEC_ADDR, struct.pack("<ff", 3.0, -4.0))

        self_buf = bytearray(0x13000)
        struct.pack_into("<I", self_buf, 0x10, flags10)
        self_buf[0x60] = self_60 & 0xFF
        struct.pack_into("<I", self_buf, 0x121CC, 7)
        struct.pack_into("<i", self_buf, 0x12264, len(slots))
        for j, (e4, e6, e2, ea) in enumerate(slots):
            off = 0x12100 + j * 4
            struct.pack_into("<H", self_buf, off + 0xE2, e2)
            struct.pack_into("<H", self_buf, off + 0xE4, e4)
            struct.pack_into("<h", self_buf, off + 0xE6, e6)
            struct.pack_into("<H", self_buf, off + 0xEA, ea)
        self.uc.mem_write(SELF_ADDR, bytes(self_buf))

        trace: list[tuple] = []
        case3_calls = 0

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            nonlocal case3_calls
            if addr == TRAP_ADDR:
                uc.emu_stop()
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

            if name == "engine_func_002c2b1c":
                uc.reg_write(arm.UC_ARM_REG_R0, R9_ADDR)
            elif name == "func_00231b54":
                trace.append((name,))
                uc.reg_write(arm.UC_ARM_REG_R0, ret_1b54)
            elif name == "camp_func_002315c8":
                s0, s1 = struct.unpack("<II", uc.mem_read(sp, 8))
                idx = r1 - 0xFB5
                trace.append((name, r0, r1))
                uc.mem_write(r2, struct.pack("<I", idx))
                uc.mem_write(r3, struct.pack("<I", 0x10 + idx))
                uc.mem_write(s1, struct.pack("<I", 0x20 + idx))
                uc.mem_write(s0, struct.pack("<I", 0x30 + idx))
            elif name == "func_002315b4":
                trace.append((name, r0, r1, r2, r3))
                if r0 == hit_idx:
                    if r0 == 2:
                        case3_calls += 1
                        uc.reg_write(arm.UC_ARM_REG_R0, 1 if case3_calls == 1 else case3_second_ret)
                    else:
                        uc.reg_write(arm.UC_ARM_REG_R0, 1)
                else:
                    uc.reg_write(arm.UC_ARM_REG_R0, 0)
            elif name == "func_0039ae80":
                trace.append((name, r0, r1))
                uc.reg_write(arm.UC_ARM_REG_R0, ret_ae80)
            elif name == "func_00231f58":
                trace.append((name, r0))
                uc.reg_write(arm.UC_ARM_REG_R0, VEC_ADDR)
            elif name == "func_00231b38":
                vals = struct.unpack("<ff", uc.mem_read(r1, 8))
                trace.append((name, r0, vals))
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        try:
            self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
            self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=100000)
        finally:
            self.uc.hook_del(hook)

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "f10": struct.unpack("<I", self.uc.mem_read(SELF_ADDR + 0x10, 4))[0],
            "b56_61": bytes(self.uc.mem_read(SELF_ADDR + 0x56, 12)),
            "b5a8c": bytes(self.uc.mem_read(SELF_ADDR + 0x5A8C, 2)),
            "d5a": self.uc.mem_read(R9_ADDR + 0xD5A, 1)[0],
            "trace": trace,
        }


def build_cases() -> list[tuple[str, dict]]:
    return [
        ("clear_flag_sb18", {"sb_18": 1, "ret_1b54": 1}),
        ("clear_flag_1b54_0", {"sb_18": 0, "ret_1b54": 0, "hit_idx": -1}),
        ("case0_hit", {"hit_idx": 0, "self_60": 5, "ret_ae80": 9}),
        ("case0_hit_res0", {"hit_idx": 0, "self_60": 5, "ret_ae80": 0}),
        ("case0_j0_stop", {"hit_idx": 0, "slots": ((1, 5, 1, 1),), "self_60": 5}),
        ("case0_e2_0", {"hit_idx": 0, "slots": ((1, 3, 1, 1), (1, 5, 0, 1)), "self_60": 5}),
        ("case1_scale2", {"hit_idx": 1, "r9_d5a": 6, "flags10": 0x00030000}),
        ("case1_skip_d5a", {"hit_idx": 1, "r9_d5a": 12}),
        ("case3_scale05", {"hit_idx": 3, "r9_d5a": 12, "flags10": 0x00030000}),
        ("case3_skip_d5a", {"hit_idx": 3, "r9_d5a": 6}),
        ("case2_zero", {"hit_idx": 2, "case3_second_ret": 1}),
        ("case2_no_second", {"hit_idx": 2, "case3_second_ret": 0}),
        ("case4_hit", {"hit_idx": 4, "slots": ((1, 5, 1, 1), (1, 7, 5, 1)), "self_60": 5, "ret_ae80": 11}),
        ("case4_last_stop", {"hit_idx": 4, "slots": ((1, 5, 1, 1),), "self_60": 5}),
        ("case4_ea_0", {"hit_idx": 4, "slots": ((1, 5, 1, 0), (0, 0, 5, 0)), "self_60": 5}),
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
        ("wrong_clear_mask", "~0x02000000u", "~0x01000000u"),
        ("wrong_case1_scale", "scale_vec_39b864(vec_ptr, 2.0f);", "scale_vec_39b864(vec_ptr, 3.0f);"),
        ("wrong_case2_d5a", "r9[0xD5Au] = 6u;", "r9[0xD5Au] = 7u;"),
        ("wrong_case3_b58", "self[0x58u] = 5u;", "self[0x58u] = 4u;"),
        ("wrong_case4_dir", "func_0039ae80(self, -1);", "func_0039ae80(self, 1);"),
    ]
    for mut_name, old, new in mutations:
        assert old in cpp_text, f"mutation anchor missing: {mut_name}"
        mut_src = cpp_text.replace(old, new, 1)
        cand_code, rodata_blobs, _ = compile_candidate(work_dir, mut_src)
        failures = run_suite(orig_code, cand_code, rodata_blobs)
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_0039b864"
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
