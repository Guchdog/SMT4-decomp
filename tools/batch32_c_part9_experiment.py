#!/usr/bin/env python3
"""
Batch 32 C Part 9 differential verification runner:
  - engine_func_002c6f7c (0x002C6F7C, 264 B)
  - engine_func_002d13d4 (0x002D13D4, 260 B)
  - engine_func_002dcd68 (0x002DCD68, 240 B)
  - effParticle_func_002e7b44 (0x002E7B44, 236 B)
  - ui_func_002f077c (0x002F077C, 268 B)
"""

import os
import struct
import subprocess
from pathlib import Path
import struct
import subprocess
import sys

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

ROOT = Path(__file__).resolve().parent.parent
CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "engine" / "leaf_batch32_c.cpp"
BUILD_DIR = ROOT / "build" / "batch32_c_part9"

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
    return uc

def test_engine_func_002c6f7c():
    print("Testing engine_func_002c6f7c (0x002C6F7C)...")
    orig_code = load_original_bytes(0x002C6F7C, 264)
    comp, relocs = compile_function("engine_func_002c6f7c")

    CALL_24C60C = 0x0024C60C
    CALL_1D2058 = 0x001D2058
    CALL_24C5EC = 0x0024C5EC
    CALL_2C34A4 = 0x002C34A4
    CALL_2C3B48 = 0x002C3B48
    CALL_28CA7C = 0x0028CA7C
    CALL_24C5DC = 0x0024C5DC
    CALL_28CABC = 0x0028CABC

    syms = {
        "engine_func_0024c60c": CALL_24C60C,
        "engine_func_001d2058": CALL_1D2058,
        "engine_func_0024c5ec": CALL_24C5EC,
        "engine_func_002c34a4": CALL_2C34A4,
        "engine_func_002c3b48": CALL_2C3B48,
        "engine_func_0028ca7c": CALL_28CA7C,
        "engine_func_0024c5dc": CALL_24C5DC,
        "AsdEffectTexture_func_0028cabc": CALL_28CABC,
    }
    comp_code = stage_body(comp, relocs, 0x002C6F7C, syms, "engine_func_002c6f7c")

    DESC_PTR = 0x00320000
    TARGET_PTR = 0x00330000
    BUF_PTR = 0x00340000
    TABLE_BASE = 0x00472480

    stub_ret = struct.pack("<I", 0xE12FFF1E) # bx lr

    test_cases = [
        {"res_ec": 0, "table_flag": 1, "mode": 1},
        {"res_ec": 0x00350000, "table_flag": 0, "mode": 1},
        {"res_ec": 0x00350000, "table_flag": 1, "mode": 1},
        {"res_ec": 0x00350000, "table_flag": 1, "mode": 4},
        {"res_ec": 0x00350000, "table_flag": 1, "mode": 9},
        {"res_ec": 0x00350000, "table_flag": 1, "mode": 0},
    ]

    for tc in test_cases:
        results = []
        target_field28 = []
        buf_contents = []

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002C6F7C, code_bytes)
            for fn in syms.values():
                uc.mem_write(fn, stub_ret)

            def hook_24c60c(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, 0x1111)
            uc.hook_add(UC_HOOK_CODE, hook_24c60c, None, CALL_24C60C, CALL_24C60C + 4)

            def hook_1d2058(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, TARGET_PTR)
            uc.hook_add(UC_HOOK_CODE, hook_1d2058, None, CALL_1D2058, CALL_1D2058 + 4)

            def hook_24c5ec(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, tc["res_ec"])
            uc.hook_add(UC_HOOK_CODE, hook_24c5ec, None, CALL_24C5EC, CALL_24C5EC + 4)

            def hook_2c34a4(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, BUF_PTR)
            uc.hook_add(UC_HOOK_CODE, hook_2c34a4, None, CALL_2C34A4, CALL_2C34A4 + 4)

            def hook_28ca7c(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, 0xAAAA1111)
            uc.hook_add(UC_HOOK_CODE, hook_28ca7c, None, CALL_28CA7C, CALL_28CA7C + 4)

            def hook_24c5dc(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, 0xBBBB4444)
            uc.hook_add(UC_HOOK_CODE, hook_24c5dc, None, CALL_24C5DC, CALL_24C5DC + 4)

            def hook_28cabc(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, 0xCCCC9999)
            uc.hook_add(UC_HOOK_CODE, hook_28cabc, None, CALL_28CABC, CALL_28CABC + 4)

            # Setup memory structures
            uc.mem_write(DESC_PTR, b"\x00" * 0x40)
            uc.mem_write(DESC_PTR + 0x0C, struct.pack("<H", 0x1234))
            uc.mem_write(DESC_PTR + 0x1C, struct.pack("<H", tc["mode"]))

            uc.mem_write(TARGET_PTR, b"\x00" * 0x40)
            uc.mem_write(TARGET_PTR + 0x18, struct.pack("<I", 2)) # table index 2

            # table entry 2 at TABLE_BASE + 2 * 24
            uc.mem_write(TABLE_BASE + 2 * 24 + 0x10, struct.pack("<B", tc["table_flag"]))

            if tc["res_ec"] != 0:
                uc.mem_write(tc["res_ec"], struct.pack("<H", 0x4321))

            uc.mem_write(BUF_PTR, b"\x00" * 16)

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_R0, DESC_PTR)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)

            uc.emu_start(0x002C6F7C, 0xF0000000, timeout=2000000)
            res = uc.reg_read(UC_ARM_REG_R0)
            results.append(res)
            target_field28.append(struct.unpack("<I", uc.mem_read(TARGET_PTR + 0x28, 4))[0])
            buf_contents.append(bytes(uc.mem_read(BUF_PTR, 12)))

        assert results[0] == results[1], f"engine_func_002c6f7c ret mismatch: {results[0]:08x} vs {results[1]:08x}"
        assert target_field28[0] == target_field28[1], f"engine_func_002c6f7c field28 mismatch: {target_field28[0]:08x} vs {target_field28[1]:08x}"
        assert buf_contents[0] == buf_contents[1], f"engine_func_002c6f7c buf mismatch: {buf_contents[0].hex()} vs {buf_contents[1].hex()}"

    print("  engine_func_002c6f7c: PASS (all cases match)")

