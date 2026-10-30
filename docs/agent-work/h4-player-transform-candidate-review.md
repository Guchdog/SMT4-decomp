# H4 Phase 2: PlayerActor_UpdateVisibilityTransform Candidate Review

## Review Metadata
- Target: `0x001B4A54` (`PlayerActor_UpdateVisibilityTransform`)
- Artifacts reviewed:
  - `experiments/semantic_equivalence/h4_player_transform_candidate.cpp`
  - `tools/h4_player_transform_experiment.py`
  - `docs/agent-work/h4-player-transform-candidate.md`

## Evaluation
1. **ABI and Calling Conventions**:
   - Freestanding C++ compiled for ARMv6K hard-VFP.
   - Preserves `r4-r6`, `d8`, `lr`. Correctly restores stack and registers upon exit.
   - Size is 284 bytes, fitting inside the 288-byte allocated slot.
2. **Correct Pointer Semantics**:
   - Correctly distinguishes pointer-to-pointer dereference for `g_PlayerActorWork` (`0x0044CDA0`) versus direct global struct addressing for `g_RepeatGate` (`0x0049F91C`).
3. **Differential Verification Quality**:
   - 8 distinct offline fixtures simulated under Unicorn ARM11MPCore.
   - Bitwise flag updates (`model->flags & 2`), visual node byte mutation (`offset 0x1F6`), dirty bit clearance (`state->dirty_flag = 0`), and call mock parameters match the original binary identically.
   - Positive mutation detection passes.
4. **Recommendation**:
   - ACCEPT candidate for integration staging into `code.h4-final.bin` and IPS patch.
