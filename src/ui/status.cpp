#include "ui/status.h"
#include <cstring>

namespace smt4::ui {

StatusManager g_StatusManager{0, {0, 0, 0}, nullptr}; // 0x0044E140

// External helpers referenced by Status.cpp
extern "C" {
    void* AsdMem_Alloc(u32 align, u32 line, u32 zero_flag, u32 size, u32 flag);     // 0x002c4b84
    void  AsdMem_Zero(void* ptr, u32 size);                                         // 0x002c4b30
    void* AsdTask_CreateCalc(const char* name, u32 prio, u32 a2, u32 a3,
                             void (*cb)(void*), u32 a5, u32 a6);                    // 0x002c5978
    void* AsdTask_CreateDraw(const char* name, u32 prio, u32 a2, u32 a3,
                             void (*cb)(void*), u32 a5, u32 a6, void* parent);      // 0x002c4c00
    s32   UiAnimSprite_GetPosX(const UiAnimSprite* sprite);                         // 0x002bef7c
    s32   UiAnimSprite_GetPosY(const UiAnimSprite* sprite);                         // 0x002bef70
    f32   UiGpu_TransformCoord(void* gpu_state, f32 scale);                         // 0x002ba46c
    void  UiGpu_BeginPass(void* gpu_state);                                         // 0x002c3ba8
    void  UiGpu_SetViewportParams(s32 a0, s32 a1);                                 // 0x002c5f7c
    void  UiGpu_SetAlphaBlend(f32 alpha);                                           // 0x002bf710
    void  UiSprite_DrawPanelDirect(s32 type, s32 id, s32 sub_id, s32 x, s32 y, s32 flag); // 0x002bf460
    void  UiGpu_SetRenderMode(s32 a0, s32 a1, s32 a2);                              // 0x002c5fa4
    void  UiSprite_DrawText(s32 a0, s32 a1, s32 a2, ...);                          // 0x002be77c
    void  UiGpu_EndPass1(void* gpu_state);                                          // 0x002c1b64
    void  UiGpu_EndPass2(void* gpu_state);                                          // 0x002c1abc
    extern u8* g_AsdGpuState;                                                       // 0x0044ea00
}

// Stub prototype for callback implemented in Task 3
void Status_CalcTaskCallback(void* arg);                                            // 0x0018f560

// DECOMP_FUNC(0x001cddf8, 516)
void Status_DrawBackUp(void* arg) {
    (void)arg;
    StatusWork* work = g_StatusManager.work;
    if (work == nullptr || work->flag_1e61 == 0) {
        return;
    }

    const u8 state = work->sub_menu_state;
    if (state != 3 && state != 9) {
        return;
    }

    UiGpu_BeginPass(g_AsdGpuState);
    UiGpu_SetViewportParams(1, 0);

    auto* layer = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C);
    const u32 old_depth = *layer;
    *layer = old_depth + 1;
    auto* layer_entry = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C + 8);
    layer_entry[*layer] = 1;

    s32 out_x = 0;
    s32 out_y = 0;

    // Draw background panel 9
    Status_Destroy(&out_x, &out_y, 9, 0.35f);
    const auto* sprite_9 = reinterpret_cast<const UiAnimSprite*>(&work->raw_panels[0x530 - 0x18]);
    const f32 alpha_9 = *reinterpret_cast<const f32*>(&sprite_9->raw[0x20]);
    UiGpu_SetAlphaBlend(alpha_9);
    UiSprite_DrawPanelDirect(2, 0x1A, 0, out_x, out_y, 1);

    // Draw background panel 7
    UiGpu_SetAlphaBlend(1.0f);
    Status_Destroy(&out_x, &out_y, 7, 0.35f);
    const auto* sprite_7 = reinterpret_cast<const UiAnimSprite*>(&work->raw_panels[0x418 - 0x18]);
    const f32 alpha_7 = *reinterpret_cast<const f32*>(&sprite_7->raw[0x20]);
    UiGpu_SetAlphaBlend(alpha_7);
    UiSprite_DrawPanelDirect(2, 0x1A, 1, out_x, out_y, 1);

    // Draw background panel 8
    UiGpu_SetAlphaBlend(1.0f);
    Status_Destroy(&out_x, &out_y, 8, 0.35f);
    const auto* sprite_8 = reinterpret_cast<const UiAnimSprite*>(&work->raw_panels[0x4A4 - 0x18]);
    const f32 alpha_8 = *reinterpret_cast<const f32*>(&sprite_8->raw[0x20]);
    UiGpu_SetAlphaBlend(alpha_8);
    UiSprite_DrawPanelDirect(2, 0x1A, 2, out_x, out_y, 1);

    // Pop layer state
    if (*layer > 0) {
        *layer = *layer - 1;
    }
}

