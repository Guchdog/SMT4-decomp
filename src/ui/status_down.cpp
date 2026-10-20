#include "ui/status_down.h"
#include "engine/asd_symbols.h"
#include <cstring>

namespace smt4::ui {

StatusDownWork* g_StatusDownWork = nullptr; // 0x0044E190

struct ItemTableEntry {
    u16 id;          // +0x00
    u8  category;    // +0x02
    u8  rarity;      // +0x03
    u16 unk_04;      // +0x04
    u16 flags;       // +0x06 (bit 0: valid/usable)
    u8  unk_08[0x30];// +0x08..+0x38
    u16 skill_id;    // +0x38
};

struct SkillTableEntry {
    u8  unk_00[0x22];// +0x00..+0x22
    s16 cost_raw;    // +0x22
    u8  unk_24[0x0E];// +0x24..+0x32
    u16 sort_order;  // +0x32
};

struct UiLayoutRect {
    s16 w;           // +0x00
    s16 h;           // +0x02
};

struct UiLayoutNode {
    u8  unk_00[8];   // +0x00..+0x08
    s16 x;           // +0x08
    s16 y;           // +0x0A
    const UiLayoutRect* rect; // +0x0C
};

// External engine / AsdSDK / UI helper routines referenced by StatusDown.cpp
extern "C" {
    void* AsdMem_Alloc(u32 align, u32 line, u32 zero_flag, u32 size, u32 flag);     // 0x002c4b84
    void  AsdMem_Zero(void* ptr, u32 size);                                         // 0x002c4b30
    void  AsdMem_Copy(void* dst, const void* src, u32 size);                        // 0x002c5ff4
    void  AsdMem_FreeWork(void* ptr);                                               // 0x002c4360

    void* AsdTask_CreateCalc(const char* name, u32 prio, u32 a2, u32 a3,
                             void (*cb)(void*), u32 a5, u32 a6);                    // 0x002c5978
    void* AsdTask_CreateDraw(const char* name, u32 prio, u32 a2, u32 a3,
                             void (*cb)(void*), u32 a5, u32 a6, void* parent);      // 0x002c4c00
    void  AsdTask_DestroyPair(void* calc_task, u32 mode);                           // 0x002c45b8

    void* AsdText_CreateDefault(u32 arg0);                                          // 0x002bda1c
    void  AsdText_SetAlpha(void* text_handle, u32 alpha);                           // 0x002bda10
    void  AsdText_SetColorAndScale(void* text_handle, u32 a1, u32 rgba, f32 scale); // 0x002bda00
    void  AsdText_SetMessageSource(void* text_handle, u32 mode, s32 mask,
                                   u32 a3, u32 a4, const void* msg_data, s32 id);   // 0x00296d8c
    s32   AsdText_GetLineCount(void* text_handle);                                  // 0x002b787c
    void  AsdText_DestroyHandle(void* text_handle);                                 // 0x002a7b50

    void  UiSpriteGroup_Init(void* group);                                          // 0x002c3344
    void  UiSpriteGroup_BindTable(void* group, const void* t0, u32 s0,
                                  u32 s1, const void* t1, u32 s2,
                                  u32 a6, u32 a7, const void* t2, u32 s3);          // 0x002c32f8

    void  UiAnimSprite_Setup(UiAnimSprite* sprite, u32 res_group_id, s32 idx,
                             void* sprite_group, u32 flag, f32 scale);              // 0x002bdb2c
    void  UiAnimSprite_SetupEx(UiAnimSprite* sprite, u32 res_group_id, s32 idx,
                               u32 sub_id, void* sprite_group, u32 a5, f32 scale);  // 0x002bf0a8
    void  UiAnimSprite_SetAnim(UiAnimSprite* sprite, s32 anim_idx, s32 mode);       // 0x002bdac0
    void  UiAnimSprite_SetLayer(UiAnimSprite* sprite, s32 layer);                   // 0x002bf030
    s32   UiAnimSprite_GetPosX(const UiAnimSprite* sprite);                         // 0x002bef7c
    s32   UiAnimSprite_GetPosY(const UiAnimSprite* sprite);                         // 0x002bef70
    void  UiSprite_SetGlobalAlpha(f32 alpha);                                       // 0x002bf710
    void  UiSprite_DrawNode(u32 screen, u32 group_id, u32 node_id,
                            s32 x, s32 y, s32 prio);                                // 0x002bf460
    void  UiSprite_DrawPanel(u32 screen, u32 group_id, u32 panel_id,
                             s32 x, s32 y, s32 prio);                               // 0x002bf558
    void  UiScissor_SetRect(s32 x, s32 y, s32 w, s32 h, s32 enable);                // 0x0029a418
    void  UiFont_FormatString(char* dst, const char* fmt, ...);                     // 0x002be7fc
    void  UiFont_DrawText(u32 font_id, u32 rgba, const char* text,
                          f32 x, f32 y, f32 scale_x, f32 rot, f32 scale_y);         // 0x002be77c
    void  UiFont_DrawFormatted(u32 screen, s32 x, s32 y, s32 mode, s32 width,
                               s32 prio, const char* fmt, s32 val);                 // 0x002be16c
    void  UiSkill_DrawItemIconAndCount(s32 item_id, s32 x, s32 y, s32 prio, s32 a4);// 0x002b6a98
    void  UiSkill_DrawSkillCostAndInfo(u16 skill_id, s32 x, s32 y, s32 prio);       // 0x002e1e60
    void  UiParty_DrawDemonBars(s16 demon_id, s32 x, s32 y, s32 prio,
                                f32 scale, s32 a5);                                 // 0x002b6f74
    void  UiScrollBar_Draw(UiListCursor* cursor, s32 x, s32 y, u32 group_id,
                           s32 up_h, s32 down_h, u32 a6, u32 a7,
                           u32 a8, u32 a9, u32 a10, s32 btn_h,
                           s32 up_h2, s32 down_h2, s32 prio, s32 a15);              // 0x00290c38

    void  UiListCursor_Setup(UiListCursor* cursor, s32 total_items,
                             s32 visible_rows, s32 cols, s32 wrap_row, s32 repeat); // 0x0029fae8
    s32   UiListCursor_GetRowCount(const UiListCursor* cursor);                     // 0x0029f0f4
    s32   UiListCursor_GetSelectedRow(const UiListCursor* cursor);                  // 0x0029f248
    s32   UiListCursor_GetScrollOffset(const UiListCursor* cursor);                 // 0x0029f260
    void  UiListCursor_SetSelectedRow(UiListCursor* cursor, s32 row);               // 0x0029edfc
    void  UiListCursor_SetSelectedCol(UiListCursor* cursor, s32 col);               // 0x0029eb58
    void  UiListCursor_ResetScroll(UiListCursor* cursor, s32 pos);                  // 0x0020fe24

    s32   UiTouch_GetRegionTouchState(s16 handle);                                  // 0x0029d8fc
    s32   UiCursor_HandleInput(UiListCursor* cursor);                               // 0x0029e3bc
    bool  UiAnimSprite_UpdateCalc(UiAnimSprite* sprite, s32 mode);                  // 0x002b9220
    void  UiAnimSprite_StepAnimation(UiAnimSprite* sprite);                         // 0x002bf9f0

    s16   UiTouch_RegisterRegion(u32 group_id, u32 node_id);                        // 0x002b88c4
    s16   UiTouch_RegisterRectRegion(s32 x, s32 y, s32 w, s32 h);                   // 0x0029e2f4
    void  UiTouch_UnregisterLastRegion();                                           // 0x002b9008
    const UiLayoutNode* UiLayout_GetNode(u32 group_id, u32 node_id);                // 0x002bf6d0

    s32   Camp_GetTransitionDir();                                                  // 0x0029e2b0
    void  Camp_SetFadeColor(u32 screen, u32 rgba);                                  // 0x0029f10c
    s32   Camp_GetSubMenuState();                                                   // 0x00288408
    s32   Camp_GetMainMenuId();                                                     // 0x0029af30
    const u16* Camp_GetSelectedActorPtr();                                          // 0x0029af4c
    bool  Camp_IsActorPlayer(u16 actor_id);                                         // 0x0029ec6c
    bool  Camp_CanShowLRPrompts();                                                  // 0x00288700
    void  Sound_PlaySE(s32 se_id);                                                  // 0x002b8b78
    const void* Msg_GetCommonArchive(u32 archive_id);                               // 0x002b49d8
    const void* Msg_GetEntryFromBundle(const void* bundle, s32 msg_index);          // 0x00389294
    const ItemTableEntry* Item_GetTableEntry(u16 item_id);                          // 0x002b9364
    const SkillTableEntry* Skill_GetTableEntry(u16 skill_id);                       // 0x00257744
    s32   Skill_CalcNormalizedCost(s16 raw_cost);                                   // 0x00257678
    const char* Skill_GetNameString(u16 skill_id);                                  // 0x0026ad50
    s32   Party_GetDemonLevel(s32 demon_id);                                        // 0x0028d498
    s32   Party_GetDemonOrderNumber(s32 demon_id, s32 flag);                        // 0x0029ac70
    s32   Party_GetDemonActiveIndex(s32 demon_id);                                  // 0x0029abc0
    const u8* Party_GetDemonWorkPtr(s32 demon_id);                                  // 0x002ae3f0
    const u8* Camp_GetSortConfig();                                                 // 0x002a0fac
    bool  Flag_CheckEventBit(u32 flag_id);                                          // 0x002c0ba8
    bool  Category_IsUnlocked(u16 category_id);                                     // 0x00262edc
    bool  Category_HasItems(u32 category_id);                                       // 0x002890d0
    void  Camp_SetSubHeaderMode(u32 mode);                                          // 0x002a0ea8
    s32   Category_GetVisibleRowLimit();                                            // 0x0026ace0

    void  qsort_arm(void* base, s32 nmemb, u32 size,
                    s32 (*compar)(const void*, const void*));                       // 0x002b7f0a / 0x0027f3d4
    s32   SkillSort_ByNameDesc(const void*, const void*);                           // 0x002dca04
    s32   ItemSort_ByCountAsc(const void*, const void*);                            // 0x001d1bb8
    s32   ItemSort_ByCountDesc(const void*, const void*);                           // 0x002c6d30
    s32   ItemSort_ByNameAsc(const void*, const void*);                             // 0x001f61a4
    s32   ItemSort_ByNameDesc(const void*, const void*);                            // 0x002dca98

    extern const u8 g_StatusDownSpriteTable[];                                      // 0x00407d58
    extern u8* g_AsdGpuState;                                                       // 0x0044ea00
}

// DECOMP_FUNC(0x001ddab4, 68)
void StatusDown_OpenDefaultView() {
    StatusDownWork* work = g_StatusDownWork;
    UiAnimSprite_SetAnim(&work->panel_sprites[0], 1, 0);

    StatusDownWork* w = g_StatusDownWork;
    w->state_timer = 0;
    const u32 old_state = w->state;
    w->state = 1;
    w->prev_state = old_state;
    work->sub_state = 3;
}

// DECOMP_FUNC(0x001ee5a4, 548)
void StatusDown_PopulateSkillList(const u8* skill_bitfield) {
    StatusDownWork* work = g_StatusDownWork;
    work->skill_count = 0;
    work->skill_total = 0;
    AsdMem_Zero(work->skill_entries, sizeof(work->skill_entries));

    for (u16 i = 0; i < 0x500; ++i) {
        const ItemTableEntry* entry = Item_GetTableEntry(i);
        if (entry == nullptr) {
            continue;
        }
        if ((entry->flags & 1) == 0 || entry->skill_id == 0) {
            continue;
        }
        const u16 sid = entry->skill_id;
        if ((skill_bitfield[sid >> 3] & (1u << (sid & 7))) != 0) {
            const s16 idx = work->skill_count;
            work->skill_entries[idx].id = entry->id;
            work->skill_entries[idx].value = entry->skill_id;
            work->skill_count = static_cast<s16>(idx + 1);
        }
        work->skill_total = static_cast<s16>(work->skill_total + 1);
    }

    UiListCursor_Setup(&work->skill_cursor, work->skill_count, 11, 1, 0, 1);

    StatusDownWork* w = g_StatusDownWork;
    const u8* sort_cfg = Camp_GetSortConfig();
    const u8 skill_sort = sort_cfg[0x15];
    const u8 sort_key = skill_sort & 0x7F;
    const bool desc = (skill_sort >> 7) != 0;

    if (sort_key == 1) {
        qsort_arm(w->skill_entries, w->skill_count, sizeof(StatusDownListEntry),
                  desc ? StatusDown_SkillSortByIdDesc : StatusDown_SkillSortByIdAsc);
    }
    if ((sort_cfg[0x15] & 0x7F) == 0x21) {
        const bool d = (sort_cfg[0x15] >> 7) != 0;
        qsort_arm(w->skill_entries, w->skill_count, sizeof(StatusDownListEntry),
                  d ? StatusDown_SkillSortByCostDesc : StatusDown_SkillSortByCostAsc);
    }
    if ((sort_cfg[0x15] & 0x7F) == 3) {
        const bool d = (sort_cfg[0x15] >> 7) != 0;
        qsort_arm(w->skill_entries, w->skill_count, sizeof(StatusDownListEntry),
                  d ? SkillSort_ByNameDesc : StatusDown_SkillSortByNameAsc);
    }

    work->needs_refresh = 1;
}

// DECOMP_FUNC(0x001ee7c8, 384)
void StatusDown_PopulateItemList(const u8* item_counts) {
    StatusDownWork* work = g_StatusDownWork;
    work->item_count = 0;
    work->item_nonzero_count = 0;
    AsdMem_Zero(work->item_entries, sizeof(work->item_entries));

    for (u16 i = 0; i < 0x500; ++i) {
        const ItemTableEntry* entry = Item_GetTableEntry(i);
        if (entry == nullptr || (entry->flags & 1) == 0) {
            continue;
        }
        const u16 item_id = entry->id;
        const u8 qty = item_counts[item_id];
        if (qty == 0) {
            continue;
        }
        const s16 idx = work->item_count;
        work->item_entries[idx].id = item_id;
        work->item_entries[idx].value = qty;
        if (qty != 0) {
            work->item_nonzero_count = static_cast<s16>(work->item_nonzero_count + 1);
        }
        work->item_count = static_cast<s16>(idx + 1);
    }

    UiListCursor_Setup(&work->item_cursor, work->item_count, 9, 4, 1, 1);

    if (work->item_count > 0 &&
        work->item_count <= (work->item_saved_col + (work->item_saved_row << 2))) {
        const s16 new_row = static_cast<s16>((work->item_count - 1) / 4);
        const s16 new_col = static_cast<s16>((work->item_count - 1) - (new_row << 2));
        work->item_saved_row = new_row;
        work->item_saved_col = new_col;
        UiListCursor_SetSelectedRow(&work->item_cursor, new_row);
        UiListCursor_SetSelectedCol(&work->item_cursor, work->item_saved_col);
    } else {
        UiListCursor_SetSelectedRow(&work->item_cursor, work->item_saved_row);
        UiListCursor_SetSelectedCol(&work->item_cursor, work->item_saved_col);
    }

    StatusDown_SortItemList();
    work->needs_refresh = 1;
}

// DECOMP_FUNC(0x001f60dc, 152)
s32 StatusDown_SkillSortByCostAsc(const void* a, const void* b) {
    const auto* lhs = static_cast<const StatusDownListEntry*>(a);
    const auto* rhs = static_cast<const StatusDownListEntry*>(b);

    const SkillTableEntry* sk_a = Skill_GetTableEntry(lhs->value);
    const SkillTableEntry* sk_b = Skill_GetTableEntry(rhs->value);
    Item_GetTableEntry(lhs->id);
    Item_GetTableEntry(rhs->id);

    const s32 cost_a = Skill_CalcNormalizedCost(sk_a->cost_raw);
    const s32 cost_b = Skill_CalcNormalizedCost(sk_b->cost_raw);
    if (cost_a != cost_b) {
        return cost_a - cost_b;
    }

    const ItemTableEntry* it_a = Item_GetTableEntry(lhs->id);
    const ItemTableEntry* it_b = Item_GetTableEntry(rhs->id);
    if (it_a->category != it_b->category) {
        return static_cast<s32>(it_a->category) - static_cast<s32>(it_b->category);
    }
    if (it_b->rarity != it_a->rarity) {
        return static_cast<s32>(it_b->rarity) - static_cast<s32>(it_a->rarity);
    }
    return static_cast<s32>(it_a->id) - static_cast<s32>(it_b->id);
}

// DECOMP_FUNC(0x001f6174, 48)
s32 StatusDown_SkillSortByNameAsc(const void* a, const void* b) {
    const auto* lhs = static_cast<const StatusDownListEntry*>(a);
    const auto* rhs = static_cast<const StatusDownListEntry*>(b);

    const SkillTableEntry* sk_a = Skill_GetTableEntry(lhs->value);
    const SkillTableEntry* sk_b = Skill_GetTableEntry(rhs->value);
    return static_cast<s32>(sk_a->sort_order) - static_cast<s32>(sk_b->sort_order);
}

// DECOMP_FUNC(0x00206be8, 80)
s32 StatusDown_SkillSortByIdAsc(const void* a, const void* b) {
    const auto* lhs = static_cast<const StatusDownListEntry*>(a);
    const auto* rhs = static_cast<const StatusDownListEntry*>(b);

    const ItemTableEntry* it_a = Item_GetTableEntry(lhs->id);
    const ItemTableEntry* it_b = Item_GetTableEntry(rhs->id);
    if (it_a->category != it_b->category) {
        return static_cast<s32>(it_a->category) - static_cast<s32>(it_b->category);
    }
    if (it_b->rarity != it_a->rarity) {
        return static_cast<s32>(it_b->rarity) - static_cast<s32>(it_a->rarity);
    }
    return static_cast<s32>(it_a->id) - static_cast<s32>(it_b->id);
}

// DECOMP_FUNC(0x00206c38, 132)
s32 StatusDown_ItemSortByTypeAsc(const void* a, const void* b) {
    const auto* lhs = static_cast<const StatusDownListEntry*>(a);
    const auto* rhs = static_cast<const StatusDownListEntry*>(b);

    if (lhs->value == 0) {
        return (rhs->value != 0) ? 1 : 0;
    }
    if (rhs->value == 0) {
        return -1;
    }
    if (lhs->value != rhs->value) {
        return static_cast<s32>(lhs->value) - static_cast<s32>(rhs->value);
    }

    const ItemTableEntry* it_a = Item_GetTableEntry(lhs->id);
    const ItemTableEntry* it_b = Item_GetTableEntry(rhs->id);
    if (it_a->category != it_b->category) {
        return static_cast<s32>(it_a->category) - static_cast<s32>(it_b->category);
    }
    if (it_b->rarity != it_a->rarity) {
        return static_cast<s32>(it_b->rarity) - static_cast<s32>(it_a->rarity);
    }
    return static_cast<s32>(it_a->id) - static_cast<s32>(it_b->id);
}

// DECOMP_FUNC(0x00206cbc, 124)
s32 StatusDown_ItemSortByIdAsc(const void* a, const void* b) {
    const auto* lhs = static_cast<const StatusDownListEntry*>(a);
    const auto* rhs = static_cast<const StatusDownListEntry*>(b);

    if (lhs->value == 0) {
        return (rhs->value != 0) ? 1 : 0;
    }
    if (rhs->value == 0) {
        return -1;
    }

    const ItemTableEntry* it_a = Item_GetTableEntry(lhs->id);
    const ItemTableEntry* it_b = Item_GetTableEntry(rhs->id);
    if (it_a->category != it_b->category) {
        return static_cast<s32>(it_a->category) - static_cast<s32>(it_b->category);
    }
    if (it_b->rarity != it_a->rarity) {
        return static_cast<s32>(it_b->rarity) - static_cast<s32>(it_a->rarity);
    }
    return static_cast<s32>(it_a->id) - static_cast<s32>(it_b->id);
}

// DECOMP_FUNC(0x00215990, 180)
void StatusDown_SetPartyPrompt(const StatusDownPartyPrompt* prompt) {
    StatusDownWork* work = g_StatusDownWork;
    if (work->active_sound_id >= 0 && work->active_mode == 1) {
        const s32 menu_id = Camp_GetMainMenuId();
        const s32 se_id = (menu_id == 0xD || menu_id == 6) ? 0x2F : 0x1F;
        Sound_PlaySE(se_id);
    }

    work->active_sound_id = -1;
    work->prompt_field0 = prompt->field0;
    work->prompt_field1 = prompt->field1;
    work->prompt_field2 = prompt->field2;
    work->prompt_field3 = prompt->field3;

    UiListCursor_Setup(&work->list_cursor_prompt, 7, 7, 1, 0, 1);
    work->needs_refresh = 1;
}

// DECOMP_FUNC(0x00215a44, 28)
void StatusDown_SetActiveSoundId(s16 sound_id) {
    if (g_StatusDownWork != nullptr) {
        g_StatusDownWork->active_sound_id = sound_id;
    }
}

// DECOMP_FUNC(0x00215a68, 248)
void StatusDown_SetPartySlots(const u16* ids, s32 count) {
    StatusDownWork* work = g_StatusDownWork;
    std::memset(work->new_party_flags, 0, sizeof(work->new_party_flags));
    std::memset(work->party_ids, 0, sizeof(work->party_ids));
    AsdMem_Copy(work->party_ids, ids, static_cast<u32>(count << 1));

    s32 valid_count = 0;
    while (valid_count < count && work->party_ids[valid_count] != 0) {
        ++valid_count;
    }

    UiListCursor_Setup(&work->list_cursor_main, valid_count, 8, 1, 0, 1);
    work->needs_refresh = 1;
    work->flag_548 = 0;
}

// DECOMP_FUNC(0x00223b88, 40)
bool StatusDown_IsState20() {
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        return false;
    }
    return work->state == 20;
}