def test_engine_func_002d13d4():
    print("Testing engine_func_002d13d4 (0x002D13D4)...")
    orig_code = load_original_bytes(0x002D13D4, 260)
    comp, relocs = compile_function("engine_func_002d13d4")

    CALL_207334 = 0x00207334
    syms = {"effGeometry_func_00207334": CALL_207334}
    comp_code = stage_body(comp, relocs, 0x002D13D4, syms, "engine_func_002d13d4")

    RES_PTR = 0x00320000
    DESC_PTR = 0x00321000
    DST_BUF = 0x00322000
    SRC_BUF = 0x00325000

    stub_ret = struct.pack("<I", 0xE12FFF1E)

    test_cases = [
        {"arg0": 0, "arg1": 2, "arg2": 3, "arg3": 4},
        {"arg0": 1, "arg1": 2, "arg2": 3, "arg3": 4},
        {"arg0": 2, "arg1": 3, "arg2": 1, "arg3": 5},
        {"arg0": 3, "arg1": 1, "arg2": 4, "arg3": 2},
    ]

    for tc in test_cases:
        results = []
        dst_dumps = []

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002D13D4, code_bytes)
            uc.mem_write(CALL_207334, stub_ret)

            def hook_207334(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, RES_PTR)
            uc.hook_add(UC_HOOK_CODE, hook_207334, None, CALL_207334, CALL_207334 + 4)

            # Setup descriptor
            uc.mem_write(RES_PTR, struct.pack("<I", DESC_PTR))
            uc.mem_write(DESC_PTR + 0x48, struct.pack("<I", DST_BUF))
            uc.mem_write(DST_BUF, b"\x00" * 0x2000)

            # Setup src buffer with predictable halfwords
            src_words = [i * 3 + 1 for i in range(128)]
            uc.mem_write(SRC_BUF, struct.pack(f"<{len(src_words)}H", *src_words))

            sp = STACK_BASE + STACK_SIZE - 0x1000
            # Stack args for caller: [sp, #0] is arg4 (SRC_BUF), [sp, #4] is arg5 (0x1234)
            uc.mem_write(sp, struct.pack("<II", SRC_BUF, 0x1234))

            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_R0, tc["arg0"])
            uc.reg_write(UC_ARM_REG_R1, tc["arg1"])
            uc.reg_write(UC_ARM_REG_R2, tc["arg2"])
            uc.reg_write(UC_ARM_REG_R3, tc["arg3"])
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)

            uc.emu_start(0x002D13D4, 0xF0000000, timeout=2000000)
            res = uc.reg_read(UC_ARM_REG_R0)
            results.append(res)
            dst_dumps.append(bytes(uc.mem_read(DST_BUF, 0x1000)))

        assert results[0] == results[1], f"engine_func_002d13d4 ret mismatch: {results[0]:08x} vs {results[1]:08x}"
        assert dst_dumps[0] == dst_dumps[1], f"engine_func_002d13d4 dst mismatch!"

    print("  engine_func_002d13d4: PASS (all cases match)")

