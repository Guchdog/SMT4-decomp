#!/usr/bin/env python3
"""Differential test runner for leaf_batch32_c Part 11 candidates against code.bin.

Tests:
  - 0x002cfd24: engine_func_002cfd24 (256 B)
  - 0x002dc840: camp_func_002dc840 (300 B)
  - 0x002e4104: battle_func_002e4104 (304 B)
  - 0x002f0e94: ui_func_002f0e94 (272 B)
  - 0x002f12ec: engine_func_002f12ec (324 B)
"""

import struct
import sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.arm_const import *
import unicorn

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "engine" / "leaf_batch32_c.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STACK_BASE = 0x0FFF0000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

BUILD_DIR = ROOT / "build" / "batch32_c_part11"

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
CALL_A8A08 = 0x002A8A08
CALL_4BA9C = 0x0024BA9C
CALL_B9364 = 0x002B9364
CALL_7EB98 = 0x0027EB98
CALL_50960 = 0x00250960
CALL_553EC = 0x002553EC
CALL_50800 = 0x00250800
CALL_7E1A0 = 0x0027E1A0

BASE_SYMS = {
    "engine_func_00296f60": CALL_96F60,
    "ui_func_00249bac": CALL_49BAC,
    "func_00249b54": CALL_49B54,
    "ui_func_00293c98": CALL_93C98,
    "battle_func_00249b0c": CALL_49B0C,
    "battle_func_0028df54": CALL_8DF54,
    "camp_func_002a8a08": CALL_A8A08,
    "battle_func_0024ba9c": CALL_4BA9C,
    "camp_func_002b9364": CALL_B9364,
    "script_vm_func_0027eb98": CALL_7EB98,
    "func_00250960": CALL_50960,
    "battle_func_002553ec": CALL_553EC,
    "battle_func_00250800": CALL_50800,
    "battle_func_0027e1a0": CALL_7E1A0,
}

BASE_CTX = 0x00320000
UNIT_TABLE = 0x00330000
EXTRA_UNIT = 0x00360000
CAMP_DATA = 0x00370000
SORT_CTX = 0x0043DD68
GLOBAL_CTX = 0x0043427C

stub_ret = struct.pack("<I", 0xE12FFF1E) # bx lr

