#!/usr/bin/env python3
"""Differential test for ui_func_003be55c (0x003BE55C) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts ui_func_003be55c,
resolves all 10 external callees (including ui_func_003beb40), and compares
the pinned original against the compiled candidate across r8!=0 (kind 0/1,
flags 0x8000, view[0x1E], 0x200/0x80 modifiers, bonus roll) and r8==0
(secondary_id < 0x6D vs >= 0x6D, cap to 1) plus mutant negative controls.
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
FUNC_ADDR = 0x003BE55C
FUNC_SIZE = 792
FUNC_NAME = "ui_func_003be55c"

STUB_BASE = 0x00110000
MEM_BASE = 0x20000000
MEM_SIZE = 0x00020000
UI_ADDR = 0x20000000
OBJ_ADDR = 0x20005000
SKILL_ADDR = 0x20006000
ROW1_ADDR = 0x20007000
ROW2_ADDR = 0x20008000
REC_ADDR = 0x20009000
STACK_TOP = 0x2001F000
TRAP_ADDR = 0x001F0000

CALLEES = {
    0x0023EC3C: ("script_vm_func_0023ec3c", 1),
    0x002475E4: ("camp_func_002475e4", 3),
    0x0027DCA0: ("ui_func_0027dca0", 2),
    0x00282B94: ("ui_func_00282b94", 2),
    0x00293C98: ("ui_func_00293c98", 0),
    0x0029EE4C: ("camp_func_0029ee4c", 2),
    0x002A89E4: ("camp_func_002a89e4", 1),
    0x002AE3F0: ("battle_func_002ae3f0", 1),
    0x002B4854: ("camp_func_002b4854", 1),
    0x003BEB40: ("ui_func_003beb40", 4),
}

STUB_ADDRS = {addr: STUB_BASE + idx * 4 for idx, addr in enumerate(sorted(CALLEES))}
ADDR_BY_STUB = {v: k for k, v in STUB_ADDRS.items()}
NAME_TO_STUB = {CALLEES[k][0]: v for k, v in STUB_ADDRS.items()}


def f32_bits(v: float) -> int:
    return struct.unpack("<I", struct.pack("<f", v))[0]


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
    out_dir = ROOT / "build" / "test_leaf_003be55c"
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
        self.uc.mem_map(MEM_BASE, MEM_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))

        for addr in STUB_ADDRS.values():
            self.uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)

        ui = bytearray(0x4600)
        struct.pack_into("<I", ui, 0xE0, case.get("ui_e0", 0))
        struct.pack_into("<I", ui, 0x44A0, case.get("ui_44a0", 0))
        struct.pack_into("<I", ui, 0x44AC, case.get("ui_44ac", 0))
        self.uc.mem_write(UI_ADDR, bytes(ui))

        obj = bytearray(0x40)
        obj[0x23] = case.get("kind", 1)
        struct.pack_into("<H", obj, 0x2C, case.get("obj_2c", 100))
        struct.pack_into("<I", obj, 0x38, case.get("obj_38", 0))
        self.uc.mem_write(OBJ_ADDR, bytes(obj))

        row1 = bytearray(0x200)
        struct.pack_into("<H", row1, 0x1C6, case.get("row1_1c6", 0))
        self.uc.mem_write(ROW1_ADDR, bytes(row1))

        row2 = bytearray(0x200)
        struct.pack_into("<h", row2, 0x1B8, case.get("row2_1b8", 250))
        struct.pack_into("<H", row2, 0x1C6, case.get("row2_1c6", 0))
        self.uc.mem_write(ROW2_ADDR, bytes(row2))

        sk = bytearray(0x80)
        struct.pack_into("<H", sk, 0x66, case.get("sk_66", 0))
        sk[0x69] = case.get("sk_69", 0) & 0xFF
        self.uc.mem_write(SKILL_ADDR, bytes(sk))

        rec = bytearray(0x100)
        struct.pack_into("<H", rec, 0x10, case.get("rec_10", 400))
        struct.pack_into("<H", rec, 0xEE, case.get("rec_ee", 300))
        self.uc.mem_write(REC_ADDR, bytes(rec))

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

            if orig_target == 0x003BEB40:
                s0 = round(struct.unpack("<f", struct.pack("<I", uc.reg_read(arm.UC_ARM_REG_S0)))[0], 4)
                s1 = round(struct.unpack("<f", struct.pack("<I", uc.reg_read(arm.UC_ARM_REG_S1)))[0], 4)
                sp = uc.reg_read(arm.UC_ARM_REG_SP)
                st0 = struct.unpack("<i", uc.mem_read(sp, 4))[0]
                call_log.append((cname, r0, r1, r2, r3, st0, s0, s1))
            elif orig_target == 0x002475E4:
                call_log.append((cname, r1, r2))
            else:
                call_log.append((cname, *(r0, r1, r2, r3)[:arity]))

            ret = 0
            if orig_target == 0x00293C98:
                ret = UI_ADDR
            elif orig_target == 0x002AE3F0:
                ret = OBJ_ADDR if case.get("has_obj", True) else 0
            elif orig_target == 0x002B4854:
                ret = SKILL_ADDR if case.get("has_sk", True) else 0
            elif orig_target == 0x00282B94:
                ret = ROW1_ADDR if r1 == case["primary_id"] else ROW2_ADDR
            elif orig_target == 0x002475E4:
                v = bytearray(0x28)
                v[0x1D] = case.get("v1d", 0)
                v[0x1E] = case.get("v1e", 1)
                struct.pack_into("<bb", v, 0x1F, case.get("v1f", 2), case.get("v20", 3))
                uc.mem_write(r0, bytes(v))
            elif orig_target == 0x003BEB40:
                ret = case.get("beb40_ret", 120)
            elif orig_target == 0x0023EC3C:
                ret = 5
            elif orig_target in (0x0027DCA0, 0x002A89E4):
                ret = REC_ADDR
            elif orig_target == 0x0029EE4C:
                ret = case.get("ee4c_ret", 1)
            uc.reg_write(arm.UC_ARM_REG_R0, ret & 0xFFFFFFFF)

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_BASE, end=STUB_BASE + 0x100)
        sp_init = STACK_TOP - 8
        self.uc.mem_write(sp_init, struct.pack("<ii", case["primary_id"], case["secondary_id"]))
        self.uc.reg_write(arm.UC_ARM_REG_R0, case.get("a0", 1))
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x30001000)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x30002000)
        self.uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(case.get("base_val", 1.5)))
        self.uc.reg_write(arm.UC_ARM_REG_SP, sp_init)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)
        finally:
            self.uc.hook_del(hook)

        return {
            "ret": struct.unpack("<i", struct.pack("<I", self.uc.reg_read(arm.UC_ARM_REG_R0)))[0],
            "call_log": call_log,
        }


def make_cases() -> list[dict]:
    return [
        {"name": "v1e_0_v1d_1_returns_minus1", "primary_id": 10, "secondary_id": 20, "v1e": 0, "v1d": 1},
        {"name": "obj_flags_7f0000_returns_minus1", "primary_id": 10, "secondary_id": 20, "obj_38": 0x10000},
        {"name": "obj_kind_1_flag_8000_half_row2", "primary_id": 10, "secondary_id": 20, "obj_38": 0x8000, "row2_1b8": 151},
        {
            "name": "obj_kind_1_beb40_div3_cap100_mods_bonus",
            "primary_id": 10,
            "secondary_id": 20,
            "beb40_ret": 303,
            "row1_1c6": 0x200,
            "row2_1c6": 0x80,
            "row2_1b8": 200,
        },
        {"name": "obj_kind_0_skips_calc", "primary_id": 10, "secondary_id": 20, "kind": 0},
        {"name": "no_obj_a0_0_sec_lt_6d_cap1", "primary_id": 10, "secondary_id": 20, "has_obj": False, "a0": 0, "sk_69": 50, "rec_ee": 400, "row2_1c6": 8},
        {"name": "no_obj_a0_0_sec_ge_6d_ee4c_1", "primary_id": 10, "secondary_id": 0x6D, "has_obj": False, "a0": 0, "sk_69": 50, "rec_10": 400, "ee4c_ret": 1},
        {"name": "no_obj_a0_0_sk69_0_uses_sk66", "primary_id": 10, "secondary_id": 0x70, "has_obj": False, "a0": 0, "sk_66": 42, "sk_69": 0, "ee4c_ret": 0},
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
        ("obj_8000", "flags38 & 0x8000u", "flags38 & 0x4000u"),
        ("div3_cap100", "if (r4 > 0x64) {", "if (r4 > 0x65) {"),
        ("mod_200", "primary_row + 0x1C6) & 0x200u", "primary_row + 0x1C6) & 0x400u"),
        ("bonus_roll", "script_vm_func_0023ec3c(0xF)", "script_vm_func_0023ec3c(0xE)"),
        ("sec_6d_thresh", "secondary_id < 0x6D", "secondary_id < 0x6E"),
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
