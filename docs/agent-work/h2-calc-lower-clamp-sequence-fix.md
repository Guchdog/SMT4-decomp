# H2 Calc persistent lower-clamp check

Extended the persistent State-1 logical action sequence with a second
`(4,0)` decrement response after option 0 is already zero. Both original and
patched sides assert the value remains 0 on each decrement tick, and the
per-tick comparator continues checking full work/config bytes and consumed
service traces. The existing increment-at-10 clamp case remains in the same
sequence.

A focused regression calls the sequence's work-value assertion with the
selected option set to `0xFFFFFFFF` (underflow representation) and `1`; both
must fail the expected-zero assertion.

Final fresh evidence is under
`build/agent-work/H2-semantic/h2-calc-lower-clamp-sequence-fix/run-001/checks/final-rerun-20261026/`
(report SHA-256 `c716ce01551f3c2021a2a0e146c0aa284ee426c2f43adde674ab41bdb5c2738b`).
The two-seed run and detailed limits are in its `report.json` and the structured
handoff beside the task packet. This remains offline callback evidence under
logical-service controls and does not establish physical input mapping or
whole-title/runtime behavior.
