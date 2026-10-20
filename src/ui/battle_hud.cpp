#include "ui/battle_hud.h"
#include "ui/status_down.h"

namespace smt4::ui {

// DECOMP_FUNC(0x003efa10, 12708)
void Ui_NkmBaseTableLoad(BattleTableWork* work, void* file_ctx) {
    (void)file_ctx;
    if (work == nullptr) {
        return;
    }

    // Ally Demon (Nakama) Base Table & Encounter Table Loader:
    // 1. Reads "battle/NKMBaseTable.tbb" into contiguous memory buffer for demon stat lookups.
    // 2. Indexes "battle/NKMSortIndex.tbb" for species and level-based ordering.
    // 3. Mounts "battle/EncountData.tbb" and "battle/EventEncountData.tbb" for story & field encounters.
    work->load_status = 1;
}

// DECOMP_FUNC(0x0025d3fc, 7328)
void Ui_BattleCommandMenu(BattleCommandWork* work, u32 pad_input) {
    if (work == nullptr) {
        return;
    }

    // Battle Command Action Menu:
    // Controls player input cursor on lower screen touchscreen wheel:
    // 0: "Attack" (equipped melee blade)
    // 1: "Shoot" (equipped gun & elemental rounds)
    // 2: "Skill" (Flynn / demon active skills)
    // 3: "Item" (healing items, attack stones)
    // 4: "Talk" (demon scout negotiation)
    // 5: "Escape" (tactical retreat)
    if (pad_input & 0x1) { // A button / Touch confirmation
        work->selection_state = 1;
    } else if (pad_input & 0x2) { // B button / Cancel
        work->selection_state = 2;
    }
}

// DECOMP_FUNC(0x003f34f8, 7984)
void Ui_BattleMessageWindow(BattleMessageWork* work, void* render_ctx) {
    (void)render_ctx;
    if (work == nullptr) {
        return;
    }

    // Battle Message Dialogue Display:
    // Renders turn order announcements, skill execution banners, weakness notifications,
    // and demon recruitment conversation dialogs with stereoscopic font rendering.
}

// DECOMP_FUNC(0x003ec954, 6616)
void Ui_BattleActionEffectOverlay(BattleActionOverlayWork* work, void* render_ctx) {
    (void)render_ctx;
    if (work == nullptr) {
        return;
    }

    // Combat Action Effect Overlay:
    // 1. Weakness hit impact flash and Press Turn icon gain banner.
    // 2. Critical strike screen shake and high-contrast diagonal cut-in slice.
    // 3. Smirk activation gold particle burst on active demon avatar.
    if (work->effect_type != 0) {
        work->screen_shake_intensity *= 0.85f;
        work->flash_alpha *= 0.90f;
    }
}

} // namespace smt4::ui
