#!/usr/bin/env python3
"""Differential test for batch 32 C part 8:
- ui_func_002dbd58 (0x002DBD58, 248 B)
- ui_func_002dbc2c (0x002DBC2C, 300 B)
- ui_func_002e3c68 (0x002E3C68, 264 B)
- camp_func_002dc738 (0x002DC738, 264 B)
- ui_func_002e0b50 (0x002E0B50, 260 B)
"""

from __future__ import annotations

from pathlib import Path
import struct
import sys

from unicorn import (
    Uc,
    UC_ARCH_ARM,
    UC_MODE_ARM,
    UC_HOOK_MEM_UNMAPPED,
)
from unicorn.arm_const import (
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_R4,
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

COMPILED_FUNCTIONS = None
COMPILED_ST_VALUES = {}
RODATA_ADDR = 0x10050000
RODATA_BYTES = b""
SOURCE = ROOT / "src/engine/leaf_batch32_c.cpp"

with open(ORIG_BIN, "rb") as f:
    ORIG_DATA = f.read()

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS, COMPILED_ST_VALUES, RODATA_BYTES
    if COMPILED_FUNCTIONS is None:
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

def unmapped_hook(uc, access, address, size, value, user_data):
    aligned = address & ~0xFFF
    uc.mem_map(aligned, 0x1000)
    return True

def create_emulator() -> Uc:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, ORIG_DATA)
    uc.mem_map(0x00480000, 0x00100000)
    uc.mem_map(0x10000000, 0x00100000)
    if RODATA_BYTES:
        uc.mem_write(RODATA_ADDR, RODATA_BYTES)
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, unmapped_hook)

    val = uc.reg_read(UC_ARM_REG_C1_C0_2)
    val |= (0xF << 20)
    uc.reg_write(UC_ARM_REG_C1_C0_2, val)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    return uc

