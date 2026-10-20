#include "ui/mikado_ui.h"
#include "ui/status_down.h"

namespace smt4::ui {

// DECOMP_FUNC(0x001eeea0, 5556)
void Ui_MikadoCastleScene(MikadoCastleWork* work, void* scene_ctx) {
    (void)scene_ctx;
    if (work == nullptr) {
        return;
    }

    // Mikado Castle Navigation Hub:
    // Handles location selection, background castle artwork display,
    // and story event transitions between Samurai districts.
    work->background_scroll_pos += 0.25f;
}

} // namespace smt4::ui
