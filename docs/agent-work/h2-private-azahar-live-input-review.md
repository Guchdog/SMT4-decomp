# H2 private Azahar live-input observer: independent review

## Decision

**accept**, for the bounded source/test review. The extension's source routes the five listed `(control_id, mode)` tuples through the logical-query path, records a result only at a matching return site on the originating thread, and returns from the shared helper before any guest read for an unrelated tuple. Live query entry/return handling does not take the full H2 memory snapshot. On-demand snapshots are a separate live-only request and validate the already-validated title/process identity before guest reads.

This accepts the source/test design for a future guarded runtime assignment. It does not establish that the private build runs, that callbacks occur at the expected timing, or that any runtime/manual comparison has been made.

## Findings

- `h2_observer.cpp:58-62` enumerates exactly `(9,1)`, `(4,0)`, `(3,0)`, `(0,1)`, `(1,1)`. At `:440-484`, live mode ignores unselected PCs, queues a pending query only for those tuples, pairs a return by thread ID and normalized LR return PC, checks stack pointer equality, and emits the result from `r0`. For the shared `0x002C1830` entry, an unrecognized tuple returns at `:481` before allowlist snapshots or reads; recognized live queries return at `:484` before the full snapshot path.
- `core.cpp:118-147` invokes this callback only for selected observation PCs or when the atomic manual-snapshot request is pending. Its process reader validates guest virtual pages before `ReadBlock`; it does not write guest memory. The read path is ordinary in-process emulated memory access. The reviewed source adds no debugger/RPC/network route, and observer setup rejects GDB/RPC enabled configurations.
- `CaptureManualSnapshot` at `h2_observer.cpp:257-297` is live-only, requires a validated title and matching program ID, process ID, and process name, then reads the config bytes and bounded `TitleConfigWork` region. The Qt shortcut requests a snapshot through the system's atomic flag; it does not snapshot each query. The snapshot is serviced at a later core instruction callback, so capture time is the next eligible emulated instruction, not the exact keypress instant.
- The focused C++ harness contains a positive logical-query entry/return case, a wrong-thread and missing-return control, an unrelated `(99,77)` negative control asserting zero reads/no snapshot/no query-return event, and a live-mode filtering plus manual titleConfig snapshot case. It covers the required behaviors at source/harness level. It exercises only one of the five accepted pairs as a positive example; the other four are present in the implementation's predicate but lack separate positive harness cases.

## Manual comparison capability and limits

The JSONL sequence can support a manually paired comparison when an operator brackets a short, repeatable input action with Ctrl+Shift+F8 state snapshots and compares the ordered logical-query returns plus `g_ConfigBytes`/`TitleConfigWork` bytes across original and patched runs. The observer neither records nor synthesizes host input. Records have a sequence number and guest PC, but no wall-clock, frame, tick, or explicit action label; the operator must keep actions isolated and annotate which action each snapshot brackets. A request may be serviced one or more instruction callbacks after the shortcut, and a request made while emulation is paused waits until execution resumes. Results are limited to the five statically documented query tuples and the title/process identity accepted at startup; this is not complete host-input telemetry or a runtime equivalence result.

## Provenance and review execution

The seven packet-declared Azahar source/test/patch/manifest hashes listed in `task.json` match the current files. No source, test, patch, manifest, profile, board, or milestone files were changed. I performed read-only source and test inspection and hash verification only. I did not run a test, build, wrapper, emulator, debugger, RPC/network route, profile access, or input automation.

Current source/test hashes:

| File | SHA-256 |
|---|---|
| `azahar/src/core/h2_observer.cpp` | `4bbbb86bdea4f40dc27a3ac8068d86030841e8dc423b10c8d3a9d9668092371d` |
| `azahar/src/core/h2_observer.h` | `f0bd7b862f0097077c20f4d00ca762e23dc3c399c2a2d0cce59453a2514664d4` |
| `azahar/src/core/core.cpp` | `1895a57e7d6d57de5de2e5a43e9af114bb07eb3b08a134df10fc39d8eda6654a` |
| `azahar/src/citra_qt/citra_qt.cpp` | `754f1a694f4198187e8c7c214051273de8dec942ecbc73a6765650fddf5c316c` |
| `tests/test_h2_observer.cpp` | `af6d97ced9d5c17bbeb00a5d035dbea2b3d11f4cb79942733d1cbd70d5a911ef` |
| `azahar-h2-observer.patch` | `3ed1e814abc52c390b00eadb0f7c165ff4d6afc79a61e92b58f52fe8ced3ea16` |
| `h2-delivery-manifest.json` | `54a5b876c21e58224505e9babb125eb21b51d6faf0ae5753759644d67592bc6f` |

## Evidence levels and next action

- Compiled: `not_run` by this reviewer; prior implementation claims are not independently verified here.
- Differential: `not_run`.
- Caller: source wiring reviewed; no runtime caller evidence from this review.
- Runtime: `not_run`.

Next action: coordinator may accept this bounded review and assign the guarded paired manual-input runtime comparison, recording the fixed profiles/image, isolated input actions, snapshot ordering, and capture completeness. Do not infer runtime equivalence from this review.
