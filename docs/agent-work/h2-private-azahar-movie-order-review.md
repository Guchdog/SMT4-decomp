# H2 private Azahar movie order review — handoff

## Decision

**Status: accept for isolated diagnostic replay.** The current executable SHA-256 matches the delivery manifest. The source review supports replay of the recorded H2 CTM in an isolated fresh-profile run, without savestate load/save. This review does not establish H2 functional acceptance.

## Scope and identity

- Owner: `h2_private_azahar_movie_review`
- Task: `h2-private-azahar-movie-order-review`, run `run-002`
- Reviewed source tree: `build/agent-work/H2-semantic/h2-private-azahar-source`
- No source edits, builds, tests, emulator launches, profile inspection, or emulator controls were performed.
- Manifest records binary `build-clang64/bin/Release/azahar.exe`, SHA-256 `0d99853eb4e90ffd94115bbec9a30191d1f347f57f9aab0342657df6526e4e0a`.

## Findings

1. **Per-type indexing preserves record bytes and expected-type selection.** `BuildH2InputIndex` walks complete 7-byte `ControllerState` records, buckets offsets by the first-byte type, and resets all six cursors. `ReadH2Input` selects an offset only from the requested type bucket and copies the complete record, preserving its payload. In deterministic mode each `Play` overload requests its corresponding enum type. This addresses cross-type cursor shifts from callback ordering.

2. **Exhaustion and completion are bounded, with one domain assumption.** A missing stream returns `false` without modifying the caller's state. After a nonempty stream is consumed, repeated polls select its final sample and stop advancing that cursor. Playback finishes once both the PadAndCircle and Touch cursors are exhausted, even if their lengths differ. Completion intentionally does not wait for accelerometer, gyroscope, IR, or extra-HID streams; that appears scoped to the recorded H2 pad/touch scenario, not a general movie playback policy. A trace with no pad or no touch records could finish immediately when the other cursor is also done; the actual trace counts were outside the allowed paths.

3. **Activation is restricted to H2 observer startup.** Qt sets deterministic input playback from `system.IsH2ObserverEnabled()` immediately before `StartPlayback`; `StartPlayback` builds the index only when the flag is enabled. Normal playback retains the serialized single-cursor path. `Shutdown` clears the flag and per-type cursors. The H2 observer path also requires a movie request and validates movie/revision/title identity before startup.

4. **Savestate restore is not supported by these new cursors.** Movie serialization saves `current_byte` and `current_input`, but not `h2_input_cursors` or the deterministic-playback flag; loading a read-only movie state restores the legacy byte cursor and re-enters `Playing` without rebuilding/restoring the per-type cursors. A save/load during deterministic replay can therefore resume at mismatched per-device positions. Keep the isolated runtime replay free of savestate load/save operations and use a fresh observer profile/run.

5. **Source, patch, and binary manifest hashes match.** SHA-256 checks of `movie.h`, `movie.cpp`, `citra_qt.cpp`, `azahar-h2-observer.patch`, and the current `build-clang64/bin/Release/azahar.exe` match their corresponding delivery-manifest entries (case-insensitive comparison).

## Runtime replay recommendation

The coordinator may replay the already-recorded CTM in a fresh isolated H2 observer run. The current executable SHA-256 matches the manifest. Do not load or save savestates. Preserve observer output and replay logs; treat the run as diagnostic evidence only. Stop if per-type exhaustion or completion occurs before the expected H2 observer sequence, and report that as a counterexample rather than accepting the milestone.

## Evidence levels and limitations

- Source/manifest inspection: **completed**.
- Current source and patch hash comparison to manifest: **completed**.
- Current executable hash comparison to manifest: **completed; exact SHA-256 match**.
- Build, tests, runtime replay, CTM record counts, and savestate behavior execution: **not run**.
- Functional H2 acceptance: **not claimed**.

## Commands and exits

Commands were read-only PowerShell source/manifest inspection and SHA-256 queries; each completed with exit code `0`:

- `Get-Content` on `AGENTS.md`, `docs/agent-workflow.md`, the task brief/packet, the three declared source files, the delivery manifest, and the declared patch.
- `Select-String` on `movie.cpp` and `citra_qt.cpp` for index, cursor, completion, activation, playback startup, and shutdown sites.
- `Get-FileHash -Algorithm SHA256` on `movie.h`, `movie.cpp`, `citra_qt.cpp`, `azahar-h2-observer.patch`, and `build-clang64/bin/Release/azahar.exe`.

## Source hashes observed

- `movie.h`: `d844e386b170dbf19a18ec00d4cba68af690a2c7f7c626eac0e3ce02ea34dfa4`
- `movie.cpp`: `9057a561f78b15819119aabed26a7f67192e5d0701cd743aa722719fe1ef5c8d`
- `citra_qt.cpp`: `8deccc335a498374215b40fa3b77ab9f6313e807dd21e90e795dfdfc8da7c823`
- `azahar-h2-observer.patch`: `5bfe8b93bda9ba740a1c46a6e5ae00c55cc50b01685cdbda5ef9efe48fb3e81f`

## Executable hash observed

- `azahar.exe`: `0d99853eb4e90ffd94115bbec9a30191d1f347f57f9aab0342657df6526e4e0a` (matches manifest).
## Next action

Coordinator: proceed with the bounded fresh-profile CTM replay using the verified executable, without savestate load/save, and capture the outcome as diagnostic evidence.



