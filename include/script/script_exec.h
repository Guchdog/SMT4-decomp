#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::script {

/**
 * FlowScript Execution Context & Native Host Command Engine.
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\event\eventCommand.cpp` / `scrScriptProcess.cpp`
 * Global script manager pointer: `0x00447E28`.
 */
struct FlowScriptExecContext {
    void* script_work;                  // +0x00: Pointer to parent ScriptWork
    const u8* pc;                       // +0x04: Current instruction pointer (bytecode)
    const u8* code_base;                // +0x08: Start of bytecode section
    u32 current_opcode;                 // +0x0C: Active opcode index
    u32 stack_ptr;                      // +0x10: Expression evaluation stack pointer
    s32 eval_stack[32];                 // +0x14..+0x94: Operand stack
    u32 flags;                          // +0x94: VM runtime execution flags
    u32 local_var_count;                // +0x98: Number of local variables
    s32 local_vars[64];                 // +0x9C..+0x19C: Local variable bank
    u32 yield_reason;                   // +0x19C: VM yield / wait condition
    u32 return_value;                   // +0x1A0: Function return register
};

/**
 * FlowScript VM State Control & Actor Event Coordinator.
 * Interacts with Camp / Status / Demonica subsystem contexts at `0x0043DCF0`.
 */
struct FlowScriptStateControl {
    u32 state;                          // +0x00: Active execution state
    u32 sub_mode;                       // +0x04: Sub-mode / transition index
    u32 wait_timer;                     // +0x08: Frame delay counter
    u32 target_actor_id;                // +0x0C: Target Flynn/demon index
    void* active_ui_window;             // +0x10: Attached message or prompt window
    u8 raw[0x200 - 0x14];               // +0x14..+0x200: Subsystem event buffer
};

/**
 * Dispatches 0x72 native engine/game commands from FlowScript bytecode,
 * including map transitions, indoor barrier maps (scr_keekaimap_indoor),
 * main/side quest flag checks (scr_sq_mq_hajiki), and boss encounter warnings (scr_boss_warning).
 *
 * Address: 0x001b7e78, Size: 34,684 bytes
 */
s32 FlowScript_DispatchNativeCommands(FlowScriptExecContext* ctx);

/**
 * Evaluates VM high-level state machine flow, event actor selection,
 * and UI message dialog synchronization for FlowScript scripts.
 *
 * Address: 0x001c3ed4, Size: 18,660 bytes
 */
s32 FlowScript_EvalStateControl(FlowScriptStateControl* ctrl);

} // namespace smt4::script
