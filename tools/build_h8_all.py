#!/usr/bin/env python3
"""Build and verify all Milestone H8 semantic C++ candidates."""
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

EXP_DIR = ROOT / 'experiments/semantic_equivalence'
EXP_DIR.mkdir(parents=True, exist_ok=True)
BUILD_DIR = ROOT / 'build/h8_candidates'
BUILD_DIR.mkdir(parents=True, exist_ok=True)

# 1. StatusBustUp_Init (0x00223A90, 248 bytes)
bustup_cpp = EXP_DIR / 'h8_ui_status_bustup_candidate.cpp'
bustup_cpp.write_text('''#include <cstdint>

typedef uint32_t u32;
typedef uint8_t u8;
typedef int8_t s8;

extern "C" {
    void AsdRes_002c4e28(u32 id);
    void AsdRes_002c5b04(u32 id, u32 flag);
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void engine_func_002c3b48(void* ptr, u32 size);

    extern void* g_StatusBustUpWork_0044e158;
}

struct StatusBustUpWork {
    s8 ref_count;
    u8 pad[3];
    void* buffer1;
    void* buffer2;
};

extern "C" void h8_ui_status_bustup_candidate() {
    StatusBustUpWork* work = static_cast<StatusBustUpWork*>(g_StatusBustUpWork_0044e158);
    if (work->ref_count <= 0) {
        AsdRes_002c4e28(0x17);
        AsdRes_002c5b04(0x23, 0);
        if (!work->buffer1) {
            void* b1 = AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 0x266, 1);
            work->buffer1 = b1;
            engine_func_002c3b48(b1, 0x266);
        }
        if (!work->buffer2) {
            void* b2 = AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 0x81, 1);
            work->buffer2 = b2;
            engine_func_002c3b48(b2, 0x81);
        }
    }
    work->ref_count++;
}

extern "C" void h8_ui_status_bustup_mutation() {
    StatusBustUpWork* work = static_cast<StatusBustUpWork*>(g_StatusBustUpWork_0044e158);
    work->ref_count = -1;
}
''', encoding='utf-8')

# 2. StatusCamera_Init (0x00258E38, 480 bytes)
camera_cpp = EXP_DIR / 'h8_ui_status_camera_candidate.cpp'
camera_cpp.write_text('''#include <cstdint>

typedef uint32_t u32;
typedef uint8_t u8;
typedef float f32;

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    void  engine_func_002bc828(u32 a, u32 b, u32 c);
    void  engine_func_002c2210(void* obj, u32 flag);
    void  engine_func_002c20a8(void* obj, const f32* eye, const f32* target, const f32* up);
    void  engine_func_002c1ffc(void* obj, u32 flag, const f32* params);
    void  engine_func_00298fec(void* obj);
    void  engine_func_002c1740(void* obj);
    void  engine_func_002c1774(void* obj, f32 a, f32 b);

    extern void* g_StatusCameraWork_0044e178;
}

struct Vec3 {
    f32 x, y, z;
};

extern "C" void h8_ui_status_camera_candidate(const Vec3* pos, const Vec3* target, const Vec3* up,
                                             f32 fov, f32 aspect, f32 near_p, f32 far_p, f32 extra) {
    u8* work = static_cast<u8*>(g_StatusCameraWork_0044e178);
    if (!work) {
        work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 0x53C, 1));
        g_StatusCameraWork_0044e178 = work;
    }
    AsdMem_Zero_002c4b30(work, 0x53C);

    Vec3* work_target = reinterpret_cast<Vec3*>(work + 0x514);
    Vec3* work_pos    = reinterpret_cast<Vec3*>(work + 0x508);
    Vec3* work_up     = reinterpret_cast<Vec3*>(work + 0x520);

    *work_target = *target;
    *work_pos    = *pos;
    *work_up     = *up;

    *reinterpret_cast<f32*>(work + 0x530) = near_p;
    *reinterpret_cast<f32*>(work + 0x534) = fov;
    *reinterpret_cast<f32*>(work + 0x538) = aspect;
    *reinterpret_cast<f32*>(work + 0x52C) = far_p;

    Vec3 view_target;
    view_target.x = work_pos->x + work_target->x * far_p;
    view_target.y = work_pos->y + work_target->y * far_p;
    view_target.z = work_pos->z + work_target->z * far_p;

    f32 up_arr[3] = {0.0f, 1.0f, 0.0f};

    engine_func_002bc828(0, 0xC8, 0xF0);
    engine_func_002c2210(work, 1);
    engine_func_002c20a8(work, reinterpret_cast<const f32*>(work_pos), reinterpret_cast<const f32*>(&view_target), up_arr);
    engine_func_002c1ffc(work, 1, reinterpret_cast<const f32*>(work + 0x530));
    engine_func_00298fec(work);
    engine_func_002c1740(work);
    engine_func_002c1774(work, extra, far_p);
}

extern "C" void h8_ui_status_camera_mutation(const Vec3* pos, const Vec3* target, const Vec3* up,
                                             f32 fov, f32 aspect, f32 near_p, f32 far_p, f32 extra) {
    g_StatusCameraWork_0044e178 = nullptr;
}
''', encoding='utf-8')

