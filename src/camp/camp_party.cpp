#include "camp/camp_party.h"
#include "ui/status_down.h"

namespace smt4::camp {

// DECOMP_FUNC(0x0032cb08, 12620)
void Camp_SubModeProcess(void* task_ctx) {
    (void)task_ctx;
    CampWork* work = g_CampWork;
    if (work == nullptr || work->state == 0) {
        return;
    }

    // Demonica Camp Sub-Mode & Demon Stock Processor:
    // 1. Manages party member formation (Flynn + 3 active demon allies in battle):
    //    - Summoning demon from stock into battle party slot
    //    - Returning demon from battle party back to stock
    //    - Swapping positions between party slots
    // 2. Demon Whisper System:
    //    - When a demon learns all inherent skills, triggers Demon Whisper event
    //    - Prompts Flynn to learn new skills or upgrade existing skill tiers (+1..+8)
    // 3. Sub-mode transition coordinator:
    //    - Handles transitions into Status Down inspection, Skill mutation checks,
    //      and item application modals.
}

} // namespace smt4::camp
