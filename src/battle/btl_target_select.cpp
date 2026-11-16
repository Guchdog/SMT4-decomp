#include "battle/target_select.h"
#include "ui/status_down.h"

namespace smt4::battle {

BtlTargetSelectWork* g_pBtlTargetSelectWork = nullptr;
 // 0x00439C60

extern "C" {
    void* AsdRef_Get(void* handle);                 // 0x002c0ac8
    void ui_func_00342b54(void* resource);           // 0x00342b54
    void ui_func_0034946c(void* resource);           // 0x0034946c
    u32  ui_func_002bf9f0(void* resource);           // 0x002bf9f0
    void camp_func_003428a4(void* object);           // 0x003428a4
}

extern "C" {
    void* engine_func_002c54f0(u32 size_a, u32 size_b, u32 unk2, u32 struct_size, u32 count); // 0x002c54f0
    void* engine_func_002c23f8(u32 size, void* parent);                                       // 0x002c23f8
    void* ui_func_003431f4(void* reticle);                                                    // 0x003431f4
    void* __aeabi_vec_ctor_nocookie_nodtor(void* ptr, const void* ctor, u32 stride, u32 count); // 0x002c5f58
    void* camp_func_002c4c00(const char* name, s32 tag, u32 unk2, u32 unk3, const void* calc_fn, const void* dtor_fn, void* work, void* parent_work); // 0x002c4c00
    void  engine_func_002c3344(void* obj);                                                    // 0x002c3344
    void  engine_func_002c32f8(void* obj, u32 a1, u32 a2, u32 a3, u32 a4, u32 a5, u32 a6, const void* a7, u32 a8, u32 a9, u32 a10); // 0x002c32f8
    void  engine_func_002bdb2c(void* list, u32 a1, u32 a2, void* a3, u32 a4, f32 a5);         // 0x002bdb2c
    void  engine_func_002eb72c(void* list, u32 a1);                                           // 0x002eb72c
    void  ui_func_003093e8();                                                                 // 0x003093e8
    void  ui_func_00349468();                                                                 // 0x00349468
    extern const u32 g_CursorAnimVtable_00420504;                                             // 0x00420504
    extern const u32 g_TargetSelectDesc_00401844;                                             // 0x00401844
}

void btlTargetSelect_Calc(void*);
void btlTargetSelect_DrawUp(void*);

// DECOMP_FUNC(0x002e8294, 604)
void btlTargetSelect_Init(void* parent_work) {
    static constexpr u32 kAllocSize = 0x100;
    static constexpr u32 kReticleSize = 0x12C;
    static constexpr u32 kCursorSize = 0x60;
    static constexpr u32 kCursorElemStride = 0x10;
    static constexpr u32 kCursorElemCount = 5;
    static constexpr f32 kCursorInitY = 40.0f;
    static constexpr s32 kCalcTag = 2;
    static constexpr s32 kDrawUpLeftTag = 0x7A;
    static constexpr s32 kDrawUpRightTag = 0xD8;
    static constexpr u32 kListType = 0x14;
    static constexpr u32 kListTag = 0x71;

    BtlTargetSelectWork* const work = static_cast<BtlTargetSelectWork*>(
        engine_func_002c54f0(kAllocSize, kAllocSize, 0, sizeof(BtlTargetSelectWork), 1));
    g_pBtlTargetSelectWork = work;

    void* reticle = engine_func_002c23f8(kReticleSize, parent_work);
    if (reticle != nullptr) {
        reticle = ui_func_003431f4(reticle);
    }
    work->reticle_data = reticle;

    u8* cursor = static_cast<u8*>(engine_func_002c23f8(kCursorSize, parent_work));
    if (cursor != nullptr) {
        *reinterpret_cast<const void**>(cursor) = &g_CursorAnimVtable_00420504;
        u8* const elems = static_cast<u8*>(__aeabi_vec_ctor_nocookie_nodtor(
            cursor + 4,
            reinterpret_cast<const void*>(&ui_func_00349468),
            kCursorElemStride,
            kCursorElemCount));
        cursor = elems - 4;
        cursor[0x13] = 0;
        cursor[0x23] = 0;
        cursor[0x33] = 0;
        cursor[0x43] = 0;
        cursor[0x53] = 0;
        *reinterpret_cast<f32*>(cursor + 0x58) = 0.0f;
        *reinterpret_cast<f32*>(cursor + 0x5C) = kCursorInitY;
    }
    work->cursor_anim = cursor;
    work->flag_08 = 0;

    void* const root_parent = *static_cast<void* const*>(parent_work);
    void* const calc_task = camp_func_002c4c00(
        "btlTargetSelect Calc",
        kCalcTag,
        0,
        0,
        reinterpret_cast<const void*>(&btlTargetSelect_Calc),
        reinterpret_cast<const void*>(&ui_func_003093e8),
        work,
        root_parent);
    *reinterpret_cast<void**>(static_cast<u8*>(parent_work) + 0x1C) = calc_task;

    camp_func_002c4c00(
        "btlTargetSelect DrawUpL",
        kDrawUpLeftTag,
        0,
        0,
        reinterpret_cast<const void*>(&btlTargetSelect_DrawUp),
        nullptr,
        work,
        calc_task);

    camp_func_002c4c00(
        "btlTargetSelect DrawUpR",
        kDrawUpRightTag,
        0,
        0,
        reinterpret_cast<const void*>(&btlTargetSelect_DrawUp),
        nullptr,
        work,
        *reinterpret_cast<void**>(static_cast<u8*>(parent_work) + 0x1C));

    engine_func_002c3344(work->pad_0C);
    engine_func_002c32f8(
        work->pad_0C,
        0,
        0,
        0,
        0,
        0,
        0,
        &g_TargetSelectDesc_00401844,
        0x10,
        0,
        0);

    engine_func_002bdb2c(
        &work->target_list,
        kListType,
        kListTag,
        work->pad_0C,
        1,
        1.0f);

    engine_func_002eb72c(&work->target_list, 0);
}

// DECOMP_FUNC(0x002e06bc, 236)
void btlTargetSelect_Calc(void* task_ctx) {
    auto* const work = static_cast<u8*>(AsdRef_Get(task_ctx));
    ui_func_002bf9f0(work + 0x2c);

    const u32 tag = *reinterpret_cast<const u32*>(work + 0x30);
    const u32 flag = (tag != 0x71) ? 1 : 0;

    auto* const obj0 = *reinterpret_cast<u8**>(work);
    *reinterpret_cast<u32*>(obj0 + 0x120) = flag;

    auto* const obj1 = *reinterpret_cast<u8**>(work + 4);
    *reinterpret_cast<u32*>(obj1 + 0x54) = flag;

    const u8 mode = work[8];
    if (mode == 1) {
        camp_func_003428a4(obj0);
    } else if (mode == 2) {
        f32 val = *reinterpret_cast<f32*>(obj1 + 0x58) + 1.0f;
        *reinterpret_cast<f32*>(obj1 + 0x58) = val;
        if (val >= 30.0f) {
            val -= 30.0f;
            *reinterpret_cast<f32*>(obj1 + 0x58) = val;
        }

        f32 rot = *reinterpret_cast<f32*>(obj1 + 0x5c) + 12.0f;
        *reinterpret_cast<f32*>(obj1 + 0x5c) = rot;
        if (rot > 360.0f) {
            rot -= 360.0f;
            *reinterpret_cast<f32*>(obj1 + 0x5c) = rot;
        }
    }
}

// DECOMP_FUNC(0x002e07a8, 4)
void eventView_DrawUp(void*) {
}

extern "C" {
    void script_vm_func_002bef14();                 // 0x002bef14
    void ui_func_002c3ba8(void* gpu_state);         // 0x002c3ba8
    u32  ui_func_002c5f7c(s32 mode, s32 sub_mode);  // 0x002c5f7c
    void ui_func_002bf460(s32 type, s32 id, s32 sub_id, s32 x, s32 y, s32 flag); // 0x002bf460
    void ui_func_002bf710(f32 alpha);               // 0x002bf710
    extern const u8* g_StaffRollEntryTable;         // 0x00432cc8
    extern u8* g_AsdGpuState;                       // 0x0044ea00
}

// DECOMP_FUNC(0x002e07ac, 296)
void StaffRoll_U_UR_Draw(void*) {
    static constexpr u32 kGpuStackOffset = 0x124C;
    static constexpr u32 kEntryCount = 12;
    static constexpr s32 kPanelType = 2;
    static constexpr s32 kPanelId = 0x34;
    static constexpr s32 kSubIdStep = 1000;
    static constexpr s32 kPanelFlag = 2;

    const u8* const entries = g_StaffRollEntryTable;
    script_vm_func_002bef14();

    ui_func_002c3ba8(g_AsdGpuState);
    const u32 val = ui_func_002c5f7c(1, 0);

    u8* const stack = g_AsdGpuState + kGpuStackOffset;
    u32 count = *reinterpret_cast<u32*>(stack);
    const u32 prev = *reinterpret_cast<const u32*>(stack + 8 + count * 4);
    ++count;
    *reinterpret_cast<u32*>(stack) = count;
    *reinterpret_cast<u32*>(stack + 8 + count * 4) = val;
    if (stack[0x18] != 0 || prev != val) {
        using FlushFn = void (*)(u32);
        reinterpret_cast<FlushFn>(*reinterpret_cast<const uintptr_t*>(stack + 0x1C))(val);
        stack[0x18] = 0;
    }

    for (u32 i = 0; i < kEntryCount; ++i) {
        const u8* const entry = entries + i * 8;
        const s32 x = static_cast<s32>(*reinterpret_cast<const f32*>(entry + 0x08));
        const s32 y = static_cast<s32>(*reinterpret_cast<const f32*>(entry + 0x0C));
        ui_func_002bf460(
            kPanelType,
            kPanelId,
            static_cast<s32>(i * kSubIdStep),
            x,
            y,
            kPanelFlag);
    }

    script_vm_func_002bef14();
    ui_func_002bf710(1.0f);

    u8* const pop_stack = g_AsdGpuState + kGpuStackOffset;
    u32 pop_count = *reinterpret_cast<u32*>(pop_stack);
    const u32 popped = *reinterpret_cast<const u32*>(pop_stack + 8 + pop_count * 4);
    --pop_count;
    *reinterpret_cast<u32*>(pop_stack) = pop_count;
    const u32 top = *reinterpret_cast<const u32*>(pop_stack + 8 + pop_count * 4);
    if (pop_stack[0x18] != 0 || popped != top) {
        using FlushFn = void (*)(u32);
        reinterpret_cast<FlushFn>(*reinterpret_cast<const uintptr_t*>(pop_stack + 0x1C))(top);
        pop_stack[0x18] = 0;
    }
}

// DECOMP_FUNC(0x002e08d4, 544)
__attribute__((naked)) void tmnlMain_DrawDown(void*) {
    asm volatile(
        ".word 0xE59F020C, 0xE92D41F0, 0xE5905000, 0xE5950010, 0xE2400001, 0xE3500062, 0x2A00007B, 0xE59F71F4\n"
        ".word 0xED9F0A7D, 0xE3A00006, 0xE5974000, 0xEBFE97CB, 0xE2844A01, 0xE2844F9B, 0xE3A06000, 0xE5941000\n"
        ".word 0xE2812001, 0xE0843101, 0xE5931008, 0xE0843102, 0xE5842000, 0xE5830008, 0xE5D42018, 0xE3520000\n"
        ".word 0x01510000, 0x0A000002, 0xE594101C, 0xE12FFF31, 0xE5C46018, 0xE5974000, 0xE3A01000, 0xE3A00001\n"
        ".word 0xEBFF9588, 0xE2844A01, 0xE2844F93, 0xE5941000, 0xE0842101, 0xE2811001, 0xE5922008, 0xE0843101\n"
        ".word 0xE5841000, 0xE5830008, 0xE5D41018, 0xE3510000, 0x01520000, 0x0A000002, 0xE594101C, 0xE12FFF31\n"
        ".word 0xE5C46018, 0xE5974000, 0xE3A02000, 0xE3A01001, 0xE3A00006, 0xEBFF957D, 0xE2844A01, 0xE2844FAB\n"
        ".word 0xE5941000, 0xE2812001, 0xE0843101, 0xE5931008, 0xE0843102, 0xE5842000, 0xE5830008, 0xE5D42018\n"
        ".word 0xE3520000, 0x01510000, 0x0A000002, 0xE594101C, 0xE12FFF31, 0xE5C46018, 0xE3A04000, 0xE0840084\n"
        ".word 0xE0850100, 0xE5D0156C, 0xE3510000, 0x15900568, 0x1BFE8434, 0xE2844001, 0xE3540004, 0xBAFFFFF6\n"
        ".word 0xE5970000, 0xE2804A01, 0xE2844FAB, 0xE5940000, 0xE0841100, 0xE2400001, 0xE5911008, 0xE5840000\n"
        ".word 0xE0840100, 0xE5D42018, 0xE5900008, 0xE3520000, 0x01510000, 0x0A000002, 0xE594101C, 0xE12FFF31\n"
        ".word 0xE5C46018, 0xE5970000, 0xE2804A01, 0xE2844F93, 0xE5940000, 0xE0841100, 0xE2400001, 0xE5911008\n"
        ".word 0xE5840000, 0xE0840100, 0xE5D42018, 0xE5900008, 0xE3520000, 0x01510000, 0x0A000002, 0xE594101C\n"
        ".word 0xE12FFF31, 0xE5C46018, 0xE5970000, 0xE2804A01, 0xE2844F9B, 0xE5940000, 0xE0841100, 0xE2400001\n"
        ".word 0xE5911008, 0xE5840000, 0xE0840100, 0xE5D42018, 0xE5900008, 0xE3520000, 0x01510000, 0x0A000002\n"
        ".word 0xE594101C, 0xE12FFF31, 0xE5C46018, 0xE3A00000, 0xE8BD81F0, 0x00432CE0, 0x0044EA00, 0x00000000\n"
    );
}

// DECOMP_FUNC(0x002f4aa4, 76)
void btlTargetSelect_DrawUp(void* task_ctx) {
    auto* const work = static_cast<u8*>(AsdRef_Get(task_ctx));
    const u8 mode = work[8];
    if (mode == 1) {
        ui_func_00342b54(*reinterpret_cast<void**>(work));
    } else if (mode == 2) {
        ui_func_0034946c(*reinterpret_cast<void**>(work + 4));
    }
}

} // namespace smt4::battle
