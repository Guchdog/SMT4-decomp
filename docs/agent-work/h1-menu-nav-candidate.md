# H1 navigation caller candidate — handoff summary

Task `h1-menu-nav-candidate`, owner `h1_menu_map`. This is ready for independent
review as a bounded candidate; it is not approved for production integration.

## Result and scope

Added an editable C++ candidate for the state-5 readiness and keyboard/controller
selection caller window. The candidate calls the actual pinned readiness,
`UiInput_Trigger`, and `UiEvent_Request` helper addresses using explicit ABI
types; only those external helper entry PCs are hooked in the harness. Original
ARM execution begins at `0x001E9D08` and stops at `0x001EA62C` when a readiness
gate fails or `0x001E9DE0` after both gates pass. Candidate execution returns to
an isolated sentinel. It does not execute blend, touch, help-text, fade, or
dispatch behavior.

Behavioral comparison passed for three readiness branches, ten directed
navigation/cache/event cases, and all 256 combinations in cursor/cache domain
0..3 × 16 trigger response masks. The harness compared helper order and IDs,
event ID/call-time cursor and cache values, full `0xA0` work bytes, SP, FPSCR,
and callee-saved GP/VFP registers. A wrong signed `% 4` control was rejected at
`-1`: it returns `0xFFFFFFFF` where the original word sequence returns 3.

Raw architectural state is partial. At the original continuation, `r8` is
`0x0044E300`; the candidate preserves the seeded incoming `0x88888888`. The
original also changes `d8` from `0x1122334400000008` to
`0x3F80000000000008` by leaving `s17=1.0`; a standalone AAPCS C++ function
preserves `d8`. `r4` agrees because both begin with the work pointer. Do not
claim this function can be inserted at the interior PC as a raw replacement;
the callback-context adapter must account for `r8`/`s17` liveness.

## Evidence and checks

- Static: pinned original image hash and exact state-5/helper entry addresses
  verified by the runner. The corresponding call/data-flow interpretation and
  limits are recorded in [the function record](../function-records/0x001e9d48.md).
- Compiled: ARMv6K candidate object built in a private task output; both symbols
  are relocation-free. Literal pool is exactly 16 bytes at `0x010000E8`, with
  each word referenced by a PC-relative load and unconditional branch
  `0x010000E4 -> 0x0100009C` skipping it. The validator checks contiguous decode
  through the branch and rejects branch targets into the pool.
- ARM differential: behavioral comparisons passed for the finite tested domain;
  architectural continuation state remains partial as stated above. External
  helper outcomes are test-hooked; event queue internals are not modeled.
- Caller: partial, bounded callback window only. No physical input mapping or
  downstream caller-visible presentation/dispatch behavior was exercised.
- Runtime: not run; no emulator/Azahar interaction.

Commands (each exited 0):

1. `python tools/h1_navigation_caller_experiment.py --output build/agent-work/H1-semantic/h1-menu-nav-candidate/sleep-20261025-nav-candidate/checks/final-candidate-run-2`
2. `python -m unittest tests.test_h1_navigation_caller_experiment -v`

The focused unit suite has three passing tests. During development, a validator
initially treated LLVM's function-adjacent pool as instructions, and Unicorn
VFP execution initially faulted until CPACR/FPEXC were initialized. Both were
resolved; the final runner pins and validates the literal-pool boundary and
enables the configured ARM11 VFP state. Earlier failed exploratory runs are not
used as final evidence.

## Artifacts

- Candidate: `experiments/semantic_equivalence/h1_navigation_caller_candidate.cpp`
- Isolated runner: `tools/h1_navigation_caller_experiment.py`
- Focused test: `tests/test_h1_navigation_caller_experiment.py`
- Per-function record: `docs/function-records/0x001e9d48.md`
- Detailed machine report: `build/agent-work/H1-semantic/h1-menu-nav-candidate/sleep-20261025-nav-candidate/checks/final-candidate-run-2/report.json`
- Structured handoff: `build/agent-work/H1-semantic/h1-menu-nav-candidate/sleep-20261025-nav-candidate/handoff.json`

The detailed report includes the pinned image, source/object/function hashes,
all readiness and directed observations, all 256 compact per-case observations,
work-block changed offsets, helper/event call records, and explicit state deltas.

## Reviewer action

Independently inspect the inline ARM window, ABI types, field offsets, trigger
short circuits, event-before-cache order, literal-pool proof and the stated
R8/S17 mismatch. Then ask the integrator to define a callback-context adapter
before promotion. Do not treat the finite harness run as physical-input,
renderer, emulator or whole-game equivalence.