# 3. Status_UpdateAffinityTable (0x00293E4C, 520 bytes)
affinity_cpp = EXP_DIR / 'h8_ui_status_affinity_candidate.cpp'
affinity_cpp.write_text('''#include <cstdint>

typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    void StatusDown_SetDisplayMode_00292f44(u32 mode);

    extern void* g_StatusContext_0044e140;
}

extern "C" void h8_ui_status_affinity_candidate() {
    u8* ctx = static_cast<u8*>(g_StatusContext_0044e140);
    if (!ctx) return;
    u8* r4 = *reinterpret_cast<u8**>(ctx + 4);
    if (!r4) return;

    *reinterpret_cast<u32*>(r4 + 0x14) = 0;
    r4[0x1E63] = 1;
    u8 r0 = r4[0x1E63 + 3]; // offset 0x1E66 or 0x1E67

    u8* r1_ptr = *reinterpret_cast<u8**>(ctx + 4);
    u8* r5 = r1_ptr + 0x1000;
    u32 state_2e4 = *reinterpret_cast<u32*>(r5 + 0x2E4);

    if (r0 == 0) {
        if (state_2e4 == 0) StatusDown_SetDisplayMode_00292f44(0);
        else if (state_2e4 == 1) StatusDown_SetDisplayMode_00292f44(1);
        else if (r4[0x1E63] == 0 && state_2e4 == 2) StatusDown_SetDisplayMode_00292f44(2);
    } else if (r0 == 6) {
        if (state_2e4 == 0) StatusDown_SetDisplayMode_00292f44(0);
        else if (state_2e4 == 1) StatusDown_SetDisplayMode_00292f44(1);
        else if (state_2e4 == 2) StatusDown_SetDisplayMode_00292f44(5);
    } else if (r0 == 8 || r0 == 9 || r0 == 10 || r0 == 11 || r0 == 7) {
        if (state_2e4 == 0) StatusDown_SetDisplayMode_00292f44(1);
        else if (state_2e4 == 1) StatusDown_SetDisplayMode_00292f44(4);
        else if (state_2e4 == 2) StatusDown_SetDisplayMode_00292f44(5);
    } else if (r0 == 14) {
        if (state_2e4 == 0) StatusDown_SetDisplayMode_00292f44(0);
    } else if (r0 == 13) {
        if (state_2e4 == 0) StatusDown_SetDisplayMode_00292f44(0);
        else if (state_2e4 == 1) StatusDown_SetDisplayMode_00292f44(1);
        else if (r4[0x1E63] == 0) {
            if (state_2e4 == 2) StatusDown_SetDisplayMode_00292f44(4);
            else if (state_2e4 == 3) StatusDown_SetDisplayMode_00292f44(5);
        }
    } else {
        if (r4[0x12F1] == 6) {
            if (state_2e4 == 0) StatusDown_SetDisplayMode_00292f44(1);
        } else {
            if (state_2e4 == 0) StatusDown_SetDisplayMode_00292f44(0);
            else if (state_2e4 == 1) StatusDown_SetDisplayMode_00292f44(1);
            if (r4[0x1E63] == 0) {
                if (state_2e4 == 2) StatusDown_SetDisplayMode_00292f44(4);
                else if (state_2e4 == 3) StatusDown_SetDisplayMode_00292f44(5);
            }
        }
    }
}

extern "C" void h8_ui_status_affinity_mutation() {
    StatusDown_SetDisplayMode_00292f44(0xDEADBEEF);
}
''', encoding='utf-8')