// DECOMP_FUNC(0x0026abe0, 84)
void StatusDown_SetSubIdsA(const u16* ids, s32 count) {
    if (count > 8) {
        return;
    }
    StatusDownWork* work = g_StatusDownWork;
    std::memset(work->sub_ids_a, 0, sizeof(work->sub_ids_a));
    if (count < 0) {
        work->has_sub_ids_a = 0;
        return;
    }
    work->has_sub_ids_a = 1;
    AsdMem_Copy(work->sub_ids_a, ids, static_cast<u32>(count << 1));
}

// DECOMP_FUNC(0x0026b01c, 176)
void StatusDown_PopFirstSubIdA() {
    StatusDownWork* work = g_StatusDownWork;
    const u16 first_a = work->sub_ids_a[0];
    for (s32 i = 0; i < 8; ++i) {
        if (work->sub_ids_b[i] != 0 && work->sub_ids_b[i] == first_a) {
            work->sub_ids_b[i] = 0;
        }
    }

    work->sub_ids_a[0] = 0;
    for (s32 pass = 0; pass < 7; ++pass) {
        const s32 limit = 7 - pass;
        for (s32 j = 0; j < limit; ++j) {
            const s32 idx = pass + j;
            if (work->sub_ids_a[idx] == 0 && work->sub_ids_a[idx + 1] != 0) {
                work->sub_ids_a[idx] = work->sub_ids_a[idx + 1];
                work->sub_ids_a[idx + 1] = 0;
            }
        }
    }
}

