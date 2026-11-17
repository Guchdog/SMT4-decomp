#!/usr/bin/env python3
"""Differential test for engine_func_001197c4 (0x001197C4) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts engine_func_001197c4,
resolves its 7 callees and global audio manager (0x004E3154), and compares
the pinned original against the compiled candidate across inactive, fade-in,
fade-out, stop/pause/unlink, and mutant negative controls.
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
FUNC_ADDR = 0x001197C4
FUNC_SIZE = 772
FUNC_NAME = "engine_func_001197c4"

STUB_BASE = 0x00110000
MGR_PAGE = 0x004E3000
MGR_ADDR = 0x004E3154

MEM_BASE = 0x20000000
MEM_SIZE = 0x00020000
NODE0_ADDR = 0x20000000
NODE1_ADDR = 0x20000100
SND0_ADDR = 0x20001000
SND1_ADDR = 0x20001100
EXTRA0_ADDR = 0x20002000
STACK_TOP = 0x2001F000
TRAP_ADDR = 0x001F0000

CALLEES = {
    0x001328F8: ("func_001328f8", 1),
    0x00147288: ("engine_func_00147288", 1),
    0x0015A3F4: ("func_0015a3f4", 2),
    0x002BD620: ("func_002bd620", 1),
    0x002C3A24: ("engine_func_002c3a24", 1),
    0x002C3AA8: ("engine_func_002c3aa8", 1),
    0x002C4360: ("engine_func_002c4360", 1),
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
    out_dir = ROOT / "build" / "test_leaf_001197c4"
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
        self.uc.mem_map(MGR_PAGE, 0x1000)
        self.uc.mem_map(MEM_BASE, MEM_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))

        for stub_addr in STUB_ADDRS.values():
            self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)
        self.uc.mem_write(MGR_PAGE, b"\x00" * 0x1000)

        nodes = case.get("nodes", [])
        mgr = bytearray(0x20)
        struct.pack_into("<Ii", mgr, 0, NODE0_ADDR if nodes else 0, len(nodes))
        mgr[0x15] = case.get("active", 1)
        mgr[0x16] = case.get("tick_flag", 1)
        self.uc.mem_write(MGR_ADDR, bytes(mgr))

        node_addrs = [NODE0_ADDR, NODE1_ADDR]
        snd_addrs = [SND0_ADDR, SND1_ADDR]
        playing_map = {}
        for idx, nd in enumerate(nodes):
            na = node_addrs[idx]
            sa = snd_addrs[idx]
            nxt = node_addrs[idx + 1] if idx + 1 < len(nodes) else 0
            prv = node_addrs[idx - 1] if idx > 0 else 0
            playing_map[sa] = nd.get("playing", 1)

            nb = bytearray(0xA0)
            struct.pack_into("<I", nb, 0x38, sa)
            struct.pack_into("<I", nb, 0x6C, nd.get("extra", 0))
            struct.pack_into("<II", nb, 0x70, nxt, prv)
            struct.pack_into("<i", nb, 0x78, nd.get("dur", 10))
            struct.pack_into("<i", nb, 0x84, nd.get("cur", 0))
            struct.pack_into("<i", nb, 0x8C, nd.get("stop_mode", 0))
            struct.pack_into("<I", nb, 0x90, nd.get("flags", 0x40))
            struct.pack_into("<f", nb, 0x94, nd.get("vol", 1.0))
            self.uc.mem_write(na, bytes(nb))

            sb = bytearray(0x10)
            sb[4] = nd.get("snd_state", 0)
            self.uc.mem_write(sa, bytes(sb))

        call_log: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr not in ADDR_BY_STUB:
                return
            orig_target = ADDR_BY_STUB[addr]
            cname, arity = CALLEES[orig_target]
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)

            if orig_target == 0x00147288:
                s0 = round(struct.unpack("<f", struct.pack("<I", uc.reg_read(arm.UC_ARM_REG_S0)))[0], 5)
                call_log.append((cname, r0, s0))
            else:
                call_log.append((cname, *(r0, r1)[:arity]))

            ret = 0
            if orig_target == 0x001328F8:
                ret = playing_map.get(r0, 0)
            uc.reg_write(arm.UC_ARM_REG_R0, ret)

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_BASE, end=STUB_BASE + 0x100)
        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)
        finally:
            self.uc.hook_del(hook)

        return {
            "call_log": call_log,
            "mgr": bytes(self.uc.mem_read(MGR_ADDR, 0x20)),
            "node0": bytes(self.uc.mem_read(NODE0_ADDR, 0xA0)),
            "node1": bytes(self.uc.mem_read(NODE1_ADDR, 0xA0)),
        }


def make_cases() -> list[dict]:
    return [
        {"name": "inactive_unlocks_and_exits", "active": 0, "tick_flag": 1, "nodes": []},
        {
            "name": "playing_fade_in_mid_and_done",
            "active": 1,
            "tick_flag": 1,
            "nodes": [
                {"playing": 1, "flags": 0x42 | 0x20, "dur": 10, "cur": 4, "vol": 0.8},
                {"playing": 1, "flags": 0x42 | 0x20, "dur": 10, "cur": 12, "vol": 0.8},
            ],
        },
        {
            "name": "playing_fade_out_mid_and_stop_100",
            "active": 1,
            "tick_flag": 1,
            "nodes": [
                {"playing": 1, "flags": 0x42 | 0x10, "dur": 10, "cur": 3, "vol": 1.0},
                {"playing": 1, "flags": 0x42 | 0x10 | 0x100, "dur": 10, "cur": 11, "vol": 1.0},
            ],
        },
        {
            "name": "playing_fade_out_done_flag_80",
            "active": 1,
            "tick_flag": 1,
            "nodes": [
                {"playing": 1, "flags": 0x42 | 0x10 | 0x80, "dur": 5, "cur": 6, "vol": 1.0},
            ],
        },
        {
            "name": "stopped_unlink_first_of_two_and_pause_second",
            "active": 1,
            "tick_flag": 1,
            "nodes": [
                {"playing": 0, "flags": 0x42, "stop_mode": 0, "extra": EXTRA0_ADDR},
                {"playing": 0, "flags": 0x42, "stop_mode": 1},
            ],
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
            print("  orig log:", orig_res["call_log"])
            print("  cand log:", cand_res["call_log"])
            return 1
        print(f"PASS [{case['name']}]")

    mutants = [
        ("active_check", "mgr[0x15] == 0", "mgr[0x15] == 1"),
        ("fade_in_mask", "if ((flags & 0x20u) != 0) {", "if ((flags & 0x40u) != 0) {"),
        ("fade_out_100", "func_0015a3f4(snd, 1);", "func_0015a3f4(snd, 2);"),
        ("pause_flag_200", "(flags & ~2u) | 0x200u;", "(flags & ~2u) | 0x400u;"),
        ("clear_tick", "mgr[0x16] = 0;", "mgr[0x16] = 1;"),
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
