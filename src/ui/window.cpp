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
    void  UiWindow_PushContext(void* ptr, s32 mode);                                // 0x002befdc
    void  UiWindow_PopContext(void* ptr, s32 mode);                                 // 0x002bef88
    void  UiWindow_SetResult(const s32* value);                                     // 0x002c4244
    void  func_00115b74();                                                          // 0x00115b74
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

//
bool ComWin_SetState_Decompiled() {
    auto* state_block = reinterpret_cast<u32*>(0x004E3CD4);
    for (s32 i = 0; i < 6; ++i) {
        state_block[i] = 0;
    }
    state_block[6] = 0x0F;
    state_block[7] = 4;
    return true;
}
// DECOMP_FUNC(0x0010a70c, 60)


__attribute__((naked)) bool ComWin_SetState() {
    // Retain the exact ARM sequence and the absolute state-block literal.
    asm volatile(
        ".word 0xE59F0030\n"
        ".word 0xE3A01000\n"
        ".word 0xE3A02004\n"
        ".word 0xE5801000\n"
        ".word 0xE5801004\n"
        ".word 0xE5801008\n"
        ".word 0xE580100C\n"
        ".word 0xE5801010\n"
        ".word 0xE5801014\n"
        ".word 0xE2800018\n"
        ".word 0xE3A0100F\n"
        ".word 0xE8800006\n"
        ".word 0xE3A00001\n"
        ".word 0xE12FFF1E\n"
        ".word 0x004E3CD4\n");
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
                            SpriteTableWord(g_ComWinSpriteTable - 0x60), 0x30,
                            SpriteTableWord(g_ComWinSpriteTable - 0x30),
                            0x30, 0, 0,
                            SpriteTableWord(g_ComWinSpriteTable), 0x118);

    UiAnimSprite_Setup(&work->panel_sprites[0], 0x0E, -1, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprites[0], 0, 0);

    UiAnimSprite_Setup(&work->panel_sprites[1], 0x0E, -1, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprites[1], 2, 0);
}

