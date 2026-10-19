#include "ui/status_down.h"
#include <cstring>

namespace smt4::ui {

StatusDownWork* g_StatusDownWork = nullptr; // 0x0044E190

// External engine / AsdSDK / UI helper routines referenced by StatusDown.cpp
extern "C" {
    void* AsdMem_AllocZeroed(u32 size, s32 align, const char* file, s32 line);      // 0x002cc860
    void  AsdMem_Free(void* ptr);                                                    // 0x00175c08
    void* AsdTask_Create(void (*cb)(void*), void* arg, const char* name, u32 prio, u32 flags); // 0x002cb270
    void  AsdTask_Destroy(void* task);                                               // 0x002caef4
    void* AsdText_Create(u32 capacity);                                              // 0x002c8600
    void  AsdText_Destroy(void* text_handle);                                        // 0x002c9524

    void  UiSpriteGroup_Init(void* group, const void* table, u32 count);             // 0x002c3344
    bool  UiSpriteGroup_BindTable(void* group, const void* table, u32 count);        // 0x002c32f8
    bool  UiSpriteGroup_IsReady(const void* group);                                  // 0x001cccd0
    void* UiSpriteGroup_GetResource(void* group, s32 index);                         // 0x002c6c34
    void  UiSpriteGroup_Release(void* group);                                        // 0x002c31e8

    void  UiAnimSprite_Init(UiAnimSprite* sprite);                                   // 0x001cc310
    void  UiAnimSprite_BindResource(UiAnimSprite* sprite, void* res, const char* name, s32 mode); // 0x002c6c5c
    void  UiAnimSprite_Update(UiAnimSprite* sprite);                                 // 0x002c5ed0
    void  UiAnimSprite_Draw(UiAnimSprite* sprite, f32 x, f32 y);                     // 0x002c6018
    bool  UiAnimSprite_IsAnimFinished(const UiAnimSprite* sprite);                   // 0x001cc3a8
    void  UiAnimSprite_SetAnimIndex(UiAnimSprite* sprite, s32 anim_idx, s32 loop_mode); // 0x002c5ec8
    void  UiAnimSprite_SetLayerOrder(UiAnimSprite* sprite, u32 layer);               // 0x001cc3c8

    void  UiListCursor_Init(UiListCursor* cursor);                                   // 0x0029fae8
    void  UiListCursor_SetPosition(UiListCursor* cursor, u32 x, u32 y);              // 0x0029f0f4
    void  UiListCursor_SetTextArgs(UiListCursor* cursor, void* text_handle, s32 msg_id, u32 a3, u32 a4); // 0x0029f248
    void  UiListCursor_SetSelection(UiListCursor* cursor, s32 index, s32 count);     // 0x0029edfc

    void  StatusDown_FillHalfwords(s16* dst, u32 count, s32 value);                  // 0x002c4450
    void  StatusDown_InitSubPanels(StatusDownWork* work);                            // 0x001cc93c
    void  StatusDown_ClearPortraits(StatusDownWork* work);                           // 0x001cd308
    void  StatusDown_LoadDefaultParty(StatusDownWork* work);                         // 0x001cce88
    void  StatusDown_RefreshModeAssets(StatusDownWork* work, s32 mode);              // 0x001ccc58
    void  StatusDown_CalcTaskCallback(void* arg);                                    // 0x001ca648
    void  StatusDown_DrawTaskCallback(void* arg);                                    // 0x001cc914

    s32   Party_GetActiveSlotOrder(u16* out_slots);                                  // 0x002f6848
    bool  Party_IsDemonValid(u16 demon_id);                                          // 0x002b285c
    bool  SubScreen_IsBlocked();                                                     // 0x002efec8

    extern const u8 g_StatusDownSpriteTable[];                                       // 0x00407d58
    extern const s32 g_StatusDownHelpMsgIds[4];                                      // 0x00407d78
}

// DECOMP_FUNC(0x001ddab4, 68)
void StatusDown_OpenDefaultView() {
    StatusDown_Init(0);
    StatusDownWork* work = g_StatusDownWork;
    if (work != nullptr && work->state == 0) {
        work->state = 1;
        work->prev_state = 0;
        work->sub_state = 0;
        work->state_timer = 0;
        StatusDown_LoadDefaultParty(work);
    }
    StatusDown_SetDisplayMode(0);
}

// DECOMP_FUNC(0x00215990, 180)
void StatusDown_SetPartyPrompt(u32 a0, u32 a1, u32 a2, u16 a3) {
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        return;
    }

