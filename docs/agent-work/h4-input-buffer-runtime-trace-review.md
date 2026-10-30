# Independent review: H4 runtime input-buffer trace (run-005 review of run-004 evidence)

## Summary

The run-005 review packet revalidates all 14 declared input hashes; they bind the raw sidecars, aggregate report, source-save integrity artifact, corrected trace document, and runner. These are the run-004 evidence sources; no sidecar pinning remains outstanding. The cited runtime report and its paired per-run JSON sidecars support a bounded passive memory observation after a scripted save-UI path to the field manager: 250 field-manager observations per profile; four later, sequential producer-path breakpoints; and all-zero sampled primary, alternate, and counter bytes at the probe entry/stop points. The snapshot helper is read-only.

This is not an active axis-input trace, continuous buffer history, player movement test, or H4 equivalence result. It establishes memory-state observations only. The JSON includes scripted trigger-0 results to confirm the populated save slot and acknowledge “Load complete”; there was no physical/front-end gameplay or axis input. Screenshot fields are null, so the claimed field checkpoint is not visually corroborated by this run.

## Provenance

Aggregate report: `build/agent-work/H4-semantic/h4-runtime-buffer-capture/run-001/checks/runtime-input-trace-007/report.json`, SHA-256 `9cee1c43ae14a71337c95e8dc88db1b3214dec83bd793cd478638ea00d780fe0`, status `observed`.

Run-004 explicitly pins both raw sidecars: `original.json` `586188ecb263aa540df95e418b5a904b458978873edff6928680c4266de25d0e` and `patched.json` `50653685394bafcc5e89dede0cc91060ce40528c42c249f725805d34c72aeed`. It also pins `source-save-integrity.json`, SHA-256 `11d47c141b4cf2c958879a40bd7bb6fbe744d739544da90a8006de0fe8542b29`. The aggregate omits profile manifests, so the pinned sidecars supply the per-file hashes.

The runtime report labels runs original/patched but contains no original/patched executable or H3 patch/source-object hashes. The source identity is therefore not bound by this JSON report.

## Ticks and buffer probes

Each sidecar has `field_manager_reached=true`, 250 `field_scene_ticks` observations indexed 0–249, and 249 additional successful `field_tick_status` entries indexed 1–249. Detailed buffer fields are present only at sampled ticks 0, 1, 2, 5, 10, 25, 50, 100 and 249; each sampled primary/alternate record is zero. The 250 callbacks are counted/observed, but buffer bytes are not recorded continuously on every tick.

After the tick batch, `probe_field_calls` visits four addresses in order. All hit in both profiles, were not interrupted, and entry/stop snapshots match:

| Address | Entry r0-r3 | Observed buffer state |
|---|---|---|
| `0x001078E8` | `0x004E3BE8, 0x004E3C28, 0, 1` | 0x30 primary span, 0x10 alternate span, and 0x7C counter table all zero |
| `0x001078EC` | `1, 0x004E3C2C, 0x004E3C30, 0` | Same; entry equals stop |
| `0x0011C640` | `0x10000000, 0x004E3C28, 1, 0x000FFED0` | Same; entry equals stop |
| `0x0011C644` | `0x000FFED4, 0x000FFED0, 0, 0` | Same; entry equals stop |

The primary snapshot begins at `0x004E3C28` and spans 0x30 bytes; the separate 0x10-byte snapshot at `0x004E3C48` duplicates the alternate record's first 16 bytes in that span. The 0x7C-byte counter table starts at `0x004E3C58`. Original and patched values match for all of these probe snapshots and their manager/calibration prefixes. The data do not identify the producer's source object as a physical input device.

## Documentation reconciliation and remaining discrepancy

The run-004-pinned version of `h4-input-buffer-runtime-trace.md` has corrected the earlier `0x001078E8` description: it now records `r0=0x004E3BE8`, loaded through `0x004650A0`, and explicitly distinguishes it from the alternate sample at `0x004E3C48`. This matches the raw registers and snapshot label. It also narrows the equality statement to the callback signature and discloses the view difference. The milestone now carries the same caveat.

