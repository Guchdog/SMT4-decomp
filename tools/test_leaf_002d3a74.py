#!/usr/bin/env python3
"""Differential test for script_vm_func_002d3a74 (0x002D3A74) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts script_vm_func_002d3a74,
resolves its 7 callees and global pointers (0x00447A60, 0x0049FC0C), and
compares the pinned original against the compiled candidate across all state
machine cases (0, 1, 2, 0x63, default) plus mutant negative controls.
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
FUNC_ADDR = 0x002D3A74
FUNC_SIZE = 760
FUNC_NAME = "script_vm_func_002d3a74"

STUB_BASE = 0x00110000
GLOBAL_447000 = 0x00447000
GLOBAL_49F000 = 0x0049F000
G_STATE_PTR = 0x00447A60
G_PAIR_ADDR = 0x0049FC0C

MEM_BASE = 0x20000000
MEM_SIZE = 0x00020000
STATE_ADDR = 0x20000000
ENTRIES_ADDR = 0x20004000
STACK_TOP = 0x2001F000
TRAP_ADDR = 0x001F0000

CALLEES = {
    0x0024AEF0: ("script_vm_func_0024aef0", 0),
    0x0025BE50: ("engine_func_0025be50", 3),
    0x00275818: ("script_vm_func_00275818", 0),
    0x0028549C: ("engine_func_0028549c", 2),
    0x002A06C8: ("engine_func_002a06c8", 2),
    0x002DF760: ("script_vm_func_002df760", 1),
    0x002E0078: ("camp_func_002e0078", 1),
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
    out_dir = ROOT / "build" / "test_leaf_002d3a74"
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
        self.uc.mem_map(GLOBAL_447000, 0x1000)
        self.uc.mem_map(GLOBAL_49F000, 0x1000)
        self.uc.mem_map(MEM_BASE, MEM_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))

        for stub_addr in STUB_ADDRS.values():
            self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)
        self.uc.mem_write(G_STATE_PTR, struct.pack("<I", STATE_ADDR))
        self.uc.mem_write(G_PAIR_ADDR, struct.pack("<II", 0x11223344, 0x55667788))

        st = bytearray(0x600)
        struct.pack_into("<hhhh", st, 4, case.get("f4", 1), case.get("f6", 2), case["state"], case.get("idx_a", 0))
        struct.pack_into("<I", st, 0x18 + case.get("idx_a", 0) * 8, 0x30000000)
        for s_idx in case.get("used_slots", ()):
            st[0x24 + s_idx * 60] = 1
        self.uc.mem_write(STATE_ADDR, bytes(st))

        entries = bytearray(0x1000)
        for idx, ent in enumerate(case.get("entries", [])):
            struct.pack_into("<hhhhhh", entries, idx * 16, ent["f0"], ent["f2"], ent["x"], ent["y"], ent["w"], ent["h"])
        self.uc.mem_write(ENTRIES_ADDR, bytes(entries))

        call_log: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr not in ADDR_BY_STUB:
                return
            orig_target = ADDR_BY_STUB[addr]
            cname, arity = CALLEES[orig_target]
            regs = [uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4)]
            call_log.append((cname, *regs[:arity]))

            ret = 0
            if orig_target == 0x0024AEF0:
                ret = len(case.get("entries", []))
            elif orig_target == 0x002E0078:
                ret = ENTRIES_ADDR + regs[0] * 16
            elif orig_target == 0x002DF760:
                ret = 1 if regs[0] in case.get("blocked", ()) else 0
            elif orig_target == 0x0025BE50:
                ret = 0x31000000
            elif orig_target == 0x0028549C:
                ret = 0x32000000 + len(call_log)
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
            "state_mem": bytes(self.uc.mem_read(STATE_ADDR, 0x450)),
        }


def make_ent(f0=1, f2=2, x=10, y=20, w=30, h=40):
    return {"f0": f0, "f2": f2, "x": x, "y": y, "w": w, "h": h}


def make_cases() -> list[dict]:
    return [
        {"name": "state_0_empty", "state": 0, "entries": []},
        {"name": "state_0_one_match", "state": 0, "entries": [make_ent(-1, 2), make_ent(1, 3), make_ent(1, 2)]},
        {
            "name": "state_0_two_matches_one_blocked",
            "state": 0,
            "blocked": (1,),
            "entries": [make_ent(1, 2), make_ent(1, 2), make_ent(1, 2)],
        },
        {"name": "state_0x63_returns_1", "state": 0x63},
        {"name": "state_default_returns_0", "state": 5},
        {
            "name": "state_1_falls_into_2_two_matches",
            "state": 1,
            "idx_a": 1,
            "used_slots": (0,),
            "entries": [make_ent(1, 2, 1, 2, 3, 4), make_ent(1, 2, 5, 6, 7, 8)],
        },
        {
            "name": "state_2_empty",
            "state": 2,
            "idx_a": 0,
            "entries": [],
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
            print("  orig ret/log:", orig_res["ret"], orig_res["call_log"])
            print("  cand ret/log:", cand_res["ret"], cand_res["call_log"])
            return 1
        print(f"PASS [{case['name']}]")

    mutants = [
        ("state0_done_val", "*reinterpret_cast<s16*>(g_state + 0x08) = 0x63;", "*reinterpret_cast<s16*>(g_state + 0x08) = 0x64;"),
        ("model_size", "0x1C0u", "0x1C4u"),
        ("slot_stride", "slot_idx * 60 + 0x24", "slot_idx * 64 + 0x24"),
        ("slot_bias_1500", "i + 0x1500", "i + 0x1501"),
        ("state2_ret", "return 1;  // state2", "return 0;  // state2"),
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
