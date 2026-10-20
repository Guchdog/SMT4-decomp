#pragma once
#include <cstddef>
#include "types.h"
#include "battle/battle.h"

namespace smt4::battle {

/**
 * Combat Battle Action & Press Turn Loop Controller.
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\battle\btlMain.cpp`
 */
struct BtlActionWork {
    u32 phase;                          // +0x00: Combat turn phase
    u32 current_actor_slot;             // +0x04: Current active Flynn/demon slot
    u32 press_turn_icons_total;         // +0x08: Starting turn icons count
    u32 press_turn_icons_remain;        // +0x0C: Remaining active turn icons
    u32 press_turn_flash_mask;          // +0x10: Bitmask of half/flashing icons
    u32 smirk_status_mask;              // +0x14: Bitmask of actors currently Smirking
    u32 target_slot_mask;               // +0x18: Selected enemy target slots
    u32 action_skill_id;                // +0x1C: Current chosen skill/attack ID
    u8 raw[0x200 - 0x020];              // +0x020..+0x200: Damage formulas, affinity check results, and buff/debuff tiers
};

/**
 * Dynamic 3D Battle Camera Controller.
 * Controls stereoscopic camera tracking during turn transitions, spell effects, and critical attacks.
 */
struct BtlCameraWork {
    f32 eye_pos[3];                     // +0x00: Camera world position (X, Y, Z)
    f32 target_pos[3];                  // +0x0C: Focus target coordinates
    f32 up_vector[3];                   // +0x18: Up vector
    f32 fov_degrees;                    // +0x24: Field of view
    f32 stereo_separation;              // +0x28: 3D parallax interocular distance
    u32 tracking_mode;                  // +0x2C: Follow player / focus enemy / full party overview
    u8 raw[0x100 - 0x030];              // +0x030..+0x100: Interpolation curves and shake parameters
};

/**
 * Evaluates combat turn progression, Press Turn icon deductions,
 * weakness hits (giving half turns), misses/nulls (losing multiple icons),
 * and Smirk activation chances.
 *
 * Address: 0x003cccd8, Size: 9,192 bytes
 */
s32 Btl_ActionCalc(BtlActionWork* action, void* btl_ctx);

/**
 * Computes dynamic camera angles, zoom cut-ins on critical strikes,
 * and 3D eye separation for upper stereoscopic screen presentation.
 *
 * Address: 0x003d3dd4, Size: 6,896 bytes
 */
void Btl_CameraCalc(BtlCameraWork* camera, void* btl_ctx);

} // namespace smt4::battle