def test_engine_func_002dcd68():
    print("Testing engine_func_002dcd68 (0x002DCD68)...")
    orig_code = load_original_bytes(0x002DCD68, 240)
    comp, relocs = compile_function("engine_func_002dcd68")

    CALL_2B47CC = 0x002B47CC
    CALL_288AD4 = 0x00288AD4
    syms = {
        "engine_func_002b47cc": CALL_2B47CC,
        "func_00288ad4": CALL_288AD4,
    }
    comp_code = stage_body(comp, relocs, 0x002DCD68, syms, "engine_func_002dcd68")

    stub_ret = struct.pack("<I", 0xE12FFF1E)

    OBJ_A = 0x00320000
    OBJ_B = 0x00330000
    ARG_A = 0x00340000
    ARG_B = 0x00340004

    # Test cases:
    # 1. Best idx diff
    # 2. Equal best idx, cmp_val diff
    # 3. Equal best idx, cmp_val == 0, field_98 diff
    # 4. Completely equal
    test_cases = [
        # tc 0: obj_a highest at i=1, obj_b highest at i=3
        {
            "a_74": [0x0400, 0x1400, 0x0800, 0, 0, 0, 0, 0],
            "b_74": [0x0400, 0x0800, 0x0400, 0x1800, 0, 0, 0, 0],
            "a_98": 10, "b_98": 10
        },
        # tc 1: both highest at i=2, but a has larger val
        {
            "a_74": [0, 0, 0x2000, 0, 0, 0, 0, 0],
            "b_74": [0, 0, 0x1000, 0, 0, 0, 0, 0],
            "a_98": 10, "b_98": 10
        },
        # tc 2: both identical 74 table, differing 98
        {
            "a_74": [0x400] * 8,
            "b_74": [0x400] * 8,
            "a_98": 50, "b_98": 20
        },
        # tc 3: completely identical
        {
            "a_74": [0x800] * 8,
            "b_74": [0x800] * 8,
            "a_98": 100, "b_98": 100
        },
    ]

    for tc in test_cases:
        results = []
        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002DCD68, code_bytes)
            for fn in syms.values():
                uc.mem_write(fn, stub_ret)

            def hook_2b47cc(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                if r0 == 0x10:
                    uc.reg_write(UC_ARM_REG_R0, OBJ_A)
                else:
                    uc.reg_write(UC_ARM_REG_R0, OBJ_B)
            uc.hook_add(UC_HOOK_CODE, hook_2b47cc, None, CALL_2B47CC, CALL_2B47CC + 4)

            def hook_288ad4(uc, addr, size, ud):
                # Signed comparison: return 1 if a < b, -1 if a > b, 0 if equal
                a = uc.reg_read(UC_ARM_REG_R0)
                b = uc.reg_read(UC_ARM_REG_R1)
                if a & 0x80000000: a -= 0x100000000
                if b & 0x80000000: b -= 0x100000000
                if a < b:
                    uc.reg_write(UC_ARM_REG_R0, 1)
                elif a > b:
                    uc.reg_write(UC_ARM_REG_R0, 0xFFFFFFFF)
                else:
                    uc.reg_write(UC_ARM_REG_R0, 0)
            uc.hook_add(UC_HOOK_CODE, hook_288ad4, None, CALL_288AD4, CALL_288AD4 + 4)

            # Global 0x00402688
            uc.mem_write(0x00402688, struct.pack("<II", 18, 18))

            uc.mem_write(ARG_A, struct.pack("<H", 0x10))
            uc.mem_write(ARG_B, struct.pack("<H", 0x20))

            uc.mem_write(OBJ_A, b"\x00" * 0x100)
            uc.mem_write(OBJ_B, b"\x00" * 0x100)

            uc.mem_write(OBJ_A + 0x74, struct.pack("<8h", *tc["a_74"]))
            uc.mem_write(OBJ_B + 0x74, struct.pack("<8h", *tc["b_74"]))
            uc.mem_write(OBJ_A + 0x98, struct.pack("<H", tc["a_98"]))
            uc.mem_write(OBJ_B + 0x98, struct.pack("<H", tc["b_98"]))

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_R0, ARG_A)
            uc.reg_write(UC_ARM_REG_R1, ARG_B)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)

            uc.emu_start(0x002DCD68, 0xF0000000, timeout=2000000)
            res = uc.reg_read(UC_ARM_REG_R0)
            if res & 0x80000000:
                res -= 0x100000000
            results.append(res)

        assert results[0] == results[1], f"engine_func_002dcd68 mismatch: {results[0]} vs {results[1]}"

    print("  engine_func_002dcd68: PASS (all cases match)")

