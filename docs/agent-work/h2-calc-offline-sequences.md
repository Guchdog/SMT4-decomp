# H2 Calc persistent offline sequences

This task-local Unicorn runner builds the reviewed final-address Calc patch
once, fixes original and patched artifact hashes for each sequence, and keeps
each machine's work/global/config state across consecutive callback ticks.
Each sequence branch starts from a fresh clone. The original image hash is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; the
patched image hash is
`c9ebf62679043512c22c684b50f9e9cbf1fe824e016f119c2de4bddf664eb45d`.

The latest two-seed run passed 16 sequences and 54 ticks. Coverage includes:

- State 0 resource wait, ready initialization and State-1 entry;
- State-1 no-event, logical decrement `(4, 0)`, increment `(3, 0)`, and the
  zero/ten clamps, including a repeated `(4, 0)` decrement on a value already
  at zero;
- State-1 logical transition to State 2, pending script polling, and fresh
  branches for each script-exit decision value 0 through 3;
- State-2 result 0 to State 3, not-ready polling, and State-3 readiness to
  State 4; and the separate State-1 logical transition to State 3.

No exit decision is labeled confirm or cancel. At every tick the differential
checks return/fault/PC/SP, callee-saved `r4-r11` and `d8-d15`, complete work and
config bytes, global pointer/config bytes, and ordered service trace. Each side
also checks the expected state, logical service response and selected option
value where applicable. A negative control maps logical decrement `(4, 0)` to
increment `(3, 0)` on the patched side; it is detected as a work-memory
difference (original option becomes 0, mutant option becomes 2).

The lower-bound follow-up rerun is
`build/agent-work/H2-semantic/h2-calc-lower-clamp-sequence-fix/run-001/checks/final-rerun-20261026/report.json`
(SHA-256 `c716ce01551f3c2021a2a0e146c0aa284ee426c2f43adde674ab41bdb5c2738b`).
It records the patched image and IPS identities, object hash, all 16 sequences,
and per-tick work/config/global/ABI/trace evidence. The lower-bound sequence
contains both the first decrement-to-zero and a second decrement-at-zero tick;
both sides assert the option remains zero. The earlier sequence-run report
remains available at
`build/agent-work/H2-semantic/h2-calc-offline-sequences/run-001/checks/final-5/report.json`.

## Limits

Logical service return values are harness controls and establish no physical
button mapping. Cursor, touch, resource, script/task, rendering, audio,
animation and state-decision helpers remain HLE boundaries; the original
mapper and encoder bodies execute from the pinned image. This runner calls
Calc repeatedly in the callback harness, not through the title initializer or
task scheduler. It does not establish visible UI, persistence, profile
behavior, Azahar/RSP behavior, keyboard/mouse behavior, or whole-game
equivalence. Malformed cursor/work layouts and unresolved service domains
remain outside the tested support claim.