# 4. StatusDown_SortItemList (0x0032C4BC, 372 bytes)
sortitem_cpp = EXP_DIR / 'h8_ui_statusdown_itemsort_candidate.cpp'
sortitem_cpp.write_text('''#include <cstdint>

typedef uint32_t u32;
typedef uint8_t u8;
typedef int16_t s16;

typedef int (*CompareFn)(const void*, const void*);

extern "C" {
    u8* UiMenu_GetSortOptions_002a0fac(void* work);
    void qsort_002b7f0a(void* base, u32 num, u32 size, CompareFn cmp);
    void qsort_tail_0027f3d4(void* base, u32 num, u32 size, CompareFn cmp);

    extern void* g_StatusDownContext_0044e190;
    extern int StatusDown_ItemSortByIdAsc(const void*, const void*);
    extern int StatusDown_ItemSortByIdDesc(const void*, const void*);
    extern int StatusDown_ItemSortByTypeAsc(const void*, const void*);
    extern int StatusDown_ItemSortByTypeDesc(const void*, const void*);
    extern int engine_func_002dca98(const void*, const void*);
    extern int engine_func_002c6d30(const void*, const void*);
    extern int engine_func_001f61a4(const void*, const void*);
    extern int engine_func_001d1bb8(const void*, const void*);
}

extern "C" void h8_ui_statusdown_itemsort_candidate() {
    u8* work = static_cast<u8*>(g_StatusDownContext_0044e190);
    if (!work) return;

    u8* opt = UiMenu_GetSortOptions_002a0fac(work);
    u8 mode_byte = opt[0x16];
    u32 crit = mode_byte & 0x7F;
    bool desc = (mode_byte >> 7) != 0;

    void* base = work + 0xE30;
    s16 count = *reinterpret_cast<s16*>(work + 0x2230);

    if (crit == 1) {
        CompareFn cmp = desc ? StatusDown_ItemSortByIdDesc : StatusDown_ItemSortByIdAsc;
        qsort_002b7f0a(base, count, 4, cmp);
    } else if (crit == 8) {
        CompareFn cmp = desc ? engine_func_002c6d30 : engine_func_002dca98;
        qsort_002b7f0a(base, count, 4, cmp);
    } else if (crit == 2) {
        CompareFn cmp = desc ? StatusDown_ItemSortByTypeDesc : StatusDown_ItemSortByTypeAsc;
        qsort_002b7f0a(base, count, 4, cmp);
    } else if (crit == 3) {
        CompareFn cmp = desc ? engine_func_001d1bb8 : engine_func_001f61a4;
        qsort_002b7f0a(base, count, 4, cmp);
    }
}

extern "C" void h8_ui_statusdown_itemsort_mutation() {
    u8* work = static_cast<u8*>(g_StatusDownContext_0044e190);
    if (work) work[0x410] = 0xFF;
}
''', encoding='utf-8')