// DECOMP_FUNC(0x0026b0d0, 1636)
void StatusDown_SetupTouchRegions() {
    StatusDownWork* work = g_StatusDownWork;
    for (s32 i = 0; i < work->registered_touch_count; ++i) {
        UiTouch_UnregisterLastRegion();
    }
    work->registered_touch_count = 0;
    AsdMem_FillBytes(work->slot_touch_handles, 0x29, -1);

    switch (work->state) {
        case 3: {
            const s32 count = UiListCursor_GetRowCount(&work->list_cursor_main);
            for (s32 i = 0; i < count; ++i) {
                work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, static_cast<u32>(0x414 + i));
                ++work->registered_touch_count;
            }
            work->l_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50F);
            work->r_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50E);
            work->registered_touch_count = static_cast<s8>(work->registered_touch_count + 2);
            break;
        }
        case 4: {
            const s32 count = UiListCursor_GetRowCount(&work->list_cursor_main);
            for (s32 i = 0; i < count; ++i) {
                work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, static_cast<u32>(0x414 + i));
                ++work->registered_touch_count;
            }
            break;
        }
        case 6: {
            const s32 count = UiListCursor_GetRowCount(&work->list_cursor_main);
            for (s32 i = 0; i < count; ++i) {
                work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, static_cast<u32>(0x414 + i));
                ++work->registered_touch_count;
            }
            const s16 h = UiTouch_RegisterRegion(0x1A, 0x4F1);
            work->slot_touch_handles[work->registered_touch_count] = h;
            ++work->registered_touch_count;
            break;
        }
        case 11: {
            const s32 count = UiListCursor_GetRowCount(&work->list_cursor_main) - 1;
            for (s32 i = 0; i < count; ++i) {
                work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, static_cast<u32>(0x414 + i));
                ++work->registered_touch_count;
            }
            const UiLayoutNode* node_btn = UiLayout_GetNode(0x1A, 0x4F1);
            const UiLayoutNode* node_bg = UiLayout_GetNode(0x1A, 0x41F);
            const s16 h = UiTouch_RegisterRectRegion(node_btn->x, node_btn->y,
                                                     node_bg->rect->w, node_btn->rect->h);
            work->slot_touch_handles[work->registered_touch_count] = h;
            ++work->registered_touch_count;
            break;
        }
        case 16: {
            for (s32 i = 0; i < 7; ++i) {
                if (!Flag_CheckEventBit(0x410) && (i == 1 || i == 2)) {
                    work->slot_touch_handles[i] = 0;
                } else {
                    work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, static_cast<u32>(0x466 + i));
                }
                ++work->registered_touch_count;
            }
            work->l_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50F);
            work->r_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50E);
            work->registered_touch_count = static_cast<s8>(work->registered_touch_count + 2);
            break;
        }
        case 17: {
            for (s32 i = 0; i < 11; ++i) {
                work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, static_cast<u32>(0x44C + i));
                ++work->registered_touch_count;
            }
            work->scroll_up_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4E7);
            work->scroll_down_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4E8);
            work->btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4E9);
            work->registered_touch_count = static_cast<s8>(work->registered_touch_count + 3);
            work->l_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50F);
            work->r_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50E);
            work->registered_touch_count = static_cast<s8>(work->registered_touch_count + 2);
            break;
        }
        case 19: {
            for (s32 row = 0; row < 9; ++row) {
                for (s32 col = 0; col < 4; ++col) {
                    const s32 idx = col + (row << 2);
                    if (idx >= work->item_nonzero_count) {
                        break;
                    }
                    work->slot_touch_handles[idx] = UiTouch_RegisterRegion(0x1A, static_cast<u32>(0x4AE + idx));
                    ++work->registered_touch_count;
                }
            }
            work->scroll_up_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4E7);
            work->scroll_down_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4E8);
            work->btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4E9);
            work->registered_touch_count = static_cast<s8>(work->registered_touch_count + 3);
            work->l_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50F);
            work->r_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50E);
            work->registered_touch_count = static_cast<s8>(work->registered_touch_count + 2);
            break;
        }
        case 21: {
            work->scroll_up_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4EA);
            work->scroll_down_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4EB);
            work->btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4EC);
            work->registered_touch_count = static_cast<s8>(work->registered_touch_count + 3);
            work->l_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50F);
            work->r_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50E);
            work->registered_touch_count = static_cast<s8>(work->registered_touch_count + 2);
            break;
        }
        case 22:
        case 23:
        case 25:
        case 26: {
            const s32 count = UiListCursor_GetRowCount(&work->category_cursor) - 1;
            for (s32 i = 0; i < count; ++i) {
                work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, static_cast<u32>(0x414 + i));
                ++work->registered_touch_count;
            }
            const s16 back_handle = UiTouch_RegisterRegion(0x1A, 0x54A);
            const s32 total_rows = UiListCursor_GetRowCount(&work->category_cursor);
            work->slot_touch_handles[total_rows - 1] = back_handle;
            ++work->registered_touch_count;
            break;
        }
        default:
            break;
    }
}

// DECOMP_FUNC(0x0026d8c0, 28)
void StatusDown_SetVisibility(u8 visible) {
    if (g_StatusDownWork != nullptr) {
        g_StatusDownWork->visibility_flag = visible;
    }
}

