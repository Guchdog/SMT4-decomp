#!/usr/bin/env python3
"""Differential test for ui_func_0034359c (0x0034359C) using Unicorn ARM."""

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

FUNC_ADDR = 0x0034359C
FUNC_SIZE = 1044
FUNC_NAME = "ui_func_0034359c"
TRAP_ADDR = 0x000F0000
STUB_BASE = 0x000F1000
RODATA_BASE = 0x000F4000
CB_BASE = 0x000F8000

SELF_ADDR = 0x004A0000
STACK_TOP = 0x08020000

CALLEES = {
    0x002C1784: ("engine_func_002c1784", 1),
    0x002C17AC: ("engine_func_002c17ac", 1),
    0x002C1D3C: ("ui_func_002c1d3c", 2),
    0x002C5F7C: ("ui_func_002c5f7c", 2),
    0x00286834: ("engine_func_00286834", 1),
    0x0023D5AC: ("camp_func_0023d5ac", 4),
    0x002C5FA4: ("battle_func_002c5fa4", 3),
    0x003105DC: ("func_003105dc", 4),
    0x0031B9A0: ("func_0031b9a0", 3),
    0x002B7978: ("ui_func_002b7978", 4),
}
STUB_BY_NAME = {name: STUB_BASE + idx * 4 for idx, (_, (name, _)) in enumerate(CALLEES.items())}
ADDR_BY_STUB = {STUB_BASE + idx * 4: addr for idx, addr in enumerate(CALLEES.keys())}
STK_OFFS = (0x120C, 0x122C, 0x124C, 0x126C, 0x128C, 0x12AC)


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


def f32_bits(val: float) -> int:
    return struct.unpack("<I", struct.pack("<f", val))[0]


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
        for stub_addr in list(ADDR_BY_STUB) + [CB_BASE + k * 4 for k in range(6)]:
            self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE1A00000))

    def run(self, *, flags: int, a1: int, a2: int, f0: float, dirty: int, prev_val: int) -> dict:
        self_buf = bytearray(0x1300)
        struct.pack_into("<I", self_buf, 0x528, 0x77)
        struct.pack_into("<I", self_buf, 0x11E4, 0x88)
        for k, off in enumerate(STK_OFFS):
            struct.pack_into("<I", self_buf, off, 0)
            struct.pack_into("<I", self_buf, off + 8, prev_val)
            self_buf[off + 0x18] = dirty & 0xFF
            struct.pack_into("<I", self_buf, off + 0x1C, CB_BASE + k * 4)
        self.uc.mem_write(SELF_ADDR, bytes(self_buf))

        trace: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr == TRAP_ADDR:
                uc.emu_stop()
                return
            if CB_BASE <= addr < CB_BASE + 24:
                k = (addr - CB_BASE) // 4
                trace.append(("stk_cb", k, uc.reg_read(arm.UC_ARM_REG_R0)))
                uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
                return
            if addr not in ADDR_BY_STUB:
                return
            target = ADDR_BY_STUB[addr]
            name, nargs = CALLEES[target]
            regs = (arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1, arm.UC_ARM_REG_R2, arm.UC_ARM_REG_R3)
            args = tuple(uc.reg_read(regs[i]) for i in range(nargs))

            if name == "engine_func_002c1784":
                trace.append((name, args))
                uc.reg_write(arm.UC_ARM_REG_R0, 320)
            elif name == "engine_func_002c17ac":
                trace.append((name, args))
                uc.reg_write(arm.UC_ARM_REG_R0, 240)
            elif name == "engine_func_00286834":
                s0 = uc.reg_read(arm.UC_ARM_REG_S0)
                trace.append((name, args, s0))
                uc.reg_write(arm.UC_ARM_REG_R0, 0x101)
            elif name == "ui_func_002b7978":
                s_vals = tuple(uc.reg_read(r) for r in (arm.UC_ARM_REG_S0, arm.UC_ARM_REG_S1, arm.UC_ARM_REG_S2, arm.UC_ARM_REG_S3, arm.UC_ARM_REG_S4))
                trace.append((name, args, s_vals))
            elif name in ("ui_func_002c5f7c", "camp_func_0023d5ac", "battle_func_002c5fa4", "func_003105dc", "func_0031b9a0"):
                ret = 0x100 + sum(args)
                trace.append((name, args, ret))
                uc.reg_write(arm.UC_ARM_REG_R0, ret)
            else:
                trace.append((name, args))
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        try:
            self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_R1, a1)
            self.uc.reg_write(arm.UC_ARM_REG_R2, a2)
            self.uc.reg_write(arm.UC_ARM_REG_R3, flags)
            self.uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(f0))
            self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
            self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=100000)
        finally:
            self.uc.hook_del(hook)

        return {"self": bytes(self.uc.mem_read(SELF_ADDR + 0x1200, 0xD0)), "trace": trace}


def build_cases() -> list[tuple[str, dict]]:
    return [
        ("flags0_clean", {"flags": 0, "a1": 0x555, "a2": 9, "f0": 0.75, "dirty": 0, "prev_val": 0}),
        ("flags7_dirty", {"flags": 7, "a1": 0x999, "a2": 3, "f0": 0.25, "dirty": 1, "prev_val": 0x102}),
        ("flags5_match_prev", {"flags": 5, "a1": 0x111, "a2": 0, "f0": 1.0, "dirty": 0, "prev_val": 0x102}),
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
        ("wrong_f_bit2", "((flags & 4u) != 0u) ? 2u : 0u", "((flags & 4u) != 0u) ? 1u : 0u"),
        ("wrong_stk_off", "self + 0x124Cu", "self + 0x1250u"),
        ("wrong_dirty_check", "if (stk[0x18u] != 0u || prev != val)", "if (prev != val)"),
        ("wrong_b7978_z", "ui_func_002b7978(a1, a1, a1, a1, 0.0f, 0.0f, w, h, f0);", "ui_func_002b7978(a1, a1, a1, a1, 1.0f, 0.0f, w, h, f0);"),
        ("wrong_restore_1e4", "ui_func_002c1d3c(self, saved_1e4);", "ui_func_002c1d3c(self, 0u);"),
    ]
    for mut_name, old, new in mutations:
        assert old in cpp_text, f"mutation anchor missing: {mut_name}"
        mut_src = cpp_text.replace(old, new, 1)
        cand_code, rodata_blobs, _ = compile_candidate(work_dir, mut_src)
        try:
            failures = run_suite(orig_code, cand_code, rodata_blobs)
        except unicorn.UcError as exc:
            failures = [f"uc_error: {exc}"]
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_0034359c"
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
