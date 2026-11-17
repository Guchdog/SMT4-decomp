#!/usr/bin/env python3
"""Differential test for engine_func_0021dac4 (0x0021DAC4) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts engine_func_0021dac4,
resolves its 6 external callees and "POLY" literal, and compares the pinned
original against the compiled candidate across flag!=0 and flag==0 paths,
including script_vm_func_0024f460 register + VFP + 15-word stack arguments.
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
FUNC_ADDR = 0x0021DAC4
FUNC_SIZE = 744
FUNC_NAME = "engine_func_0021dac4"

STUB_BASE = 0x00110000
RODATA_ADDR = 0x00120000
MGR_ADDR = 0x20000000
ENTRIES_ADDR = 0x20010000
MEM_BASE = 0x20000000
MEM_SIZE = 0x00030000
STACK_TOP = 0x2002F000
TRAP_ADDR = 0x001F0000

CALLEES = {
    0x0024F460: "script_vm_func_0024f460",
    0x0025687C: "camp_func_0025687c",
    0x002C0BA8: "script_vm_func_002c0ba8",
    0x002C0BCC: "engine_func_002c0bcc",
    0x002C2B1C: "engine_func_002c2b1c",
    0x00323730: "camp_func_00323730",
}

STUB_ADDRS = {addr: STUB_BASE + idx * 4 for idx, addr in enumerate(sorted(CALLEES))}
ADDR_BY_STUB = {v: k for k, v in STUB_ADDRS.items()}
NAME_TO_STUB = {CALLEES[k]: v for k, v in STUB_ADDRS.items()}


def parse_rodata_sections(obj_path: Path) -> bytes:
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
    return b"POLY\x00"


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
    rodata_seen = 0
    for rel in relocs:
        r_off = rel.offset
        r_type = rel.relocation_type
        s_name = rel.symbol_name
        if r_type in (28, 29):
            insn = struct.unpack_from("<I", code, r_off)[0]
            cond = (insn >> 28) & 0xF
            op = (insn >> 24) & 0xF
            link = op == 0xB
            target = NAME_TO_STUB[s_name]
            pc = FUNC_ADDR + r_off
            imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
            struct.pack_into("<I", code, r_off, (cond << 28) | ((0xB if link else 0xA) << 24) | imm24)
        elif r_type == 2:  # R_ARM_ABS32 for "POLY"
            addend = struct.unpack_from("<I", code, r_off)[0]
            struct.pack_into("<I", code, r_off, RODATA_ADDR + addend)
            rodata_seen += 1
        elif r_type == 47:  # R_ARM_MOVW_ABS_NC
            val = RODATA_ADDR & 0xFFFF
            insn = struct.unpack_from("<I", code, r_off)[0]
            insn = (insn & 0xFFF0F000) | ((val >> 12) << 16) | (val & 0xFFF)
            struct.pack_into("<I", code, r_off, insn)
        elif r_type == 48:  # R_ARM_MOVT_ABS
            val = (RODATA_ADDR >> 16) & 0xFFFF
            insn = struct.unpack_from("<I", code, r_off)[0]
            insn = (insn & 0xFFF0F000) | ((val >> 12) << 16) | (val & 0xFFF)
            struct.pack_into("<I", code, r_off, insn)
        else:
            raise RuntimeError(f"Unsupported relocation type {r_type} for {s_name} at +{r_off:#x}")
    return code


def build_candidate(src_text: str | None = None) -> tuple[bytearray, bytes]:
    out_dir = ROOT / "build" / "test_leaf_0021dac4"
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
    rodata = parse_rodata_sections(obj_path)
    return patch_cand_code(raw, relocs), rodata


class Runner:
    def __init__(self, rodata: bytes = b"POLY\x00") -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        self.uc.mem_map(STUB_BASE, 0x1000)
        self.uc.mem_map(RODATA_ADDR, 0x1000)
        self.uc.mem_map(FUNC_ADDR & ~0xFFF, 0x2000)
        self.uc.mem_map(MEM_BASE, MEM_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))
        self.uc.mem_write(RODATA_ADDR, rodata)

        for stub_addr in STUB_ADDRS.values():
            self.uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

    def run(self, code: bytearray, case: dict) -> dict:
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        self.uc.mem_write(MEM_BASE, b"\x00" * MEM_SIZE)

        # Populate manager
        mgr = bytearray(0x1000)
        mgr[0xDE3] = case.get("mgr_count", 0) & 0xFF
        for idx, (status, slot_id) in enumerate(case.get("mgr_slots", [])):
            mgr[0xDE4 + idx] = status & 0xFF
            mgr[0xDEC + idx] = slot_id & 0xFF
        self.uc.mem_write(MGR_ADDR, bytes(mgr))

        # Populate entries (32 bytes each)
        entries = bytearray(0x1000)
        for idx, ent in enumerate(case.get("entries", [])):
            off = idx * 32
            struct.pack_into("<bbhhhhhh", entries, off, ent["f0"], ent["f1"], ent["x"], ent["y"], ent["w"], ent["h"], ent["s10"], 0)
            struct.pack_into("<h", entries, off + 0x10, ent["s10"])
            entries[off + 0x12] = ent["b12"] & 0xFF
            entries[off + 0x13] = ent["b13"] & 0xFF
        self.uc.mem_write(ENTRIES_ADDR, bytes(entries))

        call_log: list[tuple] = []

        def on_code(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
            if addr not in ADDR_BY_STUB:
                return
            orig_target = ADDR_BY_STUB[addr]
            cname = CALLEES[orig_target]
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc.reg_read(arm.UC_ARM_REG_R3)

            if orig_target == 0x002C2B1C:
                call_log.append((cname,))
                uc.reg_write(arm.UC_ARM_REG_R0, MGR_ADDR)
            elif orig_target == 0x00323730:
                call_log.append((cname,))
                uc.reg_write(arm.UC_ARM_REG_R0, len(case.get("entries", [])))
            elif orig_target == 0x0025687C:
                call_log.append((cname, r0))
                uc.reg_write(arm.UC_ARM_REG_R0, ENTRIES_ADDR + r0 * 32)
            elif orig_target == 0x002C0BA8:
                call_log.append((cname, r0))
                uc.reg_write(arm.UC_ARM_REG_R0, case.get("flag_0ba8", 0))
            elif orig_target == 0x002C0BCC:
                call_log.append((cname, r0))
                uc.reg_write(arm.UC_ARM_REG_R0, case.get("rand_0bcc", 50))
            elif orig_target == 0x0024F460:
                tag = bytes(uc.mem_read(r2, 8)).split(b"\x00", 1)[0]
                s_regs = [
                    round(struct.unpack("<f", struct.pack("<I", uc.reg_read(getattr(arm, f"UC_ARM_REG_S{i}"))))[0], 4)
                    for i in range(6)
                ]
                sp = uc.reg_read(arm.UC_ARM_REG_SP)
                st = struct.unpack("<15I", uc.mem_read(sp, 60))
                call_log.append((cname, r0, r1, tag, r3, tuple(s_regs), st))
                uc.reg_write(arm.UC_ARM_REG_R0, 0)

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_BASE, end=STUB_BASE + 0x100)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case["arg0"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["arg1"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case["flag"])
        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)
        finally:
            self.uc.hook_del(hook)

        return {
            "call_log": call_log,
            "mgr_tail": bytes(self.uc.mem_read(MGR_ADDR + 0xDE0, 0x30)),
        }


def make_entry(f0, f1, x=10, y=20, w=30, h=40, s10=0, b12=0, b13=0):
    return {"f0": f0, "f1": f1, "x": x, "y": y, "w": w, "h": h, "s10": s10, "b12": b12, "b13": b13}


def make_cases() -> list[dict]:
    return [
        {
            "name": "flag1_count0_early_exit",
            "arg0": 1,
            "arg1": 2,
            "flag": 1,
            "mgr_count": 0,
        },
        {
            "name": "flag1_replays_status2_only",
            "arg0": 1,
            "arg1": 2,
            "flag": 1,
            "mgr_count": 3,
            "mgr_slots": [(1, 0), (2, 1), (0, 2)],
            "entries": [make_entry(1, 2, 1, 2, 3, 4), make_entry(1, 2, 11, 22, 33, 44, s10=7), make_entry(1, 2)],
        },
        {
            "name": "flag0_s10_zero_pass_b13",
            "arg0": 3,
            "arg1": 4,
            "flag": 0,
            "mgr_count": 1,
            "rand_0bcc": 40,
            "entries": [make_entry(3, 4, 5, 6, 7, 8, s10=0, b12=10, b13=40)],
        },
        {
            "name": "flag0_s10_nonzero_flag0ba8_1_pass_b13",
            "arg0": 3,
            "arg1": 4,
            "flag": 0,
            "mgr_count": 0,
            "flag_0ba8": 1,
            "rand_0bcc": 25,
            "entries": [
                make_entry(-1, 4),
                make_entry(3, 5),
                make_entry(3, 4, 15, 25, 35, 45, s10=12, b12=10, b13=30),
            ],
        },
        {
            "name": "flag0_s10_nonzero_flag0ba8_0_pass_b12",
            "arg0": 3,
            "arg1": 4,
            "flag": 0,
            "mgr_count": 2,
            "flag_0ba8": 0,
            "rand_0bcc": 25,
            "entries": [
                make_entry(3, 4, 100, 200, 300, 400, s10=99, b12=25, b13=0),
                make_entry(3, 4, 1, 2, 3, 4, s10=99, b12=24, b13=99),
            ],
        },
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
        orig_res = Runner(b"POLY\x00").run(orig_code, case)
        cand_res = Runner(rodata).run(cand_code, case)
        if orig_res != cand_res:
            print(f"FAIL [{case['name']}]:")
            print("  orig:", orig_res)
            print("  cand:", cand_res)
            return 1
        print(f"PASS [{case['name']}]")

    mutants = [
        ("poly_tag", '"POLY"', '"POLZ"'),
        ("poly_scale", "200.0f", "201.0f"),
        ("poly_char", "0x3Au", "0x3Bu"),
        ("mgr_status", "mgr[0xDE4 + cur_idx] = 2;", "mgr[0xDE4 + cur_idx] = 3;"),
        ("slot_bias", "static_cast<u32>(slot_id + 0x1300)", "static_cast<u32>(slot_id + 0x1301)"),
    ]
    for name, old, new in mutants:
        assert old in src_text, f"Mutant target not found: {old}"
        m_code, m_rodata = build_candidate(src_text.replace(old, new, 1))
        detected = False
        for case in cases:
            orig_res = Runner(b"POLY\x00").run(orig_code, case)
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