// DECOMP_FUNC(0x00288718, 92)
bool StatusDown_CanOpenSubScreen() {
    if (Camp_GetSubMenuState() == 5 || Camp_GetSubMenuState() == 6 || Camp_GetSubMenuState() == 10) {
        return false;
    }
    if (Camp_GetMainMenuId() == 7 || Camp_GetMainMenuId() == 8 || Camp_GetMainMenuId() == 3) {
        return false;
    }
    return true;
}

// DECOMP_FUNC(0x0028cd5c, 28)
u32 StatusDown_GetField2384() {
    if (g_StatusDownWork != nullptr) {
        return g_StatusDownWork->field_2384;
    }
    return 0;
}

// DECOMP_FUNC(0x0028cd78, 36)
bool StatusDown_IsInactiveOrState0() {
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        return true;
    }
    return work->state == 0;
}

// DECOMP_FUNC(0x00292f44, 304)
void StatusDown_SetDisplayMode(s32 mode) {
    StatusDownWork* work = g_StatusDownWork;
    if (work->active_mode == mode) {
        return;
    }

    work->prev_active_mode = work->active_mode;
    work->active_mode = static_cast<u8>(mode);

    if (Camp_GetTransitionDir() < 0) {
        UiAnimSprite_SetAnim(&work->panel_sprites[0], 3, 0);
    } else if (Camp_GetTransitionDir() > 0) {
        UiAnimSprite_SetAnim(&work->panel_sprites[0], 2, 0);
    }

    StatusDownWork* w = g_StatusDownWork;
    for (s32 i = 0; i < w->registered_touch_count; ++i) {
        UiTouch_UnregisterLastRegion();
    }
    w->registered_touch_count = 0;
    AsdMem_FillBytes(w->slot_touch_handles, 0x29, -1);

    StatusDownWork* w2 = g_StatusDownWork;
    w2->state_timer = 0;
    const u32 old_state = w2->state;
    w2->state = 2;
    w2->prev_state = old_state;

    switch (mode) {
        case 0:
            work->sub_state = 0;
            break;
        case 1:
            work->sub_state = 3;
            break;
        case 2:
            work->sub_state = 0x10;
            break;
        case 3:
            work->sub_state = 0x11;
            break;
        case 4:
            work->sub_state = 0x13;
            break;
        case 5:
            work->sub_state = 0x15;
            break;
        default:
            break;
    }

    Camp_SetFadeColor(0, 0x323232FFu);
}

// DECOMP_FUNC(0x00293d2c, 36)
bool StatusDown_IsNotTransitioning() {
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        return true;
    }
    return work->state != 16;
}

// DECOMP_FUNC(0x00293d50, 20)
u8 StatusDown_GetActiveMode() {
    return g_StatusDownWork->active_mode;
}

// DECOMP_FUNC(0x00293e30, 28)
s8 StatusDown_GetStatusMode() {
    if (g_StatusDownWork != nullptr) {
        return g_StatusDownWork->status_mode;
    }
    return 0;
}

// DECOMP_FUNC(0x002956ac, 20)
u32 StatusDown_GetField53C() {
    return g_StatusDownWork->field_53c;
}

// DECOMP_FUNC(0x0029a520, 1696)
void StatusDown_DrawPartySlotRow(s32 x_offset, s32 y_offset, s32 demon_id,
                                 u32 node_id, f32 scale, s32 is_stock_row,
                                 s32 is_empty_mode, s32 highlight_mode) {
    StatusDownWork* work = g_StatusDownWork;
    const UiLayoutNode* row_node = UiLayout_GetNode(0x1A, node_id);
    const s32 selected_row = UiListCursor_GetSelectedRow(&work->list_cursor_main);

    const f32 pulse_alpha = *reinterpret_cast<const f32*>(&work->panel_sprites[1].raw[0x20]);
    UiSprite_SetGlobalAlpha(pulse_alpha);
    UiSprite_DrawPanel(2, 0x1A, 8, x_offset + row_node->x, y_offset + row_node->y, 0xBF);

    UiSprite_SetGlobalAlpha(1.0f);
    UiSprite_DrawNode(2, 0x1A, 0x41F, x_offset + row_node->x, y_offset + row_node->y, 0xC4);

    u32 cursor_frame_node = 0x420;
    if (work->touch_drag_state[0] == 0 && work->touch_drag_state[1] == 0 &&
        work->touch_drag_state[2] == 0 && work->lr_state_left == 0 &&
        work->lr_state_right == 0 && work->touch_hold_state >= 0) {
        cursor_frame_node = 0x421;
    }
    UiSprite_DrawNode(2, 0x1A, cursor_frame_node, x_offset + row_node->x, y_offset + row_node->y, 0xC4);

    const UiLayoutNode* clip_node = UiLayout_GetNode(0x1A, 0x420);
    UiScissor_SetRect(x_offset + row_node->x + clip_node->x,
                      y_offset + row_node->y + clip_node->y,
                      clip_node->rect->w, clip_node->rect->h, 1);

    const s32 anim_y = UiAnimSprite_GetPosY(&work->panel_sprites[3]);
    const s32 anim_x = UiAnimSprite_GetPosX(&work->panel_sprites[3]);
    UiSprite_DrawNode(2, 0x1A, 0x422,
                      x_offset + anim_x + row_node->x,
                      y_offset + anim_y + row_node->y, 0xC9);

    u32 text_color = 0xFFFFFFFFu;
    if (highlight_mode == 1) {
        text_color = 0x72E027FFu;
    } else if (highlight_mode == 2) {
        text_color = 0xDC0F14FFu;
    }

    if (work->state == 11 || work->state == 14) {
        if (work->selected_result == selected_row) {
            text_color = 0x72E027FFu;
        }
    } else if (work->state != 6 && work->state != 9) {
        if (work->flag_548 != 0 && work->highlighted_slot_index == selected_row) {
            text_color = 0x72E027FFu;
        }
    }

    const UiLayoutNode* name_node = UiLayout_GetNode(0x1A, 0x42B);
    char name_buf[64]{};
    UiFont_FormatString(name_buf, "%s", "");
    UiFont_DrawText(3, text_color, name_buf,
                    static_cast<f32>(x_offset + row_node->x + name_node->x),
                    static_cast<f32>(y_offset + row_node->y + name_node->y),
                    0.2f, 0.0f, 1.0f);

    if (is_empty_mode == 0 || demon_id != 0) {
        UiSprite_DrawNode(2, 0x1A, 0x425, x_offset + row_node->x, y_offset + row_node->y, 0xC4);
        const UiLayoutNode* bar_node = UiLayout_GetNode(0x1A, 0x42A);
        UiParty_DrawDemonBars(static_cast<s16>(demon_id),
                              x_offset + row_node->x + bar_node->x,
                              y_offset + row_node->y + bar_node->y,
                              0xC9, scale, 0);
    }

    if (is_stock_row != 0) {
        return;
    }

    if (is_empty_mode != 0) {
        UiSprite_DrawNode(2, 0x1A, 0x522, x_offset + row_node->x, y_offset + row_node->y, 0xC4);
        const UiLayoutNode* lv_node = UiLayout_GetNode(0x1A, 0x52A);
        if (demon_id != 0) {
            const s32 lv = Party_GetDemonLevel(demon_id);
            UiFont_DrawFormatted(0, x_offset + row_node->x + lv_node->x,
                                 y_offset + row_node->y + lv_node->y,
                                 1, 8, 0xC9, "%d", lv);
        } else {
            char empty_lv[64]{};
            UiFont_FormatString(empty_lv, "---");
            UiFont_DrawFormatted(0, x_offset + row_node->x + lv_node->x,
                                 y_offset + row_node->y + lv_node->y,
                                 1, 8, 0xC9, "%s", reinterpret_cast<s32>(empty_lv));
        }
        return;
    }

    UiSprite_DrawNode(2, 0x1A, 0x423, x_offset + row_node->x, y_offset + row_node->y, 0xC4);
    s32 order_num = 0;
    if (work->active_sound_id < 0) {
        order_num = Party_GetDemonOrderNumber(demon_id, 1);
    } else if (Camp_GetMainMenuId() == 6) {
        const u8* dwork = Party_GetDemonWorkPtr(demon_id);
        if (dwork != nullptr) {
            order_num = dwork[0x22];
        }
    } else {
        order_num = Party_GetDemonActiveIndex(demon_id);
    }

    const UiLayoutNode* ord_node = UiLayout_GetNode(0x1A, 0x429);
    UiFont_DrawFormatted(0, x_offset + row_node->x + ord_node->x,
                         y_offset + row_node->y + ord_node->y,
                         1, 4, 0xC9, "%d", order_num);
}

// DECOMP_FUNC(0x0029adf0, 320)
void StatusDown_DrawLRPrompts(s32 x_offset, s32 y_offset) {
    StatusDownWork* work = g_StatusDownWork;
    if (!Camp_CanShowLRPrompts()) {
        return;
    }

    if (work->lr_state_left == 1 || work->lr_state_left == 2) {
        UiSprite_DrawNode(2, 0x1A, 0x4D5, x_offset, y_offset, 0xBA);
        UiSprite_DrawNode(2, 0x1A, 0x4D9, x_offset, y_offset, 0xBA);
    } else {
        UiSprite_DrawNode(2, 0x1A, 0x4D3, x_offset, y_offset, 0xBA);
        UiSprite_DrawNode(2, 0x1A, 0x4D7, x_offset, y_offset, 0xBA);
    }

    if (work->lr_state_right == 1 || work->lr_state_right == 2) {
        UiSprite_DrawNode(2, 0x1A, 0x4D4, x_offset, y_offset, 0xBA);
        UiSprite_DrawNode(2, 0x1A, 0x4D8, x_offset, y_offset, 0xBA);
    } else {
        UiSprite_DrawNode(2, 0x1A, 0x4D2, x_offset, y_offset, 0xBA);
        UiSprite_DrawNode(2, 0x1A, 0x4D6, x_offset, y_offset, 0xBA);
    }
}

