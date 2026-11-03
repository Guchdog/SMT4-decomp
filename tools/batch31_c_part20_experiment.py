#!/usr/bin/env python3
"""Differential test for batch 31 C part 20 (Final batch: 100/100 complete):
- engine_func_002f6e70 (0x002F6E70, 152 B)
- engine_func_002f7694 (0x002F7694, 160 B)
- engine_func_002f7d30 (0x002F7D30, 164 B)
- engine_func_002feda4 (0x002FEDA4, 152 B)
- engine_func_002ff0e4 (0x002FF0E4, 156 B)
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
    UC_ARM_REG_R5,
    UC_ARM_REG_R6,
    UC_ARM_REG_R7,
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
SOURCE = ROOT / "src/engine/leaf_batch31_c.cpp"

with open(ORIG_BIN, "rb") as f:
    ORIG_DATA = f.read()

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS, COMPILED_ST_VALUES, RODATA_BYTES
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch31_c.o"
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

def test_002f6e70_and_002feda4(out: Path):
    print("Testing engine_func_002f6e70 & engine_func_002feda4...")
    comp_6e70, relocs_6e70 = compile_function("engine_func_002f6e70", out)
    comp_eda4, relocs_eda4 = compile_function("engine_func_002feda4", out)

    orig_6e70 = load_original_bytes(0x002F6E70, 152)
    orig_eda4 = load_original_bytes(0x002FEDA4, 152)

    STUB_296F60 = 0x00296F60
    STUB_293C98 = 0x00293C98
    STUB_28DF54 = 0x0028DF54

    # 0x00296F60: if r0 == 0 return 100 (target_id); else return 3 (bit_idx) -> bitmask = 1 << 3 = 8
    #   cmp r0, #0; moveq r0, #100; movne r0, #3; bx lr
    stub_296f60_code = struct.pack("<IIII", 0xe3500000, 0x03a00064, 0x13a00003, 0xe12fff1e)
    # 0x00293C98: returns 0x10010000
    stub_293c98_code = struct.pack("<III", 0xe59f0000, 0xe12fff1e, 0x10010000)
    # 0x0028DF54: writes r0 to 0x10029000
    stub_28df54_code = struct.pack("<IIII", 0xe59f1000, 0xe5810000, 0xe12fff1e, 0x10029000)

    syms_6e70 = {
        "engine_func_00296f60": STUB_296F60,
        "func_00293c98": STUB_293C98,
        "battle_func_0028df54": STUB_28DF54,
    }
    staged_6e70 = stage_body(comp_6e70, relocs_6e70, 0x002F6E70, syms_6e70, "engine_func_002f6e70")

    syms_eda4 = {
        "engine_func_00296f60": STUB_296F60,
        "func_00293c98": STUB_293C98,
        "battle_func_0028df54": STUB_28DF54,
    }
    staged_eda4 = stage_body(comp_eda4, relocs_eda4, 0x002FEDA4, syms_eda4, "engine_func_002feda4")

    # Scenarios:
    # 1. Match at slot 10 with bit 3 set in *(u16*)(record + 0x1C6) (e.g. 0x08) -> battle_func(1)
    # 2. Match at slot 10 with bit 3 clear (e.g. 0x04) -> continues, battle_func(0)
    # 3. No match at all -> battle_func(0)
    test_cases = [
        ("bit_set", 10, 0x08),
        ("bit_clear", 10, 0x04),
        ("no_match", -1, 0x08),
    ]

    for fn_name, addr, orig_b, comp_b in [
        ("engine_func_002f6e70", 0x002F6E70, orig_6e70, staged_6e70),
        ("engine_func_002feda4", 0x002FEDA4, orig_eda4, staged_eda4),
    ]:
        for tc_name, slot, val1c6 in test_cases:
            results = []
            for is_comp, code_bytes in [(False, orig_b), (True, comp_b)]:
                uc = create_emulator()
                uc.mem_write(addr, code_bytes)
                uc.mem_write(STUB_296F60, stub_296f60_code)
                uc.mem_write(STUB_293C98, stub_293c98_code)
                uc.mem_write(STUB_28DF54, stub_28df54_code)

                uc.mem_write(0x10029000, struct.pack("<I", 0xDEADBEEF))
                uc.mem_write(0x10010000, b"\x00" * 0x2000)
                uc.mem_write(0x10010000 + 0x1FC0, struct.pack("<I", 0x10030000))

                RECS_BASE = 0x10030000
                for i in range(110):
                    rec = bytearray(648)
                    if i == slot:
                        flags = 0x11
                        struct.pack_into("<I", rec, 0, flags)
                        struct.pack_into("<H", rec, 0xCE, 100) # id = 100
                        struct.pack_into("<H", rec, 0x1C6, val1c6)
                    else:
                        struct.pack_into("<I", rec, 0, 0)
                    uc.mem_write(RECS_BASE + i * 648, bytes(rec))

                sp = STACK_BASE + 0x8000
                uc.reg_write(UC_ARM_REG_SP, sp)
                uc.reg_write(UC_ARM_REG_LR, 0x00100000)

                uc.emu_start(addr, 0x00100000, count=10000)
                r0 = uc.reg_read(UC_ARM_REG_R0)
                called_val = struct.unpack("<I", uc.mem_read(0x10029000, 4))[0]
                results.append((r0, called_val))

            assert results[0] == results[1], f"Mismatch for {fn_name} {tc_name}: {results[0]} != {results[1]}"
        print(f"  {fn_name}: PASS (all cases match)")

def test_002f7694(out: Path):
    print("Testing engine_func_002f7694 (0x002F7694)...")
    comp, relocs = compile_function("engine_func_002f7694", out)
    orig_bytes = load_original_bytes(0x002F7694, 160)

    STUB_296F60 = 0x00296F60
    STUB_2B087C = 0x002B087C
    STUB_2C0BCC = 0x002C0BCC
    STUB_28DF54 = 0x0028DF54

    # 0x00296F60: returns id = 7
    stub_296f60_code = struct.pack("<II", 0xe3a00007, 0xe12fff1e)
    # 0x002B087C: returns entry at 0x10020000
    stub_2b087c_code = struct.pack("<III", 0xe59f0000, 0xe12fff1e, 0x10020000)
    # 0x002C0BCC: returns roll (e.g. returns 1 if r0 >= 1 else 0)
    #   cmp r0, #1; movge r0, #1; movlt r0, #0; bx lr
    stub_2c0bcc_code = struct.pack("<IIII", 0xe3500001, 0xa3a00001, 0xb3a00000, 0xe12fff1e)
    # 0x0028DF54: writes r0 to 0x10029000
    stub_28df54_code = struct.pack("<IIII", 0xe59f1000, 0xe5810000, 0xe12fff1e, 0x10029000)

    syms = {
        "engine_func_00296f60": STUB_296F60,
        "battle_func_002b087c": STUB_2B087C,
        "engine_func_002c0bcc": STUB_2C0BCC,
        "battle_func_0028df54": STUB_28DF54,
    }
    staged_compiled = stage_body(comp, relocs, 0x002F7694, syms, "engine_func_002f7694")

    # Scenarios:
    # 1. h0=10, h1=20, h2=30 (count=3, roll picks idx 1 -> 20)
    # 2. h0=0, h1=0, h2=0 (count=0 -> -1)
    # 3. h0=5, h1=0, h2=0 (count=1, roll picks idx 0 -> 5)
    test_cases = [
        ("three_items", 10, 20, 30),
        ("zero_items", 0, 0, 0),
        ("one_item", 5, 0, 0),
    ]

    for tc_name, h0, h1, h2 in test_cases:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002F7694, code_bytes)
            uc.mem_write(STUB_296F60, stub_296f60_code)
            uc.mem_write(STUB_2B087C, stub_2b087c_code)
            uc.mem_write(STUB_2C0BCC, stub_2c0bcc_code)
            uc.mem_write(STUB_28DF54, stub_28df54_code)

            uc.mem_write(0x10029000, struct.pack("<I", 0xDEADBEEF))
            entry_buf = bytearray(0x100)
            struct.pack_into("<H", entry_buf, 0x58, h0)
            struct.pack_into("<H", entry_buf, 0x5E, h1)
            struct.pack_into("<H", entry_buf, 0x64, h2)
            uc.mem_write(0x10020000, bytes(entry_buf))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)

            uc.emu_start(0x002F7694, 0x00100000, count=500)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            called_val = struct.unpack("<I", uc.mem_read(0x10029000, 4))[0]
            results.append((r0, called_val))

        assert results[0] == results[1], f"Mismatch for {tc_name}: {results[0]} != {results[1]}"
    print("  engine_func_002f7694: PASS (all cases match)")

def test_002f7d30(out: Path):
    print("Testing engine_func_002f7d30 (0x002F7D30)...")
    comp, relocs = compile_function("engine_func_002f7d30", out)
    orig_bytes = load_original_bytes(0x002F7D30, 164)

    STUB_296F60 = 0x00296F60
    STUB_293C98 = 0x00293C98
    STUB_29BF90 = 0x0029BF90
    STUB_28DF54 = 0x0028DF54

    # 0x00296F60: returns target_id = 77
    stub_296f60_code = struct.pack("<II", 0xe3a0004d, 0xe12fff1e)
    # 0x00293C98: returns 0x10010000
    stub_293c98_code = struct.pack("<III", 0xe59f0000, 0xe12fff1e, 0x10010000)
    # 0x0029BF90: fallback, returns 5 (if matching) or -1
    #   cmp r0, #77; moveq r0, #5; movne r0, #-1; bx lr
    stub_29bf90_code = struct.pack("<IIII", 0xe350004d, 0x03a00005, 0x13e00000, 0xe12fff1e)
    # 0x0028DF54: writes r0 to 0x10029000
    stub_28df54_code = struct.pack("<IIII", 0xe59f1000, 0xe5810000, 0xe12fff1e, 0x10029000)

    syms = {
        "engine_func_00296f60": STUB_296F60,
        "func_00293c98": STUB_293C98,
        "camp_func_0029bf90": STUB_29BF90,
        "battle_func_0028df54": STUB_28DF54,
    }
    staged_compiled = stage_body(comp, relocs, 0x002F7D30, syms, "engine_func_002f7d30")

    # Scenarios:
    # 1. Match in loop at slot 12: flags 0x09, s8=15, p27c points to obj with id=77 -> result = 15
    # 2. No match in loop, fallback returns 5 -> result = 5 + 109 = 114
    # 3. No match in loop, fallback returns -1 -> result = -1
    test_cases = [
        ("loop_match", 12, 15, True, 77),
        ("fallback_match", -1, 0, False, 77),
        ("total_fail", -1, 0, False, 999), # target_id mismatch in fallback
    ]

    for tc_name, slot, s8_val, has_ptr, sub_id in test_cases:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002F7D30, code_bytes)
            uc.mem_write(STUB_296F60, stub_296f60_code)
            uc.mem_write(STUB_293C98, stub_293c98_code)
            uc.mem_write(STUB_29BF90, stub_29bf90_code)
            uc.mem_write(STUB_28DF54, stub_28df54_code)

            uc.mem_write(0x10029000, struct.pack("<I", 0xDEADBEEF))
            uc.mem_write(0x10010000, b"\x00" * 0x2000)
            uc.mem_write(0x10010000 + 0x1FC0, struct.pack("<I", 0x10030000))

            # Sub-object at 0x10025000:
            # p27c + 0x46 = u16 sub_id
            uc.mem_write(0x10025000, b"\x00" * 0x100)
            uc.mem_write(0x10025046, struct.pack("<H", sub_id))

            RECS_BASE = 0x10030000
            for i in range(110):
                rec = bytearray(648)
                if i == slot:
                    flags = 0x09 # bit 0 and bit 3 set, bit 6 clear
                    struct.pack_into("<I", rec, 0, flags)
                    struct.pack_into("<h", rec, 8, s8_val)
                    if has_ptr:
                        struct.pack_into("<I", rec, 0x27C, 0x10025000)
                else:
                    struct.pack_into("<I", rec, 0, 0)
                uc.mem_write(RECS_BASE + i * 648, bytes(rec))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)

            uc.emu_start(0x002F7D30, 0x00100000, count=10000)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            called_val = struct.unpack("<I", uc.mem_read(0x10029000, 4))[0]
            results.append((r0, called_val))

        assert results[0] == results[1], f"Mismatch for {tc_name}: {results[0]} != {results[1]}"
    print("  engine_func_002f7d30: PASS (all cases match)")

def test_002ff0e4(out: Path):
    print("Testing engine_func_002ff0e4 (0x002FF0E4)...")
    comp, relocs = compile_function("engine_func_002ff0e4", out)
    orig_bytes = load_original_bytes(0x002FF0E4, 156)

    STUB_296F60 = 0x00296F60
    STUB_293C98 = 0x00293C98
    STUB_28DF54 = 0x0028DF54

    # 0x00296F60: if r0 == 0 return 50 (target_id); else return 2 (slot_idx)
    #   cmp r0, #0; moveq r0, #50; movne r0, #2; bx lr
    stub_296f60_code = struct.pack("<IIII", 0xe3500000, 0x03a00032, 0x13a00002, 0xe12fff1e)
    # 0x00293C98: returns 0x10010000
    stub_293c98_code = struct.pack("<III", 0xe59f0000, 0xe12fff1e, 0x10010000)
    # 0x0028DF54: writes r0 to 0x10029000
    stub_28df54_code = struct.pack("<IIII", 0xe59f1000, 0xe5810000, 0xe12fff1e, 0x10029000)

    syms = {
        "engine_func_00296f60": STUB_296F60,
        "func_00293c98": STUB_293C98,
        "battle_func_0028df54": STUB_28DF54,
    }
    staged_compiled = stage_body(comp, relocs, 0x002FF0E4, syms, "engine_func_002ff0e4")

    # Scenarios:
    # slot_idx is 2 -> offset is 0x1F2 + 2 * 2 = 0x1F6.
    # 1. Match at slot 8 with (val >> 10) == 2 (e.g. 2 << 10 = 0x0800) -> battle_func(1)
    # 2. Match at slot 8 with (val >> 10) != 2 (e.g. 1 << 10 = 0x0400) -> battle_func(0)
    # 3. No match -> battle_func(0)
    test_cases = [
        ("val_match", 8, (2 << 10) | 0x3F),
        ("val_mismatch", 8, (1 << 10) | 0x3F),
        ("no_match", -1, (2 << 10) | 0x3F),
    ]

    for tc_name, slot, val1f6 in test_cases:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002FF0E4, code_bytes)
            uc.mem_write(STUB_296F60, stub_296f60_code)
            uc.mem_write(STUB_293C98, stub_293c98_code)
            uc.mem_write(STUB_28DF54, stub_28df54_code)

            uc.mem_write(0x10029000, struct.pack("<I", 0xDEADBEEF))
            uc.mem_write(0x10010000, b"\x00" * 0x2000)
            uc.mem_write(0x10010000 + 0x1FC0, struct.pack("<I", 0x10030000))

            RECS_BASE = 0x10030000
            for i in range(110):
                rec = bytearray(648)
                if i == slot:
                    flags = 0x11
                    struct.pack_into("<I", rec, 0, flags)
                    struct.pack_into("<H", rec, 0xCE, 50) # id = 50
                    struct.pack_into("<H", rec, 0x1F6, val1f6)
                else:
                    struct.pack_into("<I", rec, 0, 0)
                uc.mem_write(RECS_BASE + i * 648, bytes(rec))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)

            uc.emu_start(0x002FF0E4, 0x00100000, count=10000)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            called_val = struct.unpack("<I", uc.mem_read(0x10029000, 4))[0]
            results.append((r0, called_val))

        assert results[0] == results[1], f"Mismatch for {tc_name}: {results[0]} != {results[1]}"
    print("  engine_func_002ff0e4: PASS (all cases match)")

def main():
    out = ROOT / "build"
    out.mkdir(parents=True, exist_ok=True)
    print("Running Part 20 differential tests...")
    test_002f6e70_and_002feda4(out)
    test_002f7694(out)
    test_002f7d30(out)
    test_002ff0e4(out)
    print("\nALL PART 20 TESTS PASSED!")

if __name__ == "__main__":
    main()
