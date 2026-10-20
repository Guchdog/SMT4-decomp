#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::ui {

/**
 * Status Screen Detailed Skill Inspector Workspace.
 * Renders full skill details:
 * - Elemental affinity icon (Physical, Gun, Fire, Ice, Elec, Force, Light, Dark, Almighty)
 * - MP consumption cost
 * - Target scope (Single, All, Random 1-4)
 * - Power rating and ailment secondary effects
 */
struct StatusSkillsWork {
    u32 actor_id;                   // +0x00: Flynn or demon index
    u32 active_skill_slot;          // +0x04: Focused skill slot (0-7)
    u32 skill_id;                   // +0x08: Skill identifier
    u32 mp_cost;                    // +0x0C: Cost in MP
    u32 affinity_element;           // +0x10: Elemental category
    char skill_desc[128];           // +0x14: Skill description string
};

/**
 * Renders skill details pane and description text on status screen.
 *
 * Address: 0x001ce98c, Size: 5,444 bytes
 */
void Ui_StatusScreenSkills(StatusSkillsWork* work, void* render_ctx);

} // namespace smt4::ui
