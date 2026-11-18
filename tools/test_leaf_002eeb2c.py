#!/usr/bin/env python3
"""Differential test for camp_func_002eeb2c (0x002EEB2C) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts camp_func_002eeb2c,
resolves all 27 external callees and 4 global regions, and compares the pinned
original against the compiled candidate across all state/step branches and
mutant negative controls.
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
FUNC_ADDR = 0x002EEB2C
FUNC_SIZE = 816
FUNC_NAME = "camp_func_002eeb2c"

STUB_BASE = 0x00110000
G_447000 = 0x00447000
G_49F000 = 0x0049F000
G_9F91C = 0x0049F91C
G_47518 = 0x00447518
G_47E88 = 0x00447E88
G_474D8 = 0x004474D8

MEM_BASE = 0x20000000
MEM_SIZE = 0x00010000
PTR_47E88 = 0x20000000
PTR_474D8 = 0x20001000
STACK_TOP = 0x2000F000
TRAP_ADDR = 0x001F0000

CALLEES = {
    0x001B4B74: ("camp_func_001b4b74", 0),
    0x0020E984: ("camp_func_0020e984", 0),
    0x00215958: ("camp_func_00215958", 1),
    0x00274200: ("script_vm_func_00274200", 0),
    0x00274230: ("script_vm_func_00274230", 0),
    0x00274A08: ("script_vm_func_00274a08", 0),
    0x0027521C: ("engine_func_0027521c", 0),
    0x0027549C: ("script_vm_func_0027549c", 0),
    0x002755D4: ("script_vm_func_002755d4", 0),
    0x00275984: ("script_vm_func_00275984", 0),
    0x00275A18: ("script_vm_func_00275a18", 0),
    0x00275A8C: ("script_vm_func_00275a8c", 0),
    0x00275B48: ("script_vm_func_00275b48", 0),
    0x00275C2C: ("script_vm_func_00275c2c", 0),
    0x00275CA0: ("script_vm_func_00275ca0", 0),
    0x00275E38: ("script_vm_func_00275e38", 0),
    0x00275E58: ("script_vm_func_00275e58", 1),
    0x00276034: ("script_vm_func_00276034", 0),
    0x002767AC: ("camp_func_002767ac", 0),
    0x0027D700: ("script_vm_func_0027d700", 1),
    0x0027DE14: ("script_vm_func_0027de14", 0),
    0x00280D30: ("FrameTex_func_00280d30", 1),
    0x0028A688: ("Camp_Init", 2),
    0x00294AD8: ("ui_func_00294ad8", 4),
    0x0029B0FC: ("ui_func_0029b0fc", 1),
    0x002B89D4: ("script_vm_func_002b89d4", 0),
    0x0031B960: ("camp_func_0031b960", 0),
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
    out_dir = ROOT / "build" / "test_leaf_002eeb2c"
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
        self.uc.mem_map(G_447000, 0x2000)
        self.uc.mem_map(G_49F000, 0x1000)
        self.uc.mem_map(MEM_BASE, MEM_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))

        for addr in STUB_ADDRS.values():
            self.uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)
        self.uc.mem_write(G_447000, b"\x00" * 0x2000)
        self.uc.mem_write(G_49F000, b"\x00" * 0x1000)

        self.uc.mem_write(G_47E88, struct.pack("<I", PTR_47E88))
        self.uc.mem_write(G_474D8, struct.pack("<I", PTR_474D8))
        self.uc.mem_write(PTR_47E88 + 0x1C, struct.pack("<3I", 11, 22, 33))
        self.uc.mem_write(PTR_47E88 + 0x194, struct.pack("<I", 0x55556666))

        g9 = bytearray(0x240)
        struct.pack_into("<II", g9, 0x04, 0x77778888, 0)
        struct.pack_into("<I", g9, 0x14, case.get("mode14", 0))
        g9[0x23] = case.get("b23", 0)
        self.uc.mem_write(G_9F91C, bytes(g9))

        g4 = bytearray(0x10)
        g4[0] = case.get("b0", 1)
        g4[1] = case.get("b1", 0)
        g4[2] = case.get("b2", 0)
        struct.pack_into("<i", g4, 4, case.get("step", 0))
        self.uc.mem_write(G_47518, bytes(g4))

        call_log: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr not in ADDR_BY_STUB:
                return
            orig_target = ADDR_BY_STUB[addr]
            cname, arity = CALLEES[orig_target]
            regs = [uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4)]
            if orig_target == 0x00294AD8:
                s = [round(struct.unpack("<f", struct.pack("<I", uc.reg_read(getattr(arm, f"UC_ARM_REG_S{i}"))))[0], 3) for i in range(9)]
                sp = uc.reg_read(arm.UC_ARM_REG_SP)
                st = struct.unpack("<8I", uc.mem_read(sp, 32))
                call_log.append((cname, *regs, tuple(s), st))
            else:
                call_log.append((cname, *regs[:arity]))

            ret = 0
            if orig_target == 0x0020E984:
                ret = case.get("ret_20e984", 1)
            elif orig_target == 0x0031B960:
                ret = case.get("ret_31b960", 1)
            elif orig_target == 0x002B89D4:
                ret = case.get("ret_2b89d4", 0)
            uc.reg_write(arm.UC_ARM_REG_R0, ret)

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_BASE, end=STUB_BASE + 0x100)
        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)
        finally:
            self.uc.hook_del(hook)

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "call_log": call_log,
            "g4": bytes(self.uc.mem_read(G_47518, 8)),
            "g9_22": (self.uc.mem_read(G_9F91C + 0x22, 2), self.uc.mem_read(G_9F91C + 0x22C, 1)),
            "p47e88_28": struct.unpack("<3I", self.uc.mem_read(PTR_47E88 + 0x28, 12)),
            "p474d8_a": self.uc.mem_read(PTR_474D8 + 0x0A, 1)[0],
        }


def make_cases() -> list[dict]:
    return [
        {"name": "mode3_done_clears_flags", "mode14": 3, "b23": 1, "b0": 0, "b2": 0, "ret_20e984": 1},
        {"name": "mode3_pending_returns_0", "mode14": 3, "b23": 0, "b0": 1, "ret_20e984": 0},
        {"name": "b1_cleanup_returns_1", "mode14": 0, "b0": 1, "b1": 1, "b2": 1},
        {"name": "step0_copies_vec_and_inc", "mode14": 0, "b0": 0, "step": 99},
        {"name": "step10_triggers_fade", "mode14": 0, "b0": 1, "step": 10},
        {"name": "step11_sets_b22_and_calls_275ca0", "mode14": 0, "b0": 1, "step": 11},
        {"name": "step12_ready_starts_camp_and_sets_100", "mode14": 0, "b0": 1, "step": 12, "ret_31b960": 1},
        {"name": "step100_finishes_when_2b89d4_0", "mode14": 0, "b0": 1, "step": 100, "ret_2b89d4": 0},
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
        ("mode3_check", "*reinterpret_cast<const u32*>(g9 + 0x14) == 3", "*reinterpret_cast<const u32*>(g9 + 0x14) == 4"),
        ("step_10", "step == 0x0A", "step == 0x09"),
        ("step_11", "*reinterpret_cast<const s32*>(g4 + 4) == 0x0B", "*reinterpret_cast<const s32*>(g4 + 4) == 0x0C"),
        ("step_12_gate", "cur > 0x0C", "cur > 0x0D"),
        ("ui_94ad8_s0", "90.0f, -0.5f", "91.0f, -0.5f"),
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
