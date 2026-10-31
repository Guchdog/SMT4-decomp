#!/usr/bin/env python3
"""Build and verify all Milestone H10 semantic C++ candidates."""
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

EXP_DIR = ROOT / 'experiments/semantic_equivalence'
EXP_DIR.mkdir(parents=True, exist_ok=True)
BUILD_DIR = ROOT / 'build/h10_candidates'
BUILD_DIR.mkdir(parents=True, exist_ok=True)

# 1. Burroughs_GetSaveData (0x002A0FAC, 24 bytes)
f1 = EXP_DIR / 'h10_camp_burroughs_getsavedata_candidate.cpp'
f1.write_text('''#include <cstdint>
struct GameWork {
    void* field_0;
    uint8_t* save_data;
};
extern "C" {
    extern GameWork g_GameWork_0043e2a8;
}

extern "C" void* h10_camp_burroughs_getsavedata_candidate() {
    return g_GameWork_0043e2a8.save_data + 0x1ec18;
}

extern "C" void h10_camp_burroughs_getsavedata_mutation() {
    g_GameWork_0043e2a8.save_data = reinterpret_cast<uint8_t*>(0xDEADBEEF);
}
''', encoding='utf-8')

# 2. Burroughs_AppDispatch (0x002A0EA8, 168 bytes)
f2 = EXP_DIR / 'h10_camp_burroughs_appdispatch_candidate.cpp'
f2.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;
typedef int32_t s32;

extern "C" {
    u32 camp_func_002971e4(u32 arg0, u32 app_id);
    void camp_func_002a0f68(u32 flag);
    void sound_func_002b8b78(u32 se_id);
    extern void* g_CampWork_0043dd68;
}

extern "C" u32 h10_camp_burroughs_appdispatch_candidate(u32 app_id) {
    u8* work = static_cast<u8*>(g_CampWork_0043dd68);
    if (!work) return 0;

    if (work[0x430] != 0) {
        *reinterpret_cast<u32*>(work + 0x478) = app_id;
        return 0;
    }

    u32 f42c = *reinterpret_cast<u32*>(work + 0x42c);
    if (camp_func_002971e4(f42c, app_id) == 0) {
        return 0;
    }

    if (app_id == 7 || app_id == 8 || app_id == 9 || app_id == 10 || app_id == 11 || app_id == 13) {
        camp_func_002a0f68(1);
        sound_func_002b8b78(0x9e);
    } else if (app_id == 12) {
        camp_func_002a0f68(1);
    }

    *reinterpret_cast<s32*>(work + 0x478) = -1;
    *reinterpret_cast<u32*>(work + 0x434) = app_id;
    work[0x430] = 1;
    return 1;
}

extern "C" void h10_camp_burroughs_appdispatch_mutation(u32 app_id) {
    g_CampWork_0043dd68 = reinterpret_cast<void*>(0xDEADBEEF);
}
''', encoding='utf-8')

# 3. Quest_ResetSelection (0x0026A004, 40 bytes)
f3 = EXP_DIR / 'h10_camp_quest_resetselection_candidate.cpp'
f3.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    extern void* g_CampWork_0043dd68;
}

extern "C" void h10_camp_quest_resetselection_candidate(u32 cat) {
    u8* work = static_cast<u8*>(g_CampWork_0043dd68);
    if (!work) return;
    work[0x420] = static_cast<u8>(cat);
    *reinterpret_cast<u32*>(work + 0x400) = 0;
    *reinterpret_cast<u32*>(work + 0x3fc) = 0;
}

extern "C" void h10_camp_quest_resetselection_mutation(u32 cat) {
    g_CampWork_0043dd68 = reinterpret_cast<void*>(0xDEADBEEF);
}
''', encoding='utf-8')

# 4. Quest_EvaluateTargetCondition (0x0026A86C, 152 bytes)
f4 = EXP_DIR / 'h10_camp_quest_evaltarget_candidate.cpp'
f4.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" u32 h10_camp_quest_evaltarget_candidate(const u8* entry, const u8* cond) {
    u32 f38 = *reinterpret_cast<const u32*>(entry + 0x38);
    u32 type = (f38 >> 16) & 0xF;
    if (type != 5 && type != 6) return 0;

    u8 cond_type = cond[0x23];
    if (cond_type == 0 || cond_type == 1) {
        u32 c28 = *reinterpret_cast<const u32*>(cond + 0x28);
        u32 target_val = (c28 >> 12) & 0x1F;
        u32 entry_val = (f38 >> 11) & 0x1F;
        return target_val == entry_val;
    }

    if (cond_type == 3) {
        if ((f38 & 0xF800) != 0xA000) return 0;
        u16 c36 = *reinterpret_cast<const u16*>(cond + 0x36);
        u32 shifted = (static_cast<u32>(c36) << 20);
        if (shifted == 0) {
            return cond[0x43] != 0;
        }
        return shifted != 0xFA000000;
    }

    return 0;
}

