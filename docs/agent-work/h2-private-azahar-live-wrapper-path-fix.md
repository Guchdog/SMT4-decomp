# H2 live wrapper private-binary path containment fix

## Result

Constrained the binary path from `h2-delivery-manifest.json` to a canonical relative descendant of that manifest's directory. Absolute paths, POSIX/Windows roots, drive paths, UNC paths, backslashes, empty components, `.` and `..` components, and colon/ADS forms are rejected before resolving. The resolver checks the private delivery root and every existing component through the executable leaf for symlink/reparse status, resolves the result, verifies containment beneath the delivery root, and confirms it is a regular file. The supplied executable still must resolve to the manifest-selected executable and match the pinned SHA-256.

The fixture now places its executable at the same relative layout used by the delivery manifest: `build-clang64/bin/Release/azahar.exe`. The live and CTM command paths in `h2_azahar_launch.py` were not changed.

## Validation

`python -m unittest test_h2_live_preflight -v` passed: **15 tests, exit 0**. New tests cover valid normalized relative input, absolute/traversal/dot/empty-segment paths, Windows drive and UNC forms, a supplied binary from a different root, and a simulated reparse point on an intermediate directory. The existing positive live command and valid CTM command-shape controls also pass. Tests use temporary synthetic trees and mock subprocess; no wrapper, executable or profile was accessed.

`python -m unittest test_h2_ctm_preflight -v` remains **exit 1**. Its fixture CTM has no A-button sample, causing `capture_start_pad_index` to reject the fixture before five of its negative assertions; the symlink branch also cannot create a symlink under this account. The separate valid-CTM command-shape control in the passing live suite verifies that the replay route still builds with `--movie-play` and no `--h2-live`. I did not change the legacy test file because it is outside this task's write scope.

## Changed-file SHA-256

| File | SHA-256 |
|---|---|
| `build/agent-work/H2-semantic/h2-private-azahar-source/h2_live_preflight.py` | `c8524fc993a93139047e8225e4736e39b83d2325bb9f5848f14e01ceaf270e53` |
| `build/agent-work/H2-semantic/h2-private-azahar-source/test_h2_live_preflight.py` | `580ff2b1150549321f27528cecc80c75450dd23de4a8511856c21ce0a9b4ee11` |
| `build/agent-work/H2-semantic/h2-private-azahar-source/h2_azahar_launch.py` | `f6ee3a86dc919a6be7ac2bbf588924dbb484ca2e3cf0a7b601add48aa40a2263` |

No tests were run against installed or staged user profiles. No binary build, launch, network, debugger, emulator or input automation was used. These checks establish path rejection and command construction for synthetic fixtures; they do not establish runtime equivalence.

Next action: independent review the path resolver and adversarial tests. Repair the stale CTM fixture separately if a green legacy-suite result is required.
