# H1 navigation family audit (static)

Scope: title callback `0x001E989C`, menu navigation fields at `work+8` and
`work+0xC`, and trigger-query call sites. This is a static audit only: no
emulator, runtime input capture, production replacement, or ledger update.

## Entry and bounded code windows

- Constructor `0x001EB02C` registers callback `0x001E989C` (the callback
  argument points to the allocated title work block). Its constructor clears
  `work+8` and `work+0xC`; it sets `work+0x60` to 1. In state 2, `work+8` is
  set to 1 when `work+0x60` is nonzero, and may be set to 3 when `work+0x95`
  is nonzero. Thus the common initialization path selects index 1, but a
  nonzero `work+0x95` overrides it to 3. The constructor's initial zero alone
  is not the visible menu selection.
- State 5 begins at `0x001E9D08`. Navigation is gated by both
  `Script_IsReadyToAdvance()` (`bl 0x00289924`) and `Camp_IsPreviewReady()`
  (`bl 0x0025A2BC`); either false branches away before polling input.
- The direction/normalization sequence is bounded by `0x001E9D48..0x001E9DC4`.
  `work+8` is read at `0x001E9D6C`, decremented at `0x001E9D70` and written at
  `0x001E9D74`; then it is read/incremented/written at
  `0x001E9DA0..0x001E9DA8`; the inline normalization is exactly
  `0x001E9DAC..0x001E9DC0` (six ARM instructions, including store to `work+8`).
  It is followed by comparison with `work+0xC` and the conditional event at
  `0x001E9DC4..0x001E9DDC`.
- The six-instruction normalization has an existing isolated candidate and
  bounded differential harness: `title_cursor_candidate.cpp`,
  `tools/title_cursor_experiment.py`, and
  `tests/test_title_cursor_experiment.py`. Its evidence applies only to that
  arithmetic/store block, not to the full callback or trigger calls.

## Direction and wrap semantics from the caller window

| Address window | Observed instruction-level behavior | What can be said |
| --- | --- | --- |
| `0x001E9D48..0x001E9D74` | Query logical ID 5; if nonzero, decrement `work+8`. Otherwise query ID `0xE`; if nonzero, decrement once. | IDs 5 and `0xE` are aliases for the previous/decrement branch in this callback. Short-circuiting means at most one decrement from this pair per update. |
| `0x001E9D78..0x001E9DA8` | Query logical ID 6; if nonzero, increment `work+8`. Otherwise query ID `0xF`; if nonzero, increment once. | IDs 6 and `0xF` are aliases for the next/increment branch in this callback. At most one increment from this pair per update. |
| `0x001E9DAC..0x001E9DC0` | Add 4, use signed quotient correction, clear low two bits of the multiple, subtract, store. | This is signed remainder-by-4 behavior, not simply unsigned `& 3`. For valid indices, previous from 0 yields 3 and next from 3 yields 0. The isolated experiment checked provisional values `-1..4`, not every 32-bit input. |
| `0x001E9DC4..0x001E9DDC` | Compare normalized `work+8` against cached `work+0xC`; if different, request event `0x0100016C`, then copy the new index into `work+0xC`. | A net-zero move does not request this selection-change event. If previous and next both trigger in one tick, the sequence decrements then increments, so for valid indices the final cursor is unchanged. |

The index domain `{0,1,2,3}` is supported by the four touch-region registrations
and selection payload stride; the static listing does not show a general clamp
of arbitrary corrupted cursor values to `[0,3]`. The signed-remainder sequence
produces `[-3,3]` for arbitrary signed inputs; the wrap interpretation relies
on the normal invariant that the cursor starts valid and the input path changes
it by at most one per direction before normalization.

After this keyboard/controller sequence, touch handling at `0x001E9E4C..`
can directly assign a region index to `work+8`. State 1 or 2 selects the first
matching region and breaks; a separate scan for touch state 6 sets the cursor
and confirmation flag, and does not break (so multiple simultaneous matches
would leave the last matching index). This input path is distinct from the
signed-wrap block.

## Trigger IDs and confirmation

- `UiInput_Trigger` is called at `0x002B902C`, with immediate IDs 5, `0xE`, 6,
  and `0xF` loaded in `r0` at the four call sites above. The helper accepts IDs
  below `0x1F` and consults global input-state/mask tables. This establishes
  logical IDs and their use by this caller; it does **not** establish their
  physical keyboard/gamepad bindings.
