# Independent review: H1 navigation continuation adapter

> Correction, 2026-10-25: I withdraw this document's original differential
> verdict. AdapterMachine.run in the reviewed runner always patches
> CALLBACK_START to the candidate shim, even for its "original" mode. The five
> reported comparisons therefore did not compare the pinned inline ARM window
> against the candidate; the review missed that patch. The pinned disassembly
> and static ABI/control-flow observations below remain useful, but the earlier
> differential and its negative-control comparisons are not valid semantic
> evidence. The later [corrected 258-case matrix review](h1-navigation-adapter-matrix-review.md)
> audits a runner that leaves the original image untouched and patches only the
> candidate-side copy.

## Review result

**Partial, no bounded-path discrepancy found.** Static inspection of the pinned
callback, candidate source/object, runner assertions, and frozen v2 report
supports the producer's five reported synthetic cases and three rejected
controls through the first touch-pointer reload at `0x001E9E50`. I did not
compile, execute, or rerun the experiment; the differential outcomes below are
producer-reported evidence. The result supports this bounded continuation
adapter design, not production placement or H1/runtime equivalence.

The packet's 18 frozen input hashes matched. Reference image SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Reviewed
candidate source SHA-256 is
`95bba0be4c59445eca0ca72c16c4b486c0737befd49ab0e60716a2c112d818ad`, candidate
object SHA-256 is
`8fa198f8e19f23b18186d79e61cb6a7b848b83ba4f04aa647b28b3c468d8032f`, and
frozen final differential report SHA-256 is
`561003ab35f2f7623a150cb12f42d90eddd8e2842824cac192c8b16bd31b15dc`.
The reviewed runner hash is
`758da5f72c950f38f09a145ed57432d0c3af9e044a0accafa60542cb565327de`, test hash
is `c74e7b53fd998bfa54ec60e1354b64500b12206eb7e76151b9551c3d1b737e68`, and
producer handoff hash is
`86f66417789f628d2aea9d20786ee51b5ce4d19d7571e464ec3a3fd5383f1a2f`.

## Pinned continuation contract

I independently decoded the pinned original at `0x001E989C`, the gate window,
both continuations, and the callback epilogue. The callback prologue saves
`r4-r8,lr`, saves `d8`, and reserves `0x20` bytes; the later common epilogue
releases that space and restores `d8` and `r4-r8,pc`. The state-5 inline window
is reached with that frame still active.

- Script readiness is called at `0x001E9D0C`; zero branches at
  `0x001E9D18` to `0x001EA62C`.
- Preview readiness is called only after script readiness succeeds at
  `0x001E9D1C`; zero branches at `0x001E9D28` to the same
  `0x001EA62C` continuation.
- Only after both checks pass does the original set `r8=0x0044E300`, set
  `s17=1.0f`, and sample the work pointer into `r4` at `0x001E9D38`.
- The reducer ends by falling through to `0x001E9DE0`. In that tail, `s17` is
  used by the blend clamp at `0x001E9E30`; `r8` is dereferenced at
  `0x001E9E4C`. Thus on successful resume the necessary live values are
  `r4=captured work pointer`, `r8=0x0044E300`, and `s17=0x3F800000`.
- At the failure continuation, the shim must retain inline-entry `r4/r8/d8`
  values until `0x001EA62C`; its first instructions reload `r6` and `r4`. The
  frozen report seeds `r4=r5=0x02000100`, `r8=0xA5080808`, and
  `s17=0x11223344`, and reports those preserved at the stop.

The object-level shim inspection agrees with its source: success restores
`r4` from the private captured-pointer mailbox, loads the singleton slot into
`r8`, sets `s17` from `0x3F800000`, then branches to `0x001E9DE0`. Failure
branches directly to `0x001EA62C` without intentionally changing `r4/r8/s17`.
The compiled shim has no relocations; its pool resolves to mailbox
`0x01003F00`, candidate `0x01002000`, slot `0x0044E300`, and the two original
continuations. Candidate and shim are still private test placements, not a
production link/cave.

## Candidate/runner audit and producer-reported cases

The C++ candidate uses no-argument `s32` readiness calls, `s32(u32)` trigger
queries, and `void(u32)` event request, consistent with the original call
sites. It captures the post-gate singleton pointer through the explicit
out-parameter before timer/input work. The naked shim calls the ordinary ABI
candidate with the mailbox address and does not adjust the enclosing frame;
the object prologue is balanced and the report asserts the SP is equal and
8-byte aligned at the stops. Success deliberately changes only the needed
`r4/r8/s17` live continuation state after the candidate returns.

The report says all five cases had matching helper/timeline order, event
observation, both bounded work blocks and global slot, callee-saved `r4-r11`,
`d8-d15`, `r6`, SP, FPSCR, and expected stop. The case details are:

| Producer case | Original/adapter stop | Observed contract |
| --- | --- | --- |
| Script false | `0x001EA62C` | Only script-ready call returns false; no reducer/timer/input/event work. Entry `r4/r8/s17` retained. |
| Preview false | `0x001EA62C` | Script true then preview false; no reducer/input/event work. Entry live values retained. |
| Unchanged selection | `0x001E9E50` | Ready calls, triggers 5/14/6/15 all false, no event; success live registers restored. |
| Changed selection and blend clamp | `0x001E9E50` | Trigger 6 advances selection 1→2; event `0x0100016C` observes selection 2/cache 0 before cache store; blend/timer tail runs. |
| Captured pointer under mutation | `0x001E9E50` | First trigger changes slot to `0x02000300`; reducer `r4` remains captured `0x02000100`; later `[r8]` reload yields `r6=0x02000300`. |

The runner's configured helper hooks provide ready/trigger return values and
return from event request at its entry. It records call order/arguments and
injects the pointer mutation after capture. The original callback prologue and
common epilogue are not executed; the entry frame is initialized synthetically.
The runner stops immediately after `ldr r6,[r8]` at `0x001E9E4C`, before physical
touch dispatch. Its equality check covers the stated work buffers and slot,
not arbitrary process memory.

The three negative controls are targeted and rejected in the report:

- Wrong status target sends a failed readiness result to the success tail;
  it stops at `0x001E9E50` instead of `0x001EA62C` and changes live state/work.
- Missing `s17` restoration changes `s17` and blend memory despite reaching the
  same stop.
- Reloading the mutable global instead of using the captured pointer changes
  `r4` and work effects under the adversarial slot mutation.

The candidate's pointer publication addresses the unresolved mutation seam in
the preceding feasibility note. No discrepancy appeared in the reviewed
source/object/report for this exact test arrangement.

## Evidence classification and limits

- Static original branch, frame, and register contract: independently checked
  against the pinned image and decoded object.
- Candidate compilation and differential: the object/report/test assertions
  were inspected; compilation and Unicorn outcomes are producer-reported and
  were not rerun by this reviewer.
- Caller evidence: partial, since the frame is represented at the inline
  window and only the bounded continuation through `0x001E9E50` is covered.
- Runtime: not run. Real readiness/input internals, physical input, event queue
  effects, production placement/linking, Azahar, later callback behavior, and
  whole-H1 equivalence are not established.

Recommendation: accept this as reviewed bounded adapter evidence, retain the
original dependencies and runtime limitations, and require the integrator to
own any placement/integration and caller/runtime comparison as a separate
task. Machine-readable producer report and provenance are in the v2 task packet
and its frozen differential output; no source or runner changes were made by
this review.
