# Coordinator review: `TitleConfig_Calc` candidate (`0x001EA928`)

## Review result

**Accept as a bounded experimental function reconstruction. Do not promote it
as an integrated H2 replacement yet.** The candidate preserves the observed
state dispatch, state-0 readiness/initialization order, state-1 row selection,
input query order, clamps, config encoding, changed-value effects, cursor
transitions, state-2 decision branches, state-3 readiness transition, and the
state-4 `-1` return. The corrected `work+0x154` script-result store and the TBB
payload stride `0x96` agree with the pinned listing and reviewed contract.

The handoff's hashes and ownership checks pass. Its two seeded differential
runs compare 64 cases each against the pinned original, covering the directed
state/branch matrix and initialized state-1 samples. The comparator includes
return/continuation state, callee-saved registers and VFP state, full work and
config ranges, and ordered modeled calls. Its config-byte corruption control
is detected. These results support callback-local behavior only under shared
deterministic service mocks; they do not validate those services or the title
caller.

## Limits before integration

Subsequent static review identified `IfTouch_Init`'s manager-state producer and
the `TOUCH CALC` callback. The H2 sentinel-to-manager relation, runtime order,
physical input meaning, and guest injection remain unresolved; see the
[manager-state audit](h2-input-manager-touch-state-producer-audit.md).

- Logical input, touch, cursor, script/task decisions, rendering, audio,
  animation, and state-decision helpers remain mocked boundaries. Three
  mappers and four encoders execute the pinned original. Keep this distinction
  in any ledger or production record.
- The `+0x1C..+0x22` touch-handle producer mismatch is unresolved. No physical
  button meaning or guest memory injection is established. The RSP return
  register seam at `0x001EABE0` remains a proposed runtime probe, not proven
  behavior.
- State-1 transitions and state-2 polling are separate callback cases, not a
  caller sequence. Changed-option exit, cancel/confirm semantics, re-entry,
  persistence, and runtime behavior remain unverified.
- The special-handle arithmetic uses signed C++ intermediates. The tested
  fixtures do not establish a range that rules out signed overflow. Before
  broadening its supported domain, either use explicit 32-bit wrapping
  arithmetic matching ARM or constrain and document the valid input range.

The function record and experiment report state these limits. Keep the
candidate experimental until a caller composition and the defined original vs
patched Azahar scenario are verified. The handoff's `passed` fields are not
whole-H2 acceptance.

## Evidence checked

- `build/agent-work/H2-semantic/h2-calc-candidate/run-001/handoff.json` and
  both referenced reports; `check-handoff` passed.
- `experiments/semantic_equivalence/h2_calc_candidate.cpp`, including state
  0/1/2/3/4 and `>=5` paths.
- `docs/agent-work/h2-calc-contract-review.md`,
  `docs/agent-work/h2-input-seam-review.md`, and
  `docs/function-records/0x001ea928.md`.

