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
    void* engine_func_002c2be8(const f32* values);                                  // 0x002c2be8
    s32   script_vm_func_0025a274(s32 value);                                       // 0x0025a274
    s32   ui_func_002d569c(s32 value);                                              // 0x002d569c
    s32   ui_func_002d56fc(s32 value);                                              // 0x002d56fc
    void  func_0011b558(void* value);                                               // 0x0011b558
    void  engine_func_0011b5e8(void* value);                                       // 0x0011b5e8
    void  AsdMem_Zero(void* ptr, u32 size);                                         // 0x002c4b30
    void  AsdMem_Copy(void* dst, const void* src, u32 size);                        // 0x002c5ff4
    u32   battle_func_002bf148(u32 value);                                           // 0x002bf148
    void  engine_func_002c25f4(u32 value);                                          // 0x002c25f4
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
    void  UiWindow_PushContext(void* ptr, s32 mode, void* vp_handle);               // 0x002befdc
    void  UiWindow_PopContext(void* ptr, s32 mode);                                 // 0x002bef88
    void  UiWindow_SetResult(const s32* value);                                     // 0x002c4244
    void  func_00115b74();                                                          // 0x00115b74
    void* engine_func_002c54f0(u32 a0, u32 a1, u32 a2, u32 a3, u32 a4);        // 0x002c54f0
    u32   engine_func_002bdc08(void* voice, u32 release);                       // 0x002bdc08
    void  engine_func_002bdbcc(void* ptr);                                      // 0x002bdbcc
    u32   camp_func_002bf030(void* object, u32 selector);                       // 0x002bf030
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
    void* ui_func_002c0ac8();                                                       // 0x002c0ac8
    u32   func_002c00e8(u32);                                                       // 0x002c00e8
    u32   func_002bfcb4(u32, void*);                                                // 0x002bfcb4
    void  func_002bfc88(void*, void*);                                              // 0x002bfc88
    void* battle_func_002b6e60();                                                   // 0x002b6e60
    u32   ui_func_002bf9f0(void*);                                                  // 0x002bf9f0
}

// Forward declaration for task callback
void ComWin_Calc(void* arg);                                                        // 0x0011b094

// DECOMP_FUNC(0x0010a70c, 60)
bool ComWin_SetState() {
    auto* const state_block = reinterpret_cast<u32*>(0x004E3CD4);
    for (s32 i = 0; i < 6; ++i) {
        state_block[i] = 0;
    }
    state_block[6] = 0x0F;
    state_block[7] = 4;
    return true;
}

extern "C" {
    extern const u8 g_ComWinSpriteTable_00403890;                                          // 0x00403890
    extern const u8 g_ComWinSpriteTable_004038c0;                                          // 0x004038c0
}

// DECOMP_FUNC(0x0010a748, 504)
void ComWin_Init() {
    static constexpr u32 kWorkSize = 0x188;
    static constexpr u32 kCalcTag = 1;
    static constexpr u32 kDrawUpLeftTag = 0x81;
    static constexpr u32 kDrawUpRightTag = 0xDF;
    static constexpr s32 kSpriteType = 0x0E;

    u8* work = reinterpret_cast<u8*>(g_ComWinWork);
    if (work == nullptr) {
        work = static_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, kWorkSize, 1));
        g_ComWinWork = reinterpret_cast<ComWinWork*>(work);
    }

    AsdMem_Zero(work, kWorkSize);

    void* const calc_task = AsdTask_CreateCalc(
        "ComWin Calc",
        kCalcTag,
        0,
        0,
        ComWin_Calc,
        0,
        0);
    *reinterpret_cast<void**>(work) = calc_task;

    AsdTask_CreateDraw(
        "ComWin DrawUpLeft",
        kDrawUpLeftTag,
        0,
        0,
        ComWin_DrawUp,
        0,
        0,
        calc_task);

    AsdTask_CreateDraw(
        "ComWin DrawUpRight",
        kDrawUpRightTag,
        0,
        0,
        ComWin_DrawUp,
        0,
        0,
        calc_task);

    u8* const bound_work = reinterpret_cast<u8*>(g_ComWinWork);
    UiSpriteGroup* const sprite_group = reinterpret_cast<UiSpriteGroup*>(bound_work + 0x1C);
    UiAnimSprite* const panel_sprite = reinterpret_cast<UiAnimSprite*>(bound_work + 0x3C);
    UiAnimSprite* const cursor_sprite = reinterpret_cast<UiAnimSprite*>(bound_work + 0xC8);

    UiSpriteGroup_Init(sprite_group);
    UiSpriteGroup_BindTable(
        sprite_group,
        0,
        0,
        SpriteTableWord(&g_ComWinSpriteTable_00403890),
        0x30,
        SpriteTableWord(&g_ComWinSpriteTable_004038c0),
        0x30,
        0,
        0,
        SpriteTableWord(g_ComWinSpriteTable),
        0x118);

    using ComWinSetup = void (*)(UiAnimSprite*, s32, s32, s32, UiSpriteGroup*, u32, f32);
    using ComWinSetAnim = void (*)(UiAnimSprite*, s32);

    reinterpret_cast<ComWinSetup>(UiAnimSprite_Setup)(
        panel_sprite,
        kSpriteType,
        -1,
        2,
        sprite_group,
        1,
        1.0f);
    reinterpret_cast<ComWinSetAnim>(UiAnimSprite_SetAnim)(panel_sprite, 0);

    reinterpret_cast<ComWinSetup>(UiAnimSprite_Setup)(
        cursor_sprite,
        kSpriteType,
        -1,
        3,
        sprite_group,
        1,
        1.0f);
    reinterpret_cast<ComWinSetAnim>(UiAnimSprite_SetAnim)(cursor_sprite, 2);
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void ComWin_Init_Draft() {
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
                            SpriteTableWord(g_ComWinSpriteTable - 0x60), 0x30,
                            SpriteTableWord(g_ComWinSpriteTable - 0x30),
                            0x30, 0, 0,
                            SpriteTableWord(g_ComWinSpriteTable), 0x118);

    UiAnimSprite_Setup(&work->panel_sprites[0], 0x0E, -1, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprites[0], 0, 0);

    UiAnimSprite_Setup(&work->panel_sprites[1], 0x0E, -1, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprites[1], 2, 0);
}
#endif

// DECOMP_FUNC(0x0010a940, 20)
void* ComWin_GetState(u32 a0, u32 a1, u32 a2, u32 a3) {
    return engine_func_002c54f0(a0, a1, a2, a3, 1);
}

// DECOMP_FUNC(0x0010a954, 1352)
extern "C" {
    void        func_001260b8(void* ctx);                                       // 0x001260b8
    void        func_001188d0(void* ctx);                                       // 0x001188d0
    void        func_00124c48(void* arg);                                       // 0x00124c48
    const char* ui_func_002be828(u32 id, s32 mode);                             // 0x002be828
    void        ui_func_002be548(s32 val, s32 x, s32 y, s32 a3, s32 a4);        // 0x002be548
    void        ui_func_002be4dc(s32 a0);                                       // 0x002be4dc
    void        ui_func_002be16c(s32 a0, s32 x, s32 y, s32 a3, s32 a4, s32 a5,
                                 const char* fmt, ...);                         // 0x002be16c
    void        ui_func_002bdeb8(u32 val, s32 x, s32 y, s32 a3);                // 0x002bdeb8
    s32         ui_func_002bef7c(void* sprite);                                   // 0x002bef7c
    s32         ui_func_002bef70(void* sprite);                                   // 0x002bef70
    void        script_vm_func_002bef14();                                      // 0x002bef14
    const u8*   camp_func_002bf6d0(s32 type, s32 id);                           // 0x002bf6d0
    void        func_002bf558(s32 type, s32 id, s32 sub_id,
                              s32 x, s32 y, s32 flag);                          // 0x002bf558
    void        ui_func_002be7fc(char* dst, const char* fmt, ...);              // 0x002be7fc
    void        ui_func_002be77c(s32 align, u32 color, const char* text,
                                 f32 x, f32 y, f32 scale, f32 z, f32 alpha);    // 0x002be77c
}

