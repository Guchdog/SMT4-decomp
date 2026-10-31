#!/usr/bin/env python3
"""Build and verify all Milestone H9 semantic C++ candidates."""
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

EXP_DIR = ROOT / 'experiments/semantic_equivalence'
EXP_DIR.mkdir(parents=True, exist_ok=True)
BUILD_DIR = ROOT / 'build/h9_candidates'
BUILD_DIR.mkdir(parents=True, exist_ok=True)

# 1. UniteEffect_Init (0x002E315C, 344 bytes)
uniteeff_cpp = EXP_DIR / 'h9_camp_uniteeffect_init_candidate.cpp'
uniteeff_cpp.write_text('''#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void  engine_func_002c0ba8(void* ptr, u32 id);
    void  engine_func_002976ac(void* ptr, const char* mbm, const char* bf);

    extern void* g_UniteEffectWork_0043dd90;
}

extern "C" void h9_camp_uniteeffect_init_candidate() {
    u8* work = static_cast<u8*>(g_UniteEffectWork_0043dd90);
    if (!work) {
        work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 0x958, 1));
        g_UniteEffectWork_0043dd90 = work;
    }
    AsdMem_Zero_002c4b30(work, 0x958);

    void* calc = AsdTask_Create_002c5978("UniteEffect CALC", 2, 0, 0, reinterpret_cast<void*>(0x002F6420), work, 0);
    *reinterpret_cast<void**>(work) = calc;

    AsdTask_CreateDraw_002c4c00("UniteEffect UP", 0xE7, 0, 0, reinterpret_cast<void*>(0x002C9DA4), work, 0);
    AsdTask_CreateDraw_002c4c00("UniteEffect DOWN", 0x6F, 0, 0, reinterpret_cast<void*>(0x002C9DA4), work, 0);

    engine_func_002c0ba8(work + 0x18, 0x25);
    engine_func_002976ac(work, "camp/unite_eff.mbm", "camp/unite_eff.bf");
}

extern "C" void h9_camp_uniteeffect_init_mutation() {
    g_UniteEffectWork_0043dd90 = reinterpret_cast<void*>(0xDEADBEEF);
}
''', encoding='utf-8')

# 2. bibleMain_Init (0x00269CC8, 352 bytes)
biblemain_cpp = EXP_DIR / 'h9_camp_biblemain_init_candidate.cpp'
biblemain_cpp.write_text('''#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);

    extern void* g_BibleMainWork_0043da10;
}

struct BibleMainWork {
    void* proc_task;
    void* draw_up_task;
    void* draw_down_task;
    u8 flag_0c;
    u8 flag_0d;
    u8 pad[2];
    u32 state;
    u8 flag_14;
    u8 pad2[11];
};

extern "C" void h9_camp_biblemain_init_candidate() {
    BibleMainWork* work = static_cast<BibleMainWork*>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 0x20, 1));
    g_BibleMainWork_0043da10 = work;
    if (!work) return;

    work->flag_0c = 0;
    work->flag_0d = 0;
    work->state = 1;
    work->flag_14 = 1;

    void* calc = AsdTask_Create_002c5978("BibleMainProc", 2, 0, 0, reinterpret_cast<void*>(0x001E4640), work, 0);
    work->proc_task = calc;

    work->draw_up_task = AsdTask_CreateDraw_002c4c00("BibleDrawUp", 0x6F, 1, 0, reinterpret_cast<void*>(0x0020EC04), work, reinterpret_cast<u32>(calc));
    work->draw_down_task = AsdTask_CreateDraw_002c4c00("BibleDrawDown", 0xE6, 1, 0, reinterpret_cast<void*>(0x002C9DA4), work, reinterpret_cast<u32>(calc));
}

extern "C" void h9_camp_biblemain_init_mutation() {
    g_BibleMainWork_0043da10 = reinterpret_cast<void*>(0xDEADBEEF);
}
''', encoding='utf-8')

