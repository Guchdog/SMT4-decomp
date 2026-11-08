#!/usr/bin/env python3
"""Differential test for ui_func_002580a8 (0x002580a8) using Unicorn ARM emulation."""

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
FUNC_ADDR = 0x002580a8
FUNC_SIZE = 576

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
STATE_ADDR = 0x00600000
RODATA_ADDR = 0x00700000
TRAP_ADDR = 0x90000000

RAND_FUNC_ADDR = 0x00297004

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
    out_dir = ROOT / "build/test_leaf_002580a8"
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_file = out_dir / "leaf_batch45_a.o"
    src_file = ROOT / "src/engine/leaf_batch45_a.cpp"
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    rodata = get_elf_section(obj_file, ".rodata")
    for k in funcs:
        if "ui_func_002580a8" in k or "002580a8" in k:
            return funcs[k][0], funcs[k][1], rodata
    raise KeyError("ui_func_002580a8 not found in compiled object")

def apply_relocations(code_bytes, relocs):
    fixed = bytearray(code_bytes)
    for rel in relocs:
        offset = rel.offset
        sym = rel.symbol_name
        target = 0
        if "ui_func_00297004" in sym or sym == "00297004":
            target = RAND_FUNC_ADDR
        elif sym == "": # rodata literal
            target = RODATA_ADDR

        if rel.relocation_type in (28, 29, 10): # R_ARM_CALL / R_ARM_JUMP24 / R_ARM_THM_CALL
            pc = FUNC_ADDR + offset + 8
            disp = (target - pc) >> 2
            insn = struct.unpack_from("<I", fixed, offset)[0]
            insn = (insn & 0xFF000000) | (disp & 0x00FFFFFF)
            struct.pack_into("<I", fixed, offset, insn)
        elif rel.relocation_type == 2: # R_ARM_ABS32
            orig_addend = struct.unpack_from("<I", fixed, offset)[0]
            struct.pack_into("<I", fixed, offset, RODATA_ADDR + orig_addend)
    return bytes(fixed)

def setup_emulator(code_bytes, rodata_bytes=None, rand_sequence=None):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    val = uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, val | (0xF << 20))
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00250000, 0x10000)
    uc.mem_map(0x00290000, 0x10000) # Covers RAND_FUNC_ADDR
    uc.mem_map(STACK_ADDR, STACK_SIZE)
    uc.mem_map(STATE_ADDR, 0x1000)
    uc.mem_map(RODATA_ADDR, 0x10000)
    uc.mem_map(TRAP_ADDR, 0x1000)

    uc.mem_write(FUNC_ADDR, code_bytes)
    if rodata_bytes:
        uc.mem_write(RODATA_ADDR, rodata_bytes)

    # Mock rand func to return deterministic values from sequence
    if rand_sequence is not None:
        seq = list(rand_sequence)
        idx = [0]
        def hook_rand(uc, address, size, user_data):
            if address == RAND_FUNC_ADDR:
                min_v = uc.reg_read(arm.UC_ARM_REG_R0)
                max_v = uc.reg_read(arm.UC_ARM_REG_R1)
                lr = uc.reg_read(arm.UC_ARM_REG_LR)
                if idx[0] < len(seq):
                    val = seq[idx[0]]
                    idx[0] += 1
                else:
                    val = min_v
                # Clamp or use directly
                uc.reg_write(arm.UC_ARM_REG_R0, val)
                uc.reg_write(arm.UC_ARM_REG_PC, lr)
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_rand)

    return uc

def run_test_case(code_bytes, rodata_bytes, initial_state, rand_seq):
    uc = setup_emulator(code_bytes, rodata_bytes, rand_seq)
    uc.mem_write(STATE_ADDR, struct.pack("<ffffhh", *initial_state))
    uc.reg_write(arm.UC_ARM_REG_R0, STATE_ADDR)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_ADDR + 0x8000)
    uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
    uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
    out = uc.mem_read(STATE_ADDR, 20)
    return struct.unpack("<ffffhh", out)

