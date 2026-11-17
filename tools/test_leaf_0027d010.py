#!/usr/bin/env python3
"""Differential test for engine_func_0027d010 (0x0027D010) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts engine_func_0027d010,
resolves all 8 external callees (including Thumb ui_func_002be7fc) and the
"map/unit/u%03d.bam" literal, and compares the pinned original against the
compiled candidate across states 0, 1, 2, 0x63, default, and mutant controls.
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
FUNC_ADDR = 0x0027D010
FUNC_SIZE = 804
FUNC_NAME = "engine_func_0027d010"

STUB_BASE = 0x00110000
RODATA_BASE = 0x00120000
GLOBAL_PAGE = 0x00447000
G_ST_PTR = 0x00447A48

MEM_BASE = 0x20000000
MEM_SIZE = 0x00020000
ST_ADDR = 0x20000000
ENTRIES_ADDR = 0x20002000
STACK_TOP = 0x2001F000
TRAP_ADDR = 0x001F0000

THUMB_CALLEES = {0x002BE7FC}

CALLEES = {
    0x0024AF28: ("engine_func_0024af28", 1),
    0x0028549C: ("engine_func_0028549c", 2),
    0x0029A2D0: ("engine_func_0029a2d0", 2),
    0x002A06C8: ("engine_func_002a06c8", 2),
    0x002AE16C: ("engine_func_002ae16c", 1),
    0x002BE7FC: ("ui_func_002be7fc", 3),
    0x002C0BA8: ("script_vm_func_002c0ba8", 1),
    0x0030F728: ("engine_func_0030f728", 0),
}

STUB_ADDRS = {addr: STUB_BASE + idx * 4 for idx, addr in enumerate(sorted(CALLEES))}
ADDR_BY_STUB = {v: k for k, v in STUB_ADDRS.items()}
NAME_TO_STUB = {CALLEES[k][0]: v for k, v in STUB_ADDRS.items()}


def parse_rodata_str(obj_path: Path) -> bytes:
    elf = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", elf, 0x20)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", elf, 0x2E)
    sections = [struct.unpack_from("<10I", elf, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = sections[e_shstrndx][4]
    for sh in sections:
        n_off = shstr_off + sh[0]
        name = elf[n_off : elf.find(b"\x00", n_off)].decode("ascii", errors="replace")
        if name == ".rodata.str1.1":
            return elf[sh[4] : sh[4] + sh[5]]
    return b"map/unit/u%03d.bam\x00"


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
        elif rel.relocation_type == 2:
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into("<I", code, rel.offset, RODATA_BASE + addend)
        else:
            raise RuntimeError(f"Unsupported relocation type {rel.relocation_type} for {rel.symbol_name}")
    return code


def build_candidate(src_text: str | None = None) -> tuple[bytearray, bytes]:
    out_dir = ROOT / "build" / "test_leaf_0027d010"
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
    rodata = parse_rodata_str(obj_path)
    return patch_cand_code(raw, relocs), rodata


class Runner:
    def __init__(self, rodata: bytes = b"") -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        self.uc.mem_map(STUB_BASE, 0x1000)
        self.uc.mem_map(RODATA_BASE, 0x10000)
        self.uc.mem_map(FUNC_ADDR & ~0xFFF, 0x2000)
        self.uc.mem_map(GLOBAL_PAGE, 0x1000)
        self.uc.mem_map(MEM_BASE, MEM_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))
        if rodata:
            self.uc.mem_write(RODATA_BASE, rodata)

        for orig_addr, stub_addr in STUB_ADDRS.items():
            if orig_addr in THUMB_CALLEES:
                self.uc.mem_write(stub_addr, struct.pack("<HH", 0x4770, 0))
            else:
                self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)
        self.uc.mem_write(G_ST_PTR, struct.pack("<I", ST_ADDR))

        st = bytearray(0x500)
        struct.pack_into("<hhhh", st, 6, case.get("f6", 1), case.get("f8", 2), case["state"], case.get("idx_c", 0))
        struct.pack_into("<h", st, 0x0E, case.get("slot_e", 0))
        st[0x14] = case.get("b14", 0)
        struct.pack_into("<I", st, 0x18, case.get("base_slot", 0))
        struct.pack_into("<I", st, 0x1C + case.get("base_slot", 0) * 40 + 0x18, 0x30001000)
        for s_idx in case.get("used_slots", ()):
            st[0x1C + s_idx * 40] = 1
        if "slot_16" in case:
            struct.pack_into("<H", st, 0x1C + case.get("slot_e", 0) * 40 + 0x16, case["slot_16"])
            struct.pack_into("<I", st, 0x1C + case.get("slot_e", 0) * 40 + 0x18, 0x30002000)
            st[0x1C + case.get("slot_e", 0) * 40 + 0x24] = case.get("slot_24", 0)
        self.uc.mem_write(ST_ADDR, bytes(st))

        entries = bytearray(0x200)
        for idx, ent in enumerate(case.get("entries", [])):
            struct.pack_into("<bbhhhhhhh", entries, idx * 16, ent["f0"], ent["f1"], ent["uid"], ent["x"], ent["y"], ent["w"], ent["h"], ent["fc"], ent["fe"])
        self.uc.mem_write(ENTRIES_ADDR, bytes(entries))

        call_log: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr not in ADDR_BY_STUB:
                return
            orig_target = ADDR_BY_STUB[addr]
            cname, arity = CALLEES[orig_target]
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc.reg_read(arm.UC_ARM_REG_R2)

            if orig_target == 0x002BE7FC:
                fmt = bytes(uc.mem_read(r1, 32)).split(b"\x00", 1)[0]
                uc.mem_write(r0, fmt + b"\x00")
                call_log.append((cname, fmt, r2))
            elif orig_target == 0x0029A2D0:
                path = bytes(uc.mem_read(r0, 32)).split(b"\x00", 1)[0]
                call_log.append((cname, path, r1))
            else:
                call_log.append((cname, *(r0, r1, r2)[:arity]))

            ret = 0
            if orig_target == 0x0030F728:
                ret = len(case.get("entries", []))
            elif orig_target == 0x0024AF28:
                ret = ENTRIES_ADDR + r0 * 16
            elif orig_target == 0x002C0BA8:
                ret = 1 if r0 in case.get("flags_on", ()) else 0
            elif orig_target == 0x0029A2D0:
                ret = 0x31000000
            elif orig_target == 0x0028549C:
                ret = 0x32000000
            elif orig_target == 0x002AE16C:
                ret = case.get("mdl_ready", 1)
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
            "st": bytes(self.uc.mem_read(ST_ADDR, 0x100)),
        }


def make_ent(f0=1, f1=2, uid=5, fc=0, fe=0):
    return {"f0": f0, "f1": f1, "uid": uid, "x": 10, "y": 20, "w": 30, "h": 40, "fc": fc, "fe": fe}


def make_cases() -> list[dict]:
    return [
        {"name": "state_0_empty", "state": 0, "entries": []},
        {"name": "state_0_match_second_after_flag_skip", "state": 0, "used_slots": (0,), "flags_on": (11,), "entries": [make_ent(-1, 2), make_ent(1, 2, fc=10), make_ent(1, 2, fc=11, fe=11), make_ent(1, 2, fc=11, fe=0)]},
        {"name": "state_0x63_returns_1", "state": 0x63},
        {"name": "state_default_returns_0", "state": 5},
        {"name": "state_1_uid7_loads_kind7", "state": 1, "slot_e": 1, "entries": [make_ent(uid=7)]},
        {"name": "state_1_uid14_b14_0_loads_kind38", "state": 1, "slot_e": 1, "b14": 0, "entries": [make_ent(uid=0x0E)]},
        {"name": "state_1_uid14_b14_1_falls_into_2", "state": 1, "slot_e": 1, "b14": 1, "base_slot": 0, "entries": [make_ent(uid=0x0E, fc=3, fe=4)]},
        {"name": "state_2_not_ready_returns_0", "state": 2, "slot_e": 1, "slot_16": 5, "slot_24": 0, "mdl_ready": 0, "entries": [make_ent(uid=5)]},
    ]


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = patch_orig_code(raw_bin[off : off + FUNC_SIZE])
    src_text = SRC_CPP.read_text(encoding="utf-8")
    cand_code, rodata = build_candidate()
    print(f"{FUNC_NAME}: orig {len(orig_code)} B, cand {len(cand_code)} B")

    cases = make_cases()
    for case in cases:
        orig_res = Runner().run(orig_code, case)
        cand_res = Runner(rodata).run(cand_code, case)
        if orig_res != cand_res:
            print(f"FAIL [{case['name']}]:")
            print("  orig ret/log:", orig_res["ret"], orig_res["call_log"])
            print("  cand ret/log:", cand_res["ret"], cand_res["call_log"])
            return 1
        print(f"PASS [{case['name']}]")

    mutants = [
        ("path_fmt", '"map/unit/u%03d.bam"', '"map/unit/x%03d.bam"'),
        ("uid_14", "unit_id == 0x0E", "unit_id == 0x0F"),
        ("kind_38", "engine_func_0029a2d0(path, 0x38u)", "engine_func_0029a2d0(path, 0x39u)"),
        ("slot_stride_40", "slot_idx * 40 + 0x1C", "slot_idx * 44 + 0x1C"),
        ("bias_2000", "+ 0x2000", "+ 0x2004"),
    ]
    for name, old, new in mutants:
        assert old in src_text, f"Mutant target not found: {old}"
        m_code, m_rodata = build_candidate(src_text.replace(old, new, 1))
        detected = False
        for case in cases:
            orig_res = Runner().run(orig_code, case)
            try:
                bad_res = Runner(m_rodata).run(m_code, case)
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