// DECOMP_FUNC(0x0029bfec, 152)
void StatusDown_Close() {
    StatusDownWork* work = g_StatusDownWork;
    if (work->state == 0) {
        return;
    }

    UiAnimSprite_SetAnim(&work->panel_sprites[0], 2, 0);

    StatusDownWork* w = g_StatusDownWork;
    w->state_timer = 0;
    const u32 old_state = w->state;
    w->state = 2;
    w->prev_state = old_state;
    work->sub_state = 0;
    work->active_mode = 0;

    for (s32 i = 0; i < w->registered_touch_count; ++i) {
        UiTouch_UnregisterLastRegion();
    }
    w->registered_touch_count = 0;
    AsdMem_FillBytes(w->slot_touch_handles, 0x29, -1);
}

// DECOMP_FUNC(0x0029c6c4, 24)
void StatusDown_SetFlag412(u8 val) {
    if (g_StatusDownWork != nullptr) {
        g_StatusDownWork->flag_412 = val;
    }
}

// DECOMP_FUNC(0x0029c70c, 32)
bool StatusDown_IsNotState1() {
    return g_StatusDownWork->state != 1;
}

// DECOMP_FUNC(0x0029c72c, 32)
bool StatusDown_IsNotState2() {
    return g_StatusDownWork->state != 2;
}

// DECOMP_FUNC(0x002cf4e0, 352)
void StatusDown_UpdateHelpMessage(s32 msg_index) {
    StatusDownWork* work = g_StatusDownWork;
    if (work->active_sound_id < 0 && msg_index >= 0 && work->active_mode == 1) {
        const s32 menu_id = Camp_GetMainMenuId();
        s32 se_id = 0x2B;
        if (menu_id == 0xD || menu_id == 6) {
            se_id = 0x31;
        } else if (menu_id == 8 || menu_id == 9 || menu_id == 0xB || menu_id == 7) {
            se_id = 0x60;
        } else if (menu_id == 2) {
            se_id = 0x27;
        }
        Sound_PlaySE(se_id);
    }

    work->active_sound_id = static_cast<s16>(msg_index);
    if (msg_index < 0) {
        const void* common_arc = Msg_GetCommonArchive(0x40);
        AsdText_SetMessageSource(work->text_handle, 3, -1, 0, 3, common_arc, 0);
    } else {
        const void* entry = Msg_GetEntryFromBundle(g_CampMessageBundle, msg_index);
        if (entry == nullptr) {
            entry = Msg_GetCommonArchive(0x40);
        }
        AsdText_SetMessageSource(work->text_handle, 3, -1, 0, 3, entry, msg_index);
    }

    const s32 line_count = AsdText_GetLineCount(work->text_handle);
    UiListCursor_Setup(&work->list_cursor_help, line_count, 8, 1, 0, 1);
    UiListCursor_ResetScroll(&work->list_cursor_help, 0);
    work->needs_refresh = 1;
}

// DECOMP_FUNC(0x002d931c, 764)
void StatusDown_Init() {
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        work = static_cast<StatusDownWork*>(
            AsdMem_Alloc(0x100, 0xD1D, 0, sizeof(StatusDownWork), 1));
        g_StatusDownWork = work;
    }

    AsdMem_Zero(work, sizeof(StatusDownWork));

    work->calc_task = AsdTask_CreateCalc("TMD CALC", 2, 0, 0,
                                         StatusDown_CalcTaskCallback, 0, 0);
    work->draw_task = AsdTask_CreateDraw("TMD DDRAW", 0xE7, 0, 0,
                                         StatusDown_DrawTaskCallback, 0, 0, work->calc_task);

    StatusDownWork* w = g_StatusDownWork;
    UiSpriteGroup_Init(&w->sprite_group);
    UiSpriteGroup_BindTable(&w->sprite_group,
                            g_StatusDownSpriteTable - 0xA8, 0x48,
                            0x48, g_StatusDownSpriteTable - 0x18, 0x18,
                            0, 0, g_StatusDownSpriteTable, 0x134);

    UiAnimSprite_Setup(&w->panel_sprites[0], 0x1A, 0x3E8, &w->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&w->panel_sprites[0], 0, 0);

    UiAnimSprite_Setup(&w->panel_sprites[1], 0x1A, 0x3E8, &w->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&w->panel_sprites[1], 0, 0);
    UiAnimSprite_SetLayer(&w->panel_sprites[1], 1);

    UiAnimSprite_Setup(&w->panel_sprites[2], 0x1A, 0x3E8, &w->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&w->panel_sprites[2], 0, 0);
    UiAnimSprite_SetLayer(&w->panel_sprites[2], 1);

    UiAnimSprite_Setup(&w->panel_sprites[3], 0x1A, 0x3E8, &w->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&w->panel_sprites[3], 4, 0);

    UiAnimSprite_Setup(&w->panel_sprites[4], 0x1A, 0x3E8, &w->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&w->panel_sprites[4], 5, 0);

    UiAnimSprite_Setup(&w->panel_sprites[5], 0x1A, 0x3E8, &w->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&w->panel_sprites[5], 0, 0);

    UiAnimSprite_SetupEx(&w->panel_sprites[6], 0x1A, -1, 0x1C, &w->sprite_group, 0xC9, 1.0f);
    UiAnimSprite_SetLayer(&w->panel_sprites[6], 2);
    *reinterpret_cast<u16*>(&w->panel_sprites[6].raw[0x3A]) = 2;

    w->text_handle = AsdText_CreateDefault(0);
    AsdText_SetAlpha(w->text_handle, 0xFF);
    AsdText_SetColorAndScale(w->text_handle, 0, 0x646464FFu, 0.0f);

    AsdMem_FillBytes(w->slot_touch_handles, 0x29, -1);
    w->visibility_flag = 1;
}

// DECOMP_FUNC(0x002d9618, 36)
void StatusDown_EnterState3_Alt() {
    StatusDownWork* work = g_StatusDownWork;
    if (work != nullptr) {
        const u32 prev = work->state;
        work->state = 3;
        work->prev_state = prev;
        work->sub_state = 0;
        work->state_timer = 0;
    }
}

// DECOMP_FUNC(0x002dc96c, 152)
s32 StatusDown_SkillSortByCostDesc(const void* a, const void* b) {
    const auto* lhs = static_cast<const StatusDownListEntry*>(a);
    const auto* rhs = static_cast<const StatusDownListEntry*>(b);

    const SkillTableEntry* sk_a = Skill_GetTableEntry(lhs->value);
    const SkillTableEntry* sk_b = Skill_GetTableEntry(rhs->value);
    Item_GetTableEntry(lhs->id);
    Item_GetTableEntry(rhs->id);

    const s32 cost_b = Skill_CalcNormalizedCost(sk_b->cost_raw);
    const s32 cost_a = Skill_CalcNormalizedCost(sk_a->cost_raw);
    if (cost_b != cost_a) {
        return cost_b - cost_a;
    }

    const ItemTableEntry* it_a = Item_GetTableEntry(lhs->id);
    const ItemTableEntry* it_b = Item_GetTableEntry(rhs->id);
    if (it_b->category != it_a->category) {
        return static_cast<s32>(it_b->category) - static_cast<s32>(it_a->category);
    }
    if (it_b->rarity != it_a->rarity) {
        return static_cast<s32>(it_b->rarity) - static_cast<s32>(it_a->rarity);
    }
    return static_cast<s32>(it_a->id) - static_cast<s32>(it_b->id);
}

// DECOMP_FUNC(0x002e2f44, 408)
void StatusDown_UpdatePartySlotsAndDiff(const u16* ids, s32 count) {
    StatusDownWork* work = g_StatusDownWork;
    u16 prev_ids[8];
    std::memcpy(prev_ids, work->party_ids, sizeof(prev_ids));
    std::memset(work->new_party_flags, 0, sizeof(work->new_party_flags));
    std::memset(work->party_ids, 0, sizeof(work->party_ids));
    AsdMem_Copy(work->party_ids, ids, static_cast<u32>(count << 1));

    s32 valid_count = 0;
    while (valid_count < count && work->party_ids[valid_count] != 0) {
        ++valid_count;
    }

    UiListCursor_Setup(&work->list_cursor_main, valid_count, 8, 1, 0, 1);
    work->needs_refresh = 1;
    work->flag_548 = 0;

    for (s32 i = 0; i < count; ++i) {
        const u16 cur_id = work->party_ids[i];
        if (cur_id == 0) {
            continue;
        }
        s32 j = 0;
        for (; j < 8; ++j) {
            if (prev_ids[j] != 0 && prev_ids[j] == cur_id) {
                break;
            }
        }
        if (j >= 8) {
            work->new_party_flags[i] = 1;
        }
    }
}

// DECOMP_FUNC(0x002e4534, 80)
s32 StatusDown_SkillSortByIdDesc(const void* a, const void* b) {
    const auto* lhs = static_cast<const StatusDownListEntry*>(a);
    const auto* rhs = static_cast<const StatusDownListEntry*>(b);

    const ItemTableEntry* it_a = Item_GetTableEntry(lhs->id);
    const ItemTableEntry* it_b = Item_GetTableEntry(rhs->id);
    if (it_b->category != it_a->category) {
        return static_cast<s32>(it_b->category) - static_cast<s32>(it_a->category);
    }
    if (it_b->rarity != it_a->rarity) {
        return static_cast<s32>(it_b->rarity) - static_cast<s32>(it_a->rarity);
    }
    return static_cast<s32>(it_a->id) - static_cast<s32>(it_b->id);
}

