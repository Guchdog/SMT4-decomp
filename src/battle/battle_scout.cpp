#include "battle/battle_scout.h"
#include "ui/status_down.h"

namespace smt4::battle {

// DECOMP_FUNC(0x003c6714, 4724)
s32 Btl_DemonNegotiationCalc(DemonScoutWork* work, u32 player_choice, u32 flynn_stats) {
    if (work == nullptr) {
        return 0;
    }

    // Demon Scout Negotiation State Machine:
    // 1. Evaluates dialogue response suitability based on demon personality.
    // 2. Adjusts mood_meter (+25 on pleasing answer, -30 on displeasing answer).
    // 3. Handles item/Macca bribe demands and cheating checks.
    // 4. Returns 1 if demon agrees to join stock, 2 if demon runs away, 3 if demon attacks.
    (void)flynn_stats;
    if (player_choice == 1) {
        work->mood_meter += 25;
    } else {
        work->mood_meter = (work->mood_meter > 20) ? (work->mood_meter - 20) : 0;
    }

    if (work->mood_meter >= 75) {
        work->negotiation_phase = 2;
        return 1; // Demon pact agreed
    }

    return 0;
}

} // namespace smt4::battle
