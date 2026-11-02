# Independent slot integration review: `0x001FF3C4`

## Recommendation

**Bounded approval for the reproducible accumulated-image slot artifact and its four offline caller compositions.** All declared packet hashes matched. I independently regenerated the integrated artifact in fresh `run003`; its base, result, IPS, body, and report hashes match the pinned run002 artifact. All four accumulated `TitleConfig_Calc` scenarios passed. I found no placement or composition mismatch. No emulator or whole-game equivalence is claimed.

## Reproduction and object isolation

The integration runner’s `candidate_body()` compiles to a fixed module-level object path by default. To keep the packet inputs frozen, I redirected that in-memory `h2_1ff3c4_experiment.OBJ` value to the fresh `build/h2-1ff3c4-integrated/run003/candidate.o` and invoked the unchanged `h2_1ff3c4_integrate.main()` path with `--output build/h2-1ff3c4-integrated/run003`. This used one focused compile and did not overwrite shared/pinned build outputs. The run-local object SHA-256 is `29346e7b35333bbb4dbb9d0f662225aeda68194b393336f6b66a8e2333d531ae`.

Fresh report SHA-256: `c381c2eb2c2b8d8769960c95c1cffae46c374c4fbc691f7fa421da4ec13e7fc6`. It records base SHA-256 `d16516c9ce191d88f728d14dcc08bf4bf2a6d3a81ee11603f4b00253e8b1c9cb`, result SHA-256 `37cb6046f1be329d7af06ef36430a52897b49c0f96d5b5fdb4353bef39fd4876`, and IPS SHA-256 `8dc60d81cbaed38086924c717d6213581434ea1145aa614c1c2f751c97b4ad38`. The report’s body is 880 bytes with SHA-256 `44c6adab3101df0623cdeeea1b69459c41c7d0bfb4c8f12bd9fe62db9dd04717`.

## Slot and IPS audit

The pinned base is the accumulated H2 image already containing the `0x0029F278` updater. The new 880-byte sequence is written at `0x001FF3C4`, inside its original 1104-byte span. I independently compared the fresh base and final image: all differing bytes fall within `[0x001FF3C4, 0x001FF744)`, and the remaining 224 bytes through the original slot end match the base. Reapplying the single-record IPS to the base reconstructs the exact result image. The original and result sizes match.

The relocation report contains exactly ten `R_ARM_CALL` sites, each rebased to the even ARM address `0x00254CA8`. The main body is 580 bytes; the two relocation-free helpers are 152 bytes at offset `0x244` and 148 bytes at offset `0x2DC`, forming one contiguous 880-byte sequence. This matches the body hash and placement from the independently reviewed direct run. No unrelated image slot changed.

## Caller composition results

All four pinned accumulated-image comparisons passed with 14 caller trace events each:

- stable cursor
- active cursor without input
- logical input bits
- initialized H2 cursor

The integration runner compares the accumulated base with only this slot replacement, while the actual candidate updater and query dependency execute in their respective images. Unrelated outer Calc services remain modeled. The H2 case uses the statically recovered initialized cursor scenario. This establishes those fixture compositions only, not all caller states or natural runtime scheduling.

## Limits and next action

This is offline artifact and caller evidence. The task did not run the full build or emulator. Physical input mapping/timing, runtime audio, malformed pointers, concurrency/MMIO, and whole-game equivalence remain unverified. The underlying query service remains the pinned original dependency; modeled outer Calc service boundaries remain.

**Next action:** accept the in-place slot artifact for integrator-owned H2 closure, then run the defined accumulated-image runtime scenario only after offline checks pass.
