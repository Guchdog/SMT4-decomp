# `0x00286928` runtime probe (`runtime-probe-002`) — independent read-only review

**Verdict: ACCEPT `runtime-probe-002` (`7ea75a94...`) as bounded paired runtime evidence for the recorded 812-byte cumulative image (`1616aa24...` / IPS `cc63c2fe...`), while keeping the historical 812-byte vs current 808-byte (`df697fe2...`) distinction in `docs/function-records/0x00286928.md` and all H2-open / stub / reachability limits explicit.**

## 1. Frozen pins, cumulative image/IPS, & runtime report audit

- Read-only audit (`compiler_slots: 0`); no build, runner rerun, or emulator was run.
- Recomputed all `13/13` `input_sha256` entries in `build/agent-work/H2-semantic/h2-helper-00286928-runtime-review/run-001/task.json`: `13/13` matched (`reference_sha256` = `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- `build/h2-86928-integration/cumulative-image/manifest.json` (`bfb7826d...`):
  - `base_sha256`: `f87b3149c03a58cc16eb3e903f0102b6f7ce47fdb3523740e992c3824f94e940`
  - `patched_sha256`: `1616aa24873a72beafdc9ae12cf688f9d7575b11a3f9b3f366c77fddd1f4e703`
  - `ips_sha256`: `cc63c2fe655bdc38c3c017531cc429de6eb9c9a287f6f9c5ad31126a8e5a2252` (`629` records, `ips_roundtrip: true`, `only_new_slot_differs_from_base: true`).
- `build/h2-86928-integration/runtime-probe-002/autonomous-gdb-verification.json` (`7ea75a94...`):
  - `passed: true`, `paired_scripted_behavior_matched: true`, `scripted_action_count: 51`, `checkpoint_comparisons`: `19/19` passed (`g_ConfigBytes_equal: true`, `TitleConfigWork_normalized_equal: true`).
  - `helper_runtime_probe`: `address: "0x286928"`, `original_hit_count: 129`, `patched_hit_count: 129`, `entry_arguments_and_raw_returns_matched: true` (capturing `r0..r3`, `[sp]`, `[sp+4]`, and return `r0`, all with `r3 = 6`, `stack_words = [0, 0]`, `lr in {0x001ECC04, 0x0031E94C}`).

## 2. Wrapper & breakpoint capture audit (`tools/h2_86928_runtime_verify.py`)

- Sets software breakpoint at even ARM entry `0x00286928`, captures `r0..r3`, `sp`, `lr`, and `[sp], [sp+4]`, clears `0x00286928`, single-steps one instruction (`pc == 0x0028692C`), re-arms `0x00286928`, sets a transient breakpoint at `lr` (when `lr != target`), and records `{pc, r0}` on return before clearing `lr`. Handles nested hits recursively.

## 3. Preserved limits & claim scope

- `docs/function-records/0x00286928.md` and `docs/agent-work/h2-86928-implementation.md` accurately preserve:
  - `h2_full_acceptance_supported: false`, `controlled_lifecycle_completed: false`, `same_session_reentry_both: false`.
  - `physical_input_mapping_proven: false`, `input_scheduling_proven: false` (uses `UiListCursor_SetSelectedRow` + one-frame logical query stub).
  - Historical 812-byte cumulative image scope vs the current 808-byte `q=0` pointer-reload revision (`df697fe2...`); does not prove all 17 callees, all selector branches, or whole-game equivalence.
