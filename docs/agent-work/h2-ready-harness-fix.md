# H2 readiness differential harness correction

Status: corrected isolated differential passed. No candidate semantics, production source, ledger, caller flow, or emulator runtime was changed.

The independent review identified that the first synthetic `TitleConfigWork` fixture at `0x00410000` fell inside the mapped pinned `code.bin` region (`0x00100000..0x00478000`). It did not expose a predicate mismatch in the original four-case matrix, but it could overwrite image data and was unsuitable for broader composition.

## Correction

- The synthetic workspace now maps at `0x00500000`, outside the full code mapping. `validate_workspace_layout` rejects overlap before executing either callback.
- The differential seeds and checks SP, general callee-saved `r4-r11`, and VFP callee-saved `d8-d15`.
- Original ARM and candidate still share the same explicit registration lookup mock. The candidate source is unchanged.

## Verification

- `python -m py_compile tools/h2_ready_experiment.py tests/test_h2_ready_experiment.py` — passed.
- `python -m unittest tests.test_h2_ready_experiment -v` — 7 tests passed, including accepted non-overlap and rejected overlap.
- `python tools/h2_ready_experiment.py --output build/agent-work/H2-semantic/h2-ready-harness-fix/run-003/checks/differential --code extracted/exefs/code.bin` — 4/4 lifecycle cases passed; the always-ready negative control was detected.
- Corrected report: `build/agent-work/H2-semantic/h2-ready-harness-fix/run-003/checks/differential/report.json`.

Candidate source SHA-256 remains `c90953425118541e7baea4f02f16d2793a5a9a34119a5fe753156c443e28f0ae`. Refreshed runner SHA-256 is `663563a5d61f21a496eeaffd49c87bc66f694cf2181f0e3bb3f8d5dfa44df0a8` and object SHA-256 is `f042839a9a9ead45e70786b8af6e47f7b28fc4fe35a841ee84dfcde604af557d`.

## Limits

This remains an isolated callback experiment. `battle_func_002BF41C` is mocked; the title state-10 caller has not been executed with the candidate, and Azahar, H2 input, persistence and restart remain untested. The original overlapping-fixture run is superseded. The updated function record points to the corrected run; production source and ledger remain unchanged.