// DECOMP_FUNC(0x002e4584, 132)
s32 StatusDown_ItemSortByTypeDesc(const void* a, const void* b) {
    const auto* lhs = static_cast<const StatusDownListEntry*>(a);
    const auto* rhs = static_cast<const StatusDownListEntry*>(b);

    if (lhs->value == 0) {
        return (rhs->value != 0) ? 1 : 0;
    }
    if (rhs->value == 0) {
        return -1;
    }
    if (rhs->value != lhs->value) {
        return static_cast<s32>(rhs->value) - static_cast<s32>(lhs->value);
    }

    const ItemTableEntry* it_a = Item_GetTableEntry(lhs->id);
    const ItemTableEntry* it_b = Item_GetTableEntry(rhs->id);
    if (it_b->category != it_a->category) {
        return static_cast<s32>(it_b->category) - static_cast<s32>(it_a->category);
    }
    if (it_a->rarity != it_b->rarity) {
        return static_cast<s32>(it_a->rarity) - static_cast<s32>(it_b->rarity);
    }
    return static_cast<s32>(it_b->id) - static_cast<s32>(it_a->id);
}

// DECOMP_FUNC(0x002e4608, 124)
s32 StatusDown_ItemSortByIdDesc(const void* a, const void* b) {
    const auto* lhs = static_cast<const StatusDownListEntry*>(a);
    const auto* rhs = static_cast<const StatusDownListEntry*>(b);

    if (lhs->value == 0) {
        return (rhs->value != 0) ? 1 : 0;
    }
    if (rhs->value == 0) {
        return -1;
    }

    const ItemTableEntry* it_a = Item_GetTableEntry(lhs->id);
    const ItemTableEntry* it_b = Item_GetTableEntry(rhs->id);
    if (it_b->category != it_a->category) {
        return static_cast<s32>(it_b->category) - static_cast<s32>(it_a->category);
    }
    if (it_a->rarity != it_b->rarity) {
        return static_cast<s32>(it_a->rarity) - static_cast<s32>(it_b->rarity);
    }
    return static_cast<s32>(it_b->id) - static_cast<s32>(it_a->id);
}

// DECOMP_FUNC(0x002efde0, 44)
s32 StatusDown_GetPartyMaxIndex() {
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        return 0;
    }
    return UiListCursor_GetRowCount(&work->list_cursor_main) - 1;
}

// DECOMP_FUNC(0x002efe0c, 32)
bool StatusDown_IsNotState4() {
    return g_StatusDownWork->state != 4;
}

// DECOMP_FUNC(0x002efe2c, 28)
s8 StatusDown_GetField2388() {
    if (g_StatusDownWork != nullptr) {
        return g_StatusDownWork->field_2388;
    }
    return 0;
}

// DECOMP_FUNC(0x002efe48, 68)
void StatusDown_SetSubIdsB(const u16* ids, s32 count) {
    if (count > 8) {
        return;
    }
    StatusDownWork* work = g_StatusDownWork;
    std::memset(work->sub_ids_b, 0, sizeof(work->sub_ids_b));
    AsdMem_Copy(work->sub_ids_b, ids, static_cast<u32>(count << 1));
}

// DECOMP_FUNC(0x002efe8c, 24)
void StatusDown_SetFlag411(u8 val) {
    if (g_StatusDownWork != nullptr) {
        g_StatusDownWork->flag_411 = val;
    }
}

// DECOMP_FUNC(0x002efea4, 36)
void StatusDown_EnterState4() {
    StatusDownWork* work = g_StatusDownWork;
    if (work != nullptr) {
        const u32 prev = work->state;
        work->state = 4;
        work->prev_state = prev;
        work->sub_state = 0;
        work->state_timer = 0;
    }
}

// DECOMP_FUNC(0x002f6524, 44)
bool StatusDown_IsState7() {
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        return false;
    }
    return work->state == 7;
}

// DECOMP_FUNC(0x002f6550, 132)
void StatusDown_Destroy() {
    StatusDownWork* work = g_StatusDownWork;
    for (s32 i = 0; i < work->registered_touch_count; ++i) {
        UiTouch_UnregisterLastRegion();
    }
    work->registered_touch_count = 0;
    AsdMem_FillBytes(work->slot_touch_handles, 0x29, -1);

    AsdText_DestroyHandle(work->text_handle);
    AsdTask_DestroyPair(work->calc_task, 0);
    AsdMem_FreeWork(work);
    g_StatusDownWork = nullptr;
}

// DECOMP_FUNC(0x002f65d4, 76)
bool StatusDown_IsCursorAtLastPartySlot() {
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        return false;
    }
    const s32 selected = UiListCursor_GetSelectedRow(&work->list_cursor_main);
    const s32 count = UiListCursor_GetRowCount(&work->list_cursor_main);
    return selected == (count - 1);
}

// DECOMP_FUNC(0x002f6620, 200)
void StatusDown_SelectLastPartySlotAndEnterState11(s32 result_val, u32 arg1) {
    StatusDownWork* work = g_StatusDownWork;
    work->selected_result = result_val;
    work->callback_arg1 = arg1;

    const s32 old_count = UiListCursor_GetRowCount(&work->list_cursor_main);
    UiListCursor_Setup(&work->list_cursor_main, old_count + 1, 9, 1, 0, 1);

    const s32 new_count = UiListCursor_GetRowCount(&work->list_cursor_main);
    UiListCursor_SetSelectedRow(&work->list_cursor_main, new_count - 1);
    work->needs_refresh = 1;

    StatusDownWork* w = g_StatusDownWork;
    for (s32 i = 0; i < w->registered_touch_count; ++i) {
        UiTouch_UnregisterLastRegion();
    }
    w->registered_touch_count = 0;
    AsdMem_FillBytes(w->slot_touch_handles, 0x29, -1);

    StatusDownWork* w2 = g_StatusDownWork;
    w2->state_timer = 0;
    const u32 prev = w2->state;
    w2->state = 11;
    w2->prev_state = prev;

    StatusDown_SetupTouchRegions();
}

// DECOMP_FUNC(0x002f66e8, 36)
void StatusDown_EnterState3() {
    StatusDownWork* work = g_StatusDownWork;
    if (work != nullptr) {
        const u32 prev = work->state;
        work->state = 3;
        work->prev_state = prev;
        work->sub_state = 0;
        work->state_timer = 0;
    }
}

// DECOMP_FUNC(0x0030aa98, 40)
void StatusDown_EnterState6_Simple() {
    StatusDownWork* work = g_StatusDownWork;
    if (work != nullptr) {
        const u32 prev = work->state;
        work->state = 6;
        work->prev_state = prev;
        work->sub_state = 0;
        work->state_timer = 0;
    }
}

// DECOMP_FUNC(0x0030aac0, 32)
bool StatusDown_IsState15() {
    return g_StatusDownWork->state == 15;
}

// DECOMP_FUNC(0x0030aae0, 32)
bool StatusDown_IsState10() {
    return g_StatusDownWork->state == 10;
}

// DECOMP_FUNC(0x0030ab00, 52)
void StatusDown_EnterState14(s32 selected_result) {
    StatusDownWork* work = g_StatusDownWork;
    if (work != nullptr) {
        const u32 prev = work->state;
        work->state = 14;
        work->prev_state = prev;
        work->sub_state = 0;
        work->state_timer = 0;
        work->selected_result = selected_result;
    }
}

// DECOMP_FUNC(0x0030ab34, 60)
void StatusDown_EnterState6() {
    StatusDownWork* work = g_StatusDownWork;
    if (work != nullptr) {
        const u32 prev = work->state;
        work->state = 6;
        work->prev_state = prev;
        work->sub_state = 0;
        work->state_timer = 0;
        work->selected_result = -1;
        work->request_close_flag = 0;
    }
}

// DECOMP_FUNC(0x00311494, 356)
void StatusDown_OpenCategorySelect(u16 arg0, u8 flag_413) {
    StatusDownWork* work = g_StatusDownWork;
    work->category_arg0 = arg0;
    work->flag_413 = flag_413;
    std::memset(work->category_ids, 0, sizeof(work->category_ids));

    s32 matched_count = 0;
    for (u32 id = 0x79F; id <= 0x802; ++id) {
        if (id == 0) {
            id = 1;
        }
        if (Category_IsUnlocked(static_cast<u16>(id)) && Category_HasItems(id)) {
            work->category_ids[matched_count++] = static_cast<u16>(id);
        }
    }

    Camp_SetSubHeaderMode(0xE);
    Sound_PlaySE(5);
    UiAnimSprite_SetAnim(&work->panel_sprites[0], 1, 0);

    if (Category_GetVisibleRowLimit() <= matched_count) {
        const s32 rows = Category_GetVisibleRowLimit() + 1;
        UiListCursor_Setup(&work->category_cursor, rows, 9, 1, 1, 1);
        work->sub_state = 0x19;
    } else {
        const s32 rows = Category_GetVisibleRowLimit();
        UiListCursor_Setup(&work->category_cursor, rows, 9, 1, 1, 1);
        UiListCursor_SetSelectedRow(&work->category_cursor, matched_count);
        work->sub_state = 0x16;
    }

    StatusDownWork* w = g_StatusDownWork;
    w->state_timer = 0;
    const u32 old_state = w->state;
    w->state = 1;
    w->prev_state = old_state;
}

// DECOMP_FUNC(0x00317f80, 36)
void StatusDown_RequestClose() {
    StatusDownWork* work = g_StatusDownWork;
    if (work != nullptr && work->state != 0) {
        work->request_close_flag = 1;
    }
}

// DECOMP_FUNC(0x0032303c, 40)
s32 StatusDown_GetSelectedPartyIndex() {
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        return -1;
    }
    return UiListCursor_GetSelectedRow(&work->list_cursor_main);
}

