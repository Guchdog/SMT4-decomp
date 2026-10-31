#!/usr/bin/env python3
"""Build and verify all Milestone H12 semantic C++ candidates (Advanced Combat: Turn Subsystems, Smirk, Turn Data, Negotiation, Results)."""
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

EXP_DIR = ROOT / 'experiments/semantic_equivalence'
EXP_DIR.mkdir(parents=True, exist_ok=True)
BUILD_DIR = ROOT / 'build/h12_candidates'
BUILD_DIR.mkdir(parents=True, exist_ok=True)

# 1. Battle_InitTurnSubsystems (0x00123050, 64 bytes)
f1 = EXP_DIR / 'h12_battle_initturnsubsystems_candidate.cpp'
f1.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    extern void* g_BattleTurnWork_0044e32c;
    void sub_136FA4(void*);
    void sub_132FB8(void*);
    void sub_1423C0(void*);
    void sub_13348C(void*);
}

extern "C" u32 h12_battle_initturnsubsystems_candidate(void* arg) {
    g_BattleTurnWork_0044e32c = arg;
    u8* p = static_cast<u8*>(arg);
    sub_136FA4(p);
    sub_132FB8(p + 4);
    sub_1423C0(p + 8);
    sub_13348C(p + 0xC);
    return 0;
}

extern "C" u32 h12_battle_initturnsubsystems_mutation(void* arg) {
    return 0xDEADBEEF;
}
''', encoding='utf-8')

# 2. Battle_GetUnitSmirkState (0x00129C58, 24 bytes)
f2 = EXP_DIR / 'h12_battle_getunitsmirkstate_candidate.cpp'
f2.write_text('''#include <cstdint>
typedef int32_t s32;
typedef int8_t s8;
typedef uint8_t u8;

struct alignas(4) SmirkWork {
    u8 pad[0x1C];
    u8* sub;
};

extern "C" {
    extern SmirkWork g_BattleSmirkWork_00471a70;
}

extern "C" s32 h12_battle_getunitsmirkstate_candidate() {
    return *reinterpret_cast<s8*>(g_BattleSmirkWork_00471a70.sub + 0x75);
}

extern "C" s32 h12_battle_getunitsmirkstate_mutation() {
    return 0xDEADBEEF;
}
''', encoding='utf-8')

# 3. Battle_GetSmirkActor (0x00129CBC, 20 bytes)
f3 = EXP_DIR / 'h12_battle_getsmirkactor_candidate.cpp'
f3.write_text('''#include <cstdint>
typedef uint8_t u8;

struct alignas(4) BattleSmirkWork {
    u8 pad[0xC];
    void* actor;
    u8 pad2[0xC];
    void* sub;
};

extern "C" {
    extern BattleSmirkWork g_BattleSmirkWork_00471a70;
}

extern "C" void* h12_battle_getsmirkactor_candidate() {
    return g_BattleSmirkWork_00471a70.actor;
}

extern "C" void* h12_battle_getsmirkactor_mutation() {
    return reinterpret_cast<void*>(0xDEADBEEF);
}
''', encoding='utf-8')

# 4. Battle_ExchangeSmirkSlot (0x00129C70, 76 bytes)
f4 = EXP_DIR / 'h12_battle_exchangesmirkslot_candidate.cpp'
f4.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

struct alignas(4) SmirkSubWork {
    u8 pad[0x10];
    u32 slots[7];
};

struct alignas(4) BattleSmirkWork {
    u8 pad[0xC];
    void* actor;
    u8 pad2[0xC];
    SmirkSubWork* sub;
};

extern "C" {
    extern BattleSmirkWork g_BattleSmirkWork_00471a70;
    void sub_2C3AA8(void*);
    void sub_2C3A24(void*);
}

extern "C" u32 h12_battle_exchangesmirkslot_candidate(u32 val, u32 slot) {
    if (slot >= 7) return 0;
    SmirkSubWork* sub = g_BattleSmirkWork_00471a70.sub;
    sub_2C3AA8(sub);
    u32 old_val = sub->slots[slot];
    sub->slots[slot] = val;
    sub_2C3A24(sub);
    return old_val;
}

extern "C" u32 h12_battle_exchangesmirkslot_mutation(u32 val, u32 slot) {
    return 0xDEADBEEF;
}
''', encoding='utf-8')

# 5. Battle_InitTurnData (0x00136FA4, 40 bytes)
f5 = EXP_DIR / 'h12_battle_initturndata_candidate.cpp'
f5.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    extern void* g_BattleStateWork_004655c0;
    void sub_1422F8();
}

