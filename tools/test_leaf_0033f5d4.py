#!/usr/bin/env python3
"""Differential test for func_0033f5d4 (0x0033F5D4) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts func_0033f5d4,
resolves battle_func_0033d660 and battle_func_0023e180, and compares the
pinned original against the compiled candidate across idx>=count, empty range,
exact keyframe hit, linear interpolation, flag==0 vs flag!=0, and mutants.
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
FUNC_ADDR = 0x0033F5D4
FUNC_SIZE = 788
FUNC_NAME = "func_0033f5d4"

STUB_BASE = 0x00110000
STUB_33D660 = STUB_BASE + 0x00
STUB_23E180 = STUB_BASE + 0x04

MEM_BASE = 0x20000000
MEM_SIZE = 0x00010000
SELF_ADDR = 0x20000000
META_ADDR = 0x20001000
RANGE_ADDR = 0x20002000
KEYS_ADDR = 0x20003000
STACK_TOP = 0x2000F000
TRAP_ADDR = 0x001F0000


def f32_bits(v: float) -> int:
    return struct.unpack("<I", struct.pack("<f", v))[0]


def encode_arm_branch(pc: int, target: int, link: bool) -> int:
    imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if link else 0xEA000000
    return opcode | imm24


def patch_orig_code(raw: bytes) -> bytearray:
    code = bytearray(raw)
    mapping = {0x0033D660: STUB_33D660, 0x0023E180: STUB_23E180}
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
            if target in mapping:
                struct.pack_into("<I", code, off, encode_arm_branch(pc, mapping[target], link=(op == 0xB)))
    return code


def patch_cand_code(raw: bytes, relocs: list) -> bytearray:
    code = bytearray(raw)
    mapping = {"battle_func_0033d660": STUB_33D660, "battle_func_0023e180": STUB_23E180}
    for rel in relocs:
        if rel.relocation_type in (28, 29):
            insn = struct.unpack_from("<I", code, rel.offset)[0]
            cond = (insn >> 28) & 0xF
            op = (insn >> 24) & 0xF
            link = op == 0xB
            target = mapping[rel.symbol_name]
            pc = FUNC_ADDR + rel.offset
            imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
            struct.pack_into("<I", code, rel.offset, (cond << 28) | ((0xB if link else 0xA) << 24) | imm24)
        else:
            raise RuntimeError(f"Unsupported relocation type {rel.relocation_type} for {rel.symbol_name}")
    return code


def build_candidate(src_text: str | None = None) -> bytearray:
    out_dir = ROOT / "build" / "test_leaf_0033f5d4"
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

        for addr in (STUB_33D660, STUB_23E180):
            self.uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)

        self.uc.mem_write(SELF_ADDR + 0x10, struct.pack("<I", META_ADDR))
        self.uc.mem_write(SELF_ADDR + 0x20, struct.pack("<I", KEYS_ADDR))
        self.uc.mem_write(SELF_ADDR + 0x24, struct.pack("<I", RANGE_ADDR))

        self.uc.mem_write(META_ADDR + 0x0E, struct.pack("<H", case.get("meta_count", 4)))

        idx = case["idx"]
        self.uc.mem_write(
            RANGE_ADDR + idx * 4,
            struct.pack("<HH", case.get("start_k", 0), case.get("len_k", 2)),
        )

        keys_buf = bytearray(0x200)
        for k_i, (t, f8, fc, f10, f14) in enumerate(case.get("keys", [])):
            off = k_i * 24
            struct.pack_into("<i", keys_buf, off + 0x04, t)
            struct.pack_into("<ffff", keys_buf, off + 0x08, f8, fc, f10, f14)
        self.uc.mem_write(KEYS_ADDR, bytes(keys_buf))

        call_log: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r2 = uc.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc.reg_read(arm.UC_ARM_REG_R3)
            s0 = round(struct.unpack("<f", struct.pack("<I", uc.reg_read(arm.UC_ARM_REG_S0)))[0], 5)
            sp = uc.reg_read(arm.UC_ARM_REG_SP)
            if addr == STUB_33D660:
                st0, p_xy, p_uv, st3 = struct.unpack("<IIII", uc.mem_read(sp, 16))
                f_xy = tuple(round(x, 5) for x in struct.unpack("<2f", uc.mem_read(p_xy, 8)))
                f_uv = tuple(round(x, 5) for x in struct.unpack("<2f", uc.mem_read(p_uv, 8)))
                call_log.append(("33d660", r0, r2, r3, s0, round(struct.unpack("<f", struct.pack("<I", st0))[0], 5), f_xy, f_uv, round(struct.unpack("<f", struct.pack("<I", st3))[0], 5)))
            elif addr == STUB_23E180:
                st0 = struct.unpack("<I", uc.mem_read(sp, 4))[0]
                call_log.append(("23e180", r0, r2, r3, s0, round(struct.unpack("<f", struct.pack("<I", st0))[0], 5)))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_BASE, end=STUB_BASE + 0x10)
        sp_init = STACK_TOP - 12
        self.uc.mem_write(sp_init, struct.pack("<fIf", case["f0"], case["flag"], case["f2"]))
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, idx)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x1111)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x2222)
        self.uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(case["time"]))
        self.uc.reg_write(arm.UC_ARM_REG_S1, f32_bits(case["s1"]))
        self.uc.reg_write(arm.UC_ARM_REG_SP, sp_init)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)
        finally:
            self.uc.hook_del(hook)

        return {"call_log": call_log}


KEYS = [
    (0, 10.0, 20.0, 50.0, 60.0),
    (10, 30.0, 60.0, 150.0, 260.0),
    (20, 40.0, 80.0, 200.0, 300.0),
]


def make_cases() -> list[dict]:
    return [
        {"name": "idx_ge_meta_count_early_exit", "meta_count": 2, "idx": 2, "time": 5.0, "s1": 1.0, "f0": 0.5, "flag": 1, "f2": 0.25},
        {"name": "exact_keyframe_hit_flag1", "idx": 0, "start_k": 0, "len_k": 3, "keys": KEYS, "time": 10.0, "s1": 1.5, "f0": 0.5, "flag": 1, "f2": 0.25},
        {"name": "interp_between_keys_flag1", "idx": 0, "start_k": 0, "len_k": 3, "keys": KEYS, "time": 15.0, "s1": 2.0, "f0": 0.5, "flag": 1, "f2": 0.25},
        {"name": "past_end_uses_last_key_flag0", "idx": 0, "start_k": 0, "len_k": 3, "keys": KEYS, "time": 25.0, "s1": 1.0, "f0": 0.75, "flag": 0, "f2": 0.5},
        {"name": "empty_range_uses_last_key_flag1", "idx": 0, "start_k": 2, "len_k": 0, "keys": KEYS, "time": 5.0, "s1": 1.0, "f0": 0.5, "flag": 1, "f2": 0.25},
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
        ("meta_count_guard", "idx >= *reinterpret_cast<const u16*>(meta + 0x0Eu)", "idx > *reinterpret_cast<const u16*>(meta + 0x0Eu)"),
        ("uv_scale", "0x3C23D70Au", "0x3C33D70Au"),
        ("key_stride", "keys + k * 24", "keys + k * 28"),
        ("flag_branch", "if (args.flag != 0)", "if (args.flag == 0)"),
        ("last_k_off", "last_k * 24", "last_k * 28"),
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
