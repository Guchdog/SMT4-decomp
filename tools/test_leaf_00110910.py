#!/usr/bin/env python3
"""Differential test for engine_func_00110910 (0x00110910) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts engine_func_00110910,
resolves all 8 external callees (including Thumb vector ctor/dtor helpers),
and compares the pinned original against the compiled candidate across
item loops, 3 intrusive bucket-sort passes (usat [0..127]), and mutants.
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
FUNC_ADDR = 0x00110910
FUNC_SIZE = 796
FUNC_NAME = "engine_func_00110910"

STUB_BASE = 0x00120000
MEM_BASE = 0x20000000
MEM_SIZE = 0x00020000
SELF_ADDR = 0x20000000
ITEMS_ADDR = 0x20001000
NODES_ADDR = 0x20002000
STACK_TOP = 0x2001F000
TRAP_ADDR = 0x001F0000

THUMB_CALLEES = {0x002C5F58, 0x002C68BC}

CALLEES = {
    0x0012F36C: ("engine_func_0012f36c", 1),
    0x001407E8: ("func_001407e8", 0),
    0x002BB0B4: ("engine_func_002bb0b4", 2),
    0x002BB170: ("func_002bb170", 1),
    0x002BB218: ("engine_func_002bb218", 0),
    0x002BF774: ("engine_func_002bf774", 3),
    0x002C5F58: ("ui_func_002c5f58", 4),
    0x002C68BC: ("func_002c68bc", 4),
}

STUB_ADDRS = {addr: STUB_BASE + idx * 4 for idx, addr in enumerate(sorted(CALLEES))}
ADDR_BY_STUB = {v: k for k, v in STUB_ADDRS.items()}
NAME_TO_STUB = {CALLEES[k][0]: v for k, v in STUB_ADDRS.items()}


def encode_arm_branch(pc: int, target: int, link: bool, thumb: bool = False) -> int:
    if thumb:
        diff = target - (pc + 8)
        h_bit = (diff >> 1) & 1
        imm24 = (diff >> 2) & 0x00FFFFFF
        return 0xFA000000 | (h_bit << 24) | imm24
    imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if link else 0xEA000000
    return opcode | imm24


def patch_orig_code(raw: bytes) -> bytearray:
    code = bytearray(raw)
    for off in range(0, len(code), 4):
        insn = struct.unpack_from("<I", code, off)[0]
        cond = (insn >> 28) & 0xF
        op = (insn >> 24) & 0xF
        pc = FUNC_ADDR + off
        if cond == 0xF and (op & 0xE) == 0xA:
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            h_bit = (insn >> 24) & 1
            target = pc + 8 + (imm24 << 2) + (h_bit << 1)
            if target in STUB_ADDRS:
                struct.pack_into("<I", code, off, encode_arm_branch(pc, STUB_ADDRS[target], True, thumb=True))
        elif cond != 0xF and op in (0xA, 0xB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
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
            orig_addr = ADDR_BY_STUB[target]
            if orig_addr in THUMB_CALLEES and cond == 0xE and link:
                struct.pack_into("<I", code, rel.offset, encode_arm_branch(pc, target, True, thumb=True))
            else:
                imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
                struct.pack_into("<I", code, rel.offset, (cond << 28) | ((0xB if link else 0xA) << 24) | imm24)
        else:
            raise RuntimeError(f"Unsupported relocation type {rel.relocation_type} for {rel.symbol_name}")
    return code


def build_candidate(src_text: str | None = None) -> bytearray:
    out_dir = ROOT / "build" / "test_leaf_00110910"
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

        for orig_addr, stub_addr in STUB_ADDRS.items():
            if orig_addr in THUMB_CALLEES:
                self.uc.mem_write(stub_addr, struct.pack("<HH", 0x4770, 0))
            else:
                self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)

        self_buf = bytearray(0x100)
        struct.pack_into("<II", self_buf, 0x20, case.get("n_items", 0), ITEMS_ADDR)
        lists = case.get("lists", [[], [], []])
        node_cursor = NODES_ADDR
        list_queues: dict[int, list[int]] = {}
        for l_idx, keys in enumerate(lists):
            base_off = 0x28 + l_idx * 0x20
            list_addr = SELF_ADDR + base_off + 8
            q: list[int] = []
            for k_val in keys:
                na = node_cursor
                node_cursor += 0x100
                nb = bytearray(0x100)
                struct.pack_into("<i", nb, 0x50, k_val)
                nb[0x98] = 0
                self.uc.mem_write(na, bytes(nb))
                q.append(na + 0xD4)
            list_queues[list_addr] = q
            struct.pack_into("<II", self_buf, base_off + 8, len(q), q[0] if q else 0)
        self.uc.mem_write(SELF_ADDR, bytes(self_buf))

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

            if orig_target == 0x002C5F58:
                uc.mem_write(r0, b"\x00" * (r2 * r3))
                call_log.append((cname, r2, r3))
            elif orig_target == 0x002C68BC:
                call_log.append((cname, r2, r3))
            elif orig_target == 0x002BB170:
                q = list_queues[r0]
                q.pop(0)
                uc.mem_write(r0, struct.pack("<II", len(q), q[0] if q else 0))
            elif orig_target == 0x002BF774:
                q = list_queues.setdefault(r0, [])
                q.append(r2)
                uc.mem_write(r0, struct.pack("<II", len(q), q[0]))
            elif orig_target == 0x002BB218:
                call_log.append((cname,))
                uc.reg_write(arm.UC_ARM_REG_R0, 0x30001234)
            else:
                call_log.append((cname, *(r0, r1, r2, r3)[:arity]))

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
            "sorted": [list_queues[SELF_ADDR + 0x30 + i * 0x20] for i in range(3)],
        }


def make_cases() -> list[dict]:
    return [
        {"name": "empty_all", "n_items": 0, "lists": [[], [], []]},
        {"name": "items_3_single_node_lists", "n_items": 3, "lists": [[5], [10], [20]]},
        {
            "name": "all_three_lists_sorted_with_usat_bounds",
            "n_items": 2,
            "lists": [[200, 5, -5, 10], [50, 3], [127, 0, 64]],
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
        ("item_stride", "* 72u", "* 76u"),
        ("usat_max", "raw > 127", "raw > 63"),
        ("usat_min", "raw < 0", "raw < 10"),
        ("list_thresh", "list_base + 8) < 2", "list_base + 8) < 3"),
        ("tail_arg1", "engine_func_002bb0b4(ret_obj, 0);", "engine_func_002bb0b4(ret_obj, 1);"),
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
