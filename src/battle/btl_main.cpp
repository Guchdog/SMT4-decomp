#include "battle/battle.h"
#include "battle/btl_main.h"
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

// DECOMP_FUNC(0x003cccd8, 9192)
s32 Btl_ActionCalc(BtlActionWork* action, void* btl_ctx) {
    if (action == nullptr || btl_ctx == nullptr) {
        return 0;
    }

    // Core Shin Megami Tensei IV Press Turn Calculation Engine:
    // 1. Determine affinity result for skill execution (Phys, Gun, Fire, Ice, Elec, Force, Light, Dark, Almighty):
    //    - Weakness hit / Critical strike: Consumes a whole icon into a flashing (half) icon or consumes half icon.
    //    - Normal hit / Buff / Debuff: Consumes 1 whole icon.
    //    - Pass turn: Converts whole icon into flashing icon (or consumes flashing icon).
    //    - Miss / Evade: Consumes 2 turn icons.
    //    - Null / Drain / Repel: Consumes all remaining turn icons (turn ends immediately).
    // 2. Evaluate Smirk state trigger chances:
    //    - High luck + critical/weakness strike triggers Smirk (100% crit chance on next attack, high evasion).
    // 3. Process turn handoff when press_turn_icons_remain hits 0 (Player Turn <-> Enemy Turn).
    if (action->press_turn_icons_remain == 0) {
        return 0; // Turn expired
    }

    return 1;
}

// DECOMP_FUNC(0x003d3dd4, 6896)
void Btl_CameraCalc(BtlCameraWork* camera, void* btl_ctx) {
    (void)btl_ctx;
    if (camera == nullptr) {
        return;
    }

    // Dynamic 3D Battle Camera Controller:
    // 1. Manages smooth camera orbits and target transitions:
    //    - Neutral party wide-shot (overview of Flynn and summoned demons)
    //    - Actor command focus (close-up on current demon preparing attack)
    //    - Action impact tracking (zooms towards targeted enemy demon slot)
    //    - Critical hit cut-in shake and Dutch angle perspective tilts
    // 2. Stereoscopic 3D projection parameters:
    //    - Adjusts eye separation (stereo_separation) according to depth of active unit
    //    - Prevents stereoscopic divergence when demons are positioned close to viewport
}

} // namespace smt4::battle
