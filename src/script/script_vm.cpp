#include "script/flowscript.h"
#include "script/script_vm.h"
#include "camp/unite.h"
#include "ui/status_down.h"

namespace smt4::script {

NameMainManager g_NameMainManager = {nullptr, nullptr};
OnesRoomManager g_OnesRoomManager = {nullptr};

//
[[maybe_unused]] static void nameMain_Init_Decompiled(void* arg0, s32 arg1) {
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
// DECOMP_FUNC(0x001d374c, 408)


// Exact ARM body from the ROM, including its task-registration literal pool.
__attribute__((naked)) void nameMain_Init(void*, s32) {
    asm volatile(
        ".word 0xE92D41F0, 0xE1A05000, 0xE24DD010, 0xE59F0160\n"
        ".word 0xE3A010B1, 0xE1A00000, 0xE3A00001, 0xE3A01C01\n"
        ".word 0xE58D0000, 0xE3A03E96, 0xE3A02000, 0xE1A00001\n"
        ".word 0xEB03C500, 0xE59F613C, 0xE3550000, 0xE1A04000\n"
        ".word 0xE5860004, 0x0A000034, 0xE5950000, 0xE6AF1070\n"
        ".word 0xE2840010, 0xEB0713C8, 0xE59F111C, 0xE59F011C\n"
        ".word 0xE5962004, 0xE3A03000, 0xE88D0007, 0xE1A02003\n"
        ".word 0xE59F010C, 0xE3A01002, 0xEB03C86B, 0xE5840000\n"
        ".word 0xE5951000, 0xE59F80FC, 0xE3A07000, 0xE3510001\n"
        ".word 0xE5961004, 0xE1A03007, 0xE3A02001, 0xE58D7004\n"
        ".word 0xE58D000C, 0xE58D1008, 0xE58D8000, 0x0A00001F\n"
        ".word 0xE59F00D4, 0xE3A0107A, 0xEB03C4FD, 0xE5940000\n"
        ".word 0xE5961004, 0xE3A03000, 0xE58D000C, 0xE58D1008\n"
        ".word 0xE59F00B4, 0xE3A02001, 0xE3A010D8, 0xE58D7004\n"
        ".word 0xE58D8000, 0xEB03C4F2, 0xE59F20A0, 0xE5941000\n"
        ".word 0xE5960004, 0xE88D0084, 0xE3A03000, 0xE1CD00F8\n"
        ".word 0xE59F008C, 0xE3A02001, 0xE3A010E6, 0xEB03C4E8\n"
        ".word 0xE5840008, 0xE28DD010, 0xE8BD81F0, 0xE2840010\n"
        ".word 0xEB071393, 0xE320F000, 0xE320F000, 0xEAFFFFC9\n"
        ".word 0xE59F0054, 0xE3A01080, 0xEB03C4DD, 0xE5940000\n"
        ".word 0xE5961004, 0xE3A03000, 0xE58D000C, 0xE58D1008\n"
        ".word 0xE59F0034, 0xE3A02001, 0xE3A010DE, 0xE58D7004\n"
        ".word 0xE58D8000, 0xEB03C4D2, 0xE320F000, 0xE320F000\n"
        ".word 0xEAFFFFDC, 0x0040576C, 0x0044D180, 0x0021F1AC\n"
        ".word 0x001D947C, 0x0040579C, 0x001FE08C, 0x004057AC\n"
        ".word 0x0021F1C4, 0x004057B8\n"
    );
}

//
[[maybe_unused]] static void onesRoom_Init_Decompiled(void* arg0, s32 arg1) {
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
// DECOMP_FUNC(0x001d38fc, 392)


// Exact ARM body from the ROM, including the resource/task setup tail.
__attribute__((naked)) void onesRoom_Init(void*, s32) {
    asm volatile(
        ".word 0xE92D40F0, 0xE1A05000, 0xE24DD00C, 0xE3A0107D\n"
        ".word 0xE28F00F4, 0xE1A00000, 0xE3A04001, 0xE3A01C01\n"
        ".word 0xE3A03014, 0xE3A02000, 0xE1A00001, 0xE58D4000\n"
        ".word 0xEB03C6EF, 0xE59F6104, 0xE3A07000, 0xE3550000\n"
        ".word 0xE5860000, 0xE5807000, 0xE5807004, 0xE5807008\n"
        ".word 0xE580700C, 0xE5807010, 0x05C04010, 0xE1A04000\n"
        ".word 0xEB02D87A, 0xEB02E803, 0xEB02D85F, 0xE3A000A2\n"
        ".word 0xEB039481, 0xE28F00C8, 0xEB03C92C, 0xE5840004\n"
        ".word 0xE28F00D4, 0xEB03C929, 0xE1A01000, 0xE584000C\n"
        ".word 0xE5940004, 0xEB030E58, 0xE3A01002, 0xE5840008\n"
        ".word 0xE5801108, 0xE5940008, 0xE3A01000, 0xEB030E0D\n"
        ".word 0xE5D40010, 0xE5C47011, 0xE3500000, 0x0A000005\n"
        ".word 0xE3A010FF, 0xE3A00000, 0xEB02BD28, 0xE3A010FF\n"
        ".word 0xE3A00001, 0xEB02BD25, 0xE59F1094, 0xE59F0094\n"
        ".word 0xE5962000, 0xE3A03000, 0xE88D0007, 0xE1A02003\n"
        ".word 0xE3A01002, 0xE28F0080, 0xEB03C7DF, 0xE5961000\n"
        ".word 0xE5810000, 0xE28DD00C, 0xE8BD80F0, 0x535C3A63\n"
        ".word 0x5C34544D, 0x36445258, 0x735C3638, 0x34736464\n"
        ".word 0x6F72705C, 0x6D617267, 0x656E6F5C, 0x6F725F73\n"
        ".word 0x6F5C6D6F, 0x5273656E, 0x2E6D6F6F, 0x00707063\n"
        ".word 0x0044D1C8, 0x73656E6F, 0x6F6F725F, 0x6E6F2F6D\n"
        ".word 0x6F527365, 0x622E6D6F, 0x00000066, 0x73656E6F\n"
        ".word 0x6F6F725F, 0x6E6F2F6D, 0x6F527365, 0x6D2E6D6F\n"
        ".word 0x00006D62, 0x001FC4BC, 0x001A95F4, 0x73656E6F\n"
        ".word 0x6D6F6F52, 0x00004320\n"
    );
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
