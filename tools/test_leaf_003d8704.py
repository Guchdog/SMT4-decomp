#!/usr/bin/env python3
"""Differential test for battle_func_003d8704 (0x003d8704) using Unicorn ARM emulation."""

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
FUNC_ADDR = 0x003d8704
FUNC_SIZE = 456

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
OBJ_ADDR = 0x00600000
OBJ_SIZE = 0x1000
RODATA_ADDR = 0x00700000
TRAP_ADDR = 0x90000000

def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)

def get_elf_section(path, target_name):
    data = Path(path).read_bytes()
    e_shoff, e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<IIHH", data, 32)[0], struct.unpack_from("<H", data, 46)[0], struct.unpack_from("<H", data, 48)[0], struct.unpack_from("<H", data, 50)[0]
    sections = [struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    for s in sections:
        end = shstrtab.find(b"\x00", s[0])
        name = shstrtab[s[0]:end].decode("ascii", errors="replace")
        if name == target_name:
            return data[s[4] : s[4] + s[5]]
    return b""

def compile_candidate():
    out_dir = ROOT / "build/test_leaf_003d8704"
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_file = out_dir / "leaf_batch45_a.o"
    src_file = ROOT / "src/engine/leaf_batch45_a.cpp"
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    rodata = get_elf_section(obj_file, ".rodata")
    for k in funcs:
        if "battle_func_003d8704" in k or "003d8704" in k:
            return funcs[k][0], funcs[k][1], rodata
    raise KeyError("battle_func_003d8704 not found in compiled object")

def apply_relocations(code_bytes, relocs):
    fixed = bytearray(code_bytes)
    for rel in relocs:
        offset = rel.offset
        if rel.relocation_type == 2:  # R_ARM_ABS32
            orig_addend = struct.unpack_from("<I", fixed, offset)[0]
            struct.pack_into("<I", fixed, offset, RODATA_ADDR + orig_addend)
    return bytes(fixed)

def run_unicorn(code_bytes, preset_id, slot_id, rodata_bytes=None, dirty_byte=0xCC):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    val = uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, val | (0xF << 20))
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x003D0000, 0x10000)
    uc.mem_map(STACK_ADDR, STACK_SIZE)
    uc.mem_map(OBJ_ADDR, OBJ_SIZE)
    uc.mem_map(RODATA_ADDR, 0x10000)
    uc.mem_map(TRAP_ADDR, 0x1000)

    uc.mem_write(FUNC_ADDR, code_bytes)
    uc.mem_write(OBJ_ADDR, bytes([dirty_byte]) * OBJ_SIZE)
    if rodata_bytes:
        uc.mem_write(RODATA_ADDR, rodata_bytes)

    uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, preset_id)
    uc.reg_write(arm.UC_ARM_REG_R2, slot_id)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_ADDR + 0x8000)
    uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)

    uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
    return uc.mem_read(OBJ_ADDR, OBJ_SIZE)

def main():
    orig_code = get_orig_bytes()
    cand_raw, relocs, rodata = compile_candidate()
    cand_code = apply_relocations(cand_raw, relocs)
    print(f"Original size: {len(orig_code)} B, Candidate size: {len(cand_raw)} B, Relocs: {len(relocs)}, Rodata: {len(rodata)} B")

    # Test cases: (preset_id, slot_id, dirty_byte)
    test_cases = [
        # Presets 0..5 on default slot (0)
        (0, 0, 0xCC),
        (1, 0, 0xAA),
        (2, 0, 0x55),
        (3, 0, 0x33),
        (4, 0, 0x77),
        (5, 0, 0x99),
        # Slot 1 (offset 0x5AC)
        (0, 1, 0x11),
        (1, 1, 0x22),
        (2, 1, 0x33),
        (3, 1, 0x44),
        # Slot 2 (offset 0x5F0)
        (1, 2, 0x55),
        (3, 2, 0x66),
        (5, 2, 0x77),
        # Other slot values (default to 0x568)
        (2, 3, 0x88),
        (4, 99, 0x99),
        # Presets >= 6 (no-op)
        (6, 0, 0xEE),
        (7, 1, 0xDD),
        (100, 2, 0xBB),
    ]

    all_passed = True
    for i, (preset, slot, dirty) in enumerate(test_cases):
        mem_orig = run_unicorn(orig_code, preset, slot, dirty_byte=dirty)
        mem_cand = run_unicorn(cand_code, preset, slot, rodata_bytes=rodata, dirty_byte=dirty)

        if mem_orig == mem_cand:
            print(f"Case {i+1:2d} (preset={preset:3d}, slot={slot:2d}): PASS [identical 4096-byte memory state]")
        else:
            print(f"Case {i+1:2d} (preset={preset:3d}, slot={slot:2d}): FAIL!")
            for off in range(0, OBJ_SIZE, 4):
                w_orig = struct.unpack_from("<I", mem_orig, off)[0]
                w_cand = struct.unpack_from("<I", mem_cand, off)[0]
                if w_orig != w_cand:
                    print(f"  Mismatch at offset 0x{off:03X}: orig=0x{w_orig:08X}, cand=0x{w_cand:08X}")
            all_passed = False

    if all_passed:
        print("\nALL TEST CASES PASSED!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
