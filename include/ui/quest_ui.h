#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::ui {

/**
 * Hunter Association Quest Center Request Board Workspace.
 * Manages Main and Challenge Quests, client details, difficulty stars, and rewards.
 */
struct QuestCenterWork {
    u32 active_tab;                 // +0x00: 0 = Accepted Quests, 1 = Available Quests, 2 = Completed
    u32 selected_quest_index;       // +0x04: Cursor selection
    u32 total_available_quests;     // +0x08: Quests displayed on bulletin board
    u32 client_npc_id;              // +0x0C: Quest giver NPC model ID
    u32 reward_macca;               // +0x10: Monetary payout
};

/**
 * Renders the Hunter Association request bulletin board and quest details pane.
 *
 * Address: 0x0021243c, Size: 5,820 bytes
 */
void Ui_QuestCenterListRender(QuestCenterWork* work, void* draw_ctx);

} // namespace smt4::ui
