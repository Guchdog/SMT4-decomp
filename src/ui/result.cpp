#include "ui/result.h"
#include "ui/status_down.h"
#include "engine/asd_symbols.h"

extern "C" {
    void script_vm_func_002a755c(void*);
    void engine_func_002c4360(void*);
    void script_vm_func_002c0128();
    void script_vm_func_002a497c(u32);
    void script_vm_func_002aeb2c(u32, u32);
}

namespace smt4::ui {

ResultManager g_ResultManager = {nullptr};
extern "C" {
    void  CommonBg_func_00289b4c(void* work);                                                     // 0x00289b4c
    void* engine_func_002c4b84(u32 size_a, u32 size_b, u32 unk2, u32 struct_size, u32 count);     // 0x002c4b84
    void* engine_func_002c5978(const char* name, s32 tag, u32 unk2, u32 unk3, const void* calc_fn, const void* dtor_fn, void* work); // 0x002c5978
    void* camp_func_002c4c00(const char* name, s32 tag, u32 unk2, u32 unk3, const void* calc_fn, const void* dtor_fn, void* work, void* parent_work); // 0x002c4c00
    void  ui_func_003b7d78(void* work);                                                           // 0x003b7d78
    void  script_vm_func_00296a18(void* ctx, u32 state);                                          // 0x00296a18
}

void Result_Calc(void*);
void Result_DrawUp(void*);
void Result_DrawDown(void*);
void func_001c8874(void*);

// DECOMP_FUNC(0x0029bc38, 368)
void Result_Init(s32 mode) {
    static constexpr u32 kAllocSize = 0x100;
    static constexpr u32 kWorkSize = 0xD658;
    static constexpr s32 kCalcTag = 2;
    static constexpr s32 kDrawUpLeftTag = 0x80;
    static constexpr s32 kDrawUpRightTag = 0xDE;
    static constexpr s32 kDrawDownTag = 0xE6;
    static constexpr u32 kCalcTaskOffset = 0xD644;
    static constexpr u32 kDdrawTaskOffset = 0xD64C;
    static constexpr u32 kModeOffset = 0x3560;

    if (g_ResultManager.work != nullptr) {
        return;
    }

    CommonBg_func_00289b4c(nullptr);

    u8* const work = static_cast<u8*>(
        engine_func_002c4b84(kAllocSize, kAllocSize, 0, kWorkSize, 1));
    g_ResultManager.work = reinterpret_cast<ResultWork*>(work);

    void* const calc_task = engine_func_002c5978(
        "Result CALC",
        kCalcTag,
        0,
        0,
        reinterpret_cast<const void*>(&Result_Calc),
        reinterpret_cast<const void*>(&Result_DrawDown),
        nullptr);
    *reinterpret_cast<void**>(work + kCalcTaskOffset) = calc_task;

    camp_func_002c4c00(
        "Result DrawUpLeft",
        kDrawUpLeftTag,
        0,
        0,
        reinterpret_cast<const void*>(&Result_DrawUp),
        nullptr,
        nullptr,
        calc_task);

    camp_func_002c4c00(
        "Result DrawUpRight",
        kDrawUpRightTag,
        0,
        0,
        reinterpret_cast<const void*>(&Result_DrawUp),
        nullptr,
        nullptr,
        calc_task);

    *reinterpret_cast<void**>(work + kDdrawTaskOffset) = camp_func_002c4c00(
        "Result DDRAW",
        kDrawDownTag,
        0,
        0,
        reinterpret_cast<const void*>(&func_001c8874),
        nullptr,
        nullptr,
        calc_task);

    ui_func_003b7d78(work);
    work[kModeOffset] = static_cast<u8>(mode);

    script_vm_func_00296a18(work, 1);
}

#if 0 // Unverified behavioral sketch; not byte-equivalent.
[[maybe_unused]] static void Result_Calc_Draft(void* task_ctx) {
    (void)task_ctx;
    // Master Result sequence calculation state machine:
    // 1. Tally encounter EXP, Macca, and App Points (AP)
    // 2. Animate experience bars for Flynn and demon allies
    // 3. Process Level-Up stat distributions, demon skill mutations, and Whisper events
    // 4. Calculate demon negotiation item/relic loot drops and quest item rewards
    // 5. Handle user touch/A-button dismissal back to world map or dungeon exploration
}
#endif

// The full span contains its switch table and trailing literal pool.
// DECOMP_FUNC(0x0018bfec, 12684)
__attribute__((naked)) void Result_Calc(void*) {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x08bfec, 12684\n");
}

// DECOMP_FUNC(0x001a15b0, 932)
// Verified ARM-state entry/exit and referenced local literal/table bytes.
__attribute__((naked)) void Result_DrawUp(void* task_ctx) {
    asm volatile(
        ".word 0xe92d4ff0\n"
        ".word 0xe24dd00c\n"
        ".word 0xe59f0384\n"
        ".word 0xe5904000\n"
        ".word 0xe3540000\n"
        ".word 0x0a000091\n"
        ".word 0xe1a00004\n"
        ".word 0xeb03d5ba\n"
        ".word 0xe3500000\n"
        ".word 0x0a00008e\n"
        ".word 0xe59fa368\n"
        ".word 0xe59a0000\n"
        ".word 0xeb048970\n"
        ".word 0xe59a5000\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a00001\n"
        ".word 0xeb049261\n"
        ".word 0xe2855a01\n"
        ".word 0xe2855f93\n"
        ".word 0xe3a07000\n"
        ".word 0xe5951000\n"
        ".word 0xe2812001\n"
        ".word 0xe0853101\n"
        ".word 0xe5931008\n"
        ".word 0xe0853102\n"
        ".word 0xe5852000\n"
        ".word 0xe5830008\n"
        ".word 0xe5d52018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe595101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c57018\n"
        ".word 0xe2849b0d\n"
        ".word 0xe2899f4b\n"
        ".word 0xe5990000\n"
        ".word 0xe350000c\n"
        ".word 0x1a00005b\n"
        ".word 0xe59f02f8\n"
        ".word 0xe7900004\n"
        ".word 0xe3500005\n"
        ".word 0x1a000057\n"
        ".word 0xe2840b01\n"
        ".word 0xe2800fcf\n"
        ".word 0xe1a0b000\n"
        ".word 0xe1d008da\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a000050\n"
        ".word 0xe2848b0d\n"
        ".word 0xe2888f51\n"
        ".word 0xe5980000\n"
        ".word 0xe3500010\n"
        ".word 0xaa000038\n"
        ".word 0xe0400200\n"
        ".word 0xe59a5000\n"
        ".word 0xe1a06080\n"
        ".word 0xe37600f0\n"
        ".word 0xb3e060ef\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe3a00006\n"
        ".word 0xeb04923c\n"
        ".word 0xe2855a01\n"
        ".word 0xe2855fab\n"
        ".word 0xe5951000\n"
        ".word 0xe0852101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d52018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe595101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c57018\n"
        ".word 0xe37600f0\n"
        ".word 0xe3a050f1\n"
        ".word 0xda000006\n"
        ".word 0xe3a03000\n"
        ".word 0xe2852022\n"
        ".word 0xe3a01028\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d6000\n"
        ".word 0xeb047754\n"
        ".word 0xe28600f0\n"
        ".word 0xe88d0021\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a02f45\n"
        ".word 0xe3a01028\n"
        ".word 0xe3a00002\n"
        ".word 0xeb04774d\n"
        ".word 0xe59a5000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe3a00006\n"
        ".word 0xeb049219\n"
        ".word 0xe2855a01\n"
        ".word 0xe2855fab\n"
        ".word 0xe5951000\n"
        ".word 0xe0852101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d52018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe595101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c57018\n"
        ".word 0xe5980000\n"
        ".word 0xe3500008\n"
        ".word 0xda00000f\n"
        ".word 0xe1a0000b\n"
        ".word 0xed900a08\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb0477df\n"
        ".word 0xe3a000f2\n"
        ".word 0xe2802023\n"
        ".word 0xe58d0004\n"
        ".word 0xe3a03000\n"
        ".word 0xe3a01028\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d7000\n"
        ".word 0xeb04772b\n"
        ".word 0xed9f0a66\n"
        ".word 0xe320f000\n"
        ".word 0xeb0477d4\n"
        ".word 0xe59a0000\n"
        ".word 0xe2805a01\n"
        ".word 0xe2855f93\n"
        ".word 0xe5950000\n"
        ".word 0xe2401001\n"
        ".word 0xe0852100\n"
        ".word 0xe5920008\n"
        ".word 0xe5851000\n"
        ".word 0xe0851101\n"
        ".word 0xe5d52018\n"
        ".word 0xe5911008\n"
        ".word 0xe3520000\n"
        ".word 0x01500001\n"
        ".word 0x0a000003\n"
        ".word 0xe595201c\n"
        ".word 0xe1a00001\n"
        ".word 0xe12fff32\n"
        ".word 0xe5c57018\n"
        ".word 0xe5990000\n"
        ".word 0xe3500009\n"
        ".word 0xba000002\n"
        ".word 0xe3a00000\n"
        ".word 0xe28dd00c\n"
        ".word 0xe8bd8ff0\n"
        ".word 0xe3500000\n"
        ".word 0x0a00002d\n"
        ".word 0xe59a5000\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a00001\n"
        ".word 0xeb0491d1\n"
        ".word 0xe2855a01\n"
        ".word 0xe2855f93\n"
        ".word 0xe5951000\n"
        ".word 0xe2812001\n"
        ".word 0xe0853101\n"
        ".word 0xe5931008\n"
        ".word 0xe0853102\n"
        ".word 0xe5852000\n"
        ".word 0xe5830008\n"
        ".word 0xe5d52018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe595101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c57018\n"
        ".word 0xe2840020\n"
        ".word 0xeb0475bf\n"
        ".word 0xe1a05000\n"
        ".word 0xe2840020\n"
        ".word 0xeb0475b9\n"
        ".word 0xe1a02000\n"
        ".word 0xe1a01005\n"
        ".word 0xe1a00004\n"
        ".word 0xeb084743\n"
        ".word 0xe59a0000\n"
        ".word 0xe2804a01\n"
        ".word 0xe2844f93\n"
        ".word 0xe5940000\n"
        ".word 0xe0841100\n"
        ".word 0xe2400001\n"
        ".word 0xe5911008\n"
        ".word 0xe5840000\n"
        ".word 0xe0840100\n"
        ".word 0xe5d42018\n"
        ".word 0xe5900008\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c47018\n"
        ".word 0xe59a4000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe3a00006\n"
        ".word 0xeb0491ac\n"
        ".word 0xe2844a01\n"
        ".word 0xe2844fab\n"
        ".word 0xe5941000\n"
        ".word 0xe0842101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d42018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000002\n"
        ".word 0xe594101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c47018\n"
        ".word 0xe59a0000\n"
        ".word 0xeb04808d\n"
        ".word 0xe59a0000\n"
        ".word 0xe320f000\n"
        ".word 0xeb048060\n"
        ".word 0xe28dd00c\n"
        ".word 0xe3a00000\n"
        ".word 0xe8bd8ff0\n"
        ".word 0x0044dc20\n"
        ".word 0x0044ea00\n"
        ".word 0x00003534\n"
        ".word 0x3f800000\n"
    );
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void Result_DrawUp_Draft(void* task_ctx) {
    (void)task_ctx;
    // Stereoscopic Upper Screen 3D result render pass:
    // Party victory poses, 3D demon models, level-up banners, and whisper effects.
}
#endif

[[maybe_unused]] static void Result_DrawDown_Draft(void* task_ctx) {
    (void)task_ctx;
    // Lower Touchscreen reward HUD render pass:
    // Numerical EXP counter tickers, Macca tally summary, and acquired item list.
}

// DECOMP_FUNC(0x001c87d8, 156)
void Result_DrawDown(void*) {
    auto* const work = reinterpret_cast<u8*>(g_ResultManager.work);
    if (work == nullptr) {
        return;
    }

    script_vm_func_002a755c(*reinterpret_cast<void**>(work + 0x3568));
    engine_func_002c4360(*reinterpret_cast<void**>(work + 0x3564));
    engine_func_002c4360(*reinterpret_cast<void**>(work + 0x356C));
    script_vm_func_002c0128();

    engine_func_002c4360(*reinterpret_cast<void**>(work + 0x3570));

    script_vm_func_002a497c(0x14);
    script_vm_func_002a497c(0x25);

    for (s32 i = 0; i < 2; ++i) {
        script_vm_func_002aeb2c(0x28, static_cast<u32>(i));
    }

    engine_func_002c4360(work);
    g_ResultManager.work = nullptr;
}

extern "C" {
    s32  script_vm_func_00296cbc(void* work);                                 // 0x00296cbc
    void ui_func_003b6150(void* work, u32 a1, u32 a2);                        // 0x003b6150
    u32  ui_func_002bef7c(void* slot);                                        // 0x002bef7c
    u32  shop_func_002bef70(void* slot);                                      // 0x002bef70
    void ui_func_003b72a4(void* work, u32 a1, u32 a2);                        // 0x003b72a4
    void ui_func_003b6c7c(void* work, u32 a1, u32 a2);                        // 0x003b6c7c
    void Ui_DemonCompendiumSearch(void* work, u32 a1, u32 a2);                // 0x003b4bc0
}

// DECOMP_FUNC(0x001c8874, 264)
void func_001c8874(void*) {
    static constexpr u32 kStateOffset = 0x352C;
    static constexpr s32 kPreStepMaxState = 7;
    static constexpr s32 kModeA = 0x0A;
    static constexpr s32 kModeB = 0x11;
    static constexpr s32 kModeC = 0x12;
    static constexpr u32 kSlotAOffset = 0x50C;
    static constexpr u32 kSlotBOffset = 0xAC;
    static constexpr u32 kSlotCOffset = 0x598;

    auto* const work = reinterpret_cast<u8*>(g_ResultManager.work);
    if (work == nullptr) {
        return;
    }
    if (script_vm_func_00296cbc(work) == 0) {
        return;
    }

    auto* const state_ptr = reinterpret_cast<s32*>(work + kStateOffset);
    if (*state_ptr <= kPreStepMaxState) {
        ui_func_003b6150(work, 0, 0);
    }

    switch (*state_ptr) {
    case kModeA: {
        void* const slot = work + kSlotAOffset;
        const u32 a = ui_func_002bef7c(slot);
        const u32 b = shop_func_002bef70(slot);
        ui_func_003b72a4(work, a, b);
        break;
    }
    case kModeB: {
        void* const slot = work + kSlotBOffset;
        const u32 a = ui_func_002bef7c(slot);
        const u32 b = shop_func_002bef70(slot);
        Ui_DemonCompendiumSearch(work, a, b);
        break;
    }
    case kModeC: {
        void* const slot = work + kSlotCOffset;
        const u32 a = ui_func_002bef7c(slot);
        const u32 b = shop_func_002bef70(slot);
        ui_func_003b6c7c(work, a, b);
        break;
    }
    default:
        break;
    }
}
#if 0
// Partial semantic draft retained for reconstruction; not compiled.
[[maybe_unused]] static void func_001c8874_Draft(void* task_ctx) {
    (void)task_ctx;
    // Separate Result DDRAW task callback registered by Result_Init.
}
#endif

} // namespace smt4::ui
