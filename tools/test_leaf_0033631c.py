#!/usr/bin/env python3
"""Differential test for script_vm_func_0033631c (0x0033631c) using Unicorn ARM emulation."""

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
FUNC_ADDR = 0x0033631c
FUNC_SIZE = 640

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
CTX_ADDR = 0x00600000
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
    out_dir = ROOT / "build/test_leaf_0033631c"
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_file = out_dir / "leaf_batch45_a.o"
    src_file = ROOT / "src/engine/leaf_batch45_a.cpp"
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    func_sym_offset = get_symbol_offset(obj_file, "0033631c")
    for k in funcs:
        if "script_vm_func_0033631c" in k or "0033631c" in k:
            return funcs[k][0], funcs[k][1], func_sym_offset
    raise KeyError("script_vm_func_0033631c not found in compiled object")

def apply_relocations(code_bytes, relocs, func_sym_offset):
    fixed = bytearray(code_bytes)
    for rel in relocs:
        offset = rel.offset
        if rel.relocation_type == 2: # R_ARM_ABS32
            orig_addend = struct.unpack_from("<I", fixed, offset)[0]
            target = FUNC_ADDR + (orig_addend - func_sym_offset)
            struct.pack_into("<I", fixed, offset, target)
    return bytes(fixed)

def setup_emulator(code_bytes):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    val = uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, val | (0xF << 20))
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00330000, 0x10000)
    uc.mem_map(STACK_ADDR, STACK_SIZE)
    uc.mem_map(CTX_ADDR, 0x10000)
    uc.mem_map(TRAP_ADDR, 0x1000)

    uc.mem_write(FUNC_ADDR, code_bytes)
    return uc

def run_test(code_bytes, state, step, max_steps, cur_color, start_color, end_color, channel=0):
    uc = setup_emulator(code_bytes)
    base = CTX_ADDR + channel * 4
    uc.mem_write(base + 0x4A0C, struct.pack("<I", cur_color))
    uc.mem_write(base + 0x4A14, struct.pack("<I", start_color))
    uc.mem_write(base + 0x4A1C, struct.pack("<I", end_color))
    uc.mem_write(base + 0x4A24, struct.pack("<I", state))
    uc.mem_write(base + 0x4A2C, struct.pack("<i", step))
    uc.mem_write(base + 0x4A34, struct.pack("<i", max_steps))

    uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, channel)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_ADDR + 0x8000)
    uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
    uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)

    new_cur = struct.unpack("<I", uc.mem_read(base + 0x4A0C, 4))[0]
    new_state = struct.unpack("<I", uc.mem_read(base + 0x4A24, 4))[0]
    new_step = struct.unpack("<i", uc.mem_read(base + 0x4A2C, 4))[0]
    return new_cur, new_state, new_step

def main():
    orig_code = get_orig_bytes()
    cand_raw, relocs, func_sym_offset = compile_candidate()
    cand_code = apply_relocations(cand_raw, relocs, func_sym_offset)
    print(f"Original size: {len(orig_code)} B, Candidate size: {len(cand_code)} B, Relocs: {len(relocs)}")

    # Test cases covering states 0..7, channel 0 and 1, steps 0..max, boundaries
    cases = [
        # (state, step, max_steps, cur_color, start_color, end_color, channel)
        (0, 0, 10, 0, 0xFF000000, 0x00FF0000, 0),
        (0, 0, 10, 0, 0xFF000000, 0x00FF0000, 1),
        (1, 0, 10, 0, 0xFF000000, 0x00FF0000, 0),
        (1, 1, 10, 0, 0xFF000000, 0x00FF0000, 0),
        (1, 5, 10, 0, 0xFF000000, 0x00FF0000, 0),
        (1, 8, 10, 0, 0xFF000000, 0x00FF0000, 0),
        (1, 9, 10, 0, 0xFF000000, 0x00FF0000, 0), # Reaches max_steps
        (2, 10, 10, 0, 0xFF000000, 0x00FF0000, 0),
        (3, 10, 10, 0x00FF0000, 0xFF000000, 0x00FF0000, 0),
        (4, 0, 10, 0, 0x00FF0000, 0xFF000000, 0),
        (4, 0, 10, 0, 0x00FF0000, 0xFF000000, 1),
        (5, 0, 10, 0, 0x00FF0000, 0xFF000000, 0),
        (5, 1, 10, 0, 0x00FF0000, 0xFF000000, 0),
        (5, 5, 10, 0, 0x00FF0000, 0xFF000000, 0),
        (5, 8, 10, 0, 0x00FF0000, 0xFF000000, 0),
        (5, 9, 10, 0, 0x00FF0000, 0xFF000000, 0), # Reaches max_steps
        (6, 10, 10, 0, 0x00FF0000, 0xFF000000, 0),
        (7, 10, 10, 0xFF000000, 0x00FF0000, 0xFF000000, 0),
        (8, 0, 10, 0x12345678, 0, 0, 0), # Out of range state
        # Full RGBA blend
        (1, 4, 16, 0, 0x80402010, 0x10204080, 0),
        (5, 4, 16, 0, 0x80402010, 0x10204080, 0),
    ]

    all_passed = True
    for i, c in enumerate(cases):
        orig_out = run_test(orig_code, *c)
        cand_out = run_test(cand_code, *c)

        if orig_out == cand_out:
            print(f"Case {i+1:2d} (state={c[0]}, step={c[1]}/{c[2]}): PASS -> cur=0x{cand_out[0]:08X}, state={cand_out[1]}, step={cand_out[2]}")
        else:
            print(f"Case {i+1:2d} (state={c[0]}, step={c[1]}/{c[2]}): FAIL!")
            print(f"  Orig: {orig_out}")
            print(f"  Cand: {cand_out}")
            all_passed = False

    if all_passed:
        print("\nALL TEST CASES PASSED!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
