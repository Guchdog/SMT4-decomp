#include "ui/status_down.h"
#include "ui/status.h"
#include "engine/asd_symbols.h"
#include <cstring>

namespace smt4::ui {

// 0x002C32F8 copies its ten trailing arguments verbatim; table pointers are
// passed as their 32-bit address words.
static inline u32 SpriteTableWord(const void* pointer) {
    return static_cast<u32>(reinterpret_cast<std::uintptr_t>(pointer));
}

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
    void  AsdMem_Copy(void* dst, const void* src, u32 size);
    s32   camp_func_0029f0f4(void* cursor);
    s32   camp_func_0029f248(void* cursor);                        // 0x002c5ff4
    void* camp_func_00257744(u32 id);
    void* camp_func_002b9364(u32 id);
    s32   func_00257678(s32 cost_raw);
    void  AsdMem_FreeWork(void* ptr);                                               // 0x002c4360
    void  camp_func_002c4450(void* ptr, u32 size, s32 val);                         // 0x002c4450

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
    s32   AsdText_GetLineCount(void* text_handle) __asm__("engine_func_002b787c"); // 0x002b787c
    void  AsdText_DestroyHandle(void* text_handle);                                 // 0x002a7b50

    // UiSpriteGroup_Init / UiSpriteGroup_BindTable are declared canonically in
    // engine/asd_symbols.h (0x002C3344 / 0x002C32F8).

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
    // 5th/6th arguments are the integer draw-bars gate and row offset.
    void  UiParty_DrawDemonBars(s16 demon_id, s32 x, s32 y, s32 prio,
                                s32 draw_bars, s32 a5);                             // 0x002b6f74
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
    const UiLayoutNode* camp_func_002bf6d0(u32 group, u32 node_id);                // 0x002bf6d0
    void  UiTouch_UnregisterLastRegion();                                           // 0x002b9008
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
    // Keep these comparator calls bound to the names present in the function
    // ledger so asm_diff can resolve their ARM call relocations.
    const SkillTableEntry* Skill_GetTableEntry(u16 skill_id)
        asm("camp_func_00257744");                                                  // 0x00257744
    void* Battle_GetTalkEntry(u32 id)
        asm("camp_func_002b9364");                                                  // 0x002b9364
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

// Canonical 0x002BF6D0 returns `const void*`; offset-compatible view used by
// this TU (x +0x08, y +0x0A, rect pointer +0x0C).
static inline const UiLayoutNode* LayoutNode(u32 group_id, u32 node_id) {
    return static_cast<const UiLayoutNode*>(UiLayout_GetNode(group_id, node_id));
}

// DECOMP_FUNC(0x001ddab4, 68)
void StatusDown_OpenDefaultView() {
    auto* work = g_StatusDownWork;
    UiAnimSprite_SetAnim(&work->panel_sprites[0], 1, 0);
    work = g_StatusDownWork;
    work->state_timer = 0;
    u32 prev = work->state;
    work->state = 1;
    work->prev_state = prev;
    work->sub_state = 3;
}

// DECOMP_FUNC(0x001ee5a4, 548)
void StatusDown_PopulateSkillList(const u8* skill_bitfield) {
    auto* work = g_StatusDownWork;
    work->skill_count = 0;
    work->skill_total = 0;
    AsdMem_Zero(work->skill_entries, sizeof(work->skill_entries));

    for (u16 i = 0; i < 0x500; ++i) {
        const auto* entry = static_cast<const ItemTableEntry*>(Battle_GetTalkEntry(i));
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

    auto* w = g_StatusDownWork;
    const u8* sort_cfg = Camp_GetSortConfig();
    const u8 skill_sort = sort_cfg[0x15];
    const u8 sort_key = skill_sort & 0x7F;
    const bool desc = (skill_sort >> 7) != 0;

    if (sort_key == 1) {
        qsort_arm(w->skill_entries, w->skill_count, sizeof(StatusDownListEntry),
                  desc ? StatusDown_SkillSortByIdDesc : StatusDown_SkillSortByIdAsc);
    } else if (sort_key == 0x21) {
        qsort_arm(w->skill_entries, w->skill_count, sizeof(StatusDownListEntry),
                  desc ? StatusDown_SkillSortByCostDesc : StatusDown_SkillSortByCostAsc);
    } else if (sort_key == 3) {
        qsort_arm(w->skill_entries, w->skill_count, sizeof(StatusDownListEntry),
                  desc ? SkillSort_ByNameDesc : StatusDown_SkillSortByNameAsc);
    }

    work->needs_refresh = 1;
}

// DECOMP_FUNC(0x001ee7c8, 384)
void StatusDown_PopulateItemList(const u8* item_counts) {
    auto* work = g_StatusDownWork;
    work->item_count = 0;
    work->item_nonzero_count = 0;
    AsdMem_Zero(work->item_entries, sizeof(work->item_entries));

    for (u16 i = 0; i < 0x500; ++i) {
        const auto* entry = static_cast<const ItemTableEntry*>(Battle_GetTalkEntry(i));
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
    const auto* ea = static_cast<const StatusDownListEntry*>(a);
    const auto* eb = static_cast<const StatusDownListEntry*>(b);
    const auto* sa = reinterpret_cast<const SkillTableEntry*>(camp_func_00257744(ea->value));
    const auto* sb = reinterpret_cast<const SkillTableEntry*>(camp_func_00257744(eb->value));
    s32 ca = func_00257678(sa->cost_raw);
    s32 cb = func_00257678(sb->cost_raw);
    s32 diff = ca - cb;
    if (diff != 0) {
        return diff;
    }
    const auto* ia = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(ea->id));
    const auto* ib = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(eb->id));
    diff = static_cast<s32>(ia->category) - static_cast<s32>(ib->category);
    if (diff != 0) {
        return diff;
    }
    diff = static_cast<s32>(ib->rarity) - static_cast<s32>(ia->rarity);
    if (diff != 0) {
        return diff;
    }
    return static_cast<s32>(ia->id) - static_cast<s32>(ib->id);
}
// DECOMP_FUNC(0x001f6174, 48)
s32 StatusDown_SkillSortByNameAsc(const void* a, const void* b) {
    const auto* ea = static_cast<const StatusDownListEntry*>(a);
    const auto* eb = static_cast<const StatusDownListEntry*>(b);
    const auto* sa = reinterpret_cast<const SkillTableEntry*>(camp_func_00257744(ea->value));
    const auto* sb = reinterpret_cast<const SkillTableEntry*>(camp_func_00257744(eb->value));
    return static_cast<s32>(sa->sort_order) - static_cast<s32>(sb->sort_order);
}
// DECOMP_FUNC(0x00206be8, 80)
s32 StatusDown_SkillSortByIdAsc(const void* a, const void* b) {
    const auto* ea = static_cast<const StatusDownListEntry*>(a);
    const auto* eb = static_cast<const StatusDownListEntry*>(b);
    const auto* ia = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(ea->id));
    const auto* ib = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(eb->id));
    s32 diff = static_cast<s32>(ia->category) - static_cast<s32>(ib->category);
    if (diff != 0) {
        return diff;
    }
    diff = static_cast<s32>(ib->rarity) - static_cast<s32>(ia->rarity);
    if (diff != 0) {
        return diff;
    }
    return static_cast<s32>(ia->id) - static_cast<s32>(ib->id);
}
// DECOMP_FUNC(0x00206c38, 132)
s32 StatusDown_ItemSortByTypeAsc(const void* a, const void* b) {
    const auto* ea = static_cast<const StatusDownListEntry*>(a);
    const auto* eb = static_cast<const StatusDownListEntry*>(b);
    u16 va = ea->value;
    u16 vb = eb->value;
    if (va == 0) {
        return vb != 0 ? 1 : 0;
    }
    if (vb == 0) {
        return -1;
    }
    s32 diff = static_cast<s32>(va) - static_cast<s32>(vb);
    if (diff != 0) {
        return diff;
    }
    const auto* ia = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(ea->id));
    const auto* ib = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(eb->id));
    diff = static_cast<s32>(ia->category) - static_cast<s32>(ib->category);
    if (diff != 0) {
        return diff;
    }
    diff = static_cast<s32>(ib->rarity) - static_cast<s32>(ia->rarity);
    if (diff != 0) {
        return diff;
    }
    return static_cast<s32>(ia->id) - static_cast<s32>(ib->id);
}
// DECOMP_FUNC(0x00206cbc, 124)
s32 StatusDown_ItemSortByIdAsc(const void* a, const void* b) {
    const auto* ea = static_cast<const StatusDownListEntry*>(a);
    const auto* eb = static_cast<const StatusDownListEntry*>(b);
    u16 va = ea->value;
    u16 vb = eb->value;
    if (va == 0) {
        return vb != 0 ? 1 : 0;
    }
    if (vb == 0) {
        return -1;
    }
    const auto* ia = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(ea->id));
    const auto* ib = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(eb->id));
    s32 diff = static_cast<s32>(ia->category) - static_cast<s32>(ib->category);
    if (diff != 0) {
        return diff;
    }
    diff = static_cast<s32>(ib->rarity) - static_cast<s32>(ia->rarity);
    if (diff != 0) {
        return diff;
    }
    return static_cast<s32>(ia->id) - static_cast<s32>(ib->id);
}

// DECOMP_FUNC(0x00215990, 180)
void StatusDown_SetPartyPrompt(const StatusDownPartyPrompt* prompt) {
    auto* work = g_StatusDownWork;
    if (work->active_sound_id >= 0 && work->active_mode == 1) {
        s32 menu_id = Status_GetMainMenuId();
        if (menu_id == 0xD || menu_id == 6) {
            Sound_PlaySE(0x2F);
        } else {
            Sound_PlaySE(0x1F);
        }
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
void StatusDown_SetActiveSoundId(s16 id) {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work != nullptr) {
        work->active_sound_id = id;
    }
}

// DECOMP_FUNC(0x00215a68, 248)
void StatusDown_SetPartySlots(const u16* party_slots, s32 count) {
    auto* work = g_StatusDownWork;
    for (s32 i = 0; i < 4; ++i) {
        reinterpret_cast<u32*>(work->new_party_flags)[i] = 0;
        reinterpret_cast<u32*>(work->party_ids)[i] = 0;
    }
    AsdMem_Copy(work->party_ids, party_slots, count * sizeof(u16));
    s32 total_items = 0;
    while (total_items < count && work->party_ids[total_items] != 0) {
        total_items++;
    }
    UiListCursor_Setup(&work->list_cursor_main, total_items, 8, 1, 0, 1);
    work->needs_refresh = 1;
    work->flag_548 = 0;
}

// DECOMP_FUNC(0x00223b88, 40)
bool StatusDown_IsState20() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work == nullptr) {
        return false;
    }
    return work->state == 0x14;
}

// DECOMP_FUNC(0x0026abe0, 84)
void StatusDown_SetSubIdsA(const u16* ids, s32 count) {
    if (count > 8) {
        return;
    }
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    for (int i = 0; i < 8; i++) {
        work->sub_ids_a[i] = 0;
    }
    if (count < 0) {
        work->has_sub_ids_a = 0;
        return;
    }
    work->has_sub_ids_a = 1;
    AsdMem_Copy(work->sub_ids_a, ids, count * sizeof(u16));
}

// DECOMP_FUNC(0x0026b01c, 176)
void StatusDown_PopFirstSubIdA() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    u16 first_a = work->sub_ids_a[0];
    for (int i = 0; i < 8; i++) {
        if (work->sub_ids_b[i] != 0 && work->sub_ids_b[i] == first_a) {
            work->sub_ids_b[i] = 0;
        }
    }
    work->sub_ids_a[0] = 0;
    for (int i = 0; i < 7; i++) {
        for (int j = i; j < 7; j++) {
            if (work->sub_ids_a[j] == 0 && work->sub_ids_a[j + 1] != 0) {
                work->sub_ids_a[j] = work->sub_ids_a[j + 1];
                work->sub_ids_a[j + 1] = 0;
            }
        }
    }
}

