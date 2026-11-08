#!/usr/bin/env python3
"""
Comprehensive Unicorn differential verification harness for all 125 functions
in src/ui/battle_hud_reset_batch.cpp (5,428 total bytes).
"""

import re
import struct
import sys
from pathlib import Path
import unicorn
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_LR

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / "extracted" / "exefs" / "code.bin"
ORIG_DATA = CODE_PATH.read_bytes()
SRC_PATH = ROOT / "src" / "ui" / "battle_hud_reset_batch.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00500000
STACK_BASE = 0x0FFFF000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x100

def create_emulator():
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)
    return uc

def main():
    print("Compiling src/ui/battle_hud_reset_batch.cpp...")
    build_dir = ROOT / "build" / "hud_reset_test"
    build_dir.mkdir(parents=True, exist_ok=True)
    obj = build_dir / "battle_hud_reset_batch.o"
    res = compile_tu_armv6k(SRC_PATH, obj, repo_root=ROOT)
    if res.returncode != 0:
        print("COMPILATION FAILED:")
        print(res.stderr)
        sys.exit(1)
    print("Compiled successfully. Extracting functions...")
    functions = extract_elf_functions_detailed(obj)

    text = SRC_PATH.read_text(encoding="utf-8")
    func_decls = re.findall(r'// DECOMP_FUNC\((0x[0-9a-fA-F]+),\s*(\d+)\)\s*\nvoid\s+([a-zA-Z0-9_]+)\(\)', text)
    print(f"Testing {len(func_decls)} functions with Unicorn differential tests...")

    TARGET_DECOMP = 0x00380000

    passed = 0
    total_bytes = 0

    for addr_str, sz_str, name in func_decls:
        addr = int(addr_str, 16)
        sz = int(sz_str)
        total_bytes += sz

        # Find compiled function bytes
        dec_code = None
        for mangled, (b, relocs) in functions.items():
            if name in mangled:
                dec_code = b
                break
        if dec_code is None:
            raise KeyError(f"Function {name} not found in compiled object")

        # Test original
        uc_orig = create_emulator()
        uc_orig.mem_write(CODE_BASE, ORIG_DATA)
        writes_orig = []
        def hook_orig(uc, access, address, size, value, user_data):
            writes_orig.append((address, size, value))
        uc_orig.hook_add(unicorn.UC_HOOK_MEM_WRITE, hook_orig)
        uc_orig.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc_orig.reg_write(UC_ARM_REG_LR, 0x00000000)
        uc_orig.emu_start(addr, 0x00000000, timeout=100000)

        # Test decompiled
        uc_dec = create_emulator()
        uc_dec.mem_write(CODE_BASE, ORIG_DATA)
        uc_dec.mem_write(TARGET_DECOMP, dec_code)
        writes_dec = []
        def hook_dec(uc, access, address, size, value, user_data):
            writes_dec.append((address, size, value))
        uc_dec.hook_add(unicorn.UC_HOOK_MEM_WRITE, hook_dec)
        uc_dec.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc_dec.reg_write(UC_ARM_REG_LR, 0x00000000)
        uc_dec.emu_start(TARGET_DECOMP, 0x00000000, timeout=100000)

        # Compare final state of all written memory locations
        assert len(writes_orig) > 0, f"No writes in original for {name}"
        assert len(writes_dec) > 0, f"No writes in decompiled for {name}"
        
        all_written_addrs = set(a for a, s, v in writes_orig) | set(a for a, s, v in writes_dec)
        for written_addr in all_written_addrs:
            val_orig = uc_orig.mem_read(written_addr, 4)
            val_dec = uc_dec.mem_read(written_addr, 4)
            assert val_orig == val_dec, f"Memory mismatch at {hex(written_addr)} for {name}: orig={val_orig.hex()}, dec={val_dec.hex()}"

        passed += 1

    print(f"\nALL {passed} FUNCTIONS ({total_bytes} BYTES) PASSED 100% UNICORN DIFFERENTIAL TEST!")

if __name__ == "__main__":
    main()
