#include "ui/window.h"
#include "engine/asd_symbols.h"
#include <cstring>

namespace smt4::ui {

// 0x002C32F8 copies its ten trailing arguments verbatim; table pointers are
// passed as their 32-bit address words.
static inline u32 SpriteTableWord(const void* pointer) {
    return static_cast<u32>(reinterpret_cast<std::uintptr_t>(pointer));
}

ComWinWork* g_ComWinWork = nullptr; // 0x0043E0F8

// External engine and UI helpers referenced by ComWin
extern "C" {
    void* AsdMem_Alloc(u32 align, u32 line, u32 zero_flag, u32 size, u32 flag);     // 0x002c4b84
    void  AsdMem_Zero(void* ptr, u32 size);                                         // 0x002c4b30
    void* AsdTask_CreateCalc(const char* name, u32 prio, u32 a2, u32 a3,
                             void (*cb)(void*), u32 a5, u32 a6);                    // 0x002c5978
    void* AsdTask_CreateDraw(const char* name, u32 prio, u32 a2, u32 a3,
                             void (*cb)(void*), u32 a5, u32 a6, void* parent);      // 0x002c4c00
    // UiSpriteGroup_Init / UiSpriteGroup_BindTable are declared canonically in
    // engine/asd_symbols.h (0x002C3344 / 0x002C32F8).
    void  UiAnimSprite_Setup(UiAnimSprite* sprite, s32 type, s32 id,
                             UiSpriteGroup* group, u32 flag, f32 scale);            // 0x002bf0a8
    void  UiAnimSprite_SetAnim(UiAnimSprite* sprite, s32 anim, s32 frame);          // 0x002bf030
    void  UiGpu_BeginPass(void* gpu_state);                                         // 0x002c3ba8
    void* UiGpu_SetViewportParams(s32 a0, s32 a1);                                 // 0x002c5f7c
    void  UiGpu_SetAlphaBlend(f32 alpha);                                           // 0x002bf710
    f32   UiGpu_TransformCoord(void* gpu_state, f32 scale);                         // 0x002ba46c
    void  UiSprite_DrawPanelDirect(s32 type, s32 id, s32 sub_id, s32 x, s32 y, s32 flag); // 0x002bf460
    void  UiWindow_ExecSub(void* ptr);                                              // 0x002c54f0
    void  UiWindow_PushContext(void* ptr, s32 mode);                                // 0x002befdc
    void  UiWindow_PopContext(void* ptr, s32 mode);                                 // 0x002bef88
    void  UiWindow_SetResult(s32 val);                                              // 0x002c4244
    void  UiWindow_ResetState(void* ptr);                                           // 0x002bdbcc
    void* AsdText_CreateDefault(s32 a0);                                            // 0x002bda1c
    void  AsdText_SetAlpha(void* handle, u32 alpha);                                // 0x002bda10
    void  AsdText_SetColorAndScale(void* handle, s32 a0, u32 color, f32 scale);    // 0x002bda00
    void  UiAnimSprite_SetupEx(UiAnimSprite* sprite, s32 type, s32 id, s32 a3,
                               UiSpriteGroup* group, u32 flag, f32 scale);          // 0x002bdb2c
    void  UiAnimSprite_SetMode(UiAnimSprite* sprite, s32 m0, s32 m1);               // 0x002bdac0
    extern u8* g_AsdGpuState;                                                       // 0x0044ea00
    extern u8  g_ComWinSpriteTable[];                                               // 0x004038F0
    extern u8  g_InfoWinSpriteTable[];                                              // 0x00403AA8
    extern u8  g_GuestWinSpriteTable[];                                             // 0x00403A38
    void* UiEngine_GetContext();                                                    // 0x002c2b1c
}

// Forward declaration for task callback
void ComWin_Calc(void* arg);                                                        // 0x0011b094

// DECOMP_FUNC(0x0010a6fc, 16)
void ComWin_SetParam1C(u32 val) {
    auto* ptr = reinterpret_cast<u32*>(0x00464D48 + 0x1C);
    *ptr = val;
}

// DECOMP_FUNC(0x0010a70c, 60)
bool ComWin_SetState() {
    auto* state_block = reinterpret_cast<u32*>(0x004E3CD4);
    for (s32 i = 0; i < 6; ++i) {
        state_block[i] = 0;
    }
    state_block[6] = 0x0F;
    state_block[7] = 4;
    return true;
}

// DECOMP_FUNC(0x0010a748, 504)
void ComWin_Init() {
    ComWinWork* work = g_ComWinWork;
    if (work == nullptr) {
        work = static_cast<ComWinWork*>(
            AsdMem_Alloc(0x100, 0x122, 0, sizeof(ComWinWork), 1));
        g_ComWinWork = work;
    }

    AsdMem_Zero(work, sizeof(ComWinWork));

    work->calc_task = AsdTask_CreateCalc("ComWin Calc", 1, 0, 0,
                                         ComWin_Calc, 0, 0);
    work->draw_up_left = AsdTask_CreateDraw("ComWin DrawUpLeft", 0x81, 0, 0,
                                            ComWin_DrawUp, 0, 0, work->calc_task);
    work->draw_up_right = AsdTask_CreateDraw("ComWin DrawUpRight", 0xDF, 0, 0,
                                             ComWin_DrawUp, 0, 0, work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(&work->sprite_group,
                            0, 0,
                            SpriteTableWord(g_ComWinSpriteTable - 0x30), 0x30,
                            SpriteTableWord(g_ComWinSpriteTable - 0x30),
                            0x30, 0, 0,
                            SpriteTableWord(g_ComWinSpriteTable), 0x118);

    UiAnimSprite_Setup(&work->panel_sprites[0], 0x0E, -1, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprites[0], 0, 0);

    UiAnimSprite_Setup(&work->panel_sprites[1], 0x0E, -1, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprites[1], 2, 0);
}

// DECOMP_FUNC(0x0010a940, 20)
void ComWin_GetState(u32* out_state) {
    (void)out_state;
    UiWindow_ExecSub(nullptr);
}

// DECOMP_FUNC(0x0010a954, 1352)
void ComWin_ProcessDialog() {
    auto* ctx = *reinterpret_cast<u8**>(0x0043E188 + 8);
    if (ctx == nullptr || ctx[0x83] != 0) {
        return;
    }

    const u8 type = ctx[9];
    if (type == 0x0B) {
        if (ctx[8] != 0) {
            const f32 alpha = *reinterpret_cast<const f32*>(&ctx[0xC4 + 0x20]);
            UiGpu_SetAlphaBlend(alpha);
            UiGpu_SetViewportParams(1, 0);
            UiWindow_PushContext(g_AsdGpuState, 3);
            UiSprite_DrawPanelDirect(2, 0x0E, 0x101, 0, 6, 0);
            UiWindow_PopContext(g_AsdGpuState, 3);
            UiGpu_SetAlphaBlend(1.0f);
        }
    } else if (type == 0x13) {
        // Mode 0x13 dialog processing
        UiGpu_SetAlphaBlend(1.0f);
        UiSprite_DrawPanelDirect(2, 0x0E, 0x102, 0, 6, 0);
    }
}

// DECOMP_FUNC(0x0010ae9c, 44)
void ComWin_CheckFlag() {
    auto* val_ptr = *reinterpret_cast<u32**>(0x00465058);
    if (val_ptr != nullptr) {
        const u32 flag = *val_ptr ^ 1;
        auto* table = reinterpret_cast<u32*>(0x00465064);
        (void)table[flag];
    }
}

// DECOMP_FUNC(0x0010aec8, 12)
void ComWin_GetResult() {
    const s32 res = *reinterpret_cast<const s32*>(0x00465024);
    UiWindow_SetResult(res);
}

// DECOMP_FUNC(0x0010aed4, 100)
void ComWin_Reset() {
    auto* block = *reinterpret_cast<u8***>(0x004E2F68 + 0x204);
    if (block != nullptr) {
        for (s32 i = 0; i < 8; ++i) {
            if (block[i] != nullptr) {
                UiWindow_ResetState(block[i] + 0x20);
            }
        }
    }
}

// DECOMP_FUNC(0x0011a354, 1632)
void ComWin_DrawUp(void* arg) {
    (void)arg;
    ComWinWork* work = g_ComWinWork;
    if (work == nullptr || work->draw_up_right == nullptr) {
        return;
    }

    UiGpu_BeginPass(g_AsdGpuState);
    UiGpu_SetViewportParams(1, 0);

    auto* layer = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C);
    const u32 old_depth = *layer;
    *layer = old_depth + 1;
    auto* layer_entry = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C + 8);
    layer_entry[*layer] = 1;

