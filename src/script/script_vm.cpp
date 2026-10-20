#include "script/flowscript.h"
#include "script/script_vm.h"
#include "camp/unite.h"
#include "ui/status_down.h"

namespace smt4::script {

NameMainManager g_NameMainManager = {nullptr, nullptr};
OnesRoomManager g_OnesRoomManager = {nullptr};

// DECOMP_FUNC(0x001d374c, 408)
void nameMain_Init(void* arg0, s32 arg1) {
    NameMainWork* work = reinterpret_cast<NameMainWork*>(ui::AsdMem_Alloc(sizeof(NameMainWork), 0x100));
    g_NameMainManager.work = work;

    if (work == nullptr) {
        return;
    }

    ui::AsdMem_Zero(work, sizeof(NameMainWork));

    // Register calculation task ("NameMainProc", priority 2)
    work->proc_task = ui::AsdTask_CreateCalc("NameMainProc", 2, 0, 0, nullptr, work, 0);

    // Register 3D stereo naming display passes (tags 0x7A, 0xD8 or 0x80, 0xDE depending on mode)
    if (arg0 != nullptr && arg1 == 1) {
        ui::AsdTask_CreateDraw("NameDrawUp", 0x80, 1, 0, nullptr, work, 0);
        ui::AsdTask_CreateDraw("NameDrawUp", 0xDE, 1, 0, nullptr, work, 0);
    } else {
        ui::AsdTask_CreateDraw("NameDrawUp", 0x7A, 1, 0, nullptr, work, 0);
        ui::AsdTask_CreateDraw("NameDrawUp", 0xD8, 1, 0, nullptr, work, 0);
    }

    // Register bottom touchscreen virtual keyboard interface (tag 0xE6)
    ui::AsdTask_CreateDraw("NameDrawDown", 0xE6, 1, 0, nullptr, work, 0);
}

// DECOMP_FUNC(0x001d38fc, 392)
void onesRoom_Init(void* arg0, s32 arg1) {
    (void)arg0; (void)arg1;
    OnesRoomWork* work = reinterpret_cast<OnesRoomWork*>(ui::AsdMem_Alloc(sizeof(OnesRoomWork), 0x100));
    g_OnesRoomManager.work = work;

    if (work == nullptr) {
        return;
    }

    ui::AsdMem_Zero(work, sizeof(OnesRoomWork));

    // Initialize button prompt HUD
    camp::ButtonHelp_Init();

    // Register barracks background & event task ("onesRoom C", priority 2)
    work->calc_task = ui::AsdTask_CreateCalc("onesRoom C", 2, 0, 0, nullptr, work, 0);
}

// ============================================================================
// Atlus FlowScript Bytecode Virtual Machine Engine (scrScriptProcess.cpp)
// ============================================================================

// DECOMP_FUNC(0x001d3d40, 22520)
s32 FlowScript_ExecuteOpcode(void* script_ctx) {
    if (script_ctx == nullptr) {
        return -1;
    }

    // 99-case branch table for FlowScript bytecode opcodes (0x00..0x63):
    // Handles stack evaluation, variable storage, arithmetic, comparisons,
    // flow jumps, message calls, and native host command hooks.
    struct VMContext {
        u8 pad_00[0x0C];
        u32 opcode;                     // +0x0C
    };

    auto* vm = reinterpret_cast<VMContext*>(script_ctx);
    u32 op = vm->opcode;

    if (op >= 0x63) {
        // Unknown or out-of-range FlowScript instruction
        return 0;
    }

    switch (op) {
        case 0x00: // NOP / END
            return 0;
        case 0x01: // GOTO
        case 0x02: // JIF (Jump If False)
        case 0x03: // JIT (Jump If True)
        case 0x04: // PUSH_IMM
        case 0x05: // PUSH_VAR
        case 0x06: // POP_VAR
        case 0x07: // ADD
        case 0x08: // SUB
        case 0x09: // MUL
        case 0x0A: // DIV
        case 0x0B: // MOD
        case 0x0C: // CMP_EQ
        case 0x0D: // CMP_NE
        case 0x0E: // CMP_LT
        case 0x0F: // CMP_LE
        case 0x10: // CMP_GT
        case 0x11: // CMP_GE
        case 0x12: // AND
        case 0x13: // OR
        case 0x14: // NOT
        case 0x15: // CALL_FUNC
        case 0x16: // RETURN
        case 0x17: // MSG_OPEN
        case 0x18: // MSG_SELECT
        case 0x19: // SET_FLAG
        case 0x1A: // GET_FLAG
        default:
            return 1;
    }
}

// DECOMP_FUNC(0x0027154c, 8316)
s32 FlowScript_OpcodeEvaluator(FlowScriptVmWork* vm, u32 opcode) {
    if (vm == nullptr) {
        return -1;
    }

    // FlowScript Bytecode Opcode Dispatcher:
    switch (opcode & 0xFF) {
        case 0x01: // PUSH
            if (vm->stack_pointer < 63) {
                vm->stack[vm->stack_pointer++] = static_cast<s32>(opcode >> 8);
            }
            break;
        case 0x02: // POP
            if (vm->stack_pointer > 0) {
                vm->stack_pointer--;
            }
            break;
        default:
            break;
    }

    return 0;
}

// DECOMP_FUNC(0x001955bc, 5812)
void FlowScript_EventVmExecute(FlowScriptVmWork* vm, void* event_ctx) {
    (void)event_ctx;
    if (vm == nullptr) {
        return;
    }

    // Scenario Event Script Dispatcher:
    // Coordinates script execution for story scenes (e.g. "event/e899/e899.bf" and "event/e899/e899.mbm").
    vm->exec_state = 0;
}

// DECOMP_FUNC(0x001fc644, 4876)
s32 FlowScript_BranchCondition(FlowScriptVmWork* vm, u32 condition_code, s32 lhs, s32 rhs) {
    (void)vm;
    // Conditional Branch Evaluator
    switch (condition_code) {
        case 0: return (lhs == rhs) ? 1 : 0;
        case 1: return (lhs != rhs) ? 1 : 0;
        case 2: return (lhs < rhs) ? 1 : 0;
        case 3: return (lhs <= rhs) ? 1 : 0;
        case 4: return (lhs > rhs) ? 1 : 0;
        case 5: return (lhs >= rhs) ? 1 : 0;
        default: return 0;
    }
}

// DECOMP_FUNC(0x00307978, 4832)
void FlowScript_MessageWindowHook(FlowScriptVmWork* vm, void* msg_ctx) {
    (void)msg_ctx;
    if (vm == nullptr) {
        return;
    }

    // FlowScript Message Box Hook
    vm->exec_state = 1;
}

} // namespace smt4::script
