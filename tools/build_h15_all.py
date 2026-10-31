#!/usr/bin/env python3
"""Build and verify all Milestone H15 semantic C++ candidates (UI Engine, Fonts, and 2D Rendering)."""
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

EXP_DIR = ROOT / 'experiments/semantic_equivalence'
EXP_DIR.mkdir(parents=True, exist_ok=True)
BUILD_DIR = ROOT / 'build/h15_candidates'
BUILD_DIR.mkdir(parents=True, exist_ok=True)

# 1. UiText_SetCodeField10 (0x0010E570, 16 bytes)
f1 = EXP_DIR / 'h15_uitext_setcodefield10_candidate.cpp'
f1.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

struct UiTextCode10 {
    u8 pad[0x10];
    u32 code10;
};

extern "C" {
    extern UiTextCode10 g_UiTextCode_00464d48;
}

extern "C" void h15_uitext_setcodefield10_candidate(u32 val) {
    g_UiTextCode_00464d48.code10 = val;
}

extern "C" void h15_uitext_setcodefield10_mutation(u32 val) {
    g_UiTextCode_00464d48.code10 = val ^ 1;
}
''', encoding='utf-8')

# 2. UiText_SetCodeField28 (0x0010E5BC, 16 bytes)
f2 = EXP_DIR / 'h15_uitext_setcodefield28_candidate.cpp'
f2.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

struct UiTextCode28 {
    u8 pad[0x28];
    u32 code28;
};

extern "C" {
    extern UiTextCode28 g_UiTextCode_00464d48;
}

extern "C" void h15_uitext_setcodefield28_candidate(u32 val) {
    g_UiTextCode_00464d48.code28 = val;
}

extern "C" void h15_uitext_setcodefield28_mutation(u32 val) {
    g_UiTextCode_00464d48.code28 = val ^ 1;
}
''', encoding='utf-8')

# 3. UiDialog_GetState (0x00126084, 16 bytes)
f3 = EXP_DIR / 'h15_uidialog_getstate_candidate.cpp'
f3.write_text('''#include <cstdint>
typedef int8_t s8;

extern "C" {
    void* sub_2C0AC8();
}

extern "C" s8 h15_uidialog_getstate_candidate() {
    s8* p = (s8*)sub_2C0AC8();
    return p[0x8C];
}

extern "C" s8 h15_uidialog_getstate_mutation() {
    s8* p = (s8*)sub_2C0AC8();
    return (s8)(p[0x8C] ^ 1);
}
''', encoding='utf-8')

# 4. UiDialog_GetFlags (0x001260A8, 16 bytes)
f4 = EXP_DIR / 'h15_uidialog_getflags_candidate.cpp'
f4.write_text('''#include <cstdint>
typedef uint32_t u32;

extern "C" {
    void* sub_2C0AC8();
}

extern "C" u32 h15_uidialog_getflags_candidate() {
    u32* p = (u32*)sub_2C0AC8();
    return *p;
}

extern "C" u32 h15_uidialog_getflags_mutation() {
    u32* p = (u32*)sub_2C0AC8();
    return *p ^ 1;
}
''', encoding='utf-8')

# 5. UiDialog_GetCursorIndex (0x00126220, 16 bytes)
f5 = EXP_DIR / 'h15_uidialog_getcursorindex_candidate.cpp'
f5.write_text('''#include <cstdint>
typedef int8_t s8;

extern "C" {
    void* sub_2C0AC8();
}

extern "C" s8 h15_uidialog_getcursorindex_candidate() {
    s8* p = (s8*)sub_2C0AC8();
    return p[0x94];
}

extern "C" s8 h15_uidialog_getcursorindex_mutation() {
    s8* p = (s8*)sub_2C0AC8();
    return (s8)(p[0x94] ^ 1);
}
''', encoding='utf-8')

