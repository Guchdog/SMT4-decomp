# Independent H2 setup review: `0x0029F278`

## Recommendation

**Bounded approval for the recovered initialized H2 cursor domain and the offline slot comparisons.** I verified the packet pins and independently ran the latest slot runner into fresh `run005` with seed `20261106` and 141 seeded samples. All 158 direct cases passed; all four original-image and all four accumulated-image `TitleConfig_Calc` compositions passed. The wrong-call-target control was detected. I found no counterexample in these fixtures.

## H2 initialized setup and query trace

The frozen `0x001FF3C4` contract identifies the H2 setup values: axis 0 flags `6`, width `3`, start `2`, threshold `3`, count `3`, index/offset zero, and query bytes `(6,5,32,32,15,14,32,32)`. Axis 1 has width `1`, threshold/count `1`, IDs `(3,4,32,32,12,13,32,32)`, and zero index/offset. The runner’s named `h2-initialized-axis0-special-ids` fixture matches these fields (including axis flags), sets the total to `3`, and uses ordinary zeroed logical-input state. In caller scenarios it writes the equivalent initialized fields into `TitleConfig_Calc` work at `+0xE8`.

The direct trace begins with `cursor_begin(20,20,20,20)`, then one `axis_move(cursor)` call. Decimal pointer `4722688` is `0x00481000`, the fixture’s cursor/axis-0 address; there is no second axis-move call. This matches the wrapper’s signed `axis0 threshold > 1` gate and axis1 threshold `1` skip. The nested query observations include `(6,15)` then `(5,14)` through mode-0’s `0x002BFFBC` service calls, followed by the logical-query traffic. The observed logical queries include the ordered calibration sequence `14,15,12,13` after each special-ID pair. The wrapper’s initial `cursor_begin` occurs before `axis_move`; the pinned wrapper contract says this initializes byte `0x00465288` to `1`, which enables the calibration path.

The runner does not hook `0x00254CA8` itself, so it does not emit each outer `(id0,id1,mode)` tuple as a direct trace row. The required ten-call mode sequence—`(6,15)` and `(5,14)` at modes `0,2,1`, then the `(32,32)` sentinels—is supported by the frozen static contract/disassembly and the runner’s observed nested helper-call order; the `0/2/1` attribution is contract-derived rather than independently captured as an outer call argument. This is a trace-granularity limit, not a detected mismatch. The calibration path is observed through its nested logical-query calls, under the wrapper’s preceding global initialization.

## Fresh run and caller compositions

Command:

```powershell
python tools/h2_29f278_slot_experiment.py --output build/agent-work/H2-semantic/h2-titleconfig-0029f278-slot/run005 --seed 20261106 --samples 141
```

Exit code 0. The report SHA-256 is `03fbf0e74575cd696a031060cc11301642380597876ce0ae7ac9557e3e7b93dc`. It records 158/158 direct passes, no first counterexample, and a detected wrong-target control. It pins candidate source `545cf388…4481a`, runner `fa26d733…f3e64`, original image `1f98884f…aa558`, accumulated base `acd8b2f3…51446`, and accumulated result `d16516c9…1c9cb`. The in-place body is 1024 bytes plus the four-byte mask table at `0x0029F678`; the 508-byte suffix is preserved. Original and accumulated overlay hashes match the frozen run004 evidence.

All four original-image caller cases passed: stable cursor, active cursor/no input, logical bits, and H2 initialized cursor. All four corresponding accumulated-image cases passed as well. Those harness scenarios execute the appropriate `TitleConfig_Calc` image and updater/helper code while retaining modeled unrelated outer Calc services. Each H2 initialized row reports 14 caller-trace events and matching output. These are fixture-driven compositions, not proof of natural runtime scheduling.

## Limits and next step

The evidence uses a statically recovered initialized cursor fixture and synthetic ordinary RAM. It does not prove physical control mapping or event timing, arbitrary future mutations of query bytes, runtime sound, invalid/malformed object behavior, MMIO/concurrency behavior, or whole-game equivalence. The interior-entry scan only checks word-aligned ARM branches and aligned absolute-pointer candidates. No emulator or full build was run in this supplemental review.

**Next action:** accept this supplemental H2 setup coverage with the mode-capture limitation recorded, retain the truthful `non_matching` ledger classification, and proceed through the integrator’s offline closure before any scoped runtime comparison.