# ---------------------------------------------------------------------------
# Test 1: ui_func_002dbd58 (0x002DBD58)
# ---------------------------------------------------------------------------
def test_002dbd58(out: Path):
    print("Testing ui_func_002dbd58 (0x002DBD58)...")
    comp, relocs = compile_function("ui_func_002dbd58", out)
    orig_bytes = load_original_bytes(0x002DBD58, 248)

    CALL_96F60 = 0x00296F60
    CALL_49BAC = 0x00249BAC
    CALL_49B54 = 0x00249B54
    CALL_93C98 = 0x00293C98
    CALL_49B0C = 0x00249B0C
    CALL_8DF54 = 0x0028DF54

    BASE_CTX = 0x10090000
    UNIT_TABLE = 0x100A0000
    EXTRA_UNIT = 0x100B0000

    syms = {
        "engine_func_00296f60": CALL_96F60,
        "ui_func_00249bac": CALL_49BAC,
        "func_00249b54": CALL_49B54,
        "ui_func_00293c98": CALL_93C98,
        "battle_func_00249b0c": CALL_49B0C,
        "battle_func_0028df54": CALL_8DF54,
    }
    staged_compiled = stage_body(comp, relocs, 0x002DBD58, syms, "ui_func_002dbd58")

    stub_ret = struct.pack("<I", 0xe12fff1e) # bx lr

    test_cases = [
        # (target, start, count, extra_flag, extra_val)
        (0x1234, 0, 3, 0, 0),        # target matches unit 1 (val 0x1234) -> 1
        (0x9999, 0, 3, 0, 0),        # target not found -> 0
        (0x5555, 0, 2, 1, 0x5555),   # target matches extra unit -> 1
        (0x5555, 0, 2, 0, 0x5555),   # extra flag 0 -> not found -> 0
        (0x1234, 0, 0, 0, 0),        # count 0 -> 0
    ]

    for target, st_val, cnt_val, extra_flg, extra_val in test_cases:
        results = []
        df54_calls = []

        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002DBD58, code_bytes)

            for fn in (CALL_96F60, CALL_49BAC, CALL_49B54, CALL_93C98, CALL_49B0C, CALL_8DF54):
                uc.mem_write(fn, stub_ret)

            def hook_96f60(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                if r0 == 0:
                    uc.reg_write(UC_ARM_REG_R0, target)
                else:
                    uc.reg_write(UC_ARM_REG_R0, 0)
            uc.hook_add(1, hook_96f60, None, CALL_96F60, CALL_96F60 + 4)

            def hook_49b54(uc, addr, size, ud):
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                uc.mem_write(r1, struct.pack("<I", st_val))
                uc.mem_write(r2, struct.pack("<I", cnt_val))
            uc.hook_add(1, hook_49b54, None, CALL_49B54, CALL_49B54 + 4)

            def hook_93c98(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, BASE_CTX)
            uc.hook_add(1, hook_93c98, None, CALL_93C98, CALL_93C98 + 4)

            def hook_49b0c(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, EXTRA_UNIT)
            uc.hook_add(1, hook_49b0c, None, CALL_49B0C, CALL_49B0C + 4)

            cur_df54 = []
            def hook_8df54(uc, addr, size, ud):
                cur_df54.append(uc.reg_read(UC_ARM_REG_R0))
            uc.hook_add(1, hook_8df54, None, CALL_8DF54, CALL_8DF54 + 4)

            uc.mem_write(BASE_CTX + 0x1FC0, struct.pack("<I", UNIT_TABLE))
            uc.mem_write(BASE_CTX + 0x49C5, struct.pack("<B", extra_flg))
            uc.mem_write(EXTRA_UNIT + 0xCE, struct.pack("<H", extra_val))

            # Units in UNIT_TABLE: stride 648
            # Unit 0: val 0x1111, status 1
            # Unit 1: val 0x1234, status 1
            # Unit 2: val 0x1234, status 0x11 (inactive)
            uc.mem_write(UNIT_TABLE + 0 * 648, struct.pack("<I", 1))
            uc.mem_write(UNIT_TABLE + 0 * 648 + 0xCE, struct.pack("<H", 0x1111))

            uc.mem_write(UNIT_TABLE + 1 * 648, struct.pack("<I", 1))
            uc.mem_write(UNIT_TABLE + 1 * 648 + 0xCE, struct.pack("<H", 0x1234))

            uc.mem_write(UNIT_TABLE + 2 * 648, struct.pack("<I", 0x11))
            uc.mem_write(UNIT_TABLE + 2 * 648 + 0xCE, struct.pack("<H", 0x1234))

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)

            uc.emu_start(0x002DBD58, 0xF0000000, timeout=2000000)
            res = uc.reg_read(UC_ARM_REG_R0)
            results.append(res)
            df54_calls.append(cur_df54)

        assert results[0] == results[1], f"ui_func_002dbd58 mismatch ret: {results[0]} != {results[1]}"
        assert df54_calls[0] == df54_calls[1], f"ui_func_002dbd58 mismatch df54: {df54_calls[0]} != {df54_calls[1]}"

    print("  ui_func_002dbd58: PASS (all cases match)")

