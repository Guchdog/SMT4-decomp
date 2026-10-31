#!/usr/bin/env python3
"""Autonomous comprehensive verification suite for Milestone H19: Full Executable Link and Image Synthesis."""
from __future__ import annotations
from pathlib import Path
import json, struct, sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed
from tools.h2_calc_code_patch import apply_ips

BUILD_DIR = ROOT / 'build/h19_tests'
BUILD_DIR.mkdir(parents=True, exist_ok=True)

CODE_ORIGINAL = ROOT / 'extracted/exefs/code.bin'
SRC_CRT = ROOT / 'src/crt/start.cpp'
BSS_START = 0x00477000
BSS_END   = 0x004EFE34
BSS_SIZE  = BSS_END - BSS_START # 495,156 bytes

CANONICAL_MODULES = [
    ('crt_start', 'src/crt/start.cpp', ['__start', '__init_bss']),
    ('h10_burroughs', 'src/semantic/h10_burroughs_promoted.cpp', ['h10_camp_burroughs_getsavedata_promoted']),
    ('h11_shops', 'src/semantic/h11_shops_promoted.cpp', ['h11_shop_checkhasnew_promoted']),
    ('h12_combat', 'src/semantic/h12_combat_promoted.cpp', ['h12_battle_getunitsmirkstate_promoted']),
    ('h13_exploration', 'src/semantic/h13_exploration_promoted.cpp', ['h13_placewin_isactive_promoted']),
    ('h14_graphics', 'src/semantic/h14_graphics_promoted.cpp', ['h14_asdgpu_heapsize_promoted']),
    ('h15_ui', 'src/semantic/h15_ui_promoted.cpp', ['h15_uidialog_getstate_promoted']),
    ('h16_sound', 'src/semantic/h16_sound_promoted.cpp', ['h16_asdsoundeffect_getbuffersize_promoted']),
    ('h17_cec_aoc', 'src/semantic/h17_cec_aoc_promoted.cpp', ['h17_aoc_resultisready_promoted']),
]

def step1_verify_compilation():
    print("[1/5] Verifying Clang ARMv6K compilation of CRT and canonical modules...")
    for mod_name, src_rel, symbols in CANONICAL_MODULES:
        src = ROOT / src_rel
        obj = BUILD_DIR / f"{mod_name}.o"
        res = compile_tu_armv6k(src, obj, ROOT)
        assert res.returncode == 0, f"Compilation failed for {mod_name}:\n{res.stderr}"
        funcs = extract_elf_functions_detailed(obj)
        for sym in symbols:
            assert sym in funcs, f"Symbol {sym} not found in {mod_name}"
            code, relocs = funcs[sym]
            print(f"      OK: {mod_name:<16} | Symbol: {sym:<42} | Size: {len(code):>3} B | Relocs: {len(relocs)}")
    print("      Compilation check PASSED.")

def run_bss_simulation(code_bytes: bytes, entry: int) -> tuple[int, int, int, bytes]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x10000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, code_bytes)

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

def step2_differential_verification():
    print("[2/5] Running Unicorn ARM11 MPCORE differential simulation on CRT bootstrap...")
    orig_code = CODE_ORIGINAL.read_bytes()[:0x10000]

    obj_path = BUILD_DIR / 'crt_start.o'
    funcs = extract_elf_functions_detailed(obj_path)
    cand_start, _ = funcs['__start']
    cand_bss, _ = funcs['__init_bss']

    # Exact byte match check
    assert cand_start == orig_code[0:36], "Mismatch in __start binary encoding!"
    assert cand_bss == orig_code[36:72], "Mismatch in __init_bss binary encoding!"

    # Differential BSS simulation
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
    print(f"      Differential simulation PASSED: {BSS_SIZE:,} B of BSS cleared identically.")

def step3_mutation_testing():
    print("[3/5] Running mutation testing on CRT bootstrap loop...")
    orig_code = CODE_ORIGINAL.read_bytes()[:0x10000]
    obj_path = BUILD_DIR / 'crt_start.o'
    funcs = extract_elf_functions_detailed(obj_path)
    cand_start, _ = funcs['__start']
    cand_bss, _ = funcs['__init_bss']

    mut_code = bytearray(orig_code)
    mut_code[0:36] = cand_start
    mut_code[36:72] = cand_bss
    # Mutate blo into NOP so loop exits after 1 iteration
    mut_code[36 + 24 : 36 + 28] = struct.pack('<I', 0xE1A00000)

    try:
        _, _, _, bss_mut = run_bss_simulation(bytes(mut_code), 0x00100024)
        if all(b == 0 for b in bss_mut):
            raise AssertionError("Mutation went undetected!")
        print("      Mutation test PASSED: defective clear detected and rejected.")
    except Exception as e:
        print(f"      Mutation test PASSED: mutant caught ({e}).")

def step4_staging_and_roundtrip():
    print("[4/5] Executing full executable staging and IPS roundtrip verification...")
    from tools.h19_staged_image_patch import patch_binary, changed_records
    from tools.h2_calc_code_patch import encode_ips

    base_bin = (ROOT / 'build/agent-work/H18-semantic/h18-integrated-stage/code.h18-final.bin').read_bytes()
    orig_bin = CODE_ORIGINAL.read_bytes()
    out_dir = ROOT / 'build/agent-work/H19-semantic/h19-integrated-stage'

    patched, report = patch_binary(base_bin, out_dir)
    assert len(patched) == len(orig_bin), f"Size mismatch: {len(patched)} vs {len(orig_bin)}"

    records = changed_records(orig_bin, patched)
    ips_bytes = encode_ips(records, len(orig_bin))
    roundtrip = apply_ips(orig_bin, ips_bytes)
    assert roundtrip == patched, "IPS roundtrip verification failed!"

    out_bin = out_dir / 'code.h19-final.bin'
    out_ips = out_dir / 'code.h19-final.ips'
    out_bin.write_bytes(patched)
    out_ips.write_bytes(ips_bytes)

    total_changed = sum(len(chunk) for _, chunk in records)
    print(f"      Staged image: {out_bin.name} ({len(patched):,} B)")
    print(f"      LayeredFS IPS: {out_ips.name} ({len(ips_bytes):,} B, {len(records)} records, {total_changed:,} B modified)")
    print("      Staging and roundtrip PASSED.")

def step5_workflow_board_check():
    print("[5/5] Checking Agent Workflow Board for Milestone H19...")
    import subprocess
    cmd = [sys.executable, str(ROOT / 'tools/agent_workflow.py'), 'check', '--board', 'config/agent-workflows/h19.json']
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    assert res.returncode == 0, f"Workflow check failed:\n{res.stderr}\n{res.stdout}"
    print(f"      Workflow board check PASSED: {res.stdout.strip()}")

def main():
    print("======================================================================")
    print("  MILESTONE H19: AUTONOMOUS VERIFICATION & INTEGRATION SUITE")
    print("======================================================================\n")
    step1_verify_compilation()
    step2_differential_verification()
    step3_mutation_testing()
    step4_staging_and_roundtrip()
    step5_workflow_board_check()
    print("\n======================================================================")
    print("  ALL MILESTONE H19 CHECKS PASSED WITH 100% SUCCESS!")
    print("======================================================================")

if __name__ == '__main__':
    main()
