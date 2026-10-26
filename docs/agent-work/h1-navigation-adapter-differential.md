# H1 navigation tail-adapter differential

> Correction, 2026-10-25: the differential verdict in this report is
> withdrawn. The shared AdapterMachine.run implementation patches the inline
> callback entry to the adapter shim unconditionally, including for the
> purported original mode, so these five cases and three controls never
> compared pinned inline ARM against the candidate. The source/object hashes,
> candidate design, static continuation analysis and exact historical command
> results remain recorded, but the outcome must not be cited as semantic
> differential evidence. The independent [corrected 258-case matrix review](h1-navigation-adapter-matrix-review.md)
> runs the original image untouched and patches only the candidate-side copy.

Task: `h1-navigation-adapter-differential`; owner: `h1_title_init`.

## Result

The isolated C++ reducer plus naked ARM tail shim matches the pinned inline
callback through `0x001E9E50` for the five directed cases in the fresh v2 run.
On gate failure it reaches `0x001EA62C`. On success it restores `r4` from the
captured work-pointer mailbox, sets `r8=0x0044E300` and `s17=1.0f`, then resumes
the original body at `0x001E9DE0`, executes the blend clamp and touch pointer
reload at `0x001E9E4C`, and stops before `0x001E9E50`. It does not return from the
interior window to the callback caller.

The candidate captures the title work pointer only after both readiness gates
pass, publishes that exact pointer via an explicit out pointer, and keeps using
it for timer/cursor/cache mutation. In the adversarial case the first trigger
hook changes global slot `0x0044E300` from `0x02000100` to `0x02000300` after
capture. Original and adapted paths still have `r4=0x02000100` at continuation,
while the later original `ldr r6,[r8]` correctly observes the changed pointer
in `r6=0x02000300`. The candidate mailbox remains `0x02000100`.

## Directed cases and controls

Fresh report cases:

- Script false and preview false both reach `0x001EA62C`; no timer/cursor/cache
  writes or input queries occur on these paths.
- Unchanged selection reaches `0x001E9E50` without an event.
- Changed selection increments cursor from 1 to 2, calls event `0x0100016C`
  while cache is still 0, stores the cache afterward, performs timer/blend
  changes, and reaches `0x001E9E50`.
- A second changed-selection case mutates the singleton after work-pointer
  capture and preserves original `r4` while verifying touch reload in `r6`.

All five cases agree on helper/timeline order, event observations, both work
blocks, global-slot value, `r4-r8`, `d8-d15` (including `s17`), `r6`, SP and
FPSCR; each case asserts that SP remains 8-byte aligned. The wrong-status-target control routes a false gate to the success body
and is rejected at the wrong stop. The missing-`s17` control changes `s17` and
blend memory. The pointer-reload control uses the mutated global for `r4` and
changes work effects. All three negative controls are rejected.

## Provenance and evidence

- Reference `extracted/exefs/code.bin`: SHA-256
  `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Candidate source SHA-256:
  `95bba0be4c59445eca0ca72c16c4b486c0737befd49ab0e60716a2c112d818ad`.
- Runner SHA-256:
  `758da5f72c950f38f09a145ed57432d0c3af9e044a0accafa60542cb565327de`.
- Focused test SHA-256:
  `c74e7b53fd998bfa54ec60e1354b64500b12206eb7e76151b9551c3d1b737e68`.
- ARM object and report hashes are recorded in the task handoff.
- Fresh v2 differential output:
  `build/agent-work/H1-semantic/h1-navigation-adapter-differential/sleep-20261025-nav-adapter-diff-v2/checks/final-differential/`.
- Fresh v2 focused unittest completed successfully; its report/object are
  retained under `checks/unittest-1792942945483669700/`.

Compiled: `passed`. Offline Unicorn ARM differential: `passed` for these
synthetic cases through the first touch pointer reload. Caller: `partial`; the
callback frame is represented at the inline-window entry. Runtime: `not_run`.

## Limits and next action

The harness supplies explicit readiness/input results and returns from the
event helper at its entry hook; real input hardware and event queue internals
are not executed. The original callback prologue/common epilogue, physical
touch dispatch, later callback behavior, production link/placement, runtime
normal object graphs, Azahar, saves, and whole-H1 behavior are outside scope.
Keep the original called helpers and continuation in place pending separate
caller/runtime and integration work. This experiment does not approve a
production patch.
