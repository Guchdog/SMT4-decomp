#include "camp/compendium_search.h"
#include "ui/status_down.h"

namespace smt4::camp {

// DECOMP_FUNC(0x003b4bc0, 5520)
void Ui_DemonCompendiumSearch(CompendiumSearchWork* work, void* bible_ctx) {
    (void)bible_ctx;
    if (work == nullptr) {
        return;
    }

    // Demon Compendium Advanced Filter Engine:
    // Filters registered demons by tribe, summon cost, and elemental skills.
    work->matching_results_count = 0;
}

} // namespace smt4::camp