def test_effParticle_func_002e7b44():
    print("Testing effParticle_func_002e7b44 (0x002E7B44)...")
    orig_code = load_original_bytes(0x002E7B44, 236)
    comp, relocs = compile_function("effParticle_func_002e7b44")

    CALL_2C2430 = 0x002C2430
    CALL_2C4360 = 0x002C4360
    CALL_2C34A4 = 0x002C34A4
    CALL_2A51DC = 0x002A51DC
    CALL_2490E0 = 0x002490E0

    syms = {
        "engine_func_002c2430": CALL_2C2430,
        "engine_func_002c4360": CALL_2C4360,
        "engine_func_002c34a4": CALL_2C34A4,
        "effParts_func_002a51dc": CALL_2A51DC,
        "effParts_func_002490e0": CALL_2490E0,
    }
    comp_code = stage_body(comp, relocs, 0x002E7B44, syms, "effParticle_func_002e7b44")

    stub_ret = struct.pack("<I", 0xE12FFF1E)

    SELF_PTR = 0x00320000
    OLD_BUF = 0x00330000
    NEW_BUF = 0x00340000
    F4C_PTR = 0x00350000

    test_cases = [
        {"has_f4c": False, "count": 0, "has_old": False},
        {"has_f4c": False, "count": 3, "has_old": True},
        {"has_f4c": True, "count": 1, "has_old": False},
        {"has_f4c": True, "count": 4, "has_old": True},
    ]

    for tc in test_cases:
        freed = []
        cleaned = []
        self_f3c = []
        self_f40 = []
        new_buf_dump = []

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002E7B44, code_bytes)
            for fn in syms.values():
                uc.mem_write(fn, stub_ret)

            cur_clean = []
            def hook_2c2430(uc, addr, size, ud):
                cur_clean.append(uc.reg_read(UC_ARM_REG_R0))
            uc.hook_add(UC_HOOK_CODE, hook_2c2430, None, CALL_2C2430, CALL_2C2430 + 4)

            cur_free = []
            def hook_2c4360(uc, addr, size, ud):
                cur_free.append(uc.reg_read(UC_ARM_REG_R0))
            uc.hook_add(UC_HOOK_CODE, hook_2c4360, None, CALL_2C4360, CALL_2C4360 + 4)

            def hook_2c34a4(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, NEW_BUF)
            uc.hook_add(UC_HOOK_CODE, hook_2c34a4, None, CALL_2C34A4, CALL_2C34A4 + 4)

            def hook_2a51dc(uc, addr, size, ud):
                uc.reg_write(UC_ARM_REG_R0, 0x1000)
            uc.hook_add(UC_HOOK_CODE, hook_2a51dc, None, CALL_2A51DC, CALL_2A51DC + 4)

            clone_idx = [1]
            def hook_2490e0(uc, addr, size, ud):
                val = 0x1000 + clone_idx[0]
                clone_idx[0] += 1
                uc.reg_write(UC_ARM_REG_R0, val)
            uc.hook_add(UC_HOOK_CODE, hook_2490e0, None, CALL_2490E0, CALL_2490E0 + 4)

            uc.mem_write(SELF_PTR, b"\x00" * 0x100)
            uc.mem_write(NEW_BUF, b"\x00" * 0x100)

            if tc["has_f4c"]:
                uc.mem_write(F4C_PTR, b"\x00" * 16)
                uc.mem_write(F4C_PTR + 8, struct.pack("<I", tc["count"]))
                uc.mem_write(SELF_PTR + 0x4C, struct.pack("<I", F4C_PTR))
            else:
                uc.mem_write(SELF_PTR, struct.pack("<I", tc["count"]))
                uc.mem_write(SELF_PTR + 0x4C, struct.pack("<I", 0))

            if tc["has_old"]:
                uc.mem_write(OLD_BUF, struct.pack("<4I", 0x11, 0x22, 0x33, 0x44))
                uc.mem_write(SELF_PTR + 0x40, struct.pack("<I", OLD_BUF))
                uc.mem_write(SELF_PTR + 0x3C, struct.pack("<I", OLD_BUF))
            else:
                uc.mem_write(SELF_PTR + 0x40, struct.pack("<I", 0))
                uc.mem_write(SELF_PTR + 0x3C, struct.pack("<I", 0))

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_R0, SELF_PTR)
            uc.reg_write(UC_ARM_REG_R1, 0x9999)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)

            uc.emu_start(0x002E7B44, 0xF0000000, timeout=2000000)
            freed.append(cur_free)
            cleaned.append(cur_clean)
            self_f3c.append(struct.unpack("<I", uc.mem_read(SELF_PTR + 0x3C, 4))[0])
            self_f40.append(struct.unpack("<I", uc.mem_read(SELF_PTR + 0x40, 4))[0])
            new_buf_dump.append(bytes(uc.mem_read(NEW_BUF, 16)))

        assert freed[0] == freed[1], f"effParticle_func_002e7b44 free mismatch: {freed[0]} vs {freed[1]}"
        assert cleaned[0] == cleaned[1], f"effParticle_func_002e7b44 clean mismatch: {cleaned[0]} vs {cleaned[1]}"
        assert self_f3c[0] == self_f3c[1], f"effParticle_func_002e7b44 f3c mismatch: {self_f3c[0]} vs {self_f3c[1]}"
        assert self_f40[0] == self_f40[1], f"effParticle_func_002e7b44 f40 mismatch: {self_f40[0]} vs {self_f40[1]}"
        assert new_buf_dump[0] == new_buf_dump[1], f"effParticle_func_002e7b44 buf mismatch!"

    print("  effParticle_func_002e7b44: PASS (all cases match)")

