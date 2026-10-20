#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::ui {

/**
 * Touchscreen Dungeon MiniMap Radar & 2D Projection Workspace.
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\map\mapEpl.cpp` / `uiMiniMap.cpp`
 */
struct UiMiniMapWork {
    f32 player_pos[3];                  // +0x00: Flynn world coordinates (X, Y, Z)
    f32 compass_heading_rad;            // +0x0C: North compass rotation angle in radians
    f32 zoom_scale;                     // +0x10: Radar zoom multiplier
    u32 radar_mode;                     // +0x14: Fullscreen map vs. mini corner radar
    u32 active_floor_id;                // +0x18: Current dungeon floor index
    u32 icon_count;                     // +0x1C: Active map blip/POI count
    u8 raw[0x200 - 0x020];              // +0x020..+0x200: POI coordinates (terminals, chests, demon domains, NPCs)
};

/**
 * Renders the lower touchscreen MiniMap radar display, computing 2D projections,
 * player avatar cursor orientation, fog-of-war discovery tiles, and point-of-interest icons.
 *
 * Address: 0x0025f8f0, Size: 11,004 bytes
 */
void Ui_MiniMapRender(UiMiniMapWork* work, void* draw_ctx);

} // namespace smt4::ui
