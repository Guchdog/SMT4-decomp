#!/usr/bin/env python3
"""Differential test for camp_func_003d0910 (0x003D0910) using Unicorn ARM."""

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

FUNC_ADDR = 0x003D0910
FUNC_SIZE = 996
FUNC_NAME = "camp_func_003d0910"
TRAP_ADDR = 0x000F0000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000

R8_ADDR = 0x004A0000
R8_0_ADDR = 0x004A1000
R6_ADDR = 0x004A4000
R6_20_ADDR = 0x004A4100
R6_28_ADDR = 0x004A4200
ARR_BASE = 0x004B0000
STACK_TOP = 0x08020000

CALLEES = {
    0x002B7F08: "camp_func_002b7f08",
    0x003D12CC: "script_vm_func_003d12cc",
    0x0022AD74: "func_0022ad74",
    0x002AE3F0: "battle_func_002ae3f0",
    0x0029AC70: "battle_func_0029ac70",
    0x0029ABC0: "battle_func_0029abc0",
    0x00227968: "ui_func_00227968",
    0x0029EC6C: "ui_func_0029ec6c",
    0x00229B2C: "script_vm_func_00229b2c",
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
        top = (insn >> 24) & 0xFF
        if (insn & 0x0F000000) == 0x0B000000 or (top & 0xFE) == 0xFA:
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            h_bit = (insn >> 24) & 1 if (top & 0xFE) == 0xFA else 0
            pc = FUNC_ADDR + off
            target = (pc + 8 + imm24 * 4 + h_bit * 2) & ~3
            if target in CALLEES:
                stub = STUB_BY_NAME[CALLEES[target]]
                rel = (stub - (pc + 8)) // 4
                struct.pack_into("<I", buf, off, 0xEB000000 | (rel & 0x00FFFFFF))
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
        for stub_addr in ADDR_BY_STUB:
            self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE1A00000))

    def run(
        self,
        *,
        active_elems: tuple[int, ...] = (0, 108),
        flags_20: int = 2,
        limit_ec: int = 10,
        arr9: tuple[int, ...] = (1, 0, 2, 0, 0, 0, 0, 0, 3),
        ret_12cc_1: int = 0,
        ret_12cc_0: int = 0,
        cost_map: dict[int, int] | None = None,
        hit_at: tuple[int, int, int] | None = None,
        ret_ec6c: int = 0,
    ) -> dict:
        cost_map = cost_map or {}
        self.uc.mem_write(R8_ADDR, struct.pack("<I", R8_0_ADDR))
        r8_0 = bytearray(0x2000)
        struct.pack_into("<I", r8_0, 0x1FC0, ARR_BASE)
        self.uc.mem_write(R8_0_ADDR, bytes(r8_0))

        arr_buf = bytearray(0x6D * 0x288)
        for idx in active_elems:
            off = idx * 0x288
            struct.pack_into("<I", arr_buf, off, 0x400)
            struct.pack_into("<H", arr_buf, off + 0xCE, 0x500 + idx)
        self.uc.mem_write(ARR_BASE, bytes(arr_buf))

        r6_buf = bytearray(0x40)
        struct.pack_into("<I", r6_buf, 0x20, R6_20_ADDR)
        struct.pack_into("<I", r6_buf, 0x28, R6_28_ADDR)
        self.uc.mem_write(R6_ADDR, bytes(r6_buf))
        self.uc.mem_write(R6_20_ADDR, struct.pack("<I", flags_20))

        r6_28 = bytearray(0x200)
        struct.pack_into("<h", r6_28, 0xEC, limit_ec)
        self.uc.mem_write(R6_28_ADDR, bytes(r6_28))

        trace: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
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

            if name == "camp_func_002b7f08":
                if r2 == 4:
                    ptrs = struct.unpack(f"<{r1}I", uc.mem_read(r0, r1 * 4)) if r1 else ()
                    trace.append((name, ptrs, r1, r2, r3))
                else:
                    vals = struct.unpack(f"<{r1}H", uc.mem_read(r0, r1 * 2))
                    trace.append((name, vals, r1, r2, r3))
            elif name == "script_vm_func_003d12cc":
                s0 = struct.unpack("<I", uc.mem_read(sp, 4))[0]
                ptrs = struct.unpack(f"<{r3}I", uc.mem_read(r2, r3 * 4)) if r3 else ()
                trace.append((name, r0, r1, ptrs, r3, s0))
                uc.reg_write(arm.UC_ARM_REG_R0, ret_12cc_1 if s0 == 1 else ret_12cc_0)
            elif name == "func_0022ad74":
                trace.append((name, r0))
                uc.mem_write(r1, struct.pack("<9H", *arr9))
            elif name == "battle_func_002ae3f0":
                trace.append((name, r0))
                uc.reg_write(arm.UC_ARM_REG_R0, 0x3000 + r0 if r0 != 99 else 0)
            elif name == "battle_func_0029ac70":
                trace.append((name, r0, r1))
                uc.reg_write(arm.UC_ARM_REG_R0, cost_map.get(r0, 5))
            elif name == "battle_func_0029abc0":
                trace.append((name, r0))
                uc.reg_write(arm.UC_ARM_REG_R0, cost_map.get(r0, 5))
            elif name == "ui_func_00227968":
                s0, s1, s2 = struct.unpack("<III", uc.mem_read(sp, 12))
                ptrs = struct.unpack(f"<{s0}I", uc.mem_read(r3, s0 * 4)) if s0 else ()
                trace.append((name, r0, r1, r2, ptrs, s0, s1, s2))
                uc.reg_write(arm.UC_ARM_REG_R0, 1 if hit_at == (r2 - 0x3000, s1, s2) else 0)
            elif name == "ui_func_0029ec6c":
                trace.append((name, r0))
                uc.reg_write(arm.UC_ARM_REG_R0, ret_ec6c)
            elif name == "script_vm_func_00229b2c":
                trace.append((name, r0))
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        try:
            self.uc.reg_write(arm.UC_ARM_REG_R0, R8_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_R1, R6_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
            self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=100000)
        finally:
            self.uc.hook_del(hook)

        return {
            "h14c_14e": struct.unpack("<HH", self.uc.mem_read(R6_28_ADDR + 0x14C, 4)),
            "trace": trace,
        }


