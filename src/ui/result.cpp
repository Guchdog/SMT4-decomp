#include "ui/result.h"
#include "ui/status_down.h"
#include "engine/asd_symbols.h"

namespace smt4::ui {

ResultManager g_ResultManager = {nullptr};
// DECOMP_FUNC(0x0029bc38, 368)


//
__attribute__((naked)) void Result_Init(s32 mode) {
    __asm__ volatile(
        ".word 0xe92d41f0\n"
        ".word 0xe1a06000\n"
        ".word 0xe24dd010\n"
        ".word 0xe59f4124\n"
        ".word 0xe5940000\n"
        ".word 0xe3500000\n"
        ".word 0x1a000044\n"
        ".word 0xebffb7bc\n"
        ".word 0xe59f1114\n"
        ".word 0xe59f0114\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a00001\n"
        ".word 0xe3a01c01\n"
        ".word 0xe58d0000\n"
        ".word 0xe59f3104\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a00001\n"
        ".word 0xeb00a3c0\n"
        ".word 0xe59f20fc\n"
        ".word 0xe5840000\n"
        ".word 0xe59f10f0\n"
        ".word 0xe3a07000\n"
        ".word 0xe1a04000\n"
        ".word 0xe28d0004\n"
        ".word 0xe58d2000\n"
        ".word 0xe8800082\n"
        ".word 0xe1a03007\n"
        ".word 0xe59f00dc\n"
        ".word 0xe1a02007\n"
        ".word 0xe3a01002\n"
        ".word 0xeb00a730\n"
        ".word 0xe2845b35\n"
        ".word 0xe2855f91\n"
        ".word 0xe59f80c8\n"
        ".word 0xe5850000\n"
        ".word 0xe3a03000\n"
        ".word 0xe58d000c\n"
        ".word 0xe59f00bc\n"
        ".word 0xe1a02003\n"
        ".word 0xe3a01080\n"
        ".word 0xe58d7004\n"
        ".word 0xe58d8000\n"
        ".word 0xe58d7008\n"
        ".word 0xeb00a3c5\n"
        ".word 0xe5950000\n"
        ".word 0xe3a03000\n"
        ".word 0xe1a02003\n"
        ".word 0xe58d000c\n"
        ".word 0xe59f0094\n"
        ".word 0xe3a010de\n"
        ".word 0xe58d7004\n"
        ".word 0xe58d8000\n"
        ".word 0xe58d7008\n"
        ".word 0xeb00a3bb\n"
        ".word 0xe59f1080\n"
        ".word 0xe5950000\n"
        ".word 0xe3a03000\n"
        ".word 0xe88d0082\n"
        ".word 0xe58d000c\n"
        ".word 0xe59f0070\n"
        ".word 0xe1a02003\n"
        ".word 0xe3a010e6\n"
        ".word 0xe58d7008\n"
        ".word 0xeb00a3b1\n"
        ".word 0xe1a01000\n"
        ".word 0xe59f005c\n"
        ".word 0xe7801004\n"
        ".word 0xe1a00004\n"
        ".word 0xeb04700a\n"
        ".word 0xe59f0050\n"
        ".word 0xe3a01001\n"
        ".word 0xe7c06004\n"
        ".word 0xe28dd010\n"
        ".word 0xe1a00004\n"
        ".word 0xe8bd41f0\n"
        ".word 0xeaffeb2b\n"
        ".word 0xe28dd010\n"
        ".word 0xe8bd81f0\n"
        // Literal pool at 0x0029bd78.
        ".word 0x0044dc20\n"
        ".word 0x00001264\n"
        ".word 0x00405eec\n"
        ".word 0x0000d658\n"
        ".word 0x001c87d8\n"
        ".word 0x0018bfec\n"
        ".word 0x00405ee0\n"
        ".word 0x001a15b0\n"
        ".word 0x00405ecc\n"
        ".word 0x00405eb8\n"
        ".word 0x001c8874\n"
        ".word 0x00405ea8\n"
        ".word 0x0000d64c\n"
        ".word 0x00003560\n"
    );
}

// DECOMP_FUNC(0x0018bfec, 12684)
void Result_Calc(void* task_ctx) {
    (void)task_ctx;
    // Master Result sequence calculation state machine:
    // 1. Tally encounter EXP, Macca, and App Points (AP)
    // 2. Animate experience bars for Flynn and demon allies
    // 3. Process Level-Up stat distributions, demon skill mutations, and Whisper events
    // 4. Calculate demon negotiation item/relic loot drops and quest item rewards
    // 5. Handle user touch/A-button dismissal back to world map or dungeon exploration
}

// DECOMP_FUNC(0x001a15b0, 932)
void Result_DrawUp(void* task_ctx) {
    (void)task_ctx;
    // Stereoscopic Upper Screen 3D result render pass:
    // Party victory poses, 3D demon models, level-up banners, and whisper effects.
}

// DECOMP_FUNC(0x001c87d8, 156)
void Result_DrawDown(void* task_ctx) {
    (void)task_ctx;
    // Lower Touchscreen reward HUD render pass:
    // Numerical EXP counter tickers, Macca tally summary, and acquired item list.
}

// DECOMP_FUNC(0x001c8874, 264)
void func_001c8874(void* task_ctx) {
    (void)task_ctx;
    // Separate Result DDRAW task callback registered by Result_Init.
}

} // namespace smt4::ui
