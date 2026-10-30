# H4 Phase 2: ScriptVM_NestedHandler11 Candidate Report

## 1. Executive Summary
- **Target Function**: `0x001B4B98` (`ScriptVM_NestedHandler11`)
- **Original Size**: 36 bytes
- **Candidate Size**: 36 bytes (freestanding ARMv6K compilation)
- **Status**: PASSED (4/4 fixtures, differential equivalence verified against original binary, mutation detected)

## 2. Function Contract & Semantic Behavior
- **Context**: Field script VM nested opcode 11 handler.
- **Inputs**: None (`r0` initialized internally to 0).
- **Control Flow**:
  1. Call `ScriptVM_GetBounds_00296f60(0)` to retrieve upper bound limit.
  2. Call `ScriptVM_ClampRange_00297004(0, max_val)` to clamp range.
  3. Call `ScriptVM_ApplyState_0028df54(clamped)` to apply clamped field parameter.
  4. Returns literal integer `1` (success/continue status).

## 3. Verification Evidence
- Differential runner: `tools/h4_script_vm_handler_experiment.py` using Unicorn ARM11MPCore.
- Fixtures:
  - `normal_range`: returns 1, invokes all three callees with correct sequence.
  - `zero_range`: handles zero bound limit, passes 0 to apply state.
  - `negative_bounds`: handles clamped negative lower boundary.
  - `large_bounds`: handles high range limit.
- Mutation test: inverted return status (0 instead of 1) detected and flagged as differential mismatch.