# ---------------------------------------------------------------------------
# Test 2: ui_func_002dbc2c (0x002DBC2C)
# ---------------------------------------------------------------------------
def test_002dbc2c(out: Path):
    print("Testing ui_func_002dbc2c (0x002DBC2C)...")
    comp, relocs = compile_function("ui_func_002dbc2c", out)
    orig_bytes = load_original_bytes(0x002DBC2C, 300)

    CALL_96F60 = 0x00296F60
    CALL_49BAC = 0x00249BAC
    CALL_49B54 = 0x00249B54
    CALL_93C98 = 0x00293C98
    CALL_49B0C = 0x00249B0C
    CALL_C615C = 0x002C615C
    CALL_8DF54 = 0x0028DF54

    BASE_CTX = 0x10090000
    UNIT_TABLE = 0x100A0000
    EXTRA_UNIT = 0x100B0000

    syms = {
        "engine_func_00296f60": CALL_96F60,
        "ui_func_00249bac": CALL_49BAC,
        "func_00249b54": CALL_49B54,
        "ui_func_00293c98": CALL_93C98,
        "battle_func_00249b0c": CALL_49B0C,
        "ui_func_002c615c": CALL_C615C,
        "battle_func_0028df54": CALL_8DF54,
    }
    staged_compiled = stage_body(comp, relocs, 0x002DBC2C, syms, "ui_func_002dbc2c")

    stub_ret = struct.pack("<I", 0xe12fff1e) # bx lr

    test_cases = [
        # (target_pct, cur_hp, max_hp, extra_flag, extra_cur, extra_max)
        (50, 30, 100, 0, 0, 0),     # 30% <= 50% -> 1
        (50, 80, 100, 0, 0, 0),     # 80% > 50% -> 0
        (50, 80, 100, 1, 20, 100),  # extra unit 20% <= 50% -> 1
        (50, 80, 100, 1, 90, 100),  # extra unit 90% > 50% -> 0
    ]

    for target_pct, cur_hp, max_hp, extra_flg, e_cur, e_max in test_cases:
        results = []
        df54_calls = []

        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002DBC2C, code_bytes)

            for fn in (CALL_96F60, CALL_49BAC, CALL_49B54, CALL_93C98, CALL_49B0C, CALL_C615C, CALL_8DF54):
                uc.mem_write(fn, stub_ret)

            def hook_96f60(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                if r0 == 0:
                    uc.reg_write(UC_ARM_REG_R0, target_pct)
                else:
                    uc.reg_write(UC_ARM_REG_R0, 0)
            uc.hook_add(1, hook_96f60, None, CALL_96F60, CALL_96F60 + 4)

            def hook_49b54(uc, addr, size, ud):
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                uc.mem_write(r1, struct.pack("<I", 0))
                uc.mem_write(r2, struct.pack("<I", 1))
            uc.hook_add(1, hook_49b54, None, CALL_49B54, CALL_49B54 + 4)

            def hook_93c98(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, BASE_CTX)
            uc.hook_add(1, hook_93c98, None, CALL_93C98, CALL_93C98 + 4)

            def hook_49b0c(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, EXTRA_UNIT)
            uc.hook_add(1, hook_49b0c, None, CALL_49B0C, CALL_49B0C + 4)

            def hook_c615c(uc, addr, size, ud):
                num = uc.reg_read(UC_ARM_REG_R0)
                den = uc.reg_read(UC_ARM_REG_R1)
                res = num // den if den else 0
                uc.reg_write(UC_ARM_REG_R0, res)
            uc.hook_add(1, hook_c615c, None, CALL_C615C, CALL_C615C + 4)

            cur_df54 = []
            def hook_8df54(uc, addr, size, ud):
                cur_df54.append(uc.reg_read(UC_ARM_REG_R0))
            uc.hook_add(1, hook_8df54, None, CALL_8DF54, CALL_8DF54 + 4)

            uc.mem_write(BASE_CTX + 0x1FC0, struct.pack("<I", UNIT_TABLE))
            uc.mem_write(BASE_CTX + 0x49C5, struct.pack("<B", extra_flg))

            # Unit 0
            uc.mem_write(UNIT_TABLE, struct.pack("<I", 1))
            uc.mem_write(UNIT_TABLE + 0xCC + 0xE8, struct.pack("<H", cur_hp))
            uc.mem_write(UNIT_TABLE + 0xCC + 0xEA, struct.pack("<h", max_hp))

            # Extra Unit
            uc.mem_write(EXTRA_UNIT + 0xCC + 0xE8, struct.pack("<H", e_cur))
            uc.mem_write(EXTRA_UNIT + 0xCC + 0xEA, struct.pack("<h", e_max))

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)

            uc.emu_start(0x002DBC2C, 0xF0000000, timeout=2000000)
            res = uc.reg_read(UC_ARM_REG_R0)
            results.append(res)
            df54_calls.append(cur_df54)

        assert results[0] == results[1], f"ui_func_002dbc2c mismatch ret: {results[0]} != {results[1]}"
        assert df54_calls[0] == df54_calls[1], f"ui_func_002dbc2c mismatch df54: {df54_calls[0]} != {df54_calls[1]}"

    print("  ui_func_002dbc2c: PASS (all cases match)")