// DECOMP_FUNC(0x0032be34, 1672)
void StatusDown_DrawSkillList(s32 x_offset, s32 y_offset) {
    StatusDownWork* work = g_StatusDownWork;
    UiListCursor* cursor = &work->skill_cursor;
    const s32 scroll_offset = UiListCursor_GetScrollOffset(cursor);
    const s32 selected_row = UiListCursor_GetSelectedRow(cursor);

    bool hide_names = false;
    const s32 menu_id = Camp_GetMainMenuId();
    if (menu_id == 0xD) {
        hide_names = true;
    } else if (menu_id == 6) {
        const u16* actor_ptr = Camp_GetSelectedActorPtr();
        if (!Camp_IsActorPlayer(*actor_ptr)) {
            hide_names = true;
        }
    }

    UiSprite_DrawPanel(2, 0x1A, 5, x_offset, y_offset, 0xB3);
    UiSprite_DrawPanel(2, 0x1A, 0xB, x_offset, y_offset, 0xB5);
    StatusDown_DrawLRPrompts(x_offset, y_offset);

    for (s32 row = 0; row < 11; ++row) {
        const StatusDownListEntry& entry = work->skill_entries[scroll_offset + row];
        if (entry.value == 0) {
            continue;
        }

        const UiLayoutNode* row_node = UiLayout_GetNode(0x1A, static_cast<u32>(0x44C + row));
        const UiLayoutNode* name_node = UiLayout_GetNode(0x1A, 0x44B);

        if (hide_names) {
            char buf[64]{};
            UiFont_FormatString(buf, "???");
            UiFont_DrawText(2, 0xFF, buf,
                            static_cast<f32>(x_offset + row_node->x + name_node->x),
                            static_cast<f32>(y_offset + row_node->y + name_node->y),
                            0.28f, 0.0f, 1.0f);
        } else {
            const char* sk_name = Skill_GetNameString(entry.value);
            if (sk_name != nullptr) {
                UiFont_DrawText(2, 0xFF, sk_name,
                                static_cast<f32>(x_offset + row_node->x + name_node->x),
                                static_cast<f32>(y_offset + row_node->y + name_node->y),
                                0.28f, 0.0f, 1.0f);
            }
        }

        const UiLayoutNode* icon_node = UiLayout_GetNode(0x1A, 0x449);
        const s32 item_id_arg = hide_names ? 0 : static_cast<s16>(entry.id);
        UiSkill_DrawItemIconAndCount(item_id_arg,
                                     x_offset + row_node->x + icon_node->x,
                                     y_offset + row_node->y + icon_node->y,
                                     0xB5, 0);

        const UiLayoutNode* cost_node = UiLayout_GetNode(0x1A, 0x44A);
        UiSkill_DrawSkillCostAndInfo(entry.value,
                                     x_offset + row_node->x + cost_node->x,
                                     y_offset + row_node->y + cost_node->y,
                                     0xB5);
    }

    if (work->state == 17) {
        const StatusDownListEntry& sel_entry = work->skill_entries[scroll_offset + selected_row];
        if (sel_entry.value != 0) {
            const UiLayoutNode* sel_node = UiLayout_GetNode(0x1A, static_cast<u32>(0x42C + selected_row));
            const f32 pulse_alpha = *reinterpret_cast<const f32*>(&work->panel_sprites[1].raw[0x20]);
            UiSprite_SetGlobalAlpha(pulse_alpha);
            UiSprite_DrawPanel(2, 0x1A, 8, x_offset + sel_node->x, y_offset + sel_node->y, 0xBF);

            UiSprite_SetGlobalAlpha(1.0f);
            UiSprite_DrawNode(2, 0x1A, 0x41F, x_offset + sel_node->x, y_offset + sel_node->y, 0xC4);

            u32 cursor_frame_node = 0x420;
            if (work->touch_drag_state[0] == 0 && work->touch_drag_state[1] == 0 &&
                work->touch_drag_state[2] == 0 && work->lr_state_left == 0 &&
                work->lr_state_right == 0 && work->touch_hold_state >= 0) {
                cursor_frame_node = 0x421;
            }
            UiSprite_DrawNode(2, 0x1A, cursor_frame_node, x_offset + sel_node->x, y_offset + sel_node->y, 0xC4);
            UiSprite_DrawNode(2, 0x1A, 0x457, x_offset + sel_node->x, y_offset + sel_node->y, 0xC4);

            const UiLayoutNode* clip_node = UiLayout_GetNode(0x1A, 0x420);
            UiScissor_SetRect(x_offset + sel_node->x + clip_node->x,
                              y_offset + sel_node->y + clip_node->y,
                              clip_node->rect->w, clip_node->rect->h, 1);

            const s32 anim_y = UiAnimSprite_GetPosY(&work->panel_sprites[3]);
            const s32 anim_x = UiAnimSprite_GetPosX(&work->panel_sprites[3]);
            UiSprite_DrawNode(2, 0x1A, 0x422,
                              x_offset + anim_x + sel_node->x,
                              y_offset + anim_y + sel_node->y, 0xC9);

            const UiLayoutNode* icon_node = UiLayout_GetNode(0x1A, 0x458);
            const s32 item_id_arg = hide_names ? 0 : static_cast<s16>(sel_entry.id);
            UiSkill_DrawItemIconAndCount(item_id_arg,
                                         x_offset + sel_node->x + icon_node->x,
                                         y_offset + sel_node->y + icon_node->y,
                                         0xC9, 0);

            const UiLayoutNode* cost_node = UiLayout_GetNode(0x1A, 0x459);
            UiSkill_DrawSkillCostAndInfo(sel_entry.value,
                                         x_offset + sel_node->x + cost_node->x,
                                         y_offset + sel_node->y + cost_node->y,
                                         0xC9);
        }
    }

    if (UiListCursor_GetRowCount(cursor) <= 0) {
        UiSprite_DrawPanel(2, 0x1A, 0x1B, x_offset, y_offset, 0xDD);
    }

    UiScrollBar_Draw(cursor, x_offset, y_offset, 0x1A,
                     0x405, 0x406, 0x403, 0x400,
                     0x403, 0x403, 0x403, work->btn_touch_handle,
                     work->scroll_up_touch_handle, work->scroll_down_touch_handle,
                     0xC4, 0);
}

// DECOMP_FUNC(0x0032c4bc, 372)
void StatusDown_SortItemList() {
    StatusDownWork* work = g_StatusDownWork;
    const u8* sort_cfg = Camp_GetSortConfig();
    const u8 item_sort = sort_cfg[0x16];

    if ((item_sort & 0x7F) == 1) {
        const bool desc = (item_sort >> 7) != 0;
        qsort_arm(work->item_entries, work->item_count, sizeof(StatusDownListEntry),
                  desc ? StatusDown_ItemSortByIdDesc : StatusDown_ItemSortByIdAsc);
    }
    if ((sort_cfg[0x16] & 0x7F) == 8) {
        const bool desc = (sort_cfg[0x16] >> 7) != 0;
        qsort_arm(work->item_entries, work->item_count, sizeof(StatusDownListEntry),
                  desc ? StatusDown_ItemSortByTypeDesc : StatusDown_ItemSortByTypeAsc);
    }
    if ((sort_cfg[0x16] & 0x7F) == 2) {
        const bool desc = (sort_cfg[0x16] >> 7) != 0;
        qsort_arm(work->item_entries, work->item_count, sizeof(StatusDownListEntry),
                  desc ? ItemSort_ByCountDesc : ItemSort_ByCountAsc);
    }
    if ((sort_cfg[0x16] & 0x7F) == 3) {
        const bool desc = (sort_cfg[0x16] >> 7) != 0;
        qsort_arm(work->item_entries, work->item_count, sizeof(StatusDownListEntry),
                  desc ? ItemSort_ByNameDesc : ItemSort_ByNameAsc);
    }
}

// DECOMP_FUNC(0x00187014, 5176)
void StatusDown_DrawPartyAndSubViews(s32 x_offset, s32 y_offset) {
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        return;
    }

    const s32 selected_row = UiListCursor_GetSelectedRow(&work->list_cursor_main);
    bool mask_names = false;
    const s32 main_menu_id = Camp_GetMainMenuId();
    if (main_menu_id == 0xD) {
        mask_names = true;
    } else if (main_menu_id == 6) {
        const u16* actor_ptr = Camp_GetSelectedActorPtr();
        if (actor_ptr != nullptr && !Camp_IsActorPlayer(*actor_ptr)) {
            mask_names = true;
        }
    }

    UiSprite_DrawPanel(2, 0x1A, 4, x_offset, y_offset, 0xB3);
    UiSprite_DrawPanel(2, 0x1A, 6, x_offset, y_offset, 0xB5);
    StatusDown_DrawLRPrompts(x_offset, y_offset);

    for (s32 i = 0; i < 8; ++i) {
        const u16 demon_id = work->party_ids[i];
        const u32 node_id = static_cast<u32>(0x414 + i);
        if (demon_id != 0) {
            s32 highlight = 0;
            if (work->new_party_flags[i] != 0) {
                highlight = 1;
            }
            StatusDown_DrawPartySlotRow(x_offset, y_offset, demon_id, node_id, 1.0f, 0, 1, highlight);
        } else {
            StatusDown_DrawPartySlotRow(x_offset, y_offset, 0, node_id, 1.0f, 0, 1, 0);
        }
    }

    if (work->has_sub_ids_a != 0) {
        for (s32 i = 0; i < 8; ++i) {
            const u16 sub_id = work->sub_ids_a[i];
            if (sub_id != 0) {
                const u32 node_id = static_cast<u32>(0x434 + i);
                StatusDown_DrawPartySlotRow(x_offset, y_offset, sub_id, node_id, 1.0f, 1, 0, 0);
            }
        }
    }
}