def test_ui_func_002f0e94():
    print("Testing ui_func_002f0e94 (0x002F0E94)...")
    orig_code = load_original_bytes(0x002F0E94, 272)
    comp, relocs = compile_function("ui_func_002f0e94")
    comp_code = stage_body(comp, relocs, 0x002F0E94, BASE_SYMS, "ui_func_002f0e94")

    test_cases = [
        # tc 0: sel=0, unit 0 val has (2 << 10). Match!
        {"sel": 0, "u0_val": (2 << 10) | 1, "u_flags": 1, "extra_active": 0, "extra_val": 0},
        # tc 1: sel=1, unit 0 val has (1 << 10). No match.
        {"sel": 1, "u0_val": (1 << 10) | 1, "u_flags": 1, "extra_active": 0, "extra_val": 0},
        # tc 2: sel=0, unit 0 has (2 << 10), but flags 0x11 (inactive) -> no match
        {"sel": 0, "u0_val": (2 << 10) | 1, "u_flags": 0x11, "extra_active": 0, "extra_val": 0},
        # tc 3: sel=0, unit 0 has (1 << 10), bonus unit has (2 << 10) -> Match!
        {"sel": 0, "u0_val": (1 << 10) | 1, "u_flags": 1, "extra_active": 1, "extra_val": (2 << 10) | 5},
        # tc 4: sel=0, unit 0 has (1 << 10), bonus unit has (3 << 10) -> No match
        {"sel": 0, "u0_val": (1 << 10) | 1, "u_flags": 1, "extra_active": 1, "extra_val": (3 << 10) | 5},
    ]

    for tc in test_cases:
        results = []
        df54_calls = []

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002F0E94, code_bytes)
            for fn in BASE_SYMS.values():
                uc.mem_write(fn, stub_ret)

            def hook_96f60(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                if r0 == 0:
                    uc.reg_write(UC_ARM_REG_R0, tc["sel"])
                else:
                    uc.reg_write(UC_ARM_REG_R0, 0)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_96f60, begin=CALL_96F60, end=CALL_96F60)

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
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_49b54, begin=CALL_49B54, end=CALL_49B54)

            def hook_93c98(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, BASE_CTX)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_93c98, begin=CALL_93C98, end=CALL_93C98)

            def hook_49b0c(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, EXTRA_UNIT)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_49b0c, begin=CALL_49B0C, end=CALL_49B0C)

            called_df54 = []
            def hook_8df54(uc, addr, size, ud):
                val = uc.reg_read(UC_ARM_REG_R0)
                called_df54.append(val)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_8df54, begin=CALL_8DF54, end=CALL_8DF54)

            # Setup memory structures
            uc.mem_write(BASE_CTX + 0x1FC0, struct.pack("<I", UNIT_TABLE))
            uc.mem_write(BASE_CTX + 0x49C5, struct.pack("<B", tc["extra_active"]))

            uc.mem_write(UNIT_TABLE, struct.pack("<I", tc["u_flags"]))
            uc.mem_write(UNIT_TABLE + 0x1F2 + tc["sel"] * 2, struct.pack("<H", tc["u0_val"]))

            uc.mem_write(EXTRA_UNIT + 0x1F2 + tc["sel"] * 2, struct.pack("<H", tc["extra_val"]))

            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, 0x002FFFF0)
            uc.mem_write(0x002FFFF0, stub_ret)

            uc.emu_start(0x002F0E94, 0x002FFFF0, timeout=2000000)
            ret_r0 = uc.reg_read(UC_ARM_REG_R0)
            results.append(ret_r0)
            df54_calls.append(list(called_df54))

        assert results[0] == results[1], f"Return mismatch: orig={results[0]} comp={results[1]} tc={tc}"
        assert df54_calls[0] == df54_calls[1], f"df54 call mismatch: orig={df54_calls[0]} comp={df54_calls[1]} tc={tc}"
    print("  ui_func_002f0e94: PASS (all cases match)")


def test_engine_func_002cfd24():
    print("Testing engine_func_002cfd24 (0x002CFD24)...")
    orig_code = load_original_bytes(0x002CFD24, 256)
    comp, relocs = compile_function("engine_func_002cfd24")
    comp_code = stage_body(comp, relocs, 0x002CFD24, BASE_SYMS, "engine_func_002cfd24")

    PTR_SLOTS = 0x00340000

    test_cases = [
        # tc 0: r4 < 0x6d -> early exit, no battle_func_0024ba9c
        {"r4": 0x60, "count1": 1, "free_slot": 0, "camp_target": 0, "camp_len": 4, "target_found_at": 2},
        # tc 1: r4 = 0x6d (target = 0). Slot 0 free, camp target 0 found at index 2
        {"r4": 0x6d, "count1": 1, "free_slot": 0, "camp_target": 0, "camp_len": 4, "target_found_at": 2},
        # tc 2: r4 = 0x70 (target = 3). Slot 1 free, camp target 3 found at index 0
        {"r4": 0x70, "count1": 2, "free_slot": 1, "camp_target": 3, "camp_len": 4, "target_found_at": 0},
        # tc 3: r4 = 0x75 (target = 8). Slot 0 free, camp target 8 not found -> r6 = -1
        {"r4": 0x75, "count1": 0, "free_slot": 0, "camp_target": 8, "camp_len": 4, "target_found_at": -1},
        # tc 4: count1 >= 4 -> early exit
        {"r4": 0x70, "count1": 4, "free_slot": 0, "camp_target": 3, "camp_len": 4, "target_found_at": 0},
    ]

    for tc in test_cases:
        results = []
        ba9c_calls = []

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002CFD24, code_bytes)
            for fn in BASE_SYMS.values():
                uc.mem_write(fn, stub_ret)

            def hook_96f60(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, tc["r4"])
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_96f60, begin=CALL_96F60, end=CALL_96F60)

            def hook_93c98(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, BASE_CTX)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_93c98, begin=CALL_93C98, end=CALL_93C98)

            def hook_a8a08(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, CAMP_DATA)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_a8a08, begin=CALL_A8A08, end=CALL_A8A08)

            called_ba9c = []
            def hook_4ba9c(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                sp = uc.reg_read(UC_ARM_REG_SP)
                sp0, sp4 = struct.unpack("<II", uc.mem_read(sp, 8))
                called_ba9c.append((r0, r1, r2, r3, sp0, sp4))
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_4ba9c, begin=CALL_4BA9C, end=CALL_4BA9C)

            # Setup memory structures
            uc.mem_write(BASE_CTX + 0x1FC4, struct.pack("<h", tc["count1"]))
            uc.mem_write(BASE_CTX + 0x1E98, struct.pack("<I", PTR_SLOTS))

            # Slots flags: 0x50 offset in each 276-byte entry
            for i in range(4):
                slot_flag = 0 if i == tc["free_slot"] else 1
                uc.mem_write(PTR_SLOTS + i * 276 + 0x50, struct.pack("<I", slot_flag))

            # Camp table at CAMP_DATA: length at 0x910B, entries at 0x90F0
            uc.mem_write(CAMP_DATA + 0x910B, struct.pack("<B", tc["camp_len"]))
            for i in range(tc["camp_len"]):
                val = tc["camp_target"] if i == tc["target_found_at"] else 0x7F
                uc.mem_write(CAMP_DATA + 0x90F0 + i, struct.pack("<b", val))

            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, 0x002FFFF0)
            uc.mem_write(0x002FFFF0, stub_ret)

            uc.emu_start(0x002CFD24, 0x002FFFF0, timeout=2000000)
            ret_r0 = uc.reg_read(UC_ARM_REG_R0)
            results.append(ret_r0)
            ba9c_calls.append(list(called_ba9c))

        assert results[0] == results[1], f"Return mismatch: orig={results[0]} comp={results[1]} tc={tc}"
        assert ba9c_calls[0] == ba9c_calls[1], f"ba9c mismatch: orig={ba9c_calls[0]} comp={ba9c_calls[1]} tc={tc}"
    print("  engine_func_002cfd24: PASS (all cases match)")