    // Stereoscopic parallax shift (0.29f scale)
    const f32 shift = UiGpu_TransformCoord(g_AsdGpuState, 0.29f);
    const s32 base_x = static_cast<s32>(shift);

    // Apply alpha from message panel sprite
    const f32 alpha = *reinterpret_cast<const f32*>(&work->panel_sprites[0].raw[0x20]);
    UiGpu_SetAlphaBlend(alpha);

    // Draw message dialog frame panel
    UiSprite_DrawPanelDirect(2, 0x0E, 0x01, base_x, 0, 1);

    // Draw dialog text background
    UiSprite_DrawPanelDirect(2, 0x0E, 0x02, base_x, 0, 1);

    // Restore layer matrix
    if (*layer > 0) {
        *layer = *layer - 1;
    }
}

void ComWin_Calc(void* arg) {
    (void)arg;
}

InfoWinWork* g_InfoWinWork = nullptr; // 0x0043E128

// DECOMP_FUNC(0x0010af38, 16)
bool InfoWin_IsActive() {
    return g_InfoWinWork != nullptr && g_InfoWinWork->state != 0;
}

// DECOMP_FUNC(0x0010af48, 60)
void InfoWin_SetState(u32 state) {
    InfoWinWork* work = g_InfoWinWork;
    if (work != nullptr) {
        work->state = state;
        work->timer = 0x1E;
        work->flags = 0;
    }
}