    work->prompt_field0 = a0;
    work->prompt_field1 = a1;
    work->prompt_field2 = a2;
    work->prompt_field3 = a3;

    UiListCursor_SetPosition(&work->list_cursor_prompt, 4, 0xAC);
    UiListCursor_SetTextArgs(&work->list_cursor_prompt, work->text_handle, 0xCF, 0, 0);

    u16 active_slots[12]{};
    const s32 count = Party_GetActiveSlotOrder(active_slots);
    for (s32 i = 0; i < count; ++i) {
        if (active_slots[i] == 0) {
            UiListCursor_SetSelection(&work->list_cursor_main, i, count);
            break;
        }
    }
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
    if (work == nullptr) {
        return;
    }

    if (work->state == 0) {
        work->state = 1;
        work->prev_state = 0;
        work->sub_state = 0;
        work->state_timer = 0;
    }

    work->needs_refresh = 1;
    work->flag_548 = 0;

    std::memset(work->party_ids, 0, sizeof(work->party_ids));
    std::memset(work->new_party_flags, 0, sizeof(work->new_party_flags));

    for (s32 i = 0; i < count; ++i) {
        work->party_ids[i] = ids[i];
    }

    StatusDown_FillHalfwords(work->slot_table, 0x29, -1);
    work->loaded_icon_count = 0;
    StatusDown_ClearPortraits(work);
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
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        return;
    }

    work->has_sub_ids_a = 1;
    std::memset(work->sub_ids_a, 0, sizeof(work->sub_ids_a));
    for (s32 i = 0; i < count; ++i) {
        work->sub_ids_a[i] = ids[i];
    }
}

// DECOMP_FUNC(0x0026b01c, 176)
u16 StatusDown_PopFirstSubIdA() {
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        return 0;
    }

    const u16 popped = work->sub_ids_a[0];
    if (popped != 0) {
        u16 shifted[8]{};
        for (s32 i = 0; i < 7; ++i) {
            shifted[i] = work->sub_ids_a[i + 1];
        }
        std::memcpy(work->sub_ids_a, shifted, sizeof(work->sub_ids_a));
        std::memcpy(work->sub_ids_b, shifted, sizeof(work->sub_ids_b));
        work->needs_refresh = 1;
    }
    return popped;
}

// DECOMP_FUNC(0x0026d8c0, 28)
void StatusDown_SetVisibility(u8 visible) {
    if (g_StatusDownWork != nullptr) {
        g_StatusDownWork->visibility_flag = visible;
    }
}

// DECOMP_FUNC(0x00288718, 92)
bool StatusDown_CanOpenSubScreen() {
    if (SubScreen_IsBlocked()) {
        return false;
    }
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        return false;
    }
    const u32 st = work->state;
    if (st != 2 && st != 8 && st != 0) {
        return false;
    }
    return UiSpriteGroup_IsReady(&work->sprite_group);
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
    if (work == nullptr) {
        return;
    }

    work->prev_active_mode = work->active_mode;
    StatusDown_RefreshModeAssets(work, mode);

    if (mode == 0) {
        work->active_mode = 0;
        UiAnimSprite_SetAnimIndex(&work->panel_sprites[0], 0, 1);
    } else if (mode == 1) {
        work->active_mode = 1;
        UiAnimSprite_SetAnimIndex(&work->panel_sprites[0], 1, 1);
        UiAnimSprite_SetAnimIndex(&work->panel_sprites[3], 1, 0);
        UiAnimSprite_SetAnimIndex(&work->panel_sprites[4], 1, 0);
        work->lr_state_left = 1;
        work->lr_state_right = 1;
    } else if (mode == 2) {
        work->active_mode = 2;
        if (work->prev_active_mode != 2) {
            UiAnimSprite_SetAnimIndex(&work->panel_sprites[3], 3, 0);
            UiAnimSprite_SetAnimIndex(&work->panel_sprites[4], 3, 0);
            work->lr_state_left = 1;
            work->lr_state_right = 1;
        }
        UiAnimSprite_SetAnimIndex(&work->panel_sprites[1], 1, 1);
        UiAnimSprite_SetAnimIndex(&work->panel_sprites[2], 1, 1);
    }
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

