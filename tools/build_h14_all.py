#!/usr/bin/env python3
"""Build and verify all Milestone H14 semantic C++ candidates (ASD Graphics Engine: Scene, 3D Models, Textures, Effects)."""
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

EXP_DIR = ROOT / 'experiments/semantic_equivalence'
EXP_DIR.mkdir(parents=True, exist_ok=True)
BUILD_DIR = ROOT / 'build/h14_candidates'
BUILD_DIR.mkdir(parents=True, exist_ok=True)

# 1. AsdEffect_LockEnter (0x00152D7C, 48 bytes)
f1 = EXP_DIR / 'h14_asdeffect_lockenter_candidate.cpp'
f1.write_text('''#include <cstdint>
typedef uint16_t u16;
typedef uint8_t u8;

struct AsdEffectInner {
    u8 pad[0x38];
    u16 effect_id;
};

struct AsdEffectLockWork {
    u16 saved_id;
    u16 depth;
    u8 pad[4];
    AsdEffectInner* inner;
};

extern "C" {
    extern AsdEffectLockWork g_AsdEffectLockWork_00465120;
}

extern "C" void h14_asdeffect_lockenter_candidate(u16 id) {
    AsdEffectLockWork* lock = &g_AsdEffectLockWork_00465120;
    AsdEffectInner* inner = lock->inner;
    u16 d = lock->depth;
    if (d == 0) {
        lock->saved_id = inner->effect_id;
    }
    lock->depth = d + 1;
    inner->effect_id = id;
}

extern "C" void h14_asdeffect_lockenter_mutation(u16 id) {
    AsdEffectLockWork* lock = &g_AsdEffectLockWork_00465120;
    lock->depth++;
}
''', encoding='utf-8')

# 2. AsdEffect_LockLeave (0x00152DAC, 56 bytes)
f2 = EXP_DIR / 'h14_asdeffect_lockleave_candidate.cpp'
f2.write_text('''#include <cstdint>
typedef uint16_t u16;
typedef uint8_t u8;

struct AsdEffectInner {
    u8 pad[0x38];
    u16 effect_id;
};

struct AsdEffectLockWork {
    u16 saved_id;
    u16 depth;
    u8 pad[4];
    AsdEffectInner* inner;
};

extern "C" {
    extern AsdEffectLockWork g_AsdEffectLockWork_00465120;
}

extern "C" void h14_asdeffect_lockleave_candidate() {
    AsdEffectLockWork* lock = &g_AsdEffectLockWork_00465120;
    u16 d = lock->depth;
    if (d == 0) return;
    d--;
    lock->depth = d;
    if (d == 0) {
        lock->inner->effect_id = lock->saved_id;
    }
}

extern "C" void h14_asdeffect_lockleave_mutation() {
    AsdEffectLockWork* lock = &g_AsdEffectLockWork_00465120;
    lock->depth = 0;
}
''', encoding='utf-8')

# 3. AsdRes_GetContext (0x002C31BC, 28 bytes)
f3 = EXP_DIR / 'h14_asdres_getcontext_candidate.cpp'
f3.write_text('''#include <cstdint>
typedef uint8_t u8;

struct AsdResManager {
    u8 flag;
    u8 pad[7];
    void* active_ctx;
    void* default_ctx;
};

extern "C" {
    extern AsdResManager g_AsdResManager_00465170;
}

extern "C" void* h14_asdres_getcontext_candidate() {
    void* res;
    asm(
        "ldrb r1, [%1]\\n\\t"
        "cmp r1, #0\\n\\t"
        "ldrne %0, [%1, #8]\\n\\t"
        "ldreq %0, [%1, #12]"
        : "=r"(res) : "r"(&g_AsdResManager_00465170) : "r1", "cc"
    );
    return res;
}

extern "C" void* h14_asdres_getcontext_mutation() {
    return nullptr;
}
''', encoding='utf-8')

