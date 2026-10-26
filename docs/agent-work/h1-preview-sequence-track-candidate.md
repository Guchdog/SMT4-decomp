# H1 preview sequence/track selector candidate

This task reconstructs `0x002B1C8C` in the separate experimental source
`experiments/semantic_equivalence/h1_preview_sequence_track_candidate.cpp`.
The pinned body is 368 bytes at `[0x002B1C8C,0x002B1DFC)` and has SHA-256
`8097eb2315dd6b7f6dd72be434ee38223841c6470bfa3b923b362900572ba092`.
It has no direct callees. Its static H1 caller is the `mov r0,r4; bl 0x002B1C8C`
pair at `0x002BFC44/0x002BFC48` in the preview helper; the result is ignored.

The independent local contract is recorded in
`docs/function-records/0x002b1c8c.md`. In particular, this entry's sentinel
rules are distinct from sibling helpers: table-row next `-2` restarts at the
first row; table-row `-3` is an ordinary signed value; sequence-current `-1`
completes; sequence-next `-1` and `-3` complete; sequence-next `-2` falls
through as an unmatched signed lookup selector and clears the current handle.
The lookup descriptor's byte length at `+6` is divided by four for the number
of entries; its record-array pointer is at `+0x18`. Sequence selectors count
preceding table entries whose signed first halfword equals `-1`, then select
the record at the requested ordinal. No invalid-pointer/index behavior is
claimed.

The private differential runner is
`tools/h1_preview_sequence_track_experiment.py`. Run-01 used offline Unicorn
ARM11 MPCore to compare the pinned body and compiled ARMv6K C++ over 24
synthetic valid-memory cases. All 24 passed. The matrix includes early gates,
duration/progress boundary and signed cases, ordinary and sentinel row
transitions, sequence `-1/-2/-3` distinctions, selector hit/miss and count
boundaries, negative row/sequence indices, and sequence halfword-index wrap.
A mutated candidate reads duration from record `+0` instead of `+2`; the
duration-control case detects the mutation through `r0` and memory differences.
The comparator checks return `r0`, `r4-r11`, SP, stop/fault state, full mapped
data SHA-256, and caller-owned stack. This is partial offline differential
evidence, not whole-domain equivalence.

The focused test module is
`tests/test_h1_preview_sequence_track_experiment.py` (5 assertions). Inputs
declared by the task packet were frozen and matched their packet hashes during
the run. Only the five leased files were edited; the source ledger retains its
existing `matching` classification. No production implementation, shared
runner, full build, caller-level differential, or game runtime was changed or
run.

Remaining limits include valid-storage-only fixtures, unvalidated arbitrary
pointer/index domains and aliasing, absent live H1 object/scene lifecycle
evidence, and no dynamic execution of the encompassing preview caller. Next
step is independent review of the pinned lookup/count/sentinel contract and
candidate differential before any separate integration decision.
