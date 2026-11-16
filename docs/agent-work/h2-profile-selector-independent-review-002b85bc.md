# Independent Review: `0x002B85BC` (`ui_func_002b85bc`) Profile Selector

## Verdict

**Disposition:** **Accept** `ui_func_002b85bc` (`src/engine/leaf_batch44_c.cpp:1232-1290`, `non_matching`, `372/472` bytes, `11` even ARM `R_ARM_CALL` relocations) for its bounded hook-modeled domain and both exercised caller slices (`0x99`, `0xDC`).

This review does not claim transitive service equivalence, live TBB/profile data, or Azahar audio/runtime equivalence.

## 1. Independent Disassembly & Contract Audit (`0x002B85BC`, 472 bytes)

Inspected `extracted/exefs/code.bin` (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`) at `0x002B85BC..0x002B8794` (literal `0x0043DA28` at `0x002B8790`) and verified all 16 `input_sha256` pins:

- **Profile lookups & early return**: Reads `O = *(u32*)(0x0043DA28 + 4)`, calls `0x002AEA28(O[0x4C9])` then `0x002AEA28(request)`. If either returns `0`, returns `r0` of the second lookup (`0x002B85E0..0x002B85E8`).
- **Three profile-flag branches & status-8 multiplicity**:
  - `old_profile[0x0C] == 0 && new_profile[0x0C] != 0`: reloads `O` from `0x0043DA28 + 4`, loops `i = 0..5` calling `0x002BF030(O + 0x34 + 0x8C*i, 1)`, clears nonzero `O[0x494 + 4*i]` to `0` and calls `0x002A8A8C()` once; then loops `j = 0..1` on `O + 0x37C + 0x8C*j`, rereading `O[0x4C8]` (`== 1 -> 0x002BDAC0(slot, 3, 0)`, else `0x002AA268(slot, 0, 1)`).
  - Otherwise (`old[0x0C] != 0` or `new[0x0C] == 0`): reloads `O`, loops `i = 0..5` calling `0x002BF030(O + 0x34 + 0x8C*i, 1)`; skips `0`, calls `0x002A8A8C()` once if `7` or `9`, reloads `O[0x494 + 4*i]`, and calls `0x002A8A8C()` `3` times if `8` else `1` time.
- **Cleanup & return**: Reloads `O` from `0x0043DA28 + 4`, writes `*(u32*)(O + 0x0C) = 0`, `*(u32*)(O + 0x10) = 3`, returns `O + 0x0C`.
- **Ledger**: `config/functions.csv` truthfully classifies `0x002b85bc` as `non_matching`.

## 2. Fresh Offline Rerun & Affected TUs

- `python tools/h2_profile_selector_experiment.py --out build/agent-work/H2-semantic/h2-profile-selector-review-002b85bc/run-001/checks/fresh` (exit `0`, `report.json` SHA-256 `398a1b757ddfdc1a2776b362705c4968a0adf516a8a4186861193276ba73405a`):
  - `9/9` direct cases (`mismatch_count=0`, including `old_profile_null`, `new_profile_null`, `old_active_status_matrix`, `status_7_mutates_to_8_then_three_call_block`, `new_active_status_clear_mode_1`, `new_active_status_clear_mode_2`, `both_profile_flags_zero`, `manager_pointer_reload`, `null_object_fault` at `0x4C9`).
  - `2/2` original `0x002B8B78` caller slices (`title_config_init_request_0x99`, `nested_callback_request_0xDC`, `equal=true`).
  - `5/5` negative controls detected (`loop_bound`, `status_clear`, `service_multiplicity`, `two_slot_args`, `cleanup_value`).
  - `372/472` bytes, `11` even ARM `R_ARM_CALL` relocations (`0x002AEA28` x2, `0x002A8A8C` x4, `0x002BF030`, `0x002BDAC0` x2, `0x002AA268` x2; all `target_bit0_clear=true`), `ips_replay=true`, `changed_outside_slot=false`.
- `python tools/build_check.py --tu src/engine/leaf_batch32_c.cpp --out-dir .../run-001/tu-compile -j 1` (exit `0`, `.o` SHA-256 `9f98ea6a7f0f7c96644e6a2fb4b6503390c66d80f78e14ab1a33b7e926d63b1e`) and `src/engine/leaf_batch44_c.cpp` (exit `0`, `.o` SHA-256 `f46154067a8aca79e270014fc7a26b5e16d5e41f49e5573c34fce34eed8fd7eb`).

## 3. Limits

- Deterministic hooks for all 5 direct callees and wrapper helpers; valid non-aliased ordinary RAM (plus the single explicit `null_object_fault` read at `0x4C9`); live TBB/audio/runtime remain unverified.
