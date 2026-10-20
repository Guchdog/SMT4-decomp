#include "ui/status_skills.h"
#include "ui/status_down.h"

namespace smt4::ui {

// DECOMP_FUNC(0x001ce98c, 5444)
void Ui_StatusScreenSkills(StatusSkillsWork* work, void* render_ctx) {
    (void)render_ctx;
    if (work == nullptr) {
        return;
    }

    // Status Screen Skill Inspector:
    // Formats and displays skill name, elemental badges, MP cost, and effect description.
}

} // namespace smt4::ui