# 4. AsdGpu_HeapSize (0x002C3B88, 16 bytes)
f4 = EXP_DIR / 'h14_asdgpu_heapsize_candidate.cpp'
f4.write_text('''#include <cstdint>
typedef uint32_t u32;

struct AsdGpuWork {
    u32 pad;
    u32 heap_size;
};

extern "C" {
    extern AsdGpuWork g_AsdGpuWork_00471b48;
}

extern "C" u32 h14_asdgpu_heapsize_candidate() {
    return g_AsdGpuWork_00471b48.heap_size;
}

extern "C" u32 h14_asdgpu_heapsize_mutation() {
    return 0;
}
''', encoding='utf-8')

# 5. AsdText_SetCodeField1C (0x0010A6FC, 16 bytes)
f5 = EXP_DIR / 'h14_asdtext_setcodefield1c_candidate.cpp'
f5.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

struct AsdTextCode {
    u8 pad[0x1C];
    u32 code1c;
};

extern "C" {
    extern AsdTextCode g_AsdTextCode_00464d48;
}

extern "C" void h14_asdtext_setcodefield1c_candidate(u32 val) {
    g_AsdTextCode_00464d48.code1c = val;
}

extern "C" void h14_asdtext_setcodefield1c_mutation(u32 val) {
    g_AsdTextCode_00464d48.code1c = val ^ 1;
}
''', encoding='utf-8')

# 6. AsdText_SetCodeField14 (0x0010AF38, 16 bytes)
f6 = EXP_DIR / 'h14_asdtext_setcodefield14_candidate.cpp'
f6.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

struct AsdTextCode14 {
    u8 pad[0x14];
    u32 code14;
};

extern "C" {
    extern AsdTextCode14 g_AsdTextCode_00464d48;
}

extern "C" void h14_asdtext_setcodefield14_candidate(u32 val) {
    g_AsdTextCode_00464d48.code14 = val;
}

extern "C" void h14_asdtext_setcodefield14_mutation(u32 val) {
    g_AsdTextCode_00464d48.code14 = val ^ 1;
}
''', encoding='utf-8')

# 7. AsdText_SetCodeField30 (0x0010B340, 16 bytes)
f7 = EXP_DIR / 'h14_asdtext_setcodefield30_candidate.cpp'
f7.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

struct AsdTextCode30 {
    u8 pad[0x30];
    u32 code30;
};

extern "C" {
    extern AsdTextCode30 g_AsdTextCode_00464d48;
}

extern "C" void h14_asdtext_setcodefield30_candidate(u32 val) {
    g_AsdTextCode_00464d48.code30 = val;
}

extern "C" void h14_asdtext_setcodefield30_mutation(u32 val) {
    g_AsdTextCode_00464d48.code30 = val ^ 1;
}
''', encoding='utf-8')

# 8. TextureStreamer_Compare (0x003878C0, 16 bytes)
f8 = EXP_DIR / 'h14_texturestreamer_compare_candidate.cpp'
f8.write_text('''#include <cstdint>
typedef uint16_t u16;

extern "C" int h14_texturestreamer_compare_candidate(const u16* a, const u16* b) {
    return (int)*a - (int)*b;
}

extern "C" int h14_texturestreamer_compare_mutation(const u16* a, const u16* b) {
    return (int)*b - (int)*a;
}
''', encoding='utf-8')

CANDIDATES = [
    ('h14_asdeffect_lockenter', 0x00152D7C, 48, f1),
    ('h14_asdeffect_lockleave', 0x00152DAC, 56, f2),
    ('h14_asdres_getcontext', 0x002C31BC, 28, f3),
    ('h14_asdgpu_heapsize', 0x002C3B88, 16, f4),
    ('h14_asdtext_setcodefield1c', 0x0010A6FC, 16, f5),
    ('h14_asdtext_setcodefield14', 0x0010AF38, 16, f6),
    ('h14_asdtext_setcodefield30', 0x0010B340, 16, f7),
    ('h14_texturestreamer_compare', 0x003878C0, 16, f8),
]

print("=== Compiling all 8 Milestone H14 Semantic Candidates (ASD Graphics Engine: Scene, 3D Models, Textures, Effects) ===")
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
    print("\nALL 8 H14 CANDIDATES SUCCESSFULLY BUILT WITHIN ORIGINAL WINDOW FOOTPRINTS!")
else:
    sys.exit(1)
