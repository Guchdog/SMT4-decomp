# H2 observer failure isolation

## Change

The RunLoop's optional H2 observer callback now has an explicit `void` contract. Manual snapshot failure, ordinary capture failure, or a thrown capture/serialization exception calls `FailClosed` and returns from the observer callback; the core loop then proceeds to `ExecuteCore`. The existing `HasFailed()` guard skips later observer callbacks. The observer suppresses a clean `complete` terminal record after failure and attempts an `incomplete` terminal record while output remains available.

`bootmanager.cpp` is unchanged (SHA-256 `05ae1b22191e0e2f90e3d99e14d4c1456ad26acd53395d45580e91b3032f4ab1`). It continues to stop and report genuine non-success results returned by `Core::System`; observer failure no longer has a boolean path that can be translated into `ErrorUnknown`.

## Focused checks

- Existing `test_h2_observer.exe` passed with exit code 0 when run with the clang64 runtime directory on `PATH`. Its test output reports mode limits, disabled no-op, invalid configuration, program ID filtering, PC allowlist/snapshots, bounds, and live TitleConfig/H2-input capture. The binary directly exercises `H2Observer`, not the RunLoop-to-Qt boundary.
- The private Azahar `azahar.exe` target built successfully with `--parallel 1`; the build compiled `core.cpp`, relinked `libcitra_core.a`, and linked `azahar.exe`. Build output is retained under `build/agent-work/H2-semantic/h2-observer-failure-isolation/run-002/checks/`. The completed command returned exit code 0.
- No emulator, profile, debugger, network, or host input was used.

## Limits

No RunLoop integration fixture is available within the assigned file lease. I did not add a source-shape test as a substitute. The direct observer unit binary does not validate that callback failure continues guest execution in a live Core::System instance, nor does it test JSONL writes failing at runtime. This change isolates the optional observer path; it does not identify the cause of the earlier screenshot/fatal dialog, reproduce live capture, or establish H2 behavior/equivalence.
