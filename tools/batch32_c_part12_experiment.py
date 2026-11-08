#!/usr/bin/env python3
"""Differential test runner for leaf_batch32_c Part 12 candidates against code.bin.

Tests:
  - 0x002b626c: engine_func_002b626c (336 B)
  - 0x002b6c80: func_002b6c80 (276 B)
  - 0x002c4460: engine_func_002c4460 (320 B)
  - 0x002ec0a4: ui_func_002ec0a4 (276 B)
  - 0x002ef890: camp_func_002ef890 (284 B)
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

BUILD_DIR = ROOT / "build" / "batch32_c_part12"

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

CALL_140DAC = 0x00140DAC
CALL_140D40 = 0x00140D40
CALL_2B06A0 = 0x002B06A0
CALL_2BF460 = 0x002BF460
CALL_2BF6D0 = 0x002BF6D0
CALL_2B0908 = 0x002B0908
CALL_2C0AC8 = 0x002C0AC8
CALL_28DC54 = 0x0028DC54
CALL_BTNHELP = 0x0028D974
CALL_2972E8 = 0x002972E8
CALL_247C64 = 0x00247C64
CALL_1EDC04 = 0x001EDC04
CALL_193B44 = 0x00193B44
CALL_291BE8 = 0x00291BE8
CALL_1A1E6C = 0x001A1E6C
CALL_291A5C = 0x00291A5C
CALL_2874E4 = 0x002874E4

BASE_SYMS = {
    "func_00140dac": CALL_140DAC,
    "func_00140d40": CALL_140D40,
    "func_002b06a0": CALL_2B06A0,
    "ui_func_002bf460": CALL_2BF460,
    "camp_func_002bf6d0": CALL_2BF6D0,
    "func_002b0908": CALL_2B0908,
    "ui_func_002c0ac8": CALL_2C0AC8,
    "camp_func_0028dc54": CALL_28DC54,
    "ButtonHelp_Init": CALL_BTNHELP,
    "ui_func_002972e8": CALL_2972E8,
    "SaveLoad_Thread_func_00247c64": CALL_247C64,
    "script_vm_func_001edc04": CALL_1EDC04,
    "camp_func_00193b44": CALL_193B44,
    "script_vm_func_00291be8": CALL_291BE8,
    "camp_func_001a1e6c": CALL_1A1E6C,
    "script_vm_func_00291a5c": CALL_291A5C,
    "engine_func_002874e4": CALL_2874E4,
}

stub_ret = struct.pack("<I", 0xE12FFF1E) # bx lr


def test_engine_func_002b626c():
    print("Testing engine_func_002b626c (0x002B626C)...")
    orig_code = load_original_bytes(0x002B626C, 336)
    comp, relocs = compile_function("engine_func_002b626c")
    comp_code = stage_body(comp, relocs, 0x002B626C, BASE_SYMS, "engine_func_002b626c")

    SRC_ADDR = 0x00320000
    DST_ADDR = 0x00330000

    test_patterns = [
        bytes([(i * 7 + 3) & 0xFF for i in range(256)]),
        bytes([0xFF for _ in range(256)]),
        bytes([0x00 for _ in range(256)]),
        bytes([i for i in range(256)]),
    ]

    for pat in test_patterns:
        results = []
        dst_mem = []

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002B626C, code_bytes)

            uc.mem_write(SRC_ADDR, pat)
            uc.mem_write(DST_ADDR, b"\x00" * 256)

            uc.reg_write(UC_ARM_REG_R0, SRC_ADDR)
            uc.reg_write(UC_ARM_REG_R1, DST_ADDR)
            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, 0x002FFFF0)
            uc.mem_write(0x002FFFF0, stub_ret)

            uc.emu_start(0x002B626C, 0x002FFFF0, timeout=2000000)
            ret_r0 = uc.reg_read(UC_ARM_REG_R0)
            results.append(ret_r0)
            dst_mem.append(uc.mem_read(DST_ADDR, 160))

        assert results[0] == results[1], f"Return mismatch: orig={results[0]} comp={results[1]}"
        assert dst_mem[0] == dst_mem[1], f"Memory mismatch"
    print("  engine_func_002b626c: PASS (all cases match)")


def test_func_002b6c80():
    print("Testing func_002b6c80 (0x002B6C80)...")
    orig_code = load_original_bytes(0x002B6C80, 276)
    comp, relocs = compile_function("func_002b6c80")
    comp_code = stage_body(comp, relocs, 0x002B6C80, BASE_SYMS, "func_002b6c80")

    GLOBAL_PTR_LOC = 0x00433158
    GLOBAL_OBJ = 0x00320000

    test_cases = [
        # tc 0: id < 0 -> early return
        {"id": -1, "arg1": 10, "arg2": 20, "arg3": 30, "dac_ret": 0},
        # tc 1: func_00140dac returns 1 -> calls func_00140d40
        {"id": 5, "arg1": 10, "arg2": 20, "arg3": 30, "dac_ret": 1},
        # tc 2: func_00140dac returns 0, id = 0x15 (< 0x200) -> calls func_002b06a0 with res=0
        {"id": 0x15, "arg1": 10, "arg2": 20, "arg3": 30, "dac_ret": 0},
        # tc 3: func_00140dac returns 0, id = 0x215 (>= 0x200) -> calls func_002b06a0 with res=3000
        {"id": 0x215, "arg1": 100, "arg2": 200, "arg3": 300, "dac_ret": 0},
    ]

    for tc in test_cases:
        calls_d40 = []
        calls_6a0 = []

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002B6C80, code_bytes)
            for fn in BASE_SYMS.values():
                uc.mem_write(fn, stub_ret)

            def hook_140dac(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, tc["dac_ret"])
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_140dac, begin=CALL_140DAC, end=CALL_140DAC)

            called_d40 = []
            def hook_140d40(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                sp = uc.reg_read(UC_ARM_REG_SP)
                sp0 = struct.unpack("<I", uc.mem_read(sp, 4))[0]
                called_d40.append((r0, r1, r2, r3, sp0))
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_140d40, begin=CALL_140D40, end=CALL_140D40)

            called_6a0 = []
            def hook_2b06a0(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                sp = uc.reg_read(UC_ARM_REG_SP)
                sp0, sp4, sp8 = struct.unpack("<III", uc.mem_read(sp, 12))
                rect = struct.unpack("<4i", uc.mem_read(sp8, 16))
                called_6a0.append((r0, r1, r2, r3, sp0, sp4, rect))
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2b06a0, begin=CALL_2B06A0, end=CALL_2B06A0)

            uc.mem_write(GLOBAL_PTR_LOC, struct.pack("<I", GLOBAL_OBJ))

            uc.reg_write(UC_ARM_REG_R0, tc["id"])
            uc.reg_write(UC_ARM_REG_R1, tc["arg1"])
            uc.reg_write(UC_ARM_REG_R2, tc["arg2"])
            uc.reg_write(UC_ARM_REG_R3, tc["arg3"])
            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, 0x002FFFF0)
            uc.mem_write(0x002FFFF0, stub_ret)

            uc.emu_start(0x002B6C80, 0x002FFFF0, timeout=2000000)
            calls_d40.append(list(called_d40))
            calls_6a0.append(list(called_6a0))

        assert calls_d40[0] == calls_d40[1], f"calls_d40 mismatch: orig={calls_d40[0]} comp={calls_d40[1]} tc={tc}"
        assert calls_6a0[0] == calls_6a0[1], f"calls_6a0 mismatch: orig={calls_6a0[0]} comp={calls_6a0[1]} tc={tc}"
    print("  func_002b6c80: PASS (all cases match)")


def test_engine_func_002c4460():
    print("Testing engine_func_002c4460 (0x002C4460)...")
    orig_code = load_original_bytes(0x002C4460, 320)
    comp, relocs = compile_function("engine_func_002c4460")
    comp_code = stage_body(comp, relocs, 0x002C4460, BASE_SYMS, "engine_func_002c4460")

    TABLE_LOC = 0x004E3CF4
    TABLE_BASE = 0x00320000
    NODE_A = 0x00340000
    NODE_B = 0x00350000
    OLD_PARENT = 0x00360000

    test_cases = [
        # tc 0: reparent node B (key2) to node A (key1). Node B previously had OLD_PARENT.
        {"key1": (1 << 20) | 0x10, "key2": (2 << 20) | 0x20, "has_old_parent": True, "old_is_first": True},
        # tc 1: node B had old parent, but is second child.
        {"key1": (1 << 20) | 0x10, "key2": (2 << 20) | 0x20, "has_old_parent": True, "old_is_first": False},
        # tc 2: node B had no parent initially.
        {"key1": (1 << 20) | 0x10, "key2": (2 << 20) | 0x20, "has_old_parent": False, "old_is_first": False},
    ]

    NODE_SIBLING = 0x00370000

    for tc in test_cases:
        mem_dumps = []

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002C4460, code_bytes)

            # Table pointer at TABLE_LOC
            uc.mem_write(TABLE_LOC, struct.pack("<I", TABLE_BASE))
            # Zero table
            uc.mem_write(TABLE_BASE, b"\x00" * 0x1000)

            # Bucket for key1: hash = 1 -> index 2 (offset 8)
            uc.mem_write(TABLE_BASE + 8, struct.pack("<I", NODE_A))
            # Node A: id at +0x24
            uc.mem_write(NODE_A, b"\x00" * 0x80)
            uc.mem_write(NODE_A + 0x24, struct.pack("<I", 0x10))

            # Bucket for key2: hash = 2 -> index 4 (offset 16)
            uc.mem_write(TABLE_BASE + 16, struct.pack("<I", NODE_B))
            # Node B: id at +0x24
            uc.mem_write(NODE_B, b"\x00" * 0x80)
            uc.mem_write(NODE_B + 0x24, struct.pack("<I", 0x20))

            # Old parent setup
            uc.mem_write(OLD_PARENT, b"\x00" * 0x80)
            uc.mem_write(NODE_SIBLING, b"\x00" * 0x80)

            if tc["has_old_parent"]:
                uc.mem_write(NODE_B + 0x54, struct.pack("<I", OLD_PARENT))
                if tc["old_is_first"]:
                    uc.mem_write(OLD_PARENT + 0x58, struct.pack("<I", NODE_B))
                    uc.mem_write(NODE_B + 0x5C, struct.pack("<I", NODE_SIBLING))
                else:
                    uc.mem_write(OLD_PARENT + 0x58, struct.pack("<I", NODE_SIBLING))
                    uc.mem_write(NODE_SIBLING + 0x5C, struct.pack("<I", NODE_B))

            uc.reg_write(UC_ARM_REG_R0, tc["key1"])
            uc.reg_write(UC_ARM_REG_R1, tc["key2"])
            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, 0x002FFFF0)
            uc.mem_write(0x002FFFF0, stub_ret)

            uc.emu_start(0x002C4460, 0x002FFFF0, timeout=2000000)

            dump = {
                "node_a_child": uc.mem_read(NODE_A + 0x58, 4),
                "node_b_parent": uc.mem_read(NODE_B + 0x54, 4),
                "node_b_sibling": uc.mem_read(NODE_B + 0x5C, 4),
                "old_parent_child": uc.mem_read(OLD_PARENT + 0x58, 4),
            }
            mem_dumps.append(dump)

        assert mem_dumps[0] == mem_dumps[1], f"Memory mismatch: orig={mem_dumps[0]} comp={mem_dumps[1]} tc={tc}"
    print("  engine_func_002c4460: PASS (all cases match)")


def test_ui_func_002ec0a4():
    print("Testing ui_func_002ec0a4 (0x002EC0A4)...")
    orig_code = load_original_bytes(0x002EC0A4, 276)
    comp, relocs = compile_function("ui_func_002ec0a4")
    comp_code = stage_body(comp, relocs, 0x002EC0A4, BASE_SYMS, "ui_func_002ec0a4")

    CTX_OBJ = 0x00320000
    NODE_OBJ = 0x00340000
    ENTRY_OBJ = 0x00350000

    test_cases = [
        # tc 0: r7_count <= 3 -> early exit
        {"r1_off": 10, "r2_val": 50, "r3": 0, "r4": 0, "r5": 0, "r6_scale": 2, "r7_count": 3},
        # tc 1: r7_count = 5 (rem_steps = 2), r3=1, r4=0, r5=1
        {"r1_off": 20, "r2_val": 100, "r3": 1, "r4": 0, "r5": 1, "r6_scale": 3, "r7_count": 5},
        # tc 2: r7_count = 6 (rem_steps = 3), r3=0, r4=1, r5=0
        {"r1_off": 0, "r2_val": 30, "r3": 0, "r4": 1, "r5": 0, "r6_scale": -1, "r7_count": 6},
    ]

    for tc in test_cases:
        calls_460 = []
        calls_908 = []

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002EC0A4, code_bytes)
            for fn in BASE_SYMS.values():
                uc.mem_write(fn, stub_ret)

            called_460 = []
            def hook_2bf460(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                sp = uc.reg_read(UC_ARM_REG_SP)
                sp0, sp4 = struct.unpack("<II", uc.mem_read(sp, 8))
                called_460.append((r0, r1, r2, r3, sp0, sp4))
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2bf460, begin=CALL_2BF460, end=CALL_2BF460)

            def hook_2bf6d0(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, NODE_OBJ)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2bf6d0, begin=CALL_2BF6D0, end=CALL_2BF6D0)

            called_908 = []
            def hook_2b0908(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                sp = uc.reg_read(UC_ARM_REG_SP)
                sp0, sp4, sp8, spC = struct.unpack("<IIII", uc.mem_read(sp, 16))
                called_908.append((r0, r1, r2, r3, sp0, sp4, sp8, spC))
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2b0908, begin=CALL_2B0908, end=CALL_2B0908)

            # Memory setup:
            # CTX_OBJ: offset 4 has base_ptr
            uc.mem_write(CTX_OBJ + 4, struct.pack("<I", 0x00330000))
            # NODE_OBJ: offset 0x0C has ENTRY_OBJ pointer
            uc.mem_write(NODE_OBJ + 0x0C, struct.pack("<I", ENTRY_OBJ))
            # ENTRY_OBJ: s16 at offset 0 (r3_val), s16 at offset 2 (r1_val)
            uc.mem_write(ENTRY_OBJ, struct.pack("<hh", 15, 240)) # 240 / 12 = 20

            # Push 5 stack arguments: arg 4, arg 5, arg 6 (pad), arg 7 (scale), arg 8 (count)
            sp_init = STACK_TOP - 0x14
            uc.mem_write(sp_init, struct.pack("<IIIiI", tc["r4"], tc["r5"], 0, tc["r6_scale"], tc["r7_count"]))

            uc.reg_write(UC_ARM_REG_R0, CTX_OBJ)
            uc.reg_write(UC_ARM_REG_R1, tc["r1_off"])
            uc.reg_write(UC_ARM_REG_R2, tc["r2_val"])
            uc.reg_write(UC_ARM_REG_R3, tc["r3"])
            uc.reg_write(UC_ARM_REG_SP, sp_init)
            uc.reg_write(UC_ARM_REG_LR, 0x002FFFF0)
            uc.mem_write(0x002FFFF0, stub_ret)

            uc.emu_start(0x002EC0A4, 0x002FFFF0, timeout=2000000)
            calls_460.append(list(called_460))
            calls_908.append(list(called_908))

        assert calls_460[0] == calls_460[1], f"calls_460 mismatch: orig={calls_460[0]} comp={calls_460[1]} tc={tc}"
        assert calls_908[0] == calls_908[1], f"calls_908 mismatch: orig={calls_908[0]} comp={calls_908[1]} tc={tc}"
    print("  ui_func_002ec0a4: PASS (all cases match)")


def test_camp_func_002ef890():
    print("Testing camp_func_002ef890 (0x002EF890)...")
    orig_code = load_original_bytes(0x002EF890, 284)
    comp, relocs = compile_function("camp_func_002ef890")
    comp_code = stage_body(comp, relocs, 0x002EF890, BASE_SYMS, "camp_func_002ef890")

    CTX_R4 = 0x00320000
    STRUCT_R5 = 0x0043E2F0

    test_cases = [
        # tc 0: state = 8 -> initialize and transition to state 9, return 0
        {"state": 8, "vm_res": 0, "cnt_init": 0, "sub_init": 0, "camp_res": 0},
        # tc 1: state = 9, vm returns 1 -> transition to state 10, return 0
        {"state": 9, "vm_res": 1, "cnt_init": 0, "sub_init": 0, "camp_res": 0},
        # tc 2: state = 9, vm returns 0, cnt < 7 -> increment cnt, return 0
        {"state": 9, "vm_res": 0, "cnt_init": 3, "sub_init": 1, "camp_res": 0},
        # tc 3: state = 9, vm returns 0, cnt reaches 8 -> increment sub, return 0
        {"state": 9, "vm_res": 0, "cnt_init": 7, "sub_init": 2, "camp_res": 0},
        # tc 4: state = 10 -> finish transition, return -1
        {"state": 10, "vm_res": 0, "cnt_init": 0, "sub_init": 0, "camp_res": 1},
        # tc 5: state = 5 (unhandled) -> return 0
        {"state": 5, "vm_res": 0, "cnt_init": 0, "sub_init": 0, "camp_res": 0},
    ]

    for tc in test_cases:
        results = []
        r4_states = []
        r5_dumps = []

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002EF890, code_bytes)
            for fn in BASE_SYMS.values():
                uc.mem_write(fn, stub_ret)

            def hook_2c0ac8(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, CTX_R4)
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_2c0ac8, begin=CALL_2C0AC8, end=CALL_2C0AC8)

            def hook_1edc04(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, tc["vm_res"])
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_1edc04, begin=CALL_1EDC04, end=CALL_1EDC04)

            def hook_193b44(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, tc["camp_res"])
            uc.hook_add(unicorn.UC_HOOK_CODE, hook_193b44, begin=CALL_193B44, end=CALL_193B44)

            # Memory setup:
            uc.mem_write(CTX_R4 + 4, struct.pack("<I", tc["state"]))

            uc.mem_write(STRUCT_R5, b"\x00" * 32)
            uc.mem_write(STRUCT_R5 + 6, struct.pack("<H", tc["sub_init"]))
            uc.mem_write(STRUCT_R5 + 8, struct.pack("<I", tc["cnt_init"]))

            uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc.reg_write(UC_ARM_REG_LR, 0x002FFFF0)
            uc.mem_write(0x002FFFF0, stub_ret)

            uc.emu_start(0x002EF890, 0x002FFFF0, timeout=2000000)
            ret_r0 = uc.reg_read(UC_ARM_REG_R0)
            if ret_r0 >= 0x80000000:
                ret_r0 -= 0x100000000
            results.append(ret_r0)

            final_state = struct.unpack("<I", uc.mem_read(CTX_R4 + 4, 4))[0]
            r4_states.append(final_state)
            r5_dump = uc.mem_read(STRUCT_R5, 16)
            r5_dumps.append(r5_dump)

        assert results[0] == results[1], f"Return mismatch: orig={results[0]} comp={results[1]} tc={tc}"
        assert r4_states[0] == r4_states[1], f"r4_states mismatch: orig={r4_states[0]} comp={r4_states[1]} tc={tc}"
        assert r5_dumps[0] == r5_dumps[1], f"r5_dumps mismatch: orig={r5_dumps[0]} comp={r5_dumps[1]} tc={tc}"
    print("  camp_func_002ef890: PASS (all cases match)")


def main():
    print("Running Batch 32 C Part 12 differential tests...")
    test_engine_func_002b626c()
    test_func_002b6c80()
    test_engine_func_002c4460()
    test_ui_func_002ec0a4()
    test_camp_func_002ef890()
    print("\nALL BATCH 32 C PART 12 TESTS PASSED!")

if __name__ == "__main__":
    main()
