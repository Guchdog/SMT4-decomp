#!/usr/bin/env python3
"""Differential test for shop_func_003a211c (0x003A211C) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the shop_func_003a211c body,
resolves its direct calls and any .rodata relocations, and runs the pinned
original (extracted/exefs/code.bin) against the candidate in separate Unicorn
machines with identical fixtures.
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
OUT_DIR = ROOT / "build/test_leaf_003a211c"

FUNC_ADDR = 0x003A211C
FUNC_SIZE = 696

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x001D0000  # covers 0x0022F364..0x0029EBC4 and 0x003A211C
BIN_RODATA_ADDR = 0x00400000
BIN_RODATA_SIZE = 0x00060000  # covers 0x00407678 and 0x0044E020 from code.bin
CAND_RODATA_ADDR = 0x00600000
CAND_RODATA_SIZE = 0x00010000
WORK_ADDR = 0x00700000
WORK_SIZE = 0x00010000
VOBJ_ADDR = 0x00720000
VOBJ_SIZE = 0x00001000
VTBL_ADDR = 0x00730000
VTBL_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_230E54 = 0x00230E54  # func_00230e54
STUB_231D60 = 0x00231D60  # camp_func_00231d60
STUB_29EBC4 = 0x0029EBC4  # shop_func_0029ebc4
STUB_2338AC = 0x002338AC  # unite_func_002338ac
STUB_240E8C = 0x00240E8C  # shop_func_00240e8c
STUB_22F364 = 0x0022F364  # shop_func_0022f364
STUB_2337A0 = 0x002337A0  # shop_func_002337a0
STUB_23347C = 0x0023347C  # func_0023347c
STUB_VCALL4 = 0x002D0000  # virtual method vtbl[4]

STUB_NAMES = {
    STUB_230E54: "func_00230e54",
    STUB_231D60: "camp_func_00231d60",
    STUB_29EBC4: "shop_func_0029ebc4",
    STUB_2338AC: "unite_func_002338ac",
    STUB_240E8C: "shop_func_00240e8c",
    STUB_22F364: "shop_func_0022f364",
    STUB_2337A0: "shop_func_002337a0",
    STUB_23347C: "func_0023347c",
    STUB_VCALL4: "vcall4",
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


def s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


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

    # Find symtab and rel section for func_name
    symtab_sec = next(s for n, s in zip(sec_names, sections) if n == ".symtab")
    sym_data = data[symtab_sec[4] : symtab_sec[4] + symtab_sec[5]]
    syms = [struct.unpack_from("<IIIBBH", sym_data, i) for i in range(0, len(sym_data), 16)]

    # Find text section index and function offset for func_name
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
    for name, sec in zip(sec_names, sections):
        if sec[1] == 9 and sec[7] == func_shndx:  # SHT_REL targeting func_shndx
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
    candidate = funcs.get("shop_func_003a211c")
    if candidate is None:
        raise RuntimeError(f"shop_func_003a211c not found in {obj_file}")

    sections, abs32_targets = elf_sections_and_abs32_targets(obj_file, "shop_func_003a211c")
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


def compile_candidate_baseline() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"compile failed:\n{result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
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
    def __init__(self, bin_rodata: bytes) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        for addr, size in (
            (CODE_ADDR, CODE_SIZE),
            (BIN_RODATA_ADDR, BIN_RODATA_SIZE),
            (CAND_RODATA_ADDR, CAND_RODATA_SIZE),
            (WORK_ADDR, WORK_SIZE),
            (VOBJ_ADDR, VOBJ_SIZE),
            (VTBL_ADDR, VTBL_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(addr, size)

        self.uc.mem_write(BIN_RODATA_ADDR, bin_rodata)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))
        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))

        self.uc.hook_add(
            unicorn.UC_HOOK_CODE,
            self._on_stub,
            begin=STUB_22F364,
            end=STUB_VCALL4 + 4,
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

        if address == STUB_230E54:
            arg4 = struct.unpack("<I", uc.mem_read(sp, 4))[0]
            self.call_log.append(("230e54", r0, r1, s32(r2), s32(r3), arg4))
        elif address == STUB_231D60:
            a4 = struct.unpack("<I", uc.mem_read(sp, 4))[0]
            a5 = struct.unpack("<I", uc.mem_read(sp + 4, 4))[0]
            self.call_log.append(("231d60", r0, s32(r1), s32(r2), s32(r3), a4, a5))
        elif address == STUB_29EBC4:
            self.call_log.append(("29ebc4", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["top_idx"] & 0xFFFFFFFF)
        elif address == STUB_2338AC:
            self.call_log.append(("2338ac", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["visible"] & 0xFFFFFFFF)
        elif address == STUB_240E8C:
            self.call_log.append(("240e8c", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["cur_row"] & 0xFFFFFFFF)
        elif address == STUB_22F364:
            val = struct.unpack("<I", uc.mem_read(r3, 4))[0]
            self.call_log.append(("22f364", r0, s32(r1), s32(r2), r3, val))
        elif address == STUB_2337A0:
            self.call_log.append(("2337a0", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["sel_idx"] & 0xFFFFFFFF)
        elif address == STUB_23347C:
            self.call_log.append(("23347c", r0, s32(r1), s32(r2)))
        elif address == STUB_VCALL4:
            self.call_log.append(("vcall4", r0, r1))

    def run(self, code: bytes, rodata: bytes, case: dict) -> dict:
        self.case = case
        self.call_log = []
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        self.uc.mem_write(FUNC_ADDR, code)
        if rodata:
            for addr, chunk in rodata.items():
                self.uc.mem_write(addr, chunk)
        self.uc.mem_write(WORK_ADDR, b"\x00" * WORK_SIZE)
        self.uc.mem_write(VOBJ_ADDR, struct.pack("<I", VTBL_ADDR))
        self.uc.mem_write(VTBL_ADDR + 0x10, struct.pack("<I", STUB_VCALL4))
        self.uc.mem_write(STACK_ADDR, b"\xCC" * STACK_SIZE)

        tab = case["tab"]
        self.uc.mem_write(WORK_ADDR + 0x04, struct.pack("<I", case["state"]))
        self.uc.mem_write(WORK_ADDR + 0x37C, struct.pack("<I", case["prio"]))
        self.uc.mem_write(WORK_ADDR + 0x85C, struct.pack("<I", VOBJ_ADDR))
        self.uc.mem_write(WORK_ADDR + 0x860, struct.pack("<I", tab))
        self.uc.mem_write(WORK_ADDR + 0x864, struct.pack("<I", case["sub"]))

        panel_off = 0x880 + tab * 0x74
        self.uc.mem_write(WORK_ADDR + panel_off + 0x08, struct.pack("<i", case["panel_count"]))

        entries_off = 0xC94 + tab * 0x1002
        for i in range(16):
            self.uc.mem_write(WORK_ADDR + entries_off + i * 4, struct.pack("<I", 0x1000 + i))

        self.uc.reg_write(arm.UC_ARM_REG_R0, WORK_ADDR)
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
            "work_mem": bytes(self.uc.mem_read(WORK_ADDR, WORK_SIZE)),
        }


def base_case(**overrides) -> dict:
    case = {
        "name": "base",
        "tab": 0,
        "sub": 0,
        "state": 5,
        "prio": 0xB5,
        "panel_count": 5,
        "top_idx": 2,
        "visible": 4,
        "cur_row": 1,
        "sel_idx": 3,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases = []
    for tab in range(9):
        cases.append(base_case(name=f"tab_{tab}", tab=tab, sub=tab % 4))
    for st in (0, 5, 6, 7, 9, 10, 11, 15, 16, 17):
        cases.append(base_case(name=f"state_{st}", state=st))
    cases.append(base_case(name="visible_0_panel_count_0", visible=0, panel_count=0))
    cases.append(base_case(name="highlight_panel_count_0", state=5, panel_count=0))
    return cases


def compare_results(orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee_saved", "call_log", "writes", "work_mem"):
        if orig[key] != cand[key]:
            diffs.append(f"{key} mismatch")
    return diffs


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = raw_bin[off : off + FUNC_SIZE]
    bin_rodata = raw_bin[BIN_RODATA_ADDR - 0x00100000 : BIN_RODATA_ADDR - 0x00100000 + BIN_RODATA_SIZE]

    cand_code, cand_rodata = compile_candidate_baseline()
    print(f"shop_func_003a211c: orig {len(orig_code)} B, cand {len(cand_code)} B, rodata_chunks {len(cand_rodata)}")

    cases = make_cases()
    for case in cases:
        orig_res = Runner(bin_rodata).run(orig_code, b"", case)
        cand_res = Runner(bin_rodata).run(cand_code, cand_rodata, case)
        diffs = compare_results(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{case['name']}]: {diffs}")
            print("  orig log:", orig_res["call_log"])
            print("  cand log:", cand_res["call_log"])
            return 1
        print(f"PASS [{case['name']}]")

    mutants = [
        ("tab6_kind", "tab_kind = 0x0B;", "tab_kind = 0x0A;"),
        ("table_a", "constexpr u32 kTableA[4] = {0x6F, 0x6E, 0x71, 0x70};", "constexpr u32 kTableA[4] = {0x6F, 0x6E, 0x71, 0x72};"),
        ("table_b", "constexpr u32 kTableB[4] = {0x7A, 0x79, 0x7C, 0x7B};", "constexpr u32 kTableB[4] = {0x7A, 0x79, 0x7C, 0x7D};"),
        ("sub_indices", "{3, 1},", "{3, 0},"),
        ("highlight_state", "state == 0xF || state == 0x10", "state == 0xF || state == 0x11"),
        ("entry_stride", "work + 0xC94 + cur_tab * 0x1002", "work + 0xC94 + cur_tab * 0x1000"),
        ("panel_stride", "work + 0x880 + cur_tab * 0x74", "work + 0x880 + cur_tab * 0x70"),
    ]
    for name, old, new in mutants:
        m_code, m_rodata = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig_res = Runner(bin_rodata).run(orig_code, b"", case)
            bad_res = Runner(bin_rodata).run(m_code, m_rodata, case)
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
