#!/usr/bin/env python3
"""Differential test for engine_func_002a1578 (0x002a1578) using Unicorn ARM emulation."""

import struct
import sys
from pathlib import Path
import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
FUNC_ADDR = 0x002a1578
FUNC_SIZE = 584

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
VAL_ADDR = 0x00600000
TRAP_ADDR = 0x90000000

def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)

def get_symbol_offset(obj_file, sym_name):
    data = Path(obj_file).read_bytes()
    e_shoff, e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<IIHH", data, 32)[0], struct.unpack_from("<H", data, 46)[0], struct.unpack_from("<H", data, 48)[0], struct.unpack_from("<H", data, 50)[0]
    sections = [struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    symtab = [s for s in sections if s[1] == 2][0]
    strtab = sections[symtab[6]]
    for i in range(symtab[5] // 16):
        st_name, st_val, st_size, st_info, st_other, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + i * 16)
        name = data[strtab[4] + st_name:].split(b"\x00")[0].decode("ascii", errors="replace")
        if sym_name in name:
            return st_val
    return 0

def compile_candidate():
    out_dir = ROOT / "build/test_leaf_002a1578"
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_file = out_dir / "leaf_batch45_a.o"
    src_file = ROOT / "src/engine/leaf_batch45_a.cpp"
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    func_sym_offset = get_symbol_offset(obj_file, "002a1578")
    for k in funcs:
        if "engine_func_002a1578" in k or "002a1578" in k:
            return funcs[k][0], funcs[k][1], func_sym_offset
    raise KeyError("engine_func_002a1578 not found in compiled object")

def apply_relocations(code_bytes, relocs, func_sym_offset):
    fixed = bytearray(code_bytes)
    for rel in relocs:
        offset = rel.offset
        if rel.relocation_type == 2: # R_ARM_ABS32
            orig_addend = struct.unpack_from("<I", fixed, offset)[0]
            target = FUNC_ADDR + (orig_addend - func_sym_offset)
            struct.pack_into("<I", fixed, offset, target)
    return bytes(fixed)

def run_test(code_bytes, val):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(0x002a0000, 0x10000)
    uc.mem_map(STACK_ADDR, STACK_SIZE)
    uc.mem_map(VAL_ADDR, 0x1000)
    uc.mem_map(TRAP_ADDR, 0x1000)

    uc.mem_write(FUNC_ADDR, code_bytes)
    uc.mem_write(VAL_ADDR, struct.pack("<I", val))
    uc.reg_write(arm.UC_ARM_REG_R0, VAL_ADDR)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_ADDR + 0x8000)
    uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
    uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
    return uc.reg_read(arm.UC_ARM_REG_R0)

def main():
    orig_code = get_orig_bytes()
    cand_raw, relocs, func_sym_offset = compile_candidate()
    cand_code = apply_relocations(cand_raw, relocs, func_sym_offset)
    print(f"Original size: {len(orig_code)} B, Candidate size: {len(cand_code)} B, Relocs: {len(relocs)}")

    # All test inputs:
    # 1. 0
    # 2. All 18 category 0x34 keys
    # 3. Category 0x20 key + non-key
    # 4. Category 0x11: sub-id in [260, 279], < 260, >= 280
    # 5. Category 0x28, 0x2E (unmodified)
    # 6. Random/arbitrary IDs
    test_inputs = [
        0,
        # Cat 0x34 mapped keys
        0xC920D095, 0xC920D073, 0xC860D069, 0xC860D06E, 0xC900D075,
        0xC920D086, 0xC920D08C, 0xC920D08F, 0xE0A0D0A9, 0xC920D0A4,
        0xC920D0A7, 0xC920D0A8, 0xE0C0D066, 0xE0E0D068, 0xC8A0D018,
        0xD860D020, 0xD860D024, 0xD880D023,
        # Cat 0x34 unmapped
        (0x34 << 10) | 50, (0x34 << 10) | 150, (0x34 << 10) | 350,
        # Cat 0x20 mapped and unmapped
        0xC8A08035, (0x20 << 10) | 1, (0x20 << 10) | 200,
        # Cat 0x11
        (0x11 << 10) | 259, (0x11 << 10) | 260, (0x11 << 10) | 270,
        (0x11 << 10) | 279, (0x11 << 10) | 280, (0x11 << 10) | 10,
        # Cat 0x28, 0x2E
        (0x28 << 10) | 123, (0x2E << 10) | 456,
        # Other categories
        0x00000001, 0x12345678, 0xDEADBEEF, 0xFFFFFFFF
    ]

    all_passed = True
    for i, val in enumerate(test_inputs):
        orig_ret = run_test(orig_code, val)
        cand_ret = run_test(cand_code, val)

        if orig_ret == cand_ret:
            print(f"Case {i+1:2d} (val=0x{val:08X}): PASS -> 0x{cand_ret:08X}")
        else:
            print(f"Case {i+1:2d} (val=0x{val:08X}): FAIL! Orig=0x{orig_ret:08X}, Cand=0x{cand_ret:08X}")
            all_passed = False

    if all_passed:
        print("\nALL TEST CASES PASSED!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