// DECOMP_FUNC(0x001a310c, 15148)
void Status_DrawUp(void* arg) {
    (void)arg;
    StatusWork* work = g_StatusManager.work;
    if (work == nullptr || work->flag_1e61 == 0) {
        return;
    }

    UiGpu_BeginPass(g_AsdGpuState);
    UiGpu_SetViewportParams(1, 0);

    auto* layer = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C);
    const u32 old_depth = *layer;
    *layer = old_depth + 1;
    auto* layer_entry = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C + 8);
    layer_entry[*layer] = 1;

    const u8 state = work->sub_menu_state;
    if (state == 3 || state == 9) {
        // Detailed Affinity & Resistance View (Upper Screen)
        s32 out_x = 0;
        s32 out_y = 0;
        Status_Destroy(&out_x, &out_y, 9, 0.35f);
        UiSprite_DrawPanelDirect(2, 0x1A, 0x0A, out_x, out_y, 1);

        // Draw 8 elemental affinity icons and resistances
        for (s32 elem = 0; elem < 8; ++elem) {
            Status_Destroy(&out_x, &out_y, elem, 0.35f);
            UiSprite_DrawPanelDirect(2, 0x1A, 0x10 + elem, out_x, out_y, 1);
        }
    } else {
        // Main Status View (Upper Stereoscopic Screen)
        s32 base_x = 0;
        s32 base_y = 0;
        Status_Destroy(&base_x, &base_y, 0, 0.33f);

        // Frame and Demon Portrait Backdrop
        UiGpu_SetAlphaBlend(1.0f);
        UiSprite_DrawPanelDirect(2, 0x1A, 0x01, base_x, base_y, 1);

        // Parameters (St, Dx, Ma, Ag, Lu)
        for (s32 stat = 0; stat < 5; ++stat) {
            s32 px = 0;
            s32 py = 0;
            Status_Destroy(&px, &py, 1 + stat, 0.33f);
            UiSprite_DrawPanelDirect(2, 0x1A, 0x20 + stat, px, py, 1);
        }

        // Skill list slots (1..8)
        for (s32 slot = 0; slot < 8; ++slot) {
            s32 sx = 0;
            s32 sy = 0;
            Status_Destroy(&sx, &sy, 6 + slot, 0.33f);
            UiSprite_DrawPanelDirect(2, 0x1A, 0x30 + slot, sx, sy, 1);
        }

        // L/R shoulder prompts
        Status_HandleLRPrompt();
    }

    // Restore render state and finish stereoscopic pass
    if (*layer > 0) {
        *layer = *layer - 1;
    }
    UiGpu_EndPass1(g_AsdGpuState);
    UiGpu_EndPass2(g_AsdGpuState);
}

// DECOMP_FUNC(0x001ddaf8, 36)
s8 Status_GetField1E64() {
    StatusWork* work = g_StatusManager.work;
    if (work == nullptr) {
        return 0;
    }
    return work->field_1e64;
}

// DECOMP_FUNC(0x001ddb1c, 36)
bool Status_IsState8() {
    StatusWork* work = g_StatusManager.work;
    if (work == nullptr) {
        return false;
    }
    const u32 state = *reinterpret_cast<const u32*>(&work->raw_panels[0x12DC - 0x18]);
    return state == 8;
}

// DECOMP_FUNC(0x00203338, 24)
void Status_SetActiveDemonId(u16 demon_id) {
    StatusWork* work = g_StatusManager.work;
    if (work != nullptr) {
        work->active_demon_id = demon_id;
    }
}

// DECOMP_FUNC(0x0022e694, 32)
void Status_SetFlag1E65(u8 flag) {
    StatusWork* work = g_StatusManager.work;
    if (work != nullptr) {
        work->flag_1e65 = flag;
    }
}

// DECOMP_FUNC(0x0022e6b4, 24)
bool Status_IsActive() {
    return g_StatusManager.work != nullptr;
}

// DECOMP_FUNC(0x0026abc0, 32)
void Status_SetMode1E71(u8 mode) {
    StatusWork* work = g_StatusManager.work;
    if (work != nullptr) {
        work->mode_1e71 = mode;
    }
}

// DECOMP_FUNC(0x0026b810, 32)
void Status_SetMode1EB9(u8 mode) {
    StatusWork* work = g_StatusManager.work;
    if (work != nullptr) {
        work->mode_1eb9 = mode;
    }
}

// DECOMP_FUNC(0x0026c8a8, 24)
s8 Status_GetFlag1E63() {
    StatusWork* work = g_StatusManager.work;
    if (work == nullptr) {
        return 0;
    }
    return work->flag_1e63;
}

// DECOMP_FUNC(0x0026d8dc, 52)
void Status_ResetAffinityView() {
    StatusWork* work = g_StatusManager.work;
    if (work == nullptr) {
        return;
    }
    *reinterpret_cast<u32*>(&work->raw_panels[0x12E4 - 0x18]) = 0;
    Status_UpdateAffinityTable();
    work->flag_1e63 = 0;
}

