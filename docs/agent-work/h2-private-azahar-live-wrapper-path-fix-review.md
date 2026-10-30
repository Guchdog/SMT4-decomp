# Independent review: private Azahar binary path containment fix

## Recommendation: accept the scoped live-route fix

The resolver closes the previously reported manifest-path traversal gap for the
live preflight. It accepts only canonical forward-slash relative descendants,
rejects absolute, drive, UNC, rooted, traversal, empty, dot, backslash, NUL and
colon/alternate-stream forms, resolves beneath the delivery root, checks every
component from that root through the file leaf for reparse points, and requires
a regular file. The resulting executable must still equal the supplied
executable after resolution and pass the pinned SHA-256 check.

I found no remaining escape from the resolved delivery root through the
manifest's binary path. The root itself is checked for reparse status before
resolution. This review treats the delivery directory as the trust boundary;
ancestors above the manifest's parent are not walked. Because the executable
path is normalized to the resolved root and the binary hash is fixed, that
does not defeat descendant containment. If the intended policy also forbids a
delivery root reached through an ancestor junction, add a walk from the
manifest path to the filesystem root and a fixture for it.

## Adversarial path and reparse coverage

The focused tests cover:

- A valid normalized path matching `build-clang64/bin/Release/azahar.exe`.
- An absolute path, `../` and embedded `..` traversal, `.`, empty components,
  drive-rooted and drive-relative Windows paths, backslash paths, and UNC paths.
- A same-content executable under a different root, rejected because it does
  not resolve to the manifest-selected file.
- A simulated intermediate reparse point at `build-clang64`, rejected before
  hashing/launch. The fixture uses the same simulation approach when the
  platform cannot create a symlink.
- A wrong-content private executable, rejected by SHA-256.

The implementation checks the delivery-root leaf and each descendant
component before resolving it, then verifies containment and file type after
resolution. The final supplied path is separately checked for leaf reparse
status and resolved equality with the selected file. A dangling descendant
reparse point is rejected as a missing component, so it cannot pass the
preflight.

The task-packet hashes for all 11 frozen inputs matched at review time. The
reviewed source hashes are `h2_live_preflight.py`
`c8524fc993a93139047e8225e4736e39b83d2325bb9f5848f14e01ceaf270e53`,
`test_h2_live_preflight.py`
`580ff2b1150549321f27528cecc80c75450dd23de4a8511856c21ae0a9b4ee11`, and
`h2_azahar_launch.py`
`f6ee3a86dc919a6be7ac2bbf588924dbb484ca2e3cf0a7b601add48aa40a2263`.
The launcher file hash is identical to the prior live-wrapper review packet;
the path fix changed only the live-preflight helper and its tests.

## Command-route preservation and remaining evidence

`build_live_launch()` remains separate from `build_launch()`. Live mode uses
the no-movie flags and final CCI position. The existing CTM builder still
computes the start-pad index, passes `--movie-play` and the observer options,
and places the CCI last. The live test suite contains a valid-CTM control that
asserts `--movie-play` remains present and `--h2-live` absent. The launcher
source hash above provides direct evidence that neither command builder
changed in this path-fix task.

The implementation report states that the focused live suite passed 15 tests.
This review was read-only and did not run tests. The prior review recorded the
legacy CTM suite as failing because its fixture has no A-button sample and a
symlink fallback cannot create a symlink under that account. The valid CTM
control in the live suite does not repair that separate legacy fixture.

No wrapper invocation, Azahar launch, profile access, emulator, debugger,
network, or input automation was performed. The review approves the path fix
within the live-route delivery-root boundary; it does not assert runtime
equivalence or make a new claim about the legacy CTM fixture result.