// DECOMP_FUNC(0x0010af84, 560)
void InfoWin_Init() {
    InfoWinWork* work = g_InfoWinWork;
    if (work == nullptr) {
        work = static_cast<InfoWinWork*>(
            AsdMem_Alloc(0x100, 0xFF, 0, sizeof(InfoWinWork), 1));
        g_InfoWinWork = work;
    }

    AsdMem_Zero(work, sizeof(InfoWinWork));

    work->calc_task = AsdTask_CreateCalc("InfoWin Calc", 1, 0, 0,
                                         InfoWin_Calc, 0, 0);
    work->draw_up_left = AsdTask_CreateDraw("InfoWin DrawUpLeft", 0x81, 0, 0,
                                            InfoWin_DrawUp, 0, 0, work->calc_task);
    work->draw_up_right = AsdTask_CreateDraw("InfoWin DrawUpRight", 0xDF, 0, 0,
                                             InfoWin_DrawUp, 0, 0, work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(&work->sprite_group,
                            SpriteTableWord(g_InfoWinSpriteTable), 0x24,
                            0, 0, 0, 0, 0, 0, 0, 0);

    UiAnimSprite_SetupEx(&work->panel_sprites[0], 0x0E, 0x87, 0, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetMode(&work->panel_sprites[0], 0, 0);

    UiAnimSprite_SetupEx(&work->panel_sprites[1], 0x0E, 0x87, 0, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetMode(&work->panel_sprites[1], 2, 0);

    work->text_handle = AsdText_CreateDefault(0);
    AsdText_SetAlpha(work->text_handle, 0xFF);
    AsdText_SetColorAndScale(work->text_handle, 0, 0x646464FFu, 0.0f);

    work->timer = 0x1E;
}

// DECOMP_FUNC(0x0010b1b4, 172)
void InfoWin_ShowMessage(const char* msg) {
    (void)msg;
    InfoWinWork* work = g_InfoWinWork;
    if (work == nullptr) {
        return;
    }
    work->state = 1;
    work->timer = 0x1E;
}

// DECOMP_FUNC(0x0010b260, 192)
void InfoWin_UpdateTimer() {
    InfoWinWork* work = g_InfoWinWork;
    if (work == nullptr || work->state == 0) {
        return;
    }
    if (work->timer > 0) {
        work->timer--;
    } else {
        work->state = 0;
    }
}

// DECOMP_FUNC(0x0010b320, 32)
void InfoWin_Dismiss() {
    InfoWinWork* work = g_InfoWinWork;
    if (work != nullptr) {
        work->state = 0;
        work->timer = 0;
    }
}

// DECOMP_FUNC(0x0011ae10, 792)
void InfoWin_DrawUp(void* arg) {
    (void)arg;
    InfoWinWork* work = g_InfoWinWork;
    if (work == nullptr || work->draw_up_right == nullptr || work->state == 0) {
        return;
    }

    UiGpu_BeginPass(g_AsdGpuState);
    UiGpu_SetViewportParams(1, 0);

    auto* layer = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C);
    const u32 old_depth = *layer;
    *layer = old_depth + 1;
    auto* layer_entry = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C + 8);
    layer_entry[*layer] = 1;

    // Parallax shift for info alert
    const f32 shift = UiGpu_TransformCoord(g_AsdGpuState, 0.35f);
    const s32 base_x = static_cast<s32>(shift);

    const f32 alpha = *reinterpret_cast<const f32*>(&work->panel_sprites[0].raw[0x20]);
    UiGpu_SetAlphaBlend(alpha);

    // Draw alert banner backdrop & frame
    UiSprite_DrawPanelDirect(2, 0x0E, 0x05, base_x, 0, 1);
    UiSprite_DrawPanelDirect(2, 0x0E, 0x06, base_x, 0, 1);

    if (*layer > 0) {
        *layer = *layer - 1;
    }
}

// DECOMP_FUNC(0x0011b128, 588)
void InfoWin_Calc(void* arg) {
    (void)arg;
    InfoWinWork* work = g_InfoWinWork;
    if (work == nullptr || work->state == 0) {
        return;
    }
    InfoWin_UpdateTimer();
}

GuestWinWork* g_GuestWinWork = nullptr; // 0x0043E110

void GuestWin_Calc(void* arg);                                                      // 0x0011b128

// DECOMP_FUNC(0x0010b340, 16)
bool GuestWin_IsActive() {
    return g_GuestWinWork != nullptr && g_GuestWinWork->state != 0;
}

// DECOMP_FUNC(0x0010b350, 448)
void GuestWin_Init() {
    GuestWinWork* work = g_GuestWinWork;
    if (work == nullptr) {
        work = static_cast<GuestWinWork*>(
            AsdMem_Alloc(0x100, 0xF5, 0, sizeof(GuestWinWork), 1));
        g_GuestWinWork = work;
    }

    AsdMem_Zero(work, sizeof(GuestWinWork));

    work->calc_task = AsdTask_CreateCalc("GuestWin Calc", 1, 0, 0,
                                         GuestWin_Calc, 0, 0);
    work->draw_up_left = AsdTask_CreateDraw("GuestWin DrawUpLeft", 0x81, 0, 0,
                                            GuestWin_DrawUp, 0, 0, work->calc_task);
    work->draw_up_right = AsdTask_CreateDraw("GuestWin DrawUpRight", 0xDF, 0, 0,
                                             GuestWin_DrawUp, 0, 0, work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(&work->sprite_group,
                            SpriteTableWord(g_GuestWinSpriteTable - 0x30), 0x18,
                            SpriteTableWord(g_GuestWinSpriteTable - 0x18), 0x18,
                            0, 0, 0, 0,
                            SpriteTableWord(g_GuestWinSpriteTable), 0x70);

    UiAnimSprite_SetupEx(&work->panel_sprite, 0x0E, 0x87, 0, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprite, 0, 0);
}

// DECOMP_FUNC(0x0010b510, 104)
void GuestWin_HandlePrompt() {
    auto* ctx = reinterpret_cast<u8*>(UiEngine_GetContext());
    if (ctx == nullptr) {
        return;
    }

    auto* timer_block = reinterpret_cast<s16*>(ctx + 0xF28);
    auto* flag_block = ctx + 0xF20;

    for (s32 i = 0; i < 16; ++i) {
        u8 flags = flag_block[i * 0x14];
        if ((flags & 7) == 7 && !(flags & 8)) {
            s16 timer = timer_block[i * (0x14 / 2)];
            if (timer > 0) {
                timer--;
                timer_block[i * (0x14 / 2)] = timer;
            }
            if (timer == 0) {
                flag_block[i * 0x14] |= 8;
            }
        }
    }
}

// DECOMP_FUNC(0x0011a9b4, 1116)
void GuestWin_DrawUp(void* arg) {
    (void)arg;
    GuestWinWork* work = g_GuestWinWork;
    if (work == nullptr || work->draw_up_right == nullptr || work->state == 0) {
        return;
    }

    UiGpu_BeginPass(g_AsdGpuState);
    UiGpu_SetViewportParams(1, 0);

    auto* layer = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C);
    const u32 old_depth = *layer;
    *layer = old_depth + 1;
    auto* layer_entry = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C + 8);
    layer_entry[*layer] = 1;

    // Stereoscopic parallax shift (0.35f scale)
    const f32 shift = UiGpu_TransformCoord(g_AsdGpuState, 0.35f);
    const s32 base_x = static_cast<s32>(shift);

    const f32 alpha = *reinterpret_cast<const f32*>(&work->panel_sprite.raw[0x20]);
    UiGpu_SetAlphaBlend(alpha);

    // Draw partner prompt banner backdrop & Demonica prompt icon
    UiSprite_DrawPanelDirect(2, 0x0E, 0x03, base_x, 0, 1);
    UiSprite_DrawPanelDirect(2, 0x0E, 0x04, base_x, 0, 1);

    if (*layer > 0) {
        *layer = *layer - 1;
    }
}

