# Handoff notes: H1 title fade front gate

Repair tasks `h1-title-fade-repair` and `h1-title-fade-s0-repair`, owner
`h1_title_fade` / `h1_menu_map`. Latest isolated run:
`build/agent-work/H1-semantic/h1-title-fade-s0-repair/sleep-20261025-fade-s0`.

## Result

Implemented an isolated readable C++ front gate for `0x00210030`, a separate
Unicorn-based original-versus-candidate experiment, and focused unittest. The
candidate reloads `object+8` at the three original load points, makes the two
observed hard-float calls, returns the machine `r0` on early exit, and forwards
the positive continuation's `r0`. It deliberately continues to use pinned
original bodies at `0x002872A4`, `0x0020FFA0`, and `0x00210074`.

The follow-up preserves incoming fade `s0` after the second helper and after the
third parent-pointer reload, before reading the final gate, matching original
`0x00210054..0x0021005C`. The runner now compares returned `s0` as well as `r0`.
Two explicit external-entry seam cases overwrite `s0` with `0x41200000` at
`0x0020FFA0`; both the final-gate early return and positive continuation restore
the original `0x3F400000` fade bits in original and candidate.

The original entry takes a pointer in `r0`, a float in `s0`, saves `r4/lr` and
`d8`, and preserves the incoming float across the first two direct calls. Each
direct target is a signed-zero gate with a positive fallthrough into a larger
body. The final gate also falls through to a neighboring body. The deeper
second-body table/callback path and final continuation graph remain uncovered.
There is no observed real callback binding or runtime-normal object fixture.

## Checks

- `python tools/h1_title_fade_experiment.py --code build/azahar-validation/exefs/code.bin --output build/agent-work/H1-semantic/h1-title-fade-s0-repair/sleep-20261025-fade-s0/checks/differential/report.json` — exit 0; 15 directed ARM cases, parent-pointer reload seams, two second-helper `s0` clobber paths, `r0`/`s0` comparisons, and the wrong-boundary negative control passed.
- `python -m unittest tests.test_h1_title_fade_experiment -v` — exit 0.

Reports: `checks/differential/report.json` and `checks/unittest/report.json`;
objects: corresponding `h1_title_fade_candidate.o` files.
The adversarial case mutates parent `+8` to `0x02000600` at the first callback,
then to `0x02000700` at the second-helper seam. The second helper and final
continuation receive the reloaded child pointers. The new `s0` seam injects a
different VFP value at second-helper entry and asserts original/candidate return
with the input fade on both final-gate paths. Reports record exact return-r0/s0
values, source/object hashes, compiler flags, the wrong-boundary control, and
partial body limits. Current source SHA-256 is
`e5c05eecd57c7b965ae4f2406d4770b32eb68d50a69c643eaa315104eaf717d6`; object
SHA-256 is `258db8e94623f5c41e68704836ddf9901da626ac43ac6150011b0d8b6b2df01a`;
differential report SHA-256 is
`3cc1ab7ae04b182fa972dc505ab26eb4c4bb53562914a9995dae471050a4fdd8`. The
original image hash is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

## Review and next action

Treat this as a bounded front-gate reconstruction, not a complete promotion
candidate. The `s0` review finding is covered for an explicit second-helper
entry clobber on early and positive final-gate paths; the deeper positive
`0x0020FFA0` callback body remains untested, as do the deeper
`0x00210074` path, real caller consumption of `r0`/`s0`, runtime object graphs,
and emulator behavior. No caller integration, production edit, or ledger
change was performed here.
