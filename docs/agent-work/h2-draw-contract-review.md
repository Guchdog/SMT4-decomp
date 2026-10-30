# Coordinator review: `TitleConfig_Draw` contract

## Review result

**Recommendation:** accept the instruction-level contract report as a sound map for selecting the next draw slice. It is not a draw implementation or evidence of UI equivalence.

I reviewed the handoff and report against the initializer and calc contracts. The report keeps the initializer-created work object and callback registration distinct from unresolved scheduler behavior; it records the row loop and the `0x3A` TBB lookup separately from inferred labels; it includes the renderer-cache writes and possible indirect callback; and it leaves touch meanings, layout/text interpretation, and valid cursor ranges open. Its proposed comparison captures ordered helper calls and cache effects from identical initialized state, with calc frozen, and includes ABI and memory checks.

The row descriptor arithmetic is consistent with the reviewed `0x96` stride: indices 0, 1, and 2 address offsets `0`, `0x96`, and `0x12C`. The report correctly distinguishes this draw descriptor from the calc text path's additional `+0x16` offset. It also limits the visible three-option interpretation to an inference until table/helper or runtime evidence supplies it.

The handoff ownership/provenance check passed. Compilation, ARM differential, caller execution, and runtime comparison are all recorded `not_run`; that is accurate. Accepting this research task means the contract report is ready to guide implementation/test design, not that `TitleConfig_Draw` is reconstructed.

## Next evidence

Before promoting a draw candidate, retain original renderer/TBB/layout dependencies explicitly or reconstruct them, then compare ordered drawing calls, indirect callbacks, and exact renderer-cache changes from an initializer-created stable state. Use the CLI/GDB scenario for the integrated original-versus-patched run; no keyboard or mouse control is part of the plan.
