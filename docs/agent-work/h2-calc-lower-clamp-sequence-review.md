# Independent review: H2 Calc lower-clamp sequence

## Review result

The revised State-1 sequence now explicitly performs a second logical
`(4,0)` decrement after option 0 has reached zero. The same `PersistentCalc`
instance is reused for both ticks, and the per-tick expected-value assertion
requires option 0 to remain zero on both original and patched sides. The
increment-nine-to-ten and increment-at-ten cases remain. The two-seed final
report passes 16/16 sequences and 54/54 ticks, and the wrong logical-map control
is still detected.

## Frozen identities and sequence evidence

- All frozen input hashes in
  `build/agent-work/H2-semantic/h2-calc-lower-clamp-sequence-review/run-001/task.json`
  matched at review time.
- The frozen final report
  `build/agent-work/H2-semantic/h2-calc-lower-clamp-sequence-fix/run-001/checks/final/report.json`
  has SHA-256 `0700de32c1171f458d0034e51b233384bf29bea3e558668961434f85d848a2e8`.
  It reports original image hash
  `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` and
  patched image hash
  `c9ebf62679043512c22c684b50f9e9cbf1fe824e016f119c2de4bddf664eb45d`.
  I independently hashed the emitted `patched-image.bin`; it matches the
  patched image identity. Per-tick report fields consistently identify the
  original and patched image respectively.
- The State-1 action sequence has five ordered ticks: no event, decrement from
  one to zero, decrement again at zero, increment from nine to ten, and
  increment again at ten. The report shows original and patched option tuples
  `(0,9,seed_row2)` after each decrement tick and `(0,10,seed_row2)` after both
  increment ticks, for seeds 7 and 20261024. State remains 1 at every tick.
- `run_sequence` constructs one original and one patched machine per sequence;
  `PersistentCalc.tick` reuses those machines and does not reinitialize guest
  work/config/global state. Therefore the second decrement consumes the zero
  stored by the preceding tick, rather than a newly seeded value. A fresh
  sequence receives new machines.

## Regression sensitivity and negative control

The focused sequence test asserts both decrement steps use `(4,0)` and both
expect option 0 to be zero. A separate assertion test feeds `_assert_tick` the
wrong values `0xFFFFFFFF` and `1` and confirms each fails the expected-zero
condition. This checks the expectation validator's sensitivity; it is not a
second compiled mutant with the lower clamp removed. The actual original vs
patched report exercises the repeated-zero input on both code images.

The increment boundary is preserved: the sequence reaches ten from nine and
then issues another `(3,0)` increment while already at ten, with expected
option 1 equal to ten. The wrong-map control changes patched logical decrement
query `(4,0)` to increment query `(3,0)`; it remains detected as a full-work
difference, with original option 0 equal to zero and mutant value equal to two.

## Remaining limits

Logical `(id,mode)` service responses are harness controls and establish no
physical input mapping. Cursor, touch, resource, script/task, rendering, audio,
animation and state-decision helpers remain HLE boundaries; original mapper
and encoder bodies run from the pinned image. The Calc callback is run
persistent in its own offline harness, not through the title initializer or
scheduler. This evidence does not establish visible UI, persistence/profile
behavior, Azahar/RSP, keyboard/mouse behavior, or whole-game equivalence. State-2
results are not assigned confirm/cancel meanings; helper domains and malformed
cursor/work layouts remain unresolved. No emulator, RSP, or input action was
used in this review.

The result supports the lower and upper option-boundary behavior within the
modeled logical-service sequence. Broader caller, physical-input, persistence,
and runtime evidence is still required before promotion beyond the bounded
offline callback claim. This review inspected frozen files and outputs only; it
did not rerun compilation or the differential experiment.
