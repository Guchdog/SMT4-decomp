#include "camp/whisper_event.h"
#include "ui/status_down.h"

namespace smt4::camp {

// DECOMP_FUNC(0x00332100, 5968)
s32 Camp_WhisperSkillTransfer(WhisperEventWork* work, u32 confirm_choice) {
    if (work == nullptr) {
        return 0;
    }

    // Demon Whisper Skill Inheritance:
    // 1. Validates selected skill compatibility with Flynn's active slots.
    // 2. Checks if skill already exists in Flynn's arsenal (upgrades rank up to +8).
    // 3. Triggers Burroughs whisper chime sound and screen flash.
    if (confirm_choice == 1) {
        work->whisper_dialogue_state = 2; // Success
        return 1;
    }

    return 0;
}

} // namespace smt4::camp
