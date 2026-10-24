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
__attribute__((naked)) void Status_Destroy(s32*, s32*, s32, f32) {
    asm volatile(
        ".arm\n"
        "push {r4, r5, r6, r7, r8, lr}\n"
        "mov r5, r0\n"
        "mov r6, r1\n"
        "ldr r0, [pc, #0x54]\n"
        "rsb r1, r2, r2, lsl #3\n"
        "vpush {d8}\n"
        "add r1, r1, r1, lsl #2\n"
        "ldr r0, [r0, #4]\n"
        "vmov.f32 s16, s0\n"
        "add r4, r0, r1, lsl #2\n"
        "add r0, r4, #0x44\n"
        ".word 0xeb00d77c\n" // bl 0x002bef7c: ui_func_002bef7c
        "mov r7, r0\n"
        "ldr r0, [pc, #0x30]\n"
        "vmov.f32 s0, s16\n"
        "ldr r0, [r0]\n"
        ".word 0xeb00c4b3\n" // bl 0x002ba46c: ui_func_002ba46c
        "vcvt.s32.f32 s0, s0\n"
        "vmov r0, s0\n"
        "add r0, r0, r7\n"
        "str r0, [r5]\n"
        "add r0, r4, #0x44\n"
        ".word 0xeb00d76e\n" // bl 0x002bef70: shop_func_002bef70
        "str r0, [r6]\n"
        "vpop {d8}\n"
        "pop {r4, r5, r6, r7, r8, pc}\n"
        ".word 0x0044e140\n"
        ".word 0x0044ea00\n");
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

[[maybe_unused]] static s32 Status_HandleLRPrompt_Decompiled() {
    StatusWork* work = g_StatusManager.work;
    if (work == nullptr) {
        return 1;
    }

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
    if (mode == 13 && prompt_flag == 0) {
        return 4;
    }
    return prompt_flag == 0 ? 3 : 2;
}

// Exact ARM-state restoration of Status.cpp's four-way L/R prompt selector.
// The literal words are the verified 0x00293d64..0x00293e30 span; retaining
// the disassembly here also preserves its branch and literal-pool placement.
// DECOMP_FUNC(0x00293d64, 204)
__attribute__((naked)) s32 Status_HandleLRPrompt() {
    asm volatile(
        ".word 0xE59F00BC, 0xE5901004, 0xE59F00B8, 0xE7D00001\n"
        ".word 0xE3500003, 0x13500005, 0x0A00001C, 0xE3500006\n"
        ".word 0x13500008, 0x13500009, 0x0A000018, 0xE59F0090\n"
        ".word 0xE2811C1E, 0xE2811066, 0xE5902004, 0xE5D10000\n"
        ".word 0xE2821C12, 0xE3500000, 0x0A000012, 0xE3500006\n"
        ".word 0x13500008, 0x0A000014, 0xE3500009, 0x1350000A\n"
        ".word 0x0A000011, 0xE350000B, 0x13500007, 0x0A00000E\n"
        ".word 0xE350000E, 0x0A000005, 0xE350000D, 0xE5D100F1\n"
        ".word 0x0A00000B, 0xE3500000, 0x0A00000B, 0xEA000004\n"
        ".word 0xE3A00001, 0xE12FFF1E, 0xE5D100F1, 0xE3500000\n"
        ".word 0x0A000001, 0xE3A00002, 0xE12FFF1E, 0xE3A00003\n"
        ".word 0xE12FFF1E, 0xE3500000, 0x1AFFFFF9, 0xE3A00004\n"
        ".word 0xE12FFF1E, 0x0044E140, 0x00001E67\n"
    );
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

[[maybe_unused]] static f32 Status_GetCalculatedScale_Decompiled() {
    StatusWork* work = g_StatusManager.work;
    if (work == nullptr || work->scale_calc_val <= 0) {
        return 6.3f;
    }

    const f32 factor = work->unk_1ea4[0] == 0 ? 0.08f :
                       work->unk_1ea4[0] == 1 ? 0.105f :
                       work->unk_1ea4[0] == 2 ? 0.01f : 0.0f;
    return 6.3f + (static_cast<f32>(work->scale_calc_val) * factor);
}

// Exact ARM-state restoration. The mode byte at +0x1EA4 selects one of three
// scale coefficients; unsupported modes and non-positive values keep 6.3f.
// DECOMP_FUNC(0x00295010, 172)
__attribute__((naked)) f32 Status_GetCalculatedScale() {
    asm volatile(
        ".word 0xE59F0090, 0xEDDF0A20, 0xED9F0A20, 0xED9F1A20\n"
        ".word 0xE5901004, 0xE59F0080, 0xE7900001, 0xE3500000\n"
        ".word 0xDA000017, 0xE2811B07, 0xE2811FA9, 0xE5D11000\n"
        ".word 0xE3510000, 0x0A000004, 0xE3510001, 0x0A000007\n"
        ".word 0xE3510002, 0x1A00000E, 0xEA000009, 0xEE010A90\n"
        ".word 0xED9F2A12, 0xEEF81AE1, 0xEE410A82, 0xEA000008\n"
        ".word 0xEE010A90, 0xED9F2A0E, 0xEEF81AE1, 0xEE410A82\n"
        ".word 0xEA000003, 0xEE010A90, 0xED9F2A0A, 0xEEF81AE1\n"
        ".word 0xEE410A82, 0xE320F000, 0xEAFFB798, 0x40C9999A\n"
        ".word 0x00000000, 0x40900000, 0x0044E140, 0x00001EA0\n"
        ".word 0x3DA3D70A, 0x3DD70A3D, 0x3C23D70A\n"
    );
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

[[maybe_unused]] static void StatusBustUp_Init_Decompiled() {
    StatusBustUpManager* mgr = &g_StatusBustUpManager;
    engine::AsdTMTexTable_func_002c4e28(0x17);
    engine::AsdTMTexTable_func_002c5b04(0x23, 0);
    if (mgr->ref_count <= 0) {
        if (mgr->buffer1 == nullptr) {
            mgr->buffer1 = AsdMem_Alloc(0x266, 1);
            AsdMem_Zero(mgr->buffer1, 0x266);
        }
        if (mgr->buffer2 == nullptr) {
            mgr->buffer2 = AsdMem_Alloc(0x81, 0x100);
            AsdMem_Zero(mgr->buffer2, 0x81);
        }
    }
    mgr->ref_count++;
}

// Exact ARM-state restoration of StatusBustUp.cpp's lazy allocator path. The
// two arrays are 0x266 and 0x81 bytes; the routine also initializes the shared
// texture-table state before checking its signed reference count.
// DECOMP_FUNC(0x00223a90, 248)
__attribute__((naked)) void StatusBustUp_Init() {
    asm volatile(
        ".word 0xE92D40F8, 0xE59F40AC, 0xE1D400D0, 0xE3500000\n"
        ".word 0xCA000024, 0xE3A00017, 0xEB0284DE, 0xE3A01000\n"
        ".word 0xE3A00023, 0xEB028812, 0xE5940004, 0xE3A05001\n"
        ".word 0xE3500000, 0x1A00000C, 0xE3A0101A, 0xE28F0078\n"
        ".word 0xE1A00000, 0xE59F60A8, 0xE3A01C01, 0xE3A02000\n"
        ".word 0xE1A03006, 0xE1A00001, 0xE58D5000, 0xEB028424\n"
        ".word 0xE1A01006, 0xE5840004, 0xEB028012, 0xE5940008\n"
        ".word 0xE3500000, 0x1A00000B, 0xE3A0101E, 0xE28F0038\n"
        ".word 0xE1A00000, 0xE3A01C01, 0xE3A03081, 0xE3A02000\n"
        ".word 0xE1A00001, 0xE58D5000, 0xEB028415, 0xE3A01081\n"
        ".word 0xE5840008, 0xEB028003, 0xE5D40000, 0xE2800001\n"
        ".word 0xE5C40000, 0xE8BD80F8, 0x0044E158, 0x535C3A63\n"
        ".word 0x5C34544D, 0x36445258, 0x735C3638, 0x34736464\n"
        ".word 0x6F72705C, 0x6D617267, 0x6174735C, 0x5C737574\n"
        ".word 0x74617453, 0x75427375, 0x70557473, 0x7070632E\n"
        ".word 0x00000000, 0x00000266\n"
    );
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
