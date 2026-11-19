#!/usr/bin/env python3
"""Differential test for battle_func_00105460 (0x00105460) using Unicorn ARM."""

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

FUNC_ADDR = 0x00105460
FUNC_SIZE = 1000
FUNC_NAME = "battle_func_00105460"
TRAP_ADDR = 0x000F0000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000

G_ADDR = 0x004E39E0
CFG_ADDR = 0x004E4000
STACK_TOP = 0x08020000

CALLEES = {
    0x001123B8: ("battle_func_001123b8", 2),
    0x002C2A5C: ("battle_func_002c2a5c", 4),
    0x002C2A2C: ("battle_func_002c2a2c", 1),
    0x002C28F4: ("battle_func_002c28f4", 2),
    0x002C27EC: ("battle_func_002c27ec", 1),
    0x002C2700: ("battle_func_002c2700", 4),
    0x002C26A8: ("battle_func_002c26a8", 2),
    0x002C2684: ("battle_func_002c2684", 2),
    0x0010E9EC: ("engine_func_0010e9ec", 3),
    0x0010D180: ("battle_func_0010d180", 1),
    0x0010E5E0: ("battle_func_0010e5e0", 1),
    0x002BF140: ("battle_func_002bf140", 2),
    0x0011311C: ("battle_func_0011311c", 2),
    0x00113104: ("battle_func_00113104", 3),
    0x0010A4DC: ("battle_func_0010a4dc", 0),
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
        cfg_nonnull: bool,
        cfg8: int = 1,
        g_c0: int = 0x500,
        g_138: int = 0x500,
        g_1c8: int = 0,
        g_1fc_init: int = 0x7777,
    ) -> dict:
        g_buf = bytearray(0x220)
        struct.pack_into("<I", g_buf, 0xC0, g_c0)
        struct.pack_into("<I", g_buf, 0x138, g_138)
        struct.pack_into("<I", g_buf, 0x1C8, g_1c8)
        struct.pack_into("<I", g_buf, 0x1CC, 0xDEAD)
        struct.pack_into("<I", g_buf, 0x1FC, g_1fc_init)
        self.uc.mem_write(G_ADDR, bytes(g_buf))

        cfg_vals = [0x100 + i for i in range(11)]
        cfg_vals[8] = cfg8
        self.uc.mem_write(CFG_ADDR, struct.pack("<11I", *cfg_vals))

        trace: list[tuple] = []
        handle_seq = 1
        out_seq = 100

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            nonlocal handle_seq, out_seq
            if addr == TRAP_ADDR:
                uc.emu_stop()
                return
            if addr not in ADDR_BY_STUB:
                return
            target = ADDR_BY_STUB[addr]
            name, nargs = CALLEES[target]
            regs = (arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1, arm.UC_ARM_REG_R2, arm.UC_ARM_REG_R3)
            args = tuple(uc.reg_read(regs[i]) for i in range(nargs))

            if name == "battle_func_002c2a5c" and args[1] == 1:
                trace.append((name, "stack_tmp", args[1], args[2], args[3]))
                uc.mem_write(args[0], struct.pack("<I", 0xABCD))
            elif name == "battle_func_002c26a8":
                trace.append((name, args[0]))
                out_seq += 1
                uc.mem_write(args[1], struct.pack("<I", out_seq))
            elif name == "battle_func_002c28f4":
                trace.append((name, args))
                for k in range(args[0]):
                    handle_seq += 1
                    uc.mem_write(args[1] + k * 4, struct.pack("<I", handle_seq))
            else:
                trace.append((name, args))
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        try:
            self.uc.reg_write(arm.UC_ARM_REG_R0, CFG_ADDR if cfg_nonnull else 0)
            self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
            self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=100000)
        finally:
            self.uc.hook_del(hook)

        return {"g": bytes(self.uc.mem_read(G_ADDR, 0x204)), "trace": trace}


def build_cases() -> list[tuple[str, dict]]:
    return [
        ("cfg_null", {"cfg_nonnull": False, "g_c0": 0x500, "g_138": 0x500, "g_1c8": 0}),
        ("cfg_cnt2_1c8_1", {"cfg_nonnull": True, "cfg8": 1, "g_c0": 0x400, "g_138": 0x500, "g_1c8": 1}),
        ("cfg_cnt3_138_ne", {"cfg_nonnull": True, "cfg8": 0, "g_c0": 0x500, "g_138": 0x400, "g_1c8": 0}),
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
        ("wrong_cfg8_cnt", "const u32 count = (src[8] == 1u) ? 2u : 3u;", "const u32 count = (src[8] == 1u) ? 2u : 4u;"),
        ("wrong_tex_410", "0x410u, count, 0xF0u, 0x190u, fp);", "0x411u, count, 0xF0u, 0x190u, fp);"),
        ("wrong_t64_add", "+ 0x44A2FA85u;", "+ 0x44A2FA86u;"),
        ("wrong_1c8_guard", "if (*reinterpret_cast<const u32*>(g + 0x1C8u) != 0u)", "if (*reinterpret_cast<const u32*>(g + 0x1C8u) == 0u)"),
        ("wrong_500_cmp", "(*reinterpret_cast<const u32*>(g + 0x138u) != 0x500u)", "(*reinterpret_cast<const u32*>(g + 0x138u) == 0x500u)"),
    ]
    for mut_name, old, new in mutations:
        assert old in cpp_text, f"mutation anchor missing: {mut_name}"
        mut_src = cpp_text.replace(old, new, 1)
        cand_code, rodata_blobs, _ = compile_candidate(work_dir, mut_src)
        failures = run_suite(orig_code, cand_code, rodata_blobs)
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_00105460"
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