def test_camp_func_002dc840():
    print("Testing camp_func_002dc840 (0x002DC840)...")
    orig_code = load_original_bytes(0x002DC840, 300)
    comp, relocs = compile_function("camp_func_002dc840")
    comp_code = stage_body(comp, relocs, 0x002DC840, BASE_SYMS, "camp_func_002dc840")

    TABLE_BASE = 0x00380000
    NODE_A = 0x003A0000
    NODE_B = 0x003B0000
    NODE_A2 = 0x003C0000
    NODE_B2 = 0x003D0000

    test_cases = [
        # tc 0: val_b > val_a -> positive diff
        {"val_a": 100, "val_b": 200, "nb2": 0, "na2": 0, "na3": 0, "nb3": 0, "nb0": 0, "na0": 0},
        # tc 1: val_b < val_a -> negative diff
        {"val_a": 300, "val_b": 100, "nb2": 0, "na2": 0, "na3": 0, "nb3": 0, "nb0": 0, "na0": 0},
        # tc 2: val_b == val_a, node_b[2] != node_a[2]
        {"val_a": 100, "val_b": 100, "nb2": 5, "na2": 2, "na3": 0, "nb3": 0, "nb0": 0, "na0": 0},
        # tc 3: val_b == val_a, node[2] equal, node_a[3] != node_b[3]
        {"val_a": 100, "val_b": 100, "nb2": 5, "na2": 5, "na3": 10, "nb3": 2, "nb0": 0, "na0": 0},
        # tc 4: val_b == val_a, node[2] equal, node[3] equal, tie-break on node_b[0..1] - node_a[0..1]
        {"val_a": 100, "val_b": 100, "nb2": 5, "na2": 5, "na3": 2, "nb3": 2, "nb0": 50, "na0": 20},
    ]

    for tc in test_cases:
        results = []

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002DC840, code_bytes)
            for fn in BASE_SYMS.values():
                uc.mem_write(fn, stub_ret)

            def hook_b9364(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                if r0 == 1:
                    uc.reg_write(UC_ARM_REG_R0, NODE_A)
                elif r0 == 2:
                    uc.reg_write(UC_ARM_REG_R0, NODE_B)
                elif r0 == 3:
                    uc.reg_write(UC_ARM_REG_R0, NODE_A2)
                else:
                    uc.reg_write(UC_ARM_REG_R0, NODE_B2)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_b9364, begin=CALL_B9364, end=CALL_B9364)

            # Global pointer at SORT_CTX (0x0043DD68) points to TABLE_BASE
            uc.mem_write(SORT_CTX, struct.pack("<I", TABLE_BASE))

            # slot 0 and slot 1
            slot_a = 0
            slot_b = 1
            uc.mem_write(TABLE_BASE + slot_a * 4 + 0x78A0, struct.pack("<I", tc["val_a"]))
            uc.mem_write(TABLE_BASE + slot_b * 4 + 0x78A0, struct.pack("<I", tc["val_b"]))

            # w_a has id_a=1, id_a2=3; w_b has id_b=2, id_b2=4
            w_a = 1 | (3 << 15)
            w_b = 2 | (4 << 15)
            uc.mem_write(TABLE_BASE + slot_a * 8 + 0x1390, struct.pack("<I", w_a))
            uc.mem_write(TABLE_BASE + slot_b * 8 + 0x1390, struct.pack("<I", w_b))

            # Nodes: offset 0 (u16), offset 2 (u8), offset 3 (u8)
            uc.mem_write(NODE_A, struct.pack("<HBB", tc["na0"], tc["na2"], tc["na3"]))
            uc.mem_write(NODE_B, struct.pack("<HBB", tc["nb0"], tc["nb2"], tc["nb3"]))
            uc.mem_write(NODE_A2, struct.pack("<HBB", 1, 1, 1))
            uc.mem_write(NODE_B2, struct.pack("<HBB", 2, 1, 1))

            # Args: r0 = &slot_a, r1 = &slot_b
            arg_a = STACK_TOP - 0x20
            arg_b = STACK_TOP - 0x18
            uc.mem_write(arg_a, struct.pack("<H", slot_a))
            uc.mem_write(arg_b, struct.pack("<H", slot_b))

            uc.reg_write(UC_ARM_REG_R0, arg_a)
            uc.reg_write(UC_ARM_REG_R1, arg_b)
            uc.reg_write(UC_ARM_REG_SP, STACK_TOP - 0x40)
            uc.reg_write(UC_ARM_REG_LR, 0x002FFFF0)
            uc.mem_write(0x002FFFF0, stub_ret)

            uc.emu_start(0x002DC840, 0x002FFFF0, timeout=2000000)
            ret_r0 = uc.reg_read(UC_ARM_REG_R0)
            # Normalize signed 32-bit
            if ret_r0 >= 0x80000000:
                ret_r0 -= 0x100000000
            results.append(ret_r0)

        assert results[0] == results[1], f"Return mismatch: orig={results[0]} comp={results[1]} tc={tc}"
    print("  camp_func_002dc840: PASS (all cases match)")