# 3. bibleLegionSkill_Init (0x003AB770, 592 bytes)
legionskill_cpp = EXP_DIR / 'h9_camp_biblelegionskill_init_candidate.cpp'
legionskill_cpp.write_text('''#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void  unite_func_00232800(void* ptr, u32 a, u32 b, u32 c);
    void  unite_func_00233600(void* ptr);
    void  shop_func_002333d4(void* ptr, u32 flag);
    void* engine_func_002c23f8(u32 size);
    void  unite_func_002333bc(void* ptr);
    void  unite_func_003ab0d0(void* ptr);
    void  unite_func_00233804(void* ptr, u32 a, u32 b, u32 c);
    void  camp_func_0029f10c(u32 a, u32 color);
    void  bibleLegionDraw_func_003ad300();

    extern void* g_BibleLegionSkillHandle_0043d9f8;
}

extern "C" void h9_camp_biblelegionskill_init_candidate(u8* work) {
    *reinterpret_cast<u32*>(work + 0x14) = 0;
    *reinterpret_cast<u32*>(work + 0x18) = 0;
    work[0x94] = 0;
    *reinterpret_cast<u16*>(work + 0xA5B0) = 0;

    void** vtbl = *reinterpret_cast<void***>(work);
    reinterpret_cast<void(*)(void*)>(vtbl[8])(work);

    void** handle = static_cast<void**>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 4, 1));
    g_BibleLegionSkillHandle_0043d9f8 = handle;
    handle[0] = work;

    void* calc = AsdTask_Create_002c5978("BIBLE LEGIONSKILL CALC", 2, 0, 0, reinterpret_cast<void*>(0x003AD034), handle, 0);
    *reinterpret_cast<void**>(work + 4) = calc;

    AsdTask_CreateDraw_002c4c00("BIBLE LEGIONSKILL UP", 0x6F, 1, 0, reinterpret_cast<void*>(0x003AD288), handle, reinterpret_cast<u32>(calc));
    AsdTask_CreateDraw_002c4c00("BIBLE LEGIONSKILL DOWN", 0xE6, 1, 0, reinterpret_cast<void*>(0x003AD588), handle, reinterpret_cast<u32>(calc));

    unite_func_00232800(work + 0xC8, 0x140, 0, 0x1D);
    unite_func_00233600(work + 0xDC);
    shop_func_002333d4(work + 0xDC, 0);
    shop_func_002333d4(work + 0xDC, 1);

    void* ui = engine_func_002c23f8(0x68);
    if (ui) {
        unite_func_002333bc(ui);
        *static_cast<void**>(ui) = reinterpret_cast<void*>(0x0042207C);
    }
    *reinterpret_cast<void**>(work + 0x590) = ui;
    *reinterpret_cast<void**>(static_cast<u8*>(ui) + 0x64) = work + 0xC8;

    unite_func_003ab0d0(work);
    unite_func_00233804(work + 0x56C, 0x1D, 0x40E, 0xA);
    work[0x56C] = 1;
    camp_func_0029f10c(0, 0x323232FF);
    bibleLegionDraw_func_003ad300();
    *reinterpret_cast<u32*>(work + 0x14) = 1;
    *reinterpret_cast<u32*>(work + 0x18) = 0;
}

extern "C" void h9_camp_biblelegionskill_init_mutation() {
    g_BibleLegionSkillHandle_0043d9f8 = reinterpret_cast<void*>(0xDEADBEEF);
}
''', encoding='utf-8')

