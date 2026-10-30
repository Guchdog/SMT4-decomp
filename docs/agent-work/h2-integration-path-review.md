# Coordinator review: H2 integration-path contract

## Review result

**Accept the report as a read-only integration plan.** The recommended Calc-only
slice is the smallest coherent replacement supported by current candidate
evidence: leave initialization and its registrations original, redirect only
`TitleConfig_Calc` at `0x001EA928`, and place the compiled body in the pinned
`.text` padding. The report correctly distinguishes this proposed patch from a
patch already built, validated, or run.

The placement arithmetic is consistent with the pinned image metadata:
`.text` begins at `0x00100000`, has unaligned size `0x002FE624`, and aligned size
`0x002FF000`. That leaves `0x9DC` bytes (2,524) from `0x003FE624` to
`0x003FF000`. The Calc experiment body is 2,096 bytes, and its four reported
local `.text` relocations rebase by adding the cave VMA to their local addends.
The branch from the original entry is within ARM branch range. These facts
support feasibility, not the correctness of an implementation.

The report also correctly states that `semantic_experiment.patch_image` is
restricted to an existing relocation-free leaf allowlist; the checked-in H1
integration runner does not reconstruct the external H1 runtime IPS writer;
and a live cave PC alone proves reachability, not behavior. Its prescribed
requirements—pinned hash and bounds, strict relocation validation, deterministic
IPS plus independent application, final-address ARM/caller checks, and live
original-versus-patched observables—are necessary before promotion.

## Runtime comparator caution

The H1 runtime report's first row sets `matched: true` while raw `timer_64`,
`blend_68`, and `fade_98` values differ between the two snapshots. The H2
comparison must define exactly which state values are expected to match at
each synchronized stop, and must not claim full-state equality from selected
fields alone. This review does not invalidate the H1 scenario's recorded
selected-observable results; it narrows their use as a whole-state precedent.

## Next implementation gate

Assign an integrator-owned Calc-only code-cave/IPS builder with tests for
address placement, branch encoding, relocation rebasing, overflow/collision
rejection, deterministic IPS application, and byte preservation. Then compare
the patched image at the final cave VMA before any Azahar run. Keep unresolved
input, service, caller, persistence, and runtime limitations from the Calc
review attached to the patch record.

## Evidence checked

- `build/agent-work/H2-semantic/h2-integration-path-contract/run-001/handoff.json`;
  ownership/provenance check passed.
- `docs/agent-work/h2-integration-path-contract.md`.
- `build/agent-work/H2-semantic/h2-calc-candidate/run-001/checks/final-final-seed-7/report.json`.
- `build/agent-work/H1-semantic/h1-menu-slice-integration/run-01/checks/azahar-runtime/runtime-report.json`.
- `docs/function-reconstruction-workflow.md` patcher capacity/limits.