extern "C" u32 h10_camp_quest_evaltarget_mutation(const u8* entry, const u8* cond) {
    return 0xDEADBEEF;
}
''', encoding='utf-8')

# 5. Quest_GetAvailability (0x0026A9FC, 196 bytes)
f5 = EXP_DIR / 'h10_camp_quest_getavailability_candidate.cpp'
f5.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    u8* Quest_GetMainEntry_002ae3f0(u32 id);
    u8* Quest_GetSubTable_002aa224(void*);
    u8* engine_func_002c0ec4(u32, u32);
    u8* engine_func_002c0e9c();
    u8* engine_func_002c0e4c(u8*);
    u8* Quest_FindEntry_002b48dc(void* params);
    extern void* g_QuestTableMgr_00433158;
}

extern "C" u32 h10_camp_quest_getavailability_candidate(u32 quest_id) {
    if (quest_id <= 0x190) {
        u8* entry = Quest_GetMainEntry_002ae3f0(quest_id);
        if (!entry) return 0;
        u32 f38 = *reinterpret_cast<u32*>(entry + 0x38);
        return (static_cast<int32_t>(f38) >= 0) ? 1 : 0;
    }

    u8* sub = Quest_GetSubTable_002aa224(g_QuestTableMgr_00433158);
    u8* entry = nullptr;
    if (sub) {
        entry = sub;
    } else {
        u8* p1 = engine_func_002c0ec4(4, 1);
        u8* p2 = engine_func_002c0e9c();
        u8* p3 = engine_func_002c0e4c(p1);
        u32 search_buf[16];
        search_buf[9] = quest_id;
        entry = Quest_FindEntry_002b48dc(search_buf);
    }

    if (!entry) return 0;
    u32 f38 = *reinterpret_cast<u32*>(entry + 0x38);
    return !(f38 & 0x40000000);
}

extern "C" u32 h10_camp_quest_getavailability_mutation(u32 quest_id) {
    return 0xDEADBEEF;
}
''', encoding='utf-8')

# 6. Quest_UnpackEntryData (0x0026AAC0, 256 bytes)
f6 = EXP_DIR / 'h10_camp_quest_unpackentry_candidate.cpp'
f6.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" {
    u8* Quest_GetStaticDef_002b087c(u32 id);
    void AsdMem_Zero_002c4b30(void* ptr, u32 size);
    void Quest_InitEntrySub_002bcf58(void* ptr);
    u8* Quest_GetDynamicRecord_002b9364(u32 id);
    void Quest_FormatTitle_0024be90(void* out, u16 flag);
}

extern "C" void h10_camp_quest_unpackentry_candidate(u32 quest_id, u8* out) {
    u8* def = Quest_GetStaticDef_002b087c(quest_id);
    AsdMem_Zero_002c4b30(out, 0x604);

    *reinterpret_cast<u16*>(out + 0x46) = static_cast<u16>(quest_id);
    out[0x48] = def[2];

    *reinterpret_cast<u16*>(out) = *reinterpret_cast<u16*>(def + 4);
    *reinterpret_cast<u16*>(out + 2) = *reinterpret_cast<u16*>(def + 8);
    *reinterpret_cast<u16*>(out + 4) = *reinterpret_cast<u16*>(def + 0xc);
    *reinterpret_cast<u16*>(out + 6) = *reinterpret_cast<u16*>(def + 0xe);
    *reinterpret_cast<u16*>(out + 8) = *reinterpret_cast<u16*>(def + 0x10);
    *reinterpret_cast<u16*>(out + 0xa) = *reinterpret_cast<u16*>(def + 0x12);
    *reinterpret_cast<u16*>(out + 0xc) = *reinterpret_cast<u16*>(def + 0x14);

    Quest_InitEntrySub_002bcf58(out + 0x1c);

    *reinterpret_cast<u32*>(out + 0xe) = *reinterpret_cast<u32*>(out);
    *reinterpret_cast<u32*>(out + 0x12) = *reinterpret_cast<u32*>(out + 4);
    *reinterpret_cast<u32*>(out + 0x16) = *reinterpret_cast<u32*>(out + 8);
    *reinterpret_cast<u16*>(out + 0x1a) = *reinterpret_cast<u16*>(out + 0xc);

    for (int i = 0; i < 8; ++i) {
        *reinterpret_cast<u16*>(out + 0x34 + i * 2) = *reinterpret_cast<u16*>(def + 0x48 + i * 2);
    }

    u8* rec = Quest_GetDynamicRecord_002b9364(quest_id);
    u16 flag = *reinterpret_cast<u16*>(rec + 0x38);
    Quest_FormatTitle_0024be90(out, flag);

    *reinterpret_cast<u16*>(out + 0x2a) = *reinterpret_cast<u16*>(out + 0xe);
    *reinterpret_cast<u16*>(out + 0x2c) = *reinterpret_cast<u16*>(out + 0x10);
}

