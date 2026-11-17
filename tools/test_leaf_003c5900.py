#!/usr/bin/env python3
"""Differential test for battle_func_003c5900 (0x003C5900) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts battle_func_003c5900,
resolves battle_func_002564cc, battle_func_0022a5d8, and battle_func_0022a5f8,
and exhaustively compares all 26 dispatch indices (0..25) plus out-of-range
inputs and mutant negative controls.
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
FUNC_ADDR = 0x003C5900
FUNC_SIZE = 804
FUNC_NAME = "battle_func_003c5900"

STUB_BASE = 0x00110000
MEM_BASE = 0x20000000
MEM_SIZE = 0x00010000
SELF_ADDR = 0x20000000
DST_ADDR = 0x20001000
PTR_ADDR = 0x20005000
STACK_TOP = 0x2000F000
TRAP_ADDR = 0x001F0000

CALLEES = {
    0x0022A5D8: ("battle_func_0022a5d8", 1),
    0x0022A5F8: ("battle_func_0022a5f8", 1),
    0x002564CC: ("battle_func_002564cc", 1),
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
    out_dir = ROOT / "build" / "test_leaf_003c5900"
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
        self.uc.mem_map(STUB_BASE, 0x1000)
        self.uc.mem_map(FUNC_ADDR & ~0xFFF, 0x2000)
        self.uc.mem_map(MEM_BASE, MEM_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))

        for addr in STUB_ADDRS.values():
            self.uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, idx: int) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)
        self.uc.mem_write(SELF_ADDR + 0x10, struct.pack("<I", 0x30001234))
        self.uc.mem_write(PTR_ADDR, struct.pack("<I", 0xCAFEBABE))

        call_log: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr not in ADDR_BY_STUB:
                return
            orig_target = ADDR_BY_STUB[addr]
            cname, _ = CALLEES[orig_target]
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            call_log.append((cname, r0))

            ret = 0
            if orig_target == 0x002564CC:
                ret = idx & 0xFFFFFFFF
            elif orig_target == 0x0022A5D8:
                ret = 0x11223344
            elif orig_target == 0x0022A5F8:
                ret = PTR_ADDR
            uc.reg_write(arm.UC_ARM_REG_R0, ret)

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_BASE, end=STUB_BASE + 0x100)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, DST_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)
        finally:
            self.uc.hook_del(hook)

        return {
            "call_log": call_log,
            "dst_fields": struct.unpack("<26I", self.uc.mem_read(DST_ADDR + 0x22A8, 26 * 4)),
        }


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = patch_orig_code(raw_bin[off : off + FUNC_SIZE])
    src_text = SRC_CPP.read_text(encoding="utf-8")
    cand_code = build_candidate()
    print(f"{FUNC_NAME}: orig {len(orig_code)} B, cand {len(cand_code)} B")

    indices = list(range(26)) + [26, -1]
    for idx in indices:
        orig_res = Runner().run(orig_code, idx)
        cand_res = Runner().run(cand_code, idx)
        if orig_res != cand_res:
            print(f"FAIL [idx={idx}]:")
            print("  orig:", orig_res)
            print("  cand:", cand_res)
            return 1
    print(f"PASS [all {len(indices)} indices: 0..25, 26, -1]")

    mutants = [
        ("range_bound", "idx >= 0x1Au", "idx >= 0x19u"),
        ("deref_mask_3", "(1u << 3)", "(1u << 2)"),
        ("deref_mask_25", "(1u << 25)", "(1u << 24)"),
        ("dst_base", "+ 0x22A8u", "+ 0x22ACu"),
        ("self_10", "void* const obj = *reinterpret_cast<void* const*>(self + 0x10);", "void* const obj = *reinterpret_cast<void* const*>(self + 0x14);"),
    ]
    for name, old, new in mutants:
        assert old in src_text, f"Mutant target not found: {old}"
        m_code = build_candidate(src_text.replace(old, new, 1))
        detected = False
        for idx in indices:
            orig_res = Runner().run(orig_code, idx)
            try:
                bad_res = Runner().run(m_code, idx)
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

    print(f"ALL PASS: {len(indices)} cases + {len(mutants)} negative controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
