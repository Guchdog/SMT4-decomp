# Independent review: guarded no-CTM Azahar live wrapper

## Recommendation: request fixes

The live command is separated from the movie replay route and the staging,
image, profile, CCI and output checks are substantial. Static review found a
path-confinement gap in the delivery-manifest executable path: the supplied
manifest can name an absolute path or a `..` path outside its own directory,
and the live preflight accepts it if the executable bytes match the hard-coded
SHA-256. It also checks reparse status on the manifest/executable leaf only,
not each ancestor component. The executable content remains hash-pinned, but
the intended private-delivery location is not enforced against a changed
manifest or a directory junction. Add relative-path and resolved-containment
checks plus ancestor reparse checks, with traversal and reparse fixtures, before
accepting the private-path guard.

## Live command and safeguards reviewed

`build_live_launch()` calls `preflight_h2_live()` before constructing the
command. Its argv contains the resolved private binary, `--h2-snapshot` with
the checked output path, `--h2-run-root`, `--h2-user-dir` for the selected
staged profile, and `--h2-live`; it contains no `--movie-play` or CTM input.
The CCI is the last argv token. Qt plugin paths and working directory come
from the selected staged app. `main()` rejects `--live` combined with
`--movie`, and `subprocess.run` occurs only after preflight has succeeded.
The live positive fixture mocks subprocess and asserts no movie option, CCI
last, selected profile root, and the app working directory.

The live preflight pins the original/final image hashes, integration-manifest
hash and content identities, standalone IPS identity/path, CCI full-file hash,
NCSD/NCCH bounds and SMT4 program ID, staged executable hash, and private
observer executable hash/revision. It requires the manifest and supplied run
root to resolve to the same direct child of the approved staging parent and
requires the staging manifest at that root. It verifies the original and
patched `app/user` roots, full per-file inventories and hashes, case-collision
absence, distinct profile roots, and identical profile contents outside the
expected patched IPS. It also checks the portable Qt config has exactly one
explicit false entry for each GDB and RPC key and checks both staging-manifest
flags are false.

Output must be an absolute `.jsonl` direct child of the stage root; traversal,
pre-existing output, final output reparse point, stage root reparse point and
output-parent reparse point are rejected. Existing live tests exercise
traversal, an existing output, a symlink/reparse output (or simulated reparse
fallback), GDB/RPC enablement, profile-root substitution, changed profile
content, and a wrong private-binary hash. Profile-pair content, file-set and
casing mutations are tested even after their individual inventories are
refreshed, which verifies the cross-profile comparison is not trusting only
the manifest assertion.

The key remaining path concern is specific: `_load_private_binary()` forms the
expected binary with `(manifest_path.parent / binary_meta.path).resolve()` but
does not reject absolute paths or `..`, and it does not require the result to
remain under `manifest_path.parent`. `_is_reparse()` checks the supplied
manifest and binary path leaves, but not ancestor directories; a junction in
the path is therefore not necessarily rejected. The fixed executable hash
blocks different binary contents, but does not prove the resolved file lives
under the intended private-delivery root. A TOCTOU window also remains between
checking that the output path does not exist and Azahar opening it; a private
fresh stage root makes that narrower, but the output is not atomically
reserved.

## CTM replay route and existing fixture status

`build_launch()` remains a separate route: it validates the movie/header,
computes the prior-A start-pad index, then constructs `--movie-play`, snapshot,
run-root, user-dir and start-pad options with the CCI last. The live branch
does not call it or alter its command construction. The new live test’s
`test_existing_ctm_replay_route_still_builds_movie_command` creates a CTM with
one valid A press, mocks subprocess, and checks `--movie-play` remains present
while `--h2-live` is absent. This supports preservation of command shape, not
a historical byte-for-byte comparison of the Python file.

The prior implementation report records the legacy
`test_h2_ctm_preflight` suite as exit 1: its base fixture contains only an empty
CTM header, so the wrapper rejects it for having no recorded A-button press;
the symlink case also cannot create a symlink under that account. The source
fixture confirms the empty header. This review did not run tests, consistent
with the assigned read-only review plan. The dedicated live suite’s valid CTM
control repairs the fixture by appending a one-sample A press; it does not
clear the legacy suite result. Fix the fixture separately if a green CTM-suite
regression is required.

## Scope and next action

At review start, all 14 `task.json` frozen-input SHA-256 values matched. I
reviewed only the declared source, test, staging, delivery-manifest and report
paths. I did not run tests, invoke the wrapper, launch Azahar, or inspect
production profiles. The implementation report states that the live fixture
suite passed 11 tests with mocked subprocess calls; this review did not rerun
or independently verify that execution claim.

Next, constrain the live executable path to a relative path under the delivery
manifest directory, reject `.`/`..` traversal and reparse points throughout
the resolved path chain, and add adversarial tests for an absolute/traversal
manifest path and a parent junction. Keep the existing movie builder separate
and repair the stale CTM fixture in an independently assigned test change.
