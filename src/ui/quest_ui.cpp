#include "ui/quest_ui.h"
#include "ui/status_down.h"

namespace smt4::ui {

// DECOMP_FUNC(0x0021243c, 5820)
void Ui_QuestCenterListRender(QuestCenterWork* work, void* draw_ctx) {
    (void)draw_ctx;
    if (work == nullptr) {
        return;
    }

    // Hunter Association Quest Board:
    // Renders challenge quest notices, delivery objectives, demon subjugation targets,
    // and Macca/Item reward summaries on the lower touch display.
}

} // namespace smt4::ui