# 4. bibleLegionDraw_Init (0x003AD300, 596 bytes)
legiondraw_cpp = EXP_DIR / 'h9_camp_biblelegiondraw_init_candidate.cpp'
legiondraw_cpp.write_text('''#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;
typedef int8_t s8;
typedef int16_t s16;
typedef float f32;

struct LegionDrawManager {
    s8 ref_count;
    u8 pad[3];
    u8* work;
};

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void  UiSpriteGroup_Init_002c3344(void* obj);
    void  UiSpriteGroup_BindTable_002c32f8(void* obj, u32 t1, u32 s1, u32 t2, u32 s2, u32 a, u32 b, u32 c, u32 d, u32 t3, u32 s3);
    void  camp_func_002bdb2c(void* node, u32 a, u32 b, void* grp, f32 scale, u32 flag);
    void  battle_func_002af854(void* node, u32 a, u32 b);

    extern LegionDrawManager g_BibleLegionDrawManager_0043d9e0;
}

extern "C" void h9_camp_biblelegiondraw_init_candidate() {
    LegionDrawManager* mgr = &g_BibleLegionDrawManager_0043d9e0;
    if (mgr->ref_count <= 0) {
        u8* work = mgr->work;
        if (!work) {
            work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 0x474, 1));
            mgr->work = work;
            *reinterpret_cast<u32*>(work + 4) = 0;
            *reinterpret_cast<s16*>(work + 8) = -1;
            *reinterpret_cast<u32*>(work + 0xC) = 0;
            *reinterpret_cast<s16*>(work + 0x10) = -1;
            *reinterpret_cast<u32*>(work + 0x14) = 0;
            *reinterpret_cast<s16*>(work + 0x18) = -1;
            work[0x1C] = 0;
            work[0x1D] = 0;
            work[0x1E] = 0;
            work[0x1F] = 0;
            AsdMem_Zero_002c4b30(work + 0x290, 0x1E0);
            *reinterpret_cast<u32*>(work + 0x470) = 0;
        }

        void* calc = AsdTask_Create_002c5978("LegionDrawUp CALC", 2, 0, 0, reinterpret_cast<void*>(0x003AC6A0), 0, 0);
        *reinterpret_cast<void**>(work) = calc;

        UiSpriteGroup_Init_002c3344(work + 0x20);
        UiSpriteGroup_BindTable_002c32f8(work + 0x20, 0x00402414, 0x24, 0x00402438, 0x18, 0, 0, 0, 0, 0x00402450, 0x70);

        for (u32 i = 0; i < 2; ++i) {
            u8* node = work + i * 0x8C;
            camp_func_002bdb2c(node + 0x40, 0x23, 0, work + 0x20, 1.0f, 0x15);
            battle_func_002af854(node + 0x40, 0, 0);
            camp_func_002bdb2c(node + 0x158, 0x23, 0, work + 0x20, 1.0f, 0x15);
            battle_func_002af854(node + 0x158, 1, 0);
        }
    }
    mgr->ref_count++;
}

extern "C" void h9_camp_biblelegiondraw_init_mutation() {
    LegionDrawManager* mgr = &g_BibleLegionDrawManager_0043d9e0;
    mgr->ref_count = -1;
}
''', encoding='utf-8')

# 5. SortMenu_Init (0x0029E63C, 644 bytes)
sortmenu_cpp = EXP_DIR / 'h9_camp_sortmenu_init_candidate.cpp'
sortmenu_cpp.write_text('''#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;
typedef int8_t s8;
typedef int32_t s32;
typedef float f32;

struct SortMenuManager {
    s8 ref_count;
    u8 pad[3];
    u8* work;
};

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void  UiSpriteGroup_Init_002c3344(void* obj);
    void  UiSpriteGroup_BindTable_002c32f8(void* obj, u32 t1, u32 s1, u32 t2, u32 s2, u32 a, u32 b, u32 c, u32 d, u32 t3, u32 s3);
    void  UiAnimSprite_SetupEx_002bdb2c(void* node, u32 a, u32 b, void* grp, f32 scale, u32 flag);
    void  UiAnimSprite_SetMode_002bdac0(void* node, u32 a, u32 b);

    extern SortMenuManager g_SortMenuManager_0043dd20;
}

extern "C" void h9_camp_sortmenu_init_candidate(s32 mode) {
    SortMenuManager* mgr = &g_SortMenuManager_0043dd20;
    if (mgr->ref_count <= 0) {
        u8* work = mgr->work;
        if (!work) {
            work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 0x878, 1));
            mgr->work = work;
        }
        AsdMem_Zero_002c4b30(work, 0x878);

        void* calc = AsdTask_Create_002c5978("SORT CALC", 2, 0, 0, reinterpret_cast<void*>(0x001A1E7C), work, 0);
        *reinterpret_cast<void**>(work) = calc;

        void* draw = AsdTask_CreateDraw_002c4c00("SORT DDRAW", 0xE7, 0, 0, reinterpret_cast<void*>(0x001A25CC), work, 0);
        *reinterpret_cast<void**>(work + 4) = draw;

        UiSpriteGroup_Init_002c3344(work + 0x08);
        UiSpriteGroup_BindTable_002c32f8(work + 0x08, 0x00402DAC, 0x24, 0x00402DAC, 0x18, 0, 0, 0, 0, 0x00402DAC, 0xA8);

        for (u32 i = 0; i < 13; ++i) {
            u8* node = work + 0x28 + i * 0x64;
            UiAnimSprite_SetupEx_002bdb2c(node, 0x1E, 0, work + 0x08, 1.0f, 0);
            UiAnimSprite_SetMode_002bdac0(node, 0, 0);
        }

        *reinterpret_cast<s32*>(work + 0x750) = mode;
    }
    mgr->ref_count++;
}

extern "C" void h9_camp_sortmenu_init_mutation() {
    SortMenuManager* mgr = &g_SortMenuManager_0043dd20;
    mgr->ref_count = -1;
}
''', encoding='utf-8')

