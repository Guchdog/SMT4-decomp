# Independent review: cumulative H2 cursor image

## Recommendation

**Bounded approval for the cumulative offline image and its seven paired caller scenarios.** All packet hashes matched, and I regenerated the composition into a fresh private output. The result reproduces the pinned cumulative image and report hashes. Four `TitleConfig_Calc` comparisons and three mover/query comparisons passed. The batch adds no new whole-image interworking finding relative to the accumulated base.

This does not establish unrestricted equivalence for `0x00254CA8`: the axis reader’s no-write output path is still excluded, and H2 has not been shown to avoid it. The cumulative fixtures force both floats to be written. Runtime and whole-game claims remain out of scope.

## Fresh recomposition and changed-byte scope

I ran:

```powershell
python tools/h2_cursor_cumulative_closure.py --output build/agent-work/H2-semantic/h2-titleconfig-cursor-cumulative-review/run001/recomposed
```

Exit code: 0. The regenerated report SHA-256 is `470d4613d5ebdf43acd7097d8b74839020c8996a02362b45445ad61e2b0238cd`, identical to both pinned closure reports. Its inputs and outputs are:

- Accumulated base: `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446`
- Updater+mover image: `37cb6046f1be329d7af06ef36430a52897b49c0f96d5b5fdb4353bef39fd4876`
- Query-service IPS: `db23257413866439b86d9ce784da6804b5153106b7386a26356f1751443400ae`
- Cumulative image: `aca919c95b0bc58af0a50b9f9f7f7d22084c2eb1dba5767889258920b08c582f`
- Image size: 3,633,152 bytes, unchanged

I independently applied the query IPS to the updater+mover image; the result equals the regenerated cumulative binary byte-for-byte. Compared with the pinned accumulated base, 2,179 bytes differ. Every differing byte lies inside the three candidate patch extents: `[0x0029F278, 0x0029F67C)` (1028 bytes), `[0x001FF3C4, 0x001FF734)` (880 bytes), and `[0x00254CA8, 0x00254F28)` (640 bytes). The report’s `changed_ranges` are these candidate extents, not 289 separate contiguous byte-difference runs; I separately counted 289 contiguous runs and found none outside those extents. Thus the reported scope is accurate as patch/write scope.

## Paired caller evidence

The fresh closure runner executed the actual selected image bodies for the comparisons:

- Four `TitleConfig_Calc` comparisons passed: stable cursor, active cursor without input, logical input bits, and initialized H2 IDs `(6,15)` / `(5,14)`. The image being exercised contains the candidate updater. Unrelated outer Calc services and the logical-query boundary remain modeled by the existing harness.
- Three mover/query comparisons passed: initialized H2 idle, primary ID 6 with special ID 15, and primary ID 6 with special ID 14. These run the selected image’s mover and logical-query bodies together, with lower query, axis-reader, and angle services controlled by deterministic seams. The recorded trace lengths are 48, 60, and 48 calls, respectively.

All fixtures write both axis sample floats. They verify these defined offline scenarios and do not establish physical inputs, live dependency cadence, or that no-write cases are unreachable.

## Whole-image interworking audit

I compared the pinned base audit with the cumulative-image audit. Both have 105 subsystems and 8 expected overlaps, zero unexpected overlaps, the same `expected_h18_promotions`, `fmt_helper_thumb_bit_restored: true`, and `h2_helpers_preserved: true`. Both report H3 entry absent. Their `branch_issues` and issue strings are identical: the two pre-existing H8 ARM `B` instructions at `0x0032C5D0` and `0x0032C600` target Thumb address `0x0027F3D4`. There is no added interworking finding attributable to this H2 batch, but the aggregate audit is not clean because those inherited errors remain.

## Limits and next action

The `0x0027FBC8` no-write output domain remains unresolved and excluded; no evidence shows that live H2 always writes the two float outputs. The Calc harness models unrelated services; mover scenarios control lower dependencies. Physical mapping/scheduling, runtime audio, emulator behavior, and whole-game equivalence were not tested. This review regenerated the offline composition and callers but did not compile or run a full build.

**Next action:** accept the combined image as bounded offline evidence, keep the no-write limitation explicit, and require separate caller/runtime evidence before claiming that the supported domain covers live H2. The two inherited H8 branch issues remain outside this H2 batch and still block a clean aggregate interworking audit.
