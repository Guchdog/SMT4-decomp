#!/usr/bin/env python3
"""Differential test for ui_func_002108d0 (0x002108D0) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts ui_func_002108d0,
resolves all 13 external callees plus the render-stack callback and globals
(0x0043DA28, 0x0044EA00), and compares the pinned original against the compiled
candidate across inactive, state10, anim/sprite, text/bitmap, and mutant cases.
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
FUNC_ADDR = 0x002108D0
FUNC_SIZE = 788
FUNC_NAME = "ui_func_002108d0"

STUB_BASE = 0x00110000
STUB_STACK_CB = STUB_BASE + 0x40
GLOBAL_43D000 = 0x0043D000
GLOBAL_44E000 = 0x0044E000
G_UI_PTR = 0x0043DA28
G_GPU_PTR = 0x0044EA00

MEM_BASE = 0x20000000
MEM_SIZE = 0x00020000
UI_ADDR = 0x20000000
GPU_ADDR = 0x20001000
NODE1_ADDR = 0x20003000
NODE2_ADDR = 0x20003100
STACK_TOP = 0x2001F000
TRAP_ADDR = 0x001F0000

CALLEES = {
    0x00190D48: ("ui_func_00190d48", 0),
    0x001F4014: ("engine_func_001f4014", 3),
    0x0029A504: ("func_0029a504", 1),
    0x002B792C: ("func_002b792c", 4),
    0x002BE77C: ("ui_func_002be77c", 3),
    0x002BEF70: ("shop_func_002bef70", 1),
    0x002BEF7C: ("ui_func_002bef7c", 1),
    0x002BF460: ("ui_func_002bf460", 4),
    0x002BF6D0: ("camp_func_002bf6d0", 2),
    0x002C1ABC: ("ui_func_002c1abc", 1),
    0x002C1B64: ("ui_func_002c1b64", 1),
    0x002C3BA8: ("ui_func_002c3ba8", 1),
    0x002C5F7C: ("ui_func_002c5f7c", 2),
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
        if cond != 0xF and op in (0xA, 0xB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = FUNC_ADDR + off
            target = pc + 8 + (imm24 << 2)
            if target in STUB_ADDRS:
                struct.pack_into("<I", code, off, encode_arm_branch(pc, STUB_ADDRS[target], link=(op == 0xB)))
    return code


def patch_cand_code(raw: bytes, relocs: list) -> bytearray:
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
        else:
            raise RuntimeError(f"Unsupported relocation type {rel.relocation_type} for {rel.symbol_name}")
    return code


def build_candidate(src_text: str | None = None) -> bytearray:
    out_dir = ROOT / "build" / "test_leaf_002108d0"
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
    return patch_cand_code(raw, relocs)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        self.uc.mem_map(STUB_BASE, 0x1000)
        self.uc.mem_map(FUNC_ADDR & ~0xFFF, 0x2000)
        self.uc.mem_map(GLOBAL_43D000, 0x1000)
        self.uc.mem_map(GLOBAL_44E000, 0x1000)
        self.uc.mem_map(MEM_BASE, MEM_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))

        for addr in list(STUB_ADDRS.values()) + [STUB_STACK_CB]:
            self.uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)
        self.uc.mem_write(G_UI_PTR + 4, struct.pack("<I", UI_ADDR))
        self.uc.mem_write(G_GPU_PTR, struct.pack("<I", GPU_ADDR))

        ui = bytearray(0x600)
        struct.pack_into("<I", ui, 0x10, case.get("state10", 0))
        struct.pack_into("<i", ui, 0x3A8, case.get("v3a8", 0x3F800000))
        ui[0x4C4] = case.get("b4c4", 1)
        ui[0x4C5] = case.get("b4c5", 1)
        ui[0x4C8] = case.get("b4c8", 0)
        ui[0x4CB] = case.get("b4cb", 1)
        struct.pack_into("<I", ui, 0x4CC, 0xAABBCCDD)
        ui[0x4D0:0x4D4] = b"STR1"
        ui[0x510:0x514] = b"STR2"
        ui[0x554] = case.get("b554", 0)
        struct.pack_into("<I", ui, 0x558, 0x30000000)
        ui[0x55C] = case.get("b55c", 0)
        self.uc.mem_write(UI_ADDR, bytes(ui))

        gpu = bytearray(0x1300)
        struct.pack_into("<II", gpu, 0x124C, 0, 0)
        struct.pack_into("<I", gpu, 0x1254, case.get("prev_mode", 9))
        gpu[0x1264] = case.get("dirty", 0)
        struct.pack_into("<I", gpu, 0x1268, STUB_STACK_CB)
        self.uc.mem_write(GPU_ADDR, bytes(gpu))

        self.uc.mem_write(NODE1_ADDR + 8, struct.pack("<hh", 10, 20))
        self.uc.mem_write(NODE2_ADDR + 8, struct.pack("<hh", 30, 40))

        call_log: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc.reg_read(arm.UC_ARM_REG_R3)
            if addr == STUB_STACK_CB:
                call_log.append(("stack_cb", r0))
                return
            if addr not in ADDR_BY_STUB:
                return
            orig_target = ADDR_BY_STUB[addr]
            cname, arity = CALLEES[orig_target]
            if orig_target == 0x002B792C:
                s0 = round(struct.unpack("<f", struct.pack("<I", uc.reg_read(arm.UC_ARM_REG_S0)))[0], 4)
                sp = uc.reg_read(arm.UC_ARM_REG_SP)
                st = struct.unpack("<2I", uc.mem_read(sp, 8))
                call_log.append((cname, r0, r1, r2, r3, s0, st))
            elif orig_target == 0x002BE77C:
                s = [round(struct.unpack("<f", struct.pack("<I", uc.reg_read(getattr(arm, f"UC_ARM_REG_S{i}"))))[0], 4) for i in range(5)]
                call_log.append((cname, r0, r1, r2, tuple(s)))
            elif orig_target == 0x002BF460:
                sp = uc.reg_read(arm.UC_ARM_REG_SP)
                st = struct.unpack("<2I", uc.mem_read(sp, 8))
                call_log.append((cname, r0, r1, r2, r3, st))
            else:
                call_log.append((cname, *(r0, r1, r2, r3)[:arity]))

            ret = 0
            if orig_target == 0x002C5F7C:
                ret = case.get("new_mode", 7)
            elif orig_target == 0x002BEF7C:
                ret = 111
            elif orig_target == 0x002BEF70:
                ret = 222
            elif orig_target == 0x002BF6D0:
                ret = NODE1_ADDR if r1 == 0x1D else NODE2_ADDR
            uc.reg_write(arm.UC_ARM_REG_R0, ret)

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_BASE, end=STUB_STACK_CB + 4)
        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)
        finally:
            self.uc.hook_del(hook)

        return {"ret": self.uc.reg_read(arm.UC_ARM_REG_R0), "call_log": call_log}


def make_cases() -> list[dict]:
    return [
        {"name": "b4c4_zero_early_exit", "b4c4": 0},
        {"name": "state10_gt3_skips_draw", "state10": 4, "prev_mode": 7, "new_mode": 7},
        {"name": "b4c8_1_b55c_1_bitmaps", "state10": 1, "b4c8": 1, "b55c": 1},
        {"name": "b4c8_0_b554_0_text_and_1f4014", "state10": 2, "b4c8": 0, "b55c": 0, "b554": 0},
        {"name": "b4c8_0_b554_1_1f4014_and_text", "state10": 3, "b4c8": 0, "b55c": 0, "b554": 1},
        {"name": "v3a8_below_1f_skips_prompts", "state10": 0, "v3a8": 0x3F000000},
    ]


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
        ("b4c4_gate", "r4[0x4C4] == 0", "r4[0x4C5] == 0"),
        ("state10_bound", "state10 <= 3", "state10 <= 2"),
        ("bf460_group", "ui_func_002bf460(2, 0x12, 0, x, y, 0x10);", "ui_func_002bf460(2, 0x13, 0, x, y, 0x10);"),
        ("be77c_scale", "0x3F6E147Bu", "0x3F800000u"),
        ("b554_cmp", "r4[0x554] != 1", "r4[0x554] != 2"),
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
