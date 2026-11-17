#!/usr/bin/env python3
"""Differential test for ui_func_0037c4e8 (0x0037C4E8) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts ui_func_0037c4e8,
resolves all 11 external callees plus virtual slot +0x40 and callback +0xC24,
and compares the pinned original against the compiled candidate across
failure guards, fmt==3 ADPCM coefs, fmt!=3, callback present/null, and mutants.
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
FUNC_ADDR = 0x0037C4E8
FUNC_SIZE = 800
FUNC_NAME = "ui_func_0037c4e8"

STUB_BASE = 0x00110000
STUB_VFN40 = STUB_BASE + 0x40
STUB_C24 = STUB_BASE + 0x44

MEM_BASE = 0x20000000
MEM_SIZE = 0x00020000
SELF_ADDR = 0x20000000
OUT_ADDR = 0x20002000
VOBJ_ADDR = 0x20003000
VTBL_ADDR = 0x20003100
S18_ADDR = 0x20003200
BASE4_ADDR = 0x20004000
STACK_TOP = 0x2001F000
TRAP_ADDR = 0x001F0000

CALLEES = {
    0x002C5FF4: ("engine_func_002c5ff4", 3),
    0x002C6C10: ("ui_func_002c6c10", 2),
    0x0037B370: ("func_0037b370", 1),
    0x0037BCC8: ("func_0037bcc8", 3),
    0x0037BF10: ("func_0037bf10", 1),
    0x003E68BC: ("func_003e68bc", 1),
    0x003E7014: ("func_003e7014", 1),
    0x003E7038: ("func_003e7038", 2),
    0x003E705C: ("func_003e705c", 1),
    0x003E7080: ("func_003e7080", 3),
    0x003E70A4: ("func_003e70a4", 4),
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
    out_dir = ROOT / "build" / "test_leaf_0037c4e8"
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

        for addr in list(STUB_ADDRS.values()) + [STUB_VFN40, STUB_C24]:
            self.uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)

        self_buf = bytearray(0xD00)
        struct.pack_into("<I", self_buf, 0x04, BASE4_ADDR)
        struct.pack_into("<I", self_buf, 0x10, 0x12345678)
        struct.pack_into("<I", self_buf, 0x14, VOBJ_ADDR)
        struct.pack_into("<I", self_buf, 0x18, S18_ADDR)
        struct.pack_into("<H", self_buf, 0x30, 0xBEEF)
        struct.pack_into("<I", self_buf, 0xC24, STUB_C24 if case.get("has_c24", False) else 0)
        struct.pack_into("<I", self_buf, 0xC28, 0xCAFEBABE)
        self.uc.mem_write(SELF_ADDR, bytes(self_buf))

        self.uc.mem_write(VOBJ_ADDR, struct.pack("<I", VTBL_ADDR))
        self.uc.mem_write(VTBL_ADDR + 0x40, struct.pack("<I", STUB_VFN40))
        self.uc.mem_write(S18_ADDR + 0x10, struct.pack("<I", 999))

        call_log: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc.reg_read(arm.UC_ARM_REG_R3)
            if addr == STUB_VFN40:
                call_log.append(("vfn40", r0, r1, r2))
                return
            if addr == STUB_C24:
                call_log.append(("c24", r1))
                ok = case.get("c24_ok", 1)
                if ok:
                    uc.mem_write(r0, struct.pack("<I", 0x77777777))
                uc.reg_write(arm.UC_ARM_REG_R0, ok)
                return
            if addr not in ADDR_BY_STUB:
                return
            orig_target = ADDR_BY_STUB[addr]
            cname, arity = CALLEES[orig_target]
            if orig_target == 0x002C5FF4:
                uc.mem_write(r0, bytes(uc.mem_read(r1, r2)))
                call_log.append((cname, r0, r2))
            elif orig_target in (0x003E7038, 0x003E7080, 0x003E70A4):
                call_log.append((cname, r0, r2 if arity >= 3 else 0))
            else:
                call_log.append((cname, *(r0, r1, r2, r3)[:arity]))

            ret = 0
            if orig_target == 0x0037BCC8:
                ret = case.get("bcc8_ok", 1)
            elif orig_target == 0x003E7038:
                ret = case.get("e7038_ok", 1)
                if ret:
                    hdr = bytearray(0x38)
                    hdr[0] = 5
                    hdr[1] = case.get("hdr1", 2)
                    struct.pack_into("<III", hdr, 4, 44100, 1000, 2000)
                    struct.pack_into("<IIII", hdr, 0x14, 16, 4, 8, 9)
                    struct.pack_into("<III", hdr, 0x20, 10, 20, 30)
                    struct.pack_into("<I", hdr, 0x34, 0x100)
                    uc.mem_write(r1, bytes(hdr))
            elif orig_target == 0x003E705C:
                ret = case.get("channels", 2)
            elif orig_target == 0x003E7014:
                ret = case.get("n_bands", 2)
            elif orig_target == 0x0037B370:
                ret = case.get("fmt", 3)
            elif orig_target == 0x003E7080:
                ret = case.get("e7080_ok", 1)
                if ret:
                    ch = bytes([1, 2, 3, 4, 2, 0xAA, 0xBB, 0])
                    uc.mem_write(r1, ch)
            elif orig_target == 0x003E70A4:
                ret = case.get("e70a4_ok", 1)
                if ret:
                    ca = bytes(range(32)) + struct.pack("<HHH", 11, 22, 33)
                    cb = struct.pack("<HHH", 44, 55, 66)
                    uc.mem_write(r1, ca)
                    uc.mem_write(r2, cb)
            elif orig_target == 0x003E68BC:
                ret = r0
            elif orig_target == 0x002C6C10:
                ret = (r0 + r1 - 1) // r1
            uc.reg_write(arm.UC_ARM_REG_R0, ret)

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_BASE, end=STUB_C24 + 4)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, OUT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)
        finally:
            self.uc.hook_del(hook)

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "call_log": call_log,
            "self_mid": bytes(self.uc.mem_read(SELF_ADDR + 0x38, 0x28)),
            "self_coefs": bytes(self.uc.mem_read(SELF_ADDR + 0xA90, 0x60)),
            "out": bytes(self.uc.mem_read(OUT_ADDR, 0x88)),
        }


def make_cases() -> list[dict]:
    return [
        {"name": "bcc8_fail", "bcc8_ok": 0},
        {"name": "e7038_fail", "e7038_ok": 0},
        {"name": "fmt3_2ch_2bands_c24_ok", "fmt": 3, "channels": 2, "n_bands": 5, "has_c24": True, "c24_ok": 1},
        {"name": "fmt1_2ch_0bands_no_c24", "fmt": 1, "channels": 2, "n_bands": 0, "hdr1": 0, "has_c24": False},
        {"name": "c24_fail_returns_0", "fmt": 1, "channels": 1, "n_bands": 1, "has_c24": True, "c24_ok": 0},
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
            for k in ("self_mid", "self_coefs", "out"):
                if orig_res[k] != cand_res[k]:
                    print(f"  diff in {k}:")
                    print(f"    orig: {orig_res[k].hex()}")
                    print(f"    cand: {cand_res[k].hex()}")
            return 1
        print(f"PASS [{case['name']}]")

    mutants = [
        ("bands_cap_4", "if (r7 > 4)", "if (r7 > 5)"),
        ("fmt_3_check", "if (fmt == 3)", "if (fmt == 4)"),
        ("slot_stride_44", "i * 44u + 0xA92u", "i * 48u + 0xA92u"),
        ("base_plus_8", "base + 8 +", "base + 12 +"),
        ("vfn_slot_40", "*reinterpret_cast<const u8* const*>(v_obj) + 0x40", "*reinterpret_cast<const u8* const*>(v_obj) + 0x44"),
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
