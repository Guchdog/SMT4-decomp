#!/usr/bin/env python3
"""Differential test for ui_func_00126920 (0x00126920) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts ui_func_00126920,
resolves its 6 callees and globals (0x0043DFC0, 0x0043E048), and compares
the pinned original against the compiled candidate across all state/model/
offset/0xC8 branches and mutant negative controls.
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
FUNC_ADDR = 0x00126920
FUNC_SIZE = 792
FUNC_NAME = "ui_func_00126920"

STUB_BASE = 0x00110000
GLOBAL_PAGE = 0x0043D000
G_OBJ_PTR = 0x0043DFC0
G_KEYS_ARR = 0x0043E048

MEM_BASE = 0x20000000
MEM_SIZE = 0x00010000
OBJ_ADDR = 0x20000000
MDL_ADDR = 0x20001000
MDL8_ADDR = 0x20002000
STACK_TOP = 0x2000F000
TRAP_ADDR = 0x001F0000

CALLEES = {
    0x00138878: ("ui_func_00138878", 3),
    0x002ADF2C: ("engine_func_002adf2c", 4),
    0x002AE074: ("engine_func_002ae074", 3),
    0x002AE16C: ("engine_func_002ae16c", 1),
    0x002AE18C: ("ui_func_002ae18c", 2),
    0x002BF41C: ("battle_func_002bf41c", 1),
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
    out_dir = ROOT / "build" / "test_leaf_00126920"
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
        self.uc.mem_map(GLOBAL_PAGE, 0x2000)
        self.uc.mem_map(MEM_BASE, MEM_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))

        for addr in STUB_ADDRS.values():
            self.uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)
        self.uc.mem_write(G_OBJ_PTR, struct.pack("<I", OBJ_ADDR if case.get("obj_ok", True) else 0))
        self.uc.mem_write(G_KEYS_ARR, struct.pack("<4I", 101, 102, 103, 104))

        obj = bytearray(0x680)
        struct.pack_into("<f", obj, 0x5D8, 12.0)
        struct.pack_into("<I", obj, 0x5E0, 0x5555)
        struct.pack_into("<I", obj, 0x5E4, MDL_ADDR if case.get("has_mdl", True) else 0)
        struct.pack_into("<I", obj, 0x5E8, 77)
        struct.pack_into("<I", obj, 0x5EC, case.get("state", 5))
        struct.pack_into("<II", obj, 0x5F4, case.get("v5f4", 0), case.get("v5f8", 0))
        struct.pack_into("<ii", obj, 0x5FC, case.get("c5fc", 0), case.get("c600", 0))
        for idx, val in enumerate(case.get("slots", (0, 0, 0, 0))):
            struct.pack_into("<I", obj, 0x630 + idx * 4, val)
        struct.pack_into("<fff", obj, 0x640, 1.5, 2.5, 3.5)
        struct.pack_into("<ff", obj, 0x650, 4.5, 5.5)
        self.uc.mem_write(OBJ_ADDR, bytes(obj))
        self.uc.mem_write(MDL_ADDR + 8, struct.pack("<I", MDL8_ADDR))

        call_log: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr not in ADDR_BY_STUB:
                return
            orig_target = ADDR_BY_STUB[addr]
            cname, arity = CALLEES[orig_target]
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc.reg_read(arm.UC_ARM_REG_R3)

            if orig_target == 0x002ADF2C:
                va = tuple(round(x, 4) for x in struct.unpack("<3f", uc.mem_read(r1, 12)))
                vb = tuple(round(x, 4) for x in struct.unpack("<3f", uc.mem_read(r2, 12)))
                sp = uc.reg_read(arm.UC_ARM_REG_SP)
                st0, st1 = struct.unpack("<ii", uc.mem_read(sp, 8))
                call_log.append((cname, r0, va, vb, r3, st0, st1))
            elif orig_target == 0x00138878:
                s0 = round(struct.unpack("<f", struct.pack("<I", uc.reg_read(arm.UC_ARM_REG_S0)))[0], 4)
                s1 = round(struct.unpack("<f", struct.pack("<I", uc.reg_read(arm.UC_ARM_REG_S1)))[0], 4)
                call_log.append((cname, r0, r1, r2, s0, s1))
            elif orig_target == 0x002AE074:
                call_log.append((cname, r0, r1))
            else:
                call_log.append((cname, *(r0, r1, r2, r3)[:arity]))

            ret = 0
            if orig_target == 0x002BF41C:
                ret = 1 if r0 in case.get("alive", ()) else 0
            elif orig_target == 0x002AE16C:
                ret = case.get("mdl_ready", 1)
            elif orig_target == 0x002AE074:
                ret = case.get("bone_ok", 1)
                if ret:
                    uc.mem_write(r2, struct.pack("<3f", 10.0, 20.0, 30.0))
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
            "state": struct.unpack("<I", self.uc.mem_read(OBJ_ADDR + 0x5EC, 4))[0],
            "slots": struct.unpack("<4I", self.uc.mem_read(OBJ_ADDR + 0x630, 16)),
        }


def make_cases() -> list[dict]:
    return [
        {"name": "null_obj_returns_1", "obj_ok": False},
        {"name": "state_2_returns_1", "state": 2},
        {"name": "state_4_returns_0", "state": 4},
        {
            "name": "state5_c600_200_and_c5fc_200",
            "state": 5,
            "slots": (0x3001, 0x3002, 0x3003, 0),
            "alive": (0x3001, 0x3002),
            "c600": 0xC8,
            "c5fc": 0xC8,
            "v5f4": 1,
            "v5f8": 2,
        },
        {
            "name": "state5_c5fc_200_slot0_and_slot1",
            "state": 5,
            "slots": (0x3001, 0x3002, 0, 0),
            "alive": (0x3001, 0x3002),
            "c600": 0,
            "c5fc": 0xC8,
            "v5f4": 0,
            "v5f8": 0,
        },
        {
            "name": "state5_bone_fail_calls_138878",
            "state": 5,
            "slots": (0x3001, 0x3002, 0, 0),
            "alive": (0x3001, 0x3002),
            "bone_ok": 0,
        },
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
        ("state_2_3", "state == 2 || state == 3", "state == 2 || state == 4"),
        ("vec_a_648", "r5 + 0x648", "r5 + 0x64C"),
        ("c600_flag_1", "z_bias, 1);", "z_bias, 2);"),
        ("c5fc_flag_7", "z_bias, 7);", "z_bias, 8);"),
        ("end_state_6", "*reinterpret_cast<u32*>(r5 + 0x5EC) = 6;", "*reinterpret_cast<u32*>(r5 + 0x5EC) = 7;"),
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
