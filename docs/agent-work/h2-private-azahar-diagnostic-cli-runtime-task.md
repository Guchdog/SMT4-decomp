# H2 private Azahar diagnostic CLI: matched runtime comparison

## Goal

Use the reviewed private Azahar CLI to compare the original and final H2-patched
images with the same pinned CCI and identical recorded CTM input. Capture the
guest config bytes, title-config work/cursor/touch snapshots, H2 logical-query
arguments/results, input movie identity and terminal observer status. This task
does not close H2 by itself.

## Preconditions

- The follow-up independent review recommends acceptance and its handoff passes
  `check-handoff`.
- Recompute the private Azahar binary, feature patch, delivery-manifest, CCI,
  original/final image, IPS and profile identities immediately before use.
- Use only staging-root portable profiles and the reviewed wrapper. Do not use
  installed Azahar or user save/config trees.
- Both profiles must start from equivalent staged user data and differ only by
  the expected IPS. If a recording or run changes either profile, preserve the
  result, then create a fresh run-scoped paired stage from the same seed before
  comparison; do not weaken the preflight or hand-edit its manifest.
- Use one identical CTM for both profiles. It must match title ID and pinned
  source revision. Prefer an existing verified CTM if one covers the scenario.
  Otherwise ask the user to record one with Azahar's CLI; the agent must not
  drive keyboard/mouse or synthesize host input.

## Runtime procedure

1. Start with one serialized original-profile run, using the wrapper and CTM
   playback. If user recording is required, launch the private Azahar by CLI in
   a separate recording session, ask the user to perform the same title-menu
   Audio Settings sequence, and verify the saved CTM identity before playback.
2. Run original and patched profiles against the same CCI and CTM, one process
   at a time. Save independent JSONL outputs under the assigned ignored build
   run directory. Record the full command, exit code, PID, selected portable
   profile, CCI/movie/image/IPS/binary hashes and Azahar logs.
3. Require a terminal `complete` event in both observer outputs; preserve any
   `incomplete` output as a failed capture. Pair records by movie tick/sequence,
   PC/site, title-config state, exact `g_ConfigBytes[0..2]`, work/cursor bytes,
   touch-manager snapshots, and every H2 query `(id, mode, result)`.
4. Compare cancel and confirm branches, re-entry, selected slider changes,
   bounds, and restart persistence. The recorded CTM must demonstrate which
   actions actually occurred; report any missing branch instead of inferring it.
5. Compare H2 behavior with the existing user-reported original/patched manual
   observations. Separate those reports from observer/process evidence. Record
   mismatches, unresolved scheduling/input semantics, and exact domain limits.

## Restrictions and handoff

Use Azahar CLI only; no keyboard/mouse automation, GDB/RSP, RPC, network
listener, firewall change, guest write, installed profile, or user save-tree
access. Keep the two emulator processes serialized and profiles isolated. Do
not update milestone status until the comparison has been independently
reviewed. Return exact commands/results, artifact hashes, first divergence,
capture terminal status, human-recorded actions, and unresolved cases.
