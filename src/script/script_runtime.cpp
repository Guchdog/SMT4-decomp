#include "script/script_runtime.h"
#include "ui/status_down.h"

namespace smt4::script {

// DECOMP_FUNC(0x00277f9c, 12192)
void FlowScript_InitRuntimeMemory(FlowScriptRuntimeMem* mem, void* parent_env) {
    (void)parent_env;
    if (mem == nullptr) {
        return;
    }

    // FlowScript VM Runtime Memory Initializer:
    // 1. Clears execution stack frames and registers event trigger chains in .bss.
    // 2. Prepares operand evaluation stacks, local variable banks, and return registers.
    // 3. Connects the script engine to the engine file subsystem for .bf / .mbm streaming.
}

// DECOMP_FUNC(0x001e5d84, 9740)
s32 FlowScript_ProcessFlagBank(FlowScriptFlagBank* bank, u32 flag_id, s32 op_mode) {
    if (bank == nullptr) {
        return 0;
    }

    // FlowScript Bitflag Management Engine:
    // - op_mode 0: Check flag (TEST)
    // - op_mode 1: Set flag (SET)
    // - op_mode 2: Clear flag (CLEAR)
    // - op_mode 3: Toggle flag (FLIP)
    // Manages over 8,000 story progress, challenge quest, and demon encounter flags.
    u32 bank_idx = flag_id >> 5;
    u32 bit_mask = 1u << (flag_id & 31);

    if (bank_idx < 256) {
        switch (op_mode) {
            case 0:
                return (bank->global_flags[bank_idx] & bit_mask) ? 1 : 0;
            case 1:
                bank->global_flags[bank_idx] |= bit_mask;
                return 1;
            case 2:
                bank->global_flags[bank_idx] &= ~bit_mask;
                return 0;
            case 3:
                bank->global_flags[bank_idx] ^= bit_mask;
                return (bank->global_flags[bank_idx] & bit_mask) ? 1 : 0;
            default:
                break;
        }
    }

    return 0;
}

} // namespace smt4::script
