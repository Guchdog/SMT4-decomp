#!/usr/bin/env python3
"""Differential test for battle_func_001b02e8 (0x001B02E8) using Unicorn ARM."""

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
FUNC_ADDR = 0x001B02E8
FUNC_SIZE = 364
FUNC_NAME = "battle_func_001b02e8"

STUB_BASE = 0x00110000
RODATA_BASE = 0x00120000
MEM_BASE = 0x20000000
MEM_SIZE = 0x00020000
SELF_ADDR = 0x20000000
MC_ADDR = 0x20004000
PT_ADDR = 0x20005000
DEMON_BASE = 0x2000F000
SKILL_BASE = 0x20010000
STACK_TOP = 0x2001E000
TRAP_ADDR = 0x001F0000

CALLEES = {
    0x002B66EC: ("script_vm_func_002b66ec", 0),
    0x002AE3F0: ("battle_func_002ae3f0", 1),
    0x002AE464: ("battle_func_002ae464", 1),
    0x002A8A08: ("camp_func_002a8a08", 0),
    0x002A89E4: ("camp_func_002a89e4", 1),
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
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        if rodata_blobs:
            for addr, blob in rodata_blobs:
                self.uc.mem_write(addr, blob)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))

    def run(
        self,
        mc_skills: list[int],
        party_ids: list[int],
        demon_skills: dict[int, list[int]],
        blocked_55: set[int],
        blocked_ae464: set[int],
    ) -> dict:
        self.uc.mem_write(SELF_ADDR + 0x341C, b"\xFF" * 0x40)

        mc_buf = bytearray(0x50)
        for idx, sk in enumerate(mc_skills):
            struct.pack_into("<H", mc_buf, 0x34 + idx * 2, sk)
        self.uc.mem_write(MC_ADDR, bytes(mc_buf))

        pt_buf = bytearray(0x9120)
        for idx, uid in enumerate(party_ids):
            struct.pack_into("<b", pt_buf, 0x9108 + idx, uid)
        self.uc.mem_write(PT_ADDR, bytes(pt_buf))

        for uid, skills in demon_skills.items():
            dbuf = bytearray(0x50)
            for idx, sk in enumerate(skills):
                struct.pack_into("<H", dbuf, 0x34 + idx * 2, sk)
            self.uc.mem_write(DEMON_BASE + uid * 0x80, bytes(dbuf))

        # Skill entries at SKILL_BASE + sk * 0x60
        for sk in range(1, 20):
            sbuf = bytearray(0x60)
            sbuf[0x55] = 1 if sk in blocked_55 else 0
            self.uc.mem_write(SKILL_BASE + sk * 0x60, bytes(sbuf))

        trace: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr == TRAP_ADDR:
                uc.emu_stop()
                return
            if addr not in ADDR_BY_STUB:
                return
            target = ADDR_BY_STUB[addr]
            name, nargs = CALLEES[target]
            args = tuple(uc.reg_read(arm.UC_ARM_REG_R0 + i) for i in range(nargs))
            trace.append((name, args))
            if name == "script_vm_func_002b66ec":
                uc.reg_write(arm.UC_ARM_REG_R0, MC_ADDR)
            elif name == "battle_func_002ae3f0":
                sk = args[0]
                uc.reg_write(arm.UC_ARM_REG_R0, 0 if sk == 0 else SKILL_BASE + sk * 0x60)
            elif name == "battle_func_002ae464":
                uc.reg_write(arm.UC_ARM_REG_R0, 1 if args[0] in blocked_ae464 else 0)
            elif name == "camp_func_002a8a08":
                uc.reg_write(arm.UC_ARM_REG_R0, PT_ADDR)
            elif name == "camp_func_002a89e4":
                uid = args[0]
                uc.reg_write(arm.UC_ARM_REG_R0, DEMON_BASE + uid * 0x80 if uid in demon_skills else 0)
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
            "table": bytes(self.uc.mem_read(SELF_ADDR + 0x341C, 0x40)),
            "trace": trace,
        }


def build_cases() -> list[tuple[str, dict]]:
    return [
        ("all_empty", {
            "mc_skills": [0] * 8,
            "party_ids": [-1, -1, -1],
            "demon_skills": {},
            "blocked_55": set(),
            "blocked_ae464": set(),
        }),
        ("mixed_filters", {
            "mc_skills": [1, 2, 0, 3, 4, 5, 6, 7],
            "party_ids": [0, -1, 2],
            "demon_skills": {
                0: [8, 9, 10, 0, 11, 12, 13, 14],
                2: [1, 3, 5, 7, 0, 0, 0, 0],
            },
            "blocked_55": {2, 9, 13},
            "blocked_ae464": {4, 11, 5},
        }),
        ("null_demon", {
            "mc_skills": [1, 1, 1, 1, 1, 1, 1, 1],
            "party_ids": [0, 1, 2],
            "demon_skills": {0: [2, 3, 4, 5, 6, 7, 8, 9]},
            "blocked_55": set(),
            "blocked_ae464": set(),
        }),
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
        ("wrong_zero_count", "i < 16u;", "i < 15u;"),
        ("wrong_mc_off", "self + 0x341Cu + mc_count * 2u", "self + 0x341Eu + mc_count * 2u"),
        ("wrong_pt_off", "pt + 0x9108 + party_idx", "pt + 0x9109 + party_idx"),
        ("wrong_flag_55", "skill[0x55] == 0u", "skill[0x54] == 0u"),
        ("wrong_demon_off", "self + 0x342Cu + static_cast<u32>(party_idx) * 0x10u", "self + 0x342Cu + static_cast<u32>(party_idx) * 0x12u"),
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
    work_dir = ROOT / "build" / "test_leaf_001b02e8"
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
