#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::ui {

/**
 * Terminal Room 3D Portal & Fast Travel UI Workspace.
 * Models: `terminal/terminal2.bam`, `terminal/terminal.bccam`, `terminal/terminal02.bccam`
 * Controls teleportation destinations across Tokyo underground network.
 */
struct TerminalSceneWork {
    u32 current_terminal_id;        // +0x00: Current terminal room location
    u32 selected_destination_id;    // +0x04: Target fast travel point
    u32 unlocked_terminals_mask;    // +0x08: Bitmask of discovered terminals
    f32 portal_rotation_angle;      // +0x0C: 3D portal swirling vortex angle
    u32 transition_state;           // +0x10: 0 = menu, 1 = warping, 2 = arrived
};

/**
 * Renders Terminal room 3D portal animation and travel destination menu.
 *
 * Address: 0x001d98c4, Size: 5,880 bytes
 */
void Ui_TerminalSceneRender(TerminalSceneWork* work, void* camera_ctx);

} // namespace smt4::ui
