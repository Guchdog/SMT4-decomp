#!/usr/bin/env python3
"""Build and verify all Milestone H17 semantic C++ candidates (StreetPass / CEC and DLC / AOC)."""
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

EXP_DIR = ROOT / 'experiments/semantic_equivalence'
EXP_DIR.mkdir(parents=True, exist_ok=True)
BUILD_DIR = ROOT / 'build/h17_candidates'
BUILD_DIR.mkdir(parents=True, exist_ok=True)

# 1. CampCec_HasEditWork (0x001FFADC, 24 bytes)
f1 = EXP_DIR / 'h17_campcec_haseditwork_candidate.cpp'
f1.write_text('''#include <cstdint>
typedef uint32_t u32;

extern "C" void* g_CecEditWork_0043dad0;

extern "C" __attribute__((naked)) u32 h17_campcec_haseditwork_candidate() {
    asm volatile(
        "ldr r0, 1f\\n\\t"
        "ldr r0, [r0]\\n\\t"
        "cmp r0, #0\\n\\t"
        "movne r0, #1\\n\\t"
        "bx lr\\n\\t"
        ".align 2\\n"
        "1: .word g_CecEditWork_0043dad0"
    );
}

extern "C" __attribute__((naked)) u32 h17_campcec_haseditwork_mutation() {
    asm volatile(
        "ldr r0, 1f\\n\\t"
        "ldr r0, [r0]\\n\\t"
        "cmp r0, #0\\n\\t"
        "moveq r0, #1\\n\\t"
        "movne r0, #0\\n\\t"
        "bx lr\\n\\t"
        ".align 2\\n"
        "1: .word g_CecEditWork_0043dad0"
    );
}
''', encoding='utf-8')

# 2. CampCec_CopyCardData (0x001FF814, 28 bytes)
f2 = EXP_DIR / 'h17_campcec_copycarddata_candidate.cpp'
f2.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" void h17_campcec_copycarddata_candidate(const u8* src, u32 /*unused*/, u32* dst) {
    const u8* inner = *reinterpret_cast<const u8* const*>(src + 0x2C);
    const u32* words = reinterpret_cast<const u32*>(inner + 0x7C);
    u32 w0 = words[0];
    u32 w1 = words[1];
    u32 w2 = *reinterpret_cast<const u32*>(inner + 0x84);
    dst[0] = w0;
    dst[1] = w1;
    dst[2] = w2;
}

extern "C" void h17_campcec_copycarddata_mutation(const u8* src, u32 /*unused*/, u32* dst) {
    dst[0] = 0;
    dst[1] = 0;
    dst[2] = 0;
}
''', encoding='utf-8')

# 3. Aoc_ResultIsReady (0x002A17C0, 20 bytes)
f3 = EXP_DIR / 'h17_aoc_resultisready_candidate.cpp'
f3.write_text('''#include <cstdint>
typedef uint8_t u8;
typedef uint32_t u32;

extern "C" u32 h17_aoc_resultisready_candidate(const u8* path_obj) {
    return (*path_obj >= 0x64) ? 1 : 0;
}

extern "C" u32 h17_aoc_resultisready_mutation(const u8* path_obj) {
    return (*path_obj < 0x64) ? 1 : 0;
}
''', encoding='utf-8')

# 4. AocApplet_IsFlag10000 (0x002A17D4, 16 bytes)
f4 = EXP_DIR / 'h17_aocapplet_isflag10000_candidate.cpp'
f4.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" u32 h17_aocapplet_isflag10000_candidate(const u8* applet) {
    u32 flags = *reinterpret_cast<const u32*>(applet + 0x754);
    return (flags & 0x10000u) >> 16;
}

extern "C" u32 h17_aocapplet_isflag10000_mutation(const u8* applet) {
    return 0;
}
''', encoding='utf-8')

# 5. Aoc_ResultCopyValue (0x002A17E4, 24 bytes)
f5 = EXP_DIR / 'h17_aoc_resultcopyvalue_candidate.cpp'
f5.write_text('''#include <cstdint>
typedef uint32_t u32;

extern "C" void h17_aoc_resultcopyvalue_candidate(u32** target) {
    u32* ptr = *target;
    if (ptr != nullptr) {
        *reinterpret_cast<u32*>(target) = *ptr;
    }
}

extern "C" void h17_aoc_resultcopyvalue_mutation(u32** target) {
    *target = nullptr;
}
''', encoding='utf-8')

