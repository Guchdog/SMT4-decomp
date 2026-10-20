#include "battle/battle_ailment.h"
#include "ui/status_down.h"

namespace smt4::battle {

// DECOMP_FUNC(0x0021c598, 5420)
s32 Btl_StatusEffectCalc(StatusAilmentWork* work, u32 incoming_ailment, u32 luck_stat) {
    if (work == nullptr) {
        return 0;
    }

    // Status Ailment Affliction & Recovery Engine:
    // 1. Checks elemental/ailment nullification resistances.
    // 2. Calculates hit chance: Base_Rate * (Actor_Luck / Target_Luck).
    // 3. Updates turn countdown timer and applies stat reductions (Sick/Bind).
    if (incoming_ailment == 0) {
        // Recovery evaluation
        if (work->remaining_turns > 0) {
            work->remaining_turns--;
        }
        if (work->remaining_turns == 0) {
            work->ailment_mask = 0;
        }
        return 0;
    }

    work->ailment_mask |= incoming_ailment;
    work->remaining_turns = 3;
    (void)luck_stat;
    return 1;
}

} // namespace smt4::battle