void GuestWin_Calc(void* arg) {
    (void)arg;
    GuestWin_HandlePrompt();
}

// ============================================================================
// PlaceWin: Location & Area Banner HUD Window (c:\SMT4\XRD686\sdds4\program\font\PlaceWin\PlaceWin.cpp)
// ============================================================================

PlaceWinWork* g_PlaceWinWork = nullptr; // 0x0043E140
static const u8 g_PlaceWinSpriteTable[0x20] = {0};

// DECOMP_FUNC(0x0026385c, 64)
void PlaceWin_SetPos(f32 x, f32 y, f32 z, f32 w) {
    PlaceWinWork* work = g_PlaceWinWork;
    if (work == nullptr) {
        return;
    }
    f32* pos = reinterpret_cast<f32*>(&work->panel_sprite.raw[0x84]);
    pos[0] = x;
    pos[1] = y;
    pos[2] = z;
    pos[3] = w;
}

// DECOMP_FUNC(0x0026389c, 64)
void PlaceWin_SetScale(s32 idx, s32 layer, f32 sx, f32 sy, f32 sz, f32 sw) {
    PlaceWinWork* work = g_PlaceWinWork;
    if (work == nullptr || idx < 0) {
        return;
    }
    (void)layer;
    f32* scale = reinterpret_cast<f32*>(&work->panel_sprite.raw[0x98]);
    scale[0] = sx;
    scale[1] = sy;
    scale[2] = sz;
    scale[3] = sw;
}

