#pragma once
#include <cstddef>
#include "types.h"
#include "camp/camp.h"

namespace smt4::camp {

/**
 * Demonica Camp Menu Main Runtime Context.
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\camp\Camp.cpp`
 * Global camp controller pointer: `0x0043DD68`.
 */
struct CampMainContext {
    void* calc_task;                    // +0x000: Calculation task handle
    void* draw_task;                    // +0x004: Stereo render task handle
    u32 current_menu_tab;               // +0x008: Active Demonica tab (0=Item, 1=Skill, 2=App, 3=Party, 4=Quest, 5=System)
    u32 active_subpage;                 // +0x00C: Subpage / list index
    u32 cursor_index;                   // +0x010: Highlighted item/party slot index
    u32 scroll_offset;                  // +0x014: Top visible row
    u32 party_member_count;             // +0x018: Flynn + active demon slots
    u32 demonica_app_count;             // +0x01C: Unlocked Gauntlet applications
    u8 raw[0x600 - 0x020];              // +0x020..+0x600: Menu layout tables, texture coordinates, and prompt states
};

/**
 * Executes the master Demonica Camp menu state machine:
 * - Top & Bottom screen UI tab switching (Items, Skills, Gauntlet Apps, Party, Quests, Config)
 * - Party demon slot selection, skill details inspection, and whisper status
 * - Touchscreen button interactions and slide navigation
 *
 * Address: 0x0017fe9c, Size: 27,308 bytes
 */
void Camp_MainProc(void* task_ctx);

/**
 * Renders the stereoscopic dual-screen Demonica interface:
 * - Upper screen (3D): 3D demon models, Demonica visor holographic UI, level-up banners, and party stats
 * - Lower screen (Touch): Interactive menu buttons, item inventory lists, and party formation slots
 *
 * Address: 0x0019a3ec, Size: 12,900 bytes
 */
void Camp_DrawStereoViews(void* task_ctx);

} // namespace smt4::camp
