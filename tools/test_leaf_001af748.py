#!/usr/bin/env python3
"""Differential test for ui_func_001af748 (0x001AF748) using Unicorn ARM."""

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

FUNC_ADDR = 0x001AF748
FUNC_SIZE = 960
FUNC_NAME = "ui_func_001af748"
TRAP_ADDR = 0x000F0000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000

G_GLOBAL_PTR = 0x0043DD50
GLOBAL_ADDR = 0x004A0000
CTX_ADDR = 0x004A2000
STACK_TOP = 0x08020000

CALLEES = {
    0x00299064: ("script_vm_func_00299064", 1),
    0x00290694: ("script_vm_func_00290694", 0),
    0x002BF460: ("ui_func_002bf460", 6),
    0x002BF558: ("func_002bf558", 6),
    0x002990BC: ("script_vm_func_002990bc", 1),
    0x002B6700: ("script_vm_func_002b6700", 0),
    0x0028F5A8: ("script_vm_func_0028f5a8", 1),
    0x002990DC: ("script_vm_func_002990dc", 3),
    0x0029909C: ("script_vm_func_0029909c", 1),
    0x0028F460: ("script_vm_func_0028f460", 1),
    0x00333CE0: ("script_vm_func_00333ce0", 1),
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
        if (insn & 0x0F000000) == 0x0B000000:
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
        self.uc.mem_map(0x00100000, 0x00300000)
        self.uc.mem_map(0x00400000, 0x00200000)
        self.uc.mem_map(0x08000000, 0x00100000)
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
        arg0: int,
        arg1: int,
        arg2: int,
        arg3: int,
        arg4: int,
        flag_5c4: int,
        ret_99064: int,
        ret_90694: int,
        ret_990bc: int,
        ctx_nonnull: bool,
        ctx_6: int,
        ret_8f5a8: int,
        ret_333ce0: int,
        dc_hits: tuple[int, ...],
        dc_vals: tuple[int, ...],
        ret_9909c: int,
        ret_8f460: int,
    ) -> dict:
        self.uc.mem_write(G_GLOBAL_PTR, struct.pack("<I", GLOBAL_ADDR))
        g_buf = bytearray(0x600)
        g_buf[0x5C4] = flag_5c4 & 0xFF
        self.uc.mem_write(GLOBAL_ADDR, bytes(g_buf))

        ctx_buf = bytearray(0x20)
        ctx_buf[6] = ctx_6 & 0xFF
        self.uc.mem_write(CTX_ADDR, bytes(ctx_buf))

        trace: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr == TRAP_ADDR:
                uc.emu_stop()
                return
            if addr not in ADDR_BY_STUB:
                return
            target = ADDR_BY_STUB[addr]
            name, nargs = CALLEES[target]
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc.reg_read(arm.UC_ARM_REG_R3)
            sp = uc.reg_read(arm.UC_ARM_REG_SP)
            if nargs == 6:
                s0, s1 = struct.unpack("<II", uc.mem_read(sp, 8))
                trace.append((name, r0, r1, r2, r3, s0, s1))
            elif name == "script_vm_func_002990dc":
                trace.append((name, (r0, r1)))
            else:
                args = (r0, r1, r2, r3)[:nargs]
                trace.append((name, args))

            if name == "script_vm_func_00299064":
                uc.reg_write(arm.UC_ARM_REG_R0, ret_99064)
            elif name == "script_vm_func_00290694":
                uc.reg_write(arm.UC_ARM_REG_R0, ret_90694)
            elif name == "script_vm_func_002990bc":
                uc.reg_write(arm.UC_ARM_REG_R0, ret_990bc)
            elif name == "script_vm_func_002b6700":
                uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR if ctx_nonnull else 0)
            elif name == "script_vm_func_0028f5a8":
                uc.reg_write(arm.UC_ARM_REG_R0, ret_8f5a8)
            elif name == "script_vm_func_00333ce0":
                uc.reg_write(arm.UC_ARM_REG_R0, ret_333ce0)
            elif name == "script_vm_func_002990dc":
                idx = r1
                hit = dc_hits[idx] if 0 <= idx < len(dc_hits) else 0
                val = dc_vals[idx] if 0 <= idx < len(dc_vals) else 0
                if hit:
                    uc.mem_write(r2, struct.pack("<i", val))
                uc.reg_write(arm.UC_ARM_REG_R0, hit)
            elif name == "script_vm_func_0029909c":
                uc.reg_write(arm.UC_ARM_REG_R0, ret_9909c)
            elif name == "script_vm_func_0028f460":
                uc.reg_write(arm.UC_ARM_REG_R0, ret_8f460)
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        try:
            self.uc.reg_write(arm.UC_ARM_REG_R0, arg0)
            self.uc.reg_write(arm.UC_ARM_REG_R1, arg1)
            self.uc.reg_write(arm.UC_ARM_REG_R2, arg2)
            self.uc.reg_write(arm.UC_ARM_REG_R3, arg3)
            self.uc.mem_write(STACK_TOP, struct.pack("<I", arg4))
            self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
            self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=100000)
        finally:
            self.uc.hook_del(hook)

        return {"ret": self.uc.reg_read(arm.UC_ARM_REG_R0), "trace": trace}


