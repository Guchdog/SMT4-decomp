#!/usr/bin/env python3
"""Differential test for camp_func_0018b39c (0x0018B39C) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the camp_func_0018b39c body,
resolves its direct calls (including BLX into Thumb 0x002BE7FC) and .rodata
string relocations, and runs the pinned original (extracted/exefs/code.bin)
against the candidate in separate Unicorn machines with identical fixtures.
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
SOURCE = ROOT / "src/engine/leaf_batch45_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_0018b39c"

FUNC_ADDR = 0x0018B39C
FUNC_SIZE = 708

CODE_ADDR = 0x00180000
CODE_SIZE = 0x00180000  # covers 0x0018B39C..0x002D0000
GLOBAL_ADDR = 0x00430000
GLOBAL_SIZE = 0x00020000  # covers 0x0043DC58 and 0x0044EA00
CAND_RODATA_ADDR = 0x00600000
CAND_RODATA_SIZE = 0x00010000
OBJ_ADDR = 0x00700000
OBJ_SIZE = 0x00001000
BASE_ADDR = 0x00710000
BASE_SIZE = 0x00002000
NODES_ADDR = 0x00720000
NODES_SIZE = 0x00001000
TBB_ADDR = 0x00730000
TBB_SIZE = 0x00001000
PAYLOAD_ADDR = 0x00740000
PAYLOAD_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_29F260 = 0x0029F260
STUB_29F248 = 0x0029F248
STUB_2BF558 = 0x002BF558
STUB_2BF6D0 = 0x002BF6D0
STUB_2C5FA4 = 0x002C5FA4
STUB_2BF460 = 0x002BF460
STUB_2C0BA8 = 0x002C0BA8
STUB_2C0EC4 = 0x002C0EC4
STUB_2C0E9C = 0x002C0E9C
STUB_2C0E4C = 0x002C0E4C
STUB_2BE7FC = 0x002BE7FC  # Thumb
STUB_2BE77C = 0x002BE77C
STUB_196EE0 = 0x00196EE0
STUB_CB = 0x002D0000

THUMB_STUBS = {STUB_2BE7FC}

STUB_NAMES = {
    STUB_29F260: "camp_func_0029f260",
    STUB_29F248: "camp_func_0029f248",
    STUB_2BF558: "func_002bf558",
    STUB_2BF6D0: "camp_func_002bf6d0",
    STUB_2C5FA4: "battle_func_002c5fa4",
    STUB_2BF460: "ui_func_002bf460",
    STUB_2C0BA8: "script_vm_func_002c0ba8",
    STUB_2C0EC4: "Tbb_GetGlobalSubTable",
    STUB_2C0E9C: "Tbb_GetPayloadData",
    STUB_2C0E4C: "Tbb_GetRowCount",
    STUB_2BE7FC: "ui_func_002be7fc",
    STUB_2BE77C: "ui_func_002be77c",
    STUB_196EE0: "camp_func_00196ee0",
    STUB_CB: "cb_stub",
}
SYMBOL_TO_ADDRESS = {name: address for address, name in STUB_NAMES.items()}

CALLEE_SAVED = {
    "r4": arm.UC_ARM_REG_R4,
    "r5": arm.UC_ARM_REG_R5,
    "r6": arm.UC_ARM_REG_R6,
    "r7": arm.UC_ARM_REG_R7,
    "r8": arm.UC_ARM_REG_R8,
    "r9": arm.UC_ARM_REG_R9,
    "r10": arm.UC_ARM_REG_R10,
    "r11": arm.UC_ARM_REG_R11,
}
CALLEE_SAVED_START = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}
S_REGS = (
    arm.UC_ARM_REG_S0,
    arm.UC_ARM_REG_S1,
    arm.UC_ARM_REG_S2,
    arm.UC_ARM_REG_S3,
    arm.UC_ARM_REG_S4,
)


def s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def read_cstr(uc: unicorn.Uc, addr: int, limit: int = 128) -> bytes:
    raw = bytes(uc.mem_read(addr, limit))
    end = raw.find(0)
    return raw[:end] if end != -1 else raw


def elf_sections_and_abs32_targets(path: Path, func_name: str) -> tuple[dict[str, bytes], dict[int, str]]:
    data = path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    e_shstrndx = struct.unpack_from("<H", data, 50)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    sec_names: list[str] = []
    result: dict[str, bytes] = {}
    for section in sections:
        end = shstrtab.find(b"\x00", section[0])
        name = shstrtab[section[0] : end].decode("ascii", errors="replace")
        sec_names.append(name)
        if section[1] != 8:
            result[name] = data[section[4] : section[4] + section[5]]

    symtab_sec = next(s for n, s in zip(sec_names, sections) if n == ".symtab")
    sym_data = data[symtab_sec[4] : symtab_sec[4] + symtab_sec[5]]
    syms = [struct.unpack_from("<IIIBBH", sym_data, i) for i in range(0, len(sym_data), 16)]

    strtab_data = result[".strtab"]
    func_shndx = None
    func_val = 0
    for st_name, st_val, _sz, _info, _other, st_shndx in syms:
        end = strtab_data.find(b"\x00", st_name)
        if strtab_data[st_name:end].decode("ascii", errors="replace") == func_name:
            func_shndx = st_shndx
            func_val = st_val
            break

    abs32_targets: dict[int, str] = {}
    for _name, sec in zip(sec_names, sections):
        if sec[1] == 9 and sec[7] == func_shndx:
            rel_data = data[sec[4] : sec[4] + sec[5]]
            for i in range(0, len(rel_data), 8):
                r_offset, r_info = struct.unpack_from("<II", rel_data, i)
                if (r_info & 0xFF) == 2:
                    sym_idx = r_info >> 8
                    target_shndx = syms[sym_idx][5]
                    abs32_targets[r_offset - func_val] = sec_names[target_shndx]
    return result, abs32_targets


def relocate_candidate(obj_file: Path) -> tuple[bytes, dict[int, bytes]]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("camp_func_0018b39c")
    if candidate is None:
        raise RuntimeError(f"camp_func_0018b39c not found in {obj_file}")

    sections, abs32_targets = elf_sections_and_abs32_targets(obj_file, "camp_func_0018b39c")
    rodata_map: dict[str, int] = {}
    rodata_chunks: dict[int, bytes] = {}
    next_addr = CAND_RODATA_ADDR

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):
            target = SYMBOL_TO_ADDRESS.get(rel.symbol_name)
            if target is None:
                raise RuntimeError(f"unresolved relocation {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            offset = target - pc
            if target in THUMB_STUBS:
                if offset & 3:
                    raise RuntimeError(f"unaligned Thumb target 0x{target:08x}")
                instruction = (
                    0xFA000000
                    | ((offset >> 2) & 0x00FFFFFF)
                    | ((offset & 2) << 23)
                )
                struct.pack_into("<I", code, rel.offset, instruction)
            else:
                if offset & 3:
                    raise RuntimeError(f"unaligned ARM target 0x{target:08x}")
                original = struct.unpack_from("<I", code, rel.offset)[0]
                cond = original & 0xFF000000
                struct.pack_into("<I", code, rel.offset, cond | ((offset >> 2) & 0x00FFFFFF))
        elif rel.relocation_type == 2:
            sec_name = abs32_targets[rel.offset]
            if sec_name not in rodata_map:
                rodata_map[sec_name] = next_addr
                rodata_chunks[next_addr] = sections[sec_name]
                next_addr += (len(sections[sec_name]) + 0xFFF) & ~0xFFF
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into("<I", code, rel.offset, rodata_map[sec_name] + addend)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code), rodata_chunks


def compile_candidate_baseline() -> tuple[bytes, dict[int, bytes]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"compile failed:\n{result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, dict[int, bytes]]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    result = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"mutant {name} compile failed:\n{result.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        for addr, size in (
            (CODE_ADDR, CODE_SIZE),
            (GLOBAL_ADDR, GLOBAL_SIZE),
            (CAND_RODATA_ADDR, CAND_RODATA_SIZE),
            (OBJ_ADDR, OBJ_SIZE),
            (BASE_ADDR, BASE_SIZE),
            (NODES_ADDR, NODES_SIZE),
            (TBB_ADDR, TBB_SIZE),
            (PAYLOAD_ADDR, PAYLOAD_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(addr, size)

        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))
        for address in STUB_NAMES:
            if address in THUMB_STUBS:
                self.uc.mem_write(address, struct.pack("<H", 0x4770))
            else:
                self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))

        self.uc.hook_add(
            unicorn.UC_HOOK_CODE,
            self._on_stub,
            begin=STUB_196EE0,
            end=STUB_CB + 4,
        )
        self.uc.hook_add(
            unicorn.UC_HOOK_MEM_WRITE,
            self._on_write,
            begin=0,
            end=0xFFFFFFFF,
        )

        self.case: dict = {}
        self.call_log: list[tuple] = []
        self.writes: list[tuple[int, int, int]] = []

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
            return
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address, size, user_data) -> None:
        if address not in STUB_NAMES:
            return
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        sp = uc.reg_read(arm.UC_ARM_REG_SP)

        if address == STUB_29F260:
            self.call_log.append(("29f260", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["slot_idx"])
        elif address == STUB_29F248:
            self.call_log.append(("29f248", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_2BF558:
            a4 = s32(struct.unpack("<I", uc.mem_read(sp, 4))[0])
            a5 = s32(struct.unpack("<I", uc.mem_read(sp + 4, 4))[0])
            self.call_log.append(("2bf558", r0, r1, r2, s32(r3), a4, a5))
        elif address == STUB_2BF460:
            a4 = s32(struct.unpack("<I", uc.mem_read(sp, 4))[0])
            a5 = s32(struct.unpack("<I", uc.mem_read(sp + 4, 4))[0])
            self.call_log.append(("2bf460", r0, r1, r2, s32(r3), a4, a5))
        elif address == STUB_2BF6D0:
            self.call_log.append(("2bf6d0", r0, r1))
            addr = NODES_ADDR + (0 if r1 == 0x20 else 0x20)
            uc.reg_write(arm.UC_ARM_REG_R0, addr)
        elif address == STUB_2C5FA4:
            self.call_log.append(("2c5fa4", r0, r1, r2))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["c5fa4_vals"][r1])
        elif address == STUB_CB:
            self.call_log.append(("cb", r0))
        elif address == STUB_2C0BA8:
            self.call_log.append(("2c0ba8", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, 1 if r0 in self.case["true_flags"] else 0)
        elif address == STUB_2C0EC4:
            self.call_log.append(("2c0ec4", r0, r1))
            uc.reg_write(arm.UC_ARM_REG_R0, TBB_ADDR)
        elif address == STUB_2C0E9C:
            self.call_log.append(("2c0e9c", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, PAYLOAD_ADDR if self.case["has_payload"] else 0)
        elif address == STUB_2C0E4C:
            self.call_log.append(("2c0e4c", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["row_count"])
        elif address == STUB_2BE7FC:
            fmt = read_cstr(uc, r1)
            arg = read_cstr(uc, r2)
            self.call_log.append(("2be7fc", fmt, arg))
            uc.mem_write(r0, arg + b"\x00")
            uc.reg_write(arm.UC_ARM_REG_R0, len(arg))
        elif address == STUB_2BE77C:
            text = read_cstr(uc, r2)
            floats = tuple(uc.reg_read(reg) for reg in S_REGS)
            self.call_log.append(("2be77c", r0, r1, text, floats))
        elif address == STUB_196EE0:
            ptr = struct.unpack("<I", uc.mem_read(sp, 4))[0]
            text = read_cstr(uc, ptr)
            self.call_log.append(("196ee0", r0, s32(r1), s32(r2), r3, text))

    def run(self, code: bytes, rodata: dict[int, bytes], case: dict) -> dict:
        self.case = case
        self.call_log = []
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        self.uc.mem_write(FUNC_ADDR, code)
        if rodata:
            for addr, chunk in rodata.items():
                self.uc.mem_write(addr, chunk)

        self.uc.mem_write(0x0043DC58, struct.pack("<I", OBJ_ADDR))
        self.uc.mem_write(0x0044EA00, struct.pack("<I", BASE_ADDR))

        self.uc.mem_write(OBJ_ADDR, b"\x00" * OBJ_SIZE)
        self.uc.mem_write(OBJ_ADDR + 0xA8, struct.pack("<B", case["obj_a8"]))
        self.uc.mem_write(
            OBJ_ADDR + 0x80 + case["slot_idx"] * 4,
            struct.pack("<I", 0xCAFEBABE),
        )

        self.uc.mem_write(BASE_ADDR, b"\x00" * BASE_SIZE)
        ctrl = BASE_ADDR + 0x12AC
        self.uc.mem_write(ctrl + 0x00, struct.pack("<I", 0))
        self.uc.mem_write(ctrl + 0x08, struct.pack("<I", case["prev_slot0"]))
        self.uc.mem_write(ctrl + 0x18, struct.pack("<B", case["dirty_flag"]))
        self.uc.mem_write(ctrl + 0x1C, struct.pack("<I", STUB_CB))

        self.uc.mem_write(NODES_ADDR, b"\x00" * NODES_SIZE)
        self.uc.mem_write(NODES_ADDR + 0x08, struct.pack("<hh", 10, -5))
        self.uc.mem_write(NODES_ADDR + 0x20 + 0x08, struct.pack("<hh", 30, 12))

        self.uc.mem_write(PAYLOAD_ADDR, b"\x00" * PAYLOAD_SIZE)
        for idx, label in enumerate((b"RowZero", b"RowOne", b"RowTwo")):
            self.uc.mem_write(PAYLOAD_ADDR + (idx << 7), label + b"\x00")

        self.uc.mem_write(STACK_ADDR, b"\xCC" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_R0, case["x"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["y"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for name, reg in CALLEE_SAVED.items():
            self.uc.reg_write(reg, CALLEE_SAVED_START[name])

        self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)

        return {
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()},
            "call_log": list(self.call_log),
            "writes": sorted(self.writes),
            "base_mem": bytes(self.uc.mem_read(BASE_ADDR, BASE_SIZE)),
        }


def base_case(**overrides) -> dict:
    case = {
        "name": "base",
        "x": 20,
        "y": 40,
        "obj_a8": 0,
        "slot_idx": 2,
        "prev_slot0": 100,
        "dirty_flag": 1,
        "c5fa4_vals": {1: 111, 7: 222},
        "true_flags": {0x555, 0x557},
        "row_count": 3,
        "has_payload": True,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    return [
        base_case(name="both_flags_row2_screen2"),
        base_case(name="flag_557_row1_screen3", true_flags={0x557}, obj_a8=1, x=-15, y=-25),
        base_case(name="flag_555_row0_no_dirty_same_val", true_flags={0x555}, dirty_flag=0, prev_slot0=111, c5fa4_vals={1: 111, 7: 111}),
        base_case(name="no_flags_early_exit", true_flags=set()),
        base_case(name="row_oob_early_exit", true_flags={0x555, 0x557}, row_count=2),
        base_case(name="null_payload_row0_early_exit", true_flags={0x555}, has_payload=False),
    ]


def compare_results(orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee_saved", "call_log", "writes", "base_mem"):
        if orig[key] != cand[key]:
            diffs.append(f"{key} mismatch")
    return diffs


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = raw_bin[off : off + FUNC_SIZE]

    cand_code, cand_rodata = compile_candidate_baseline()
    print(f"camp_func_0018b39c: orig {len(orig_code)} B, cand {len(cand_code)} B, rodata_chunks {len(cand_rodata)}")

    cases = make_cases()
    for case in cases:
        orig_res = Runner().run(orig_code, {}, case)
        cand_res = Runner().run(cand_code, cand_rodata, case)
        diffs = compare_results(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{case['name']}]: {diffs}")
            print("  orig log:", orig_res["call_log"])
            print("  cand log:", cand_res["call_log"])
            return 1
        print(f"PASS [{case['name']}]")

    mutants = [
        ("group", "constexpr u32 kGroup = 0x2F;", "constexpr u32 kGroup = 0x2E;"),
        ("color", "constexpr u32 kTextColor = 0xE09800FFu;", "constexpr u32 kTextColor = 0xE09800FEu;"),
        ("flag1", "constexpr u32 kFlagPrimary = 0x555;", "constexpr u32 kFlagPrimary = 0x554;"),
        ("flag2", "constexpr u32 kFlagSecondary = 0x557;", "constexpr u32 kFlagSecondary = 0x556;"),
        ("tbb", "constexpr u32 kTbbTableId = 0x36;", "constexpr u32 kTbbTableId = 0x37;"),
        ("screen", "(obj[0xA8] == 1) ? 3u : 2u", "(obj[0xA8] == 2) ? 3u : 2u"),
    ]
    for name, old, new in mutants:
        m_code, m_rodata = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig_res = Runner().run(orig_code, {}, case)
            bad_res = Runner().run(m_code, m_rodata, case)
            if compare_results(orig_res, bad_res):
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