// DECOMP_FUNC(0x001ca648, 8908)
void StatusDown_CalcTaskCallback(void* arg) {
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        return;
    }

    work->field_2388 = 0;
    UiCursor_HandleInput(&work->list_cursor_main);
    work->status_mode = 0;

    work->touch_drag_state[0] = UiTouch_GetRegionTouchState(work->scroll_up_touch_handle);
    work->touch_drag_state[1] = UiTouch_GetRegionTouchState(work->scroll_down_touch_handle);
    work->touch_drag_state[2] = UiTouch_GetRegionTouchState(work->btn_touch_handle);
    work->lr_state_left = UiTouch_GetRegionTouchState(work->l_btn_touch_handle);
    work->lr_state_right = UiTouch_GetRegionTouchState(work->r_btn_touch_handle);

    work->touch_hold_state = -1;
    for (s32 i = 0; i < 36; ++i) {
        const s16 handle = work->slot_touch_handles[i];
        if (handle >= 0) {
            const s32 tstate = UiTouch_GetRegionTouchState(handle);
            if (tstate == 1 || tstate == 2) {
                work->touch_hold_state = i;
                break;
            }
        }
    }

    if (!Camp_CanShowLRPrompts()) {
        work->lr_state_left = 0;
        work->lr_state_right = 0;
    }

    const u32 state = work->state;
    switch (state) {
        case 0:
            break;
        case 1: {
            const bool anim_done = UiAnimSprite_UpdateCalc(&work->panel_sprites[0], 0);
            if (anim_done) {
                work->state_timer = 0;
                work->prev_state = work->state;
                work->state = work->sub_state;
                StatusDown_SetupTouchRegions();
                work->needs_refresh = 1;
            }
            break;
        }
        case 2: {
            UiAnimSprite_StepAnimation(&work->panel_sprites[0]);
            const bool anim_done = UiAnimSprite_UpdateCalc(&work->panel_sprites[0], 1);
            if (anim_done) {
                work->state_timer = 0;
                work->prev_state = work->state;
                work->state = work->sub_state;
                StatusDown_SetupTouchRegions();
                work->needs_refresh = 1;
            }
            break;
        }
        case 3: {
            if (work->touch_hold_state >= 0) {
                UiListCursor_SetSelectedRow(&work->list_cursor_main, work->touch_hold_state);
                work->needs_refresh = 1;
            }
            if (work->request_close_flag != 0) {
                StatusDown_Close();
            }
            break;
        }
        case 4: {
            if (work->touch_hold_state >= 0) {
                UiListCursor_SetSelectedRow(&work->list_cursor_main, work->touch_hold_state);
                work->needs_refresh = 1;
            }
            if (work->request_close_flag != 0) {
                StatusDown_Close();
            }
            break;
        }
        case 6: {
            if (work->touch_hold_state >= 0) {
                UiListCursor_SetSelectedRow(&work->list_cursor_main, work->touch_hold_state);
                work->needs_refresh = 1;
            }
            break;
        }
        case 11: {
            if (work->touch_hold_state >= 0) {
                UiListCursor_SetSelectedRow(&work->list_cursor_main, work->touch_hold_state);
                work->needs_refresh = 1;
            }
            break;
        }
        case 14: {
            break;
        }
        case 16: {
            if (work->touch_hold_state >= 0) {
                UiListCursor_SetSelectedRow(&work->list_cursor_main, work->touch_hold_state);
                work->needs_refresh = 1;
            }
            break;
        }
        case 17:
        case 18: {
            UiCursor_HandleInput(&work->skill_cursor);
            if (work->touch_hold_state >= 0) {
                UiListCursor_SetSelectedRow(&work->skill_cursor, work->touch_hold_state);
                work->needs_refresh = 1;
            }
            break;
        }
        case 19:
        case 20: {
            UiCursor_HandleInput(&work->item_cursor);
            if (work->touch_hold_state >= 0) {
                const s32 sel_row = work->touch_hold_state / 4;
                const s32 sel_col = work->touch_hold_state % 4;
                UiListCursor_SetSelectedRow(&work->item_cursor, sel_row);
                UiListCursor_SetSelectedCol(&work->item_cursor, sel_col);
                work->needs_refresh = 1;
            }
            break;
        }
        case 22:
        case 23:
        case 25:
        case 26: {
            UiCursor_HandleInput(&work->category_cursor);
            if (work->touch_hold_state >= 0) {
                UiListCursor_SetSelectedRow(&work->category_cursor, work->touch_hold_state);
                work->needs_refresh = 1;
            }
            break;
        }
        default:
            break;
    }

    ++work->state_timer;
}

// DECOMP_FUNC(0x001cc914, 5348)
void StatusDown_DrawTaskCallback(void* arg) {
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr || work->visibility_flag == 0) {
        return;
    }

    const s32 base_x = UiAnimSprite_GetPosX(&work->panel_sprites[0]);
    const s32 base_y = UiAnimSprite_GetPosY(&work->panel_sprites[0]);

    s32 state = work->state;
    if (state == 1) {
        state = work->sub_state;
    } else if (state == 2) {
        state = work->prev_state;
    }

    if (state < 3 || state >= 28) {
        return;
    }

    if (state >= 3 && state <= 15) {
        StatusDown_DrawPartyAndSubViews(base_x, base_y);
    } else if (state == 16) {
        UiSprite_DrawPanel(2, 0x1A, 0x0C, base_x, base_y, 0xB3);
        UiSprite_DrawNode(2, 0x1A, 0x51E, base_x, base_y, 0xB5);
        UiSprite_DrawNode(2, 0x1A, 0x52C, base_x, base_y, 0xB5);
        StatusDown_DrawLRPrompts(base_x, base_y);

        for (s32 i = 0; i < 7; ++i) {
            const u16 demon_id = work->party_ids[i];
            const u32 node_id = static_cast<u32>(0x466 + i);
            if (demon_id != 0) {
                StatusDown_DrawPartySlotRow(base_x, base_y, demon_id, node_id, 1.0f, 0, 0, 0);
            }
        }
    } else if (state == 17 || state == 18) {
        StatusDown_DrawSkillList(base_x, base_y);
    } else if (state == 19 || state == 20) {
        UiListCursor* cursor = &work->item_cursor;
        const s32 scroll_row = UiListCursor_GetScrollOffset(cursor);

        UiSprite_DrawPanel(2, 0x1A, 0x10, base_x, base_y, 0xB3);
        UiSprite_DrawPanel(2, 0x1A, 0x12, base_x, base_y, 0xB5);
        StatusDown_DrawLRPrompts(base_x, base_y);

        for (s32 row = 0; row < 9; ++row) {
            for (s32 col = 0; col < 4; ++col) {
                const s32 idx = col + ((scroll_row + row) << 2);
                if (idx >= work->item_count) {
                    break;
                }
                const StatusDownListEntry& entry = work->item_entries[idx];
                if (entry.id == 0 || entry.value == 0) {
                    continue;
                }
                const u32 node_id = static_cast<u32>(0x4AE + col + (row << 2));
                const UiLayoutNode* node = UiLayout_GetNode(0x1A, node_id);
                if (node != nullptr) {
                    UiSkill_DrawItemIconAndCount(entry.id, base_x + node->x, base_y + node->y, 0xB5, entry.value);
                }
            }
        }

        if (UiListCursor_GetRowCount(cursor) <= 0) {
            UiSprite_DrawPanel(2, 0x1A, 0x1B, base_x, base_y, 0xDD);
        }

        UiScrollBar_Draw(cursor, base_x, base_y, 0x1A,
                         0x405, 0x406, 0x403, 0x400,
                         0x403, 0x403, 0x403, work->btn_touch_handle,
                         work->scroll_up_touch_handle, work->scroll_down_touch_handle,
                         0xC4, 0);
    } else if (state == 21) {
        UiSprite_DrawPanel(2, 0x1A, 0x14, base_x, base_y, 0xB3);
        UiSprite_DrawPanel(2, 0x1A, 0x16, base_x, base_y, 0xB5);
        StatusDown_DrawLRPrompts(base_x, base_y);
    } else if (state >= 22 && state <= 27) {
        UiListCursor* cursor = &work->category_cursor;
        const s32 scroll_row = UiListCursor_GetScrollOffset(cursor);

        UiSprite_DrawPanel(2, 0x1A, 0x18, base_x, base_y, 0xB3);
        UiSprite_DrawPanel(2, 0x1A, 0x1A, base_x, base_y, 0xB5);
        StatusDown_DrawLRPrompts(base_x, base_y);

        const s32 visible_limit = Category_GetVisibleRowLimit();
        for (s32 row = 0; row < visible_limit; ++row) {
            const s32 idx = scroll_row + row;
            if (idx >= 8) {
                break;
            }
            const u16 cat_id = work->category_ids[idx];
            if (cat_id == 0) {
                continue;
            }
            const u32 node_id = static_cast<u32>(0x414 + row);
            const UiLayoutNode* node = UiLayout_GetNode(0x1A, node_id);
            if (node != nullptr) {
                UiSprite_DrawNode(2, 0x1A, node_id, base_x + node->x, base_y + node->y, 0xC4);
            }
        }

        UiScrollBar_Draw(cursor, base_x, base_y, 0x1A,
                         0x405, 0x406, 0x403, 0x400,
                         0x403, 0x403, 0x403, work->btn_touch_handle,
                         work->scroll_up_touch_handle, work->scroll_down_touch_handle,
                         0xC4, 0);
    }
}

} // namespace smt4::ui
