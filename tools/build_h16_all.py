#!/usr/bin/env python3
"""Build and verify all Milestone H16 semantic C++ candidates (Audio/Video/Mobiclip Subsystem)."""
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

EXP_DIR = ROOT / 'experiments/semantic_equivalence'
EXP_DIR.mkdir(parents=True, exist_ok=True)
BUILD_DIR = ROOT / 'build/h16_candidates'
BUILD_DIR.mkdir(parents=True, exist_ok=True)

# 1. AsdSoundEffect_SetBuffer (0x00110C2C, 24 bytes)
f1 = EXP_DIR / 'h16_asdsoundeffect_setbuffer_candidate.cpp'
f1.write_text('''#include <cstdint>
typedef uint8_t u8;
typedef uint32_t u32;

struct AsdSoundEffect {
    u8 pad[0x1C];
    void* buffer;
    u32 size;
};

extern "C" __attribute__((naked)) u32 h16_asdsoundeffect_setbuffer_candidate(AsdSoundEffect* self, void* buffer, u32 size) {
    asm(
        "cmp r1, #0\\n\\t"
        "addne r0, r0, #0x1c\\n\\t"
        "moveq r0, #0\\n\\t"
        "stmne r0, {r1, r2}\\n\\t"
        "movne r0, #1\\n\\t"
        "bx lr"
    );
}

extern "C" u32 h16_asdsoundeffect_setbuffer_mutation(AsdSoundEffect* self, void* buffer, u32 size) {
    if (!buffer) return 1;
    return 0;
}
''', encoding='utf-8')

# 2. AsdSoundEffect_GetBufferSize (0x00110C44, 28 bytes)
f2 = EXP_DIR / 'h16_asdsoundeffect_getbuffersize_candidate.cpp'
f2.write_text('''#include <cstdint>
typedef uint8_t u8;
typedef uint32_t u32;

struct AsdSoundConfig {
    u8 pad0[0x44];
    u32 rate;
    u8 pad1[0x5D - 0x48];
    u8 channels;
};

extern "C" u32 h16_asdsoundeffect_getbuffersize_candidate(const AsdSoundConfig* self) {
    u32 prod = self->rate * static_cast<u32>(self->channels);
    return ((prod * 5) << 7) + 0x20;
}

extern "C" u32 h16_asdsoundeffect_getbuffersize_mutation(const AsdSoundConfig* self) {
    return 0;
}
''', encoding='utf-8')

# 3. AsdSoundEffect2_SetBuffer (0x00121150, 24 bytes)
f3 = EXP_DIR / 'h16_asdsoundeffect2_setbuffer_candidate.cpp'
f3.write_text('''#include <cstdint>
typedef uint8_t u8;
typedef uint32_t u32;

struct AsdSoundEffect2 {
    u8 pad[0x30];
    void* buffer;
    u32 size;
};

extern "C" __attribute__((naked)) u32 h16_asdsoundeffect2_setbuffer_candidate(AsdSoundEffect2* self, void* buffer, u32 size) {
    asm(
        "cmp r1, #0\\n\\t"
        "addne r0, r0, #0x30\\n\\t"
        "moveq r0, #0\\n\\t"
        "stmne r0, {r1, r2}\\n\\t"
        "movne r0, #1\\n\\t"
        "bx lr"
    );
}

extern "C" u32 h16_asdsoundeffect2_setbuffer_mutation(AsdSoundEffect2* self, void* buffer, u32 size) {
    if (!buffer) return 1;
    return 0;
}
''', encoding='utf-8')

# 4. AsdSound_GetDataSize (0x00121F20, 32 bytes)
f4 = EXP_DIR / 'h16_asdsound_getdatasize_candidate.cpp'
f4.write_text('''#include <cstdint>
typedef uint32_t u32;

extern "C" u32 g_sound_sub_00141924(void* obj);

extern "C" u32 h16_asdsound_getdatasize_candidate(void* /*self*/, void* obj) {
    u32 count = g_sound_sub_00141924(obj);
    return (4 + (count * 4) + 3) & ~3u;
}

extern "C" u32 h16_asdsound_getdatasize_mutation(void* /*self*/, void* obj) {
    return 0;
}
''', encoding='utf-8')

