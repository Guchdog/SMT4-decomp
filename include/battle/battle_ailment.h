#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::battle {

/**
 * Combat Status Ailment Work.
 * Handles Shin Megami Tensei IV status ailments:
 * - Poison (damage per turn)
 * - Sick (stat drop, critical vulnerability)
 * - Panic (random action or Macca toss)
 * - Sleep (skip turn, HP/MP recovery, critical vulnerability)
 * - Bind (cannot act, high dodge penalty)
 * - Lost (ejected from combat)
 * - Daze (staggered)
 */
struct StatusAilmentWork {
    u32 target_actor_id;            // +0x00: Actor slot
    u32 ailment_mask;               // +0x04: Active ailment bitflags
    u32 remaining_turns;            // +0x08: Duration turns
    f32 damage_factor;              // +0x0C: Tick damage multiplier
};

/**
 * Calculates ailment resistance, infliction probability, tick damage, and natural recovery.
 *
 * Address: 0x0021c598, Size: 5,420 bytes
 */
s32 Btl_StatusEffectCalc(StatusAilmentWork* work, u32 incoming_ailment, u32 luck_stat);

} // namespace smt4::battle
