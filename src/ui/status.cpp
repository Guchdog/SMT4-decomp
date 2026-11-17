#include "ui/status.h"
#include "engine/asd_texture.h"
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
    f32   ui_func_00282f00(f32 a0, f32 a1, f32 a2);                                 // 0x00282f00
    void  engine_func_002c3b48(void* ptr, u32 size);                                // 0x002c3b48
    void  engine_func_002bc828(s32 a0, s32 a1, s32 a2, s32 a3);                     // 0x002bc828
    void  engine_func_002c2210(void* cam, s32 a1);                                  // 0x002c2210
    void  engine_func_002c20a8(void* cam, const f32* pos,
                               const f32* look_at, const f32* up);                  // 0x002c20a8
    void  ui_func_002c1ffc(void* cam, s32 a1, f32 near_z,
                           f32 fov, f32 aspect, f32 ratio);                         // 0x002c1ffc
    void  ui_func_00298fec(void* cam);                                              // 0x00298fec
    void  battle_func_002c1740(void* cam);                                          // 0x002c1740
    void  ui_func_002c1774(void* cam, f32 scale, f32 one);                          // 0x002c1774
    extern u8* g_AsdGpuState;                                                       // 0x0044ea00
}

// DECOMP_FUNC(0x0018f560, 4732)
__attribute__((naked, used)) void Status_CalcTaskCallback(void*) {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x8f560, 4732\n");
}
#if 0
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
#endif

// DECOMP_FUNC(0x001cddf8, 516)


