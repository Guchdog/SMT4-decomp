# H2 cursor cumulative closure — run001

## Result

Composed the reviewed `0x0029F278` stateful cursor updater, `0x001FF3C4` axis mover, and bounded `0x00254CA8` logical-query service into one offline image. The closure script applies the reviewed query IPS to the already reviewed updater+mover image, verifies the pinned input hashes, exact image length, deterministic output, and that every changed byte lies inside the three candidate bodies.

| Evidence | Result |
|---|---:|
| Original accumulated H2 base SHA-256 | `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446` |
| Updater + mover image SHA-256 | `37cb6046f1be329d7af06ef36430a52897b49c0f96d5b5fdb4353bef39fd4876` |
| Query IPS SHA-256 | `db23257413866439b86d9ce784da6804b5153106b7386a26356f1751443400ae` |
| Cumulative image SHA-256 | `aca919c95b0bc58af0a50b9f9f7f7d22084c2eb1dba5767889258920b08c582f` |
| Image size | 3,633,152 bytes, unchanged |
| Changed bytes | 2,179; all inside the three reviewed candidate extents |
| `TitleConfig_Calc` scenarios | 4/4 passed against the accumulated original base |
| Mover + logical service scenarios | 3/3 passed against the accumulated original base |

The Calc scenarios cover a stable cursor, active cursor without input, logical input bits, and initialized H2 IDs `(6,15)` / `(5,14)`. They execute the actual cursor implementation in each compared image; unrelated outer Calc services and the logical-query boundary are modeled by the existing harness. The mover scenarios execute the selected image's actual mover and logical-service bodies together, while lower query, axis-reader, and angle dependencies use deterministic seams. Cases exercise idle H2 state and special IDs 15 and 14. The harness reports 48, 60, and 48 ordered calls respectively. Both float output samples are written in these scenarios.

The full accumulated interworking audit reports the same two pre-existing H8 ARM-to-Thumb branch findings on both the original accumulated base and this image (`0x32C5D0` and `0x32C600` to `0x27F3D4`). It reports zero unexpected overlaps and preserved H2 helpers. The audit also reports H3 entry absent on both images. These existing whole-image findings prevent a green aggregate audit; this H2 batch introduces no additional finding in that comparison.

## Reproduction

```powershell
python tools/h2_cursor_cumulative_closure.py --output build/agent-work/H2-semantic/h2-titleconfig-cursor-cumulative-closure/run001/results-002
python tools/audit_accumulated_substitutions.py --image build/agent-work/H2-semantic/h2-titleconfig-cursor-cumulative-closure/run001/results-002/code.h2-cursor-cumulative.bin --output build/agent-work/H2-semantic/h2-titleconfig-cursor-cumulative-closure/run001/results-002/interworking-audit.json
```

The closure command exits 0. `report.json` is the machine-readable comparison record; `code.h2-cursor-cumulative.bin` and `.ips` preserve the composed image and final incremental patch. The original base and intermediate artifacts are unchanged.

## Limits

This is bounded offline Unicorn evidence, not runtime or whole-game equivalence. The Calc harness models unrelated outer services. Lower logical, axis-reader, and angle services are controlled for the mover composition. The `0x0027FBC8` no-write output path remains unresolved and is excluded; H2 has not been proven to avoid it. Physical control mapping, natural event timing, runtime audio, and emulator behavior remain unverified. The three ledger rows remain truthfully classified `non_matching`.

The individual bodies already passed independent review. This cumulative image and its combined composition report still need an independent closure review before treating the combined batch as reviewed.
