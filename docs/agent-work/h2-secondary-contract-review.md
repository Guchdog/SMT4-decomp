# Coordinator review: `TitleConfig_Secondary` contract

## Review result

**Recommendation:** accept the static callback contract as a reliable cleanup/control-flow map. It does not prove when the task system runs the callback or whether its state update frees anything.

The report correctly follows the global `g_TitleConfigWork` pointer rather than the callback argument, records the unconditional `work+4` flag, both reread loops, nullable cleanup slots, task-registration gate, and final global reload/release/clear sequence. It cross-checks that `0x002B9008` mutates a separate touch/global halfword instead of either title-work counter, and it avoids interpreting `0x002C45B8`'s state update as a heap free. ABI and no-return claims are bounded to direct instructions.

The ownership/provenance check passed. No C++ candidate, differential, real caller, scheduler, or runtime evidence exists. The recommended isolated harness and later caller observation are appropriate; this report is accepted as recon only.

## Next evidence

If the callback is reconstructed, preserve exact call order, loop rereads, null checks, state arguments, and clear-after-call order while keeping its helpers explicit. For full H2 acceptance, capture whether it runs after Calc's terminal state, how often it runs, and when task/work pointers become invalid in the actual title caller. Do not infer those lifecycle facts from the factory callback tuple or helper names.
