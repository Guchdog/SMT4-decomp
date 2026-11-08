#!/usr/bin/env python3
"""Differential test for batch 32 C part 3:
- script_vm_func_002dfd94 (0x002DFD94, 92 B)
- func_002cd970 (0x002CD970, 132 B)
- func_002e4a38 (0x002E4A38, 132 B)
- func_002d4ef4 (0x002D4EF4, 148 B)
- engine_func_002cbf38 (0x002CBF38, 164 B)
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
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
    UC_ARM_REG_S0,
    UC_ARM_REG_S1,
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

def test_002dfd94(out: Path):
    print("Testing script_vm_func_002dfd94 (0x002DFD94)...")
    comp, relocs = compile_function("script_vm_func_002dfd94", out)
    orig_bytes = load_original_bytes(0x002DFD94, 92)

    PTR_GLOBAL = 0x00447A78
    TABLE_ADDR = 0x10020000

    staged_compiled = stage_body(comp, relocs, 0x002DFD94, {}, "script_vm_func_002dfd94")

    # Cases: (target_val, match_slot, is_active)
    # None match_slot means table has no match
    cases = [
        (0x1234, None, False),
        (0x1234, 0, True),
        (0x5678, 42, True),
        (0x9ABC, 127, True),
        (0xDEF0, 50, False),  # value matches but slot active flag (0x1D0) == 0
    ]

    for target_val, match_slot, is_active in cases:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002DFD94, code_bytes)

            # Map buffer for table (0x80 * 404 + 0x1000 bytes)
            table_data = bytearray(0x80 * 404 + 0x1000)
            if match_slot is not None:
                elem_off = match_slot * 404
                if is_active:
                    table_data[elem_off + 0x1D0] = 1
                struct.pack_into("<I", table_data, elem_off + 0x1E8, target_val)

            uc.mem_write(TABLE_ADDR, bytes(table_data))
            uc.mem_write(PTR_GLOBAL, struct.pack("<I", TABLE_ADDR))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, target_val)

            uc.emu_start(0x002DFD94, 0x00100000, count=2000)

            # Check modified table
            res_table = uc.mem_read(TABLE_ADDR, len(table_data))
            results.append(res_table)

        assert results[0] == results[1], f"Mismatch for case ({hex(target_val)}, {match_slot}, {is_active})"
    print("  script_vm_func_002dfd94: PASS (all cases match)")

def test_002cd970(out: Path):
    print("Testing func_002cd970 (0x002CD970)...")
    comp, relocs = compile_function("func_002cd970", out)
    orig_bytes = load_original_bytes(0x002CD970, 132)

    COUNT_PTR = 0x00433278
    TABLE_BASE = 0x00478000

    staged_compiled = stage_body(comp, relocs, 0x002CD970, {}, "func_002cd970")

    # Cases: (idx, target_val, count, match_type, match_i)
    # match_type: 0 = none, 1 = at 0x30, 2 = at 0x48
    cases = [
        (-1, 0x111, 10, 0, 0),
        (10, 0x111, 10, 0, 0),  # out of bounds idx >= count
        (15, 0x111, 10, 0, 0),
        (2, 0x111, 10, 0, 0),   # in bounds, no match -> returns 0
        (2, 0x222, 10, 1, 0),   # match at i=0, offset 0x30
        (2, 0x333, 10, 2, 0),   # match at i=0, offset 0x48
        (4, 0x444, 10, 1, 2),   # match at i=2, offset 0x30
        (4, 0x555, 10, 2, 2),   # match at i=2, offset 0x48
        (7, 0x666, 10, 1, 4),   # match at i=4, offset 0x30
        (7, 0x777, 10, 2, 4),   # match at i=4, offset 0x48
    ]

    for idx, target_val, count, mtype, mi in cases:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002CD970, code_bytes)

            # Table size: count * 328
            tbl_data = bytearray(max(count, idx + 1) * 328)
            if mtype == 1 and idx >= 0:
                slot_off = idx * 328 + mi * 24
                struct.pack_into("<I", tbl_data, slot_off + 0x30, target_val)
            elif mtype == 2 and idx >= 0:
                slot_off = idx * 328 + mi * 24
                struct.pack_into("<I", tbl_data, slot_off + 0x48, target_val)

            uc.mem_write(TABLE_BASE, bytes(tbl_data))
            uc.mem_write(COUNT_PTR, struct.pack("<I", count))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, idx & 0xFFFFFFFF)
            uc.reg_write(UC_ARM_REG_R1, target_val)

            uc.emu_start(0x002CD970, 0x00100000, count=500)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            results.append(r0)

        assert results[0] == results[1], f"Mismatch for case ({idx}, {hex(target_val)}, {mtype}, {mi}): {hex(results[0])} != {hex(results[1])}"
    print("  func_002cd970: PASS (all cases match)")

def test_002e4a38(out: Path):
    print("Testing func_002e4a38 (0x002E4A38)...")
    comp, relocs = compile_function("func_002e4a38", out)
    orig_bytes = load_original_bytes(0x002E4A38, 132)

    STUB_2B4854 = 0x002B4854

    # We need to map row pointers returned by camp_func_002b4854
    # Unit 1 -> ROW_A (0x10010000)
    # Unit 2 -> ROW_B (0x10010100)
    ROW_A = 0x10010000
    ROW_B = 0x10010100

    # camp_func_002b4854 stub:
    # if r0 == 1 return ROW_A else return ROW_B
    # cmp r0, #1
    # ldreq r0, =ROW_A
    # ldrne r0, =ROW_B
    # bx lr
    stub_code = struct.pack("<IIIII",
        0xe3500001,  # cmp r0, #1
        0x059f0004,  # ldreq r0, [pc, #4]
        0x159f0004,  # ldrne r0, [pc, #4]
        0xe12fff1e,  # bx lr
        ROW_A,
    ) + struct.pack("<I", ROW_B)

    syms = {
        "camp_func_002b4854": STUB_2B4854,
    }
    staged_compiled = stage_body(comp, relocs, 0x002E4A38, syms, "func_002e4a38")

    # (val70_a, val70_b, val6f_a, val6f_b)
    cases = [
        (10, 25, 0, 0),    # diff in 0x70: 25 - 10 = 15
        (30, 12, 0, 0),    # diff in 0x70: 12 - 30 = -18
        (50, 50, 7, 20),   # equal 0x70, diff in 0x6f: 20 - 7 = 13
        (50, 50, 20, 7),   # equal 0x70, diff in 0x6f: 7 - 20 = -13
        (50, 50, 15, 15),  # equal both: 0
    ]

    PARAM_A = 0x10008000
    PARAM_B = 0x10008004

    for v70_a, v70_b, v6f_a, v6f_b in cases:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002E4A38, code_bytes)
            uc.mem_write(STUB_2B4854, stub_code)

            # Setup rows
            row_a = bytearray(0x80)
            row_b = bytearray(0x80)
            struct.pack_into("<I", row_a, 0x70, v70_a)
            struct.pack_into("<I", row_b, 0x70, v70_b)
            row_a[0x6F] = v6f_a
            row_b[0x6F] = v6f_b

            uc.mem_write(ROW_A, bytes(row_a))
            uc.mem_write(ROW_B, bytes(row_b))

            # Setup param pointers (holding unit id 1 and 2 as uint16)
            uc.mem_write(PARAM_A, struct.pack("<H", 1))
            uc.mem_write(PARAM_B, struct.pack("<H", 2))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, PARAM_A)
            uc.reg_write(UC_ARM_REG_R1, PARAM_B)

            uc.emu_start(0x002E4A38, 0x00100000, count=500)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            # Normalize signed 32-bit
            if r0 >= 0x80000000:
                r0 -= 0x100000000
            results.append(r0)

        assert results[0] == results[1], f"Mismatch for case ({v70_a}, {v70_b}, {v6f_a}, {v6f_b}): {results[0]} != {results[1]}"

    # Test companion entry 1: func_002e4a94 (0x002E4A94)
    comp_4a94, relocs_4a94 = compile_function("func_002e4a94", out)
    staged_4a94 = stage_body(comp_4a94, relocs_4a94, 0x002E4A94, {}, "func_002e4a94")
    for a_val, b_val in [(0x12340005, 0x56780009), (0xFF, 0x01), (0x20, 0x20)]:
        results = []
        for is_comp, (entry, code_bytes) in enumerate([(0x002E4A94, orig_bytes[0x5C:0x5C+24]), (0x002E4A94, staged_4a94)]):
            uc = create_emulator()
            uc.mem_write(0x002E4A94, code_bytes)
            uc.mem_write(PARAM_A, struct.pack("<I", a_val))
            uc.mem_write(PARAM_B, struct.pack("<I", b_val))
            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, PARAM_A)
            uc.reg_write(UC_ARM_REG_R1, PARAM_B)
            uc.emu_start(0x002E4A94, 0x00100000, count=50)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            if r0 >= 0x80000000:
                r0 -= 0x100000000
            results.append(r0)
        assert results[0] == results[1], f"func_002e4a94 mismatch for ({hex(a_val)}, {hex(b_val)}): {results[0]} != {results[1]}"

    # Test companion entry 2: func_002e4aac (0x002E4AAC)
    comp_4aac, relocs_4aac = compile_function("func_002e4aac", out)
    staged_4aac = stage_body(comp_4aac, relocs_4aac, 0x002E4AAC, {}, "func_002e4aac")
    for a_val, b_val in [(50, 100), (300, 100), (200, 200)]:
        results = []
        for is_comp, (entry, code_bytes) in enumerate([(0x002E4AAC, orig_bytes[0x74:0x74+16]), (0x002E4AAC, staged_4aac)]):
            uc = create_emulator()
            uc.mem_write(0x002E4AAC, code_bytes)
            uc.mem_write(PARAM_A, struct.pack("<H", a_val))
            uc.mem_write(PARAM_B, struct.pack("<H", b_val))
            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, PARAM_A)
            uc.reg_write(UC_ARM_REG_R1, PARAM_B)
            uc.emu_start(0x002E4AAC, 0x00100000, count=50)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            if r0 >= 0x80000000:
                r0 -= 0x100000000
            results.append(r0)
        assert results[0] == results[1], f"func_002e4aac mismatch for ({a_val}, {b_val}): {results[0]} != {results[1]}"

    print("  func_002e4a38: PASS (all cases match)")

def test_002d4ef4(out: Path):
    print("Testing func_002d4ef4 (0x002D4EF4)...")
    comp, relocs = compile_function("func_002d4ef4", out)
    orig_bytes = load_original_bytes(0x002D4EF4, 148)

    TABLE_ADDR = 0x004C2424
    staged_compiled = stage_body(comp, relocs, 0x002D4EF4, {}, "func_002d4ef4")

    # (count, req_type, x, y, entries)
    # entries: list of (min_x, min_y, max_x, max_y, type)
    cases = [
        (0, 1, 15.0, 35.0, []),
        (1, 1, 15.0, 35.0, [(10.0, 30.0, 20.0, 40.0, 1)]),  # inside, matching type
        (1, 2, 15.0, 35.0, [(10.0, 30.0, 20.0, 40.0, 1)]),  # inside, non-matching type
        (1, 0, 15.0, 35.0, [(10.0, 30.0, 20.0, 40.0, 1)]),  # inside, req_type 0 (accept any)
        (1, 1, 5.0, 35.0,  [(10.0, 30.0, 20.0, 40.0, 1)]),  # outside left
        (1, 1, 25.0, 35.0, [(10.0, 30.0, 20.0, 40.0, 1)]),  # outside right
        (1, 1, 15.0, 25.0, [(10.0, 30.0, 20.0, 40.0, 1)]),  # outside top
        (1, 1, 15.0, 45.0, [(10.0, 30.0, 20.0, 40.0, 1)]),  # outside bottom
        (3, 2, 105.0, 205.0, [                               # match on 3rd entry
            (10.0, 30.0, 20.0, 40.0, 1),
            (50.0, 60.0, 70.0, 80.0, 2),
            (100.0, 200.0, 110.0, 210.0, 2),
        ]),
    ]

    for count, req_type, px, py, entries in cases:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002D4EF4, code_bytes)

            tbl_buf = bytearray(0x1000)
            struct.pack_into("<I", tbl_buf, 0xE00, count)
            for i, (min_x, min_y, max_x, max_y, etype) in enumerate(entries):
                off = i * 28
                struct.pack_into("<f", tbl_buf, off + 0x00, min_x)
                struct.pack_into("<f", tbl_buf, off + 0x08, min_y)
                struct.pack_into("<f", tbl_buf, off + 0x0C, max_x)
                struct.pack_into("<f", tbl_buf, off + 0x14, max_y)
                struct.pack_into("<I", tbl_buf, off + 0x18, etype)

            uc.mem_write(TABLE_ADDR, bytes(tbl_buf))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, req_type)
            uc.reg_write(UC_ARM_REG_S0, struct.unpack('<I', struct.pack('<f', px))[0])
            uc.reg_write(UC_ARM_REG_S1, struct.unpack('<I', struct.pack('<f', py))[0])

            uc.emu_start(0x002D4EF4, 0x00100000, count=500)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            results.append(r0)

        assert results[0] == results[1], f"Mismatch for case ({count}, {req_type}, {px}, {py}): {results[0]} != {results[1]}"
    print("  func_002d4ef4: PASS (all cases match)")

def test_002cbf38(out: Path):
    print("Testing engine_func_002cbf38 (0x002CBF38)...")
    comp, relocs = compile_function("engine_func_002cbf38", out)
    orig_bytes = load_original_bytes(0x002CBF38, 164)

    STUB_UI = 0x00254AC4
    STUB_CLEANUP = 0x002C3714
    STUB_ENGINE = 0x002BB8E4

    CLEANUP_TRACKER = 0x10009000

    # STUB_UI: returns ret_ui
    # STUB_CLEANUP: records r0 to CLEANUP_TRACKER
    # STUB_ENGINE: returns ret_eng
    stub_cleanup_code = struct.pack("<IIIII",
        0xe59f1004,  # ldr r1, [pc, #4]
        0xe5810000,  # str r0, [r1]
        0xe12fff1e,  # bx lr
        0xe1a00000,  # nop
        CLEANUP_TRACKER
    )

    syms = {
        "ui_func_00254ac4": STUB_UI,
        "func_002c3714": STUB_CLEANUP,
        "engine_func_002bb8e4": STUB_ENGINE,
    }
    staged_compiled = stage_body(comp, relocs, 0x002CBF38, syms, "engine_func_002cbf38")

    OBJ_ADDR = 0x10007000

    # (ret_ui, param2, ret_eng)
    cases = [
        (0, 0, 0),     # ui fails -> returns 0xE0E046BC
        (1, 0, 0),     # ui succeeds, param2=0 -> returns 0xE7E3FFFF
        (1, 1, 42),    # ui succeeds, param2=1 -> clears obj fields, calls engine -> returns 42
        (1, 1, -1),    # ui succeeds, param2=1 -> returns -1
    ]

    for ret_ui, param2, ret_eng in cases:
        stub_ui_code = struct.pack("<II", 0xe3a00000 | (ret_ui & 0xFF), 0xe12fff1e)
        if ret_eng >= 0:
            stub_eng_code = struct.pack("<II", 0xe3a00000 | (ret_eng & 0xFF), 0xe12fff1e)
        else:
            stub_eng_code = struct.pack("<II", 0xe3e00000 | (~ret_eng & 0xFF), 0xe12fff1e)

        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002CBF38, code_bytes)
            uc.mem_write(STUB_UI, stub_ui_code)
            uc.mem_write(STUB_CLEANUP, stub_cleanup_code)
            uc.mem_write(STUB_ENGINE, stub_eng_code)

            # Setup obj
            obj_data = bytearray(0x40)
            obj_data[0x0C:0x20] = b'\xAA' * 0x14
            uc.mem_write(OBJ_ADDR, bytes(obj_data))
            uc.mem_write(CLEANUP_TRACKER, b'\x00\x00\x00\x00')

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, OBJ_ADDR)
            uc.reg_write(UC_ARM_REG_R1, 0x1234)
            uc.reg_write(UC_ARM_REG_R2, param2)

            uc.emu_start(0x002CBF38, 0x00100000, count=500)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            cleanup_called_with = struct.unpack("<I", uc.mem_read(CLEANUP_TRACKER, 4))[0]
            obj_post = uc.mem_read(OBJ_ADDR, 0x20)
            results.append((r0, cleanup_called_with, obj_post))

        assert results[0] == results[1], f"Mismatch for case ({ret_ui}, {param2}, {ret_eng}): {results[0]} != {results[1]}"

    # Test companion entry: func_002cbfcc (0x002CBFCC)
    comp_cc, relocs_cc = compile_function("func_002cbfcc", out)
    staged_cc = stage_body(comp_cc, relocs_cc, 0x002CBFCC, {}, "func_002cbfcc")

    TARGET_BYTE = 0x00464AF0 + 2
    for byte_val in [0x55, 0xAA, 0x00, 0xFF]:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes[0x94:0x94+12]), (True, staged_cc)]:
            uc = create_emulator()
            uc.mem_write(0x002CBFCC, code_bytes)
            uc.mem_write(TARGET_BYTE, b'\x12')

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, byte_val)

            uc.emu_start(0x002CBFCC, 0x00100000, count=50)
            val = uc.mem_read(TARGET_BYTE, 1)[0]
            results.append(val)
        assert results[0] == results[1], f"func_002cbfcc mismatch for {hex(byte_val)}: {results[0]} != {results[1]}"

    print("  engine_func_002cbf38: PASS (all cases match)")

def main():
    out = ROOT / "build"
    out.mkdir(exist_ok=True)
    print("Running Batch 32 C Part 3 differential tests...")
    test_002dfd94(out)
    test_002cd970(out)
    test_002e4a38(out)
    test_002d4ef4(out)
    test_002cbf38(out)
    print("\nALL BATCH 32 C PART 3 TESTS PASSED!")

if __name__ == "__main__":
    main()
