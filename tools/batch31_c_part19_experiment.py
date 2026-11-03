#!/usr/bin/env python3
"""Differential test for batch 31 C part 19:
- ui_func_002eb300 (0x002EB300, 156 B)
- script_vm_func_002f0204 (0x002F0204, 180 B)
- engine_func_002f03d0 (0x002F03D0, 168 B)
- engine_func_002f0478 (0x002F0478, 168 B)
- script_vm_func_002f3acc (0x002F3ACC, 172 B)
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
    UC_ARM_REG_D0,
    UC_ARM_REG_D1,
    UC_ARM_REG_S0,
    UC_ARM_REG_S1,
    UC_ARM_REG_S2,
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

def test_002eb300(out: Path):
    print("Testing ui_func_002eb300 (0x002EB300)...")
    comp, relocs = compile_function("ui_func_002eb300", out)
    orig_bytes = load_original_bytes(0x002EB300, 156)

    # Callees:
    # ui_func_0029ec6c = 0x0029EC6C
    # ui_func_0027dd78 = 0x0027DD78
    # ui_func_0026330c = 0x0026330C
    STUB_29EC6C = 0x0029EC6C
    STUB_27DD78 = 0x0027DD78
    STUB_26330C = 0x0026330C

    # Implement stubs:
    # 0x0029EC6C: returns (r0 & 0x7F) + 5
    #   add r0, r0, #5; bx lr
    stub_29ec6c_code = struct.pack("<II", 0xe2800005, 0xe12fff1e)
    # 0x0027DD78: returns pointer 0x10025000
    #   ldr r0, =0x10025000; bx lr
    stub_27dd78_code = struct.pack("<III", 0xe59f0000, 0xe12fff1e, 0x10025000)
    # 0x0026330C: writes [0x11223344, 0x55667788] to [r0, #0]
    #   ldr r1, =0x11223344; str r1, [r0]; ldr r1, =0x55667788; str r1, [r0, #4]; bx lr
    stub_26330c_code = struct.pack("<IIIIIII",
        0xe59f1008, 0xe5801000, 0xe59f1004, 0xe5801004, 0xe12fff1e, 0x11223344, 0x55667788
    )

    syms = {
        "ui_func_0029ec6c": STUB_29EC6C,
        "ui_func_0027dd78": STUB_27DD78,
        "ui_func_0026330c": STUB_26330C,
    }
    staged_compiled = stage_body(comp, relocs, 0x002EB300, syms, "ui_func_002eb300")

    # Global pointer at 0x00439C60
    # *(u32*)0x00439C60 = 0x10020000
    # *(u32*)(0x10020000 + 4) = 0x10021000
    # Target table is at 0x10021000 + 4 = 0x10021004

    test_cases = [
        # (slot, vec3_data, arg2, b3..b8)
        (0, [10, 20, 30], 0x10, 1, 2, 3, 4, 5, 6),
        (1, [100, 200, 300], 0x25, 11, 12, 13, 14, 15, 16),
        (4, [0x11, 0x22, 0x33], 0x50, 21, 22, 23, 24, 25, 26),
        (5, [1, 2, 3], 0x60, 31, 32, 33, 34, 35, 36),  # slot >= 5, should no-op
        (10, [1, 2, 3], 0x70, 41, 42, 43, 44, 45, 46), # out of bounds, should no-op
    ]

    for slot, vec3_vals, arg2, b3, b4, b5, b6, b7, b8 in test_cases:
        results = []
        for is_compiled, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002EB300, code_bytes)
            uc.mem_write(STUB_29EC6C, stub_29ec6c_code)
            uc.mem_write(STUB_27DD78, stub_27dd78_code)
            uc.mem_write(STUB_26330C, stub_26330c_code)

            # Setup table
            uc.mem_write(0x00439C60, struct.pack("<I", 0x10020000))
            uc.mem_write(0x10020004, struct.pack("<I", 0x10021000))
            # Zero table memory
            uc.mem_write(0x10021000, b"\x00" * 0x100)

            # Setup vec3 on memory
            VEC3_ADDR = 0x10024000
            uc.mem_write(VEC3_ADDR, struct.pack("<III", *vec3_vals))

            sp = STACK_BASE + 0x8000
            # Push stack args (b4, b5, b6, b7, b8) at sp
            stack_args = struct.pack("<IIIII", b4, b5, b6, b7, b8)
            uc.mem_write(sp, stack_args)

            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, slot)
            uc.reg_write(UC_ARM_REG_R1, VEC3_ADDR)
            uc.reg_write(UC_ARM_REG_R2, arg2)
            uc.reg_write(UC_ARM_REG_R3, b3)

            uc.emu_start(0x002EB300, 0x00100000, count=500)
            table_state = uc.mem_read(0x10021000, 0x100)
            results.append(table_state)

        assert results[0] == results[1], f"Mismatch for slot {slot}: orig != comp"
    print("  ui_func_002eb300: PASS (all cases match)")

def test_002f0204(out: Path):
    print("Testing script_vm_func_002f0204 (0x002F0204)...")
    comp, relocs = compile_function("script_vm_func_002f0204", out)
    orig_bytes = load_original_bytes(0x002F0204, 180)

    # Callees:
    # engine_func_00296f60 = 0x00296F60
    # script_vm_func_0027eb98 = 0x0027EB98
    # func_00293c98 = 0x00293C98
    STUB_296F60 = 0x00296F60
    STUB_27EB98 = 0x0027EB98
    STUB_293C98 = 0x00293C98

    # Stubs:
    # 0x00296F60: returns 0x55 (r0)
    stub_296f60_code = struct.pack("<II", 0xe3a00055, 0xe12fff1e)
    # 0x0027EB98: returns pointer passed in r0 (or 0x10020000)
    #   ldr r0, =0x10020000; bx lr
    stub_27eb98_code = struct.pack("<III", 0xe59f0000, 0xe12fff1e, 0x10020000)
    # 0x00293C98: returns data base pointer 0x10010000
    #   ldr r0, =0x10010000; bx lr
    stub_293c98_code = struct.pack("<III", 0xe59f0000, 0xe12fff1e, 0x10010000)

    syms = {
        "engine_func_00296f60": STUB_296F60,
        "script_vm_func_0027eb98": STUB_27EB98,
        "func_00293c98": STUB_293C98,
    }
    staged_compiled = stage_body(comp, relocs, 0x002F0204, syms, "script_vm_func_002f0204")

    # Scenarios:
    # 1. Matching record at slot 4 (first slot)
    # 2. Matching record at slot 10
    # 3. No matching record (all have flag 1)
    scenarios = [
        ("first_match", 4),
        ("later_match", 10),
        ("no_match", -1),
    ]

    for name, match_slot in scenarios:
        results = []
        for is_compiled, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002F0204, code_bytes)
            uc.mem_write(STUB_296F60, stub_296f60_code)
            uc.mem_write(STUB_27EB98, stub_27eb98_code)
            uc.mem_write(STUB_293C98, stub_293c98_code)

            # Global at 0x0043427C -> 0x10020000
            uc.mem_write(0x0043427C, struct.pack("<I", 0x10020000))
            # Scene obj at 0x10020000:
            # scene + 0x28 -> sub_obj at 0x10025000
            uc.mem_write(0x10020000, b"\x00" * 0x100)
            uc.mem_write(0x10020028, struct.pack("<I", 0x10025000))
            uc.mem_write(0x10025000, b"\x00" * 0x200)

            # func_00293c98() returns 0x10010000
            # 0x10010000 + 0x1FC0 -> pointer to records at 0x10030000
            uc.mem_write(0x10010000, b"\x00" * 0x2000)
            uc.mem_write(0x10010000 + 0x1FC0, struct.pack("<I", 0x10030000))

            # Initialize 60 records of 648 bytes (0x10030000 to 0x1003A000)
            # Default flags: 0x01 (not matching)
            for i in range(60):
                flags = 0x00 if i == match_slot else 0x01
                uc.mem_write(0x10030000 + i * 648, struct.pack("<I", flags))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)

            uc.emu_start(0x002F0204, 0x00100000, count=5000)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            sub_val = uc.mem_read(0x1002514C, 2)
            comb_val = uc.mem_read(0x10011FD0, 8)
            scene_slots = uc.mem_read(0x10020038, 60)
            results.append((r0, sub_val, comb_val, scene_slots))

        assert results[0] == results[1], f"Mismatch for scenario {name}: {results[0]} != {results[1]}"
    print("  script_vm_func_002f0204: PASS (all cases match)")

def test_002f03d0_and_002f0478(out: Path):
    print("Testing engine_func_002f03d0 & engine_func_002f0478...")
    comp_03d0, relocs_03d0 = compile_function("engine_func_002f03d0", out)
    comp_0478, relocs_0478 = compile_function("engine_func_002f0478", out)

    orig_03d0 = load_original_bytes(0x002F03D0, 168)
    orig_0478 = load_original_bytes(0x002F0478, 168)

    # Callees:
    # engine_func_00296f60 = 0x00296F60
    # func_00293c98 = 0x00293C98
    # ui_func_002c615c = 0x002C615C
    # battle_func_0028df54 = 0x0028DF54
    STUB_296F60 = 0x00296F60
    STUB_293C98 = 0x00293C98
    STUB_2C615C = 0x002C615C
    STUB_28DF54 = 0x0028DF54

    # 0x00296F60: if r0 == 0 return 42 (target_id); else return 50 (threshold)
    #   cmp r0, #0; moveq r0, #42; movne r0, #50; bx lr
    stub_296f60_code = struct.pack("<IIII", 0xe3500000, 0x03a0002a, 0x13a00032, 0xe12fff1e)
    # 0x00293C98: returns 0x10010000
    stub_293c98_code = struct.pack("<III", 0xe59f0000, 0xe12fff1e, 0x10010000)
    # 0x002C615C: division r0 / r1
    #   sdiv if supported, or stub:
    #   cmp r1, #0; beq zero; mov r2, r0; mov r0, #0;
    #   Let's do simple subtract loop:
    #   mov r2, #0; loop: cmp r0, r1; blt done; sub r0, r0, r1; add r2, r2, #1; b loop; done: mov r0, r2; bx lr
    stub_2c615c_code = struct.pack("<IIIIIIII",
        0xe3a02000, # mov r2, #0
        0xe1500001, # cmp r0, r1
        0xb1a00002, # movlt r0, r2
        0xb12fff1e, # bxlt lr
        0xe0400001, # sub r0, r0, r1
        0xe2822001, # add r2, r2, #1
        0xeafffff9, # b loop
        0xe12fff1e, # bx lr
    )
    # 0x0028DF54: writes r0 to 0x10029000
    #   ldr r1, =0x10029000; str r0, [r1]; bx lr
    stub_28df54_code = struct.pack("<IIII", 0xe59f1000, 0xe5810000, 0xe12fff1e, 0x10029000)

    syms_03d0 = {
        "engine_func_00296f60": STUB_296F60,
        "func_00293c98": STUB_293C98,
        "ui_func_002c615c": STUB_2C615C,
        "battle_func_0028df54": STUB_28DF54,
    }
    staged_03d0 = stage_body(comp_03d0, relocs_03d0, 0x002F03D0, syms_03d0, "engine_func_002f03d0")

    syms_0478 = {
        "engine_func_00296f60": STUB_296F60,
        "func_00293c98": STUB_293C98,
        "ui_func_002c615c": STUB_2C615C,
        "battle_func_0028df54": STUB_28DF54,
    }
    staged_0478 = stage_body(comp_0478, relocs_0478, 0x002F0478, syms_0478, "engine_func_002f0478")

    # Test both functions on identical scenarios:
    # 1. Match at slot 5 with ratio <= threshold (e.g. num=1, denom=10 -> 100/10=10 <= 50) -> battle_func(1)
    # 2. Match at slot 5 with ratio > threshold (e.g. num=10, denom=10 -> 1000/10=100 > 50) -> continues, calls battle_func(0)
    # 3. No match at all -> calls battle_func(0)
    test_cases = [
        ("match_le_threshold", 5, 1, 10),
        ("match_gt_threshold", 5, 10, 10),
        ("no_match", -1, 1, 10),
    ]

    for fn_name, addr, orig_b, comp_b, num_off, den_off in [
        ("engine_func_002f03d0", 0x002F03D0, orig_03d0, staged_03d0, 0x1B4, 0x1B6),
        ("engine_func_002f0478", 0x002F0478, orig_0478, staged_0478, 0x1B8, 0x1BA),
    ]:
        for tc_name, slot, num_val, denom_val in test_cases:
            results = []
            for is_comp, code_bytes in [(False, orig_b), (True, comp_b)]:
                uc = create_emulator()
                uc.mem_write(addr, code_bytes)
                uc.mem_write(STUB_296F60, stub_296f60_code)
                uc.mem_write(STUB_293C98, stub_293c98_code)
                uc.mem_write(STUB_2C615C, stub_2c615c_code)
                uc.mem_write(STUB_28DF54, stub_28df54_code)

                uc.mem_write(0x10029000, struct.pack("<I", 0xDEADBEEF))
                # 0x10010000 + 0x1FC0 -> pointer to records at 0x10030000
                uc.mem_write(0x10010000, b"\x00" * 0x2000)
                uc.mem_write(0x10010000 + 0x1FC0, struct.pack("<I", 0x10030000))

                # Initialize 109 records (0x10030000 + i * 648)
                RECS_BASE = 0x10030000
                for i in range(110):
                    rec = bytearray(648)
                    if i == slot:
                        flags = 0x11 # (flags & 0x10) != 0 && (flags & 1) != 0 && (flags & 0x40) == 0
                        struct.pack_into("<I", rec, 0, flags)
                        struct.pack_into("<H", rec, 0xCE, 42) # id = 42
                        struct.pack_into("<H", rec, num_off, num_val)
                        struct.pack_into("<h", rec, den_off, denom_val)
                    else:
                        struct.pack_into("<I", rec, 0, 0x00) # unmatching
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

def test_002f3acc(out: Path):
    print("Testing script_vm_func_002f3acc (0x002F3ACC)...")
    comp, relocs = compile_function("script_vm_func_002f3acc", out)
    orig_bytes = load_original_bytes(0x002F3ACC, 172)

    # Callee:
    # engine_func_00287d54 = 0x00287D54
    STUB_287D54 = 0x00287D54

    # 0x00287D54: Euclidean distance calculation:
    #   vsub.f32 s3, s3, s0
    #   vsub.f32 s0, s4, s1
    #   vsub.f32 s1, s5, s2
    #   vmul.f32 s2, s3, s3
    #   vmla.f32 s2, s0, s0
    #   vmla.f32 s2, s1, s1
    #   vsqrt.f32 s0, s2
    #   bx lr
    # In original binary:
    stub_287d54_code = load_original_bytes(0x00287D54, 32)

    syms = {
        "engine_func_00287d54": STUB_287D54,
    }
    staged_compiled = stage_body(comp, relocs, 0x002F3ACC, syms, "script_vm_func_002f3acc")

    # Scenarios:
    # 1. Matching entry at index 3: active=1, type=0x1D, pos within 10 units -> state 0x12
    # 2. Entry at index 3 is outside 10 units (dist=20.0f); entry at index 7 has type 0x26, dist=5.0f -> entry 7 updated
    # 3. Entry at index 3 has type 0x10 (invalid type), dist=5.0f -> ignored
    # 4. Entry at index 3 has active=0, dist=5.0f -> ignored
    # 5. No entry within 10 units -> none updated
    test_cases = [
        ("direct_match", 3, 0x1D, (0.0, 3.0, 4.0)),      # dist = 5.0f < 10.0f
        ("later_match", 7, 0x26, (1.0, 2.0, 2.0)),       # dist = 3.0f < 10.0f
        ("wrong_type", 3, 0x10, (0.0, 3.0, 4.0)),
        ("inactive", 3, 0x1D, (0.0, 3.0, 4.0)),
        ("far_away", 3, 0x1D, (100.0, 100.0, 100.0)),
    ]

    for tc_name, target_slot, entry_type, entry_pos in test_cases:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002F3ACC, code_bytes)
            uc.mem_write(STUB_287D54, stub_287d54_code)

            # Global 0x00447A78 -> points to 0x10020000
            uc.mem_write(0x00447A78, struct.pack("<I", 0x10020000))
            # 128 entries at 0x10020000 + 0x1D0 + i * 404
            BASE_ADDR = 0x10020000
            uc.mem_write(BASE_ADDR, b"\x00" * (0x1D0 + 128 * 404))

            for i in range(128):
                e_addr = BASE_ADDR + 0x1D0 + i * 404
                if i == target_slot:
                    active = 0 if tc_name == "inactive" else 1
                    uc.mem_write(e_addr, struct.pack("<B", active))
                    uc.mem_write(e_addr + 0x04, struct.pack("<I", 0)) # state = 0
                    uc.mem_write(e_addr + 0x14, struct.pack("<I", entry_type))
                    uc.mem_write(e_addr + 0x50, struct.pack("<fff", *entry_pos))
                else:
                    # Inactive or far away
                    uc.mem_write(e_addr, struct.pack("<B", 0))

            # Target pos: (0.0, 0.0, 0.0)
            # Under AAPCS-VFP:
            # Struct Vec3 passed in s0, s1, s2
            # Set s0, s1, s2 = 0.0
            uc.reg_write(UC_ARM_REG_D0, 0)
            uc.reg_write(UC_ARM_REG_D1, 0)

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)

            uc.emu_start(0x002F3ACC, 0x00100000, count=5000)

            # Read all 128 states
            states = [struct.unpack("<I", uc.mem_read(BASE_ADDR + 0x1D0 + i * 404 + 4, 4))[0] for i in range(128)]
            results.append(states)

        assert results[0] == results[1], f"Mismatch for {tc_name}: {results[0]} != {results[1]}"
    print("  script_vm_func_002f3acc: PASS (all cases match)")

def main():
    out = ROOT / "build"
    out.mkdir(parents=True, exist_ok=True)
    print("Running Part 19 differential tests...")
    test_002eb300(out)
    test_002f0204(out)
    test_002f03d0_and_002f0478(out)
    test_002f3acc(out)
    print("\nALL PART 19 TESTS PASSED!")

if __name__ == "__main__":
    main()
