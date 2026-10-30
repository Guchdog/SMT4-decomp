# H2 private Azahar diagnostic CLI fixes: independent review task

## Goal

Independently review the corrected pinned Azahar observer patch, wrapper and
profile preflight before any runtime assignment. Verify both findings from the
prior review are actually closed and that logical-query return capture remains
bounded to the approved H2 seam.

## Inputs

- `docs/agent-work/h2-private-azahar-diagnostic-cli-fixes-task.md`
- `docs/agent-work/h2-private-azahar-diagnostic-cli-review.md`
- `docs/agent-work/h2-private-azahar-diagnostic-cli-implementation.md`
- `docs/agent-work/h2-input-seam-contract.md`
- `build/agent-work/H2-semantic/h2-private-azahar-diagnostic-cli-fixes/run-001/task.json`
- `build/agent-work/H2-semantic/h2-private-azahar-diagnostic-cli-fixes/run-001/handoff.json`
- `build/agent-work/H2-semantic/h2-private-azahar-diagnostic-cli-fixes/run-001/report.json`
- `build/agent-work/H2-semantic/h2-private-azahar-source/azahar-h2-observer.patch`
- `build/agent-work/H2-semantic/h2-private-azahar-source/h2-delivery-manifest.json`
- `build/agent-work/H2-semantic/h2-private-azahar-source/h2_ctm_preflight.py`
- `build/agent-work/H2-semantic/h2-private-azahar-source/h2_azahar_launch.py`
- `build/agent-work/H2-semantic/h2-private-azahar-source/test_h2_ctm_preflight.py`
- `build/agent-work/H2-semantic/h2-private-azahar-source/tests/test_h2_observer.cpp`
- Corrected private Azahar source files named in the delivery manifest.

## Review requirements

- Independently verify the current handoff, report, patch, delivery manifest,
  binary and changed-file hashes, pinned revision, exact build/test commands,
  and task ownership/provenance.
- Confirm observer mode rejects absent/invalid CTM playback before capture,
  verifies title and source revision, and confirms playback entered the playing
  state before starting emulation. Check setup failure cannot produce a
  complete capture.
- Confirm wrapper checks the live original and patched trees against the full
  manifest inventory, enforces component containment and portable profile
  layout, detects traversal/symlink/case collisions, checks executable/CCI/IPS
  identities and original IPS absence, and rejects before child launch.
- Confirm H2 query entry/return capture is fixed-site, per guest-thread, bounded,
  and records arguments plus return value without adding unrelated PCs or
  arbitrary memory reads. Check wrong-thread, nested/pending, and teardown
  behavior against implementation and harness coverage.
- Inspect focused negative controls for meaningful sensitivity and identify any
  false-green path, especially incomplete output, profile changes after
  validation, and CTM/playback state transitions.
- Return `accept`, `request_fixes`, or `blocked` with precise file/line findings.
  Acceptance only qualifies the private diagnostic CLI for a separate
  coordinator-assigned runtime task; it does not authorize runtime by itself or
  close H2.

## Restrictions

Read-only source/artifact review. Do not run builds/tests, invoke the wrapper,
access or modify actual staging profiles, launch/connect to Azahar, inspect user
save trees, use debugger/RPC/network/firewall, write guest memory, or automate
host input. Write only the assigned review report and structured handoff.

