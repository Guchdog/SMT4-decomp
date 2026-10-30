# H2 logical-query caller composition absolute-gate correction: independent review

## Result

The correction addresses the prior comparator gap. The frozen runner now
requires clean execution and expected ABI preservation for each baseline and
candidate run before differential equality can pass. The refreshed report shows
43/43 scenarios and 172/172 per-execution gate sets true, required query entries
present, and a wrong-counter control detected as a work-state difference. The
final report hash matches the handoff and the self-hash field is gone. I found no
issue within this correction's bounded acceptance criteria.

## Gate and negative-test review

`compare_runs` checks both operands individually for `fault is None`,
`stopped is True`, and `preserved == expected_preserved` before comparing
`fault`, stop state, return value, PC, preserved state, work/config bytes, service
trace, wrapper-argument trace, and query-entry trace. The separate
`absolute_gates` summary records those same three conditions for each execution.
The report has 43 case rows, four named executions per row (`original`,
`calc_cpp`, `typed_queries_cpp`, `calc_and_queries_cpp`), and 172 gate objects.
All 172 have all three fields true; all 43 rows pass all three candidate-vs-
original comparisons.

The focused tests add controls for matching faulted operands and matching
incorrectly preserved ABI state. Since `compare_runs` gates the original and
candidate separately, equal bad states are rejected instead of being accepted
as differential matches. These tests are reported as passed by the implementation
handoff; I inspected their source but did not execute them in this read-only
review.

## Query reachability and mutation sensitivity

The report observes exactly the required unique entries:
`(0,3)`, `(0,4)`, `(0,12)`, `(0,13)`, `(1,0)`, `(1,1)`, and `(1,9)`. The
fallback-D row reaches mode-0 IDs 4 and 13; the fallback-C row reaches mode-0
IDs 3 and 12. The mode-1 ID-9, ID-0-positive, and ID-1-positive rows reach the
corresponding IDs. All 43 scenario rows include per-execution absolute gates.

The wrong-counter control reports `detected: true` and
`difference: "work differs"` in the fallback-D scenario. This makes the
observable that catches the mutant explicit and demonstrates sensitivity beyond
query-entry logging.

## Provenance and limits

All 15 input hashes declared in the review packet match. The report's pinned
image SHA is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
The final report SHA-256 is
`f7a2f37419620b26951f36cc7fa367d30031b0fdf43786b5e0b7a495ea40475f`, matching
the implementation handoff. No `report_sha256` self-digest field is present.
The candidate Calc/mode-0/mode-1 source hashes in the report match the frozen
sources.

This remains offline injected composition evidence. Counters are seeded directly
from requested logical outcomes; producer scheduling/freshness, physical input
meaning, selector-zero, event delivery, and a safe runtime injection seam are
not established. Other non-input Calc dependencies retain deterministic HLE,
mode-0 retains the original `0x002C6C10`, IPS/code-image integration is not
claimed, and runtime is `not_run`. Thus the corrected evidence supports the
reported caller slice, not whole-title or Azahar runtime equivalence.

## Review activity

Read-only checks: packet/input and report/handoff hash comparison; inspection of
the composition runner, focused tests, final report, and synchronized composition
note. No build, test, emulator, RSP, or guest-state command was run by this
reviewer.

Recommendation: accept the absolute-gate correction for independent-review
purposes. Keep producer and runtime acceptance open as stated in the report.