s32 ComWin_ProcessDialog() {
    auto* const ctx = *reinterpret_cast<u8**>(0x0043E188 + 0x08);
    if (ctx[0x83] != 0) {
        return 0;
    }

    const u8 mode = ctx[0x09];
    if (mode == 0x0B) {
        if (ctx[0x08] != 0) {
            const f32 alpha = *reinterpret_cast<const f32*>(ctx + 0xC4 + 0x20);
            UiGpu_SetAlphaBlend(alpha);
            void* const vp = UiGpu_SetViewportParams(1, 0);
            UiWindow_PushContext(g_AsdGpuState, 3, vp);
            UiSprite_DrawPanelDirect(2, 0x0E, 0x101, 0, 0, 6);
            UiWindow_PopContext(g_AsdGpuState, 3);
            UiGpu_SetAlphaBlend(1.0f);
        }
        func_001260b8(ctx);
        func_001188d0(*reinterpret_cast<u8**>(0x0043E188 + 0x08));
    } else if (mode == 0x13) {
        if (ctx[0x08] != 0) {
            const f32 alpha = *reinterpret_cast<const f32*>(ctx + 0xC4 + 0x20);
            UiGpu_SetAlphaBlend(alpha);
            void* const vp = UiGpu_SetViewportParams(1, 0);
            UiWindow_PushContext(g_AsdGpuState, 3, vp);
            UiSprite_DrawPanelDirect(2, 0x3A, 0x8D, 0, 0, 6);
            UiWindow_PopContext(g_AsdGpuState, 3);
            UiGpu_SetAlphaBlend(1.0f);
        }
        func_001260b8(ctx);
        func_001188d0(*reinterpret_cast<u8**>(0x0043E188 + 0x08));
    }

    auto* const cur = *reinterpret_cast<u8**>(0x0043E188 + 0x08);
    if (cur[0x7D] != 0 && cur[0x7F] == 0) {
        func_00124c48(nullptr);
    }

    auto* const cur2 = *reinterpret_cast<u8**>(0x0043E188 + 0x08);
    if (cur2[0x7E] != 0) {
        const s32 base_x = ui_func_002bef7c(cur2 + 0x754);
        const s32 base_y = ui_func_002bef70(cur2 + 0x754);
        void* const vp = UiGpu_SetViewportParams(1, 0);
        UiWindow_PushContext(g_AsdGpuState, 3, vp);
        UiGpu_SetAlphaBlend(1.0f);
        script_vm_func_002bef14();

        const u8* const panel = camp_func_002bf6d0(0x0E, 0xC8);
        func_002bf558(
            2,
            0x0E,
            0x0A,
            *reinterpret_cast<const s16*>(panel + 0x08) + base_x,
            *reinterpret_cast<const s16*>(panel + 0x0A) + base_y,
            0x0B);

        char text_buf[0x40];
        const char* const name_str = ui_func_002be828(
            *reinterpret_cast<const u32*>((*reinterpret_cast<u8**>(0x0043E188 + 0x08)) + 0x68),
            0);
        ui_func_002be7fc(text_buf, "%s", name_str);

        const u8* const name_layout = camp_func_002bf6d0(0x0E, 0xC2);
        const s32 name_x = *reinterpret_cast<const s16*>(name_layout + 0x08) + *reinterpret_cast<const s16*>(panel + 0x08) + base_x;
        const s32 name_y = *reinterpret_cast<const s16*>(name_layout + 0x0A) + *reinterpret_cast<const s16*>(panel + 0x0A) + base_y;
        ui_func_002be77c(
            2,
            0xFF,
            text_buf,
            static_cast<f32>(name_x),
            static_cast<f32>(name_y),
            0.0f,
            0.0f,
            1.0f);

        const u8* const icon_layout = camp_func_002bf6d0(0x0E, 0xC1);
        const s32 icon_x = *reinterpret_cast<const s16*>(panel + 0x08) + *reinterpret_cast<const s16*>(icon_layout + 0x08) + base_x;
        const s32 icon_y = *reinterpret_cast<const s16*>(panel + 0x0A) + *reinterpret_cast<const s16*>(icon_layout + 0x0A) + base_y;
        const s16 item_id = static_cast<s16>(*reinterpret_cast<const u32*>((*reinterpret_cast<u8**>(0x0043E188 + 0x08)) + 0x68));
        ui_func_002be548(item_id, icon_x, icon_y, 0x10, 0);

        ui_func_002be4dc(0xFF);
        const u8* const count_layout = camp_func_002bf6d0(0x0E, 0xC6);
        const s32 count_x = *reinterpret_cast<const s16*>(count_layout + 0x08) + *reinterpret_cast<const s16*>(panel + 0x08) + base_x;
        const s32 count_y = *reinterpret_cast<const s16*>(count_layout + 0x0A) + *reinterpret_cast<const s16*>(panel + 0x0A) + base_y;
        const u32 count_val = *reinterpret_cast<const u32*>((*reinterpret_cast<u8**>(0x0043E188 + 0x08)) + 0x6C);
        ui_func_002be16c(0, count_x, count_y, 1, 4, 0x10, "%d", count_val);

        const u8* const mul_layout = camp_func_002bf6d0(0x0E, 0xC7);
        const s32 mul_x = *reinterpret_cast<const s16*>(mul_layout + 0x08) + *reinterpret_cast<const s16*>(panel + 0x08) + base_x;
        const s32 mul_y = *reinterpret_cast<const s16*>(mul_layout + 0x0A) + *reinterpret_cast<const s16*>(panel + 0x0A) + base_y;
        ui_func_002be16c(0, mul_x, mul_y, 0, 1, 0x10, "*");

        script_vm_func_002bef14();
        UiWindow_PopContext(g_AsdGpuState, 3);
    }

    auto* const cur3 = *reinterpret_cast<u8**>(0x0043E188 + 0x08);
    if (*reinterpret_cast<const u32*>(cur3 + 0x8C) != 0) {
        const s32 base_x = ui_func_002bef7c(cur3 + 0x984);
        const s32 base_y = ui_func_002bef70(cur3 + 0x984);
        void* const vp = UiGpu_SetViewportParams(1, 0);
        UiWindow_PushContext(g_AsdGpuState, 3, vp);
        UiGpu_SetAlphaBlend(1.0f);
        script_vm_func_002bef14();

        const u8* const panel = camp_func_002bf6d0(0x0E, 0xC0);
        func_002bf558(
            2,
            0x0E,
            0x11,
            *reinterpret_cast<const s16*>(panel + 0x08) + base_x,
            *reinterpret_cast<const s16*>(panel + 0x0A) + base_y,
            0x0B);

        const u16 val = *reinterpret_cast<const u16*>(cur3 + 0x90);
        ui_func_002bdeb8(
            val,
            *reinterpret_cast<const s16*>(panel + 0x08) + base_x,
            *reinterpret_cast<const s16*>(panel + 0x0A) + base_y,
            0);

        s32 idx = -1;
        s32 i = 0;
        for (s32 threshold = 100000000; threshold > 0; threshold /= 10, ++i) {
            if (threshold <= static_cast<s32>(val) && idx < 0) {
                idx = i;
            }
        }
        const u8* const star_layout = camp_func_002bf6d0(0x0E, idx < 0 ? 0x5D : (0x65 - idx));
        ui_func_002be4dc(0xFF);
        const s32 star_x = *reinterpret_cast<const s16*>(panel + 0x08) + *reinterpret_cast<const s16*>(star_layout + 0x08) + base_x;
        const s32 star_y = *reinterpret_cast<const s16*>(panel + 0x0A) + *reinterpret_cast<const s16*>(star_layout + 0x0A) + base_y;
        ui_func_002be16c(0, star_x, star_y, 0, 0x0F, 0x10, "*");

        script_vm_func_002bef14();
        UiWindow_PopContext(g_AsdGpuState, 3);
    }

    return 0;
}

// DECOMP_FUNC(0x0010ae9c, 44)
void ComWin_CheckFlag() {
    const u32 flag = *reinterpret_cast<const u32*>(0x00465058) ^ 1;
    const u32 selected = reinterpret_cast<const u32*>(0x00465064)[flag];
    engine_func_002c25f4(battle_func_002bf148(selected));
}

// DECOMP_FUNC(0x0010aec8, 12)
void ComWin_GetResult() {
    UiWindow_SetResult(reinterpret_cast<const s32*>(0x00465024));
}

// DECOMP_FUNC(0x0010aed4, 16)
s32 func_0010aed4() {
    func_00115b74();
    return 0;
}

// DECOMP_FUNC(0x0010aee4, 84)
void ComWin_Reset() {
    auto* const context = *reinterpret_cast<u8**>(0x004E2F68 + 0x204);
    if (context == nullptr) {
        return;
    }
    for (u32 i = 0; i < 8; ++i) {
        auto* const slot = context + (i << 2);
        void* const entry = *reinterpret_cast<void**>(slot + 0x20);
        if (entry != nullptr) {
            engine_func_002bdc08(entry, 0);
            engine_func_002bdbcc(slot + 0x20);
        }
    }
}

// DECOMP_FUNC(0x0011a354, 1632)
extern "C" {
    void engine_func_002c0000(void* dst, const void* src);                       // 0x002c0000
    void ui_func_002b71f8(void* dst, const void* a, const void* b);             // 0x002b71f8
    void ui_func_002b9438(void* gpu_state, const void* mtx);                    // 0x002b9438
    s32  ui_func_002b7118(const char* text, s32 a1);                            // 0x002b7118
    void ui_func_002b70f0(s32 id, s32 x, s32 y, s32 z);                         // 0x002b70f0
    void ui_func_002b6f74(s32 id, s32 x, s32 y, s32 z, s32 flag, s32 zero);     // 0x002b6f74
    void ui_func_002b6ecc(u32 id, s32 x, s32 y, s32 z);                         // 0x002b6ecc
    void ui_func_002c1b64(void* gpu_state);                                     // 0x002c1b64
    f32  ui_func_002ba46c(void* gpu_state, f32 scale);                          // 0x002ba46c
    void* battle_func_002c5fa4(s32 a0, s32 a1, s32 a2);                         // 0x002c5fa4
}

