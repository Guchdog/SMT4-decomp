#!/usr/bin/env python3
"""Differential test for engine_func_003e9ba8 (0x003e9ba8) using Unicorn ARM emulation."""

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
FUNC_ADDR = 0x003e9ba8
FUNC_SIZE = 652

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
OBJ_ADDR = 0x00600000
TARGET_ADDR = 0x00610000
DATA_ADDR = 0x00620000
TRAP_ADDR = 0x90000000

MOCK_2C2BE8_ADDR = 0x002c2be8

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
    out_dir = ROOT / "build/test_leaf_003e9ba8"
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_file = out_dir / "leaf_batch45_a.o"
    src_file = ROOT / "src/engine/leaf_batch45_a.cpp"
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    func_sym_offset = get_symbol_offset(obj_file, "003e9ba8")
    for k in funcs:
        if "engine_func_003e9ba8" in k or "003e9ba8" in k:
            return funcs[k][0], funcs[k][1], func_sym_offset
    raise KeyError("engine_func_003e9ba8 not found in compiled object")

def apply_relocations(code_bytes, relocs, func_sym_offset):
    fixed = bytearray(code_bytes)
    for rel in relocs:
        offset = rel.offset
        sym = rel.symbol_name
        target = 0
        if "engine_func_002c2be8" in sym or sym == "002c2be8":
            target = MOCK_2C2BE8_ADDR

        if rel.relocation_type in (28, 29, 10): # R_ARM_CALL / R_ARM_JUMP24 / R_ARM_THM_CALL
            pc = FUNC_ADDR + offset + 8
            disp = (target - pc) >> 2
            insn = struct.unpack_from("<I", fixed, offset)[0]
            insn = (insn & 0xFF000000) | (disp & 0x00FFFFFF)
            struct.pack_into("<I", fixed, offset, insn)
        elif rel.relocation_type == 2: # R_ARM_ABS32
            orig_addend = struct.unpack_from("<I", fixed, offset)[0]
            target = FUNC_ADDR + (orig_addend - func_sym_offset)
            struct.pack_into("<I", fixed, offset, target)
    return bytes(fixed)

def setup_emulator(code_bytes):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    val = uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, val | (0xF << 20))
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x003e0000, 0x10000)
    uc.mem_map(0x002c0000, 0x10000) # Covers MOCK_2C2BE8_ADDR
    uc.mem_map(STACK_ADDR, STACK_SIZE)
    uc.mem_map(OBJ_ADDR, 0x10000)
    uc.mem_map(TARGET_ADDR, 0x10000)
    uc.mem_map(DATA_ADDR, 0x10000)
    uc.mem_map(TRAP_ADDR, 0x1000)

    uc.mem_write(FUNC_ADDR, code_bytes)

    # Stub 0x2c2be8 with mock that packs clamp(rgba)*255
    def hook_2c2be8(uc, address, size, user_data):
        if address == MOCK_2C2BE8_ADDR:
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            rgba = struct.unpack("<4f", uc.mem_read(r0, 16))
            r = min(255, max(0, int(rgba[0] * 255.0 + 0.5)))
            g = min(255, max(0, int(rgba[1] * 255.0 + 0.5)))
            b = min(255, max(0, int(rgba[2] * 255.0 + 0.5)))
            a = min(255, max(0, int(rgba[3] * 255.0 + 0.5)))
            packed = (a << 24) | (b << 16) | (g << 8) | r
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            uc.reg_write(arm.UC_ARM_REG_R0, packed)
            uc.reg_write(arm.UC_ARM_REG_PC, lr)
    uc.hook_add(unicorn.UC_HOOK_CODE, hook_2c2be8)

    return uc

def run_test_case(code_bytes, type_val, data_floats, init_target_near_far=(0.0, 0.0)):
    uc = setup_emulator(code_bytes)

    # Setup obj struct
    uc.mem_write(OBJ_ADDR, struct.pack("<I", OBJ_ADDR + 0x20))
    uc.mem_write(OBJ_ADDR + 0x20 + 0x14, struct.pack("<I", type_val))

    # Clear target mem and set near/far
    uc.mem_write(TARGET_ADDR, bytes(0x200))
    uc.mem_write(TARGET_ADDR + 0x120, struct.pack("<f", init_target_near_far[0]))
    uc.mem_write(TARGET_ADDR + 0x124, struct.pack("<f", init_target_near_far[1]))

    # Setup data
    uc.mem_write(DATA_ADDR, struct.pack(f"<{len(data_floats)}f", *data_floats))

    uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, TARGET_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R2, DATA_ADDR)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_ADDR + 0x8000)
    uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
    uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)

    # Read modified target region (0xBC .. 0x130 = 116 bytes)
    return uc.mem_read(TARGET_ADDR + 0xBC, 116)

def main():
    orig_code = get_orig_bytes()
    cand_raw, relocs, func_sym_offset = compile_candidate()
    cand_code = apply_relocations(cand_raw, relocs, func_sym_offset)
    print(f"Original size: {len(orig_code)} B, Candidate size: {len(cand_raw)} B, Relocs: {len(relocs)}")

    cases = [
        # Case 0: Ambient color
        (0, [0.1, 0.2, 0.3, 1.0], (0.0, 0.0)),
        (0, [1.0, 0.0, 0.5, 0.8], (0.0, 0.0)),
        # Case 1: Diffuse color
        (1, [0.5, 0.6, 0.7, 1.0], (0.0, 0.0)),
        # Case 2: Specular 0
        (2, [0.8, 0.8, 0.8, 0.0], (0.0, 0.0)),
        # Case 3: Specular 1
        (3, [0.0, 1.0, 0.0, 1.0], (0.0, 0.0)),
        # Case 4: Light direction vector
        (4, [0.0, 3.0, 4.0], (0.0, 0.0)),
        (4, [1.0, 1.0, 1.0], (0.0, 0.0)),
        (4, [-2.0, 3.0, -6.0], (0.0, 0.0)),
        # Case 5: Fog near (target far = 100.0)
        (5, [10.0], (0.0, 100.0)),
        (5, [0.0], (0.0, 50.0)),
        (5, [99.995], (0.0, 100.0)), # Epsilon clamp check
        # Case 6: Fog far (target near = 10.0)
        (6, [100.0], (10.0, 0.0)),
        (6, [200.0], (20.0, 0.0)),
        (6, [10.005], (10.0, 0.0)), # Epsilon clamp check
        # Out of range type (7, 10)
        (7, [1.0, 2.0, 3.0, 4.0], (0.0, 0.0)),
        (10, [1.0, 2.0, 3.0, 4.0], (0.0, 0.0)),
    ]

    all_passed = True
    for i, (type_val, data_floats, init_nf) in enumerate(cases):
        orig_out = run_test_case(orig_code, type_val, data_floats, init_nf)
        cand_out = run_test_case(cand_code, type_val, data_floats, init_nf)

        if orig_out == cand_out:
            print(f"Case {i+1:2d} (type={type_val}): PASS")
        else:
            print(f"Case {i+1:2d} (type={type_val}): FAIL!")
            print(f"  Orig: {orig_out[:32]}")
            print(f"  Cand: {cand_out[:32]}")
            all_passed = False

    if all_passed:
        print("\nALL TEST CASES PASSED!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