#if 0 // Unverified behavioral reconstruction; retained for reference only.
[[maybe_unused]] static void StatusDown_SetupTouchRegions_Draft() {
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
            const UiLayoutNode* node_btn = LayoutNode(0x1A, 0x4F1);
            const UiLayoutNode* node_bg = LayoutNode(0x1A, 0x41F);
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
#endif

// DECOMP_FUNC(0x0026b0d0, 1636)
void StatusDown_SetupTouchRegions() {
    auto* work = g_StatusDownWork;
    const s32 prev_count = static_cast<u8>(work->registered_touch_count);
    for (s32 i = 0; i < prev_count; ++i) {
        UiTouch_UnregisterLastRegion();
    }
    work->registered_touch_count = 0;
    camp_func_002c4450(work->slot_touch_handles, 0x29, -1);

    switch (work->state) {
    case 3: {
        for (s32 i = 0; i < camp_func_0029f0f4(&work->list_cursor_main); ++i) {
            work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, 0x414 + i);
            work->registered_touch_count++;
        }
        work->l_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50F);
        work->r_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50E);
        work->registered_touch_count += 2;
        break;
    }
    case 4: {
        for (s32 i = 0; i < camp_func_0029f0f4(&work->list_cursor_main); ++i) {
            work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, 0x414 + i);
            work->registered_touch_count++;
        }
        break;
    }
    case 6: {
        for (s32 i = 0; i < camp_func_0029f0f4(&work->list_cursor_main); ++i) {
            work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, 0x414 + i);
            work->registered_touch_count++;
        }
        const s32 last_slot = static_cast<u8>(work->registered_touch_count);
        work->slot_touch_handles[last_slot] = UiTouch_RegisterRegion(0x1A, 0x4F1);
        work->registered_touch_count++;
        break;
    }
    case 11: {
        for (s32 i = 0; i < camp_func_0029f0f4(&work->list_cursor_main) - 1; ++i) {
            work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, 0x414 + i);
            work->registered_touch_count++;
        }
        const auto* node_a = camp_func_002bf6d0(0x1A, 0x4F1);
        const auto* node_b = camp_func_002bf6d0(0x1A, 0x41F);
        const s16 handle = UiTouch_RegisterRectRegion(
            node_a->x, node_a->y, node_b->rect->w, node_a->rect->h);
        const s32 last_slot = static_cast<u8>(work->registered_touch_count);
        work->slot_touch_handles[last_slot] = handle;
        work->registered_touch_count++;
        break;
    }
    case 16: {
        for (s32 i = 0; i < 7; ++i) {
            if (Flag_CheckEventBit(0x410) || (i != 1 && i != 2)) {
                work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, 0x466 + i);
            } else {
                work->slot_touch_handles[i] = 0;
            }
            work->registered_touch_count++;
        }
        work->l_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50F);
        work->r_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50E);
        work->registered_touch_count += 2;
        break;
    }
    case 17: {
        for (s32 i = 0; i < 11; ++i) {
            work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, 0x44C + i);
            work->registered_touch_count++;
        }
        work->scroll_up_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4E7);
        work->scroll_down_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4E8);
        work->btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4E9);
        work->registered_touch_count += 3;
        work->l_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50F);
        work->r_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50E);
        work->registered_touch_count += 2;
        break;
    }
    case 19: {
        const s32 total_items = *reinterpret_cast<const s16*>(reinterpret_cast<const u8*>(work) + 0x2232);
        for (s32 row = 0; row < 9; ++row) {
            for (s32 col = 0; col < 4; ++col) {
                const s32 idx = row * 4 + col;
                if (idx < total_items) {
                    work->slot_touch_handles[idx] = UiTouch_RegisterRegion(0x1A, 0x4AE + idx);
                    work->registered_touch_count++;
                }
            }
        }
        work->scroll_up_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4E7);
        work->scroll_down_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4E8);
        work->btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4E9);
        work->registered_touch_count += 3;
        work->l_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50F);
        work->r_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50E);
        work->registered_touch_count += 2;
        break;
    }
    case 21: {
        work->scroll_up_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4EA);
        work->scroll_down_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4EB);
        work->btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x4EC);
        work->registered_touch_count += 3;
        work->l_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50F);
        work->r_btn_touch_handle = UiTouch_RegisterRegion(0x1A, 0x50E);
        work->registered_touch_count += 2;
        break;
    }
    case 22:
    case 23:
    case 25:
    case 26: {
        for (s32 i = 0; i < camp_func_0029f0f4(&work->category_cursor) - 1; ++i) {
            work->slot_touch_handles[i] = UiTouch_RegisterRegion(0x1A, 0x414 + i);
            work->registered_touch_count++;
        }
        const s16 handle = UiTouch_RegisterRegion(0x1A, 0x54A);
        const s32 count = camp_func_0029f0f4(&work->category_cursor);
        work->slot_touch_handles[count - 1] = handle;
        work->registered_touch_count++;
        break;
    }
    default:
        break;
    }
}

// DECOMP_FUNC(0x0026d8c0, 28)
void StatusDown_SetVisibility(u8 val) {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work != nullptr) {
        work->visibility_flag = val;
    }
}

// DECOMP_FUNC(0x00288718, 92)
bool StatusDown_CanOpenSubScreen() {
    if (Status_GetSubMenuState() == 5 ||
        Status_GetSubMenuState() == 6 ||
        Status_GetSubMenuState() == 10 ||
        Status_GetMainMenuId() == 7 ||
        Status_GetMainMenuId() == 8 ||
        Status_GetMainMenuId() == 3) {
        return false;
    }
    return true;
}

// DECOMP_FUNC(0x0028cd5c, 28)
u32 StatusDown_GetField2384() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work == nullptr) {
        return 0;
    }
    return work->field_2384;
}

// DECOMP_FUNC(0x0028cd78, 36)
bool StatusDown_IsInactiveOrState0() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work == nullptr) {
        return true;
    }
    return work->state == 0;
}

// DECOMP_FUNC(0x00292f44, 304)
void StatusDown_SetDisplayMode(s32 mode) {
    auto* work = g_StatusDownWork;
    if (work->active_mode == mode) {
        return;
    }
    work->prev_active_mode = work->active_mode;
    work->active_mode = static_cast<u8>(mode);
    s32 dir = Camp_GetTransitionDir();
    if (dir < 0) {
        UiAnimSprite_SetAnim(&work->panel_sprites[0], 3, 0);
    } else if (Camp_GetTransitionDir() > 0) {
        UiAnimSprite_SetAnim(&work->panel_sprites[0], 2, 0);
    }
    const u8 tr_count = static_cast<u8>(work->registered_touch_count);
    for (s32 i = 0; i < tr_count; ++i) {
        UiTouch_UnregisterLastRegion();
    }
    work->registered_touch_count = 0;
    AsdMem_FillBytes(work->slot_touch_handles, 0x29, 0xFFFFFFFF);
    work = g_StatusDownWork;
    work->state_timer = 0;
    u32 prev = work->state;
    work->state = 2;
    work->prev_state = prev;
    if (mode == 0) {
        work->sub_state = 0;
    } else if (mode == 1) {
        work->sub_state = 3;
    } else if (mode == 2) {
        work->sub_state = 0x10;
    } else if (mode == 3) {
        work->sub_state = 0x11;
    } else if (mode == 4) {
        work->sub_state = 0x13;
    } else if (mode == 5) {
        work->sub_state = 0x15;
    }
    Camp_SetFadeColor(0, 0x323232FF);
}
// DECOMP_FUNC(0x00293d2c, 36)
bool StatusDown_IsNotTransitioning() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    return (work->state != 0x12 && work->state != 0x14);
}

// DECOMP_FUNC(0x00293d50, 20)
u8 StatusDown_GetActiveMode() {
    // This fixed-ROM global is a pointer slot at 0x0044E190.
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    return work->active_mode;
}

// DECOMP_FUNC(0x00293e30, 28)
s8 StatusDown_GetStatusMode() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work == nullptr) {
        return 0;
    }
    return work->status_mode;
}

// DECOMP_FUNC(0x002956ac, 20)
u32 StatusDown_GetField53C() {
    // Keep the linked image's absolute pointer-slot literal in the object.
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    return work->field_53c;
}