void ComWin_DrawUp(void*) {
    auto* const work = *reinterpret_cast<u8**>(0x0043E0F8);
    if (*reinterpret_cast<const u32*>(work + 0x08) == 0) {
        return;
    }

    UiGpu_BeginPass(g_AsdGpuState);
    const u32 vp_val = static_cast<u32>(reinterpret_cast<uintptr_t>(UiGpu_SetViewportParams(1, 0)));
    auto* const vp_stack = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C);
    const u32 old_vp_depth = vp_stack[0];
    const u32 prev_vp = vp_stack[2 + old_vp_depth];
    vp_stack[0] = old_vp_depth + 1;
    vp_stack[2 + old_vp_depth + 1] = vp_val;
    if (*reinterpret_cast<u8*>(g_AsdGpuState + 0x1264) != 0 || prev_vp != vp_val) {
        auto* const cb = *reinterpret_cast<void (**)(u32, u32)>(g_AsdGpuState + 0x1268);
        cb(vp_val, prev_vp);
        *reinterpret_cast<u8*>(g_AsdGpuState + 0x1264) = 0;
    }

    const s32 stereo_x = static_cast<s32>(ui_func_002ba46c(g_AsdGpuState, 0.29f));
    UiGpu_SetAlphaBlend(*reinterpret_cast<const f32*>(work + 0x5C));

    const f32 kIdentity[16] = {
        1.0f, 0.0f, 0.0f, 0.0f,
        0.0f, 1.0f, 0.0f, 0.0f,
        0.0f, 0.0f, 1.0f, 0.0f,
        0.0f, 0.0f, 0.0f, 1.0f,
    };
    f32 mtx_a[16];
    f32 mtx_b[16];
    engine_func_002c0000(mtx_a, kIdentity);
    engine_func_002c0000(mtx_b, kIdentity);

    const u8* layout = nullptr;
    if (work[0x12] == 0) {
        layout = camp_func_002bf6d0(0x0E, 0xDC);
    }
    if (work[0x12] == 1) {
        layout = camp_func_002bf6d0(0x0E, 0xDD);
    }
    const s16* const dims = *reinterpret_cast<const s16* const*>(layout + 0x0C);
    const s32 cx = *reinterpret_cast<const s16*>(layout + 0x08) + stereo_x + (dims[0] / 2);
    const s32 cy = *reinterpret_cast<const s16*>(layout + 0x0A) + (dims[1] / 2);

    for (s32 i = 0; i < 16; ++i) {
        mtx_b[i] = 0.0f;
    }
    mtx_b[0] = 1.0f;
    mtx_b[3] = static_cast<f32>(cx);
    mtx_b[5] = 1.0f;
    mtx_b[7] = static_cast<f32>(cy);
    mtx_b[10] = 1.0f;
    mtx_b[15] = 1.0f;
    ui_func_002b71f8(mtx_a, mtx_a, mtx_b);

    const f32 scale = *reinterpret_cast<const f32*>(work + 0x60);
    for (s32 i = 0; i < 16; ++i) {
        mtx_b[i] = 0.0f;
    }
    mtx_b[0] = scale;
    mtx_b[5] = scale;
    mtx_b[10] = scale;
    mtx_b[15] = 1.0f;
    ui_func_002b71f8(mtx_a, mtx_a, mtx_b);

    const u8* const layout2 = camp_func_002bf6d0(0x0E, 0x15);
    const s16* const dims2 = *reinterpret_cast<const s16* const*>(layout2 + 0x0C);
    for (s32 i = 0; i < 16; ++i) {
        mtx_b[i] = 0.0f;
    }
    mtx_b[0] = 1.0f;
    mtx_b[3] = static_cast<f32>(-(4 + (dims2[0] / 2)));
    mtx_b[5] = 1.0f;
    mtx_b[7] = static_cast<f32>(-(4 + (dims2[1] / 2)));
    mtx_b[10] = 1.0f;
    mtx_b[15] = 1.0f;
    ui_func_002b71f8(mtx_a, mtx_a, mtx_b);

    ui_func_002b9438(g_AsdGpuState, mtx_a);

    if (*reinterpret_cast<const u32*>(work + 0x08) == 2) {
        UiGpu_SetAlphaBlend(*reinterpret_cast<const f32*>(work + 0xE8));
    }

    auto set_mode = [&](u32 mode_val) {
        auto* const mode_stack = reinterpret_cast<u32*>(g_AsdGpuState + 0x12AC);
        const u32 depth = mode_stack[0];
        const u32 prev = mode_stack[2 + depth];
        mode_stack[2 + depth] = mode_val;
        if (*reinterpret_cast<u8*>(g_AsdGpuState + 0x12C4) != 0 || prev != mode_val) {
            auto* const cb = *reinterpret_cast<void (**)(u32, u32)>(g_AsdGpuState + 0x12C8);
            cb(mode_val, prev);
            *reinterpret_cast<u8*>(g_AsdGpuState + 0x12C4) = 0;
        }
    };

    set_mode(static_cast<u32>(reinterpret_cast<uintptr_t>(battle_func_002c5fa4(6, 1, 0))));
    func_002bf558(2, 0x0E, 3, 0, 0, 0x65);

    set_mode(static_cast<u32>(reinterpret_cast<uintptr_t>(battle_func_002c5fa4(6, 7, 0))));
    UiGpu_SetAlphaBlend(*reinterpret_cast<const f32*>(work + 0x5C));
    func_002bf558(2, 0x0E, 2, 0, 0, 0x6A);

    if (work[0x10] != 0) {
        if (work[0x12] == 0) {
            layout = camp_func_002bf6d0(0x0E, 0xDC);
        }
        if (work[0x12] == 1) {
            layout = camp_func_002bf6d0(0x0E, 0xDD);
        }
        const char* const text = reinterpret_cast<const char*>(work + 0x154);
        const s32 text_w = ui_func_002b7118(text, 4);
        const s16* const ldims = *reinterpret_cast<const s16* const*>(layout + 0x0C);
        const s32 text_x = (ldims[0] - text_w) / 2;
        ui_func_002be77c(
            4,
            0xFF,
            text,
            static_cast<f32>(text_x),
            6.0f,
            0.57f,
            0.0f,
            *reinterpret_cast<const f32*>(work + 0x5C));

        const u32 kind = *reinterpret_cast<const u32*>(work + 0x14);
        if (kind == 1) {
            UiSprite_DrawPanelDirect(2, 0x0E, 0xDF, text_x - 0x0D, 7, 0x6F);
            UiSprite_DrawPanelDirect(2, 0x0E, 0xDE, text_x - 0x0D, 7, 0x74);
        }
        if (kind == 4) {
            ui_func_002b70f0(*reinterpret_cast<const s16*>(work + 0x18), text_x - 0x0D, 8, 0x79);
        }
        if (kind == 2) {
            ui_func_002b6f74(
                *reinterpret_cast<const s16*>(work + 0x18),
                text_x - 0x0D,
                8,
                0x79,
                *reinterpret_cast<const s8*>(work + 0x11),
                0);
        }
        if (kind == 3) {
            ui_func_002be548(*reinterpret_cast<const s16*>(work + 0x18), text_x - 0x0D, 8, 0x79, 0);
        }
        if (kind == 5) {
            ui_func_002b6ecc(*reinterpret_cast<const u16*>(work + 0x18), text_x - 0x0D, 8, 0x79);
        }
    }

    ui_func_002c1b64(g_AsdGpuState);
    UiGpu_SetAlphaBlend(1.0f);

    auto* const vp_pop = reinterpret_cast<u32*>(g_AsdGpuState + 0x124C);
    const u32 cur_depth = vp_pop[0];
    const u32 popped = vp_pop[2 + cur_depth];
    vp_pop[0] = cur_depth - 1;
    const u32 restored = vp_pop[2 + cur_depth - 1];
    if (*reinterpret_cast<u8*>(g_AsdGpuState + 0x1264) != 0 || popped != restored) {
        auto* const cb = *reinterpret_cast<void (**)(u32, u32)>(g_AsdGpuState + 0x1268);
        cb(restored, popped);
        *reinterpret_cast<u8*>(g_AsdGpuState + 0x1264) = 0;
    }
}

void ComWin_Calc(void* arg) {
    (void)arg;
}

InfoWinWork* g_InfoWinWork = nullptr; // 0x0043E128

// DECOMP_FUNC(0x0010af48, 60)
void InfoWin_SetState(u32 state) {
    auto* context = reinterpret_cast<u8*>(0x004C3B20);
    func_0011b558(*reinterpret_cast<void**>(context + 0x1C0));
    engine_func_0011b5e8(context);
    if (state == 3) {
        *reinterpret_cast<volatile u8*>(0x0044D020) = 1;
    }
}