# 6. UniteCtrl_RosterPopulate (0x003C9EBC, 664 bytes)
unitectrl_cpp = EXP_DIR / 'h9_camp_unitectrl_roster_candidate.cpp'
unitectrl_cpp.write_text('''#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" {
    void* ui_Tbb_GetGlobalSubTable_001b9a90(u32 a, u32 b);
    u32   ui_Tbb_GetRowCount_001b9aa4(void* tbl);
    void* Battle_GetTalkEntry_00215fa8(u16 id);
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  qsort_002b7f0a(void* base, u32 num, u32 size, void* cmp);

    extern void* g_UniteCtrlRoster_0043dd40;
}

struct UniteBibleRow {
    u16 id;
    u8 race;
    u8 field_03;
    u16 flags;
};

struct UniteCtrlEntry {
    u16 demon_id;
    u8 field_02;
    u8 pad;
};

struct UniteCtrlRoster {
    u8 counts[0x38];
    UniteCtrlEntry* buckets[0x38];
    u16 field_118;
    u16 field_11a;
    u16 field_11c;
    u16 field_11e;
    u8  field_120;
    u8  field_121;
    u8  field_122[4];
    u8  field_126[4];
    u8  field_12a[4];
    u8  field_12e[4];
    u8  field_132;
    u8  pad_133;
    u16 field_134;
    u8  field_136;
    u8  pad_137;
    u16 field_138;
    u16 field_13a;
    u8  pad_13c[6];
    u8  field_142;
    u8  field_143;
    u8  pad_144[0x38];
    u8  field_17c;
};

extern "C" void h9_camp_unitectrl_roster_candidate(UniteCtrlRoster* roster) {
    void* tbl = ui_Tbb_GetGlobalSubTable_001b9a90(0, 0);
    u32 row_count = ui_Tbb_GetRowCount_001b9aa4(tbl);

    u8 local_counts[0x38];
    for (u32 i = 0; i < 0x38; ++i) {
        local_counts[i] = 0;
        roster->counts[i] = 0;
        roster->buckets[i] = nullptr;
    }

    for (u32 i = 0; i < row_count; ++i) {
        UniteBibleRow* row = static_cast<UniteBibleRow*>(Battle_GetTalkEntry_00215fa8(static_cast<u16>(i)));
        if (!row) continue;
        u32 race = row->race;
        if (race < 0x38 && (row->flags & 1)) {
            roster->counts[race]++;
        }
    }

    for (u32 i = 0; i < 0x38; ++i) {
        u8 count = roster->counts[i];
        if (count > 0) {
            roster->buckets[i] = static_cast<UniteCtrlEntry*>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, count * sizeof(UniteCtrlEntry), 1));
        }
    }

    for (u32 i = 0; i < row_count; ++i) {
        UniteBibleRow* row = static_cast<UniteBibleRow*>(Battle_GetTalkEntry_00215fa8(static_cast<u16>(i)));
        if (!row) continue;
        u32 race = row->race;
        if (race < 0x38 && (row->flags & 1)) {
            u8 idx = local_counts[race]++;
            UniteCtrlEntry* ent = roster->buckets[race];
            if (ent) {
                ent[idx].demon_id = row->id;
                ent[idx].field_02 = row->field_03;
            }
        }
    }

    for (u32 i = 0; i < 0x38; ++i) {
        if (roster->buckets[i]) {
            qsort_002b7f0a(roster->buckets[i], roster->counts[i], sizeof(UniteCtrlEntry), reinterpret_cast<void*>(0x00219600));
        }
    }

    roster->field_11c = 0;
    roster->field_11e = 0;
    roster->field_118 = 0;
    roster->field_11a = 0;
    roster->field_143 = 0;
    roster->field_120 = 0;
    roster->field_121 = 0;
    for (u32 i = 0; i < 4; ++i) roster->field_122[i] = 0;
    for (u32 i = 0; i < 4; ++i) roster->field_126[i] = 0;
    for (u32 i = 0; i < 4; ++i) roster->field_12a[i] = 0;
    for (u32 i = 0; i < 4; ++i) roster->field_12e[i] = 0;
    roster->field_132 = 0;
    roster->field_134 = static_cast<u16>(roster->field_134 & 0x03FF);
    roster->field_136 = 0;
    roster->field_138 = 0xFFFF;
    roster->field_13a = 0xFFFF;
    roster->field_17c = 0;
}

extern "C" void h9_camp_unitectrl_roster_mutation(UniteCtrlRoster* roster) {
    roster->counts[0] = 0xFF;
}
''', encoding='utf-8')

