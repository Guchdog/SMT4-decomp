# H18 private staging: fitting `0x003f` initializer subentries

## Result and artifacts

Using pinned `code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, I compiled candidates and staged exactly 11 bodies at their original final VMAs into a private image. No production source, ledger, task board, canonical build cache, or emulator was changed.

- Staged image: `build/agent-work/batch-h18-001/h18-003f-family-fit-staging/run-001/checks/final-fit/staged_code.bin`, SHA-256 `e886bd9e322129e93cf7b8cbad7e3cfe705fc55981b1e37de8f93cbb95a36e53`.
- IPS: `build/agent-work/batch-h18-001/h18-003f-family-fit-staging/run-001/checks/final-fit/candidate.ips`, SHA-256 `d94d484cbb1e087e74e07eb845b772e5f98730ac568a34c2254b963fa7dc519c`.
- Validation report: `build/agent-work/batch-h18-001/h18-003f-family-fit-staging/run-001/checks/final-fit/report.json`, SHA-256 `2ca9c6497136f23237a84ff1103d16224eb15637d6dd6933f44cdc24ede18d84`.

The 11 compiled candidates were relocation-free per their compile helpers, ARM-word aligned, and each fit its assigned interval: `0x003f3274` (120/128 bytes), eight entries `0x003f32f4..0x003f3428` (36/44 bytes each), and `0x003f34a0`/`0x003f34cc` (36/44 bytes each). Total changed bytes were 361, all within those candidate bodies. IPS replay reproduced the staged image. The entire `0x003f31d8..0x003f34f8` span was checked, with the `0x003f31d8` body, oversized `0x003f3454` interval `[0x003f3454,0x003f34a0)`, and every byte outside the compound span unchanged.

## Functional and control evidence

The staged-body bytes were compared at their final guest addresses against original behavior: 20 directed cases for `0x003f3274`, 20 for each of the eight `0x003f32f4` family entries, and 20 each for `0x003f34a0` and `0x003f34cc`. All passed. The run detected 5/5 `0x003f3274` mutants, 8/8 per-entry sentinel mutants, and 2/2 `0x003f34a0`/`0x003f34cc` mutants. It also ran 20 original-versus-staged executions of the preserved `0x003f3454` body; memory/ABI/helper traces matched and the ARM veneer to Thumb transition was observed each time.

The staging utility is `tools/h18_003f_family_fit_staging.py`; its unit tests check the exact 11-slot set, IPS roundtrip and preservation of `0x003f3454`, and reject oversized/extra entries. `py_compile` and both unit tests passed.

## Limits and next step

These are offline Unicorn tests on the pinned image with synthetic memory fixtures. Existing scans do not establish real startup callers or initialization order. The preserved `0x003f3454` helper path is still modeled by the existing iterator harness; its real iterator behavior is not covered. No caller composition, production integration, or runtime/game scenario was run. The staged image is an experimental private artifact, not an integrated replacement or whole-game-equivalence claim.

Next, investigate the actual startup registration/caller path and compose the initializers in the order used by the game. Keep `0x003f3454` original until its candidate is reduced to the 76-byte interval or an alternate placement is independently proven. If runtime evidence is needed after offline interworking, differential, and caller gates pass, compare original and staged images through the private loopback GDB workflow.
