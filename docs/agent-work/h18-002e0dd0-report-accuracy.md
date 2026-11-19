# H18 0x002e0dd0 report-accuracy update

Owner: `luna_probe_review`. Fixed only the leased report metadata, regression test, and historical review annotation. No candidate C++ or board edits; no emulator.

## Stop metadata correction

The ignored-result caller loop already passed the true stop tuple `(0x003bbe18,)` to both original and candidate execution; only the serialized `stop` field incorrectly substituted synthetic `RETURN` due a mismatched caller-name comparison. It now serializes the loop's actual `stop` value. The focused test requires the ignored-result caller to report `0x3bbe18` and the two `ui_func_003bbfb0` caller paths to report `0x1001000` (their synthetic return LR).

The old review's `0x81` conclusion remains in the historical body but a new top note explicitly marks it refuted and links [the corrected independent caller review](h18-002e0dd0-caller-correction-review.md). The preserved historical text is not silently rewritten.

## Validation

TDD red run: before the runner correction, `python -m unittest tests.test_h18_002e0dd0_experiment -v` failed because the ignored-result stop field was `0x1001000`, expected `0x3bbe18`.

After the correction:

- `python -m py_compile tools/h18_002e0dd0_experiment.py tests/test_h18_002e0dd0_experiment.py` — exit 0.
- `python -m unittest tests.test_h18_002e0dd0_experiment -v` — exit 0, 1 focused test passed.
- `python tools/h18_002e0dd0_experiment.py --image extracted/exefs/code.bin --output build/agent-work/batch-h18-001/h18-002e0dd0-report-accuracy/run-001/checks/stop-metadata-seed-20261118 --seed 20261118 --samples 8` — exit 0; 33 direct cases, 3 caller compositions, and all 3 negative controls passed. Serialized caller stop fields are now `0x3bbe18`, `0x1001000`, `0x1001000`.

This is offline Unicorn differential/caller evidence with modeled dependencies, not runtime emulator evidence or whole-game equivalence.
