# H2 private Azahar diagnostic CLI: follow-up review fixes

## Goal

Close the two findings from
`h2-private-azahar-diagnostic-cli-fixes-review.md` before any runtime assignment.
Keep all earlier movie, title/revision, profile-tree, path, and bounded query
return safeguards intact.

## Finding 1: verify the profile pair differs only by the expected IPS

After both live profile trees have been fully enumerated and each inventory has
been checked against its files, compare the original and patched inventories
directly. Require identical case-normalized relative-path sets except for the
documented IPS path; require matching size and SHA-256 for every shared path;
require the original to omit the IPS and patched to contain exactly the IPS
whose hash matches `standalone_ips.sha256`. Do not trust
`profiles_differ_only_by_ips: true` as proof. Add fixtures where both trees
individually match their own manifest but differ in a non-IPS file, path case,
or file set, plus a positive control where only the expected IPS differs.

## Finding 2: ignore non-H2 queries at the shared helper PC

At `0x002C1830`, retain argument/result capture only for the five documented H2
`(id, mode)` pairs. A different pair must not generate a generic H2 snapshot,
guest memory reads, or a query-return record. Extend the C++ observer harness to
assert all three absences; preserve capture for H2 pairs and ensure unrelated
allowlisted sites still behave as before.

## Validation and handoff

- Run focused offline Python profile-fixture and C++ observer tests, including
  negative controls, then rebuild pinned private `citra_core` and `azahar.exe`
  with at most two jobs because the observer source changes.
- Regenerate the feature patch, binary/delivery manifest hashes, implementation
  report, and structured handoff. Keep compatibility patches separate.
- No emulator launch, wrapper invocation, actual staging-profile access, user
  save-tree access, debugger/RPC/network/firewall, guest write, or host input
  automation. Runtime remains `not_run` pending a new independent review.
- Update only the private Azahar build tree and implementation report assigned
  to this task. Do not edit the board, milestone/status docs, or shared code.

Return `ready_for_review` only if both findings have direct negative-control
coverage; otherwise return `blocked` with the smallest counterexample.