extern "C" void h12_battle_initturndata_candidate(u32* p) {
    *p = 0x1C00;
    u8* st = static_cast<u8*>(g_BattleStateWork_004655c0);
    u32* flags = reinterpret_cast<u32*>(st + 0x770);
    *flags = (*flags & ~0x2000u) | 0x11000u;
    sub_1422F8();
}

extern "C" void h12_battle_initturndata_mutation(u32* p) {
    *p = 0;
    sub_1422F8();
}
''', encoding='utf-8')

# 6. Result_Cleanup (0x001C87D8, 156 bytes)
f6 = EXP_DIR / 'h12_result_cleanup_candidate.cpp'
f6.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    extern void* g_ResultWork_0044dc20;
    void sub_2A755C(void*);
    void sub_2C4360(void*);
    void sub_2C0128();
    void sub_2A497C(u32);
    void sub_2AEB2C(u32, u32);
}

extern "C" void h12_result_cleanup_candidate() {
    u8* work = static_cast<u8*>(g_ResultWork_0044dc20);
    if (!work) return;
    sub_2A755C(*reinterpret_cast<void**>(work + 0x3568));
    sub_2C4360(*reinterpret_cast<void**>(work + 0x3564));
    sub_2C4360(*reinterpret_cast<void**>(work + 0x356c));
    sub_2C0128();
    sub_2C4360(*reinterpret_cast<void**>(work + 0x3570));
    sub_2A497C(0x14);
    sub_2A497C(0x25);
    for (u32 i = 0; i < 2; ++i) {
        sub_2AEB2C(0x28, i);
    }
    sub_2C4360(work);
    g_ResultWork_0044dc20 = nullptr;
}

extern "C" void h12_result_cleanup_mutation() {
    g_ResultWork_0044dc20 = reinterpret_cast<void*>(0xDEADBEEF);
}
''', encoding='utf-8')

# 7. Battle_IsUnitDefeated (0x0028DE4C, 56 bytes)
f7 = EXP_DIR / 'h12_battle_isunitdefeated_candidate.cpp'
f7.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef int32_t s32;
typedef uint8_t u8;

extern "C" u32 h12_battle_isunitdefeated_candidate(const void* unit) {
    const u8* u = static_cast<const u8*>(unit);
    u32 flags = *reinterpret_cast<const u32*>(u + 0x44A0);
    if (flags & 2) return 0;
    if (flags & 0x02000000) return 1;
    s32 hp = *reinterpret_cast<const s32*>(u + 0xC4);
    return (hp < 0) ? 1 : 0;
}

extern "C" u32 h12_battle_isunitdefeated_mutation(const void* unit) {
    return 0;
}
''', encoding='utf-8')

# 8. Battle_ResetUnitStateBuffer (0x00215938, 32 bytes)
f8 = EXP_DIR / 'h12_battle_resetunitstatebuffer_candidate.cpp'
f8.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    extern u8 g_BattleUnitTable_00478000[];
    void* sub_2BCF58(void* dest, const void* src, u32 n);
}

extern "C" void* h12_battle_resetunitstatebuffer_candidate(u32 idx, const void* src) {
    u8* unit = g_BattleUnitTable_00478000 + idx * 328;
    return sub_2BCF58(unit + 0x2C, src, 0x90);
}

extern "C" void* h12_battle_resetunitstatebuffer_mutation(u32 idx, const void* src) {
    u8* unit = g_BattleUnitTable_00478000 + idx * 328;
    return sub_2BCF58(unit + 0x2C, src, 0);
}
''', encoding='utf-8')

CANDIDATES = [
    ('h12_battle_initturnsubsystems', 0x00123050, 64, f1),
    ('h12_battle_getunitsmirkstate', 0x00129C58, 24, f2),
    ('h12_battle_getsmirkactor', 0x00129CBC, 20, f3),
    ('h12_battle_exchangesmirkslot', 0x00129C70, 76, f4),
    ('h12_battle_initturndata', 0x00136FA4, 40, f5),
    ('h12_result_cleanup', 0x001C87D8, 156, f6),
    ('h12_battle_isunitdefeated', 0x0028DE4C, 56, f7),
    ('h12_battle_resetunitstatebuffer', 0x00215938, 32, f8),
]

print("=== Compiling all 8 Milestone H12 Semantic Candidates (Advanced Combat) ===")
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
    print("\nALL 8 H12 CANDIDATES SUCCESSFULLY BUILT WITHIN ORIGINAL WINDOW FOOTPRINTS!")
else:
    sys.exit(1)
