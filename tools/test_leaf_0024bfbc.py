#!/usr/bin/env python3
"""Differential test for camp_func_0024bfbc (0x0024bfbc) using Unicorn ARM emulation."""

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
FUNC_ADDR = 0x0024bfbc
FUNC_SIZE = 528

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
BUF_ADDR = 0x00600000
BUF_SIZE = 64
RODATA_ADDR = 0x00700000
RODATA_STR_ADDR = 0x00710000
TRAP_ADDR = 0x90000000

VENEER_ADDR = 0x002BE7F4

def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)

def get_elf_sections_and_relocs(path):
    data = Path(path).read_bytes()
    e_shoff, e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<IIHH", data, 32)[0], struct.unpack_from("<H", data, 46)[0], struct.unpack_from("<H", data, 48)[0], struct.unpack_from("<H", data, 50)[0]
    sections = [struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    
    sec_dict = {}
    for i, s in enumerate(sections):
        end = shstrtab.find(b"\x00", s[0])
        name = shstrtab[s[0]:end].decode("ascii", errors="replace")
        sec_dict[name] = data[s[4] : s[4] + s[5]]
        
    return sec_dict

def compile_candidate():
    out_dir = ROOT / "build/test_leaf_0024bfbc"
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_file = out_dir / "leaf_batch45_a.o"
    src_file = ROOT / "src/engine/leaf_batch45_a.cpp"
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    secs = get_elf_sections_and_relocs(obj_file)
    rodata = bytearray(secs.get(".rodata", b""))
    rodata_str = secs.get(".rodata.str1.1", b"")
    rel_rodata = secs.get(".rel.rodata", b"")

    # Relocate .rodata table
    for i in range(len(rel_rodata) // 8):
        off, info = struct.unpack_from("<II", rel_rodata, i * 8)
        rel_type = info & 0xFF
        if rel_type == 2: # R_ARM_ABS32
            orig_addend = struct.unpack_from("<I", rodata, off)[0]
            struct.pack_into("<I", rodata, off, RODATA_STR_ADDR + orig_addend)

    for k in funcs:
        if "camp_func_0024bfbc" in k or "0024bfbc" in k:
            return funcs[k][0], funcs[k][1], bytes(rodata), rodata_str
    raise KeyError("camp_func_0024bfbc not found in compiled object")

def apply_relocations(code_bytes, relocs):
    fixed = bytearray(code_bytes)
    for rel in relocs:
        offset = rel.offset
        sym = rel.symbol_name
        target = 0
        if "ui_func_002be7fc" in sym or sym == "002be7fc":
            target = VENEER_ADDR
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

def setup_emulator(code_bytes, rodata_bytes=None, rodata_str_bytes=None):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)

    uc.mem_map(0x00240000, 0x10000)
    uc.mem_map(0x002B0000, 0x10000) # Covers VENEER_ADDR
    uc.mem_map(STACK_ADDR, STACK_SIZE)
    uc.mem_map(BUF_ADDR, 0x10000)
    uc.mem_map(RODATA_ADDR, 0x10000)
    uc.mem_map(RODATA_STR_ADDR, 0x10000)
    uc.mem_map(TRAP_ADDR, 0x1000)

    uc.mem_write(FUNC_ADDR, code_bytes)
    if rodata_bytes:
        uc.mem_write(RODATA_ADDR, rodata_bytes)
    if rodata_str_bytes:
        uc.mem_write(RODATA_STR_ADDR, rodata_str_bytes)

    # Stub veneer with bx lr
    uc.mem_write(VENEER_ADDR, b"\x1e\xff\x2f\xe1")

    # Hook veneer execution to simulate UiFont_FormatString
    def hook_veneer(uc, address, size, user_data):
        if address == VENEER_ADDR:
            dst_ptr = uc.reg_read(arm.UC_ARM_REG_R0)
            fmt_ptr = uc.reg_read(arm.UC_ARM_REG_R1)
            # Read null-terminated string from fmt_ptr
            str_data = bytearray()
            p = fmt_ptr
            while True:
                b = uc.mem_read(p, 1)[0]
                str_data.append(b)
                if b == 0:
                    break
                p += 1
            # Copy to dst_ptr
            uc.mem_write(dst_ptr, bytes(str_data))
            # Return string length
            length = len(str_data) - 1
            uc.reg_write(arm.UC_ARM_REG_R0, length)
            # Return via LR
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            uc.reg_write(arm.UC_ARM_REG_PC, lr)

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_veneer)
    return uc

def run_function(uc, element_id, dirty_byte=0xCC):
    uc.mem_write(BUF_ADDR, bytes([dirty_byte]) * BUF_SIZE)
    uc.reg_write(arm.UC_ARM_REG_R0, BUF_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, element_id)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_ADDR + 0x8000)
    uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)

    uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
    ret_val = uc.reg_read(arm.UC_ARM_REG_R0)
    buf_out = uc.mem_read(BUF_ADDR, BUF_SIZE)
    return ret_val, buf_out

def main():
    orig_code = get_orig_bytes()
    cand_raw, relocs, rodata, rodata_str = compile_candidate()
    cand_code = apply_relocations(cand_raw, relocs)
    print(f"Original size: {len(orig_code)} B, Candidate size: {len(cand_raw)} B, Relocs: {len(relocs)}, Rodata: {len(rodata)} B, RodataStr: {len(rodata_str)} B")

    # Test cases: all valid elements + gaps + invalid values
    test_cases = [
        0, 1, 2, 3, 4, 5, 6, 7,     # Phys, Gun, Fire, Ice, Elec, Force, Light, Dark
        8, 9, 10,                   # Gaps (invalid)
        11, 12, 13, 14, 15, 16, 17, 18, # Poison, Panic, Sleep, Bind, Sick, Lost, Almighty, Heal
        19, 20, 100, 0xFFFFFFFF     # Invalid / out of range
    ]

    all_passed = True
    for i, elem_id in enumerate(test_cases):
        uc_orig = setup_emulator(orig_code)
        ret_orig, buf_orig = run_function(uc_orig, elem_id)

        uc_cand = setup_emulator(cand_code, rodata, rodata_str)
        ret_cand, buf_cand = run_function(uc_cand, elem_id)

        match = (ret_orig == ret_cand) and (buf_orig == buf_cand)
        if match:
            # decode string if valid
            s = buf_cand[:buf_cand.find(b"\x00")].decode("shift_jis", errors="replace") if ret_cand > 0 else "<none>"
            s_safe = s.encode("ascii", "backslashreplace").decode("ascii")
            print(f"Case {i+1:2d} (elem=0x{elem_id:02X}): PASS [ret={ret_cand}, str={repr(s_safe)}]")
        else:
            print(f"Case {i+1:2d} (elem=0x{elem_id:02X}): FAIL!")
            print(f"  Orig: ret={ret_orig}, buf={buf_orig[:16]}")
            print(f"  Cand: ret={ret_cand}, buf={buf_cand[:16]}")
            all_passed = False

    if all_passed:
        print("\nALL TEST CASES PASSED!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