- Later, at `0x001EA180..0x001EA190`, logical ID 0 is passed to
  `UiInput_Trigger2` (`0x002BFFBC`) as part of the confirm gate, after
  `UiMenu_CheckCursorSound(1)` and only when the touch-confirm flag is clear.
  A true result proceeds; false returns to the wait state. Touch confirmation
  reaches the same downstream dispatch using the flag instead.
- A successful confirmation requests event `0x0100016D` at `0x001EA1B4`; this
  is separate from the selection-change event `0x0100016C`.
- The title draw/update code uses the selected index to read help text from
  table `0x3A` at payload offset `0x16 + 0x56 * index` (`0x001EA12C..`). This
  corroborates four logical slots, but says nothing about physical bindings.

## Evidence classes and unresolved checks

**Observed statically:** the pinned `code.bin` has SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, matching
`config/game_info.json`; Capstone decodes the windows and call immediates above.
The constructor registers this callback. The source's readable callback is
inside `#if 0`; it is a transcription, not compiled semantic reconstruction.

**Inferred from the listing:** IDs 5/`0xE` mean previous and IDs 6/`0xF` mean
next specifically at these call sites; a valid cursor wraps 0↔3; event
`0x0100016C` tracks selection changes; ID 0 participates in confirmation.
These are control/data-flow interpretations of static machine code.

**Requires runtime evidence:** which physical keys, buttons, or analog inputs
produce those logical IDs; whether repeated/held input is filtered upstream;
actual input priority when opposing IDs are simultaneous; touch-state values
and simultaneous-touch behavior in Azahar; whether every destination visually
updates as expected. Do not label the physical mapping verified until captured
with controlled one-input-at-a-time traces.

## Verification boundaries

No full navigation-loop candidate is claimed here. The existing cursor pilot
does not include the four calls to `UiInput_Trigger`, the cached-index comparison,
touch handling, help-text refresh, or confirm dispatch. The isolated trigger-
result-to-cursor reducer and its explicit stub contract are reported below;
emulator testing is still required for physical bindings and integrated
presentation.

## Isolated family experiment (2026-10-24)

The bounded ARM harness can execute the pinned caller instructions with
`UiInput_Trigger` (`0x002B902C`) stubbed by explicit logical-ID responses. From
`0x001E9D48` through the stop at `0x001E9DE0`, Unicorn reached the stop with the
expected trigger-call sequence and without mapping game globals. The two
readiness gates were also executed separately from `0x001E9D0C`: false script
readiness skipped the preview gate; false preview readiness branched away
before trigger polling; both true reached `0x001E9D2C`, immediately before the
unrelated global/VFP animation setup.

Added isolated files:

- `experiments/semantic_equivalence/title_navigation_family_candidate.cpp`
  models gate bits, the two short-circuit alias pairs, signed wrap, selection
  cache, and the caller-visible selection-event request observation.
- `tools/title_navigation_family_experiment.py` pins the image hash, executes
  the original ARM windows with explicit stubs, compiles and validates the
  candidate, and stores reports only under ignored `build/` output.
- `tests/test_title_navigation_family_experiment.py` checks the evidence.

The focused test passes all three readiness-gate combinations, eleven named
edge cases, and an exhaustive 256-case sweep over valid cursor/cache values
`0..3` and all 16 trigger-result masks. It checks primary/alias short-circuit,
both direction branches, wrap at both ends, cache hits/misses, event ID and
the cursor/cache values visible at the event call. Candidate disassembly has no
`BL`/`BLX` helper calls; in particular it does not invoke or replace
`0x002C6C10` (the candidate spells out the recorded arithmetic).

The original `UiEvent_Request` target at `0x002B91C4` is an explicit boundary
stub: it records `r0` and `work+8`/`work+0xC` at the call, then returns. This
supports the call ID/order and cache-before/after observation only; it does
not model or claim the event queue's internal side effects. The candidate is
isolated and is not integrated into the reconstructed callback, production
source, progress ledger, ROM, or emulator. Physical controls, touch, the rest
of the callback, and whole-game behavior remain unverified.
