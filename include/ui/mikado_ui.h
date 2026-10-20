#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::ui {

/**
 * Eastern Kingdom of Mikado Castle & Aquila Palace UI Scene Workspace.
 * Coordinates town navigation menus across Mikado locations:
 * - Aquila Palace / Monastery (Hugo, Gabby)
 * - Lake Mikado (fishing, gathering)
 * - Kiccigiorgi Forest
 * - Barracks / Square
 */
struct MikadoCastleWork {
    u32 current_sub_area;           // +0x00: Current Mikado location index
    u32 selected_menu_option;       // +0x04: Focused navigation option
    u32 time_of_day;                // +0x08: Daytime / Sunset / Night illumination
    f32 background_scroll_pos;      // +0x0C: Parallax banner scroll position
};

/**
 * Handles Mikado Castle hub navigation and stereoscopic background rendering.
 *
 * Address: 0x001eeea0, Size: 5,556 bytes
 */
void Ui_MikadoCastleScene(MikadoCastleWork* work, void* scene_ctx);

} // namespace smt4::ui