// DECOMP_FUNC(0x0029a520, 1696)
// Verified ARM-state entry/exit and referenced local literal/table bytes.
__attribute__((naked)) void StatusDown_DrawPartySlotRow(s32 x_offset, s32 y_offset, s32 demon_id,
                                 u32 node_id, f32 scale, s32 is_stock_row,
                                 s32 is_empty_mode, s32 highlight_mode) {
    asm volatile(
        ".word 0xe92d4ff0\n"
        ".word 0xe1a06000\n"
        ".word 0xed2d8b02\n"
        ".word 0xe24dd06c\n"
        ".word 0xe59f040c\n"
        ".word 0xe1a07001\n"
        ".word 0xe59da0a0\n"
        ".word 0xe1a09002\n"
        ".word 0xe5905000\n"
        ".word 0xe1a01003\n"
        ".word 0xed9d8a26\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb00945e\n"
        ".word 0xe1a04000\n"
        ".word 0xe2850b01\n"
        ".word 0xe28000d4\n"
        ".word 0xe58d0064\n"
        ".word 0xeb001337\n"
        ".word 0xe58d0060\n"
        ".word 0xe3a0b000\n"
        ".word 0xe28500b4\n"
        ".word 0xed900a08\n"
        ".word 0xeb009464\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a010bf\n"
        ".word 0xe3a02008\n"
        ".word 0xe0800007\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a0101a\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0093ec\n"
        ".word 0xeddf8ae7\n"
        ".word 0xeeb00a68\n"
        ".word 0xeb009457\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a080c4\n"
        ".word 0xe59f238c\n"
        ".word 0xe0800007\n"
        ".word 0xe88d0101\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a0101a\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0093a1\n"
        ".word 0xe5950418\n"
        ".word 0xe3a02e42\n"
        ".word 0xe3500000\n"
        ".word 0x0595041c\n"
        ".word 0x03500000\n"
        ".word 0x1a000009\n"
        ".word 0xe5950420\n"
        ".word 0xe3500000\n"
        ".word 0x05950424\n"
        ".word 0x03500000\n"
        ".word 0x05950428\n"
        ".word 0x03500000\n"
        ".word 0x1a000002\n"
        ".word 0xe5950414\n"
        ".word 0xe3500000\n"
        ".word 0xa59f2334\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a010c4\n"
        ".word 0xe0800007\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a0101a\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb009388\n"
        ".word 0xe3a01e42\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb009421\n"
        ".word 0xe58d0054\n"
        ".word 0xe59f0300\n"
        ".word 0xe5901000\n"
        ".word 0xe3a00003\n"
        ".word 0xe2818a01\n"
        ".word 0xe2888fc3\n"
        ".word 0xe5981000\n"
        ".word 0xe0881101\n"
        ".word 0xe5912008\n"
        ".word 0xe5810008\n"
        ".word 0xe5d81018\n"
        ".word 0xe3510000\n"
        ".word 0x03520003\n"
        ".word 0x0a000003\n"
        ".word 0xe598101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c80018\n"
        ".word 0xe3a00001\n"
        ".word 0xe58d0000\n"
        ".word 0xe59d0054\n"
        ".word 0xe59d2054\n"
        ".word 0xe59d3054\n"
        ".word 0xe1d410fa\n"
        ".word 0xe590000c\n"
        ".word 0xe1d220fa\n"
        ".word 0xe1d380f8\n"
        ".word 0xe1d4c0f8\n"
        ".word 0xe1d030f2\n"
        ".word 0xe0811002\n"
        ".word 0xe1d000f0\n"
        ".word 0xe08c2008\n"
        ".word 0xe082c006\n"
        ".word 0xe1a02000\n"
        ".word 0xe0811007\n"
        ".word 0xe1a0000c\n"
        ".word 0xebffff4e\n"
        ".word 0xe2850f73\n"
        ".word 0xe320f000\n"
        ".word 0xeb009221\n"
        ".word 0xe1d410fa\n"
        ".word 0xe0800007\n"
        ".word 0xe0808001\n"
        ".word 0xe2850f73\n"
        ".word 0xeb00921f\n"
        ".word 0xe1d410f8\n"
        ".word 0xe0800006\n"
        ".word 0xe3a020c9\n"
        ".word 0xe0803001\n"
        ".word 0xe58d2004\n"
        ".word 0xe59f2240\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d8000\n"
        ".word 0xeb00934e\n"
        ".word 0xe59f0228\n"
        ".word 0xe5901000\n"
        ".word 0xe3a00000\n"
        ".word 0xe2818a01\n"
        ".word 0xe2888fc3\n"
        ".word 0xe5981000\n"
        ".word 0xe0882101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d82018\n"
        ".word 0xe3520000\n"
        ".word 0x03510000\n"
        ".word 0x0a000003\n"
        ".word 0xe598101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c80018\n"
        ".word 0xe59d00a4\n"
        ".word 0xe3e08000\n"
        ".word 0xe3500001\n"
        ".word 0x059f81e0\n"
        ".word 0x0a000001\n"
        ".word 0xe3500002\n"
        ".word 0x059f81d8\n"
        ".word 0xe2850b01\n"
        ".word 0xe58d000c\n"
        ".word 0xe5950400\n"
        ".word 0xe350000b\n"
        ".word 0x1350000e\n"
        ".word 0x0a00001b\n"
        ".word 0xe3500006\n"
        ".word 0x13500009\n"
        ".word 0x0a000007\n"
        ".word 0xe5d50548\n"
        ".word 0xe3500000\n"
        ".word 0x0a000004\n"
        ".word 0xe595154c\n"
        ".word 0xe59d0060\n"
        ".word 0xe1510000\n"
        ".word 0x1a000000\n"
        ".word 0xe59f8190\n"
        ".word 0xe59f1194\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb0093be\n"
        ".word 0xe35a0000\n"
        ".word 0xe1a05000\n"
        ".word 0x0a000001\n"
        ".word 0xe3590000\n"
        ".word 0x0a000014\n"
        ".word 0xe59d009c\n"
        ".word 0xe3500000\n"
        ".word 0x0a000017\n"
        ".word 0xe28f1f5b\n"
        ".word 0xe28d0010\n"
        ".word 0xfa008ffe\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000017\n"
        ".word 0xe5951544\n"
        ".word 0xe59d0060\n"
        ".word 0xe1510000\n"
        ".word 0x0affffe9\n"
        ".word 0xe59d0064\n"
        ".word 0xeb001233\n"
        ".word 0xe2401001\n"
        ".word 0xe59d0060\n"
        ".word 0xe1510000\n"
        ".word 0x159f8138\n"
        ".word 0x0affffe2\n"
        ".word 0xeaffffe2\n"
        ".word 0xe28f1e13\n"
        ".word 0xe28d0010\n"
        ".word 0xfa008fec\n"
        ".word 0xe59f8120\n"
        ".word 0xe320f000\n"
        ".word 0xea000005\n"
        ".word 0xe1a00009\n"
        ".word 0xeb0089e4\n"
        ".word 0xe1a02000\n"
        ".word 0xe28f1f51\n"
        ".word 0xe28d0010\n"
        ".word 0xfa008fe3\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d510fa\n"
        ".word 0xe1d420f8\n"
        ".word 0xe1d530f8\n"
        ".word 0xe0800001\n"
        ".word 0xe0800007\n"
        ".word 0xe0821003\n"
        ".word 0xe0811006\n"
        ".word 0xee000a90\n"
        ".word 0xee001a10\n"
        ".word 0xeeb02a68\n"
        ".word 0xe28d2010\n"
        ".word 0xe1a01008\n"
        ".word 0xeddf1a42\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xe3a00003\n"
        ".word 0xed9f1a3f\n"
        ".word 0xeb008fb0\n"
        ".word 0xe35a0000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000001\n"
        ".word 0xe3590000\n"
        ".word 0x0a00001b\n"
        ".word 0xe1d410fa\n"
        ".word 0xe3a000c4\n"
        ".word 0xe58d0004\n"
        ".word 0xe0811007\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d400f8\n"
        ".word 0xe59f20cc\n"
        ".word 0xe3a0101a\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0092d9\n"
        ".word 0xe59f10bc\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb009372\n"
        ".word 0xe3a01000\n"
        ".word 0xed8d8a00\n"
        ".word 0xe58d1004\n"
        ".word 0xe1d030fa\n"
        ".word 0xe1d410fa\n"
        ".word 0xe1d420f8\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0811003\n"
        ".word 0xe3a030c9\n"
        ".word 0xe0800002\n"
        ".word 0xe0812007\n"
        ".word 0xe0801006\n"
        ".word 0xe6bf0079\n"
        ".word 0xeb00718d\n"
        ".word 0xe320f000\n"
        ".word 0xea00001e\n"
        ".word 0x0044e190\n"
        ".word 0x3f800000\n"
        ".word 0x0000041f\n"
        ".word 0x00000421\n"
        ".word 0x0044ea00\n"
        ".word 0x00000422\n"
        ".word 0x72e027ff\n"
        ".word 0xdc0f14ff\n"
        ".word 0x0000042b\n"
        ".word 0x48814881\n"
        ".word 0x00004881\n"
        ".word 0x5a5a5aff\n"
        ".word 0x85826d82\n"
        ".word 0x40819782\n"
        ".word 0x85829282\n"
        ".word 0x89828782\n"
        ".word 0x94829382\n"
        ".word 0x81829282\n"
        ".word 0x89829482\n"
        ".word 0x8e828f82\n"
        ".word 0x90824081\n"
        ".word 0x93828f82\n"
        ".word 0x89829382\n"
        ".word 0x8c828282\n"
        ".word 0x49818582\n"
        ".word 0x00000000\n"
        ".word 0x00007325\n"
        ".word 0x00000000\n"
        ".word 0x3e4ccccd\n"
        ".word 0x00000425\n"
        ".word 0x0000042a\n"
        ".word 0xe59d009c\n"
        ".word 0xe3500000\n"
        ".word 0x1a000026\n"
        ".word 0xe35a0000\n"
        ".word 0x0a00003c\n"
        ".word 0xe1d410fa\n"
        ".word 0xe3a000c4\n"
        ".word 0xe58d0004\n"
        ".word 0xe0811007\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d400f8\n"
        ".word 0xe59f21b4\n"
        ".word 0xe3a0101a\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb009297\n"
        ".word 0xe59f11a4\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb009330\n"
        ".word 0xe3590000\n"
        ".word 0xe1a05000\n"
        ".word 0xe3a08008\n"
        ".word 0x0a000015\n"
        ".word 0xe1a00009\n"
        ".word 0xebffca9c\n"
        ".word 0xe58d000c\n"
        ".word 0xe28d0004\n"
        ".word 0xe28f2f5f\n"
        ".word 0xe3a010c9\n"
        ".word 0xe58d8000\n"
        ".word 0xe8800006\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d520fa\n"
        ".word 0xe1d410f8\n"
        ".word 0xe1d530f8\n"
        ".word 0xe0822000\n"
        ".word 0xe0822007\n"
        ".word 0xe0810003\n"
        ".word 0xe0801006\n"
        ".word 0xe3a03001\n"
        ".word 0xe3a00000\n"
        ".word 0xeb008dc0\n"
        ".word 0xe28dd06c\n"
        ".word 0xecbd8b02\n"
        ".word 0xe8bd8ff0\n"
        ".word 0xe28f1f4e\n"
        ".word 0xe28d0010\n"
        ".word 0xfa008f5e\n"
        ".word 0xe28d1010\n"
        ".word 0xe3a000c9\n"
        ".word 0xe58d8000\n"
        ".word 0xe1cd00f4\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d520fa\n"
        ".word 0xe1d410f8\n"
        ".word 0xe1d530f8\n"
        ".word 0xe0822000\n"
        ".word 0xe0822007\n"
        ".word 0xe0810003\n"
        ".word 0xe0801006\n"
        ".word 0xe3a03001\n"
        ".word 0xe3a00000\n"
        ".word 0xeb008dab\n"
        ".word 0xe28dd06c\n"
        ".word 0xecbd8b02\n"
        ".word 0xe8bd8ff0\n"
        ".word 0xe1d400fa\n"
        ".word 0xe59f20e4\n"
        ".word 0xe0801007\n"
        ".word 0xe3a000c4\n"
        ".word 0xe58d0004\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a0101a\n"
        ".word 0xe0803006\n"
        ".word 0xe3a00002\n"
        ".word 0xeb00925a\n"
        ".word 0xe59d000c\n"
        ".word 0xe1d007fe\n"
        ".word 0xe3500000\n"
        ".word 0xaa000005\n"
        ".word 0xe3a01001\n"
        ".word 0xe1a00009\n"
        ".word 0xeb000057\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000005\n"
        ".word 0xe320f000\n"
        ".word 0xeb000102\n"
        ".word 0xe3500006\n"
        ".word 0xe1a00009\n"
        ".word 0x0a000002\n"
        ".word 0xeb000022\n"
        ".word 0xe1a0b000\n"
        ".word 0xea000003\n"
        ".word 0xe320f000\n"
        ".word 0xeb004e2a\n"
        ".word 0xe3500000\n"
        ".word 0x15d0b022\n"
        ".word 0xe59f1068\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb0092dd\n"
        ".word 0xe3a03004\n"
        ".word 0xe28d5004\n"
        ".word 0xe28f2048\n"
        ".word 0xe3a010c9\n"
        ".word 0xe58d3000\n"
        ".word 0xe8850806\n"
        ".word 0xe1d030fa\n"
        ".word 0xe1d410fa\n"
        ".word 0xe1d420f8\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0811003\n"
        ".word 0xe3a03001\n"
        ".word 0xe0800002\n"
        ".word 0xe0812007\n"
        ".word 0xe0801006\n"
        ".word 0xe3a00000\n"
        ".word 0xeb008d73\n"
        ".word 0xe28dd06c\n"
        ".word 0xecbd8b02\n"
        ".word 0xe8bd8ff0\n"
        ".word 0x00000522\n"
        ".word 0x0000052a\n"
        ".word 0x00006425\n"
        ".word 0x002d2d2d\n"
        ".word 0x00000423\n"
        ".word 0x00000429\n"
    );
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void StatusDown_DrawPartySlotRow_Draft(s32 x_offset, s32 y_offset, s32 demon_id,
                                 u32 node_id, f32 scale, s32 is_stock_row,
                                 s32 is_empty_mode, s32 highlight_mode) {
    StatusDownWork* work = g_StatusDownWork;
    const UiLayoutNode* row_node = LayoutNode(0x1A, node_id);
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

    const UiLayoutNode* clip_node = LayoutNode(0x1A, 0x420);
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

    const UiLayoutNode* name_node = LayoutNode(0x1A, 0x42B);
    char name_buf[64]{};
    UiFont_FormatString(name_buf, "%s", "");
    UiFont_DrawText(3, text_color, name_buf,
                    static_cast<f32>(x_offset + row_node->x + name_node->x),
                    static_cast<f32>(y_offset + row_node->y + name_node->y),
                    0.2f, 0.0f, 1.0f);

    if (is_empty_mode == 0 || demon_id != 0) {
        UiSprite_DrawNode(2, 0x1A, 0x425, x_offset + row_node->x, y_offset + row_node->y, 0xC4);
        const UiLayoutNode* bar_node = LayoutNode(0x1A, 0x42A);
        // The listing stores the caller's float word (1.0f at every call site)
        // directly into the callee's integer gate slot (0x0029A908); convert
        // the reconstructed float parameter to the gate value.
        UiParty_DrawDemonBars(static_cast<s16>(demon_id),
                              x_offset + row_node->x + bar_node->x,
                              y_offset + row_node->y + bar_node->y,
                              0xC9, static_cast<s32>(scale), 0);
    }

    if (is_stock_row != 0) {
        return;
    }

    if (is_empty_mode != 0) {
        UiSprite_DrawNode(2, 0x1A, 0x522, x_offset + row_node->x, y_offset + row_node->y, 0xC4);
        const UiLayoutNode* lv_node = LayoutNode(0x1A, 0x52A);
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

    const UiLayoutNode* ord_node = LayoutNode(0x1A, 0x429);
    UiFont_DrawFormatted(0, x_offset + row_node->x + ord_node->x,
                         y_offset + row_node->y + ord_node->y,
                         1, 4, 0xC9, "%d", order_num);
}
#endif

// DECOMP_FUNC(0x0029adf0, 320)
void StatusDown_DrawLRPrompts(s32 x_offset, s32 y_offset) {
    auto* work = g_StatusDownWork;
    if (!Camp_CanShowLRPrompts()) {
        return;
    }
    u32 left = work->lr_state_left;
    if (left == 1 || left == 2) {
        UiSprite_DrawNode(2, 0x1A, 0x4D5, x_offset, y_offset, 0xBA);
        UiSprite_DrawNode(2, 0x1A, 0x4D9, x_offset, y_offset, 0xBA);
    } else {
        UiSprite_DrawNode(2, 0x1A, 0x4D3, x_offset, y_offset, 0xBA);
        UiSprite_DrawNode(2, 0x1A, 0x4D7, x_offset, y_offset, 0xBA);
    }
    u32 right = work->lr_state_right;
    if (right == 1 || right == 2) {
        UiSprite_DrawNode(2, 0x1A, 0x4D4, x_offset, y_offset, 0xBA);
        UiSprite_DrawNode(2, 0x1A, 0x4D8, x_offset, y_offset, 0xBA);
    } else {
        UiSprite_DrawNode(2, 0x1A, 0x4D2, x_offset, y_offset, 0xBA);
        UiSprite_DrawNode(2, 0x1A, 0x4D6, x_offset, y_offset, 0xBA);
    }
}

// DECOMP_FUNC(0x0029bfec, 152)
void StatusDown_Close() {
    auto* work = g_StatusDownWork;
    if (work->state == 0) {
        return;
    }
    UiAnimSprite_SetAnim(&work->panel_sprites[0], 2, 0);
    work = g_StatusDownWork;
    work->state_timer = 0;
    u32 prev = work->state;
    work->state = 2;
    work->prev_state = prev;
    work->sub_state = 0;
    work->active_mode = 0;
    const u8 tr_count = static_cast<u8>(work->registered_touch_count);
    for (s32 i = 0; i < tr_count; ++i) {
        UiTouch_UnregisterLastRegion();
    }
    work->registered_touch_count = 0;
    AsdMem_FillBytes(work->slot_touch_handles, 0x29, 0xFFFFFFFF);
}

// DECOMP_FUNC(0x0029c6c4, 24)
void StatusDown_SetFlag412(u8 val) {
    // Preserve the target's absolute pointer-slot literal and null-guarded store.
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work != nullptr) {
        work->flag_412 = val;
    }
}

// DECOMP_FUNC(0x0029c70c, 32)
bool StatusDown_IsNotState1() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    return work->state != 1;
}

// DECOMP_FUNC(0x0029c72c, 32)
bool StatusDown_IsNotState2() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    return work->state != 2;
}

// DECOMP_FUNC(0x002cf4e0, 352)
void StatusDown_UpdateHelpMessage(s32 msg_index) {
    auto* work = g_StatusDownWork;
    if (work->active_sound_id < 0 && msg_index >= 0 && work->active_mode == 1) {
        const s32 menu_id = Status_GetMainMenuId();
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
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(StatusDownWork), 1));
        g_StatusDownWork = work;
    }

    AsdMem_Zero(work, sizeof(StatusDownWork));

    work->calc_task = AsdTask_CreateCalc("TMD CALC", 2, 0, 0,
                                         StatusDown_CalcTaskCallback, 0, 0);
    work->draw_task = AsdTask_CreateDraw("TMD DDRAW", 0xE7, 0, 0,
                                         StatusDown_DrawTaskCallback, 0, 0, work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(&work->sprite_group,
                            SpriteTableWord(g_StatusDownSpriteTable - 0xA8), 0x48,
                            SpriteTableWord(g_StatusDownSpriteTable - 0x60), 0x48,
                            SpriteTableWord(g_StatusDownSpriteTable - 0x18),
                            0x18, 0, 0,
                            SpriteTableWord(g_StatusDownSpriteTable), 0x134);

    UiAnimSprite_Setup(&work->panel_sprites[0], 0x1A, 0x3E8, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprites[0], 0, 0);

    UiAnimSprite_Setup(&work->panel_sprites[1], 0x1A, 0x3E8, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetLayer(&work->panel_sprites[1], 0);

    UiAnimSprite_Setup(&work->panel_sprites[2], 0x1A, 0x3E8, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetLayer(&work->panel_sprites[2], 1);

    UiAnimSprite_Setup(&work->panel_sprites[3], 0x1A, 0x3E8, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprites[3], 4, 0);

    UiAnimSprite_Setup(&work->panel_sprites[4], 0x1A, 0x3E8, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprites[4], 5, 0);

    UiAnimSprite_Setup(&work->panel_sprites[5], 0x1A, 0x3E8, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprites[5], 0, 0);

    UiAnimSprite_SetupEx(&work->panel_sprites[6], 0x1A, -1, 0x1C, &work->sprite_group, 0xC9, 1.0f);
    UiAnimSprite_SetLayer(&work->panel_sprites[6], 2);
    *reinterpret_cast<u16*>(&work->panel_sprites[6].raw[0x3A]) = 2;

    work->text_handle = AsdText_CreateDefault(0);
    AsdText_SetAlpha(work->text_handle, 0xFF);
    AsdText_SetColorAndScale(work->text_handle, 0, 0x646464FFu, 0.0f);

    camp_func_002c4450(work->slot_touch_handles, 0x29, -1);
    work->visibility_flag = 1;
}

//
void StatusDown_EnterState3_Alt_Decompiled() {
    StatusDownWork* work = g_StatusDownWork;
    if (work != nullptr) {
        const u32 prev = work->state;
        work->state = 3;
        work->prev_state = prev;
        work->sub_state = 0;
        work->state_timer = 0;
    }
}
// DECOMP_FUNC(0x002d9618, 36)
void StatusDown_EnterState3_Alt() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    work->state_timer = 0;
    u32 prev = work->state;
    work->state = 3;
    work->prev_state = prev;
}
// DECOMP_FUNC(0x002dc96c, 152)
s32 StatusDown_SkillSortByCostDesc(const void* a, const void* b) {
    const auto* ea = static_cast<const StatusDownListEntry*>(a);
    const auto* eb = static_cast<const StatusDownListEntry*>(b);
    const auto* sa = reinterpret_cast<const SkillTableEntry*>(camp_func_00257744(ea->value));
    const auto* sb = reinterpret_cast<const SkillTableEntry*>(camp_func_00257744(eb->value));
    s32 ca = func_00257678(sa->cost_raw);
    s32 cb = func_00257678(sb->cost_raw);
    s32 diff = cb - ca;
    if (diff != 0) {
        return diff;
    }
    const auto* ia = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(ea->id));
    const auto* ib = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(eb->id));
    diff = static_cast<s32>(ib->category) - static_cast<s32>(ia->category);
    if (diff != 0) {
        return diff;
    }
    diff = static_cast<s32>(ib->rarity) - static_cast<s32>(ia->rarity);
    if (diff != 0) {
        return diff;
    }
    return static_cast<s32>(ia->id) - static_cast<s32>(ib->id);
}

