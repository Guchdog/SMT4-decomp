# H3 title state-7 caller composition

## Result

Implemented an offline Unicorn caller-composition runner for the pinned title
callback's state-7 path at `0x001EA32C`. With work byte `+0x7C` clear, the
original caller invokes `0x002A7604(0)`, then entry `0x0030A9A4`, writes state 8
to work `+0x9C`, and exits at `0x001EA62C`. The candidate run patches only the
caller BL at `0x001EA348` to the freshly compiled candidate in injected ARM
memory. The original run executes the pinned function body.

The harness supplies explicit deterministic stubs for `0x002A7604`,
`0x00202950`, and `0x002BF6D0`. It initializes manager/work memory with
nonzero bytes and the presentation point with signed halfwords `(-32768,
32767)`. Original and candidate agree on exit, return/fault status, state,
manager bytes, work bytes, dependency call order, and the contractual `r0/r1`
arguments. Full register traces are retained; `r2/r3` are caller-saved and
differ after candidate execution, so they are not part of the call-argument
equivalence assertion.

The nonzero `+0x7C` gate case confirms both executions skip dependency calls and
leave state 7 unchanged. The negative control changes the caller's `mov r0,#8`
to `mov r0,#7`; the post-call state assertion detects the incorrect transition.

## Evidence

- Compiled candidate: passed, ARMv6K hard-float flags, no relocations.
- Offline caller composition: passed, one state-7 success case and one gate
  skip case, with original and candidate execution.
- Negative control: passed; the wrong-next-state mutant is detected.
- ARM/Thumb: the pinned call is an ARM `BL` to aligned address `0x0030A9A4`
  (low bit clear). Candidate injected target is 4-byte aligned and reached via
  an ARM `BL` encoding. No emulator was used.
- Runtime: not run.

Fresh report and object:
`build/agent-work/H3-semantic/h3-title-caller-composition/run-001/checks/caller-composition-3/`.

## Limits and next action

The stubs define deterministic dependency returns; their internals are not
validated here. The check covers state-7's zero gate and nonzero skip gate only.
It does not cover state-8 polling, the downstream load result, save fixtures,
or runtime game behavior. An independent reviewer should inspect this runner,
verify its call-site patch and assertions, and rerun the report before promotion.
