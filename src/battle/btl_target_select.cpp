#include "battle/target_select.h"
#include "ui/status_down.h"

namespace smt4::battle {

BtlTargetSelectWork* g_pBtlTargetSelectWork = nullptr; // 0x00439C60

// DECOMP_FUNC(0x002e8294, 604)
void btlTargetSelect_Init(void* parent_work) {
    BtlTargetSelectWork* work = reinterpret_cast<BtlTargetSelectWork*>(ui::AsdMem_Alloc(sizeof(BtlTargetSelectWork), 0x100));
    g_pBtlTargetSelectWork = work;

    if (work == nullptr) {
        return;
    }

    // Allocate reticle render buffer (0x12C bytes)
    work->reticle_data = ui::AsdMem_Alloc(0x12C, 0x100);

    // Allocate cursor animation controller (0x60 bytes)
    work->cursor_anim = ui::AsdMem_Alloc(0x60, 0x100);

    work->flag_08 = 0;

    // Register "btlTargetSelect Calc" task (tag 2)
    ui::AsdTask_CreateCalc("btlTargetSelect Calc", 2, 0, 0, nullptr, work, 0);

    // Register stereoscopic Upper Left (0x7A) and Upper Right (0xD8) target reticle draw passes
    ui::AsdTask_CreateDraw("btlTargetSelect DrawUpL", 0x7A, 0, 0, nullptr, work, 0);
    ui::AsdTask_CreateDraw("btlTargetSelect DrawUpR", 0xD8, 0, 0, nullptr, work, 0);
}

// DECOMP_FUNC(0x002e06bc, 1080)
void btlTargetSelect_Calc(void* task_ctx) {
    (void)task_ctx;
    // Calculates cursor positioning over single/all enemies or party members,
    // cycles targets based on D-pad input, and computes screen-space reticle coordinates.
}

// DECOMP_FUNC(0x002f4aa4, 76)
void btlTargetSelect_DrawUp(void* task_ctx) {
    (void)task_ctx;
    // Renders the 3D stereoscopic target selector cursor and weakness highlight brackets.
}

} // namespace smt4::battle
