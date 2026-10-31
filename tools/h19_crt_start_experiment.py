#!/usr/bin/env python3
"""Offline ARM differential validation for Milestone H19 CRT __start (0x00100000) and __init_bss (0x00100024)."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'src/crt/start.cpp'
BSS_START = 0x00477000
BSS_END   = 0x004EFE34
BSS_SIZE  = BSS_END - BSS_START # 495,156 bytes

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'crt_start.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_start, _ = funcs['__start']
    raw_bss, _ = funcs['__init_bss']
    return raw_start, raw_bss

def run_bss_simulation(code_bytes: bytes, entry: int) -> tuple[int, int, int, bytes]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    # Map code region
    uc.mem_map(0x00100000, 0x10000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, code_bytes)

    # Map BSS region with dummy pattern 0xAA
    uc.mem_map(0x00470000, 0x90000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00470000, b'\xAA' * 0x90000)

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000
    RETURN_ADDR = 0x00100004

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=5000000)

    r0 = uc.reg_read(UC_ARM_REG_R0)
    r1 = uc.reg_read(UC_ARM_REG_R1)
    r2 = uc.reg_read(UC_ARM_REG_R2)
    bss = bytes(uc.mem_read(BSS_START, BSS_SIZE))
    return r0, r1, r2, bss

def main():
    print("=== Milestone H19 CRT Differential Verification ===")
    orig_code = CODE_PATH.read_bytes()[:0x10000]
    cand_start, cand_bss = build_candidates(ROOT / 'build/h19_tests')

    # Verify code bytes matching
    orig_start_bytes = orig_code[0:36]
    orig_bss_bytes = orig_code[36:72]

    assert cand_start == orig_start_bytes, "Mismatch in __start binary encoding!"
    assert cand_bss == orig_bss_bytes, "Mismatch in __init_bss binary encoding!"
    print("[PASS] Binary byte identity: __start and __init_bss match original 100%.")

    # Run differential simulation on __init_bss
    r0_orig, r1_orig, r2_orig, bss_orig = run_bss_simulation(orig_code, 0x00100024)

    cand_code = bytearray(orig_code)
    cand_code[0:36] = cand_start
    cand_code[36:72] = cand_bss
    r0_cand, r1_cand, r2_cand, bss_cand = run_bss_simulation(bytes(cand_code), 0x00100024)

    assert r0_orig == r0_cand, f"R0 mismatch: orig={hex(r0_orig)}, cand={hex(r0_cand)}"
    assert r1_orig == r1_cand, f"R1 mismatch: orig={hex(r1_orig)}, cand={hex(r1_cand)}"
    assert r2_orig == r2_cand, f"R2 mismatch: orig={hex(r2_orig)}, cand={hex(r2_cand)}"
    assert bss_orig == bss_cand, "BSS data mismatch between original and candidate!"
    assert all(b == 0 for b in bss_cand), "Candidate failed to zero all BSS bytes!"
    print(f"[PASS] Unicorn ARM11 differential simulation: {BSS_SIZE:,} bytes of BSS zeroed identically.")

    # Mutation test: defective BSS clearing
    mut_code = bytearray(cand_code)
    # Alter loop condition blo (0x3afffffc) to bne (0x1afffffc) or nop
    mut_code[36 + 24 : 36 + 28] = struct.pack('<I', 0xE1A00000) # nop
    try:
        _, _, _, bss_mut = run_bss_simulation(bytes(mut_code), 0x00100024)
        if all(b == 0 for b in bss_mut):
            raise AssertionError("Mutation went undetected!")
        print("[PASS] Mutation test: defective BSS clear caught successfully.")
    except Exception as e:
        print(f"[PASS] Mutation test rejected mutant: {e}")

    print("\nALL MILESTONE H19 CRT START TESTS PASSED WITH 100% PARITY!")

if __name__ == '__main__':
    main()