def build_cases() -> list[tuple[str, dict]]:
    return [
        ("early_12cc_1", {"ret_12cc_1": 1}),
        ("pass1_hit_flags2", {"flags_20": 2, "hit_at": (3, 1, 0), "arr9": (1, 99, 2, 0, 0, 0, 0, 0, 3), "cost_map": {1: 11}}),
        ("early_12cc_0", {"ret_12cc_0": 1}),
        ("pass2_hit_flags0", {"flags_20": 0, "hit_at": (2, 0, 1), "cost_map": {1: 10}}),
        ("pass3_hit", {"flags_20": 2, "hit_at": (1, 0, 2)}),
        ("ec6c_hit", {"ret_ec6c": 1}),
        ("fallthrough_flags0", {"flags_20": 0, "active_elems": ()}),
        ("fallthrough_flags4", {"flags_20": 4}),
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
        ("wrong_arr_count", "i < 0x6Du;", "i < 0x6Cu;"),
        ("wrong_cmp_fn", "0x002196A4u", "0x001E1708u"),
        ("wrong_cost_cmp", "if (cost > static_cast<s32>(limit))", "if (cost >= static_cast<s32>(limit))"),
        ("wrong_pass3_arg", "try_pass_3d0910(r8, r6, ptrs, count, arr9, 2u, 0u)", "try_pass_3d0910(r8, r6, ptrs, count, arr9, 3u, 0u)"),
        ("wrong_flags6", "((flags & 6u) != 0u)", "((flags & 2u) != 0u)"),
    ]
    for mut_name, old, new in mutations:
        assert old in cpp_text, f"mutation anchor missing: {mut_name}"
        mut_src = cpp_text.replace(old, new, 1)
        cand_code, rodata_blobs, _ = compile_candidate(work_dir, mut_src)
        failures = run_suite(orig_code, cand_code, rodata_blobs)
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_003d0910"
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
