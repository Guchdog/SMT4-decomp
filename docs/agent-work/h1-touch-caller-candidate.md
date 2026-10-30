# H1 title touch caller candidate

This experiment reconstructs the bounded scan at `0x001E9E4C..0x001E9EB8` as
readable C++ and compares it with the pinned original ARM window. The candidate
calls the actual helper ABI at `0x0029D8FC` through a fixed-address
`s32 (*)(s16)` function pointer. The differential harness hooks only this
external helper entry and feeds response sequences indexed by signed handle and
call occurrence, so a handle may report different values on repeated probes or
on the later scan.

The pinned instruction window establishes a first-selection scan followed by a
full four-handle confirmation scan. A first response of 1 selects and exits the
first scan. For every other response, the original calls the helper a second
time for that handle and selects only if that second response is 2. The later
scan calls each handle once; every state-6 response replaces cursor `+8` and
sets confirmation byte `+0x63` to 1. No match preserves both prior fields.

The final focused report is
`build/agent-work/H1-semantic/h1-touch-caller-candidate/sleep-20261025-touch-candidate/checks/final/report.json`.
It records 7/7 directed differential cases and both deliberate wrong controls
detected. Covered cases include first and last priority, sticky confirmation,
no match, response changes between passes, and signed halfword handle edges.

Evidence is compiled `passed`, ARM differential `passed`, caller `partial`,
runtime `not_run`. The original is an inline callback window while the C++ is a
standalone function, so only the relevant state and ABI obligations are
compared; scratch/caller-saved registers are not asserted equal. The helper's
internal behavior, physical input bindings/hitboxes, actual Azahar runtime, and
whole-game behavior remain unvalidated. Review the candidate and its original
caller contract before any integration.
