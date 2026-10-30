# H2 private Azahar live log capacity

## Result

Added distinct mode bounds to the private H2 observer. Movie/CTM replay defaults remain **4,096 records / 16 MiB**. Manually controlled live capture now uses a bounded **250,000 records / 64 MiB** ceiling, applied in `H2Observer::Initialize` only when `live_mode` is true. The header exposes named constants and `ApplyH2ObserverCaptureLimits`, which is directly asserted by the focused C++ harness. Existing custom CTM limits remain effective because the helper leaves non-live configurations unchanged.

The harness passed all cases, including its existing explicit one-record CTM truncation test and live observer capture flow. The private `azahar.exe` target rebuilt successfully with a maximum of two jobs. The generated observer patch and delivery manifest were regenerated. A manifest verifier checked 27 source, compatibility input, patch, and binary hash entries; all matched.

## Changed artifacts and hashes

- `build/agent-work/H2-semantic/h2-private-azahar-source/azahar/src/core/h2_observer.h` — `f021dca847cd5f20a83376a3819d27cc84feae100a5b378dcffab4d018736629`
- `build/agent-work/H2-semantic/h2-private-azahar-source/azahar/src/core/h2_observer.cpp` — `46ff2cdbe1bc398b8d80019c5b77e33ff50f4aaf28f9ae5610947494abb8d8ad`
- `build/agent-work/H2-semantic/h2-private-azahar-source/tests/test_h2_observer.cpp` — `aaea3a77acedb46a4907974faa30c40f07b9ede330f385e6d80850ec0a956284`
- `build/agent-work/H2-semantic/h2-private-azahar-source/azahar-h2-observer.patch` — `928cdf761fcddb670d234956dc437505bf92a688594f04811c9c77e7d9d3b158`
- `build/agent-work/H2-semantic/h2-private-azahar-source/h2-delivery-manifest.json` — `42d1710538bb4a983edd78aae79c0e1cdf422e1b9806a7e7b08623ddf53d237e`
- Private executable `build/agent-work/H2-semantic/h2-private-azahar-source/build-clang64/bin/Release/azahar.exe` — `e9eaa321899a796c17e9460cf8b4a7e003e2606712f1fcc8f1fb485d8f5f406d`
- Package verifier output `build/agent-work/H2-semantic/h2-private-azahar-live-log-capacity/001/package-hash-verification.json` — 27 entries verified, `all_ok: true`.

## Commands and evidence

- Focused harness compile: `C:/msys64/clang64/bin/c++.exe -std=c++20 -O0 -I build/agent-work/H2-semantic/h2-private-azahar-source/azahar/src build/agent-work/H2-semantic/h2-private-azahar-source/tests/test_h2_observer.cpp build/agent-work/H2-semantic/h2-private-azahar-source/azahar/src/core/h2_observer.cpp -o build/agent-work/H2-semantic/h2-private-azahar-live-log-capacity/001/checks/observer-harness/test_h2_observer.exe` — compiled successfully. Execution required `C:/msys64/clang64/bin` on `PATH` for its runtime DLLs; rerun exited 0 and printed `All H2Observer unit tests PASSED.`
- Private target build: `C:/msys64/clang64/bin/cmake.exe --build build/agent-work/H2-semantic/h2-private-azahar-source/build-clang64 --target azahar.exe --config Release --parallel 2` — exit 0 (`ninja: no work to do` on the final confirmation; the preceding build linked `bin/Release/azahar.exe`). The attempted target name `azahar` was not a Ninja target (exit 1); `ninja -t targets` identified `azahar.exe` and the correct target then built.
- Package regeneration: `python package_h2_delivery.py` from the private package root — exit 0.
- Hash verification: `python build/agent-work/H2-semantic/h2-private-azahar-live-log-capacity/001/verify_package_hashes.py` — exit 0; checked all manifest feature inputs, compatibility inputs, patches, and executable.

## Evidence boundary and next action

Compiled and focused harness evidence is available. No Azahar process was launched; no emulator, runtime, profile, debugger, network, or input automation was used. Therefore there is no runtime evidence for long live-session capacity or whole-game behavior. This change demonstrates that the configured bound is raised, not that a 250,000-record capture was exercised. Next, independently review the patch and, under a separate explicit runtime assignment, capture a manually controlled live session without attaching a movie or savestate.