# 5. StatusDown_PopulateItemList (0x001EE7C8, 384 bytes)
popitem_cpp = EXP_DIR / 'h8_ui_statusdown_itemlist_candidate.cpp'
popitem_cpp.write_text('''#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;
typedef int16_t s16;

struct ItemEntry {
    u16 item_id;
    u8 pad[4];
    u16 flags;
};

extern "C" {
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    ItemEntry* ItemTable_Get_002b9364(u32 id);
    void  UiPage_Setup_0029fae8(void* page, s16 count, u32 rows, u32 cols, u32 f1, u32 f2);
    void  UiPage_SetScroll_0029edfc(void* page, s16 scroll);
    void  UiPage_SetCursor_0029eb58(void* page, s16 cursor);
    void  StatusDown_SortItemList_0032c4bc();

    extern void* g_StatusDownContext_0044e190;
}

extern "C" void h8_ui_statusdown_itemlist_candidate(const u8* item_counts) {
    u8* work = static_cast<u8*>(g_StatusDownContext_0044e190);
    if (!work) return;

    u8* header = work + 0x2200;
    *reinterpret_cast<u16*>(header + 0x30) = 0;
    *reinterpret_cast<u16*>(header + 0x32) = 0;

    AsdMem_Zero_002c4b30(work + 0xE30, 0x1400);

    for (u32 i = 0; i < 0x500; ++i) {
        ItemEntry* entry = ItemTable_Get_002b9364(i);
        if (entry && (entry->flags & 1)) {
            u16 id = entry->item_id;
            u8 qty = item_counts[id];
            if (qty > 0) {
                s16 count = *reinterpret_cast<s16*>(header + 0x30);
                u8* slot = work + 0xE30 + count * 4;
                *reinterpret_cast<u16*>(slot) = id;
                *reinterpret_cast<u16*>(slot + 2) = qty;
                *reinterpret_cast<u16*>(header + 0x32) += 1;
                *reinterpret_cast<s16*>(header + 0x30) = count + 1;
            }
        }
    }

    s16 total_items = *reinterpret_cast<s16*>(header + 0x30);
    void* page = work + 0x223C;
    UiPage_Setup_0029fae8(page, total_items, 9, 4, 1, 1);

    if (total_items > 0) {
        s16 scroll = *reinterpret_cast<s16*>(header + 0x36);
        s16 cursor = *reinterpret_cast<s16*>(header + 0x34);
        if (total_items <= cursor + scroll * 4) {
            scroll = (total_items - 1) / 4;
            cursor = total_items - 1 - scroll * 4;
            *reinterpret_cast<s16*>(header + 0x36) = scroll;
            *reinterpret_cast<s16*>(header + 0x34) = cursor;
        }
        UiPage_SetScroll_0029edfc(page, scroll);
        UiPage_SetCursor_0029eb58(page, cursor);
    } else {
        UiPage_SetScroll_0029edfc(page, *reinterpret_cast<s16*>(header + 0x36));
        UiPage_SetCursor_0029eb58(page, *reinterpret_cast<s16*>(header + 0x34));
    }

    StatusDown_SortItemList_0032c4bc();
    work[0x410] = 1;
}

extern "C" void h8_ui_statusdown_itemlist_mutation(const u8* item_counts) {
    u8* work = static_cast<u8*>(g_StatusDownContext_0044e190);
    if (work) work[0x410] = 0;
}
''', encoding='utf-8')

# 6. StatusDown_PopulateSkillList (0x001EE5A4, 548 bytes)
popskill_cpp = EXP_DIR / 'h8_ui_statusdown_skilllist_candidate.cpp'
popskill_cpp.write_text('''#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;
typedef int16_t s16;

struct SkillEntry {
    u16 skill_id;
    u8 pad[4];
    u16 flags;
    u8 pad2[0x30];
    u16 cost;
};

typedef int (*CompareFn)(const void*, const void*);

extern "C" {
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    SkillEntry* SkillTable_Get_002b9364(u32 id);
    void  UiPage_Setup_0029fae8(void* page, s16 count, u32 rows, u32 cols, u32 f1, u32 f2);
    u8*   UiMenu_GetSortOptions_002a0fac(void* work);
    void  qsort_002b7f0a(void* base, u32 num, u32 size, CompareFn cmp);

    extern void* g_StatusDownContext_0044e190;
    extern int StatusDown_SkillSortByIdAsc(const void*, const void*);
    extern int StatusDown_SkillSortByIdDesc(const void*, const void*);
    extern int StatusDown_SkillSortByCostAsc(const void*, const void*);
    extern int StatusDown_SkillSortByCostDesc(const void*, const void*);
    extern int StatusDown_SkillSortByNameAsc(const void*, const void*);
    extern int StatusDown_SkillSortByNameDesc(const void*, const void*);
}

extern "C" void h8_ui_statusdown_skilllist_candidate(const u8* skill_bitfield) {
    u8* work = static_cast<u8*>(g_StatusDownContext_0044e190);
    if (!work) return;

    u8* header = work + 0xDC0;
    *reinterpret_cast<u16*>(header + 0x8) = 0;
    *reinterpret_cast<u16*>(header + 0xA) = 0;

    AsdMem_Zero_002c4b30(work + 0x5C8, 0x800);

    for (u32 i = 0; i < 0x500; ++i) {
        SkillEntry* entry = SkillTable_Get_002b9364(i);
        if (entry && (entry->flags & 1) && entry->cost != 0) {
            u16 sid = entry->cost; // cost/id index
            if (skill_bitfield[sid >> 3] & (1 << (sid & 7))) {
                s16 count = *reinterpret_cast<s16*>(header + 0x8);
                u8* slot = work + 0x5C8 + count * 4;
                *reinterpret_cast<u16*>(slot) = entry->skill_id;
                *reinterpret_cast<u16*>(slot + 2) = entry->cost;
                *reinterpret_cast<s16*>(header + 0x8) = count + 1;
            }
            *reinterpret_cast<u16*>(header + 0xA) += 1;
        }
    }

    s16 total = *reinterpret_cast<s16*>(header + 0x8);
    void* page = work + 0xDCC;
    UiPage_Setup_0029fae8(page, total, 11, 1, 0, 1);

    u8* opt = UiMenu_GetSortOptions_002a0fac(work);
    u8 mode_byte = opt[0x15];
    u32 crit = mode_byte & 0x7F;
    bool desc = (mode_byte >> 7) != 0;

    void* base = work + 0x5C8;
    s16 count = *reinterpret_cast<s16*>(work + 0xDC8);

    if (crit == 1) {
        CompareFn cmp = desc ? StatusDown_SkillSortByIdDesc : StatusDown_SkillSortByIdAsc;
        qsort_002b7f0a(base, count, 4, cmp);
    } else if (crit == 0x21) {
        CompareFn cmp = desc ? StatusDown_SkillSortByNameDesc : StatusDown_SkillSortByNameAsc;
        qsort_002b7f0a(base, count, 4, cmp);
    } else if (crit == 3) {
        CompareFn cmp = desc ? StatusDown_SkillSortByCostDesc : StatusDown_SkillSortByCostAsc;
        qsort_002b7f0a(base, count, 4, cmp);
    }

    work[0x410] = 1;
}

extern "C" void h8_ui_statusdown_skilllist_mutation(const u8* skill_bitfield) {
    u8* work = static_cast<u8*>(g_StatusDownContext_0044e190);
    if (work) work[0x410] = 0;
}
''', encoding='utf-8')

