# Coordinator review: H2 initializer dependencies

## Review result

**Recommendation:** accept the helper map as the contract boundary for an orchestration-only initializer candidate. Keep unresolved subsystems as original calls.

The report distinguishes caller argument facts from helper semantics and does not infer scheduler order or synchronous asset readiness. It captures the allocation result publication and unchecked null path, opaque task-factory tuple words, exact group descriptor setup, split GPR/VFP sprite arguments, cursor setup arguments, asynchronous table requests, the sound call, and the null-mode shared UI reset. The strongest fully described direct helpers are the sprite-group clear/bind and mode-0 sprite animation setup; the other calls should remain dependencies until their contracts are separately established.

The recommended differential boundary is appropriately broad for an initializer: compare the poisoned work object, global publication, task handles, config bytes, helper call sequence and ABI state, while representing scheduler and asynchronous effects only to the extent their contracts support. It preserves original null/fault behavior and avoids treating callback registration as proof of dispatch order.

The handoff provenance check passed. This remains static research; compilation, ARM differential, caller composition, and runtime evidence are `not_run`. Accepting this task approves the dependency map only, not an initializer replacement.

## Next implementation boundary

Build a readable C++ orchestration candidate with explicit calls to the original dependencies and a helper-specific harness that records those boundaries. Stub a dependency only where its modeled effects and limits are declared; otherwise execute its pinned original body. Review the candidate and harness independently before any production promotion.
