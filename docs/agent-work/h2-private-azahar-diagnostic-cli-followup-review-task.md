# H2 private Azahar diagnostic CLI: follow-up independent review

## Goal

Independently verify that the last two review findings are closed before any
runtime assignment.

## Review focus

- Verify the current follow-up task/handoff/report hashes, pinned Azahar
  revision, delivery manifest, feature patch and rebuilt binary identities.
- Trace the live cross-profile comparison in `h2_ctm_preflight.py`: both actual
  profile inventories must first match their own file sets and hashes; then the
  original/patched inventories must have exactly the same paths, casing, sizes
  and hashes except for the expected IPS, absent in original and present with
  the expected hash in patched. Check that a manifest-only assertion cannot
  override actual disagreement.
- Trace `OnBeforeInstruction` handling of `0x002C1830`: H2 pairs retain their
  entry arguments, paired return values, and normal snapshots; non-H2 pairs must
  produce no guest reads, generic snapshots, or query-return events. Verify
  unrelated allowlisted PCs remain unaffected.
- Inspect the newly added negative and positive controls and check their
  sensitivity against the implementation. Verify the prior fixes for movie
  validation/playback state, live profile hashes/containment and IPS/executable/
  CCI identities remain in place.
- Recommend `accept`, `request_fixes`, or `blocked` with precise evidence and
  limitations. Acceptance qualifies the private CLI for a separate coordinator
  runtime assignment only; it neither authorizes a launch itself nor closes H2.

## Restrictions

Read-only review. Do not run builds/tests, invoke the wrapper, inspect actual
staged profiles, launch/connect to Azahar, access user save trees, use debugger/
RPC/network/firewall, modify guest memory, or automate host input. Write only
the assigned report and structured handoff.