# 7. StatusDown_Init (0x002D931C, 764 bytes)
statusdown_init_cpp = EXP_DIR / 'h8_ui_statusdown_init_candidate.cpp'
statusdown_init_cpp.write_text('''#include <cstdint>

typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void  UiSpriteGroup_Init_002c3344(void* group);
    void  UiSpriteGroup_BindTable_002c32f8(void* group, u32 a, u32 b, void* c, u32 d, void* e, u32 f, u32 g, void* h, u32 i);
    void  UiAnimSprite_SetupEx_002bdb2c(void* sprite, u32 id, int param, u32 index, void* group, u32 flag, float scale);
    void  UiAnimSprite_SetMode_002bdac0(void* sprite, u32 mode);
    void  UiAnimSprite_SetMode_002bf030(void* sprite, u32 mode);
    void* engine_func_002bda1c(void* sprite);
    void  engine_func_002bda10(void* ptr, u32 alpha);
    void  engine_func_002bda00(void* ptr, u32 a, u32 b, float scale);
    void  engine_func_002c4450(void* ptr, u32 a, int b);

    extern void* g_StatusDownContext_0044e190;
    extern u8    g_StatusDownSpriteTable_00407d58[];
}

extern "C" void h8_ui_statusdown_init_candidate() {
    u8* work = static_cast<u8*>(g_StatusDownContext_0044e190);
    if (!work) {
        work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 0x2394, 1));
        g_StatusDownContext_0044e190 = work;
    }
    AsdMem_Zero_002c4b30(work, 0x2394);

    void* calc_task = AsdTask_Create_002c5978("TMD CALC", 2, 0, 0, reinterpret_cast<void*>(0x001CA648), work, 0);
    *reinterpret_cast<void**>(work) = calc_task;

    AsdTask_CreateDraw_002c4c00("TMD DDRAW", 0x57, 0, 0, reinterpret_cast<void*>(0x001CC914), work, reinterpret_cast<u32>(calc_task));

    u8* group = work + 0x28;
    UiSpriteGroup_Init_002c3344(group);

    u8* table = g_StatusDownSpriteTable_00407d58;
    UiSpriteGroup_BindTable_002c32f8(group, 0, 0x50, table - 0xA0, 0x50, table - 0x50, 0, 0, table, 0x150);

    UiAnimSprite_SetupEx_002bdb2c(work + 0x48, 0x20, -1, 0, group, 1, 1.0f);
    UiAnimSprite_SetMode_002bdac0(work + 0x48, 0);

    UiAnimSprite_SetupEx_002bdb2c(work + 0xD4, 0x20, -1, 1, group, 1, 1.0f);
    UiAnimSprite_SetMode_002bf030(work + 0xD4, 0);

    void* spr = engine_func_002bda1c(work + 0x160);
    *reinterpret_cast<void**>(work + 0x22A0) = spr;
    engine_func_002bda10(spr, 0xFF);
    engine_func_002bda00(spr, 0, 0, 1.0f);

    engine_func_002c4450(work + 0x42C, 0x29, -1);
    work[0x2392] = 1;
}

extern "C" void h8_ui_statusdown_init_mutation() {
    g_StatusDownContext_0044e190 = reinterpret_cast<void*>(0xDEADBEEF);
}
''', encoding='utf-8')

