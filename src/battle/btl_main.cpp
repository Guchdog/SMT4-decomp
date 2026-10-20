#include "battle/battle.h"
#include "ui/status_down.h"

namespace smt4::battle {

BtlMainManager g_BtlMainManager = {nullptr, nullptr, nullptr};

// DECOMP_FUNC(0x001b0cb0, 812)
void btlMain_Init(void* arg0, s32 arg1) {
    // 1. Allocate primary battle engine work (0x4A58 bytes)
    BtlMainWork* work = reinterpret_cast<BtlMainWork*>(ui::AsdMem_Alloc(sizeof(BtlMainWork), 0x100));
    g_BtlMainManager.main_work = work;

    // 2. Allocate secondary skill/encounter table buffer (0x97E8 bytes)
    void* table_buf = ui::AsdMem_Alloc(0x97E8, 0x100);
    g_BtlMainManager.table_buffer = table_buf;

    // 3. Allocate auxiliary voice/effect queue buffer (0x104A bytes)
    void* extra_buf = ui::AsdMem_Alloc(0x104A, 0x100);
    g_BtlMainManager.extra_buffer = extra_buf;

    if (work == nullptr) {
        return;
    }

    // 4. Initialize battle arena parameters and setup state
    btlMain_Setup(work);

    // 5. Unpack encounter parameters if supplied
    if (arg0 != nullptr && arg1 > 0) {
        if (arg1 == 4) {
            work->encounter_id = *reinterpret_cast<s16*>(arg0);
        } else if (arg1 == 0x12) {
            struct EncounterParams {
                s8 pad_00;
                s8 pad_01;
                s16 sub_enc;
                s16 phase;
                s16 turn;
                s16 round;
                s16 init_side;
                u8 preemptive;
                u8 pad_0D;
                s16 press_slots;
                s16 blink_slots;
            };
            const auto* params = reinterpret_cast<const EncounterParams*>(arg0);
            if (params->pad_00 != 0) {
                work->sub_encounter_id = params->sub_enc;
            } else {
                work->encounter_id = params->sub_enc;
            }
            work->btl_phase = params->phase;
            work->turn_count = params->turn;
            work->round_count = params->round;
            work->initiative_side = params->init_side;
            work->preemptive_type = (params->pad_00 != 0) ? 0 : params->preemptive;
            work->press_turn_slots = params->press_slots;
            work->blinking_turn_slots = params->blink_slots;
        }
    } else {
        work->combat_flags |= 0x202;
    }

    work->state_flag = 0;

    // 6. Register core combat loop calculation task ("BTLMAIN C", priority 2)
    work->calc_task = ui::AsdTask_CreateCalc("BTLMAIN C", 2, 0, 0, nullptr, work, 0);

    // 7. Register upper and lower rendering tasks
    ui::AsdTask_CreateDraw("BTLMAIN U", 0x73, 0, 0, nullptr, work, 0);
    ui::AsdTask_CreateDraw("BTLMAIN D", 0xE6, 0, 0, nullptr, work, 0);

    // 8. Register screen fade overlays (stereoscopic upper left/right + lower)
    ui::AsdTask_CreateDraw("BTLFADE UL", 0x80, 0, 0, nullptr, work, 0);
    ui::AsdTask_CreateDraw("BTLFADE UR", 0xDE, 0, 0, nullptr, work, 0);
    ui::AsdTask_CreateDraw("BTLFADE D", 0xE9, 0, 0, nullptr, work, 0);
}

// DECOMP_FUNC(0x001b6a98, 1824)
void btlMain_Setup(BtlMainWork* work) {
    if (work == nullptr) {
        return;
    }
    // Initialize 3D camera matrices, arena lighting, demon model slots,
    // Turn order queues, and Press Turn counters.
    ui::AsdMem_Zero(work, sizeof(BtlMainWork));
    work->press_turn_slots = 4;
    work->blinking_turn_slots = 0;
}

// DECOMP_FUNC(0x001b55f0, 5288)
void btlMain_Calc(void* task_ctx) {
    (void)task_ctx;
    // Master battle turn state machine:
    // Handles Phase transitions: Command Input -> Action Execution ->
    // Press Turn Consumption -> Weakness / Smirk check -> Round Evaluation ->
    // Victory / Defeat / Demon Negotiation outcomes.
}

// DECOMP_FUNC(0x001e4990, 340)
void btlMain_DrawUp(void* task_ctx) {
    (void)task_ctx;
    // Upper screen 3D combat viewport and stereoscopic battle fade render pass.
}

// DECOMP_FUNC(0x0020eee8, 1140)
void btlMain_DrawDown(void* task_ctx) {
    (void)task_ctx;
    // Lower touch screen battle menus, action prompts, and bottom fade render pass.
}

} // namespace smt4::battle
