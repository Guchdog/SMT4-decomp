# H2 TitleConfig_Draw signedness correction

## Change

The TBB guard in `candidate_002cafd0` now compares the absolute index as `u32`, matching the original ARM `cmp r7,#3; bhs` condition. The differential runner adds two one-row guard fixtures with absolute indices `-1` and `3`. Their option lookups are backed by explicitly seeded words at `work+0x24` and `work+0x34`, both inside the initialized `0x158`-byte work object. The runner verifies the expected no-TBB behavior in both original and candidate, not just equality: each case must have no subtable/payload call and no formatter call. The case report records these observations.

## Validation

- `python -m py_compile tools/h2_draw_experiment.py tests/test_h2_draw_experiment.py` — exit 0.
- `python -m unittest tests.test_h2_draw_experiment -v` — exit 0, four tests passed.
- `python tools/h2_draw_experiment.py --output build/agent-work/H2-semantic/h2-draw-candidate-signedness-fix/run-001/checks/final-v2` — exit 0; compiled candidate and wrong-stride negative control, 46/46 differential cases passed, no counterexample, negative control detected as a trace difference.

Report: `build/agent-work/H2-semantic/h2-draw-candidate-signedness-fix/run-001/checks/final-v2/report.json` (SHA-256 `40106e77c35d57230573b787e80f6cac089c814e5493f62d324e1cda96e2471a`). Reference: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Candidate source: `bef32aa76f533cb15d1372b9e4eace6b7a2c4dbfd7d95bd57877ab0f130fcc6e`. Runner: `43391efdd5efa790de0fd82d14ab32db317eb58ff7d06637eee2211a7a88c402`. ARM object: `000b4855164bfa7c8775ab32a4a02b936e9c878435c29f0ab8d95ebcffc9b9c2`.

## Evidence boundary

The new fixtures establish that the original and candidate both skip the TBB path for those controlled absolute indices while performing safe in-object option-word reads. They do not show that a negative cursor offset or index 3 can occur from the initialized title caller. Cursor, TBB, layout, format/font, panel/sprite, renderer, and touch behavior remain deterministic mocks; caller, runtime, visible UI meaning, persistence, scheduler/calc interaction, and whole-game equivalence remain untested. No production integration or emulator/input control was performed.

## Next action

Independent review the corrected source and explicit guard assertions. If accepted, continue with a real initialized-caller draw-task comparison before considering production promotion.