// DECOMP_FUNC(0x002638dc, 32)
void PlaceWin_Dismiss() {
    PlaceWinWork* work = g_PlaceWinWork;
    if (work != nullptr) {
        work->state = 3;
        UiAnimSprite_SetAnim(&work->panel_sprite, 1, 0);
    }
}

// DECOMP_FUNC(0x002638fc, 20)
void PlaceWin_SetVisible(u8 visible) {
    PlaceWinWork* work = g_PlaceWinWork;
    if (work != nullptr) {
        work->flags = visible;
    }
}

// DECOMP_FUNC(0x00263910, 60)
bool PlaceWin_CheckState() {
    PlaceWinWork* work = g_PlaceWinWork;
    if (work == nullptr || work->state == 0) {
        return false;
    }
    return work->state != 3;
}

// DECOMP_FUNC(0x0026394c, 44)
bool PlaceWin_IsActive() {
    PlaceWinWork* work = g_PlaceWinWork;
    if (work == nullptr) {
        return false;
    }
    return work->state != 0;
}

// DECOMP_FUNC(0x00263978, 124)
void PlaceWin_ShowMessage(const char* msg) {
    PlaceWinWork* work = g_PlaceWinWork;
    if (work == nullptr || msg == nullptr) {
        return;
    }
    work->state = 1;
    work->flags = 1;
    UiAnimSprite_SetAnim(&work->panel_sprite, 0, 0);
    for (s32 i = 0; i < 127 && msg[i] != '\0'; ++i) {
        work->message[i] = msg[i];
        work->message[i + 1] = '\0';
    }
}