// DECOMP_FUNC(0x002e2f44, 408)
void StatusDown_UpdatePartySlotsAndDiff(const u16* ids, s32 count) {
    auto* work = g_StatusDownWork;
    u16 prev_ids[8];
    for (s32 i = 0; i < 8; ++i) {
        prev_ids[i] = work->party_ids[i];
    }
    for (s32 i = 0; i < 4; ++i) {
        reinterpret_cast<u32*>(work->new_party_flags)[i] = 0;
        reinterpret_cast<u32*>(work->party_ids)[i] = 0;
    }
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
    const auto* ea = static_cast<const StatusDownListEntry*>(a);
    const auto* eb = static_cast<const StatusDownListEntry*>(b);
    const auto* ia = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(ea->id));
    const auto* ib = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(eb->id));
    s32 diff = static_cast<s32>(ib->category) - static_cast<s32>(ia->category);
    if (diff != 0) {
        return diff;
    }
    diff = static_cast<s32>(ib->rarity) - static_cast<s32>(ia->rarity);
    if (diff != 0) {
        return diff;
    }
    return static_cast<s32>(ia->id) - static_cast<s32>(ib->id);
}
// DECOMP_FUNC(0x002e4584, 132)
s32 StatusDown_ItemSortByTypeDesc(const void* a, const void* b) {
    const auto* ea = static_cast<const StatusDownListEntry*>(a);
    const auto* eb = static_cast<const StatusDownListEntry*>(b);
    u16 va = ea->value;
    u16 vb = eb->value;
    if (va == 0) {
        return vb != 0 ? 1 : 0;
    }
    if (vb == 0) {
        return -1;
    }
    s32 diff = static_cast<s32>(vb) - static_cast<s32>(va);
    if (diff != 0) {
        return diff;
    }
    const auto* ia = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(ea->id));
    const auto* ib = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(eb->id));
    diff = static_cast<s32>(ib->category) - static_cast<s32>(ia->category);
    if (diff != 0) {
        return diff;
    }
    diff = static_cast<s32>(ia->rarity) - static_cast<s32>(ib->rarity);
    if (diff != 0) {
        return diff;
    }
    return static_cast<s32>(ib->id) - static_cast<s32>(ia->id);
}
// DECOMP_FUNC(0x002e4608, 124)
s32 StatusDown_ItemSortByIdDesc(const void* a, const void* b) {
    const auto* ea = static_cast<const StatusDownListEntry*>(a);
    const auto* eb = static_cast<const StatusDownListEntry*>(b);
    u16 va = ea->value;
    u16 vb = eb->value;
    if (va == 0) {
        return vb != 0 ? 1 : 0;
    }
    if (vb == 0) {
        return -1;
    }
    const auto* ia = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(ea->id));
    const auto* ib = reinterpret_cast<const ItemTableEntry*>(camp_func_002b9364(eb->id));
    s32 diff = static_cast<s32>(ib->category) - static_cast<s32>(ia->category);
    if (diff != 0) {
        return diff;
    }
    diff = static_cast<s32>(ia->rarity) - static_cast<s32>(ib->rarity);
    if (diff != 0) {
        return diff;
    }
    return static_cast<s32>(ib->id) - static_cast<s32>(ia->id);
}

// DECOMP_FUNC(0x002efde0, 44)
s32 StatusDown_GetPartyMaxIndex() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work == nullptr) {
        return 0;
    }
    return camp_func_0029f0f4(&work->list_cursor_main) - 1;
}

// DECOMP_FUNC(0x002efe0c, 32)
bool StatusDown_IsNotState4() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    return work->state != 4;
}

// DECOMP_FUNC(0x002efe2c, 28)
s8 StatusDown_GetField2388() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work == nullptr) {
        return 0;
    }
    return work->field_2388;
}

// DECOMP_FUNC(0x002efe48, 68)
void StatusDown_SetSubIdsB(const u16* ids, s32 count) {
    if (count > 8) {
        return;
    }
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    for (int i = 0; i < 8; i++) {
        work->sub_ids_b[i] = 0;
    }
    AsdMem_Copy(work->sub_ids_b, ids, count * sizeof(u16));
}

// DECOMP_FUNC(0x002efe8c, 24)
void StatusDown_SetFlag411(u8 val) {
    // Preserve the target's absolute pointer-slot literal and null-guarded store.
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work != nullptr) {
        work->flag_411 = val;
    }
}

//
void StatusDown_EnterState4_Decompiled() {
    StatusDownWork* work = g_StatusDownWork;
    if (work != nullptr) {
        const u32 prev = work->state;
        work->state = 4;
        work->prev_state = prev;
        work->sub_state = 0;
        work->state_timer = 0;
    }
}
// DECOMP_FUNC(0x002efea4, 36)
void StatusDown_EnterState4() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    work->state_timer = 0;
    u32 prev = work->state;
    work->state = 4;
    work->prev_state = prev;
    StatusDown_SetupTouchRegions();
}

// DECOMP_FUNC(0x002f6524, 44)
bool StatusDown_IsState7() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work == nullptr) {
        return false;
    }
    return work->state == 7;
}

// DECOMP_FUNC(0x002f6550, 132)
void StatusDown_Destroy() {
    auto* work = g_StatusDownWork;
    const u8 tr_count = static_cast<u8>(work->registered_touch_count);
    for (s32 i = 0; i < tr_count; ++i) {
        UiTouch_UnregisterLastRegion();
    }
    work->registered_touch_count = 0;
    AsdMem_FillBytes(work->slot_touch_handles, 0x29, 0xFFFFFFFF);
    AsdText_DestroyHandle(work->text_handle);
    AsdTask_DestroyPair(work->calc_task, 0);
    AsdMem_FreeWork(work);
    g_StatusDownWork = nullptr;
}


// DECOMP_FUNC(0x002f65d4, 76)
bool StatusDown_IsCursorAtLastPartySlot() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work == nullptr) {
        return false;
    }
    s32 cur = camp_func_0029f248(&work->list_cursor_main);
    s32 max = camp_func_0029f0f4(&work->list_cursor_main) - 1;
    return cur == max;
}

// DECOMP_FUNC(0x002f6620, 200)
void StatusDown_SelectLastPartySlotAndEnterState11(s32 a0, u32 a1) {
    auto* work = g_StatusDownWork;
    work->selected_result = a0;
    work->callback_arg1 = a1;
    s32 count = UiListCursor_GetRowCount(&work->list_cursor_main);
    UiListCursor_Setup(&work->list_cursor_main, count + 1, 9, 1, 0, 1);
    s32 new_count = UiListCursor_GetRowCount(&work->list_cursor_main);
    UiListCursor_SetSelectedRow(&work->list_cursor_main, new_count - 1);
    work->needs_refresh = 1;
    work = g_StatusDownWork;
    const u8 tr_count = static_cast<u8>(work->registered_touch_count);
    for (s32 i = 0; i < tr_count; ++i) {
        UiTouch_UnregisterLastRegion();
    }
    work->registered_touch_count = 0;
    AsdMem_FillBytes(work->slot_touch_handles, 0x29, 0xFFFFFFFF);
    work = g_StatusDownWork;
    work->state_timer = 0;
    u32 prev = work->state;
    work->state = 0x0B;
    work->prev_state = prev;
    StatusDown_SetupTouchRegions();
}

//
void StatusDown_EnterState3_Decompiled() {
    StatusDownWork* work = g_StatusDownWork;
    if (work != nullptr) {
        const u32 prev = work->state;
        work->state = 3;
        work->prev_state = prev;
        work->sub_state = 0;
        work->state_timer = 0;
    }
}
// DECOMP_FUNC(0x002f66e8, 36)
void StatusDown_EnterState3() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    work->state_timer = 0;
    u32 prev = work->state;
    work->state = 3;
    work->prev_state = prev;
}

//
void StatusDown_EnterState6_Simple_Decompiled() {
    StatusDownWork* work = g_StatusDownWork;
    if (work != nullptr) {
        const u32 prev = work->state;
        work->state = 6;
        work->prev_state = prev;
        work->sub_state = 0;
        work->state_timer = 0;
    }
}
// DECOMP_FUNC(0x0030aa98, 40)
void StatusDown_EnterState6_Simple() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work != nullptr) {
        u32 prev = work->state;
        work->state = 6;
        work->prev_state = prev;
    }
}

// DECOMP_FUNC(0x0030aac0, 32)
bool StatusDown_IsState15() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    return work->state == 0xF;
}

// DECOMP_FUNC(0x0030aae0, 32)
bool StatusDown_IsState10() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    return work->state == 0xA;
}

//
void StatusDown_EnterState14_Decompiled(s32 selected_result) {
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
// DECOMP_FUNC(0x0030ab00, 52)
void StatusDown_EnterState14(s32 selected_result) {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (selected_result == 0) {
        work->selected_result = -1;
    }
    work->state_timer = 0;
    u32 prev = work->state;
    work->state = 0xE;
    work->prev_state = prev;
}

// DECOMP_FUNC(0x0030ab34, 60)
void StatusDown_EnterState6() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    work->state_timer = 0;
    u32 prev = work->state;
    work->state = 6;
    work->prev_state = prev;
    StatusDown_SetupTouchRegions();
    work->request_close_flag = 0;
}

// DECOMP_FUNC(0x00311494, 356)
void StatusDown_OpenCategorySelect(u16 arg0, u8 flag_413) {
    auto* work = g_StatusDownWork;
    work->category_arg0 = arg0;
    work->flag_413 = flag_413;
    for (s32 i = 0; i < 4; ++i) {
        reinterpret_cast<u32*>(work->category_ids)[i] = 0;
    }

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

    auto* w = g_StatusDownWork;
    w->state_timer = 0;
    const u32 old_state = w->state;
    w->state = 1;
    w->prev_state = old_state;
}

//
void StatusDown_RequestClose_Decompiled() {
    StatusDownWork* work = g_StatusDownWork;
    if (work != nullptr && work->state != 0) {
        work->request_close_flag = 1;
    }
}
// DECOMP_FUNC(0x00317f80, 36)
void StatusDown_RequestClose() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work != nullptr) {
        work->request_close_flag = 1;
    }
}

// DECOMP_FUNC(0x0032303c, 40)
s32 StatusDown_GetSelectedPartyIndex() {
    auto* work = *reinterpret_cast<StatusDownWork* volatile*>(0x0044E190);
    if (work == nullptr) {
        return -1;
    }
    return camp_func_0029f248(&work->list_cursor_main);
}