def test_ui_func_002f077c():
    print("Testing ui_func_002f077c (0x002F077C)...")
    orig_code = load_original_bytes(0x002F077C, 268)
    comp, relocs = compile_function("ui_func_002f077c")

    CALL_96F60 = 0x00296F60
    CALL_49BAC = 0x00249BAC
    CALL_49B54 = 0x00249B54
    CALL_93C98 = 0x00293C98
    CALL_49B0C = 0x00249B0C
    CALL_8DF54 = 0x0028DF54

    syms = {
        "engine_func_00296f60": CALL_96F60,
        "ui_func_00249bac": CALL_49BAC,
        "func_00249b54": CALL_49B54,
        "ui_func_00293c98": CALL_93C98,
        "battle_func_00249b0c": CALL_49B0C,
        "battle_func_0028df54": CALL_8DF54,
    }
    comp_code = stage_body(comp, relocs, 0x002F077C, syms, "ui_func_002f077c")

    stub_ret = struct.pack("<I", 0xE12FFF1E)

    BASE_CTX = 0x00320000
    UNIT_TABLE = 0x00330000
    EXTRA_UNIT = 0x00360000

    test_cases = [
        # tc 0: empty table, extra 0 -> 8df54(0)
        {"bit": 3, "st": 0, "cnt": 0, "u_flags": 1, "u_f1c6": 0, "extra_flg": 0, "extra_f1c6": 0},
        # tc 1: unit matches bit 3 (1<<3 = 8) -> 8df54(1)
        {"bit": 3, "st": 0, "cnt": 2, "u_flags": 1, "u_f1c6": 8, "extra_flg": 0, "extra_f1c6": 0},
        # tc 2: unit has flag 0x10 (inactive) -> skips -> 8df54(0)
        {"bit": 3, "st": 0, "cnt": 2, "u_flags": 0x11, "u_f1c6": 8, "extra_flg": 0, "extra_f1c6": 0},
        # tc 3: table doesn't match, extra unit matches bit 3 -> 8df54(1)
        {"bit": 3, "st": 0, "cnt": 1, "u_flags": 1, "u_f1c6": 0, "extra_flg": 1, "extra_f1c6": 8},
        # tc 4: table doesn't match, extra unit active but doesn't match -> 8df54(0)
        {"bit": 3, "st": 0, "cnt": 1, "u_flags": 1, "u_f1c6": 0, "extra_flg": 1, "extra_f1c6": 0},
    ]

    for tc in test_cases:
        results = []
        df54_calls = []

        for code_bytes in (orig_code, comp_code):
            uc = create_emulator()
            uc.mem_write(0x002F077C, code_bytes)
            for fn in syms.values():
                uc.mem_write(fn, stub_ret)

            def hook_96f60(uc, addr, size, ud):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                if r0 == 0:
                    uc.reg_write(UC_ARM_REG_R0, tc["bit"])
                else:
                    uc.reg_write(UC_ARM_REG_R0, 0)
            uc.hook_add(UC_HOOK_CODE, hook_96f60, None, CALL_96F60, CALL_96F60 + 4)

            def hook_49b54(uc, addr, size, ud):
                # r1 = out_start, r2 = out_count (or in 2-arg r0=out_start, r1=out_count)
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                # check which registers hold valid stack pointers in STACK_BASE range
                if STACK_BASE <= r1 < STACK_BASE + STACK_SIZE and STACK_BASE <= r2 < STACK_BASE + STACK_SIZE:
                    uc.mem_write(r1, struct.pack("<I", tc["st"]))
                    uc.mem_write(r2, struct.pack("<I", tc["cnt"]))
                elif STACK_BASE <= r0 < STACK_BASE + STACK_SIZE and STACK_BASE <= r1 < STACK_BASE + STACK_SIZE:
                    uc.mem_write(r0, struct.pack("<I", tc["st"]))
                    uc.mem_write(r1, struct.pack("<I", tc["cnt"]))
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
            uc.mem_write(BASE_CTX + 0x49C5, struct.pack("<B", tc["extra_flg"]))

            uc.mem_write(UNIT_TABLE, b"\x00" * (648 * 4))
            uc.mem_write(UNIT_TABLE + 0 * 648, struct.pack("<I", tc["u_flags"]))
            uc.mem_write(UNIT_TABLE + 0 * 648 + 0x1C6, struct.pack("<H", tc["u_f1c6"]))

            uc.mem_write(EXTRA_UNIT, b"\x00" * 0x300)
            uc.mem_write(EXTRA_UNIT + 0x1C6, struct.pack("<H", tc["extra_f1c6"]))

            sp = STACK_BASE + STACK_SIZE - 0x1000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0xF0000000)

            uc.emu_start(0x002F077C, 0xF0000000, timeout=2000000)
            res = uc.reg_read(UC_ARM_REG_R0)
            results.append(res)
            df54_calls.append(cur_df54)

        assert results[0] == results[1], f"ui_func_002f077c ret mismatch: {results[0]} vs {results[1]}"
        assert df54_calls[0] == df54_calls[1], f"ui_func_002f077c df54 mismatch: {df54_calls[0]} vs {df54_calls[1]}"

    print("  ui_func_002f077c: PASS (all cases match)")

if __name__ == "__main__":
    print("Running Batch 32 C Part 9 differential tests...")
    test_engine_func_002c6f7c()
    test_engine_func_002d13d4()
    test_engine_func_002dcd68()
    test_effParticle_func_002e7b44()
    test_ui_func_002f077c()
    print("\nALL BATCH 32 C PART 9 TESTS PASSED!")
