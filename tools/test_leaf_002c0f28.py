#!/usr/bin/env python3
"""Differential test for func_002c0f28 (0x002C0F28) using Unicorn ARM."""

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

FUNC_ADDR = 0x002C0F28
FUNC_SIZE = 1016
FUNC_NAME = "func_002c0f28"
TRAP_ADDR = 0x000F0000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000
CB_STUB = 0x000F8000

G_CB = 0x0044E3B0
G_E368 = 0x0044E368
OUT_A = 0x004A0000
OUT_B = 0x004A0004
OUT_C = 0x004A0008
STACK_TOP = 0x08020000

CALLEES = {
    0x0011D11C: ("func_0011d11c", 0),
    0x002BB480: ("func_002bb480", 1),
    0x002BB624: ("func_002bb624", 0),
    0x002BB4C0: ("func_002bb4c0", 0),
    0x002C0EFC: ("func_002c0efc", 0),
    0x0013B508: ("camp_func_0013b508", 7),
    0x0011D8C4: ("func_0011d8c4", 0),
    0x002C1494: ("func_002c1494", 0),
    0x002BB4D4: ("func_002bb4d4", 1),
    0x0012A62C: ("func_0012a62c", 0),
    0x002C14F4: ("engine_func_002c14f4", 2),
    0x002B5AE8: ("func_002b5ae8", 1),
    0x0012A6D8: ("func_0012a6d8", 1),
    0x00128408: ("func_00128408", 0),
    0x0012A28C: ("func_0012a28c", 0),
    0x002BB774: ("func_002bb774", 1),
    0x002BB7A0: ("func_002bb7a0", 1),
    0x0011D1E0: ("func_0011d1e0", 1),
    0x0012A5F8: ("func_0012a5f8", 2),
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
        self.uc.mem_write(FUNC_ADDR, code_bytes)
        if rodata_blobs:
            for addr, data in rodata_blobs:
                self.uc.mem_write(addr, data)
        for stub_addr in list(ADDR_BY_STUB) + [CB_STUB]:
            self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE1A00000))

    def run(
        self,
        *,
        fp_val: int = 3,
        steps: tuple[tuple[int, int, int, int, int, int], ...] = ((0, 100, 1, 10, 20, 1),),
        has_cb: bool = True,
        ret_c1494: tuple[int, ...] = (0, 0, 0),
        ret_a62c: int = 0,
    ) -> dict:
        self.uc.mem_write(OUT_A, struct.pack("<I", 0xDEAD0001))
        self.uc.mem_write(OUT_B, struct.pack("<I", 0xDEAD0002))
        self.uc.mem_write(OUT_C, struct.pack("<I", 0xDEAD0003))
        self.uc.mem_write(G_E368, struct.pack("<I", 0xCAFE1234))

        cb_buf = bytearray(0x90)
        struct.pack_into("<I", cb_buf, 0x48, CB_STUB if has_cb else 0)
        struct.pack_into("<I", cb_buf, 0x88, 0x7777)
        self.uc.mem_write(G_CB, bytes(cb_buf))

        trace: list[tuple] = []
        step_idx = 0
        c1494_idx = 0
        cur_cb_ret = 1

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            nonlocal step_idx, c1494_idx, cur_cb_ret
            if addr == TRAP_ADDR:
                uc.emu_stop()
                return
            if addr == CB_STUB:
                r0 = uc.reg_read(arm.UC_ARM_REG_R0)
                r1 = uc.reg_read(arm.UC_ARM_REG_R1)
                r2 = uc.reg_read(arm.UC_ARM_REG_R2)
                r3 = uc.reg_read(arm.UC_ARM_REG_R3)
                sp = uc.reg_read(arm.UC_ARM_REG_SP)
                s0, s1, s2 = struct.unpack("<III", uc.mem_read(sp, 12))
                trace.append(("cb", r0, r1, r2, r3, s0, s1, s2))
                uc.reg_write(arm.UC_ARM_REG_R0, cur_cb_ret)
                uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
                return
            if addr not in ADDR_BY_STUB:
                return
            target = ADDR_BY_STUB[addr]
            name, nargs = CALLEES[target]
            regs = (arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1, arm.UC_ARM_REG_R2, arm.UC_ARM_REG_R3)
            args = tuple(uc.reg_read(regs[i]) for i in range(min(nargs, 4)))
            sp = uc.reg_read(arm.UC_ARM_REG_SP)

            if name == "func_0011d11c":
                trace.append((name,))
                uc.reg_write(arm.UC_ARM_REG_R0, fp_val)
            elif name == "camp_func_0013b508":
                p_v4, p_v3, t_lo, t_hi = struct.unpack("<IIII", uc.mem_read(sp, 16))
                rc, o20, o24, ov4, ov3, cb_r = steps[step_idx]
                step_idx += 1
                cur_cb_ret = cb_r
                trace.append((name, args[2], args[3], t_lo | (t_hi << 32)))
                uc.mem_write(args[0], struct.pack("<I", o20))
                uc.mem_write(args[1], struct.pack("<I", o24))
                uc.mem_write(p_v4, struct.pack("<I", ov4))
                uc.mem_write(p_v3, struct.pack("<I", ov3))
                uc.reg_write(arm.UC_ARM_REG_R0, rc & 0xFFFFFFFF)
            elif name == "func_002c1494":
                val = ret_c1494[c1494_idx] if c1494_idx < len(ret_c1494) else 0
                c1494_idx += 1
                trace.append((name, val))
                uc.reg_write(arm.UC_ARM_REG_R0, val)
            elif name == "func_0012a62c":
                trace.append((name,))
                uc.reg_write(arm.UC_ARM_REG_R0, ret_a62c & 0xFFFFFFFF)
            elif name == "engine_func_002c14f4":
                trace.append((name, args[0]))
            else:
                trace.append((name, args))
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        try:
            self.uc.reg_write(arm.UC_ARM_REG_R0, OUT_A)
            self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11)
            self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22)
            self.uc.reg_write(arm.UC_ARM_REG_R3, OUT_B)
            self.uc.mem_write(STACK_TOP, struct.pack("<IIQ", OUT_C, 0, 0x1122334455667788))
            self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
            self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=100000)
        finally:
            self.uc.hook_del(hook)

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "outs": struct.unpack("<III", self.uc.mem_read(OUT_A, 12)),
            "trace": trace,
        }


