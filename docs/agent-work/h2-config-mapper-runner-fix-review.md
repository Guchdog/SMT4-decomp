# Coordinator review: H2 config mapper runner refinement

## Review result

**Recommendation:** accept the harness refinement and use the refreshed mapper reports for the isolated helper claims. This does not expand the mapper contract or establish initializer, UI, persistence, integration, or runtime behavior.

I reviewed the implementation and tests after the worker handoff. `mapper_access_violation` now rejects a nonempty observed data/stack write set from either execution, while intentionally permitting different immutable table-read footprints. The helper is called for each case before result and memory comparisons. The focused tests exercise both original and candidate write rejection and the allowed table-read difference. The report records empty write sets for both sides, retains exhaustive byte coverage and the threshold negative control, and records caller/runtime as `not_run`.

The check-handoff ownership/provenance validation passed. The handoff lists four focused tests and two fresh seeded runs, each covering all 256 byte values plus 256 seeded byte cases for each mapper. The source/object/reference identities and report hashes are recorded in the handoff. The shared runner change is scoped to this mapper-specific runner.

## Limits

The write check covers data and stack bytes observed by this runner's hooks; it does not prove absence of writes to uninstrumented memory regions. That limitation is explicit in the handoff. The accepted claim remains the three isolated byte-to-index helpers for the zero-extended byte domain used by the initializer. Caller composition, the full initializer, UI draw/edit behavior, save persistence, integrated patch behavior, and Azahar runtime comparison remain open.

## Recommendation for next work

Keep the mapper candidates eligible for integration once the initializer and calc slices have compatible interfaces and independent review. Before H2 closure, compare the original and integrated patch through the defined Azahar CLI/GDB scenario using isolated profiles; an entry hit alone is insufficient.
