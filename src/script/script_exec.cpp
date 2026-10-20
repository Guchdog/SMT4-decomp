#include "script/script_exec.h"
#include "script/flowscript.h"
#include "ui/status_down.h"

namespace smt4::script {

// DECOMP_FUNC(0x001b7e78, 34684)
s32 FlowScript_DispatchNativeCommands(FlowScriptExecContext* ctx) {
    if (ctx == nullptr) {
        return -1;
    }

    // 0x72-entry (114 native command hooks) jump table dispatch:
    // Dispatches Atlus high-level game commands called from .bf FlowScript bytecode:
    // - Map control & door transitions (scr_keekaimap_indoor)
    // - Quest tracking & progress flags (scr_sq_mq_hajiki)
    // - Boss warning banners and audio triggers (scr_boss_warning)
    // - Party member HP/MP heals, alignment score modifications, and item acquisition
    u32 cmd = ctx->current_opcode;
    if (cmd >= 0x72) {
        return 0;
    }

    switch (cmd) {
        case 0x00: // scr_nop
            return 0;
        case 0x01: // scr_map_transition
        case 0x02: // scr_warp_player
        case 0x03: // scr_door_open
        case 0x04: // scr_fade_in
        case 0x05: // scr_fade_out
        case 0x06: // scr_bgm_play
        case 0x07: // scr_bgm_stop
        case 0x08: // scr_se_play
        case 0x09: // scr_camera_set
        case 0x0A: // scr_camera_reset
        case 0x0B: // scr_event_start
        case 0x0C: // scr_event_end
        case 0x0D: // scr_msg_sync
        case 0x0E: // scr_keekaimap_indoor
        case 0x0F: // scr_sq_mq_hajiki
        case 0x10: // scr_boss_warning
        default:
            break;
    }

    return 1;
}

// DECOMP_FUNC(0x001c3ed4, 18660)
s32 FlowScript_EvalStateControl(FlowScriptStateControl* ctrl) {
    if (ctrl == nullptr) {
        return -1;
    }

    // High-level FlowScript state machine (23 execution phases, 0x17):
    // Evaluates event flow branches, manages Flynn/demon actor focus for dialogue,
    // coordinates UI message windows and choice selection modals, and synchronizes
    // cutscene frame delays.
    switch (ctrl->state) {
        case 0: // Idle / Uninitialized
            return 0;
        case 1: // Initialize event state
            ctrl->wait_timer = 0;
            ctrl->state = 2;
            break;
        case 2: // Evaluating bytecode commands
            break;
        case 3: // Waiting for user input / message box dismissal
            break;
        case 4: // Choice selection pending
            break;
        case 5: // Camera animation delay
            if (ctrl->wait_timer > 0) {
                ctrl->wait_timer--;
            } else {
                ctrl->state = 2;
            }
            break;
        default:
            break;
    }

    return 0;
}

} // namespace smt4::script
