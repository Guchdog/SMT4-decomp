#!/usr/bin/env python3
"""Differential test for ui_func_00145e9c (0x00145E9C) using Unicorn ARM."""

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

FUNC_ADDR = 0x00145E9C
FUNC_SIZE = 1000
FUNC_NAME = "ui_func_00145e9c"
TRAP_ADDR = 0x000F0000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000
VT_STUB = 0x000F8000

SELF_ADDR = 0x004A0000
STREAM_ADDR = 0x004A2000
VTABLE_ADDR = 0x004A2100
BASE_OFF = 0x004B0000
STACK_TOP = 0x08020000

CALLEES = {
    0x002A4E50: ("ui_func_002a4e50", 6),
    0x002C3B00: ("ui_func_002c3b00", 1),
    0x00145E7C: ("nn_sdk_func_00145e7c", 1),
    0x002BBD10: ("nn_sdk_func_002bbd10", 2),
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
        for stub_addr in list(ADDR_BY_STUB) + [VT_STUB]:
            self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE1A00000))

    def run(
        self,
        *,
        hdr: tuple[int, ...] = (0, 1, 16, 3, 20, 5, 24, 7, 28, 0x99),
        hdr2: tuple[int, ...] | None = None,
        vtx_count: int = 2,
        idx_count: int = 3,
        max_end: int = 0x1000,
        read_flag: int = 0,
        read_rcs: tuple[int, ...] = (0, 0, 0, 0, 0, 0),
        read_lens: tuple[int, ...] | None = None,
        v4_val: int = 0,
        ret_e7c: int = 0,
    ) -> dict:
        hdr2 = hdr2 or hdr
        self.uc.mem_write(SELF_ADDR, b"\x00" * 0x140)
        self.uc.mem_write(SELF_ADDR + 4, struct.pack("<i", v4_val))
        self.uc.mem_write(VTABLE_ADDR, struct.pack("<I", VT_STUB))
        self.uc.mem_write(STREAM_ADDR, struct.pack("<I", VTABLE_ADDR))

        trace: list[tuple] = []
        read_idx = 0

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            nonlocal read_idx
            if addr == TRAP_ADDR:
                uc.emu_stop()
                return
            if addr == VT_STUB:
                r1 = uc.reg_read(arm.UC_ARM_REG_R1)
                r2 = uc.reg_read(arm.UC_ARM_REG_R2)
                r3 = uc.reg_read(arm.UC_ARM_REG_R3)
                sp = uc.reg_read(arm.UC_ARM_REG_SP)
                dst, sz = struct.unpack("<II", uc.mem_read(sp, 8))
                off64 = r2 | (r3 << 32)
                rc = read_rcs[read_idx] if read_idx < len(read_rcs) else 0
                nread = read_lens[read_idx] if (read_lens and read_idx < len(read_lens)) else sz
                trace.append(("stream_read", read_idx, off64, sz, dst >= BASE_OFF))
                if rc >= 0:
                    if read_idx == 0:
                        uc.mem_write(dst, struct.pack("<10I", *hdr)[:nread])
                    elif read_idx == 1 and read_flag != 0 and off64 == 0:
                        uc.mem_write(dst, struct.pack("<10I", *hdr2)[:nread])
                    else:
                        uc.mem_write(dst, bytes((0x30 + read_idx) for _ in range(nread)))
                    uc.mem_write(r1, struct.pack("<I", nread))
                read_idx += 1
                uc.reg_write(arm.UC_ARM_REG_R0, rc & 0xFFFFFFFF)
                uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
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

            if name == "ui_func_002a4e50":
                s0, s1 = struct.unpack("<II", uc.mem_read(sp, 8))
                trace.append((name, r0, r1, r2, r3, s0, s1))
            elif name == "nn_sdk_func_002bbd10":
                trace.append((name, r0))
            elif name == "nn_sdk_func_00145e7c":
                trace.append((name, r0))
                uc.reg_write(arm.UC_ARM_REG_R0, ret_e7c & 0xFFFFFFFF)
            else:
                trace.append((name, r0))
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        try:
            self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_R1, STREAM_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_R2, vtx_count)
            self.uc.reg_write(arm.UC_ARM_REG_R3, idx_count)
            self.uc.mem_write(STACK_TOP, struct.pack("<III", BASE_OFF, max_end, read_flag))
            self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
            self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=100000)
        finally:
            self.uc.hook_del(hook)

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "self": bytes(self.uc.mem_read(SELF_ADDR, 0x130)),
            "trace": trace,
        }


def build_cases() -> list[tuple[str, dict]]:
    return [
        ("hdr_rc_err", {"read_rcs": (-5,)}),
        ("hdr_short", {"read_lens": (0x24,)}),
        ("flag1_hdr2_err", {"read_flag": 1, "read_rcs": (0, -1)}),
        ("flag1_sum_neg", {"read_flag": 1, "hdr2": (0, 0, 0x80000000, 0, 0, 0, 0, 0, 0, 0)}),
        ("size_overflow", {"read_flag": 0, "max_end": 0x10}),
        ("flag0_ok_v4_0", {"read_flag": 0, "v4_val": 0}),
        ("flag1_ok_v4_neg9", {"read_flag": 1, "v4_val": -9, "ret_e7c": -2}),
        ("flag1_payload_err", {"read_flag": 1, "read_rcs": (0, 0, 0, -3)}),
        ("flag0_v4_neg8", {"read_flag": 0, "v4_val": -8}),
        ("flag0_v4_pos8", {"read_flag": 0, "v4_val": 8}),
        ("flag0_v4_pos9", {"read_flag": 0, "v4_val": 9}),
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
        ("wrong_short_err", "0xC8A04554u", "0xC8A04555u"),
        ("wrong_vtx_shift", "vtx_count << 5", "vtx_count << 4"),
        ("wrong_idx_mul", "idx_count * 24u", "idx_count * 20u"),
        ("wrong_v4_neg8", "(v4 >= -8) ? 1 : 0", "(v4 >= -7) ? 1 : 0"),
        ("wrong_v4_pos8", "(v4 <= 8) ? 3 : 4", "(v4 <= 7) ? 3 : 4"),
    ]
    for mut_name, old, new in mutations:
        assert old in cpp_text, f"mutation anchor missing: {mut_name}"
        mut_src = cpp_text.replace(old, new, 1)
        cand_code, rodata_blobs, _ = compile_candidate(work_dir, mut_src)
        failures = run_suite(orig_code, cand_code, rodata_blobs)
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_00145e9c"
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
