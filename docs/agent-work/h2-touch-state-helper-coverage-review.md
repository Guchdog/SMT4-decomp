# Follow-up review: touch-state getter equality coverage

## Result

The final-all-states report resolves the previously reported state-1 gap. Its 45 directed matching-handle cases form the complete Cartesian product of nine sampled active indices and raw states `{0, 1, 2, 6, 255}`. Each entry has `active == handle`, `match: true`, and `return == state`; this includes all nine matching cases with state `1`. The unchanged full signed-handle matrix still passes 589,824/589,824 cases, and the wrong-index control remains detected with active `10`, handle `11`, state `6`, original return `0`, mutant return `6`.

This closes the state-1 equality-branch coverage gap for the five selected byte values. It does not exercise all 256 byte values, all possible active-index values, or runtime touch semantics.

## Report and validation logic

Reviewed report: `build/agent-work/H2-semantic/h2-touch-state-helper-production/run-003/checks/final-all-states-20261026/report.json`. Its final file SHA-256 is `ffa1852f6e9764f3af645f20aeb31e0cc65bc43fe5b81c1a87d131d62a31c4f3`, matching the task packet and updated integration record. The report's embedded `report_sha256` is `02e0c4f74f027f87d400d7a994a77c35f4d2550584b6efc455a9329736422203`; the runner computes this before adding that field and rewriting the file, so the external final-file hash is the provenance digest.

I inspected `tools/h2_touch_state_experiment.py` without running it. For each directed equality case, the runner invokes pinned ARM and the compiled candidate, compares fault/return/PC/SP/preserved-register observations, checks the expected return against the raw state, and verifies preserved registers. The `original_writes` and `candidate_writes` hooks accumulate across the full matrix and the directed cases; any guest writes fail the report. The report lists both write arrays as empty. The status is `passed` with `first_mismatch: null`.

The report's `abi_and_effects.callee_saved_registers_preserved` field is computed from the empty write arrays, rather than directly from the per-call preservation booleans. However, the run loop independently fails on any `r4-r11`/SP preservation drift, and each directed equality case checks preservation before it is recorded. Thus the passed status is the meaningful ABI evidence; the boolean's construction is a metadata-quality caveat.

The wrong-index control is unchanged from the first review and remains sensitive to ignoring the active-index comparison: active `10`, handle `11`, raw state `6` yields original `0` versus mutant `6`. The corrected report still records `detected: true`.

## Integration and remaining limits

The first review's integration boundary remains accurate. The production-source function is 44 bytes against the original 40-byte span, remains `non_matching`, and was not installed in code.bin/IPS. Source promotion and helper differential are separate from code-image patching. H2 runtime acceptance remains open.

The report conditions behavior on an initialized IfTouch manager and tests only nine selected active indices. It does not determine what the raw state byte means, how the touch callback is scheduled relative to H2 Calc, how active indices relate to H2 handles at runtime, or what physical input produces the byte. No visible UI, persistence, restart, or Azahar runtime behavior is established.

I read the prepared sources and report and recomputed the final report hash. No builds, tests, emulator, RSP, or UI actions were performed. The prior state-1 coverage limitation is resolved for the listed five sampled values; retain all no-IPS and runtime limits in the H2 decision.
