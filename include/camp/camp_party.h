#pragma once
#include <cstddef>
#include "types.h"
#include "camp/camp.h"

namespace smt4::camp {

/**
 * Demonica Party Stock & Sub-Mode Navigation Controller.
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\camp\PartyPanel\PartyPanel.cpp`
 * Interacts directly with `g_CampWork` (0x0043DA90).
 */
struct CampPartyWork {
    u32 sub_mode;                       // +0x00: Current camp sub-mode index
    u32 selected_slot;                  // +0x04: Active cursor demon/actor slot (0..3 active, 4..27 stock)
    u32 target_swap_slot;               // +0x08: Target slot for party rearrangement
    u32 demon_whisper_pending;          // +0x0C: Flag indicating demon learned all skills and is ready to whisper
    u32 filter_affinity_mask;           // +0x10: Filter demons by skill element
    u8 raw[0x100 - 0x014];              // +0x014..+0x100: Cached demon parameters and stock scroll metrics
};

/**
 * Processes Demonica sub-modes, demon stock management, party member swapping,
 * demon summon/return actions, and skill inspection.
 *
 * Address: 0x0032cb08, Size: 12,620 bytes
 */
void Camp_SubModeProcess(void* task_ctx);

} // namespace smt4::camp
