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

} // namespace smt4::battle
