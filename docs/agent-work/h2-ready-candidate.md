# H2 candidate: `TitleConfig_IsReady` (`0x002FC0EC`)

Status: experimental C++ reconstruction and isolated ARM differential passed. Caller composition and runtime evidence remain open.

## Contract

The function has no explicit parameters and returns its boolean-like result in `r0`. It loads `g_TitleConfigWork` from `0x0044E2D0`. A null work pointer returns `1` (ready). With non-null work, it forwards the first word (`work->calc_task`) to `battle_func_002BF41C`; an active/registered task returns `0` (not ready), and an unregistered task returns `1`. In particular, `work->calc_task == nullptr` is passed to the helper rather than handled locally.

The title caller invokes this predicate in `TitleMain_Calc` state 10. It stays in state 10 while the result is zero and calls `Title_ResetForBoot` when the result is nonzero. The task helper's boolean-like lookup contract and the initializer's first-field layout are taken from the accepted H2 secondary/init contract evidence; this task does not revalidate the helper implementation.

## Implementation and verification

- Editable experimental implementation: `experiments/semantic_equivalence/h2_ready_candidate.cpp`.
- Differential runner: `tools/h2_ready_experiment.py`.
- Focused tests: `tests/test_h2_ready_experiment.py`.
- Function record: `docs/function-records/0x002fc0ec.md`.
- Final run: `build/agent-work/H2-semantic/h2-ready-candidate/run-001/checks/differential-002/report.json`.

The runner compiled one ARMv6K object and compared the pinned original function to the candidate at a separate address under an identical explicit helper model. It matched 4/4 cases across null-global, registered-task, unregistered-task, and null-task-handle forwarding conditions. The incorrect always-ready candidate was caught on the registered-task case. The comparator also checked helper trace, return PC, stack pointer, and `r4` preservation. Five focused unit tests pass.

## Harness refinement after independent review

The independent review found that the first synthetic work fixture (`0x00410000`) overlapped the mapped `code.bin` region. The candidate did not show a mismatch, but that workspace was not suitable for broader composition. The runner now maps the fixture at `0x00500000`, outside the full mapped image range, and rejects any future overlap. It also checks SP, `r4-r11`, and `d8-d15` preservation.

The corrected run is `build/agent-work/H2-semantic/h2-ready-harness-fix/run-003/checks/differential/report.json`; it again passes all 4 lifecycle cases and detects the always-ready negative control. The refreshed focused suite passes 7 tests. The earlier run remains historical evidence only.

## Development attempts and limits

An initial compilation probe used an invalid `constexpr reinterpret_cast` and was corrected before the final compile. The first differential run mapped only the text size and failed before emulation because the configured `code.bin` image also contains data through `0x00477000`; the runner was corrected to map the complete pinned image, and the succeeding run matched all cases. These failures did not modify the original image.

The differential models `battle_func_002BF41C`; it does not exercise that helper's body. The title state-10 caller was traced statically, but no caller-composition test with this candidate was run. No Azahar, input, edit/cancel/confirm, persistence, or restart scenario was run. The production source and ledger are unchanged, and the byte-different work must not be labeled `matching` if later promoted.

Next: independently review the candidate and runner, then integrate only with explicit runtime evidence for the title completion path and the wider H2 scenario.
