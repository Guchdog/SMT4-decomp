# H4 Phase 2: PlayerActor_UpdateVisibilityTransform Candidate Report

## 1. Executive Summary
- **Target Function**: `0x001B4A54` (`PlayerActor_UpdateVisibilityTransform`)
- **Original Size**: 288 bytes
- **Candidate Size**: 284 bytes (freestanding ARMv6K compilation)
- **Status**: PASSED (8/8 fixtures, differential equivalence verified against original binary, mutation detected)

## 2. Function Contract & Semantic Behavior
- **Context**: Executed every field frame tick by master dispatcher `0x002767B0` during field traversal.
- **Inputs**:
  - `g_PlayerActorWork` (`0x0044CDA0`): dereferenced to `PlayerActorWork` structure.
  - `g_RepeatGate` (`0x0049F91C`): global pause gate; offset `+0x22` (`menu_pause_flag`).
  - Model backend at `model->backend` (`offset +0x08`).
  - Visual node at `backend->visual_node` (`offset +0x2C`).
- **Control Flow**:
  1. Early exit if `model == NULL`.
  2. If `g_RepeatGate.menu_pause_flag != 0`:
     - If `(model->flags & 2) == 0`: set bit 2 (`flags |= 2`) and hide model (`visible_1f6 = 0`).
     - Early return (transform updates suppressed during pause/menu).
  3. If not paused:
     - If `state->active != 0`: if hidden (`flags & 2`), clear bit 2 (`flags &= ~2`) and make visible (`visible_1f6 = 1`).
     - If `state->active == 0`: if visible (`!(flags & 2)`), set bit 2 (`flags |= 2`) and hide model (`visible_1f6 = 0`).
  4. Transform Commit:
     - Check `state->dirty_flag`. If 0, return.
     - Call `Model_SetTranslation_0028c8a8(backend, 0, state->pos)`.
     - Call `Model_SetRotation_0028c880(backend, 0, 0.0f, state->yaw, 0.0f)`.
     - Call `Model_SetScale_002a5a54(backend, scale, 0.0f)`.
     - Call `Model_CommitTransform_00287300(backend, scale, 0.0f)`.
     - Clear `state->dirty_flag = 0`.

## 3. Verification Evidence
- Differential runner: `tools/h4_player_transform_experiment.py` using Unicorn ARM11MPCore.
- Fixtures:
  - `paused_visible`: hides model, sets flag bit 2, skips transform.
  - `paused_hidden`: retains hidden state, skips transform.
  - `unpaused_active_hidden`: restores visibility, executes all 4 transform subroutines, clears dirty bit.
  - `unpaused_active_visible`: retains visibility, executes all 4 transform subroutines, clears dirty bit.
  - `unpaused_inactive_visible`: hides model, skips transform.
  - `unpaused_inactive_hidden`: retains hidden state, skips transform.
  - `unpaused_inactive_dirty`: hides model, executes transform updates because dirty flag is set.
  - `null_model`: safely exits without dereferencing or calling transform backend.
- Mutation test: inverted active logic correctly caused differential failure against original retail binary.
