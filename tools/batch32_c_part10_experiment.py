#!/usr/bin/env python3
"""
Batch 32 C Part 10 differential verification runner:
  - engine_func_002f0888 (0x002F0888, 312 B)
  - ui_func_002f09c0 (0x002F09C0, 300 B)
  - ui_func_002f0aec (0x002F0AEC, 332 B)
  - ui_func_002f0c38 (0x002F0C38, 332 B)
  - ui_func_002f0d84 (0x002F0D84, 272 B)
"""

import os
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC, UC_HOOK_CODE
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
)

CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000
STACK_BASE = 0x0FFF0000
STACK_SIZE = 0x00010000

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "engine" / "leaf_batch32_c.cpp"
BUILD_DIR = ROOT / "build" / "batch32_c_part10"

ORIG_DATA = CODE_BIN.read_bytes()

COMPILED_FUNCTIONS = None
COMPILED_ST_VALUES = {}
RODATA_ADDR = 0x10050000
RODATA_BYTES = b""

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

def compile_function(func_name: str, out: Path = BUILD_DIR, source: Path = SOURCE):
    global COMPILED_FUNCTIONS, COMPILED_ST_VALUES, RODATA_BYTES
    if COMPILED_FUNCTIONS is None:
        out.mkdir(parents=True, exist_ok=True)
        obj = out / "leaf_batch32_c.o"
        compile_tu_armv6k(source, obj)
        COMPILED_FUNCTIONS = extract_elf_functions_detailed(obj)
        data = obj.read_bytes()
        e_shoff = struct.unpack_from('<I', data, 32)[0]
        e_shentsize = struct.unpack_from('<H', data, 46)[0]
        e_shnum = struct.unpack_from('<H', data, 48)[0]
        sections = [struct.unpack_from('<IIIIIIIIII', data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
        shstr = sections[struct.unpack_from('<H', data, 50)[0]]
        shstrtab = data[shstr[4]:shstr[4]+shstr[5]]
        def get_sh_name(off):
            return shstrtab[off:].split(b'\x00')[0].decode('ascii')
        for s in sections:
            if get_sh_name(s[0]) == ".rodata":
                RODATA_BYTES = data[s[4]:s[4]+s[5]]
                break

        symtab_sec = [s for s in sections if s[1] == 2][0]
        strtab_sec = sections[symtab_sec[6]]
        strtab_data = data[strtab_sec[4]:strtab_sec[4]+strtab_sec[5]]
        count = symtab_sec[5] // 16
        for i in range(count):
            st_name, st_value, st_size, st_info, st_other, st_shndx = struct.unpack_from('<IIIBBH', data, symtab_sec[4] + i * 16)
            name = strtab_data[st_name:].split(b'\x00')[0].decode('ascii', errors='ignore')
            if name:
                COMPILED_ST_VALUES[name] = st_value
    return COMPILED_FUNCTIONS[func_name]

def stage_body(body: bytes, relocs, target_addr: int, symbol_map: dict[str, int], func_name: str = "") -> bytes:
    data = bytearray(body)
    st_val = COMPILED_ST_VALUES.get(func_name, 0)
    for reloc in relocs:
        sym = reloc.symbol_name
        if sym == "":
            inst = struct.unpack_from("<I", data, reloc.offset)[0]
            if 0 <= inst < len(RODATA_BYTES):
                actual_addr = RODATA_ADDR + inst
            else:
                off_in_fn = inst - st_val
                actual_addr = target_addr + off_in_fn
            struct.pack_into("<I", data, reloc.offset, actual_addr)
            continue
        if sym not in symbol_map:
            raise RuntimeError(f"Unmapped relocation: {sym}")
        stub_addr = symbol_map[sym]
        inst = struct.unpack_from("<I", data, reloc.offset)[0]
        if inst == 0:
            struct.pack_into("<I", data, reloc.offset, stub_addr)
            continue
        rel_off = stub_addr - (target_addr + reloc.offset + 8)
        if (inst & 0xFE000000) == 0xFA000000:
            h = (rel_off >> 1) & 1
            imm24 = (rel_off >> 2) & 0x00FFFFFF
            inst = 0xFA000000 | (h << 24) | imm24
        else:
            imm24 = (rel_off >> 2) & 0x00FFFFFF
            inst = (inst & 0xFF000000) | imm24
        struct.pack_into("<I", data, reloc.offset, inst)
    return bytes(data)

def create_emulator() -> Uc:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc.mem_write(CODE_BASE, ORIG_DATA)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)
    uc.mem_map(0x10000000, 0x00100000, UC_PROT_READ | UC_PROT_WRITE)
    if RODATA_BYTES:
        uc.mem_write(RODATA_ADDR, RODATA_BYTES)
    return uc

CALL_96F60 = 0x00296F60
CALL_49BAC = 0x00249BAC
CALL_49B54 = 0x00249B54
CALL_93C98 = 0x00293C98
CALL_49B0C = 0x00249B0C
CALL_8DF54 = 0x0028DF54
CALL_C615C = 0x002C615C

BASE_SYMS = {
    "engine_func_00296f60": CALL_96F60,
    "ui_func_00249bac": CALL_49BAC,
    "func_00249b54": CALL_49B54,
    "ui_func_00293c98": CALL_93C98,
    "battle_func_00249b0c": CALL_49B0C,
    "battle_func_0028df54": CALL_8DF54,
    "ui_func_002c615c": CALL_C615C,
}

BASE_CTX = 0x00320000
UNIT_TABLE = 0x00330000
EXTRA_UNIT = 0x00360000

stub_ret = struct.pack("<I", 0xE12FFF1E) # bx lr

def test_engine_func_002f0888():
    print("Testing engine_func_002f0888 (0x002F0888)...")
    orig_code = load_original_bytes(0x002F0888, 312)
    comp, relocs = compile_function("engine_func_002f0888")
    comp_code = stage_body(comp, relocs, 0x002F0888, BASE_SYMS, "engine_func_002f0888")

    test_cases = [
        # tc 0: sel=0 (offset 7), target_val=50. Match on unit 0
        {"sel": 0, "target_val": 50, "u0_val": 50, "u_flags": 1, "extra_active": 0, "extra_val": 0},
        # tc 1: sel=1 (offset 10), target_val=80. Unit 0 has 50, no match
        {"sel": 1, "target_val": 80, "u0_val": 50, "u_flags": 1, "extra_active": 0, "extra_val": 0},
        # tc 2: sel=2 (offset 11), target_val=100. Unit 0 matches but flags 0x10 (inactive) -> no match
        {"sel": 2, "target_val": 100, "u0_val": 100, "u_flags": 0x11, "extra_active": 0, "extra_val": 0},
        # tc 3: sel=0, target_val=60. Unit 0 has 10, bonus unit matches!
        {"sel": 0, "target_val": 60, "u0_val": 10, "u_flags": 1, "extra_active": 1, "extra_val": 60},
        # tc 4: sel=0, target_val=60. Unit 0 has 10, bonus unit has 70 -> no match
        {"sel": 0, "target_val": 60, "u0_val": 10, "u_flags": 1, "extra_active": 1, "extra_val": 70},
    ]

    for tc in test_cases:
        results = []
        df54_calls = []

        slot_offsets = {0: 7, 1: 10, 2: 11}
        slot_off = slot_offsets[tc["sel"]]

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002F0888, code_bytes)
            for fn in BASE_SYMS.values():
                uc.mem_write(fn, stub_ret)

            def hook_96f60(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                if r0 == 0:
                    uc.reg_write(UC_ARM_REG_R0, 0)
                elif r0 == 1:
                    uc.reg_write(UC_ARM_REG_R0, tc["sel"])
                elif r0 == 2:
                    uc.reg_write(UC_ARM_REG_R0, tc["target_val"])
            uc.hook_add(UC_HOOK_CODE, hook_96f60, None, CALL_96F60, CALL_96F60 + 4)

            def hook_49b54(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                if STACK_BASE <= r1 < STACK_BASE + STACK_SIZE and STACK_BASE <= r2 < STACK_BASE + STACK_SIZE:
                    uc.mem_write(r1, struct.pack("<I", 0))
                    uc.mem_write(r2, struct.pack("<I", 1))
                elif STACK_BASE <= r0 < STACK_BASE + STACK_SIZE and STACK_BASE <= r1 < STACK_BASE + STACK_SIZE:
                    uc.mem_write(r0, struct.pack("<I", 0))
                    uc.mem_write(r1, struct.pack("<I", 1))
            uc.hook_add(UC_HOOK_CODE, hook_49b54, None, CALL_49B54, CALL_49B54 + 4)

            def hook_93c98(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, BASE_CTX)
            uc.hook_add(UC_HOOK_CODE, hook_93c98, None, CALL_93C98, CALL_93C98 + 4)

            def hook_49b0c(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, EXTRA_UNIT)
            uc.hook_add(UC_HOOK_CODE, hook_49b0c, None, CALL_49B0C, CALL_49B0C + 4)

            cur_df54 = []
            def hook_8df54(uc, addr, size, ud):
                cur_df54.append(uc.reg_read(UC_ARM_REG_R0))
            uc.hook_add(UC_HOOK_CODE, hook_8df54, None, CALL_8DF54, CALL_8DF54 + 4)

            uc.mem_write(BASE_CTX, b"\x00" * 0x5000)
            uc.mem_write(BASE_CTX + 0x1FC0, struct.pack("<I", UNIT_TABLE))
            uc.mem_write(BASE_CTX + 0x49C5, struct.pack("<B", tc["extra_active"]))

            uc.mem_write(UNIT_TABLE, b"\x00" * 648)
            uc.mem_write(UNIT_TABLE, struct.pack("<I", tc["u_flags"]))
            uc.mem_write(UNIT_TABLE + 0x72 + slot_off * 2, struct.pack("<h", tc["u0_val"]))

            uc.mem_write(EXTRA_UNIT, b"\x00" * 0x200)
            uc.mem_write(EXTRA_UNIT + 0x72 + slot_off * 2, struct.pack("<h", tc["extra_val"]))

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)

            uc.emu_start(0x002F0888, 0xF0000000, timeout=2000000)
            res = uc.reg_read(UC_ARM_REG_R0)
            results.append(res)
            df54_calls.append(cur_df54)

        assert results[0] == results[1], f"engine_func_002f0888 ret mismatch: {results[0]} vs {results[1]}"
        assert df54_calls[0] == df54_calls[1], f"engine_func_002f0888 df54 mismatch: {df54_calls[0]} vs {df54_calls[1]}"

    print("  engine_func_002f0888: PASS (all cases match)")

def test_ui_func_002f09c0():
    print("Testing ui_func_002f09c0 (0x002F09C0)...")
    orig_code = load_original_bytes(0x002F09C0, 300)
    comp, relocs = compile_function("ui_func_002f09c0")
    comp_code = stage_body(comp, relocs, 0x002F09C0, BASE_SYMS, "ui_func_002f09c0")

    test_cases = [
        # tc 0: target 50%. Unit HP = 60/100 (60% >= 50%) -> match
        {"target_pct": 50, "cur_hp": 60, "max_hp": 100, "extra_active": 0, "extra_hp": 0, "extra_max": 100},
        # tc 1: target 50%. Unit HP = 40/100 (40% < 50%) -> no match
        {"target_pct": 50, "cur_hp": 40, "max_hp": 100, "extra_active": 0, "extra_hp": 0, "extra_max": 100},
        # tc 2: target 50%. Unit HP = 30/100. Bonus unit HP = 45/100 (45% <= 50%) -> bonus matches!
        {"target_pct": 50, "cur_hp": 30, "max_hp": 100, "extra_active": 1, "extra_hp": 45, "extra_max": 100},
        # tc 3: target 50%. Unit HP = 30/100. Bonus unit HP = 80/100 (80% > 50%) -> no match!
        {"target_pct": 50, "cur_hp": 30, "max_hp": 100, "extra_active": 1, "extra_hp": 80, "extra_max": 100},
    ]

    for tc in test_cases:
        results = []
        df54_calls = []

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002F09C0, code_bytes)
            for fn in BASE_SYMS.values():
                uc.mem_write(fn, stub_ret)

            def hook_96f60(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                if r0 == 0:
                    uc.reg_write(UC_ARM_REG_R0, tc["target_pct"])
                else:
                    uc.reg_write(UC_ARM_REG_R0, 0)
            uc.hook_add(UC_HOOK_CODE, hook_96f60, None, CALL_96F60, CALL_96F60 + 4)

            def hook_49b54(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                if STACK_BASE <= r1 < STACK_BASE + STACK_SIZE and STACK_BASE <= r2 < STACK_BASE + STACK_SIZE:
                    uc.mem_write(r1, struct.pack("<I", 0))
                    uc.mem_write(r2, struct.pack("<I", 1))
                elif STACK_BASE <= r0 < STACK_BASE + STACK_SIZE and STACK_BASE <= r1 < STACK_BASE + STACK_SIZE:
                    uc.mem_write(r0, struct.pack("<I", 0))
                    uc.mem_write(r1, struct.pack("<I", 1))
            uc.hook_add(UC_HOOK_CODE, hook_49b54, None, CALL_49B54, CALL_49B54 + 4)

            def hook_93c98(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, BASE_CTX)
            uc.hook_add(UC_HOOK_CODE, hook_93c98, None, CALL_93C98, CALL_93C98 + 4)

            def hook_49b0c(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, EXTRA_UNIT)
            uc.hook_add(UC_HOOK_CODE, hook_49b0c, None, CALL_49B0C, CALL_49B0C + 4)

            def hook_c615c(uc, addr, size, ud):
                num = uc.reg_read(UC_ARM_REG_R0)
                den = uc.reg_read(UC_ARM_REG_R1)
                res = num // den if den != 0 else 0
                uc.reg_write(UC_ARM_REG_R0, res)
            uc.hook_add(UC_HOOK_CODE, hook_c615c, None, CALL_C615C, CALL_C615C + 4)

            cur_df54 = []
            def hook_8df54(uc, addr, size, ud):
                cur_df54.append(uc.reg_read(UC_ARM_REG_R0))
            uc.hook_add(UC_HOOK_CODE, hook_8df54, None, CALL_8DF54, CALL_8DF54 + 4)

            uc.mem_write(BASE_CTX, b"\x00" * 0x5000)
            uc.mem_write(BASE_CTX + 0x1FC0, struct.pack("<I", UNIT_TABLE))
            uc.mem_write(BASE_CTX + 0x49C5, struct.pack("<B", tc["extra_active"]))

            uc.mem_write(UNIT_TABLE, b"\x00" * 648)
            uc.mem_write(UNIT_TABLE, struct.pack("<I", 1)) # valid flags
            uc.mem_write(UNIT_TABLE + 0xCC + 0xE8, struct.pack("<H", tc["cur_hp"]))
            uc.mem_write(UNIT_TABLE + 0xCC + 0xEA, struct.pack("<h", tc["max_hp"]))

            uc.mem_write(EXTRA_UNIT, b"\x00" * 0x200)
            uc.mem_write(EXTRA_UNIT + 0xCC + 0xE8, struct.pack("<H", tc["extra_hp"]))
            uc.mem_write(EXTRA_UNIT + 0xCC + 0xEA, struct.pack("<h", tc["extra_max"]))

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)

            uc.emu_start(0x002F09C0, 0xF0000000, timeout=2000000)
            res = uc.reg_read(UC_ARM_REG_R0)
            results.append(res)
            df54_calls.append(cur_df54)

        assert results[0] == results[1], f"ui_func_002f09c0 ret mismatch: {results[0]} vs {results[1]}"
        assert df54_calls[0] == df54_calls[1], f"ui_func_002f09c0 df54 mismatch: {df54_calls[0]} vs {df54_calls[1]}"

    print("  ui_func_002f09c0: PASS (all cases match)")

def test_ui_func_002f0aec():
    print("Testing ui_func_002f0aec (0x002F0AEC)...")
    orig_code = load_original_bytes(0x002F0AEC, 332)
    comp, relocs = compile_function("ui_func_002f0aec")
    comp_code = stage_body(comp, relocs, 0x002F0AEC, BASE_SYMS, "ui_func_002f0aec")

    test_cases = [
        # tc 0: target_id 0x12, target_pct 50%. Unit matches ID and HP 40% <= 50% -> match
        {"target_id": 0x12, "target_pct": 50, "u_id": 0x12, "cur_hp": 40, "max_hp": 100, "extra_active": 0, "extra_id": 0, "extra_hp": 0},
        # tc 1: target_id 0x12, target_pct 50%. Unit matches ID but HP 70% > 50% -> no match
        {"target_id": 0x12, "target_pct": 50, "u_id": 0x12, "cur_hp": 70, "max_hp": 100, "extra_active": 0, "extra_id": 0, "extra_hp": 0},
        # tc 2: target_id 0x12. Unit ID is 0x34 (no match). Bonus unit ID 0x12, HP 30% <= 50% -> bonus matches!
        {"target_id": 0x12, "target_pct": 50, "u_id": 0x34, "cur_hp": 20, "max_hp": 100, "extra_active": 1, "extra_id": 0x12, "extra_hp": 30},
        # tc 3: target_id 0x12. Unit ID is 0x34. Bonus unit ID 0x12, HP 80% > 50% -> no match!
        {"target_id": 0x12, "target_pct": 50, "u_id": 0x34, "cur_hp": 20, "max_hp": 100, "extra_active": 1, "extra_id": 0x12, "extra_hp": 80},
    ]

    for tc in test_cases:
        results = []
        df54_calls = []

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002F0AEC, code_bytes)
            for fn in BASE_SYMS.values():
                uc.mem_write(fn, stub_ret)

            def hook_96f60(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                if r0 == 0:
                    uc.reg_write(UC_ARM_REG_R0, tc["target_id"])
                elif r0 == 1:
                    uc.reg_write(UC_ARM_REG_R0, tc["target_pct"])
                else:
                    uc.reg_write(UC_ARM_REG_R0, 0)
            uc.hook_add(UC_HOOK_CODE, hook_96f60, None, CALL_96F60, CALL_96F60 + 4)

            def hook_49b54(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                if STACK_BASE <= r1 < STACK_BASE + STACK_SIZE and STACK_BASE <= r2 < STACK_BASE + STACK_SIZE:
                    uc.mem_write(r1, struct.pack("<I", 0))
                    uc.mem_write(r2, struct.pack("<I", 1))
                elif STACK_BASE <= r0 < STACK_BASE + STACK_SIZE and STACK_BASE <= r1 < STACK_BASE + STACK_SIZE:
                    uc.mem_write(r0, struct.pack("<I", 0))
                    uc.mem_write(r1, struct.pack("<I", 1))
            uc.hook_add(UC_HOOK_CODE, hook_49b54, None, CALL_49B54, CALL_49B54 + 4)

            def hook_93c98(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, BASE_CTX)
            uc.hook_add(UC_HOOK_CODE, hook_93c98, None, CALL_93C98, CALL_93C98 + 4)

            def hook_49b0c(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, EXTRA_UNIT)
            uc.hook_add(UC_HOOK_CODE, hook_49b0c, None, CALL_49B0C, CALL_49B0C + 4)

            def hook_c615c(uc, addr, size, ud):
                num = uc.reg_read(UC_ARM_REG_R0)
                den = uc.reg_read(UC_ARM_REG_R1)
                res = num // den if den != 0 else 0
                uc.reg_write(UC_ARM_REG_R0, res)
            uc.hook_add(UC_HOOK_CODE, hook_c615c, None, CALL_C615C, CALL_C615C + 4)

            cur_df54 = []
            def hook_8df54(uc, addr, size, ud):
                cur_df54.append(uc.reg_read(UC_ARM_REG_R0))
            uc.hook_add(UC_HOOK_CODE, hook_8df54, None, CALL_8DF54, CALL_8DF54 + 4)

            uc.mem_write(BASE_CTX, b"\x00" * 0x5000)
            uc.mem_write(BASE_CTX + 0x1FC0, struct.pack("<I", UNIT_TABLE))
            uc.mem_write(BASE_CTX + 0x49C5, struct.pack("<B", tc["extra_active"]))

            uc.mem_write(UNIT_TABLE, b"\x00" * 648)
            uc.mem_write(UNIT_TABLE, struct.pack("<I", 1))
            uc.mem_write(UNIT_TABLE + 0xCE, struct.pack("<H", tc["u_id"]))
            uc.mem_write(UNIT_TABLE + 0xCC + 0xE8, struct.pack("<H", tc["cur_hp"]))
            uc.mem_write(UNIT_TABLE + 0xCC + 0xEA, struct.pack("<h", 100))

            uc.mem_write(EXTRA_UNIT, b"\x00" * 0x200)
            uc.mem_write(EXTRA_UNIT + 0xCE, struct.pack("<H", tc["extra_id"]))
            uc.mem_write(EXTRA_UNIT + 0xCC + 0xE8, struct.pack("<H", tc["extra_hp"]))
            uc.mem_write(EXTRA_UNIT + 0xCC + 0xEA, struct.pack("<h", 100))

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)

            uc.emu_start(0x002F0AEC, 0xF0000000, timeout=2000000)
            res = uc.reg_read(UC_ARM_REG_R0)
            results.append(res)
            df54_calls.append(cur_df54)

        assert results[0] == results[1], f"ui_func_002f0aec ret mismatch: {results[0]} vs {results[1]}"
        assert df54_calls[0] == df54_calls[1], f"ui_func_002f0aec df54 mismatch: {df54_calls[0]} vs {df54_calls[1]}"

    print("  ui_func_002f0aec: PASS (all cases match)")

def test_ui_func_002f0c38():
    print("Testing ui_func_002f0c38 (0x002F0C38)...")
    orig_code = load_original_bytes(0x002F0C38, 332)
    comp, relocs = compile_function("ui_func_002f0c38")
    comp_code = stage_body(comp, relocs, 0x002F0C38, BASE_SYMS, "ui_func_002f0c38")

    test_cases = [
        # tc 0: target_id 0x12, target_pct 50%. Unit matches ID and MP 40% <= 50% -> match
        {"target_id": 0x12, "target_pct": 50, "u_id": 0x12, "cur_mp": 40, "max_mp": 100, "extra_active": 0, "extra_id": 0, "extra_mp": 0},
        # tc 1: target_id 0x12, target_pct 50%. Unit matches ID but MP 70% > 50% -> no match
        {"target_id": 0x12, "target_pct": 50, "u_id": 0x12, "cur_mp": 70, "max_mp": 100, "extra_active": 0, "extra_id": 0, "extra_mp": 0},
        # tc 2: target_id 0x12. Unit ID is 0x34 (no match). Bonus unit ID 0x12, MP 30% <= 50% -> bonus matches!
        {"target_id": 0x12, "target_pct": 50, "u_id": 0x34, "cur_mp": 20, "max_mp": 100, "extra_active": 1, "extra_id": 0x12, "extra_mp": 30},
        # tc 3: target_id 0x12. Unit ID is 0x34. Bonus unit ID 0x12, MP 80% > 50% -> no match!
        {"target_id": 0x12, "target_pct": 50, "u_id": 0x34, "cur_mp": 20, "max_mp": 100, "extra_active": 1, "extra_id": 0x12, "extra_mp": 80},
    ]

    for tc in test_cases:
        results = []
        df54_calls = []

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002F0C38, code_bytes)
            for fn in BASE_SYMS.values():
                uc.mem_write(fn, stub_ret)

            def hook_96f60(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                if r0 == 0:
                    uc.reg_write(UC_ARM_REG_R0, tc["target_id"])
                elif r0 == 1:
                    uc.reg_write(UC_ARM_REG_R0, tc["target_pct"])
                else:
                    uc.reg_write(UC_ARM_REG_R0, 0)
            uc.hook_add(UC_HOOK_CODE, hook_96f60, None, CALL_96F60, CALL_96F60 + 4)

            def hook_49b54(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                if STACK_BASE <= r1 < STACK_BASE + STACK_SIZE and STACK_BASE <= r2 < STACK_BASE + STACK_SIZE:
                    uc.mem_write(r1, struct.pack("<I", 0))
                    uc.mem_write(r2, struct.pack("<I", 1))
                elif STACK_BASE <= r0 < STACK_BASE + STACK_SIZE and STACK_BASE <= r1 < STACK_BASE + STACK_SIZE:
                    uc.mem_write(r0, struct.pack("<I", 0))
                    uc.mem_write(r1, struct.pack("<I", 1))
            uc.hook_add(UC_HOOK_CODE, hook_49b54, None, CALL_49B54, CALL_49B54 + 4)

            def hook_93c98(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, BASE_CTX)
            uc.hook_add(UC_HOOK_CODE, hook_93c98, None, CALL_93C98, CALL_93C98 + 4)

            def hook_49b0c(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, EXTRA_UNIT)
            uc.hook_add(UC_HOOK_CODE, hook_49b0c, None, CALL_49B0C, CALL_49B0C + 4)

            def hook_c615c(uc, addr, size, ud):
                num = uc.reg_read(UC_ARM_REG_R0)
                den = uc.reg_read(UC_ARM_REG_R1)
                res = num // den if den != 0 else 0
                uc.reg_write(UC_ARM_REG_R0, res)
            uc.hook_add(UC_HOOK_CODE, hook_c615c, None, CALL_C615C, CALL_C615C + 4)

            cur_df54 = []
            def hook_8df54(uc, addr, size, ud):
                cur_df54.append(uc.reg_read(UC_ARM_REG_R0))
            uc.hook_add(UC_HOOK_CODE, hook_8df54, None, CALL_8DF54, CALL_8DF54 + 4)

            uc.mem_write(BASE_CTX, b"\x00" * 0x5000)
            uc.mem_write(BASE_CTX + 0x1FC0, struct.pack("<I", UNIT_TABLE))
            uc.mem_write(BASE_CTX + 0x49C5, struct.pack("<B", tc["extra_active"]))

            uc.mem_write(UNIT_TABLE, b"\x00" * 648)
            uc.mem_write(UNIT_TABLE, struct.pack("<I", 1))
            uc.mem_write(UNIT_TABLE + 0xCE, struct.pack("<H", tc["u_id"]))
            uc.mem_write(UNIT_TABLE + 0xCC + 0xEC, struct.pack("<H", tc["cur_mp"]))
            uc.mem_write(UNIT_TABLE + 0xCC + 0xEE, struct.pack("<h", 100))

            uc.mem_write(EXTRA_UNIT, b"\x00" * 0x200)
            uc.mem_write(EXTRA_UNIT + 0xCE, struct.pack("<H", tc["extra_id"]))
            uc.mem_write(EXTRA_UNIT + 0xCC + 0xEC, struct.pack("<H", tc["extra_mp"]))
            uc.mem_write(EXTRA_UNIT + 0xCC + 0xEE, struct.pack("<h", 100))

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)

            uc.emu_start(0x002F0C38, 0xF0000000, timeout=2000000)
            res = uc.reg_read(UC_ARM_REG_R0)
            results.append(res)
            df54_calls.append(cur_df54)

        assert results[0] == results[1], f"ui_func_002f0c38 ret mismatch: {results[0]} vs {results[1]}"
        assert df54_calls[0] == df54_calls[1], f"ui_func_002f0c38 df54 mismatch: {df54_calls[0]} vs {df54_calls[1]}"

    print("  ui_func_002f0c38: PASS (all cases match)")

def test_ui_func_002f0d84():
    print("Testing ui_func_002f0d84 (0x002F0D84)...")
    orig_code = load_original_bytes(0x002F0D84, 272)
    comp, relocs = compile_function("ui_func_002f0d84")
    comp_code = stage_body(comp, relocs, 0x002F0D84, BASE_SYMS, "ui_func_002f0d84")

    test_cases = [
        # tc 0: target 30. Unit 0 has 50 (avg 50 >= 30) -> 1
        {"target": 30, "u_val": 50, "extra_active": 0, "extra_val": 0},
        # tc 1: target 60. Unit 0 has 50 (avg 50 < 60) -> 0
        {"target": 60, "u_val": 50, "extra_active": 0, "extra_val": 0},
        # tc 2: target 40. Unit 0 has 20, Bonus has 80 -> avg (20+80)/2 = 50 >= 40 -> 1
        {"target": 40, "u_val": 20, "extra_active": 1, "extra_val": 80},
        # tc 3: target 60. Unit 0 has 20, Bonus has 80 -> avg 50 < 60 -> 0
        {"target": 60, "u_val": 20, "extra_active": 1, "extra_val": 80},
    ]

    for tc in test_cases:
        results = []
        df54_calls = []

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002F0D84, code_bytes)
            for fn in BASE_SYMS.values():
                uc.mem_write(fn, stub_ret)

            def hook_96f60(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                if r0 == 0:
                    uc.reg_write(UC_ARM_REG_R0, tc["target"])
                else:
                    uc.reg_write(UC_ARM_REG_R0, 0)
            uc.hook_add(UC_HOOK_CODE, hook_96f60, None, CALL_96F60, CALL_96F60 + 4)

            def hook_49b54(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                if STACK_BASE <= r1 < STACK_BASE + STACK_SIZE and STACK_BASE <= r2 < STACK_BASE + STACK_SIZE:
                    uc.mem_write(r1, struct.pack("<I", 0))
                    uc.mem_write(r2, struct.pack("<I", 1))
                elif STACK_BASE <= r0 < STACK_BASE + STACK_SIZE and STACK_BASE <= r1 < STACK_BASE + STACK_SIZE:
                    uc.mem_write(r0, struct.pack("<I", 0))
                    uc.mem_write(r1, struct.pack("<I", 1))
            uc.hook_add(UC_HOOK_CODE, hook_49b54, None, CALL_49B54, CALL_49B54 + 4)

            def hook_93c98(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, BASE_CTX)
            uc.hook_add(UC_HOOK_CODE, hook_93c98, None, CALL_93C98, CALL_93C98 + 4)

            def hook_49b0c(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, EXTRA_UNIT)
            uc.hook_add(UC_HOOK_CODE, hook_49b0c, None, CALL_49B0C, CALL_49B0C + 4)

            def hook_c615c(uc, addr, size, ud):
                num = uc.reg_read(UC_ARM_REG_R0)
                den = uc.reg_read(UC_ARM_REG_R1)
                res = num // den if den != 0 else 0
                uc.reg_write(UC_ARM_REG_R0, res)
            uc.hook_add(UC_HOOK_CODE, hook_c615c, None, CALL_C615C, CALL_C615C + 4)

            cur_df54 = []
            def hook_8df54(uc, addr, size, ud):
                cur_df54.append(uc.reg_read(UC_ARM_REG_R0))
            uc.hook_add(UC_HOOK_CODE, hook_8df54, None, CALL_8DF54, CALL_8DF54 + 4)

            uc.mem_write(BASE_CTX, b"\x00" * 0x5000)
            uc.mem_write(BASE_CTX + 0x1FC0, struct.pack("<I", UNIT_TABLE))
            uc.mem_write(BASE_CTX + 0x49C5, struct.pack("<B", tc["extra_active"]))

            uc.mem_write(UNIT_TABLE, b"\x00" * 648)
            uc.mem_write(UNIT_TABLE, struct.pack("<I", 1))
            uc.mem_write(UNIT_TABLE + 0x100 + 0xCC, struct.pack("<H", tc["u_val"]))

            uc.mem_write(EXTRA_UNIT, b"\x00" * 0x200)
            uc.mem_write(EXTRA_UNIT + 0x100 + 0xCC, struct.pack("<H", tc["extra_val"]))

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)

            uc.emu_start(0x002F0D84, 0xF0000000, timeout=2000000)
            res = uc.reg_read(UC_ARM_REG_R0)
            results.append(res)
            df54_calls.append(cur_df54)

        assert results[0] == results[1], f"ui_func_002f0d84 ret mismatch: {results[0]} vs {results[1]}"
        assert df54_calls[0] == df54_calls[1], f"ui_func_002f0d84 df54 mismatch: {df54_calls[0]} vs {df54_calls[1]}"

    print("  ui_func_002f0d84: PASS (all cases match)")

if __name__ == "__main__":
    print("Running Batch 32 C Part 10 differential tests...")
    test_engine_func_002f0888()
    test_ui_func_002f09c0()
    test_ui_func_002f0aec()
    test_ui_func_002f0c38()
    test_ui_func_002f0d84()
    print("\nALL BATCH 32 C PART 10 TESTS PASSED!")
