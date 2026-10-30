# H2 private Azahar diagnostic CLI implementation

## Result

Updated the private diagnostic build based on Azahar commit `219d743a1e698101fe1ab8bef43e6563126c3c27`. The full source patch, separated build-compatibility patches, and SHA-256 input manifest are in `build/agent-work/H2-semantic/h2-private-azahar-source/`.

Observer mode now rejects a missing `--movie-play` before observer output is opened. Native startup validates the CTM with Azahar's `Movie::ValidateMovie` (including header magic, exact source revision and input count) and checks the CTM program ID. After loading the guest, it checks loader and process IDs, PID, process name, and nonempty movie path. After `StartPlayback`, it requires play mode `Playing`, expected title ID, and an exact-valid header before starting `EmuThread`. A failed playback setup writes `incomplete` when possible and exits before the emulation thread.

The wrapper revalidates the staging root and both live profile trees before constructing the launch command. It enforces component containment and the `app/user` layout; rejects symlink/reparse traversal; hashes each tree's exact file inventory; detects missing, extra, modified, and case-colliding files; verifies each staged `app/azahar.exe`, shared CCI, original-profile IPS absence, and patched-profile IPS identity; and checks original/final image identities. It passes the checked profile's user root through `--h2-user-dir`. The Qt frontend sets that existing user root before constructing `QtConfig`, so the private executable uses the staged profile. The wrapper also verifies the private binary against the delivery manifest. Raw direct Qt invocation can enforce movie identity and playback, but cannot attest staging-manifest/profile contents; the wrapper is the supported launch path.

The observer now pairs H2 logical-query calls to their returns. It tracks only the five H2 `(control_id, mode)` pairs at the fixed `camp_func_002C1830` entry, stores `(r0, r1, LR, SP)` by guest thread, and captures return `r0` at the matching LR with matching SP. It handles thread switches with per-thread pending stacks, caps pending calls at 64, and writes `incomplete` if a tracked call is unmatched at teardown. No additional fixed PC sites or guest reads were added. Existing `UiTouch_GetRegionTouchState` entry/return observations remain. These records expose the logical query result, but do not prove which physical HID event produced it.

## Validation

- `cmake --build build-clang64 --target citra_core --parallel 2`: exit 0, 131/131 steps.
- `cmake --build build-clang64 --target azahar.exe --parallel 2` with the existing MSYS binary directory on this process PATH: exit 0, 29/29 steps. No dependencies were installed.
- `python -m unittest -v test_h2_ctm_preflight.py`: exit 0, 7 tests. Tests use temporary staging/profile fixtures only and mock the child process. Negative controls cover absent/missing/invalid movie, CTM title/revision/magic/length, profile escapes and symlink/reparse, file inventory changes/collisions, IPS, executable, CCI, and working-directory errors; rejected cases assert the child process was not called.
- `c++ -std=c++20 -Iazahar/src tests/test_h2_observer.cpp azahar/src/core/h2_observer.cpp -o tests/test_h2_observer.exe`, then run with the existing MSYS runtime directory on PATH: exit 0. Cases cover disabled observer, invalid title, bounded output, required-read failure, movie preflight/playback failure, paired logical args and result, non-H2 query filtering, wrong-thread return, and missing-return teardown.
- No Azahar launch, wrapper process launch, real staging-profile access, emulator connection, guest write, network/debugger/RPC/firewall action, or host input automation occurred.

## Evidence limits

The wrapper tests prove its validation and command construction against small temporary fixtures; they do not establish the current bytes of the real staged profiles, which were not accessed. The private Qt executable was built but not launched. Runtime snapshot coherence and profile selection remain to be checked by a separate, reviewed runtime assignment.

Azahar movie replay supplies recorded raw HID values. Even with matched logical query IDs/results and touch-manager snapshots, the current capture does not establish physical button labels or that the game follows the expected UI branch. The `camp_func_002C1830` results are now recorded; the title's touch manager remains an original dependency. H2 remains open pending independent review and original-versus-patched runtime comparison.


## Follow-up review fixes