# 6. UiText_GetDrawCoordX (0x00126628, 16 bytes)
f6 = EXP_DIR / 'h15_uitext_getdrawcoordx_candidate.cpp'
f6.write_text('''#include <cstdint>
typedef uint32_t u32;

extern "C" {
    void* sub_2C0AC8();
}

extern "C" u32 h15_uitext_getdrawcoordx_candidate() {
    u32* p = (u32*)sub_2C0AC8();
    return p[0x38 / 4];
}

extern "C" u32 h15_uitext_getdrawcoordx_mutation() {
    u32* p = (u32*)sub_2C0AC8();
    return p[0x38 / 4] + 1;
}
''', encoding='utf-8')

# 7. UiText_GetDrawCoordY (0x00126638, 16 bytes)
f7 = EXP_DIR / 'h15_uitext_getdrawcoordy_candidate.cpp'
f7.write_text('''#include <cstdint>
typedef uint32_t u32;

extern "C" {
    void* sub_2C0AC8();
}

extern "C" u32 h15_uitext_getdrawcoordy_candidate() {
    u32* p = (u32*)sub_2C0AC8();
    return p[0x3C / 4];
}

extern "C" u32 h15_uitext_getdrawcoordy_mutation() {
    u32* p = (u32*)sub_2C0AC8();
    return p[0x3C / 4] + 1;
}
''', encoding='utf-8')

# 8. UiManager_GetContextHandle (0x0026B844, 16 bytes)
f8 = EXP_DIR / 'h15_uimanager_getcontexthandle_candidate.cpp'
f8.write_text('''#include <cstdint>
typedef uint32_t u32;

struct UiContextManager {
    u32 pad;
    u32 handle;
};

extern "C" {
    extern UiContextManager g_UiContextManager_0043e2a8;
}

extern "C" u32 h15_uimanager_getcontexthandle_candidate() {
    return g_UiContextManager_0043e2a8.handle;
}

extern "C" u32 h15_uimanager_getcontexthandle_mutation() {
    return g_UiContextManager_0043e2a8.handle ^ 1;
}
''', encoding='utf-8')

CANDIDATES = [
    ('h15_uitext_setcodefield10', 0x0010E570, 16, f1),
    ('h15_uitext_setcodefield28', 0x0010E5BC, 16, f2),
    ('h15_uidialog_getstate', 0x00126084, 16, f3),
    ('h15_uidialog_getflags', 0x001260A8, 16, f4),
    ('h15_uidialog_getcursorindex', 0x00126220, 16, f5),
    ('h15_uitext_getdrawcoordx', 0x00126628, 16, f6),
    ('h15_uitext_getdrawcoordy', 0x00126638, 16, f7),
    ('h15_uimanager_getcontexthandle', 0x0026B844, 16, f8),
]

print("=== Compiling all 8 Milestone H15 Semantic Candidates (UI Engine, Fonts, 2D Rendering) ===")
total_window = sum(c[2] for c in CANDIDATES)
total_compiled = 0
all_ok = True

for name, addr, window, src in CANDIDATES:
    obj = BUILD_DIR / f"{name}.o"
    res = compile_tu_armv6k(src, obj, ROOT)
    if res.returncode != 0:
        print(f"[FAIL] {name}: compilation error:\n{res.stderr}")
        all_ok = False
        continue

    funcs = extract_elf_functions_detailed(obj)
    cand_name = f"{name}_candidate"
    if cand_name not in funcs:
        print(f"[FAIL] {name}: candidate function {cand_name} not found in {list(funcs.keys())}")
        all_ok = False
        continue

    code, relocs = funcs[cand_name]
    size = len(code)
    total_compiled += size
    margin = window - size
    if margin < 0:
        print(f"[OVERFLOW] {name:<35} | Cand: {size:>4} B | Window: {window:>4} B | OVERFLOW by {-margin} B!")
        all_ok = False
    else:
        print(f"[OK] {name:<35} | Cand: {size:>4} B | Window: {window:>4} B | Headroom: +{margin:>4} B | Relocs: {len(relocs)}")

print("-" * 80)
print(f"Total window: {total_window} B | Total compiled: {total_compiled} B | Overall headroom: +{total_window - total_compiled} B")

if all_ok:
    print("\nALL 8 H15 CANDIDATES SUCCESSFULLY BUILT WITHIN ORIGINAL WINDOW FOOTPRINTS!")
else:
    sys.exit(1)
