#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::camp {

/**
 * Demon Compendium Search & Filter Workspace.
 * Enables searching compendium demons by:
 * - Race / Tribe (Megami, Deity, Fada, Beast, Yoma, etc.)
 * - Skill affinity / element
 * - Summon Macca cost
 * - Level range
 */
struct CompendiumSearchWork {
    u32 filter_race;                // +0x00: Target demon tribe filter
    u32 filter_level_min;           // +0x04: Minimum level
    u32 filter_level_max;           // +0x08: Maximum level
    u32 matching_results_count;     // +0x0C: Number of demons matching filter
    u16 result_demon_ids[128];      // +0x10: Filtered demon ID list
};

/**
 * Filters the demon compendium based on specified search criteria.
 *
 * Address: 0x003b4bc0, Size: 5,520 bytes
 */
void Ui_DemonCompendiumSearch(CompendiumSearchWork* work, void* bible_ctx);

} // namespace smt4::camp