# 7. bibleDevil_Init (0x003A7AD8, 668 bytes)
bibledevil_cpp = EXP_DIR / 'h9_camp_bibledevil_init_candidate.cpp'
bibledevil_cpp.write_text('''#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;
typedef int32_t s32;
typedef int16_t s16;

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void  unite_func_00232800(void* ptr, u32 a, u32 b, u32 c);
    void* engine_func_002c23f8(u32 size);
    void  unite_func_002333bc(void* ptr);
    void  unite_func_0022d5c8(void* ptr);
    void  unite_func_003aad60(void* ptr);
    void  unite_func_0022df7c(void* ptr, u32 val);
    s32   unite_func_002338ac(void* ptr);
    void  unite_func_00233600(void* ptr);
    void  unite_func_00233804(void* ptr, u32 a, u32 b, u32 c);
    void  camp_func_0029f10c(u32 a, u32 color);
    void  unite_func_002e32c8();
    void  camp_func_0022d33c(void* ptr);

    extern void* g_BibleDevilHandle_0043d9c8;
}

extern "C" void h9_camp_bibledevil_init_candidate(u8* work) {
    work[0x5A5] = 1;
    work[0x94] = 0;
    *reinterpret_cast<u16*>(work + 0xA5B0) = 0;
    *reinterpret_cast<s16*>(work + 0xA5B2) = -1;

    void** vtbl = *reinterpret_cast<void***>(work);
    reinterpret_cast<void(*)(void*)>(vtbl[8])(work);

    void** handle = static_cast<void**>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 4, 1));
    g_BibleDevilHandle_0043d9c8 = handle;
    handle[0] = work;

    void* calc = AsdTask_Create_002c5978("BIBLE DEVIL CALC", 2, 0, 0, reinterpret_cast<void*>(0x003AAF08), handle, 0);
    *reinterpret_cast<void**>(work + 4) = calc;

    AsdTask_CreateDraw_002c4c00("BIBLE DEVIL UP", 0x6F, 1, 0, reinterpret_cast<void*>(0x003AC958), handle, reinterpret_cast<u32>(calc));
    AsdTask_CreateDraw_002c4c00("BIBLE DEVIL DOWN", 0xE6, 1, 0, reinterpret_cast<void*>(0x003ACC74), handle, reinterpret_cast<u32>(calc));

    unite_func_00232800(work + 0xC8, 0x140, 0, 0x1D);

    void* ui = engine_func_002c23f8(0x68);
    if (ui) {
        unite_func_002333bc(ui);
        *static_cast<void**>(ui) = reinterpret_cast<void*>(0x0042207C);
    }
    *reinterpret_cast<void**>(work + 0x590) = ui;
    *reinterpret_cast<void**>(static_cast<u8*>(ui) + 0x64) = work + 0xC8;

    unite_func_0022d5c8(work);
    unite_func_003aad60(work + 0x5A8);
    unite_func_0022df7c(work + 0x5A8, 0);

    s32 vis = unite_func_002338ac(work + 0x20);
    for (s32 i = 0; i < vis; ++i) {
        s16 did = *reinterpret_cast<s16*>(work + 0x5A8 + 4 + i * 0x20);
        if (did != 0) {
            unite_func_0022df7c(work + 0x5A8, static_cast<u16>(did));
        }
    }

    unite_func_00233600(work + 0xDC);

    s32 rows = *reinterpret_cast<s32*>(work + 0x568);
    if (rows > 10) rows = 10;
    unite_func_00233804(work + 0x56C, 0x1D, 0x40E, rows);
    work[0x56C] = 1;
    camp_func_0029f10c(0, 0x323232FF);
    *reinterpret_cast<u32*>(work + 0x14) = 0;
    *reinterpret_cast<u32*>(work + 0x18) = 0;
    unite_func_002e32c8();
    camp_func_0022d33c(work);
}

extern "C" void h9_camp_bibledevil_init_mutation() {
    g_BibleDevilHandle_0043d9c8 = reinterpret_cast<void*>(0xDEADBEEF);
}
''', encoding='utf-8')

