# H4 Phase 2: Map_DispatchTrigger Candidate Report

## 1. Executive Summary
- **Target Function**: `0x001B4B74` (`Map_DispatchTrigger`)
- **Original Size**: 36 bytes
- **Candidate Size**: 32 bytes (freestanding ARMv6K compilation)
- **Status**: PASSED (5/5 fixtures, differential equivalence verified against original binary, mutation detected)

## 2. Function Contract & Semantic Behavior
- **Context**: Map event trigger dispatcher, responsible for signaling map trigger handling subsystem when map context is active.
- **Inputs**:
  - `g_MapContextWork` (`0x0044CFD0`): dereferences `manager` pointer at offset `+0x04`.
  - `manager->trigger_handler` at offset `+0x08`.
- **Control Flow**:
  1. Inspect `g_MapContextWork.manager`. If null, early exit.
  2. Inspect `manager->trigger_handler`. If null, early exit.
  3. Tail-call `TriggerHandler_SetPendingFlag_003ba944(handler)`, which sets bit `0x80` at `handler + 0x20`.

## 3. Verification Evidence
- Differential runner: `tools/h4_map_dispatch_experiment.py` using Unicorn ARM11MPCore.
- Fixtures:
  - `full_chain_clean`: valid manager & handler, sets flag `0x80`.
  - `full_chain_preflagged`: flag already contains `0x80`, preserves bitfield integrity.
  - `full_chain_other_flags`: bitwise OR `0x55 | 0x80 = 0xD5` verified.
  - `null_manager`: gracefully exits with 0 target calls.
  - `null_handler`: gracefully exits with 0 target calls.
- Mutation test: inverted handler null check correctly produced differential mismatch against retail original.