def test_battle_func_002e4104():
    print("Testing battle_func_002e4104 (0x002E4104)...")
    orig_code = load_original_bytes(0x002E4104, 304)
    comp, relocs = compile_function("battle_func_002e4104")
    comp_code = stage_body(comp, relocs, 0x002E4104, BASE_SYMS, "battle_func_002e4104")

    TEST_UNIT = 0x00350000
    PTR_SLOTS = 0x00340000

    test_cases = [
        # tc 0: slot = -1 -> early return
        {"mult": 50, "stat_b6": 100, "stat_b4": 80, "slot": -1},
        # tc 1: slot = 0, mult = 50, stat_b6 = 100 -> scaled = 50
        {"mult": 50, "stat_b6": 100, "stat_b4": 80, "slot": 0},
        # tc 2: slot = 1, mult = 120, stat_b6 = 80 -> scaled = 96
        {"mult": 120, "stat_b6": 80, "stat_b4": 50, "slot": 1},
        # tc 3: slot = 2, mult = 0, stat_b6 = 50 -> scaled = 0
        {"mult": 0, "stat_b6": 50, "stat_b4": 30, "slot": 2},
    ]

    for tc in test_cases:
        results = []
        calls_553ec = []
        calls_50800 = []

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002E4104, code_bytes)
            for fn in BASE_SYMS.values():
                uc.mem_write(fn, stub_ret)

            def hook_96f60(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, tc["mult"])
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_96f60, begin=CALL_96F60, end=CALL_96F60)

            def hook_93c98(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, BASE_CTX)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_93c98, begin=CALL_93C98, end=CALL_93C98)

            def hook_49b0c(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, TEST_UNIT)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_49b0c, begin=CALL_49B0C, end=CALL_49B0C)

            def hook_7eb98(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, 0x12345678)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_7eb98, begin=CALL_7EB98, end=CALL_7EB98)

            called_553ec = []
            def hook_553ec(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                sp = uc.reg_read(UC_ARM_REG_SP)
                stack_words = struct.unpack("<21I", uc.mem_read(sp, 84))
                called_553ec.append((r0, r1, r2, r3, stack_words))
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_553ec, begin=CALL_553EC, end=CALL_553EC)

            called_50800 = []
            def hook_50800(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                sp = uc.reg_read(UC_ARM_REG_SP)
                sp0, sp4, sp8 = struct.unpack("<III", uc.mem_read(sp, 12))
                called_50800.append((r0, r1, r2, r3, sp0, sp4, sp8))
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_50800, begin=CALL_50800, end=CALL_50800)

            # Setup memory structures
            uc.mem_write(GLOBAL_CTX, struct.pack("<I", 0x00390000))
            uc.mem_write(BASE_CTX + 0x1E98, struct.pack("<I", PTR_SLOTS))

            # Unit at TEST_UNIT: offset 8 is slot (s16), unit + 0x100 + 0xB6 is stat_b6, + 0xB4 is stat_b4
            uc.mem_write(TEST_UNIT + 8, struct.pack("<h", tc["slot"]))
            uc.mem_write(TEST_UNIT + 0x100 + 0xB6, struct.pack("<h", tc["stat_b6"]))
            uc.mem_write(TEST_UNIT + 0x100 + 0xB4, struct.pack("<h", tc["stat_b4"]))

            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, 0x002FFFF0)
            uc.mem_write(0x002FFFF0, stub_ret)

            uc.emu_start(0x002E4104, 0x002FFFF0, timeout=2000000)
            ret_r0 = uc.reg_read(UC_ARM_REG_R0)
            results.append(ret_r0)
            calls_553ec.append(list(called_553ec))
            calls_50800.append(list(called_50800))

        assert results[0] == results[1], f"Return mismatch: orig={results[0]} comp={results[1]} tc={tc}"
        assert calls_553ec[0] == calls_553ec[1], f"calls_553ec mismatch: orig={calls_553ec[0]} comp={calls_553ec[1]} tc={tc}"
        assert calls_50800[0] == calls_50800[1], f"calls_50800 mismatch: orig={calls_50800[0]} comp={calls_50800[1]} tc={tc}"
    print("  battle_func_002e4104: PASS (all cases match)")


