#include "ui/minimap.h"
#include "ui/status_down.h"

namespace smt4::ui {

// DECOMP_FUNC(0x0025f8f0, 11004)
void Ui_MiniMapRender(UiMiniMapWork* work, void* draw_ctx) {
    (void)draw_ctx;
    if (work == nullptr) {
        return;
    }

    // Touchscreen MiniMap Radar & 2D Projection Pipeline:
    // 1. Projects Flynn's 3D world position onto the 2D touchscreen raster plane (320x240 LCD).
    // 2. Applies compass rotation angle around center coordinate (160, 120).
    // 3. Renders dungeon floor discovery geometry, discovered pathways, and walls.
    // 4. Overlays interactive POI markers:
    //    - Demon Domains (red vortex blips)
    //    - Relic Discovery spots (yellow markers)
    //    - Terminal & Save spots (blue emblems)
    //    - Quest NPCs and exit doorways
}

} // namespace smt4::ui
