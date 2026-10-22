#include "ui/result.h"
#include "ui/status_down.h"
#include "engine/asd_symbols.h"

namespace smt4::ui {

ResultManager g_ResultManager = {nullptr};

// DECOMP_FUNC(0x0029bc38, 368)
void Result_Init(s32 mode) {
    if (g_ResultManager.work != nullptr) {
        return;
    }

    ResultWork* work = reinterpret_cast<ResultWork*>(AsdMem_Alloc(sizeof(ResultWork), 0x100));
    g_ResultManager.work = work;

    if (work == nullptr) {
        return;
    }

    // Register calculation task ("Result CALC", priority 2)
    work->calc_task = AsdTask_CreateCalc("Result CALC", 2, 0, 0, nullptr, work, 0);

    // Register stereoscopic 3D reward showcase passes (Upper Left 0x80, Upper Right 0xDE)
    AsdTask_CreateDraw("Result DrawUpLeft", 0x80, 0, 0, nullptr, work, 0);
    AsdTask_CreateDraw("Result DrawUpRight", 0xDE, 0, 0, nullptr, work, 0);

    // Register bottom touchscreen reward breakdown and EXP gauges ("Result DDRAW", tag 0xE6)
    work->draw_down_task = AsdTask_CreateDraw("Result DDRAW", 0xE6, 0, 0, nullptr, work, 0);

    work->result_mode = static_cast<u8>(mode);
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

// DECOMP_FUNC(0x001c87d8, 420)
void Result_DrawDown(void* task_ctx) {
    (void)task_ctx;
    // Lower Touchscreen reward HUD render pass:
    // Numerical EXP counter tickers, Macca tally summary, and acquired item list.
}

} // namespace smt4::ui
