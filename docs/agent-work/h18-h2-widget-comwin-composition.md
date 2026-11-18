# H18 widget helper / ComWin_Calc composition

## Independent bounded review

The existing `h1_preview_helper_candidate.cpp` was compiled unchanged and linked at private VMA `0x01000000`. The runner also compiles the existing experimental `h18_h2_comwin_calc.cpp` unchanged. It runs four combinations from the actual ComWin callback entry `0x0011b094`: original callback/original widget, original callback/C++ widget, C++ callback/original widget, and both C++ candidates. Each combination uses the same pinned image and fixture. The harness intercepts the original widget address only to redirect to the linked candidate; the candidate's five dependency calls resolve to dedicated named stubs in that private image.

Thirteen scenarios cover ComWin states 0, 1, 2, 3, 4 and 5, including state-1/state-4 readiness transitions, state-2's ignored widget result, common-tail ready/not-ready returns, the signed early gate, both interpolation direction choices, and a sequence branch that calls the animation setter. All four variants match for return, SP, callee-saved registers, ComWin state/counter, widget bytes, and the normalized external-helper trace. The interpolation case reaches `0x002c615c` twice plus all three tail helpers; the sequence case reaches `0x002bdac0` plus all three tails. Thus all five external helpers are observed in at least one fixture.

Two compiled negative controls are detected: inverting the widget's completion conjunction changes the state-1 transition, and inverting the ComWin state-1 gate also changes its resulting state. The focused unittest checks every variant equality, expected branch traces and both controls.

## Five explicit external-helper models

The runner preserves the assumptions recorded by the existing helper contract:

| Callee | Model used | Why the observed arguments are normalized this way |
|---|---|---|
| `0x002bdac0` | Record `(object, animation, frame)`, return zero, no memory writes | Return is ignored; three argument registers are compared. |
| `0x002c615c` | Record `(signed delta, duration)`, return truncating signed `delta/duration`, or zero for zero duration | The contract identifies two inputs and the return is used in fixed-point updates. Tested durations are positive and small. |
| `0x002b1fc0` | Record object pointer, return zero, no writes | One effective object argument is supported by the helper contract; its pinned prologue immediately overwrites `r1` from `[r0+0x87]`. |
| `0x002b1dfc` | Record object pointer, return zero, no writes | One effective object argument; prologue overwrites `r1` from `[r0+0x88]`. |
| `0x002b1c8c` | Record object pointer, return zero, no writes | One effective object argument; prologue overwrites `r1` from `[r0+0x89]`. |

For the three void tail helpers, only their effective `r0` input is in the trace. The original call-site's caller-saved `r1-r3` values are not treated as extra arguments. The helper contract's call table specifies `r0=object`; the callees' own decoded prologues corroborate that these are object-only entry points. Interpolation retains its two defined arguments/result; animation retains all three arguments.

These are controlled dependency models, not reconstructions of the five callees. In particular, no side effects from their implementations are included. Equality across the four variants therefore applies only to these fixtures and these explicit models. The row and sequence fixtures are valid, aligned, and in bounds; no natural ComWin object lifecycle, real task-scheduler invocation, runtime UI, or helper callback behavior is established. The H1 candidate remains experimental and is not promoted by this composition.