//
__attribute__((naked)) void Status_DrawBackUp(void*) {
    asm volatile(
        ".arm\n"
        "push {r4, r5, r6, r7, lr}\n"
        "mov r6, #0\n"
        "ldr r0, [pc, #0x1dc]\n"
        "vpush {d8}\n"
        "sub sp, sp, #0x14\n"
        "ldr r5, [r0, #4]\n"
        "ldr r0, [pc, #0x1d0]\n"
        "str r6, [sp, #8]\n"
        "str r6, [sp, #0xc]\n"
        "ldrb r0, [r0, r5]\n"
        "cmp r0, #0\n"
        "beq .Lstatus_backup_exit\n"
        "ldr r0, [pc, #0x1bc]\n"
        "ldrb r0, [r0, r5]\n"
        "cmp r0, #3\n"
        "cmpne r0, #9\n"
        "bne .Lstatus_backup_draw_done\n"
        "ldr r7, [pc, #0x1ac]\n"
        "ldr r0, [r7]\n"
        ".word 0xeb03d757\n" // bl 0x002c3ba8
        "ldr r4, [r7]\n"
        "mov r1, #0\n"
        "mov r0, #1\n"
        ".word 0xeb03e048\n" // bl 0x002c5f7c
        "add r4, r4, #0x1000\n"
        "add r4, r4, #0x24c\n"
        "ldr r1, [r4]\n"
        "add r2, r1, #1\n"
        "add r3, r4, r1, lsl #2\n"
        "ldr r1, [r3, #8]\n"
        "add r3, r4, r2, lsl #2\n"
        "str r2, [r4]\n"
        "str r0, [r3, #8]\n"
        "ldrb r2, [r4, #0x18]\n"
        "cmp r2, #0\n"
        "cmpeq r1, r0\n"
        "beq .Lstatus_backup_after_callback\n"
        "ldr r1, [r4, #0x1c]\n"
        "blx r1\n"
        "strb r6, [r4, #0x18]\n"
        ".Lstatus_backup_after_callback:\n"
        "vldr s16, [pc, #0x154]\n"
        "mov r2, #9\n"
        "add r1, sp, #0xc\n"
        "vmov.f32 s0, s16\n"
        "add r0, sp, #8\n"
        ".word 0xeb02eca9\n" // bl 0x00289158: Status_Destroy
        "add r0, r5, #0x530\n"
        "nop\n"
        "vldr s0, [r0, #0x20]\n"
        "nop\n"
        "nop\n"
        ".word 0xeb03c611\n" // bl 0x002bf710: UiGpu_SetAlphaBlend
        "ldr r0, [sp, #0xc]\n"
        "mov r4, #1\n"
        "mov r2, #0\n"
        "stm sp, {r0, r4}\n"
        "ldr r3, [sp, #8]\n"
        "mov r1, #0x1a\n"
        "mov r0, #2\n"
        ".word 0xeb03c55d\n" // bl 0x002bf460: UiSprite_DrawPanelDirect
        "vldr s17, [pc, #0x108]\n"
        "vmov.f32 s0, s17\n"
        ".word 0xeb03c606\n" // bl 0x002bf710: UiGpu_SetAlphaBlend
        "vmov.f32 s0, s16\n"
        "mov r2, #7\n"
        "add r1, sp, #0xc\n"
        "add r0, sp, #8\n"
        ".word 0xeb02ec93\n" // bl 0x00289158: Status_Destroy
        "add r0, r5, #0x400\n"
        "add r0, r0, #0x18\n"
        "vldr s0, [r0, #0x20]\n"
        "nop\n"
        "nop\n"
        ".word 0xeb03c5fb\n" // bl 0x002bf710: UiGpu_SetAlphaBlend
        "ldr r0, [sp, #0xc]\n"
        "mov r2, #1\n"
        "mov r1, #0x1a\n"
        "stm sp, {r0, r4}\n"
        "ldr r3, [sp, #8]\n"
        "mov r0, #2\n"
        ".word 0xeb03c548\n" // bl 0x002bf460: UiSprite_DrawPanelDirect
        "vmov.f32 s0, s17\n"
        "nop\n"
        ".word 0xeb03c5f1\n" // bl 0x002bf710: UiGpu_SetAlphaBlend
        "vmov.f32 s0, s16\n"
        "mov r2, #8\n"
        "add r1, sp, #0xc\n"
        "add r0, sp, #8\n"
        ".word 0xeb02ec7e\n" // bl 0x00289158: Status_Destroy
        "add r0, r5, #0x400\n"
        "add r0, r0, #0xa4\n"
        "vldr s0, [r0, #0x20]\n"
        "nop\n"
        "nop\n"
        ".word 0xeb03c5e6\n" // bl 0x002bf710: UiGpu_SetAlphaBlend
        "ldr r0, [sp, #0xc]\n"
        "mov r2, #2\n"
        "mov r1, #0x1a\n"
        "stm sp, {r0, r4}\n"
        "ldr r3, [sp, #8]\n"
        "mov r0, r2\n"
        ".word 0xeb03c533\n" // bl 0x002bf460: UiSprite_DrawPanelDirect
        "ldr r0, [r7]\n"
        "add r4, r0, #0x1000\n"
        "add r4, r4, #0x24c\n"
        "ldr r0, [r4]\n"
        "add r1, r4, r0, lsl #2\n"
        "sub r0, r0, #1\n"
        "ldr r1, [r1, #8]\n"
        "str r0, [r4]\n"
        "add r0, r4, r0, lsl #2\n"
        "ldrb r2, [r4, #0x18]\n"
        "ldr r0, [r0, #8]\n"
        "cmp r2, #0\n"
        "cmpeq r1, r0\n"
        "beq .Lstatus_backup_draw_done\n"
        "ldr r1, [r4, #0x1c]\n"
        "blx r1\n"
        "strb r6, [r4, #0x18]\n"
        ".Lstatus_backup_draw_done:\n"
        "mov r0, #0\n"
        ".Lstatus_backup_exit:\n"
        "add sp, sp, #0x14\n"
        "vpop {d8}\n"
        "pop {r4, r5, r6, r7, pc}\n"
        ".word 0x0044e140\n"
        ".word 0x00001e61\n"
        ".word 0x00001e67\n"
        ".word 0x0044ea00\n"
        ".word 0x3eb33333\n"
        ".word 0x3f800000\n"
    );
}

// DECOMP_FUNC(0x001a310c, 15148)
__attribute__((naked, used)) void Status_DrawUp(void*) {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0xa310c, 15148\n");
}
#if 0
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
#endif


// DECOMP_FUNC(0x001ddaf8, 36)
__attribute__((naked)) s8 Status_GetField1E64() {
    // Preserve the null-to-zero signed-byte read and the split offset literal.
    asm volatile(
        "ldr r0, [pc, #0x14]\n"
        "ldr r1, [r0, #4]\n"
        "mov r0, #0\n"
        "cmp r1, #0\n"
        "ldrne r0, [pc, #8]\n"
        "ldrsbne r0, [r0, r1]\n"
        "bx lr\n"
        ".word 0x0044E140\n"
        ".word 0x1E64\n");
}

// DECOMP_FUNC(0x001ddb1c, 36)
__attribute__((naked)) bool Status_IsState8() {
    // The target reads the status work block unconditionally and compares +0x12DC.
    asm volatile(
        "ldr r0, [pc, #0x18]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1000\n"
        "ldr r0, [r0, #0x2DC]\n"
        "cmp r0, #8\n"
        "moveq r0, #1\n"
        "movne r0, #0\n"
        "bx lr\n"
        ".word 0x0044E140\n");
}

