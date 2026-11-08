#!/usr/bin/env python3
"""Differential execution test for 180 texture conversion leaf functions.

Verifies src/engine/tex_conv_leaves_170.cpp (stride 0x400),
tex_conv_leaves_177.cpp (stride 0x100), and tex_conv_leaves_17d.cpp (stride 0x200)
compiled with clang against original ARM code from extracted/exefs/code.bin in Unicorn emulator.
"""

import sys
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = Path('extracted/exefs/code.bin')
ORIG_DATA = CODE_PATH.read_bytes()

CODE_BASE = 0x00100000
CODE_SIZE = 0x00500000
SRC_BUF = 0x02000000
DST_BUF = 0x02100000
STACK_ADDR = 0x03000000
BUF_SIZE = 0x00100000
PATTERN_DATA = bytes(((i * 7 + 13) % 256) for i in range(0x10000))

BLOCKS = [
    ('src/engine/tex_conv_leaves_170.cpp', '0x400'),
    ('src/engine/tex_conv_leaves_177.cpp', '0x100'),
    ('src/engine/tex_conv_leaves_17d.cpp', '0x200'),
]

def run_tests():
    build_dir = Path('build/test_tex_conv_experiment')
    build_dir.mkdir(parents=True, exist_ok=True)
    
    total_passed = 0
    total_failed = 0
    
    for file_path_str, stride_str in BLOCKS:
        src_path = Path(file_path_str)
        obj_path = build_dir / f"{src_path.stem}.o"
        
        print(f"Compiling {src_path} (stride {stride_str})...")
        res = compile_tu_armv6k(src_path, obj_path, repo_root=Path('.'))
        if res.returncode != 0:
            print(f"Compilation error for {src_path}:", res.stderr)
            sys.exit(1)
            
        dec_funcs = extract_elf_functions_detailed(obj_path)
        
        # Parse functions from source file
        f_text = src_path.read_text(encoding='utf-8')
        f_funcs = re.findall(r'// DECOMP_FUNC\((0x[0-9a-fA-F]+),\s*(\d+)\)\s*\nextern "C" void\s+([a-zA-Z0-9_]+)\(', f_text)
        assert len(f_funcs) == 60, f"Expected 60 funcs, got {len(f_funcs)}"
        
        block_passed = 0
        block_failed = 0
        
        for orig_addr_str, orig_sz_str, func_name in f_funcs:
            orig_addr = int(orig_addr_str, 16)
            
            if func_name not in dec_funcs:
                print(f"[{func_name}] Missing symbol in ELF!")
                block_failed += 1
                continue
                
            dec_code = dec_funcs[func_name][0]
            
            # Differential execution with count = 4
            # 1. Original in code.bin
            uc_orig = Uc(UC_ARCH_ARM, UC_MODE_ARM)
            uc_orig.mem_map(CODE_BASE, CODE_SIZE, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
            uc_orig.mem_map(SRC_BUF, BUF_SIZE, UC_PROT_READ | UC_PROT_WRITE)
            uc_orig.mem_map(DST_BUF, BUF_SIZE, UC_PROT_READ | UC_PROT_WRITE)
            uc_orig.mem_map(STACK_ADDR, BUF_SIZE, UC_PROT_READ | UC_PROT_WRITE)
            uc_orig.mem_write(CODE_BASE, ORIG_DATA)
            uc_orig.mem_write(SRC_BUF, PATTERN_DATA)
            uc_orig.reg_write(UC_ARM_REG_R0, SRC_BUF + 0x1000)
            uc_orig.reg_write(UC_ARM_REG_R1, DST_BUF + 0x1000)
            uc_orig.reg_write(UC_ARM_REG_R2, 4)
            uc_orig.reg_write(UC_ARM_REG_SP, STACK_ADDR + 0x8000)
            uc_orig.reg_write(UC_ARM_REG_LR, 0x0)
            try:
                uc_orig.emu_start(orig_addr, 0x0, timeout=100000)
            except Exception as e:
                print(f"[{func_name}] Orig execution error: {e}")
                block_failed += 1
                continue
            dst_orig = uc_orig.mem_read(DST_BUF + 0x1000, 0x2000)
            
            # 2. Decompiled ARMv6K code
            uc_dec = Uc(UC_ARCH_ARM, UC_MODE_ARM)
            uc_dec.mem_map(CODE_BASE, CODE_SIZE, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
            uc_dec.mem_map(SRC_BUF, BUF_SIZE, UC_PROT_READ | UC_PROT_WRITE)
            uc_dec.mem_map(DST_BUF, BUF_SIZE, UC_PROT_READ | UC_PROT_WRITE)
            uc_dec.mem_map(STACK_ADDR, BUF_SIZE, UC_PROT_READ | UC_PROT_WRITE)
            uc_dec.mem_write(CODE_BASE, ORIG_DATA)
            uc_dec.mem_write(0x00380000, dec_code)
            uc_dec.mem_write(SRC_BUF, PATTERN_DATA)
            uc_dec.reg_write(UC_ARM_REG_R0, SRC_BUF + 0x1000)
            uc_dec.reg_write(UC_ARM_REG_R1, DST_BUF + 0x1000)
            uc_dec.reg_write(UC_ARM_REG_R2, 4)
            uc_dec.reg_write(UC_ARM_REG_SP, STACK_ADDR + 0x8000)
            uc_dec.reg_write(UC_ARM_REG_LR, 0x0)
            try:
                uc_dec.emu_start(0x00380000, 0x0, timeout=100000)
            except Exception as e:
                print(f"[{func_name}] Dec execution error: {e}")
                block_failed += 1
                continue
            dst_dec = uc_dec.mem_read(DST_BUF + 0x1000, 0x2000)
            
            if dst_orig == dst_dec:
                block_passed += 1
            else:
                print(f"[{func_name}] Destination buffer mismatch!")
                block_failed += 1
                
        print(f"  Result for {src_path.name}: {block_passed}/60 passed, {block_failed} failed")
        total_passed += block_passed
        total_failed += block_failed
        
    print(f"\n==========================================")
    print(f"TOTAL: {total_passed}/180 functions passed differential testing.")
    print(f"==========================================")
    assert total_passed == 180 and total_failed == 0, f"Some functions failed! ({total_failed} failed)"
    return True

if __name__ == '__main__':
    run_tests()
