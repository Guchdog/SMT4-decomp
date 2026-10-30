# Coordinator review: H2 initializer orchestration candidate

## Review result

**Recommendation:** accept this as a supported experimental C++ orchestration candidate under the runner's declared HLE boundaries. Do not promote it as a complete initializer replacement yet.

The candidate follows the pinned call order and direct values, preserves the ignored entry argument and unchecked allocation result, stores the calc-task handle, initializes only documented fields, calls the original mapping/fill/copy/group/animation helpers, and returns through the original eight-byte copy helper. The task factory stack words and sprite/cursor arguments are represented in typed calls; the runner captures relevant GPR, stack, and VFP payloads at the real wrapper boundaries. The corrected `+0x1A`-before-fill order matches the current original instruction sequence.

I reviewed the task-local harness and reports. It runs the pinned original body and candidate in separate ARM11MPCore Unicorn states, enables VFP, uses a poisoned workspace and varied config words/incoming `r0`, compares work/global/config memory, final return/PC/SP and callee-saved state, and compares declared helper call arguments. Both corrected-source seeded reports pass their five cases and detect the `0x18` to `0x17` negative control. The source and object hashes match the records. The run-002 handoff was refreshed after the milestone input changed; its provenance check passes.

## HLE boundary and limits

The reports intentionally replace allocator, process-factory, sprite-resource, cursor, async-load, sound, and UI-reset effects with explicit synthetic HLE models. Those models make this a useful orchestration and call-contract differential, but they do not establish the real helpers' allocation, scheduler, sprite, cursor, asset, audio, or UI behavior. Original mapper bodies and pair/group/animation helpers execute from the pinned image; the mapper candidates are not part of this result. No real caller, callback scheduling, editing, cancel/confirm, persistence, integrated patch, or Azahar runtime path was tested.

The focused unit test for trace projection is synthetic support evidence; the original-versus-candidate Unicorn reports are the substantive candidate evidence. Current ledger status remains about the checked-in original wrapper and has not changed. Any later non-identical production replacement needs a truthful non-matching classification and caller/runtime evidence.

## Next integration evidence

Before promoting this initializer, replace or independently validate the synthetic HLE boundaries against their real engine contracts, then run the actual MainTitle State 9/10 caller and verify readiness/reset behavior. Keep the edit/persistence scenario separate and use the reviewed Azahar CLI/GDB route with isolated profiles and no OS keyboard/mouse control.