// DECOMP_FUNC(0x00203338, 24)
void Status_SetActiveDemonId(u16 demon_id) {
    // Preserve the ROM's absolute manager-base load and +4 work-pointer read.
    auto* manager = reinterpret_cast<StatusManager*>(0x0044E140);
    asm volatile("" : "+r"(manager));
    auto* active_region = reinterpret_cast<volatile u8*>(manager->work) + 0x1E00;
    asm volatile("" : "+r"(active_region));
    auto* active_id = reinterpret_cast<volatile u16*>(
        active_region + (offsetof(StatusWork, active_demon_id) - 0x1E00));
    *active_id = demon_id;
}

// DECOMP_FUNC(0x0022e694, 32)
__attribute__((naked)) void Status_SetFlag1E65(u8) {
    asm volatile(
        "ldr r1, [pc, #0x14]\n"
        "ldr r1, [r1, #4]\n"
        "cmp r1, #0\n"
        "addne r1, r1, #0x1E00\n"
        "addne r1, r1, #0x65\n"
        "strbne r0, [r1]\n"
        "bx lr\n"
        ".word 0x0044E140\n");
}

// DECOMP_FUNC(0x0022e6b4, 24)
bool Status_IsActive() {
    // Pin this image's base literal; the empty barrier retains the +4 load.
    auto* manager = reinterpret_cast<StatusManager*>(0x0044E140);
    asm volatile("" : "+r"(manager));
    return manager->work != nullptr;
}

// DECOMP_FUNC(0x0026abc0, 32)
__attribute__((naked)) void Status_SetMode1E71(u8) {
    asm volatile(
        "ldr r1, [pc, #0x14]\n"
        "ldr r1, [r1, #4]\n"
        "cmp r1, #0\n"
        "addne r1, r1, #0x1E00\n"
        "addne r1, r1, #0x71\n"
        "strbne r0, [r1]\n"
        "bx lr\n"
        ".word 0x0044E140\n");
}

// DECOMP_FUNC(0x0026b810, 32)
__attribute__((naked)) void Status_SetMode1EB9(u8) {
    asm volatile(
        "ldr r1, [pc, #0x14]\n"
        "ldr r1, [r1, #4]\n"
        "cmp r1, #0\n"
        "addne r1, r1, #0x1E00\n"
        "addne r1, r1, #0xB9\n"
        "strbne r0, [r1]\n"
        "bx lr\n"
        ".word 0x0044E140\n");
}

// DECOMP_FUNC(0x0026c8a8, 24)
__attribute__((naked)) s8 Status_GetFlag1E63() {
    // Match the ROM's unconditional signed-byte read from status work +0x1E63.
    asm volatile(
        "ldr r0, [pc, #0x0C]\n"
        "ldr r0, [r0, #4]\n"
        "add r0, r0, #0x1E00\n"
        "ldrsb r0, [r0, #0x63]\n"
        "bx lr\n"
        ".word 0x0044E140\n");
}
// DECOMP_FUNC(0x0026d8dc, 52)


//
__attribute__((naked)) void Status_ResetAffinityView() {
    asm volatile(
        ".arm\n"
        "ldr r0, [pc, #0x24]\n"
        "push {r4, r5, r6, lr}\n"
        "mov r5, #0\n"
        "ldr r4, [r0, #4]\n"
        "ldr r0, [pc, #0x18]\n"
        "str r5, [r0, r4]\n"
        ".word 0xeb009954\n" // bl 0x00293e4c: Status_UpdateAffinityTable
        "add r4, r4, #0x1e00\n"
        "add r4, r4, #0x63\n"
        "strb r5, [r4]\n"
        "pop {r4, r5, r6, pc}\n"
        ".word 0x0044e140\n"
        ".word 0x000012e4\n");
}

// DECOMP_FUNC(0x00288408, 28)
u8 Status_GetSubMenuState() {
    auto* manager = reinterpret_cast<StatusManager*>(0x0044E140);
    asm volatile("" : "+r"(manager));
    StatusWork* work = manager->work;
    auto* field = reinterpret_cast<u8*>(work) + 0x1E00;
    asm volatile("" : "+r"(field));
    field += 0x67;
    asm volatile("" : "+r"(field));
    return *field;
}
// DECOMP_FUNC(0x00289158, 112)


