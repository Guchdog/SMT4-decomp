# Independent review: H2 offline caller composition

## Review result

The runner gives useful, reproducible evidence that the initializer candidate
composes with the pinned State-9/10 caller for its three declared scenarios.
The single patched entry point, transition sequence, task registration tuple,
task-active schedule, state/config memory comparisons, ABI preservation checks,
and wrong-callback negative control are all visible in the implementation and
the frozen report. I found one caller-boundary gap that should be resolved
before treating the result as a full caller-equivalence pass: the raw evidence
contains a differing argument to an initializer HLE call, but the comparator
discards it and the stub does not validate it.

## Evidence checked

- Every frozen `input_sha256` entry in
  `build/agent-work/H2-semantic/h2-offline-caller-composition-review/run-001/task.json`
  matched at review time. The reviewed report is
  `build/agent-work/H2-semantic/h2-offline-caller-composition/run-001/checks/final-5/report.json`
  (SHA-256 `35bd1c20d24fcaf0324de684f90119bc9bfa111f9c543a55b1facfc7f0882950`).
- `CallerMachine.__init__` writes the compiled candidate into its private
  injection region and changes only the instruction at `0x002F4CA0` to branch
  to that region. Both machines otherwise run the pinned image. The State-9/10
  callback and readiness body at `0x002FC0EC` are original code on both sides.
- The report records three passing cases: baseline config, a distinct 8-byte
  config, and `flag_7c=1`. For both transition cases the phase states are
  `[10, 10, 5]`; the gate stays at State 9 and records no initializer, allocator,
  or process-factory event.
- The Calc factory tuple checks the primary callback, secondary callback, and
  `TitleConfigWork` stack context. The Draw tuple checks its callback, reserved
  words, and Calc task token. The readiness HLE is queried for that exact token
  with active results `[1, 0]`, exercising pending then reset. Work/config bytes,
  global pointers, return/PC/SP, `r4-r11`, and `d8-d15` are compared at phase
  boundaries; reset field values and deterministic touch handles are separately
  asserted.
- The negative control changes the candidate Calc callback address from
  `0x001EA928` to `0x001EA92C`. Both the expected tuple validator and the
  original-versus-mutant tuple comparison detect it.

## Finding: observed initializer HLE argument is not checked

At the `0x002B8B78` boundary reached from call site `0x002F4DF0`, the raw report
records `r0-r3` as
`[0x99, 0x02002150, 0, 1]` for the original and
`[0x99, 0x002B8B78, 0, 1]` for the candidate. Stack words and `s0-s3` match.
The current stub returns zero without checking its inputs. `_phase_projection`
compares only `r0` at generic boundaries, so this difference does not fail the
differential. This may be a caller-saved scratch value, but the available
evidence does not establish that `r1` is unused by the real helper. Preserve
the result as a bounded memory/state composition pass and either establish the
helper's argument contract or add a justified explicit allowance/assertion
before claiming this boundary equivalent.

Relatedly, `validate_registration` labels a reset helper address-sequence
mismatch as an “order/arguments” mismatch, while it checks only the ordered
callee addresses. The State-10 reset trace currently has matching captured
`r0-r3`, stack words, and `s0-s3` on both sides, but these values are not
asserted by that validator. The report should not be read as proving arbitrary
reset-helper arguments equivalent. This is a validator coverage gap, not an
observed reset-argument mismatch.

## Scope and promotion advice

Allocator, process factory, task-active lookup, sprite/resource/cursor setup,
sound/message, transition, touch registration, cursor mode, environment load,
and model visibility are explicit HLEs. Their real internals are not validated.
The runner proves callback registration and Calc handle linkage only; it does
not schedule or execute either Calc callback. In particular, it does not prove
Calc editing behavior, State-1 input/cursor behavior, persistence or save
behavior, profile behavior, Azahar/RSP behavior, or whole-game equivalence. The
two config blocks exercise initializer mapping/copy composition only; they do
not validate mapper candidates.

Keep this evidence experimental and caller-scoped. It supports the initializer's
observed state/memory transition under the modeled HLEs, with the noted helper
argument unresolved. It is not enough for production promotion or a Calc,
persistence, or UI claim. No build, test rerun, emulator, RSP, or input operation
was performed during this independent review.