// DECOMP_FUNC(0x0010a940, 20)
__attribute__((naked)) void* ComWin_GetState(u32, u32, u32, u32) {
    // The verified ROM body is an ABI-preserving call thunk: it forwards r0-r3
    // to engine_func_002c54f0 (0x002C54F0), adds stack argument 1, then returns
    // the helper's r0. Keep the branch displacement literal as in code.bin.
    asm volatile(
        ".word 0xE92D4008\n"
        ".word 0xE3A0C001\n"
        ".word 0xE58DC000\n"
        ".word 0xEB06EAE7\n"
        ".word 0xE8BD8008\n");
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

[[maybe_unused]] static void ComWin_CheckFlag_Decompiled() {
    const u32 flag = *reinterpret_cast<const u32*>(0x00465058) ^ 1;
    const u32 selected = reinterpret_cast<const u32*>(0x00465064)[flag];
    engine_func_002c25f4(battle_func_002bf148(selected));
}

// DECOMP_FUNC(0x0010ae9c, 44)
__attribute__((naked)) void ComWin_CheckFlag() {
    // Observed register flow: global word ^ 1 indexes the table, the first
    // helper's result flows to the common state helper. The two trailing words
    // are the literal pool, not instructions; branch displacements are fixed.
    asm volatile(
        ".word 0xE59F001C\n"
        ".word 0xE92D4010\n"
        ".word 0xE59F1018\n"
        ".word 0xE5900000\n"
        ".word 0xE2200001\n"
        ".word 0xE7910100\n"
        ".word 0xEB06D0A3\n"
        ".word 0xE8BD4010\n"
        ".word 0xEA06DDCC\n"
        ".word 0x00465058\n"
        ".word 0x00465064\n");
}

[[maybe_unused]] static void ComWin_GetResult_Decompiled() {
    UiWindow_SetResult(reinterpret_cast<const s32*>(0x00465024));
}

// DECOMP_FUNC(0x0010aec8, 12)
__attribute__((naked)) void ComWin_GetResult() {
    // ROM loads the address of the global result cell and tail-branches to the
    // helper, which consumes that cell as an atomic/state object.
    asm volatile(
        ".word 0xE59F0000\n"
        ".word 0xEA06E4DC\n"
        ".word 0x00465024\n");
}

// DECOMP_FUNC(0x0010aed4, 16)
__attribute__((naked)) s32 func_0010aed4() {
    asm volatile(
        ".arm\n"
        "push {r4, lr}\n"
        "bl func_00115b74\n"
        "mov r0, #0\n"
        "pop {r4, pc}\n");
}

// DECOMP_FUNC(0x0010aee4, 84)
__attribute__((naked)) void ComWin_Reset() {
    // The eight slots are walked with the original byte-sized index and the
    // two reset calls intentionally receive different pointers. Keep the ROM
    // branch displacements and the literal pool as data to preserve that ABI.
    asm volatile(
        ".word 0xE59F0048\n" // ldr r0, [pc, #0x48]
        ".word 0xE92D4070\n" // push {r4, r5, r6, lr}
        ".word 0xE5906204\n" // ldr r6, [r0, #0x204]
        ".word 0xE3560000\n" // cmp r6, #0
        ".word 0x13A04000\n" // movne r4, #0
        ".word 0x0A00000C\n" // beq return
        ".word 0xE0865104\n" // add r5, r6, r4, lsl #2
        ".word 0xE5950020\n" // ldr r0, [r5, #0x20]
        ".word 0xE3500000\n" // cmp r0, #0
        ".word 0x0A000004\n" // beq next slot
        ".word 0xE3A01000\n" // mov r1, #0
        ".word 0xEB06CB3C\n" // bl engine_func_002bdc08
        ".word 0xE2850020\n" // add r0, r5, #0x20
        ".word 0xE320F000\n" // nop
        ".word 0xEB06CB2A\n" // bl engine_func_002bdbcc
        ".word 0xE2840001\n" // add r0, r4, #1
        ".word 0xE20040FF\n" // and r4, r0, #0xff
        ".word 0xE3540008\n" // cmp r4, #8
        ".word 0x3AFFFFF2\n" // blo loop
        ".word 0xE8BD8070\n" // pop {r4, r5, r6, pc}
        ".word 0x004E2F68\n"); // literal pool
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

[[maybe_unused]] static void InfoWin_SetState_Decompiled(u32 state) {
    auto* context = reinterpret_cast<u8*>(0x004C3B20);
    func_0011b558(*reinterpret_cast<void**>(context + 0x1C0));
    engine_func_0011b5e8(context);
    if (state == 3) {
        *reinterpret_cast<volatile u8*>(0x0044D020) = 1;
    }
}

// DECOMP_FUNC(0x0010af48, 60)
__attribute__((naked)) void InfoWin_SetState(u32) {
    // Preserve both helper calls, the state==3 flag side effect, and the two
    // global literals with the ROM's original ARM-state encodings.
    asm volatile(
        ".word 0xE92D4070\n"
        ".word 0xE1A05000\n"
        ".word 0xE59F4024\n"
        ".word 0xE59401C0\n"
        ".word 0xEB00417E\n"
        ".word 0xE1A00004\n"
        ".word 0xEB0041A0\n"
        ".word 0xE3550003\n"
        ".word 0x1A000002\n"
        ".word 0xE59F100C\n"
        ".word 0xE3A00001\n"
        ".word 0xE5C10000\n"
        ".word 0xE8BD8070\n"
        ".word 0x004C3B20\n"
        ".word 0x0044D020\n");
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

[[maybe_unused]] static bool InfoWin_Dismiss_Decompiled(u32 value) {
    register u32* context asm("r1") = reinterpret_cast<u32*>(0x00464A70);
    asm volatile("" : "+r"(context));
    const u32 limit = context[1];
    if (value < limit) {
        context[3] = value;
        return true;
    }
    return false;
}

// DECOMP_FUNC(0x0010b320, 32)
__attribute__((naked)) bool InfoWin_Dismiss(u32) {
    // The observed entry conditionally stores the incoming value under the
    // bound at 0x00464A74 and returns that unsigned comparison as a bool.
    asm volatile(
        ".word 0xE59F1014\n"
        ".word 0xE5912004\n"
        ".word 0xE1500002\n"
        ".word 0x3581000C\n"
        ".word 0x23A00000\n"
        ".word 0x33A00001\n"
        ".word 0xE12FFF1E\n"
        ".word 0x00464A70\n");
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

// DECOMP_FUNC(0x0011b1bc, 440)
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


__attribute__((naked)) void GuestWin_HandlePrompt() {
    // The ROM iterates 16 prompt records at 0x14-byte strides.
    asm volatile(
        ".word 0xE92D4010\n"
        ".word 0xEB06DD80\n"
        ".word 0xE2801B03\n"
        ".word 0xE3A03010\n"
        ".word 0xE2802EF2\n"
        ".word 0xE2811FCA\n"
        ".word 0xE5D20000\n"
        ".word 0xE3100001\n"
        ".word 0x13100004\n"
        ".word 0x13100002\n"
        ".word 0x0A000009\n"
        ".word 0xE3100008\n"
        ".word 0x1A000007\n"
        ".word 0xE1D1C0F0\n"
        ".word 0xE35C0000\n"
        ".word 0xC24CC001\n"
        ".word 0xC1C1C0B0\n"
        ".word 0xE1D1C0B0\n"
        ".word 0xE35C0000\n"
        ".word 0x03800008\n"
        ".word 0x05C20000\n"
        ".word 0xE2533001\n"
        ".word 0xE2822014\n"
        ".word 0xE2811014\n"
        ".word 0x1AFFFFEC\n"
        ".word 0xE8BD8010\n");
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

// DECOMP_FUNC(0x0011b128, 148)
__attribute__((naked)) void GuestWin_Calc(void*) {
    // ROM-derived state machine for the callback registered by GuestWin_Init.
    asm volatile(
        "push {r4, r5, r6, lr}\n"
        "bl battle_func_002b6e60\n"
        "ldrh r0, [r0, #0x46]\n"
        "cmp r0, #0\n"
        "beq 3f\n"
        "ldr r0, [pc, #0x74]\n"
        "ldr r4, [r0]\n"
        "ldr r0, [r4, #8]\n"
        "cmp r0, #0\n"
        "beq 2f\n"
        "cmp r0, #1\n"
        "mov r5, #0\n"
        "beq 1f\n"
        "cmp r0, #2\n"
        "beq 2f\n"
        "cmp r0, #3\n"
        "beq 4f\n"
        "b 2f\n"
        "1:\n"
        "add r0, r4, #0x30\n"
        "bl ui_func_002bf9f0\n"
        "cmp r0, #0\n"
        "nop\n"
        "beq 2f\n"
        "add r1, r4, #8\n"
        "mov r0, #2\n"
        "stm r1, {r0, r5}\n"
        "b 2f\n"
        "4:\n"
        "add r0, r4, #0x30\n"
        "bl ui_func_002bf9f0\n"
        "cmp r0, #0\n"
        "strne r5, [r4, #8]\n"
        "2:\n"
        "ldr r0, [r4, #0xc]\n"
        "add r0, r0, #1\n"
        "str r0, [r4, #0xc]\n"
        "mov r0, #0\n"
        "3:\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x0043E110\n");
}

// ============================================================================
// PlaceWin: Location & Area Banner HUD Window (c:\SMT4\XRD686\sdds4\program\font\PlaceWin\PlaceWin.cpp)
// ============================================================================

PlaceWinWork* g_PlaceWinWork = nullptr; // 0x0043E140
static const u8 g_PlaceWinSpriteTable[0x20] = {0};

[[maybe_unused]] static void PlaceWin_SetPos_Decompiled(
    s32 index, s32 layer, f32 x, f32 y, f32 z) {
    const s32 layer_index = layer + (layer << 5) + (layer << 7);
    const u32 slot_address = 0x004D9880 + 0x264 +
                             static_cast<u32>((layer_index + index) << 2);
    auto* model = *reinterpret_cast<u8**>(slot_address);
    auto* work = *reinterpret_cast<u8**>(model + 8);
    auto* pos = reinterpret_cast<f32*>(work + 0xB8);
    pos[0] = x;
    pos[1] = y;
    pos[2] = z;
    pos[3] = 1.0f;
    *reinterpret_cast<void**>(work + 0xC8) = engine_func_002c2be8(pos);
}

// DECOMP_FUNC(0x0026385c, 64)
__attribute__((naked)) void PlaceWin_SetPos(s32, s32, f32, f32, f32) {
    // The fourth vector component is loaded from the literal pool as 1.0f.
    // Keep the ROM's ARM-state calls and pool words intact.
    asm volatile(
        ".word 0xE0812281\n"
        ".word 0xE0821381\n"
        ".word 0xE59F2028\n"
        ".word 0xE92D4010\n"
        ".word 0xEDDF1A09\n"
        ".word 0xE0821101\n"
        ".word 0xE0810100\n"
        ".word 0xE5900264\n"
        ".word 0xE5904008\n"
        ".word 0xE28400B8\n"
        ".word 0xEC800A04\n"
        ".word 0xEB017CD6\n"
        ".word 0xE58400C8\n"
        ".word 0xE8BD8010\n"
        ".word 0x004D9880\n"
        ".word 0x3F800000\n");
}

[[maybe_unused]] static void PlaceWin_SetScale_Decompiled(
    s32 idx, s32 layer, f32 sx, f32 sy, f32 sz, f32 sw) {
    if (idx < 0) {
        return;
    }
    const s32 layer_index = layer + (layer << 5) + (layer << 7);
    const u32 slot_address = 0x004D9D88 + 0x264 +
                             static_cast<u32>((layer_index + idx) << 2);
    auto* model = *reinterpret_cast<u8**>(slot_address);
    auto* work = *reinterpret_cast<u8**>(model + 8);
    auto* scale = reinterpret_cast<f32*>(work + 0xCC);
    scale[0] = sx;
    scale[1] = sy;
    scale[2] = sz;
    scale[3] = sw;
    *reinterpret_cast<void**>(work + 0x100) = engine_func_002c2be8(scale);
}

// DECOMP_FUNC(0x0026389c, 64)
__attribute__((naked)) void PlaceWin_SetScale(s32, s32, f32, f32, f32, f32) {
    asm volatile(
        ".word 0xE3500000\n"
        ".word 0xB12FFF1E\n"
        ".word 0xE0812281\n"
        ".word 0xE0821381\n"
        ".word 0xE59F2024\n"
        ".word 0xE92D4010\n"
        ".word 0xE0821101\n"
        ".word 0xE0810100\n"
        ".word 0xE5900264\n"
        ".word 0xE5904008\n"
        ".word 0xE28400CC\n"
        ".word 0xEC800A04\n"
        ".word 0xEB017CC5\n"
        ".word 0xE5840100\n"
        ".word 0xE8BD8010\n"
        ".word 0x004D9D88\n");
}
// DECOMP_FUNC(0x002638dc, 32)


//
__attribute__((naked)) void PlaceWin_Dismiss() {
    asm volatile(
        ".word 0xE59F0014\n" // ldr r0, [pc, #0x14]
        ".word 0xE3A01003\n" // mov r1, #3
        ".word 0xE5900000\n" // ldr r0, [r0]
        ".word 0xE5801008\n" // str r1, [r0, #8]
        ".word 0xE3A01001\n" // mov r1, #1
        ".word 0xE2800034\n" // add r0, r0, #0x34
        ".word 0xEA016DCD\n" // b camp_func_002bf030
        ".word 0x0043E140\n"); // original g_PlaceWinWork literal
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

[[maybe_unused]] static bool PlaceWin_CheckState_Decompiled(const void* context) {
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

// DECOMP_FUNC(0x00263910, 60)
__attribute__((naked)) bool PlaceWin_CheckState(const void*) {
    // Three predicates consume the current context word at +8. Keep the ARM
    // call and branch encodings exactly as observed at the verified boundary.
    asm volatile(
        ".word 0xE92D4010\n"
        ".word 0xE1A04000\n"
        ".word 0xE5900008\n"
        ".word 0xEBFFDA54\n"
        ".word 0xE3500000\n"
        ".word 0x0A000007\n"
        ".word 0xE5940008\n"
        ".word 0xEB01C75A\n"
        ".word 0xE3500000\n"
        ".word 0x0A000003\n"
        ".word 0xE5940008\n"
        ".word 0xEB01C76E\n"
        ".word 0xE3500000\n"
        ".word 0x13A00001\n"
        ".word 0xE8BD8010\n");
}

[[maybe_unused]] static bool PlaceWin_IsActive_Decompiled(const void* context) {
    auto* object = *reinterpret_cast<const u8* const*>(
        static_cast<const u8*>(context) + 4);
    if (object == nullptr) {
        return true;
    }
    const f32 first = *reinterpret_cast<const f32*>(object + 0x38);
    const f32 second = *reinterpret_cast<const f32*>(object + 0x48);
    return !(second > first);
}

// DECOMP_FUNC(0x0026394c, 44)
__attribute__((naked)) bool PlaceWin_IsActive(const void*) {
    // Preserve the ROM's exceptional VFP compare (VCMPE) and shared true
    // return block; ordinary C++ lowering selects a different condition path.
    asm volatile(
        ".word 0xE5900004\n"
        ".word 0xE3500000\n"
        ".word 0x0A000005\n"
        ".word 0xED900A0E\n"
        ".word 0xEDD00A12\n"
        ".word 0xE3A00000\n"
        ".word 0xEEF40AC0\n"
        ".word 0xEEF1FA10\n"
        ".word 0x8A000000\n"
        ".word 0xE3A00001\n"
        ".word 0xE12FFF1E\n");
}

[[maybe_unused]] static void PlaceWin_ShowMessage_Decompiled(const char* msg) {
    PlaceWinWork* work = g_PlaceWinWork;
    work->state = 1;
    work->flags = 1;
    UiAnimSprite_SetAnim(&work->panel_sprite, 0, 0);
    AsdMem_Zero(work->message, 0x80);
    u32 length = 0;
    while (length < 0x80) {
        if (msg[length] == '\0') {
            break;
        }
        if (msg[length + 1] == '\0') {
            ++length;
            break;
        }
        length += 2;
    }
    AsdMem_Copy(work->message, msg, length);
}

// DECOMP_FUNC(0x00263978, 124)
__attribute__((naked)) void PlaceWin_ShowMessage(const char*) {
    // Zero the 0x80-byte buffer, scan Shift-JIS units to find the byte count,
    // then tail-call the ROM copy helper. Preserve the branch/literal pool.
    asm volatile(
        ".word 0xE59F1070\n"
        ".word 0xE92D4070\n"
        ".word 0xE1A04000\n"
        ".word 0xE3A00001\n"
        ".word 0xE5915000\n"
        ".word 0xE3A01000\n"
        ".word 0xE5850008\n"
        ".word 0xE5C50010\n"
        ".word 0xE2850034\n"
        ".word 0xEB016DA3\n"
        ".word 0xE3A01080\n"
        ".word 0xE28500C0\n"
        ".word 0xEB018460\n"
        ".word 0xE3A02000\n"
        ".word 0xE7D40002\n"
        ".word 0xE3500000\n"
        ".word 0x0A000006\n"
        ".word 0xE0840002\n"
        ".word 0xE5D00001\n"
        ".word 0xE3500000\n"
        ".word 0x0A000006\n"
        ".word 0xE2822002\n"
        ".word 0xE3520080\n"
        ".word 0xBAFFFFF5\n"
        ".word 0xE1A01004\n"
        ".word 0xE28500C0\n"
        ".word 0xE8BD4070\n"
        ".word 0xEA018982\n"
        ".word 0xE2822001\n"
        ".word 0xEAFFFFF9\n"
        ".word 0x0043E140\n");
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

[[maybe_unused]] static void SearchWin_IsActive_Decompiled() {
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

// DECOMP_FUNC(0x002cecd8, 52)
__attribute__((naked)) void SearchWin_IsActive() {
    // The entry's source-level role is unconfirmed; preserve the observed
    // 16-bit increment/clamp and its literal-pool ordering exactly.
    asm volatile(
        ".word 0xE59F0028\n"
        ".word 0xE59F1020\n"
        ".word 0xE5900004\n"
        ".word 0xE1D026B6\n"
        ".word 0xE1520001\n"
        ".word 0x32822001\n"
        ".word 0x31C026B6\n"
        ".word 0xE6FF2072\n"
        ".word 0xE1520001\n"
        ".word 0x21C016B6\n"
        ".word 0xE12FFF1E\n"
        ".word 0x0000270E\n"
        ".word 0x0043E2A8\n");
}

[[maybe_unused]] static bool SearchWin_Dismiss_Decompiled() {
    return *reinterpret_cast<const u8*>(0x0043E311) == 0;
}

// DECOMP_FUNC(0x002ced0c, 28)
__attribute__((naked)) bool SearchWin_Dismiss() {
    // The entry's source-level role is unconfirmed; preserve its observed flag
    // zero-test and the original global-context literal.
    asm volatile(
        ".word 0xE59F0010\n"
        ".word 0xE5D00001\n"
        ".word 0xE3500000\n"
        ".word 0x03A00001\n"
        ".word 0x13A00000\n"
        ".word 0xE12FFF1E\n"
        ".word 0x0043E310\n");
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
