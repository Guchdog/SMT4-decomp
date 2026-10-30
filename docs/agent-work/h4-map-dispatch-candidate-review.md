# H4 Phase 2: Map_DispatchTrigger Candidate Review

## Review Metadata
- Target: `0x001B4B74` (`Map_DispatchTrigger`)
- Artifacts reviewed:
  - `experiments/semantic_equivalence/h4_map_dispatch_candidate.cpp`
  - `tools/h4_map_dispatch_experiment.py`
  - `docs/agent-work/h4-map-dispatch-candidate.md`

## Evaluation
1. **Calling Convention & Safety**:
   - Freestanding C++ compiled for ARMv6K.
   - Clean leaf/tail-call flow; preserves non-volatile registers.
   - 32 bytes compiled, within 36-byte target window.
2. **Behavioral Integrity**:
   - Accurately models the two-level pointer dereference `g_MapContextWork.manager->trigger_handler`.
   - Tail-calls `TriggerHandler_SetPendingFlag_003ba944` with `handler` as `r0`.
   - Verified across 5 differential fixtures with positive mutation detection.
3. **Recommendation**:
   - ACCEPT candidate for integration into `code.h4-final.bin` and IPS patch.
