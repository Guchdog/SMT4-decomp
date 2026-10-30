# Coordinator review: H2 logical input seam

This review predates the [manager-state producer follow-up](h2-input-manager-touch-state-producer-audit.md), which identifies the `TOUCH CALC` callback and corrects the registration-record base. The review's conclusions about Calc's four `-1` work arguments, opaque state meaning, the unresolved relation to H2 registrations, and physical input mapping remain open.

## Review result

**Recommendation:** accept the report's negative finding about undocumented memory handles and its offline logical-service boundary. Add a narrower source-derived runtime probe at a documented call-return register seam; do not write the suspected touch/input memory fields.

The report supports that `UiTouch_GetRegionTouchState` compares an active panel ID to a halfword handle and returns an opaque manager byte, while the initializer fills Calc's `+0x1C..+0x22` reads with `0xFFFFFFFF` and observed region registration stores results at `+0x14..+0x18`. It correctly leaves the handle mismatch and physical input mapping unresolved. The global query helpers consume internal input tables whose producer chain has not been traced. Its offline `(id, mode) -> result` harness boundary is valid for Calc's logical branch contract, but it is not evidence of a real guest event.

## Candidate CLI/GDB seam

The Calc listing at `0x001EABDC` calls `camp_func_002C1830(4, 0)` and resumes at `0x001EABE0`, where the next instructions compare returned `r0` to zero. A debugger breakpoint at `0x001EABE0` can therefore pause after the logical query has completed and before Calc consumes its result. A bounded driver may read `r0`, save it, send the single-register `P` write for register 0 with a documented logical result, read it back, then continue. This changes the service return in a stopped emulated CPU context; it does not alter an undocumented memory representation or use OS keyboard/mouse input.

Azahar 2126.2's official GDB stub source dispatches packet `P` to `WriteRegister`; that routine writes the selected ARM context register, updates the active CPU context, and replies `OK` ([pinned source](https://raw.githubusercontent.com/azahar-emu/azahar/2126.2/src/core/gdbstub/gdbstub.cpp)). This is source evidence only. The installed executable's version is not yet verified and its actual packet behavior remains untested, so first run a disposable isolated CLI session and perform a same-value `r0` round-trip at a known stop. Require the expected reply, register readback, bounded continue, and clean detach before attempting a logical-result control.

For H2, the positive-control case may set only the documented return of `(4,0)` to `1`, with other logical queries left at observed values, then capture Calc's work/config delta. Treat this as logical-service injection, not a physical button mapping. Map equivalent call-return seams for cursor movement and state-2 confirmation before claiming a full edit/confirm sequence. If the local `P` probe fails or the stop PC is unexpected, stop and leave those runtime scenarios unvalidated; do not fall back to keyboard/mouse control.

## Evidence boundary

The run-002 input-seam handoff passed ownership/provenance validation. The report and this review establish no RSP session, no register write, no real input event, no candidate differential, and no runtime equivalence. The next task is a reviewed read-only observer plus reversible single-register capability probe in the staged Azahar CLI instance; only after that succeeds should it be extended to the mapped logical return points.
