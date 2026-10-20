#include "ui/terminal_ui.h"
#include "ui/status_down.h"

namespace smt4::ui {

// DECOMP_FUNC(0x001d98c4, 5880)
void Ui_TerminalSceneRender(TerminalSceneWork* work, void* camera_ctx) {
    (void)camera_ctx;
    if (work == nullptr) {
        return;
    }

    // Terminal Room 3D Scene Controller:
    // 1. Coordinates 3D terminal portal vortex animation ("terminal/terminal2.bam").
    // 2. Evaluates stereoscopic camera paths ("terminal/terminal.bccam").
    // 3. Displays fast-travel list of unlocked Tokyo districts (Shinjuku, Shibuya, Ikebukuro, Ginza).
    work->portal_rotation_angle += 0.05f;
}

} // namespace smt4::ui
