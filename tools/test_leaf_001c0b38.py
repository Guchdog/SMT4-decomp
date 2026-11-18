#!/usr/bin/env python3
"""Differential test for ui_func_001c0b38 (0x001C0B38) using Unicorn ARM."""

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

FUNC_ADDR = 0x001C0B38
FUNC_SIZE = 612
FUNC_NAME = "ui_func_001c0b38"
TRAP_ADDR = 0x000F0000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000

G_SB = 0x0043DA28
G_ARR6 = 0x0043DA50
G_ARR7 = 0x0043DA68
R4_ADDR = 0x004A0000
STACK_TOP = 0x08020000

CALLEES = {
    0x002BF9F0: ("ui_func_002bf9f0", 1),
    0x002B9220: ("camp_func_002b9220", 2),
    0x00220888: ("func_00220888", 0),
    0x002AE2B4: ("func_002ae2b4", 1),
    0x002B8B78: ("script_vm_func_002b8b78", 1),
    0x002B8794: ("camp_func_002b8794", 4),
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
        state: int,
        r4_c: int,
        b4c8: int = 0,
        b4c6: int = 0,
        active_slots: tuple[int, ...] = (0, 0, 0, 0, 0, 0),
        slot_8a: tuple[int, ...] = (0, 0, 0, 0, 0, 0),
        sb_10: int = -1,
        clear_sb10_in_b8b78: bool = False,
        arr6: tuple[int, ...] = (-1, -1, -1, -1, -1, -1),
        arr7: tuple[int, ...] = (10, 20, 30, 40, 50, 60),
    ) -> dict:
        sb_buf = bytearray(0x80)
        struct.pack_into("<I", sb_buf, 4, R4_ADDR)
        struct.pack_into("<i", sb_buf, 0x10, sb_10)
        self.uc.mem_write(G_SB, bytes(sb_buf))
        self.uc.mem_write(G_ARR6, struct.pack("<6i", *arr6))
        self.uc.mem_write(G_ARR7, struct.pack("<6I", *arr7))

        r4_buf = bytearray(0x500)
        struct.pack_into("<i", r4_buf, 0xC, r4_c)
        struct.pack_into("<i", r4_buf, 0x10, state)
        struct.pack_into("<I", r4_buf, 0x4B8, 0x12345678)
        struct.pack_into("<H", r4_buf, 0x4BC, 0x9ABC)
        r4_buf[0x4C6] = b4c6 & 0xFF
        r4_buf[0x4C8] = b4c8 & 0xFF
        for i in range(6):
            r4_buf[0x494 + i * 4] = active_slots[i] & 0xFF
            r4_buf[0x34 + i * 0x8C + 0x8A] = slot_8a[i] & 0xFF
        self.uc.mem_write(R4_ADDR, bytes(r4_buf))

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
            args = tuple(uc.reg_read(regs[i]) for i in range(nargs))
            trace.append((name, args))
            if name == "script_vm_func_002b8b78" and clear_sb10_in_b8b78:
                uc.mem_write(G_SB + 0x10, struct.pack("<i", -1))
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
            "r4": bytes(self.uc.mem_read(R4_ADDR, 0x500)),
            "trace": trace,
        }


def build_cases() -> list[tuple[str, dict]]:
    return [
        ("st_0", {"state": 0, "r4_c": 2}),
        ("st_1_4c8_0_trans", {"state": 1, "r4_c": 4, "b4c8": 0, "active_slots": (1, 0, 1, 0, 0, 0), "slot_8a": (0, 0, 1, 0, 0, 0)}),
        ("st_1_4c8_1_4c6_1", {"state": 1, "r4_c": 1, "b4c8": 1, "b4c6": 1, "active_slots": (0, 1, 0, 0, 0, 0)}),
        ("st_1_4c8_1_4c6_0", {"state": 1, "r4_c": 1, "b4c8": 1, "b4c6": 0}),
        ("st_2", {"state": 2, "r4_c": 1}),
        ("st_3_trans", {"state": 3, "r4_c": 6, "active_slots": (0, 0, 0, 0, 0, 1), "slot_8a": (0, 0, 0, 0, 0, 1)}),
        ("st_3_no_trans", {"state": 3, "r4_c": 2, "active_slots": (0, 0, 0, 1, 0, 0), "slot_8a": (0, 0, 0, 1, 0, 0)}),
        ("sb10_ge0_and_arr", {"state": 0, "r4_c": 0, "sb_10": 0x105, "clear_sb10_in_b8b78": True, "arr6": (0x201, -1, 0, -2, 5, 0x309)}),
        ("sb10_ge0_stay", {"state": 0, "r4_c": 0, "sb_10": 3, "clear_sb10_in_b8b78": False, "arr6": (1, 1, 1, 1, 1, 1)}),
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
        ("wrong_4c8_val", "if (r4[0x4C8u] == 1u)", "if (r4[0x4C8u] == 2u)"),
        ("wrong_slot_stride", "r4 + 0x37Cu + i * 0x8Cu", "r4 + 0x37Cu + i * 0x88u"),
        ("wrong_st3_next", "*reinterpret_cast<s32*>(cur + 0x10u) = 0;", "*reinterpret_cast<s32*>(cur + 0x10u) = 1;"),
        ("wrong_sb10_mask", "static_cast<u32>(v10) & 0xFFu", "static_cast<u32>(v10)"),
        ("wrong_arr6_loop", "for (s32 i = 0; i < 6; ++i) {\n            if (arr6[i] >= 0)", "for (s32 i = 0; i < 5; ++i) {\n            if (arr6[i] >= 0)"),
    ]
    for mut_name, old, new in mutations:
        assert old in cpp_text, f"mutation anchor missing: {mut_name}"
        mut_src = cpp_text.replace(old, new, 1)
        cand_code, rodata_blobs, _ = compile_candidate(work_dir, mut_src)
        failures = run_suite(orig_code, cand_code, rodata_blobs)
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_001c0b38"
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