def main():
    orig_code = get_orig_bytes()
    cand_raw, relocs, rodata = compile_candidate()
    cand_code = apply_relocations(cand_raw, relocs)
    print(f"Original size: {len(orig_code)} B, Candidate size: {len(cand_raw)} B, Relocs: {len(relocs)}, Rodata: {len(rodata)} B")

    # Differential test cases
    # (amp_x, amp_y, off_x, off_y, max_timer, cur_timer), rand_seq
    cases = [
        # 1. Finished shake (max_timer <= cur_timer): resets struct
        ((10.0, 10.0, 5.0, 5.0, 10, 10), [0, 0, 0, 0, 0]),
        ((10.0, 10.0, 5.0, 5.0, 10, 11), [0, 0, 0, 0, 0]),
        # 2. Warmup negative cur_timer
        ((10.0, 10.0, 5.0, 5.0, 10, -3), [0, 0, 0, 0, 0]),
        ((10.0, 10.0, 5.0, 5.0, 10, -1), [0, 0, 0, 0, 0]),
        # 3. Continuous shake (max_timer == -1)
        ((10.0, 20.0, 0.0, 0.0, -1, 0), [750, 1500, 0, 0]),
        ((10.0, 20.0, 0.0, 0.0, -1, 0), [750, 1500, 1, 1]),
        # 4. Standard shake initial frame (prev_x = 0, prev_y = 0)
        ((10.0, 10.0, 0.0, 0.0, 10, 0), [1000, 1000, 0, 0]),
        ((10.0, 10.0, 0.0, 0.0, 10, 0), [1000, 1000, 1, 1]),
        ((10.0, 10.0, 0.0, 0.0, 10, 0), [500, 800, 0, 1]),
        # 5. Damping frames (remaining <= 3)
        ((10.0, 10.0, 2.0, 2.0, 10, 7), [500, 500, 0, 0, 0]), # rem = 3 -> damping = 0.75
        ((10.0, 10.0, 2.0, 2.0, 10, 8), [500, 500, 0, 0, 1]), # rem = 2 -> damping = 0.50
        ((10.0, 10.0, 2.0, 2.0, 10, 9), [500, 500, 1, 1, 0]), # rem = 1 -> damping = 0.25
        # 6. Direction logic: prev_x != 0, prev_y == 0
        ((10.0, 10.0, 5.0, 0.0, 10, 2), [800, 800, 0, 0]),
        ((10.0, 10.0, -5.0, 0.0, 10, 2), [800, 800, 1, 1]),
        # 7. Direction logic: prev_x == 0, prev_y != 0
        ((10.0, 10.0, 0.0, 5.0, 10, 2), [800, 800, 0, 0]),
        ((10.0, 10.0, 0.0, -5.0, 10, 2), [800, 800, 1, 1]),
        # 8. Direction logic: both prev_x != 0 and prev_y != 0 with coin flip 0 and 1
        ((10.0, 10.0, 5.0, 5.0, 10, 2), [800, 800, 0, 0, 0]),
        ((10.0, 10.0, 5.0, 5.0, 10, 2), [800, 800, 0, 0, 1]),
        ((10.0, 10.0, -5.0, -5.0, 10, 2), [800, 800, 1, 1, 0]),
        ((10.0, 10.0, -5.0, -5.0, 10, 2), [800, 800, 1, 1, 1]),
        # 9. Timer boundary at 0x7FFE (32766)
        ((10.0, 10.0, 0.0, 0.0, -1, 32765), [1000, 1000, 0, 0]),
        ((10.0, 10.0, 0.0, 0.0, -1, 32766), [1000, 1000, 0, 0]),
    ]

    all_passed = True
    for i, (state, rand_seq) in enumerate(cases):
        orig_res = run_test_case(orig_code, None, state, rand_seq)
        cand_res = run_test_case(cand_code, rodata, state, rand_seq)

        # Compare float fields with small epsilon
        match = True
        for idx in range(4):
            if abs(orig_res[idx] - cand_res[idx]) > 1e-4:
                match = False
                break
        if orig_res[4:] != cand_res[4:]:
            match = False

        if match:
            print(f"Case {i+1:2d}: PASS [timer={cand_res[5]}, off=({cand_res[2]:.2f}, {cand_res[3]:.2f})]")
        else:
            print(f"Case {i+1:2d}: FAIL!")
            print(f"  Orig: {orig_res}")
            print(f"  Cand: {cand_res}")
            all_passed = False

    if all_passed:
        print("\nALL TEST CASES PASSED!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