// DECOMP_FUNC(0x002639f4, 448)
void PlaceWin_Init() {
    PlaceWinWork* work = g_PlaceWinWork;
    if (work == nullptr) {
        work = static_cast<PlaceWinWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(PlaceWinWork), 1));
        g_PlaceWinWork = work;
    }

    AsdMem_Zero(work, sizeof(PlaceWinWork));

    work->calc_task = AsdTask_CreateCalc("PlaceWin Calc", 1, 0, 0,
                                         PlaceWin_Calc, 0, 0);
    work->draw_up_left = AsdTask_CreateDraw("PlaceWin DrawUpLeft", 0x81, 0, 0,
                                            nullptr, 0, 0, work->calc_task);
    work->draw_up_right = AsdTask_CreateDraw("PlaceWin DrawUpRight", 0xDF, 0, 0,
                                             nullptr, 0, 0, work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(&work->sprite_group,
                            SpriteTableWord(g_PlaceWinSpriteTable - 0x30), 0x18,
                            SpriteTableWord(g_PlaceWinSpriteTable - 0x18), 0x18,
                            0, 0, 0, 0,
                            SpriteTableWord(g_PlaceWinSpriteTable), 0x70);

    UiAnimSprite_SetupEx(&work->panel_sprite, 0x0E, 0x87, 0, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprite, 0, 0);
}

// DECOMP_FUNC(0x00263bb4, 660)
void PlaceWin_Calc(void* arg) {
    (void)arg;
    PlaceWinWork* work = g_PlaceWinWork;
    if (work == nullptr || work->state == 0) {
        return;
    }

    switch (work->state) {
        case 1: // Appearing / Slide-in
            work->state = 2;
            break;
        case 2: // Displaying area banner
            break;
        case 3: // Fade-out / Dismiss
            work->state = 0;
            break;
        default:
            break;
    }
}

// ============================================================================
// RunWin: Running / Escape Prompt Window (c:\SMT4\XRD686\sdds4\program\font\SearchWin\RunWin.cpp)
// ============================================================================

RunWinWork* g_RunWinWork = nullptr; // 0x0043E158
static const u8 g_RunWinSpriteTable[0x20] = {0};

// DECOMP_FUNC(0x002027dc, 372)
void RunWin_Init() {
    RunWinWork* work = g_RunWinWork;
    if (work == nullptr) {
        work = static_cast<RunWinWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(RunWinWork), 1));
        g_RunWinWork = work;
    }

    AsdMem_Zero(work, sizeof(RunWinWork));

    work->calc_task = AsdTask_CreateCalc("RunWin Calc", 1, 0, 0,
                                         RunWin_DrawDownAndCalc, 0, 0);
    work->draw_down = AsdTask_CreateDraw("RunWin DrawDown", 0xE9, 0, 0,
                                         RunWin_DrawDownAndCalc, 0, 0, work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(&work->sprite_group,
                            SpriteTableWord(g_RunWinSpriteTable - 0x48), 0x24,
                            SpriteTableWord(g_RunWinSpriteTable - 0x24), 0x24,
                            0, 0, 0, 0,
                            SpriteTableWord(g_RunWinSpriteTable), 0x70);

    UiAnimSprite_SetupEx(&work->panel_sprite, 0x0E, 0x87, 0, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprite, 0, 0);
}

// DECOMP_FUNC(0x0018f178, 988)
void RunWin_DrawDownAndCalc(void* arg) {
    (void)arg;
    RunWinWork* work = g_RunWinWork;
    if (work == nullptr || work->state == 0 || !work->visible) {
        return;
    }

    // State machine logic (RunWin_Calc callback slice)
    switch (work->state) {
        case 1: // Entering run state
            if (work->timer > 0) {
                work->timer--;
            } else {
                work->state = 2;
            }
            break;
        case 2: // Running
            break;
        case 3: // Exiting run state
            work->state = 0;
            break;
        default:
            break;
    }

    // Bottom screen HUD draw pass
    UiGpu_BeginPass(g_AsdGpuState);
    UiGpu_SetViewportParams(0, 0); // Bottom screen pass

    auto* layer = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C);
    const u32 old_depth = *layer;
    *layer = old_depth + 1;
    auto* layer_entry = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C + 8);
    layer_entry[*layer] = 1;

    UiSprite_DrawPanelDirect(2, 0x0E, 0x05, 160, 200, 1);

    if (*layer > 0) {
        *layer = *layer - 1;
    }
}