// DECOMP_FUNC(0x0010af84, 560)
void InfoWin_Init() {
    static constexpr u32 kWorkSize = 0x1BC;
    static constexpr u32 kCalcTag = 1;
    static constexpr u32 kDrawUpLeftTag = 0x81;
    static constexpr u32 kDrawUpRightTag = 0xDF;
    static constexpr s32 kSpriteType = 0x0E;
    static constexpr s32 kSpriteId = 0x87;
    static constexpr u32 kTextColor = 0x646464FFu;
    static constexpr u32 kInitialTimer = 0x1E;

    u8* work = reinterpret_cast<u8*>(g_InfoWinWork);
    if (work == nullptr) {
        work = static_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, kWorkSize, 1));
        g_InfoWinWork = reinterpret_cast<InfoWinWork*>(work);
    }

    AsdMem_Zero(work, kWorkSize);

    void* const calc_task = AsdTask_CreateCalc(
        "InfoWin Calc",
        kCalcTag,
        0,
        0,
        InfoWin_Calc,
        0,
        0);
    *reinterpret_cast<void**>(work) = calc_task;

    AsdTask_CreateDraw(
        "InfoWin DrawUpLeft",
        kDrawUpLeftTag,
        0,
        0,
        InfoWin_DrawUp,
        0,
        0,
        calc_task);

    AsdTask_CreateDraw(
        "InfoWin DrawUpRight",
        kDrawUpRightTag,
        0,
        0,
        InfoWin_DrawUp,
        0,
        0,
        calc_task);

    u8* const bound_work = reinterpret_cast<u8*>(g_InfoWinWork);
    UiSpriteGroup* const sprite_group = reinterpret_cast<UiSpriteGroup*>(bound_work + 0x24);
    UiAnimSprite* const panel_sprite = reinterpret_cast<UiAnimSprite*>(bound_work + 0x44);
    UiAnimSprite* const arrow_sprite = reinterpret_cast<UiAnimSprite*>(bound_work + 0xD0);

    UiSpriteGroup_Init(sprite_group);
    UiSpriteGroup_BindTable(
        sprite_group,
        SpriteTableWord(g_InfoWinSpriteTable),
        0x24,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0);

    using InfoWinSetupEx = void (*)(UiAnimSprite*, s32, s32, UiSpriteGroup*, u32, f32);
    reinterpret_cast<InfoWinSetupEx>(UiAnimSprite_SetupEx)(
        panel_sprite,
        kSpriteType,
        kSpriteId,
        sprite_group,
        1,
        1.0f);
    UiAnimSprite_SetMode(panel_sprite, 0, 0);

    reinterpret_cast<InfoWinSetupEx>(UiAnimSprite_SetupEx)(
        arrow_sprite,
        kSpriteType,
        kSpriteId,
        sprite_group,
        1,
        1.0f);
    UiAnimSprite_SetMode(arrow_sprite, 2, 0);

    void* const text_handle = AsdText_CreateDefault(0);
    *reinterpret_cast<void**>(bound_work + 0x1B8) = text_handle;
    AsdText_SetAlpha(text_handle, 0xFFFFFFFFu);
    AsdText_SetColorAndScale(
        *reinterpret_cast<void**>(bound_work + 0x1B8),
        0,
        kTextColor,
        0.0f);

    *reinterpret_cast<u32*>(bound_work + 0x10) = kInitialTimer;
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void InfoWin_Init_Draft() {
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
#endif

// Incomplete first-pass C++ sketch. The extracted body also dereferences the
// input through AsdRef_Get, checks several flags at +0xF60/+0xF63/+0xF99,
// initializes the referenced render object, and updates bytes at +0xF62/+0xF63.
[[maybe_unused]] static void InfoWin_ShowMessage_Draft(const char* msg) {
    (void)msg;
    InfoWinWork* work = g_InfoWinWork;
    if (work == nullptr) {
        return;
    }
    work->state = 1;
    work->timer = 0x1E;
}

// The complete ARM body includes a literal pool word at 0x0010B25C.
// DECOMP_FUNC(0x0010b1b4, 172)
void InfoWin_ShowMessage(const char*) {
    auto* const work = reinterpret_cast<u8*>(ui_func_002c0ac8());
    auto* const f00 = work + 0xF00;

    const u8 b60 = f00[0x60];
    if (b60 == 0) {
        return;
    }
    const u8 b63 = f00[0x63];
    if (b63 != 0) {
        return;
    }

    const u8 b99 = f00[0x99];
    if (b99 == 0) {
        return;
    }
    void* const sound_obj = *reinterpret_cast<void**>(0x0044EA00);
    UiGpu_BeginPass(sound_obj);

    auto* const obj = *reinterpret_cast<u8**>(work + 4);
    *reinterpret_cast<u32*>(obj + 0x14) = 0x200;
    *reinterpret_cast<u32*>(obj + 0x18) = 0x200;

    work[0xF62] = static_cast<u8>(func_002bfcb4(0, obj));
    func_002bfc88(obj, obj);

    *reinterpret_cast<s32*>(obj + 0x14) >>= 1;
    *reinterpret_cast<s32*>(obj + 0x18) >>= 1;

    work[0xF63] = 1;
}

// Incomplete first-pass C++ sketch; the exact body also obtains an object via
// AsdRef_Get and runs its render/state setup path when its control flags allow.
[[maybe_unused]] static void InfoWin_UpdateTimer_Draft() {
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

// The complete ARM body includes its literal pool word at 0x0010B31C.
// DECOMP_FUNC(0x0010b260, 192)
void InfoWin_UpdateTimer() {
    auto* const work = reinterpret_cast<u8*>(ui_func_002c0ac8());
    if (func_002c00e8(0) != 0) {
        work[0xF65] = 1;
        return;
    }

    const u8 b60 = work[0xF60];
    if (b60 == 0) {
        return;
    }

    auto* const f00 = work + 0xF00;
    if (f00[0x64] != 0 || f00[0x65] != 0) {
        return;
    }

    const u8 b99 = f00[0x99];
    if (b99 == 0) {
        return;
    }
    void* const sound_obj = *reinterpret_cast<void**>(0x0044EA00);
    UiGpu_BeginPass(sound_obj);

    auto* const obj = *reinterpret_cast<u8**>(work + 8);
    *reinterpret_cast<u32*>(obj + 0x14) = 0x200;
    *reinterpret_cast<u32*>(obj + 0x18) = 0x200;

    work[0xF62] = static_cast<u8>(func_002bfcb4(0, obj));
    func_002bfc88(obj, obj);

    *reinterpret_cast<s32*>(obj + 0x14) >>= 1;
    *reinterpret_cast<s32*>(obj + 0x18) >>= 1;

    work[0xF64] = 1;
}

// DECOMP_FUNC(0x0010b320, 32)
bool InfoWin_Dismiss(u32 value) {
    u32* context = reinterpret_cast<u32*>(0x00464A70);
    const u32 limit = context[1];
    if (value < limit) {
        context[3] = value;
        return true;
    }
    return false;
}

extern "C" {
    void engine_func_002b9220(void* sprite, u32 a1);                                        // 0x002b9220
    s32  ui_func_002bef7c(void* sprite);                                                    // 0x002bef7c
    s32  ui_func_002bef70(void* sprite);                                                    // 0x002bef70
    const u8* camp_func_002bf6d0(s32 type, s32 id);                                         // 0x002bf6d0
    void func_002b68dc(s32 x, s32 y, s32 w, s32 h);                                         // 0x002b68dc
    void func_002b792c(void* text, s32 x, s32 y, s32 a3, s32 a4, s32 a5, f32 scale);        // 0x002b792c
    void func_002b67f8();                                                                   // 0x002b67f8
}

// DECOMP_FUNC(0x0011ae10, 792)
void InfoWin_DrawUp(void*) {
    static constexpr f32 kParallaxScale = 0.27f;

    auto* const work = reinterpret_cast<u8*>(g_InfoWinWork);
    if (*reinterpret_cast<const u32*>(work + 0x08) == 0 || work[0x20] == 0) {
        return;
    }

    auto sync_viewport = [](u8* vp_stack, void* old_vp, void* target_vp) {
        if (vp_stack[0x18] != 0 || old_vp != target_vp) {
            using ViewportCb = void (*)(void*);
            (*reinterpret_cast<const ViewportCb*>(vp_stack + 0x1C))(target_vp);
            vp_stack[0x18] = 0;
        }
    };

    UiGpu_BeginPass(g_AsdGpuState);

    void* const new_vp = UiGpu_SetViewportParams(1, 0);
    auto* const vp_stack = g_AsdGpuState + 0x124C;
    auto* const vp_idx = reinterpret_cast<s32*>(vp_stack);
    auto* const vp_slots = reinterpret_cast<void**>(vp_stack + 0x08);
    const s32 push_idx = *vp_idx;
    void* const prev_vp = vp_slots[push_idx];
    *vp_idx = push_idx + 1;
    vp_slots[push_idx + 1] = new_vp;
    sync_viewport(vp_stack, prev_vp, new_vp);

    const s32 base_x = ui_func_002bef7c(work + 0x44) +
                       static_cast<s32>(UiGpu_TransformCoord(g_AsdGpuState, kParallaxScale));
    const s32 base_y = ui_func_002bef70(work + 0x44);

    UiSprite_DrawPanelDirect(2, 0x0E, 0x87, base_x, base_y, 0x15);
    UiSprite_DrawPanelDirect(2, 0x0E, 0x88, base_x, base_y, 0x15);

    if (work[0x21] != 0) {
        const u8* const clip_layout = camp_func_002bf6d0(0x0E, 0x87);
        const s16* const rect = *reinterpret_cast<const s16* const*>(clip_layout + 0x0C);
        func_002b68dc(
            base_x + *reinterpret_cast<const s16*>(clip_layout + 0x08),
            base_y + *reinterpret_cast<const s16*>(clip_layout + 0x0A),
            rect[0], rect[1]);

        const u8* const text_layout = camp_func_002bf6d0(0x0E, 0x89);
        const s32 tx = base_x + *reinterpret_cast<const s16*>(text_layout + 0x08);
        const s32 ty = base_y + *reinterpret_cast<const s16*>(text_layout + 0x0A);
        void* const text_obj = *reinterpret_cast<void* const*>(work + 0x1B8);

        if (work[0x23] != 0) {
            func_002b792c(text_obj, tx, ty, 0xC9, 6, 0, 1.0f);
        } else {
            func_002b792c(
                text_obj, tx + *reinterpret_cast<const s32*>(work + 0x18), ty, 0xC9, 6, 0, 1.0f);
            if (work[0x22] != 0) {
                func_002b792c(
                    text_obj, tx + *reinterpret_cast<const s32*>(work + 0x1C), ty, 0xC9, 6, 0, 1.0f);
            }
        }
        func_002b67f8();
    }

    UiSprite_DrawPanelDirect(2, 0x0E, 0x86, base_x, base_y, 0x1F);
    UiSprite_DrawPanelDirect(2, 0x0E, 0x102, base_x, base_y, 0x1F);

    auto* const pop_stack = g_AsdGpuState + 0x124C;
    auto* const pop_idx = reinterpret_cast<s32*>(pop_stack);
    auto* const pop_slots = reinterpret_cast<void**>(pop_stack + 0x08);
    const s32 cur_idx = *pop_idx;
    void* const popped_vp = pop_slots[cur_idx];
    *pop_idx = cur_idx - 1;
    void* const restored_vp = pop_slots[cur_idx - 1];
    sync_viewport(pop_stack, popped_vp, restored_vp);
}

// DECOMP_FUNC(0x0011b1bc, 440)
void InfoWin_Calc(void*) {
    static constexpr s32 kScrollGap = 0x2A;
    static constexpr s32 kScrollDelayFrames = 0x1E;
    static constexpr s32 kCloseTimer = 0x1E;

    u8* const work = reinterpret_cast<u8*>(g_InfoWinWork);
    const u32 state = *reinterpret_cast<const u32*>(work + 0x08);

    switch (state) {
    case 1:
        if (ui_func_002bf9f0(work + 0x44) != 0) {
            if (work[0x23] != 0) {
                *reinterpret_cast<u32*>(work + 0x08) = 4;
            } else {
                *reinterpret_cast<u32*>(work + 0x08) = 2;
                UiAnimSprite_SetMode(reinterpret_cast<UiAnimSprite*>(work + 0xD0), 2, 0);
            }
            *reinterpret_cast<u32*>(work + 0x0C) = 0;
        }
        break;
    case 2: {
        engine_func_002b9220(work + 0xD0, 0);
        const s32 width = ui_func_002bef7c(work + 0xD0);
        *reinterpret_cast<s32*>(work + 0x18) = width;
        if (width <= 0) {
            *reinterpret_cast<s32*>(work + 0x18) = 0;
            *reinterpret_cast<u32*>(work + 0x08) = 3;
            *reinterpret_cast<u32*>(work + 0x0C) = 0;
        }
        *reinterpret_cast<s32*>(work + 0x1C) =
            *reinterpret_cast<const s32*>(work + 0x18) +
            *reinterpret_cast<const s32*>(work + 0x14) +
            kScrollGap;
        break;
    }
    case 3:
        if (*reinterpret_cast<const s32*>(work + 0x0C) > kScrollDelayFrames && work[0x22] != 0) {
            const s32 span = *reinterpret_cast<const s32*>(work + 0x14);
            const s32 x0 = *reinterpret_cast<const s32*>(work + 0x18) - 1;
            *reinterpret_cast<s32*>(work + 0x18) = x0;
            if (x0 < -span) {
                *reinterpret_cast<s32*>(work + 0x18) =
                    *reinterpret_cast<const s32*>(work + 0x1C) + span + kScrollGap;
            }
            const s32 span2 = *reinterpret_cast<const s32*>(work + 0x14);
            const s32 x1 = *reinterpret_cast<const s32*>(work + 0x1C) - 1;
            *reinterpret_cast<s32*>(work + 0x1C) = x1;
            if (x1 < -span2) {
                *reinterpret_cast<s32*>(work + 0x1C) =
                    *reinterpret_cast<const s32*>(work + 0x18) + span2 + kScrollGap;
            }
        }
        break;
    case 4: {
        const s32 timer = *reinterpret_cast<const s32*>(work + 0x10);
        if (timer >= 0 && *reinterpret_cast<const s32*>(work + 0x0C) > timer) {
            *reinterpret_cast<u32*>(work + 0x08) = 5;
            *reinterpret_cast<s32*>(work + 0x10) = kCloseTimer;
            UiAnimSprite_SetMode(reinterpret_cast<UiAnimSprite*>(work + 0x44), 1, 0);
        }
        break;
    }
    case 5:
        if (ui_func_002bf9f0(work + 0x44) != 0) {
            work[0x23] = 0;
            *reinterpret_cast<u32*>(work + 0x08) = 0;
            *reinterpret_cast<u32*>(work + 0x0C) = 0;
        }
        break;
    default:
        break;
    }

    *reinterpret_cast<s32*>(work + 0x0C) += 1;
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void InfoWin_Calc_Draft(void* arg) {
    (void)arg;
    InfoWinWork* work = g_InfoWinWork;
    if (work == nullptr || work->state == 0) {
        return;
    }
    InfoWin_UpdateTimer();
}
#endif

GuestWinWork* g_GuestWinWork = nullptr; // 0x0043E110

void GuestWin_Calc(void* arg);                                                      // 0x0011b128

extern "C" {
    void GuestWin_Calc_0011b128(void*);                                                     // 0x0011b128
    extern const u8 g_GuestWinSpriteTable_00403a08;                                         // 0x00403a08
    extern const u8 g_GuestWinSpriteTable_00403a20;                                         // 0x00403a20
}

// DECOMP_FUNC(0x0010b350, 448)
void GuestWin_Init() {
    static constexpr u32 kWorkSize = 0xBC;
    static constexpr u32 kCalcTag = 1;
    static constexpr u32 kDrawUpLeftTag = 0x81;
    static constexpr u32 kDrawUpRightTag = 0xDF;
    static constexpr s32 kSpriteType = 0x0E;
    static constexpr s32 kSpriteId = 0x87;

    u8* work = reinterpret_cast<u8*>(g_GuestWinWork);
    if (work == nullptr) {
        work = static_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, kWorkSize, 1));
        g_GuestWinWork = reinterpret_cast<GuestWinWork*>(work);
    }

    AsdMem_Zero(work, kWorkSize);

    void* const calc_task = AsdTask_CreateCalc(
        "GuestWin Calc",
        kCalcTag,
        0,
        0,
        GuestWin_Calc_0011b128,
        0,
        0);
    *reinterpret_cast<void**>(work) = calc_task;

    AsdTask_CreateDraw(
        "GuestWin DrawUpLeft",
        kDrawUpLeftTag,
        0,
        0,
        GuestWin_DrawUp,
        0,
        0,
        calc_task);

    AsdTask_CreateDraw(
        "GuestWin DrawUpRight",
        kDrawUpRightTag,
        0,
        0,
        GuestWin_DrawUp,
        0,
        0,
        calc_task);

    u8* const bound_work = reinterpret_cast<u8*>(g_GuestWinWork);
    UiSpriteGroup* const sprite_group = reinterpret_cast<UiSpriteGroup*>(bound_work + 0x10);
    UiAnimSprite* const panel_sprite = reinterpret_cast<UiAnimSprite*>(bound_work + 0x30);

    UiSpriteGroup_Init(sprite_group);
    UiSpriteGroup_BindTable(
        sprite_group,
        SpriteTableWord(&g_GuestWinSpriteTable_00403a08),
        0x18,
        SpriteTableWord(&g_GuestWinSpriteTable_00403a20),
        0x18,
        0,
        0,
        0,
        0,
        SpriteTableWord(g_GuestWinSpriteTable),
        0x70);

    using GuestWinSetupEx = void (*)(UiAnimSprite*, s32, s32, UiSpriteGroup*, u32, f32);
    reinterpret_cast<GuestWinSetupEx>(UiAnimSprite_SetupEx)(
        panel_sprite,
        kSpriteType,
        kSpriteId,
        sprite_group,
        1,
        1.0f);

    using GuestWinSetAnim = void (*)(UiAnimSprite*, s32);
    reinterpret_cast<GuestWinSetAnim>(UiAnimSprite_SetAnim)(
        panel_sprite,
        0);
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void GuestWin_Init_Draft() {
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
#endif

//
void GuestWin_HandlePrompt_Decompiled() {
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
// DECOMP_FUNC(0x0010b510, 104)
void GuestWin_HandlePrompt() {
    auto* const ctx = reinterpret_cast<u8*>(UiEngine_GetContext());

    for (s32 i = 0; i < 16; ++i) {
        auto* const flag_ptr = ctx + 0x3C80 + i * 0x14;
        const u8 flags = *flag_ptr;
        if ((flags & 7) == 7 && !(flags & 8)) {
            auto* const timer_ptr = reinterpret_cast<s16*>(ctx + 0xF28 + i * 0x14);
            s16 timer = *timer_ptr;
            if (timer > 0) {
                timer--;
                *timer_ptr = timer;
            }
            if (timer == 0) {
                *flag_ptr = flags | 8;
            }
        }
    }
}

extern "C" {
    s32   script_vm_func_002b6e78();                                                        // 0x002b6e78
    s32   script_vm_func_002b6e44();                                                        // 0x002b6e44
    void* battle_func_002c5fa4(s32 a0, s32 a1, s32 a2);                                     // 0x002c5fa4
    void  ui_func_002be77c(s32 align, u32 color, const char* text,
                           f32 x, f32 y, f32 scale, f32 z, f32 alpha);                      // 0x002be77c
    void  script_vm_func_002bef14();                                                        // 0x002bef14
    void  battle_func_002beae4(s32 a0, s32 a1, s32 a2, s32 a3,
                               s32 s0, s32 s1, s32 s2, s32 s3,
                               s32 s4, s32 s5, s32 s6, s32 s7, s32 s8);                     // 0x002beae4
    s32   battle_func_002b6e10();                                                           // 0x002b6e10
    const u8* battle_func_002b6d94(s32 a0, u16 a1);                                         // 0x002b6d94
    void  func_002b6c80(u16 a0, s32 x, s32 y, s32 w);                                       // 0x002b6c80
    const char* camp_func_002bd13c(u16 id);                                                 // 0x002bd13c
    void  ui_func_002b6a98(s32 id, s32 x, s32 y, s32 w, s32 a4);                            // 0x002b6a98
    const char* camp_func_002bd258(u16 id);                                                 // 0x002bd258
    void  ui_func_002be7fc(char* dst, const char* fmt, ...);                                // 0x002be7fc
}

// DECOMP_FUNC(0x0011a9b4, 1116)
void GuestWin_DrawUp(void*) {
    static constexpr f32 kParallaxScale = 0.27f;
    static constexpr f32 kTextScale = 0.85f;
    static constexpr u32 kTextColor = 0xFFu;

    auto* const work = reinterpret_cast<u8*>(g_GuestWinWork);
    if (*reinterpret_cast<const u32*>(work + 0x08) == 0) {
        return;
    }
    const s32 guest_state = script_vm_func_002b6e78();
    if (guest_state == 0 || guest_state == 1) {
        return;
    }
    const u8* guest = static_cast<const u8*>(battle_func_002b6e60());
    if (*reinterpret_cast<const u16*>(guest + 0x46) == 0) {
        return;
    }

    auto sync_stack = [](u8* stack, void* old_val, void* target_val) {
        if (stack[0x18] != 0 || old_val != target_val) {
            using StackCb = void (*)(void*);
            (*reinterpret_cast<const StackCb*>(stack + 0x1C))(target_val);
            stack[0x18] = 0;
        }
    };

    auto push_vp = [&](void* val) {
        auto* const stack = g_AsdGpuState + 0x124C;
        auto* const idx_ptr = reinterpret_cast<s32*>(stack);
        auto* const slots = reinterpret_cast<void**>(stack + 0x08);
        const s32 idx = *idx_ptr;
        void* const prev = slots[idx];
        *idx_ptr = idx + 1;
        slots[idx + 1] = val;
        sync_stack(stack, prev, val);
    };

    auto pop_vp = [&]() {
        auto* const stack = g_AsdGpuState + 0x124C;
        auto* const idx_ptr = reinterpret_cast<s32*>(stack);
        auto* const slots = reinterpret_cast<void**>(stack + 0x08);
        const s32 idx = *idx_ptr;
        void* const popped = slots[idx];
        *idx_ptr = idx - 1;
        void* const restored = slots[idx - 1];
        sync_stack(stack, popped, restored);
    };

    auto set_mode = [&](void* val) {
        auto* const stack = g_AsdGpuState + 0x12AC;
        const s32 idx = *reinterpret_cast<const s32*>(stack);
        auto* const slots = reinterpret_cast<void**>(stack + 0x08);
        void* const prev = slots[idx];
        slots[idx] = val;
        sync_stack(stack, prev, val);
    };

    UiGpu_BeginPass(g_AsdGpuState);
    push_vp(UiGpu_SetViewportParams(1, 0));

    s32 base_x = ui_func_002bef7c(work + 0x30) +
                 static_cast<s32>(UiGpu_TransformCoord(g_AsdGpuState, kParallaxScale));
    const s32 raw_y = ui_func_002bef70(work + 0x30);
    const f32 alpha = *reinterpret_cast<const f32*>(work + 0x50);
    UiGpu_SetAlphaBlend(alpha);

    const u8* anchor = camp_func_002bf6d0(0x0E, 0xDA);
    if (script_vm_func_002b6e44() != 0) {
        anchor = camp_func_002bf6d0(0x0E, 0xDB);
    }
    base_x += *reinterpret_cast<const s16*>(anchor + 0x08);
    const s32 base_y = raw_y + *reinterpret_cast<const s16*>(anchor + 0x0A);

    set_mode(battle_func_002c5fa4(6, 1, 0));
    UiSprite_DrawPanelDirect(2, 0x0E, 0xC9, base_x, base_y, 0x15);

    set_mode(battle_func_002c5fa4(6, 7, 0));
    for (s32 sub_id = 0xCA; sub_id <= 0xCD; ++sub_id) {
        UiSprite_DrawPanelDirect(2, 0x0E, sub_id, base_x, base_y, 0x1A);
    }
    UiSprite_DrawPanelDirect(2, 0x0E, 0xCE, base_x, base_y, 0x1F);
    UiSprite_DrawPanelDirect(2, 0x0E, 0xCF, base_x, base_y, 0x1F);

    battle_func_002beae4(
        *reinterpret_cast<const s16*>(guest + 0x2A),
        *reinterpret_cast<const s16*>(guest + 0x0E),
        0, 0,
        0x0E, 0xD0, 0xD3, 0xD2, 0xD1, base_x, base_y, 0x24, 0);

    const u8* const name_layout = camp_func_002bf6d0(0x0E, 0xD9);
    const s32 icon_x = base_x + *reinterpret_cast<const s16*>(name_layout + 0x08);
    const s32 icon_y = base_y + *reinterpret_cast<const s16*>(name_layout + 0x0A);

    char name_buf[32];
    if (battle_func_002b6e10() != 0) {
        const auto* const g1 = static_cast<const u8*>(battle_func_002b6e60());
        const u16 id1 = *reinterpret_cast<const u16*>(g1 + 0x606);
        const auto* const g2 = static_cast<const u8*>(battle_func_002b6e60());
        const s16 id2 = *reinterpret_cast<const s16*>(g2 + 0x604);
        const u8* const entry = battle_func_002b6d94(id2, id1);
        func_002b6c80(*reinterpret_cast<const u16*>(entry + 0x5A), icon_x, icon_y, 0x24);
        const auto* const g3 = static_cast<const u8*>(battle_func_002b6e60());
        ui_func_002be7fc(name_buf, camp_func_002bd13c(*reinterpret_cast<const u16*>(g3 + 0x604)));
    } else {
        const s16 guest_id = *reinterpret_cast<const s16*>(guest + 0x46);
        ui_func_002b6a98(guest_id, icon_x, icon_y, 0x24, 0);
        ui_func_002be7fc(name_buf, camp_func_002bd258(*reinterpret_cast<const u16*>(guest + 0x46)));
    }

    const u8* const label_layout = camp_func_002bf6d0(0x0E, 0xD8);
    const f32 tx = static_cast<f32>(base_x + *reinterpret_cast<const s16*>(label_layout + 0x08));
    const f32 ty = static_cast<f32>(base_y + *reinterpret_cast<const s16*>(label_layout + 0x0A));
    ui_func_002be77c(2, kTextColor, name_buf, tx, ty, kTextScale, 0.0f, alpha);

    script_vm_func_002bef14();
    UiGpu_SetAlphaBlend(1.0f);
    pop_vp();
}

// ============================================================================
// PlaceWin: Location & Area Banner HUD Window (c:\SMT4\XRD686\sdds4\program\font\PlaceWin\PlaceWin.cpp)
// ============================================================================

PlaceWinWork* g_PlaceWinWork = nullptr; // 0x0043E140
static const u8 g_PlaceWinSpriteTable[0x20] = {0};

// DECOMP_FUNC(0x0026385c, 64)
void PlaceWin_SetPos(s32 index, s32 layer, f32 x, f32 y, f32 z) {
    const s32 layer_index = layer + (layer << 5) + (layer << 7);
    const u32 slot_address = 0x004D9880 + 0x264 +
                             static_cast<u32>((layer_index + index) * 4);
    auto* const slot = *reinterpret_cast<u8* const*>(slot_address);
    auto* const target = *reinterpret_cast<u8* const*>(slot + 8);
    auto* const floats = reinterpret_cast<f32*>(target + 0xB8);
    floats[0] = x;
    floats[1] = y;
    floats[2] = z;
    floats[3] = 1.0f;
    *reinterpret_cast<void**>(target + 0xC8) = engine_func_002c2be8(floats);
}

// DECOMP_FUNC(0x0026389c, 64)
void PlaceWin_SetScale(s32 idx, s32 layer, f32 sx, f32 sy, f32 sz, f32 sw) {
    if (idx < 0) {
        return;
    }
    const s32 layer_index = layer + (layer << 5) + (layer << 7);
    const u32 slot_address = 0x004D9D88 + 0x264 +
                             static_cast<u32>((layer_index + idx) * 4);
    auto* const slot = *reinterpret_cast<u8* const*>(slot_address);
    auto* const target = *reinterpret_cast<u8* const*>(slot + 8);
    auto* const floats = reinterpret_cast<f32*>(target + 0xCC);
    floats[0] = sx;
    floats[1] = sy;
    floats[2] = sz;
    floats[3] = sw;
    *reinterpret_cast<void**>(target + 0x100) = engine_func_002c2be8(floats);
}
// DECOMP_FUNC(0x002638dc, 32)
void PlaceWin_Dismiss() {
    auto* const work = *reinterpret_cast<u8**>(0x0043E140);
    *reinterpret_cast<u32*>(work + 8) = 3;
    camp_func_002bf030(work + 0x34, 1);
}

// DECOMP_FUNC(0x002638fc, 20)
void PlaceWin_SetVisible(u8 visible) {
    // The ROM context at 0x0043DA28 holds the object pointer at +4; its
    // visibility byte is at +0x4C5. The ROM performs no null check.
    register u8** context_slot asm("r1") =
        reinterpret_cast<u8**>(0x0043DA28);
    asm volatile("" : "+r"(context_slot));
    auto* context = context_slot[1];
    context[0x4C5] = visible;
}

// DECOMP_FUNC(0x00263910, 60)
bool PlaceWin_CheckState(const void* context) {
    const auto* bytes = static_cast<const u8*>(context);
    if (script_vm_func_0025a274(
            *reinterpret_cast<const s32*>(bytes + 8)) == 0) {
        return false;
    }
    if (ui_func_002d569c(*reinterpret_cast<const s32*>(bytes + 8)) == 0) {
        return false;
    }
    return ui_func_002d56fc(*reinterpret_cast<const s32*>(bytes + 8)) != 0;
}

// DECOMP_FUNC(0x0026394c, 44)
bool PlaceWin_IsActive(const void* context) {
    auto* object = *reinterpret_cast<const u8* const*>(
        static_cast<const u8*>(context) + 4);
    if (object == nullptr) {
        return true;
    }
    const f32 first = *reinterpret_cast<const f32*>(object + 0x38);
    const f32 second = *reinterpret_cast<const f32*>(object + 0x48);
    return !(second > first);
}

// DECOMP_FUNC(0x00263978, 124)
void PlaceWin_ShowMessage(const char* msg) {
    PlaceWinWork* work = g_PlaceWinWork;
    work->state = 1;
    work->flags = 1;
    UiAnimSprite_SetAnim(&work->panel_sprite, 0, 0);
    AsdMem_Zero(work->message, 0x80);
    u32 length = 0;
    while (length < 0x80 && msg[length] != 0) {
        if (msg[length + 1] == 0) {
            length += 1;
            break;
        }
        length += 2;
    }
    AsdString_Strcpy(work->message, msg);
}

extern "C" {
    void PlaceWin_Calc_0032ac30(void*);                                                     // 0x0032ac30
    void PlaceWin_Draw_0032aa84(void*);                                                     // 0x0032aa84
    void camp_func_0029c56c(void*, s32);                                                    // 0x0029c56c
    void camp_func_002a06dc(void*, s32);                                                    // 0x002a06dc
    void engine_func_002a58ec(void*, s32, f32, f32);                                        // 0x002a58ec
    void script_vm_func_002d5780(void*, f32);                                               // 0x002d5780
    void script_vm_func_002e11bc(void*, s32);                                               // 0x002e11bc
    void func_00151404();                                                                   // 0x00151404
    void func_0015555c();                                                                   // 0x0015555c
    extern const u8 g_PlaceWinSpriteTable_00403acc;                                         // 0x00403acc
    extern const u8 g_PlaceWinSpriteTable_00403ae4;                                         // 0x00403ae4
    extern const u8 g_PlaceWinSpriteTable_00403afc;                                         // 0x00403afc
}

// DECOMP_FUNC(0x002639f4, 448)
void PlaceWin_Init() {
    static constexpr u32 kWorkSize = 0x140;
    static constexpr u32 kCalcTag = 1;
    static constexpr u32 kDrawUpLeftTag = 0x81;
    static constexpr u32 kDrawUpRightTag = 0xDF;
    static constexpr s32 kSpriteType = 0x0E;
    static constexpr s32 kSpriteId = 0x87;

    u8* work = reinterpret_cast<u8*>(g_PlaceWinWork);
    if (work == nullptr) {
        work = static_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, kWorkSize, 1));
        g_PlaceWinWork = reinterpret_cast<PlaceWinWork*>(work);
    }

    AsdMem_Zero(work, kWorkSize);

    void* const calc_task = AsdTask_CreateCalc(
        "PlaceWin Calc",
        kCalcTag,
        0,
        0,
        PlaceWin_Calc_0032ac30,
        0,
        0);
    *reinterpret_cast<void**>(work) = calc_task;

    AsdTask_CreateDraw(
        "PlaceWin DrawUpLeft",
        kDrawUpLeftTag,
        0,
        0,
        PlaceWin_Draw_0032aa84,
        0,
        0,
        calc_task);

    AsdTask_CreateDraw(
        "PlaceWin DrawUpRight",
        kDrawUpRightTag,
        0,
        0,
        PlaceWin_Draw_0032aa84,
        0,
        0,
        calc_task);

    u8* const bound_work = reinterpret_cast<u8*>(g_PlaceWinWork);
    UiSpriteGroup* const sprite_group = reinterpret_cast<UiSpriteGroup*>(bound_work + 0x14);
    UiAnimSprite* const panel_sprite = reinterpret_cast<UiAnimSprite*>(bound_work + 0x34);

    UiSpriteGroup_Init(sprite_group);
    UiSpriteGroup_BindTable(
        sprite_group,
        SpriteTableWord(&g_PlaceWinSpriteTable_00403acc),
        0x18,
        SpriteTableWord(&g_PlaceWinSpriteTable_00403ae4),
        0x18,
        0,
        0,
        0,
        0,
        SpriteTableWord(&g_PlaceWinSpriteTable_00403afc),
        0x70);

    using PlaceWinSetupEx = void (*)(UiAnimSprite*, s32, s32, UiSpriteGroup*, u32, f32);
    reinterpret_cast<PlaceWinSetupEx>(UiAnimSprite_SetupEx)(
        panel_sprite,
        kSpriteType,
        kSpriteId,
        sprite_group,
        1,
        1.0f);

    using PlaceWinSetAnim = void (*)(UiAnimSprite*, s32);
    reinterpret_cast<PlaceWinSetAnim>(UiAnimSprite_SetAnim)(
        panel_sprite,
        0);
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void PlaceWin_Init_Draft() {
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
#endif

// DECOMP_FUNC(0x00263bb4, 660)
void PlaceWin_Calc(void* arg, s32 mode) {
    static constexpr f32 kDefaultFade = 0.3f;
    static constexpr f32 kFocusScale = 0.6f;
    static constexpr f32 kFocusPos = 0.1f;

    auto* const work = static_cast<u8*>(arg);
    const s32 prev_mode = *reinterpret_cast<const s32*>(work + 0x550);
    if (prev_mode == mode) {
        return;
    }

    auto get_slot_34 = [work](s32 idx) -> void* {
        return *reinterpret_cast<void**>(work + idx * 4 + 0x34);
    };
    auto get_slot_3c = [work](s32 idx) -> u8* {
        return *reinterpret_cast<u8**>(work + idx * 4 + 0x3C);
    };
    auto get_sub = [&](s32 idx) -> u8* {
        return *reinterpret_cast<u8**>(get_slot_3c(idx) + 0x04);
    };

    if (prev_mode != -1) {
        camp_func_0029c56c(get_slot_3c(prev_mode), 0);
        script_vm_func_002d5780(
            get_slot_34(*reinterpret_cast<const s32*>(work + 0x560)), 0.0f);
        u8* const prev_sub = get_sub(*reinterpret_cast<const s32*>(work + 0x550));
        *reinterpret_cast<f32*>(prev_sub + 0x40) = 0.0f;
        prev_sub[0x58] = 1;
        using VtableFn = void (*)(void*);
        auto* const vtable = *reinterpret_cast<VtableFn* const*>(prev_sub);
        vtable[0x20 / 4](prev_sub);
    }

    *reinterpret_cast<s32*>(work + 0x550) = mode;
    camp_func_002a06dc(get_slot_3c(mode), 0);
    engine_func_002a58ec(
        get_slot_34(*reinterpret_cast<const s32*>(work + 0x560)), mode, 0.0f, 0.0f);
    script_vm_func_002d5780(
        get_slot_34(*reinterpret_cast<const s32*>(work + 0x560)), 1.0f);

    u8* const cur_sub = get_sub(*reinterpret_cast<const s32*>(work + 0x550));
    using BlendFn = f32 (*)(void*, f32, f32);
    const auto blend_fn =
        *reinterpret_cast<const BlendFn*>(cur_sub + 0x4C);
    const f32 blend_res = blend_fn(
        *reinterpret_cast<void* const*>(cur_sub + 0x50),
        *reinterpret_cast<const f32*>(cur_sub + 0x44),
        *reinterpret_cast<const f32*>(cur_sub + 0x48));
    *reinterpret_cast<u32*>(cur_sub + 0x3C) =
        *reinterpret_cast<const u32*>(cur_sub + 0x38);
    *reinterpret_cast<f32*>(cur_sub + 0x38) = blend_res;
    cur_sub[0x58] = 1;

    u8* const sub_after = get_sub(*reinterpret_cast<const s32*>(work + 0x550));
    *reinterpret_cast<f32*>(sub_after + 0x40) = 1.0f;

    if (mode == 0 || mode == 2) {
        script_vm_func_002e11bc(
            get_slot_34(*reinterpret_cast<const s32*>(work + 0x560)),
            mode == 2 ? 1 : 0);
        u8* const mode_sub = get_sub(*reinterpret_cast<const s32*>(work + 0x550));
        *reinterpret_cast<void**>(mode_sub + 0x4C) = reinterpret_cast<void*>(
            mode == 2 ? &func_00151404 : &func_0015555c);
        mode_sub[0x58] = 1;
        PlaceWin_SetScale(0, 0, 1.0f, 1.0f, 1.0f, 1.0f);
        PlaceWin_SetPos(0, 0, kDefaultFade, kDefaultFade, kDefaultFade);
    } else if (mode == 1) {
        script_vm_func_002e11bc(
            get_slot_34(*reinterpret_cast<const s32*>(work + 0x560)), 0);
        u8* const mode_sub = get_sub(*reinterpret_cast<const s32*>(work + 0x550));
        *reinterpret_cast<void**>(mode_sub + 0x4C) =
            reinterpret_cast<void*>(&func_0015555c);
        mode_sub[0x58] = 1;
        PlaceWin_SetScale(0, 0, kFocusScale, kFocusScale, kFocusScale, 1.0f);
        PlaceWin_SetPos(0, 0, kFocusPos, kFocusPos, kFocusPos);
    }
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void PlaceWin_Calc_Draft(void* arg) {
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
#endif

// ============================================================================
// RunWin: Running / Escape Prompt Window (c:\SMT4\XRD686\sdds4\program\font\SearchWin\RunWin.cpp)
// ============================================================================

RunWinWork* g_RunWinWork = nullptr; // 0x0043E158
static const u8 g_RunWinSpriteTable[0x20] = {0};

extern "C" {
    void RunWin_Calc_0018f4ac(void*);                                                       // 0x0018f4ac
    extern const u8 g_RunWinSpriteTable_00403b6c;                                           // 0x00403b6c
    extern const u8 g_RunWinSpriteTable_00403b90;                                           // 0x00403b90
    extern const u8 g_RunWinSpriteTable_00403bb4;                                           // 0x00403bb4
}

// DECOMP_FUNC(0x002027dc, 372)
void RunWin_Init() {
    static constexpr u32 kWorkSize = sizeof(RunWinWork);
    static constexpr u32 kCalcTag = 1;
    static constexpr u32 kDrawDownTag = 0xE9;
    static constexpr s32 kSpriteType = 0x0E;
    static constexpr s32 kSpriteId = 0x87;

    RunWinWork* work = g_RunWinWork;
    if (work == nullptr) {
        work = static_cast<RunWinWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, kWorkSize, 1));
        g_RunWinWork = work;
    }

    AsdMem_Zero(work, kWorkSize);

    work->calc_task = AsdTask_CreateCalc(
        "RunWin Calc",
        kCalcTag,
        0,
        0,
        RunWin_Calc_0018f4ac,
        0,
        0);

    AsdTask_CreateDraw(
        "RunWin DrawDown",
        kDrawDownTag,
        0,
        0,
        RunWin_DrawDownAndCalc,
        0,
        0,
        work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(
        &work->sprite_group,
        SpriteTableWord(&g_RunWinSpriteTable_00403b6c),
        0x24,
        SpriteTableWord(&g_RunWinSpriteTable_00403b90),
        0x24,
        0,
        0,
        0,
        0,
        SpriteTableWord(&g_RunWinSpriteTable_00403bb4),
        0x70);

    using RunWinSetupEx = void (*)(UiAnimSprite*, s32, s32, UiSpriteGroup*, u32, f32);
    reinterpret_cast<RunWinSetupEx>(UiAnimSprite_SetupEx)(
        &work->panel_sprite,
        kSpriteType,
        kSpriteId,
        &work->sprite_group,
        1,
        1.0f);

    using RunWinSetAnim = void (*)(UiAnimSprite*, s32);
    reinterpret_cast<RunWinSetAnim>(UiAnimSprite_SetAnim)(
        &work->panel_sprite,
        0);
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void RunWin_Init_Draft() {
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
#endif

extern "C" {
    void  UiGpu_SetAlphaBlend(f32 alpha);                                                   // 0x002bf710
    void  func_002bf558(s32 type, s32 id, s32 sub_id, s32 x, s32 y, s32 flag);              // 0x002bf558
    void* battle_func_002c5fa4(s32 a0, s32 a1, s32 a2);                                     // 0x002c5fa4
    void  ui_func_002be77c(s32 align, u32 color, const char* text,
                           f32 x, f32 y, f32 scale, f32 z, f32 alpha);                      // 0x002be77c
    void  script_vm_func_002bef14();                                                        // 0x002bef14
}

// DECOMP_FUNC(0x0018f178, 988)
void RunWin_DrawDownAndCalc(void*) {
    static constexpr f32 kParallaxScale = 0.27f;
    static constexpr f32 kTextScale = 0.56640625f;
    static constexpr u32 kTextColor = 0xF49800FFu;

    auto* const work = reinterpret_cast<u8*>(g_RunWinWork);
    if (*reinterpret_cast<const u32*>(work + 0x08) == 0 || work[0x14] == 0) {
        return;
    }

    auto sync_render_mode = [](u8* mode_stack, void* old_mode, void* target_mode) {
        if (mode_stack[0x18] != 0 || old_mode != target_mode) {
            using ModeCb = void (*)(void*);
            (*reinterpret_cast<const ModeCb*>(mode_stack + 0x1C))(target_mode);
            mode_stack[0x18] = 0;
        }
    };

    UiGpu_BeginPass(g_AsdGpuState);
    UiSprite_DrawPanelDirect(2, 0x0E, 0x14F, 0, 0, 0x6D);

    const s32 base_x = ui_func_002bef7c(work + 0x38) +
                       static_cast<s32>(UiGpu_TransformCoord(g_AsdGpuState, kParallaxScale));
    const s32 base_y = ui_func_002bef70(work + 0x38);

    UiGpu_SetAlphaBlend(*reinterpret_cast<const f32*>(work + 0x58));
    func_002bf558(2, 0x0E, 0x13, base_x, base_y, 0x6E);

    void* const new_mode = battle_func_002c5fa4(6, 1, 0);
    auto* const mode_stack = g_AsdGpuState + 0x12AC;
    auto* const mode_idx = reinterpret_cast<s32*>(mode_stack);
    auto* const mode_slots = reinterpret_cast<void**>(mode_stack + 0x08);
    const s32 push_idx = *mode_idx;
    void* const prev_mode = mode_slots[push_idx];
    *mode_idx = push_idx + 1;
    mode_slots[push_idx + 1] = new_mode;
    sync_render_mode(mode_stack, prev_mode, new_mode);

    UiSprite_DrawPanelDirect(2, 0x0E, 0x150, base_x, 0, 0x6F);
    UiSprite_DrawPanelDirect(2, 0x0E, 0x151, base_x, 0, 0x6F);

    auto* const pop_stack = g_AsdGpuState + 0x12AC;
    auto* const pop_idx = reinterpret_cast<s32*>(pop_stack);
    auto* const pop_slots = reinterpret_cast<void**>(pop_stack + 0x08);
    const s32 cur_idx = *pop_idx;
    void* const popped_mode = pop_slots[cur_idx];
    *pop_idx = cur_idx - 1;
    void* const restored_mode = pop_slots[cur_idx - 1];
    sync_render_mode(pop_stack, popped_mode, restored_mode);

    const u8* const text_layout = camp_func_002bf6d0(0x0E, 0x153);
    const f32 tx = static_cast<f32>(base_x - 0x0E + *reinterpret_cast<const s16*>(text_layout + 0x08));
    const f32 ty = static_cast<f32>(base_y + *reinterpret_cast<const s16*>(text_layout + 0x0A));
    ui_func_002be77c(
        4, kTextColor, reinterpret_cast<const char*>(work + 0xC4),
        tx, ty, kTextScale, 0.0f, *reinterpret_cast<const f32*>(work + 0x58));

    const s32 phase = *reinterpret_cast<const s32*>(work + 0x10) / 5;
    const s32 a = phase % 8;
    const s32 b = (a + 7) % 8;
    const s32 c = (phase + 4) % 8;
    const s32 d = (c + 7) % 8;

    for (s32 row = 0; row < 3; ++row) {
        for (s32 col = 0; col < 3; ++col) {
            const s32 idx = row * 3 + col;
            const u8* const cell_layout = camp_func_002bf6d0(0x0E, 0x157 + idx);
            s32 sub_id = 0x154;
            if (idx == a || idx == c) {
                sub_id = 0x155;
            } else if (idx == b || idx == d) {
                sub_id = 0x156;
            }
            UiSprite_DrawPanelDirect(
                2, 0x0E, sub_id,
                base_x + *reinterpret_cast<const s16*>(cell_layout + 0x08),
                *reinterpret_cast<const s16*>(cell_layout + 0x0A),
                0x6F);
        }
    }

    script_vm_func_002bef14();
    UiGpu_SetAlphaBlend(1.0f);
}

// ============================================================================
// SearchWin: Demonica Radar & Relic Search Window (c:\SMT4\XRD686\sdds4\program\font\SearchWin\SearchWin.cpp)
// ============================================================================

SearchWinWork* g_SearchWinWork = nullptr; // 0x0043E170

// DECOMP_FUNC(0x002cecd8, 52)
void SearchWin_IsActive() {
    auto* context = *reinterpret_cast<u8**>(0x0043E2AC);
    auto* counter = reinterpret_cast<u16*>(context + 0x66);
    u16 value = *counter;
    if (value < 0x270E) {
        value = static_cast<u16>(value + 1);
        *counter = value;
    }
    if (value >= 0x270E) {
        *counter = 0x270E;
    }
}

// DECOMP_FUNC(0x002ced0c, 28)
bool SearchWin_Dismiss() {
    return *reinterpret_cast<const u8*>(0x0043E311) == 0;
}

extern "C" {
    void SearchWin_Calc_001ad07c(void*);                                                    // 0x001ad07c
    extern const u8 g_SearchWinSpriteTable_00403c24;                                        // 0x00403c24
    extern const u8 g_SearchWinSpriteTable_00403c48;                                        // 0x00403c48
    extern const u8 g_SearchWinSpriteTable_00403c6c;                                        // 0x00403c6c
}

// DECOMP_FUNC(0x002ced28, 348)
void SearchWin_Init() {
    static constexpr u32 kWorkSize = sizeof(SearchWinWork);
    static constexpr u32 kCalcTag = 1;
    static constexpr u32 kDrawUpLeftTag = 0x81;
    static constexpr u32 kDrawUpRightTag = 0xDF;
    static constexpr s32 kSpriteType = 0x0E;
    static constexpr s32 kSpriteId = 0x87;

    SearchWinWork* work = g_SearchWinWork;
    if (work == nullptr) {
        work = static_cast<SearchWinWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, kWorkSize, 1));
        g_SearchWinWork = work;
    }

    AsdMem_Zero(work, kWorkSize);

    work->calc_task = AsdTask_CreateCalc(
        "SearchWin Calc",
        kCalcTag,
        0,
        0,
        SearchWin_Calc_001ad07c,
        0,
        0);

    AsdTask_CreateDraw(
        "SearchWin DrawUpLeft",
        kDrawUpLeftTag,
        0,
        0,
        SearchWin_DrawUpAndCalc,
        0,
        0,
        work->calc_task);

    AsdTask_CreateDraw(
        "SearchWin DrawUpRight",
        kDrawUpRightTag,
        0,
        0,
        SearchWin_DrawUpAndCalc,
        0,
        0,
        work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(
        &work->sprite_group,
        SpriteTableWord(&g_SearchWinSpriteTable_00403c24),
        0x24,
        SpriteTableWord(&g_SearchWinSpriteTable_00403c48),
        0x24,
        0,
        0,
        0,
        0,
        SpriteTableWord(&g_SearchWinSpriteTable_00403c6c),
        0x70);

    using SearchWinSetupEx = void (*)(UiAnimSprite*, s32, s32, UiSpriteGroup*, u32, f32);
    reinterpret_cast<SearchWinSetupEx>(UiAnimSprite_SetupEx)(
        &work->panel_sprite,
        kSpriteType,
        kSpriteId,
        &work->sprite_group,
        1,
        1.0f);

    using SearchWinSetAnim = void (*)(UiAnimSprite*, s32);
    reinterpret_cast<SearchWinSetAnim>(UiAnimSprite_SetAnim)(
        &work->panel_sprite,
        0);
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void SearchWin_Init_Draft() {
    SearchWinWork* work = g_SearchWinWork;
    if (work == nullptr) {
        work = static_cast<SearchWinWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(SearchWinWork), 1));
        g_SearchWinWork = work;
    }

    AsdMem_Zero(work, sizeof(SearchWinWork));

    work->calc_task = AsdTask_CreateCalc("SearchWin Calc", 1, 0, 0,
                                         SearchWin_DrawUpAndCalc, 0, 0);
    AsdTask_CreateDraw("SearchWin DrawUpLeft", 0x81, 0, 0,
                       SearchWin_DrawUpAndCalc, 0, 0, work->calc_task);
    AsdTask_CreateDraw("SearchWin DrawUpRight", 0xDF, 0, 0,
                       SearchWin_DrawUpAndCalc, 0, 0, work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(&work->sprite_group,
                            0x00403C24u, 0x24,
                            0x00403C48u, 0x24,
                            0, 0, 0, 0,
                            0x00403C6Cu, 0x70);

    // The ROM ABI for 0x002BDB2C takes the sprite group in r3; there is no
    // separate fourth integer argument before it. Keep this corrected
    // six-argument view local because other reconstructed call sites still
    // use their current signatures.
    using SearchWinSetupEx = void (*)(UiAnimSprite*, s32, s32,
                                     UiSpriteGroup*, u32, f32);
    reinterpret_cast<SearchWinSetupEx>(UiAnimSprite_SetupEx)(
        &work->panel_sprite, 0x0E, 0x87, &work->sprite_group, 1, 1.0f);
    // 0x002BF030 consumes (sprite, animation); it initializes its two
    // internal search indices itself, so the source frame argument is not
    // present in the ROM ABI.
    using SearchWinSetAnim = void (*)(UiAnimSprite*, s32);
    reinterpret_cast<SearchWinSetAnim>(UiAnimSprite_SetAnim)(
        &work->panel_sprite, 0);
}
#endif

// DECOMP_FUNC(0x001accd4, 1104)
void SearchWin_DrawUpAndCalc(void*) {
    static constexpr f32 kParallaxScale = 0.27f;
    static constexpr f32 kTextScale = 0.56640625f;
    static constexpr u32 kTextColor = 0xF49800FFu;

    auto* const work = reinterpret_cast<u8*>(g_SearchWinWork);
    if (*reinterpret_cast<const u32*>(work + 0x08) == 0 || work[0x14] == 0) {
        return;
    }

    auto sync_stack = [](u8* stack, void* old_val, void* target_val) {
        if (stack[0x18] != 0 || old_val != target_val) {
            using StackCb = void (*)(void*);
            (*reinterpret_cast<const StackCb*>(stack + 0x1C))(target_val);
            stack[0x18] = 0;
        }
    };

    auto push_stack = [&](u32 offset, void* val) {
        auto* const stack = g_AsdGpuState + offset;
        auto* const idx_ptr = reinterpret_cast<s32*>(stack);
        auto* const slots = reinterpret_cast<void**>(stack + 0x08);
        const s32 idx = *idx_ptr;
        void* const prev = slots[idx];
        *idx_ptr = idx + 1;
        slots[idx + 1] = val;
        sync_stack(stack, prev, val);
    };

    auto pop_stack = [&](u32 offset) {
        auto* const stack = g_AsdGpuState + offset;
        auto* const idx_ptr = reinterpret_cast<s32*>(stack);
        auto* const slots = reinterpret_cast<void**>(stack + 0x08);
        const s32 idx = *idx_ptr;
        void* const popped = slots[idx];
        *idx_ptr = idx - 1;
        void* const restored = slots[idx - 1];
        sync_stack(stack, popped, restored);
    };

    UiGpu_BeginPass(g_AsdGpuState);
    push_stack(0x124C, UiGpu_SetViewportParams(1, 0));

    const s32 base_x = ui_func_002bef7c(work + 0x38) +
                       static_cast<s32>(UiGpu_TransformCoord(g_AsdGpuState, kParallaxScale));
    const s32 base_y = ui_func_002bef70(work + 0x38);

    UiGpu_SetAlphaBlend(*reinterpret_cast<const f32*>(work + 0x58));
    func_002bf558(2, 0x0E, 0x14, base_x, base_y, 0x65);

    push_stack(0x12AC, battle_func_002c5fa4(6, 1, 0));
    func_002bf558(2, 0x0E, 0x15, base_x, base_y, 0x66);
    pop_stack(0x12AC);

    const u8* const text_layout = camp_func_002bf6d0(0x0E, 0x16F);
    const f32 tx = static_cast<f32>(base_x + *reinterpret_cast<const s16*>(text_layout + 0x08));
    const f32 ty = static_cast<f32>(base_y + *reinterpret_cast<const s16*>(text_layout + 0x0A));
    ui_func_002be77c(
        4, kTextColor, reinterpret_cast<const char*>(work + 0xC4),
        tx, ty, kTextScale, 0.0f, *reinterpret_cast<const f32*>(work + 0x58));

    const s32 phase = *reinterpret_cast<const s32*>(work + 0x10) / 5;
    const s32 a = phase % 8;
    const s32 b = (a + 7) % 8;
    const s32 c = (phase + 4) % 8;
    const s32 d = (c + 7) % 8;

    for (s32 row = 0; row < 3; ++row) {
        for (s32 col = 0; col < 3; ++col) {
            const s32 idx = row * 3 + col;
            const u8* const cell_layout = camp_func_002bf6d0(0x0E, 0x170 + idx);
            s32 sub_id = 0x154;
            if (idx == a || idx == c) {
                sub_id = 0x155;
            } else if (idx == b || idx == d) {
                sub_id = 0x156;
            }
            UiSprite_DrawPanelDirect(
                2, 0x0E, sub_id,
                base_x + *reinterpret_cast<const s16*>(cell_layout + 0x08),
                *reinterpret_cast<const s16*>(cell_layout + 0x0A),
                0x6F);
        }
    }

    script_vm_func_002bef14();
    UiGpu_SetAlphaBlend(1.0f);
    pop_stack(0x124C);
}

} // namespace smt4::ui
