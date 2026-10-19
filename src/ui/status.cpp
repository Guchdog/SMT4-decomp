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
    extern u8* g_AsdGpuState;                                                       // 0x0044ea00
}

// Stub prototypes for callbacks implemented in later tasks
void Status_DrawBackUp(void* arg);                                                  // 0x001cddf8
void Status_DrawUp(void* arg);                                                      // 0x001a310c
void Status_CalcTaskCallback(void* arg);                                            // 0x0018f560

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