// ============================================================================
// SearchWin: Demonica Radar & Relic Search Window (c:\SMT4\XRD686\sdds4\program\font\SearchWin\SearchWin.cpp)
// ============================================================================

SearchWinWork* g_SearchWinWork = nullptr; // 0x0043E170
static const u8 g_SearchWinSpriteTable[0x20] = {0};

// DECOMP_FUNC(0x002cecd8, 52)
bool SearchWin_IsActive() {
    SearchWinWork* work = g_SearchWinWork;
    if (work == nullptr) {
        return false;
    }
    return work->state != 0;
}

// DECOMP_FUNC(0x002ced0c, 28)
void SearchWin_Dismiss() {
    SearchWinWork* work = g_SearchWinWork;
    if (work != nullptr) {
        work->state = 3;
    }
}

// DECOMP_FUNC(0x002ced28, 348)
void SearchWin_Init() {
    SearchWinWork* work = g_SearchWinWork;
    if (work == nullptr) {
        work = static_cast<SearchWinWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(SearchWinWork), 1));
        g_SearchWinWork = work;
    }

    AsdMem_Zero(work, sizeof(SearchWinWork));

    work->calc_task = AsdTask_CreateCalc("SearchWin Calc", 1, 0, 0,
                                         SearchWin_DrawUpAndCalc, 0, 0);
    work->draw_up_left = AsdTask_CreateDraw("SearchWin DrawUpLeft", 0x81, 0, 0,
                                            SearchWin_DrawUpAndCalc, 0, 0, work->calc_task);
    work->draw_up_right = AsdTask_CreateDraw("SearchWin DrawUpRight", 0xDF, 0, 0,
                                             SearchWin_DrawUpAndCalc, 0, 0, work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(&work->sprite_group,
                            SpriteTableWord(g_SearchWinSpriteTable - 0x48), 0x24,
                            SpriteTableWord(g_SearchWinSpriteTable - 0x24), 0x24,
                            0, 0, 0, 0,
                            SpriteTableWord(g_SearchWinSpriteTable), 0x70);

    UiAnimSprite_SetupEx(&work->panel_sprite, 0x0E, 0x87, 0, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprite, 0, 0);
}

// DECOMP_FUNC(0x001accd4, 1104)
void SearchWin_DrawUpAndCalc(void* arg) {
    (void)arg;
    SearchWinWork* work = g_SearchWinWork;
    if (work == nullptr || work->state == 0 || !work->visible) {
        return;
    }

    // State machine logic (SearchWin_Calc slice)
    switch (work->state) {
        case 1: // Scanning radar sweep
            if (work->timer > 0) {
                work->timer--;
            } else {
                work->state = 2;
            }
            break;
        case 2: // Target locked / prompt active
            break;
        case 3: // Fade out
            work->state = 0;
            break;
        default:
            break;
    }

    // Upper stereoscopic pass (3D radar prompt)
    UiGpu_BeginPass(g_AsdGpuState);
    UiGpu_SetViewportParams(1, 0);

    auto* layer = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C);
    const u32 old_depth = *layer;
    *layer = old_depth + 1;
    auto* layer_entry = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C + 8);
    layer_entry[*layer] = 1;

    // Stereoscopic parallax shift (0.45f scale for radar reticle)
    const f32 shift = UiGpu_TransformCoord(g_AsdGpuState, 0.45f);
    const s32 base_x = static_cast<s32>(shift);

    UiSprite_DrawPanelDirect(2, 0x0E, 0x06, 200 + base_x, 120, 1);

    if (*layer > 0) {
        *layer = *layer - 1;
    }
}

} // namespace smt4::ui
