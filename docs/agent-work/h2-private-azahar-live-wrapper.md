# H2 no-CTM live observer wrapper

## Result

Implemented a separate `--live` wrapper route for the private Azahar observer. It does not accept or pass a movie, performs a dedicated stage/profile/CCI/binary preflight, and passes `--h2-live` with a fresh JSONL output path. The existing CTM replay builder remains intact; a focused valid-CTM command test confirms it still emits `--movie-play` and omits `--h2-live`.

Example command shape:

```powershell
python h2_azahar_launch.py `
  --manifest <stage-root>/staging-manifest.json `
  --delivery-manifest <private-azahar>/h2-delivery-manifest.json `
  --profile patched `
  --live `
  --run-root <stage-root> `
  --output <stage-root>/live-input.jsonl `
  --azahar <private-azahar>/build-clang64/bin/Release/azahar.exe
```

The command builder places `--h2-live`, `--h2-snapshot`, the run-root and the selected staged `app/user` root before the CCI, which remains the final positional argument. It sets Qt plugin paths from the selected staged `app` working directory. The wrapper only launches after preflight returns a command; tests mock `subprocess.run` and assert it is not called for rejected cases.

## Preflight guards

`h2_live_preflight.py` reuses the reviewed staged-profile inventory and pair validators while adding live-specific checks. It requires a run directory that is a direct child of the pinned manual-comparison root, the exact root `staging-manifest.json`, exact `original/app/user` and `patched/app/user` trees, matching live file inventories outside the expected patched IPS, and the pinned IPS identity. It checks both configs and manifest flags for GDB/RPC disabled, rejects output traversal, existing outputs and output reparse points, and confines output to a new `.jsonl` directly under the staged run root. This prevents selecting an installed or source user tree through the wrapper.

The private executable path must resolve to the path declared in the delivery manifest and its current hash must match the pinned private observer binary. The staged CCI must be the run-root `pinned-title.cci`, match the pinned full-file SHA-256, and expose the expected SMT4 program ID in its first NCCH partition. The staging manifest's final-image hash and its referenced integration-manifest hash/content must match the reviewed H2 image revision. The full CCI hash pins the exact game image bytes; the stage contract does not carry a separate CCI source-code revision field.

## Validation

The task-owned offline suite passed: **11 tests, exit 0**. It covers valid live command construction, no movie argument, CCI-last ordering, unchanged CTM command construction, wrong private binary, wrong CCI hash/title, wrong final-image revision identity, original/patched profile mismatch, output traversal/existing/reparse controls, disabled-GDB/RPC requirements, wrong staged user root, and movie/live conflict. All profile fixtures are synthetic temporary trees; no staged production profile was opened. All wrapper `subprocess.run` calls are mocked.

I also ran `python -m unittest test_h2_ctm_preflight -v` as a replay regression; it exited 1. The existing fixture's fake CTM header contains no recorded A-button sample, so `capture_start_pad_index` rejects the fixture before multiple negative-control assertions. Its Windows symlink fallback also cannot create a symlink under the current account. The new live suite's valid-CTM control constructs a CTM with an A sample and confirms the replay command shape. I did not modify that unowned existing test file.

No Azahar build, wrapper launch, profile access, emulator, debugger, RPC/network, or input automation was performed. The tests establish command/preflight behavior for synthetic fixtures; they do not establish a successful live run, callback timing, or runtime semantic equivalence.

## Changed-file hashes

| File | SHA-256 |
|---|---|
| `build/agent-work/H2-semantic/h2-private-azahar-source/h2_live_preflight.py` | `b9c05c2b4bb574d2215606d3ca7b5b6951e10b6fcc1f974b5aa048e8b3119f6a` |
| `build/agent-work/H2-semantic/h2-private-azahar-source/test_h2_live_preflight.py` | `17e1fc472eedf63f799c434b4f0f6975c14f82c4e344cb4e0b9160fa967edc9f` |
| `build/agent-work/H2-semantic/h2-private-azahar-source/h2_azahar_launch.py` | `f6ee3a86dc919a6be7ac2bbf588924dbb484ca2e3cf0a7b601add48aa40a2263` |

Next action: independent review of the new live preflight and command-builder tests. The existing CTM fixture can be repaired in a separately assigned test change if a clean full replay-suite result is required.
