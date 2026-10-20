#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::script {

/**
 * FlowScript Virtual Machine Execution Context.
 * Evaluates compiled `.bf` bytecode instructions, maintaining an operand stack,
 * program counter, frame call stack, and message window hooks.
 */
struct FlowScriptVmWork {
    const u8* bytecode_base;        // +0x00: Pointer to .bf code segment
    u32 program_counter;            // +0x04: Current byte offset in bytecode
    s32 stack[64];                  // +0x08: Expression evaluation operand stack
    u32 stack_pointer;              // +0x108: Top of operand stack
    u32 active_flag_bank;           // +0x10C: Target flag bank (global, scenario, local)
    u32 exec_state;                 // +0x110: 0 = running, 1 = yield/wait, 2 = halted
};

/**
 * Main bytecode instruction evaluation loop for FlowScript VM.
 * Handles arithmetic, logical operations, stack push/pop, and system calls.
 *
 * Address: 0x0027154c, Size: 8,316 bytes
 */
s32 FlowScript_OpcodeEvaluator(FlowScriptVmWork* vm, u32 opcode);

/**
 * Executes a scenario event FlowScript binary (`event/e899/e899.bf` + `e899.mbm`).
 *
 * Address: 0x001955bc, Size: 5,812 bytes
 */
void FlowScript_EventVmExecute(FlowScriptVmWork* vm, void* event_ctx);

/**
 * Evaluates conditional jump instructions (JZ, JNZ, CMP) and bitwise flag checks.
 *
 * Address: 0x001fc644, Size: 4,876 bytes
 */
s32 FlowScript_BranchCondition(FlowScriptVmWork* vm, u32 condition_code, s32 lhs, s32 rhs);

/**
 * Hooks dialogue window choices, text prompts, and message progression into the VM.
 *
 * Address: 0x00307978, Size: 4,832 bytes
 */
void FlowScript_MessageWindowHook(FlowScriptVmWork* vm, void* msg_ctx);

} // namespace smt4::script
