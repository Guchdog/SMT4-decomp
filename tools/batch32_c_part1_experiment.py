#!/usr/bin/env python3
"""Differential test for batch 32 C part 1:
- battle_func_002b8b54 (0x002B8B54, 28 B)
- camp_func_002b8ce4 (0x002B8CE4, 64 B)
- battle_func_002c1740 (0x002C1740, 52 B)
- func_002c36ec (0x002C36EC, 40 B)
- battle_func_002e3830 (0x002E3830, 28 B)
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

def test_002b8b54(out: Path):
    print("Testing battle_func_002b8b54 (0x002B8B54)...")
    comp, relocs = compile_function("battle_func_002b8b54", out)
    orig_bytes = load_original_bytes(0x002B8B54, 28)

    STUB_2BF41C = 0x002BF41C
    syms = {
        "battle_func_002bf41c": STUB_2BF41C,
    }
    staged_compiled = stage_body(comp, relocs, 0x002B8B54, syms, "battle_func_002b8b54")

    # Stubs:
    # 0x002BF41C: returns 1 (found) or 0 (not found) based on passed task
    #   cmp r0, #0; moveq r0, #0; movne r0, #1; bx lr
    stub_code = struct.pack("<IIII", 0xe3500000, 0x03a00000, 0x13a00001, 0xe12fff1e)

    for task_val in [0, 1, 0x12345678]:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002B8B54, code_bytes)
            uc.mem_write(STUB_2BF41C, stub_code)

            PTR_ADDR = 0x10020000
            uc.mem_write(PTR_ADDR, struct.pack("<I", task_val))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, PTR_ADDR)

            uc.emu_start(0x002B8B54, 0x00100000, count=100)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            results.append(r0)

        assert results[0] == results[1], f"Mismatch for task_val {task_val}: {results[0]} != {results[1]}"
    print("  battle_func_002b8b54: PASS (all cases match)")

def test_002e3830(out: Path):
    print("Testing battle_func_002e3830 (0x002E3830)...")
    comp, relocs = compile_function("battle_func_002e3830", out)
    orig_bytes = load_original_bytes(0x002E3830, 28)

    STUB_2BF41C = 0x002BF41C
    syms = {
        "battle_func_002bf41c": STUB_2BF41C,
    }
    staged_compiled = stage_body(comp, relocs, 0x002E3830, syms, "battle_func_002e3830")

    stub_code = struct.pack("<IIII", 0xe3500000, 0x03a00000, 0x13a00001, 0xe12fff1e)

    for task_val in [0, 1, 0xABCDEF01]:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002E3830, code_bytes)
            uc.mem_write(STUB_2BF41C, stub_code)

            CTX_ADDR = 0x10020000
            uc.mem_write(CTX_ADDR, b"\x00" * 0x40)
            uc.mem_write(CTX_ADDR + 0x2C, struct.pack("<I", task_val))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, CTX_ADDR)

            uc.emu_start(0x002E3830, 0x00100000, count=100)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            results.append(r0)

        assert results[0] == results[1], f"Mismatch for task_val {task_val}: {results[0]} != {results[1]}"
    print("  battle_func_002e3830: PASS (all cases match)")

def test_002b8ce4(out: Path):
    print("Testing camp_func_002b8ce4 (0x002B8CE4)...")
    comp, relocs = compile_function("camp_func_002b8ce4", out)
    orig_bytes = load_original_bytes(0x002B8CE4, 64)

    syms = {}
    staged_compiled = stage_body(comp, relocs, 0x002B8CE4, syms, "camp_func_002b8ce4")

    # Table is at 0x004D9758, stride 20 bytes:
    # +0x04: s32 count
    # +0x10: u8 status
    test_cases = [
        # (idx, status, count)
        (0, 0, 0),       # status 0 -> 1
        (1, 3, 1),       # status 3, count 1 -> 1
        (2, 3, 5),       # status 3, count 5 -> 1
        (3, 3, 0),       # status 3, count 0 -> 0
        (4, 3, -1),      # status 3, count -1 -> 0
        (5, 1, 10),      # status 1 -> 0
        (6, 2, 10),      # status 2 -> 0
    ]

    for idx, status, count in test_cases:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002B8CE4, code_bytes)

            entry_addr = 0x004D9758 + idx * 20
            uc.mem_write(entry_addr + 4, struct.pack("<i", count))
            uc.mem_write(entry_addr + 0x10, struct.pack("<B", status))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, idx)

            uc.emu_start(0x002B8CE4, 0x00100000, count=100)
            r0 = uc.reg_read(UC_ARM_REG_R0)
            results.append(r0)

        assert results[0] == results[1], f"Mismatch for case ({idx}, {status}, {count}): {results[0]} != {results[1]}"
    print("  camp_func_002b8ce4: PASS (all cases match)")

def test_002c1740(out: Path):
    print("Testing battle_func_002c1740 (0x002C1740)...")
    comp, relocs = compile_function("battle_func_002c1740", out)
    orig_bytes = load_original_bytes(0x002C1740, 52)

    syms = {}
    staged_compiled = stage_body(comp, relocs, 0x002C1740, syms, "battle_func_002c1740")

    # 0x0044EA58 has pointer mgr.
    # *(mgr + 4) has pointer table (32 words).
    scenarios = [
        ("insert_at_0", 0x10025000, [0]*32),
        ("insert_at_5", 0x10025000, [0x5555]*5 + [0]*27),
        ("table_full", 0x10025000, [0x7777]*32),
    ]

    for name, item, initial_table in scenarios:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002C1740, code_bytes)

            uc.mem_write(0x0044EA58, struct.pack("<I", 0x10010000))
            uc.mem_write(0x10010004, struct.pack("<I", 0x10020000))
            uc.mem_write(0x10020000, struct.pack("<32I", *initial_table))

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, item)

            uc.emu_start(0x002C1740, 0x00100000, count=500)
            final_table = uc.mem_read(0x10020000, 32 * 4)
            results.append(final_table)

        assert results[0] == results[1], f"Mismatch for scenario {name}: {results[0]} != {results[1]}"
    print("  battle_func_002c1740: PASS (all cases match)")

def test_002c36ec(out: Path):
    print("Testing func_002c36ec (0x002C36EC)...")
    comp, relocs = compile_function("func_002c36ec", out)
    orig_bytes = load_original_bytes(0x002C36EC, 40)

    syms = {}
    staged_compiled = stage_body(comp, relocs, 0x002C36EC, syms, "func_002c36ec")

    # Test entry 1 at +0x00 (writes val to 0x0044E0B0)
    for val in [0, 1, 0x55, 0xFF]:
        results = []
        for is_comp, code_bytes in [(False, orig_bytes), (True, staged_compiled)]:
            uc = create_emulator()
            uc.mem_write(0x002C36EC, code_bytes)
            uc.mem_write(0x0044E0B0, b"\x00")

            sp = STACK_BASE + 0x8000
            uc.reg_write(UC_ARM_REG_SP, sp)
            uc.reg_write(UC_ARM_REG_LR, 0x00100000)
            uc.reg_write(UC_ARM_REG_R0, val)

            uc.emu_start(0x002C36EC, 0x00100000, count=20)
            res_byte = uc.mem_read(0x0044E0B0, 1)
            results.append(res_byte)

        assert results[0] == results[1], f"Mismatch for func_002c36ec val {val}: {results[0]} != {results[1]}"
    print("  func_002c36ec: PASS (all cases match)")

def main():
    out = ROOT / "build"
    out.mkdir(parents=True, exist_ok=True)
    print("Running Batch 32 C Part 1 differential tests...")
    test_002b8b54(out)
    test_002e3830(out)
    test_002b8ce4(out)
    test_002c1740(out)
    test_002c36ec(out)
    print("\nALL BATCH 32 C PART 1 TESTS PASSED!")

if __name__ == "__main__":
    main()