The raw runner computes `field_scene_semantics_equal` from only `(entry r0, entry r3, r1_r2_context_arg)` at each tick. The captured 0x170-byte view prefix is not wholly equal: at offsets `+0x164..+0x166`, all nine detailed tick snapshots show original bytes `00 64 71` and patched bytes `80 4A 76`. The bytes are untyped here and remain unexplained. Therefore the current text's explicit callback-signature scope and “three bytes remain unexplained” wording are accurate; do not call the complete field state equal.

The run-004-pinned trace markdown links the separate `source-save-integrity.json` artifact and explicitly says that runtime JSON contains hashes only for staged copies. That integrity artifact distinguishes the known fixture SHA-256 recorded before the runtime trace (`6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`) from a separately recorded post-trace SHA-256 (same digest), and records `unchanged_from_known_fixture=true`. This is an appropriately separate provenance source; the runtime JSON itself does not contain a source-save hash. I reviewed only the pinned JSON artifact and did not open or hash the source save file.

## Read-only telemetry and input boundary

`axis_input_snapshot(rsp)` reads the manager prefix, the pointed 0x20-byte calibration prefix, primary/alternate buffer spans, and counter table via `rsp_read_mem`. It contains no guest-memory or register write operation. The surrounding routine manipulates software breakpoints and continues execution; its optional `axis_output` branch can write only for the separate `0x0027FBC8` camera-reader probe. This run's addresses are the four producer-path sites and the raw events contain no `axis_override` entry.

The observed sequence uses controlled trigger-0 logical results for UI navigation/acknowledgment. Thus “no input” is accurate only as “no physical/front-end gameplay or axis event.” The probes are sequential after 250 field callbacks, not per-frame observations of those addresses. The raw report records no active-input response or cadence. Neither the `field_scene_semantics_equal` flag nor a loaded manager checkpoint establishes visual-scene equivalence, player position changes, movement, interactions, transitions, physical control mapping, or H4 acceptance.

## Staged save/profile integrity

In both sidecars the staged save copy is 151,088 bytes and has SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` before and after; `save_unchanged=true`. Each sidecar contains 16 tracked non-mod profile file hashes in `profile_user_before` and `profile_after`; each pair is identical and `non_mod_profile_unchanged=true`.

The original and patched **starting** profile manifests are not identical: six entries differ—`config/qt-config.ini`, `log/azahar_log.old.txt`, `log/azahar_log.txt`, two OpenGL shader-cache files, and `sysdata/play_time.bin`. Thus the report supports no changes within each tracked profile during its run, not identical profile baselines. The aggregate JSON omits the manifests. The documented statement that staged non-mod profile files stayed unchanged within each run is accurate.

## Assessment

Accept the zero-buffer result as bounded memory evidence and the snapshot helper as read-only. Retain the corrected r0/callback-signature language in the current docs; keep the unexplained view-byte difference visible. The raw sidecars and source-save integrity artifact are already pinned in run-004. Source/image hashes tying the original/patched runtime executions to exact code remain absent. H4 remains open for an active input source/event trace, repeatable refresh cadence, verified player-state update/movement, interaction, and zone transition.

## Checks performed

- Compared all 14 hashes in run-005 `task.json`; all matched. Run-004 had also pinned the sidecars and source-save integrity artifact.
- Parsed the aggregate report, both pinned raw JSON sidecars, and the pinned source-save integrity artifact (hashes above); checked 250 callback observations, 249 subsequent callback statuses, the four ordered hit records, selected zero-buffer snapshots, probe entry/stop equality, staged save hashes, and profile manifests.
- Compared original/patched probe captures and view bytes; confirmed the three-byte difference at view offset `+0x164..+0x166` and six different starting profile entries.
- Read the snapshot helper and optional override guard. No source save access, build, test rerun, emulator launch, input action, or guest-memory write was performed.