extern "C" void h10_camp_quest_unpackentry_mutation(u32 quest_id, u8* out) {
    if (out) out[0] = 0xFF;
}
''', encoding='utf-8')

# 7. AppStore_SetFlag (0x003253D8, 56 bytes)
f7 = EXP_DIR / 'h10_camp_appstore_setflag_candidate.cpp'
f7.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    void app_func_00242a80(void* work, u32 flag);
    u8* app_func_00293c98();
    extern void* g_AppStoreWork_00439ca8;
}

extern "C" u32 h10_camp_appstore_setflag_candidate() {
    void* work = g_AppStoreWork_00439ca8;
    app_func_00242a80(work, 1);
    u8* base = app_func_00293c98();
    u32* flag_ptr = reinterpret_cast<u32*>(base + 0x44a0);
    *flag_ptr |= 0x20000000;
    return 1;
}

extern "C" void h10_camp_appstore_setflag_mutation() {
    g_AppStoreWork_00439ca8 = reinterpret_cast<void*>(0xDEADBEEF);
}
''', encoding='utf-8')

# 8. AppStore_GetAppParam (0x00325444, 52 bytes)
f8 = EXP_DIR / 'h10_camp_appstore_getappparam_candidate.cpp'
f8.write_text('''#include <cstdint>
typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" {
    u32 app_func_00296f60(u32);
    u8* app_func_00293c98();
    void app_func_00245318(u8*, u32);
    u8* engine_func_002c0e9c();
    void app_func_0028df54(u16);
}

extern "C" u32 h10_camp_appstore_getappparam_candidate() {
    u32 r4 = app_func_00296f60(0);
    u8* r0 = app_func_00293c98();
    app_func_00245318(r0, 4);
    u8* table = engine_func_002c0e9c();
    u16 val = *reinterpret_cast<u16*>(table + (r4 * 4));
    app_func_0028df54(val);
    return 1;
}

extern "C" void h10_camp_appstore_getappparam_mutation() {
    // Deliberate bug
}
''', encoding='utf-8')

candidates = [
    (f1, 'h10_camp_burroughs_getsavedata', 'h10_camp_burroughs_getsavedata_candidate', 0x002A0FAC, 24),
    (f2, 'h10_camp_burroughs_appdispatch', 'h10_camp_burroughs_appdispatch_candidate', 0x002A0EA8, 168),
    (f3, 'h10_camp_quest_resetselection', 'h10_camp_quest_resetselection_candidate', 0x0026A004, 40),
    (f4, 'h10_camp_quest_evaltarget', 'h10_camp_quest_evaltarget_candidate', 0x0026A86C, 152),
    (f5, 'h10_camp_quest_getavailability', 'h10_camp_quest_getavailability_candidate', 0x0026A9FC, 196),
    (f6, 'h10_camp_quest_unpackentry', 'h10_camp_quest_unpackentry_candidate', 0x0026AAC0, 256),
    (f7, 'h10_camp_appstore_setflag', 'h10_camp_appstore_setflag_candidate', 0x003253D8, 56),
    (f8, 'h10_camp_appstore_getappparam', 'h10_camp_appstore_getappparam_candidate', 0x00325444, 52),
]

all_passed = True
print("=== Compiling all 8 Milestone H10 Semantic Candidates ===")
for src, name, cand_fn, addr, orig_size in candidates:
    obj = BUILD_DIR / f'{name}.o'
    res = compile_tu_armv6k(src, obj, ROOT)
    if res.returncode != 0:
        print(f"FAILED to compile {src}: {res.stderr}")
        all_passed = False
        continue

    funcs = extract_elf_functions_detailed(obj)
    if cand_fn not in funcs:
        print(f"FAILED: symbol {cand_fn} not found in {obj}")
        all_passed = False
        continue

    code, relocs = funcs[cand_fn]
    cand_size = len(code)
    margin = orig_size - cand_size

    status = "OK" if margin >= 0 else "OVERFLOW"
    if margin < 0:
        all_passed = False

    print(f"[{status}] {name:<36} | Cand: {cand_size:>4} B | Window: {orig_size:>4} B | Headroom: +{margin:>4} B | Relocs: {len(relocs)}")

if not all_passed:
    sys.exit(1)

print("\nALL 8 H10 CANDIDATES SUCCESSFULLY BUILT WITHIN ORIGINAL WINDOW FOOTPRINTS!")
