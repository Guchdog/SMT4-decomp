#!/usr/bin/env python3
"""Build and verify all Milestone H13 semantic C++ candidates (Advanced Exploration, Minimap, Overworld, Place Window)."""
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

EXP_DIR = ROOT / 'experiments/semantic_equivalence'
EXP_DIR.mkdir(parents=True, exist_ok=True)
BUILD_DIR = ROOT / 'build/h13_candidates'
BUILD_DIR.mkdir(parents=True, exist_ok=True)

# 1. PlaceWin_SetVisible (0x002638FC, 20 bytes)
f1 = EXP_DIR / 'h13_placewin_setvisible_candidate.cpp'
f1.write_text('''#include <cstdint>
typedef uint8_t u8;

struct PlaceWinWork {
    u8 pad[0x4C5];
    u8 visible;
};

extern "C" {
    extern PlaceWinWork* g_PlaceWinWork_0043da28[];
}

extern "C" void h13_placewin_setvisible_candidate(u8 visible) {
    PlaceWinWork* w = g_PlaceWinWork_0043da28[1];
    w->visible = visible;
}

extern "C" void h13_placewin_setvisible_mutation(u8 visible) {
    PlaceWinWork* w = g_PlaceWinWork_0043da28[1];
    w->visible = visible ^ 1;
}
''', encoding='utf-8')

# 2. PlaceWin_Dismiss (0x002638DC, 32 bytes)
f2 = EXP_DIR / 'h13_placewin_dismiss_candidate.cpp'
f2.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

struct PlaceWinContext {
    u8 pad[8];
    u32 state;
    u8 pad2[0x28];
    u8 sub[4];
};

extern "C" {
    extern PlaceWinContext* g_PlaceWinContext_0043e140;
    void sub_2BF030(void* sub, u32 flag);
}

extern "C" void h13_placewin_dismiss_candidate() {
    PlaceWinContext* ctx = g_PlaceWinContext_0043e140;
    ctx->state = 3;
    sub_2BF030(ctx->sub, 1);
}

extern "C" void h13_placewin_dismiss_mutation() {
    PlaceWinContext* ctx = g_PlaceWinContext_0043e140;
    ctx->state = 0;
    sub_2BF030(ctx->sub, 0);
}
''', encoding='utf-8')

# 3. PlaceWin_IsActive (0x0026394C, 44 bytes)
f3 = EXP_DIR / 'h13_placewin_isactive_candidate.cpp'
f3.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

struct PlaceWinTimer {
    u8 pad[0x38];
    float duration;
    u8 pad2[0xC];
    float elapsed;
};

struct PlaceWinHolder {
    u8 pad[4];
    PlaceWinTimer* timer;
};

extern "C" u32 h13_placewin_isactive_candidate(PlaceWinHolder* holder) {
    PlaceWinTimer* t = holder->timer;
    if (!t) return 1;
    return (t->elapsed > t->duration) ? 0 : 1;
}

extern "C" u32 h13_placewin_isactive_mutation(PlaceWinHolder* holder) {
    return 0;
}
''', encoding='utf-8')

# 4. MapField_ClearActiveFlag (0x00208A70, 20 bytes)
f4 = EXP_DIR / 'h13_mapfield_clearactiveflag_candidate.cpp'
f4.write_text('''#include <cstdint>
typedef uint8_t u8;

struct alignas(4) MapFieldState {
    u8 pad[0x2F8];
    u8 active_flag;
};

extern "C" {
    extern MapFieldState g_MapFieldState_0049f91c;
}

extern "C" void h13_mapfield_clearactiveflag_candidate() {
    g_MapFieldState_0049f91c.active_flag = 0;
}

extern "C" void h13_mapfield_clearactiveflag_mutation() {
    g_MapFieldState_0049f91c.active_flag = 1;
}
''', encoding='utf-8')