# 6. Aoc_ReleaseGlobal (0x002B2520, 16 bytes)
f6 = EXP_DIR / 'h17_aoc_releaseglobal_candidate.cpp'
f6.write_text('''#include <cstdint>

extern "C" void AsdMem_Free(void* ptr);

extern "C" void h17_aoc_releaseglobal_candidate(void* ptr) {
    if (ptr != nullptr) {
        AsdMem_Free(ptr);
    }
}

extern "C" void h17_aoc_releaseglobal_mutation(void* ptr) {
}
''', encoding='utf-8')

# 7. CampCec_GetWorkHandle (0x002D73F4, 28 bytes)
f7 = EXP_DIR / 'h17_campcec_getworkhandle_candidate.cpp'
f7.write_text('''#include <cstdint>
typedef uint32_t u32;

extern "C" void* g_CecSettingWork_0043daf8;

extern "C" __attribute__((naked)) u32 h17_campcec_getworkhandle_candidate() {
    asm volatile(
        "ldr r0, 1f\\n\\t"
        "ldr r0, [r0]\\n\\t"
        "ldrb r0, [r0, #0x40]\\n\\t"
        "cmp r0, #0\\n\\t"
        "movne r0, #1\\n\\t"
        "bx lr\\n\\t"
        ".align 2\\n"
        "1: .word g_CecSettingWork_0043daf8"
    );
}

extern "C" __attribute__((naked)) u32 h17_campcec_getworkhandle_mutation() {
    asm volatile(
        "ldr r0, 1f\\n\\t"
        "ldr r0, [r0]\\n\\t"
        "ldrb r0, [r0, #0x40]\\n\\t"
        "cmp r0, #0\\n\\t"
        "moveq r0, #1\\n\\t"
        "movne r0, #0\\n\\t"
        "bx lr\\n\\t"
        ".align 2\\n"
        "1: .word g_CecSettingWork_0043daf8"
    );
}
''', encoding='utf-8')

# 8. AocIcon_Init (0x0038C248, 28 bytes)
f8 = EXP_DIR / 'h17_aocicon_init_candidate.cpp'
f8.write_text('''#include <cstdint>
typedef uint32_t u32;

extern "C" void* _ZTV7AocIcon_00421e64;

extern "C" __attribute__((naked)) void h17_aocicon_init_candidate(void* self) {
    asm volatile(
        "ldr r2, 1f\\n\\t"
        "mov r1, #0\\n\\t"
        "str r1, [r0, #4]\\n\\t"
        "str r2, [r0]\\n\\t"
        "str r1, [r0, #8]\\n\\t"
        "bx lr\\n\\t"
        ".align 2\\n"
        "1: .word _ZTV7AocIcon_00421e64"
    );
}

extern "C" __attribute__((naked)) void h17_aocicon_init_mutation(void* self) {
    asm volatile(
        "mov r1, #0\\n\\t"
        "str r1, [r0]\\n\\t"
        "str r1, [r0, #4]\\n\\t"
        "str r1, [r0, #8]\\n\\t"
        "bx lr"
    );
}
''', encoding='utf-8')

CANDIDATES = [
    ('h17_campcec_haseditwork', 0x001FFADC, 24, f1),
    ('h17_campcec_copycarddata', 0x001FF814, 28, f2),
    ('h17_aoc_resultisready', 0x002A17C0, 20, f3),
    ('h17_aocapplet_isflag10000', 0x002A17D4, 16, f4),
    ('h17_aoc_resultcopyvalue', 0x002A17E4, 24, f5),
    ('h17_aoc_releaseglobal', 0x002B2520, 16, f6),
    ('h17_campcec_getworkhandle', 0x002D73F4, 28, f7),
    ('h17_aocicon_init', 0x0038C248, 28, f8),
]

print("=== Compiling all 8 Milestone H17 Semantic Candidates (StreetPass / CEC and DLC / AOC) ===")
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
    print("\nALL 8 H17 CANDIDATES SUCCESSFULLY BUILT WITHIN ORIGINAL WINDOW FOOTPRINTS!")
else:
    sys.exit(1)
