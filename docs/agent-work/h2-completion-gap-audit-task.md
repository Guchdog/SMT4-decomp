# H2 completion gap audit

## Goal

Independently map every H2 milestone acceptance item to current repository
evidence and identify what must still be proven before H2 can close. This is a
read-only audit to guide the coordinator's matched runtime capture and later
closure; do not redefine the H2 scope.

## Review requirements

- Read `docs/milestones/H2-audio-settings.md`, `docs/functional-status.md`,
  `docs/reconstruction-milestones.md`, the active H2 board and its H2 task
  states. Treat the six numbered H2 acceptance tests as the requirement list.
- For each criterion, identify the authoritative evidence files/reports and
  classify it as proved, partial, contradicted, or missing. Check evidence
  scope and hashes where convenient; do not use task acceptance/static links as
  proof of runtime equivalence.
- Audit each named reconstructed function/helper and required caller test for
  differential evidence, ABI/memory/branch domain, promotion/IPS inclusion and
  unresolved original/HLE dependencies. Distinguish accepted function slices
  from whole titleConfig behavior.
- Incorporate the first failed runtime command report and current runtime task
  state. Do not assume that the new CLI dispatch fix has runtime-tested Qt
  startup; it has only passed offline source/harness review.
- Return a concise acceptance matrix with exact outstanding evidence and the
  smallest complete sequence needed to close H2 before H3. Flag any additional
  non-runtime prerequisite that would block closure.

## Restrictions

Read-only audit. Do not run builds/tests, change source/board/milestone files,
invoke wrapper, read actual staged profiles, launch/connect to Azahar, use
debugger/RPC/network/firewall, access user save trees, or automate host input.
Write only the assigned audit report and handoff.