# 5. MapNavi_SetTargetCoords (0x001D2E24, 40 bytes)
f5 = EXP_DIR / 'h13_mapnavi_settargetcoords_candidate.cpp'
f5.write_text('''#include <cstdint>
typedef uint16_t u16;
typedef uint8_t u8;

struct MapNaviTarget {
    u8 pad[4];
    u16 target_x;
    u16 target_y;
    u16 angle;
    u8 active;
};

extern "C" {
    extern MapNaviTarget* g_MapNaviTarget_004474d8;
}

extern "C" void h13_mapnavi_settargetcoords_candidate(u16 x, u16 y) {
    MapNaviTarget* navi = g_MapNaviTarget_004474d8;
    navi->angle = 0;
    navi->target_x = x;
    navi->target_y = y;
    navi->active = 1;
}

extern "C" void h13_mapnavi_settargetcoords_mutation(u16 x, u16 y) {
    MapNaviTarget* navi = g_MapNaviTarget_004474d8;
    navi->target_x = 0;
    navi->target_y = 0;
    navi->active = 0;
}
''', encoding='utf-8')

# 6. MapNavi_Reset (0x001D2E0C, 24 bytes)
f6 = EXP_DIR / 'h13_mapnavi_reset_candidate.cpp'
f6.write_text('''#include <cstdint>
typedef uint32_t u32;

extern "C" {
    extern void** g_MapRuntimeWork_00447060;
    void sub_2C45B8(void* work, u32 flag);
}

extern "C" void h13_mapnavi_reset_candidate() {
    void* w = *g_MapRuntimeWork_00447060;
    sub_2C45B8(w, 0);
}

extern "C" void h13_mapnavi_reset_mutation() {
    void* w = *g_MapRuntimeWork_00447060;
    sub_2C45B8(w, 1);
}
''', encoding='utf-8')

# 7. MapEpl_CalcScale (0x00193B28, 28 bytes)
f7 = EXP_DIR / 'h13_mapepl_calcscale_candidate.cpp'
f7.write_text('''#include <cstdint>
typedef uint32_t u32;

extern "C" {
    u32 sub_2C3290();
    u32 sub_20FDE0(u32);
}

extern "C" u32 h13_mapepl_calcscale_candidate() {
    u32 a = sub_2C3290();
    u32 b = sub_20FDE0(0);
    return a * b;
}

extern "C" u32 h13_mapepl_calcscale_mutation() {
    u32 a = sub_2C3290();
    u32 b = sub_20FDE0(0);
    return a + b;
}
''', encoding='utf-8')

# 8. MapCalc_DistanceToEntity (0x001D3A9C, 32 bytes)
f8 = EXP_DIR / 'h13_mapcalc_distancetoentity_candidate.cpp'
f8.write_text('''#include <cstdint>
typedef uint32_t u32;

extern "C" {
    float sub_266D70(u32 arg);
    void sub_2E05BC(float dist);
}

extern "C" u32 h13_mapcalc_distancetoentity_candidate() {
    float dist_sq = sub_266D70(0);
    float dist;
    asm("vsqrt.f32 %0, %1" : "=t"(dist) : "t"(dist_sq));
    sub_2E05BC(dist);
    return 1;
}

extern "C" u32 h13_mapcalc_distancetoentity_mutation() {
    return 0;
}
''', encoding='utf-8')

CANDIDATES = [
    ('h13_placewin_setvisible', 0x002638FC, 20, f1),
    ('h13_placewin_dismiss', 0x002638DC, 32, f2),
    ('h13_placewin_isactive', 0x0026394C, 44, f3),
    ('h13_mapfield_clearactiveflag', 0x00208A70, 20, f4),
    ('h13_mapnavi_settargetcoords', 0x001D2E24, 40, f5),
    ('h13_mapnavi_reset', 0x001D2E0C, 24, f6),
    ('h13_mapepl_calcscale', 0x00193B28, 28, f7),
    ('h13_mapcalc_distancetoentity', 0x001D3A9C, 32, f8),
]

print("=== Compiling all 8 Milestone H13 Semantic Candidates (Advanced Exploration, Minimap, Overworld) ===")
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
    print("\nALL 8 H13 CANDIDATES SUCCESSFULLY BUILT WITHIN ORIGINAL WINDOW FOOTPRINTS!")
else:
    sys.exit(1)