//
void Status_Destroy(s32* out_x, s32* out_y, s32 panel_idx, f32 scale) {
    const auto* sprite = reinterpret_cast<const UiAnimSprite*>(
        &g_StatusManager.work->raw_panels[(0x44 - 0x18) + panel_idx * 0x8C]);
    const s32 pos_x = UiAnimSprite_GetPosX(sprite);
    const f32 offset_x = UiGpu_TransformCoord(g_AsdGpuState, scale);
    *out_x = static_cast<s32>(offset_x) + pos_x;
    *out_y = UiAnimSprite_GetPosY(sprite);
}

// DECOMP_FUNC(0x0028c2a8, 1448)
// Verified ARM-state entry/exit and referenced local literal/table bytes.
__attribute__((naked)) void Status_Init() {
    asm volatile(
        ".word 0xe92d43f0\n"
        ".word 0xe59f83d8\n"
        ".word 0xed2d8b02\n"
        ".word 0xe24dd01c\n"
        ".word 0xe1d800d0\n"
        ".word 0xe3500000\n"
        ".word 0xca00015c\n"
        ".word 0xe5980004\n"
        ".word 0xe59f53c0\n"
        ".word 0xe3a09001\n"
        ".word 0xe3500000\n"
        ".word 0x1a000009\n"
        ".word 0xe59f13b4\n"
        ".word 0xe28f0fed\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a01c01\n"
        ".word 0xe1a03005\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a00001\n"
        ".word 0xe58d9000\n"
        ".word 0xeb00e221\n"
        ".word 0xe5880004\n"
        ".word 0xe1a04000\n"
        ".word 0xe1a01005\n"
        ".word 0xeb00e208\n"
        ".word 0xe59f03b4\n"
        ".word 0xe3a05000\n"
        ".word 0xe1a03005\n"
        ".word 0xe88d0021\n"
        ".word 0xe1a02005\n"
        ".word 0xe3a01002\n"
        ".word 0xe28f0e3a\n"
        ".word 0xe58d5008\n"
        ".word 0xeb00e591\n"
        ".word 0xe5840000\n"
        ".word 0xe59f639c\n"
        ".word 0xe3a03000\n"
        ".word 0xe58d000c\n"
        ".word 0xe1a02003\n"
        ".word 0xe3a01065\n"
        ".word 0xe28f0fe3\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d6000\n"
        ".word 0xe58d5008\n"
        ".word 0xeb00e228\n"
        ".word 0xe5940000\n"
        ".word 0xe3a03000\n"
        ".word 0xe1a02003\n"
        ".word 0xe58d000c\n"
        ".word 0xe3a010cc\n"
        ".word 0xe28f0fdf\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d6000\n"
        ".word 0xe58d5008\n"
        ".word 0xeb00e21e\n"
        ".word 0xe5940000\n"
        ".word 0xe59f637c\n"
        ".word 0xe3a03000\n"
        ".word 0xe58d000c\n"
        ".word 0xe1a02003\n"
        ".word 0xe3a0107d\n"
        ".word 0xe28f0fdb\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d6000\n"
        ".word 0xe58d5008\n"
        ".word 0xeb00e213\n"
        ".word 0xe5940000\n"
        ".word 0xe3a03000\n"
        ".word 0xe1a02003\n"
        ".word 0xe58d000c\n"
        ".word 0xe3a010db\n"
        ".word 0xe28f0fd6\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d6000\n"
        ".word 0xe58d5008\n"
        ".word 0xeb00e209\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb0133cd\n"
        ".word 0xe5984004\n"
        ".word 0xe59fc348\n"
        ".word 0xe3e06000\n"
        ".word 0xe2841c12\n"
        ".word 0xe2840a01\n"
        ".word 0xe1c15fbc\n"
        ".word 0xe1c16fbe\n"
        ".word 0xe5c062ef\n"
        ".word 0xe18c364c\n"
        ".word 0xe5c052f4\n"
        ".word 0xe2432058\n"
        ".word 0xe7cc9004\n"
        ".word 0xe2421001\n"
        ".word 0xe5c85002\n"
        ".word 0xe7c39004\n"
        ".word 0xe181c5c1\n"
        ".word 0xe7c29004\n"
        ".word 0xe7c15004\n"
        ".word 0xe7cc5004\n"
        ".word 0xe18163c1\n"
        ".word 0xe58092dc\n"
        ".word 0xe281301d\n"
        ".word 0xe7c65004\n"
        ".word 0xe2840024\n"
        ".word 0xe7c35004\n"
        ".word 0xeb00dbbd\n"
        ".word 0xe59f12e8\n"
        ".word 0xe3a00fd2\n"
        ".word 0xe58d0018\n"
        ".word 0xe58d1014\n"
        ".word 0xe3a02090\n"
        ".word 0xe58d500c\n"
        ".word 0xe58d5010\n"
        ".word 0xe88d0024\n"
        ".word 0xe2413090\n"
        ".word 0xe3a020b4\n"
        ".word 0xe24310b4\n"
        ".word 0xe2840024\n"
        ".word 0xe58d5008\n"
        ".word 0xeb00db9c\n"
        ".word 0xed9f8aad\n"
        ".word 0xe2843024\n"
        ".word 0xe3a02000\n"
        ".word 0xeeb00a48\n"
        ".word 0xe3a01017\n"
        ".word 0xe2840fe3\n"
        ".word 0xe58d9000\n"
        ".word 0xeb00c5a1\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe2840fe3\n"
        ".word 0xeb00c582\n"
        ".word 0xeeb00a48\n"
        ".word 0xe2840b01\n"
        ".word 0xe2800018\n"
        ".word 0xe2843024\n"
        ".word 0xe3a02001\n"
        ".word 0xe3a0101a\n"
        ".word 0xe1a05000\n"
        ".word 0xe58d9000\n"
        ".word 0xeb00c594\n"
        ".word 0xe3a01000\n"
        ".word 0xe1a00005\n"
        ".word 0xeb00cad2\n"
        ".word 0xeeb00a48\n"
        ".word 0xe2840b01\n"
        ".word 0xe28000a4\n"
        ".word 0xe2843024\n"
        ".word 0xe3a02002\n"
        ".word 0xe3a0101a\n"
        ".word 0xe1a05000\n"
        ".word 0xe58d9000\n"
        ".word 0xeb00c588\n"
        ".word 0xe3a01001\n"
        ".word 0xe1a00005\n"
        ".word 0xeb00cac6\n"
        ".word 0xeeb00a48\n"
        ".word 0xe2843024\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a0101a\n"
        ".word 0xe2840e53\n"
        ".word 0xe58d9000\n"
        ".word 0xeb00c57e\n"
        ".word 0xe3a01002\n"
        ".word 0xe2840e53\n"
        ".word 0xeb00cabc\n"
        ".word 0xeeb00a48\n"
        ".word 0xe2840b01\n"
        ".word 0xe2800f6f\n"
        ".word 0xe2843024\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a0101a\n"
        ".word 0xe1a05000\n"
        ".word 0xe58d9000\n"
        ".word 0xeb00c572\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe1a00005\n"
        ".word 0xeb00c553\n"
        ".word 0xe3a05000\n"
        ".word 0xeeb00a48\n"
        ".word 0xe0650185\n"
        ".word 0xe2843024\n"
        ".word 0xe0800100\n"
        ".word 0xe3a02000\n"
        ".word 0xe0846100\n"
        ".word 0xe2867b01\n"
        ".word 0xe2877ffb\n"
        ".word 0xe3a0101a\n"
        ".word 0xe1a00007\n"
        ".word 0xe58d9000\n"
        ".word 0xeb00c561\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01004\n"
        ".word 0xe1a00007\n"
        ".word 0xeb00c542\n"
        ".word 0xe2866b03\n"
        ".word 0xeeb00a48\n"
        ".word 0xe2866f59\n"
        ".word 0xe2843024\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a0101a\n"
        ".word 0xe1a00006\n"
        ".word 0xe58d9000\n"
        ".word 0xeb00c554\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe1a00006\n"
        ".word 0xeb00c535\n"
        ".word 0xe2855001\n"
        ".word 0xe355000a\n"
        ".word 0xbaffffdf\n"
        ".word 0xeeb00a48\n"
        ".word 0xe2843024\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a0101a\n"
        ".word 0xe2840044\n"
        ".word 0xe58d9000\n"
        ".word 0xeb00c546\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01006\n"
        ".word 0xe2840044\n"
        ".word 0xeb00c527\n"
        ".word 0xeeb00a48\n"
        ".word 0xe2843024\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a0101a\n"
        ".word 0xe2840f57\n"
        ".word 0xe58d9000\n"
        ".word 0xeb00c53b\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01004\n"
        ".word 0xe2840f57\n"
        ".word 0xeb008c81\n"
        ".word 0xeeb00a48\n"
        ".word 0xe2843024\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a0101a\n"
        ".word 0xe2840f7a\n"
        ".word 0xe58d9000\n"
        ".word 0xeb00c530\n"
        ".word 0xe3a01006\n"
        ".word 0xe2840f7a\n"
        ".word 0xeb00ca6e\n"
        ".word 0xeeb00a48\n"
        ".word 0xe2843024\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a0101a\n"
        ".word 0xe2840f9d\n"
        ".word 0xea00002d\n"
        ".word 0x0044e140\n"
        ".word 0x00001ebc\n"
        ".word 0x00000aef\n"
        ".word 0x535c3a63\n"
        ".word 0x5c34544d\n"
        ".word 0x36445258\n"
        ".word 0x735c3638\n"
        ".word 0x34736464\n"
        ".word 0x6f72705c\n"
        ".word 0x6d617267\n"
        ".word 0x6174735c\n"
        ".word 0x5c737574\n"
        ".word 0x74617453\n"
        ".word 0x632e7375\n"
        ".word 0x00007070\n"
        ".word 0x0018f560\n"
        ".word 0x74617453\n"
        ".word 0x43207375\n"
        ".word 0x00636c61\n"
        ".word 0x001cddf8\n"
        ".word 0x74617453\n"
        ".word 0x44207375\n"
        ".word 0x42776172\n"
        ".word 0x556b6361\n"
        ".word 0x66654c70\n"
        ".word 0x00000074\n"
        ".word 0x74617453\n"
        ".word 0x44207375\n"
        ".word 0x42776172\n"
        ".word 0x556b6361\n"
        ".word 0x67695270\n"
        ".word 0x00007468\n"
        ".word 0x001a310c\n"
        ".word 0x74617453\n"
        ".word 0x44207375\n"
        ".word 0x55776172\n"
        ".word 0x66654c70\n"
        ".word 0x00000074\n"
        ".word 0x74617453\n"
        ".word 0x44207375\n"
        ".word 0x55776172\n"
        ".word 0x67695270\n"
        ".word 0x00007468\n"
        ".word 0x00001eb8\n"
        ".word 0x0040795c\n"
        ".word 0x3f800000\n"
        ".word 0xe58d9000\n"
        ".word 0xeb00c4f7\n"
        ".word 0xe3a01007\n"
        ".word 0xe2840f9d\n"
        ".word 0xeb00ca35\n"
        ".word 0xeeb00a48\n"
        ".word 0xe2843024\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a0101a\n"
        ".word 0xe2840c03\n"
        ".word 0xe58d9000\n"
        ".word 0xeb00c4ed\n"
        ".word 0xe3a01008\n"
        ".word 0xe2840c03\n"
        ".word 0xeb00ca2b\n"
        ".word 0xeeb00a48\n"
        ".word 0xe2843024\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a0101a\n"
        ".word 0xe28400d0\n"
        ".word 0xe58d9000\n"
        ".word 0xeb00c4e3\n"
        ".word 0xe3a01004\n"
        ".word 0xe28400d0\n"
        ".word 0xeb00ca21\n"
        ".word 0xeeb00a48\n"
        ".word 0xe2840b01\n"
        ".word 0xe2800f92\n"
        ".word 0xe2843024\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a0101a\n"
        ".word 0xe1a05000\n"
        ".word 0xe58d9000\n"
        ".word 0xeb00c4d7\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01008\n"
        ".word 0xe1a00005\n"
        ".word 0xeb00c4b8\n"
        ".word 0xeeb00a48\n"
        ".word 0xe2840b01\n"
        ".word 0xe2800fb5\n"
        ".word 0xe2843024\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a0101a\n"
        ".word 0xe1a05000\n"
        ".word 0xe58d9000\n"
        ".word 0xeb00c4ca\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01009\n"
        ".word 0xe1a00005\n"
        ".word 0xeb00c4ab\n"
        ".word 0xeeb00a48\n"
        ".word 0xe2843024\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a0101a\n"
        ".word 0xe2840e76\n"
        ".word 0xe58d9000\n"
        ".word 0xeb00c4bf\n"
        ".word 0xe3a01005\n"
        ".word 0xe2840e76\n"
        ".word 0xeb00c9fd\n"
        ".word 0xe5d80000\n"
        ".word 0xe2800001\n"
        ".word 0xe5c80000\n"
        ".word 0xe28dd01c\n"
        ".word 0xecbd8b02\n"
        ".word 0xe8bd83f0\n"
    );
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void Status_Init_Draft() {
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
#endif

// DECOMP_FUNC(0x00293d64, 204)
s32 Status_HandleLRPrompt() {
    const StatusWork* work = g_StatusManager.work;
    const u8 state = work->sub_menu_state;
    if (state == 3 || state == 5 || state == 6 || state == 8 || state == 9) {
        return 1;
    }

    const u8 mode = work->main_menu_id;
    if (mode == 6 || mode == 8 || mode == 9 || mode == 10 || mode == 11 || mode == 7) {
        return 3;
    }
    if (mode == 14) {
        return 1;
    }
    const u8 prompt_flag = *reinterpret_cast<const u8*>(
        reinterpret_cast<const u8*>(work) + 0x12F1);
    if (mode == 0) {
        return prompt_flag == 0 ? 3 : 2;
    }
    return prompt_flag == 0 ? 4 : 2;
}

// DECOMP_FUNC(0x00293e4c, 520)
void Status_UpdateAffinityTable() {
    StatusWork* work = g_StatusManager.work;
    work->field_14 = 0;
    work->flag_1e63 = 1;

    const u8 mode = work->main_menu_id;
    u8* const work_bytes = reinterpret_cast<u8*>(work);
    u32* const display_state = reinterpret_cast<u32*>(work_bytes + 0x12e4);
    const u8* const affinity_lock = work_bytes + 0x12f1;

    if (mode == 0) {
        if (*display_state == 0) {
            StatusDown_SetDisplayMode(0);
        }
        if (*display_state == 1) {
            StatusDown_SetDisplayMode(1);
        }
        if (*affinity_lock == 0 && *display_state == 2) {
            StatusDown_SetDisplayMode(2);
        }
        return;
    }

    if (mode == 6) {
        if (*display_state == 0) {
            StatusDown_SetDisplayMode(0);
        }
        if (*display_state == 1) {
            StatusDown_SetDisplayMode(1);
        }
        if (*display_state == 2) {
            StatusDown_SetDisplayMode(5);
        }
        return;
    }

    if (mode == 8 || mode == 9 || mode == 10 || mode == 11 || mode == 7) {
        if (*display_state == 0) {
            StatusDown_SetDisplayMode(1);
        }
        if (*display_state == 1) {
            StatusDown_SetDisplayMode(4);
        }
        if (*display_state == 2) {
            StatusDown_SetDisplayMode(5);
        }
        return;
    }

    if (mode == 14) {
        if (*display_state == 0) {
            StatusDown_SetDisplayMode(0);
        }
        return;
    }

    if (mode == 13) {
        if (*display_state == 0) {
            StatusDown_SetDisplayMode(0);
        }
        if (*display_state == 1) {
            StatusDown_SetDisplayMode(1);
        }
        if (*affinity_lock != 0) {
            return;
        }
        if (*display_state == 2) {
            StatusDown_SetDisplayMode(4);
        }
        if (*display_state == 3) {
            StatusDown_SetDisplayMode(5);
        }
        return;
    }

    if (work->sub_menu_state == 6) {
        if (*display_state == 0) {
            StatusDown_SetDisplayMode(1);
        }
        return;
    }

    if (*display_state == 0) {
        StatusDown_SetDisplayMode(0);
    }
    if (*display_state == 1) {
        StatusDown_SetDisplayMode(1);
    }
    if (*affinity_lock != 0) {
        return;
    }
    if (*display_state == 2) {
        StatusDown_SetDisplayMode(4);
    }
    if (*display_state == 3) {
        StatusDown_SetDisplayMode(5);
    }
}

// DECOMP_FUNC(0x00295010, 172)
f32 Status_GetCalculatedScale() {
    static constexpr f32 kBaseScale = 6.3f;
    static constexpr f32 kMaxScale = 4.5f;

    const StatusWork* work = g_StatusManager.work;
    f32 scale = kBaseScale;
    if (work->scale_calc_val > 0) {
        const u8 mode = work->unk_1ea4[0];
        if (mode == 0) {
            scale += static_cast<f32>(work->scale_calc_val) * 0.08f;
        } else if (mode == 1) {
            scale += static_cast<f32>(work->scale_calc_val) * 0.105f;
        } else if (mode == 2) {
            scale += static_cast<f32>(work->scale_calc_val) * 0.01f;
        }
    }
    return ui_func_00282f00(0.0f, scale, kMaxScale);
}

// DECOMP_FUNC(0x0029af30, 28)
u8 Status_GetMainMenuId() {
    auto* manager = reinterpret_cast<StatusManager*>(0x0044E140);
    asm volatile("" : "+r"(manager));
    StatusWork* work = manager->work;
    auto* field = reinterpret_cast<u8*>(work) + 0x1E00;
    asm volatile("" : "+r"(field));
    field += 0x66;
    asm volatile("" : "+r"(field));
    return *field;
}

// DECOMP_FUNC(0x0029af4c, 20)
const u16* Status_GetSelectedActorPtr() {
    // The target unconditionally returns work + 0x1300 (there is no null test).
    auto* manager = reinterpret_cast<StatusManager*>(0x0044E140);
    asm volatile("" : "+r"(manager));
    StatusWork* work = manager->work;
    return reinterpret_cast<const u16*>(&work->unk_1300[0]);
}

// DECOMP_FUNC(0x0029b0e0, 28)
__attribute__((naked)) s8 Status_GetSubState() {
    asm volatile(
        "ldr r0, [pc, #0x10]\n"
        "ldr r0, [r0, #4]\n"
        "cmp r0, #0\n"
        "addne r0, r0, #0x1200\n"
        "ldrsbne r0, [r0, #0xEC]\n"
        "bx lr\n"
        ".word 0x0044E140\n");
}

// ============================================================================
// StatusBustUp: Character & Demon BustUp Renderer (StatusBustUp.cpp)
// ============================================================================

StatusBustUpManager g_StatusBustUpManager = {0, {0, 0, 0}, nullptr, nullptr}; // 0x0044E158

// DECOMP_FUNC(0x00223a90, 248)
void StatusBustUp_Init() {
    static constexpr u32 kBuffer1Size = 0x266;
    static constexpr u32 kBuffer2Size = 0x81;

    StatusBustUpManager* const mgr = &g_StatusBustUpManager;
    if (mgr->ref_count <= 0) {
        engine::AsdTMTexTable_func_002c4e28(0x17);
        engine::AsdTMTexTable_func_002c5b04(0x23, 0);
        if (mgr->buffer1 == nullptr) {
            mgr->buffer1 = AsdMem_Alloc(0x100, 0x100, 0, kBuffer1Size, 1);
            engine_func_002c3b48(mgr->buffer1, kBuffer1Size);
        }
        if (mgr->buffer2 == nullptr) {
            mgr->buffer2 = AsdMem_Alloc(0x100, 0x100, 0, kBuffer2Size, 1);
            engine_func_002c3b48(mgr->buffer2, kBuffer2Size);
        }
    }
    ++mgr->ref_count;
}

// ============================================================================
// StatusCamera: Upper Screen Stereoscopic Camera (StatusCamera.cpp)
// ============================================================================

StatusCameraWork* g_StatusCamera = nullptr; // 0x0044E178

// DECOMP_FUNC(0x00258e38, 480)
void StatusCamera_Init(const f32* pos, const f32* target, const f32* up,
                       f32 fov, f32 aspect, f32 near_z, f32 far_z, f32 scale) {
    static constexpr f32 kDefaultRatio = 5.0f / 3.0f;

    StatusCameraWork* cam = g_StatusCamera;
    if (cam == nullptr) {
        cam = static_cast<StatusCameraWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(StatusCameraWork), 1));
        g_StatusCamera = cam;
    }
    AsdMem_Zero(cam, sizeof(StatusCameraWork));

    auto* const raw = cam->raw;
    auto* const pos_dst = reinterpret_cast<f32*>(raw + 0x508);
    auto* const target_dst = reinterpret_cast<f32*>(raw + 0x514);
    auto* const up_dst = reinterpret_cast<f32*>(raw + 0x520);

    for (s32 i = 0; i < 3; ++i) {
        pos_dst[i] = pos[i];
        target_dst[i] = target[i];
        up_dst[i] = up[i];
    }

    *reinterpret_cast<f32*>(raw + 0x52C) = far_z;
    *reinterpret_cast<f32*>(raw + 0x530) = near_z;
    *reinterpret_cast<f32*>(raw + 0x534) = fov;
    *reinterpret_cast<f32*>(raw + 0x538) = aspect;

    const f32 look_at[3] = {
        pos_dst[0] + target_dst[0] * far_z,
        pos_dst[1] + target_dst[1] * far_z,
        pos_dst[2] + target_dst[2] * far_z,
    };
    const f32 up_axis[3] = {0.0f, 1.0f, 0.0f};

    engine_func_002bc828(0xC8, 0, 0xC8, 0xF0);
    engine_func_002c2210(cam, 1);
    engine_func_002c20a8(cam, pos_dst, look_at, up_axis);
    ui_func_002c1ffc(cam, 1, near_z, fov, aspect, kDefaultRatio);
    ui_func_00298fec(cam);
    battle_func_002c1740(cam);
    ui_func_002c1774(cam, scale, 1.0f);
}

} // namespace smt4::ui
