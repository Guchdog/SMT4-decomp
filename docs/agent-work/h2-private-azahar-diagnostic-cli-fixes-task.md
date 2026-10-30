# H2 private Azahar diagnostic CLI fixes

## Goal

Close the two P1 findings from
[`h2-private-azahar-diagnostic-cli-review.md`](h2-private-azahar-diagnostic-cli-review.md)
before any runtime assignment:

1. Observer mode must fail closed unless a valid, matching movie is actually
   requested and playback is confirmed before the emulation thread starts.
2. The launch wrapper must validate the current staged profile trees and path
   containment; it cannot treat profile-inventory fields in the staging
   manifest as proof of live files.

Use the existing private Azahar checkout at commit
`219d743a1e698101fe1ab8bef43e6563126c3c27`. Do not switch emulator or source
revision. Preserve separate feature and build-compatibility patches. H2 remains
open until a fresh independent review and a later authorized matched runtime
capture.

## Required changes

### Require movie playback in the native observer

- If `--h2-snapshot` is requested without `--movie-play`/`-p`, reject before
  loading the title or creating a capture that could be mistaken for replayed
  evidence.
- Validate the CTM header's title ID and source revision in the native observer
  startup path as well as in the wrapper, so direct raw CLI invocation cannot
  bypass the deterministic-input gate.
- Confirm that movie playback actually entered the playing state before starting
  `EmuThread`; if Azahar's playback setup fails, write a bounded `incomplete`
  status when possible and exit nonzero. Do not infer successful playback from a
  nonempty path or a void `StartPlayback` call.
- Keep the capture disabled by default. Preserve existing normal Azahar behavior
  when observer mode is absent.

### Revalidate live staging package and profiles

Update `h2_ctm_preflight.py` and the `h2_azahar_launch.py` wrapper to validate the
actual staging package before starting the private binary:

- Resolve the staging root from the manifest and require it to be a valid
  directory. Require the selected profile's `user_root`, app directory, and
  working directory to be inside that staging root using filesystem
  path-component containment, not string prefixes.
- Require the working directory to match the selected profile's expected app
  root and the user root to match the manifest's `app/user` layout. Reject
  missing roots, path traversal, sibling-prefix paths, and symlink escapes.
- Re-enumerate each live profile tree and compare the complete relative-path set
  and SHA-256 values against its manifest inventory. Reject missing, changed,
  extra, or case-colliding files. This must verify the patched profile's IPS and
  prove the original profile has no IPS.
- Verify the staged per-profile Azahar executable identities and CCI against the
  manifest. Continue to verify the private diagnostic executable against its
  pinned delivery hash, and both original/final code images against recorded
  hashes.
- Ensure every preflight failure occurs before `subprocess.run`. Return the
  validated selected profile root and use the staged app working directory so
  Azahar's portable profile resolution selects exactly that profile.
- The wrapper is the supported launch path. Clearly document that raw Qt CLI
  invocation without the wrapper cannot provide staging-manifest/profile-tree
  assurance, even though the native observer independently enforces movie title
  and revision.

## Tests and evidence

Add focused offline tests using temporary directories and small fixture files:

- observer enabled without movie playback is rejected before boot;
- valid CTM accepted; wrong title, wrong revision, truncated header, and bad
  magic rejected before playback;
- movie playback setup failure does not start the emulation thread or produce a
  complete capture;
- profile-root/workdir outside staging root, sibling-prefix, traversal, and
  symlink escape are rejected;
- missing, modified, extra, and case-colliding live profile files are rejected;
- patched IPS mismatch or original-profile IPS is rejected;
- staged executable and CCI mismatch are rejected;
- negative controls verify every rejection occurs before the mocked subprocess
  launch.

Rebuild the private Azahar core and Qt executable with at most two jobs. Do not
run a canonical game build. Save exact commands, exits, tool versions, binary and
patch hashes, test outputs, and a delivery manifest. Keep `azahar.exe` and all
source/build artifacts under ignored `build/` paths; never vendor them into Git.

## Restrictions

- Do not launch Azahar, invoke the wrapper, inspect or change actual staged
  profiles, connect to an emulator, or perform runtime capture during this fix
  task. Those actions require fresh independent review and a separate coordinator
  runtime assignment.
- No GDB/RSP, RPC, network listener, firewall change, guest memory write, host
  keyboard/mouse automation, installed profile change, or user save-tree access.
- Do not update H2 status, the active board, milestone records, or shared
  interfaces. The coordinator owns those files.
- If the loader cannot reliably confirm movie playback or the manifest cannot
  supply a verifiable staging root/profile layout, stop with a precise blocker
  and proposed evidence needed to unblock.

## Handoff

Update the private implementation report, create a fresh structured handoff, and
record the current source/binary/patch hashes and every validation command. The
handoff should be `ready_for_review` only if both findings are fixed with
focused negative controls; otherwise return `blocked` with the smallest concrete
counterexample. Runtime evidence remains `not_run` and H2 remains open.