// DECOMP_FUNC(0x0029adf0, 320)
void StatusDown_DrawLRPrompts(StatusDownWork* work, s32 mode) {
    if (work->active_mode != 1 && work->active_mode != 2) {
        return;
    }

    if (work->lr_state_left == 1) {
        if (UiAnimSprite_IsAnimFinished(&work->panel_sprites[3])) {
            const s32 next_anim = (mode == 2) ? 2 : 0;
            UiAnimSprite_SetAnimIndex(&work->panel_sprites[3], next_anim, 0);
            work->lr_state_left = 0;
        }
    }
    UiAnimSprite_Update(&work->panel_sprites[3]);
    UiAnimSprite_SetLayerOrder(&work->panel_sprites[3], 1);
    UiAnimSprite_Draw(&work->panel_sprites[3], 0.0f, 0.0f);

    if (work->lr_state_right == 1) {
        if (UiAnimSprite_IsAnimFinished(&work->panel_sprites[4])) {
            const s32 next_anim = (mode == 2) ? 2 : 0;
            UiAnimSprite_SetAnimIndex(&work->panel_sprites[4], next_anim, 0);
            work->lr_state_right = 0;
        }
    }
    UiAnimSprite_Update(&work->panel_sprites[4]);
    UiAnimSprite_SetLayerOrder(&work->panel_sprites[4], 1);
    UiAnimSprite_Draw(&work->panel_sprites[4], 0.0f, 0.0f);
}

// DECOMP_FUNC(0x0029bfec, 152)
void StatusDown_Close() {
    StatusDownWork* work = g_StatusDownWork;
    if (work != nullptr) {
        const u32 st = work->state;
        if (st != 2 && st != 8 && st != 0) {
            work->state = 8;
            work->prev_state = st;
            work->sub_state = 0;
            work->state_timer = 0;
            work->flag_413 = 0;
            StatusDown_ClearPortraits(work);
        }
    }
    StatusDown_SetDisplayMode(0);
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
void StatusDown_UpdateHelpMessage(StatusDownWork* work, s32 msg_index) {
    UiListCursor_SetPosition(&work->list_cursor_help, 4, 0xAC);

    s32 msg_id = -1;
    switch (msg_index) {
        case 0:
            msg_id = g_StatusDownHelpMsgIds[0];
            break;
        case 1:
            msg_id = g_StatusDownHelpMsgIds[1];
            break;
        case 2:
            msg_id = g_StatusDownHelpMsgIds[2];
            break;
        case 3:
            msg_id = g_StatusDownHelpMsgIds[3];
            break;
        default:
            break;
    }

    UiListCursor_SetTextArgs(&work->list_cursor_help, work->text_handle, msg_id, 0, 0);
}

// DECOMP_FUNC(0x002d931c, 764)
void StatusDown_Init(u8 visibility) {
    if (g_StatusDownWork == nullptr) {
        auto* mem = static_cast<StatusDownWork*>(
            AsdMem_AllocZeroed(sizeof(StatusDownWork), 0x1000,
                               "c:\\SMT4\\XRD686\\sdds4\\program\\status\\StatusDown.cpp", 0xB8));
        if (mem != nullptr) {
            for (s32 i = 0; i < 7; ++i) {
                UiAnimSprite_Init(&mem->panel_sprites[i]);
            }
            UiListCursor_Init(&mem->list_cursor_main);
            UiListCursor_Init(&mem->list_cursor_prompt);
            UiListCursor_Init(&mem->list_cursor_help);
        }
        g_StatusDownWork = mem;

        mem->calc_task = AsdTask_Create(StatusDown_CalcTaskCallback, mem, "TMD CALC", 2, 0);
        mem->draw_task = AsdTask_Create(StatusDown_DrawTaskCallback, mem, "TMD DDRAW", 0xE7, 0);
        mem->visibility_flag = visibility;

        UiSpriteGroup_Init(&mem->sprite_group, g_StatusDownSpriteTable, 4);
        while (!UiSpriteGroup_BindTable(&mem->sprite_group, g_StatusDownSpriteTable, 4)) {
        }

        void* res0 = UiSpriteGroup_GetResource(&mem->sprite_group, 0);
        UiAnimSprite_BindResource(&mem->panel_sprites[0], res0, "root", 0);

        void* res1 = UiSpriteGroup_GetResource(&mem->sprite_group, 1);
        UiAnimSprite_BindResource(&mem->panel_sprites[1], res1, "up_l", 0);
        UiAnimSprite_BindResource(&mem->panel_sprites[2], res1, "up_r", 0);
        UiAnimSprite_BindResource(&mem->panel_sprites[3], res1, "down_l", 0);
        UiAnimSprite_BindResource(&mem->panel_sprites[4], res1, "down_r", 0);
        UiAnimSprite_BindResource(&mem->panel_sprites[5], res1, "up_c", 0);
        UiAnimSprite_BindResource(&mem->panel_sprites[6], res1, "down_c", 0);

        StatusDown_FillHalfwords(mem->slot_table, 0x29, -1);
        mem->loaded_icon_count = 0;
        mem->text_handle = AsdText_Create(0x800);
        mem->active_sound_id = -1;

        StatusDown_InitSubPanels(mem);
    }

    StatusDownWork* work = g_StatusDownWork;
    if (work != nullptr && work->state == 0) {
        work->state = 1;
        work->prev_state = 0;
        work->sub_state = 0;
        work->state_timer = 0;
        StatusDown_LoadDefaultParty(work);
    }
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

// DECOMP_FUNC(0x002e2f44, 408)
void StatusDown_UpdatePartySlotsAndDiff(const u16* ids, s32 count, u8 flag) {
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        return;
    }

    if (work->state == 0) {
        work->state = 1;
        work->prev_state = 0;
        work->sub_state = 0;
        work->state_timer = 0;
    }

    work->needs_refresh = 1;
    work->flag_548 = flag;

    u16 prev_ids[8];
    std::memcpy(prev_ids, work->party_ids, sizeof(prev_ids));
    std::memset(work->party_ids, 0, sizeof(work->party_ids));
    std::memset(work->new_party_flags, 0, sizeof(work->new_party_flags));

    for (s32 i = 0; i < count; ++i) {
        work->party_ids[i] = ids[i];
    }

    for (s32 i = 0; i < 8; ++i) {
        const u16 cur_id = work->party_ids[i];
        if (cur_id == 0 || !Party_IsDemonValid(cur_id)) {
            continue;
        }
        bool existed = false;
        for (s32 j = 0; j < 8; ++j) {
            if (cur_id == prev_ids[j]) {
                existed = true;
                break;
            }
        }
        if (!existed) {
            work->new_party_flags[i] = 1;
        }
    }

    StatusDown_FillHalfwords(work->slot_table, 0x29, -1);
    work->loaded_icon_count = 0;
    StatusDown_ClearPortraits(work);
}

// DECOMP_FUNC(0x002efde0, 44)
s32 StatusDown_GetPartyMaxIndex() {
    if (g_StatusDownWork != nullptr) {
        u16 active_slots[12]{};
        return Party_GetActiveSlotOrder(active_slots) - 1;
    }
    return 0;
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
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        return;
    }

    std::memset(work->sub_ids_b, 0, sizeof(work->sub_ids_b));
    for (s32 i = 0; i < count; ++i) {
        work->sub_ids_b[i] = ids[i];
    }
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
    if (work == nullptr) {
        return;
    }

    if (work->calc_task != nullptr) {
        AsdTask_Destroy(work->calc_task);
    }
    if (work->draw_task != nullptr) {
        AsdTask_Destroy(work->draw_task);
    }
    if (work->text_handle != nullptr) {
        AsdText_Destroy(work->text_handle);
        work->text_handle = nullptr;
    }

    UiSpriteGroup_Release(&work->sprite_group);
    AsdMem_Free(g_StatusDownWork);
    g_StatusDownWork = nullptr;
}

