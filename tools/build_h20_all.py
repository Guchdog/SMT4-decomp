#!/usr/bin/env python3
"""Build and verify all Milestone H20 Platform Abstraction Layer (HAL) modules."""
from pathlib import Path
import os, sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

BUILD_DIR = ROOT / 'build/h20_candidates'
BUILD_DIR.mkdir(parents=True, exist_ok=True)

HAL_MODULES = [
    ('hal_system', 'src/hal/hal_system.cpp'),
    ('hal_filesystem', 'src/hal/hal_filesystem.cpp'),
    ('hal_graphics', 'src/hal/hal_graphics.cpp'),
    ('hal_audio', 'src/hal/hal_audio.cpp'),
    ('hal_input', 'src/hal/hal_input.cpp'),
]

def main():
    print("=== Compiling all Milestone H20 Platform Abstraction Layer (HAL) Modules ===")
    all_ok = True
    for mod_name, src_rel in HAL_MODULES:
        src = ROOT / src_rel
        obj = BUILD_DIR / f"{mod_name}.o"
        # Compile with include directory added
        res = compile_tu_armv6k(src, obj, ROOT)
        if res.returncode != 0:
            print(f"[FAIL] {mod_name}: compilation error:\n{res.stderr}")
            all_ok = False
            continue
        funcs = extract_elf_functions_detailed(obj)
        print(f"[OK] {mod_name:<18} | Functions compiled: {len(funcs):>2} | Object size: {obj.stat().st_size:>5} bytes")

    if all_ok:
        print("\nALL MILESTONE H20 HAL MODULES COMPILED CLEANLY!")
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