# ---------------------------------------------------------------------------
# Test 3: ui_func_002e3c68 (0x002E3C68)
# ---------------------------------------------------------------------------
def test_002e3c68(out: Path):
    print("Testing ui_func_002e3c68 (0x002E3C68)...")
    comp, relocs = compile_function("ui_func_002e3c68", out)
    orig_bytes = load_original_bytes(0x002E3C68, 264)

    CALL_96F60 = 0x00296F60
    CALL_49BAC = 0x00249BAC
    CALL_49B54 = 0x00249B54
    CALL_93C98 = 0x00293C98
    CALL_49B0C = 0x00249B0C
    CALL_8DF54 = 0x0028DF54

    BASE_CTX = 0x10090000
    UNIT_TABLE = 0x100A0000
    EXTRA_UNIT = 0x100B0000

    syms = {
        "engine_func_00296f60": CALL_96F60,
        "ui_func_00249bac": CALL_49BAC,
        "func_00249b54": CALL_49B54,
        "ui_func_00293c98": CALL_93C98,
        "battle_func_00249b0c": CALL_49B0C,
        "battle_func_0028df54": CALL_8DF54,
    }
    staged_compiled = stage_body(comp, relocs, 0x002E3C68, syms, "ui_func_002e3c68")

    stub_ret = struct.pack("<I", 0xe12fff1e) # bx lr

    test_cases = [
        # (bit_idx, unit_flags, extra_flag, extra_flags)
        (3, 1 << 3, 0, 0),       # bit 3 set -> 1
        (3, 1 << 2, 0, 0),       # bit 3 not set -> 0
        (4, 1 << 2, 1, 1 << 4),  # extra unit has bit 4 -> 1
        (4, 1 << 2, 1, 1 << 2),  # extra unit does not have bit 4 -> 0
    ]

    for bit_idx, u_flags, extra_flg, e_flags in test_cases:
        results = []
        df54_calls = []

        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002E3C68, code_bytes)

            for fn in (CALL_96F60, CALL_49BAC, CALL_49B54, CALL_93C98, CALL_49B0C, CALL_8DF54):
                uc.mem_write(fn, stub_ret)

            def hook_96f60(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                if r0 == 0:
                    uc.reg_write(UC_ARM_REG_R0, bit_idx)
                else:
                    uc.reg_write(UC_ARM_REG_R0, 0)
            uc.hook_add(1, hook_96f60, None, CALL_96F60, CALL_96F60 + 4)

            def hook_49b54(uc, addr, size, ud):
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                uc.mem_write(r1, struct.pack("<I", 0))
                uc.mem_write(r2, struct.pack("<I", 1))
            uc.hook_add(1, hook_49b54, None, CALL_49B54, CALL_49B54 + 4)

            def hook_93c98(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, BASE_CTX)
            uc.hook_add(1, hook_93c98, None, CALL_93C98, CALL_93C98 + 4)

            def hook_49b0c(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, EXTRA_UNIT)
            uc.hook_add(1, hook_49b0c, None, CALL_49B0C, CALL_49B0C + 4)

            cur_df54 = []
            def hook_8df54(uc, addr, size, ud):
                cur_df54.append(uc.reg_read(UC_ARM_REG_R0))
            uc.hook_add(1, hook_8df54, None, CALL_8DF54, CALL_8DF54 + 4)

            uc.mem_write(BASE_CTX + 0x1FC0, struct.pack("<I", UNIT_TABLE))
            uc.mem_write(BASE_CTX + 0x49C5, struct.pack("<B", extra_flg))

            # Unit 0
            uc.mem_write(UNIT_TABLE, struct.pack("<I", 1))
            uc.mem_write(UNIT_TABLE + 0x1C6, struct.pack("<H", u_flags))

            # Extra Unit
            uc.mem_write(EXTRA_UNIT + 0x1C6, struct.pack("<H", e_flags))

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)

            uc.emu_start(0x002E3C68, 0xF0000000, timeout=2000000)
            res = uc.reg_read(UC_ARM_REG_R0)
            results.append(res)
            df54_calls.append(cur_df54)

        assert results[0] == results[1], f"ui_func_002e3c68 mismatch ret: {results[0]} != {results[1]}"
        assert df54_calls[0] == df54_calls[1], f"ui_func_002e3c68 mismatch df54: {df54_calls[0]} != {df54_calls[1]}"

    print("  ui_func_002e3c68: PASS (all cases match)")

