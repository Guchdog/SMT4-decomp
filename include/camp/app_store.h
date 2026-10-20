#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::camp {

/**
 * Burroughs Demonica App Store Workspace.
 * Manages App Points (AP), application purchasing, unlocking fusion upgrades,
 * party expansion slots, skill expansion, and scout perks (Scout+, Fundraise+).
 */
struct AppStoreWork {
    u32 current_ap;                 // +0x00: Flynn's current App Points
    u32 app_unlock_flags[8];        // +0x04: 256 app bitflags
    u32 selected_app_id;            // +0x24: Currently highlighted application
    u32 app_cost;                   // +0x28: AP cost of focused application
    u32 purchase_result;            // +0x2C: 0 = idle, 1 = success, 2 = insufficient AP
};

/**
 * Handles Burroughs App Store UI browsing, purchasing, and perk activation.
 *
 * Address: 0x00325478, Size: 5,072 bytes
 */
s32 Ui_DemonicaAppStore(AppStoreWork* work, u32 purchase_confirm);

} // namespace smt4::camp
