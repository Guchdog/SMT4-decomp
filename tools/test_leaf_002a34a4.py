#!/usr/bin/env python3
"""Differential test for engine_func_002a34a4 (0x002A34A4) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts engine_func_002a34a4,
resolves its 4 callees and 2 global pointers (0x00464AF0, 0x00464B70), and
compares the pinned original against the compiled candidate across flag!=0,
flag==0, linked-list traversal, table slot search, and mutant controls.
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
FUNC_ADDR = 0x002A34A4
FUNC_SIZE = 740
FUNC_NAME = "engine_func_002a34a4"

STUB_BASE = 0x00110000
GLOBAL_PAGE = 0x00464000
GLOBAL_4AF0 = 0x00464AF0
GLOBAL_4B70 = 0x00464B70

MEM_BASE = 0x20000000
MEM_SIZE = 0x00030000
SELF_ADDR = 0x20000000
OBJ_ADDR = 0x20001000
ELEM_ADDR = 0x20002000
ARR_ADDR = 0x20003000
NODE_ADDR = 0x20004000
CUR_ADDR = 0x20005000
CUR2_ADDR = 0x20005400
ITEM_ADDR = 0x20006000
PAIR1_ADDR = 0x20007000
TBL_ADDR = 0x20008000
STACK_TOP = 0x2002F000
TRAP_ADDR = 0x001F0000

CALLEES = {
    0x002A2DB4: ("func_002a2db4", 2),
    0x002A2DDC: ("camp_func_002a2ddc", 2),
    0x002C2BE8: ("engine_func_002c2be8", 1),
    0x002C3568: ("script_vm_func_002c3568", 1),
}

STUB_ADDRS = {addr: STUB_BASE + idx * 4 for idx, addr in enumerate(sorted(CALLEES))}
ADDR_BY_STUB = {v: k for k, v in STUB_ADDRS.items()}
NAME_TO_STUB = {CALLEES[k][0]: v for k, v in STUB_ADDRS.items()}


def f32_bits(val: float) -> int:
    return struct.unpack("<I", struct.pack("<f", val))[0]


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
    out_dir = ROOT / "build" / "test_leaf_002a34a4"
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

        for stub_addr in STUB_ADDRS.values():
            self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)
        self.uc.mem_write(GLOBAL_PAGE, b"\x00" * 0x2000)

        # Globals
        self.uc.mem_write(GLOBAL_4AF0 + 5, bytes([case.get("global_flag5", 0)]))
        self.uc.mem_write(GLOBAL_4B70, struct.pack("<I", case.get("global_key", 0xCAFEBABE)))

        # self
        self_buf = bytearray(0x40)
        struct.pack_into("<I", self_buf, 0x08, OBJ_ADDR)
        arr_count = case.get("arr_count", 0)
        struct.pack_into("<II", self_buf, 0x10, ARR_ADDR, ARR_ADDR + arr_count * 4)
        struct.pack_into("<i", self_buf, 0x24, case.get("v24", 0))
        self.uc.mem_write(SELF_ADDR, bytes(self_buf))

        # arr[0] = ELEM_ADDR
        self.uc.mem_write(ARR_ADDR, struct.pack("<I", ELEM_ADDR))

        # obj
        obj_buf = bytearray(0x400)
        struct.pack_into("<i", obj_buf, 0x274, NODE_ADDR - (OBJ_ADDR + 0x274))
        struct.pack_into("<i", obj_buf, 0x288, TBL_ADDR - (OBJ_ADDR + 0x288))
        self.uc.mem_write(OBJ_ADDR, bytes(obj_buf))

        # node -> cur -> cur2
        node_buf = bytearray(0x40)
        struct.pack_into("<i", node_buf, 0x08, CUR_ADDR - (NODE_ADDR + 0x08))
        struct.pack_into("<i", node_buf, 0x0C, ITEM_ADDR - (NODE_ADDR + 0x0C))
        self.uc.mem_write(NODE_ADDR, bytes(node_buf))

        cur_buf = bytearray(0x40)
        if case.get("follow_chain", False):
            struct.pack_into("<I", cur_buf, 0x00, 0x20000004)
            struct.pack_into("<i", cur_buf, 0x1C, CUR2_ADDR - (CUR_ADDR + 0x1C))
        else:
            struct.pack_into("<I", cur_buf, 0x00, 0x10000001)
        self.uc.mem_write(CUR_ADDR, bytes(cur_buf))

        cur2_buf = bytearray(0x40)
        struct.pack_into("<I", cur2_buf, 0x00, 0x30000002)
        self.uc.mem_write(CUR2_ADDR, bytes(cur2_buf))

        # item
        item_buf = bytearray(0x40)
        struct.pack_into("<I", item_buf, 0x00, case.get("item_hdr", 0x80000001))
        self.uc.mem_write(ITEM_ADDR, bytes(item_buf))

        # tbl entries (indices 0..5, each 28 bytes at +0x2C)
        tbl_buf = bytearray(0x200)
        for idx, (w4, w10) in enumerate(case.get("tbl_slots", [(0xF, 0)] * 6)):
            off = 0x2C + idx * 28
            struct.pack_into("<I", tbl_buf, off + 0x04, w4)
            struct.pack_into("<I", tbl_buf, off + 0x10, w10)
        self.uc.mem_write(TBL_ADDR, bytes(tbl_buf))

        call_log: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr not in ADDR_BY_STUB:
                return
            orig_target = ADDR_BY_STUB[addr]
            cname, arity = CALLEES[orig_target]
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)

            if orig_target == 0x002C2BE8:
                floats = struct.unpack("<4f", uc.mem_read(r0, 16))
                call_log.append((cname, tuple(round(x, 6) for x in floats)))
                uc.reg_write(arm.UC_ARM_REG_R0, 0xAABBCC00 + len(call_log))
            elif orig_target == 0x002C3568:
                val = struct.unpack("<I", uc.mem_read(r0, 4))[0]
                call_log.append((cname, val))
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            elif orig_target == 0x002A2DDC:
                call_log.append((cname, r1))
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            elif orig_target == 0x002A2DB4:
                ptr = struct.unpack("<I", uc.mem_read(r1, 4))[0]
                call_log.append((cname, ptr))
                uc.mem_write(r0, struct.pack("<II", 0, PAIR1_ADDR))
                uc.reg_write(arm.UC_ARM_REG_R0, 0)

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_BASE, end=STUB_BASE + 0x100)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["flag"])
        self.uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(case["val"]))
        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)
        finally:
            self.uc.hook_del(hook)

        return {
            "call_log": call_log,
            "obj": bytes(self.uc.mem_read(OBJ_ADDR, 0x300)),
            "elem": bytes(self.uc.mem_read(ELEM_ADDR, 0x300)),
            "item": bytes(self.uc.mem_read(ITEM_ADDR, 0x40)),
            "pair1": bytes(self.uc.mem_read(PAIR1_ADDR, 0x20)),
            "tbl": bytes(self.uc.mem_read(TBL_ADDR, 0x100)),
        }


def make_cases() -> list[dict]:
    return [
        {
            "name": "flag1_count0_uses_obj",
            "flag": 1,
            "val": 0.25,
            "arr_count": 0,
            "v24": 1,
        },
        {
            "name": "flag1_count1_v24_pos_uses_elem",
            "flag": 1,
            "val": 0.75,
            "arr_count": 1,
            "v24": 2,
        },
        {
            "name": "flag0_follow_chain_flag5_on_slot2",
            "flag": 0,
            "val": 0.5,
            "follow_chain": True,
            "global_flag5": 1,
            "global_key": 0x12345678,
            "item_hdr": 0x80000001,
            "tbl_slots": [(0xF, 0), (0xF, 0), (0x3, 0), (0xF, 0), (0xF, 0), (0xF, 0)],
            "arr_count": 1,
            "v24": 1,
        },
        {
            "name": "flag0_no_chain_flag5_off_all_empty",
            "flag": 0,
            "val": 0.125,
            "follow_chain": False,
            "global_flag5": 0,
            "global_key": 0xDEADBEEF,
            "item_hdr": 0x80000001,
            "tbl_slots": [(0xF, 0)] * 6,
            "arr_count": 0,
            "v24": 0,
        },
        {
            "name": "flag0_slot4_skips_tbl_patch",
            "flag": 0,
            "val": 0.9,
            "follow_chain": False,
            "global_flag5": 0,
            "item_hdr": 0x80000001,
            "tbl_slots": [(0xF, 0), (0xF, 0), (0xF, 0), (0xF, 0), (0x1, 1), (0xF, 0)],
            "arr_count": 1,
            "v24": 1,
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
            for k in orig_res:
                if orig_res[k] != cand_res[k]:
                    print(f"  diff in {k}:")
                    print(f"    orig: {orig_res[k]}")
                    print(f"    cand: {cand_res[k]}")
            return 1
        print(f"PASS [{case['name']}]")

    mutants = [
        ("obj_174_val", "*reinterpret_cast<u32*>(obj + 0x174) = 2;", "*reinterpret_cast<u32*>(obj + 0x174) = 3;"),
        ("chain_magic", "== 0x20000004u", "== 0x20000005u"),
        ("pair_14_hi", "| 0x1000u", "| 0x2000u"),
        ("tbl_e1_4", "| 0xE3u", "| 0xE4u"),
        ("dst_d8_off", "dst + 0xD8", "dst + 0xDC"),
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
