# H2 live query trace and launch lineage

## Result

Implemented a narrowly scoped Dynarmic translation hook for the live H2 logical
query path. The live path now injects observer callbacks before the instruction
at `0x002C1830` and before the six statically enumerated Calc return PCs
`0x001EAAC0`, `0x001EABE0`, `0x001EAC24`, `0x001EAC54`, `0x001EAE68`, and
`0x001EAF18`. These callbacks capture live R0/R1 and SP/LR values in IR, then
record the guest thread/process identity and observer sequence. Only the five
accepted `(control_id, mode)` tuples produce query entries. Returns are paired
by thread, normalized LR return address, and matching SP; wrong return sites,
wrong threads, and stack mismatches do not produce a result.

Qt live mode retains the normal tight `RunLoop()` behavior. Query entry and
return PCs are excluded from the coarse pre-slice observer so the JIT hook is
their single source of records. The existing Ctrl+Shift+F8 on-demand memory
snapshot request remains independent. No F9 trace arm, full-session stepping,
guest writes, or host-input injection was added. The hook is present in each
Dynarmic instance from JIT creation, while its runtime callback is a no-op
unless the live observer is enabled; this avoids a JIT-cache invalidation race
when observer setup follows JIT construction.

The live wrapper launch ledger remains separate from CTM replay. Live launches
record argv, cwd, preflight hashes, intended private executable identity, OS
reported executable path/hash while the process is alive, host PID, and exit
code. Staged stock executable identity remains a distinct field. CTM continues
to use its prior subprocess route and capture limits.

## Validation

- Built private `azahar.exe` in `build-clang64` with CMake/Ninja and at most two
  jobs. The final target linked successfully; the binary SHA-256 is
  `d5e5678b2af6d8e4acedc98f1c85713cd09e5757b3478c1a0dcde8aad5323c3d`.
- C++ observer harness passed. It covers all five accepted tuples, entry/return
  sequence linkage, non-H2 controls, wrong-thread returns, mismatched return
  PCs, and stack mismatch rejection. Coarse `ShouldObservePC` remains false for
  the JIT-owned query sites while the explicitly marked hook path records them.
- `python -m unittest test_h2_live_preflight -v`: 19 tests passed after package
  regeneration, including no-movie live invocation, CCI-last argv ordering,
  launch-record fields, and mismatch rejection before subprocess launch.
- Regenerated `azahar-h2-observer.patch` and `h2-delivery-manifest.json`; a
  package hash verifier checked all 30 binary, feature, shim, and patch entries.
  The manifest includes `src/core/arm/dynarmic/arm_dynarmic.cpp` and the private
  core include-path change needed for Dynarmic's bundled MCL header.
- The existing CTM wrapper suite remains red: 5 failures and 1 error of 8.
  Several fixture paths fail first with `CTM contains no recorded A-button
  press`; the symlink fixture cannot create a symlink on this Windows account
  (WinError 1314). No CTM route or fixture was changed for this task.

## Evidence limits and next step

The build and offline tests prove compileability and observer/wrapper behavior,
not that a live emulator reaches the hook PCs or that a real paired run is
equivalent. No Azahar process was launched and no profile was inspected. A
separately authorized live capture can now use the reviewed launcher: bracket
one repeatable action with Ctrl+Shift+F8 snapshots and compare ordered query
entry/return records and snapshots across the two staged profiles. A zero query
event should now be interpreted alongside the compiled JIT hook, output
capacity/truncation status, and the launch ledger; it is not by itself proof of
input equivalence.
