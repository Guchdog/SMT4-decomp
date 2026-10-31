#!/usr/bin/env python3
"""Build and verify all Milestone H18 canonical promoted modules in src/semantic/."""
from pathlib import Path
import os, sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

SEMANTIC_DIR = ROOT / 'src/semantic'
SEMANTIC_DIR.mkdir(parents=True, exist_ok=True)
BUILD_DIR = ROOT / 'build/h18_candidates'
BUILD_DIR.mkdir(parents=True, exist_ok=True)

MODULES = [
    ('h10_burroughs', 'src/semantic/h10_burroughs_promoted.cpp', 'h10_camp_burroughs_getsavedata_promoted'),
    ('h11_shops', 'src/semantic/h11_shops_promoted.cpp', 'h11_shop_checkhasnew_promoted'),
    ('h12_combat', 'src/semantic/h12_combat_promoted.cpp', 'h12_battle_getunitsmirkstate_promoted'),
    ('h13_exploration', 'src/semantic/h13_exploration_promoted.cpp', 'h13_placewin_isactive_promoted'),
    ('h14_graphics', 'src/semantic/h14_graphics_promoted.cpp', 'h14_asdgpu_heapsize_promoted'),
    ('h15_ui', 'src/semantic/h15_ui_promoted.cpp', 'h15_uidialog_getstate_promoted'),
    ('h16_sound', 'src/semantic/h16_sound_promoted.cpp', 'h16_asdsoundeffect_getbuffersize_promoted'),
    ('h17_cec_aoc', 'src/semantic/h17_cec_aoc_promoted.cpp', 'h17_aoc_resultisready_promoted'),
]

def main():
    print("=== Compiling all 8 Milestone H18 Promoted Canonical Modules ===")
    all_ok = True
    for mod_name, src_rel, symbol in MODULES:
        src = ROOT / src_rel
        obj = BUILD_DIR / f"{mod_name}.o"
        res = compile_tu_armv6k(src, obj, ROOT)
        if res.returncode != 0:
            print(f"[FAIL] {mod_name}: compilation error:\n{res.stderr}")
            all_ok = False
            continue
        funcs = extract_elf_functions_detailed(obj)
        if symbol not in funcs:
            print(f"[FAIL] {mod_name}: symbol {symbol} not found in {list(funcs.keys())}")
            all_ok = False
            continue
        code, relocs = funcs[symbol]
        print(f"[OK] {mod_name:<20} | Symbol: {symbol:<42} | Size: {len(code):>3} B | Relocs: {len(relocs)}")

    if all_ok:
        print("\nALL 8 PROMOTED CANONICAL MODULES COMPILED CLEANLY!")
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
