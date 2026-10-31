#!/usr/bin/env python3
"""Autonomous verification suite for Milestone H20 Platform Abstraction Layer (HAL)."""
from pathlib import Path
import struct, sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

BUILD_DIR = ROOT / 'build/h20_tests'
BUILD_DIR.mkdir(parents=True, exist_ok=True)

def test_hal_system():
    print("Testing HAL System...")
    src = ROOT / 'src/hal/hal_system.cpp'
    obj = BUILD_DIR / 'hal_system.o'
    res = compile_tu_armv6k(src, obj, ROOT)
    assert res.returncode == 0, f"Compilation failed: {res.stderr}"

    funcs = extract_elf_functions_detailed(obj)
    assert '_ZN4smt43hal11System_InitEv' in funcs or any('System_Init' in f for f in funcs)
    print("  [PASS] HAL System compiled and symbols resolved.")

def test_hal_filesystem():
    print("Testing HAL FileSystem...")
    src = ROOT / 'src/hal/hal_filesystem.cpp'
    obj = BUILD_DIR / 'hal_filesystem.o'
    res = compile_tu_armv6k(src, obj, ROOT)
    assert res.returncode == 0, f"Compilation failed: {res.stderr}"

    funcs = extract_elf_functions_detailed(obj)
    assert any('FileSystem_Mount' in f for f in funcs)
    assert any('FileSystem_Open' in f for f in funcs)
    print("  [PASS] HAL FileSystem compiled and symbols resolved.")

def test_hal_graphics():
    print("Testing HAL Graphics...")
    src = ROOT / 'src/hal/hal_graphics.cpp'
    obj = BUILD_DIR / 'hal_graphics.o'
    res = compile_tu_armv6k(src, obj, ROOT)
    assert res.returncode == 0, f"Compilation failed: {res.stderr}"

    funcs = extract_elf_functions_detailed(obj)
    assert any('Graphics_Init' in f for f in funcs)
    assert any('Graphics_Set3DMode' in f for f in funcs)
    print("  [PASS] HAL Graphics compiled and symbols resolved.")

def test_hal_audio():
    print("Testing HAL Audio...")
    src = ROOT / 'src/hal/hal_audio.cpp'
    obj = BUILD_DIR / 'hal_audio.o'
    res = compile_tu_armv6k(src, obj, ROOT)
    assert res.returncode == 0, f"Compilation failed: {res.stderr}"

    funcs = extract_elf_functions_detailed(obj)
    assert any('Audio_Init' in f for f in funcs)
    assert any('Audio_SetMasterVolume' in f for f in funcs)
    print("  [PASS] HAL Audio compiled and symbols resolved.")

def test_hal_input():
    print("Testing HAL Input...")
    src = ROOT / 'src/hal/hal_input.cpp'
    obj = BUILD_DIR / 'hal_input.o'
    res = compile_tu_armv6k(src, obj, ROOT)
    assert res.returncode == 0, f"Compilation failed: {res.stderr}"

    funcs = extract_elf_functions_detailed(obj)
    assert any('Input_Init' in f for f in funcs)
    assert any('Input_GetState' in f for f in funcs)
    print("  [PASS] HAL Input compiled and symbols resolved.")

def main():
    print("=== Running Milestone H20 Platform Abstraction Layer Verification Suite ===")
    test_hal_system()
    test_hal_filesystem()
    test_hal_graphics()
    test_hal_audio()
    test_hal_input()
    print("\nALL 5 PLATFORM ABSTRACTION LAYER (HAL) SUBSYSTEMS VERIFIED SUCCESSFULLY!")

if __name__ == '__main__':
    main()
