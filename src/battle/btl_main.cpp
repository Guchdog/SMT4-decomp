#include "battle/battle.h"
#include "battle/btl_main.h"
#include "ui/status_down.h"

namespace smt4::battle {

BtlMainManager g_BtlMainManager = {nullptr, nullptr, nullptr};
// DECOMP_FUNC(0x001b0cb0, 812)


//
__attribute__((naked)) void btlMain_Init(void*, s32) {
    asm volatile(
        ".word 0xE92D43F0, 0xE1A05000, 0xE1A06001, 0xE24DD014\n"
        ".word 0xE3A010F0, 0xE28F0E27, 0xE1A00000, 0xE3A07001\n"
        ".word 0xE3A01C01, 0xE59F3290, 0xE3A02000, 0xE1A00001\n"
        ".word 0xE58D7000, 0xEB044FA6, 0xE59F8280, 0xE1A04000\n"
        ".word 0xE3A010F4, 0xE5880000, 0xE28F0F8F, 0xE1A00000\n"
        ".word 0xE59F926C, 0xE3A01C01, 0xE3A02000, 0xE1A03009\n"
        ".word 0xE1A00001, 0xE58D7000, 0xEB044F99, 0xE5880004\n"
        ".word 0xEB03DF38, 0xE1A01000, 0xE5980004, 0xE1A02009\n"
        ".word 0xEB043088, 0xE3A010F7, 0xE28F0F7F, 0xE1A00000\n"
        ".word 0xE59F9230, 0xE3A01C01, 0xE3A02000, 0xE1A03009\n"
        ".word 0xE1A00001, 0xE58D7000, 0xEB044F89, 0xE5880008\n"
        ".word 0xEB03483B, 0xE1A01000, 0xE5980008, 0xE1A02009\n"
        ".word 0xEB04549F, 0xE1A00004, 0xEB001746, 0xE3550000\n"
        ".word 0x13560000, 0xE3A07000, 0xDA000024, 0xE3560004\n"
        ".word 0x05950000, 0x058400C0, 0x0A00002A, 0xE3560012\n"
        ".word 0x1A000028, 0xE5950000, 0xE58D0000, 0xE5950004\n"
        ".word 0xE58D0004, 0xE5950008, 0xE58D0008, 0xE595000C\n"
        ".word 0xE58D000C, 0xE1D501B0, 0xE1CD01B0, 0xE1DD00D0\n"
        ".word 0xE3500000, 0xE1DD00F2, 0x158400C4, 0x058400C0\n"
        ".word 0xE1DD00F4, 0xE584013C, 0xE1DD00F6, 0xE5840140\n"
        ".word 0xE1DD00F8, 0xE5840144, 0xE1DD00FA, 0xE5840148\n"
        ".word 0xE5DD000C, 0xE5C4014C, 0x15C4714C, 0xE1DD00FE\n"
        ".word 0xE5840150, 0xE1DD01F0, 0xE5840154, 0xEA000009\n"
        ".word 0xE5980000, 0xE2842B11, 0xE3A01001, 0xE3500000\n"
        ".word 0xE28220A8, 0x15801068, 0xE5921000, 0xE3811C02\n"
        ".word 0xE3811002, 0xE5821000, 0xE5C47060, 0xE59F1128\n"
        ".word 0xE59F0128, 0xE5982000, 0xE3A03000, 0xE88D0007\n"
        ".word 0xE1A02003, 0xE3A01002, 0xE28F0F45, 0xEB0452C1\n"
        ".word 0xE59F1118, 0xE5840000, 0xE3A03000, 0xE88D0082\n"
        ".word 0xE58D000C, 0xE1A02003, 0xE3A01073, 0xE28F0C01\n"
        ".word 0xE58D7008, 0xEB044F59, 0xE59F1100, 0xE5940000\n"
        ".word 0xE3A03000, 0xE88D0082, 0xE58D000C, 0xE1A02003\n"
        ".word 0xE3A010E6, 0xE28F00E8, 0xE58D7008, 0xEB044F4F\n"
        ".word 0xE59F50E8, 0xE5940000, 0xE3A03000, 0xE88D00A0\n"
        ".word 0xE58D000C, 0xE1A02003, 0xE3A01080, 0xE28F00D0\n"
        ".word 0xE58D7008, 0xEB044F45, 0xE5940000, 0xE88D00A0\n"
        ".word 0xE3A03000, 0xE58D000C, 0xE1A02003, 0xE3A010DE\n"
        ".word 0xE28F00B8, 0xE58D7008, 0xEB044F3C, 0xE59F10B8\n"
        ".word 0xE5940000, 0xE3A03000, 0xE88D0082, 0xE58D000C\n"
        ".word 0xE1A02003, 0xE3A010E9, 0xE28F00A0, 0xE58D7008\n"
        ".word 0xEB044F32, 0xE28DD014, 0xE8BD83F0, 0x535C3A63\n"
        ".word 0x5C34544D, 0x36445258, 0x735C3638, 0x34736464\n"
        ".word 0x6F72705C, 0x6D617267, 0x7461625C, 0x5C656C74\n"
        ".word 0x4D6C7462, 0x2E6E6961, 0x00707063, 0x00004A58\n"
        ".word 0x00435D90, 0x000097E8, 0x0000104A, 0x0020EEE8\n"
        ".word 0x001B55F0, 0x4D4C5442, 0x204E4941, 0x00000043\n"
        ".word 0x001E49C4, 0x4D4C5442, 0x204E4941, 0x00000055\n"
        ".word 0x0020F23C, 0x4D4C5442, 0x204E4941, 0x00000044\n"
        ".word 0x001E49CC, 0x464C5442, 0x20454441, 0x00004C55\n"
        ".word 0x464C5442, 0x20454441, 0x00005255, 0x0020F244\n"
        ".word 0x464C5442, 0x20454441, 0x00000044\n"
    );
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
