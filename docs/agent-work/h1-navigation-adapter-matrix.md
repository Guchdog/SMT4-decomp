# H1 navigation adapter matrix

## Result

**Bounded synthetic caller-window differential passed.** A fresh private run
compared the pinned original inline window at `0x001E9D08` with the unchanged
compiled navigation adapter and tail shim. All 256 combinations of the four
trigger-response bits and cursor/cache values in `0..3` matched through the
first touch-pointer reload at `0x001E9E50`. The script-not-ready and
preview-not-ready cases both reached the original failure continuation at
`0x001EA62C` without trigger or event calls. The report has no positive-domain
first mismatch.

This is not a complete callback or runtime result. The readiness, trigger, and
event entry points return configured synthetic values; the active callback
frame, work blocks, and title pointer slot are synthetic. No physical input,
event-queue internals, renderer, production shim placement, Azahar, or game
runtime was used.

## Coverage and observations

The 4-bit mask order is trigger IDs `[5, 14, 6, 15]`; each bit controls that
logical trigger's configured nonzero/zero result. The test crosses all 16 masks
with each of 16 `(cursor, cached)` pairs in `[0,1,2,3]`, for 256 cases. It also
tests `(script, preview)=(0,1)` and `(1,0)` readiness. The former calls only
script readiness; the latter calls script then preview. Both skip all triggers
and events and branch to `0x001EA62C`.

For every row, the runner compares the original and adapter's final selection
and cache, ordered readiness/trigger/event observations and arguments, complete
synthetic work blocks, global slot value, callee-saved `r4-r11`, `d8-d15`, live
`s17`, `r6`, `sp`, and FPSCR. The report includes those register values and
hashes for the captured and alternate work ranges per row. Successful rows stop
at `0x001E9E50`, immediately after the original `ldr r6,[r8]` touch-pointer
reload; the adapter's captured pointer mailbox equals the original work
pointer. Gate-false rows stop at `0x001EA62C` and leave the seeded mailbox
unchanged.

On a cursor change, event `0x0100016C` is observed with the newly normalized
selection and old cache, before the cache store. If selection does not change,
no event is requested. The negative control recompiles a private mutant that
uses raw signed remainder instead of the candidate's ARM-compatible
normalization. At cursor `0`, cached `0`, only trigger `5` set, the original
produces selection/cache `3/3`; the mutant produces `0xFFFFFFFF/0xFFFFFFFF`,
and its event and memory projections differ. This confirms that the matrix
detects a normalization error.

## Reproducibility

- Pinned `code.bin` SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Unchanged candidate source SHA-256: `95bba0be4c59445eca0ca72c16c4b486c0737befd49ab0e60716a2c112d818ad`.
- Fresh candidate object SHA-256: `8fa198f8e19f23b18186d79e61cb6a7b848b83ba4f04aa647b28b3c468d8032f`.
- Differential report SHA-256: `b46eaeb959b46df8e21d5a81238f43e8a0347b70f1d2e015b6631d2e8385e8d0`.
- Runner and focused report-assertion test were run after the report was generated. Both passed; the assertions verify all 256 unique tuples, gate behavior, the negative control, bounded-memory equality, register coverage, and the success stop.
- Compiler use was sequential and limited to one candidate object and one private mutant object, under `results-v3`; no canonical build cache was used.

Evidence classification: compiled `passed`; private Unicorn ARM differential `partial` (all specified synthetic cases passed); caller `partial`; runtime `not_run`. The static/instrumented window does not run the function prologue/common epilogue or establish real callback placement, live runtime pointers, physical controls, event queue effects, later callback work, or whole-H1 equivalence.

The structured handoff and machine-readable report are in the packet's
`overnight-20261025-navigation-matrix` output directory.