// DECOMP_FUNC(0x002f65d4, 76)
bool StatusDown_IsCursorAtLastPartySlot() {
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        return false;
    }

    u16 active_slots[12]{};
    const s32 last_index = Party_GetActiveSlotOrder(active_slots) - 1;
    const s16 cursor_idx = *reinterpret_cast<const s16*>(&work->list_cursor_main.raw[2]);
    return cursor_idx == last_index;
}

// DECOMP_FUNC(0x002f6620, 200)
void StatusDown_SelectLastPartySlotAndEnterState11(s32 result_val, u32 arg1) {
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        return;
    }

    work->selected_result = result_val;
    if (result_val < 0) {
        u16 active_slots[12]{};
        const s32 count = Party_GetActiveSlotOrder(active_slots);
        UiListCursor_SetSelection(&work->list_cursor_main, count - 1, count);
    }

    const u32 prev = work->state;
    work->state = 11;
    work->prev_state = prev;
    work->sub_state = 0;
    work->state_timer = 0;
    work->callback_arg1 = arg1;
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
    if (work != nullptr) {
        const s16 cursor_idx = *reinterpret_cast<const s16*>(&work->list_cursor_main.raw[2]);
        return static_cast<s32>(work->party_ids[cursor_idx]);
    }
    return 0;
}

} // namespace smt4::ui
