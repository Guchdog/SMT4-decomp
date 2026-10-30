# H4 Phase 2: ScriptVM_NestedHandler11 Candidate Review

## Review Metadata
- Target: `0x001B4B98` (`ScriptVM_NestedHandler11`)
- Artifacts reviewed:
  - `experiments/semantic_equivalence/h4_script_vm_handler_candidate.cpp`
  - `tools/h4_script_vm_handler_experiment.py`
  - `docs/agent-work/h4-script-vm-handler-candidate.md`

## Evaluation
1. **Calling Convention & Safety**:
   - Freestanding C++ compiled for ARMv6K.
   - Restores stack frame and returns 1 in `r0`.
   - Size is exactly 36 bytes matching the target window.
2. **Behavioral Integrity**:
   - Accurately invokes the 3 VM helper routines in order with identical register arguments.
   - Verified across 4 differential fixtures with positive mutation detection.
3. **Recommendation**:
   - ACCEPT candidate for integration into `code.h4-final.bin` and IPS patch.
