# Independent review: H2 Calc persistent offline sequences

## Review result

The persistent sequence runner uses separate original and patched ARM images,
creates fresh machines for each sequence, and retains each machine's guest work,
config, and global state across the sequence's consecutive callback ticks. The
final report's per-tick artifact hashes match the pinned original and reviewed
final-address patched image. Both seed passes cover 16 sequences and 52 ticks,
with expected state/action checks, full relevant memory/ABI/trace comparisons,
and a detected wrong-logical-map control.

The evidence supports callback state and memory behavior under the harness's
declared service responses. One lower-bound nuance remains: the sequence
decrements an option from one to zero, but does not issue another decrement
while the option is already zero. Treat that as reaching the lower boundary,
not as a direct assertion of the already-zero clamp branch.

## Artifact identity and persistence

- All frozen inputs in
  `build/agent-work/H2-semantic/h2-calc-offline-sequences-review/run-001/task.json`
  matched at review time.
- The final report at
  `build/agent-work/H2-semantic/h2-calc-offline-sequences/run-001/checks/final-5/report.json`
  has SHA-256 `3ceaad7345a0770c4626809dce0c083bea4e78adbda65812a3e4f8d60f4852cb`.
  It reports original image SHA-256
  `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` and
  patched image SHA-256
  `c9ebf62679043512c22c684b50f9e9cbf1fe824e016f119c2de4bddf664eb45d`.
- I independently hashed the emitted `patched-image.bin`; it matches the
  patched hash. The candidate object hash matches the report's
  `cd4c0eb1cbf21ac849f994370c0403fb2a6919b0263afd834db5928e768c60b8`.
  Every sequence tick records the original and patched hash in the correct
  fields, and all tick records match the report-level identities.
- In `run_sequence`, two `PersistentCalc` instances are constructed once per
  sequence from the same initial scenario and seed. `PersistentCalc` constructs
  a `CalcMachine` once; `tick` changes its scenario controls and calls `run`
  without reinitializing guest memory. `run` clears only per-tick registers,
  trace, and access sets, leaving work/config/global contents in the same
  Unicorn address space. Each later sequence constructs new machines, so prior
  sequence state does not leak into the next branch.

## Coverage and comparisons

The final report records seeds 7 and 20261024, with eight sequences per seed:
State-0 resource wait/ready/State-1 entry; State-1 no-event and logical
decrement/increment paths; four independent State-2 exit results; State-2 to
State-3 and State-3 readiness; and the separate State-1 logical transition to
State 3. The exit results `0..3` are tested as raw helper returns and are not
named confirm/cancel.

For every tick, the harness checks both sides against expected state, action
response and selected option/config effects, then compares original vs patched
return, PC, preserved `r4-r11`, SP, `d8-d15`, complete work bytes, config bytes,
work/config globals, and ordered consumed service traces. Faults, missing return
sentinels and ABI violations fail. The report is `passed=true`, with 16/16
sequences and 52/52 ticks passing.

The wrong-map control changes the patched-side logical response from decrement
query `(4,0)` to increment query `(3,0)`. The expected work value diverges:
original becomes zero and mutant becomes two. The comparator detects `work
differs`. This demonstrates sensitivity to that specific mapping error.

## Boundary note and scope limits

In `state1-logical-actions-and-clamps`, State 1 begins with option 0 equal to
one; query `(4,0)` decrements it to zero. The following increment path checks
nine to ten and ten remaining ten. Thus the output reaches the lower bound,
and the upper clamp is exercised at ten, but the repeated-decrement case
`0 -> 0` is not directly present in these sequences. Consider adding that
directed tick if the acceptance claim needs an explicit check of the
already-zero guard.

Logical `(id,mode)` responses are harness controls, not physical button events
or button-to-query mapping evidence. Cursor, touch, resource, script/task,
render, audio, animation, and state-decision helpers remain HLE boundaries; the
original mapper and encoder bodies execute from the pinned image. The harness
calls Calc repeatedly in its own callback machine, not through the title
initializer or scheduler. It does not establish title-scheduler behavior,
visible UI, physical input, persistence, profile behavior, Azahar/RSP behavior,
or whole-game equivalence. No State-2 result is semantically labeled; helper
domains and malformed cursor/work layouts remain unresolved.

This read-only review did not run a compiler, differential runner, emulator,
RSP, or input operation. Keep the result experimental and callback-scoped; use
separate caller, input, persistence, and runtime evidence before broader
promotion.