The follow-up preflight now compares the inventories produced by the two live
profile walks, after each walk verifies the exact file set, byte size, and SHA-256
against its own manifest. It requires the same relative paths with exact casing
and identical size/hash for every shared entry; the original tree must omit the
IPS, and the patched tree must contain the exact expected IPS path and hash.
The `profiles_differ_only_by_ips` manifest field remains a required declaration,
but it is no longer treated as evidence by itself. Offline fixtures mutate
patched non-IPS bytes, path casing, and file set while refreshing that profile's
manifest, so the single-tree checks succeed and the cross-tree check rejects
those cases. The unchanged two-profile fixture with only the expected IPS passes.

At `camp_func_002C1830`, the generic snapshot path is now skipped unless the
entry arguments are one of the five H2 `(id, mode)` pairs. Other calls at this
shared helper PC therefore issue no process-memory reads and emit no H2 snapshot
or logical-query return. The C++ negative control counts process reads and
checks both record types are absent; the H2 query return-pairing controls still
pass.

Follow-up validation on the pinned private Azahar source:

- `python -m unittest -v test_h2_ctm_preflight.py`: exit 0, 8 tests passed using temporary profile fixtures and mocked subprocess calls.
- `c++ -std=c++20 -Iazahar/src tests/test_h2_observer.cpp azahar/src/core/h2_observer.cpp -o tests/test_h2_observer.exe`: exit 0; running `tests/test_h2_observer.exe`: exit 0.
- `cmake --build build-clang64 --target citra_core --parallel 2`: exit 0, 2 incremental build steps.
- `cmake --build build-clang64 --target azahar.exe --parallel 2`: exit 0, 1 incremental link step.
- `python package_h2_delivery.py`: exit 0; regenerated feature patch and delivery manifest after the build.

No wrapper or Azahar process was launched, no actual staged profile was read,
and no runtime capture was performed. Runtime evidence remains `not_run`; H2
remains open pending independent review and a separately assigned runtime
comparison.

## Live manual capture mode

The private CLI now accepts `--h2-live` alongside `--h2-snapshot`,
`--h2-run-root`, and `--h2-user-dir`. This mode validates the loaded SMT4
process, requires no CTM, starts immediately, and keeps the normal Azahar run
loop. It filters observations to the TitleConfig initializer, Calc states,
Secondary, and ready gate, so unrelated touch, script, and logical-query
traffic does not fill the capture. Reaching the record or byte limit writes a
`truncated` terminal event and stops logging while allowing emulation to
continue.

The focused C++ observer tests pass, including manual-live validation,
TitleConfig-only filtering, and nonfatal record-limit behavior. The private
Azahar executable rebuilt with two jobs and the delivery manifest was
regenerated. A live patched-profile window is now running from the verified
`run-007` staged app and CCI with no movie; its JSONL output is
`build/h2-manual-comparison/run-007/checks/live-patched.jsonl`. Runtime
observation of a user-opened Audio Settings screen is still pending. The
normal-loop PC sampling may miss short-lived call entries; the next manual
check will establish whether it catches the screen's TitleConfig calls.


## CLI dispatch correction

The `citra_meta` entry point probes `citra_cli` before handing arguments to the
Qt frontend. `CheckForOptions` now uses a bounded short-option scan against the
provided option string instead of platform `getopt` behavior. It recognizes
compression options only as single-dash short options declared by `c:x:o:`;
`--movie-play`, `--movie-record`, `--h2-snapshot`, and similarly prefixed long
options are left for Qt. The scanner supports both `-c VALUE` and `-cVALUE`
forms, and honors `--` as the end-of-options marker. `ParseCommand` now returns
failure if called without a compression option rather than falling off a
non-void function.

`tests/test_citra_cli_dispatch.cpp` exercises compression-option positive
controls (`-c`, `-x`, `-o`, and attached arguments), H2/movie long-option
negative controls, similarly prefixed long options, and the actual
`ParseCommand` compression-parser handoff through an offline stub. The Qt
executable was rebuilt with at most two jobs. The wrapper and Azahar were not
run; runtime remains unverified and H2 remains open.
