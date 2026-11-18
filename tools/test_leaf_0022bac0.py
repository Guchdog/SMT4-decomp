#!/usr/bin/env python3
"""Differential test for func_0022bac0 (0x0022BAC0) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts func_0022bac0,
resolves func_0022c198 and the allocator vtable (+0, +4, +8), and compares
the pinned original against the compiled candidate across in-place insert,
overlap forward/backward, realloc success, fallback to new_size, and OOM.
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
FUNC_ADDR = 0x0022BAC0
FUNC_SIZE = 808
FUNC_NAME = "func_0022bac0"

STUB_BASE = 0x00110000
STUB_22C198 = STUB_BASE + 0x00
STUB_ALLOC0 = STUB_BASE + 0x04
STUB_FREE4 = STUB_BASE + 0x08
STUB_ALLOC8 = STUB_BASE + 0x0C

MEM_BASE = 0x20000000
MEM_SIZE = 0x00020000
SELF_ADDR = 0x20000000
ALLOC_ADDR = 0x20001000
VTBL_ADDR = 0x20001100
OLD_BUF_ADDR = 0x20002000
NEW_BUF_ADDR = 0x20003000
STACK_TOP = 0x2001F000
TRAP_ADDR = 0x001F0000


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
            if target == 0x0022C198:
                struct.pack_into("<I", code, off, encode_arm_branch(pc, STUB_22C198, link=(op == 0xB)))
    return code


def patch_cand_code(raw: bytes, relocs: list) -> bytearray:
    code = bytearray(raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29) and rel.symbol_name == "func_0022c198":
            insn = struct.unpack_from("<I", code, rel.offset)[0]
            cond = (insn >> 28) & 0xF
            op = (insn >> 24) & 0xF
            link = op == 0xB
            pc = FUNC_ADDR + rel.offset
            imm24 = ((STUB_22C198 - (pc + 8)) >> 2) & 0x00FFFFFF
            struct.pack_into("<I", code, rel.offset, (cond << 28) | ((0xB if link else 0xA) << 24) | imm24)
        else:
            raise RuntimeError(f"Unsupported relocation type {rel.relocation_type} for {rel.symbol_name}")
    return code


def build_candidate(src_text: str | None = None) -> bytearray:
    out_dir = ROOT / "build" / "test_leaf_0022bac0"
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

        for addr in (STUB_22C198, STUB_ALLOC0, STUB_FREE4, STUB_ALLOC8):
            self.uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)

        init_data = case["init_data"]
        self.uc.mem_write(OLD_BUF_ADDR, init_data)
        self.uc.mem_write(SELF_ADDR, struct.pack("<IIII", ALLOC_ADDR, OLD_BUF_ADDR, case["cap"], len(init_data)))
        self.uc.mem_write(ALLOC_ADDR, struct.pack("<I", VTBL_ADDR))
        self.uc.mem_write(VTBL_ADDR, struct.pack("<III", STUB_ALLOC0, STUB_FREE4, STUB_ALLOC8))

        call_log: list[tuple] = []
        alloc_seq = list(case.get("alloc_seq", [NEW_BUF_ADDR]))

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc.reg_read(arm.UC_ARM_REG_R2)
            if addr == STUB_22C198:
                call_log.append(("22c198", r0, r1))
                uc.reg_write(arm.UC_ARM_REG_R0, case.get("grow_cap", r1 * 2))
            elif addr == STUB_ALLOC0:
                call_log.append(("alloc0", r0, r1))
                uc.reg_write(arm.UC_ARM_REG_R0, alloc_seq.pop(0) if alloc_seq else 0)
            elif addr == STUB_FREE4:
                call_log.append(("free4", r0, r1))
            elif addr == STUB_ALLOC8:
                call_log.append(("alloc8", r0, r1, r2))
                uc.reg_write(arm.UC_ARM_REG_R0, alloc_seq.pop(0) if alloc_seq else 0)

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_BASE, end=STUB_BASE + 0x10)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["pos"])
        self.uc.reg_write(arm.UC_ARM_REG_R2, case["count"])
        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)
        finally:
            self.uc.hook_del(hook)

        alloc, buf_ptr, cap, sz = struct.unpack("<IIII", self.uc.mem_read(SELF_ADDR, 16))
        pos, count = case["pos"], case["count"]
        buf_bytes = bytes(self.uc.mem_read(buf_ptr, sz))
        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "call_log": call_log,
            "hdr": (alloc, buf_ptr, cap, sz),
            "prefix": buf_bytes[:pos],
            "suffix": buf_bytes[pos + count :],
        }


def make_cases() -> list[dict]:
    return [
        {"name": "inplace_middle_tail_gt_count", "init_data": b"ABCDEFGH", "cap": 11, "pos": 2, "count": 3},
        {"name": "inplace_middle_tail_lt_count", "init_data": b"ABCDEF", "cap": 16, "pos": 4, "count": 5},
        {"name": "inplace_zero_count", "init_data": b"ABCDEF", "cap": 16, "pos": 3, "count": 0},
        {"name": "realloc_grow_cap_ok", "init_data": b"ABCDEF", "cap": 6, "pos": 2, "count": 4, "grow_cap": 16, "alloc_seq": [NEW_BUF_ADDR]},
        {"name": "realloc_fallback_to_new_size", "init_data": b"ABCDEF", "cap": 6, "pos": 2, "count": 4, "grow_cap": 16, "alloc_seq": [0, 0, NEW_BUF_ADDR]},
        {"name": "realloc_oom_returns_0", "init_data": b"ABCDEF", "cap": 6, "pos": 2, "count": 4, "grow_cap": 16, "alloc_seq": [0, 0, 0, 0]},
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
        ("cap_check", "cap >= new_size", "cap > new_size"),
        ("vfn_alloc8", "0x0040FE40u", "0x0040FE44u"),
        ("free_slot", "*reinterpret_cast<const u8* const*>(alloc) + 4", "*reinterpret_cast<const u8* const*>(alloc) + 8"),
        ("oom_ret", "new_buf = try_alloc_0022bac0(alloc, new_size);\n        if (new_buf == nullptr) {\n            free_fn(alloc, nullptr);\n            return 0;", "new_buf = try_alloc_0022bac0(alloc, new_size);\n        if (new_buf == nullptr) {\n            free_fn(alloc, nullptr);\n            return 1;"),
        ("set_size", "*reinterpret_cast<u32*>(self + 0x0C) = new_size;", "*reinterpret_cast<u32*>(self + 0x0C) = new_size + 1;"),
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