# ---------------------------------------------------------------------------
# Test 4: camp_func_002dc738 (0x002DC738)
# ---------------------------------------------------------------------------
def test_002dc738(out: Path):
    print("Testing camp_func_002dc738 (0x002DC738)...")
    comp, relocs = compile_function("camp_func_002dc738", out)
    orig_bytes = load_original_bytes(0x002DC738, 264)

    CALL_B9364 = 0x002B9364
    TABLE_PTR = 0x0043DD68
    BASE_ADDR = 0x10090000

    syms = {
        "camp_func_002b9364": CALL_B9364,
    }
    staged_compiled = stage_body(comp, relocs, 0x002DC738, syms, "camp_func_002dc738")

    stub_ret = struct.pack("<I", 0xe12fff1e) # bx lr
    NODE_BASE = 0x100A0000

    # Node descriptors:
    # id -> (field_0, field_2, field_3)
    node_data = {
        10: (100, 10, 5),
        20: (200, 20, 5),
        30: (300, 10, 8),
        40: (150, 10, 5),
    }

    test_cases = [
        # (w_a, w_b)
        # Case 1: different field_2: id 10 (f2=10) vs id 20 (f2=20)
        (10, 20),
        # Case 2: same field_2, different field_3: id 10 (f3=5) vs id 30 (f3=8)
        (10, 30),
        # Case 3: same field_2, same field_3, different field_0: id 10 (f0=100) vs id 40 (f0=150)
        (10, 40),
        # Case 4: tie on primary, tie-break on secondary ((w >> 15) & 0x7FFF)
        (10 | (20 << 15), 10 | (10 << 15)),
        # Case 5: identical in both
        (10 | (20 << 15), 10 | (20 << 15)),
    ]

    ITEM_A = 0x100B0000
    ITEM_B = 0x100B0010

    for w_a, w_b in test_cases:
        results = []

        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002DC738, code_bytes)
            uc.mem_write(CALL_B9364, stub_ret)

            # Map table pointer at 0x0043DD68
            uc.mem_write(TABLE_PTR, struct.pack("<I", BASE_ADDR))

            # Slot 0 is item_a, Slot 1 is item_b
            uc.mem_write(ITEM_A, struct.pack("<H", 0))
            uc.mem_write(ITEM_B, struct.pack("<H", 1))

            # Store words in table: slot 0 at base + 0*8 + 0x1390, slot 1 at base + 1*8 + 0x1390
            uc.mem_write(BASE_ADDR + 0 * 8 + 0x1390, struct.pack("<I", w_a))
            uc.mem_write(BASE_ADDR + 1 * 8 + 0x1390, struct.pack("<I", w_b))

            # Populate nodes
            for nid, (f0, f2, f3) in node_data.items():
                p = NODE_BASE + nid * 16
                uc.mem_write(p + 0, struct.pack("<H", f0))
                uc.mem_write(p + 2, struct.pack("<B", f2))
                uc.mem_write(p + 3, struct.pack("<B", f3))

            def hook_b9364(uc, addr, size, ud):
                nid = uc.reg_read(UC_ARM_REG_R0)
                uc.reg_write(UC_ARM_REG_R0, NODE_BASE + nid * 16)
            uc.hook_add(1, hook_b9364, None, CALL_B9364, CALL_B9364 + 4)

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)
            uc.reg_write(UC_ARM_REG_R0, ITEM_A)
            uc.reg_write(UC_ARM_REG_R1, ITEM_B)

            uc.emu_start(0x002DC738, 0xF0000000, timeout=2000000)
            res = uc.reg_read(UC_ARM_REG_R0)
            # Normalize to 32-bit signed
            if res >= 0x80000000:
                res -= 0x100000000
            results.append(res)

        assert results[0] == results[1], f"camp_func_002dc738 mismatch: {results[0]} != {results[1]} for case {(hex(w_a), hex(w_b))}"

    print("  camp_func_002dc738: PASS (all cases match)")