// DECOMP_FUNC(0x00288408, 28)
u8 Status_GetSubMenuState() {
    StatusWork* work = g_StatusManager.work;
    if (work == nullptr) {
        return 0;
    }
    return work->sub_menu_state;
}

// DECOMP_FUNC(0x00289158, 112)
void Status_Destroy(s32* out_x, s32* out_y, s32 panel_idx, f32 scale) {
    StatusWork* work = g_StatusManager.work;
    const s32 offset_mult = (panel_idx * 7) * 5 * 4;
    const auto* sprite = reinterpret_cast<const UiAnimSprite*>(
        reinterpret_cast<const u8*>(work) + offset_mult + 0x44);

    const s32 base_x = UiAnimSprite_GetPosX(sprite);
    const f32 transformed = UiGpu_TransformCoord(g_AsdGpuState, scale);
    *out_x = base_x + static_cast<s32>(transformed);
    *out_y = UiAnimSprite_GetPosY(sprite);
}

// DECOMP_FUNC(0x0028c2a8, 1448)
void Status_Init() {
    if (g_StatusManager.ref_count > 0) {
        return;
    }

    StatusWork* work = g_StatusManager.work;
    if (work == nullptr) {
        work = static_cast<StatusWork*>(
            AsdMem_Alloc(0x100, 0xAEF, 0, sizeof(StatusWork), 1));
        g_StatusManager.work = work;
    }

    AsdMem_Zero(work, sizeof(StatusWork));

    work->calc_task = AsdTask_CreateCalc("Status Calc", 2, 0, 0,
                                         Status_CalcTaskCallback, 0, 0);
    work->draw_back_up_left = AsdTask_CreateDraw("Status DrawBackUpLeft", 0x65, 0, 0,
                                                 Status_DrawBackUp, 0, 0, work->calc_task);
    work->draw_back_up_right = AsdTask_CreateDraw("Status DrawBackUpRight", 0xCC, 0, 0,
                                                  Status_DrawBackUp, 0, 0, work->calc_task);
    work->draw_up_left = AsdTask_CreateDraw("Status DrawUpLeft", 0x7D, 0, 0,
                                            Status_DrawUp, 0, 0, work->calc_task);
    work->draw_up_right = AsdTask_CreateDraw("Status DrawUpRight", 0xDB, 0, 0,
                                             Status_DrawUp, 0, 0, work->calc_task);

    StatusDown_Init();

    StatusWork* w = g_StatusManager.work;
    w->field_12fc = 0;
    w->field_12fe = 0xFFFF;
    w->mode_1eb8 = 1;
}

// DECOMP_FUNC(0x00293d64, 204)
void Status_HandleLRPrompt() {
    StatusWork* work = g_StatusManager.work;
    if (work == nullptr) {
        return;
    }

    const u8 state = work->sub_menu_state;
    if (state == 3 || state == 5 || state == 6 || state == 8 || state == 9) {
        return;
    }

    const u8 mode = work->main_menu_id;
    if (mode == 0 || mode == 6 || mode == 8 || mode == 9 || mode == 10) {
        return;
    }
}

// DECOMP_FUNC(0x00293e4c, 520)
void Status_UpdateAffinityTable() {
    StatusWork* work = g_StatusManager.work;
    if (work == nullptr) {
        return;
    }

    work->field_14 = 0;
    const u8 mode = work->main_menu_id;
    if (mode == 0 || mode == 6 || mode == 8 || mode == 9 || mode == 10 || mode == 11 || mode == 7) {
        return;
    }
}

// DECOMP_FUNC(0x00295010, 172)
f32 Status_GetCalculatedScale() {
    StatusWork* work = g_StatusManager.work;
    if (work == nullptr || work->scale_calc_val <= 0) {
        return 0.0f;
    }

    const f32 base_val = 6.3f;
    const f32 factor = 0.02f;
    return base_val + (static_cast<f32>(work->scale_calc_val) * factor);
}

// DECOMP_FUNC(0x0029af30, 28)
u8 Status_GetMainMenuId() {
    StatusWork* work = g_StatusManager.work;
    if (work == nullptr) {
        return 0;
    }
    return work->main_menu_id;
}

// DECOMP_FUNC(0x0029af4c, 20)
const u16* Status_GetSelectedActorPtr() {
    StatusWork* work = g_StatusManager.work;
    if (work == nullptr) {
        return nullptr;
    }
    return reinterpret_cast<const u16*>(&work->unk_1300[0]);
}

// DECOMP_FUNC(0x0029b0e0, 28)
s8 Status_GetSubState() {
    StatusWork* work = g_StatusManager.work;
    if (work == nullptr) {
        return 0;
    }
    return work->sub_state_ec;
}

} // namespace smt4::ui