# 8. GauntletAppMenu_Init (0x002E2454, 764 bytes)
gauntlet_cpp = EXP_DIR / 'h8_camp_gauntletmenu_init_candidate.cpp'
gauntlet_cpp.write_text('''#include <cstdint>

typedef uint32_t u32;
typedef uint8_t u8;

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  AsdMem_Zero_002c4b30(void* ptr, u32 size);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void  engine_func_002c0ba8(void* ptr, u32 id);
    void  engine_func_002488a8(void* ptr);
    void  engine_func_002976ac(void* ptr, const char* mbm, const char* bf);

    extern void* g_GauntletAppWork_0044e1a0;
}

extern "C" void h8_camp_gauntletmenu_init_candidate() {
    u8* work = static_cast<u8*>(g_GauntletAppWork_0044e1a0);
    if (!work) {
        work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x100, 0x122, 0, 0x1B8, 1));
        g_GauntletAppWork_0044e1a0 = work;
    }
    AsdMem_Zero_002c4b30(work, 0x1B8);

    void* calc_task = AsdTask_Create_002c5978("Gauntlet App CALC", 2, 0, 0, reinterpret_cast<void*>(0x00329410), work, 0);
    *reinterpret_cast<void**>(work) = calc_task;

    AsdTask_CreateDraw_002c4c00("Gauntlet App DDRAW", 0x57, 0, 0, reinterpret_cast<void*>(0x0032B070), work, reinterpret_cast<u32>(calc_task));

    engine_func_002c0ba8(work + 0x18, 0x521);
    engine_func_002c0ba8(work + 0x48, 0x526);
    engine_func_002c0ba8(work + 0x78, 0x527);
    engine_func_002c0ba8(work + 0xA8, 0x59F);

    engine_func_002488a8(work + 0xD8);
    engine_func_002976ac(work, "camp/gauntletApp.mbm", "camp/gauntletApp.bf");
}

extern "C" void h8_camp_gauntletmenu_init_mutation() {
    g_GauntletAppWork_0044e1a0 = reinterpret_cast<void*>(0xDEADBEEF);
}
''', encoding='utf-8')

candidates = [
    ('h8_ui_status_bustup', bustup_cpp, 'h8_ui_status_bustup_candidate', 248),
    ('h8_ui_status_camera', camera_cpp, 'h8_ui_status_camera_candidate', 480),
    ('h8_ui_status_affinity', affinity_cpp, 'h8_ui_status_affinity_candidate', 520),
    ('h8_ui_statusdown_itemsort', sortitem_cpp, 'h8_ui_statusdown_itemsort_candidate', 372),
    ('h8_ui_statusdown_itemlist', popitem_cpp, 'h8_ui_statusdown_itemlist_candidate', 384),
    ('h8_ui_statusdown_skilllist', popskill_cpp, 'h8_ui_statusdown_skilllist_candidate', 548),
    ('h8_ui_statusdown_init', statusdown_init_cpp, 'h8_ui_statusdown_init_candidate', 764),
    ('h8_camp_gauntletmenu_init', gauntlet_cpp, 'h8_camp_gauntletmenu_init_candidate', 764),
]

all_passed = True
print("=== Compiling all 8 Milestone H8 Candidates ===")
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
    print(f"[{status}] {name:<28} | Cand: {cand_sz:>4} B | Window: {win_sz:>4} B | Headroom: +{margin:>4} B | Relocs: {len(relocs)}")

if all_passed:
    print("ALL CANDIDATES COMPILED CLEANLY WITHIN ALLOCATED WINDOWS!")
else:
    sys.exit(1)
