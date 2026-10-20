#include "battle/battle.h"
#include "ui/status_down.h"

namespace smt4::battle {

BtlHelpManager g_BtlHelpManager = {nullptr};
BtlTalkBuffer* g_pBtlTalkBuffer = nullptr;

// DECOMP_FUNC(0x001d2528, 232)
void btlHelp_Init(BtlHelpWork* work) {
    if (work == nullptr) {
        return;
    }
    if (work->calc_task == nullptr) {
        // Register "btlHelp Calc" task with priority 2
        work->calc_task = ui::AsdTask_CreateCalc("btlHelp Calc", 2, 0, 0, nullptr, work, 0);
    }
    if (g_BtlHelpManager.buffer == nullptr) {
        g_BtlHelpManager.buffer = ui::AsdMem_Alloc(0xC, 0x100);
        if (g_BtlHelpManager.buffer != nullptr) {
            ui::AsdMem_Zero(g_BtlHelpManager.buffer, 0xC);
        }
    }
}

// DECOMP_FUNC(0x001d2610, 308)
void btlTalk_Init(BtlTalkWork* work, void* ctx, s32 arg2, s32 arg3) {
    if (work == nullptr) {
        return;
    }
    BtlTalkBuffer* buf = reinterpret_cast<BtlTalkBuffer*>(ui::AsdMem_Alloc(sizeof(BtlTalkBuffer), 0x100));
    g_pBtlTalkBuffer = buf;

    work->talk_task = ui::AsdTask_CreateCalc("btlTalk Calc", 2, 0, 0, nullptr, work, 0);

    if (buf != nullptr) {
        ui::AsdMem_Zero(buf, sizeof(BtlTalkBuffer));
        buf->parent = work;
        buf->ctx = ctx;
        buf->arg2 = arg2;
        buf->arg3 = arg3;
        buf->state = 0;
    }
}

// DECOMP_FUNC(0x001d2744, 644)
void btlUnit_Init(BtlUnitWork* work) {
    if (work == nullptr) {
        return;
    }
    // Register "btlUnit Calc" and "btlUnit DrawUp" tasks
    work->unit_task = ui::AsdTask_CreateCalc("btlUnit Calc", 2, 0, 0, nullptr, work, 0);
    ui::AsdTask_CreateDraw("btlUnit DrawUp", 0x6F, 0, 0, nullptr, work, 0);
}

// DECOMP_FUNC(0x001d29c8, 240)
s32 btlUnit_CheckPartyActive(BtlUnitWork* work) {
    if (work == nullptr) {
        return 0;
    }

    // Check main active party slots (8 slots)
    if (work->party_slots != nullptr) {
        for (s32 i = 0; i < 8; ++i) {
            u16 unit_id = work->party_slots[i];
            if (unit_id != 0) {
                // If unit status is active (not dead/inactive status 3)
                return 1;
            }
        }
    }

    // Check reserve slots (8 slots)
    if (work->reserve_slots != nullptr) {
        for (s32 i = 0; i < 8; ++i) {
            u16 unit_id = work->reserve_slots[i];
            if (unit_id != 0) {
                return 1;
            }
        }
    }

    // Check guest unit
    if (work->guest_unit != nullptr) {
        return 1;
    }

    return 0;
}

// ============================================================================
// Core Battle UI & Turn Gauge Renderer (btlUI.cpp)
// ============================================================================

BtlUIManager g_BtlUIManager = {nullptr, {0}, nullptr};

// DECOMP_FUNC(0x001a83c8, 488)
void btlUI_Init(BtlUIWork* work) {
    if (work == nullptr) {
        return;
    }

    // Allocate 0xF040 bytes dynamic render buffer if not yet allocated
    if (g_BtlUIManager.buffer == nullptr) {
        g_BtlUIManager.buffer = ui::AsdMem_Alloc(0xF040, 0x100);
    }

    // Register tasks with respective tags:
    // btlUI Calc: tag 0x02
    work->calc_task = ui::AsdTask_CreateCalc("btlUI Calc", 2, 0, 0, nullptr, work, 0);

    // btlUI DrawUpLeft (tag 0x7A) & DrawUpRight (tag 0xD8) for stereoscopic 3D
    ui::AsdTask_CreateDraw("btlUI DrawUpLeft", 0x7A, 0, 0, nullptr, work, 0);
    ui::AsdTask_CreateDraw("btlUI DrawUpRight", 0xD8, 0, 0, nullptr, work, 0);

    // btlUI DrawDown (tag 0xE7): bottom touch screen combat HUD
    ui::AsdTask_CreateDraw("btlUI DrawDown", 0xE7, 0, 0, nullptr, work, 0);

    // btlUI DrawNumber (tag 0xE9): floating damage/healing numbers
    ui::AsdTask_CreateDraw("btlUI DrawNumber", 0xE9, 0, 0, nullptr, work, 0);

    g_BtlUIManager.ui_work = work;
}

// DECOMP_FUNC(0x0019e034, 4772)
void btlUI_Calc(void* task_ctx) {
    (void)task_ctx;
    // Main UI calculation loop: updates turn icons, press turn gauge states,
    // active skill descriptions, and weakness popups.
}

// DECOMP_FUNC(0x001b71e0, 3224)
void btlUI_DrawUp(void* task_ctx) {
    (void)task_ctx;
    // Top-screen stereoscopic HUD render pass: enemy target markers,
    // turn icons, press turn gauge, and battle status badges.
}

// DECOMP_FUNC(0x001e4ae4, 360)
void btlUI_DrawDown(void* task_ctx) {
    (void)task_ctx;
    // Bottom-screen touch combat controls render pass: Attack, Gun, Skill,
    // Item, Next, and Auto-battle buttons.
}

// DECOMP_FUNC(0x0020f35c, 296)
void btlUI_DrawNumber(void* task_ctx) {
    (void)task_ctx;
    // Animated damage, critical, smirk, and recovery number sprite rendering.
}

} // namespace smt4::battle
