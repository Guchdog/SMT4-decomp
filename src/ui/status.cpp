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
    void* UiGpu_SetViewportParams(s32 a0, s32 a1);                                 // 0x002c5f7c
    void  UiGpu_SetAlphaBlend(f32 alpha);                                           // 0x002bf710
    void  UiSprite_DrawPanelDirect(s32 type, s32 id, s32 sub_id, s32 x, s32 y, s32 flag); // 0x002bf460
    void* UiGpu_SetRenderMode(s32 a0, s32 a1, s32 a2);                              // 0x002c5fa4
    void  UiSprite_DrawText(s32 a0, s32 a1, s32 a2, ...);                          // 0x002be77c
    void  UiGpu_EndPass1(void* gpu_state);                                          // 0x002c1b64
    void  UiGpu_EndPass2(void* gpu_state);                                          // 0x002c1abc
    void  UiAnimSprite_UpdateCalc(void* sprite);                                    // 0x002bf9f0
    void  UiStatus_UpdateLayout(void* ptr, s32 mode);                               // 0x0029538c
    void  UiCamp_UpdateNode(void* ptr, s32 mode);                                   // 0x002b9220
    void  UiStatus_SetPanelMode(void* ptr, s32 a1, s32 a2);                         // 0x00296528
    f32   UiStatus_CalcScaleRatio(s32 a0, s32 a1);                                  // 0x00293ca8
    s32   UiMath_ClampVal(s32 a0, s32 a1);                                          // 0x002c6c10
    extern u8* g_AsdGpuState;                                                       // 0x0044ea00
}

// DECOMP_FUNC(0x0018f560, 4912)
void Status_CalcTaskCallback(void* arg) {
    (void)arg;
    StatusWork* work = g_StatusManager.work;
    if (work == nullptr) {
        return;
    }

    work->sub_state_ec = 0;

    // Advance sprite animations
    UiAnimSprite_UpdateCalc(&work->raw_panels[0x15C - 0x18]);
    UiAnimSprite_UpdateCalc(&work->raw_panels[0x1E8 - 0x18]);

    const u8 flag_1eb4 = work->unk_1ea4[0x1EB4 - 0x1EA4];
    if (flag_1eb4 != 0) {
        UiAnimSprite_UpdateCalc(&work->raw_panels[0x274 - 0x18]);
        UiAnimSprite_UpdateCalc(&work->raw_panels[0x300 - 0x18]);
        const s8 s1 = *reinterpret_cast<const s8*>(&work->raw_panels[0x274 - 0x18 + 0x8A]);
        const s8 s2 = *reinterpret_cast<const s8*>(&work->raw_panels[0x300 - 0x18 + 0x8A]);
        if (s1 != 0 && s2 != 0) {
            work->unk_1ea4[0x1EB4 - 0x1EA4] = 0;
        }
    }

    u32* p_state = reinterpret_cast<u32*>(&work->raw_panels[0x12DC - 0x18]);
    const u32 state = *p_state;

    switch (state) {
    case 0: {
        // Initial setup and fade-in
        if (work->sub_menu_state == 9) {
            *p_state = 0;
            *reinterpret_cast<u8*>(&work->raw_panels[0x12F2 - 0x18]) = 1;
            break;
        }
        UiStatus_UpdateLayout(&work->raw_panels[0x418 - 0x18], 1);
        UiStatus_UpdateLayout(&work->raw_panels[0x4A4 - 0x18], 0);
        break;
    }
    case 1: {
        // Active view: demon stats, switching, input processing
        UiAnimSprite_UpdateCalc(&work->raw_panels[0x44 - 0x18]);
        UiAnimSprite_UpdateCalc(&work->raw_panels[0xD0 - 0x18]);

        const s16 selected_demon = *reinterpret_cast<const s16*>(&work->unk_1300[0]);
        if (selected_demon == 0x155 || selected_demon == 0x156) {
            UiStatus_SetPanelMode(&work->raw_panels[0x38C - 0x18], 1, 1);
        } else {
            UiStatus_SetPanelMode(&work->raw_panels[0x38C - 0x18], 0, 0);
        }

        if (static_cast<s16>(work->field_12fe) > 0) {
            const u32 mode_1e74 = *reinterpret_cast<const u32*>(&work->unk_1e72[0x1E74 - 0x1E72]);
            if (mode_1e74 != 0) {
                u32* tick_ptr = reinterpret_cast<u32*>(&work->unk_1300[0x1E78 - 0x1300]);
                *tick_ptr += 2;
                const f32 ratio = UiStatus_CalcScaleRatio(0, 0);
                *tick_ptr = UiMath_ClampVal(*tick_ptr, static_cast<s32>(ratio));
            }
        }
        UiAnimSprite_UpdateCalc(&work->raw_panels[0x5BC - 0x18]);
        break;
    }
    case 2:
    case 3:
    case 4:
    case 5:
    case 6: {
        // Transition and affinity view animation steps
        for (s32 i = 0; i < 10; ++i) {
            const s32 offset = i * 140;
            UiCamp_UpdateNode(&work->raw_panels[0x400 - 0x18 + offset + 0x3EC], 1);
            UiCamp_UpdateNode(&work->raw_panels[0xC00 - 0x18 + offset + 0x164], 0);
        }
        break;
    }
    case 7: {
        // Fade out / exiting
        UiAnimSprite_UpdateCalc(&work->raw_panels[0x44 - 0x18]);
        UiAnimSprite_UpdateCalc(&work->raw_panels[0xD0 - 0x18]);
        break;
    }
    case 8:
    default:
        break;
    }

    // Tick frame counters
    u32* p_tick10 = reinterpret_cast<u32*>(&work->unk_1300[0x1310 - 0x1300]);
    u32* p_tick14 = reinterpret_cast<u32*>(&work->unk_1300[0x1314 - 0x1300]);
    *p_tick10 += 1;
    *p_tick14 += 1;
}

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