# ---------------------------------------------------------------------------
# Test 5: ui_func_002e0b50 (0x002E0B50)
# ---------------------------------------------------------------------------
def test_002e0b50(out: Path):
    print("Testing ui_func_002e0b50 (0x002E0B50)...")
    comp, relocs = compile_function("ui_func_002e0b50", out)
    orig_bytes = load_original_bytes(0x002E0B50, 260)

    CALL_C0B94 = 0x002C0B94
    STATE_ADDR = 0x0044E0F8
    CTX_ADDR = 0x10090000

    syms = {
        "ui_func_002c0b94": CALL_C0B94,
    }
    staged_compiled = stage_body(comp, relocs, 0x002E0B50, syms, "ui_func_002e0b50")

    stub_ret = struct.pack("<I", 0xe12fff1e) # bx lr

    test_cases = [
        # (ctx_null, state_flag, ctx_flag)
        (False, 1, 0), # state_flag != 0 -> copies state to ctx, ctx_flag = 1, state_flag = 0
        (False, 0, 1), # state_flag == 0, ctx_flag != 0 -> copies ctx to state
        (False, 0, 0), # state_flag == 0, ctx_flag == 0 -> copies state to ctx, ctx_flag = 1
        (True, 1, 0),  # ctx == null -> no-op
    ]

    for ctx_null, s_flag, c_flag in test_cases:
        state_after = []
        ctx_after = []

        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002E0B50, code_bytes)
            uc.mem_write(CALL_C0B94, stub_ret)

            def hook_c0b94(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, 0 if ctx_null else CTX_ADDR)
            uc.hook_add(1, hook_c0b94, None, CALL_C0B94, CALL_C0B94 + 4)

            # Setup state at 0x0044E0F8
            uc.mem_write(STATE_ADDR, b"\x11\x22\x33\x44" + bytes([s_flag]))

            # Setup ctx at CTX_ADDR
            uc.mem_write(CTX_ADDR + 0x24B7C, b"\xAA\xBB\xCC\xDD" + bytes([c_flag]))

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)

            uc.emu_start(0x002E0B50, 0xF0000000, timeout=2000000)
            state_after.append(uc.mem_read(STATE_ADDR, 5))
            if not ctx_null:
                ctx_after.append(uc.mem_read(CTX_ADDR + 0x24B7C, 5))
            else:
                ctx_after.append(b"")

        assert state_after[0] == state_after[1], f"ui_func_002e0b50 mismatch state: {state_after[0]} != {state_after[1]}"
        assert ctx_after[0] == ctx_after[1], f"ui_func_002e0b50 mismatch ctx: {ctx_after[0]} != {ctx_after[1]}"

    print("  ui_func_002e0b50: PASS (all cases match)")


def main():
    print("Running Batch 32 C Part 8 differential tests...")
    out_dir = ROOT / "build"
    out_dir.mkdir(exist_ok=True)

    test_002dbd58(out_dir)
    test_002dbc2c(out_dir)
    test_002e3c68(out_dir)
    test_002dc738(out_dir)
    test_002e0b50(out_dir)

    print("\nALL BATCH 32 C PART 8 TESTS PASSED!")

if __name__ == "__main__":
    main()