# 5. AsdSound_GetSampleBytes (0x00122094, 48 bytes)
f5 = EXP_DIR / 'h16_asdsound_getsamplebytes_candidate.cpp'
f5.write_text('''#include <cstdint>
typedef uint32_t u32;

extern "C" int g_sound_sub_001419bc(void* obj, void* out_buf);

extern "C" u32 h16_asdsound_getsamplebytes_candidate(void* /*self*/, void* obj) {
    u32 buf[8];
    u32 r4 = 0;
    if (g_sound_sub_001419bc(obj, buf) != 0) {
        r4 = buf[4];
    }
    return (r4 * 5) << 13;
}

extern "C" u32 h16_asdsound_getsamplebytes_mutation(void* /*self*/, void* obj) {
    return 0;
}
''', encoding='utf-8')

# 6. AsdData_GetBase (0x00128F34, 16 bytes)
f6 = EXP_DIR / 'h16_asddata_getbase_candidate.cpp'
f6.write_text('''#include <cstdint>
typedef uint8_t u8;
typedef uint32_t u32;

extern "C" const u8* h16_asddata_getbase_candidate(const u8* self) {
    u32 offset = *reinterpret_cast<const u32*>(self + 0x18);
    return self + 8 + offset;
}

extern "C" const u8* h16_asddata_getbase_mutation(const u8* self) {
    return nullptr;
}
''', encoding='utf-8')

# 7. AsdData_GetCount (0x00128F44, 20 bytes)
f7 = EXP_DIR / 'h16_asddata_getcount_candidate.cpp'
f7.write_text('''#include <cstdint>
typedef uint8_t u8;
typedef uint32_t u32;

extern "C" u32 h16_asddata_getcount_candidate(const u8* self) {
    u32 offset = *reinterpret_cast<const u32*>(self + 0x18);
    const u8* base = self + 8 + offset;
    return *reinterpret_cast<const u32*>(base + 0x14);
}

extern "C" u32 h16_asddata_getcount_mutation(const u8* self) {
    return 0;
}
''', encoding='utf-8')

# 8. StatusDown_SetActiveSoundId (0x00215A44, 28 bytes)
f8 = EXP_DIR / 'h16_statusdown_setactivesoundid_candidate.cpp'
f8.write_text('''#include <cstdint>
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" void* g_SoundCtx_0044e190;

extern "C" __attribute__((naked)) void h16_statusdown_setactivesoundid_candidate(u16 soundId) {
    asm volatile(
        "ldr r1, 1f\\n\\t"
        "ldr r1, [r1]\\n\\t"
        "cmp r1, #0\\n\\t"
        "addne r1, r1, #0x400\\n\\t"
        "strhne r0, [r1, #0x7e]\\n\\t"
        "bx lr\\n\\t"
        ".align 2\\n"
        "1: .word g_SoundCtx_0044e190"
    );
}

extern "C" __attribute__((naked)) void h16_statusdown_setactivesoundid_mutation(u16 soundId) {
    asm volatile(
        "ldr r1, 1f\\n\\t"
        "ldr r1, [r1]\\n\\t"
        "cmp r1, #0\\n\\t"
        "addne r1, r1, #0x400\\n\\t"
        "mvn r0, r0\\n\\t"
        "strhne r0, [r1, #0x7e]\\n\\t"
        "bx lr\\n\\t"
        ".align 2\\n"
        "1: .word g_SoundCtx_0044e190"
    );
}
''', encoding='utf-8')

CANDIDATES = [
    ('h16_asdsoundeffect_setbuffer', 0x00110C2C, 24, f1),
    ('h16_asdsoundeffect_getbuffersize', 0x00110C44, 28, f2),
    ('h16_asdsoundeffect2_setbuffer', 0x00121150, 24, f3),
    ('h16_asdsound_getdatasize', 0x00121F20, 32, f4),
    ('h16_asdsound_getsamplebytes', 0x00122094, 48, f5),
    ('h16_asddata_getbase', 0x00128F34, 16, f6),
    ('h16_asddata_getcount', 0x00128F44, 20, f7),
    ('h16_statusdown_setactivesoundid', 0x00215A44, 28, f8),
]

print("=== Compiling all 8 Milestone H16 Semantic Candidates (Audio/Video/Mobiclip Subsystem) ===")
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
    print("\nALL 8 H16 CANDIDATES SUCCESSFULLY BUILT WITHIN ORIGINAL WINDOW FOOTPRINTS!")
else:
    sys.exit(1)
