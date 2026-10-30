using s32 = int;
using u32 = unsigned int;

extern "C" {
    s32 ScriptVM_GetBounds_00296f60(s32 index);
    s32 ScriptVM_ClampRange_00297004(s32 min_val, s32 max_val);
    void ScriptVM_ApplyState_0028df54(s32 value);

    s32 h4_script_vm_handler_candidate();
    s32 h4_script_vm_handler_mutation();
}

s32 h4_script_vm_handler_candidate() {
    s32 max_val = ScriptVM_GetBounds_00296f60(0);
    s32 clamped = ScriptVM_ClampRange_00297004(0, max_val);
    ScriptVM_ApplyState_0028df54(clamped);
    return 1;
}

s32 h4_script_vm_handler_mutation() {
    s32 max_val = ScriptVM_GetBounds_00296f60(0);
    s32 clamped = ScriptVM_ClampRange_00297004(0, max_val);
    ScriptVM_ApplyState_0028df54(clamped);
    return 0; // Mutated return value
}