# 8. ButtonHelp_Init (0x0028D974, 736 bytes)
btnhelp_cpp = EXP_DIR / 'h9_camp_buttonhelp_init_candidate.cpp'
btnhelp_cpp.write_text('''#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;
typedef int8_t s8;
typedef float f32;

struct ButtonHelpManager {
    s8 ref_count;
    u8 pad[3];
    u8* work;
};

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void  UiSpriteGroup_Init_002c3344(void* obj);
    void  UiSpriteGroup_BindTable_002c32f8(void* obj, u32 t1, u32 s1, u32 t2, u32 s2, u32 a, u32 b, u32 c, u32 d, u32 t3, u32 s3);
    void  UiAnimSprite_SetupEx_002bdb2c(void* node, u32 a, u32 b, void* grp, f32 scale, u32 flag);
    void  UiAnimSprite_SetMode_002bf030(void* node, u32 a, u32 b, u32 c);

    extern ButtonHelpManager g_ButtonHelpManager_0043da28;
}

extern "C" void h9_camp_buttonhelp_init_candidate() {
    ButtonHelpManager* mgr = &g_ButtonHelpManager_0043da28;
    if (mgr->ref_count <= 0) {
        u8* work = mgr->work;
        if (!work) {
            work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 0x564, 1));
            mgr->work = work;
        }
        AsdMem_Zero_002c4b30(work, 0x564);

        void* calc = AsdTask_Create_002c5978("ButtonHelp CALC", 1, 0, 0, reinterpret_cast<void*>(0x002108CC), work, 0);
        *reinterpret_cast<void**>(work) = calc;

        void* draw = AsdTask_CreateDraw_002c4c00("ButtonHelp DDRAW", 0xE6, 0, 0, reinterpret_cast<void*>(0x002108D0), work, 0);
        *reinterpret_cast<void**>(work + 8) = draw;

        UiSpriteGroup_Init_002c3344(work + 0x14);
        UiSpriteGroup_BindTable_002c32f8(work + 0x14, 0x004025A0, 0x0C, 0x004025A0, 0x30, 0, 0, 0, 0, 0x004025A0, 0xA8);

        for (u32 i = 0; i < 6; ++i) {
            u8* node = work + 0x34 + i * 0x64;
            UiAnimSprite_SetupEx_002bdb2c(node, 0x12, 3, work + 0x14, 1.0f, 0x10);
            UiAnimSprite_SetMode_002bf030(node, 0x12, i + 0x11, 3);
        }
    }
    mgr->ref_count++;
}

extern "C" void h9_camp_buttonhelp_init_mutation() {
    ButtonHelpManager* mgr = &g_ButtonHelpManager_0043da28;
    mgr->ref_count = -1;
}
''', encoding='utf-8')

candidates = [
    ('h9_camp_uniteeffect_init', uniteeff_cpp, 'h9_camp_uniteeffect_init_candidate', 344),
    ('h9_camp_biblemain_init', biblemain_cpp, 'h9_camp_biblemain_init_candidate', 352),
    ('h9_camp_biblelegionskill_init', legionskill_cpp, 'h9_camp_biblelegionskill_init_candidate', 592),
    ('h9_camp_biblelegiondraw_init', legiondraw_cpp, 'h9_camp_biblelegiondraw_init_candidate', 596),
    ('h9_camp_sortmenu_init', sortmenu_cpp, 'h9_camp_sortmenu_init_candidate', 644),
    ('h9_camp_unitectrl_roster', unitectrl_cpp, 'h9_camp_unitectrl_roster_candidate', 664),
    ('h9_camp_bibledevil_init', bibledevil_cpp, 'h9_camp_bibledevil_init_candidate', 668),
    ('h9_camp_buttonhelp_init', btnhelp_cpp, 'h9_camp_buttonhelp_init_candidate', 736),
]

all_passed = True
print("=== Compiling all 8 Milestone H9 Semantic Candidates ===")
for name, src, fn_name, win_sz in candidates:
    obj = BUILD_DIR / f"{name}.o"
    res = compile_tu_armv6k(src, obj, ROOT)
    if res.returncode != 0:
        print(f"FAILED: {name}")
        print(res.stderr)
        all_passed = False
        continue
    funcs = extract_elf_functions_detailed(obj)
    raw, relocs = funcs[fn_name]
    cand_sz = len(raw)
    margin = win_sz - cand_sz
    status = "OK" if margin >= 0 else "OVERFLOW"
    if margin < 0: all_passed = False
    print(f"[{status}] {name:<30} | Cand: {cand_sz:>4} B | Window: {win_sz:>4} B | Headroom: +{margin:>4} B | Relocs: {len(relocs)}")

if all_passed:
    print("ALL 8 CANDIDATES COMPILED CLEANLY WITHIN ALLOCATED WINDOWS!")
else:
    sys.exit(1)