// DECOMP_FUNC(0x0032be34, 1672)
// Verified ARM-state entry/exit and referenced local literal/table bytes.
__attribute__((naked)) void StatusDown_DrawSkillList(s32 x_offset, s32 y_offset) {
    asm volatile(
        ".word 0xe92d4ff0\n"
        ".word 0xe1a05001\n"
        ".word 0xe1a08000\n"
        ".word 0xe59f03d8\n"
        ".word 0xed2d8b04\n"
        ".word 0xe24dd074\n"
        ".word 0xe5907000\n"
        ".word 0xed9f8af1\n"
        ".word 0xe2870b03\n"
        ".word 0xe2800f73\n"
        ".word 0xe1a04000\n"
        ".word 0xe58d0070\n"
        ".word 0xebfdccfd\n"
        ".word 0xe1a0b000\n"
        ".word 0xe1a00004\n"
        ".word 0xebfdccf4\n"
        ".word 0xe3a0a000\n"
        ".word 0xe58d000c\n"
        ".word 0xebfdbc2b\n"
        ".word 0xe350000d\n"
        ".word 0x0a000006\n"
        ".word 0xe3500006\n"
        ".word 0x1a000005\n"
        ".word 0xebfdbc2d\n"
        ".word 0xe1d000b0\n"
        ".word 0xebfdcb73\n"
        ".word 0xe3500000\n"
        ".word 0x1a000000\n"
        ".word 0xe3a0a001\n"
        ".word 0xe3a000b3\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a03008\n"
        ".word 0xe3a02005\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d5000\n"
        ".word 0xebfe4da3\n"
        ".word 0xe3a000b5\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a03008\n"
        ".word 0xe3a0200b\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d5000\n"
        ".word 0xebfe4d9b\n"
        ".word 0xe1a01005\n"
        ".word 0xe1a00008\n"
        ".word 0xebfdbbbe\n"
        ".word 0xeddf8aca\n"
        ".word 0xed9f9aca\n"
        ".word 0xe3a04000\n"
        ".word 0xe08b0004\n"
        ".word 0xe0870100\n"
        ".word 0xe2809c05\n"
        ".word 0xe1d90cba\n"
        ".word 0xe3500000\n"
        ".word 0x0a000068\n"
        ".word 0xe2841b01\n"
        ".word 0xe281104c\n"
        ".word 0xe3a0001a\n"
        ".word 0xebfe4de9\n"
        ".word 0xe1a06000\n"
        ".word 0xe59f12f8\n"
        ".word 0xe3a0001a\n"
        ".word 0xebfe4de5\n"
        ".word 0xe35a0000\n"
        ".word 0xe58d0000\n"
        ".word 0x0a00001a\n"
        ".word 0xe28f1fb9\n"
        ".word 0xe28d0030\n"
        ".word 0xfafe4a2a\n"
        ".word 0xe59d1000\n"
        ".word 0xe59d3000\n"
        ".word 0xe1d600fa\n"
        ".word 0xe1d620f8\n"
        ".word 0xe1d110fa\n"
        ".word 0xe1d330f8\n"
        ".word 0xeeb02a48\n"
        ".word 0xe0800001\n"
        ".word 0xe0821003\n"
        ".word 0xe0800005\n"
        ".word 0xe0811008\n"
        ".word 0xee000a90\n"
        ".word 0xee001a10\n"
        ".word 0xeef01a68\n"
        ".word 0xeeb01a49\n"
        ".word 0xe28d2030\n"
        ".word 0xe3a010ff\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xe3a00002\n"
        ".word 0xebfe49f5\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000018\n"
        ".word 0xe1d90cba\n"
        ".word 0xebfcfb65\n"
        ".word 0xe1b02000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000013\n"
        ".word 0xe59d1000\n"
        ".word 0xe59dc000\n"
        ".word 0xe1d600fa\n"
        ".word 0xe1d630f8\n"
        ".word 0xe1d110fa\n"
        ".word 0xe1dcc0f8\n"
        ".word 0xeeb02a48\n"
        ".word 0xe0800001\n"
        ".word 0xe083100c\n"
        ".word 0xe0800005\n"
        ".word 0xe0811008\n"
        ".word 0xee000a90\n"
        ".word 0xee001a10\n"
        ".word 0xeef01a68\n"
        ".word 0xeeb01a49\n"
        ".word 0xe3a010ff\n"
        ".word 0xe3a00002\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xebfe49d9\n"
        ".word 0xe59f121c\n"
        ".word 0xe3a0001a\n"
        ".word 0xebfe4dab\n"
        ".word 0xe3a01000\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d610fa\n"
        ".word 0xe35a0000\n"
        ".word 0x0a000009\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d630f8\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0811002\n"
        ".word 0xe0812005\n"
        ".word 0xe0800003\n"
        ".word 0xe0801008\n"
        ".word 0xe3a030b5\n"
        ".word 0xe3a00000\n"
        ".word 0xea000008\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d630f8\n"
        ".word 0xe1d0c0f8\n"
        ".word 0xe0811002\n"
        ".word 0xe0812005\n"
        ".word 0xe083300c\n"
        ".word 0xe0831008\n"
        ".word 0xe1d90cf8\n"
        ".word 0xe3a030b5\n"
        ".word 0xebfe2a84\n"
        ".word 0xe59f11b0\n"
        ".word 0xe3a0001a\n"
        ".word 0xebfe4d8f\n"
        ".word 0xe1d610fa\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d630f8\n"
        ".word 0xe1d0c0f8\n"
        ".word 0xe0811002\n"
        ".word 0xe0812005\n"
        ".word 0xe083300c\n"
        ".word 0xe0831008\n"
        ".word 0xe1d90cba\n"
        ".word 0xe3a030b5\n"
        ".word 0xebfed768\n"
        ".word 0xe2844001\n"
        ".word 0xe354000b\n"
        ".word 0xbaffff8d\n"
        ".word 0xe5970400\n"
        ".word 0xe2879b01\n"
        ".word 0xe3500011\n"
        ".word 0x1a0000ca\n"
        ".word 0xe59d000c\n"
        ".word 0xe080000b\n"
        ".word 0xe0870100\n"
        ".word 0xe2800c05\n"
        ".word 0xe58d0008\n"
        ".word 0xe1d00cba\n"
        ".word 0xe3500000\n"
        ".word 0x0a0000c2\n"
        ".word 0xe59d000c\n"
        ".word 0xe2801b01\n"
        ".word 0xe281102c\n"
        ".word 0xe3a0001a\n"
        ".word 0xebfe4d70\n"
        ".word 0xe1a04000\n"
        ".word 0xe28700b4\n"
        ".word 0xed900a08\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xebfe4d7a\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a010bf\n"
        ".word 0xe3a02008\n"
        ".word 0xe0800005\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a0101a\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xebfe4d02\n"
        ".word 0xeeb00a48\n"
        ".word 0xe320f000\n"
        ".word 0xebfe4d6d\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a060c4\n"
        ".word 0xe59f20d8\n"
        ".word 0xe0800005\n"
        ".word 0xe88d0041\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a0101a\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xebfe4cb7\n"
        ".word 0xe5970418\n"
        ".word 0xe3a02e42\n"
        ".word 0xe3500000\n"
        ".word 0x0597041c\n"
        ".word 0x03500000\n"
        ".word 0x1a000009\n"
        ".word 0xe5970420\n"
        ".word 0xe3500000\n"
        ".word 0x05970424\n"
        ".word 0x03500000\n"
        ".word 0x05970428\n"
        ".word 0x03500000\n"
        ".word 0x1a000002\n"
        ".word 0xe5970414\n"
        ".word 0xe3500000\n"
        ".word 0xa59f2080\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a0101a\n"
        ".word 0xe0800005\n"
        ".word 0xe88d0041\n"
        ".word 0xe1d400f8\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xebfe4c9f\n"
        ".word 0xe1d400fa\n"
        ".word 0xe59f205c\n"
        ".word 0xe3a0101a\n"
        ".word 0xe0800005\n"
        ".word 0xe88d0041\n"
        ".word 0xe1d400f8\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xebfe4c96\n"
        ".word 0xe3a01e42\n"
        ".word 0xe3a0001a\n"
        ".word 0xebfe4d2f\n"
        ".word 0xe1a0b000\n"
        ".word 0xe59f0030\n"
        ".word 0xea00000c\n"
        ".word 0x3f800000\n"
        ".word 0x0044e190\n"
        ".word 0x00000000\n"
        ".word 0x3e8f5c29\n"
        ".word 0x0000044b\n"
        ".word 0x48814881\n"
        ".word 0x00004881\n"
        ".word 0x00000449\n"
        ".word 0x0000044a\n"
        ".word 0x0000041f\n"
        ".word 0x00000421\n"
        ".word 0x00000457\n"
        ".word 0x0044ea00\n"
        ".word 0xe5901000\n"
        ".word 0xe3a00003\n"
        ".word 0xe2816a01\n"
        ".word 0xe2866fc3\n"
        ".word 0xe5961000\n"
        ".word 0xe0862101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d62018\n"
        ".word 0xe3520000\n"
        ".word 0x03510003\n"
        ".word 0x0a000003\n"
        ".word 0xe596101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c60018\n"
        ".word 0xe3a00001\n"
        ".word 0xe58d0000\n"
        ".word 0xe59b000c\n"
        ".word 0xe1dbc0fa\n"
        ".word 0xe1d410fa\n"
        ".word 0xe1dbb0f8\n"
        ".word 0xe1d460f8\n"
        ".word 0xe1d030f2\n"
        ".word 0xe1d020f0\n"
        ".word 0xe081100c\n"
        ".word 0xe086000b\n"
        ".word 0xe0811005\n"
        ".word 0xe0800008\n"
        ".word 0xebfdb853\n"
        ".word 0xe2870f73\n"
        ".word 0xe320f000\n"
        ".word 0xebfe4b26\n"
        ".word 0xe1d410fa\n"
        ".word 0xe0800005\n"
        ".word 0xe0806001\n"
        ".word 0xe2870f73\n"
        ".word 0xebfe4b24\n"
        ".word 0xe1d410f8\n"
        ".word 0xe0802008\n"
        ".word 0xe3a000c9\n"
        ".word 0xe0823001\n"
        ".word 0xe58d0004\n"
        ".word 0xe59f21a8\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d6000\n"
        ".word 0xebfe4c53\n"
        ".word 0xe51f00cc\n"
        ".word 0xe5901000\n"
        ".word 0xe3a00000\n"
        ".word 0xe2816a01\n"
        ".word 0xe2866fc3\n"
        ".word 0xe5961000\n"
        ".word 0xe0862101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d62018\n"
        ".word 0xe3520000\n"
        ".word 0x03510000\n"
        ".word 0x0a000003\n"
        ".word 0xe596101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c60018\n"
        ".word 0xe59f1154\n"
        ".word 0xe3a0001a\n"
        ".word 0xebfe4cdb\n"
        ".word 0xe3a01000\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d410fa\n"
        ".word 0xe35a0000\n"
        ".word 0x0a000009\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d430f8\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0811002\n"
        ".word 0xe0812005\n"
        ".word 0xe0800003\n"
        ".word 0xe0801008\n"
        ".word 0xe3a030c9\n"
        ".word 0xe3a00000\n"
        ".word 0xea000009\n"
        ".word 0xe1d030fa\n"
        ".word 0xe1d0c0f8\n"
        ".word 0xe1d420f8\n"
        ".word 0xe59d0008\n"
        ".word 0xe0833001\n"
        ".word 0xe082100c\n"
        ".word 0xe0832005\n"
        ".word 0xe1d00cf8\n"
        ".word 0xe0811008\n"
        ".word 0xe3a030c9\n"
        ".word 0xebfe29b3\n"
        ".word 0xe59f10e4\n"
        ".word 0xe3a0001a\n"
        ".word 0xebfe4cbe\n"
        ".word 0xe1d030fa\n"
        ".word 0xe1d410fa\n"
        ".word 0xe1d0c0f8\n"
        ".word 0xe1d420f8\n"
        ".word 0xe59d0008\n"
        ".word 0xe0833001\n"
        ".word 0xe082100c\n"
        ".word 0xe0832005\n"
        ".word 0xe1d00cba\n"
        ".word 0xe0811008\n"
        ".word 0xe3a030c9\n"
        ".word 0xebfed696\n"
        ".word 0xe59d0070\n"
        ".word 0xebfdcb39\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0xca000007\n"
        ".word 0xe3a000dd\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a03008\n"
        ".word 0xe3a0201b\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d5000\n"
        ".word 0xebfe4c47\n"
        ".word 0xe1d917f8\n"
        ".word 0xe1d907f6\n"
        ".word 0xe3a020c4\n"
        ".word 0xe28d6020\n"
        ".word 0xe3a03000\n"
        ".word 0xe59fc064\n"
        ".word 0xe886000f\n"
        ".word 0xe28da010\n"
        ".word 0xe1cc1142\n"
        ".word 0xe1d907f4\n"
        ".word 0xe1cc40c2\n"
        ".word 0xe1813441\n"
        ".word 0xe3a02b01\n"
        ".word 0xe58d3008\n"
        ".word 0xe2816003\n"
        ".word 0xe2817002\n"
        ".word 0xe58d200c\n"
        ".word 0xe58d001c\n"
        ".word 0xe58d6004\n"
        ".word 0xe58d7000\n"
        ".word 0xe88a1012\n"
        ".word 0xe3a0301a\n"
        ".word 0xe59d0070\n"
        ".word 0xe1a02005\n"
        ".word 0xe1a01008\n"
        ".word 0xebfd91e5\n"
        ".word 0xe28dd074\n"
        ".word 0xecbd8b04\n"
        ".word 0xe8bd8ff0\n"
        ".word 0x00000422\n"
        ".word 0x00000458\n"
        ".word 0x00000459\n"
        ".word 0x00000403\n"
    );
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void StatusDown_DrawSkillList_Draft(s32 x_offset, s32 y_offset) {
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

        const UiLayoutNode* row_node = LayoutNode(0x1A, static_cast<u32>(0x44C + row));
        const UiLayoutNode* name_node = LayoutNode(0x1A, 0x44B);

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

        const UiLayoutNode* icon_node = LayoutNode(0x1A, 0x449);
        const s32 item_id_arg = hide_names ? 0 : static_cast<s16>(entry.id);
        UiSkill_DrawItemIconAndCount(item_id_arg,
                                     x_offset + row_node->x + icon_node->x,
                                     y_offset + row_node->y + icon_node->y,
                                     0xB5, 0);

        const UiLayoutNode* cost_node = LayoutNode(0x1A, 0x44A);
        UiSkill_DrawSkillCostAndInfo(entry.value,
                                     x_offset + row_node->x + cost_node->x,
                                     y_offset + row_node->y + cost_node->y,
                                     0xB5);
    }

    if (work->state == 17) {
        const StatusDownListEntry& sel_entry = work->skill_entries[scroll_offset + selected_row];
        if (sel_entry.value != 0) {
            const UiLayoutNode* sel_node = LayoutNode(0x1A, static_cast<u32>(0x42C + selected_row));
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

            const UiLayoutNode* clip_node = LayoutNode(0x1A, 0x420);
            UiScissor_SetRect(x_offset + sel_node->x + clip_node->x,
                              y_offset + sel_node->y + clip_node->y,
                              clip_node->rect->w, clip_node->rect->h, 1);

            const s32 anim_y = UiAnimSprite_GetPosY(&work->panel_sprites[3]);
            const s32 anim_x = UiAnimSprite_GetPosX(&work->panel_sprites[3]);
            UiSprite_DrawNode(2, 0x1A, 0x422,
                              x_offset + anim_x + sel_node->x,
                              y_offset + anim_y + sel_node->y, 0xC9);

            const UiLayoutNode* icon_node = LayoutNode(0x1A, 0x458);
            const s32 item_id_arg = hide_names ? 0 : static_cast<s16>(sel_entry.id);
            UiSkill_DrawItemIconAndCount(item_id_arg,
                                         x_offset + sel_node->x + icon_node->x,
                                         y_offset + sel_node->y + icon_node->y,
                                         0xC9, 0);

            const UiLayoutNode* cost_node = LayoutNode(0x1A, 0x459);
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
#endif

// DECOMP_FUNC(0x0032c4bc, 372)
void StatusDown_SortItemList() {
    auto* work = g_StatusDownWork;
    const u8* sort_cfg = Camp_GetSortConfig();
    const u8 item_sort = sort_cfg[0x16];
    const u8 sort_key = item_sort & 0x7F;
    const bool desc = (item_sort >> 7) != 0;

    if (sort_key == 1) {
        qsort_arm(work->item_entries, work->item_count, sizeof(StatusDownListEntry),
                  desc ? StatusDown_ItemSortByIdDesc : StatusDown_ItemSortByIdAsc);
    } else if (sort_key == 8) {
        qsort_arm(work->item_entries, work->item_count, sizeof(StatusDownListEntry),
                  desc ? StatusDown_ItemSortByTypeDesc : StatusDown_ItemSortByTypeAsc);
    } else if (sort_key == 2) {
        qsort_arm(work->item_entries, work->item_count, sizeof(StatusDownListEntry),
                  desc ? ItemSort_ByCountDesc : ItemSort_ByCountAsc);
    } else if (sort_key == 3) {
        qsort_arm(work->item_entries, work->item_count, sizeof(StatusDownListEntry),
                  desc ? ItemSort_ByNameDesc : ItemSort_ByNameAsc);
    }
}

// DECOMP_FUNC(0x00187014, 5176)
__attribute__((naked, used)) void StatusDown_DrawPartyAndSubViews(s32, s32) {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x87014, 5176\n");
}
#if 0
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
#endif


// DECOMP_FUNC(0x001ca648, 8908)
__attribute__((naked, used)) void StatusDown_CalcTaskCallback(void*) {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0xca648, 8908\n");
}
#if 0
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
            // The original callback chooses the update mode from the panel
            // sprite's state word at +0x50: mode 1 when it is zero, mode 0
            // otherwise.  See the two paths at 0x001ca7a8-0x001ca804.
            const s16 sprite_state = *reinterpret_cast<const s16*>(
                work->panel_sprites[0].raw + 0x50);
            const bool anim_done = UiAnimSprite_UpdateCalc(
                &work->panel_sprites[0], sprite_state == 0 ? 1 : 0);
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
            const s8 sprite_anim_state = *reinterpret_cast<const s8*>(
                work->panel_sprites[0].raw + 0x8A);
            if (sprite_anim_state == 0 || work->sub_state == 0) {
                work->state_timer = 0;
                work->prev_state = work->state;
                work->state = 0;
                break;
            }

            // A live transition moves back to state 1 and selects the
            // animation from the sprite's +0x50 state word.  The ROM checks
            // these fields at 0x001ca818-0x001ca870.
            const s16 sprite_state = *reinterpret_cast<const s16*>(
                work->panel_sprites[0].raw + 0x50);
            UiAnimSprite_SetAnim(&work->panel_sprites[0],
                                sprite_state == 3 ? 0 : 1, 0);
            work->state_timer = 0;
            work->prev_state = work->state;
            work->state = 1;

            const s32 main_menu = Status_GetMainMenuId();
            const s32 transition = static_cast<s32>(work->sub_state);
            s32 sound_id = 0x27;
            const bool special_menu = main_menu == 13 || main_menu == 6;
            const bool menu_group = main_menu == 8 || main_menu == 9 ||
                                    main_menu == 11 || main_menu == 7;

            if (transition == 3 && special_menu) {
                sound_id = 0x2F;
            } else {
                if (Status_HandleLRPrompt() == 2) {
                    sound_id = 0x28;
                } else if (work->active_sound_id < 0) {
                    sound_id = 0x1F;
                }

                if (transition == 16) {
                    sound_id = 0x20;
                } else if (transition == 17) {
                    sound_id = menu_group ? 0x5E : 0x29;
                } else if (transition == 19) {
                    sound_id = menu_group ? 0x5F : 0x2A;
                } else if (transition == 21) {
                    sound_id = menu_group ? 0x60 : 0x2B;
                }
            }

            if (!(transition == 3 && menu_group)) {
                const u8 sub_menu = Status_GetSubMenuState();
                if (sub_menu != 5 && sub_menu != 6) {
                    Sound_PlaySE(sound_id);
                }
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
#endif


// DECOMP_FUNC(0x001cc914, 5348)
// Verified ARM-state entry/exit and referenced local literal/table bytes.
__attribute__((naked)) void StatusDown_DrawTaskCallback(void* arg) {
    asm volatile(
        ".word 0xe92d4ff0\n"
        ".word 0xe59f0490\n"
        ".word 0xed2d8b04\n"
        ".word 0xe24dd08c\n"
        ".word 0xe5904000\n"
        ".word 0xe2840028\n"
        ".word 0xeb03c992\n"
        ".word 0xe1a0a000\n"
        ".word 0xe2840028\n"
        ".word 0xeb03c98c\n"
        ".word 0xe5945400\n"
        ".word 0xe1a08000\n"
        ".word 0xe3550001\n"
        ".word 0x05945408\n"
        ".word 0x0a000001\n"
        ".word 0xe3550002\n"
        ".word 0x05945404\n"
        ".word 0xe355001c\n"
        ".word 0x379ff105\n"
        ".word 0xea00050c\n"
        ".word 0x001cdd98\n"
        ".word 0x001cdd98\n"
        ".word 0x001cdd98\n"
        ".word 0x001cc9d4\n"
        ".word 0x001cc9d4\n"
        ".word 0x001cc9d4\n"
        ".word 0x001cc9d4\n"
        ".word 0x001cc9d4\n"
        ".word 0x001cc9d4\n"
        ".word 0x001cc9d4\n"
        ".word 0x001cc9d4\n"
        ".word 0x001cc9d4\n"
        ".word 0x001cc9d4\n"
        ".word 0x001cc9d4\n"
        ".word 0x001cc9d4\n"
        ".word 0x001cc9d4\n"
        ".word 0x001cc9ec\n"
        ".word 0x001ccfd4\n"
        ".word 0x001ccfd4\n"
        ".word 0x001ccfec\n"
        ".word 0x001ccfec\n"
        ".word 0x001cd5d8\n"
        ".word 0x001cd874\n"
        ".word 0x001cd874\n"
        ".word 0x001cd874\n"
        ".word 0x001cd874\n"
        ".word 0x001cd874\n"
        ".word 0x001cd874\n"
        ".word 0xe1a01008\n"
        ".word 0xe1a0000a\n"
        ".word 0xebfee98c\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea0004ea\n"
        ".word 0xe59f03bc\n"
        ".word 0xeddf8aef\n"
        ".word 0xe3a07000\n"
        ".word 0xe5900000\n"
        ".word 0xeeb08a68\n"
        ".word 0xe58d0010\n"
        ".word 0xe2800b01\n"
        ".word 0xe2800f59\n"
        ".word 0xeb034a0d\n"
        ".word 0xe1a09000\n"
        ".word 0xe3a00000\n"
        ".word 0xe3a050b3\n"
        ".word 0xe58d000c\n"
        ".word 0xe58d0008\n"
        ".word 0xe1a0300a\n"
        ".word 0xe3a0200c\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03cac5\n"
        ".word 0xe3a040b5\n"
        ".word 0xe1a0300a\n"
        ".word 0xe0252185\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03ca7f\n"
        ".word 0xe59f2350\n"
        ".word 0xe1a0300a\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03ca78\n"
        ".word 0xe1a01008\n"
        ".word 0xe1a0000a\n"
        ".word 0xeb0338d9\n"
        ".word 0xe59d0010\n"
        ".word 0xeddf9aca\n"
        ".word 0xed9f9aca\n"
        ".word 0xe3a04000\n"
        ".word 0xe280bc05\n"
        ".word 0xe3540000\n"
        ".word 0xe3a06000\n"
        ".word 0x01db65b4\n"
        ".word 0x03a0703d\n"
        ".word 0x0a000022\n"
        ".word 0xe3540001\n"
        ".word 0x0a000011\n"
        ".word 0xe3540002\n"
        ".word 0x0a000017\n"
        ".word 0xe3540003\n"
        ".word 0x059f72f8\n"
        ".word 0x01db65ba\n"
        ".word 0x0a00001a\n"
        ".word 0xe3540004\n"
        ".word 0x059f72ec\n"
        ".word 0x01db65bc\n"
        ".word 0x0a000016\n"
        ".word 0xe3540005\n"
        ".word 0x059f72e0\n"
        ".word 0x01db65be\n"
        ".word 0x0a000012\n"
        ".word 0xe3540006\n"
        ".word 0x059f72d4\n"
        ".word 0x01db66b0\n"
        ".word 0xea00000e\n"
        ".word 0xe1db65b6\n"
        ".word 0xe3a070b5\n"
        ".word 0xe3a00e41\n"
        ".word 0xeb03d025\n"
        ".word 0xe3500000\n"
        ".word 0x03a04002\n"
        ".word 0x0affffdf\n"
        ".word 0xea000006\n"
        ".word 0xe59f72ac\n"
        ".word 0xe1db65b8\n"
        ".word 0xe3a00e41\n"
        ".word 0xeb03d01d\n"
        ".word 0xe3500000\n"
        ".word 0x03a04003\n"
        ".word 0x0affffd7\n"
        ".word 0xe2841b01\n"
        ".word 0xe2811066\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb03cae0\n"
        ".word 0xe1a05000\n"
        ".word 0xe1d000fa\n"
        ".word 0xe3a010b3\n"
        ".word 0xe3a0200d\n"
        ".word 0xe0800008\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d500f8\n"
        ".word 0xe3a0101a\n"
        ".word 0xe080300a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03ca77\n"
        ".word 0xe1540009\n"
        ".word 0xe59f1254\n"
        ".word 0xe3a0001a\n"
        ".word 0x058d600c\n"
        ".word 0x058d7008\n"
        ".word 0xeb03cacf\n"
        ".word 0xe3a01000\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d510fa\n"
        ".word 0xe1d530f8\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0811002\n"
        ".word 0xe0812008\n"
        ".word 0xe0800003\n"
        ".word 0xe080100a\n"
        ".word 0xe6bf0077\n"
        ".word 0xe3a030b5\n"
        ".word 0xeb03c660\n"
        ".word 0xe3560000\n"
        ".word 0xe320f000\n"
        ".word 0xda00001d\n"
        ".word 0xe59f1204\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb03cabc\n"
        ".word 0xe58d0000\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a00006\n"
        ".word 0xeb03c70e\n"
        ".word 0xe1b02000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000013\n"
        ".word 0xe59d1000\n"
        ".word 0xe59dc000\n"
        ".word 0xe1d500fa\n"
        ".word 0xe1d530f8\n"
        ".word 0xe1d110fa\n"
        ".word 0xe1dcc0f8\n"
        ".word 0xeeb02a68\n"
        ".word 0xe0800001\n"
        ".word 0xe083100c\n"
        ".word 0xe0800008\n"
        ".word 0xe081100a\n"
        ".word 0xee000a10\n"
        ".word 0xee011a10\n"
        ".word 0xeef01a69\n"
        ".word 0xe3a010ff\n"
        ".word 0xe3a00002\n"
        ".word 0xeef80ac0\n"
        ".word 0xeeb80ac1\n"
        ".word 0xeeb01a49\n"
        ".word 0xeb03c6cc\n"
        ".word 0xe2844001\n"
        ".word 0xe3540007\n"
        ".word 0xbaffff91\n"
        ".word 0xe59d0010\n"
        ".word 0xe5900400\n"
        ".word 0xe3500010\n"
        ".word 0x1a00044c\n"
        ".word 0xe3a00e41\n"
        ".word 0xeb03cfce\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a0000d2\n"
        ".word 0xe2891b01\n"
        ".word 0xe2811077\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb03ca91\n"
        ".word 0xe1a04000\n"
        ".word 0xe59d0010\n"
        ".word 0xe28000b4\n"
        ".word 0xed900a08\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb03ca9a\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a050bf\n"
        ".word 0xe59f212c\n"
        ".word 0xe0800008\n"
        ".word 0xe88d0021\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a0101a\n"
        ".word 0xe080300a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03c9e4\n"
        ".word 0xe1d400fa\n"
        ".word 0xe59f210c\n"
        ".word 0xe3a0101a\n"
        ".word 0xe0800008\n"
        ".word 0xe88d0021\n"
        ".word 0xe1d400f8\n"
        ".word 0xe080300a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03c9db\n"
        ".word 0xe1d400fa\n"
        ".word 0xe2852e3b\n"
        ".word 0xe3a0101a\n"
        ".word 0xe0800008\n"
        ".word 0xe88d0021\n"
        ".word 0xe1d400f8\n"
        ".word 0xe080300a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03c9d2\n"
        ".word 0xeeb00a68\n"
        ".word 0xe320f000\n"
        ".word 0xeb03ca7b\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a050c4\n"
        ".word 0xe3a02e47\n"
        ".word 0xe0800008\n"
        ".word 0xe88d0021\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a0101a\n"
        ".word 0xe080300a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03c9c5\n"
        ".word 0xe1d400fa\n"
        ".word 0xe59f6094\n"
        ".word 0xe3a0101a\n"
        ".word 0xe0800008\n"
        ".word 0xe88d0021\n"
        ".word 0xe1d400f8\n"
        ".word 0xe1a02006\n"
        ".word 0xe080300a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03c9bb\n"
        ".word 0xe1d400fa\n"
        ".word 0xe2852e3b\n"
        ".word 0xe3a0101a\n"
        ".word 0xe0800008\n"
        ".word 0xe88d0021\n"
        ".word 0xe1d400f8\n"
        ".word 0xe080300a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03c9b2\n"
        ".word 0xe1a01006\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb03ca4b\n"
        ".word 0xe1a06000\n"
        ".word 0xe59f7040\n"
        ".word 0xe3a00003\n"
        ".word 0xea00000f\n"
        ".word 0x0044e190\n"
        ".word 0x3f800000\n"
        ".word 0x0000052c\n"
        ".word 0x00000000\n"
        ".word 0x3e8f5c29\n"
        ".word 0x0000012d\n"
        ".word 0x000001a5\n"
        ".word 0x0000021d\n"
        ".word 0x00000295\n"
        ".word 0x0000030d\n"
        ".word 0x00000464\n"
        ".word 0x00000465\n"
        ".word 0x0000046d\n"
        ".word 0x0000046e\n"
        ".word 0x00000471\n"
        ".word 0x0044ea00\n"
        ".word 0xe5971000\n"
        ".word 0xe2815a01\n"
        ".word 0xe2855fc3\n"
        ".word 0xe5951000\n"
        ".word 0xe0852101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d52018\n"
        ".word 0xe3520000\n"
        ".word 0x03510003\n"
        ".word 0x0a000003\n"
        ".word 0xe595101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c50018\n"
        ".word 0xe3a00001\n"
        ".word 0xe58d0000\n"
        ".word 0xe596000c\n"
        ".word 0xe1d410fa\n"
        ".word 0xe1d630fa\n"
        ".word 0xe1d650f8\n"
        ".word 0xe1d4c0f8\n"
        ".word 0xe1d060f2\n"
        ".word 0xe1d020f0\n"
        ".word 0xe0810003\n"
        ".word 0xe08c3005\n"
        ".word 0xe0801008\n"
        ".word 0xe083000a\n"
        ".word 0xe1a03006\n"
        ".word 0xeb03356b\n"
        ".word 0xe59d0010\n"
        ".word 0xe2800f96\n"
        ".word 0xeb03c83e\n"
        ".word 0xe1d410fa\n"
        ".word 0xe0800008\n"
        ".word 0xe0805001\n"
        ".word 0xe59d0010\n"
        ".word 0xe2800f96\n"
        ".word 0xeb03c83b\n"
        ".word 0xe1d410f8\n"
        ".word 0xe080200a\n"
        ".word 0xe3a000c9\n"
        ".word 0xe0823001\n"
        ".word 0xe58d0004\n"
        ".word 0xe59f2404\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d5000\n"
        ".word 0xeb03c96a\n"
        ".word 0xe5970000\n"
        ".word 0xe3a01000\n"
        ".word 0xe2805a01\n"
        ".word 0xe2855fc3\n"
        ".word 0xe5950000\n"
        ".word 0xe0850100\n"
        ".word 0xe5902008\n"
        ".word 0xe5801008\n"
        ".word 0xe5d50018\n"
        ".word 0xe3500000\n"
        ".word 0x03520000\n"
        ".word 0x0a000004\n"
        ".word 0xe595201c\n"
        ".word 0xe1a00001\n"
        ".word 0xe12fff32\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c50018\n"
        ".word 0xe59d000c\n"
        ".word 0xe3500000\n"
        ".word 0xda00001b\n"
        ".word 0xe59f13a4\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb03c9ef\n"
        ".word 0xe1a05000\n"
        ".word 0xe59d000c\n"
        ".word 0xe3a01000\n"
        ".word 0xeb03c641\n"
        ".word 0xe1b02000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000011\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d410f8\n"
        ".word 0xe1d530fa\n"
        ".word 0xe1d5c0f8\n"
        ".word 0xeeb02a48\n"
        ".word 0xe0800003\n"
        ".word 0xe081100c\n"
        ".word 0xe0800008\n"
        ".word 0xe081100a\n"
        ".word 0xee000a90\n"
        ".word 0xee001a10\n"
        ".word 0xeef01a69\n"
        ".word 0xe3e01000\n"
        ".word 0xe3a00003\n"
        ".word 0xed9f1ad2\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeb03c601\n"
        ".word 0xe59f133c\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb03c9d3\n"
        ".word 0xe3a01000\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d030fa\n"
        ".word 0xe1d410fa\n"
        ".word 0xe1d420f8\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0811003\n"
        ".word 0xe3a030c9\n"
        ".word 0xe0800002\n"
        ".word 0xe0812008\n"
        ".word 0xe080100a\n"
        ".word 0xe59d0008\n"
        ".word 0xe6bf0070\n"
        ".word 0xeb03c563\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000374\n"
        ".word 0xe3590001\n"
        ".word 0x13590002\n"
        ".word 0x1affff29\n"
        ".word 0xea000370\n"
        ".word 0xe1a01008\n"
        ".word 0xe1a0000a\n"
        ".word 0xeb057b94\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea00036a\n"
        ".word 0xe51f0244\n"
        ".word 0xed1f8a91\n"
        ".word 0xe590b000\n"
        ".word 0xe28b0a02\n"
        ".word 0xe2800f8f\n"
        ".word 0xe1a05000\n"
        ".word 0xe58d0030\n"
        ".word 0xeb034894\n"
        ".word 0xe1a04000\n"
        ".word 0xe1a00005\n"
        ".word 0xeb03488b\n"
        ".word 0xe0844000\n"
        ".word 0xe1a00005\n"
        ".word 0xeb0346e0\n"
        ".word 0xe1a05000\n"
        ".word 0xe3a000b3\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a0300a\n"
        ".word 0xe3a02010\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03c943\n"
        ".word 0xe1a01008\n"
        ".word 0xe1a0000a\n"
        ".word 0xeb033766\n"
        ".word 0xe28b0c22\n"
        ".word 0xe58d0034\n"
        ".word 0xe1d003f2\n"
        ".word 0xe3500000\n"
        ".word 0xdd9f0a94\n"
        ".word 0xdb03c9a8\n"
        ".word 0xe28b0b01\n"
        ".word 0xe58d0010\n"
        ".word 0xe0850104\n"
        ".word 0xe3a07000\n"
        ".word 0xe58d0014\n"
        ".word 0xe3a05000\n"
        ".word 0xe59d0030\n"
        ".word 0xe0854107\n"
        ".word 0xeb034873\n"
        ".word 0xe1a01000\n"
        ".word 0xe59d0034\n"
        ".word 0xe0811007\n"
        ".word 0xe0856101\n"
        ".word 0xe1d003f0\n"
        ".word 0xe1560000\n"
        ".word 0xaa0000b1\n"
        ".word 0xe2841b01\n"
        ".word 0xe28110ae\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb03c984\n"
        ".word 0xe1a04000\n"
        ".word 0xe59b0400\n"
        ".word 0xe3500013\n"
        ".word 0x059d0014\n"
        ".word 0x01500006\n"
        ".word 0x1a00000d\n"
        ".word 0xe1d400fa\n"
        ".word 0xe59f21e0\n"
        ".word 0xe0801008\n"
        ".word 0xe3a000b5\n"
        ".word 0xe58d0004\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a0101a\n"
        ".word 0xe080300a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03c8d7\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000031\n"
        ".word 0xe51f0328\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe5909000\n"
        ".word 0xe3a00006\n"
        ".word 0xeb03e39f\n"
        ".word 0xe2899a01\n"
        ".word 0xe2899fab\n"
        ".word 0xe5991000\n"
        ".word 0xe0892101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d92018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe599101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c90018\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a010b5\n"
        ".word 0xe59f2158\n"
        ".word 0xe0800008\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a0101a\n"
        ".word 0xe080300a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03c8b6\n"
        ".word 0xe51f03a0\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe5909000\n"
        ".word 0xe3a00006\n"
        ".word 0xeb03e381\n"
        ".word 0xe2899a01\n"
        ".word 0xe2899fab\n"
        ".word 0xe5991000\n"
        ".word 0xe0892101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d92018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe599101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c90018\n"
        ".word 0xe08b0106\n"
        ".word 0xe2806c0e\n"
        ".word 0xe1d603b2\n"
        ".word 0xe3500000\n"
        ".word 0x0a00003a\n"
        ".word 0xe59f10d8\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb03c936\n"
        ".word 0xe3a01000\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d410fa\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d430f8\n"
        ".word 0xe1d0c0f8\n"
        ".word 0xe0811002\n"
        ".word 0xe0812008\n"
        ".word 0xe083300c\n"
        ".word 0xe083100a\n"
        ".word 0xe1d603f0\n"
        ".word 0xe3a030ba\n"
        ".word 0xeb03a61b\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a090ba\n"
        ".word 0xe2892ffb\n"
        ".word 0xe0800008\n"
        ".word 0xe88d0201\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a0101a\n"
        ".word 0xe080300a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03c883\n"
        ".word 0xe59f1074\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb03c91c\n"
        ".word 0xe1d613b2\n"
        ".word 0xe28f3068\n"
        ".word 0xe3a02006\n"
        ".word 0xe58d100c\n"
        ".word 0xe58d3008\n"
        ".word 0xe88d0204\n"
        ".word 0xe1d030fa\n"
        ".word 0xe1d410fa\n"
        ".word 0xe1d420f8\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0811003\n"
        ".word 0xe3a03001\n"
        ".word 0xe0800002\n"
        ".word 0xe0812008\n"
        ".word 0xe080100a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03c3b2\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea00002e\n"
        ".word 0x00000473\n"
        ".word 0x00000476\n"
        ".word 0x3e4ccccd\n"
        ".word 0x00000475\n"
        ".word 0x3f000000\n"
        ".word 0x000004a3\n"
        ".word 0x000004a2\n"
        ".word 0x000004a4\n"
        ".word 0x000004ad\n"
        ".word 0x00006425\n"
        ".word 0xe1d400fa\n"
        ".word 0xe3a060ba\n"
        ".word 0xe51f201c\n"
        ".word 0xe0800008\n"
        ".word 0xe88d0041\n"
        ".word 0xe1d400f8\n"
        ".word 0xe3a0101a\n"
        ".word 0xe080300a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03c858\n"
        ".word 0xe1d400fa\n"
        ".word 0xe2862ffb\n"
        ".word 0xe3a0101a\n"
        ".word 0xe0800008\n"
        ".word 0xe88d0041\n"
        ".word 0xe1d400f8\n"
        ".word 0xe080300a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03c84f\n"
        ".word 0xe51f105c\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb03c8e8\n"
        ".word 0xe28f2ff5\n"
        ".word 0xe3a01006\n"
        ".word 0xe58d2008\n"
        ".word 0xe88d0042\n"
        ".word 0xe1d030fa\n"
        ".word 0xe1d410fa\n"
        ".word 0xe1d420f8\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0811003\n"
        ".word 0xe3a03001\n"
        ".word 0xe0800002\n"
        ".word 0xe0812008\n"
        ".word 0xe080100a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03c380\n"
        ".word 0xe2855001\n"
        ".word 0xe3550004\n"
        ".word 0xbaffff43\n"
        ".word 0xe2877001\n"
        ".word 0xe3570009\n"
        ".word 0xbaffff3f\n"
        ".word 0xeeb00a48\n"
        ".word 0xeb03c8e1\n"
        ".word 0xe59b0400\n"
        ".word 0xe3500013\n"
        ".word 0x1a000046\n"
        ".word 0xe59d0034\n"
        ".word 0xe1d003f2\n"
        ".word 0xe3500000\n"
        ".word 0xda000042\n"
        ".word 0xe59d0030\n"
        ".word 0xeb0345fe\n"
        ".word 0xe1a04000\n"
        ".word 0xe59d0030\n"
        ".word 0xeb0347a3\n"
        ".word 0xe0840100\n"
        ".word 0xe2801b01\n"
        ".word 0xe28110ae\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb03c8c0\n"
        ".word 0xe1a05000\n"
        ".word 0xe28b0d05\n"
        ".word 0xed900a08\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb03c8ca\n"
        ".word 0xe51f6600\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe3a00006\n"
        ".word 0xe5964000\n"
        ".word 0xeb03e2e9\n"
        ".word 0xe2844a01\n"
        ".word 0xe2844fab\n"
        ".word 0xe5941000\n"
        ".word 0xe0842101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d42018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c40018\n"
        ".word 0xe1d500fa\n"
        ".word 0xe3a010c9\n"
        ".word 0xe59f22c8\n"
        ".word 0xe0800008\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d500f8\n"
        ".word 0xe3a0101a\n"
        ".word 0xe080300a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03c800\n"
        ".word 0xe5964000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe3a00006\n"
        ".word 0xeb03e2cc\n"
        ".word 0xe2844a01\n"
        ".word 0xe2844fab\n"
        ".word 0xe5941000\n"
        ".word 0xe0842101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d42018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c40018\n"
        ".word 0xeeb00a48\n"
        ".word 0xeb03c897\n"
        ".word 0xe59d0010\n"
        ".word 0xe3a020c4\n"
        ".word 0xe28d5020\n"
        ".word 0xe3a04000\n"
        ".word 0xe1d017f8\n"
        ".word 0xe1d007f6\n"
        ".word 0xe59f3240\n"
        ".word 0xe28d7010\n"
        ".word 0xe8850017\n"
        ".word 0xe1c31142\n"
        ".word 0xe1c3c0c2\n"
        ".word 0xe59d0010\n"
        ".word 0xe3a02b01\n"
        ".word 0xe1814441\n"
        ".word 0xe2815003\n"
        ".word 0xe1d007f4\n"
        ".word 0xe58d3018\n"
        ".word 0xe2816002\n"
        ".word 0xe58d200c\n"
        ".word 0xe58d001c\n"
        ".word 0xe58d4008\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d6000\n"
        ".word 0xe8871002\n"
        ".word 0xe3a0301a\n"
        ".word 0xe59d0030\n"
        ".word 0xe1a02008\n"
        ".word 0xe1a0100a\n"
        ".word 0xeb030dc4\n"
        ".word 0xe59d0034\n"
        ".word 0xe1d003f2\n"
        ".word 0xe3500000\n"
        ".word 0xca000218\n"
        ".word 0xe3a000dd\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a0300a\n"
        ".word 0xe3a0201b\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03c800\n"
        ".word 0xe2861d05\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb03c85b\n"
        ".word 0xe1a04000\n"
        ".word 0xe28f1f6a\n"
        ".word 0xe28d0008\n"
        ".word 0xfa03c4a2\n"
        ".word 0xe3a01002\n"
        ".word 0xe28d0008\n"
        ".word 0xeb03a6e6\n"
        ".word 0xe594200c\n"
        ".word 0xe1d410f8\n"
        ".word 0xeeb02a48\n"
        ".word 0xeddf1a70\n"
        ".word 0xe1d220f0\n"
        ".word 0xed9f1a6f\n"
        ".word 0xe0420000\n"
        ".word 0xe1d420fa\n"
        ".word 0xe0800fa0\n"
        ".word 0xe08110c0\n"
        ".word 0xe08a0001\n"
        ".word 0xe0821008\n"
        ".word 0xee000a10\n"
        ".word 0xee001a90\n"
        ".word 0xe28d2008\n"
        ".word 0xe3e01000\n"
        ".word 0xe3a00002\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeef80ae0\n"
        ".word 0xeb03c46b\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea0001ef\n"
        ".word 0xe51f0830\n"
        ".word 0xe3a040b3\n"
        ".word 0xed9f8a5c\n"
        ".word 0xe1a0300a\n"
        ".word 0xe5905000\n"
        ".word 0xe3a0200f\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03c7d4\n"
        ".word 0xe1a0300a\n"
        ".word 0xe3a0200e\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03c7cd\n"
        ".word 0xe1a01008\n"
        ".word 0xe1a0000a\n"
        ".word 0xeb0335f0\n"
        ".word 0xe2857b01\n"
        ".word 0xe1d707be\n"
        ".word 0xeb03af4a\n"
        ".word 0xe1b04000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000020\n"
        ".word 0xe5d40005\n"
        ".word 0xe3500001\n"
        ".word 0x1a000007\n"
        ".word 0xe3a000bf\n"
        ".word 0xe2802ff1\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a0300a\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03c77b\n"
        ".word 0xe5d40005\n"
        ".word 0xe3500005\n"
        ".word 0x1a000007\n"
        ".word 0xe3a000bf\n"
        ".word 0xe58d0004\n"
        ".word 0xe59f20d0\n"
        ".word 0xe1a0300a\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03c770\n"
        ".word 0xe5d40005\n"
        ".word 0xe3500004\n"
        ".word 0x1a000007\n"
        ".word 0xe3a000bf\n"
        ".word 0xe58d0004\n"
        ".word 0xe59f20a8\n"
        ".word 0xe1a0300a\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03c765\n"
        ".word 0xe3a04000\n"
        ".word 0xeb033617\n"
        ".word 0xe350000d\n"
        ".word 0xe320f000\n"
        ".word 0x0a000008\n"
        ".word 0xe3500006\n"
        ".word 0x1a00001f\n"
        ".word 0xeb033618\n"
        ".word 0xe1d000b0\n"
        ".word 0xe320f000\n"
        ".word 0xeb03455d\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a000018\n"
        ".word 0xe3a04001\n"
        ".word 0xea000016\n"
        ".word 0x00000030\n"
        ".word 0x000004a7\n"
        ".word 0x00000403\n"
        ".word 0x94826882\n"
        ".word 0x88824081\n"
        ".word 0x93828182\n"
        ".word 0x8e824081\n"
        ".word 0x94828f82\n"
        ".word 0x82824081\n"
        ".word 0x85828582\n"
        ".word 0x40818e82\n"
        ".word 0x95828682\n"
        ".word 0x85829382\n"
        ".word 0x40818482\n"
        ".word 0x85828282\n"
        ".word 0x8f828682\n"
        ".word 0x85829282\n"
        ".word 0x00004481\n"
        ".word 0x00000000\n"
        ".word 0x3e040000\n"
        ".word 0x3f800000\n"
        ".word 0x00000484\n"
        ".word 0x00000485\n"
        ".word 0xe1d707fe\n"
        ".word 0xe3500000\n"
        ".word 0xba000001\n"
        ".word 0xe3540000\n"
        ".word 0x0a00000a\n"
        ".word 0xe3a000bf\n"
        ".word 0xe58d0004\n"
        ".word 0xe59f2620\n"
        ".word 0xe1a0300a\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03c731\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea00017c\n"
        ".word 0xe285ba02\n"
        ".word 0xe3a09006\n"
        ".word 0xe28bbfaa\n"
        ".word 0xe2856a02\n"
        ".word 0xe2841b01\n"
        ".word 0xe281108d\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb03c7c2\n"
        ".word 0xe1a05000\n"
        ".word 0xe1a0000b\n"
        ".word 0xeb0346a3\n"
        ".word 0xe0800004\n"
        ".word 0xe58d0004\n"
        ".word 0xe58d9000\n"
        ".word 0xe1d520fa\n"
        ".word 0xe1d510f8\n"
        ".word 0xeeb00a48\n"
        ".word 0xe59602a0\n"
        ".word 0xe0822008\n"
        ".word 0xe081100a\n"
        ".word 0xe3a030b5\n"
        ".word 0xeb03a84b\n"
        ".word 0xe2844001\n"
        ".word 0xe3540008\n"
        ".word 0xbaffffea\n"
        ".word 0xe1d717f8\n"
        ".word 0xe1d707f6\n"
        ".word 0xe28d5020\n"
        ".word 0xe3a0c000\n"
        ".word 0xe3a040c4\n"
        ".word 0xe8851013\n"
        ".word 0xe28d9010\n"
        ".word 0xe59f2580\n"
        ".word 0xe1d707f4\n"
        ".word 0xe2421001\n"
        ".word 0xe58d001c\n"
        ".word 0xe58d2018\n"
        ".word 0xe2423002\n"
        ".word 0xe889000a\n"
        ".word 0xe241c002\n"
        ".word 0xe1816441\n"
        ".word 0xe2815003\n"
        ".word 0xe18144c1\n"
        ".word 0xe3a0301a\n"
        ".word 0xe1a02008\n"
        ".word 0xe1a0100a\n"
        ".word 0xe1a0000b\n"
        ".word 0xe88d1070\n"
        ".word 0xeb030cf3\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000148\n"
        ".word 0xe51f1acc\n"
        ".word 0xe3a000b3\n"
        ".word 0xe1a0300a\n"
        ".word 0xe3a02004\n"
        ".word 0xe5916000\n"
        ".word 0xe58d0004\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03c72e\n"
        ".word 0xe3a0b0b5\n"
        ".word 0xe1a0300a\n"
        ".word 0xe3a02017\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0900\n"
        ".word 0xeb03c727\n"
        ".word 0xe1a0300a\n"
        ".word 0xe3a02018\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0900\n"
        ".word 0xeb03c721\n"
        ".word 0xe2860a02\n"
        ".word 0xe2800fc3\n"
        ".word 0xe3a04000\n"
        ".word 0xe58d0010\n"
        ".word 0xe320f000\n"
        ".word 0xeb0274fd\n"
        ".word 0xe1500004\n"
        ".word 0xe320f000\n"
        ".word 0xca000009\n"
        ".word 0xe2842c05\n"
        ".word 0xe1a0300a\n"
        ".word 0xe282204b\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0900\n"
        ".word 0xeb03c6d3\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea00003a\n"
        ".word 0xe3550019\n"
        ".word 0x0a000006\n"
        ".word 0xe3550017\n"
        ".word 0xe3a09000\n"
        ".word 0xe3a070ff\n"
        ".word 0x0a000009\n"
        ".word 0xe355001a\n"
        ".word 0x0a000016\n"
        ".word 0xea000023\n"
        ".word 0xe59d0010\n"
        ".word 0xeb03463f\n"
        ".word 0xe1500004\n"
        ".word 0x13a09000\n"
        ".word 0x13a070ff\n"
        ".word 0x0a00002b\n"
        ".word 0xea00001c\n"
        ".word 0xe59d0010\n"
        ".word 0xeb034638\n"
        ".word 0xe1500004\n"
        ".word 0xe320f000\n"
        ".word 0x1a000017\n"
        ".word 0xe596040c\n"
        ".word 0xe3500008\n"
        ".word 0xd3e01027\n"
        ".word 0xd0090190\n"
        ".word 0xda000012\n"
        ".word 0xe2860fb9\n"
        ".word 0xeb03c57b\n"
        ".word 0xe59f741c\n"
        ".word 0xe1a09000\n"
        ".word 0xea00000d\n"
        ".word 0xe59d0010\n"
        ".word 0xeb034629\n"
        ".word 0xe1500004\n"
        ".word 0xe320f000\n"
        ".word 0x1a000008\n"
        ".word 0xe596040c\n"
        ".word 0xe3500008\n"
        ".word 0xd3e01027\n"
        ".word 0xd0090190\n"
        ".word 0xda000002\n"
        ".word 0xe2860fb9\n"
        ".word 0xeb03c56c\n"
        ".word 0xe1a09000\n"
        ".word 0xe59f73dc\n"
        ".word 0xe0860084\n"
        ".word 0xe2800c23\n"
        ".word 0xe3a02000\n"
        ".word 0xe1d007b0\n"
        ".word 0xe3500000\n"
        ".word 0x0a000001\n"
        ".word 0xeb02edb8\n"
        ".word 0xe1a02000\n"
        ".word 0xe2843b01\n"
        ".word 0xe08a0009\n"
        ".word 0xe2833014\n"
        ".word 0xe1a01008\n"
        ".word 0xe58d7000\n"
        ".word 0xeb00dcd8\n"
        ".word 0xe2844001\n"
        ".word 0xe3540008\n"
        ".word 0xbaffffb2\n"
        ".word 0xe3550018\n"
        ".word 0x1355001b\n"
        ".word 0x0a00002a\n"
        ".word 0xe3550016\n"
        ".word 0x13550017\n"
        ".word 0x1355001a\n"
        ".word 0x0a000007\n"
        ".word 0xe59d0010\n"
        ".word 0xeb034603\n"
        ".word 0xe1a04000\n"
        ".word 0xe59d0010\n"
        ".word 0xeb0345ab\n"
        ".word 0xe2400001\n"
        ".word 0xe1540000\n"
        ".word 0x0a000072\n"
        ".word 0xe3a00d8e\n"
        ".word 0xe19000b6\n"
        ".word 0xeb02ed9c\n"
        ".word 0xe3a070b3\n"
        ".word 0xe1a04000\n"
        ".word 0xe1a0300a\n"
        ".word 0xe2872e43\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d7004\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03c677\n"
        ".word 0xe59f232c\n"
        ".word 0xe1a0300a\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d7004\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03c670\n"
        ".word 0xe1a0300a\n"
        ".word 0xe0672187\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d7004\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03c669\n"
        ".word 0xe3550017\n"
        ".word 0x1355001a\n"
        ".word 0xe3a00000\n"
        ".word 0x1a000033\n"
        ".word 0xea00002f\n"
        ".word 0xe3a040b3\n"
        ".word 0xe1a0300a\n"
        ".word 0xe2842e43\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03c65c\n"
        ".word 0xe59f22c0\n"
        ".word 0xe1a0300a\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03c655\n"
        ".word 0xe1a0300a\n"
        ".word 0xe0642184\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d4004\n"
        ".word 0xe58d8000\n"
        ".word 0xeb03c64e\n"
        ".word 0xe59f128c\n"
        ".word 0xe3a0001a\n"
        ".word 0xeb03c6e7\n"
        ".word 0xe1a04000\n"
        ".word 0xe28f1d0a\n"
        ".word 0xe28d0018\n"
        ".word 0xfa03c32e\n"
        ".word 0xe1d400fa\n"
        ".word 0xe1d410f8\n"
        ".word 0xe28d2018\n"
        ".word 0xe0800008\n"
        ".word 0xe081100a\n"
        ".word 0xee000a90\n"
        ".word 0xee001a10\n"
        ".word 0xe59f1280\n"
        ".word 0xed9f2a9e\n"
        ".word 0xeddf1a9f\n"
        ".word 0xe3a00002\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xed9f1a9c\n"
        ".word 0xeb03c2ff\n"
        ".word 0xe3550018\n"
        ".word 0x1355001b\n"
        ".word 0x0a00000d\n"
        ".word 0xea000023\n"
        ".word 0xe596040c\n"
        ".word 0xe3e01027\n"
        ".word 0xe0000190\n"
        ".word 0xe3a010ff\n"
        ".word 0xe58d1000\n"
        ".word 0xe59f3248\n"
        ".word 0xe080000a\n"
        ".word 0xe1a02004\n"
        ".word 0xe1a01008\n"
        ".word 0xeb00dc6d\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000016\n"
        ".word 0xe59d0010\n"
        ".word 0xeb03459f\n"
        ".word 0xe1a04000\n"
        ".word 0xe3a01000\n"
        ".word 0xe0860084\n"
        ".word 0xe2800c23\n"
        ".word 0xe1d007b0\n"
        ".word 0xe3500000\n"
        ".word 0x0a000001\n"
        ".word 0xeb02ed39\n"
        ".word 0xe1a01000\n"
        ".word 0xe3a00000\n"
        ".word 0xe28d3004\n"
        ".word 0xe3a02001\n"
        ".word 0xe58d0000\n"
        ".word 0xe8830005\n"
        ".word 0xe6ff2071\n"
        ".word 0xe2843b01\n"
        ".word 0xe58d000c\n"
        ".word 0xe283302c\n"
        ".word 0xe1a01008\n"
        ".word 0xe1a0000a\n"
        ".word 0xeb033240\n"
        ".word 0xe3550019\n"
        ".word 0x0a000003\n"
        ".word 0xe3550017\n"
        ".word 0x1355001a\n"
        ".word 0x0a000030\n"
        ".word 0xea000058\n"
        ".word 0xe59d0010\n"
        ".word 0xeb034582\n"
        ".word 0xe1a04000\n"
        ".word 0xe59d0010\n"
        ".word 0xeb03452a\n"
        ".word 0xe2400001\n"
        ".word 0xe1500004\n"
        ".word 0x1a000010\n"
        ".word 0xe3a00d8e\n"
        ".word 0xe19000b6\n"
        ".word 0xeb02ed1b\n"
        ".word 0xe3a01000\n"
        ".word 0xe28d3004\n"
        ".word 0xe3a02001\n"
        ".word 0xe58d1000\n"
        ".word 0xe8830006\n"
        ".word 0xe1a02000\n"
        ".word 0xe58d100c\n"
        ".word 0xe59f3170\n"
        ".word 0xe1a01008\n"
        ".word 0xe1a0000a\n"
        ".word 0xeb033224\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea00003f\n"
        ".word 0xe0860084\n"
        ".word 0xe2800c23\n"
        ".word 0xe3a01000\n"
        ".word 0xe1d007b0\n"
        ".word 0xe3500000\n"
        ".word 0x0a000001\n"
        ".word 0xeb02ed06\n"
        ".word 0xe1a01000\n"
        ".word 0xe3a00000\n"
        ".word 0xe28d3004\n"
        ".word 0xe3a02001\n"
        ".word 0xe58d0000\n"
        ".word 0xe8830005\n"
        ".word 0xe6ff2071\n"
        ".word 0xe2843b01\n"
        ".word 0xe58d000c\n"
        ".word 0xe283302c\n"
        ".word 0xe1a01008\n"
        ".word 0xe1a0000a\n"
        ".word 0xeb03320d\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000028\n"
        ".word 0xe51f5f10\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe3a00006\n"
        ".word 0xe5954000\n"
        ".word 0xeb03e0a5\n"
        ".word 0xe2844a01\n"
        ".word 0xe2844fab\n"
        ".word 0xe5941000\n"
        ".word 0xe0842101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d42018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c40018\n"
        ".word 0xe2860e37\n"
        ".word 0xeb0331ed\n"
        ".word 0xe5954000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe3a00006\n"
        ".word 0xeb03e090\n"
        ".word 0xe2844a01\n"
        ".word 0xe2844fab\n"
        ".word 0xe5941000\n"
        ".word 0xe0842101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d42018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c40018\n"
        ".word 0xe28dd08c\n"
        ".word 0xe3a00000\n"
        ".word 0xecbd8b04\n"
        ".word 0xe8bd8ff0\n"
        ".word 0x00000545\n"
        ".word 0x00000489\n"
        ".word 0x008400ff\n"
        ".word 0x000004e4\n"
        ".word 0x000004e6\n"
        ".word 0x8c826082\n"
        ".word 0x85829282\n"
        ".word 0x84828182\n"
        ".word 0x40819982\n"
        ".word 0x82828f82\n"
        ".word 0x81829482\n"
        ".word 0x8e828982\n"
        ".word 0x84828582\n"
        ".word 0x00004481\n"
        ".word 0x3f800000\n"
        ".word 0x323232ff\n"
        ".word 0x00000000\n"
        ".word 0x3e960000\n"
        ".word 0x0000054a\n"
        ".word 0x00000435\n"
    );
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void StatusDown_DrawTaskCallback_Draft(void* arg) {
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
                const UiLayoutNode* node = LayoutNode(0x1A, node_id);
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
            const UiLayoutNode* node = LayoutNode(0x1A, node_id);
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
#endif

} // namespace smt4::ui
