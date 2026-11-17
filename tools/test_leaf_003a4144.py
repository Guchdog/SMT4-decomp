#!/usr/bin/env python3
"""Differential test for camp_func_003a4144 (0x003A4144) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts camp_func_003a4144,
resolves its 8 external callees, and compares the pinned original against the
compiled candidate across early-exit state transitions and all 14 mode/flag
callback dispatches plus mutant negative controls.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
SRC_CPP = ROOT / "src/engine/leaf_batch45_a.cpp"
FUNC_ADDR = 0x003A4144
FUNC_SIZE = 744
FUNC_NAME = "camp_func_003a4144"

STUB_BASE = 0x00110000
SELF_ADDR = 0x20000000
MEM_SIZE = 0x00020000
STACK_TOP = 0x2001F000
TRAP_ADDR = 0x001F0000

CALLEES = {
    0x0022E7C4: ("func_0022e7c4", 0),
    0x00230790: ("shop_func_00230790", 1),
    0x002337A0: ("shop_func_002337a0", 1),
    0x0027F3D4: ("func_0027f3d4", 4),
    0x0029E3D0: ("camp_func_0029e3d0", 0),
    0x0029E41C: ("camp_func_0029e41c", 0),
    0x0029E468: ("camp_func_0029e468", 0),
    0x002A0F68: ("camp_func_002a0f68", 1),
}

STUB_ADDRS = {addr: STUB_BASE + idx * 4 for idx, addr in enumerate(sorted(CALLEES))}
ADDR_BY_STUB = {v: k for k, v in STUB_ADDRS.items()}
NAME_TO_STUB = {CALLEES[k][0]: v for k, v in STUB_ADDRS.items()}


def encode_arm_branch(pc: int, target: int, link: bool) -> int:
    imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if link else 0xEA000000
    return opcode | imm24


def patch_orig_code(raw: bytes) -> bytearray:
    code = bytearray(raw)
    for off in range(0, len(code), 4):
        insn = struct.unpack_from("<I", code, off)[0]
        cond = (insn >> 28) & 0xF
        op = (insn >> 24) & 0xF
        if cond == 0xE and op in (0xA, 0xB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = FUNC_ADDR + off
            target = pc + 8 + (imm24 << 2)
            if target in STUB_ADDRS:
                struct.pack_into("<I", code, off, encode_arm_branch(pc, STUB_ADDRS[target], link=(op == 0xB)))
    return code


def get_func_st_value(obj_path: Path, target_name: str) -> int:
    elf = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", elf, 0x20)[0]
    e_shentsize, e_shnum, _ = struct.unpack_from("<HHH", elf, 0x2E)
    sections = [struct.unpack_from("<10I", elf, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    symtab = next(sh for sh in sections if sh[1] == 2)
    strtab = sections[symtab[6]]
    str_off = strtab[4]
    for idx in range(symtab[5] // 16):
        s_off = symtab[4] + idx * 16
        st_name, st_value = struct.unpack_from("<II", elf, s_off)
        end = elf.find(b"\x00", str_off + st_name)
        if elf[str_off + st_name : end].decode("ascii", errors="replace") == target_name:
            return st_value
    raise RuntimeError(f"{target_name} not found in symtab")


def patch_cand_code(raw: bytes, relocs: list, func_val: int) -> bytearray:
    code = bytearray(raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):
            insn = struct.unpack_from("<I", code, rel.offset)[0]
            cond = (insn >> 28) & 0xF
            op = (insn >> 24) & 0xF
            link = op == 0xB
            target = NAME_TO_STUB[rel.symbol_name]
            pc = FUNC_ADDR + rel.offset
            imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
            struct.pack_into("<I", code, rel.offset, (cond << 28) | ((0xB if link else 0xA) << 24) | imm24)
        elif rel.relocation_type == 2:  # R_ARM_ABS32 for .text switch table
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into("<I", code, rel.offset, (FUNC_ADDR - func_val) + addend)
        else:
            raise RuntimeError(f"Unsupported relocation type {rel.relocation_type} for {rel.symbol_name}")
    return code


def build_candidate(src_text: str | None = None) -> bytearray:
    out_dir = ROOT / "build" / "test_leaf_003a4144"
    out_dir.mkdir(parents=True, exist_ok=True)
    if src_text is None:
        src_path = SRC_CPP
        obj_path = out_dir / "baseline.o"
    else:
        src_path = out_dir / "mutant.cpp"
        obj_path = out_dir / "mutant.o"
        src_path.write_text(src_text, encoding="utf-8")

    res = compile_tu_armv6k(src_path, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compile failed:\n{res.stderr}")
    funcs = extract_elf_functions_detailed(obj_path)
    if FUNC_NAME not in funcs:
        raise RuntimeError(f"{FUNC_NAME} not found in compiled ELF")
    raw, relocs = funcs[FUNC_NAME]
    func_val = get_func_st_value(obj_path, FUNC_NAME)
    return patch_cand_code(raw, relocs, func_val)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(STUB_BASE, 0x1000)
        self.uc.mem_map(FUNC_ADDR & ~0xFFF, 0x2000)
        self.uc.mem_map(SELF_ADDR, MEM_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))

        for stub_addr in STUB_ADDRS.values():
            self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(SELF_ADDR, b"\x00" * MEM_SIZE)

        buf = bytearray(0x10000)
        struct.pack_into("<I", buf, 0x10, case.get("v10", 0))
        idx = case.get("v860", 0)
        struct.pack_into("<I", buf, 0x860, idx)
        r5_off = idx * 4098 + 0xC94
        struct.pack_into("<H", buf, r5_off + 0x1000, case.get("item_u16", 0x4321))
        self.uc.mem_write(SELF_ADDR, bytes(buf))

        call_log: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr not in ADDR_BY_STUB:
                return
            orig_target = ADDR_BY_STUB[addr]
            cname, arity = CALLEES[orig_target]
            regs = [uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4)]
            call_log.append((cname, *regs[:arity]))

            ret = 0
            if orig_target == 0x0029E468:
                ret = case.get("f_e468", 0)
            elif orig_target == 0x0029E3D0:
                ret = case.get("mode", 0)
            elif orig_target == 0x0022E7C4:
                ret = case.get("f_e7c4", 0)
            uc.reg_write(arm.UC_ARM_REG_R0, ret)

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_BASE, end=STUB_BASE + 0x100)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)
        finally:
            self.uc.hook_del(hook)

        return {
            "call_log": call_log,
            "state": struct.unpack("<II", self.uc.mem_read(SELF_ADDR + 4, 8)),
        }


def make_cases() -> list[dict]:
    cases = [
        {"name": "early_v10_1_v860_8", "f_e468": 1, "v10": 1, "v860": 8},
        {"name": "early_v10_1_v860_5", "f_e468": 1, "v10": 1, "v860": 5},
        {"name": "early_v10_0_v860_7", "f_e468": 0 + 1, "v10": 0, "v860": 7},
        {"name": "early_v10_0_v860_8", "f_e468": 1, "v10": 0, "v860": 8},
        {"name": "early_v10_0_v860_2", "f_e468": 1, "v10": 0, "v860": 2},
        {"name": "mode_unmatched", "f_e468": 0, "v860": 2, "mode": 99},
    ]
    for mode in (0xC, 0x1C, 3, 0x10, 0xF):
        for flag in (0, 1):
            cases.append({"name": f"mode_{mode:#x}_flag_{flag}", "f_e468": 0, "v860": 2, "mode": mode, "f_e7c4": flag})
    for v860 in (2, 8):
        for flag in (0, 1):
            cases.append({"name": f"mode_7_v860_{v860}_flag_{flag}", "f_e468": 0, "v860": v860, "mode": 7, "f_e7c4": flag})
    return cases


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = patch_orig_code(raw_bin[off : off + FUNC_SIZE])
    src_text = SRC_CPP.read_text(encoding="utf-8")
    cand_code = build_candidate()
    print(f"{FUNC_NAME}: orig {len(orig_code)} B, cand {len(cand_code)} B")

    cases = make_cases()
    for case in cases:
        orig_res = Runner().run(orig_code, case)
        cand_res = Runner().run(cand_code, case)
        if orig_res != cand_res:
            print(f"FAIL [{case['name']}]:")
            print("  orig:", orig_res)
            print("  cand:", cand_res)
            return 1
        print(f"PASS [{case['name']}]")

    mutants = [
        ("early_state_16", "state = (v860 == 8) ? 0x10u : 0xFu;", "state = (v860 == 8) ? 0x11u : 0xFu;"),
        ("r5_stride", "idx * 4098u + 0xC94u", "idx * 4096u + 0xC94u"),
        ("r0_stride", "idx * 116u + 0x880u", "idx * 120u + 0x880u"),
        ("cb_mode_c", "0x003A65C4u", "0x003A65C8u"),
        ("cb_mode_7_8", "0x003A08D4u", "0x003A08D8u"),
    ]
    for name, old, new in mutants:
        assert old in src_text, f"Mutant target not found: {old}"
        m_code = build_candidate(src_text.replace(old, new, 1))
        detected = False
        for case in cases:
            orig_res = Runner().run(orig_code, case)
            try:
                bad_res = Runner().run(m_code, case)
            except unicorn.UcError:
                detected = True
                break
            if orig_res != bad_res:
                detected = True
                break
        if not detected:
            print(f"FAIL [mutant {name}]: not detected!")
            return 1
        print(f"PASS [mutant {name} detected]")

    print(f"ALL PASS: {len(cases)} cases + {len(mutants)} negative controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