def build_cases() -> list[tuple[str, dict]]:
    base = {
        "arg0": 0x1234, "arg1": 0x11, "arg2": 0x22, "arg3": 0x33, "arg4": 1,
        "flag_5c4": 0, "ret_99064": 0, "ret_90694": 0, "ret_990bc": 0,
        "ctx_nonnull": True, "ctx_6": 0, "ret_8f5a8": 0, "ret_333ce0": 0,
        "dc_hits": (0, 0, 0, 0, 0, 0), "dc_vals": (0, 0, 0, 0, 0, 0),
        "ret_9909c": 0, "ret_8f460": 0,
    }
    return [
        ("5c4_99064_90694_hi", {**base, "flag_5c4": 1, "ret_99064": 1, "ret_90694": 1}),
        ("5c4_99064_green_lo", {**base, "flag_5c4": 1, "ret_99064": 1, "ret_90694": 0, "arg4": 0}),
        ("5c4_99064_green_hi", {**base, "flag_5c4": 1, "ret_99064": 1, "ret_90694": 0, "arg4": 1}),
        ("5c4_990bc_zero_lo", {**base, "flag_5c4": 1, "ret_99064": 0, "ret_990bc": 0, "arg4": 0}),
        ("5c4_990bc_nz_hi", {**base, "flag_5c4": 1, "ret_99064": 0, "ret_990bc": 1}),
        ("ctx_null", {**base, "ctx_nonnull": False}),
        ("ctx6_8f5a8_0_333ce0_1", {**base, "ctx_6": 1, "ret_8f5a8": 0, "ret_333ce0": 1}),
        ("ctx6_8f5a8_0_990bc_1", {**base, "ctx_6": 1, "ret_8f5a8": 0, "ret_333ce0": 0, "ret_990bc": 1, "arg4": 0}),
        ("ctx6_8f5a8_0_990bc_0", {**base, "ctx_6": 1, "ret_8f5a8": 0, "ret_333ce0": 0, "ret_990bc": 0}),
        ("ctx6_8f5a8_1_match", {**base, "ctx_6": 1, "ret_8f5a8": 1, "ret_90694": 0x1234, "arg4": 0}),
        ("ctx6_8f5a8_1_miss_bc", {**base, "ctx_6": 1, "ret_8f5a8": 1, "ret_90694": 0x9999, "ret_990bc": 1}),
        ("ctx6_8f5a8_1_miss_no_bc", {**base, "ctx_6": 1, "ret_8f5a8": 1, "ret_90694": 0x9999, "ret_990bc": 0}),
        ("ctx0_all_clear_8f460_1", {**base, "dc_hits": (1, 1, 0, 0, 0, 0), "dc_vals": (0, -1, 0, 0, 0, 0), "ret_8f460": 1}),
        ("ctx0_last_slot_fail", {**base, "dc_hits": (0, 0, 0, 0, 0, 1), "dc_vals": (0, 0, 0, 0, 0, 1), "ret_8f460": 1, "ret_990bc": 1}),
        ("ctx0_bc_only_fail", {**base, "dc_hits": (1, 0, 0, 0, 0, 0), "dc_vals": (0, 0, 0, 0, 0, 0), "ret_8f460": 1, "ret_990bc": 1, "ret_9909c": 0, "arg4": 0}),
        ("ctx0_fail_9c_1", {**base, "dc_hits": (1, 0, 0, 0, 0, 0), "dc_vals": (2, 0, 0, 0, 0, 0), "ret_8f460": 1, "ret_990bc": 1, "ret_9909c": 1}),
        ("ctx0_8f460_0_93", {**base, "ret_8f460": 0, "ret_9909c": 0, "ret_990bc": 1}),
        ("ctx0_8f460_0_c2", {**base, "ret_8f460": 0, "ret_9909c": 1, "ret_990bc": 1}),
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
        ("wrong_green_hi", "0x72E027FFu", "0x72E027FEu"),
        ("wrong_5c4_msg", "ui_func_002bf460(2u, 0x29u, 0x92u, arg1, arg2, arg3);", "ui_func_002bf460(2u, 0x29u, 0x91u, arg1, arg2, arg3);"),
        ("wrong_loop_bound", "for (s32 i = 0; i < 6; ++i)", "for (s32 i = 0; i < 5; ++i)"),
        ("wrong_out_val_cmp", "if (out_val > 0)", "if (out_val >= 0)"),
        ("wrong_c2_msg", "ui_func_002bf460(2u, 0x29u, 0xC2u, arg1, arg2, arg3);", "ui_func_002bf460(2u, 0x29u, 0x93u, arg1, arg2, arg3);"),
    ]
    for mut_name, old, new in mutations:
        assert old in cpp_text, f"mutation anchor missing: {mut_name}"
        mut_src = cpp_text.replace(old, new, 1)
        cand_code, rodata_blobs, _ = compile_candidate(work_dir, mut_src)
        failures = run_suite(orig_code, cand_code, rodata_blobs)
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_001af748"
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
