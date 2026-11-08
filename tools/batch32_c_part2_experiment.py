#!/usr/bin/env python3
"""Differential test for batch 32 C part 2:
- script_vm_func_002c9c2c (0x002C9C2C, 44 B)
- engine_func_002ca6a4 (0x002CA6A4, 80 B)
- script_vm_func_002eb0f4 (0x002EB0F4, 80 B)
- func_002cd9f4 (0x002CD9F4, 88 B)
- script_vm_func_002b91c4 (0x002B91C4, 92 B)
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

def test_002c9c2c(out: Path):
    print("Testing script_vm_func_002c9c2c (0x002C9C2C)...")
    comp, relocs = compile_function("script_vm_func_002c9c2c", out)
    orig_bytes = load_original_bytes(0x002C9C2C, 44)

    STUB_2C0BA8 = 0x002C0BA8
    STUB_24C48C = 0x0024C48C

    # Test cases:
    # 1. 2c0ba8 returns 1, 24c48c returns 1 -> returns 1
    # 2. 2c0ba8 returns 1, 24c48c returns 0 -> returns 0
    # 3. 2c0ba8 returns 0 -> returns 0 (24c48c not called)
    test_cases = [
        (1, 1),
        (1, 0),
        (0, 1),
    ]

    syms = {
        "script_vm_func_002c0ba8": STUB_2C0BA8,
        "ui_func_0024c48c": STUB_24C48C,
    }
    staged_compiled = stage_body(comp, relocs, 0x002C9C2C, syms, "script_vm_func_002c9c2c")

    for ret_ba8, ret_48c in test_cases:
        stub_ba8_code = struct.pack("<II", 0xe3a00000 | ret_ba8, 0xe12fff1e)
        stub_48c_code = struct.pack("<II", 0xe3a00000 | ret_48c, 0xe12fff1e)

        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002C9C2C, code_bytes)
            uc.mem_write(STUB_2C0BA8, stub_ba8_code)
            uc.mem_write(STUB_24C48C, stub_48c_code)

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)

            uc.emu_start(0x002C9C2C, 0x00100000, count=100)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            results.append(r0)

        assert results[0] == results[1], f"Mismatch for ({ret_ba8}, {ret_48c}): {results[0]} != {results[1]}"
    print("  script_vm_func_002c9c2c: PASS (all cases match)")

def test_002ca6a4(out: Path):
    print("Testing engine_func_002ca6a4 (0x002CA6A4)...")
    comp, relocs = compile_function("engine_func_002ca6a4", out)
    orig_bytes = load_original_bytes(0x002CA6A4, 80)

    # Entry 1 at +0x00 returns 0 unconditionally
    results = []
    for is_comp, code_bytes in [(False, orig_bytes), (True, comp)]:
        uc = create_emulator()
        uc.mem_write(0x002CA6A4, code_bytes)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00100000)

        uc.emu_start(0x002CA6A4, 0x00100000, count=20)
        r0 = uc.reg_read(UC_ARM_REG_R0)
        results.append(r0)

    assert results[0] == results[1], f"Mismatch for engine_func_002ca6a4: {results[0]} != {results[1]}"
    print("  engine_func_002ca6a4: PASS (all cases match)")

def test_002eb0f4(out: Path):
    print("Testing script_vm_func_002eb0f4 (0x002EB0F4)...")
    comp, relocs = compile_function("script_vm_func_002eb0f4", out)
    orig_bytes = load_original_bytes(0x002EB0F4, 80)

    syms = {}
    staged_compiled = stage_body(comp, relocs, 0x002EB0F4, syms, "script_vm_func_002eb0f4")

    # Table is at 0x0044CD88 (points to entries array, 32 entries of 76 bytes).
    # Entry layout:
    # +0x58: u8 active
    # +0x5C: u32 state
    scenarios = [
        ("match_at_0", 0, 1, 2),
        ("match_at_15", 15, 1, 2),
        ("wrong_state", 5, 1, 3),
        ("inactive", 5, 0, 2),
        ("none", -1, 0, 0),
    ]

    for name, target_slot, active_val, state_val in scenarios:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002EB0F4, code_bytes)

            BASE = 0x10020000
            uc.mem_write(0x0044CD88, struct.pack("<I", BASE))
            uc.mem_write(BASE, b"\x00" * (32 * 76))

            if target_slot >= 0:
                e_addr = BASE + target_slot * 76
                uc.mem_write(e_addr + 0x58, struct.pack("<B", active_val))
                uc.mem_write(e_addr + 0x5C, struct.pack("<I", state_val))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)

            uc.emu_start(0x002EB0F4, 0x00100000, count=500)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            results.append(r0)

        assert results[0] == results[1], f"Mismatch for scenario {name}: {results[0]} != {results[1]}"
    print("  script_vm_func_002eb0f4: PASS (all cases match)")

def test_002cd9f4(out: Path):
    print("Testing func_002cd9f4 (0x002CD9F4)...")
    comp, relocs = compile_function("func_002cd9f4", out)
    orig_bytes = load_original_bytes(0x002CD9F4, 88)

    syms = {}
    staged_compiled = stage_body(comp, relocs, 0x002CD9F4, syms, "func_002cd9f4")

    # Target array:
    # *0x0043E2A8 + 4 -> points to base
    # if idx >= 64: target = base + 0x24BE4 + idx
    # if idx < 64: target = base + 0x1EC98 + idx
    # returns (*target & 4) >> 2
    test_cases = [
        (-1, 0, 0),        # out of bounds -> 0
        (72, 0, 0),        # out of bounds -> 0
        (0, 0x1EC98, 4),   # bit 2 set -> 1
        (0, 0x1EC98, 0),   # bit 2 clear -> 0
        (63, 0x1EC98 + 63, 4), # bit 2 set -> 1
        (64, 0x24BE4 + 64, 4), # bit 2 set -> 1
        (64, 0x24BE4 + 64, 0), # bit 2 clear -> 0
        (71, 0x24BE4 + 71, 4), # bit 2 set -> 1
    ]

    for idx, target_off, byte_val in test_cases:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002CD9F4, code_bytes)

            BASE = 0x10000000
            uc.mem_write(0x0043E2A8 + 4, struct.pack("<I", BASE))
            if 0 <= idx < 72:
                uc.mem_write(BASE + target_off, struct.pack("<B", byte_val))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, idx & 0xFFFFFFFF)

            uc.emu_start(0x002CD9F4, 0x00100000, count=100)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            results.append(r0)

        assert results[0] == results[1], f"Mismatch for idx {idx}: {results[0]} != {results[1]}"
    print("  func_002cd9f4: PASS (all cases match)")

def test_002b91c4(out: Path):
    print("Testing script_vm_func_002b91c4 (0x002B91C4)...")
    comp, relocs = compile_function("script_vm_func_002b91c4", out)
    orig_bytes = load_original_bytes(0x002B91C4, 92)

    syms = {}
    staged_compiled = stage_body(comp, relocs, 0x002B91C4, syms, "script_vm_func_002b91c4")

    scenarios = [
        ("already_at_0", 0x10020000, [0x10020000] + [0]*31),
        ("already_at_7", 0x10020000, [0x1111]*7 + [0x10020000] + [0]*24),
        ("insert_at_0", 0x10020000, [0]*32),
        ("insert_at_10", 0x10020000, [0x2222]*10 + [0]*22),
        ("table_full", 0x10020000, [0x3333]*32),
    ]

    for name, obj, initial_table in scenarios:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002B91C4, code_bytes)

            table_bytes = struct.pack("<32I", *initial_table)
            uc.mem_write(0x004C5404, table_bytes)

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, obj)

            uc.emu_start(0x002B91C4, 0x00100000, count=500)
            final_table = uc.mem_read(0x004C5404, 32 * 4)
            results.append(final_table)

        assert results[0] == results[1], f"Mismatch for scenario {name}: {results[0]} != {results[1]}"
    print("  script_vm_func_002b91c4: PASS (all cases match)")

def main():
    out = ROOT / "build"
    out.mkdir(parents=True, exist_ok=True)
    print("Running Batch 32 C Part 2 differential tests...")
    test_002c9c2c(out)
    test_002ca6a4(out)
    test_002eb0f4(out)
    test_002cd9f4(out)
    test_002b91c4(out)
    print("\nALL BATCH 32 C PART 2 TESTS PASSED!")

if __name__ == "__main__":
    main()