def build_cases() -> list[tuple[str, dict]]:
    return [
        ("fp_63", {"fp_val": 0x63}),
        ("fp_62_r4_1", {"fp_val": 0x62, "steps": ((0, 10, 1, 1, 2, 1),)}),
        ("rc_3ef", {"steps": ((0xC00003EF, 10, 1, 1, 2, 1),)}),
        ("cb_loop_then_neg", {"steps": ((0, 10, 99, 1, 2, 0), (-5, 20, 99, 3, 4, 1)), "ret_c1494": (0, 2), "ret_a62c": -1}),
        ("r4_a_and_b_fp14", {"fp_val": 0xE, "steps": ((0, 10, 2, 1, 2, 1), (0, 11, 0xA, 3, 4, 1)), "ret_c1494": (0, 1, 0)}),
        ("r4_b_fp5", {"fp_val": 5, "steps": ((0, 10, 0xB, 1, 2, 1),), "ret_c1494": (1, 3)}),
        ("r4_c_fp4", {"fp_val": 4, "steps": ((0, 10, 0xC, 1, 2, 1),), "ret_c1494": (0, 4, 0)}),
        ("r4_d_fp12", {"fp_val": 0x12, "steps": ((0, 10, 0xD, 1, 2, 1),), "ret_c1494": (1, 0, 1)}),
        ("r4_e", {"fp_val": 3, "steps": ((0, 10, 0xE, 1, 2, 1),)}),
        ("r4_f_fp14", {"fp_val": 0xE, "steps": ((0, 10, 0xF, 1, 2, 1),), "has_cb": False}),
        ("r4_11", {"fp_val": 3, "steps": ((0, 10, 0x11, 1, 2, 1),)}),
        ("r4_40_41", {"fp_val": 3, "steps": ((0, 10, 0x41, 1, 2, 1),)}),
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
        ("wrong_fp63", "if (fp == 0x63u)", "if (fp == 0x64u)"),
        ("wrong_3ef_mask", "== 0xFBC00000u", "== 0xFBC00001u"),
        ("wrong_cb_arg", "*reinterpret_cast<const u32*>(g_cb + 0x88u)", "0u"),
        ("wrong_r4_c_map", "case 0xCu:\n            r4 = 4u;", "case 0xCu:\n            r4 = 5u;"),
        ("wrong_mask_shift", "(v <= 3u) ? (0x10u << v) : 0u", "(v <= 3u) ? (0x20u << v) : 0u"),
    ]
    for mut_name, old, new in mutations:
        assert old in cpp_text, f"mutation anchor missing: {mut_name}"
        mut_src = cpp_text.replace(old, new, 1)
        cand_code, rodata_blobs, _ = compile_candidate(work_dir, mut_src)
        failures = run_suite(orig_code, cand_code, rodata_blobs)
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_002c0f28"
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