// ============================================================================
// StatusBustUp: Character & Demon BustUp Renderer (StatusBustUp.cpp)
// ============================================================================

StatusBustUpManager g_StatusBustUpManager = {0, {0, 0, 0}, nullptr, nullptr}; // 0x0044E158

// DECOMP_FUNC(0x00223a90, 248)
void StatusBustUp_Init() {
    StatusBustUpManager* mgr = &g_StatusBustUpManager;
    if (mgr->ref_count <= 0) {
        if (mgr->buffer1 == nullptr) {
            mgr->buffer1 = AsdMem_Alloc(0x81, 0x100);
            AsdMem_Zero(mgr->buffer1, 0x81);
        }
        if (mgr->buffer2 == nullptr) {
            mgr->buffer2 = AsdMem_Alloc(0x81, 0x100);
            AsdMem_Zero(mgr->buffer2, 0x81);
        }
    }
    mgr->ref_count++;
}

// ============================================================================
// StatusCamera: Upper Screen Stereoscopic Camera (StatusCamera.cpp)
// ============================================================================

StatusCameraWork* g_StatusCamera = nullptr; // 0x0044E178

// DECOMP_FUNC(0x00258e38, 480)
void StatusCamera_Init(const f32* pos, const f32* target, const f32* up,
                       f32 fov, f32 aspect, f32 near_z, f32 far_z, f32 scale) {
    (void)pos; (void)target; (void)up; (void)fov; (void)aspect; (void)near_z; (void)far_z; (void)scale;
    StatusCameraWork* cam = g_StatusCamera;
    if (cam == nullptr) {
        cam = reinterpret_cast<StatusCameraWork*>(AsdMem_Alloc(sizeof(StatusCameraWork), 0x100));
        g_StatusCamera = cam;
    }
    AsdMem_Zero(cam, sizeof(StatusCameraWork));
}

} // namespace smt4::ui
