#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::camp {

/**
 * Demon Whisper Skill Transfer & Level-Up Event Workspace.
 * When a demon learns all inherent skills, Demon Whisper triggers, allowing Flynn
 * to inherit or augment known skills (+1 to +8 power/cost reduction).
 */
struct WhisperEventWork {
    u32 demon_stock_slot;           // +0x00: Source demon index in party
    u32 selected_skill_id;          // +0x04: Target skill chosen by player
    u32 flynn_skill_slot;           // +0x08: Destination slot in Flynn's skill list
    u32 is_upgrade;                 // +0x0C: 1 if upgrading existing skill (+1 rank)
    u32 whisper_dialogue_state;     // +0x10: Burroughs guidance step
};

/**
 * Handles Demon Whisper skill transfer and Flynn skill rank enhancement.
 *
 * Address: 0x00332100, Size: 5,968 bytes
 */
s32 Camp_WhisperSkillTransfer(WhisperEventWork* work, u32 confirm_choice);

} // namespace smt4::camp
