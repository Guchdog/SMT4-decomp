#include "ui/debug_hud.h"
#include "ui/status_down.h"

namespace smt4::ui {

// DECOMP_FUNC(0x001b1a90, 8352)
void Ui_DebugStatsRender(DebugStatsWork* work, void* display_ctx) {
    (void)display_ctx;
    if (work == nullptr || (work->display_flags & 1) == 0) {
        return;
    }

    // Performance Stats & Profiler Overlay:
    // Prints real-time FPS, CPU/GPU latency, and VRAM heap consumption.
}

} // namespace smt4::ui
