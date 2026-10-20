#include "camp/app_store.h"
#include "ui/status_down.h"

namespace smt4::camp {

// DECOMP_FUNC(0x00325478, 5072)
s32 Ui_DemonicaAppStore(AppStoreWork* work, u32 purchase_confirm) {
    if (work == nullptr) {
        return 0;
    }

    // Burroughs App Store Controller:
    // 1. Checks if Flynn has sufficient AP for selected Demonica application.
    // 2. Unlocks application bitflag (e.g. Skill Expansion 1-4, Party Slot 1-4).
    // 3. Deducts AP and plays Burroughs chime.
    if (purchase_confirm == 1) {
        if (work->current_ap >= work->app_cost) {
            work->current_ap -= work->app_cost;
            work->purchase_result = 1;
            return 1;
        } else {
            work->purchase_result = 2; // Insufficient AP
            return 0;
        }
    }

    return 0;
}

} // namespace smt4::camp