def test_engine_func_002f12ec():
    print("Testing engine_func_002f12ec (0x002F12EC)...")
    orig_code = load_original_bytes(0x002F12EC, 324)
    comp, relocs = compile_function("engine_func_002f12ec")
    comp_code = stage_body(comp, relocs, 0x002F12EC, BASE_SYMS, "engine_func_002f12ec")

    UNIT_REC = 0x00350000
    PTR_SLOTS = 0x00340000

    test_cases = [
        # tc 0: r4_arg = 1 (r6 = 0x3E0), flags_c6 = 0, stat_b6 = 100, stat_ba = 200, mults = (50, 25)
        {"r5": 50, "r7": 25, "r4": 1, "stat_b6": 100, "stat_ba": 200, "flags_c6": 0},
        # tc 1: r4_arg = 0 (r6 = 0), flags_c6 = 8, scaled1 = 5 (clamped to 1), scaled2 = 0 (becomes -1)
        {"r5": 50, "r7": 0, "r4": 0, "stat_b6": 100, "stat_ba": 200, "flags_c6": 8},
        # tc 2: r4_arg = -1 (r6 = 0), flags_c6 = 8, scaled1 = 1 (stays 1), scaled2 = -3 (stays -3)
        {"r5": 1, "r7": 3, "r4": -1, "stat_b6": 100, "stat_ba": -100, "flags_c6": 8},
        # tc 3: flags_c6 = 0, scaled1 = 0 (becomes -1), scaled2 = 50 (stays 50)
        {"r5": 0, "r7": 50, "r4": 2, "stat_b6": 100, "stat_ba": 100, "flags_c6": 0},
    ]

    for tc in test_cases:
        results = []
        calls_7e1a0 = []
        calls_50800 = []

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002F12EC, code_bytes)
            for fn in BASE_SYMS.values():
                uc.mem_write(fn, stub_ret)

            def hook_96f60(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                if r0 == 0:
                    uc.reg_write(UC_ARM_REG_R0, tc["r5"])
                elif r0 == 1:
                    uc.reg_write(UC_ARM_REG_R0, tc["r7"])
                else:
                    uc.reg_write(UC_ARM_REG_R0, tc["r4"])
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_96f60, begin=CALL_96F60, end=CALL_96F60)

            def hook_93c98(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, BASE_CTX)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_93c98, begin=CALL_93C98, end=CALL_93C98)

            def hook_7eb98(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, 0x87654321)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_7eb98, begin=CALL_7EB98, end=CALL_7EB98)

            called_7e1a0 = []
            def hook_7e1a0(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                sp = uc.reg_read(UC_ARM_REG_SP)
                stack_words = struct.unpack("<9I", uc.mem_read(sp, 36))
                called_7e1a0.append((r0, r1, r2, r3, stack_words))
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_7e1a0, begin=CALL_7E1A0, end=CALL_7E1A0)

            called_50800 = []
            def hook_50800(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                sp = uc.reg_read(UC_ARM_REG_SP)
                sp0, sp4, sp8 = struct.unpack("<III", uc.mem_read(sp, 12))
                called_50800.append((r0, r1, r2, r3, sp0, sp4, sp8))
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_50800, begin=CALL_50800, end=CALL_50800)

            # Setup memory structures
            uc.mem_write(GLOBAL_CTX, struct.pack("<I", 0x00390000))
            uc.mem_write(BASE_CTX + 0x1FC0, struct.pack("<I", UNIT_REC))
            uc.mem_write(BASE_CTX + 0x1E98, struct.pack("<I", PTR_SLOTS))

            # Unit record: at UNIT_REC + 0x100
            unit = UNIT_REC + 0x100
            uc.mem_write(unit + 0xB6, struct.pack("<h", tc["stat_b6"]))
            uc.mem_write(unit + 0xBA, struct.pack("<h", tc["stat_ba"]))
            uc.mem_write(unit + 0xC6, struct.pack("<H", tc["flags_c6"]))

            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, 0x002FFFF0)
            uc.mem_write(0x002FFFF0, stub_ret)

            uc.emu_start(0x002F12EC, 0x002FFFF0, timeout=2000000)
            ret_r0 = uc.reg_read(UC_ARM_REG_R0)
            results.append(ret_r0)
            calls_7e1a0.append(list(called_7e1a0))
            calls_50800.append(list(called_50800))

        assert results[0] == results[1], f"Return mismatch: orig={results[0]} comp={results[1]} tc={tc}"
        assert calls_7e1a0[0] == calls_7e1a0[1], f"calls_7e1a0 mismatch: orig={calls_7e1a0[0]} comp={calls_7e1a0[1]} tc={tc}"
        assert calls_50800[0] == calls_50800[1], f"calls_50800 mismatch: orig={calls_50800[0]} comp={calls_50800[1]} tc={tc}"
    print("  engine_func_002f12ec: PASS (all cases match)")


def main():
    print("Running Batch 32 C Part 11 differential tests...")
    test_ui_func_002f0e94()
    test_engine_func_002cfd24()
    test_camp_func_002dc840()
    test_battle_func_002e4104()
    test_engine_func_002f12ec()
    print("\nALL BATCH 32 C PART 11 TESTS PASSED!")

if __name__ == "__main__":
    main()
