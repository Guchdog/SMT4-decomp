#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::battle {

/**
 * Demon Scout Negotiation Workspace.
 * Handles demon recruitment conversations, Macca/HP/Item extortion, personality questions,
 * and recruitment pacts.
 */
struct DemonScoutWork {
    u32 target_demon_id;            // +0x00: Compendium demon ID
    u32 personality_type;           // +0x04: Demon personality (Snarky, Proud, Childish, Timid, etc.)
    u32 mood_meter;                 // +0x08: Current conversation enthusiasm (0-100)
    u32 requested_macca;            // +0x0C: Macca requested by demon
    u32 negotiation_phase;          // +0x10: 0 = Intro question, 1 = Bribe/Demands, 2 = Final decision
};

/**
 * Evaluates player dialog responses, item/Macca gifts, demon mood shift, and join conditions.
 *
 * Address: 0x003c6714, Size: 4,724 bytes
 */
s32 Btl_DemonNegotiationCalc(DemonScoutWork* work, u32 player_choice, u32 flynn_stats);

} // namespace smt4::battle
